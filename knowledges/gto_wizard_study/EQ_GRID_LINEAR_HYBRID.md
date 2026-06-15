# eq grid + 線形 adjust ハイブリッド公式

Grid (カテゴリ × board の非線形相互作用) + 線形 adjust の段階式モデル。

## 概念

```
Step 1: GridBase[mv_tier][board_label] で base eq score lookup
Step 2: Score = w_grid × GridBase
              + w_kicker × tp_kicker
              + w_op     × op_margin       (overpair only)
              + w_oc     × overcards_count
              + w_dv     × draw_value
              + w_opr    × opp_range
              + intercept

Step 3: Score >= T_best → best / >= T_good → good / >= T_weak → weak / else trash
```

## 性能

| variant | accuracy |
|---|---:|
| **Grid + 線形 (連続)** | **60.42%** |
| Grid + 線形 (整数) | 58.66% |
| Grid 単独 (modal lookup) | 58.0% |
| Grid 単独 (expected value optimized) | 57.47% |
| eq 分解 線形 | 59.5% |
| 8-feature 線形 | 58.8% |

## GridBase 表 (カテゴリ × board → expected eq score)

| カテゴリ | dry | paired | connected | monotone |
|------|---:|---:|---:|---:|
| ナッツメイド | 6.81 | 5.00 | 7.38 | 8.82 |
| ストロング | 7.64 | 7.99 | 5.83 | 5.97 |
| ツーペア | 7.72 | 0.00 | 3.43 | 4.94 |
| トップペア以上 | 5.53 | 4.13 | 3.75 | 3.63 |
| ミドルペア | 2.59 | 3.70 | 1.78 | 1.88 |
| エア | 0.96 | 1.31 | 1.08 | 0.95 |

## 整数係数 (書籍向け)

| 係数 | 値 |
|------|---:|
| w_grid | +2 |
| w_kicker | +0 |
| w_op (overpair margin) | +0 |
| w_oc (overcards) | +1 |
| w_dv (draw value) | +2 |
| w_opr (opp range) | +1 |
| intercept | -1 |

閾値: t_weak=8, t_good=11, t_best=15