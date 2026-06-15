# Multi-Grid v5 — 各 grid 4-9 cells に圧縮

Interaction を 4 個の小 grid に分散、全部足して 30 cells 暗記。

## 性能

| variant | accuracy | avg loss | huge% |
|---|---:|---:|---:|
| **v5 連続 (30 cells)** | 60.66% | **0.9123 BB** | 5.73% |
| **v5 整数 (書籍)** | 51.93% | **1.2850 BB** | 7.82% |
| v1 整数 (24 cells single) | 66.5% | 0.48 BB | 2.28% |
| v3 整数 (9 cells + 4 補正) | 63.6% | 0.61 BB | 3.14% |

## 公式

```
Score = G1[tier_c][board_c] (9 cells)
      + G2[tier_c][pot_c]   (6 cells)
      + G3[draw][bs_c]      (6 cells)
      + G4[board_c][bs_c]   (9 cells)
      + w_oc × overcards + intercept
if Score >= 15: raise / >= -14: call / else: fold
```

## G1: カテゴリ × board (made hand × board)

|  | dry | paired | wet |
| ---:|---:|---:|---:|
| 弱(MP/エア) | 3 | 4 | 2 |
| 中(2P/TP+) | 13 | 15 | 9 |
| 強(ナッツ/ストロング) | 4 | 2 | 12 |

## G2: カテゴリ × pot (made × opp range)

|  | SRP/DEF | 3BP/4BP |
| ---:|---:|---:|
| 弱(MP/エア) | -9 | 3 |
| 中(2P/TP+) | -8 | 3 |
| 強(ナッツ/ストロング) | -2 | -3 |

## G3: draw × bs (draw × facing bet)

|  | small (33%) | mid (75-100%) | big (overbet+) |
| ---:|---:|---:|---:|
| no_draw | 2 | -10 | -7 |
| draw あり | 1 | 4 | -3 |

## G4: board × bs (board × facing bet)

|  | small (33%) | mid (75-100%) | big (overbet+) |
| ---:|---:|---:|---:|
| dry | -3 | 2 | -6 |
| paired | 4 | 2 | -2 |
| wet | 3 | 5 | -10 |

## ベース

- w_oc = 0, intercept = -2
- t_call = -14, t_raise = 15