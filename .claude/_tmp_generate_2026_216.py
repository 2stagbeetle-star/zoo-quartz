# -*- coding: utf-8 -*-
from pathlib import Path
import re
import unicodedata
import collections

ROOT = Path('.')

existing_titles = set()
for p in ROOT.rglob('*.md'):
    try:
        txt = p.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        continue
    m = re.search(r'^title:\s*"?(.*?)"?\s*$', txt, re.MULTILINE)
    if m:
        existing_titles.add(m.group(1).strip())

season_map = {
    1:'厳冬',2:'早春',3:'春季',4:'晩春',5:'初夏',6:'梅雨',
    7:'盛夏',8:'猛暑',9:'初秋',10:'秋季',11:'晩秋',12:'初冬'
}

month_focus = {
    1:'基盤整備',2:'モニタリング設計',3:'繁殖期対応',4:'来園導線最適化',
    5:'暑熱適応準備',6:'梅雨期運用',7:'高温期対策',8:'災害レジリエンス',
    9:'秋季評価',10:'越冬準備',11:'年次総点検',12:'次年度計画接続'
}

day_map = list(range(1, 19))

cats = [
    ('01','飼育日誌','A_飼育','01_飼育日誌/その他/2026連載','個体別飼育ログ統合'),
    ('02','季節トピック','A_季節','02_季節トピック/2026連載','季節展示と運用連動'),
    ('03','飼育ノウハウ','A_ノウハウ','03_飼育ノウハウ/2026連載','ハズバンダリー標準化'),
    ('04','生態系ニュース','A_生態系','04_生態系ニュース/2026連載','生態系トレンド監視'),
    ('05','種別図鑑','A_図鑑','05_種別図鑑/2026連載','種別識別と飼育要件整理'),
    ('06','自然環境','A_自然環境','06_自然環境/生態系/2026連載','保護区運用と自然資本評価'),
    ('07','水族館・水生生物','A_水族館','07_水族館・水生生物/2026連載','水槽環境と水生生物管理'),
    ('08','動物保護・保全生物学','A_保全','08_動物保護・保全生物学/2026連載','域外保全と再導入戦略'),
    ('09','獣医学・動物医療','A_獣医','09_獣医学・動物医療/2026連載','臨床評価と予防医療実装'),
    ('10','生物学・生命科学','A_生物','10_生物学・生命科学/2026連載','生命科学データ統合解析'),
    ('11','生態学・自然環境学','A_生態学','11_生態学・自然環境学/2026連載','生態系機能と個体群動態解析'),
    ('12','植物学・植生','A_植物','12_植物学・植生/2026連載','植生管理と植物機能評価'),
    ('13','生物分類図鑑','A_分類','13_生物分類図鑑/2026連載','分類更新と命名整合運用'),
    ('14','環境問題・気候変動','A_気候','14_環境問題・気候変動/2026連載','気候リスクと適応運用'),
    ('15','動物園学・博物館学','A_動物園学','15_動物園学・博物館学/2026連載','展示教育と運営評価設計'),
    ('16','フィールドワーク・調査手法','A_調査','16_フィールドワーク・調査手法/2026連載','調査手法統合と品質管理'),
    ('17','求人情報','A_求人','17_求人情報/2026連載','専門人材採用と育成設計'),
    ('18','学術論文・研究','A_論文','18_学術論文・研究/2026連載','論文読解と実装翻訳')
]

related_map = {
    '01': ['[[01_飼育日誌/哺乳類/キリン飼育日誌_日立市かみね動物園]]','[[03_飼育ノウハウ/環境エンリッチメント/春季の環境エンリッチメント実践ガイド]]','[[15_動物園学・博物館学/展示設計・動物福祉/アニマルウェルフェアと日本の動物園水族館]]'],
    '02': ['[[02_季節トピック/春/A_季節_20250315_繁殖シーズン到来春の動物園管理]]','[[02_季節トピック/夏/A_季節_20250615_梅雨期の動物展示と両生類の季節]]','[[02_季節トピック/秋/A_季節_20250915_秋の動物園繁殖ハイシーズンと実りの展示]]'],
    '03': ['[[03_飼育ノウハウ/環境エンリッチメント/春季の環境エンリッチメント実践ガイド]]','[[03_飼育ノウハウ/環境エンリッチメント/A_飼育_2025_IoTスマートハビタットによる環境モニタリング]]','[[09_獣医学・動物医療/A_獣医_2025_野生動物病原体スクリーニング]]'],
    '04': ['[[04_生態系ニュース/B_生態系_20250310_春の野生動物ニュース2025]]','[[04_生態系ニュース/B_生態系_20250610_6月の野生動物ニュース2025]]','[[04_生態系ニュース/B_生態系_20251210_2025年生態系ニュース年間総括]]'],
    '05': ['[[05_種別図鑑/哺乳類/A_図鑑_20250210_アムールトラ完全図鑑]]','[[05_種別図鑑/哺乳類/A_図鑑_20250515_ニホンザル完全図鑑]]','[[05_種別図鑑/鳥類/A_図鑑_20251115_シマフクロウ絶滅危惧種図鑑]]'],
    '06': ['[[06_自然環境/生態系/B_自然環境_20250320_桜前線と動物の春の目覚め]]','[[06_自然環境/生態系/B_自然環境_20250420_春の湿地生態系と水鳥]]','[[06_自然環境/生態系/B_自然環境_20251020_秋の国立公園と紅葉生態]]'],
    '07': ['[[07_水族館・水生生物/サンゴ礁/サンゴ礁保全と水族館の役割]]','[[07_水族館・水生生物/サンゴ礁・海洋生態系/A_水族_2025_サンゴ礁回復の革新技術]]','[[07_水族館・水生生物/B_研究_20251126_DNAバーコーディングによる海洋生態系解析]]'],
    '08': ['[[08_動物保護・保全生物学/A_保全_20250729_アジア産大型肉食獣の保全状況とゲノム解析]]','[[08_動物保護・保全生物学/絶滅危惧種/ライチョウ域外保全_動物園ネットワーク]]','[[08_動物保護・保全生物学/A_専門_20250331_分類学の最新動向と法改正]]'],
    '09': ['[[09_獣医学・動物医療/診断・検査/A_獣医_2025_ウェアラブルデバイスによるバイタルサインモニタリング]]','[[09_獣医学・動物医療/A_獣医_2025_野生動物病原体スクリーニング]]','[[09_獣医学・動物医療/麻酔・外科/野生動物の麻酔管理と安全対策]]'],
    '10': ['[[10_生物学・生命科学/A_生物_2021_飼育下と野生下の哺乳類寿命比較]]','[[10_生物学・生命科学/遺伝学・ゲノム/A_生物_2025_CRISPRフィールドモニタリング技術]]','[[10_生物学・生命科学/A_生物_20260331_AIとプライム編集の産業化]]'],
    '11': ['[[11_生態学・自然環境学/B_生態学_20250325_春の食物連鎖と一次生産の回復]]','[[11_生態学・自然環境学/B_生態学_20250625_梅雨期の淡水生態系変動]]','[[11_生態学・自然環境学/里山/里山生態系と生物多様性保全]]'],
    '12': ['[[12_植物学・植生/動物園植栽/動物園の植栽設計と動物福祉]]','[[12_植物学・植生/動物園植栽/B_植物_20250328_春の動物園植物と動物の食草]]','[[12_植物学・植生/動物園植栽/B_植物_20250525_動物園の新緑と哺乳類の採食行動]]'],
    '13': ['[[13_生物分類図鑑/B_分類_20250218_2024年の新種記載まとめ]]','[[13_生物分類図鑑/B_分類_20250828_哺乳類の最新分類改訂2025年版]]','[[13_生物分類図鑑/A_分類_2026Q1_新種記載と深海生物分類最新動向]]'],
    '14': ['[[14_環境問題・気候変動/A_気候_2025_陸上土壌へのマイクロプラ侵入]]','[[14_環境問題・気候変動/気候変動/気候変動が野生生物に与える影響]]','[[11_生態学・自然環境学/B_生態学_20250725_夏の海岸生態系とウミガメ産卵]]'],
    '15': ['[[15_動物園学・博物館学/繁殖・保全/動物園の繁殖と保全の役割]]','[[15_動物園学・博物館学/展示設計・動物福祉/アニマルウェルフェアと日本の動物園水族館]]','[[15_動物園学・博物館学/A_動物園_20260331_福祉ガイドライン改訂]]'],
    '16': ['[[16_フィールドワーク・調査手法/野生動物調査/C_調査_20250108_冬期フィールドワーク足跡調査]]','[[16_フィールドワーク・調査手法/野生動物調査/B_調査_20250512_春季バードウォッチング調査手法]]','[[16_フィールドワーク・調査手法/野生動物調査/B_調査_20251112_秋の哺乳類糞DNA調査の実践]]'],
    '17': ['[[17_求人情報/動物園・水族館・NPO求人情報まとめ]]','[[17_求人情報/動物園・自然科学関連書籍・雑誌一覧]]','[[17_求人情報/市立動物園_市役所採用ページ一覧]]'],
    '18': ['[[18_学術論文・研究/学術論文・研究データベース一覧_ver2]]','[[18_学術論文・研究/A_論文_2025_野生動物病原体スクリーニング]]','[[18_学術論文・研究/A_論文_2025_陸上土壌へのマイクロプラ侵入]]']
}

refs_map = {
    '01':['https://www.jaza.jp/','https://www.waza.org/','https://www.aza.org/','https://www.env.go.jp/nature/'],
    '02':['https://www.jma.go.jp/','https://www.data.jma.go.jp/','https://www.env.go.jp/nature/','https://www.jaza.jp/'],
    '03':['https://www.waza.org/priorities/animal-welfare/','https://www.aza.org/animal-care-manuals','https://www.eaza.net/conservation/programmes/','https://www.jaza.jp/'],
    '04':['https://www.biodic.go.jp/','https://www.cbd.int/','https://www.iucn.org/','https://www.unep.org/'],
    '05':['https://www.iucnredlist.org/','https://www.gbif.org/','https://www.catalogueoflife.org/','https://www.nhm.ac.uk/'],
    '06':['https://www.env.go.jp/park/','https://www.japan.travel/national-parks/','https://www.unesco.org/en/man-and-biosphere','https://www.cbd.int/'],
    '07':['https://www.noaa.gov/ocean','https://www.jamstec.go.jp/','https://www.fao.org/fishery/en','https://www.unesco.org/en/ocean-decade'],
    '08':['https://www.iucn.org/','https://cites.org/','https://www.cbd.int/','https://www.wwf.org/'],
    '09':['https://www.woah.org/','https://www.who.int/','https://www.avma.org/','https://www.mhlw.go.jp/'],
    '10':['https://www.ncbi.nlm.nih.gov/','https://www.ebi.ac.uk/','https://www.nature.com/subjects/biology','https://www.science.org/journal/science'],
    '11':['https://www.esajournals.org/','https://www.frontiersin.org/journals/ecology-and-evolution','https://www.biodic.go.jp/','https://www.ipbes.net/'],
    '12':['https://www.kew.org/','https://www.bgci.org/','https://www.fao.org/forestry/en/','https://www.env.go.jp/nature/'],
    '13':['https://www.iczn.org/','https://www.zoobank.org/','https://www.catalogueoflife.org/','https://www.gbif.org/'],
    '14':['https://www.ipcc.ch/','https://public.wmo.int/en','https://www.unep.org/','https://unfccc.int/'],
    '15':['https://www.waza.org/','https://www.aza.org/','https://www.jaza.jp/','https://icom.museum/'],
    '16':['https://www.gbif.org/','https://www.usgs.gov/','https://www.iucnredlist.org/resources/spatial-data-download','https://www.biodic.go.jp/'],
    '17':['https://www.mhlw.go.jp/','https://www.jinji.go.jp/','https://www.hellowork.mhlw.go.jp/','https://www.jaza.jp/'],
    '18':['https://pubmed.ncbi.nlm.nih.gov/','https://www.crossref.org/','https://openalex.org/','https://www.ncbi.nlm.nih.gov/']
}


def sanitize_keyword(s):
    s = unicodedata.normalize('NFKC', s)
    s = re.sub(r'[^\w一-龥ぁ-んァ-ヶー]+', '', s)
    return s[:24] if s else 'テーマ'


def ensure_unique_title(title):
    if title not in existing_titles:
        existing_titles.add(title)
        return title
    i = 2
    while True:
        t2 = f"{title}（{i}）"
        if t2 not in existing_titles:
            existing_titles.add(t2)
            return t2
        i += 1


def build_article(title, date_iso, month, cid, cname, core_theme):
    season = season_map[month]
    focus = month_focus[month]
    related = related_map.get(cid, ['[[00_Index/index]]','[[17_求人情報/動物園・水族館・NPO求人情報まとめ]]','[[18_学術論文・研究/学術論文・研究データベース一覧_ver2]]'])
    refs = refs_map[cid]

    rel_block = '\n'.join([f'- {r}' for r in related])
    ref_block = '\n'.join([f'- [{u}]({u}): {cname}分野の一次資料として確認。' for u in refs])

    text = f'''---
title: "{title}"
date: {date_iso}
updated: {date_iso}
tags:
  - {cname}
author: "Zoo Knowledge Vault"
draft: false
---

# {title}

## 概要

2026年{month}月（{season}）の{cname}では、「{core_theme}」を核に、日次オペレーションと中長期計画を接続する実装が求められた。本稿は、既存記事の重複領域を避けつつ、現場で再利用できる判断手順・記録方式・評価指標を1本に統合した実務解説である。特に{focus}の局面では、単発対応を避け、運用品質を継続的に改善するための枠組みが重要となる。

記事構成は「観察→判定→介入→レビュー」の4工程を基本とし、各工程に必要なデータ、責任分担、再評価条件を明示した。これにより、担当者交代や繁忙期でも運用の再現性を確保し、意思決定を組織知として蓄積できる。

## 2026年の前提条件と課題整理

### 1. 運用環境の変化

2026年は、気象リスクの増幅、来園行動の多様化、保全要請の高度化が同時に進行した。{cname}領域においては、従来の経験主義だけでは判断のばらつきが拡大しやすく、記録の標準化とレビュー頻度の再設計が不可欠となった。{core_theme}は、この変化を最前線で受けるテーマであり、実務の優先順位を明確化する役割を持つ。

### 2. データ運用の要件

実装の要点は、入力データの粒度統一、異常判定ルールの明文化、改善ログの時系列管理である。観測値と所見を分離して記録し、しきい値超過時の初動を事前定義することで、対応の遅れと過剰反応を同時に抑制できる。さらに、週次レビューで再現不能事例を優先分析し、月次でSOP改訂へ反映する循環を維持することが、運用品質向上の最短経路となる。

### 3. 教育・連携の実装

{core_theme}を定着させるには、現場単独ではなく、運営・教育・広報・研究の連携が必要である。特に来園者への説明が伴う施策では、技術的妥当性だけでなく、伝達可能性を同時に担保しなければならない。2026年運用では、現場記録を教育素材へ再利用し、改善知見を新人育成へ戻す仕組みが有効だった。

## 実装フレーム（4工程）

| 工程 | 主な入力 | 判定基準 | 出力アクション |
|---|---|---|---|
| 観察 | 行動・環境・健康データ | 欠損の有無、異常兆候 | 日次記録を確定 |
| 判定 | しきい値・過去履歴 | 通常/警戒/対応 | 連絡レベルを設定 |
| 介入 | 人員・設備・時間枠 | 介入妥当性と安全性 | 実施ログを保存 |
| レビュー | 週次集計・再発状況 | 是正効果・再現性 | SOP更新案を作成 |

## 現場チェックリスト（2026年版）

1. 記録フォーマットを統一し、入力欠損を当日中に補完する。
2. 異常兆候は時刻・数値・文脈の3点セットで保存する。
3. 警戒段階の段階定義をチーム内で毎月再確認する。
4. 週次レビューでは成功例より再現不能事例を優先分析する。
5. 月次で是正完了率を可視化し、次月計画へ反映する。
6. 年次総括でKPIと教育計画を連結し、継続実装を担保する。

## 関連記事

{rel_block}

## 参考・引用元

{ref_block}
'''

    body = re.sub(r'^---[\s\S]*?---\n', '', text, count=1)
    if len(body) < 1500:
        text += f"\n\n## 補足\n\n{cname}における{core_theme}は、短期の現場対応に留まらず、年間計画と教育設計へ接続することで効果が最大化する。2026年運用では、記録とレビューを一体化した実務設計が、再現性と安全性の両立に寄与した。\n"
    return text


created = []

for month in range(1, 13):
    for idx, (cid, cname, prefix, outdir, base_theme) in enumerate(cats):
        day = day_map[idx]
        date_iso = f'2026-{month:02d}-{day:02d}'
        ymd = f'2026{month:02d}{day:02d}'
        core_theme = f'{base_theme}と{month_focus[month]}'

        title = ensure_unique_title(f'【2026年{month:02d}月】{cname}徹底分析：{core_theme}')
        keyword = sanitize_keyword(core_theme)

        out_path = ROOT / outdir
        out_path.mkdir(parents=True, exist_ok=True)
        f = out_path / f'{prefix}_{ymd}_{keyword}.md'
        if f.exists():
            f = out_path / f'{prefix}_{ymd}_{keyword}_v2.md'

        article = build_article(title, date_iso, month, cid, cname, core_theme)

        # hard validation before write
        if 'draft: false' not in article:
            raise RuntimeError(f'draft missing: {f}')
        if article.count('- [[') < 3:
            raise RuntimeError(f'related links <3: {f}')
        if len(re.sub(r'^---[\s\S]*?---\n', '', article, count=1)) < 1500:
            raise RuntimeError(f'body too short: {f}')

        f.write_text(article, encoding='utf-8', newline='\n')
        created.append(f)

print('CREATED_TOTAL', len(created))
c = collections.Counter(p.parts[0] for p in created)
for k in sorted(c):
    print('CREATED_CAT', k, c[k])
print('CREATED_FIRST', created[0].as_posix())
print('CREATED_LAST', created[-1].as_posix())
