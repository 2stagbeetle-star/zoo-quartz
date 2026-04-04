# デプロイスキル

## 概要
Vault の公開記事を GitHub Pages に同期・デプロイする。
記事確認・公開状態への変更が完了した後に実行する。

## 使い方
```
/deploy
```
動物/ フォルダのルートで実行すること。

## 実行手順

### ステップ 1: 公開予定記事の確認

`_drafts/` 内で `draft: false` になっている記事を確認する:
```bash
grep -rl "^draft: false" _drafts/ 2>/dev/null
```

各記事を正式フォルダへコピーする（例）:
```bash
cp "_drafts/飼育ノウハウ_YYYY-MM-DD_タイトル.md" "03_飼育ノウハウ/環境エンリッチメント/タイトル.md"
```

### ステップ 2: content/ へ同期

`~/Documents/zoo-quartz/content/` に公開カテゴリをコピー:
```bash
bash .claude/deploy.sh
```

これにより以下が自動実行される:
1. 全公開カテゴリ（00〜18）を content/ へ同期
2. ローカルビルド確認（エラーチェック）
3. GitHub へプッシュ（v4 ブランチ）
4. GitHub Actions が自動でビルド＆Pages デプロイ

### ステップ 3: 公開確認

デプロイ完了後（約2〜3分）にサイトを確認:
- **サイトURL:** https://2stagbeetle-star.github.io/zoo-quartzg56/
- **Actions状況:** https://github.com/2stagbeetle-star/zoo-quartzg56/actions

## 手動 quartz sync（代替コマンド）

```bash
cd ~/Documents/zoo-quartz
npx quartz sync
```

## 週次ワークフロー（まとめ）

```
① /weekly-article-generator  → _drafts/ に記事生成
② /article-quality-check     → 品質チェック（基準クリアまで修正）
③ Obsidian で記事確認・修正
④ draft: true → false に変更
⑤ /article-archiver          → 正式フォルダ（01〜18）へ自動分類・移動
⑥ /deploy                    → GitHub Pages にデプロイ
```
