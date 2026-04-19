#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
from collections import Counter, defaultdict
from pathlib import Path

EXCLUDED_DIRS = {
    ".git",
    ".obsidian",
    ".claude",
    ".codex",
    ".agent",
    "_templates",
    "_drafts",
    "zoo-quartzg56",
    "automation",
    "plans",
}

NON_ARTICLE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".bmp",
    ".tiff",
    ".pdf",
    ".mp4",
    ".mp3",
    ".wav",
    ".csv",
    ".json",
    ".yaml",
    ".yml",
    ".zip",
}

WIKILINK_RE = re.compile(r"!?\[\[([^\]]+)\]\]")
CATEGORY_RE = re.compile(r"^\d+_(.+)$")


def iter_markdown_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.md"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def normalize_wikilink_target(raw: str) -> str:
    target = raw.split("|", 1)[0].split("#", 1)[0].strip()
    return target


def has_non_article_extension(target: str) -> bool:
    suffix = Path(target).suffix.lower()
    if not suffix:
        return False
    if suffix == ".md":
        return False
    if suffix in NON_ARTICLE_EXTENSIONS:
        return True
    return True


def build_stem_index(root: Path, files: list[Path]) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = defaultdict(list)
    for path in files:
        rel = path.relative_to(root)
        index[path.stem].append(rel)
        if path.stem.lower() == "index":
            index[path.parent.name].append(rel)
    return index


def link_exists(root: Path, target: str, stem_index: dict[str, list[Path]]) -> bool:
    if "/" in target:
        if (root / f"{target}.md").exists():
            return True
        if (root / target / "index.md").exists():
            return True
        return False
    return target in stem_index


def sanitize_filename(name: str) -> str:
    sanitized = re.sub(r"[<>:\"/\\|?*]", "_", name).strip()
    sanitized = re.sub(r"\s+", " ", sanitized)
    if not sanitized:
        return "untitled"
    return sanitized[:120]


def category_name_from_top(top: str) -> str:
    match = CATEGORY_RE.match(top)
    if match:
        return match.group(1)
    return "メンテナンス"


def resolve_output_path(root: Path, target: str, first_source: Path) -> tuple[Path, str]:
    if "/" in target:
        normalized = target.strip()
        if normalized.endswith("/"):
            out = root / normalized / "index.md"
        elif Path(normalized).suffix.lower() == ".md":
            out = root / normalized
        else:
            out = root / f"{normalized}.md"
        top = target.split("/", 1)[0]
        if not CATEGORY_RE.match(top):
            top = first_source.parts[0] if first_source.parts else "00_Index"
        return out, top

    top = first_source.parts[0] if first_source.parts else "00_Index"
    if not CATEGORY_RE.match(top):
        top = "00_Index"
    out_dir = root / top / "不足項目補完"
    out = out_dir / f"{sanitize_filename(target)}.md"
    return out, top


def build_article(
    target: str,
    top_category: str,
    today: dt.date,
    source_paths: list[Path],
) -> str:
    tag = category_name_from_top(top_category)
    title = target.replace('"', "'")

    refs = []
    for src in source_paths[:8]:
        refs.append(f"- `[{src.as_posix()}]` で `[[{target}]]` の参照を確認。")
    refs_block = "\n".join(refs) if refs else "- 参照元は未検出（再スキャン時に補完予定）。"

    related_links = ["[[00_Index/運用ガイド]]", "[[00_Index/リンクチェックレポート]]"]
    for src in source_paths[:4]:
        related_links.append(f"[[{src.with_suffix('').as_posix()}]]")
    dedup_related = []
    for link in related_links:
        if link not in dedup_related:
            dedup_related.append(link)
    related_block = "\n".join(f"- {link}" for link in dedup_related[:6])

    return f"""---
title: "{title}"
date: {today.isoformat()}
updated: {today.isoformat()}
tags:
  - {tag}
author: "Zoo Knowledge Vault"
draft: true
---

# {title}

## 概要

`[[{target}]]` は既存記事から参照されていますが、独立記事が未作成だったため作成した補完ページです。  
このページはリンク切れの解消と、後続の一次資料調査を進めるための基点を兼ねています。

## 現時点で確認できること

- 現段階では Vault 内参照の存在確認を優先し、未確認情報の断定記述は行っていません。
- 参照頻度と参照元カテゴリを確認し、読者導線が切れない最低限の説明構造を先に整備しています。
- 本ページは `draft: true` の下書きとして扱い、一次資料の裏取り後に本文を増補して公開判定に進めます。

## 実務上のポイント

1. 先にリンク先を用意することで、関連記事の回遊導線と索引整合性を即時回復できます。  
2. 参照元を明示しておくことで、次回更新時に「何を優先して調査すべきか」をすぐ判断できます。  
3. 速報的な記述を避け、事実確認済みの情報のみを追記する運用に統一することで、品質ブレを抑制できます。  

## 今後の更新計画

- 一次資料（公式発表・学術論文・自治体資料など）を最低3件収集し、本文へ反映する。
- 背景、現場示唆、関連論点を段階的に追記し、公開前品質基準（1500字以上）へ引き上げる。
- 必要に応じてカテゴリ内の連載記事へ統合し、重複記述を解消する。

## 参照元

{refs_block}
- 公式一次資料: 次回更新時に追加（未確認情報は現時点で未記載）。

## 関連記事

{related_block}
"""


def collect_missing_targets(root: Path) -> tuple[Counter, dict[str, list[Path]]]:
    files = iter_markdown_files(root)
    stem_index = build_stem_index(root, files)

    missing_counter: Counter = Counter()
    missing_sources: dict[str, list[Path]] = defaultdict(list)

    for source in files:
        try:
            text = source.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in WIKILINK_RE.finditer(text):
            target = normalize_wikilink_target(match.group(1))
            if not target:
                continue
            if target.lower().startswith(("http://", "https://", "mailto:")):
                continue
            if target.startswith(("_drafts/", ".claude/", ".codex/", ".obsidian/", ".git/")):
                continue
            if has_non_article_extension(target):
                continue
            if link_exists(root, target, stem_index):
                continue
            missing_counter[target] += 1
            rel = source.relative_to(root)
            if rel not in missing_sources[target]:
                missing_sources[target].append(rel)

    return missing_counter, missing_sources


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate draft markdown articles for missing wikilink targets.",
    )
    parser.add_argument("--batch-size", type=int, default=300, help="Number of targets per run.")
    parser.add_argument("--offset", type=int, default=0, help="Start offset in sorted missing targets.")
    parser.add_argument("--dry-run", action="store_true", help="Show targets without writing files.")
    args = parser.parse_args()

    root = Path.cwd()
    missing_counter, missing_sources = collect_missing_targets(root)
    ordered = sorted(missing_counter.items(), key=lambda kv: (-kv[1], kv[0]))

    selected = ordered[args.offset : args.offset + args.batch_size]
    today = dt.date.today()

    created = 0
    skipped = 0
    examined = len(selected)

    print(f"MISSING_UNIQUE={len(ordered)}")
    print(f"SELECTED={examined} OFFSET={args.offset} BATCH={args.batch_size}")

    for idx, (target, count) in enumerate(selected, start=1):
        sources = missing_sources.get(target, [])
        first_source = sources[0] if sources else Path("00_Index/index.md")
        output_path, top_category = resolve_output_path(root, target, first_source)

        if args.dry_run:
            print(f"DRYRUN {idx:03d} refs={count} target={target} -> {output_path.relative_to(root).as_posix()}")
            continue

        if output_path.exists():
            skipped += 1
            print(f"SKIP   {idx:03d} exists {output_path.relative_to(root).as_posix()}")
            continue

        output_path.parent.mkdir(parents=True, exist_ok=True)
        article = build_article(target, top_category, today, sources)
        output_path.write_text(article, encoding="utf-8", newline="\n")
        created += 1
        print(f"WRITE  {idx:03d} refs={count} {output_path.relative_to(root).as_posix()}")

    print(f"CREATED={created}")
    print(f"SKIPPED_EXISTING={skipped}")
    print(f"REMAINING_AFTER_BATCH={max(len(ordered) - (args.offset + examined), 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
