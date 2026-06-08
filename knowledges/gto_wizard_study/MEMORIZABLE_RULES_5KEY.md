# 5-key 完全 MATCHA 圧縮ルール — Bet Sizing 軸込み

MATCHA Framework 5 軸すべて (Range Morphology / Hand Strength / **Bet Sizing** /
Equity Bucket / SPR は pot type で代用) を反映したマクロルール。

## ルール階層 (8 levels)

| level | cell key | cells | rules |
|-------|---------|---:|---:|
| L1 (最具体) | (pot, street, tier, eq, **bs**) | 252 | 144 |
| L2 | (pot, street, sub, eq, **bs**) | 310 | 152 |
| L3 | (pot, street, tier, eq) | 155 | 81 |
| L4 | (pot, street, eq, **bs**) | 79 | 36 |
| L5a | (pot, street, tier, **bs**) | 112 | 64 |
| L5b | (pot, street, sub, eq) | 247 | 145 |
| L6 | (pot, street, eq) | 40 | 23 |
| L7 | (pot, street) | 10 | 3 |
| Default (eq→action) | — | — | 4 |
| **合計** | | | **652** |

## 評価結果 (rule variants 比較)

| variant | rules | accuracy | avg loss | huge% |
|---|---:|---:|---:|---:|
| **5-key 圧縮 (本)** | 652 | **75.60%** | **0.3227 BB** | **1.47%** |
| 4-key 圧縮 | 230 | 73.34% | 0.39 BB | 1.78% |
| フル 4-key lookup | 556 | 78.13% | 0.21 BB | 0.82% |
| 旧 3-key 圧縮 | 51 | 63.72% | 0.88 BB | 3.43% |
| 既存公式 v9b/v10/v15 | — | 59.46% | 1.8595 BB | 9.65% |

## source 別 breakdown

| source | n | rows% | accuracy | avg loss |
|---|---:|---:|---:|---:|
| L1 | 74,688 | 48.4% | 89.80% | 0.0729 BB |
| L2 | 13,847 | 9.0% | 82.44% | 0.1188 BB |
| L3 | 1,349 | 0.9% | 68.94% | 0.3342 BB |
| L4 | 973 | 0.6% | 64.65% | 0.1053 BB |
| L5a | 14,552 | 9.4% | 63.07% | 0.3698 BB |
| L5b | 11,027 | 7.2% | 70.18% | 0.2529 BB |
| L6 | 3,902 | 2.5% | 47.21% | 0.3621 BB |
| L7 | 3,394 | 2.2% | 39.78% | 0.9148 BB |
| DEFAULT | 30,484 | 19.8% | 53.94% | 0.9656 BB |

## pot type 別

| pot | n | accuracy | avg loss | huge% |
|---|---:|---:|---:|---:|
| SRP | 43,660 | 81.56% | 0.1754 BB | 0.61% |
| 3BP | 27,648 | 76.83% | 0.2786 BB | 1.41% |
| 4BP | 48,816 | 72.73% | 0.5495 BB | 2.91% |
| DEF | 34,092 | 71.09% | 0.2225 BB | 0.56% |

## bet_size 別の defense 行動 (L4: pot×street×eq×bs ルールから抜粋)

| pot | street | eq_bucket | bet_size | action | freq | n |
|---|---|---|---|---|---:|---:|
| 3BP | flop | good_hands | small_33 | **call** | 83% | 767 |
| 3BP | flop | good_hands | med_75p | **call** | 86% | 1,123 |
| 3BP | flop | weak_hands | med_75p | **call** | 93% | 1,101 |
| 3BP | flop | trash_hands | overbet | **fold** | 94% | 1,358 |
| 3BP | turn | good_hands | med_75p | **call** | 90% | 180 |
| 3BP | turn | weak_hands | med_75p | **call** | 86% | 179 |
| 3BP | turn | trash_hands | overbet_185 | **fold** | 96% | 3,640 |
| 4BP | flop | weak_hands | overbet | **call** | 82% | 12,647 |
| 4BP | turn | trash_hands | overbet_185 | **fold** | 91% | 4,310 |
| DEF | flop | trash_hands | med_75p | **fold** | 84% | 6,985 |
| DEF | turn | good_hands | med_75p | **call** | 93% | 865 |
| DEF | turn | trash_hands | med_75p | **fold** | 90% | 2,611 |
| DEF | river | good_hands | med_75p | **call** | 100% | 308 |
| SRP | flop | good_hands | allin | **raise** | 93% | 43 |
| SRP | flop | weak_hands | overbet | **fold** | 82% | 213 |
| SRP | flop | weak_hands | allin | **call** | 95% | 39 |
| SRP | flop | trash_hands | small_33 | **fold** | 87% | 1,102 |
| SRP | flop | trash_hands | overbet | **fold** | 85% | 110 |
| SRP | flop | trash_hands | allin | **fold** | 91% | 3,979 |
| SRP | turn | good_hands | small_33 | **call** | 82% | 367 |
| SRP | turn | good_hands | med_75p | **call** | 95% | 1,515 |
| SRP | turn | weak_hands | small_33 | **call** | 81% | 826 |
| SRP | turn | weak_hands | overbet_185 | **fold** | 93% | 1,753 |
| SRP | turn | trash_hands | small_33 | **fold** | 87% | 760 |
| SRP | turn | trash_hands | med_75p | **fold** | 92% | 3,741 |
| SRP | turn | trash_hands | overbet_185 | **fold** | 98% | 1,890 |
| SRP | river | best_hands | med_75p | **raise** | 92% | 50 |
| SRP | river | best_hands | overbet | **raise** | 95% | 126 |
| SRP | river | best_hands | allin | **raise** | 96% | 92 |
| SRP | river | good_hands | overbet | **call** | 99% | 259 |
| ... (残り 6) | | | | | | |

## 結論

- **652 ルール**で accuracy **75.60%**、avg loss **0.323 BB**
- 4-key 圧縮 (230 rules) より accuracy +2.26pp、loss -17.3%
- 既存公式と比較: accuracy +16.1pp、loss -82.6%

**MATCHA 5 軸完全反映**で、判定精度がさらに向上。bet_size 軸を入れることで
「相手の bet size 別の defense 行動」が data 駆動で出る (= 守備側読者に最も実用的)。