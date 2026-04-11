---
title: "飼育下と野生下の哺乳類寿命比較記事の Web 公開"
status: draft
date: 2026-04-12
---

## Context（なぜこの作業をするのか）

ユーザーが IDE で開いている [A_生物_2021_飼育下と野生下の哺乳類寿命比較.md](10_生物学・生命科学/A_生物_2021_飼育下と野生下の哺乳類寿命比較.md) を Zoo Knowledge Vault サイト（https://2stagbeetle-star.github.io/zoo-quartzg56/）に公開したい。

**現在の状態（確認済み）**

- 対象ファイルは既に `draft: false` / 正式カテゴリフォルダ（`10_生物学・生命科学/`）に配置済み。フロントマター・カテゴリタグ（`#生物学・生命科学` 1 つ）も CLAUDE.md のルールに準拠。
- 参照しているインフォグラフィック [_images/飼育下と野生下の哺乳類の寿命比較に関する大規模データ解析_infographic.svg](_images/飼育下と野生下の哺乳類の寿命比較に関する大規模データ解析_infographic.svg) は存在している。
- 既に [zoo-quartz/content/10_生物学・生命科学/](../../../Documents/zoo-quartz/content/10_生物学・生命科学/) 側にも同名ファイルは存在するが **内容が古い**（以前は `#学術論文・研究` と `#生物学・生命科学` の **カテゴリタグが 2 つ** 付いており、CLAUDE.md ルール「カテゴリタグは 1 記事 1 つ」に違反していた）。今回の deploy で Vault 側の正しい状態に上書きされる。

つまり記事そのものは公開準備が整っており、残る作業は **Vault → Quartz content/ への同期と GitHub Pages への push** だけ。

---

## 実行方針

既存の [.claude/deploy.sh](.claude/deploy.sh) を使う（`/deploy` スキルの本体）。独自スクリプトは作らない。

```bash
cd "c:/Users/stagb/OneDrive/デスクトップ/AIコード/動物"
bash .claude/deploy.sh
```

`deploy.sh` は以下を自動実行する（[deploy.sh:34-77](.claude/deploy.sh#L34-L77)）:

1. **同期**: Vault の `00_Index` 〜 `18_学術論文・研究` 全 19 カテゴリ + `_images/` を `~/Documents/zoo-quartz/content/` に `rm -rf` → `cp -r` で同期。
2. **ローカルビルド**: `cd ~/Documents/zoo-quartz && npx quartz build`。失敗時は push せず中止。
3. **GitHub push**: `content/` / `quartz.config.ts` / `quartz.layout.ts` / `package*.json` を stage → `YYYY-MM-DD 記事更新` のメッセージで commit → `origin v4` に push。
4. GitHub Actions が自動でビルド＆ Pages デプロイ（約 2〜3 分）。

---

## 事前に認識しておくべきこと（ユーザー確認事項）

### 1. zoo-quartz 側に既存の未コミット変更がある

`~/Documents/zoo-quartz` には対象記事とは **無関係な** 以下の変更が既に存在する:

- `quartz.config.ts`
- `quartz/styles/custom.scss`
- `content/15_動物園学・博物館学/繁殖・保全/動物園の繁殖と保全の役割.md`
- `content/_images/動物園の繁殖と保全の役割_infographic.svg`

`deploy.sh` は `git add content/ quartz.config.ts quartz.layout.ts package.json package-lock.json` で一括ステージするため、これらも **同じコミットに巻き込まれて push される**（[deploy.sh:72-76](.claude/deploy.sh#L72-L76)）。

→ 本プランはこれを許容する方針で進める（commit メッセージは `YYYY-MM-DD 記事更新` なので一括でも意味が通る）。もし分けたい場合はプラン承認前に知らせてほしい。

### 2. Vault 側の 221 ファイル分の未コミット変更には影響しない

Vault リポジトリと zoo-quartz リポジトリは **別 git リポジトリ**。`deploy.sh` は Vault 側の git には一切触らない。今回の作業で Vault 側の作業ツリーが変わることはない。

### 3. 外部への push を伴う不可逆性のある操作

`origin v4` への push は公開サイトに即反映される操作。承認後に 1 回だけ実行する想定。

---

## クリティカルファイル

### 読み取り/参照のみ
- [10_生物学・生命科学/A_生物_2021_飼育下と野生下の哺乳類寿命比較.md](10_生物学・生命科学/A_生物_2021_飼育下と野生下の哺乳類寿命比較.md) — 公開対象記事
- [_images/飼育下と野生下の哺乳類の寿命比較に関する大規模データ解析_infographic.svg](_images/飼育下と野生下の哺乳類の寿命比較に関する大規模データ解析_infographic.svg) — インフォグラフィック
- [.claude/deploy.sh](.claude/deploy.sh) — 実行するスクリプト
- [.claude/skills/deploy.md](.claude/skills/deploy.md) — スキルドキュメント

### 書き込み（deploy.sh が自動で行う）
- `~/Documents/zoo-quartz/content/10_生物学・生命科学/A_生物_2021_飼育下と野生下の哺乳類寿命比較.md`（上書き）
- `~/Documents/zoo-quartz/content/_images/飼育下と野生下の哺乳類の寿命比較に関する大規模データ解析_infographic.svg`（上書き）
- その他 Vault 配下の 00〜18 カテゴリ全般（deploy.sh が一律同期するため）

---

## 実行手順

1. **事前チェック**（プラン承認後、deploy 前）
   - ユーザー確認事項 1（zoo-quartz 側の既存変更を巻き込むこと）に異論がないか確認。
2. **deploy 実行**
   ```bash
   cd "c:/Users/stagb/OneDrive/デスクトップ/AIコード/動物"
   bash .claude/deploy.sh
   ```
   ログを監視し、`[1/3] Vault → content/ 同期` / `[2/3] ローカルビルド確認` / `[3/3] GitHub へプッシュ` が順に成功することを確認。
3. **異常時の対応**
   - `[2/3]` の `npx quartz build` が失敗 → エラー内容を確認し、該当ファイル（多くの場合ウィキリンク切れやフロントマター不正）を修正して再実行。push はされないため安全。
   - `[3/3]` の push が失敗（認証・ネットワーク等） → ログを提示してユーザーに相談。

---

## 検証（デプロイ後の確認）

1. **GitHub Actions**: https://github.com/2stagbeetle-star/zoo-quartzg56/actions で最新 run が緑になることを確認（約 2〜3 分）。
2. **公開サイト**: https://2stagbeetle-star.github.io/zoo-quartzg56/10_生物学・生命科学/A_生物_2021_飼育下と野生下の哺乳類寿命比較/ にアクセスして以下を確認:
   - 記事タイトル `飼育下と野生下の哺乳類の寿命比較に関する大規模データ解析` が表示される。
   - インフォグラフィック（SVG）が表示される。
   - カテゴリタグが `#生物学・生命科学` 1 つに整理されている（以前の `#学術論文・研究` とのダブりが消えている）。
3. **zoo-quartz リポジトリ**: `cd ~/Documents/zoo-quartz && git log -1 --stat` で commit 内容を確認。

---

## やらないこと（スコープ外）

- 記事本文の加筆・修正（ユーザーは「公開してほしい」としか言っていない）。
- 参考文献セクション「情報収集中」の埋め込み（指示がない。必要ならユーザー指示後に別タスクとして実施）。
- Vault 側の 221 ファイル分の未コミット変更の commit。
- `/article-quality-check` の実行（既に `draft: false` で運用フォルダに配置済みの記事であり、今回は「公開のみ」の依頼のため）。
