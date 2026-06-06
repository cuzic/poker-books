# Probe Phase 4 Report (BvB + SB defender + 4BP turn/river)

生成: probe_phase4.py / scenarios=4 / all_rows=17818 / elapsed=135s

Section A: 位置軸の最後のピース (BvB / SB defender)、Section B: 4BP pot type 完成 (turn/river)

## ランキング

| ID | Target | n_combos | f_acc% | f_huge_loss | GTO huge_loss | bimodal% | opp_pol | opp_strong | opp_weak | opp_nut_pct |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **N_cash_4bp_river** | river_def_oop | 6486 | 60.7 | 32.947 | 41.905 | 9.0% | 0.688 | 0.441 | 0.246 | 0.11 |
| **N_cash_4bp_turn** | turn_def_oop | 6768 | 49.4 | 15.798 | 23.899 | 8.3% | 0.542 | 0.138 | 0.405 | 0.012 |
| **N_btn_sb_river** | river_def_oop | 1077 | 73.0 | 13.965 | 14.285 | 7.2% | 0.942 | 0.635 | 0.308 | 0.258 |
| **N_bvb_srp_river** | river_def_oop | 3487 | 79.7 | 9.935 | 18.284 | 6.8% | 0.946 | 0.65 | 0.296 | 0.282 |

## 詳細

### N_cash_4bp_river: Cash100 4BP × BB OOP river def (SPR <1、4BP 完成)
- target=river_def_oop, spots OK=6 FAIL=0, n_combos=6486
- ev_gap: mean=36.99, p90=127.93, max=150.6
- **formula**: acc=60.7%, huge_loss=32.947, huge%=34.5%
- modal: FOLD=42.6% CALL=57.4% RAISE=0.0%, bimodal_combo%=9.0%
- **opp range**: polarization=0.688 (strong=0.441 + weak=0.246), nut_pct=0.11, nut_eq_median=0.946, hero_dominates_nut%=2.8
- per-family huge_loss: dry_high=41.624, dynamic=40.04, dynamic_2tone=39.94, low_dry=37.846, monotone=37.566, paired=56.46
- per-board opp: d2t_T97: pol=1.00 nut_class=flush nut_pct=0.00; dry_K72: pol=0.41 nut_class=set nut_pct=0.02; dyn_T97: pol=1.00 nut_class=straight nut_pct=0.56; low_853: pol=0.69 nut_class=set nut_pct=0.00; mono_Js: pol=0.59 nut_class=flush nut_pct=0.03; pair_KK2: pol=0.45 nut_class=fullhouse nut_pct=0.05

### N_cash_4bp_turn: Cash100 4BP × BB OOP turn def (SPR ~1、4BP turn 初取得)
- target=turn_def_oop, spots OK=6 FAIL=0, n_combos=6768
- ev_gap: mean=23.351, p90=73.677, max=109.263
- **formula**: acc=49.4%, huge_loss=15.798, huge%=43.1%
- modal: FOLD=38.6% CALL=37.4% RAISE=24.0%, bimodal_combo%=8.3%
- **opp range**: polarization=0.542 (strong=0.138 + weak=0.405), nut_pct=0.012, nut_eq_median=0.943, hero_dominates_nut%=2.4
- per-family huge_loss: dry_high=23.248, dynamic=22.943, dynamic_2tone=22.471, low_dry=25.798, monotone=24.952, paired=24.026
- per-board opp: d2t_T97: pol=0.57 nut_class=flush nut_pct=0.00; dry_K72: pol=0.39 nut_class=set nut_pct=0.00; dyn_T97: pol=0.55 nut_class=straight nut_pct=0.03; low_853: pol=0.58 nut_class=set nut_pct=0.00; mono_Js: pol=0.62 nut_class=flush nut_pct=0.02; pair_KK2: pol=0.54 nut_class=fullhouse nut_pct=0.02

### N_btn_sb_river: Cash100 BTN open × SB call (BB fold) × river SB OOP def
- target=river_def_oop, spots OK=6 FAIL=0, n_combos=1077
- ev_gap: mean=12.886, p90=37.495, max=126.9
- **formula**: acc=73.0%, huge_loss=13.965, huge%=18.1%
- modal: FOLD=63.6% CALL=26.9% RAISE=9.5%, bimodal_combo%=7.2%
- **opp range**: polarization=0.942 (strong=0.635 + weak=0.308), nut_pct=0.258, nut_eq_median=0.897, hero_dominates_nut%=4.1
- per-family huge_loss: dry_high=8.082, dynamic=9.802, dynamic_2tone=10.325, low_dry=25.818, monotone=6.748, paired=24.491
- per-board opp: d2t_T97: pol=0.96 nut_class=flush nut_pct=0.00; dry_K72: pol=0.75 nut_class=set nut_pct=0.17; dyn_T97: pol=0.97 nut_class=straight nut_pct=0.68; low_853: pol=0.98 nut_class=set nut_pct=0.00; mono_Js: pol=0.99 nut_class=flush nut_pct=0.50; pair_KK2: pol=1.00 nut_class=fullhouse nut_pct=0.21

### N_bvb_srp_river: Cash100 BvB SRP × SB OOP def (vs BB IP cbet → barrel → river bet)
- target=river_def_oop, spots OK=6 FAIL=0, n_combos=3487
- ev_gap: mean=17.777, p90=48.504, max=128.1
- **formula**: acc=79.7%, huge_loss=9.935, huge%=16.3%
- modal: FOLD=67.4% CALL=29.2% RAISE=3.5%, bimodal_combo%=6.8%
- **opp range**: polarization=0.946 (strong=0.65 + weak=0.296), nut_pct=0.282, nut_eq_median=0.949, hero_dominates_nut%=1.9
- per-family huge_loss: dry_high=21.303, dynamic=23.85, dynamic_2tone=27.411, low_dry=21.755, monotone=7.945, paired=7.693
- per-board opp: d2t_T97: pol=0.92 nut_class=flush nut_pct=0.00; dry_K72: pol=0.95 nut_class=set nut_pct=0.42; dyn_T97: pol=0.90 nut_class=straight nut_pct=0.68; low_853: pol=1.00 nut_class=set nut_pct=0.00; mono_Js: pol=0.99 nut_class=flush nut_pct=0.41; pair_KK2: pol=0.92 nut_class=fullhouse nut_pct=0.18

