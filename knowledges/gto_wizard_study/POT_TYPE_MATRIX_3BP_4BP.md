# 3BP / 4BP の sub-family × tier × action 境界 (data 駆動)

dataset_unified_v2.csv の 176K rows から、3BP/4BP の board × hand tier ごとの
GTO 行動分布 (fold/call/raise) を集計。MATCHA Framework のポット種別補正の根拠。

## 概要

| pot type | street | n rows | n unique cells |
|---|---|---:|---:|
| 3BP | flop | 14,112 | 25 |
| 3BP | turn | 13,536 | 25 |
| 3BP | river | 71,346 | 58 |
| 4BP | flop | 35,280 | 55 |
| 4BP | turn | 13,536 | 25 |
| 4BP | river | 28,106 | 27 |

## 3BP flop: sub-family × tier の raise 頻度

| sub-family | ナッツメ | ストロン | ツーペア | トップペ | ミドルペ | エア |
|---|---|---|---|---|---|---|
| paired_high | 7% | 55% | — | 10% | 45% | 12% |
| Khigh_spread | — | 21% | 50% | 43% | 4% | 12% |
| mid_dry | — | 0% | 3% | 55% | 9% | 8% |
| connected_mid | — | 45% | 24% | 28% | 3% | 6% |
| monotone | — | 33% | 53% | 21% | 3% | 11% |

### 3BP flop: fold 頻度 matrix

| sub-family | ナッツメ | ストロン | ツーペア | トップペ | ミドルペ | エア |
|---|---|---|---|---|---|---|
| paired_high | 0% | 0% | — | 0% | 1% | 40% |
| Khigh_spread | — | 0% | 0% | 0% | 0% | 26% |
| mid_dry | — | 0% | 0% | 0% | 7% | 65% |
| connected_mid | — | 0% | 0% | 0% | 24% | 66% |
| monotone | — | 0% | 0% | 0% | 0% | 34% |

## 3BP turn: sub-family × tier の raise 頻度

| sub-family | ナッツメ | ストロン | ツーペア | トップペ | ミドルペ | エア |
|---|---|---|---|---|---|---|
| paired_high | 3% | 76% | — | 2% | 8% | 12% |
| Khigh_spread | — | 36% | 4% | 6% | 1% | 2% |
| mid_dry | 13% | 67% | — | 35% | 4% | 4% |
| connected_mid | — | 61% | 64% | 40% | 0% | 3% |
| monotone | 0% | 22% | — | 0% | 2% | 1% |

### 3BP turn: fold 頻度 matrix

| sub-family | ナッツメ | ストロン | ツーペア | トップペ | ミドルペ | エア |
|---|---|---|---|---|---|---|
| paired_high | 0% | 0% | — | 0% | 9% | 66% |
| Khigh_spread | — | 0% | 0% | 0% | 35% | 87% |
| mid_dry | 0% | 0% | — | 0% | 51% | 86% |
| connected_mid | — | 0% | 0% | 2% | 64% | 84% |
| monotone | 0% | 0% | — | 12% | 53% | 88% |

## 3BP river: sub-family × tier の raise 頻度

| sub-family | ナッツメ | ストロン | ツーペア | トップペ | ミドルペ | エア |
|---|---|---|---|---|---|---|
| paired_mid | 0% | 0% | — | 0% | 0% | 0% |
| paired_high | 0% | 0% | — | 0% | 0% | 0% |
| paired_broadway | 0% | — | — | — | — | 0% |
| Ahigh_spread | 0% | 0% | 0% | 0% | 0% | 0% |
| Khigh_spread | 0% | 0% | 0% | 0% | 0% | 0% |
| broadway_dry | — | 0% | 0% | 0% | 0% | 0% |
| low_dry | — | 0% | 0% | 0% | 0% | 0% |
| mid_dry | 0% | 0% | 0% | 0% | 0% | 0% |
| connected_low | 0% | 0% | 0% | 0% | 0% | 0% |
| connected_mid | 0% | 0% | 0% | 0% | 0% | 0% |
| monotone | 0% | 0% | 0% | 0% | 0% | 0% |

### 3BP river: fold 頻度 matrix

| sub-family | ナッツメ | ストロン | ツーペア | トップペ | ミドルペ | エア |
|---|---|---|---|---|---|---|
| paired_mid | 0% | 0% | — | 25% | 70% | 97% |
| paired_high | 37% | 0% | — | 33% | 56% | 93% |
| paired_broadway | 49% | — | — | — | — | 95% |
| Ahigh_spread | 0% | 0% | 0% | 1% | 75% | 95% |
| Khigh_spread | 0% | 0% | 0% | 16% | 82% | 99% |
| broadway_dry | — | 0% | 0% | 33% | 86% | 100% |
| low_dry | — | 0% | 0% | 0% | 49% | 91% |
| mid_dry | 0% | 0% | 0% | 15% | 66% | 98% |
| connected_low | 0% | 19% | 15% | 22% | 70% | 96% |
| connected_mid | 0% | 1% | 15% | 37% | 82% | 99% |
| monotone | 0% | 17% | 0% | 53% | 87% | 99% |

## 4BP flop: sub-family × tier の raise 頻度

| sub-family | ナッツメ | ストロン | ツーペア | トップペ | ミドルペ | エア |
|---|---|---|---|---|---|---|
| paired_mid | 3% | 26% | — | 43% | 100% | 11% |
| paired_high | 0% | 42% | — | 0% | 88% | 10% |
| paired_broadway | 78% | 78% | — | 42% | 55% | 26% |
| Ahigh_spread | — | 1% | 3% | 82% | 44% | 28% |
| Khigh_spread | — | 4% | 26% | 83% | 52% | 26% |
| broadway_dry | — | 12% | 46% | 79% | 31% | 23% |
| low_dry | — | 0% | 24% | 91% | 51% | 14% |
| mid_dry | — | 0% | 6% | 90% | 51% | 14% |
| connected_low | — | 21% | 69% | 100% | 38% | 23% |
| connected_mid | — | 23% | 50% | 99% | 15% | 14% |
| monotone | — | 7% | 25% | 73% | 28% | 19% |

### 4BP flop: fold 頻度 matrix

| sub-family | ナッツメ | ストロン | ツーペア | トップペ | ミドルペ | エア |
|---|---|---|---|---|---|---|
| paired_mid | 0% | 0% | — | 0% | 0% | 15% |
| paired_high | 0% | 0% | — | 0% | 0% | 14% |
| paired_broadway | 0% | 0% | — | 0% | 0% | 29% |
| Ahigh_spread | — | 0% | 0% | 0% | 0% | 31% |
| Khigh_spread | — | 0% | 0% | 0% | 0% | 33% |
| broadway_dry | — | 0% | 0% | 0% | 0% | 31% |
| low_dry | — | 0% | 0% | 0% | 0% | 15% |
| mid_dry | — | 0% | 0% | 0% | 0% | 18% |
| connected_low | — | 0% | 0% | 0% | 0% | 23% |
| connected_mid | — | 0% | 0% | 0% | 0% | 30% |
| monotone | — | 0% | 0% | 0% | 0% | 32% |

## 4BP turn: sub-family × tier の raise 頻度

| sub-family | ナッツメ | ストロン | ツーペア | トップペ | ミドルペ | エア |
|---|---|---|---|---|---|---|
| paired_high | 0% | 17% | — | 0% | 94% | 7% |
| Khigh_spread | — | 0% | 12% | 65% | 44% | 6% |
| mid_dry | 0% | 13% | — | 90% | 87% | 9% |
| connected_mid | — | 27% | 94% | 98% | 13% | 3% |
| monotone | 33% | 50% | — | 33% | 22% | 5% |

### 4BP turn: fold 頻度 matrix

| sub-family | ナッツメ | ストロン | ツーペア | トップペ | ミドルペ | エア |
|---|---|---|---|---|---|---|
| paired_high | 0% | 0% | — | 0% | 0% | 60% |
| Khigh_spread | — | 0% | 0% | 0% | 0% | 71% |
| mid_dry | 0% | 0% | — | 0% | 1% | 58% |
| connected_mid | — | 0% | 0% | 0% | 5% | 67% |
| monotone | 0% | 0% | — | 0% | 7% | 75% |

## 4BP river: sub-family × tier の raise 頻度

| sub-family | ナッツメ | ストロン | ツーペア | トップペ | ミドルペ | エア |
|---|---|---|---|---|---|---|
| paired_high | 0% | 0% | — | 0% | 0% | 0% |
| Khigh_spread | 0% | 0% | 0% | 0% | 0% | 0% |
| mid_dry | 0% | — | — | 0% | 0% | 0% |
| connected_mid | — | 0% | 0% | 0% | 0% | 0% |
| monotone | 0% | 0% | 0% | 0% | 0% | 0% |

### 4BP river: fold 頻度 matrix

| sub-family | ナッツメ | ストロン | ツーペア | トップペ | ミドルペ | エア |
|---|---|---|---|---|---|---|
| paired_high | 0% | 0% | — | 0% | 3% | 77% |
| Khigh_spread | 0% | 0% | 0% | 0% | 22% | 74% |
| mid_dry | 0% | — | — | 0% | 2% | 78% |
| connected_mid | — | 0% | 0% | 11% | 46% | 98% |
| monotone | 0% | 0% | 0% | 0% | 30% | 89% |

## tier 単独の raise 頻度 (pot type 比較)

(SRP は別ファイル `HAND_STRENGTH_BOUNDARIES.md` 参照。ここでは 3BP/4BP のみ)

| tier | 3BP flop | 4BP flop | 3BP turn | 4BP turn | 3BP river | 4BP river |
|---|---:|---:|---:|---:|---:|---:|
| ナッツメイド | 7% | 27% | 5% | 11% | 0% | 0% |
| ストロング | 31% | 19% | 52% | 21% | 0% | 0% |
| ツーペア | 33% | 31% | 34% | 53% | 0% | 0% |
| トップペア以上 | 32% | 71% | 17% | 57% | 0% | 0% |
| ミドルペア | 13% | 50% | 3% | 52% | 0% | 0% |
| エア | 10% | 19% | 4% | 6% | 0% | 0% |

## 観察 (data 駆動)

### 顕著な outlier (3BP/4BP 特有の行動)

| pot×street | sub-family | tier | raise% | n |
|---|---|---|---:|---:|
| 4BP flop | paired_mid | ミドルペア | 100% | 168 |
| 4BP flop | connected_low | トップペア以上 | 100% | 312 |
| 4BP flop | connected_mid | トップペア以上 | 99% | 1,014 |
| 4BP turn | connected_mid | トップペア以上 | 98% | 528 |
| 4BP turn | connected_mid | ツーペア | 94% | 216 |
| 4BP turn | paired_high | ミドルペア | 94% | 606 |
| 4BP flop | low_dry | トップペア以上 | 91% | 162 |
| 4BP turn | mid_dry | トップペア以上 | 90% | 330 |
| 4BP flop | mid_dry | トップペア以上 | 90% | 618 |
| 4BP flop | paired_high | ミドルペア | 88% | 576 |
| 4BP turn | mid_dry | ミドルペア | 87% | 288 |
| 4BP flop | Khigh_spread | トップペア以上 | 83% | 378 |
| 4BP flop | Ahigh_spread | トップペア以上 | 82% | 120 |
| 4BP flop | broadway_dry | トップペア以上 | 79% | 270 |
| 4BP flop | paired_broadway | ナッツメイド | 78% | 10 |
| 4BP flop | paired_broadway | ストロング | 78% | 88 |
| 3BP turn | paired_high | ストロング | 76% | 160 |
| 4BP flop | monotone | トップペア以上 | 73% | 690 |
| 4BP flop | connected_low | ツーペア | 69% | 54 |
| 3BP turn | mid_dry | ストロング | 67% | 160 |
| 4BP turn | Khigh_spread | トップペア以上 | 65% | 228 |
| 3BP turn | connected_mid | ツーペア | 64% | 216 |
| 3BP turn | connected_mid | ストロング | 61% | 176 |
| 3BP flop | paired_high | ストロング | 55% | 176 |
| 3BP flop | mid_dry | トップペア以上 | 55% | 312 |
| 4BP flop | paired_broadway | ミドルペア | 55% | 48 |
| 3BP flop | monotone | ツーペア | 53% | 54 |
| 4BP flop | Khigh_spread | ミドルペア | 52% | 882 |
| 4BP flop | mid_dry | ミドルペア | 51% | 1,062 |
| 4BP flop | low_dry | ミドルペア | 51% | 258 |

## drill / 書籍への反映

- **3BP flop**: SPR ~3.4。set 41%、TP+ ~60%、エア ~20% などが GTO 基準
- **4BP flop**: SPR ~1.3。set 4% slowplay、TP+ 60% jam ("逆転現象")
- 3BP river / 4BP river は SPR <1 で fold/call/raise が明確分離
- MATCHA Framework の "ポット種別補正章" の data 基盤として直接利用可能