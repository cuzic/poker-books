# drill 拡張版 MATCHA Framework — GTO 監査結果

dataset: dataset_unified_v2.csv (293K rows、phase 1-6 統合)
対象: poker-drill `matcha-framework-*-decisions-cards.ts` の全 decision_card

## サマリー

- 全 card: 99
- matched (dataset 内): 34 (34.3%)
- unmatched: 65 (65.7%)
- accuracy (drill_action == gto_best): **41.2%**
- avg loss / decision: **3.611 BB**
- huge mistake (>5 BB) 比率: **14.7%**
- huge mistake あたりの avg loss: **22.577 BB**

## per-deck breakdown

| deck | n | match % | acc % | avg_loss (BB) | huge % |
|------|---:|---:|---:|---:|---:|
| matcha-framework-3bet-pot-decisions | 20 | 55% | 36% | 4.666 | 27.3% |
| matcha-framework-4bet-pot-decisions | 20 | 65% | 46% | 3.938 | 7.7% |
| matcha-framework-srp-flop-decisions | 17 | 0% | N/A | N/A | N/A |
| matcha-framework-srp-river-decisions | 22 | 9% | 0% | 0.021 | 0.0% |
| matcha-framework-srp-turn-decisions | 20 | 40% | 50% | 2.526 | 12.5% |

## gap reason 分類 (unmatched cards)

- **no_dataset_match**: 43 cards
- **scenario_mismatch**: 15 cards
- **action_unparseable**: 7 cards

## 不一致 (drill_action != gto_best) の worst 20

| deck | card_id | drill | GTO | loss (BB) | answer 抜粋 |
|------|---------|-------|-----|----:|-------|
| matcha-framework-4bet-pot-decisions | mf4bp_014 | FOLD | CALL | 43.001 | FOLD |
| matcha-framework-3bet-pot-decisions | mf3bp_003 | FOLD | CALL | 19.284 | FOLD |
| matcha-framework-3bet-pot-decisions | mf3bp_017 | FOLD | CALL | 19.284 | FOLD |
| matcha-framework-srp-turn-decisions | mfsrpt_009 | FOLD | CALL | 19.284 | FOLD |
| matcha-framework-3bet-pot-decisions | mf3bp_006 | FOLD | CALL | 12.032 | FOLD |
| matcha-framework-4bet-pot-decisions | mf4bp_003 | FOLD | CALL | 4.284 | FOLD |
| matcha-framework-4bet-pot-decisions | mf4bp_013 | RAISE | CALL | 1.274 | ベット (≈ all-in) |
| matcha-framework-4bet-pot-decisions | mf4bp_018 | RAISE | CALL | 1.274 | (already all-in) |
| matcha-framework-4bet-pot-decisions | mf4bp_002 | RAISE | CALL | 0.736 | チェックレイズ (all-in) |
| matcha-framework-3bet-pot-decisions | mf3bp_020 | RAISE | CALL | 0.433 | チェックレイズ (stack off) |
| matcha-framework-4bet-pot-decisions | mf4bp_007 | RAISE | CALL | 0.429 | チェックレイズ (all-in) |
| matcha-framework-srp-turn-decisions | mfsrpt_016 | RAISE | CALL | 0.429 | ベット ミディアム (50%) |
| matcha-framework-4bet-pot-decisions | mf4bp_010 | CALL | RAISE | 0.159 | コール (stack off 用意) |
| matcha-framework-3bet-pot-decisions | mf3bp_016 | RAISE | CALL | 0.154 | ベット スモール (33%) ブラフ |
| matcha-framework-3bet-pot-decisions | mf3bp_019 | CALL | RAISE | 0.124 | コール |
| matcha-framework-srp-turn-decisions | mfsrpt_002 | RAISE | CALL | 0.07 | ベット ミディアム (66%) |
| matcha-framework-srp-river-decisions | mfsrpr_020 | RAISE | CALL | 0.028 | ベット スモール (33%) or チェック |
| matcha-framework-srp-river-decisions | mfsrpr_016 | RAISE | CALL | 0.014 | ベット ミディアム (66%) |
| matcha-framework-3bet-pot-decisions | mf3bp_013 | RAISE | CALL | 0.006 | ベット ミディアム (50%) or オールイン |
| matcha-framework-srp-turn-decisions | mfsrpt_004 | CALL | FOLD | 0.0 | チェック (give up) |

## unmatched cards (上位 30)

| deck | card_id | reason |
|------|---------|--------|
| matcha-framework-3bet-pot-decisions | mf3bp_001 | no_dataset_match (board=K♠ 7♦ 2♣ hand=A♥ K♠ scenarios=[]) |
| matcha-framework-3bet-pot-decisions | mf3bp_004 | no_dataset_match (board=7♦ 4♣ 2♠ hand=A♥ A♦ scenarios=[]) |
| matcha-framework-3bet-pot-decisions | mf3bp_005 | no_dataset_match (board=K♠ 7♦ 2♣ 5♥ hand=A♥ K♠ scenarios=['N_cash_3bp_flop', 'N_cash_3bp_river', 'P5 |
| matcha-framework-3bet-pot-decisions | mf3bp_007 | no_dataset_match (board=9♠ 8♦ 7♣ hand=A♥ A♦ scenarios=[]) |
| matcha-framework-3bet-pot-decisions | mf3bp_009 | no_dataset_match (board=K♠ K♦ 4♣ hand=A♥ J♦ scenarios=[]) |
| matcha-framework-3bet-pot-decisions | mf3bp_010 | no_dataset_match (board=K♠ 7♦ 2♣ hand=A♥ K♠ scenarios=[]) |
| matcha-framework-3bet-pot-decisions | mf3bp_011 | no_dataset_match (board=9♠ 8♦ 7♣ hand=T♥ J♦ scenarios=[]) |
| matcha-framework-3bet-pot-decisions | mf3bp_015 | no_dataset_match (board=7♦ 4♣ 2♠ hand=7♥ 7♣ scenarios=[]) |
| matcha-framework-3bet-pot-decisions | mf3bp_018 | no_dataset_match (board=7♦ 4♣ 2♠ hand=K♥ K♦ scenarios=[]) |
| matcha-framework-4bet-pot-decisions | mf4bp_006 | no_dataset_match (board=A♠ 9♦ 4♣ hand=K♥ K♦ scenarios=[]) |
| matcha-framework-4bet-pot-decisions | mf4bp_009 | no_dataset_match (board=7♦ 4♣ 2♠ hand=K♥ K♦ scenarios=[]) |
| matcha-framework-4bet-pot-decisions | mf4bp_011 | no_dataset_match (board=9♠ 8♦ 7♣ hand=9♥ 9♦ scenarios=[]) |
| matcha-framework-4bet-pot-decisions | mf4bp_012 | no_dataset_match (board=K♠ K♦ 4♣ hand=Q♥ Q♦ scenarios=[]) |
| matcha-framework-4bet-pot-decisions | mf4bp_017 | no_dataset_match (board=K♠ 7♦ 2♣ hand=7♣ 7♦ scenarios=[]) |
| matcha-framework-4bet-pot-decisions | mf4bp_019 | no_dataset_match (board=A♠ 9♦ 4♣ hand=T♥ T♦ scenarios=[]) |
| matcha-framework-4bet-pot-decisions | mf4bp_020 | no_dataset_match (board=5♦ 4♣ 2♠ hand=A♥ A♦ scenarios=[]) |
| matcha-framework-srp-flop-decisions | mfsrpf_001 | action_unparseable: 'スモールベット (33%)、頻度約 100%' |
| matcha-framework-srp-flop-decisions | mfsrpf_002 | action_unparseable: 'スモールベット (33%)、頻度約 80%' |
| matcha-framework-srp-flop-decisions | mfsrpf_003 | no_dataset_match (board=9♠ 8♦ 7♣ hand=K♥ K♠ scenarios=['N_mtt100_river']) |
| matcha-framework-srp-flop-decisions | mfsrpf_004 | no_dataset_match (board=K♠ 7♦ 2♣ hand=A♥ K♠ scenarios=['N_cash_donk_def', 'A_cash_donk_def_full', 'P |
| matcha-framework-srp-flop-decisions | mfsrpf_005 | scenario_mismatch (board=K♠ 7♦ 2♣ found in dataset but not in expected scenarios=['N_mtt100_river']) |
| matcha-framework-srp-flop-decisions | mfsrpf_006 | scenario_mismatch (board=K♠ 7♦ 2♣ found in dataset but not in expected scenarios=['N_mtt100_river']) |
| matcha-framework-srp-flop-decisions | mfsrpf_007 | no_dataset_match (board=J♠ T♠ 4♠ hand=A♥ Q♦ scenarios=['N_mtt100_river']) |
| matcha-framework-srp-flop-decisions | mfsrpf_008 | no_dataset_match (board=9♠ 8♦ 7♣ hand=T♥ 6♥ scenarios=['N_mtt100_river']) |
| matcha-framework-srp-flop-decisions | mfsrpf_009 | no_dataset_match (board=9♠ 8♦ 7♣ hand=6♥ 5♦ scenarios=['N_mtt100_river']) |
| matcha-framework-srp-flop-decisions | mfsrpf_010 | action_unparseable: 'ミディアムベット (66-75%)' |
| matcha-framework-srp-flop-decisions | mfsrpf_011 | no_dataset_match (board=J♠ T♠ 4♠ hand=A♠ 7♥ scenarios=['N_mtt100_river']) |
| matcha-framework-srp-flop-decisions | mfsrpf_012 | no_dataset_match (board=Q♥ J♦ 9♣ hand=K♠ K♦ scenarios=['N_mtt100_river']) |
| matcha-framework-srp-flop-decisions | mfsrpf_013 | action_unparseable: 'スモールベット (33%)、頻度約 80%' |
| matcha-framework-srp-flop-decisions | mfsrpf_014 | no_dataset_match (board=K♠ 7♦ 2♣ hand=A♥ K♠ scenarios=['N_mtt100_river']) |