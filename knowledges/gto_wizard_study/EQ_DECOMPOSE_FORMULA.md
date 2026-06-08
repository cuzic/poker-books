# eq 分解公式 — MV + DV + Board − OppRange

equity を 4 要素に分解。各要素は人間が暗算できる単純な lookup。

## 概念

```
EqScore = MV (made value) + DV (draw value) + BoardAdj − OppRangeStr
```

## 性能

| variant | accuracy |
|---|---:|
| 連続係数 (unconstrained) | **59.49%** |
| 連続係数 (constrained: MV+, DV+, OR-) | 55.29% |
| 整数係数 | 52.61% |
| (参考) 45-feature 線形 | 確認待ち |
| (参考) 30-feature 線形 | 52.2% |
| (参考) 24-cell grid | 58.0% |

## 入力値テーブル (素人用 lookup)

### MV — made hand 強さ (mv_cat 別)

- straight_flush: 10
- quads: 10
- fullhouse: 9
- flush: 7
- straight: 7
- set: 7
- trips: 6
- two_pair: 5
- overpair: 4
- top_pair: 3
- second_pair: 2
- third_pair: 1
- underpair: 1
- low_pair: 1
- no_made_hand: 0
- ace_high: 0
- king_high: 0

### DV — draw 強さ (dv_cat 別)

- combo_draw: 4
- nut_flush_draw: 3
- flush_draw: 3
- oesd: 3
- gutshot: 1
- twocards_bdfd: 1
- onecard_bdfd: 0
- no_draw: 0

### OppRange — 相手 range の強さ (pot_type 別)

- SRP: 0
- DEF: 1
- 3BP: 2
- 4BP: 3

## 最適パラメータ (連続)

| 特徴量 | 連続係数 | 整数 |
|---|---:|---:|
| paired | -2.983 | -3 |
| monotone | -2.859 | -3 |
| DV | +2.639 | +3 |
| connected | -2.498 | -2 |
| MV | +2.475 | +2 |
| tp_kicker | +2.458 | +2 |
| OppRange | +2.153 | +2 |
| ace | -1.999 | -2 |
| twotone | +1.718 | +2 |
| broadway | +0.477 | +0 |
| op_margin | -0.419 | +0 |
| b_high | +0.398 | +0 |
| a_r | +0.397 | +0 |
| low_only | -0.262 | +0 |
| b_r | -0.181 | +0 |
| **intercept** | -9.484 | -9 |

閾値: t_weak=5, t_good=7, t_best=12