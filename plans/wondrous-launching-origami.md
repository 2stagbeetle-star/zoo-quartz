# Claude Codeベストプラクティス導入計画

## Context

ZOO KNOWLEDGE VAULTプロジェクトにClaude Codeのベストプラクティスを導入する。
具体的には以下の3点を実施することで、AIエージェントの作業品質・追跡可能性・レビュー精度を向上させる。

1. **CLAUDE.md** — プロジェクトルートに作成し、Claudeの行動指針を定義
2. **.agent/PLANS.md** — OpenAI推奨のExecPlanドキュメント形式を導入
3. **codex-reviewスキル** — プラン作成後に自動レビューをかけるスキルを追加

---

## 作成ファイル一覧

### 1. `CLAUDE.md`（プロジェクトルート）
**パス:** `c:\Users\stagb\OneDrive\デスクトップ\AIコード\動物\CLAUDE.md`

既存の `ZOO-KNOWLEDGE-VAULT-運用ガイド.md` と重複しないよう、Claudeの**行動ルール**に絞って記載する。

**含める内容:**

```markdown
# Plan Creation
plans/ ディレクトリにMarkdownファイルを作成したら、必ずcodex-reviewスキルでレビューすること。

# ExecPlans
複雑な機能追加・大規模リファクタリング時は .agent/PLANS.md に記述された
ExecPlan形式を使い、設計から実装まで一貫して管理すること。

# Review gate (codex-review)
以下のタイミングでcodex-reviewスキルを実行し、クリーンになるまで
review→fix→re-reviewを繰り返すこと：
- スペック/プランを更新した後
- 主要な実装ステップ完了後（≥5ファイル変更 / 公開API変更 / インフラ設定変更）
- コミット/PR/リリース前

# Task Management
機能実装やコード変更時はTasksを使い進捗を管理する。
作業をステップに分解し、完了次第ステータスを更新すること。

# 判断が必要な場合
ユーザーへの確認が必要な場合はAskUserQuestionツールを使うこと。

# プロジェクト固有のルール
- 運用詳細は .claude/ZOO-KNOWLEDGE-VAULT-運用ガイド.md を参照すること
- 記事は必ずフロントマター（title, date, updated, tags, author, draft）を含めること
- draft: false にする前にarticle-quality-checkスキルを実行すること
- カテゴリタグは1記事につき必ず1つだけ付与すること
- 一次資料（公式発表・論文・プレスリリース）を優先参照すること
```

---

### 2. `.agent/PLANS.md`
**パス:** `c:\Users\stagb\OneDrive\デスクトップ\AIコード\動物\.agent\PLANS.md`

OpenAI Cookbookで公開されているExecPlan形式の定義ファイル。
このファイルをCLAUDE.mdから参照することで、Claudeが実行計画ドキュメントの書き方を理解する。

**含める内容:** ExecPlanの構造（Context / Goals / Constraints / Steps / Verification）と記述ルール

---

### 3. `.claude/skills/codex-review.md`
**パス:** `c:\Users\stagb\OneDrive\デスクトップ\AIコード\動物\.claude\skills\codex-review.md`

既存スキル（`daily-topic-researcher.md`等）と同じ形式で作成する。

**動作:** 指定されたプランファイルまたは変更内容を読み込み、以下の観点でレビューを行う：
- 論理的一貫性
- 実装可能性
- 既存スキル・ワークフローとの整合性
- セキュリティ・品質上の問題

レビュー結果を`_drafts/codex-review-[日付].md`に出力し、指摘事項があればプランを修正する。

---

## 実装順序

1. `.agent/` ディレクトリを作成し `.agent/PLANS.md` を作成
2. `.claude/skills/codex-review.md` を作成
3. `CLAUDE.md` を作成（上記2ファイルへの参照を含む）

---

## 検証方法

1. `CLAUDE.md` が存在することを確認
2. `/codex-review` とタイプしてスキルが起動するか確認
3. `plans/` に任意のMarkdownを作成し、codex-reviewが自動実行されるか確認
4. `.agent/PLANS.md` を参照してClaudeがExecPlan形式で計画書を書けるか確認

---

## 注意事項

- `codex-review` スキルはClaude自身がレビューする実装（Codexなし版）として作成する
  （外部のCodexへの接続は別途設定が必要なため）
- 既存の12スキルファイルとの重複・競合なし
- `CLAUDE.md` の内容は `.claude/ZOO-KNOWLEDGE-VAULT-運用ガイド.md` と重複しないように注意
