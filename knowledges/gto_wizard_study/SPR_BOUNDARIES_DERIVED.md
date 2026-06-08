# SPR 境界の実測 — 293K rows データから逆算

既存 unified dataset (Phase 1-6 統合、Cash/MTT/SRP/3BP/4BP/Defense 全網羅) 
から SPR を scenario_id × street × pot_type で逆算し、
SPR bin ごとの GTO 行動 (fold/call/raise) を集計。

## SPR 推定ルール

| pot_type | street | 推定 SPR | 計算根拠 |
|----------|--------|---------:|---------|
| SRP | flop  | 16  | pot 6, stack 97 (Cash100bb, open 2.6) |
| SRP | turn  | 7.5 | pot ~12, stack ~94 (after 50% cbet) |
| SRP | river | 3.0 | pot ~28, stack ~86 (after 2 barrels) |
| 3BP | flop  | 3.4 | pot 25, stack 85 |
| 3BP | turn  | 1.4 | pot 50, stack 70 |
| 3BP | river | 0.55| pot ~100, stack ~50 |
| 4BP | flop  | 1.3 | pot 55, stack 70 |
| 4BP | turn  | 0.5 | pot ~100, stack ~50 |
| 4BP | river | 0.17| pot ~150, stack ~25 |
| DEF | flop  | 4.0 | CR/donk raised pot ~22 |

MTT depth 補正: SPR × (depth/100)。MTT25 → 25%、MTT50 → 50%、MTT200 → 200%

## SPR bin ごとの GTO 行動

| SPR bin | n | fold% | call% | raise% | avg EV gap |
|---------|--:|---:|---:|---:|---:|
| オールイン(<1) | 120,978 | 59.0% | 37.8% | 3.2% | 26.176 |
| ロー(1-3) | 55,002 | 30.8% | 46.9% | 22.3% | 13.981 |
| ミディアム(3-7) | 66,602 | 53.0% | 37.8% | 9.2% | 9.546 |
| ディープ(7-15) | 10,442 | 64.9% | 28.9% | 6.2% | 4.612 |
| ベリーディープ(>15) | 40,295 | 78.9% | 17.8% | 3.3% | 33.452 |

## mv_cat × SPR bin の raise 頻度

| mv_cat | オールイン( | ロー(1-3 | ミディアム( | ディープ(7 | ベリーディー |
|---|---|---|---|---|---|
| no_made_hand | 1% | 13% | 6% | 8% | 4% |
| ace_high | 2% | 14% | 5% | 4% | 2% |
| king_high | 1% | 12% | 4% | 2% | 2% |
| low_pair | 0% | 1% | 2% | 0% | 0% |
| third_pair | 3% | 14% | 7% | 3% | 2% |
| second_pair | 9% | 39% | 11% | 3% | 3% |
| underpair | 14% | 45% | 8% | 1% | 7% |
| top_pair | 11% | 60% | 13% | 3% | 2% |
| overpair | 13% | 60% | 29% | 2% | 4% |
| two_pair | 5% | 35% | 12% | 14% | 4% |
| trips | 7% | 47% | 16% | 13% | 12% |
| set | 7% | 32% | 25% | 45% | 9% |
| straight | 2% | 39% | 21% | 96% | 8% |
| flush | 3% | 3% | 13% | 14% | 5% |
| fullhouse | 1% | 9% | 39% | 37% | 1% |

## SPR bin 間の行動変化 (隣接 bin 差)

| SPR transition | fold 差 | call 差 | raise 差 | 解釈 |
|---|---:|---:|---:|---|
| オールイン(<1) → ロー(1-3) | -28.2% | +9.1% | +19.1% | fold 減, call 増, raise 増 |
| ロー(1-3) → ミディアム(3-7) | +22.3% | -9.1% | -13.1% | fold 増, call 減, raise 減 |
| ミディアム(3-7) → ディープ(7-15) | +11.9% | -8.9% | -3.0% | fold 増, call 減 |
| ディープ(7-15) → ベリーディープ(>15) | +14.0% | -11.2% | -2.8% | fold 増, call 減 |

## scenario × 推定 SPR

| scenario_id | pot | street | 推定 SPR | n rows |
|---|---|---|---:|---:|
| N_cash_4bp_river | 4BP | river | 0.17 | 6,486 |
| P5_B_4bp_river_traj | 4BP | river | 0.17 | 17,296 |
| P6_A_mtt_4bp_river | 4BP | river | 0.17 | 4,324 |
| N_cash_4bp_turn | 4BP | turn | 0.50 | 6,768 |
| P6_A_mtt_4bp_turn | 4BP | turn | 0.50 | 6,768 |
| N_cash_3bp_river | 3BP | river | 0.55 | 6,486 |
| A_cash_3bp_river | 3BP | river | 0.55 | 51,888 |
| P5_A_mtt_3bp_river | 3BP | river | 0.55 | 6,486 |
| P5_B_3bp_river_extra | 3BP | river | 0.55 | 6,486 |
| N_mtt25_river | SRP | river | 0.75 | 5,050 |
| P5_D_river_donk_def | DEF | river | 0.80 | 2,940 |
| N_cash_4bp_flop | 4BP | flop | 1.30 | 7,056 |
| A_cash_4bp_flop | 4BP | flop | 1.30 | 21,168 |
| P6_A_mtt_4bp_flop | 4BP | flop | 1.30 | 7,056 |
| P5_A_cash_3bp_turn | 3BP | turn | 1.40 | 6,768 |
| P5_A_mtt_3bp_turn | 3BP | turn | 1.40 | 6,768 |
| P5_D_turn_donk_def | DEF | turn | 2.00 | 3,093 |
| P5_D_turn_cr_def | DEF | turn | 2.00 | 3,093 |
| B_river | SRP | river | 3.00 | 3,709 |
| N_mtt100_river | SRP | river | 3.00 | 6,486 |
| N_cash_hj_open_river | SRP | river | 3.00 | 2,941 |
| N_cash_co_open_river | SRP | river | 3.00 | 3,338 |
| N_bvb_srp_river | SRP | river | 3.00 | 3,487 |
| N_btn_sb_river | SRP | river | 3.00 | 1,077 |
| N_mtt_3bp_flop | 3BP | flop | 3.40 | 7,056 |
| N_cash_3bp_flop | 3BP | flop | 3.40 | 7,056 |
| N_cash_cr_def | DEF | flop | 4.00 | 3,127 |
| N_cash_donk_def | DEF | flop | 4.00 | 3,127 |
| A_cash_cr_def_full | DEF | flop | 4.00 | 9,356 |
| A_cash_donk_def_full | DEF | flop | 4.00 | 9,356 |
| N_mtt200_river | SRP | river | 6.00 | 6,486 |
| B_turn | SRP | turn | 7.50 | 3,900 |
| P5_C_hj_open_turn | SRP | turn | 7.50 | 3,065 |
| P5_C_co_open_turn | SRP | turn | 7.50 | 3,477 |
| N_mtt200_turn | SRP | turn | 15.00 | 6,768 |
| B_flop | SRP | flop | 16.00 | 3,996 |
| R1_past | SRP | preflop | 16.00 | 29,531 |

## MATCHA SPR 4 段階との対応

| MATCHA tier | SPR 範囲 | データ上の検証 |
|-------------|---------|---------------|
| オールイン | <1 | 4BP turn/river, 3BP river — fold/call 中心 (raise が allin か) |
| ロー | 1-3 | 4BP flop, 3BP turn — set/2pair 強気、TP pot-control |
| ミディアム | 3-7 | 3BP flop, SRP river, DEF — value/bluff 分離 |
| ディープ | >7 | SRP flop/turn — protect range, 多 sizing |

実測の bin 行動差を見て、4 段階の境界が data に裏付けされるか検証。
もし bin 間で行動差が小さい (<5%) なら統合検討、大きい (>15%) なら境界明確。