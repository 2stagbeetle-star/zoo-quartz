# 記事テンプレート作成スキル

## 概要
Zoo Knowledge Vault の 5種類の記事テンプレートを `_templates/` ディレクトリに作成する。
既存のテンプレートが存在する場合は上書きするかどうか確認する。

## 作成するテンプレート

### 1. 飼育日誌テンプレート（`_templates/飼育日誌.md`）
- フロントマター: title, date, updated, tags（飼育日誌・species_tag・category_tag）, species, animal_name, author, draft
- セクション: 観察概要テーブル、観察内容、飼育上の気づき、関連する過去の記録、参考文献

### 2. 季節トピックテンプレート（`_templates/季節トピック.md`）
- フロントマター: title, date, updated, tags（季節トピック・season・topic_tag）, season, author, draft
- セクション: はじめに、この季節の特徴、飼育現場での対応、来園者向けの見どころ、関連記事

### 3. 飼育ノウハウテンプレート（`_templates/飼育ノウハウ.md`）
- フロントマター: title, date, updated, tags（飼育ノウハウ・category_tag・difficulty）, category, difficulty, author, draft
- セクション: 概要テーブル、背景・目的、必要な準備・器材、手順、注意点・安全管理、事例・実績、関連ノウハウ

### 4. 生態系ニューステンプレート（`_templates/生態系ニュース.md`）
- フロントマター: title, date, updated, tags（生態系ニュース・topic_tag）, source, author, draft
- セクション: ニュース概要、背景と文脈、動物園・飼育現場への影響、今後の展望、情報源、関連記事

### 5. 種別図鑑テンプレート（`_templates/種別図鑑.md`）
- フロントマター: title, date, updated, tags（種別図鑑・taxon_class・conservation_status）, species_ja/en/sci, taxon_class, conservation_status, author, draft
- セクション: 基本情報テーブル、生態・習性、飼育管理のポイント、国内の飼育状況、保全に関する情報、関連種

## 完了確認
- `_templates/` の内容一覧を表示する
- 各テンプレートファイルの先頭を確認する
