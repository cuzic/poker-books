# Probe Phase 2 Report (残 scenario + Tier A 拡張)

生成: probe_phase2.py / scenarios=5 / all_rows=93366 / elapsed=9s

**目的**:
- Section A: probe_priority.py で quota 切れだった 残 2 scenario + N_mtt200_turn 残 2 boards
- Section B: Tier A 拡張 (4BP flop 18 boards / 3BP river 12 boards × 4 trajectories)

**注意**: probe_priority と同じく formula_huge_loss は audit と metric 違いのため絶対値比較不可。scenario 内 board variance / Tier A の board × family 分析が主目的。

## ランキング (formula_huge_loss 降順)

| Rank | ID | Target | GT/depth | n_combos | f_acc% | f_mean_loss | **f_huge_loss** | f_huge% | bimodal% | mean_gap | F/C/R% | ok/fail |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | **A_cash_3bp_river** | river_def_oop | Cash6mTest/100 | 51888 | 79.8 | 3.842 | **23.111** | 16.6 | 6.1% | 24.452 | 70.3/29.7/0.0% | 48/0 |
| 2 | **A_cash_4bp_flop** | flop_def_oop | Cash6mTest/100 | 21168 | 43.2 | 2.243 | **5.04** | 44.0 | 22.6% | 15.962 | 16.6/55.6/27.8% | 18/0 |
| 3 | **N_mtt200_river** | river_def_oop | MTTGeneral/200 | 6486 | 76.1 | 0.524 | **3.992** | 12.5 | 6.8% | 15.189 | 62.4/27.5/10.1% | 6/0 |
| 4 | **N_mtt200_turn** | turn_def_oop | MTTGeneral/200 | 6768 | 65.8 | 0.585 | **2.655** | 21.4 | 9.0% | 5.201 | 54.8/39.2/6.0% | 6/0 |
| 5 | **N_mtt_3bp_flop** | flop_def_oop | MTTGeneral/100 | 7056 | 64.1 | 0.525 | **2.583** | 19.3 | 19.6% | 6.167 | 29.0/61.3/9.7% | 6/0 |

## 詳細 (formula_huge_loss 降順)

### A_cash_3bp_river: Cash100 3BP river × BB def (EXTENDED 12 boards × 2 turn × 2 river / 21.8 BB loss 原因解析)
- GT=Cash6mTest_6mNL100R2 depth=100 target=river_def_oop
- spots OK=48 FAIL=0 n_combos=51888
- ev_gap: mean=24.452, p90=66.722, max=139.1
- GTO huge_loss (公式非依存): 26.824
- **formula**: acc=79.8%, mean_loss=3.842, huge_loss=23.111, huge%=16.6%
- modal split: FOLD=70.3% CALL=29.7% RAISE=0.0%, bimodal_combo%=6.1%
- per-board huge_loss: d2t_875=27.479 (n=4324), d2t_T97=31.272 (n=4324), dry_A94=21.962 (n=4324), dry_K72=22.061 (n=4324), dyn_986=28.493 (n=4324), dyn_T97=33.223 (n=4324), low_853=31.173 (n=4324), low_964=33.909 (n=4324), mono_Js=21.571 (n=4324), mono_Ts=23.139 (n=4324), pair_992=26.167 (n=4324), pair_KK2=21.718 (n=4324)
- per-family huge_loss: dry_high=22.012, dynamic=30.865, dynamic_2tone=29.364, low_dry=32.515, monotone=22.364, paired=23.969
- **opp range**: polarization=0.864 (strong=0.566 + weak=0.299), nut_pct=0.143, nut_eq_median=0.92, hero_dominates_nut%=4.3
- per-board opp: d2t_875: pol=0.73 nut_class=flush nut_pct=0.06; d2t_T97: pol=0.93 nut_class=flush nut_pct=0.00; dry_A94: pol=0.73 nut_class=set nut_pct=0.03; dry_K72: pol=0.73 nut_class=set nut_pct=0.06; dyn_986: pol=0.92 nut_class=straight nut_pct=0.24; dyn_T97: pol=0.91 nut_class=straight nut_pct=0.70; low_853: pol=1.00 nut_class=set nut_pct=0.00; low_964: pol=0.72 nut_class=set nut_pct=0.04; mono_Js: pol=1.00 nut_class=flush nut_pct=0.28; mono_Ts: pol=0.97 nut_class=flush nut_pct=0.28; pair_992: pol=0.78 nut_class=fullhouse nut_pct=0.09; pair_KK2: pol=0.92 nut_class=fullhouse nut_pct=0.12

### A_cash_4bp_flop: Cash100 4BP flop × BB def (EXTENDED 18 boards / SPR~1 公式破綻調査)
- GT=Cash6mTest_6mNL100R2 depth=100 target=flop_def_oop
- spots OK=18 FAIL=0 n_combos=21168
- ev_gap: mean=15.962, p90=44.442, max=93.053
- GTO huge_loss (公式非依存): 17.46
- **formula**: acc=43.2%, mean_loss=2.243, huge_loss=5.04, huge%=44.0%
- modal split: FOLD=16.6% CALL=55.6% RAISE=27.8%, bimodal_combo%=22.6%
- per-board huge_loss: d2t_875=17.019 (n=1176), d2t_J96=16.917 (n=1176), d2t_T97=17.337 (n=1176), dry_A94=18.816 (n=1176), dry_K72=18.261 (n=1176), dry_Q73=17.246 (n=1176), dyn_875=17.075 (n=1176), dyn_986=17.261 (n=1176), dyn_T97=18.736 (n=1176), low_752=17.35 (n=1176), low_853=16.737 (n=1176), low_964=16.508 (n=1176), mono_Js=17.005 (n=1176), mono_Qh=17.49 (n=1176), mono_Ts=17.332 (n=1176), pair_992=17.773 (n=1176), pair_J88=17.745 (n=1176), pair_KK2=18.202 (n=1176)
- per-family huge_loss: dry_high=18.084, dynamic=17.647, dynamic_2tone=17.09, low_dry=16.864, monotone=17.274, paired=17.901
- **opp range**: polarization=0.657 (strong=0.087 + weak=0.57), nut_pct=0.011, nut_eq_median=0.954, hero_dominates_nut%=0.8
- per-board opp: d2t_875: pol=0.64 nut_class=flush nut_pct=0.00; d2t_J96: pol=0.66 nut_class=flush nut_pct=0.00; d2t_T97: pol=0.67 nut_class=flush nut_pct=0.00; dry_A94: pol=0.57 nut_class=set nut_pct=0.00; dry_K72: pol=0.58 nut_class=set nut_pct=0.00; dry_Q73: pol=0.58 nut_class=set nut_pct=0.00; dyn_875: pol=0.64 nut_class=straight nut_pct=0.03; dyn_986: pol=0.64 nut_class=straight nut_pct=0.03; dyn_T97: pol=0.65 nut_class=straight nut_pct=0.03; low_752: pol=0.62 nut_class=set nut_pct=0.01; low_853: pol=0.61 nut_class=set nut_pct=0.00; low_964: pol=0.61 nut_class=set nut_pct=0.01; mono_Js: pol=0.63 nut_class=flush nut_pct=0.02; mono_Qh: pol=0.64 nut_class=flush nut_pct=0.02; mono_Ts: pol=0.65 nut_class=flush nut_pct=0.02; pair_992: pol=0.80 nut_class=fullhouse nut_pct=0.01; pair_J88: pol=0.85 nut_class=fullhouse nut_pct=0.01; pair_KK2: pol=0.77 nut_class=fullhouse nut_pct=0.01

### N_mtt200_river: MTT200 SRP river × BB def (deep)
- GT=MTTGeneral_8m depth=200 target=river_def_oop
- spots OK=6 FAIL=0 n_combos=6486
- ev_gap: mean=15.189, p90=29.171, max=190.443
- GTO huge_loss (公式非依存): 16.076
- **formula**: acc=76.1%, mean_loss=0.524, huge_loss=3.992, huge%=12.5%
- modal split: FOLD=62.4% CALL=27.5% RAISE=10.1%, bimodal_combo%=6.8%
- per-board huge_loss: d2t_T97=17.834 (n=1081), dry_K72=6.712 (n=1081), dyn_T97=17.085 (n=1081), low_853=31.702 (n=1081), mono_Js=12.836 (n=1081), pair_KK2=7.305 (n=1081)
- per-family huge_loss: dry_high=6.712, dynamic=17.085, dynamic_2tone=17.834, low_dry=31.702, monotone=12.836, paired=7.305
- **opp range**: polarization=0.843 (strong=0.599 + weak=0.244), nut_pct=0.198, nut_eq_median=0.955, hero_dominates_nut%=1.0
- per-board opp: d2t_T97: pol=0.82 nut_class=flush nut_pct=0.00; dry_K72: pol=0.70 nut_class=set nut_pct=0.08; dyn_T97: pol=0.81 nut_class=straight nut_pct=0.69; low_853: pol=1.00 nut_class=set nut_pct=0.00; mono_Js: pol=0.99 nut_class=flush nut_pct=0.30; pair_KK2: pol=0.74 nut_class=fullhouse nut_pct=0.12

### N_mtt200_turn: MTT200 SRP turn × BB def (残 2 boards 完了)
- GT=MTTGeneral_8m depth=200 target=turn_def_oop
- spots OK=6 FAIL=0 n_combos=6768
- ev_gap: mean=5.201, p90=12.054, max=125.908
- GTO huge_loss (公式非依存): 5.938
- **formula**: acc=65.8%, mean_loss=0.585, huge_loss=2.655, huge%=21.4%
- modal split: FOLD=54.8% CALL=39.2% RAISE=6.0%, bimodal_combo%=9.0%
- per-board huge_loss: d2t_T97=4.524 (n=1128), dry_K72=3.901 (n=1128), dyn_T97=4.521 (n=1128), low_853=12.755 (n=1128), mono_Js=4.408 (n=1128), pair_KK2=4.814 (n=1128)
- per-family huge_loss: dry_high=3.901, dynamic=4.521, dynamic_2tone=4.524, low_dry=12.755, monotone=4.408, paired=4.814
- **opp range**: polarization=0.697 (strong=0.248 + weak=0.448), nut_pct=0.047, nut_eq_median=0.954, hero_dominates_nut%=0.5
- per-board opp: d2t_T97: pol=0.70 nut_class=flush nut_pct=0.00; dry_K72: pol=0.46 nut_class=set nut_pct=0.03; dyn_T97: pol=0.69 nut_class=straight nut_pct=0.09; low_853: pol=0.90 nut_class=set nut_pct=0.00; mono_Js: pol=0.83 nut_class=flush nut_pct=0.12; pair_KK2: pol=0.60 nut_class=fullhouse nut_pct=0.03

### N_mtt_3bp_flop: MTT100 3BP flop × BB def
- GT=MTTGeneral_8m depth=100 target=flop_def_oop
- spots OK=6 FAIL=0 n_combos=7056
- ev_gap: mean=6.167, p90=16.241, max=56.619
- GTO huge_loss (公式非依存): 7.452
- **formula**: acc=64.1%, mean_loss=0.525, huge_loss=2.583, huge%=19.3%
- modal split: FOLD=29.0% CALL=61.3% RAISE=9.7%, bimodal_combo%=19.6%
- per-board huge_loss: d2t_T97=6.522 (n=1176), dry_K72=8.502 (n=1176), dyn_T97=7.152 (n=1176), low_853=7.231 (n=1176), mono_Js=7.023 (n=1176), pair_KK2=8.778 (n=1176)
- per-family huge_loss: dry_high=8.502, dynamic=7.152, dynamic_2tone=6.522, low_dry=7.231, monotone=7.023, paired=8.778
- **opp range**: polarization=0.717 (strong=0.127 + weak=0.589), nut_pct=0.025, nut_eq_median=0.957, hero_dominates_nut%=0.6
- per-board opp: d2t_T97: pol=0.78 nut_class=flush nut_pct=0.00; dry_K72: pol=0.61 nut_class=set nut_pct=0.01; dyn_T97: pol=0.75 nut_class=straight nut_pct=0.07; low_853: pol=0.67 nut_class=set nut_pct=0.01; mono_Js: pol=0.68 nut_class=flush nut_pct=0.05; pair_KK2: pol=0.81 nut_class=fullhouse nut_pct=0.01

