# Single Grid サイズ別 比較

補正項なしの single grid で size を 9 → 24 cells で比較。
各 size で 1500 trials × optuna で action loss を minimize。

## 性能比較

| variant | cells | 連続 acc | 連続 loss | 連続 huge% | 整数 acc | 整数 loss | 整数 huge% |
|---|---:|---:|---:|---:|---:|---:|---:|
| 9 cells (3×3) | 9 | 69.73% | 0.3874 | 1.57% | 62.81% | 0.6587 | 3.33% |
| 12a cells (4×3) | 12 | 68.68% | 0.4135 | 1.70% | 65.56% | 0.6227 | 3.39% |
| 12b cells (3×4) | 12 | 68.19% | 0.4511 | 2.06% | 62.22% | 1.4136 | 8.01% |
| 16 cells (4×4) | 16 | 69.66% | 0.4318 | 1.90% | 62.39% | 0.6614 | 3.47% |
| 18 cells (6×3) | 18 | 70.76% | 0.3906 | 1.57% | 69.44% | 0.4165 | 1.77% |
| 24 cells (6×4) | 24 | 67.70% | 0.4076 | 1.76% | 63.08% | 0.5765 | 3.10% |

## まとめ — Pareto frontier

| cells | 連続 loss (BB) | 整数 loss (BB) | 整数暗記項目 |
|---:|---:|---:|---:|
| 9 | 0.3874 | 0.6587 | 17 |
| 12 | 0.4135 | 0.6227 | 20 |
| 12 | 0.4511 | 1.4136 | 20 |
| 16 | 0.4318 | 0.6614 | 24 |
| 18 | 0.3906 | 0.4165 | 26 |
| 24 | 0.4076 | 0.5765 | 32 |

## 各サイズの整数 Grid

### 9 cells (3×3) (整数版、loss 0.6587 BB)

`   4    5    3`
`   9    6    2`
`  10    2   -1`

weights: w_tier=3, w_dv=2, w_oc=1, w_pot=2, w_bs=1, intercept=-1
thresholds: call=7, raise=31

### 12a cells (4×3) (整数版、loss 0.6227 BB)

`  -2   -1   -3`
`   3   15   -4`
`   8    8    0`
`   6    7    5`

weights: w_tier=3, w_dv=1, w_oc=1, w_pot=1, w_bs=1, intercept=5
thresholds: call=6, raise=26

### 12b cells (3×4) (整数版、loss 1.4136 BB)

`   5    6    4    5`
`  12   14    3   11`
`   8    4    7    6`

weights: w_tier=2, w_dv=1, w_oc=0, w_pot=1, w_bs=1, intercept=6
thresholds: call=14, raise=38

### 16 cells (4×4) (整数版、loss 0.6614 BB)

`   3    4    2    2`
`   3    2    8    2`
`   7   -2   -1   -3`
`  -3   -2   14   14`

weights: w_tier=4, w_dv=2, w_oc=1, w_pot=2, w_bs=1, intercept=4
thresholds: call=11, raise=39

### 18 cells (6×3) (整数版、loss 0.4165 BB)

`   0    2   -3`
`   7   12    4`
`  13    2    2`
`   2   14    0`
`   7   10   12`
`  11    9    9`

weights: w_tier=4, w_dv=3, w_oc=2, w_pot=3, w_bs=2, intercept=-2
thresholds: call=6, raise=33

### 24 cells (6×4) (整数版、loss 0.5765 BB)

`  -2    4   -5   -3`
`   2   13    0    3`
`   6   -5   10    6`
`   6    8    2    2`
`   1    9   -1    0`
`   2   -2   -4    6`

weights: w_tier=3, w_dv=2, w_oc=2, w_pot=2, w_bs=1, intercept=5
thresholds: call=8, raise=23
