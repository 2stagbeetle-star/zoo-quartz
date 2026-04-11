# Claude Code カスタマイズ要求書 完成プラン

## Context

ユーザーから「Claude Code カスタマイズ要求書（詳細版・URL内プログラム保持版）」と題された Markdown 文書が共有されたが、第4章「URL内掲載プログラム（改変なし）」の途中で途切れている。この文書は Claude Code を「継続利用可能な高性能AIエージェント環境」として運用するための要求定義を目的としており、現状は総論（基本思想・3カテゴリ分類・エージェント概念）までしか書かれていない。

本プランの目的は、この要求書を**完成させ整形する**こと。具体的には、既存1〜4章を保持したうえで、動物プロジェクト（ZOO KNOWLEDGE VAULT）の現在のカスタマイズ状態（13個のスキル、ExecPlan、グローバル設定等）を反映した**実効性のある要求書**に仕上げる。ユーザーの指示により、第4章は現状のまま残し、5章以降に「現状インベントリ」「スコープ分離」「カスタマイズ要件」「実装ロードマップ・受入基準」を追加する。

---

## 保存先

**新規作成:** `.claude/Claude-Code-カスタマイズ要求書.md`

既存の `.claude/ZOO-KNOWLEDGE-VAULT-運用ガイド.md` と並ぶ、Claude Code 運用設計ドキュメントとして配置する。

---

## 文書の最終構成

```
1. 文書の目的                    ← 既存のまま保持
2. 基本思想                      ← 既存のまま保持（3カテゴリ分類）
3. Claude Code における AI エージェントの考え方  ← 既存のまま保持
4. URL内掲載プログラム（改変なし）  ← 既存のまま保持（途切れた状態で残す）
5. 現状設定インベントリ          ← 新規追加
6. スコープ分離（プロジェクト vs グローバル） ← 新規追加
7. カスタマイズ要件              ← 新規追加
8. 実装ロードマップ・受入基準    ← 新規追加
```

---

## 新規追加章の内容設計

### 第5章：現状設定インベントリ

「基本思想」の3カテゴリ（コンテキスト注入型／ツール提供型／実行環境型）に対応させて、現在のプロジェクト固有設定とグローバル設定を事実ベースで列挙する。

**5-1. コンテキスト注入型の現状**
- プロジェクト CLAUDE.md: `動物/CLAUDE.md`（codex-review実行ルール、フロントマター必須項目、タグ体系）
- 運用ガイド: `.claude/ZOO-KNOWLEDGE-VAULT-運用ガイド.md`（日次/週次/月次サイクル定義）
- ExecPlan定義: `.agent/PLANS.md`
- カスタムスキル13個: codex-review / daily-topic-researcher / weekly-article-generator / article-quality-check / article-archiver / deploy / paper-collector / job-listing-collector / create-templates / link-integrity-check / seasonal-topic-suggest / setup-vault-structure / generate-quartz-config

**5-2. ツール提供型の現状**
- MCP接続済み: Canva / Gmail / Notion / Google Calendar（認証待ち含む）
- Claude Code 組み込みツール: WebFetch, WebSearch 等

**5-3. 実行環境型の現状**
- サブエージェント: （要確認 - `.claude/agents/` 配下の定義）
- Hooks: （要確認 - `settings.json` 内の hooks 設定）

**5-4. グローバル設定（`C:\Users\stagb\.claude\`）**
- `settings.json`: effortLevel=high, language=japanese, model=opus, alwaysThinkingEnabled=true
- 権限ポリシー: Bash コマンド制限（find/grep/xargs 等）
- プランディレクトリ: `./plans`

---

### 第6章：スコープ分離（プロジェクト vs グローバル）

どの設定を「プロジェクト固有」、どれを「ユーザーグローバル」に置くべきかの指針を示す。

| 設定種別 | 配置先 | 理由 |
|---------|-------|------|
| 記事ルール・タグ体系 | プロジェクト CLAUDE.md | ZOO VAULT 特有の運用 |
| 週次/月次ワークフロー | プロジェクト `.claude/` | このプロジェクトの業務サイクル |
| 汎用スキル（commit等） | グローバル `~/.claude/skills/` | 複数プロジェクトで再利用 |
| モデル・言語・思考モード | グローバル `settings.json` | ユーザー全体の嗜好 |
| 権限ポリシー（書込可能域） | プロジェクト `settings.json` | プロジェクトごとに異なる |
| MCP接続（Canva等） | グローバル（認証単位） | アカウント単位の接続 |

---

### 第7章：カスタマイズ要件

現状調査から判明したギャップと新規要件を整理する。

**R-1. コンテキスト注入型**
- [要件] 記事執筆用のテンプレート/フロントマター検証スキルが既に存在するため、重複がないか精査
- [要件] CLAUDE.md に「一次資料優先」の具体的な検証手順を追記

**R-2. ツール提供型**
- [要件] Canva/Gmail/Notion MCP の認証完了と、スキルからの利用パターン定義
- [要件] 学術論文収集（paper-collector）で使う外部 API の整理

**R-3. 実行環境型**
- [要件] Hooks の活用状況を明示化（PostToolUse 等で article-quality-check を自動実行する仕組みがあるか）
- [要件] サブエージェントと Skills の使い分け指針

---

### 第8章：実装ロードマップ・受入基準

**フェーズ1（短期）**
- 現状インベントリの完成・精度向上
- 未確認項目（agents/、hooks設定）の調査と記載

**フェーズ2（中期）**
- カスタマイズ要件 R-1〜R-3 の個別具体化
- 各要件に対する ExecPlan 作成

**フェーズ3（長期）**
- MCP 認証の完了と統合活用
- 運用サイクル（日次/週次/月次）の自動化率向上

**受入基準**
- [ ] 要求書が `.claude/Claude-Code-カスタマイズ要求書.md` に保存されている
- [ ] 既存1〜4章が改変されず保持されている
- [ ] 第5章が実在するファイルパスと設定値で構成されている
- [ ] 第6章の分離指針が現実の配置と矛盾しない
- [ ] 第7章の要件がアクション可能な粒度で書かれている
- [ ] 文書を読めば Claude Code カスタマイズの全体像が把握できる

---

## 重要ファイル

参照（読み取り）:
- [動物/CLAUDE.md](CLAUDE.md) - プロジェクトルール
- [.claude/ZOO-KNOWLEDGE-VAULT-運用ガイド.md](.claude/ZOO-KNOWLEDGE-VAULT-運用ガイド.md) - 運用サイクル
- [.agent/PLANS.md](.agent/PLANS.md) - ExecPlan形式
- [.claude/skills/](.claude/skills/) - 13個のスキル定義
- `C:\Users\stagb\.claude\settings.json` - グローバル設定

作成（書き込み）:
- `.claude/Claude-Code-カスタマイズ要求書.md`（新規）

---

## 実装手順

1. `.claude/Claude-Code-カスタマイズ要求書.md` を新規作成
2. ユーザー提供の既存1〜4章をそのまま冒頭に配置（第4章は途切れた状態で残す）
3. 第5章「現状設定インベントリ」を上記の構成で記述
4. 第6章「スコープ分離」の表を記述
5. 第7章「カスタマイズ要件」の R-1〜R-3 を記述
6. 第8章「実装ロードマップ・受入基準」を記述
7. `codex-review` スキルでレビュー、CLEAN になるまで修正

---

## 検証方法

1. 作成後、ファイルを読み上げて章構成が揃っていることを確認
2. 既存 CLAUDE.md と `ZOO-KNOWLEDGE-VAULT-運用ガイド.md` と内容矛盾がないかチェック
3. `codex-review` スキルを実行してレビュー結果が CLEAN になるまで修正
4. 第5章のファイルパス・スキル名が実在することを Glob/Read で突き合わせ確認

---

## 想定される未確認事項

以下はプラン実行時に現状調査が必要：
- `.claude/agents/` 配下のサブエージェント定義（存在する場合）
- `settings.json` の `hooks` セクションの中身
- プロジェクト `settings.json` の権限設定詳細
