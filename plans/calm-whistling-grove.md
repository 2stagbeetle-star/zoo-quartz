# 全記事カテゴリ別時系列一覧の作成

## Context

プロジェクト（Zoo Knowledge Vault）に蓄積された約237件の記事を、トピック（カテゴリ）ごとに分類し、各カテゴリ内で最新記事を一番上にした一覧ページを新規作成する。現状、全記事を横断して一覧できるページがないため、ナビゲーション改善のために作成する。

## 方針

`zoo-quartzg56/content/00_Index/全記事カテゴリ一覧.md` を新規作成する。既存の `index.md` は変更しない。

## 実装手順

### Step 1: bashスクリプトで全記事データ収集

`content/` 配下の `01_`〜`18_` フォルダの全 `.md` ファイルから、フロントマターの `title` と `date` を抽出し、カテゴリ名でグループ化、日付降順でソートしたデータを生成する。

### Step 2: Markdownファイル生成

以下の構造で `全記事カテゴリ一覧.md` を作成:

```yaml
---
title: "全記事カテゴリ別一覧"
date: 2026-04-12
updated: 2026-04-12
tags:
  - index
author: "Zoo Knowledge Vault"
draft: false
---
```

- カテゴリごとに `## 01 飼育日誌` のようなh2見出し
- 番号順 01→18
- 各記事行: `- 2026-04-05 — [記事タイトル](ファイル名)` 
- Quartzの `markdownLinkResolution: "shortest"` に合わせ、リンクはファイル名のみ（パス不要、.md不要）

### Step 3: 検証

1. 各カテゴリの記事件数が `find` 結果と一致するか確認
2. ローカルでQuartzビルド可能か確認

## 変更対象ファイル

- **新規**: `zoo-quartzg56/content/00_Index/全記事カテゴリ一覧.md`
- **変更なし**: `zoo-quartzg56/content/00_Index/index.md`
