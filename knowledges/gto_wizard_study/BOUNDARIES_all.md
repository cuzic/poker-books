# 境界 spec — data 駆動の境界条件

フィルタ: pot=*, street=*, depth=*, sub=*, カテゴリ=*
閾値: PURE ≥80% / STRONG 60-80% / MIXED 40-60% / BALANCED <40%
最小 n: 10

## 集計

| class | 意味 | n cells |
|---|---|---:|
| PURE | 暗記対象、書籍に書ける | 328 |
| STRONG | 基本そうする (たまに別) | 183 |
| MIXED | 拮抗、状況依存 | 108 |
| BALANCED | 完全に状況依存、要追加調査 | 0 |

## 🟢 PURE 境界 (暗記対象)

dominant action 頻度 ≥80% の cell。読者は条件確認 → 即アクション。

| pot | street | depth | sub-family | カテゴリ | action | freq | n |
|---|---|---|---|---|---|---:|---:|
| 3BP | flop | MTT100 | Khigh_spread | ミドルペア | **call** | 96% | 294 |
| 3BP | flop | Cash100 | Khigh_spread | ミドルペア | **call** | 96% | 294 |
| 3BP | flop | MTT100 | mid_dry | ツーペア | **call** | 100% | 27 |
| 3BP | flop | Cash100 | mid_dry | ツーペア | **call** | 94% | 27 |
| 3BP | flop | MTT100 | mid_dry | ミドルペア | **call** | 86% | 264 |
| 3BP | flop | Cash100 | mid_dry | ミドルペア | **call** | 83% | 264 |
| 3BP | flop | Cash100 | monotone | トップペア以上 | **call** | 81% | 138 |
| 3BP | flop | MTT100 | monotone | ミドルペア | **call** | 98% | 282 |
| 3BP | flop | Cash100 | monotone | ミドルペア | **call** | 97% | 282 |
| 3BP | flop | MTT100 | paired_high | ナッツメイド | **call** | 99% | 10 |
| 3BP | flop | Cash100 | paired_high | ナッツメイド | **call** | 87% | 10 |
| 3BP | river | Cash100 | Ahigh_spread | エア | **fold** | 95% | 2,016 |
| 3BP | river | Cash100 | Ahigh_spread | ストロング | **call** | 100% | 206 |
| 3BP | river | Cash100 | Ahigh_spread | ツーペア | **call** | 100% | 180 |
| 3BP | river | Cash100 | Ahigh_spread | トップペア以上 | **call** | 99% | 192 |
| 3BP | river | Cash100 | Ahigh_spread | ナッツメイド | **call** | 100% | 56 |
| 3BP | river | Cash100 | Khigh_spread | エア | **fold** | 99% | 2,496 |
| 3BP | river | MTT100 | Khigh_spread | エア | **fold** | 99% | 448 |
| 3BP | river | Cash100 | Khigh_spread | ストロング | **call** | 100% | 189 |
| 3BP | river | MTT100 | Khigh_spread | ストロング | **call** | 100% | 15 |
| 3BP | river | Cash100 | Khigh_spread | ツーペア | **call** | 100% | 270 |
| 3BP | river | MTT100 | Khigh_spread | ツーペア | **call** | 100% | 90 |
| 3BP | river | Cash100 | Khigh_spread | トップペア以上 | **call** | 80% | 432 |
| 3BP | river | MTT100 | Khigh_spread | トップペア以上 | **call** | 100% | 102 |
| 3BP | river | Cash100 | Khigh_spread | ナッツメイド | **call** | 100% | 56 |
| 3BP | river | Cash100 | Khigh_spread | ミドルペア | **fold** | 82% | 1,962 |
| 3BP | river | Cash100 | broadway_dry | エア | **fold** | 100% | 820 |
| 3BP | river | Cash100 | broadway_dry | ストロング | **call** | 100% | 123 |
| 3BP | river | Cash100 | broadway_dry | ツーペア | **call** | 100% | 179 |
| 3BP | river | Cash100 | broadway_dry | ミドルペア | **fold** | 86% | 830 |
| 3BP | river | Cash100 | connected_low | エア | **fold** | 96% | 1,974 |
| 3BP | river | Cash100 | connected_low | ストロング | **call** | 81% | 740 |
| 3BP | river | Cash100 | connected_low | ツーペア | **call** | 85% | 346 |
| 3BP | river | Cash100 | connected_low | ナッツメイド | **call** | 100% | 28 |
| 3BP | river | Cash100 | connected_mid | エア | **fold** | 98% | 4,920 |
| 3BP | river | MTT100 | connected_mid | エア | **fold** | 100% | 480 |
| 3BP | river | Cash100 | connected_mid | ストロング | **call** | 99% | 2,753 |
| 3BP | river | MTT100 | connected_mid | ストロング | **call** | 99% | 710 |
| 3BP | river | Cash100 | connected_mid | ツーペア | **call** | 87% | 1,078 |
| 3BP | river | Cash100 | connected_mid | ナッツメイド | **call** | 100% | 57 |
| 3BP | river | Cash100 | connected_mid | ミドルペア | **fold** | 80% | 4,946 |
| 3BP | river | MTT100 | connected_mid | ミドルペア | **fold** | 100% | 612 |
| 3BP | river | Cash100 | low_dry | エア | **fold** | 91% | 400 |
| 3BP | river | Cash100 | low_dry | ストロング | **call** | 100% | 63 |
| 3BP | river | Cash100 | low_dry | ツーペア | **call** | 100% | 90 |
| 3BP | river | Cash100 | low_dry | トップペア以上 | **call** | 100% | 132 |
| 3BP | river | Cash100 | mid_dry | エア | **fold** | 99% | 4,638 |
| 3BP | river | MTT100 | mid_dry | エア | **fold** | 95% | 726 |
| 3BP | river | Cash100 | mid_dry | ストロング | **call** | 100% | 451 |
| 3BP | river | Cash100 | mid_dry | ツーペア | **call** | 100% | 449 |
| 3BP | river | Cash100 | mid_dry | トップペア以上 | **call** | 88% | 846 |
| 3BP | river | Cash100 | mid_dry | ナッツメイド | **call** | 100% | 418 |
| 3BP | river | MTT100 | mid_dry | ナッツメイド | **call** | 100% | 181 |
| 3BP | river | Cash100 | monotone | エア | **fold** | 99% | 4,620 |
| 3BP | river | MTT100 | monotone | エア | **fold** | 97% | 525 |
| 3BP | river | Cash100 | monotone | ストロング | **call** | 81% | 1,340 |
| 3BP | river | MTT100 | monotone | ストロング | **call** | 100% | 132 |
| 3BP | river | Cash100 | monotone | ツーペア | **call** | 100% | 356 |
| 3BP | river | Cash100 | monotone | ナッツメイド | **call** | 100% | 169 |
| 3BP | river | MTT100 | monotone | ナッツメイド | **call** | 100% | 28 |
| 3BP | river | Cash100 | monotone | ミドルペア | **fold** | 88% | 3,184 |
| 3BP | river | MTT100 | monotone | ミドルペア | **fold** | 84% | 252 |
| 3BP | river | Cash100 | paired_broadway | エア | **fold** | 95% | 720 |
| 3BP | river | Cash100 | paired_high | エア | **fold** | 93% | 3,168 |
| 3BP | river | MTT100 | paired_high | エア | **fold** | 90% | 576 |
| 3BP | river | Cash100 | paired_high | ストロング | **call** | 100% | 216 |
| 3BP | river | MTT100 | paired_high | ストロング | **call** | 100% | 72 |
| 3BP | river | MTT100 | paired_high | ナッツメイド | **call** | 100% | 28 |
| 3BP | river | Cash100 | paired_mid | エア | **fold** | 97% | 2,304 |
| 3BP | river | Cash100 | paired_mid | ストロング | **call** | 100% | 288 |
| 3BP | river | Cash100 | paired_mid | ナッツメイド | **call** | 100% | 112 |
| 3BP | turn | Cash100 | Khigh_spread | エア | **fold** | 88% | 576 |
| 3BP | turn | MTT100 | Khigh_spread | エア | **fold** | 87% | 576 |
| 3BP | turn | Cash100 | Khigh_spread | ツーペア | **call** | 97% | 54 |
| 3BP | turn | MTT100 | Khigh_spread | ツーペア | **call** | 94% | 54 |
| 3BP | turn | Cash100 | Khigh_spread | トップペア以上 | **call** | 96% | 114 |
| 3BP | turn | MTT100 | Khigh_spread | トップペア以上 | **call** | 92% | 114 |
| 3BP | turn | Cash100 | connected_mid | エア | **fold** | 85% | 1,088 |
| 3BP | turn | MTT100 | connected_mid | エア | **fold** | 83% | 1,088 |
| 3BP | turn | Cash100 | mid_dry | エア | **fold** | 88% | 720 |
| 3BP | turn | MTT100 | mid_dry | エア | **fold** | 84% | 720 |
| 3BP | turn | Cash100 | mid_dry | ナッツメイド | **call** | 84% | 19 |
| 3BP | turn | MTT100 | mid_dry | ナッツメイド | **call** | 90% | 19 |
| 3BP | turn | Cash100 | monotone | エア | **fold** | 88% | 675 |
| 3BP | turn | MTT100 | monotone | エア | **fold** | 87% | 675 |
| 3BP | turn | Cash100 | monotone | トップペア以上 | **call** | 84% | 147 |
| 3BP | turn | MTT100 | monotone | トップペア以上 | **call** | 91% | 147 |
| 3BP | turn | Cash100 | monotone | ナッツメイド | **call** | 100% | 19 |
| 3BP | turn | MTT100 | monotone | ナッツメイド | **call** | 100% | 19 |
| 3BP | turn | Cash100 | paired_high | ストロング | **raise** | 82% | 80 |
| 3BP | turn | Cash100 | paired_high | ナッツメイド | **call** | 95% | 19 |
| 3BP | turn | MTT100 | paired_high | ナッツメイド | **call** | 99% | 19 |
| 3BP | turn | Cash100 | paired_high | ミドルペア | **call** | 94% | 303 |
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
| 4BP | river | Cash100 | Khigh_spread | ストロング | **call** | 100% | 189 |
| 4BP | river | MTT100 | Khigh_spread | ストロング | **call** | 100% | 15 |
| 4BP | river | Cash100 | Khigh_spread | ツーペア | **call** | 100% | 270 |
| 4BP | river | MTT100 | Khigh_spread | ツーペア | **call** | 100% | 90 |
| 4BP | river | Cash100 | Khigh_spread | トップペア以上 | **call** | 100% | 432 |
| 4BP | river | MTT100 | Khigh_spread | トップペア以上 | **call** | 100% | 102 |
| 4BP | river | Cash100 | Khigh_spread | ナッツメイド | **call** | 100% | 56 |
| 4BP | river | MTT100 | Khigh_spread | ミドルペア | **call** | 82% | 426 |
| 4BP | river | Cash100 | connected_mid | エア | **fold** | 98% | 1,720 |
| 4BP | river | MTT100 | connected_mid | エア | **fold** | 99% | 480 |
| 4BP | river | Cash100 | connected_mid | ストロング | **call** | 100% | 1,615 |
| 4BP | river | MTT100 | connected_mid | ストロング | **call** | 100% | 710 |
| 4BP | river | Cash100 | connected_mid | ツーペア | **call** | 100% | 538 |
| 4BP | river | MTT100 | connected_mid | ツーペア | **call** | 100% | 180 |
| 4BP | river | Cash100 | connected_mid | トップペア以上 | **call** | 90% | 540 |
| 4BP | river | MTT100 | connected_mid | トップペア以上 | **call** | 84% | 180 |
| 4BP | river | Cash100 | mid_dry | トップペア以上 | **call** | 100% | 36 |
| 4BP | river | MTT100 | mid_dry | トップペア以上 | **call** | 100% | 36 |
| 4BP | river | Cash100 | mid_dry | ナッツメイド | **call** | 100% | 181 |
| 4BP | river | MTT100 | mid_dry | ナッツメイド | **call** | 100% | 181 |
| 4BP | river | Cash100 | mid_dry | ミドルペア | **call** | 96% | 138 |
| 4BP | river | MTT100 | mid_dry | ミドルペア | **call** | 100% | 138 |
| 4BP | river | Cash100 | monotone | エア | **fold** | 89% | 2,400 |
| 4BP | river | Cash100 | monotone | ストロング | **call** | 100% | 531 |
| 4BP | river | Cash100 | monotone | ツーペア | **call** | 100% | 178 |
| 4BP | river | Cash100 | monotone | トップペア以上 | **call** | 100% | 587 |
| 4BP | river | Cash100 | monotone | ナッツメイド | **call** | 100% | 84 |
| 4BP | river | Cash100 | paired_high | ストロング | **call** | 100% | 216 |
| 4BP | river | Cash100 | paired_high | トップペア以上 | **call** | 100% | 138 |
| 4BP | river | Cash100 | paired_high | ナッツメイド | **call** | 100% | 806 |
| 4BP | river | Cash100 | paired_high | ミドルペア | **call** | 97% | 1,077 |
| 4BP | turn | Cash100 | Khigh_spread | ストロング | **call** | 100% | 12 |
| 4BP | turn | MTT100 | Khigh_spread | ストロング | **call** | 100% | 12 |
| 4BP | turn | Cash100 | Khigh_spread | ツーペア | **call** | 87% | 54 |
| 4BP | turn | MTT100 | Khigh_spread | ツーペア | **call** | 89% | 54 |
| 4BP | turn | Cash100 | connected_mid | ツーペア | **raise** | 92% | 108 |
| 4BP | turn | MTT100 | connected_mid | ツーペア | **raise** | 96% | 108 |
| 4BP | turn | Cash100 | connected_mid | トップペア以上 | **raise** | 98% | 264 |
| 4BP | turn | MTT100 | connected_mid | トップペア以上 | **raise** | 98% | 264 |
| 4BP | turn | Cash100 | connected_mid | ミドルペア | **call** | 83% | 708 |
| 4BP | turn | MTT100 | connected_mid | ミドルペア | **call** | 80% | 708 |
| 4BP | turn | Cash100 | mid_dry | ストロング | **call** | 83% | 80 |
| 4BP | turn | MTT100 | mid_dry | ストロング | **call** | 92% | 80 |
| 4BP | turn | Cash100 | mid_dry | トップペア以上 | **raise** | 91% | 165 |
| 4BP | turn | MTT100 | mid_dry | トップペア以上 | **raise** | 89% | 165 |
| 4BP | turn | Cash100 | mid_dry | ナッツメイド | **call** | 100% | 19 |
| 4BP | turn | MTT100 | mid_dry | ナッツメイド | **call** | 100% | 19 |
| 4BP | turn | Cash100 | mid_dry | ミドルペア | **raise** | 82% | 144 |
| 4BP | turn | MTT100 | mid_dry | ミドルペア | **raise** | 91% | 144 |
| 4BP | turn | Cash100 | paired_high | ストロング | **call** | 85% | 80 |
| 4BP | turn | MTT100 | paired_high | ストロング | **call** | 82% | 80 |
| 4BP | turn | Cash100 | paired_high | ナッツメイド | **call** | 100% | 19 |
| 4BP | turn | MTT100 | paired_high | ナッツメイド | **call** | 100% | 19 |
| 4BP | turn | Cash100 | paired_high | ミドルペア | **raise** | 94% | 303 |
| 4BP | turn | MTT100 | paired_high | ミドルペア | **raise** | 94% | 303 |
| DEF | flop | Cash100 | Ahigh_spread | エア | **fold** | 91% | 456 |
| DEF | flop | Cash100 | Ahigh_spread | ストロング | **call** | 100% | 18 |
| DEF | flop | Cash100 | Ahigh_spread | ツーペア | **call** | 100% | 36 |
| DEF | flop | Cash100 | Ahigh_spread | トップペア以上 | **call** | 91% | 204 |
| DEF | flop | Cash100 | Khigh_spread | ミドルペア | **call** | 85% | 360 |
| DEF | flop | Cash100 | broadway_dry | トップペア以上 | **call** | 86% | 342 |
| DEF | flop | Cash100 | connected_low | ツーペア | **call** | 95% | 26 |
| DEF | flop | Cash100 | connected_mid | ツーペア | **call** | 95% | 130 |
| DEF | flop | Cash100 | low_dry | ストロング | **raise** | 82% | 18 |
| DEF | flop | Cash100 | mid_dry | ツーペア | **raise** | 85% | 16 |
| DEF | flop | Cash100 | monotone | ストロング | **call** | 90% | 336 |
| DEF | flop | Cash100 | monotone | ツーペア | **call** | 95% | 54 |
| DEF | flop | Cash100 | monotone | トップペア以上 | **call** | 90% | 726 |
| DEF | flop | Cash100 | paired_broadway | ストロング | **call** | 92% | 80 |
| DEF | flop | Cash100 | paired_broadway | トップペア以上 | **call** | 95% | 180 |
| DEF | flop | Cash100 | paired_broadway | ミドルペア | **call** | 82% | 96 |
| DEF | flop | Cash100 | paired_high | ストロング | **call** | 84% | 232 |
| DEF | flop | Cash100 | paired_high | トップペア以上 | **call** | 90% | 24 |
| DEF | flop | Cash100 | paired_high | ミドルペア | **call** | 89% | 252 |
| DEF | flop | Cash100 | paired_mid | ストロング | **call** | 84% | 104 |
| DEF | flop | Cash100 | paired_mid | トップペア以上 | **call** | 92% | 60 |
| DEF | flop | Cash100 | paired_mid | ミドルペア | **call** | 90% | 84 |
| DEF | river | Cash100 | Khigh_spread | ストロング | **raise** | 100% | 15 |
| DEF | river | Cash100 | Khigh_spread | ツーペア | **raise** | 100% | 17 |
| DEF | river | Cash100 | Khigh_spread | ミドルペア | **call** | 93% | 138 |
| DEF | river | Cash100 | connected_mid | ツーペア | **call** | 100% | 66 |
| DEF | river | Cash100 | connected_mid | トップペア以上 | **call** | 82% | 108 |
| DEF | river | Cash100 | mid_dry | エア | **fold** | 86% | 362 |
| DEF | river | Cash100 | mid_dry | トップペア以上 | **call** | 100% | 36 |
| DEF | river | Cash100 | monotone | トップペア以上 | **call** | 97% | 99 |
| DEF | river | Cash100 | monotone | ナッツメイド | **raise** | 100% | 10 |
| DEF | river | Cash100 | paired_high | ストロング | **raise** | 100% | 48 |
| DEF | river | Cash100 | paired_high | ナッツメイド | **raise** | 100% | 18 |
| DEF | river | Cash100 | paired_high | ミドルペア | **call** | 95% | 117 |
| DEF | turn | Cash100 | Khigh_spread | ツーペア | **call** | 81% | 12 |
| DEF | turn | Cash100 | connected_mid | ツーペア | **call** | 95% | 52 |
| DEF | turn | Cash100 | monotone | エア | **fold** | 85% | 606 |
| DEF | turn | Cash100 | monotone | ストロング | **call** | 97% | 78 |
| DEF | turn | Cash100 | monotone | ナッツメイド | **call** | 99% | 14 |
| DEF | turn | Cash100 | paired_high | ストロング | **call** | 95% | 112 |
| DEF | turn | Cash100 | paired_high | トップペア以上 | **call** | 100% | 12 |
| DEF | turn | Cash100 | paired_high | ナッツメイド | **call** | 87% | 18 |
| DEF | turn | Cash100 | paired_high | ミドルペア | **call** | 82% | 126 |
| SRP | flop | Cash100 | Ahigh_spread | エア | **fold** | 100% | 1,020 |
| SRP | flop | Cash100 | Ahigh_spread | ツーペア | **fold** | 95% | 22 |
| SRP | flop | Cash100 | Ahigh_spread | トップペア以上 | **fold** | 88% | 194 |
| SRP | flop | Cash100 | Ahigh_spread | ミドルペア | **fold** | 100% | 701 |
| SRP | flop | Cash100 | Khigh_spread | エア | **fold** | 85% | 1,168 |
| SRP | flop | Cash100 | broadway_dry | エア | **fold** | 100% | 743 |
| SRP | flop | Cash100 | broadway_dry | ストロング | **call** | 81% | 125 |
| SRP | flop | Cash100 | broadway_dry | ツーペア | **fold** | 87% | 97 |
| SRP | flop | Cash100 | broadway_dry | ミドルペア | **fold** | 89% | 650 |
| SRP | flop | Cash100 | connected_mid | エア | **fold** | 91% | 3,502 |
| SRP | flop | Cash100 | connected_mid | ツーペア | **fold** | 90% | 787 |
| SRP | flop | Cash100 | connected_mid | トップペア以上 | **fold** | 80% | 1,651 |
| SRP | flop | Cash100 | connected_mid | ナッツメイド | **call** | 82% | 73 |
| SRP | flop | Cash100 | connected_mid | ミドルペア | **fold** | 87% | 3,440 |
| SRP | flop | Cash100 | mid_dry | エア | **fold** | 92% | 1,284 |
| SRP | flop | Cash100 | mid_dry | ストロング | **call** | 92% | 68 |
| SRP | flop | Cash100 | mid_dry | ナッツメイド | **call** | 100% | 20 |
| SRP | flop | Cash100 | monotone | エア | **fold** | 95% | 2,955 |
| SRP | flop | Cash100 | monotone | ツーペア | **fold** | 93% | 306 |
| SRP | flop | Cash100 | monotone | トップペア以上 | **fold** | 91% | 1,215 |
| SRP | flop | Cash100 | monotone | ナッツメイド | **call** | 90% | 72 |
| SRP | flop | Cash100 | monotone | ミドルペア | **fold** | 91% | 2,104 |
| SRP | flop | Cash100 | paired_high | エア | **fold** | 92% | 2,676 |
| SRP | flop | Cash100 | paired_high | トップペア以上 | **fold** | 100% | 24 |
| SRP | flop | Cash100 | paired_high | ミドルペア | **fold** | 83% | 471 |
| SRP | flop | Cash100 | paired_mid | エア | **fold** | 100% | 1,112 |
| SRP | flop | Cash100 | paired_mid | トップペア以上 | **fold** | 100% | 222 |
| SRP | flop | Cash100 | paired_mid | ナッツメイド | **call** | 84% | 64 |
| SRP | flop | Cash100 | paired_mid | ミドルペア | **fold** | 98% | 339 |
| SRP | river | MTT200 | Khigh_spread | エア | **fold** | 96% | 448 |
| SRP | river | Cash100 | Khigh_spread | エア | **fold** | 99% | 1,184 |
| SRP | river | MTT100 | Khigh_spread | エア | **fold** | 100% | 448 |
| SRP | river | MTT25 | Khigh_spread | エア | **fold** | 94% | 376 |
| SRP | river | MTT200 | Khigh_spread | ストロング | **raise** | 100% | 15 |
| SRP | river | MTT100 | Khigh_spread | ストロング | **call** | 100% | 15 |
| SRP | river | MTT100 | Khigh_spread | ツーペア | **call** | 100% | 90 |
| SRP | river | MTT25 | Khigh_spread | ツーペア | **call** | 100% | 56 |
| SRP | river | MTT200 | Khigh_spread | トップペア以上 | **call** | 99% | 102 |
| SRP | river | MTT25 | Khigh_spread | トップペア以上 | **call** | 100% | 75 |
| SRP | river | Cash100 | Khigh_spread | ミドルペア | **fold** | 90% | 771 |
| SRP | river | MTT100 | Khigh_spread | ミドルペア | **fold** | 97% | 426 |
| SRP | river | MTT200 | connected_mid | エア | **fold** | 100% | 480 |
| SRP | river | Cash100 | connected_mid | エア | **fold** | 97% | 1,088 |
| SRP | river | MTT100 | connected_mid | エア | **fold** | 100% | 480 |
| SRP | river | MTT25 | connected_mid | エア | **fold** | 100% | 392 |
| SRP | river | MTT25 | connected_mid | ストロング | **call** | 100% | 600 |
| SRP | river | MTT100 | connected_mid | ツーペア | **fold** | 81% | 180 |
| SRP | river | MTT25 | connected_mid | ツーペア | **call** | 97% | 140 |
| SRP | river | MTT100 | connected_mid | トップペア以上 | **fold** | 92% | 180 |
| SRP | river | MTT200 | connected_mid | ミドルペア | **fold** | 99% | 612 |
| SRP | river | Cash100 | connected_mid | ミドルペア | **fold** | 96% | 1,224 |
| SRP | river | MTT100 | connected_mid | ミドルペア | **fold** | 99% | 612 |
| SRP | river | MTT25 | connected_mid | ミドルペア | **fold** | 96% | 450 |
| SRP | river | MTT200 | mid_dry | エア | **fold** | 95% | 726 |
| SRP | river | Cash100 | mid_dry | エア | **fold** | 92% | 1,740 |
| SRP | river | MTT100 | mid_dry | エア | **fold** | 100% | 726 |
| SRP | river | MTT25 | mid_dry | エア | **fold** | 89% | 572 |
| SRP | river | MTT100 | mid_dry | トップペア以上 | **fold** | 94% | 36 |
| SRP | river | MTT100 | mid_dry | ナッツメイド | **call** | 94% | 181 |
| SRP | river | MTT25 | mid_dry | ナッツメイド | **call** | 100% | 143 |
| SRP | river | MTT200 | monotone | エア | **fold** | 96% | 525 |
| SRP | river | Cash100 | monotone | エア | **fold** | 99% | 1,092 |
| SRP | river | MTT100 | monotone | エア | **fold** | 97% | 525 |
| SRP | river | MTT25 | monotone | エア | **fold** | 100% | 408 |
| SRP | river | MTT200 | monotone | ストロング | **call** | 92% | 132 |
| SRP | river | Cash100 | monotone | ストロング | **call** | 92% | 313 |
| SRP | river | MTT25 | monotone | ストロング | **call** | 100% | 117 |
| SRP | river | MTT25 | monotone | トップペア以上 | **call** | 100% | 114 |
| SRP | river | MTT200 | monotone | ナッツメイド | **raise** | 94% | 28 |
| SRP | river | Cash100 | monotone | ナッツメイド | **raise** | 96% | 54 |
| SRP | river | MTT100 | monotone | ナッツメイド | **raise** | 100% | 28 |
| SRP | river | MTT25 | monotone | ミドルペア | **fold** | 87% | 189 |
| SRP | river | MTT200 | paired_high | エア | **fold** | 91% | 576 |
| SRP | river | Cash100 | paired_high | エア | **fold** | 85% | 1,424 |
| SRP | river | MTT100 | paired_high | エア | **fold** | 100% | 576 |
| SRP | river | MTT25 | paired_high | エア | **fold** | 92% | 504 |
| SRP | river | MTT200 | paired_high | ストロング | **call** | 95% | 72 |
| SRP | river | Cash100 | paired_high | ストロング | **call** | 86% | 230 |
| SRP | river | MTT100 | paired_high | ストロング | **call** | 100% | 72 |
| SRP | river | MTT25 | paired_high | ストロング | **call** | 100% | 58 |
| SRP | river | MTT200 | paired_high | ナッツメイド | **raise** | 100% | 28 |
| SRP | river | Cash100 | paired_high | ナッツメイド | **raise** | 90% | 71 |
| SRP | river | MTT100 | paired_high | ナッツメイド | **call** | 100% | 28 |
| SRP | river | MTT25 | paired_high | ナッツメイド | **call** | 100% | 18 |
| SRP | turn | Cash100 | Khigh_spread | エア | **fold** | 96% | 1,024 |
| SRP | turn | MTT200 | Khigh_spread | ストロング | **raise** | 82% | 12 |
| SRP | turn | Cash100 | Khigh_spread | ストロング | **call** | 92% | 27 |
| SRP | turn | Cash100 | Khigh_spread | ツーペア | **call** | 96% | 45 |
| SRP | turn | MTT200 | Khigh_spread | トップペア以上 | **call** | 88% | 114 |
| SRP | turn | Cash100 | Khigh_spread | トップペア以上 | **call** | 85% | 225 |
| SRP | turn | MTT200 | Khigh_spread | ミドルペア | **call** | 98% | 372 |
| SRP | turn | Cash100 | Khigh_spread | ミドルペア | **fold** | 81% | 438 |
| SRP | turn | MTT200 | connected_mid | エア | **fold** | 82% | 1,088 |
| SRP | turn | Cash100 | connected_mid | エア | **fold** | 85% | 1,672 |
| SRP | turn | MTT200 | connected_mid | ツーペア | **call** | 93% | 108 |
| SRP | turn | Cash100 | connected_mid | ツーペア | **call** | 82% | 125 |
| SRP | turn | MTT200 | connected_mid | トップペア以上 | **call** | 96% | 264 |
| SRP | turn | MTT200 | mid_dry | エア | **fold** | 98% | 720 |
| SRP | turn | Cash100 | mid_dry | エア | **fold** | 83% | 1,164 |
| SRP | turn | Cash100 | mid_dry | トップペア以上 | **call** | 83% | 267 |
| SRP | turn | MTT200 | mid_dry | ナッツメイド | **call** | 100% | 19 |
| SRP | turn | MTT200 | monotone | エア | **fold** | 90% | 675 |
| SRP | turn | Cash100 | monotone | エア | **fold** | 91% | 999 |
| SRP | turn | MTT200 | monotone | ストロング | **call** | 100% | 125 |
| SRP | turn | Cash100 | monotone | ストロング | **call** | 88% | 175 |
| SRP | turn | MTT200 | monotone | トップペア以上 | **call** | 91% | 147 |
| SRP | turn | Cash100 | monotone | トップペア以上 | **call** | 94% | 237 |
| SRP | turn | MTT200 | monotone | ナッツメイド | **call** | 99% | 19 |
| SRP | turn | Cash100 | monotone | ナッツメイド | **call** | 81% | 26 |
| SRP | turn | Cash100 | paired_high | ストロング | **call** | 93% | 168 |
| SRP | turn | Cash100 | paired_high | ミドルペア | **call** | 81% | 291 |

## 🟡 STRONG 境界 (推奨アクション)

dominant 60-80%。基本そうするが、たまに別の action もあり。

| pot | street | depth | sub-family | カテゴリ | action | freq | n |
|---|---|---|---|---|---|---:|---:|
| 4BP | river | Cash100 | mid_dry | エア | fold | 80% | 726 |
| DEF | turn | Cash100 | mid_dry | エア | fold | 80% | 712 |
| SRP | flop | Cash100 | Khigh_spread | ナッツメイド | call | 80% | 29 |
| SRP | river | MTT200 | paired_high | ミドルペア | call | 79% | 399 |
| 3BP | turn | Cash100 | monotone | ストロング | call | 79% | 125 |
| DEF | flop | Cash100 | connected_mid | ストロング | call | 79% | 266 |
| 4BP | flop | Cash100 | broadway_dry | トップペア以上 | raise | 79% | 270 |
| 3BP | flop | MTT100 | connected_mid | ツーペア | call | 79% | 54 |
| 4BP | flop | Cash100 | connected_low | ストロング | call | 79% | 82 |
| SRP | river | MTT100 | monotone | ストロング | call | 79% | 132 |
| 3BP | river | MTT100 | Khigh_spread | ミドルペア | fold | 79% | 426 |
| DEF | river | Cash100 | mid_dry | ナッツメイド | call | 79% | 58 |
| 4BP | flop | MTT100 | paired_high | エア | call | 79% | 880 |
| 4BP | flop | Cash100 | paired_broadway | ナッツメイド | raise | 78% | 10 |
| 4BP | flop | Cash100 | paired_broadway | ストロング | raise | 78% | 88 |
| SRP | river | MTT200 | Khigh_spread | ツーペア | call | 78% | 90 |
| SRP | river | MTT200 | mid_dry | トップペア以上 | fold | 78% | 36 |
| SRP | turn | MTT200 | paired_high | ミドルペア | call | 78% | 303 |
| DEF | flop | Cash100 | mid_dry | エア | fold | 78% | 2,064 |
| 4BP | flop | MTT100 | monotone | トップペア以上 | raise | 78% | 138 |
| 3BP | river | Cash100 | connected_low | トップペア以上 | call | 78% | 414 |
| DEF | river | Cash100 | monotone | ストロング | raise | 77% | 54 |
| 3BP | turn | MTT100 | monotone | ストロング | call | 77% | 125 |
| SRP | turn | Cash100 | connected_mid | ストロング | raise | 77% | 144 |
| 4BP | flop | Cash100 | connected_mid | ストロング | call | 77% | 205 |
| 4BP | flop | MTT100 | monotone | ツーペア | call | 77% | 27 |
| 4BP | turn | Cash100 | Khigh_spread | トップペア以上 | raise | 77% | 114 |
| 4BP | turn | Cash100 | monotone | エア | fold | 77% | 675 |
| SRP | turn | MTT200 | Khigh_spread | ツーペア | call | 77% | 54 |
| 4BP | river | Cash100 | Khigh_spread | ミドルペア | call | 77% | 1,962 |
| 4BP | river | Cash100 | paired_high | エア | fold | 77% | 3,168 |
| 4BP | flop | MTT100 | connected_mid | ストロング | call | 77% | 82 |
| 3BP | flop | MTT100 | connected_mid | ミドルペア | call | 77% | 552 |
| DEF | flop | Cash100 | low_dry | エア | fold | 77% | 816 |
| DEF | river | Cash100 | connected_mid | エア | fold | 76% | 216 |
| 4BP | river | MTT100 | mid_dry | エア | fold | 76% | 726 |
| SRP | flop | Cash100 | mid_dry | ツーペア | call | 76% | 23 |
| SRP | flop | Cash100 | broadway_dry | トップペア以上 | fold | 76% | 312 |
| 3BP | flop | MTT100 | monotone | トップペア以上 | call | 76% | 138 |
| 4BP | river | Cash100 | Khigh_spread | エア | fold | 76% | 2,496 |
| DEF | flop | Cash100 | low_dry | トップペア以上 | raise | 76% | 150 |
| 4BP | flop | Cash100 | low_dry | ツーペア | call | 76% | 27 |
| SRP | river | MTT100 | paired_high | ミドルペア | fold | 75% | 399 |
| 4BP | flop | Cash100 | monotone | ツーペア | call | 75% | 108 |
| 3BP | river | MTT100 | connected_mid | ツーペア | call | 75% | 180 |
| 3BP | river | Cash100 | Ahigh_spread | ミドルペア | fold | 75% | 1,674 |
| 4BP | flop | Cash100 | paired_high | エア | call | 75% | 1,760 |
| 3BP | river | Cash100 | paired_mid | トップペア以上 | call | 75% | 414 |
| SRP | turn | MTT200 | mid_dry | ミドルペア | fold | 74% | 144 |
| 4BP | flop | Cash100 | paired_mid | ストロング | call | 74% | 88 |
| 4BP | flop | Cash100 | Khigh_spread | ツーペア | call | 74% | 54 |
| 3BP | turn | MTT100 | paired_high | エア | fold | 74% | 720 |
| SRP | river | MTT100 | Khigh_spread | トップペア以上 | fold | 74% | 102 |
| 4BP | flop | Cash100 | paired_mid | エア | call | 74% | 880 |
| DEF | flop | Cash100 | broadway_dry | エア | fold | 74% | 1,216 |
| 4BP | flop | Cash100 | monotone | ミドルペア | call | 74% | 1,128 |
| DEF | turn | Cash100 | mid_dry | ナッツメイド | call | 74% | 14 |
| SRP | river | MTT100 | connected_mid | ストロング | call | 73% | 710 |
| DEF | flop | Cash100 | Khigh_spread | トップペア以上 | call | 73% | 360 |
| 4BP | turn | Cash100 | monotone | ミドルペア | call | 73% | 162 |
| 4BP | turn | Cash100 | connected_mid | ストロング | call | 73% | 88 |
| SRP | flop | Cash100 | mid_dry | ミドルペア | fold | 73% | 416 |
| 3BP | flop | MTT100 | paired_high | エア | call | 73% | 880 |
| SRP | flop | Cash100 | mid_dry | トップペア以上 | call | 73% | 391 |
| 3BP | flop | Cash100 | connected_mid | トップペア以上 | call | 73% | 288 |
| 4BP | turn | Cash100 | Khigh_spread | エア | fold | 73% | 576 |
| DEF | flop | Cash100 | broadway_dry | ツーペア | call | 73% | 34 |
| SRP | river | Cash100 | mid_dry | トップペア以上 | fold | 73% | 102 |
| 4BP | turn | MTT100 | monotone | エア | fold | 73% | 675 |
| 4BP | turn | MTT100 | connected_mid | ストロング | call | 73% | 88 |
| 3BP | river | MTT100 | connected_mid | トップペア以上 | fold | 73% | 180 |
| 4BP | flop | MTT100 | Khigh_spread | ツーペア | call | 73% | 27 |
| DEF | turn | Cash100 | monotone | ミドルペア | call | 72% | 150 |
| 3BP | flop | Cash100 | connected_mid | ツーペア | call | 72% | 54 |
| SRP | turn | Cash100 | paired_high | エア | fold | 72% | 1,264 |
| 4BP | flop | Cash100 | monotone | トップペア以上 | raise | 72% | 552 |
| SRP | river | Cash100 | connected_mid | トップペア以上 | fold | 72% | 420 |
| SRP | river | MTT200 | mid_dry | ミドルペア | call | 72% | 138 |
| SRP | river | Cash100 | mid_dry | ナッツメイド | call | 71% | 315 |
| 3BP | turn | MTT100 | paired_high | ミドルペア | call | 71% | 303 |
| DEF | turn | Cash100 | connected_mid | エア | fold | 71% | 960 |
| 4BP | flop | Cash100 | low_dry | エア | call | 71% | 720 |
| 3BP | turn | MTT100 | paired_high | ストロング | raise | 70% | 80 |
| 3BP | river | Cash100 | paired_mid | ミドルペア | fold | 70% | 1,206 |
| 3BP | flop | MTT100 | connected_mid | トップペア以上 | call | 70% | 288 |
| 4BP | flop | MTT100 | mid_dry | エア | call | 70% | 720 |
| 3BP | river | Cash100 | connected_low | ミドルペア | fold | 70% | 1,903 |
| 4BP | turn | MTT100 | Khigh_spread | エア | fold | 70% | 576 |
| 3BP | flop | MTT100 | paired_high | ミドルペア | call | 70% | 192 |
| DEF | river | Cash100 | monotone | ミドルペア | call | 70% | 118 |
| SRP | river | MTT100 | monotone | ミドルペア | fold | 70% | 252 |
| 4BP | turn | Cash100 | monotone | トップペア以上 | call | 70% | 147 |
| DEF | flop | Cash100 | broadway_dry | ストロング | call | 70% | 36 |
| 3BP | flop | Cash100 | connected_mid | ミドルペア | call | 70% | 552 |
| 4BP | river | Cash100 | monotone | ミドルペア | call | 70% | 1,625 |
| DEF | turn | Cash100 | mid_dry | ストロング | call | 69% | 12 |
| DEF | turn | Cash100 | Khigh_spread | エア | fold | 69% | 656 |
| 4BP | turn | Cash100 | monotone | ナッツメイド | call | 69% | 19 |
| 3BP | turn | MTT100 | Khigh_spread | ミドルペア | call | 69% | 372 |
| 4BP | flop | Cash100 | connected_low | ツーペア | raise | 69% | 54 |
| DEF | flop | Cash100 | monotone | ミドルペア | call | 69% | 822 |
| DEF | flop | Cash100 | connected_low | エア | fold | 69% | 1,280 |
| 4BP | turn | Cash100 | connected_mid | エア | fold | 69% | 1,088 |
| 4BP | flop | Cash100 | broadway_dry | ミドルペア | call | 69% | 570 |
| 3BP | flop | MTT100 | monotone | ストロング | call | 68% | 54 |
| SRP | turn | MTT200 | mid_dry | トップペア以上 | call | 68% | 165 |
| SRP | river | Cash100 | connected_mid | ストロング | call | 68% | 1,684 |
| DEF | flop | Cash100 | paired_high | ナッツメイド | call | 68% | 20 |
| SRP | turn | MTT200 | Khigh_spread | エア | fold | 68% | 576 |
| SRP | flop | Cash100 | Khigh_spread | ミドルペア | fold | 68% | 574 |
| 3BP | river | Cash100 | connected_mid | トップペア以上 | call | 68% | 1,380 |
| SRP | river | MTT200 | monotone | ミドルペア | fold | 68% | 252 |
| 3BP | flop | Cash100 | mid_dry | エア | fold | 67% | 720 |
| DEF | turn | Cash100 | paired_high | エア | fold | 67% | 744 |
| 4BP | flop | Cash100 | mid_dry | エア | call | 67% | 2,160 |
| 3BP | river | MTT100 | mid_dry | トップペア以上 | fold | 67% | 36 |
| DEF | turn | Cash100 | connected_mid | ストロング | raise | 67% | 128 |
| 3BP | river | Cash100 | broadway_dry | トップペア以上 | call | 67% | 210 |
| DEF | turn | Cash100 | monotone | トップペア以上 | call | 67% | 204 |
| 3BP | turn | Cash100 | mid_dry | ストロング | raise | 67% | 80 |
| DEF | river | Cash100 | Khigh_spread | トップペア以上 | raise | 67% | 75 |
| SRP | river | Cash100 | monotone | ミドルペア | fold | 67% | 618 |
| 4BP | turn | MTT100 | monotone | ミドルペア | call | 67% | 162 |
| SRP | turn | Cash100 | connected_mid | トップペア以上 | call | 67% | 408 |
| DEF | flop | Cash100 | connected_mid | エア | fold | 67% | 2,552 |
| DEF | flop | Cash100 | connected_mid | トップペア以上 | call | 66% | 882 |
| 3BP | flop | Cash100 | connected_mid | エア | fold | 66% | 1,376 |
| 4BP | flop | MTT100 | monotone | ミドルペア | call | 66% | 282 |
| SRP | flop | Cash100 | paired_mid | ストロング | fold | 66% | 196 |
| DEF | flop | Cash100 | paired_broadway | ナッツメイド | call | 66% | 20 |
| SRP | flop | Cash100 | Ahigh_spread | ストロング | fold | 66% | 196 |
| 3BP | river | Cash100 | mid_dry | ミドルペア | fold | 66% | 2,927 |
| 3BP | turn | MTT100 | mid_dry | トップペア以上 | call | 66% | 165 |
| 3BP | turn | MTT100 | mid_dry | ストロング | raise | 66% | 80 |
| DEF | flop | Cash100 | connected_low | トップペア以上 | call | 66% | 408 |
| 4BP | river | MTT100 | Khigh_spread | エア | fold | 66% | 448 |
| 3BP | flop | Cash100 | monotone | ストロング | call | 66% | 54 |
| SRP | turn | Cash100 | connected_mid | ミドルペア | fold | 66% | 1,062 |
| 4BP | turn | MTT100 | connected_mid | エア | fold | 66% | 1,088 |
| 3BP | turn | Cash100 | connected_mid | ミドルペア | fold | 66% | 708 |
| 3BP | river | Cash100 | paired_high | トップペア以上 | call | 66% | 138 |
| SRP | river | MTT25 | paired_high | ミドルペア | call | 65% | 268 |
| 3BP | flop | MTT100 | connected_mid | エア | fold | 65% | 1,376 |
| 4BP | turn | MTT100 | monotone | トップペア以上 | call | 65% | 147 |
| SRP | turn | Cash100 | mid_dry | ナッツメイド | call | 65% | 24 |
| 3BP | turn | MTT100 | connected_mid | ツーペア | raise | 65% | 108 |
| DEF | turn | Cash100 | mid_dry | トップペア以上 | call | 65% | 214 |
| 3BP | turn | Cash100 | Khigh_spread | ストロング | call | 65% | 12 |
| DEF | turn | Cash100 | Khigh_spread | トップペア以上 | call | 65% | 174 |
| 3BP | turn | Cash100 | mid_dry | トップペア以上 | call | 65% | 165 |
| 3BP | flop | Cash100 | paired_high | ストロング | raise | 65% | 88 |
| 3BP | flop | MTT100 | Khigh_spread | エア | call | 64% | 720 |
| 4BP | turn | MTT100 | monotone | ナッツメイド | call | 64% | 19 |
| SRP | turn | Cash100 | mid_dry | ストロング | call | 64% | 60 |
| 3BP | river | MTT100 | mid_dry | ミドルペア | fold | 64% | 138 |
| 3BP | flop | Cash100 | paired_high | エア | fold | 63% | 880 |
| DEF | flop | Cash100 | mid_dry | ストロング | raise | 63% | 54 |
| DEF | flop | Cash100 | monotone | エア | fold | 63% | 2,256 |
| 3BP | turn | MTT100 | Khigh_spread | ストロング | call | 63% | 12 |
| 3BP | river | MTT100 | monotone | トップペア以上 | fold | 63% | 144 |
| 3BP | turn | Cash100 | connected_mid | ツーペア | raise | 63% | 108 |
| 3BP | flop | MTT100 | mid_dry | エア | fold | 62% | 720 |
| SRP | flop | Cash100 | paired_high | ナッツメイド | fold | 62% | 633 |
| DEF | turn | Cash100 | connected_mid | ミドルペア | fold | 62% | 528 |
| 3BP | river | Cash100 | paired_high | ミドルペア | fold | 62% | 1,077 |
| DEF | turn | Cash100 | Khigh_spread | ストロング | raise | 62% | 24 |
| 3BP | turn | MTT100 | connected_mid | ミドルペア | fold | 62% | 708 |
| 4BP | flop | Cash100 | connected_low | ミドルペア | call | 62% | 528 |
| DEF | flop | Cash100 | paired_broadway | エア | fold | 62% | 624 |
| 3BP | river | Cash100 | paired_high | ナッツメイド | call | 62% | 806 |
| 3BP | turn | Cash100 | connected_mid | ストロング | raise | 62% | 88 |
| 3BP | turn | MTT100 | connected_mid | ストロング | raise | 61% | 88 |
| SRP | river | Cash100 | Khigh_spread | ツーペア | call | 61% | 125 |
| DEF | river | Cash100 | mid_dry | ミドルペア | fold | 61% | 48 |
| 3BP | flop | Cash100 | Khigh_spread | エア | call | 61% | 720 |
| DEF | flop | Cash100 | connected_mid | ミドルペア | fold | 61% | 1,272 |
| SRP | river | MTT200 | connected_mid | ツーペア | fold | 61% | 180 |
| 3BP | river | MTT100 | paired_high | ミドルペア | call | 60% | 399 |
| DEF | flop | Cash100 | connected_low | ストロング | raise | 60% | 68 |
| 4BP | flop | MTT100 | paired_high | ストロング | call | 60% | 88 |
| 4BP | turn | Cash100 | paired_high | エア | fold | 60% | 720 |
| 4BP | turn | Cash100 | Khigh_spread | ミドルペア | call | 60% | 372 |
| SRP | turn | MTT200 | connected_mid | ミドルペア | fold | 60% | 708 |

## 🟠 MIXED 境界 (拮抗、状況依存)

dominant 40-60%。2 アクションが拮抗。書籍では「状況による」と書く部分。

| pot | street | depth | sub-family | カテゴリ | fold | call | raise | n |
|---|---|---|---|---|---:|---:|---:|---:|
| 3BP | flop | MTT100 | Khigh_spread | ツーペア | 0% | 56% | 44% | 27 |
| 3BP | flop | Cash100 | Khigh_spread | ツーペア | 0% | 45% | 55% | 27 |
| 3BP | flop | MTT100 | Khigh_spread | トップペア以上 | 0% | 55% | 45% | 126 |
| 3BP | flop | Cash100 | Khigh_spread | トップペア以上 | 0% | 59% | 41% | 126 |
| 3BP | flop | MTT100 | connected_mid | ストロング | 0% | 55% | 45% | 82 |
| 3BP | flop | Cash100 | connected_mid | ストロング | 0% | 55% | 45% | 82 |
| 3BP | flop | MTT100 | mid_dry | トップペア以上 | 0% | 43% | 57% | 156 |
| 3BP | flop | Cash100 | mid_dry | トップペア以上 | 0% | 47% | 53% | 156 |
| 3BP | flop | MTT100 | monotone | エア | 33% | 56% | 11% | 675 |
| 3BP | flop | Cash100 | monotone | エア | 34% | 55% | 11% | 675 |
| 3BP | flop | MTT100 | monotone | ツーペア | 0% | 44% | 56% | 27 |
| 3BP | flop | Cash100 | monotone | ツーペア | 0% | 49% | 51% | 27 |
| 3BP | flop | MTT100 | paired_high | ストロング | 0% | 54% | 46% | 88 |
| 3BP | flop | Cash100 | paired_high | ミドルペア | 1% | 40% | 59% | 192 |
| 3BP | river | Cash100 | low_dry | ミドルペア | 49% | 51% | 0% | 396 |
| 3BP | river | Cash100 | monotone | トップペア以上 | 52% | 48% | 0% | 1,141 |
| 3BP | river | Cash100 | paired_broadway | ナッツメイド | 49% | 51% | 0% | 361 |
| 3BP | turn | Cash100 | Khigh_spread | ミドルペア | 41% | 59% | 1% | 372 |
| 3BP | turn | Cash100 | connected_mid | トップペア以上 | 4% | 60% | 36% | 264 |
| 3BP | turn | MTT100 | connected_mid | トップペア以上 | 0% | 55% | 45% | 264 |
| 3BP | turn | Cash100 | mid_dry | ミドルペア | 54% | 41% | 6% | 144 |
| 3BP | turn | MTT100 | mid_dry | ミドルペア | 48% | 49% | 3% | 144 |
| 3BP | turn | Cash100 | monotone | ミドルペア | 55% | 42% | 2% | 162 |
| 3BP | turn | MTT100 | monotone | ミドルペア | 51% | 47% | 2% | 162 |
| 3BP | turn | Cash100 | paired_high | エア | 58% | 27% | 15% | 720 |
| 4BP | flop | Cash100 | Ahigh_spread | エア | 31% | 40% | 28% | 720 |
| 4BP | flop | Cash100 | Ahigh_spread | ミドルペア | 0% | 56% | 44% | 300 |
| 4BP | flop | Cash100 | Khigh_spread | エア | 34% | 40% | 26% | 1,440 |
| 4BP | flop | MTT100 | Khigh_spread | エア | 31% | 43% | 27% | 720 |
| 4BP | flop | Cash100 | Khigh_spread | ミドルペア | 0% | 49% | 51% | 588 |
| 4BP | flop | MTT100 | Khigh_spread | ミドルペア | 0% | 47% | 53% | 294 |
| 4BP | flop | Cash100 | broadway_dry | エア | 31% | 47% | 23% | 1,440 |
| 4BP | flop | Cash100 | broadway_dry | ツーペア | 0% | 54% | 46% | 54 |
| 4BP | flop | Cash100 | connected_low | エア | 23% | 53% | 23% | 1,376 |
| 4BP | flop | Cash100 | connected_mid | エア | 31% | 55% | 14% | 3,440 |
| 4BP | flop | MTT100 | connected_mid | エア | 29% | 58% | 13% | 1,376 |
| 4BP | flop | Cash100 | connected_mid | ツーペア | 0% | 48% | 52% | 135 |
| 4BP | flop | MTT100 | connected_mid | ツーペア | 0% | 54% | 46% | 54 |
| 4BP | flop | Cash100 | low_dry | ミドルペア | 0% | 49% | 51% | 258 |
| 4BP | flop | Cash100 | mid_dry | ミドルペア | 0% | 51% | 49% | 798 |
| 4BP | flop | MTT100 | mid_dry | ミドルペア | 0% | 43% | 57% | 264 |
| 4BP | flop | Cash100 | monotone | エア | 32% | 49% | 19% | 2,700 |
| 4BP | flop | MTT100 | monotone | エア | 30% | 50% | 20% | 675 |
| 4BP | flop | Cash100 | paired_broadway | エア | 29% | 46% | 26% | 880 |
| 4BP | flop | Cash100 | paired_broadway | トップペア以上 | 0% | 58% | 42% | 150 |
| 4BP | flop | Cash100 | paired_broadway | ミドルペア | 0% | 45% | 55% | 48 |
| 4BP | flop | Cash100 | paired_high | ストロング | 0% | 57% | 43% | 176 |
| 4BP | flop | Cash100 | paired_mid | トップペア以上 | 0% | 57% | 43% | 30 |
| 4BP | river | Cash100 | connected_mid | ミドルペア | 44% | 56% | 0% | 2,072 |
| 4BP | river | MTT100 | connected_mid | ミドルペア | 53% | 47% | 0% | 612 |
| 4BP | turn | MTT100 | Khigh_spread | トップペア以上 | 0% | 48% | 52% | 114 |
| 4BP | turn | MTT100 | Khigh_spread | ミドルペア | 0% | 53% | 47% | 372 |
| 4BP | turn | Cash100 | mid_dry | エア | 58% | 33% | 9% | 720 |
| 4BP | turn | MTT100 | mid_dry | エア | 57% | 35% | 8% | 720 |
| 4BP | turn | Cash100 | monotone | ストロング | 0% | 49% | 51% | 125 |
| 4BP | turn | MTT100 | monotone | ストロング | 0% | 51% | 49% | 125 |
| 4BP | turn | MTT100 | paired_high | エア | 59% | 34% | 7% | 720 |
| DEF | flop | Cash100 | Ahigh_spread | ミドルペア | 43% | 57% | 0% | 282 |
| DEF | flop | Cash100 | Khigh_spread | エア | 40% | 45% | 15% | 1,344 |
| DEF | flop | Cash100 | Khigh_spread | ストロング | 0% | 48% | 52% | 36 |
| DEF | flop | Cash100 | Khigh_spread | ツーペア | 0% | 48% | 52% | 16 |
| DEF | flop | Cash100 | broadway_dry | ミドルペア | 32% | 59% | 9% | 450 |
| DEF | flop | Cash100 | connected_low | ミドルペア | 47% | 37% | 16% | 324 |
| DEF | flop | Cash100 | low_dry | ミドルペア | 20% | 25% | 55% | 108 |
| DEF | flop | Cash100 | mid_dry | トップペア以上 | 0% | 59% | 41% | 630 |
| DEF | flop | Cash100 | mid_dry | ミドルペア | 16% | 50% | 34% | 426 |
| DEF | flop | Cash100 | paired_high | エア | 59% | 36% | 6% | 1,520 |
| DEF | flop | Cash100 | paired_mid | エア | 53% | 40% | 6% | 784 |
| DEF | river | Cash100 | Khigh_spread | エア | 55% | 36% | 9% | 252 |
| DEF | river | Cash100 | connected_mid | ストロング | 0% | 55% | 45% | 340 |
| DEF | river | Cash100 | connected_mid | ミドルペア | 40% | 49% | 11% | 228 |
| DEF | river | Cash100 | monotone | エア | 55% | 37% | 8% | 219 |
| DEF | river | Cash100 | paired_high | エア | 52% | 39% | 9% | 292 |
| DEF | turn | Cash100 | Khigh_spread | ミドルペア | 29% | 51% | 19% | 180 |
| DEF | turn | Cash100 | connected_mid | トップペア以上 | 35% | 53% | 12% | 348 |
| DEF | turn | Cash100 | mid_dry | ミドルペア | 55% | 44% | 1% | 108 |
| SRP | flop | Cash100 | Ahigh_spread | ナッツメイド | 54% | 46% | 0% | 160 |
| SRP | flop | Cash100 | Khigh_spread | ストロング | 46% | 47% | 7% | 75 |
| SRP | flop | Cash100 | Khigh_spread | ツーペア | 14% | 57% | 29% | 29 |
| SRP | flop | Cash100 | Khigh_spread | トップペア以上 | 55% | 32% | 12% | 260 |
| SRP | flop | Cash100 | connected_mid | ストロング | 58% | 36% | 6% | 1,658 |
| SRP | flop | Cash100 | monotone | ストロング | 55% | 40% | 4% | 1,279 |
| SRP | flop | Cash100 | paired_high | ストロング | 44% | 32% | 24% | 190 |
| SRP | river | Cash100 | Khigh_spread | ストロング | 0% | 45% | 55% | 60 |
| SRP | river | Cash100 | Khigh_spread | トップペア以上 | 55% | 44% | 1% | 312 |
| SRP | river | MTT200 | Khigh_spread | ミドルペア | 45% | 44% | 11% | 426 |
| SRP | river | MTT25 | Khigh_spread | ミドルペア | 48% | 52% | 0% | 339 |
| SRP | river | MTT200 | connected_mid | ストロング | 2% | 49% | 49% | 710 |
| SRP | river | Cash100 | connected_mid | ツーペア | 51% | 49% | 0% | 350 |
| SRP | river | MTT200 | connected_mid | トップペア以上 | 57% | 43% | 0% | 180 |
| SRP | river | MTT25 | connected_mid | トップペア以上 | 41% | 59% | 0% | 102 |
| SRP | river | MTT200 | mid_dry | ナッツメイド | 0% | 51% | 49% | 181 |
| SRP | river | Cash100 | mid_dry | ミドルペア | 60% | 40% | 0% | 309 |
| SRP | river | MTT100 | mid_dry | ミドルペア | 51% | 49% | 0% | 138 |
| SRP | river | MTT25 | mid_dry | ミドルペア | 50% | 50% | 0% | 120 |
| SRP | river | MTT200 | monotone | トップペア以上 | 51% | 43% | 6% | 144 |
| SRP | river | Cash100 | monotone | トップペア以上 | 53% | 43% | 4% | 376 |
| SRP | river | MTT100 | monotone | トップペア以上 | 38% | 55% | 7% | 144 |
| SRP | river | Cash100 | paired_high | ミドルペア | 32% | 42% | 26% | 684 |
| SRP | turn | MTT200 | connected_mid | ストロング | 0% | 44% | 56% | 88 |
| SRP | turn | MTT200 | mid_dry | ストロング | 0% | 58% | 42% | 80 |
| SRP | turn | Cash100 | mid_dry | ミドルペア | 39% | 60% | 1% | 249 |
| SRP | turn | MTT200 | monotone | ミドルペア | 59% | 40% | 0% | 162 |
| SRP | turn | Cash100 | monotone | ミドルペア | 57% | 41% | 2% | 324 |
| SRP | turn | MTT200 | paired_high | エア | 55% | 31% | 14% | 720 |
| SRP | turn | MTT200 | paired_high | ストロング | 0% | 50% | 50% | 80 |
| SRP | turn | MTT200 | paired_high | ナッツメイド | 0% | 54% | 46% | 19 |
| SRP | turn | Cash100 | paired_high | ナッツメイド | 0% | 42% | 58% | 24 |

## 🔴 BALANCED (完全に状況依存、追加調査必要)

どの action も <40%。カテゴリ より細かい分類 (kicker, draw, equity etc) で
細分化しないと判断できない。MATCHA で 5 軸目以上の補正候補。

| pot | street | depth | sub-family | カテゴリ | fold | call | raise | n |
|---|---|---|---|---|---:|---:|---:|---:|

## ⚪ data 欠落 cell

今フィルタで観測されない (pot, street, depth, sub, カテゴリ) の組合せ。
新規 probe の対象候補。

観測 cell: 619 / 期待 cell: 3168 → 欠落: 2549
