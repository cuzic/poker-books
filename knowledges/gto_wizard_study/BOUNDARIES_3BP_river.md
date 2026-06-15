# 境界 spec (3BP, river) — data 駆動の境界条件

フィルタ: pot=3BP, street=river, depth=*, sub=*, カテゴリ=*
閾値: PURE ≥80% / STRONG 60-80% / MIXED 40-60% / BALANCED <40%
最小 n: 10

## 集計

| class | 意味 | n cells |
|---|---|---:|
| PURE | 暗記対象、書籍に書ける | 60 |
| STRONG | 基本そうする (たまに別) | 18 |
| MIXED | 拮抗、状況依存 | 3 |
| BALANCED | 完全に状況依存、要追加調査 | 0 |

## 🟢 PURE 境界 (暗記対象)

dominant action 頻度 ≥80% の cell。読者は条件確認 → 即アクション。

| pot | street | depth | sub-family | カテゴリ | action | freq | n |
|---|---|---|---|---|---|---:|---:|
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

## ⚪ data 欠落 cell

今フィルタで観測されない (pot, street, depth, sub, カテゴリ) の組合せ。
新規 probe の対象候補。

観測 cell: 81 / 期待 cell: 132 → 欠落: 51
