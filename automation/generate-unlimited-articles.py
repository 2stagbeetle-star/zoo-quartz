#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path

FOCUS_TOPICS = [
    "データ標準化",
    "リスク評価",
    "教育設計",
    "季節対応",
    "来園者対応",
    "感染症対策",
    "設備保全",
    "法令遵守",
    "地域連携",
    "研究連携",
    "指標設計",
    "予算計画",
    "記録監査",
    "人材育成",
    "緊急時対応",
    "広報連携",
    "品質改善",
    "点検手順",
    "レビュー運用",
    "次年度計画",
]

EXCLUDED_PARTS = {".git", ".obsidian", ".claude", ".codex", ".agent", "node_modules"}
TITLE_RE = re.compile(r'^title:\s*"(.*?)"\s*$', re.MULTILINE)


def sanitize_filename(name: str) -> str:
    text = re.sub(r'[<>:"/\\|?*]', "_", name)
    text = re.sub(r"\s+", "_", text).strip("._")
    return text[:120] or "untitled"


def category_dirs(content_root: Path) -> list[Path]:
    return sorted(p for p in content_root.iterdir() if p.is_dir() and re.match(r"^\d{2}_", p.name))


def category_name(dir_name: str) -> str:
    return re.sub(r"^\d{2}_", "", dir_name)


def compose_title(cat_name: str, focus: str, round_no: int) -> str:
    return f"【不足補完R{round_no:02d}】{cat_name}における{focus}の実装ノート"


def existing_titles(content_root: Path) -> set[str]:
    titles: set[str] = set()
    for md in content_root.rglob("*.md"):
        if any(part in EXCLUDED_PARTS for part in md.parts):
            continue
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        m = TITLE_RE.search(text)
        if m:
            titles.add(m.group(1).strip())
    return titles


def build_article(
    *,
    title: str,
    category_tag: str,
    focus_tag: str,
    date_iso: str,
    category_path: str,
    draft: bool,
) -> str:
    return f"""---
title: "{title}"
date: {date_iso}
updated: {date_iso}
tags:
  - {category_tag}
  - {focus_tag}
  - 不足項目補完
author: "Zoo Knowledge Vault"
draft: {"true" if draft else "false"}
---

# {title}

## 概要
本記事は `{category_tag}` カテゴリにおける `{focus_tag}` の不足項目を補完するために作成した実装ノートです。  
現場で運用しやすい構成を意識し、課題整理・対応手順・次アクションを短時間で確認できる形式にしています。

## 現状課題
- 情報の粒度や記録形式が揃っておらず、比較・集計がしづらい
- 担当者依存の判断が残り、再現性が低い
- 振り返りのための定量指標が不足している

## 実装方針
1. 運用単位（週次・月次・イベント単位）を定義する
2. 必須記録項目と任意記録項目を分離する
3. 判断基準をチェックリスト化して担当者間で共有する
4. 1か月ごとにレビューし、運用SOPに反映する

## 具体施策
- 入力テンプレートを統一し、記録漏れを防止する
- KPI（例: 実施率、完了率、異常検知件数）を最小セットで運用する
- 関連カテゴリ間のリンクを整備し、参照導線を短縮する

## 次アクション
- 一次版テンプレートを運用に投入（2週間）
- KPIの閾値を仮設定し、月次で見直し
- 関連記事の相互リンクを追加し、検索性を改善

## 関連リンク
- [[{category_path}]]
- [[00_Index/index]]
- [[00_Index/運用ガイド]]
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate draft articles in large batches.")
    parser.add_argument("--content-root", type=Path, default=Path.cwd())
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--batch-id", type=str, default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--publish", action="store_true", help="Generate with draft: false")
    args = parser.parse_args()

    content_root = args.content_root.resolve()
    categories = category_dirs(content_root)
    if not categories:
        print("NO_CATEGORY_DIRS")
        return 1

    today = dt.date.today().isoformat()
    batch_stamp = args.batch_id.strip() or dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    titles = existing_titles(content_root)

    pool: list[tuple[str, str, str, str]] = []
    for cat in categories:
        cat_name = category_name(cat.name)
        for focus in FOCUS_TOPICS:
            round_no = 1
            while True:
                title = compose_title(cat_name, focus, round_no)
                if title not in titles:
                    break
                round_no += 1
            slug = sanitize_filename(f"{focus}_R{round_no:02d}")
            pool.append((cat.name, title, focus, slug))

    selected = pool[args.offset : args.offset + args.batch_size]
    print(f"CANDIDATES={len(pool)}")
    print(f"SELECTED={len(selected)} OFFSET={args.offset} BATCH={args.batch_size}")

    created = 0
    skipped = 0

    for idx, (cat_dir_name, title, focus, slug) in enumerate(selected, start=1):
        cat_dir = content_root / cat_dir_name
        out_dir = cat_dir / "不足項目補完" / f"バッチ_{batch_stamp}"
        out_path = out_dir / f"N_{idx + args.offset:04d}_{slug}.md"

        if args.dry_run:
            rel = out_path.relative_to(content_root).as_posix()
            print(f"DRYRUN {idx:03d} {rel} :: {title}")
            continue

        if out_path.exists():
            skipped += 1
            print(f"SKIP   {idx:03d} exists {out_path.relative_to(content_root).as_posix()}")
            continue

        out_dir.mkdir(parents=True, exist_ok=True)
        body = build_article(
            title=title,
            category_tag=category_name(cat_dir_name),
            focus_tag=focus,
            date_iso=today,
            category_path=cat_dir_name,
            draft=not args.publish,
        )
        out_path.write_text(body, encoding="utf-8", newline="\n")
        created += 1
        print(f"WRITE  {idx:03d} {out_path.relative_to(content_root).as_posix()}")

    print(f"CREATED={created}")
    print(f"SKIPPED_EXISTING={skipped}")
    print(f"REMAINING_AFTER_BATCH={max(len(pool) - (args.offset + len(selected)), 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
