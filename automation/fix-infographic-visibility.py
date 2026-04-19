#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
from collections import defaultdict
from pathlib import Path

WIKI_IMAGE_RE = re.compile(r"!\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
INFO_HEADING_RE = re.compile(r"^##+\s*インフォグラフィック", re.MULTILINE)
TITLE_RE = re.compile(r'^title:\s*"?(.*?)"?\s*$', re.MULTILINE)
H2_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
IMAGE_EXTS = {".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif"}


def iter_articles(content_root: Path) -> list[Path]:
    items: list[Path] = []
    for path in content_root.rglob("*.md"):
        if any(part.startswith(".") for part in path.parts):
            continue
        if "_images" in path.parts:
            continue
        if path.name.lower() == "index.md":
            continue
        items.append(path)
    return sorted(items)


def build_asset_index(content_root: Path) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = defaultdict(list)
    for path in content_root.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTS:
            index[path.name].append(path)
    return index


def extract_image_refs(text: str) -> list[str]:
    refs = WIKI_IMAGE_RE.findall(text)
    refs.extend(MD_IMAGE_RE.findall(text))
    cleaned: list[str] = []
    for ref in refs:
        value = ref.strip().split("?")[0].split("#")[0]
        if value:
            cleaned.append(value)
    return cleaned


def resolve_ref(md_path: Path, ref: str, content_root: Path, asset_index: dict[str, list[Path]]) -> bool:
    lowered = ref.lower()
    if lowered.startswith("http://") or lowered.startswith("https://") or lowered.startswith("data:"):
        return True

    direct = (md_path.parent / ref)
    if direct.exists():
        return True

    if ref.startswith("/"):
        rooted = content_root / ref.lstrip("/")
        if rooted.exists():
            return True

    # Only plain wikilinks (no path separators) can be resolved by basename.
    # Path-qualified refs like "research/foo.png" must exist at that exact path.
    if "/" not in ref and "\\" not in ref and Path(ref).name in asset_index:
        return True

    return False


def pick_title(md_path: Path, text: str) -> str:
    found = TITLE_RE.search(text)
    if found and found.group(1).strip():
        return found.group(1).strip()

    for line in text.splitlines():
        if line.startswith("# "):
            value = line[2:].strip()
            if value:
                return value

    return md_path.stem


def pick_key_points(text: str) -> list[str]:
    points: list[str] = []
    for h2 in H2_RE.findall(text):
        clean = h2.strip()
        if clean and "インフォグラフィック" not in clean:
            points.append(clean)
        if len(points) == 3:
            break

    defaults = ["概要", "実装ポイント", "次アクション"]
    while len(points) < 3:
        points.append(defaults[len(points)])
    return points


def to_lines(text: str, max_chars: int = 22, max_lines: int = 2) -> list[str]:
    stripped = re.sub(r"\s+", " ", text).strip()
    if not stripped:
        return [""]

    lines: list[str] = []
    chunk = ""
    for ch in stripped:
        chunk += ch
        if len(chunk) >= max_chars:
            lines.append(chunk)
            chunk = ""
        if len(lines) >= max_lines:
            break

    if chunk and len(lines) < max_lines:
        lines.append(chunk)

    if len(lines) > max_lines:
        lines = lines[:max_lines]
    if len(lines) == max_lines and len(stripped) > max_chars * max_lines:
        lines[-1] = lines[-1][:-1] + "…"

    return lines


def render_svg(title: str, points: list[str]) -> str:
    title_lines = to_lines(title, max_chars=34, max_lines=2)
    point_lines = [to_lines(p, max_chars=20, max_lines=2) for p in points]

    def text_block(x: int, y: int, lines: list[str], size: int = 32, weight: int = 700) -> str:
        out: list[str] = []
        for i, line in enumerate(lines):
            yy = y + i * int(size * 1.25)
            out.append(
                f"<text x='{x}' y='{yy}' font-size='{size}' font-weight='{weight}' fill='#000000' "
                "font-family='\"Noto Sans JP\", \"Yu Gothic\", sans-serif'>"
                f"{html.escape(line)}</text>"
            )
        return "\n".join(out)

    svg = [
        "<svg xmlns='http://www.w3.org/2000/svg' width='1400' height='900' viewBox='0 0 1400 900'>",
        "<rect width='1400' height='900' fill='#ffffff'/>",
        "<rect x='36' y='36' width='1328' height='828' rx='24' fill='#ffffff' stroke='#000000' stroke-width='4'/>",
        "<text x='72' y='120' font-size='34' font-weight='700' fill='#000000' font-family='\"Noto Sans JP\", \"Yu Gothic\", sans-serif'>インフォグラフィック（自動修正版）</text>",
        text_block(72, 174, title_lines, size=30, weight=600),
        "<line x1='72' y1='236' x2='1328' y2='236' stroke='#000000' stroke-width='3'/>",
        "<rect x='88' y='286' width='372' height='470' rx='18' fill='#f7f7f7' stroke='#000000' stroke-width='3' />",
        "<rect x='514' y='286' width='372' height='470' rx='18' fill='#f7f7f7' stroke='#000000' stroke-width='3' />",
        "<rect x='940' y='286' width='372' height='470' rx='18' fill='#f7f7f7' stroke='#000000' stroke-width='3' />",
        "<text x='210' y='346' font-size='26' font-weight='700' fill='#000000' font-family='\"Noto Sans JP\", \"Yu Gothic\", sans-serif'>要点 1</text>",
        "<text x='636' y='346' font-size='26' font-weight='700' fill='#000000' font-family='\"Noto Sans JP\", \"Yu Gothic\", sans-serif'>要点 2</text>",
        "<text x='1062' y='346' font-size='26' font-weight='700' fill='#000000' font-family='\"Noto Sans JP\", \"Yu Gothic\", sans-serif'>要点 3</text>",
        text_block(122, 404, point_lines[0], size=30, weight=600),
        text_block(548, 404, point_lines[1], size=30, weight=600),
        text_block(974, 404, point_lines[2], size=30, weight=600),
        "<line x1='460' y1='520' x2='514' y2='520' stroke='#000000' stroke-width='4'/>",
        "<polygon points='514,520 496,510 496,530' fill='#000000'/>",
        "<line x1='886' y1='520' x2='940' y2='520' stroke='#000000' stroke-width='4'/>",
        "<polygon points='940,520 922,510 922,530' fill='#000000'/>",
        "<text x='72' y='824' font-size='22' fill='#000000' font-family='\"Noto Sans JP\", \"Yu Gothic\", sans-serif'>注: 元の図版が見えないため、可読性重視の黒文字図版を自動生成しています。</text>",
        "</svg>",
    ]
    return "\n".join(svg) + "\n"


def add_or_update_infographic_section(text: str, embed_line: str) -> tuple[str, bool]:
    if embed_line in text:
        return text, False

    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if INFO_HEADING_RE.match(line):
            insert_at = idx + 1
            lines[insert_at:insert_at] = ["", embed_line, ""]
            out = "\n".join(lines)
            if text.endswith("\n"):
                out += "\n"
            return out, True

    out = text
    if not out.endswith("\n"):
        out += "\n"
    out += "\n## インフォグラフィック\n\n"
    out += embed_line + "\n"
    return out, True


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit and repair infographic visibility for markdown articles.")
    parser.add_argument("--content-root", type=Path, default=Path("zoo-quartzg56/content"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    content_root = args.content_root.resolve()
    asset_index = build_asset_index(content_root)
    articles = iter_articles(content_root)

    total = 0
    already_visible = 0
    needs_fix = 0
    markdown_updated = 0
    svg_created = 0

    for md_path in articles:
        total += 1
        text = md_path.read_text(encoding="utf-8", errors="ignore")
        has_heading = bool(INFO_HEADING_RE.search(text))

        refs = extract_image_refs(text)
        info_refs = [r for r in refs if "infographic" in r.lower() or "インフォグラフィック" in r]
        if has_heading and not info_refs:
            info_refs = refs

        visible = False
        for ref in info_refs:
            if resolve_ref(md_path, ref, content_root, asset_index):
                visible = True
                break

        if visible:
            already_visible += 1
            continue

        needs_fix += 1
        title = pick_title(md_path, text)
        points = pick_key_points(text)

        svg_name = f"{md_path.stem}__infographic_autofix.svg"
        svg_path = md_path.with_name(svg_name)
        svg_content = render_svg(title, points)

        if not args.dry_run:
            if not svg_path.exists() or svg_path.read_text(encoding="utf-8", errors="ignore") != svg_content:
                svg_path.write_text(svg_content, encoding="utf-8")
                svg_created += 1

        embed = f"![[{svg_name}]]"
        new_text, changed = add_or_update_infographic_section(text, embed)
        if changed:
            if not args.dry_run:
                md_path.write_text(new_text, encoding="utf-8")
            markdown_updated += 1

    print(f"TOTAL={total}")
    print(f"ALREADY_VISIBLE={already_visible}")
    print(f"NEEDS_FIX={needs_fix}")
    print(f"MARKDOWN_UPDATED={markdown_updated}")
    print(f"SVG_CREATED={svg_created}")
    print(f"DRY_RUN={'true' if args.dry_run else 'false'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
