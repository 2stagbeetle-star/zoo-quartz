#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

TARGET_FILES = [
    Path("17_求人情報/生き物イベント掲示板.md"),
    Path("zoo-quartzg56/content/17_求人情報/生き物イベント掲示板.md"),
]

MAIN_START = "<!-- AUTO-EVENTS:START -->"
MAIN_END = "<!-- AUTO-EVENTS:END -->"
SPECIAL_START = "<!-- AUTO-EVENTS-SPECIAL:START -->"
SPECIAL_END = "<!-- AUTO-EVENTS-SPECIAL:END -->"

ANCHOR_RE = re.compile(
    r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
    re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
EVENT_CARD_RE = re.compile(
    r'<div class="event-card">(.*?)</div>\s*<!-- event-card -->',
    re.DOTALL,
)
DATE_PART_RE = re.compile(r"(?:(20\d{2})\s*年\s*)?(\d{1,2})\s*月\s*(\d{1,2})\s*日")
DATE_TEXT_RE = re.compile(
    r"((?:20\d{2}\s*年\s*)?\d{1,2}\s*月\s*\d{1,2}\s*日(?:\s*\([^)]+\))?"
    r"(?:\s*[〜～\-]\s*(?:(?:20\d{2}\s*年\s*)?\d{1,2}\s*月\s*\d{1,2}\s*日(?:\s*\([^)]+\))?))?)"
)
DOT_DATE_RE = re.compile(r"^(20\d{2})\.(\d{1,2})\.(\d{1,2})\s*(.+)$")
JP_DATE_LINE_RE = re.compile(r"^(20\d{2})年(\d{1,2})月(\d{1,2})日\s*(.+)$")
TOBU_LINK_RE = re.compile(r"/event/\d+\.html$")
NUMERIC_EVENT_LINK_RE = re.compile(r"/event/\d+/?$")

EVENT_KEYWORDS = [
    "イベント",
    "開催",
    "講座",
    "観察",
    "ツアー",
    "トーク",
    "ワークショップ",
    "体験",
    "企画展",
    "写真展",
    "スタンプラリー",
    "ナイト",
    "バックヤード",
    "フェス",
    "キャンペーン",
]
REPTILE_KEYWORDS = ["爬虫", "レプ", "両生", "トカゲ", "ヘビ", "カメ"]
AQUARIUM_KEYWORDS = [
    "アクア",
    "水族",
    "イルカ",
    "ペンギン",
    "海獣",
    "海洋",
    "サンゴ",
    "魚",
]

CATEGORY_ORDER = {
    "博物館": 0,
    "動物園": 1,
    "市役所（自治体）": 2,
    "民間": 3,
    "NPO": 4,
    "公園": 5,
}

FULLWIDTH_DIGITS = str.maketrans("０１２３４５６７８９", "0123456789")


@dataclass(frozen=True)
class EventItem:
    category: str
    field: str
    organizer: str
    area: str
    title: str
    date_text: str
    url: str
    source_url: str
    start_date: dt.date | None
    end_date: dt.date | None


class CollectWarning(RuntimeError):
    pass


def normalize_text(text: str) -> str:
    text = text.translate(FULLWIDTH_DIGITS)
    text = html.unescape(text)
    text = SPACE_RE.sub(" ", text.replace("\u3000", " ")).strip()
    return text


def strip_tags(text: str) -> str:
    return TAG_RE.sub(" ", text)


def fetch_html(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        content_type = resp.headers.get("Content-Type", "")
    candidates: list[str] = []
    if "charset=" in content_type:
        candidates.append(content_type.split("charset=", 1)[1].split(";")[0].strip())
    candidates.extend(["utf-8", "cp932", "euc-jp"])
    tried: set[str] = set()
    for enc in candidates:
        if not enc or enc in tried:
            continue
        tried.add(enc)
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def extract_anchors(page_html: str, base_url: str) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    for href, inner in ANCHOR_RE.findall(page_html):
        href = html.unescape(href).strip()
        if not href:
            continue
        if href.startswith("javascript:") or href.startswith("#"):
            continue
        url = urllib.parse.urljoin(base_url, href)
        text = normalize_text(strip_tags(inner))
        if not text:
            continue
        results.append((url, text))
    return results


def parse_date_range(date_text: str, today: dt.date) -> tuple[dt.date | None, dt.date | None]:
    normalized = normalize_text(date_text)
    matches = list(DATE_PART_RE.finditer(normalized))
    if not matches:
        return None, None

    parsed: list[dt.date] = []
    for match in matches:
        year_s, month_s, day_s = match.groups()
        month = int(month_s)
        day = int(day_s)
        if year_s:
            year = int(year_s)
        else:
            year = today.year
            tentative = dt.date(year, month, day)
            if tentative < today - dt.timedelta(days=180):
                year += 1
        try:
            parsed.append(dt.date(year, month, day))
        except ValueError:
            continue
    if not parsed:
        return None, None
    return min(parsed), max(parsed)


def extract_date_text(text: str) -> str:
    normalized = normalize_text(text)
    match = DATE_TEXT_RE.search(normalized)
    if not match:
        return "-"
    return normalize_text(match.group(1))


def classify_field(title: str, default_field: str = "生き物・自然") -> str:
    blob = normalize_text(title)
    if any(k in blob for k in REPTILE_KEYWORDS):
        return "爬虫類・両生類"
    if any(k in blob for k in AQUARIUM_KEYWORDS):
        return "アクアリウム・水生生物"
    return default_field


def make_event(
    *,
    category: str,
    organizer: str,
    area: str,
    title: str,
    date_text: str,
    url: str,
    source_url: str,
    today: dt.date,
    default_field: str = "生き物・自然",
) -> EventItem:
    title = normalize_text(title)
    date_text = normalize_text(date_text) if date_text else "-"
    start_date, end_date = parse_date_range(date_text, today)
    field = classify_field(title, default_field=default_field)
    return EventItem(
        category=category,
        field=field,
        organizer=organizer,
        area=area,
        title=title,
        date_text=date_text if date_text else "-",
        url=url,
        source_url=source_url,
        start_date=start_date,
        end_date=end_date,
    )


def is_event_like(text: str) -> bool:
    normalized = normalize_text(text)
    return any(k in normalized for k in EVENT_KEYWORDS)


def should_keep_event(event: EventItem, today: dt.date) -> bool:
    title = event.title
    if "終了" in title:
        return False
    if event.end_date and event.end_date < today:
        return False
    if event.date_text == "-":
        return True
    if event.end_date is None and event.start_date and event.start_date < today - dt.timedelta(days=14):
        return False
    return True


def collect_sendai_city(today: dt.date) -> list[EventItem]:
    source_url = "https://www.city.sendai.jp/zoo/event/"
    page = fetch_html(source_url)
    events: list[EventItem] = []
    seen: set[str] = set()
    for url, text in extract_anchors(page, source_url):
        if "/zoo/event/day/" not in url:
            continue
        if url in seen:
            continue
        seen.add(url)
        date_text = extract_date_text(text)
        title = text.replace(date_text, "").strip(" ・")
        if not title:
            title = text
        events.append(
            make_event(
                category="市役所（自治体）",
                organizer="仙台市 八木山動物公園フジサキの杜",
                area="宮城県仙台市",
                title=title,
                date_text=date_text,
                url=url,
                source_url=source_url,
                today=today,
                default_field="動物園・教育",
            )
        )
    return events[:20]


def collect_tobu_zoo(today: dt.date) -> list[EventItem]:
    source_url = "https://www.tobuzoo.com/event/"
    page = fetch_html(source_url)
    events: list[EventItem] = []
    seen: set[str] = set()
    for url, text in extract_anchors(page, source_url):
        parsed = urllib.parse.urlparse(url)
        if not TOBU_LINK_RE.search(parsed.path):
            continue
        if url in seen:
            continue
        seen.add(url)
        cleaned = re.sub(r"^(ピックアップ（イベント）|開催中のおすすめイベント)\s*", "", text)
        date_text = extract_date_text(cleaned)
        title = cleaned.replace(date_text, "").strip(" ・")
        if not title:
            title = cleaned
        if len(title) < 4:
            continue
        events.append(
            make_event(
                category="動物園",
                organizer="東武動物公園",
                area="埼玉県宮代町",
                title=title,
                date_text=date_text,
                url=url,
                source_url=source_url,
                today=today,
                default_field="動物園・展示",
            )
        )
    return events[:15]


def collect_kmnh_museum(today: dt.date) -> list[EventItem]:
    source_url = "https://www.kmnh.jp/event/list/event-info/"
    page = fetch_html(source_url)
    events: list[EventItem] = []
    seen: set[str] = set()
    for url, text in extract_anchors(page, source_url):
        parsed = urllib.parse.urlparse(url)
        if not NUMERIC_EVENT_LINK_RE.search(parsed.path):
            continue
        if url in seen:
            continue
        seen.add(url)
        cleaned = re.sub(r"^(申込終了|申込不要|申込受付中|受付中)\s*", "", text)
        date_text = extract_date_text(cleaned)
        title = cleaned.replace(date_text, "").strip(" ・")
        if not title:
            title = cleaned
        events.append(
            make_event(
                category="博物館",
                organizer="北九州市立いのちのたび博物館",
                area="福岡県北九州市",
                title=title,
                date_text=date_text,
                url=url,
                source_url=source_url,
                today=today,
                default_field="自然史・博物館",
            )
        )
    return events[:20]


def collect_nacsj(today: dt.date) -> list[EventItem]:
    source_url = "https://www.nacsj.or.jp/event/"
    page = fetch_html(source_url)
    events: list[EventItem] = []
    seen: set[str] = set()
    for url, text in extract_anchors(page, source_url):
        decoded_url = urllib.parse.unquote(url)
        parsed = urllib.parse.urlparse(url)
        if not NUMERIC_EVENT_LINK_RE.search(parsed.path):
            continue
        if "finish=true" in url or "終了したイベント" in decoded_url:
            continue
        if url in seen:
            continue
        seen.add(url)

        cleaned = text.replace("記事を読む", "").strip()
        cleaned = re.sub(r"^主催[:：][^ ]+\s*", "", cleaned)
        if "開催日" in cleaned:
            title = cleaned.split("開催日", 1)[0].strip()
        else:
            title = cleaned
        date_text = extract_date_text(cleaned)
        area_match = re.findall(r"（([^（）]{2,40})）", cleaned)
        area = area_match[-1] if area_match else "全国"
        events.append(
            make_event(
                category="NPO",
                organizer="日本自然保護協会（NACS-J）",
                area=area,
                title=title,
                date_text=date_text,
                url=url,
                source_url=source_url,
                today=today,
                default_field="自然保護・市民科学",
            )
        )
    return events[:25]


def _pick_best_title(candidates: Iterable[str]) -> str | None:
    cleaned: list[str] = []
    for raw in candidates:
        text = normalize_text(raw)
        if not text:
            continue
        text = re.sub(r"\[[^\]]+\]", "", text).strip()
        cleaned.append(text)
    if not cleaned:
        return None
    cleaned.sort(key=len)
    for item in cleaned:
        if 8 <= len(item) <= 90 and "…" not in item and "[…]" not in item:
            return item
    return cleaned[0]


def collect_jwcs(today: dt.date) -> list[EventItem]:
    source_url = "https://www.jwcs.org/event/"
    page = fetch_html(source_url)
    grouped: dict[str, list[str]] = {}
    for url, text in extract_anchors(page, source_url):
        decoded_url = urllib.parse.unquote(url)
        parsed = urllib.parse.urlparse(url)
        if not NUMERIC_EVENT_LINK_RE.search(parsed.path):
            continue
        if "終了したイベント" in decoded_url:
            continue
        grouped.setdefault(url, []).append(text)

    events: list[EventItem] = []
    for url, titles in grouped.items():
        title = _pick_best_title(titles)
        if not title:
            continue
        date_text = extract_date_text(title)
        events.append(
            make_event(
                category="NPO",
                organizer="野生生物保全論研究会（JWCS）",
                area="全国・オンライン",
                title=title,
                date_text=date_text,
                url=url,
                source_url=source_url,
                today=today,
                default_field="野生生物保全",
            )
        )
    return events[:15]


def collect_showa_park(today: dt.date) -> list[EventItem]:
    source_url = "https://www.showakinen-koen.jp/event/"
    page = fetch_html(source_url)
    events: list[EventItem] = []
    seen: set[str] = set()
    for block in EVENT_CARD_RE.findall(page):
        link_match = re.search(r'event-card__link"\s+href="([^"]+)"', block)
        title_match = re.search(r'event-card__name">(.*?)</div>', block, re.DOTALL)
        date_match = re.search(r'event-card__date">(.*?)</div>', block, re.DOTALL)
        if not link_match or not title_match:
            continue
        url = normalize_text(link_match.group(1))
        if url in seen:
            continue
        seen.add(url)
        title = normalize_text(strip_tags(title_match.group(1)))
        date_text = (
            normalize_text(strip_tags(date_match.group(1)))
            if date_match
            else extract_date_text(block)
        )
        if not title:
            continue
        events.append(
            make_event(
                category="公園",
                organizer="国営昭和記念公園",
                area="東京都立川市・昭島市",
                title=title,
                date_text=date_text,
                url=url,
                source_url=source_url,
                today=today,
                default_field="公園・自然観察",
            )
        )
    return events[:20]


def collect_kyoto_aquarium(today: dt.date) -> list[EventItem]:
    source_url = "https://www.kyoto-aquarium.com/news/"
    page = fetch_html(source_url)
    events: list[EventItem] = []
    seen: set[str] = set()
    for url, text in extract_anchors(page, source_url):
        parsed = urllib.parse.urlparse(url)
        if not parsed.path.startswith("/news/"):
            continue
        if "/news/page/" in parsed.path:
            continue
        if url in seen:
            continue
        match = DOT_DATE_RE.match(text)
        if not match:
            continue
        year, month, day, rest = match.groups()
        title = normalize_text(rest)
        if not is_event_like(title):
            continue
        seen.add(url)
        published = f"{year}年{int(month)}月{int(day)}日"
        event_date = extract_date_text(title)
        date_text = event_date if event_date != "-" else published
        events.append(
            make_event(
                category="民間",
                organizer="京都水族館",
                area="京都府京都市",
                title=title,
                date_text=date_text,
                url=url,
                source_url=source_url,
                today=today,
                default_field="アクアリウム・水生生物",
            )
        )
    return events[:20]


def collect_aquamarine(today: dt.date) -> list[EventItem]:
    source_url = "https://www.aquamarine.or.jp/news/"
    page = fetch_html(source_url)
    events: list[EventItem] = []
    seen: set[str] = set()
    for url, text in extract_anchors(page, source_url):
        parsed = urllib.parse.urlparse(url)
        if not parsed.path.startswith("/news/"):
            continue
        if "/news/page/" in parsed.path:
            continue
        if re.fullmatch(r"/news/20\d{2}/", parsed.path):
            continue
        if url in seen:
            continue
        match = JP_DATE_LINE_RE.match(text)
        if not match:
            continue
        year, month, day, rest = match.groups()
        title = normalize_text(rest)
        if not is_event_like(title):
            continue
        seen.add(url)
        published = f"{year}年{int(month)}月{int(day)}日"
        event_date = extract_date_text(title)
        date_text = event_date if event_date != "-" else published
        events.append(
            make_event(
                category="民間",
                organizer="アクアマリンふくしま",
                area="福島県いわき市",
                title=title,
                date_text=date_text,
                url=url,
                source_url=source_url,
                today=today,
                default_field="アクアリウム・水生生物",
            )
        )
    return events[:20]


def collect_jrs_reptile(today: dt.date) -> list[EventItem]:
    source_url = "https://www.rep-japan.co.jp/jrs/JRS2018/index.html"
    page = fetch_html(source_url)
    page = re.sub(r"<script\b[^>]*>.*?</script>", " ", page, flags=re.DOTALL | re.IGNORECASE)
    plain = normalize_text(strip_tags(page))

    match = re.search(
        r"(ジャパンレプタイルズショー20\d{2}(?:[_\s](?:Summer|Winter|SUMMER|WINTER))?(?:【[^】]+】)?)",
        plain,
    )
    if not match:
        return []
    snippet = normalize_text(match.group(1).replace("_", " "))
    date_match = re.search(r"(\d{1,2}月\d{1,2}日(?:・\d{1,2}日)?)", plain)
    date_text = date_match.group(1) if date_match else "-"
    title = snippet
    return [
        make_event(
            category="民間",
            organizer="ジャパンレプタイルズショー（レップジャパン）",
            area="静岡県静岡市",
            title=title,
            date_text=date_text,
            url=source_url,
            source_url=source_url,
            today=today,
            default_field="爬虫類・両生類",
        )
    ]


def collect_events(today: dt.date) -> tuple[list[EventItem], list[str]]:
    collectors = [
        ("博物館", collect_kmnh_museum),
        ("動物園", collect_tobu_zoo),
        ("市役所（自治体）", collect_sendai_city),
        ("民間", collect_kyoto_aquarium),
        ("民間", collect_aquamarine),
        ("民間", collect_jrs_reptile),
        ("NPO", collect_nacsj),
        ("NPO", collect_jwcs),
        ("公園", collect_showa_park),
    ]

    all_events: list[EventItem] = []
    warnings: list[str] = []
    for _, collector in collectors:
        try:
            all_events.extend(collector(today))
        except (urllib.error.URLError, urllib.error.HTTPError, CollectWarning) as exc:
            warnings.append(f"{collector.__name__}: {exc}")

    filtered = [ev for ev in all_events if should_keep_event(ev, today)]
    dedup: dict[tuple[str, str, str], EventItem] = {}
    for ev in filtered:
        key = (ev.category, ev.title, ev.url)
        if key not in dedup:
            dedup[key] = ev
    events = list(dedup.values())
    events.sort(
        key=lambda ev: (
            CATEGORY_ORDER.get(ev.category, 99),
            ev.start_date or dt.date.max,
            ev.title,
        )
    )
    return events, warnings


def md_escape(text: str) -> str:
    return normalize_text(text).replace("|", r"\|")


def domain_label(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host or url


def render_table(events: list[EventItem]) -> str:
    lines = [
        "| 区分 | 分野 | 主催 | 地域 | イベント名 | 開催日 | 情報源 |",
        "|------|------|------|------|------------|--------|--------|",
    ]
    for ev in events:
        title = f"[{md_escape(ev.title)}]({ev.url})"
        source = f"[{domain_label(ev.source_url)}]({ev.source_url})"
        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(ev.category),
                    md_escape(ev.field),
                    md_escape(ev.organizer),
                    md_escape(ev.area),
                    title,
                    md_escape(ev.date_text if ev.date_text else "-"),
                    source,
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def render_source_summary(events: list[EventItem], warnings: list[str], generated_at: dt.datetime) -> str:
    counts: dict[str, int] = {}
    for ev in events:
        counts[ev.category] = counts.get(ev.category, 0) + 1

    lines = [
        f"- 更新日時: {generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 掲載件数: {len(events)}件",
        "- 区分内訳: "
        + " / ".join(
            f"{cat}:{counts.get(cat, 0)}"
            for cat in ["博物館", "動物園", "市役所（自治体）", "民間", "NPO", "公園"]
        ),
    ]
    if warnings:
        lines.append("- 取得警告:")
        lines.extend([f"  - {w}" for w in warnings])
    return "\n".join(lines)


def render_main_block(events: list[EventItem], warnings: list[str], generated_at: dt.datetime) -> str:
    if not events:
        return "_現在、取得できるイベント情報がありませんでした。_"
    return "\n".join(
        [
            "### 最新イベント一覧",
            "",
            render_table(events),
            "",
            "### 取得状況",
            "",
            render_source_summary(events, warnings, generated_at),
        ]
    )


def render_special_block(events: list[EventItem]) -> str:
    special = [ev for ev in events if ev.field in {"爬虫類・両生類", "アクアリウム・水生生物"}]
    special.sort(
        key=lambda ev: (
            ev.start_date or dt.date.max,
            CATEGORY_ORDER.get(ev.category, 99),
            ev.title,
        )
    )
    if not special:
        return "_現在、該当イベントは取得できませんでした。_"
    lines = [
        "| 分野 | 区分 | 主催 | イベント名 | 開催日 | 情報源 |",
        "|------|------|------|------------|--------|--------|",
    ]
    for ev in special:
        title = f"[{md_escape(ev.title)}]({ev.url})"
        source = f"[{domain_label(ev.source_url)}]({ev.source_url})"
        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(ev.field),
                    md_escape(ev.category),
                    md_escape(ev.organizer),
                    title,
                    md_escape(ev.date_text if ev.date_text else "-"),
                    source,
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def replace_block(text: str, start_marker: str, end_marker: str, body: str) -> str:
    pattern = re.compile(
        rf"{re.escape(start_marker)}.*?{re.escape(end_marker)}",
        flags=re.DOTALL,
    )
    replacement = f"{start_marker}\n{body.rstrip()}\n{end_marker}"
    if not pattern.search(text):
        raise ValueError(f"marker not found: {start_marker} ... {end_marker}")
    return pattern.sub(replacement, text, count=1)


def update_frontmatter_updated(text: str, today: dt.date) -> str:
    updated_line = f"updated: {today.isoformat()}"
    if re.search(r"^updated:\s*\d{4}-\d{2}-\d{2}\s*$", text, flags=re.MULTILINE):
        return re.sub(
            r"^updated:\s*\d{4}-\d{2}-\d{2}\s*$",
            updated_line,
            text,
            count=1,
            flags=re.MULTILINE,
        )
    return text


def update_board_file(
    path: Path,
    main_block: str,
    special_block: str,
    today: dt.date,
    dry_run: bool,
) -> None:
    original = path.read_text(encoding="utf-8")
    updated = replace_block(original, MAIN_START, MAIN_END, main_block)
    updated = replace_block(updated, SPECIAL_START, SPECIAL_END, special_block)
    updated = update_frontmatter_updated(updated, today)
    if dry_run:
        return
    path.write_text(updated, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update 生き物イベント掲示板 automatically from official event pages.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory",
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not write files")
    parser.add_argument("--print", action="store_true", dest="print_output", help="Print generated markdown blocks")
    args = parser.parse_args()

    root = args.root.resolve()
    today = dt.date.today()
    now = dt.datetime.now()

    events, warnings = collect_events(today)
    main_block = render_main_block(events, warnings, now)
    special_block = render_special_block(events)

    targets = [root / rel for rel in TARGET_FILES]
    missing = [p for p in targets if not p.exists()]
    if missing:
        names = ", ".join(str(p) for p in missing)
        raise FileNotFoundError(f"Target board files not found: {names}")

    for target in targets:
        update_board_file(
            target,
            main_block=main_block,
            special_block=special_block,
            today=today,
            dry_run=args.dry_run,
        )
        print(f"UPDATED: {target.relative_to(root)}")

    print(f"EVENT_COUNT={len(events)}")
    if warnings:
        print(f"WARNINGS={len(warnings)}")
        for warning in warnings:
            print(f"WARNING: {warning}")

    if args.print_output:
        print("\n--- MAIN BLOCK ---\n")
        print(main_block)
        print("\n--- SPECIAL BLOCK ---\n")
        print(special_block)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
