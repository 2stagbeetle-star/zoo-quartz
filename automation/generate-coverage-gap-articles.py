#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
from collections import defaultdict
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


def sanitize_filename(name: str) -> str:
    text = re.sub(r"[<>:\"/\\|?*]", "_", name)
    text = re.sub(r"\s+", "_", text).strip("._")
    if not text:
        return "untitled"
    return text[:80]


def category_dirs(root: Path) -> list[Path]:
    result = []
    for path in sorted(root.iterdir()):
        if not path.is_dir():
            continue
        if re.match(r"^\d{2}_", path.name):
            result.append(path)
    return result


def category_name(dir_name: str) -> str:
    return re.sub(r"^\d{2}_", "", dir_name)


def compose_title(cat_name: str, focus: str, round_no: int) -> str:
    if round_no <= 1:
        return f"【不足補完】{cat_name}における{focus}の実装ノート"
    return f"【不足補完R{round_no:02d}】{cat_name}における{focus}の実装ノート"


def existing_titles(root: Path) -> set[str]:
    titles: set[str] = set()
    for md in root.rglob("*.md"):
        if any(part in {".git", ".obsidian", ".claude", ".codex", ".agent"} for part in md.parts):
            continue
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        m = re.search(r'^title:\s*"(.*?)"\s*$', text, re.MULTILINE)
        if m:
            titles.add(m.group(1).strip())
    return titles


def build_body(title: str, tag: str, focus: str, date_iso: str, category_path: str) -> str:
    return f"""---
title: "{title}"
date: {date_iso}
updated: {date_iso}
tags:
  - {tag}
author: "Zoo Knowledge Vault"
draft: true
---

# {title}

## 概要

本記事は `{tag}` カテゴリの不足補完として作成した実装ノートです。  
主題は「{focus}」で、現場運用で再利用しやすい判断軸と実務手順を短時間で参照できる形に整理しています。

## 何を整備するか

- 対象領域: `{category_path}`
- 補完テーマ: `{focus}`
- 目的: 属人化の低減、記録品質の統一、レビュー効率の向上

## 実務フレーム

1. 現状把握: 既存SOP、記録フォーマット、責任分担を棚卸しする。  
2. 設計: 入力データ項目、異常判定条件、エスカレーション条件を明文化する。  
3. 試行: 1〜2週間の試験運用を行い、例外ケースをログ化する。  
4. 定着: 週次レビューで差分を吸収し、月次でSOPに反映する。  

## 現場への示唆

{tag}領域では、単発の対応改善だけでは再発防止が難しく、判断基準を「いつ・誰が・どの情報で」適用するかを先に定義しておく必要があります。  
特に{focus}の改善では、実施率だけでなく「記録の再利用性」「引き継ぎ時の再現性」を同時に評価することで、運用品質が安定します。

## 次回更新で追記する項目

- 一次資料（公式発表・論文・ガイドライン）3件以上の追加  
- KPI候補と閾値設計の具体化  
- 関連記事との重複整理（統合・分割判断）  

## 関連記事

- [[00_Index/運用ガイド]]
- [[00_Index/リンクチェックレポート]]
- [[{category_path}]]

## 参照元

- カテゴリ内の既存記事群とリンク構造をもとに不足補完として起案。  
- 一次資料は次回更新時に追加予定（現時点は草案）。  
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate coverage-gap draft articles in batches.")
    parser.add_argument("--batch-size", type=int, default=300)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--batch-id", type=str, default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path.cwd()
    today = dt.date.today().isoformat()
    batch_stamp = args.batch_id.strip() or dt.datetime.now().strftime("%Y%m%d-%H%M%S")

    categories = category_dirs(root)
    if not categories:
        print("NO_CATEGORY_DIRS")
        return 1

    title_set = existing_titles(root)
    by_cat: dict[str, list[tuple[str, str, str]]] = defaultdict(list)

    for cat in categories:
        cat_name = category_name(cat.name)
        for focus in FOCUS_TOPICS:
            round_no = 1
            while True:
                title = compose_title(cat_name, focus, round_no)
                if title not in title_set:
                    break
                round_no += 1
            slug = sanitize_filename(f"{focus}_R{round_no:02d}")
            by_cat[cat.name].append((title, focus, slug))

    ordered_cats = [c.name for c in categories]
    pool: list[tuple[str, str, str, str]] = []
    active = True
    while active:
        active = False
        for cat_name_dir in ordered_cats:
            items = by_cat.get(cat_name_dir, [])
            if not items:
                continue
            active = True
            title, focus, slug = items.pop(0)
            pool.append((cat_name_dir, title, focus, slug))

    selected = pool[args.offset : args.offset + args.batch_size]
    print(f"CANDIDATES={len(pool)}")
    print(f"SELECTED={len(selected)} OFFSET={args.offset} BATCH={args.batch_size}")

    created = 0
    skipped = 0

    for idx, (cat_name_dir, title, focus, slug) in enumerate(selected, start=1):
        cat_dir = root / cat_name_dir
        out_dir = cat_dir / "不足項目補完" / f"バッチ_{batch_stamp}"
        out_path = out_dir / f"N_{idx + args.offset:04d}_{slug}.md"

        if args.dry_run:
            print(f"DRYRUN {idx:03d} {out_path.relative_to(root).as_posix()} :: {title}")
            continue

        if out_path.exists():
            skipped += 1
            print(f"SKIP   {idx:03d} exists {out_path.relative_to(root).as_posix()}")
            continue

        out_dir.mkdir(parents=True, exist_ok=True)
        body = build_body(
            title=title,
            tag=category_name(cat_name_dir),
            focus=focus,
            date_iso=today,
            category_path=cat_name_dir,
        )
        out_path.write_text(body, encoding="utf-8", newline="\n")
        created += 1
        print(f"WRITE  {idx:03d} {out_path.relative_to(root).as_posix()}")

    print(f"CREATED={created}")
    print(f"SKIPPED_EXISTING={skipped}")
    print(f"REMAINING_AFTER_BATCH={max(len(pool) - (args.offset + len(selected)), 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
