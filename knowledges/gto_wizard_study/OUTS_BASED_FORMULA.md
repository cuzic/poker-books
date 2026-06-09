# Outs ベース DV 公式

## 性能比較

| variant | 連続 acc | 連続 loss | 連続 huge% | 整数 acc | 整数 loss | 整数 huge% |
|---|---:|---:|---:|---:|---:|---:|
| outs × multiplier (rule of 4/2) | 69.76% | 0.3910 | 1.73% | 64.87% | 0.5972 | 3.27% |
| raw outs (no street scaling) | 69.86% | 0.4268 | 1.99% | 67.78% | 0.4932 | 2.49% |

| baseline | acc | loss |
|---|---:|---:|
| td4 × b4 +DV (dv_cat 5段階) | 68.81% | 0.4441 BB |
| v1 (24 single grid) | 66.5% | 0.48 BB |

## outs × multiplier (rule of 4/2) 整数 Grid

| | dry | paired | connected | monotone |
|---|---|---|---|---|
| 強メイド | 2 | 9 | 1 | 17 |
| 中メイド | 6 | 18 | 1 | 5 |
| draw | 5 | 11 | -6 | 3 |
| trash | 4 | 5 | -9 | 4 |

weights: w_tier=5, w_dv=1.0, w_oc=0, w_pot=3, w_bs=1, intercept=5
thresholds: t_call=15, t_raise=52

## raw outs (no street scaling) 整数 Grid

| | dry | paired | connected | monotone |
|---|---|---|---|---|
| 強メイド | 11 | 9 | 16 | 13 |
| 中メイド | -2 | 19 | -8 | -7 |
| draw | 15 | 6 | -9 | 17 |
| trash | -8 | -7 | -9 | -10 |

weights: w_tier=4, w_dv=0.5, w_oc=1, w_pot=3, w_bs=1, intercept=-5
thresholds: t_call=-4, t_raise=43
