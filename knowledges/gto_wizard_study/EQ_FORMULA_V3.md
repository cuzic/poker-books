# eq 計算式 v3 — 45 特徴量 (interaction 15 含む)

## 性能

| variant | accuracy |
|---|---:|
| **45-feature 連続** | **52.40%** |
| 45-feature 整数 | 49.26% |
| (参考) 30-feature 線形 | 52.18% |
| (参考) 8-feature 線形 | 58.84% |
| (参考) 24-cell grid | 58.0% |

## 上位特徴量 (連続係数 |w| 順)

| 特徴量 | 連続 | 整数 | interaction? |
|---|---:|---:|---|
| i_op_bhigh | +2.870 | +3 | ★ inter |
| i_set_paired | -2.824 | -3 | ★ inter |
| monotone | +2.795 | +3 | - |
| hero_mid_match | +2.786 | +3 | - |
| hero_suited | +2.758 | +3 | - |
| i_set_top_match | -2.691 | -3 | ★ inter |
| hero_suits_on_board | +2.685 | +3 | - |
| i_tp_kicker | +2.616 | +3 | ★ inter |
| i_air_conn | -2.565 | -3 | ★ inter |
| hero_set | +2.553 | +3 | - |
| i_set_conn | -2.531 | -3 | ★ inter |
| hero_pair | +2.483 | +2 | - |
| paired | -2.453 | -2 | - |
| i_set_mono | -2.424 | -2 | ★ inter |
| hero_top_match | +2.411 | +2 | - |
| hero_high_K | -2.222 | -2 | - |
| i_mid_overcards | -2.188 | -2 | ★ inter |
| i_oc_conn | +2.026 | +2 | ★ inter |
| hero_tp_kicker | +2.021 | +2 | - |
| hero_broadway | -1.990 | -2 | - |
| hero_high_A | -1.962 | -2 | - |
| max_gap | +1.907 | +2 | - |
| straight_outs | +1.883 | +2 | - |
| b_low | -1.806 | -2 | - |
| i_op_conn | +1.522 | +2 | ★ inter |
| **intercept** | +1.770 | +2 | - |

閾値: t_weak=9, t_good=10, t_best=23
