# 『迷わないポーカー Vol2 — ポストフロップ完全版』執筆プロジェクト

## プロジェクト概要

Cash 100bb と MTT chipEV (25/50/100/200bb) のポストフロップ判断を **UDG (Universal Defense Grid)** という単一フレームワークに統一した書籍。

旧 Vol2 (キャッシュ専用) と旧 Vol3 (MTT 専用) を統合し、**11 専用公式 → 5 tier + 3 universal rule + 3 modifier (~20 暗記項目)** に圧縮。GTO Wizard 実測データ 293K rows で huge_loss は 11 専用公式比 **62% 削減** (15.75 BB → 5.94 BB)。

## ICM/PKO の取扱い

ICM/PKO の postflop GTO data は GTO Wizard API tier 制限 (403) で取得できないため、本書では **Cash と MTT chipEV のみ対象**。ICM/PKO は将来別冊 (Vol3.5 想定) で対応予定。

## UDG (Universal Defense Grid) — 中核フレームワーク

**Layer 1: 5 tier 概念** (`scripts/three_class_model/udg_v2.py`)
- `board_polar_tier`: POLAR (dynamic/d2t/mono) / MERGED (dry_high/low_dry/paired) / MID
- `hand_strength_tier`: NUT_MADE / STRONG / TWO_PAIR / PAIR / MID_PAIR / AIR
- `bet_size_tier`: SMALL (33%pot) / MED (50-100%) / BIG (>100%) / ALLIN
- `spr_tier`: SHALLOW (<1) / LOW (1-3) / MID (3-7) / HIGH (>7)
- `equity_aware_tier`: HIGH / MID / LOW / VERY_LOW (hand_strength × equity_bucket の融合)

**Layer 2: matchup tier** = AHEAD / TIE / BEHIND (5 tier の組合せから導出)

**Layer 3: 3 universal rule** (matchup 別)
- AHEAD: RAISE on non-river non-POLAR / CALL elsewhere
- TIE: SHALLOW SPR → CALL / BIG bet → 慎重 FOLD / 既定 CALL
- BEHIND: strong_draw → CALL / SMALL × MERGED × blocker → CALL / 既定 FOLD

**Layer 4: 3 context modifier**
- vs_CR: matchup を 1 段階下げ (opp value-heavy)
- vs_donk: matchup を BEHIND→TIE のみ 1 段階上げ + RAISE→CALL 変換
- CO/HJ open river: matchup を 1 段階下げ

## Directory Structure

```
vol2-postflop/
├── chapters/               # 本文 (00-introduction〜20-cheatsheet.md + 付録 A〜C)
├── book.json               # 書誌メタデータ
├── toc.md                  # 目次・執筆ガイド
├── plan.md                 # 書籍企画書
├── CLAUDE.md               # このファイル
└── research.md             # 調査資料 (UDG v2 設計過程)
```

## 執筆方針

### 一貫した tier 概念の使用

全章で同じ tier 関数 (board_polar_tier / hand_strength_tier / ...) を引用。読者が混乱しないよう、tier の定義は ch01-06 で導入後、ch07 以降は前提として扱う。

### 公式は generator 経由 (必須)

memory `feedback_book_writing_workflow`: chapters/*.md を直接書き直してはいけない。必ず scripts/generate/specs/vol2_ch{NN}_*.yaml + generator を書いてから生成する。

### 暗記項目を明示

各章の末尾に「**この章で覚える項目** (X items)」を箱で囲んで提示。読者が累計暗記負荷を把握できるよう。

### audit data 引用

UDG v2 公式の精度は `scripts/three_class_model/NEW_FORMULA_AUDIT.md` と `UDG_V2_RESULTS.md` の数値を引用 (293K rows の実測値)。

## 章構成 (21 章 + 付録 3)

| Part | 章 | 内容 |
|------|----|------|
| 序章 | ch00 | UDG framework 全体像、暗算 philosophy |
| 第1部: tier 概念 | ch01-05 | 5 tier 関数の定義と読み方 |
| 第2部: matchup | ch06 | 5 tier → 3 matchup の導出表 |
| 第3部: rule | ch07-09 | AHEAD / TIE / BEHIND の 3 ルール |
| 第4部: pot type | ch10-12 | SRP / 3BP / 4BP modifier |
| 第5部: action context | ch13-15 | CR / donk / opener position |
| 第6部: depth | ch16-17 | 短スタック (≤25bb) / 深スタック (200bb+) |
| 第7部: 実戦 | ch18-20 | 境界ハンド / ドリル / チートシート |
| 付録 | A-C | UDG 完全表 / audit 結果 / データ取得法 |

## 関連 memory

- `project_postflop_3rule_formula.md`: 旧 v9b/v10/v15 系列 (Vol2 の元、UDG v2 で吸収)
- `project_probe_priority_findings.md`: 公式設計のためのデータ収集経緯
- `feedback_book_writing_workflow`: chapters/*.md 直接編集禁止
- `project_c_value_table_split`: preflop HandScore (Vol1 用、本書とは別系統)

## 関連 knowledges

- `knowledges/gto_wizard_study/PROBE_PRIORITY_FINDINGS.md`: probe data 全 phase 一覧
- `scripts/three_class_model/UDG_V2_RESULTS.md`: UDG v2 audit 結果と章構成提案
- `scripts/three_class_model/NEW_FORMULA_AUDIT.md`: 11 専用公式の audit
- `scripts/three_class_model/udg_v2.py`: UDG v2 実装 (Vol2 の SSOT)
