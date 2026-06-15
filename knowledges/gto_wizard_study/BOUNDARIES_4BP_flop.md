# 境界 spec (4BP, flop) — data 駆動の境界条件

フィルタ: pot=4BP, street=flop, depth=*, sub=*, カテゴリ=*
閾値: PURE ≥80% / STRONG 60-80% / MIXED 40-60% / BALANCED <40%
最小 n: 10

## 集計

| class | 意味 | n cells |
|---|---|---:|
| PURE | 暗記対象、書籍に書ける | 26 |
| STRONG | 基本そうする (たまに別) | 26 |
| MIXED | 拮抗、状況依存 | 23 |
| BALANCED | 完全に状況依存、要追加調査 | 0 |

## 🟢 PURE 境界 (暗記対象)

dominant action 頻度 ≥80% の cell。読者は条件確認 → 即アクション。

| pot | street | depth | sub-family | カテゴリ | action | freq | n |
|---|---|---|---|---|---|---:|---:|
| 4BP | flop | Cash100 | Ahigh_spread | ツーペア | **call** | 97% | 27 |
| 4BP | flop | Cash100 | Ahigh_spread | トップペア以上 | **raise** | 82% | 120 |
| 4BP | flop | Cash100 | Khigh_spread | ストロング | **call** | 97% | 18 |
| 4BP | flop | Cash100 | Khigh_spread | トップペア以上 | **raise** | 84% | 252 |
| 4BP | flop | MTT100 | Khigh_spread | トップペア以上 | **raise** | 83% | 126 |
| 4BP | flop | Cash100 | broadway_dry | ストロング | **call** | 88% | 18 |
| 4BP | flop | Cash100 | connected_low | トップペア以上 | **raise** | 100% | 312 |
| 4BP | flop | Cash100 | connected_mid | トップペア以上 | **raise** | 99% | 726 |
| 4BP | flop | MTT100 | connected_mid | トップペア以上 | **raise** | 98% | 288 |
| 4BP | flop | Cash100 | connected_mid | ミドルペア | **call** | 85% | 1,374 |
| 4BP | flop | MTT100 | connected_mid | ミドルペア | **call** | 86% | 552 |
| 4BP | flop | Cash100 | low_dry | トップペア以上 | **raise** | 91% | 162 |
| 4BP | flop | Cash100 | mid_dry | ストロング | **call** | 100% | 27 |
| 4BP | flop | Cash100 | mid_dry | ツーペア | **call** | 94% | 81 |
| 4BP | flop | MTT100 | mid_dry | ツーペア | **call** | 93% | 27 |
| 4BP | flop | Cash100 | mid_dry | トップペア以上 | **raise** | 91% | 462 |
| 4BP | flop | MTT100 | mid_dry | トップペア以上 | **raise** | 88% | 156 |
| 4BP | flop | Cash100 | monotone | ストロング | **call** | 94% | 216 |
| 4BP | flop | MTT100 | monotone | ストロング | **call** | 90% | 54 |
| 4BP | flop | Cash100 | paired_high | トップペア以上 | **call** | 100% | 12 |
| 4BP | flop | Cash100 | paired_high | ナッツメイド | **call** | 100% | 20 |
| 4BP | flop | MTT100 | paired_high | ナッツメイド | **call** | 100% | 10 |
| 4BP | flop | Cash100 | paired_high | ミドルペア | **raise** | 88% | 384 |
| 4BP | flop | MTT100 | paired_high | ミドルペア | **raise** | 88% | 192 |
| 4BP | flop | Cash100 | paired_mid | ナッツメイド | **call** | 97% | 10 |
| 4BP | flop | Cash100 | paired_mid | ミドルペア | **raise** | 100% | 168 |

## ⚪ data 欠落 cell

今フィルタで観測されない (pot, street, depth, sub, カテゴリ) の組合せ。
新規 probe の対象候補。

観測 cell: 75 / 期待 cell: 132 → 欠落: 57
