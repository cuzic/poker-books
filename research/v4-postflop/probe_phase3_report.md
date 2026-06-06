# Probe Phase 3 Report (Tier C 拡張 + 3BP allin + 位置軸)

生成: probe_phase3.py / scenarios=5 / all_rows=24991 / elapsed=23s

Section A: Tier C 拡張 (CR/donk 防御 18 boards)、Section B: R1 を 3BP に拡張、Section C: opener 位置軸

## ランキング

| ID | Target | n_combos | f_acc% | f_huge_loss | GTO huge_loss | bimodal% | opp_pol | opp_strong | opp_weak | opp_nut_pct |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **N_cash_co_open_river** | river_def_oop | 3338 | 82.9 | 3.511 | 14.518 | 9.3% | 0.918 | 0.621 | 0.297 | 0.224 |
| **N_cash_hj_open_river** | river_def_oop | 2941 | 80.3 | 3.36 | 12.571 | 11.4% | 0.938 | 0.623 | 0.315 | 0.221 |
| **A_cash_cr_def_full** | flop_def_ip_cr | 9356 | — | — | 5.787 | 15.7% | 0.693 | 0.24 | 0.453 | 0.082 |
| **A_cash_donk_def_full** | flop_def_ip_donk | 9356 | — | — | 2.8 | 17.8% | 0.782 | 0.173 | 0.609 | 0.066 |
| **N_cash_3bp_river_allin** | river_def_ip_allin | 0 | — | — | 0 | 0% | — | — | — | — |

## 詳細

### N_cash_co_open_river: Cash100 CO open × BB call SRP × river BB def (opener position diff)
- target=river_def_oop, spots OK=6 FAIL=0, n_combos=3338
- ev_gap: mean=13.425, p90=28.348, max=123.454
- **formula**: acc=82.9%, huge_loss=3.511, huge%=8.5%
- modal: FOLD=72.3% CALL=18.6% RAISE=9.1%, bimodal_combo%=9.3%
- **opp range**: polarization=0.918 (strong=0.621 + weak=0.297), nut_pct=0.224, nut_eq_median=0.944, hero_dominates_nut%=1.4
- per-family huge_loss: dry_high=21.886, dynamic=8.341, dynamic_2tone=28.923, low_dry=9.401, monotone=9.019, paired=9.262
- per-board opp: d2t_T97: pol=0.88 nut_class=flush nut_pct=0.00; dry_K72: pol=0.76 nut_class=set nut_pct=0.14; dyn_T97: pol=0.92 nut_class=straight nut_pct=0.65; low_853: pol=0.97 nut_class=set nut_pct=0.00; mono_Js: pol=0.98 nut_class=flush nut_pct=0.49; pair_KK2: pol=0.99 nut_class=fullhouse nut_pct=0.07

### N_cash_hj_open_river: Cash100 HJ open × BB call SRP × river BB def (opener position diff)
- target=river_def_oop, spots OK=6 FAIL=0, n_combos=2941
- ev_gap: mean=11.625, p90=27.702, max=83.528
- **formula**: acc=80.3%, huge_loss=3.36, huge%=9.3%
- modal: FOLD=68.7% CALL=22.8% RAISE=8.6%, bimodal_combo%=11.4%
- **opp range**: polarization=0.938 (strong=0.623 + weak=0.315), nut_pct=0.221, nut_eq_median=0.95, hero_dominates_nut%=1.1
- per-family huge_loss: dry_high=21.925, dynamic=13.332, dynamic_2tone=10.676, low_dry=11.568, monotone=8.768, paired=9.633
- per-board opp: d2t_T97: pol=0.96 nut_class=flush nut_pct=0.00; dry_K72: pol=0.75 nut_class=set nut_pct=0.16; dyn_T97: pol=0.98 nut_class=straight nut_pct=0.68; low_853: pol=0.97 nut_class=set nut_pct=0.00; mono_Js: pol=0.99 nut_class=flush nut_pct=0.47; pair_KK2: pol=0.98 nut_class=fullhouse nut_pct=0.02

### A_cash_cr_def_full: Cash100 SRP × BTN IP def vs BB CR (EXTENDED 18 boards)
- target=flop_def_ip_cr, spots OK=18 FAIL=0, n_combos=9356
- ev_gap: mean=4.374, p90=12.62, max=48.656
- **formula**: 適用外 (CR/donk/IP defender)
- modal: FOLD=46.3% CALL=48.0% RAISE=5.7%, bimodal_combo%=15.7%
- **opp range**: polarization=0.693 (strong=0.24 + weak=0.453), nut_pct=0.082, nut_eq_median=0.922, hero_dominates_nut%=0.5
- per-family huge_loss: dry_high=7.283, dynamic=7.222, dynamic_2tone=6.52, low_dry=3.38, monotone=3.491, paired=5.878
- per-board opp: d2t_875: pol=0.60 nut_class=flush nut_pct=0.00; d2t_J96: pol=0.81 nut_class=flush nut_pct=0.00; d2t_T97: pol=0.78 nut_class=flush nut_pct=0.00; dry_A94: pol=0.60 nut_class=set nut_pct=0.08; dry_K72: pol=0.46 nut_class=set nut_pct=0.04; dry_Q73: pol=0.79 nut_class=set nut_pct=0.09; dyn_875: pol=0.66 nut_class=straight nut_pct=0.12; dyn_986: pol=0.68 nut_class=straight nut_pct=0.12; dyn_T97: pol=0.79 nut_class=straight nut_pct=0.14; low_752: pol=0.58 nut_class=set nut_pct=0.12; low_853: pol=0.53 nut_class=set nut_pct=0.11; low_964: pol=0.56 nut_class=set nut_pct=0.10; mono_Js: pol=0.74 nut_class=flush nut_pct=0.15; mono_Qh: pol=0.81 nut_class=flush nut_pct=0.17; mono_Ts: pol=0.76 nut_class=flush nut_pct=0.16; pair_992: pol=0.79 nut_class=fullhouse nut_pct=0.02; pair_J88: pol=0.77 nut_class=fullhouse nut_pct=0.03; pair_KK2: pol=0.78 nut_class=fullhouse nut_pct=0.02

### A_cash_donk_def_full: Cash100 SRP × BTN IP def vs BB donk (EXTENDED 18 boards)
- target=flop_def_ip_donk, spots OK=18 FAIL=0, n_combos=9356
- ev_gap: mean=1.96, p90=4.62, max=33.293
- **formula**: 適用外 (CR/donk/IP defender)
- modal: FOLD=48.8% CALL=42.5% RAISE=8.7%, bimodal_combo%=17.8%
- **opp range**: polarization=0.782 (strong=0.173 + weak=0.609), nut_pct=0.066, nut_eq_median=0.936, hero_dominates_nut%=0.5
- per-family huge_loss: dry_high=2.786, dynamic=2.455, dynamic_2tone=2.607, low_dry=2.398, monotone=2.627, paired=4.468
- per-board opp: d2t_875: pol=0.81 nut_class=flush nut_pct=0.00; d2t_J96: pol=0.67 nut_class=flush nut_pct=0.00; d2t_T97: pol=0.86 nut_class=flush nut_pct=0.00; dry_A94: pol=0.66 nut_class=set nut_pct=0.08; dry_K72: pol=0.55 nut_class=set nut_pct=0.02; dry_Q73: pol=0.77 nut_class=set nut_pct=0.07; dyn_875: pol=0.75 nut_class=straight nut_pct=0.07; dyn_986: pol=0.69 nut_class=straight nut_pct=0.07; dyn_T97: pol=0.84 nut_class=straight nut_pct=0.13; low_752: pol=0.66 nut_class=set nut_pct=0.04; low_853: pol=0.75 nut_class=set nut_pct=0.06; low_964: pol=0.81 nut_class=set nut_pct=0.06; mono_Js: pol=0.84 nut_class=flush nut_pct=0.17; mono_Qh: pol=0.77 nut_class=flush nut_pct=0.17; mono_Ts: pol=0.73 nut_class=flush nut_pct=0.11; pair_992: pol=0.98 nut_class=fullhouse nut_pct=0.03; pair_J88: pol=0.97 nut_class=fullhouse nut_pct=0.07; pair_KK2: pol=0.97 nut_class=fullhouse nut_pct=0.03

### N_cash_3bp_river_allin: Cash100 3BP × BTN IP def vs BB river allin shove (3BP context、R1=SRP の対比)
- target=river_def_ip_allin, spots OK=0 FAIL=6, n_combos=0
- ev_gap: mean=0, p90=0, max=0
- **formula**: 適用外 (CR/donk/IP defender)
- modal: FOLD=0% CALL=0% RAISE=0%, bimodal_combo%=0%

