# Probe Phase 5 Report (A→D→B→C 順)

生成: probe_phase5.py / scenarios=10 / all_rows=59472 / elapsed=24s

Section A: pot-type × street matrix 完成、Section D: multi-street donk/CR、Section B: 高 bleed deep-dive、Section C: opener × turn 補完

## ランキング (formula_huge_loss 降順、formula N/A は後)

| ID | Target | n_combos | f_acc% | f_huge_loss | GTO huge_loss | bimodal% | opp_pol | opp_strong | opp_weak | opp_nut_pct |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **P5_B_4bp_river_traj** | river_def_oop | 17296 | 60.5 | 38.631 | 43.375 | 11.1% | 0.638 | 0.373 | 0.266 | 0.168 |
| **P5_A_mtt_3bp_river** | river_def_oop | 6486 | 77.1 | 28.654 | 29.202 | 6.6% | 0.87 | 0.588 | 0.282 | 0.181 |
| **P5_B_3bp_river_extra** | river_def_oop | 6486 | 78.0 | 22.466 | 24.89 | 5.6% | 0.9 | 0.607 | 0.292 | 0.159 |
| **P5_A_cash_3bp_turn** | turn_def_oop | 6768 | 66.3 | 5.054 | 12.478 | 9.9% | 0.711 | 0.286 | 0.424 | 0.052 |
| **P5_A_mtt_3bp_turn** | turn_def_oop | 6768 | 66.5 | 5.002 | 13.116 | 8.6% | 0.714 | 0.27 | 0.444 | 0.048 |
| **P5_C_co_open_turn** | turn_def_oop | 3477 | 71.9 | 2.432 | 6.085 | 9.2% | 0.747 | 0.265 | 0.481 | 0.041 |
| **P5_C_hj_open_turn** | turn_def_oop | 3065 | 72.1 | 1.678 | 4.967 | 7.3% | 0.786 | 0.278 | 0.507 | 0.035 |
| **P5_D_turn_cr_def** | turn_def_ip_cr | 3093 | — | — | 9.373 | 6.4% | 0.808 | 0.463 | 0.345 | 0.175 |
| **P5_D_river_donk_def** | river_def_ip_donk | 2940 | — | — | 4.689 | 9.7% | 0.663 | 0.432 | 0.231 | 0.101 |
| **P5_D_turn_donk_def** | turn_def_ip_donk | 3093 | — | — | 3.362 | 16.0% | 0.696 | 0.155 | 0.541 | 0.04 |

## 詳細

### P5_B_4bp_river_traj: Cash100 4BP × BB OOP river def (4 boards × 2 turn × 2 river, trajectory variance)
- target=river_def_oop, spots OK=0 FAIL=0 skipped(cached)=16, n_combos=17296
- ev_gap: mean=36.969, p90=118.954, max=150.6
- **formula**: acc=60.5%, huge_loss=38.631, huge%=34.1%
- modal: FOLD=47.2% CALL=52.8% RAISE=0.0%, bimodal_combo%=11.1%
- **opp range**: polarization=0.638 (strong=0.373 + weak=0.266), nut_pct=0.168, nut_eq_median=0.925
- per-family huge_loss: dry_high=41.584, dynamic=44.597, monotone=40.301, paired=47.439
- per-board opp: dry_K72: pol=0.41 nut_class=set nut_pct=0.02; dyn_T97: pol=1.00 nut_class=straight nut_pct=0.56; mono_Js: pol=0.59 nut_class=flush nut_pct=0.03; pair_KK2: pol=0.45 nut_class=fullhouse nut_pct=0.05

### P5_A_mtt_3bp_river: MTT100 3BP × BB OOP river def
- target=river_def_oop, spots OK=0 FAIL=0 skipped(cached)=6, n_combos=6486
- ev_gap: mean=26.241, p90=93.257, max=143.6
- **formula**: acc=77.1%, huge_loss=28.654, huge%=19.5%
- modal: FOLD=68.1% CALL=31.9% RAISE=0.0%, bimodal_combo%=6.6%
- **opp range**: polarization=0.87 (strong=0.588 + weak=0.282), nut_pct=0.181, nut_eq_median=0.947
- per-family huge_loss: dry_high=22.406, dynamic=34.858, dynamic_2tone=32.926, low_dry=31.507, monotone=21.558, paired=32.336
- per-board opp: d2t_T97: pol=0.94 nut_class=flush nut_pct=0.00; dry_K72: pol=0.67 nut_class=set nut_pct=0.06; dyn_T97: pol=0.92 nut_class=straight nut_pct=0.71; low_853: pol=1.00 nut_class=set nut_pct=0.00; mono_Js: pol=1.00 nut_class=flush nut_pct=0.24; pair_KK2: pol=0.69 nut_class=fullhouse nut_pct=0.07

### P5_B_3bp_river_extra: Cash100 3BP × BB OOP river def (EXTRA 6 boards、phase2 未使用)
- target=river_def_oop, spots OK=0 FAIL=0 skipped(cached)=6, n_combos=6486
- ev_gap: mean=22.608, p90=65.705, max=139.1
- **formula**: acc=78.0%, huge_loss=22.466, huge%=17.8%
- modal: FOLD=71.2% CALL=28.8% RAISE=0.0%, bimodal_combo%=5.6%
- **opp range**: polarization=0.9 (strong=0.607 + weak=0.292), nut_pct=0.159, nut_eq_median=0.778
- per-family huge_loss: dry_high=24.581, dynamic=24.794, dynamic_2tone=26.162, low_dry=33.531, monotone=23.585, paired=16.929
- per-board opp: d2t_J96: pol=0.81 nut_class=flush nut_pct=0.00; dry_Q73: pol=0.99 nut_class=set nut_pct=0.08; dyn_875: pol=0.99 nut_class=straight nut_pct=0.19; low_752: pol=0.73 nut_class=set nut_pct=0.05; mono_Qh: pol=0.88 nut_class=flush nut_pct=0.45; pair_J88: pol=1.00 nut_class=fullhouse nut_pct=0.20

### P5_A_cash_3bp_turn: Cash100 3BP × BB OOP turn def (3BP turn 初取得)
- target=turn_def_oop, spots OK=0 FAIL=0 skipped(cached)=6, n_combos=6768
- ev_gap: mean=11.385, p90=25.097, max=86.214
- **formula**: acc=66.3%, huge_loss=5.054, huge%=23.4%
- modal: FOLD=58.2% CALL=33.3% RAISE=8.5%, bimodal_combo%=9.9%
- **opp range**: polarization=0.711 (strong=0.286 + weak=0.424), nut_pct=0.052, nut_eq_median=0.951
- per-family huge_loss: dry_high=9.616, dynamic=15.842, dynamic_2tone=15.938, low_dry=12.41, monotone=8.831, paired=11.723
- per-board opp: d2t_T97: pol=0.69 nut_class=flush nut_pct=0.00; dry_K72: pol=0.67 nut_class=set nut_pct=0.02; dyn_T97: pol=0.67 nut_class=straight nut_pct=0.12; low_853: pol=0.73 nut_class=set nut_pct=0.00; mono_Js: pol=0.93 nut_class=flush nut_pct=0.14; pair_KK2: pol=0.58 nut_class=fullhouse nut_pct=0.03

### P5_A_mtt_3bp_turn: MTT100 3BP × BB OOP turn def
- target=turn_def_oop, spots OK=0 FAIL=0 skipped(cached)=6, n_combos=6768
- ev_gap: mean=12.41, p90=29.873, max=91.434
- **formula**: acc=66.5%, huge_loss=5.002, huge%=23.9%
- modal: FOLD=57.7% CALL=33.1% RAISE=9.3%, bimodal_combo%=8.6%
- **opp range**: polarization=0.714 (strong=0.27 + weak=0.444), nut_pct=0.048, nut_eq_median=0.954
- per-family huge_loss: dry_high=11.067, dynamic=16.436, dynamic_2tone=16.853, low_dry=14.098, monotone=9.934, paired=9.776
- per-board opp: d2t_T97: pol=0.68 nut_class=flush nut_pct=0.00; dry_K72: pol=0.62 nut_class=set nut_pct=0.02; dyn_T97: pol=0.64 nut_class=straight nut_pct=0.11; low_853: pol=0.68 nut_class=set nut_pct=0.00; mono_Js: pol=0.93 nut_class=flush nut_pct=0.13; pair_KK2: pol=0.74 nut_class=fullhouse nut_pct=0.02

### P5_C_co_open_turn: Cash100 CO open × BB call × BB OOP turn def (opener position turn)
- target=turn_def_oop, spots OK=0 FAIL=0 skipped(cached)=6, n_combos=3477
- ev_gap: mean=5.429, p90=14.25, max=45.293
- **formula**: acc=71.9%, huge_loss=2.432, huge%=15.2%
- modal: FOLD=64.8% CALL=29.2% RAISE=5.9%, bimodal_combo%=9.2%
- **opp range**: polarization=0.747 (strong=0.265 + weak=0.481), nut_pct=0.041, nut_eq_median=0.941
- per-family huge_loss: dry_high=9.994, dynamic=2.985, dynamic_2tone=13.319, low_dry=2.701, monotone=3.037, paired=2.582
- per-board opp: d2t_T97: pol=0.69 nut_class=flush nut_pct=0.00; dry_K72: pol=0.72 nut_class=set nut_pct=0.04; dyn_T97: pol=0.77 nut_class=straight nut_pct=0.04; low_853: pol=0.76 nut_class=set nut_pct=0.00; mono_Js: pol=0.75 nut_class=flush nut_pct=0.15; pair_KK2: pol=0.80 nut_class=fullhouse nut_pct=0.01

### P5_C_hj_open_turn: Cash100 HJ open × BB call × BB OOP turn def (opener position turn)
- target=turn_def_oop, spots OK=0 FAIL=0 skipped(cached)=6, n_combos=3065
- ev_gap: mean=4.478, p90=12.168, max=37.261
- **formula**: acc=72.1%, huge_loss=1.678, huge%=13.2%
- modal: FOLD=63.4% CALL=30.1% RAISE=6.6%, bimodal_combo%=7.3%
- **opp range**: polarization=0.786 (strong=0.278 + weak=0.507), nut_pct=0.035, nut_eq_median=0.933
- per-family huge_loss: dry_high=9.761, dynamic=7.648, dynamic_2tone=3.002, low_dry=2.437, monotone=2.824, paired=2.831
- per-board opp: d2t_T97: pol=0.76 nut_class=flush nut_pct=0.00; dry_K72: pol=0.70 nut_class=set nut_pct=0.05; dyn_T97: pol=0.88 nut_class=straight nut_pct=0.00; low_853: pol=0.82 nut_class=set nut_pct=0.00; mono_Js: pol=0.75 nut_class=flush nut_pct=0.16; pair_KK2: pol=0.81 nut_class=fullhouse nut_pct=0.00

### P5_D_turn_cr_def: Cash100 SRP × BTN IP def vs BB turn CR (after flop X-cbet-C, turn X-barrel)
- target=turn_def_ip_cr, spots OK=6 FAIL=0 skipped(cached)=0, n_combos=3093
- ev_gap: mean=9.279, p90=17.011, max=116.412
- **formula**: 適用外 (CR/donk/IP defender)
- modal: FOLD=75.7% CALL=20.4% RAISE=4.0%, bimodal_combo%=6.4%
- **opp range**: polarization=0.808 (strong=0.463 + weak=0.345), nut_pct=0.175, nut_eq_median=0.878
- per-family huge_loss: dry_high=11.633, dynamic=12.707, dynamic_2tone=10.573, low_dry=10.625, monotone=6.016, paired=4.496
- per-board opp: d2t_T97: pol=0.69 nut_class=flush nut_pct=0.00; dry_K72: pol=0.72 nut_class=set nut_pct=0.36; dyn_T97: pol=0.71 nut_class=straight nut_pct=0.30; low_853: pol=0.90 nut_class=set nut_pct=0.00; mono_Js: pol=0.82 nut_class=flush nut_pct=0.28; pair_KK2: pol=0.99 nut_class=fullhouse nut_pct=0.12

### P5_D_river_donk_def: Cash100 SRP × BTN IP def vs BB river donk (after flop X-cbet-C, turn X-X)
- target=river_def_ip_donk, spots OK=0 FAIL=0 skipped(cached)=6, n_combos=2940
- ev_gap: mean=3.563, p90=7.866, max=44.101
- **formula**: 適用外 (CR/donk/IP defender)
- modal: FOLD=35.6% CALL=46.4% RAISE=18.0%, bimodal_combo%=9.7%
- **opp range**: polarization=0.663 (strong=0.432 + weak=0.231), nut_pct=0.101, nut_eq_median=0.965
- per-family huge_loss: dry_high=4.345, dynamic=3.695, dynamic_2tone=4.104, low_dry=6.2, monotone=4.418, paired=4.708
- per-board opp: d2t_T97: pol=0.91 nut_class=flush nut_pct=0.00; dry_K72: pol=0.28 nut_class=set nut_pct=0.00; dyn_T97: pol=0.91 nut_class=straight nut_pct=0.45; low_853: pol=0.96 nut_class=set nut_pct=0.00; mono_Js: pol=0.40 nut_class=flush nut_pct=0.13; pair_KK2: pol=0.53 nut_class=fullhouse nut_pct=0.03

### P5_D_turn_donk_def: Cash100 SRP × BTN IP def vs BB turn donk (after flop X-X)
- target=turn_def_ip_donk, spots OK=0 FAIL=0 skipped(cached)=6, n_combos=3093
- ev_gap: mean=2.147, p90=6.188, max=24.041
- **formula**: 適用外 (CR/donk/IP defender)
- modal: FOLD=39.6% CALL=55.9% RAISE=4.5%, bimodal_combo%=16.0%
- **opp range**: polarization=0.696 (strong=0.155 + weak=0.541), nut_pct=0.04, nut_eq_median=0.959
- per-family huge_loss: dry_high=3.813, dynamic=3.266, dynamic_2tone=3.032, low_dry=4.573, monotone=2.504, paired=3.744
- per-board opp: d2t_T97: pol=0.74 nut_class=flush nut_pct=0.00; dry_K72: pol=0.50 nut_class=set nut_pct=0.02; dyn_T97: pol=0.72 nut_class=straight nut_pct=0.05; low_853: pol=0.62 nut_class=set nut_pct=0.00; mono_Js: pol=0.92 nut_class=flush nut_pct=0.15; pair_KK2: pol=0.67 nut_class=fullhouse nut_pct=0.02

