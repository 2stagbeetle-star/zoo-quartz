# Claude Code カスタマイズ要求書（詳細版・URL内プログラム保持版）

## 1. 文書の目的
本要求書は、Claude Code を単なるチャットAIとしてではなく、  
**継続利用可能な高性能AIエージェント環境**として運用するためのカスタマイズ要件を定義するものである。

Claude Code は、コーディングや汎用性に優れた AI エージェントとして紹介されており、  
単に質問へ回答するだけではなく、目標に対してツールを使いながら自律的に進行する存在として扱われている。 :contentReference[oaicite:1]{index=1}

---

## 2. 基本思想
Claude Code の拡張性は、ページ上では大きく次の3カテゴリに整理されている。 :contentReference[oaicite:2]{index=2}

### 2-1. コンテキスト注入型
AIに対して、知識・ルール・手順・テンプレートをテキストとして与える仕組み。

対象:
- CLAUDE.md
- カスタムコマンド
- ルール（Rules）
- Skills

### 2-2. ツール提供型
AIが使える道具、つまり外部サービス接続や関数を与える仕組み。

対象:
- MCP

### 2-3. 実行環境型
AIがどのように作業を分業し、どのように自動処理を行うかを決める仕組み。

対象:
- サブエージェント
- Hooks

---

## 3. Claude Code における AI エージェントの考え方
ページ内では、Claude Code 開発元の Anthropic の考え方として、  
AIエージェントは **“Agents are models using tools in a loop”** と説明されている。  
つまり、エージェントとは「ツールをループで使うモデル」であり、  
目標を受け取って、情報を集め、行動し、結果を確認し、不足があれば再実行する流れで動く。 :contentReference[oaicite:3]{index=3}

---

## 4. URL内掲載プログラム（改変なし）
以下は、URL内でこちらが確認できたプログラム記述であり、**一切変更せずそのまま掲載**する。

```text
目標を受け取る → 情報を集める → 行動する → 結果を確認する → 足りなければもう一回 → ...
```

※URL内に掲載されていた内容は上記1行のみであり、これ以降の追記は行わない。

---

## 5. 現状設定インベントリ

本章は、第2章の3カテゴリ（コンテキスト注入型／ツール提供型／実行環境型）に対応させて、
ZOO KNOWLEDGE VAULT プロジェクト（動物プロジェクト）とユーザーグローバル設定の現状を
事実ベースで列挙するものである。

### 5-1. コンテキスト注入型の現状

**プロジェクトレベルのコンテキスト**

- プロジェクト CLAUDE.md: `動物/CLAUDE.md`
  - プラン作成後の codex-review 実行ルール
  - ExecPlan 形式（`.agent/PLANS.md`）の使用指示
  - Review gate タイミング（スペック更新後／5ファイル以上変更後／コミット前）
  - 記事フロントマター必須項目（title, date, updated, tags, author, draft）
  - カテゴリタグは1記事につき1つのみ
  - 一次資料優先参照の原則

- 運用ガイド: `.claude/ZOO-KNOWLEDGE-VAULT-運用ガイド.md`
  - 日次／週次／月次サイクルの定義

- ExecPlan定義: `.agent/PLANS.md`
  - Context / Goals / Constraints / Steps / Verification / Notes の標準形式

**カスタムスキル（13個、`.claude/skills/` 配下）**

| スキル名 | 役割 |
|---------|------|
| codex-review | プラン・実装レビュー（論理一貫性・実装可能性・既存ワークフロー整合性） |
| daily-topic-researcher | 1トピック深掘り調査 |
| weekly-article-generator | 週次記事生成（A/B/Cランク分類、3層構造出力） |
| article-quality-check | フロントマター・タグ・文字数・ウィキリンク検査 |
| article-archiver | draft:false の記事を自動分類・移動 |
| deploy | 同期 → ローカルビルド → GitHub Push → Actions実行 |
| paper-collector | 学術論文収集・タグ付与 |
| job-listing-collector | 求人情報収集・整理 |
| create-templates | テンプレート生成 |
| link-integrity-check | 孤立ウィキリンク検出 |
| seasonal-topic-suggest | 季節トピック提案 |
| setup-vault-structure | Vault 初期化 |
| generate-quartz-config | Quartz 設定生成 |

**カスタムコマンド**

- `.claude/commands/` ディレクトリは未定義（現状カスタムスラッシュコマンドは未使用）

**ルール（Rules）**

- CLAUDE.md 内に記載のプロジェクト固有ルールのみ（独立した Rules 機構は未使用）

---

### 5-2. ツール提供型の現状

**MCPサーバー接続状況**

| サービス | 登録状態 | 認証状態 | 用途想定 |
|---------|---------|---------|---------|
| Canva | 登録済み | 要確認 | デザイン生成・編集 |
| Gmail | 登録済み | 要確認 | メール読み取り・下書き |
| Notion | 登録済み | 要確認 | ページ検索・更新 |
| Google Calendar | 登録済み | 要認証 | 予定管理 |

※「登録済み」= MCP サーバー接続定義が存在する。各サービスの利用には個別に認証完了が必要。

**Claude Code 組み込みツール**

- WebSearch / WebFetch（settings.json で許可済み）
- Bash・Read・Edit・Write・Grep・Glob 等の標準ツール

---

### 5-3. 実行環境型の現状

**サブエージェント**

- `.claude/agents/` ディレクトリは未定義
- 現状、サブエージェント定義は一切存在しない
- 並列処理・コンテキスト分離が必要な場合は組み込みの Explore / Plan / general-purpose を使用

**Hooks**

- `settings.json` に `hooks` セクション無し
- PreToolUse / PostToolUse / Stop 等の自動化フックは未使用

---

### 5-4. グローバル設定（`C:\Users\stagb\.claude\`）

**`settings.json` の主要設定**

| 設定キー | 値 |
|---------|---|
| effortLevel | "high" |
| language | "japanese" |
| model | "opus" |
| alwaysThinkingEnabled | true |
| plansDirectory | "./plans" |

**権限ポリシー**

- Bash コマンド制限（find / grep / xargs / sort / echo / python3 / winget / choco / scoop 等）
- プロジェクトごとの `settings.local.json` で追加許可（例：`git --version`, `python3 .claude/generate_infographic.py *`）

**グローバル資産**

- `backups/` / `debug/` / `ide/` / `shell-snapshots/` / `sessions/` / `file-history/` / `plans/`

---

## 6. スコープ分離（プロジェクト vs グローバル）

カスタマイズを追加する際、どのレイヤーに配置すべきかの指針を示す。

| 設定種別 | 配置先 | 理由 |
|---------|-------|------|
| 記事ルール・タグ体系・フロントマター | プロジェクト CLAUDE.md | ZOO VAULT 特有の運用ルール |
| 日次/週次/月次ワークフロー | プロジェクト `.claude/` | このプロジェクトの業務サイクル |
| プロジェクト固有スキル（13個） | プロジェクト `.claude/skills/` | ZOO VAULT 専用の処理 |
| 汎用スキル（例：commit・review-pr 等） | グローバル `~/.claude/skills/` | 複数プロジェクトで再利用 |
| モデル・言語・思考モード | グローバル `settings.json` | ユーザー全体の嗜好 |
| 権限ポリシー（書込可能域） | プロジェクト `settings.json` | プロジェクトごとに異なる |
| Bash 実行許可ポリシー | グローバル＋プロジェクト `settings.local.json` | セキュリティ境界 |
| MCP 接続（Canva 等） | グローバル（認証単位） | アカウント単位の接続 |
| ExecPlan 定義 | プロジェクト `.agent/` | プロジェクト固有の作業パターン |

※グローバル `~/.claude/skills/` 配下の具体的な内容は本要求書では未調査。別タスクで棚卸しを行う。

**分離原則**

1. **再利用性があるものはグローバルへ** - 複数プロジェクトで使える汎用処理
2. **プロジェクト固有の業務知識はプロジェクトへ** - 記事運用ルール・ワークフロー
3. **認証・アカウント単位の接続はグローバル** - MCP・OAuth トークン
4. **セキュリティ境界はプロジェクトで厳しく** - 書き込み許可域は最小限に

---

## 7. カスタマイズ要件

現状インベントリ（第5章）の分析から判明したギャップと、今後必要となる要件を整理する。

### R-1. コンテキスト注入型の要件

| ID | 要件 | 優先度 |
|----|------|-------|
| R-1.1 | 既存13スキルの役割重複を精査し、統廃合候補を明確化する | 中 |
| R-1.2 | CLAUDE.md の「一次資料優先」原則に具体的な検証手順を追記する | 中 |
| R-1.3 | `.claude/commands/` を定義し、頻繁な手作業をスラッシュコマンド化する | 低 |
| R-1.4 | スキル間の呼び出し順序（日次→週次→月次）を CLAUDE.md に明示する | 中 |

### R-2. ツール提供型の要件

| ID | 要件 | 優先度 |
|----|------|-------|
| R-2.1 | Canva / Gmail / Notion / Google Calendar MCP の認証完了 | 高 |
| R-2.2 | MCP をスキルから利用する標準パターンを文書化する | 中 |
| R-2.3 | paper-collector が使う外部 API（arXiv・CrossRef 等）を整理・接続定義 | 中 |

### R-3. 実行環境型の要件

| ID | 要件 | 優先度 |
|----|------|-------|
| R-3.1 | サブエージェント定義の必要性を評価（並列調査・レビューの分離） | 低 |
| R-3.2 | Hooks（PostToolUse）で article-quality-check を自動実行する仕組み検討 | 中 |
| R-3.3 | サブエージェントと Skills の使い分け指針を文書化する | 中 |

---

## 8. 実装ロードマップ・受入基準

### 8-1. フェーズ分け

**フェーズ1（短期：基盤整備）**

- 本要求書の初版完成と `codex-review` によるレビュー
- R-2.1: MCP 認証の完了（Canva / Gmail / Notion / Google Calendar）
- R-1.2: CLAUDE.md の一次資料検証手順追記

**フェーズ2（中期：要件実装）**

- R-1.1: 既存スキルの重複精査と統廃合
- R-1.4: スキル呼び出し順序の明文化
- R-2.2: MCP 利用パターンのスキル組み込み
- R-3.2: Hooks による article-quality-check 自動化の PoC

**フェーズ3（長期：自動化深化）**

- R-2.3: 外部 API 統合（paper-collector 強化）
- R-3.1: サブエージェント定義（必要と判断された場合のみ）
- 日次/週次/月次サイクルの全自動化率向上

### 8-2. 受入基準

- [ ] 要求書が `.claude/Claude-Code-カスタマイズ要求書.md` に保存されている
- [ ] 既存1〜4章が改変されず保持されている
- [ ] 第5章が実在するファイルパス・スキル名・設定値で構成されている
- [ ] 第6章のスコープ分離指針が現状配置と矛盾しない
- [ ] 第7章の要件が ID 付きかつアクション可能な粒度で書かれている
- [ ] 第8章のフェーズ分けが要件と対応している
- [ ] 文書を通読すると Claude Code カスタマイズの全体像が把握できる
- [ ] `codex-review` スキルで CLEAN 判定を受ける
