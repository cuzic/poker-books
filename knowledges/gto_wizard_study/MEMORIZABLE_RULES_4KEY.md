# 圧縮ルール 4-key (sub × made_tier × equity_bucket)

MATCHA Framework の 5 軸を活用したマクロルール抽出。階層 6 レイヤー + default。

## ルール階層

| level | cell key | cells 数 | rules 数 (cov ≥閾値) |
|-------|---------|---:|---:|
| A | (pot, street, tier, **eq_bucket**) | 155 | 81 (cov ≥0.8) |
| B | (pot, street, sub, **eq_bucket**) | 247 | 102 (cov ≥0.8) |
| C | (pot, street, **eq_bucket**) | 40 | 23 (cov ≥0.7) |
| D | (pot, street, tier) | 60 | 15 (cov ≥0.8) |
| E | (pot, street, sub) | 62 | 2 (cov ≥0.7) |
| F | (pot, street) | 10 | 3 (cov ≥0.6) |
| Default | eq_bucket → action map | — | 4 |
| **合計** | | | **230** |

## 評価結果

| variant | rules | accuracy | avg loss | huge% |
|---|---:|---:|---:|---:|
| **4-key 圧縮 (本ルール)** | 230 | **73.34%** | **0.3897 BB** | **1.78%** |
| フル 4-key lookup | 556 | 78.13% | 0.21 BB | 0.82% |
| 旧 3-key 圧縮 | 51 | 63.72% | 0.88 BB | 3.43% |
| 既存公式 v9b/v10/v15 | — | 59.46% | 1.8595 BB | 9.65% |

## source 別 breakdown

| source | n | rows% | accuracy | avg loss |
|---|---:|---:|---:|---:|
| A | 68,630 | 44.5% | 89.04% | 0.0866 BB |
| B | 16,893 | 11.0% | 82.82% | 0.0919 BB |
| C | 14,235 | 9.2% | 60.81% | 0.2373 BB |
| D | 6,537 | 4.2% | 66.87% | 0.5748 BB |
| E | 388 | 0.3% | 41.75% | 0.7155 BB |
| F | 5,871 | 3.8% | 44.83% | 1.1060 BB |
| DEFAULT | 41,662 | 27.0% | 53.23% | 0.9288 BB |

## pot type 別

| pot | n | accuracy | avg loss | huge% |
|---|---:|---:|---:|---:|
| SRP | 43,660 | 78.49% | 0.2638 BB | 0.83% |
| 3BP | 27,648 | 74.45% | 0.3198 BB | 1.57% |
| 4BP | 48,816 | 71.25% | 0.6405 BB | 3.59% |
| DEF | 34,092 | 68.82% | 0.2484 BB | 0.56% |

## Type A ルール一覧 (最具体: pot × street × tier × eq_bucket)

| pot | street | tier | eq_bucket | action | freq | n |
|---|---|---|---|---|---:|---:|
| 3BP | flop | ナッツメイド | best_hands | **call** | 95% | 20 |
| 3BP | flop | ミドルペア | good_hands | **call** | 87% | 2,447 |
| 3BP | turn | ナッツメイド | best_hands | **call** | 93% | 114 |
| 3BP | turn | ツーペア | best_hands | **call** | 85% | 130 |
| 3BP | turn | トップペア以上 | weak_hands | **call** | 89% | 361 |
| 3BP | turn | ミドルペア | best_hands | **call** | 100% | 12 |
| 3BP | turn | ミドルペア | good_hands | **call** | 93% | 806 |
| 3BP | turn | エア | good_hands | **call** | 97% | 248 |
| 3BP | turn | エア | trash_hands | **fold** | 92% | 4,235 |
| 4BP | flop | ナッツメイド | best_hands | **call** | 80% | 50 |
| 4BP | flop | ストロング | best_hands | **call** | 83% | 1,178 |
| 4BP | flop | ツーペア | good_hands | **call** | 84% | 108 |
| 4BP | flop | トップペア以上 | best_hands | **raise** | 81% | 1,418 |
| 4BP | flop | トップペア以上 | good_hands | **raise** | 89% | 2,344 |
| 4BP | flop | ミドルペア | weak_hands | **call** | 98% | 1,272 |
| 4BP | flop | エア | weak_hands | **call** | 81% | 11,375 |
| 4BP | turn | ナッツメイド | best_hands | **call** | 93% | 114 |
| 4BP | turn | ツーペア | good_hands | **raise** | 100% | 51 |
| 4BP | turn | ミドルペア | trash_hands | **fold** | 100% | 34 |
| 4BP | turn | エア | good_hands | **call** | 95% | 78 |
| 4BP | turn | エア | trash_hands | **fold** | 91% | 4,276 |
| DEF | flop | ストロング | best_hands | **call** | 83% | 1,050 |
| DEF | flop | ストロング | good_hands | **call** | 91% | 198 |
| DEF | flop | ツーペア | good_hands | **call** | 93% | 242 |
| DEF | flop | ミドルペア | best_hands | **call** | 100% | 9 |
| DEF | flop | エア | trash_hands | **fold** | 85% | 6,622 |
| DEF | turn | ナッツメイド | best_hands | **call** | 93% | 46 |
| DEF | turn | ストロング | good_hands | **call** | 94% | 126 |
| DEF | turn | ツーペア | best_hands | **call** | 84% | 25 |
| DEF | turn | ツーペア | good_hands | **call** | 100% | 21 |
| DEF | turn | ツーペア | weak_hands | **call** | 100% | 18 |
| DEF | turn | トップペア以上 | best_hands | **call** | 87% | 158 |
| DEF | turn | トップペア以上 | good_hands | **call** | 89% | 358 |
| DEF | turn | ミドルペア | best_hands | **call** | 100% | 30 |
| DEF | turn | ミドルペア | good_hands | **call** | 96% | 260 |
| DEF | turn | ミドルペア | trash_hands | **fold** | 93% | 272 |
| DEF | turn | エア | good_hands | **call** | 94% | 100 |
| DEF | turn | エア | trash_hands | **fold** | 90% | 2,336 |
| DEF | river | ナッツメイド | good_hands | **call** | 100% | 9 |
| DEF | river | ストロング | good_hands | **call** | 100% | 120 |
| DEF | river | ストロング | weak_hands | **call** | 100% | 10 |
| DEF | river | ツーペア | best_hands | **raise** | 100% | 17 |
| DEF | river | ツーペア | good_hands | **call** | 100% | 9 |
| DEF | river | ツーペア | weak_hands | **call** | 100% | 51 |
| DEF | river | ツーペア | trash_hands | **call** | 100% | 6 |
| DEF | river | トップペア以上 | good_hands | **call** | 100% | 76 |
| DEF | river | トップペア以上 | weak_hands | **call** | 100% | 45 |
| DEF | river | トップペア以上 | trash_hands | **call** | 81% | 108 |
| DEF | river | ミドルペア | best_hands | **call** | 82% | 44 |
| DEF | river | ミドルペア | good_hands | **call** | 100% | 94 |
| DEF | river | ミドルペア | weak_hands | **call** | 84% | 121 |
| SRP | flop | ナッツメイド | best_hands | **raise** | 100% | 62 |
| SRP | flop | ナッツメイド | trash_hands | **fold** | 86% | 204 |
| SRP | flop | ストロング | good_hands | **raise** | 93% | 43 |
| SRP | flop | ストロング | weak_hands | **call** | 93% | 30 |
| SRP | flop | ツーペア | good_hands | **call** | 82% | 40 |
| SRP | flop | ツーペア | weak_hands | **call** | 100% | 9 |
| SRP | flop | ツーペア | trash_hands | **fold** | 96% | 255 |
| SRP | flop | トップペア以上 | best_hands | **call** | 88% | 99 |
| SRP | flop | トップペア以上 | good_hands | **call** | 94% | 327 |
| SRP | flop | トップペア以上 | trash_hands | **fold** | 95% | 368 |
| SRP | flop | ミドルペア | trash_hands | **fold** | 91% | 842 |
| SRP | flop | エア | trash_hands | **fold** | 94% | 2,642 |
| SRP | turn | ストロング | good_hands | **call** | 97% | 172 |
| SRP | turn | ツーペア | best_hands | **call** | 88% | 136 |
| SRP | turn | ツーペア | good_hands | **call** | 91% | 196 |
| SRP | turn | トップペア以上 | best_hands | **call** | 96% | 133 |
| SRP | turn | トップペア以上 | good_hands | **call** | 83% | 1,401 |
| SRP | turn | トップペア以上 | weak_hands | **call** | 86% | 299 |
| SRP | turn | ミドルペア | best_hands | **call** | 88% | 25 |
| SRP | turn | ミドルペア | trash_hands | **fold** | 100% | 68 |
| SRP | turn | エア | trash_hands | **fold** | 93% | 6,323 |
| SRP | river | ナッツメイド | best_hands | **raise** | 98% | 378 |
| SRP | river | ナッツメイド | good_hands | **call** | 100% | 22 |
| SRP | river | ナッツメイド | weak_hands | **call** | 100% | 108 |
| SRP | river | ストロング | weak_hands | **call** | 86% | 972 |
| SRP | river | ツーペア | good_hands | **call** | 100% | 17 |
| SRP | river | トップペア以上 | good_hands | **call** | 100% | 53 |
| SRP | river | ミドルペア | good_hands | **call** | 100% | 82 |
| SRP | river | ミドルペア | trash_hands | **fold** | 88% | 2,871 |
| SRP | river | エア | trash_hands | **fold** | 98% | 7,201 |

## Type B ルール一覧 (board × eq_bucket)

| pot | street | sub_family | eq_bucket | action | freq | n |
|---|---|---|---|---|---:|---:|
| 3BP | flop | Khigh_spread | good_hands | **call** | 94% | 633 |
| 3BP | flop | Khigh_spread | weak_hands | **call** | 85% | 718 |
| 3BP | flop | connected_mid | trash_hands | **fold** | 100% | 812 |
| 3BP | flop | mid_dry | trash_hands | **fold** | 81% | 334 |
| 3BP | flop | monotone | good_hands | **call** | 81% | 891 |
| 3BP | flop | monotone | weak_hands | **call** | 82% | 726 |
| 3BP | turn | Khigh_spread | best_hands | **call** | 91% | 217 |
| 3BP | turn | Khigh_spread | good_hands | **call** | 100% | 324 |
| 3BP | turn | Khigh_spread | trash_hands | **fold** | 94% | 500 |
| 3BP | turn | connected_mid | trash_hands | **fold** | 99% | 1,596 |
| 3BP | turn | mid_dry | trash_hands | **fold** | 92% | 813 |
| 3BP | turn | monotone | best_hands | **call** | 94% | 142 |
| 3BP | turn | monotone | good_hands | **call** | 85% | 602 |
| 3BP | turn | monotone | weak_hands | **fold** | 84% | 1,011 |
| 3BP | turn | monotone | trash_hands | **fold** | 100% | 501 |
| 3BP | turn | paired_high | good_hands | **call** | 87% | 444 |
| 4BP | flop | connected_mid | weak_hands | **call** | 89% | 2,770 |
| 4BP | flop | connected_mid | trash_hands | **fold** | 81% | 1,715 |
| 4BP | flop | low_dry | weak_hands | **call** | 83% | 511 |
| 4BP | flop | mid_dry | weak_hands | **call** | 88% | 2,000 |
| 4BP | flop | paired_broadway | weak_hands | **call** | 91% | 397 |
| 4BP | flop | paired_high | best_hands | **call** | 89% | 384 |
| 4BP | flop | paired_high | weak_hands | **call** | 94% | 1,245 |
| 4BP | flop | paired_mid | weak_hands | **call** | 94% | 425 |
| 4BP | turn | Khigh_spread | good_hands | **raise** | 85% | 286 |
| 4BP | turn | Khigh_spread | trash_hands | **fold** | 92% | 567 |
| 4BP | turn | connected_mid | weak_hands | **call** | 86% | 1,759 |
| 4BP | turn | connected_mid | trash_hands | **fold** | 97% | 1,441 |
| 4BP | turn | mid_dry | good_hands | **raise** | 98% | 384 |
| 4BP | turn | monotone | trash_hands | **fold** | 97% | 954 |
| 4BP | turn | paired_high | good_hands | **raise** | 99% | 362 |
| 4BP | turn | paired_high | trash_hands | **fold** | 84% | 612 |
| DEF | flop | Ahigh_spread | best_hands | **call** | 100% | 48 |
| DEF | flop | Ahigh_spread | trash_hands | **fold** | 91% | 305 |
| DEF | flop | Khigh_spread | good_hands | **call** | 87% | 356 |
| DEF | flop | broadway_dry | best_hands | **call** | 85% | 82 |
| DEF | flop | broadway_dry | good_hands | **call** | 89% | 640 |
| DEF | flop | broadway_dry | trash_hands | **fold** | 93% | 380 |
| DEF | flop | connected_low | trash_hands | **fold** | 92% | 584 |
| DEF | flop | connected_mid | trash_hands | **fold** | 98% | 1,079 |
| DEF | flop | low_dry | best_hands | **raise** | 93% | 44 |
| DEF | flop | low_dry | trash_hands | **fold** | 87% | 445 |
| DEF | flop | mid_dry | trash_hands | **fold** | 86% | 1,074 |
| DEF | flop | monotone | best_hands | **call** | 93% | 301 |
| DEF | flop | monotone | good_hands | **call** | 83% | 1,217 |
| DEF | flop | monotone | trash_hands | **fold** | 89% | 1,248 |
| DEF | flop | paired_broadway | best_hands | **call** | 92% | 100 |
| DEF | flop | paired_broadway | good_hands | **call** | 82% | 266 |
| DEF | flop | paired_high | best_hands | **call** | 98% | 252 |
| DEF | flop | paired_mid | best_hands | **call** | 90% | 118 |
| ... (残り 52) | | | | | | |

## Type C ルール (equity 単独)

| pot | street | eq_bucket | action | freq | n |
|---|---|---|---|---:|---:|
| 3BP | flop | good_hands | **call** | 78% | 5,135 |
| 3BP | flop | trash_hands | **fold** | 76% | 2,886 |
| 3BP | turn | good_hands | **call** | 76% | 2,292 |
| 3BP | turn | trash_hands | **fold** | 91% | 4,310 |
| 4BP | flop | weak_hands | **call** | 82% | 12,647 |
| 4BP | turn | good_hands | **raise** | 75% | 2,239 |
| 4BP | turn | trash_hands | **fold** | 91% | 4,310 |
| DEF | flop | best_hands | **call** | 78% | 1,567 |
| DEF | flop | good_hands | **call** | 72% | 6,969 |
| DEF | flop | trash_hands | **fold** | 84% | 6,985 |
| DEF | river | good_hands | **call** | 100% | 308 |
| DEF | river | weak_hands | **call** | 75% | 342 |
| DEF | turn | best_hands | **call** | 74% | 486 |
| DEF | turn | good_hands | **call** | 93% | 865 |
| DEF | turn | trash_hands | **fold** | 90% | 2,611 |
| SRP | flop | good_hands | **call** | 71% | 1,256 |
| SRP | flop | trash_hands | **fold** | 90% | 5,191 |
| SRP | river | best_hands | **raise** | 79% | 907 |
| SRP | river | good_hands | **call** | 71% | 1,397 |
| SRP | river | trash_hands | **fold** | 90% | 11,692 |
| SRP | turn | best_hands | **call** | 70% | 1,212 |
| SRP | turn | good_hands | **call** | 78% | 3,204 |
| SRP | turn | trash_hands | **fold** | 93% | 6,391 |

## 結論

- **230 ルール**で accuracy **73.3%**、loss **0.390 BB**
- フル lookup (556 cells) から +326 cell 削減、accuracy -4.8pp、loss +85.6%
- 既存公式と比較: accuracy +13.9pp、loss -79.0%

**Sklansky Hand Groups の系譜**: 100+ hands を 8 group に圧縮した先例同様、
293K spots を 230 ルールに圧縮。MATCHA Framework の判断式として実用十分。