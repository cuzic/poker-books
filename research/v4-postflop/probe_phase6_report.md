# Probe Phase 6 Report (MTT 4BP postflop + opener × flop)

生成: probe_phase6.py / scenarios=3 / all_rows=18148 / elapsed=67s

Section A: MTT 4BP postflop 全街 (matrix gap 最大)、Section B: opener × flop 補完

## ランキング

| ID | Target | n_combos | f_acc% | f_huge_loss | GTO huge_loss | bimodal% | opp_pol | opp_strong | opp_weak | opp_nut_pct |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **P6_A_mtt_4bp_river** | river_def_oop | 4324 | 60.6 | 30.194 | 42.643 | 9.6% | 0.772 | 0.529 | 0.243 | 0.142 |
| **P6_A_mtt_4bp_turn** | turn_def_oop | 6768 | 48.5 | 17.672 | 25.337 | 8.2% | 0.531 | 0.136 | 0.396 | 0.009 |
| **P6_A_mtt_4bp_flop** | flop_def_oop | 7056 | 40.3 | 5.278 | 19.416 | 21.4% | 0.646 | 0.086 | 0.561 | 0.01 |

## 詳細

### P6_A_mtt_4bp_river: MTT100 4BP × BB OOP river def
- target=river_def_oop, spots OK=4 FAIL=0 skipped(cached)=0, n_combos=4324
- ev_gap: mean=37.615, p90=132.618, max=154.8
- **formula**: acc=60.6%, huge_loss=30.194, huge%=33.0%
- modal: FOLD=40.3% CALL=59.7% RAISE=0.0%, bimodal_combo%=9.6%
- **opp range**: polarization=0.772 (strong=0.529 + weak=0.243), nut_pct=0.142, nut_eq_median=0.955
- per-family huge_loss: dry_high=46.718, dynamic=41.913, dynamic_2tone=43.08, low_dry=39.256
- per-board opp: d2t_T97: pol=1.00 nut_class=flush nut_pct=0.00; dry_K72: pol=0.41 nut_class=set nut_pct=0.03; dyn_T97: pol=1.00 nut_class=straight nut_pct=0.54; low_853: pol=0.69 nut_class=set nut_pct=0.00

### P6_A_mtt_4bp_turn: MTT100 4BP × BB OOP turn def
- target=turn_def_oop, spots OK=6 FAIL=0 skipped(cached)=0, n_combos=6768
- ev_gap: mean=24.848, p90=77.397, max=113.85
- **formula**: acc=48.5%, huge_loss=17.672, huge%=43.4%
- modal: FOLD=36.8% CALL=38.5% RAISE=24.6%, bimodal_combo%=8.2%
- **opp range**: polarization=0.531 (strong=0.136 + weak=0.396), nut_pct=0.009, nut_eq_median=0.942
- per-family huge_loss: dry_high=25.041, dynamic=24.335, dynamic_2tone=24.295, low_dry=26.894, monotone=26.202, paired=25.225
- per-board opp: d2t_T97: pol=0.56 nut_class=flush nut_pct=0.00; dry_K72: pol=0.39 nut_class=set nut_pct=0.01; dyn_T97: pol=0.54 nut_class=straight nut_pct=0.02; low_853: pol=0.58 nut_class=set nut_pct=0.00; mono_Js: pol=0.58 nut_class=flush nut_pct=0.01; pair_KK2: pol=0.54 nut_class=fullhouse nut_pct=0.01

### P6_A_mtt_4bp_flop: MTT100 4BP × BB OOP flop def (4BP postflop matrix 完成 — flop)
- target=flop_def_oop, spots OK=6 FAIL=0 skipped(cached)=0, n_combos=7056
- ev_gap: mean=17.422, p90=48.592, max=91.419
- **formula**: acc=40.3%, huge_loss=5.278, huge%=45.5%
- modal: FOLD=15.6% CALL=58.6% RAISE=25.8%, bimodal_combo%=21.4%
- **opp range**: polarization=0.646 (strong=0.086 + weak=0.561), nut_pct=0.01, nut_eq_median=0.954
- per-family huge_loss: dry_high=20.358, dynamic=20.221, dynamic_2tone=19.154, low_dry=18.459, monotone=18.792, paired=19.745
- per-board opp: d2t_T97: pol=0.67 nut_class=flush nut_pct=0.00; dry_K72: pol=0.58 nut_class=set nut_pct=0.00; dyn_T97: pol=0.65 nut_class=straight nut_pct=0.02; low_853: pol=0.60 nut_class=set nut_pct=0.01; mono_Js: pol=0.62 nut_class=flush nut_pct=0.01; pair_KK2: pol=0.78 nut_class=fullhouse nut_pct=0.01

