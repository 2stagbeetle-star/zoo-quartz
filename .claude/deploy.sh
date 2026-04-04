#!/bin/bash
# Zoo Knowledge Vault - デプロイスクリプト
# 使い方: bash .claude/deploy.sh
# 動物/ フォルダのルートで実行すること

set -e

VAULT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
QUARTZ_DIR="$HOME/Documents/zoo-quartz"

# ── 認証トークンを ~/.env から読み込む ──
# ~/.env に以下を追記してください:
#   GITHUB_TOKEN=ghp_your_token_here
ENV_FILE="$HOME/.env"
if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1090
  set -o allexport
  source "$ENV_FILE"
  set +o allexport
fi
if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "エラー: GITHUB_TOKEN が設定されていません。" >&2
  echo "  ~/.env に以下を追記してください: GITHUB_TOKEN=ghp_..." >&2
  exit 1
fi
TOKEN="$GITHUB_TOKEN"

echo "=== Zoo Knowledge Vault デプロイ ==="
echo "Vault: $VAULT_DIR"
echo "Quartz: $QUARTZ_DIR"
echo ""

# 1. content/ へ同期（全公開カテゴリ + _images）
echo "[1/3] Vault → content/ 同期中..."
for dir in \
  00_Index 01_飼育日誌 02_季節トピック 03_飼育ノウハウ \
  04_生態系ニュース 05_種別図鑑 06_自然環境 \
  07_水族館・水生生物 08_動物保護・保全生物学 09_獣医学・動物医療 \
  10_生物学・生命科学 11_生態学・自然環境学 12_植物学・植生 \
  13_生物分類図鑑 14_環境問題・気候変動 15_動物園学・博物館学 \
  16_フィールドワーク・調査手法 17_求人情報 18_学術論文・研究; do
  if [ -d "$VAULT_DIR/$dir" ]; then
    rm -rf "$QUARTZ_DIR/content/$dir"
    cp -r "$VAULT_DIR/$dir" "$QUARTZ_DIR/content/"
  fi
done
# _images を content/_images/ へコピー（記事の相対パス参照に合わせる）
if [ -d "$VAULT_DIR/_images" ]; then
  mkdir -p "$QUARTZ_DIR/content/_images"
  cp -r "$VAULT_DIR/_images/." "$QUARTZ_DIR/content/_images/"
fi
cp "$VAULT_DIR/00_Index/index.md" "$QUARTZ_DIR/content/index.md"
echo "  完了"

# 2. ローカルビルド確認
echo "[2/3] ローカルビルド確認..."
export PATH="$PATH:/c/Program Files/nodejs"
cd "$QUARTZ_DIR"
BUILD_LOG="$(npx quartz build 2>&1)"
BUILD_EXIT=$?
echo "$BUILD_LOG" | grep -E "Done|Error|Warning" || true
if [ $BUILD_EXIT -ne 0 ]; then
  echo "エラー: quartz build が失敗しました。デプロイを中止します。" >&2
  echo "$BUILD_LOG" >&2
  exit 1
fi
echo "  完了"

# 3. GitHub へプッシュ
echo "[3/3] GitHub へプッシュ中..."
git remote set-url origin "https://2stagbeetle-star:${TOKEN}@github.com/2stagbeetle-star/zoo-quartzg56.git"
git add content/ quartz.config.ts quartz.layout.ts package.json package-lock.json 2>/dev/null || true
git diff --cached --quiet && echo "  変更なし。スキップ。" && exit 0
git commit -m "$(date '+%Y-%m-%d') 記事更新"
GIT_CONFIG_NOSYSTEM=1 GIT_TERMINAL_PROMPT=0 \
  git -c credential.helper="" push origin v4 2>&1
echo "  完了"

echo ""
echo "=== デプロイ完了 ==="
echo "サイト: https://2stagbeetle-star.github.io/zoo-quartzg56/"
