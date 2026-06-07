# 『迷わないポーカー Vol2 — ポストフロップ完全版』(MATCHA Framework 編) 執筆プロジェクト

## プロジェクト概要

『迷わないポーカー』MATCHA シリーズ Vol2 (**MATCHA Framework 編**)。Cash 100bb と MTT chipEV (25/50/100/200bb) のポストフロップ判断を **MATCHA Framework** という単一フレームワークに統一した書籍。

**MATCHA** (シリーズ共通) = **M**ath **A**lgorithm for **T**ier-**C**ategorized **H**old'em **A**ction
— ティア分類されたホールデム判断のための数学アルゴリズム

| 巻 | サブブランド | 役割 |
|---|---|---|
| Vol1 | MATCHA Formula | プリフロップの Score 公式 |
| **Vol2 (本書)** | **MATCHA Framework** | **ポストフロップの 5 判定軸 + TEA グリッド + 3 モード + 3 補正** |
| Vol3 | MATCHA Exploits | 相手タイプ別の MATCHA 歪め方 |

旧 Vol2 (キャッシュ専用) と旧 Vol3 (MTT 専用) を統合し、**11 専用公式 → 5 つの判定軸 + 3 つのモード + 3 つの補正 (~20 暗記項目)** に圧縮。GTO Wizard 実測データ 293K rows で huge_loss は 11 専用公式比 **62% 削減** (15.75 BB → 5.94 BB)。

## ICM/PKO の取扱い

ICM/PKO の postflop GTO data は GTO Wizard API tier 制限 (403) で取得できないため、本書では **Cash と MTT chipEV のみ対象**。ICM/PKO は将来別冊 (Vol2.5 想定) で対応予定。

## MATCHA Framework — 中核構造

### Layer 1: 5 つの判定軸 (`scripts/three_class_model/udg_v2.py`)

| 判定軸 | カテゴリ | コード変数 |
|---|---|---|
| ① レンジ分布 | 2極化型 / 混在型 / 密集型 | `board_polar_tier` |
| ② ハンドストレングス | ナッツメイド / ストロング / ツーペア / トップペア以上 / ミドルペア / エア | `hand_strength_tier` |
| ③ ベットサイジング | スモールベット / ミディアムベット / オーバーベット / オールイン | `bet_size_tier` |
| ④ SPR | オールインSPR / ローSPR / ミディアムSPR / ディープSPR | `spr_tier` |
| ⑤ エクイティバケット | モンスターハンド / 良ハンド / 弱ハンド / ブラフハンド | `equity_aware_tier` |

### Layer 2: TEA グリッド (中央装置)

**Tier × Edge = Action グリッド** = 5 軸の組合せから **形勢** (Edge) を導出。

| 形勢 (Edge) | 英訳 | 意味 |
|---|---|---|
| 優勢 | Ahead | hero range advantage |
| 五分五分 | Even | no edge |
| 劣勢 | Behind | villain advantage |

### Layer 3: 3 つのモード (形勢ごとの行動原則)

| 形勢 | モード | 行動原則 |
|---|---|---|
| 優勢 | **バリューモード** | 非リバー × 非2極化型 → レイズ / それ以外 → コール |
| 五分五分 | **ショーダウンモード** | オールインSPR → コール / オーバーベット × 無 draw → 慎重 FOLD / 既定 コール |
| 劣勢 | **ブラフキャッチモード** | 強ドロー → コール / スモールベット × 混在型 × ブロッカー → コール / 既定 FOLD |

### Layer 4: 3 つの補正

- **チェックレイズ補正** (vs CR): 形勢を 1 段階下げ (opp value-heavy)
- **ドンクベット補正** (vs Donk): 劣勢→五分五分に上げ + レイズ→コール変換 (opp air-heavy)
- **オープナー補正** (CO/HJ open river): 形勢を 1 段階下げ (river-only)

## Directory Structure

```
vol2-postflop/
├── chapters/               # 本文 (00-introduction〜20-cheatsheet.md + 付録 A〜C)
├── book.json               # 書誌メタデータ
├── toc.md                  # 目次・執筆ガイド (MATCHA 用語)
├── plan.md                 # 書籍企画書
├── CLAUDE.md               # このファイル
└── research.md             # 調査資料 (MATCHA 設計過程)
```

## 用語ポリシー

- **本文表記**: 日本語 (用語集 https://gistpreview.github.io/?dbb75f11330aff4346de987c4f4fb91b 準拠)
- **コード変数**: 英語維持 (実装明瞭性のため、ファイル名・関数名は legacy の `udg_v2.py` 等そのまま)
- **GTO Wizard 業界標準語**: 出典として併記、本文は日本語に置換

## 執筆方針

### 一貫した判定軸概念の使用

全章で同じ判定軸 (レンジ分布 / ハンドストレングス / ...) を引用。読者が混乱しないよう、軸の定義は ch01-06 で導入後、ch07 以降は前提として扱う。

### 公式は generator 経由 (必須)

memory `feedback_book_writing_workflow`: chapters/*.md を直接書き直してはいけない。必ず scripts/generate/specs/vol2_ch{NN}_*.yaml + generator を書いてから生成する。

### 暗記項目を明示

各章の末尾に「**この章で覚える項目** (X items)」を箱で囲んで提示。読者が累計暗記負荷を把握できるよう。

### audit data 引用

MATCHA Framework の精度は `scripts/three_class_model/NEW_FORMULA_AUDIT.md` と `UDG_V2_RESULTS.md` の数値を引用 (293K rows の実測値)。

## 章構成 (21 章 + 付録 3)

| Part | 章 | 内容 |
|------|----|------|
| 序章 | ch00 | MATCHA Framework 全体像、暗算 philosophy |
| 第1部: 判定軸 | ch01-05 | 5 つの判定軸の定義と読み方 |
| 第2部: TEA グリッド | ch06 | 5 軸 → 形勢 (Edge) の導出 |
| 第3部: モード | ch07-09 | バリュー / ショーダウン / ブラフキャッチモード |
| 第4部: ポット種別 | ch10-12 | SRP / 3BP / 4BP modifier |
| 第5部: 状況補正 | ch13-15 | チェックレイズ / ドンクベット / オープナー補正 |
| 第6部: スタック深度 | ch16-17 | 短スタック (≤25bb) / 深スタック (200bb+) |
| 第7部: 実戦 | ch18-20 | 境界ハンド / ドリル / チートシート |
| 付録 | A-C | MATCHA 完全表 / audit 結果 / データ取得法 |

## 関連 memory

- `project_vol2_postflop_udg.md`: 3 巻構成決定 + MATCHA Framework 概要
- `project_postflop_3rule_formula.md`: 旧 v9b/v10/v15 系列 (MATCHA で吸収)
- `project_probe_priority_findings.md`: 公式設計のためのデータ収集経緯
- `feedback_book_writing_workflow`: chapters/*.md 直接編集禁止
- `project_c_value_table_split`: preflop HandScore (Vol1 用、本書とは別系統)

## 関連 knowledges

- `knowledges/gto_wizard_study/PROBE_PRIORITY_FINDINGS.md`: probe data 全 phase 一覧
- `scripts/three_class_model/UDG_V2_RESULTS.md`: MATCHA audit 結果と章構成提案
- `scripts/three_class_model/NEW_FORMULA_AUDIT.md`: 11 専用公式の audit
- `scripts/three_class_model/udg_v2.py`: MATCHA Framework 実装 (Vol2 の SSOT、ファイル名は legacy)

## 用語集 (HTML)

https://gistpreview.github.io/?dbb75f11330aff4346de987c4f4fb91b

執筆中の用語確認はこの gist を SSOT とする。
