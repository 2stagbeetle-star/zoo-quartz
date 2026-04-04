# Quartz4 設定ファイル生成スキル

## 概要
Zoo Knowledge Vault 用の Quartz4 設定ファイルと GitHub Actions デプロイワークフローを生成する。
Quartz4 リポジトリのルートディレクトリで実行すること。

## 前提条件
- Quartz4 リポジトリがクローン済みであること
  ```bash
  git clone https://github.com/jackyzha0/quartz.git zoo-quartz
  cd zoo-quartz
  npm install
  ```
- GitHub リポジトリが作成済みであること

## 生成するファイル

### 1. `quartz.config.ts`

以下の設定で `quartz.config.ts` を上書き生成する:

```typescript
import { QuartzConfig } from "./quartz/cfg"
import * as Plugin from "./quartz/plugins"

const config: QuartzConfig = {
  configuration: {
    pageTitle: "Zoo Knowledge Vault",
    enableSPA: true,
    enablePopovers: true,
    analytics: null,
    locale: "ja-JP",
    baseUrl: "YOUR_GITHUB_USERNAME.github.io/zoo-quartz",
    ignorePatterns: [
      "_drafts",
      "_templates",
      ".obsidian",
      ".claude"
    ],
    defaultDateType: "modified",
    theme: {
      fontOrigin: "googleFonts",
      cdnCaching: true,
      typography: {
        header: "Noto Serif JP",
        body: "Noto Sans JP",
        code: "IBM Plex Mono",
      },
      colors: {
        lightMode: {
          light: "#faf8f5",
          lightgray: "#e8e4df",
          gray: "#5c5c5c",
          darkgray: "#222222",
          dark: "#0a0a0a",
          secondary: "#2d6a4f",
          tertiary: "#52796f",
          highlight: "rgba(45, 106, 79, 0.12)",
          textHighlight: "#fff23688",
        },
        darkMode: {
          light: "#1a1e1c",
          lightgray: "#2d3330",
          gray: "#a0a0a0",
          darkgray: "#e0e0e0",
          dark: "#ffffff",
          secondary: "#74c69d",
          tertiary: "#95d5b2",
          highlight: "rgba(116, 198, 157, 0.12)",
          textHighlight: "#b3aa0288",
        },
      },
    },
  },
  plugins: {
    transformers: [
      Plugin.FrontMatter(),
      Plugin.CreatedModifiedDate({ priority: ["frontmatter", "filesystem"] }),
      Plugin.SyntaxHighlighting(),
      Plugin.ObsidianFlavoredMarkdown({ enableInHtmlEmbed: false }),
      Plugin.GitHubFlavoredMarkdown(),
      Plugin.TableOfContents(),
      Plugin.CrawlLinks({ markdownLinkResolution: "shortest" }),
      Plugin.Description(),
      Plugin.Latex({ renderEngine: "katex" }),
    ],
    filters: [Plugin.RemoveDrafts()],
    emitters: [
      Plugin.AliasRedirects(),
      Plugin.ComponentResources(),
      Plugin.ContentPage(),
      Plugin.FolderPage(),
      Plugin.TagPage(),
      Plugin.ContentIndex({
        enableSiteMap: true,
        enableRSS: true,
      }),
      Plugin.Assets(),
      Plugin.Static(),
      Plugin.NotFoundPage(),
    ],
  },
}

export default config
```

**重要:** `baseUrl` の `YOUR_GITHUB_USERNAME` は実際のGitHubユーザー名に置き換えること。

### 2. `.github/workflows/deploy.yml`

```yaml
name: Deploy Quartz site to GitHub Pages

on:
  push:
    branches:
      - v4
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - name: Install Dependencies
        run: npm ci
      - name: Build Quartz
        run: npx quartz build
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: public

  deploy:
    needs: build
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

## 実行後の手順（手動）

```bash
# リモートリポジトリを追加（初回のみ）
git remote add origin https://github.com/YOUR_USERNAME/zoo-quartz.git

# 初回デプロイ
npx quartz sync

# GitHub の Settings → Pages → Source: GitHub Actions に設定
```

## 完了確認
- `quartz.config.ts` の `pageTitle` が "Zoo Knowledge Vault" になっていることを確認
- `.github/workflows/deploy.yml` が存在することを確認
