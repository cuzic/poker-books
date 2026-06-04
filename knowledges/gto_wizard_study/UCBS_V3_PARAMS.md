# A モデル 確定パラメータ (A+C3 Board family)

全 63 params、WRMSE 18.32%

## 1. Vol2 base[ctx5][band] (25 cell)

| ctx5 | air | weak | mid | strong | nut |
|---|---:|---:|---:|---:|---:|
| cash | 44% | 37% | 42% | 57% | 62% |
| mtt_short | 37% | 30% | 35% | 58% | 73% |
| mtt_deep | 42% | 41% | 41% | 58% | 61% |
| 3bp | 46% | 50% | 61% | 70% | 58% |
| turn | 6% | 6% | 3% | 7% | 7% |

## 2. α[ctx13] / β[ctx13] (context lift)

| ctx13 | α | β (TV≥7) |
|---|---:|---:|
| cash_100bb | +2 | -0 |
| mtt_25bb | +36 | -5 |
| mtt_50bb | +0 | -3 |
| mtt_100bb | +26 | -6 |
| mtt_200bb | -5 | -4 |
| mtt_3bp_20bb | -2 | -15 |
| mtt_3bp_25bb | +3 | -15 |
| mtt_3bp_50bb | +1 | +5 |
| mtt_3bp_100bb | +0 | +8 |
| mtt_25bb_turn_btn | -2 | -4 |
| mtt_50bb_turn_btn | +1 | -4 |
| mtt_100bb_turn_btn | +13 | -4 |
| cash_100bb_turn_btn | +1 | -5 |

## 3. Category offset

| category | offset |
|---|---:|
| default | +0 |
| slowplay | +6 |
| trash | -14 |
| premium | +7 |

## 4. Board family ε[family][ctx_group]

| family | cash | mtt_srp | 3bp |
|---|---:|---:|---:|
| dry_high | +0 | +0 | +0 |
| paired | +5 | +2 | -1 |
| dynamic | -21 | -11 | -6 |
| low_dry | -9 | -9 | -2 |

## 5. 板分類ロジック

```
paired      ← ボードに同ランクあり
dynamic     ← モノトーン OR (ストレート連結 + ツーフラ)
dry_high    ← 上記以外で、最高ランク J 以上 (baseline)
low_dry     ← 上記以外で、最高ランク T 以下
```
