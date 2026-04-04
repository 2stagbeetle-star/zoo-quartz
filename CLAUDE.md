# CLAUDE.md — ZOO KNOWLEDGE VAULT 行動ルール

プロジェクトの運用詳細は `.claude/ZOO-KNOWLEDGE-VAULT-運用ガイド.md` を参照すること。
このファイルはClaudeの**行動指針**のみを定義する。

---

# Plan Creation

`plans/` ディレクトリにMarkdownファイルを作成したら、必ず `codex-review` スキルでレビューすること。
レビューでCLEANと判定されるまでreview→fix→re-reviewを繰り返す。

---

# ExecPlans

複雑な機能追加・大規模リファクタリング時は `.agent/PLANS.md` に記述された
ExecPlan形式を使い、設計から実装まで一貫して管理すること。

---

# Review gate (codex-review)

以下のタイミングで `codex-review` スキルを実行し、クリーンになるまで繰り返すこと：

- スペック/プランを更新した後
- 主要な実装ステップ完了後（5ファイル以上変更 / 公開API変更 / インフラ設定変更）
- コミット/デプロイ前

---

# Task Management

機能実装やコード変更時はTasksを使い進捗を管理する。
作業をステップに分解し、完了次第ステータスを更新すること。

---

# 判断が必要な場合

ユーザーへの確認が必要な場合は `AskUserQuestion` ツールを使うこと。

---

# プロジェクト固有のルール

- 記事は必ずフロントマター（`title`, `date`, `updated`, `tags`, `author`, `draft`）を含めること
- `draft: false` にする前に `article-quality-check` スキルを実行すること
- カテゴリタグは1記事につき必ず1つだけ付与すること
- 一次資料（公式発表・論文・プレスリリース）を優先参照すること
- 不可逆な操作（ファイル削除・フォルダ移動）は実行前にユーザーに確認すること
