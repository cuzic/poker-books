# カテゴリ + draw 統合の 4 分類 × board grid

## 4 分類 (tier_draw)

- A 強メイド: ナッツ / ストロング / ツーペア
- B 中メイド: TP+ / MP
- C draw: エア + draw あり
- D trash: エア + no draw

## 結果

| variant | cells | 連続 acc | 連続 loss | 連続 huge% | 整数 acc | 整数 loss | 整数 huge% |
|---|---:|---:|---:|---:|---:|---:|---:|
| td4 × b3 (12 cells, no DV) | 12 | 67.47% | 0.4813 | 2.28% | 64.35% | 0.6945 | 3.82% |
| td4 × b3 (12 cells, +DV) | 12 | 69.77% | 0.3772 | 1.56% | 67.99% | 0.4655 | 2.26% |
| td4 × b4 (16 cells, no DV) | 16 | 67.92% | 0.5178 | 2.71% | 59.21% | 0.7665 | 4.05% |
| td4 × b4 (16 cells, +DV) | 16 | 69.26% | 0.4414 | 2.09% | 68.81% | 0.4441 | 2.12% |

## 比較

| baseline | acc | loss |
|---|---:|---:|
| v1 (24 single grid) | 66.5% | 0.48 BB |
| v3 (9 + 4 補正) | 63.6% | 0.61 BB |

## td4 × b3 (12 cells, no DV) (整数版)

| | dry | paired | wet |
|---|---|---|---|
| 強メイド | 0 | -2 | -3 |
| 中メイド | 14 | 14 | 3 |
| draw | 9 | 14 | 1 |
| trash | -1 | 5 | -1 |

weights: w_tier=4, w_oc=1, w_pot=3, w_bs=1, intercept=-10
t_call=-3, t_raise=19

## td4 × b3 (12 cells, +DV) (整数版)

| | dry | paired | wet |
|---|---|---|---|
| 強メイド | 4 | 0 | 1 |
| 中メイド | 4 | 5 | 2 |
| draw | 3 | 9 | -4 |
| trash | 1 | 1 | -3 |

weights: w_tier=3, w_oc=2, w_pot=2, w_bs=2, intercept=9, w_dv=3
t_call=13, t_raise=39

## td4 × b4 (16 cells, no DV) (整数版)

| | dry | paired | connected | monotone |
|---|---|---|---|---|
| 強メイド | 7 | 11 | 7 | 4 |
| 中メイド | 10 | 11 | 8 | 6 |
| draw | 8 | 12 | 8 | 14 |
| trash | 5 | 8 | 2 | -3 |

weights: w_tier=3, w_oc=1, w_pot=3, w_bs=0, intercept=-9
t_call=4, t_raise=14

## td4 × b4 (16 cells, +DV) (整数版)

| | dry | paired | connected | monotone |
|---|---|---|---|---|
| 強メイド | 5 | 6 | 0 | 2 |
| 中メイド | 6 | 10 | 5 | 0 |
| draw | 7 | 5 | -4 | 1 |
| trash | -2 | 3 | -4 | -2 |

weights: w_tier=3, w_oc=1, w_pot=3, w_bs=1, intercept=2, w_dv=2
t_call=10, t_raise=30
