# 学術論文収集・翻訳スキル

## 概要
自然科学（動物園学・保全生物学・生態学・獣医学・海洋生物学等）の最新学術論文を
英語文献から収集し、日本語要約付きで記事化する。
**月1回（第2月曜日）** の実行を推奨。

---

## ステップ 1: 検索対象ジャーナルの確認

### 優先確認ジャーナル（オープンアクセス・無料）

| 誌名 | 分野 | URL |
|-----|------|-----|
| JZAR（Journal of Zoo and Aquarium Research） | 動物園・水族館全般 | https://www.jzar.org/jzar |
| Frontiers in Conservation Science | 保全生物学 | https://www.frontiersin.org/journals/conservation-science |
| Frontiers in Ecology and Evolution | 生態・進化 | https://www.frontiersin.org/journals/ecology-and-evolution |
| Frontiers in Veterinary Science | 獣医学 | https://www.frontiersin.org/journals/veterinary-science |
| Frontiers in Marine Science | 海洋・水族館 | https://www.frontiersin.org/journals/marine-science |
| BMC Ecology and Evolution | 生態・遺伝 | https://bmcecolevol.biomedcentral.com/ |
| MDPI – J. Zool. Bot. Gard. (JZBG) | 動物園・植物園 | https://www.mdpi.com/journal/jzbg |
| MDPI – Zoo Animals | 動物全般 | https://www.mdpi.com/journal/zooanimals |
| ZooKeys | 分類学 | https://zookeys.pensoft.net/ |

### 定期チェックするデータベース

| データベース | 検索式例 | URL |
|------------|--------|-----|
| PubMed | zoo OR aquarium AND welfare OR enrichment | https://pubmed.ncbi.nlm.nih.gov/ |
| Google Scholar | "zoo" "conservation" 2025 sort:date | https://scholar.google.com/ |
| bioRxiv | ecology conservation zoo | https://www.biorxiv.org/ |
| acaric（論文サイト一覧ポータル） | 理系・自然科学の論文サイトへのリンク集 | https://acaric.jp/articles/3134#rikei_1 |

---

## 記事・論文調査の基本方針（リサーチ運用ルール）

`CLAUDE.md` の「リサーチ運用ルール（共通方針）」セクションに従うこと。
基本方針・参照範囲・記事作成時の必須条件（マークダウン保存含む）はすべて本体ルールに記載されている。

---

## ステップ 2: 論文の選定基準

以下の条件を**すべて満たす**論文を選ぶ:

1. **発行年:** 直近12ヶ月以内（または特に重要な場合は2年以内）
2. **分野:** 動物園・水族館・保全生物学・生態学・動物行動学・獣医学・海洋生物学・植物学のいずれか
3. **内容:** 動物園・水族館スタッフ、保全関係者、研究者に有益な知見を含む
4. **DOI:** 記載あり（査読済み論文を優先。プレプリントは明記）

**除外基準:** ペット・家畜のみを対象とした研究、ヒト医学研究、農業・食品科学

---

## ステップ 3: 論文の日本語要約作成

各論文について以下の形式で要約する:

```markdown
#### 🔬 [論文タイトルの日本語訳]

**原題:** *[英語タイトル]*
**掲載誌:** [誌名], [巻]([号]): [ページ] ([発行年])
**著者:** [筆頭著者] et al.
**DOI:** [doi.org/xxxxx]
**入手:** [OA/PMC/要機関アクセス等]

**日本語要約:**
[200〜400字で内容・結論・意義を平易に解説。専門用語には括弧で説明を付ける。
動物園・保全・飼育実務への応用・示唆を必ず含める。]
```

### 翻訳のルール

- **専門用語** は日本語 + 英語を併記: 例）エンリッチメント（behavioral enrichment）
- **数値・統計** はそのまま記載（p値・信頼区間等）
- **機関名・ジャーナル名** は英語のまま
- **不確実な箇所** は「[要確認]」と付記
- タイトルは意訳可。元のニュアンスを損なわないように

---

## ステップ 4: ファイルへの保存

### カテゴリ別保存先

| 分野 | 保存フォルダ |
|------|-----------|
| 動物園・飼育・福祉 | `18_学術論文・研究/動物園・飼育研究/` |
| 保全生物学・絶滅危惧種 | `18_学術論文・研究/保全生物学/` |
| 生態学・行動学・進化 | `18_学術論文・研究/生態学・行動学/` |
| 獣医学・動物医療 | `18_学術論文・研究/獣医学・動物医療/` |
| 水族館・海洋生物学 | `18_学術論文・研究/水族館・海洋生物学/` |
| 植物学・植生 | `18_学術論文・研究/植物学・植生/` |

### ファイル名形式

```
[YYYY-MM]_[キーワード]_論文まとめ.md
例: 2026-03_動物園福祉AI_論文まとめ.md
```

### フロントマター形式

```yaml
---
title: "[月次論文まとめ: テーマ名]"
date: YYYY-MM-DD
updated: YYYY-MM-DD
tags:
  - 学術論文
  - [分野タグ]
  - [キーワードタグ]
author: "Zoo Knowledge Vault"
language_original: "英語"
translated: true
draft: false
---
```

---

## ステップ 5: データベース一覧記事の更新

`18_学術論文・研究/学術論文・研究データベース一覧.md` の
**「注目論文（2024〜2025年）」** セクションに新規論文を追記:

1. `updated:` フロントマターを今日の日付に変更
2. 該当カテゴリのセクションに論文ブロックを追加
3. 古い論文（2年以上前）は「## アーカイブ論文」セクションに移動

---

## ステップ 6: 完了報告

- 収集した論文数（分野別内訳）を報告
- 新規ファイル名・更新ファイル名を列挙
- 「`/deploy` でサイトに反映できます」と案内

---

## 参考: よく使う PubMed 検索式

```
# 動物園全般
zoo[Title/Abstract] AND (welfare OR behavior OR enrichment)[Title/Abstract]
AND 2025[pdat]

# 保全繁殖
captive breeding[Title/Abstract] AND (endangered OR conservation)[Title/Abstract]
AND 2024:2025[pdat]

# 野生復帰
reintroduction[Title/Abstract] AND wildlife[Title/Abstract]
AND 2024:2025[pdat]

# 水族館・海洋
aquarium[Title/Abstract] AND (coral OR marine)[Title/Abstract]
AND 2025[pdat]

# 動物行動・エンリッチメント
enrichment[Title/Abstract] AND zoo[Title/Abstract]
AND 2024:2025[pdat]
```
