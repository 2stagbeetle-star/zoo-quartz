#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import urllib.parse
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

WIKI_IMAGE_RE = re.compile(r"!\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
INFO_HEADING_RE = re.compile(r"^##+\s*インフォグラフィック", re.MULTILINE)
DRAFT_RE = re.compile(r"^draft:\s*(true|false)\s*$", re.MULTILINE | re.IGNORECASE)
HTML_IMG_RE = re.compile(r"<img[^>]+src=[\"']([^\"']+)[\"']", re.IGNORECASE)
IMAGE_EXTS = {".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif"}


@dataclass
class RefStatus:
    ok: bool
    state: str
    target: str | None


def iter_articles(content_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in content_root.rglob("*.md"):
        if any(part.startswith(".") for part in path.parts):
            continue
        if "_images" in path.parts:
            continue
        if path.name.lower() == "index.md":
            continue
        files.append(path)
    return sorted(files)


def parse_draft_flag(text: str) -> bool:
    if not text.startswith("---\n"):
        return False
    end = text.find("\n---", 4)
    if end == -1:
        return False
    fm = text[4:end]
    m = DRAFT_RE.search(fm)
    if not m:
        return False
    return m.group(1).lower() == "true"


def extract_image_refs(text: str) -> list[str]:
    refs: list[str] = []
    refs.extend(WIKI_IMAGE_RE.findall(text))
    refs.extend(MD_IMAGE_RE.findall(text))
    out: list[str] = []
    for ref in refs:
        r = ref.strip()
        if not r:
            continue
        r = r.split("?")[0].split("#")[0]
        if r:
            out.append(r)
    return out


def build_asset_index(content_root: Path) -> dict[str, list[Path]]:
    idx: dict[str, list[Path]] = defaultdict(list)
    for p in content_root.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            idx[p.name].append(p)
    return idx


def resolve_ref(md_path: Path, ref: str, content_root: Path, asset_index: dict[str, list[Path]]) -> RefStatus:
    lowered = ref.lower()
    if lowered.startswith("http://") or lowered.startswith("https://") or lowered.startswith("data:"):
        return RefStatus(ok=True, state="external", target=ref)

    candidate = (md_path.parent / ref)
    if candidate.exists():
        return RefStatus(ok=True, state="direct", target=str(candidate))

    if ref.startswith("/"):
        rooted = content_root / ref.lstrip("/")
        if rooted.exists():
            return RefStatus(ok=True, state="rooted", target=str(rooted))

    # Only plain wikilinks (no path separators) can be resolved by basename.
    # Path-qualified refs must exist at the exact target path.
    name = Path(ref).name
    if "/" not in ref and "\\" not in ref and name in asset_index:
        paths = asset_index[name]
        if len(paths) == 1:
            return RefStatus(ok=True, state="basename", target=str(paths[0]))
        return RefStatus(ok=True, state="ambiguous", target=str(paths[0]))

    return RefStatus(ok=False, state="missing", target=None)


def local_basename(ref: str) -> str | None:
    lowered = ref.lower()
    if lowered.startswith("http://") or lowered.startswith("https://") or lowered.startswith("data:"):
        return None
    return Path(ref).name


def audit_source(content_root: Path) -> dict:
    assets = build_asset_index(content_root)
    articles = iter_articles(content_root)

    stats_all = Counter()
    stats_pub = Counter()
    broken_examples: list[dict] = []
    ambiguous_examples: list[dict] = []
    expected_pub_basenames: set[str] = set()

    for md in articles:
        text = md.read_text(encoding="utf-8", errors="ignore")
        is_draft = parse_draft_flag(text)
        refs = extract_image_refs(text)
        has_info_heading = bool(INFO_HEADING_RE.search(text))

        info_refs = [r for r in refs if "infographic" in r.lower() or "インフォグラフィック" in r]
        if has_info_heading and not info_refs:
            info_refs = refs

        buckets = [stats_all]
        if not is_draft:
            buckets.append(stats_pub)

        for b in buckets:
            b["articles"] += 1
            if is_draft:
                b["draft_articles"] += 1
            else:
                b["published_articles"] += 1

            if not info_refs:
                b["articles_without_infographic_ref"] += 1
                continue

            b["articles_with_infographic_ref"] += 1

        if not info_refs:
            continue

        states = []
        for ref in info_refs:
            status = resolve_ref(md, ref, content_root, assets)
            states.append((ref, status))

            if not is_draft and status.ok:
                bn = local_basename(ref)
                if bn:
                    expected_pub_basenames.add(bn)

        has_ok = any(s.ok for _, s in states)
        has_missing = any((not s.ok) for _, s in states)
        has_ambiguous = any(s.state == "ambiguous" for _, s in states)

        for b in buckets:
            if has_ok:
                b["articles_with_visible_infographic_ref"] += 1
            if has_missing:
                b["articles_with_missing_infographic_ref"] += 1
            if has_ambiguous:
                b["articles_with_ambiguous_infographic_ref"] += 1

        if has_missing and len(broken_examples) < 50:
            broken_examples.append(
                {
                    "article": str(md.relative_to(content_root)).replace("\\", "/"),
                    "missing_refs": [r for r, s in states if not s.ok],
                }
            )

        if has_ambiguous and len(ambiguous_examples) < 50:
            ambiguous_examples.append(
                {
                    "article": str(md.relative_to(content_root)).replace("\\", "/"),
                    "ambiguous_refs": [r for r, s in states if s.state == "ambiguous"],
                }
            )

    return {
        "all": dict(stats_all),
        "published": dict(stats_pub),
        "broken_examples": broken_examples,
        "ambiguous_examples": ambiguous_examples,
        "expected_published_infographic_basenames": sorted(expected_pub_basenames),
    }


def audit_build(public_root: Path) -> dict:
    stats = Counter()
    broken_refs: list[dict] = []
    public_infographic_basenames: set[str] = set()

    for p in public_root.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS and "infographic" in p.name.lower():
            public_infographic_basenames.add(p.name)

    html_files = sorted(public_root.rglob("*.html"))
    stats["html_files"] = len(html_files)
    stats["public_infographic_assets"] = len(public_infographic_basenames)

    for html_path in html_files:
        try:
            text = html_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        refs = HTML_IMG_RE.findall(text)
        info_refs = [r for r in refs if "infographic" in urllib.parse.unquote(r).lower()]
        if not info_refs:
            continue

        stats["html_with_infographic_img"] += 1
        page_has_broken = False

        for ref in info_refs:
            stats["infographic_img_refs"] += 1
            raw = urllib.parse.unquote(ref).split("?")[0].split("#")[0]
            if raw.startswith("http://") or raw.startswith("https://") or raw.startswith("data:"):
                stats["external_infographic_refs"] += 1
                continue

            target = (public_root / raw.lstrip("/")) if raw.startswith("/") else (html_path.parent / raw)
            normalized_target = target.resolve(strict=False)
            if normalized_target.exists():
                stats["resolved_infographic_img_refs"] += 1
            else:
                stats["broken_infographic_img_refs"] += 1
                page_has_broken = True
                if len(broken_refs) < 100:
                    broken_refs.append(
                        {
                            "html": str(html_path.relative_to(public_root)).replace("\\", "/"),
                            "src": ref,
                        }
                    )

        if page_has_broken:
            stats["html_with_broken_infographic_img"] += 1

    return {
        "stats": dict(stats),
        "broken_refs": broken_refs,
        "public_infographic_basenames": sorted(public_infographic_basenames),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Deep audit for infographic visibility in source and built site")
    parser.add_argument("--content-root", type=Path, default=Path("zoo-quartzg56/content"))
    parser.add_argument("--public-root", type=Path, default=Path("zoo-quartzg56/public"))
    parser.add_argument("--json-out", type=Path, default=Path("zoo-quartzg56/docs/infographic-audit-report.json"))
    args = parser.parse_args()

    content_root = args.content_root.resolve()
    public_root = args.public_root.resolve()

    source = audit_source(content_root)
    build = audit_build(public_root)

    expected_pub = set(source["expected_published_infographic_basenames"])
    public_assets = set(build["public_infographic_basenames"])
    missing_in_public = sorted(expected_pub - public_assets)

    report = {
        "content_root": str(content_root),
        "public_root": str(public_root),
        "source": source,
        "build": {
            "stats": build["stats"],
            "broken_refs": build["broken_refs"],
            "missing_expected_published_asset_basenames": missing_in_public,
        },
    }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"REPORT={args.json_out}")
    print("SOURCE_ALL", json.dumps(source["all"], ensure_ascii=False, sort_keys=True))
    print("SOURCE_PUBLISHED", json.dumps(source["published"], ensure_ascii=False, sort_keys=True))
    print("BUILD", json.dumps(build["stats"], ensure_ascii=False, sort_keys=True))
    print(f"MISSING_EXPECTED_PUBLISHED_ASSETS={len(missing_in_public)}")
    print(f"BROKEN_SOURCE_EXAMPLES={len(source['broken_examples'])}")
    print(f"AMBIGUOUS_SOURCE_EXAMPLES={len(source['ambiguous_examples'])}")
    print(f"BROKEN_BUILD_REFS={len(build['broken_refs'])}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
