# 週次イベント情報マルチソース収集スキル 実装計画

## Context

既存の `automation/update-event-board.py`（Python HTMLスクレイパー）は現在イベント0件を返しており、掲示板が空の状態。ユーザーはウェブサイト・X・Instagram等の多角的ソースから一次資料まで徹底したイベント収集を毎週自動実行したい。既存スクレイパーを**完全に置き換え**、Claude CodeのWebSearch/WebFetchベースの新スキルに移行する。

---

## 実装ステップ

### Step 1: スキル定義の作成

**ファイル:** `.claude/skills/weekly-event-collector.md`

スキルの処理フロー:

1. **直接サイトチェック（WebFetch）** — 主要16サイトのイベントページを直接取得
2. **WebSearch広域検索** — SNS（`site:x.com`, `site:instagram.com`）・プレスリリース・自治体広報を検索
3. **一次資料裏取り（WebFetch）** — 各候補イベントの公式ページまで遡って確認
4. **統合・整形** — 重複排除、終了済み除外、既存テーブル形式でマークダウン出力
5. **掲示板ファイル更新** — `17_求人情報/生き物イベント掲示板.md` の AUTO-EVENTS マーカー内を更新

#### 直接チェック対象サイト（16件）

| 区分 | サイト | URL |
|------|--------|-----|
| 動物園 | 東武動物公園 | tobuzoo.com/event/ |
| 動物園 | 上野動物園 | tokyo-zoo.net/zoo/ueno/ |
| 動物園 | 多摩動物公園 | tokyo-zoo.net/zoo/tama/ |
| 動物園 | 旭山動物園 | city.asahikawa.hokkaido.jp/asahiyamazoo/ |
| 自治体 | 仙台市八木山動物公園 | city.sendai.jp/zoo/event/ |
| 水族館 | 京都水族館 | kyoto-aquarium.com/news/ |
| 水族館 | アクアマリンふくしま | aquamarine.or.jp/news/ |
| 水族館 | 名古屋港水族館 | nagoyaaqua.jp/event/ |
| 水族館 | 海遊館 | kaiyukan.com/connect/event/ |
| 水族館 | サンシャイン水族館 | sunshinecity.jp/aquarium/event/ |
| 博物館 | 北九州いのちのたび博物館 | kmnh.jp/event/list/event-info/ |
| 民間 | ジャパンレプタイルズショー | rep-japan.co.jp/jrs/ |
| NPO | NACS-J | nacsj.or.jp/event/ |
| NPO | JWCS | jwcs.org/event/ |
| 公園 | 国営昭和記念公園 | showakinen-koen.jp/event/ |
| 学会 | 日本爬虫両棲類学会 | herpetology.jp/ |

#### WebSearch検索クエリ群（10件程度）

- `動物園 イベント 2026年 開催`
- `水族館 イベント 体験 ナイト 2026`
- `爬虫類 即売会 エキスポ 2026`
- `自然史博物館 特別展 生き物 2026`
- `自然観察会 野鳥 参加者募集 2026`
- `site:x.com 動物園 イベント 開催`
- `site:x.com 水族館 ナイト 体験`
- `site:instagram.com 動物園 イベント`
- `site:prtimes.jp 動物園 水族館 イベント`
- `市 動物園 イベント 令和8年度`

地域ローテーション（偏り防止）: 第1週=関東・甲信越 / 第2週=関西・中部 / 第3週=北海道・東北・北陸 / 第4週=中国・四国・九州・沖縄

#### 出力テーブル形式（既存踏襲）

```
| 区分 | 分野 | 主催 | 地域 | イベント名 | 開催日 | 情報源 |
```

取得状況ブロックに一次資料確認率を追記:
```
- 更新日時: YYYY-MM-DD HH:MM:SS
- 掲載件数: N件（上限50件）
- 収集方法: 直接取得:X件 / WebSearch:Y件
- 一次資料確認率: Z%
```

---

### Step 2: 既存バッチファイルの修正

**ファイル:** `run_daily_research.bat`

月曜日の実行ブロックに `/weekly-event-collector` を追加。既存のPythonスクレイパー呼び出し（ステップ4）を新スキルに置き換え:

```
変更前:
  [4/5] python automation\update-event-board.py
  [5/5] /weekly-article-generator (月曜のみ)

変更後:
  [4/5] /weekly-event-collector (月曜のみ)  ← 新スキル
  [5/5] /weekly-article-generator (月曜のみ)
```

平日（火〜日）のPythonスクレイパー実行は削除。

---

### Step 3: 運用ガイドの更新

**ファイル:** `.claude/ZOO-KNOWLEDGE-VAULT-運用ガイド.md`

週次ワークフローセクションに `/weekly-event-collector` の説明を追記。

---

### Step 4: 掲示板ファイルの微修正

**ファイル:** `17_求人情報/生き物イベント掲示板.md`

- 「自動更新ステータス」セクションの説明文を更新（Python → Claude Codeスキルに変更）
- 「収集ルール」セクションにSNS間接検索の説明を追加

---

## 修正対象ファイルまとめ

| 操作 | ファイル |
|------|---------|
| 新規作成 | `.claude/skills/weekly-event-collector.md` |
| 修正 | `run_daily_research.bat` |
| 修正 | `.claude/ZOO-KNOWLEDGE-VAULT-運用ガイド.md` |
| 修正 | `17_求人情報/生き物イベント掲示板.md` |

※ `automation/update-event-board.py` は削除せず残置（履歴参照用）

---

## 検証方法

1. `/weekly-event-collector` を手動実行し、掲示板ファイルにイベントが掲載されることを確認
2. テーブルのマークダウン構文が正しいことを確認（Obsidianプレビュー）
3. 一次資料リンクが有効であることをスポットチェック（3件以上）
4. 終了済みイベントが除外されていることを確認
5. `run_daily_research.bat` のフロー整合性を確認（月曜以外はイベント収集がスキップされること）
