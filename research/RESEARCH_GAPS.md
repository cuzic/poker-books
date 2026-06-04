# GTO Wizard 研究 — 未調査領域 (GAPS) ★ 大幅更新 2026-06-04

**更新**: 2026-06-04 (deep_inventory.py で 896 ファイル全数解析後の改訂版)

`deep_inventory.py` で各ファイルの `game.players[].chips_on_table` を読み取り、
シナリオを徹底分析した結果、**当初想定より既存データが遥かに充実** していることが判明。

## 📊 既存データの実態 (896 ファイル全 phase 集計)

### Phase 別分布
| Phase | ファイル数 | カバー |
|-------|---------|--------|
| Turn | 530 | Turn 行動詳細 |
| River | 202 | River 行動詳細 |
| Preflop | 164 | (多くが集約レベル、hand-level は task_a/c の 20 だけ) |

### Depth 別 (主要)
| Depth | ファイル数 |
|-------|---------|
| 100 bb (Cash + MTT 100) | 301 |
| 50 bb (MTT) | 234 |
| 200 bb | 120 |
| 25 bb (MTT) | 80 |

### Opener × Defender × Phase の組み合わせ
**postflop の 5 オープナー × 4 depth × 24 board が全て揃っている!**:

```
BTN open → BB defense (postflop): 156 + 89 + 54 = 299 files (Cash 100/50/25bb)
BTN open → BTN cbet (postflop): 49+48+24+24 = 145 files (4 depths × 24 boards)
CO open → CO cbet:  24+24+24 = 72 files (3 depths)
HJ open → HJ cbet:  24+24+24 = 72 files
UTG open → LJ act (9-max):  24+24+24 = 72 files  ← UTG 系の MTT 9-max
SB open → SB cbet:  24+24+24 = 72 files (BvB postflop)
```

→ **「BTN 以外の postflop」は既に網羅されている** (UTG/HJ/CO/SB の各 depth × board)

### Donk / BB lead 系
| 状況 | ファイル数 |
|------|---------|
| BB lead at turn (BB が turn で actor) | 96 |
| BB lead at river (BB が river で actor) | 202 |

→ BB が postflop で actor のシナリオも大量にある。ただし「donk lead」(flop で BB が先手 bet) と「cbet 後の reaction」を区別するには各ファイルの `flop_actions` を確認する必要あり。

## ✅ 既に十分カバー済 (再取得不要)

### Vol1 Preflop (集約レベル)
- 5 ポジ RFI 比率: `vol2/findings/cash_preflop_gto_summary.json`
- BB vs 各オープナー squeeze_pct: 同上
- オープナー vs 3-bet fourbet_pct: 同上
- multiway スクイーズ %: 同上

### Vol1 Preflop (hand-level)
- BB vs UTG/HJ/CO/BTN/SB の **169 hand 別 fold/call/3-bet** ← `research/v3-additional/findings/task_a_*`
- Squeeze N=1/2 × 13 シナリオの **169 hand 別** ← `task_c_*`

### Vol2 Cash Postflop
- 5 オープナー × 7 board family × IP/OOP cbet/defense (5-cat) ← `cash_5cat_gto`, `cash_board_wide_gto`
- Flop pairwise (56 board)、Turn pairwise (42 board) ← `cash_pairwise_gto.json`
- Flop detail per-mv-cat × board ← `cash_flop_detail_gto.json`

### Vol3 MTT Postflop (圧倒的に充実)
- **3BP 25/50/100bb × BTN_BB + CO_BB × 24 board × postflop hand-level**
- **5 オープナー × BB defense × 4 depth (25/50/100/200) × 24 board × postflop hand-level**
   - `def_cash100_bb_raw`, `def_mtt25/50/100_bb_raw`, `cash50bb_raw`
   - 9-max データ (LJ position) 一部含む
- **Turn 詳細 (BTN_BB Cash 100, MTT 50bb)** ← `def_cash100_bb_turn_raw`, `def_mtt50_bb_turn_raw`
- **River 詳細 (同上)** ← `def_cash100_bb_river_raw`, `def_mtt50_bb_river_raw`
- **Turn barrel SBR 別** ← `mtt_turn_barrel_SBR{15,20,25,40}.json`
- **CheckRaise SBR 別** ← `mtt_check_raise_SBR{20,25}.json`
- **MTT preflop SBR 別** ← `mtt_preflop_*` (集約)

## 🆕 attack / defense 偏り発見 (2026-06-04 再分析)

`attack_vs_defense_coverage.py` で 732 postflop ファイルを spot_type (attack/defense) で分類:

| Actor | attack | defense |
|-------|--------|---------|
| BB | 113 | **185** |
| BTN | 146 | **0** |
| CO | 72 | **0** |
| HJ | 72 | **0** |
| LJ (9m) | 72 | **0** |
| **SB** | **72 (flop only)** | **0** |

- **defense 185 ファイルは全て BB defender**
- **IP defender (BTN/CO/HJ が BB lead を受ける) は 0 件**
- **SB defender (BvB で BB の bet 受ける) は 0 件**
- **SB の turn / river は 0 件** (SB は flop attack のみ)

→ **defense 全般、特に IP defender / SB defender / SB の turn/river は完全未調査**

## ❌ 真に未調査の領域

### 🔴 高優先: Vol1 Preflop hand-level の残り

書籍 ch04 §4.2-§4.6 の preflop hand-level は **未取得**。BB defense は完成しているが IP/SB/vs3bet 等は集約のみ。

| # | 領域 | spots | 書籍参照 |
|---|------|-------|---------|
| D | **IP defense hand-level** (BTN/CO/HJ × UTG/HJ/CO) | 6 | ch04 §4.2 |
| E | **SB OOP defense hand-level** (vs UTG/HJ/CO/BTN) | 4 | ch04 §4.3 |
| F1 | **vs 3-bet オープナー hand-level** (12 シナリオ) | 12 | ch04 §4.4 |
| F2 | **4-bet defense hand-level** ★ 書籍「理論値」明言 | 5 | ch04 §4.5 |
| F3 | **5-bet defense hand-level** ★ 書籍「理論値」明言 | 1 | ch04 §4.6 |
| L | **Cash RFI 5 オープナー hand-level** | 5 | ch03 |
| C2 | **Squeeze N=3 hand-level** | ~5 | ch05 (N≥2 概算値) |

**合計**: ~38 spots = ~4 分の API call

### 🟡 中優先: Postflop の特殊シナリオ

| # | 領域 | spots | 既存との関係 |
|---|------|-------|------------|
| **S1** | **SB-BB BvB SRP postflop turn/river** ★ | ~48 | 既存は SB flop attack のみ、turn/river なし |
| **S2** | **SB defender (BvB で BB lead 受ける)** ★ | ~24 | 完全 0、BvB の OOP→IP defense ライン |
| **S3** | **IP defender (BTN/CO/HJ が BB lead 受ける)** ★ | ~30 | 完全 0、いわゆる「BB donk → IP fold/call/raise」 |
| **S4** | **3BP postflop defense (3-bettor を caller が反撃)** | ~30 | 既存 3BP は cbet 側のみ |
| **S5** | **Check-raise pot 後 (check-raise → call/raise)** | ~30 | 既存ほぼ全て raw single cbet line |
| P1 | Cash IP cbet vs raise (BTN cbet → BB raise の対応) | ~10 | 既存 turn/river raw に部分あるが BTN_BB のみ |
| P2 | 3BP HJ_BB / UTG_BB / SB_BB postflop | ~30 | 既存 3bp_raw は BTN_BB / CO_BB のみ |
| P3 | Cash 50bb / 25bb の non-MTT postflop | ~50 | 既存は MTT 用が大半 |
| P4 | Cash 4BP (4-bet pot) postflop | ~30 | 既存 3BP のみ、4BP は完全未調査 |

### 🟢 低優先: 書籍範囲拡張

| # | 領域 | spots | 書籍参照 |
|---|------|-------|---------|
| K | **ICM Bubble / FT / PCT 別 preflop+postflop** | ~30 | ch09 簡易のみ |
| Q | **Cash multiway postflop (3-way / 4-way)** | ~20 | 既存はほぼ HU |
| R | **9-max preflop hand-level** | ~10 | 9-max データは一部のみ |

## 🎯 推奨実施プラン (改訂)

### Phase α: Vol1 Preflop 完全実測化 (~38 spots / ~4 分)
タスク D + E + F1 + F2 + F3 + L + C2 = 38 spots
→ Vol1 preflop **全章** が hand-level 実測ベース化
→ 書籍 §4.5/§4.6 の「理論値、GTO 検証なし」帯を実測で確定

### Phase β: defense 不足 + SB 補強 (~162 spots / ~17 分) ★ 新規追加
タスク S1 + S2 + S3 + S4 + S5 = 162 spots
→ defense / SB の盲点を埋める。特に IP defender / SB defender / SB turn river

### Phase γ: Postflop 特殊シナリオ補強 (~120 spots / ~12 分)
タスク P1 + P2 + P3 + P4 = 約 120 spots
→ 既存 postflop の盲点 (non-BTN 3BP / Cash 4BP 等) を埋める

### Phase δ: 書籍範囲拡張 (~60 spots / ~6 分)
タスク K + Q + R = 60 spots
→ 新章追加候補 (ICM, multiway, 9-max)

## 全 Phase 合計

| Phase | 内容 | spots | 取得済 |
|-------|------|-------|--------|
| α | Vol1 Preflop hand-level の残り | 38 | **30/38** ✅ (F3/C2 は GTO tree なし) |
| **β** | **defense 不足 + SB 補強** ★ 最重要 | 162 | **16/162** S1 のみ取得 |
| γ | Postflop 特殊シナリオ補強 | 120 | 0 |
| δ | 書籍範囲拡張 | 60 | 0 |
| **計** | | **380 spots** | **46 取得済** |

## 🚨 GTO Wizard tree の制約 (2026-06-04 発見)

実際に調査して判明した GTO Wizard `Cash6mTest_6mNL100R2` tree の制約:

### ✅ サポートされている spot

- **Preflop**: 標準 sizing (R2/R2.5/R3 open, R7/R8/R10 3-bet, R20/R21 4-bet)
- **Flop**: action_solutions に出てくる sizing (`B33` / `X` / `R6.1` 等、spot 別)
- **BTN open → BB call → BTN cbet → BB defense** (= 既存 raw データの大半)

### ❌ サポートされていない spot (HTTP 204 / 422)

- **4-bet defense / 5-bet defense** (Vol1 ch04 §4.5/§4.6): 標準 sizing で 204
- **Squeeze N=3** (4 callers): 204
- **BB lead at flop (donk lead)**: 422、tree に含まれない
- **任意 bet size + check-raise** (例: `B33-R10`): 422
- **non-standard postflop sequence**: 422

→ Phase β の S2/S3/S4/S5 は **GTO Wizard tree に含まれない**ため取得不可能

### 代替策

- **BB lead 系**: 既存 `def_cash100_bb_turn_raw` 96 ファイル + `_river_raw` 202 ファイルが tree 合法な「BB lead at turn/river」データ
- **check-raise pot**: 既存 `cash_pairwise_gto.json` の SRP_OOP / 3BP_OOP で OOP_defense.raise として含まれる可能性
- **書籍 ch04 §4.5/§4.6 (4-bet/5-bet defense)**: 既知の通り「理論値、GTO 検証なし」のままで OK

## 重要な再認識

**当初は「IP defense / SB defense は未調査」と思っていたが、これは preflop の話。**

**Postflop では UTG_BB / HJ_BB / CO_BB / SB_BB の全シナリオが既存** (Vol3 findings 配下に postflop hand-level あり)。
→ Vol2 Tier 1 マトリックス (ch03-05) の検証には既存データで十分。
→ Vol2 Tier 2 (ch08-11) も既存データで十分カバー。

**「donk lead」(BB が flop で先手 bet)** は明示的な検出が必要だが、`def_*_bb_*_raw` に BB lead at turn/river の 96 + 202 ファイルがあり、これに含まれる可能性が高い。

詳細確認は `deep_inventory.py` に flop_actions 解析を追加するか、特定ファイルを開いて検証。

## 使い方

1. **新規調査を始める前に**: 本ドキュメントの 「✅ 既に十分カバー済」を確認
2. **既存データの所在を知るには**: `RESEARCH_INVENTORY.md` (集約版) / `RESEARCH_DEEP_INVENTORY.md` (詳細)
3. **個別ファイルの詳細**: `RESEARCH_INVENTORY_DETAIL.md`

調査スクリプトは `research/v3-additional/` に集約。
