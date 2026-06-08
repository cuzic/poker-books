# 3 階層 ルール (CORE / FALLBACK / DEFAULT) — 暗記負荷を最小化

読者が「いつ何を覚えるか」を明確にした 3 階層構造。

## 階層構成

| tier | 目的 | 選定基準 | ルール数 | 配置 |
|------|------|---------|---:|------|
| **CORE** | 暗記必須 | L1/L2 ∧ n≥200 ∧ freq≥0.85 | **113** | 書籍本文 + drill カード前面 |
| **FALLBACK** | 例外対応 (参照可) | L1-L7 残り | 535 | 書籍付録 + drill カード裏面 |
| **DEFAULT** | catch-all | eq_bucket → action | 4 | 「迷ったらこれ」指示 |
| **合計** | | | **652** | |

## 全体評価

| variant | rules | accuracy | avg loss | huge% |
|---|---:|---:|---:|---:|
| **3-tier (本)** | 652 | **75.62%** | **0.3224 BB** | **1.47%** |
| 5-key 圧縮 | 652 | 75.60% | 0.32 BB | 1.47% |
| 4-key 圧縮 | 230 | 73.34% | 0.39 BB | 1.78% |
| 既存公式 | — | 59.46% | 1.86 BB | 9.65% |

## 各 tier の貢献

| tier | rows | rows% | accuracy | avg loss |
|---|---:|---:|---:|---:|
| CORE | 64,934 | 42.1% | 91.82% | 0.0793 BB |
| FALLBACK | 58,798 | 38.1% | 68.96% | 0.2575 BB |
| DEFAULT | 30,484 | 19.8% | 53.94% | 0.9656 BB |

## source 別 breakdown

| source | n | rows% | accuracy | avg loss |
|---|---:|---:|---:|---:|
| CORE_L1 | 44,548 | 28.9% | 93.61% | 0.0916 BB |
| CORE_L2 | 20,386 | 13.2% | 87.90% | 0.0525 BB |
| FB_L1 | 17,174 | 11.1% | 79.06% | 0.0620 BB |
| FB_L2 | 6,427 | 4.2% | 82.50% | 0.1298 BB |
| FB_L3 | 1,349 | 0.9% | 68.94% | 0.3342 BB |
| FB_L4 | 973 | 0.6% | 64.65% | 0.1053 BB |
| FB_L5a | 14,552 | 9.4% | 63.07% | 0.3698 BB |
| FB_L5b | 11,027 | 7.2% | 70.18% | 0.2529 BB |
| FB_L6 | 3,902 | 2.5% | 47.21% | 0.3621 BB |
| FB_L7 | 3,394 | 2.2% | 39.78% | 0.9148 BB |
| DEFAULT | 30,484 | 19.8% | 53.94% | 0.9656 BB |

## CORE 113 ルール (暗記対象、frequency 順)

**この 113 ルールだけ覚えれば、全 spot の 42% を 92% accuracy で処理可能**

| # | level | pot | street | 軸1 | 軸2 | 軸3 | action | freq | n |
|---|---|---|---|---|---|---|---|---:|---:|
| 1 | L1 | SRP | river | tier=エア | eq=trash_hands | bs=med_100p | **fold** | 98% | 5,317 |
| 2 | L1 | 4BP | turn | tier=エア | eq=trash_hands | bs=overbet_185 | **fold** | 91% | 4,276 |
| 3 | L1 | SRP | turn | tier=エア | eq=trash_hands | bs=med_75p | **fold** | 92% | 3,717 |
| 4 | L1 | 3BP | turn | tier=エア | eq=trash_hands | bs=overbet_185 | **fold** | 96% | 3,604 |
| 5 | L2 | SRP | river | sub=monotone | eq=trash_hands | bs=med_100p | **fold** | 87% | 3,147 |
| 6 | L2 | 4BP | flop | sub=connected_mid | eq=weak_hands | bs=overbet | **call** | 89% | 2,770 |
| 7 | L1 | 4BP | flop | tier=トップペア以上 | eq=good_hands | bs=overbet | **raise** | 89% | 2,344 |
| 8 | L1 | DEF | turn | tier=エア | eq=trash_hands | bs=med_75p | **fold** | 90% | 2,336 |
| 9 | L2 | SRP | river | sub=connected_mid | eq=trash_hands | bs=med_100p | **fold** | 91% | 2,277 |
| 10 | L2 | SRP | flop | sub=connected_mid | eq=trash_hands | bs=allin | **fold** | 93% | 2,213 |
| 11 | L2 | 4BP | flop | sub=mid_dry | eq=weak_hands | bs=overbet | **call** | 88% | 2,000 |
| 12 | L1 | SRP | river | tier=ミドルペア | eq=trash_hands | bs=med_100p | **fold** | 87% | 1,873 |
| 13 | L1 | SRP | turn | tier=エア | eq=trash_hands | bs=overbet_185 | **fold** | 98% | 1,846 |
| 14 | L2 | 4BP | turn | sub=connected_mid | eq=weak_hands | bs=overbet_185 | **call** | 86% | 1,759 |
| 15 | L2 | 3BP | turn | sub=connected_mid | eq=trash_hands | bs=overbet_185 | **fold** | 99% | 1,596 |
| 16 | L2 | SRP | river | sub=paired_high | eq=trash_hands | bs=med_100p | **fold** | 96% | 1,514 |
| 17 | L2 | 4BP | turn | sub=connected_mid | eq=trash_hands | bs=overbet_185 | **fold** | 97% | 1,441 |
| 18 | L1 | SRP | flop | tier=エア | eq=trash_hands | bs=allin | **fold** | 100% | 1,430 |
| 19 | L1 | 3BP | flop | tier=エア | eq=trash_hands | bs=overbet | **fold** | 94% | 1,358 |
| 20 | L2 | SRP | turn | sub=connected_mid | eq=trash_hands | bs=med_75p | **fold** | 93% | 1,334 |
| 21 | L2 | SRP | turn | sub=monotone | eq=trash_hands | bs=med_75p | **fold** | 100% | 1,278 |
| 22 | L1 | 4BP | flop | tier=ミドルペア | eq=weak_hands | bs=overbet | **call** | 98% | 1,272 |
| 23 | L2 | DEF | flop | sub=monotone | eq=trash_hands | bs=med_75p | **fold** | 89% | 1,248 |
| 24 | L2 | 4BP | flop | sub=paired_high | eq=weak_hands | bs=overbet | **call** | 94% | 1,245 |
| 25 | L1 | SRP | turn | tier=エア | eq=weak_hands | bs=overbet_185 | **fold** | 92% | 1,114 |
| 26 | L1 | SRP | flop | tier=エア | eq=trash_hands | bs=small_33 | **fold** | 87% | 1,102 |
| 27 | L2 | DEF | flop | sub=connected_mid | eq=trash_hands | bs=med_75p | **fold** | 98% | 1,079 |
| 28 | L2 | DEF | flop | sub=mid_dry | eq=trash_hands | bs=med_75p | **fold** | 86% | 1,074 |
| 29 | L1 | 3BP | flop | tier=エア | eq=weak_hands | bs=med_75p | **call** | 93% | 996 |
| 30 | L2 | SRP | river | sub=Khigh_spread | eq=trash_hands | bs=overbet | **fold** | 90% | 965 |
| 31 | L2 | 4BP | turn | sub=monotone | eq=trash_hands | bs=overbet_185 | **fold** | 97% | 954 |
| 32 | L1 | SRP | river | tier=エア | eq=trash_hands | bs=overbet | **fold** | 100% | 920 |
| 33 | L2 | SRP | river | sub=mid_dry | eq=trash_hands | bs=allin | **fold** | 86% | 876 |
| 34 | L2 | SRP | flop | sub=paired_high | eq=trash_hands | bs=allin | **fold** | 97% | 876 |
| 35 | L2 | SRP | turn | sub=connected_mid | eq=good_hands | bs=med_75p | **call** | 93% | 844 |
| 36 | L1 | SRP | flop | tier=ミドルペア | eq=trash_hands | bs=allin | **fold** | 91% | 842 |
| 37 | L2 | 3BP | turn | sub=mid_dry | eq=trash_hands | bs=overbet_185 | **fold** | 92% | 813 |
| 38 | L2 | 3BP | flop | sub=connected_mid | eq=trash_hands | bs=overbet | **fold** | 100% | 812 |
| 39 | L1 | SRP | turn | tier=エア | eq=trash_hands | bs=small_33 | **fold** | 87% | 760 |
| 40 | L1 | SRP | river | tier=ミドルペア | eq=trash_hands | bs=overbet | **fold** | 96% | 748 |
| 41 | L2 | DEF | turn | sub=connected_mid | eq=trash_hands | bs=med_75p | **fold** | 89% | 740 |
| 42 | L2 | SRP | turn | sub=Khigh_spread | eq=trash_hands | bs=overbet_185 | **fold** | 99% | 732 |
| 43 | L1 | SRP | river | tier=エア | eq=trash_hands | bs=allin | **fold** | 95% | 726 |
| 44 | L1 | SRP | turn | tier=トップペア以上 | eq=good_hands | bs=med_75p | **call** | 96% | 723 |
| 45 | L2 | SRP | turn | sub=connected_mid | eq=weak_hands | bs=overbet_185 | **fold** | 93% | 659 |
| 46 | L2 | DEF | flop | sub=broadway_dry | eq=good_hands | bs=med_75p | **call** | 89% | 640 |
| 47 | L2 | SRP | turn | sub=mid_dry | eq=trash_hands | bs=overbet_185 | **fold** | 98% | 635 |
| 48 | L1 | 3BP | turn | tier=ミドルペア | eq=good_hands | bs=overbet_185 | **call** | 94% | 632 |
| 49 | L1 | 3BP | flop | tier=ミドルペア | eq=good_hands | bs=med_75p | **call** | 85% | 627 |
| 50 | L1 | SRP | turn | tier=ミドルペア | eq=weak_hands | bs=overbet_185 | **fold** | 95% | 620 |
| 51 | L2 | SRP | turn | sub=mid_dry | eq=weak_hands | bs=overbet_185 | **fold** | 93% | 615 |
| 52 | L2 | 3BP | turn | sub=monotone | eq=good_hands | bs=overbet_185 | **call** | 85% | 602 |
| 53 | L2 | DEF | flop | sub=connected_low | eq=trash_hands | bs=med_75p | **fold** | 92% | 584 |
| 54 | L2 | SRP | river | sub=mid_dry | eq=trash_hands | bs=med_100p | **fold** | 99% | 575 |
| 55 | L2 | 4BP | turn | sub=Khigh_spread | eq=trash_hands | bs=overbet_185 | **fold** | 92% | 567 |
| 56 | L2 | SRP | river | sub=Khigh_spread | eq=trash_hands | bs=med_100p | **fold** | 96% | 547 |
| 57 | L2 | SRP | turn | sub=connected_mid | eq=trash_hands | bs=overbet_185 | **fold** | 98% | 523 |
| 58 | L2 | DEF | turn | sub=Khigh_spread | eq=trash_hands | bs=med_75p | **fold** | 91% | 515 |
| 59 | L2 | DEF | turn | sub=mid_dry | eq=trash_hands | bs=med_75p | **fold** | 93% | 508 |
| 60 | L2 | 3BP | turn | sub=monotone | eq=trash_hands | bs=overbet_185 | **fold** | 100% | 501 |
| 61 | L2 | 3BP | turn | sub=Khigh_spread | eq=trash_hands | bs=overbet_185 | **fold** | 94% | 500 |
| 62 | L2 | SRP | turn | sub=Khigh_spread | eq=weak_hands | bs=overbet_185 | **fold** | 94% | 479 |
| 63 | L1 | 3BP | flop | tier=ミドルペア | eq=good_hands | bs=small_33 | **call** | 94% | 456 |
| 64 | L2 | DEF | turn | sub=paired_high | eq=trash_hands | bs=med_75p | **fold** | 85% | 449 |
| 65 | L2 | 3BP | flop | sub=monotone | eq=good_hands | bs=med_75p | **call** | 87% | 447 |
| 66 | L2 | DEF | flop | sub=low_dry | eq=trash_hands | bs=med_75p | **fold** | 87% | 445 |
| 67 | L2 | SRP | turn | sub=Khigh_spread | eq=trash_hands | bs=small_33 | **fold** | 89% | 435 |
| 68 | L2 | 4BP | flop | sub=paired_mid | eq=weak_hands | bs=overbet | **call** | 94% | 425 |
| 69 | L2 | SRP | turn | sub=monotone | eq=good_hands | bs=med_75p | **call** | 100% | 424 |
| 70 | L2 | SRP | flop | sub=connected_mid | eq=good_hands | bs=small_33 | **call** | 92% | 416 |
| 71 | L1 | SRP | turn | tier=ミドルペア | eq=good_hands | bs=med_75p | **call** | 96% | 408 |
| 72 | L2 | DEF | turn | sub=monotone | eq=trash_hands | bs=med_75p | **fold** | 94% | 399 |
| 73 | L2 | 4BP | flop | sub=paired_broadway | eq=weak_hands | bs=overbet | **call** | 91% | 397 |
| 74 | L2 | SRP | flop | sub=connected_mid | eq=trash_hands | bs=small_33 | **fold** | 92% | 396 |
| 75 | L2 | 4BP | flop | sub=paired_high | eq=best_hands | bs=overbet | **call** | 89% | 384 |
| 76 | L2 | 4BP | turn | sub=mid_dry | eq=good_hands | bs=overbet_185 | **raise** | 98% | 384 |
| 77 | L2 | DEF | flop | sub=broadway_dry | eq=trash_hands | bs=med_75p | **fold** | 93% | 380 |
| 78 | L2 | 3BP | flop | sub=paired_high | eq=weak_hands | bs=med_75p | **call** | 96% | 377 |
| 79 | L1 | SRP | flop | tier=トップペア以上 | eq=trash_hands | bs=allin | **fold** | 95% | 368 |
| 80 | L2 | 3BP | flop | sub=monotone | eq=weak_hands | bs=med_75p | **call** | 96% | 363 |
| 81 | L2 | 4BP | turn | sub=paired_high | eq=good_hands | bs=overbet_185 | **raise** | 99% | 362 |
| 82 | L1 | 3BP | turn | tier=トップペア以上 | eq=weak_hands | bs=overbet_185 | **call** | 89% | 361 |
| 83 | L2 | 3BP | flop | sub=Khigh_spread | eq=weak_hands | bs=med_75p | **call** | 87% | 361 |
| 84 | L2 | SRP | turn | sub=mid_dry | eq=trash_hands | bs=med_75p | **fold** | 86% | 360 |
| 85 | L1 | 3BP | flop | tier=エア | eq=good_hands | bs=med_75p | **call** | 91% | 358 |
| 86 | L1 | DEF | turn | tier=トップペア以上 | eq=good_hands | bs=med_75p | **call** | 89% | 358 |
| 87 | L2 | DEF | flop | sub=Khigh_spread | eq=good_hands | bs=med_75p | **call** | 87% | 356 |
| 88 | L2 | SRP | turn | sub=Khigh_spread | eq=weak_hands | bs=small_33 | **call** | 93% | 337 |
| 89 | L2 | 3BP | turn | sub=Khigh_spread | eq=good_hands | bs=overbet_185 | **call** | 100% | 324 |
| 90 | L2 | 3BP | flop | sub=Khigh_spread | eq=good_hands | bs=small_33 | **call** | 94% | 323 |
| 91 | L2 | 3BP | flop | sub=Khigh_spread | eq=good_hands | bs=med_75p | **call** | 94% | 310 |
| 92 | L2 | DEF | flop | sub=Ahigh_spread | eq=trash_hands | bs=med_75p | **fold** | 91% | 305 |
| 93 | L2 | 3BP | flop | sub=paired_high | eq=weak_hands | bs=overbet | **fold** | 86% | 301 |
| 94 | L2 | DEF | flop | sub=monotone | eq=best_hands | bs=med_75p | **call** | 93% | 301 |
| 95 | L1 | SRP | turn | tier=ミドルペア | eq=weak_hands | bs=small_33 | **call** | 99% | 296 |
| 96 | L1 | SRP | turn | tier=トップペア以上 | eq=weak_hands | bs=med_75p | **call** | 91% | 280 |
| 97 | L1 | SRP | river | tier=ナッツメイド | eq=best_hands | bs=med_100p | **raise** | 99% | 279 |
| 98 | L1 | DEF | turn | tier=ミドルペア | eq=trash_hands | bs=med_75p | **fold** | 93% | 272 |
| 99 | L2 | SRP | river | sub=paired_high | eq=good_hands | bs=med_100p | **call** | 96% | 265 |
| 100 | L1 | DEF | turn | tier=ミドルペア | eq=good_hands | bs=med_75p | **call** | 96% | 260 |
| 101 | L2 | DEF | river | sub=mid_dry | eq=trash_hands | bs=med_75p | **fold** | 100% | 258 |
| 102 | L1 | SRP | river | tier=ストロング | eq=good_hands | bs=overbet | **call** | 99% | 257 |
| 103 | L2 | SRP | river | sub=connected_mid | eq=good_hands | bs=overbet | **call** | 99% | 257 |
| 104 | L1 | SRP | flop | tier=ツーペア | eq=trash_hands | bs=allin | **fold** | 96% | 255 |
| 105 | L2 | DEF | flop | sub=paired_high | eq=best_hands | bs=med_75p | **call** | 98% | 252 |
| 106 | L1 | 3BP | turn | tier=エア | eq=good_hands | bs=overbet_185 | **call** | 97% | 248 |
| 107 | L2 | DEF | turn | sub=monotone | eq=good_hands | bs=med_75p | **call** | 99% | 247 |
| 108 | L1 | DEF | flop | tier=ツーペア | eq=good_hands | bs=med_75p | **call** | 93% | 242 |
| 109 | L1 | SRP | river | tier=エア | eq=trash_hands | bs=med_75p | **fold** | 90% | 238 |
| 110 | L1 | SRP | flop | tier=トップペア以上 | eq=good_hands | bs=small_33 | **call** | 98% | 225 |
| 111 | L2 | 3BP | turn | sub=Khigh_spread | eq=best_hands | bs=overbet_185 | **call** | 91% | 217 |
| 112 | L2 | 3BP | flop | sub=paired_high | eq=trash_hands | bs=overbet | **fold** | 90% | 212 |
| 113 | L1 | SRP | flop | tier=ナッツメイド | eq=trash_hands | bs=allin | **fold** | 86% | 204 |

## DEFAULT ルール (4 個、暗記不要だが指示として明示)

| eq_bucket | action |
|-----------|--------|
| best_hands | call |
| good_hands | call |
| weak_hands | fold |
| trash_hands | fold |

## drill / 書籍への反映プラン

### Phase 1 (即時、最低限の実用化)
- CORE 113 ルールを drill 1 deck (1 カード = 1 ルール) として作成
- 書籍 Vol2 巻末「決定論的判定表」に CORE のみ掲載
- 読者は CORE だけで 42% の spot を捌ける

### Phase 2 (詳細版)
- FALLBACK 535 ルールを drill 第 2 deck + 書籍付録
- CORE + FALLBACK で 80% の spot

### Phase 3 (catch-all)
- DEFAULT 4 ルールは指示として目立つ位置に掲載
- 「CORE/FALLBACK で迷ったら DEFAULT を見る」flow