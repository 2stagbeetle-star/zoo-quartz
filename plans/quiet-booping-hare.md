# Claude Code Chord キーバインドカスタマイズ

## Context

ObsidianページはJSレンダリングのため自動取得できなかったため、公式ドキュメント（v2.1.18+）の情報を元におすすめの chord 設定を行う。半永久的に使用することを前提に、日本語Windows環境のVSCode統合ターミナルで実用的なキーバインドを設定する。

---

## 現状

- `~/.claude/keybindings.json` は未作成
- `~/.claude/settings.json` は存在（既存設定を維持）
- Chord デフォルト（変更なし）:
  - `ctrl+x ctrl+k` → `chat:killAgents`
  - `ctrl+x ctrl+e` → `chat:externalEditor`

---

## 設定するキーバインド一覧

### Chat コンテキスト

| キー | アクション | 説明 |
|------|-----------|------|
| `ctrl+j` | `chat:newline` | Enter不要で改行挿入（最重要） |
| `ctrl+x ctrl+n` | `chat:newline` | Chord スタイルの改行（ctrl+j が使えない端末向け） |
| `ctrl+x ctrl+p` | `chat:modelPicker` | モデル選択ダイアログを開く |
| `ctrl+x ctrl+f` | `chat:fastMode` | 高速モード切り替え |
| `ctrl+x ctrl+i` | `chat:thinkingToggle` | 拡張思考モード切り替え |

### Global コンテキスト

| キー | アクション | 説明 |
|------|-----------|------|
| `ctrl+x ctrl+t` | `app:toggleTodos` | Todoリスト表示切り替え（デフォルト ctrl+t の補完） |
| `ctrl+x ctrl+o` | `app:toggleTranscript` | トランスクリプト表示切り替え |

---

## 実装ファイル

**作成するファイル:** `C:\Users\stagb\.claude\keybindings.json`

```json
{
  "$schema": "https://www.schemastore.org/claude-code-keybindings.json",
  "$docs": "https://code.claude.com/docs/ja/keybindings",
  "bindings": [
    {
      "context": "Chat",
      "bindings": {
        "ctrl+j": "chat:newline",
        "ctrl+x ctrl+n": "chat:newline",
        "ctrl+x ctrl+p": "chat:modelPicker",
        "ctrl+x ctrl+f": "chat:fastMode",
        "ctrl+x ctrl+i": "chat:thinkingToggle"
      }
    },
    {
      "context": "Global",
      "bindings": {
        "ctrl+x ctrl+t": "app:toggleTodos",
        "ctrl+x ctrl+o": "app:toggleTranscript"
      }
    }
  ]
}
```

---

## 注意点

- **`ctrl+j` について**: 一部の端末では `ctrl+j` が Enter と同じ扱い（LF/0x0A）になる場合がある。その場合は `ctrl+x ctrl+n` を使う。
- **予約済みキー（変更不可）**: `ctrl+c`, `ctrl+d`, `ctrl+m`
- **既存デフォルトとの競合なし**: `ctrl+x ctrl+n/p/f/i/t/o` はすべて未使用。

---

## 動作確認

1. `keybindings.json` 作成後、Claude Codeを再起動不要（自動リロード）
2. チャット入力中に `ctrl+j` を押して改行されることを確認
3. `/doctor` コマンドを実行して警告がないことを確認

---

## 参考

- [公式ドキュメント: キーボードショートカットのカスタマイズ](https://code.claude.com/docs/ja/keybindings)
