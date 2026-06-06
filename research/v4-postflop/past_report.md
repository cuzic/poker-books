# Past JSON Re-extraction Report

R1 hand-level rows: 29531
R1 spot summaries: 62
R3 spot summaries: 48

## R1: BB river allin shove range structure (per board family)

BTN as IP defender 視点で、BB が river で allin shove する range の structure。polarization が低い board = BB の shove に bluff が薄い (call すべき場面少)。

| family | n_spots | opp_polarization | opp_strong_pct | opp_weak_pct | opp_nut_class | opp_nut_pct | opp_nut_eq_median |
|---|---:|---:|---:|---:|---|---:|---:|
| dry_high | 12 | 0.749 | 0.743 | 0.006 | set | 0.103 | 0.706 |
| dynamic | 12 | 0.789 | 0.725 | 0.064 | straight | 0.411 | 0.705 |
| dynamic_2tone | 9 | 0.765 | 0.734 | 0.031 | flush | 0.208 | 0.868 |
| low_dry | 3 | 0.849 | 0.848 | 0.0 | set | 0.043 | 0.826 |
| monotone | 15 | 0.755 | 0.706 | 0.048 | flush | 0.473 | 0.628 |
| paired | 11 | 0.848 | 0.825 | 0.023 | fullhouse | 0.531 | 0.755 |

## R3: BB donk range vs BTN cbet range (initiator structure)

R3 _open は BB の flop initial 行動 (donk or check) を含む node、_ip_post_check は BTN が BB の check に対して cbet するか考える node。
hero 側 (initiator) の range structure と、opp 側の range structure を比較。

### R3 _open (n=24)

| family | n | hero_polarization | hero_strong | opp_polarization | opp_strong | opp_weak |
|---|---:|---:|---:|---:|---:|---:|
| dry_high | 4 | 0.636 | 0.029 | 0.615 | 0.052 | 0.564 |
| dynamic | 4 | 0.65 | 0.099 | 0.679 | 0.135 | 0.544 |
| dynamic_2tone | 4 | 0.617 | 0.047 | 0.667 | 0.096 | 0.571 |
| low_dry | 4 | 0.667 | 0.036 | 0.769 | 0.092 | 0.677 |
| monotone | 4 | 0.633 | 0.098 | 0.637 | 0.122 | 0.514 |
| paired | 4 | 0.865 | 0.102 | 0.883 | 0.152 | 0.73 |

### R3 _ip_post_check (n=24)

| family | n | hero_polarization | hero_strong | opp_polarization | opp_strong | opp_weak |
|---|---:|---:|---:|---:|---:|---:|
| dry_high | 4 | 0.615 | 0.052 | 0.636 | 0.029 | 0.607 |
| dynamic | 4 | 0.679 | 0.135 | 0.676 | 0.09 | 0.586 |
| dynamic_2tone | 4 | 0.667 | 0.096 | 0.617 | 0.046 | 0.57 |
| low_dry | 4 | 0.769 | 0.092 | 0.667 | 0.036 | 0.631 |
| monotone | 4 | 0.637 | 0.122 | 0.633 | 0.098 | 0.535 |
| paired | 4 | 0.883 | 0.152 | 0.868 | 0.101 | 0.767 |


## R1: BB shove structure × per-board (top variance)

board ごとに BB の shove range structure。polarization 高 = polar shove (nuts or air)、低 = bluff 薄。

| board_label | family | opp_polarization | opp_strong | opp_weak | opp_nut_pct | opp_nut_eq_med |
|---|---|---:|---:|---:|---:|---:|
| monotone_Js | monotone | 1.0 | 1.0 | 0.0 | 0.998 | 0.356 |
| paired_KK2 | paired | 1.0 | 0.999 | 0.001 | 0.999 | 0.79 |
| paired_KK2 | paired | 1.0 | 0.849 | 0.151 | 0.051 | 0.351 |
| paired_KK2 | paired | 1.0 | 1.0 | 0.0 | 1.0 | 0.742 |
| paired_KK2 | paired | 1.0 | 0.959 | 0.041 | 0.159 | 0.354 |
| paired_KK2 | paired | 1.0 | 1.0 | 0.0 | 0.0 | 0.304 |
| dry_high_A | dry_high | 0.994 | 0.993 | 0.0 | 0.0 | None |
| monotone_Ts | monotone | 0.983 | 0.661 | 0.322 | 0.661 | 0.81 |
| monotone_Ts | monotone | 0.982 | 0.66 | 0.322 | 0.659 | 0.767 |
| dry_high_A | dry_high | 0.939 | 0.939 | 0.0 | 0.0 | None |
| monotone_Js | monotone | 0.902 | 0.902 | 0.0 | 0.815 | 0.355 |
| dynamic_T98 | dynamic | 0.898 | 0.63 | 0.268 | 0.629 | 0.832 |
| dynamic_J97 | dynamic | 0.881 | 0.836 | 0.046 | 0.021 | 0.522 |
| dynamic_2tone_T97 | dynamic_2tone | 0.876 | 0.874 | 0.001 | 0.0 | None |
| dynamic_2tone_T97 | dynamic_2tone | 0.871 | 0.871 | 0.0 | 0.0 | None |
