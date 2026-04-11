#!/usr/bin/env python3
"""
Zoo Knowledge Vault - 統一インフォグラフィック生成スクリプト
記事種別に応じた5種のSVGテンプレートを自動選択・生成する。

使い方:
  python generate_infographic.py <記事ファイルパス> [--type TYPE] [--no-skip-books]

オプション:
  --type TYPE       インフォグラフィック種別を指定
                    summary(デフォルト) / comparison / timeline / chart / steps
  --no-skip-books   書籍・雑誌一覧ページもスキップしない

出力:
  _images/<記事名>_infographic.svg
"""

import sys
import os
import json
import re
import time
import unicodedata
import urllib.request
import urllib.error
import html

# Windows の cp932 対策: stdout/stderr を UTF-8 に強制
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ─────────────────────────────────────────────
#  設定
# ─────────────────────────────────────────────
API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not API_KEY:
    print("警告: GEMINI_API_KEY が設定されていません。ローカル解析モードで動作します。", file=sys.stderr)
    print("  設定方法: ~/.env に GEMINI_API_KEY=AIzaSy... を追記してください。", file=sys.stderr)

# 利用可能なモデルを順番に試す（無料枠優先）
MODELS = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash",
]

def get_gemini_url(model):
    return (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={API_KEY}"
    )

VAULT_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(VAULT_DIR, "_images")

BOOK_SKIP_KEYWORDS = ["書籍", "雑誌一覧", "Amazon", "楽天", "ISBN", "購入リンク"]
VALID_TYPES = {"summary", "comparison", "timeline", "chart", "steps"}

# ─────────────────────────────────────────────
#  カラーパレット（自然テーマ・ナチュラルモダン）
# ─────────────────────────────────────────────
COLORS = {
    "bg":          "#f5f2ec",   # 生成り（ノート風背景）
    "card":        "#fefcf8",   # クリーム白（カード）
    "border":      "#d8d0c4",   # 砂色ボーダー
    "header_from": "#2d5a27",   # 深い森緑（ヘッダーグラデ開始）
    "header_to":   "#4a7a3a",   # シダ緑（ヘッダーグラデ終端）
    "primary":     "#2d5a27",   # 森緑（見出し・アクセント）
    "accent":      "#c8a84b",   # 琥珀ゴールド（ラベル・強調）
    "text":        "#2c2820",   # 温かいほぼ黒（本文）
    "muted":       "#6b5e52",   # ウォームグレー（サブテキスト）
    "pale":        "#eef3eb",   # 薄い葉色（番号サークル bg）
    "white":       "#fefcf8",   # クリーム白
    "rule":        "#c8b89a",   # 横罫線色
}

# ─────────────────────────────────────────────
#  カテゴリ別アイコン定義
# ─────────────────────────────────────────────
CATEGORY_ICONS = {
    "飼育日誌":       "🐾",
    "季節トピック":   "🌸",
    "飼育ノウハウ":   "🔧",
    "生態系ニュース": "📰",
    "種別図鑑":       "📖",
    "自然環境":       "🌿",
    "水族館":         "🐠",
    "保全生物学":     "🛡️",
    "獣医学":         "🩺",
    "生物学":         "🔬",
    "生態学":         "🌲",
    "植物学":         "🌺",
    "生物分類図鑑":   "🦋",
    "環境問題":       "🌍",
    "動物園学":       "🏛️",
    "フィールドワーク": "🔭",
    "求人情報":       "💼",
    "学術論文":       "📄",
    "default":        "🌿",
}

# ─────────────────────────────────────────────
#  ポイント番号アイコン（summary型用）
# ─────────────────────────────────────────────
POINT_ICONS = ["🌱", "🌿", "🍃", "🌾"]

# ─────────────────────────────────────────────
#  インフォグラフィック前後の説明文テンプレート
# ─────────────────────────────────────────────
WRAPPER_TEMPLATES = {
    "summary": {
        "before": "この記事のポイントを視覚的にまとめました。",
        "after":  "詳細は以下の本文をご覧ください。",
    },
    "comparison": {
        "before": "以下の比較図で主要な違いを整理しています。",
        "after":  "各項目の詳細は本文で解説しています。",
    },
    "timeline": {
        "before": "主な出来事を時系列でまとめました。",
        "after":  "各ステージの詳細は本文に記載しています。",
    },
    "chart": {
        "before": "記事中の主な数値をグラフで可視化しました。",
        "after":  "データの背景と解釈は本文をご参照ください。",
    },
    "steps": {
        "before": "プロセス全体の流れを図にまとめました。",
        "after":  "各ステップの詳細は本文で説明しています。",
    },
}


# ─────────────────────────────────────────────
#  ユーティリティ
# ─────────────────────────────────────────────

def read_article(filepath):
    with open(filepath, encoding="utf-8") as f:
        return f.read()


def extract_frontmatter(content):
    """フロントマターからメタ情報を抽出"""
    title_m = re.search(r'^title:\s*["\']?([^"\'\\n]+)["\']?', content, re.MULTILINE)
    tags_m   = re.findall(r'^\s+-\s+(.+)$', content[:600], re.MULTILINE)
    date_m   = re.search(r'^date:\s*(.+)$', content, re.MULTILINE)
    return {
        "title": (title_m.group(1).strip() if title_m else "記事"),
        "tags":  tags_m,
        "date":  (date_m.group(1).strip()[:10] if date_m else ""),
    }


def detect_category(tags):
    """タグからカテゴリアイコンを決定"""
    for tag in tags:
        for cat, icon in CATEGORY_ICONS.items():
            if cat in tag:
                return cat, icon
    return "default", CATEGORY_ICONS["default"]


def is_book_page(content, tags):
    """書籍・雑誌一覧ページかどうか判定"""
    for kw in BOOK_SKIP_KEYWORDS:
        if kw in content[:500]:
            return True
    for tag in tags:
        if "書籍" in tag or "購入" in tag:
            return True
    return False


# ─────────────────────────────────────────────
#  Gemini API
# ─────────────────────────────────────────────

def call_gemini(prompt, temperature=0.3, max_tokens=1024):
    """利用可能なモデルを順番に試してGemini APIを呼び出す"""
    if not API_KEY:
        return None
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}
    }).encode("utf-8")
    for model in MODELS:
        url = get_gemini_url(model)
        req = urllib.request.Request(
            url, data=body,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                print(f"  Gemini OK ({model})")
                return text
        except urllib.error.HTTPError as e:
            if e.code == 429:
                retry_after = 15
                try:
                    retry_after = int(e.headers.get("Retry-After", 15))
                except (TypeError, ValueError):
                    pass
                print(f"  モデル {model} レート制限 (429), {retry_after}秒待機...")
                time.sleep(retry_after)
                continue
            if e.code in (403, 404):
                print(f"  モデル {model} 利用不可 ({e.code}), 次を試します...")
                continue
            print(f"  HTTP エラー {e.code}: {e.read().decode('utf-8', errors='replace')}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"  エラー: {e}", file=sys.stderr)
            return None
    print("  全モデルが利用不可", file=sys.stderr)
    return None


# ─────────────────────────────────────────────
#  ローカル抽出（Gemini なしフォールバック）
# ─────────────────────────────────────────────

def local_extract_summary(content, title):
    """Gemini なしでマークダウンから要点を抽出するローカルフォールバック"""
    lines = content.split("\n")

    summary = ""
    in_fm, fm_done = False, False
    for line in lines:
        stripped = line.strip()
        if stripped == "---":
            if not in_fm:
                in_fm = True
            else:
                fm_done = True
            continue
        if fm_done and stripped and not stripped.startswith("#") and not stripped.startswith("!"):
            summary = stripped[:72]
            break
    if not summary:
        summary = title

    headings_with_idx = [
        (i, line.lstrip("#").strip())
        for i, line in enumerate(lines)
        if re.match(r'^#{2,3}\s', line)
    ]
    points = []
    for idx, h in headings_with_idx[:4]:
        label = h[:8]
        detail = ""
        for line in lines[idx + 1:idx + 5]:
            s = line.strip()
            if s and not s.startswith("#") and not s.startswith("!") and not s.startswith("|"):
                detail = s[:28]
                break
        points.append({"label": label, "text": detail})
    while len(points) < 4:
        points.append({"label": "詳細", "text": "記事本文をご覧ください"})

    stat_value, stat_label = "", ""
    for line in lines:
        m = re.search(r'(\d+(?:\.\d+)?)\s*([種件匹頭羽個万億%％km㎞℃])', line)
        if m:
            stat_value = m.group(0)[:15]
            stat_label = line.strip()[:12]
            break

    return {"summary": summary, "points": points, "stat_value": stat_value, "stat_label": stat_label}


def local_extract_comparison(content, title):
    """マークダウンテーブルから比較データを抽出"""
    lines = content.split("\n")
    table_rows = [l.strip() for l in lines if l.strip().startswith("|") and l.count("|") >= 2]
    subjects = []
    criteria = []

    if len(table_rows) >= 2:
        header = [c.strip() for c in table_rows[0].split("|") if c.strip()]
        if len(header) >= 3:
            subjects = [h[:14] for h in header[1:3]]
        data_rows = [r for r in table_rows[1:] if not re.match(r'^[\|\s\-:]+$', r)]
        for row in data_rows[:5]:
            cells = [c.strip() for c in row.split("|") if c.strip()]
            if len(cells) >= 3:
                criteria.append({"label": cells[0][:8], "values": [cells[1][:14], cells[2][:14]]})

    if not subjects:
        subjects = ["比較A", "比較B"]
    if not criteria:
        headings = [l.lstrip("#").strip() for l in lines if re.match(r'^#{2,3}\s', l)]
        for h in headings[:4]:
            criteria.append({"label": h[:8], "values": ["—", "—"]})
    while len(criteria) < 3:
        criteria.append({"label": "—", "values": ["—", "—"]})

    stat_value, stat_label = "", ""
    for line in lines:
        m = re.search(r'(\d+(?:\.\d+)?)\s*([種件匹頭羽個万億%％km㎞℃])', line)
        if m:
            stat_value = m.group(0)[:15]
            stat_label = line.strip()[:12]
            break

    return {
        "summary": title[:68],
        "subjects": subjects[:3],
        "criteria": criteria[:5],
        "stat_value": stat_value,
        "stat_label": stat_label,
    }


def local_extract_timeline(content, title):
    """年・日付パターンから時系列イベントを抽出"""
    lines = content.split("\n")
    events = []
    for line in lines:
        m = re.search(r'(\d{4}年(?:\d{1,2}月)?|\d{1,2}月\d{1,2}日)', line)
        if m:
            year = m.group(1)[:6]
            rest = line[m.end():].strip().lstrip("：:—-").strip()
            label = rest[:12] if rest else "出来事"
            text  = rest[:28] if rest else ""
            events.append({"year": year, "label": label, "text": text})
            if len(events) >= 6:
                break

    if len(events) < 3:
        headings = [l.lstrip("#").strip() for l in lines if re.match(r'^#{2,3}\s', l)]
        for h in headings[:6 - len(events)]:
            events.append({"year": "—", "label": h[:12], "text": ""})

    while len(events) < 4:
        events.append({"year": "—", "label": "詳細", "text": "本文参照"})

    stat_value, stat_label = "", ""
    for line in lines:
        m = re.search(r'(\d+(?:\.\d+)?)\s*([種件匹頭羽個万億%％km㎞℃])', line)
        if m:
            stat_value = m.group(0)[:15]
            stat_label = line.strip()[:12]
            break

    return {
        "summary": title[:68],
        "events": events[:6],
        "stat_value": stat_value,
        "stat_label": stat_label,
    }


def local_extract_chart(content, title):
    """数値+単位パターンから棒グラフデータを抽出"""
    lines = content.split("\n")
    bars = []
    for line in lines:
        m = re.search(r'(\d+(?:\.\d+)?)\s*([種件匹頭羽個万億%％km㎞℃])', line)
        if m:
            try:
                value = float(m.group(1))
                unit  = m.group(2)[:5]
                label = line.strip()[:10]
                bars.append({"label": label, "value": value, "unit": unit})
            except ValueError:
                pass
        if len(bars) >= 6:
            break

    if len(bars) < 3:
        bars = [
            {"label": "データA", "value": 1.0, "unit": "件"},
            {"label": "データB", "value": 1.0, "unit": "件"},
            {"label": "データC", "value": 1.0, "unit": "件"},
        ]

    stat_value = f"{bars[0]['value']:.0f}{bars[0]['unit']}" if bars else ""
    stat_label = bars[0]["label"][:12] if bars else ""

    return {
        "summary": title[:68],
        "chart_title": title[:20],
        "bars": bars[:6],
        "stat_value": stat_value,
        "stat_label": stat_label,
    }


def local_extract_steps(content, title):
    """順序付きリスト・見出しから手順データを抽出"""
    lines = content.split("\n")
    steps = []
    for line in lines:
        m = re.match(r'^(\d+)[.．]\s+(.+)', line.strip())
        if m:
            text = m.group(2).strip()
            steps.append({"number": int(m.group(1)), "label": text[:10], "text": text[:28]})
        if len(steps) >= 5:
            break

    if len(steps) < 3:
        headings = [l.lstrip("#").strip() for l in lines if re.match(r'^#{2,3}\s', l)]
        steps = [{"number": i+1, "label": h[:10], "text": ""} for i, h in enumerate(headings[:5])]

    while len(steps) < 4:
        steps.append({"number": len(steps)+1, "label": "詳細", "text": "記事本文を参照"})

    stat_value, stat_label = "", ""
    for line in lines:
        m = re.search(r'(\d+(?:\.\d+)?)\s*([種件匹頭羽個万億%％km㎞℃])', line)
        if m:
            stat_value = m.group(0)[:15]
            stat_label = line.strip()[:12]
            break

    return {
        "summary": title[:68],
        "steps": steps[:5],
        "stat_value": stat_value,
        "stat_label": stat_label,
    }


def local_extract_data(content, title, infographic_type):
    dispatch = {
        "summary":    local_extract_summary,
        "comparison": local_extract_comparison,
        "timeline":   local_extract_timeline,
        "chart":      local_extract_chart,
        "steps":      local_extract_steps,
    }
    return dispatch.get(infographic_type, local_extract_summary)(content, title)


# ─────────────────────────────────────────────
#  Gemini 抽出
# ─────────────────────────────────────────────

def _parse_gemini_json(raw_txt):
    if not raw_txt:
        return None
    m = re.search(r'\{[\s\S]*\}', raw_txt)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError as e:
            print(f"  JSON解析エラー: {e}", file=sys.stderr)
            print(f"  Gemini レスポンス (先頭200字): {raw_txt[:200]}", file=sys.stderr)
    return None


def gemini_extract_summary(content, title, tags):
    tags_str = ", ".join(tags[:5])
    prompt = f"""以下の記事を分析し、JSONで回答してください。

【タイトル】{title}
【タグ】{tags_str}
【記事冒頭】
{content[:1200]}

【出力形式（JSONのみ・コードブロック不要）】
{{
  "summary": "記事全体の一文要約（70字以内・日本語）",
  "points": [
    {{"label": "キーワード（8字以内）", "text": "説明（28字以内）"}},
    {{"label": "キーワード（8字以内）", "text": "説明（28字以内）"}},
    {{"label": "キーワード（8字以内）", "text": "説明（28字以内）"}},
    {{"label": "キーワード（8字以内）", "text": "説明（28字以内）"}}
  ],
  "stat_value": "記事の核心となる数値・年・種名など（15字以内）",
  "stat_label": "上記の説明（12字以内）"
}}

条件:
- 必ずpoints は4つ
- summary, points は記事内容を忠実に反映すること
- JSONのみ出力（前置き・説明不要）
"""
    return _parse_gemini_json(call_gemini(prompt, temperature=0.3, max_tokens=1024))


def gemini_extract_comparison(content, title, tags):
    tags_str = ", ".join(tags[:5])
    prompt = f"""以下の記事を分析し、JSONで回答してください。

【タイトル】{title}
【タグ】{tags_str}
【記事冒頭】
{content[:1200]}

【出力形式（JSONのみ・コードブロック不要）】
{{
  "summary": "記事全体の一文要約（70字以内）",
  "subjects": ["比較対象A（8字以内）", "比較対象B（8字以内）"],
  "criteria": [
    {{"label": "指標名（8字以内）", "values": ["A側の値（14字以内）", "B側の値（14字以内）"]}},
    {{"label": "指標名（8字以内）", "values": ["A側の値（14字以内）", "B側の値（14字以内）"]}},
    {{"label": "指標名（8字以内）", "values": ["A側の値（14字以内）", "B側の値（14字以内）"]}},
    {{"label": "指標名（8字以内）", "values": ["A側の値（14字以内）", "B側の値（14字以内）"]}}
  ],
  "stat_value": "核心となる数値（15字以内）",
  "stat_label": "上記の説明（12字以内）"
}}

条件:
- subjects は比較される2つの主体（施設名・手法名・種名など）
- criteria は比較する観点を3〜5項目
- JSONのみ出力
"""
    data = _parse_gemini_json(call_gemini(prompt, temperature=0.3, max_tokens=1024))
    if data and "subjects" in data and "criteria" in data:
        return data
    return None


def gemini_extract_timeline(content, title, tags):
    tags_str = ", ".join(tags[:5])
    prompt = f"""以下の記事を分析し、JSONで回答してください。

【タイトル】{title}
【タグ】{tags_str}
【記事冒頭】
{content[:1200]}

【出力形式（JSONのみ・コードブロック不要）】
{{
  "summary": "記事全体の一文要約（70字以内）",
  "events": [
    {{"year": "年・時期（6字以内）", "label": "出来事名（12字以内）", "text": "説明（28字以内）"}},
    {{"year": "年・時期（6字以内）", "label": "出来事名（12字以内）", "text": "説明（28字以内）"}},
    {{"year": "年・時期（6字以内）", "label": "出来事名（12字以内）", "text": "説明（28字以内）"}},
    {{"year": "年・時期（6字以内）", "label": "出来事名（12字以内）", "text": "説明（28字以内）"}}
  ],
  "stat_value": "核心となる数値（15字以内）",
  "stat_label": "上記の説明（12字以内）"
}}

条件:
- events は時系列順に4〜6件
- year は年号・月日など時点を示す文字列
- JSONのみ出力
"""
    data = _parse_gemini_json(call_gemini(prompt, temperature=0.3, max_tokens=1024))
    if data and "events" in data and len(data["events"]) >= 2:
        return data
    return None


def gemini_extract_chart(content, title, tags):
    tags_str = ", ".join(tags[:5])
    prompt = f"""以下の記事を分析し、JSONで回答してください。

【タイトル】{title}
【タグ】{tags_str}
【記事冒頭】
{content[:1200]}

【出力形式（JSONのみ・コードブロック不要）】
{{
  "summary": "記事全体の一文要約（70字以内）",
  "chart_title": "グラフのテーマ（20字以内）",
  "bars": [
    {{"label": "ラベル（10字以内）", "value": 数値, "unit": "単位（5字以内）"}},
    {{"label": "ラベル（10字以内）", "value": 数値, "unit": "単位（5字以内）"}},
    {{"label": "ラベル（10字以内）", "value": 数値, "unit": "単位（5字以内）"}}
  ],
  "stat_value": "核心となる数値（15字以内）",
  "stat_label": "上記の説明（12字以内）"
}}

条件:
- bars の value は必ず数値（float/int）、文字列にしないこと
- bars は3〜6件
- JSONのみ出力
"""
    data = _parse_gemini_json(call_gemini(prompt, temperature=0.3, max_tokens=1024))
    if data and "bars" in data and len(data["bars"]) >= 2:
        valid_bars = []
        for bar in data["bars"]:
            try:
                bar["value"] = float(bar["value"])
                valid_bars.append(bar)
            except (TypeError, ValueError):
                pass
        if len(valid_bars) >= 2:
            data["bars"] = valid_bars
            return data
    return None


def gemini_extract_steps(content, title, tags):
    tags_str = ", ".join(tags[:5])
    prompt = f"""以下の記事を分析し、JSONで回答してください。

【タイトル】{title}
【タグ】{tags_str}
【記事冒頭】
{content[:1200]}

【出力形式（JSONのみ・コードブロック不要）】
{{
  "summary": "記事全体の一文要約（70字以内）",
  "steps": [
    {{"number": 1, "label": "ステップ名（10字以内）", "text": "説明（28字以内）"}},
    {{"number": 2, "label": "ステップ名（10字以内）", "text": "説明（28字以内）"}},
    {{"number": 3, "label": "ステップ名（10字以内）", "text": "説明（28字以内）"}},
    {{"number": 4, "label": "ステップ名（10字以内）", "text": "説明（28字以内）"}}
  ],
  "stat_value": "核心となる数値（15字以内）",
  "stat_label": "上記の説明（12字以内）"
}}

条件:
- steps は4〜5件・手順順
- number は整数
- JSONのみ出力
"""
    data = _parse_gemini_json(call_gemini(prompt, temperature=0.3, max_tokens=1024))
    if data and "steps" in data and len(data["steps"]) >= 3:
        return data
    return None


def gemini_extract_data(content, title, tags, infographic_type):
    dispatch = {
        "summary":    gemini_extract_summary,
        "comparison": gemini_extract_comparison,
        "timeline":   gemini_extract_timeline,
        "chart":      gemini_extract_chart,
        "steps":      gemini_extract_steps,
    }
    return dispatch.get(infographic_type, gemini_extract_summary)(content, title, tags)


# ─────────────────────────────────────────────
#  型検出
# ─────────────────────────────────────────────

def gemini_detect_type(content, title, tags):
    """Gemini に記事の最適なインフォグラフィック種別を判定させる"""
    tags_str = ", ".join(tags[:4])
    prompt = f"""以下の記事を分析し、最適なインフォグラフィックの種類を1語で回答してください。

【タイトル】{title}
【タグ】{tags_str}
【記事冒頭300字】
{content[:300]}

【選択肢】
- summary    : 一般的な要点まとめ（デフォルト）
- comparison : 2〜3つの対象を複数の指標で比較する記事
- timeline   : 出来事・歴史・変遷が時系列で並ぶ記事
- chart      : 3件以上の数値データを棒グラフで示せる記事
- steps      : 手順・工程・プロセスが順番に説明される記事

【回答形式】
上記5語のうち1語のみ。理由・説明不要。
"""
    raw = call_gemini(prompt, temperature=0.1, max_tokens=16)
    if raw:
        candidate = raw.strip().lower()
        if candidate in VALID_TYPES:
            return candidate
        for t in VALID_TYPES:
            if t in candidate:
                return t
    return None


def detect_infographic_type(content, tags, title, forced_type=None):
    """記事に最適なインフォグラフィック種別を判定する。
    優先順位: forced_type → キーワード判定 → Gemini → 'summary'
    """
    if forced_type and forced_type in VALID_TYPES:
        return forced_type

    combined = title + " " + " ".join(tags) + " " + content[:800]

    # 時系列型キーワード
    if any(kw in combined for kw in ["年史", "歴史", "変遷", "年表", "経緯", "沿革", "発展史"]):
        return "timeline"

    # 比較型キーワード（テーブルも必要）
    has_comparison_kw = any(kw in combined for kw in ["比較", "対比", "vs", "VS", "飼育下と野生", "との差", "と比べ"])
    has_table = any("|" in line and line.count("|") >= 2 for line in content.split("\n"))
    if has_comparison_kw and has_table:
        return "comparison"

    # 数値グラフ型キーワード
    num_lines = sum(
        1 for line in content.split("\n")
        if re.search(r'\d+(?:\.\d+)?\s*[種件匹頭羽個万億%％km㎞℃]', line)
    )
    if num_lines >= 3 or any(kw in combined for kw in ["統計", "割合", "推移", "件数", "頭数"]):
        return "chart"

    # 手順型キーワード
    ordered_items = sum(1 for line in content.split("\n") if re.match(r'^\d+[.．]\s', line.strip()))
    if ordered_items >= 3 or any(kw in combined for kw in ["手順", "工程", "ステップ", "フロー", "進め方", "やり方"]):
        return "steps"

    # Gemini で判定
    gemini_type = gemini_detect_type(content, title, tags)
    if gemini_type:
        return gemini_type

    return "summary"


# ─────────────────────────────────────────────
#  SVG テキスト折り返し（CJK 全角幅対応）
# ─────────────────────────────────────────────

def _display_width(text):
    """CJK全角文字を幅2、それ以外を幅1として表示幅を計算する"""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def wrap_text_svg(text, max_width=28):
    """SVG用に長いテキストを表示幅ベースで2行に分割（CJK全角対応）"""
    if _display_width(text) <= max_width:
        return [text]
    current_width = 0
    cut = len(text)
    for i, ch in enumerate(text):
        current_width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
        if current_width > max_width:
            cut = i
            break
    for i in range(cut, max(0, cut - 4), -1):
        if i < len(text) and text[i] in "。、 　・,":
            cut = i + 1
            break
    return [text[:cut], text[cut:]]


# ─────────────────────────────────────────────
#  SVG 共有ヘルパー
# ─────────────────────────────────────────────

def _svg_open(W, H):
    """SVG開始タグ・defs・背景・横罫線・葉装飾を返す"""
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" font-family="\'Noto Serif JP\',\'Noto Sans JP\','
        f'\'Hiragino Kaku Gothic ProN\',sans-serif">',
        '<defs>',
        '  <filter id="shadow" x="-10%" y="-10%" width="120%" height="130%">',
        '    <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000" flood-opacity="0.06"/>',
        '  </filter>',
        '  <linearGradient id="gradHeader" x1="0%" y1="0%" x2="100%" y2="0%">',
        f'    <stop offset="0%" style="stop-color:{COLORS["header_from"]};stop-opacity:1" />',
        f'    <stop offset="100%" style="stop-color:{COLORS["header_to"]};stop-opacity:1" />',
        '  </linearGradient>',
        '</defs>',
        f'<rect width="{W}" height="{H}" fill="{COLORS["bg"]}"/>',
    ]
    for rule_y in range(76, H, 24):
        lines.append(
            f'<line x1="0" y1="{rule_y}" x2="{W}" y2="{rule_y}" '
            f'stroke="{COLORS["rule"]}" stroke-width="0.5" opacity="0.18"/>'
        )
    lines += [
        f'<path d="M{W-20} 72 C{W-60} 72 {W-90} 100 {W-80} 130 '
        f'C{W-70} 160 {W-20} 150 {W-20} 130 Z" '
        f'fill="{COLORS["primary"]}" opacity="0.06"/>',
        f'<path d="M{W-20} 130 L{W-55} 100" '
        f'stroke="{COLORS["primary"]}" stroke-width="0.8" opacity="0.06"/>',
    ]
    return lines


def _svg_header_band(W, category, cat_icon, date_str):
    """森緑グラデーションヘッダー帯を返す"""
    e = html.escape
    return [
        f'<rect x="0" y="0" width="{W}" height="64" fill="url(#gradHeader)"/>',
        f'<text x="22" y="32" font-size="22" dominant-baseline="middle">{e(cat_icon)}</text>',
        f'<text x="54" y="32" font-size="13" fill="{COLORS["white"]}" '
        f'font-weight="600" dominant-baseline="middle" letter-spacing="0.06em">'
        f'{e(category)}</text>',
        f'<text x="{W-22}" y="26" font-size="11" fill="rgba(255,255,255,0.65)" '
        f'text-anchor="end">{e(date_str)}</text>',
        f'<text x="{W-22}" y="44" font-size="9" fill="{COLORS["accent"]}" '
        f'text-anchor="end" font-weight="700" letter-spacing="0.05em">ZOO KNOWLEDGE VAULT</text>',
    ]


def _svg_footer_band(W, H, stat_value, stat_label):
    """薄葉色フッター帯を返す"""
    e = html.escape
    footer_y = H - 56
    stat_v = (stat_value or "—")[:15]
    stat_l = (stat_label or "注目データ")[:16]
    return [
        f'<rect x="20" y="{footer_y}" width="{W - 40}" height="40" '
        f'fill="{COLORS["pale"]}" rx="8" stroke="{COLORS["border"]}" stroke-width="0.5"/>',
        f'<text x="40" y="{footer_y + 22}" font-size="10" fill="{COLORS["primary"]}" '
        f'font-weight="700" dominant-baseline="middle" letter-spacing="0.04em">'
        f'{e(stat_l)}</text>',
        f'<text x="{W - 40}" y="{footer_y + 22}" font-size="16" fill="{COLORS["text"]}" '
        f'font-weight="700" text-anchor="end" dominant-baseline="middle">{e(stat_v)}</text>',
    ]


def _svg_title_card(W, title, summary, card_y=82, card_h=90):
    """クリーム白タイトルカード（琥珀アクセント上部バー・サマリー付き）を返す"""
    e = html.escape
    title_lines = wrap_text_svg(title, 32)
    lines = [
        f'<rect x="20" y="{card_y}" width="{W-40}" height="{card_h}" fill="{COLORS["card"]}" '
        f'rx="10" filter="url(#shadow)" stroke="{COLORS["border"]}" stroke-width="0.5"/>',
        f'<rect x="20" y="{card_y}" width="{W-40}" height="3" fill="{COLORS["accent"]}" rx="10"/>',
    ]
    title_base_y = card_y + 30
    for i, line in enumerate(title_lines[:2]):
        lines.append(
            f'<text x="40" y="{title_base_y + i * 26}" font-size="20" fill="{COLORS["text"]}" '
            f'font-weight="700" letter-spacing="0.01em">{e(line)}</text>'
        )
    if summary and card_h >= 80:
        summary_y = card_y + card_h - 16
        summary_txt = (summary or "")[:68]
        lines += [
            f'<rect x="40" y="{summary_y - 12}" width="3" height="16" fill="{COLORS["primary"]}" rx="2"/>',
            f'<text x="52" y="{summary_y}" font-size="11" fill="{COLORS["muted"]}" '
            f'font-weight="500">{e(summary_txt)}</text>',
        ]
    return lines


# ─────────────────────────────────────────────
#  SVG ビルダー
# ─────────────────────────────────────────────

def build_svg_summary(data, title, category, cat_icon, date_str):
    """要約型: ヘッダー + タイトルカード + 4ポイントカード + フッター"""
    W, H = 800, 500
    e = html.escape

    summary    = data.get("summary", "")
    points     = (data.get("points") or [])[:4]
    stat_value = data.get("stat_value", "")
    stat_label = data.get("stat_label", "")

    while len(points) < 4:
        points.append({"label": "—", "text": ""})

    title_lines = wrap_text_svg(title, 32)
    gap    = 14
    card_w = (W - gap * 5) // 4
    card_y = 232
    card_h = 168

    svg_lines = _svg_open(W, H)
    svg_lines += _svg_header_band(W, category, cat_icon, date_str)

    # タイトルカード（summary型専用・高さ130）
    svg_lines += [
        f'<rect x="20" y="82" width="{W-40}" height="130" fill="{COLORS["card"]}" '
        f'rx="10" filter="url(#shadow)" stroke="{COLORS["border"]}" stroke-width="0.5"/>',
        f'<rect x="20" y="82" width="{W-40}" height="3" fill="{COLORS["accent"]}" rx="10"/>',
    ]
    title_base_y = 118
    for i, line in enumerate(title_lines[:2]):
        svg_lines.append(
            f'<text x="40" y="{title_base_y + i * 30}" font-size="22" fill="{COLORS["text"]}" '
            f'font-weight="700" letter-spacing="0.01em">{e(line)}</text>'
        )
    summary_txt = (summary or "")[:68]
    svg_lines += [
        f'<rect x="40" y="174" width="3" height="20" fill="{COLORS["primary"]}" rx="2"/>',
        f'<text x="52" y="188" font-size="12" fill="{COLORS["muted"]}" '
        f'font-weight="500" letter-spacing="0.01em">{e(summary_txt)}</text>',
    ]

    # ポイントカード 4枚
    for i, pt in enumerate(points):
        cx = gap + i * (card_w + gap)
        label_text   = (pt.get("label") or "")[:10]
        detail_lines = wrap_text_svg((pt.get("text") or "")[:35], 20)
        svg_lines += [
            f'<rect x="{cx}" y="{card_y}" width="{card_w}" height="{card_h}" '
            f'fill="{COLORS["card"]}" rx="10" filter="url(#shadow)" '
            f'stroke="{COLORS["border"]}" stroke-width="0.5"/>',
            f'<rect x="{cx}" y="{card_y}" width="{card_w}" height="3" '
            f'fill="{COLORS["accent"]}" rx="10"/>',
            f'<circle cx="{cx + 28}" cy="{card_y + 34}" r="15" fill="{COLORS["pale"]}" '
            f'stroke="{COLORS["border"]}" stroke-width="0.5"/>',
            f'<text x="{cx + 28}" y="{card_y + 35}" font-size="13" fill="{COLORS["primary"]}" '
            f'font-weight="700" text-anchor="middle" dominant-baseline="middle">{i+1}</text>',
            f'<text x="{cx + 50}" y="{card_y + 34}" font-size="13" fill="{COLORS["text"]}" '
            f'font-weight="700" dominant-baseline="middle">{e(label_text)}</text>',
        ]
        for j, d_line in enumerate(detail_lines[:3]):
            svg_lines.append(
                f'<text x="{cx + 16}" y="{card_y + 70 + j * 19}" font-size="11" '
                f'fill="{COLORS["muted"]}">{e(d_line)}</text>'
            )

    svg_lines += _svg_footer_band(W, H, stat_value, stat_label)
    svg_lines.append('</svg>')
    return "\n".join(svg_lines)


def build_svg_comparison(data, title, category, cat_icon, date_str):
    """比較表型: ヘッダー + タイトルカード + 比較テーブル + フッター"""
    W, H = 800, 500
    e = html.escape

    summary    = data.get("summary", "")
    subjects   = (data.get("subjects") or ["A", "B"])[:3]
    criteria   = (data.get("criteria") or [])[:5]
    stat_value = data.get("stat_value", "")
    stat_label = data.get("stat_label", "")

    while len(criteria) < 3:
        criteria.append({"label": "—", "values": ["—"] * len(subjects)})

    svg_lines = _svg_open(W, H)
    svg_lines += _svg_header_band(W, category, cat_icon, date_str)
    svg_lines += _svg_title_card(W, title, summary, card_y=82, card_h=90)

    # 比較テーブル
    table_y  = 185
    header_h = 30
    row_h    = min(38, (H - 56 - table_y - header_h - 8) // max(len(criteria), 1))
    label_w  = 170
    n_subj   = len(subjects)
    val_w    = (W - 40 - label_w) // n_subj
    table_h  = header_h + row_h * len(criteria)

    # 外枠 + 左琥珀アクセント
    svg_lines += [
        f'<rect x="20" y="{table_y}" width="{W-40}" height="{table_h}" '
        f'fill="none" stroke="{COLORS["border"]}" stroke-width="1" rx="4"/>',
        f'<rect x="20" y="{table_y}" width="3" height="{table_h}" '
        f'fill="{COLORS["accent"]}" rx="2"/>',
    ]

    # ヘッダー行
    svg_lines.append(
        f'<rect x="20" y="{table_y}" width="{label_w}" height="{header_h}" '
        f'fill="{COLORS["pale"]}" rx="4"/>'
    )
    for si, subj in enumerate(subjects):
        sx = 20 + label_w + si * val_w
        svg_lines += [
            f'<rect x="{sx}" y="{table_y}" width="{val_w}" height="{header_h}" '
            f'fill="{COLORS["primary"]}" opacity="0.85"/>',
            f'<text x="{sx + val_w // 2}" y="{table_y + header_h // 2}" '
            f'font-size="12" fill="{COLORS["white"]}" font-weight="700" '
            f'text-anchor="middle" dominant-baseline="middle">{e(subj[:14])}</text>',
        ]

    # データ行
    for ri, crit in enumerate(criteria):
        ry       = table_y + header_h + ri * row_h
        row_fill = COLORS["card"] if ri % 2 == 0 else COLORS["bg"]
        svg_lines += [
            f'<rect x="20" y="{ry}" width="{W-40}" height="{row_h}" fill="{row_fill}"/>',
            f'<line x1="20" y1="{ry}" x2="{W-20}" y2="{ry}" '
            f'stroke="{COLORS["border"]}" stroke-width="0.5"/>',
            f'<text x="28" y="{ry + row_h // 2}" font-size="12" fill="{COLORS["text"]}" '
            f'font-weight="600" dominant-baseline="middle">'
            f'{e((crit.get("label") or "")[:8])}</text>',
        ]
        vals = crit.get("values") or []
        for si in range(n_subj):
            sx      = 20 + label_w + si * val_w
            val_txt = (vals[si] if si < len(vals) else "—")[:14]
            svg_lines.append(
                f'<text x="{sx + val_w // 2}" y="{ry + row_h // 2}" '
                f'font-size="11" fill="{COLORS["muted"]}" '
                f'text-anchor="middle" dominant-baseline="middle">{e(val_txt)}</text>'
            )

    svg_lines += _svg_footer_band(W, H, stat_value, stat_label)
    svg_lines.append('</svg>')
    return "\n".join(svg_lines)


def build_svg_timeline(data, title, category, cat_icon, date_str):
    """時系列型: ヘッダー + タイトルカード + 水平タイムライン + フッター"""
    W, H = 800, 500
    e = html.escape

    summary    = data.get("summary", "")
    events     = (data.get("events") or [])[:6]
    stat_value = data.get("stat_value", "")
    stat_label = data.get("stat_label", "")

    while len(events) < 4:
        events.append({"year": "—", "label": "詳細", "text": "本文参照"})

    svg_lines = _svg_open(W, H)
    svg_lines += _svg_header_band(W, category, cat_icon, date_str)
    svg_lines += _svg_title_card(W, title, summary, card_y=82, card_h=90)

    # タイムラインスパイン
    spine_y = 260
    spine_x1, spine_x2 = 50, 750
    n = len(events)
    if n == 1:
        positions = [(spine_x1 + spine_x2) // 2]
    else:
        positions = [spine_x1 + i * (spine_x2 - spine_x1) // (n - 1) for i in range(n)]

    svg_lines.append(
        f'<line x1="{spine_x1}" y1="{spine_y}" x2="{spine_x2}" y2="{spine_y}" '
        f'stroke="{COLORS["primary"]}" stroke-width="2" opacity="0.35"/>'
    )

    for i, (ev, cx) in enumerate(zip(events, positions)):
        year  = (ev.get("year")  or "")[:6]
        label = (ev.get("label") or "")[:12]
        text  = (ev.get("text")  or "")[:28]
        above = (i % 2 == 0)

        # ノード（外円 + 内点）
        svg_lines += [
            f'<circle cx="{cx}" cy="{spine_y}" r="10" fill="{COLORS["pale"]}" '
            f'stroke="{COLORS["primary"]}" stroke-width="2"/>',
            f'<circle cx="{cx}" cy="{spine_y}" r="4" fill="{COLORS["primary"]}"/>',
        ]

        if above:
            svg_lines += [
                f'<text x="{cx}" y="{spine_y - 18}" font-size="10" fill="{COLORS["accent"]}" '
                f'font-weight="700" text-anchor="middle">{e(year)}</text>',
                f'<text x="{cx}" y="{spine_y - 36}" font-size="11" fill="{COLORS["primary"]}" '
                f'font-weight="700" text-anchor="middle">{e(label)}</text>',
            ]
            text_lines = wrap_text_svg(text, 14)
            for j, tl in enumerate(text_lines[:2]):
                svg_lines.append(
                    f'<text x="{cx}" y="{spine_y - 54 - j * 14}" font-size="9" '
                    f'fill="{COLORS["muted"]}" text-anchor="middle">{e(tl)}</text>'
                )
        else:
            svg_lines += [
                f'<text x="{cx}" y="{spine_y + 22}" font-size="10" fill="{COLORS["accent"]}" '
                f'font-weight="700" text-anchor="middle">{e(year)}</text>',
                f'<text x="{cx}" y="{spine_y + 38}" font-size="11" fill="{COLORS["primary"]}" '
                f'font-weight="700" text-anchor="middle">{e(label)}</text>',
            ]
            text_lines = wrap_text_svg(text, 14)
            for j, tl in enumerate(text_lines[:2]):
                svg_lines.append(
                    f'<text x="{cx}" y="{spine_y + 56 + j * 14}" font-size="9" '
                    f'fill="{COLORS["muted"]}" text-anchor="middle">{e(tl)}</text>'
                )

    svg_lines += _svg_footer_band(W, H, stat_value, stat_label)
    svg_lines.append('</svg>')
    return "\n".join(svg_lines)


def build_svg_chart(data, title, category, cat_icon, date_str):
    """数値グラフ型: ヘッダー + タイトルカード + 棒グラフ + フッター"""
    W, H = 800, 500
    e = html.escape

    summary     = data.get("summary", "")
    chart_title = (data.get("chart_title") or title)[:20]
    bars        = (data.get("bars") or [])[:6]
    stat_value  = data.get("stat_value", "")
    stat_label  = data.get("stat_label", "")

    try:
        max_val = max(float(b.get("value", 0)) for b in bars) if bars else 1.0
    except (TypeError, ValueError):
        max_val = 1.0
    if max_val <= 0:
        max_val = 1.0

    svg_lines = _svg_open(W, H)
    svg_lines += _svg_header_band(W, category, cat_icon, date_str)
    svg_lines += _svg_title_card(W, title, summary, card_y=82, card_h=80)

    # グラフエリア
    y_axis_x   = 70
    x_axis_y   = 415
    chart_top  = 188
    chart_h_px = x_axis_y - chart_top  # = 227

    # グラフタイトル
    svg_lines.append(
        f'<text x="{W // 2}" y="{chart_top - 6}" font-size="11" fill="{COLORS["accent"]}" '
        f'font-weight="700" text-anchor="middle">{e(chart_title)}</text>'
    )

    # 軸
    svg_lines += [
        f'<line x1="{y_axis_x}" y1="{chart_top}" x2="{y_axis_x}" y2="{x_axis_y}" '
        f'stroke="{COLORS["border"]}" stroke-width="1"/>',
        f'<line x1="{y_axis_x}" y1="{x_axis_y}" x2="{W-20}" y2="{x_axis_y}" '
        f'stroke="{COLORS["border"]}" stroke-width="1"/>',
    ]

    # グリッド線
    for pct in [0.33, 0.66, 1.0]:
        gy = x_axis_y - int(chart_h_px * pct)
        gv = max_val * pct
        svg_lines += [
            f'<line x1="{y_axis_x}" y1="{gy}" x2="{W-20}" y2="{gy}" '
            f'stroke="{COLORS["border"]}" stroke-width="0.5" stroke-dasharray="4,4" opacity="0.6"/>',
            f'<text x="{y_axis_x - 4}" y="{gy}" font-size="9" fill="{COLORS["muted"]}" '
            f'text-anchor="end" dominant-baseline="middle">{gv:.0f}</text>',
        ]

    # バー
    if bars:
        chart_w    = W - 20 - y_axis_x
        n          = len(bars)
        bar_w      = min(70, (chart_w // n) - 10)
        bar_spc    = (chart_w - bar_w * n) // (n + 1)

        for i, bar in enumerate(bars):
            try:
                bv = float(bar.get("value", 0))
            except (TypeError, ValueError):
                bv = 0.0
            unit  = (bar.get("unit")  or "")[:5]
            label = (bar.get("label") or "")[:10]
            bh    = int((bv / max_val) * chart_h_px)
            bx    = y_axis_x + bar_spc + i * (bar_w + bar_spc)
            by    = x_axis_y - bh

            svg_lines += [
                f'<rect x="{bx}" y="{by}" width="{bar_w}" height="{bh}" '
                f'fill="{COLORS["primary"]}" opacity="0.72" rx="3"/>',
                f'<text x="{bx + bar_w // 2}" y="{by - 5}" font-size="10" fill="{COLORS["text"]}" '
                f'font-weight="700" text-anchor="middle">{e(f"{bv:.0f}{unit}")}</text>',
                f'<text x="{bx + bar_w // 2}" y="{x_axis_y + 14}" font-size="10" '
                f'fill="{COLORS["muted"]}" text-anchor="middle">{e(label)}</text>',
            ]

    svg_lines += _svg_footer_band(W, H, stat_value, stat_label)
    svg_lines.append('</svg>')
    return "\n".join(svg_lines)


def build_svg_steps(data, title, category, cat_icon, date_str):
    """手順・工程型: ヘッダー + タイトルカード + 縦ステップ + フッター"""
    W, H = 800, 500
    e = html.escape

    summary    = data.get("summary", "")
    steps      = (data.get("steps") or [])[:5]
    stat_value = data.get("stat_value", "")
    stat_label = data.get("stat_label", "")

    while len(steps) < 4:
        steps.append({"number": len(steps)+1, "label": "詳細", "text": "記事本文を参照してください"})

    n_steps = len(steps)
    step_h  = 55 if n_steps <= 4 else 43

    svg_lines = _svg_open(W, H)
    svg_lines += _svg_header_band(W, category, cat_icon, date_str)
    svg_lines += _svg_title_card(W, title, summary, card_y=82, card_h=90)

    # 縦スパイン
    spine_x   = 56
    steps_top = 186
    last_cy   = steps_top + (n_steps - 1) * step_h + 22
    svg_lines.append(
        f'<line x1="{spine_x}" y1="{steps_top + 22}" x2="{spine_x}" y2="{last_cy}" '
        f'stroke="{COLORS["primary"]}" stroke-width="2" opacity="0.25"/>'
    )

    for i, step in enumerate(steps):
        sy    = steps_top + i * step_h
        cy    = sy + 22
        num   = step.get("number", i+1)
        label = (step.get("label") or "")[:10]
        text  = (step.get("text")  or "")[:32]

        svg_lines += [
            f'<circle cx="{spine_x}" cy="{cy}" r="16" fill="{COLORS["primary"]}"/>',
            f'<text x="{spine_x}" y="{cy}" font-size="13" fill="{COLORS["white"]}" '
            f'font-weight="700" text-anchor="middle" dominant-baseline="middle">{num}</text>',
            f'<text x="82" y="{sy + 16}" font-size="13" fill="{COLORS["text"]}" '
            f'font-weight="700">{e(label)}</text>',
        ]
        text_lines = wrap_text_svg(text, 50)
        for j, tl in enumerate(text_lines[:2]):
            svg_lines.append(
                f'<text x="82" y="{sy + 34 + j * 14}" font-size="11" '
                f'fill="{COLORS["muted"]}">{e(tl)}</text>'
            )
        if i < n_steps - 1:
            svg_lines.append(
                f'<line x1="78" y1="{sy + step_h - 4}" x2="{W-20}" '
                f'y2="{sy + step_h - 4}" stroke="{COLORS["rule"]}" '
                f'stroke-width="0.5" opacity="0.5"/>'
            )

    svg_lines += _svg_footer_band(W, H, stat_value, stat_label)
    svg_lines.append('</svg>')
    return "\n".join(svg_lines)


def build_svg_for_type(infographic_type, data, title, category, cat_icon, date_str):
    """型に応じたSVGビルダーをディスパッチする"""
    builders = {
        "summary":    build_svg_summary,
        "comparison": build_svg_comparison,
        "timeline":   build_svg_timeline,
        "chart":      build_svg_chart,
        "steps":      build_svg_steps,
    }
    fn = builders.get(infographic_type, build_svg_summary)
    return fn(data=data, title=title, category=category, cat_icon=cat_icon, date_str=date_str)


# ─────────────────────────────────────────────
#  参考URL収集
# ─────────────────────────────────────────────

def search_references(title, tags):
    """Gemini で参考URLを収集"""
    tags_str = " ".join(tags[:4])
    prompt = f"""以下のトピックに関連する、実在する信頼性の高いウェブサイトのURLを5件提示してください。

トピック: {title} {tags_str}

【重要な制約】
- 実際に存在するURLのみを記載してください
- 存在するか不確かなURLは絶対に記載しないでください
- 架空・推測・生成したURLは禁止です
- 不確かな場合はそのURLを省略してください
- 動物園・自然環境・保全に関する公的機関・研究機関・専門団体のサイトのみ
  (例: JAZA、環境省、IUCN、大学研究室、国立機関)
- 形式（1行1件）: - [サイト名](URL): 説明
"""
    result = call_gemini(prompt, temperature=0.2, max_tokens=800)
    if result:
        print("  注意: AIが生成したURLは実在しない場合があります。公開前にリンクを手動で確認してください。")
    return result


# ─────────────────────────────────────────────
#  記事への挿入
# ─────────────────────────────────────────────

def insert_into_article(filepath, svg_filename, references_text, infographic_type="summary", summary=""):
    """記事ファイルにインフォグラフィックと参考URLを挿入（冪等）"""
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    wrapper = WRAPPER_TEMPLATES.get(infographic_type, WRAPPER_TEMPLATES["summary"])
    infographic_section = (
        f"\n\n## インフォグラフィック\n\n"
        f"{wrapper['before']}\n\n"
        f"![[{svg_filename}]]\n\n"
        f"{wrapper['after']}\n"
    )

    ref_section = (
        f"\n## 参考・引用元\n\n"
        f"{references_text}\n"
    )

    fm_end     = content.find("---", 3)
    insert_pos = (fm_end + 3) if fm_end != -1 else 0

    if "## インフォグラフィック" in content:
        new_content = re.sub(
            r'\n## インフォグラフィック[\s\S]*?(?=\n## |\Z)',
            infographic_section,
            content
        )
    else:
        new_content = content[:insert_pos] + infographic_section + content[insert_pos:]

    # 参考URLが取得できた場合のみ、参考セクションを置換する。
    # 取得できなかった場合は既存の参考セクションを保持して内容劣化を防ぐ。
    if references_text:
        if "## 参考" in new_content or "## 情報源" in new_content:
            new_content = re.sub(
                r'\n## (参考|情報源)[\s\S]*$', ref_section, new_content
            )
        else:
            new_content = new_content.rstrip() + "\n" + ref_section

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"  記事更新: {filepath}")


# ─────────────────────────────────────────────
#  引数解析
# ─────────────────────────────────────────────

def parse_args():
    """(filepath, skip_books, forced_type) を返す"""
    argv       = sys.argv[1:]
    filepath   = None
    skip_books = True
    forced_type = None
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--no-skip-books":
            skip_books = False
        elif arg == "--type" and i + 1 < len(argv):
            candidate = argv[i + 1].lower()
            if candidate in VALID_TYPES:
                forced_type = candidate
            else:
                print(
                    f"警告: 不明な --type 値 '{candidate}'. "
                    f"有効値: {', '.join(sorted(VALID_TYPES))}",
                    file=sys.stderr
                )
            i += 1
        elif not arg.startswith("--"):
            filepath = arg
        i += 1
    return filepath, skip_books, forced_type


# ─────────────────────────────────────────────
#  エントリポイント
# ─────────────────────────────────────────────

def main():
    filepath, skip_books, forced_type = parse_args()

    if not filepath:
        print("使い方: python generate_infographic.py <記事ファイルパス> [--type TYPE] [--no-skip-books]")
        print("  --type: summary / comparison / timeline / chart / steps")
        sys.exit(1)

    if not os.path.exists(filepath):
        print(f"ファイルが見つかりません: {filepath}", file=sys.stderr)
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"処理中: {os.path.basename(filepath)}")

    content  = read_article(filepath)
    meta     = extract_frontmatter(content)
    title    = meta["title"]
    tags     = meta["tags"]
    date_str = meta["date"]

    if skip_books and is_book_page(content, tags):
        print("  スキップ: 書籍・雑誌一覧ページはインフォグラフィック対象外")
        sys.exit(0)

    print(f"  タイトル: {title}")
    print(f"  タグ: {', '.join(tags[:5])}")

    category, cat_icon = detect_category(tags)
    print(f"  カテゴリ: {category} {cat_icon}")

    # ── Step 1: 種別判定 ──
    print("  インフォグラフィック種別を判定中...")
    infographic_type = detect_infographic_type(content, tags, title, forced_type)
    print(f"  種別: {infographic_type}")

    # ── Step 2: データ抽出 ──
    print(f"  データを抽出中 (Gemini, type={infographic_type})...")
    data = gemini_extract_data(content, title, tags, infographic_type)
    if data:
        summary = data.get("summary", "")
        print(f"  要約: {summary[:50]}...")
    else:
        print("  ⚠ Gemini 利用不可 - ローカル解析にフォールバック")
        data    = local_extract_data(content, title, infographic_type)
        summary = data.get("summary", title)

    # ── Step 3: SVG生成 ──
    print(f"  SVGを構築中 (type={infographic_type})...")
    svg_content = build_svg_for_type(
        infographic_type=infographic_type,
        data=data,
        title=title,
        category=category,
        cat_icon=cat_icon,
        date_str=date_str,
    )

    os.makedirs(IMAGES_DIR, exist_ok=True)
    safe_name    = re.sub(r'[^\w\-]', '_', title)[:40]
    svg_filename = f"{safe_name}_infographic.svg"
    svg_path     = os.path.join(IMAGES_DIR, svg_filename)
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"  SVG保存: {svg_path}")

    # ── Step 4: 参考URL収集 ──
    print("  参考URL収集中 (Gemini)...")
    references = search_references(title, tags)

    # ── Step 5: 記事に挿入 ──
    insert_into_article(filepath, svg_filename, references or "", infographic_type, summary)

    print(f"完了: {svg_filename}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
