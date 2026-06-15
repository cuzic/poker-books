# 暗記可能なマクロルール — PURE 349 cell の圧縮

349 PURE cells を「人間が暗記できる単位」に集約。
Sklansky-Malmuth 系譜の "少数 group で広い coverage" アプローチ。

## マクロルール (Type 1): pot × street × カテゴリ

「3BP turn の エア は **常に fold**」のような sub_family 不問のルール。
coverage ≥ 80% (10 sub-families のうち 8 つ以上が同じ action)

| pot | street | カテゴリ | action | coverage | 適用 cell数 | 例外 |
|---|---|---|---|---:|---:|---|
| 3BP | flop | ストロング | **call** | 80% | 4/5 | paired_high=raise |
| 3BP | flop | トップペア以上 | **call** | 80% | 4/5 | mid_dry=raise |
| 3BP | flop | ミドルペア | **call** | 100% | 5/5 | なし |
| 3BP | turn | ナッツメイド | **call** | 100% | 3/3 | なし |
| 3BP | turn | トップペア以上 | **call** | 100% | 5/5 | なし |
| 3BP | turn | エア | **fold** | 100% | 5/5 | なし |
| 3BP | river | ナッツメイド | **call** | 100% | 9/9 | なし |
| 3BP | river | ストロング | **call** | 100% | 10/10 | なし |
| 3BP | river | ツーペア | **call** | 100% | 8/8 | なし |
| 3BP | river | トップペア以上 | **call** | 90% | 9/10 | monotone=fold |
| 3BP | river | ミドルペア | **fold** | 90% | 9/10 | low_dry=call |
| 3BP | river | エア | **fold** | 100% | 11/11 | なし |
| 4BP | flop | ストロング | **call** | 89% | 8/9 | paired_broadway=raise |
| 4BP | flop | エア | **call** | 100% | 11/11 | なし |
| 4BP | turn | ナッツメイド | **call** | 100% | 3/3 | なし |
| 4BP | turn | ストロング | **call** | 80% | 4/5 | monotone=raise |
| 4BP | turn | エア | **fold** | 100% | 5/5 | なし |
| 4BP | river | ナッツメイド | **call** | 100% | 4/4 | なし |
| 4BP | river | ストロング | **call** | 100% | 4/4 | なし |
| 4BP | river | ツーペア | **call** | 100% | 3/3 | なし |
| 4BP | river | トップペア以上 | **call** | 100% | 5/5 | なし |
| 4BP | river | ミドルペア | **call** | 100% | 5/5 | なし |
| 4BP | river | エア | **fold** | 100% | 5/5 | なし |
| DEF | flop | トップペア以上 | **call** | 91% | 10/11 | low_dry=raise |
| DEF | flop | エア | **fold** | 91% | 10/11 | Khigh_spread=call |
| DEF | turn | ナッツメイド | **call** | 100% | 3/3 | なし |
| DEF | turn | トップペア以上 | **call** | 100% | 5/5 | なし |
| DEF | turn | エア | **fold** | 100% | 5/5 | なし |
| DEF | river | ミドルペア | **call** | 80% | 4/5 | mid_dry=fold |
| DEF | river | エア | **fold** | 100% | 5/5 | なし |
| SRP | flop | トップペア以上 | **fold** | 88% | 7/8 | mid_dry=call |
| SRP | flop | ミドルペア | **fold** | 100% | 8/8 | なし |
| SRP | flop | エア | **fold** | 100% | 8/8 | なし |
| SRP | turn | ストロング | **call** | 80% | 4/5 | connected_mid=raise |
| SRP | turn | トップペア以上 | **call** | 100% | 4/4 | なし |
| SRP | turn | エア | **fold** | 100% | 5/5 | なし |
| SRP | river | ミドルペア | **fold** | 80% | 4/5 | paired_high=call |
| SRP | river | エア | **fold** | 100% | 5/5 | なし |

## マクロルール (Type 2): pot × street × sub_family

「4BP flop の connected_mid は **常に raise**」のような カテゴリ 不問のルール。

| pot | street | sub_family | action | coverage | 適用 cell数 | 例外 |
|---|---|---|---|---:|---:|---|
| 3BP | flop | Khigh_spread | **call** | 100% | 5/5 | なし |
| 3BP | flop | connected_mid | **call** | 80% | 4/5 | エア=fold |
| 3BP | flop | monotone | **call** | 80% | 4/5 | ツーペア=raise |
| 3BP | flop | paired_high | **call** | 80% | 4/5 | ストロング=raise |
| 3BP | turn | Khigh_spread | **call** | 80% | 4/5 | エア=fold |
| 3BP | river | low_dry | **call** | 80% | 4/5 | エア=fold |
| 4BP | flop | broadway_dry | **call** | 80% | 4/5 | トップペア以上=raise |
| 4BP | flop | monotone | **call** | 80% | 4/5 | トップペア以上=raise |
| 4BP | flop | paired_high | **call** | 80% | 4/5 | ミドルペア=raise |
| 4BP | flop | paired_mid | **call** | 80% | 4/5 | ミドルペア=raise |
| 4BP | river | Khigh_spread | **call** | 83% | 5/6 | エア=fold |
| 4BP | river | connected_mid | **call** | 80% | 4/5 | エア=fold |
| 4BP | river | monotone | **call** | 83% | 5/6 | エア=fold |
| 4BP | river | paired_high | **call** | 80% | 4/5 | エア=fold |
| DEF | flop | Ahigh_spread | **call** | 80% | 4/5 | エア=fold |
| DEF | flop | broadway_dry | **call** | 80% | 4/5 | エア=fold |
| DEF | flop | monotone | **call** | 80% | 4/5 | エア=fold |
| DEF | flop | paired_broadway | **call** | 80% | 4/5 | エア=fold |
| DEF | flop | paired_high | **call** | 80% | 4/5 | エア=fold |
| DEF | turn | monotone | **call** | 80% | 4/5 | エア=fold |
| DEF | turn | paired_high | **call** | 80% | 4/5 | エア=fold |
| DEF | river | connected_mid | **call** | 80% | 4/5 | エア=fold |
| SRP | flop | Ahigh_spread | **fold** | 100% | 6/6 | なし |
| SRP | flop | broadway_dry | **fold** | 80% | 4/5 | ストロング=call |
| SRP | flop | connected_mid | **fold** | 83% | 5/6 | ナッツメイド=call |
| SRP | flop | monotone | **fold** | 83% | 5/6 | ナッツメイド=call |
| SRP | flop | paired_high | **fold** | 100% | 5/5 | なし |
| SRP | flop | paired_mid | **fold** | 80% | 4/5 | ナッツメイド=call |
| SRP | turn | Khigh_spread | **call** | 80% | 4/5 | エア=fold |
| SRP | river | connected_mid | **fold** | 80% | 4/5 | ストロング=call |

## メタルール (Type 3): pot × street

「3BP/4BP river は **fold が中心**」のような最大級マクロ。

| pot | street | action | coverage | 適用 cell数 |
|---|---|---|---:|---:|
| SRP | flop | **fold** | 76% | 34/45 |
| 3BP | flop | **call** | 80% | 20/25 |
| 3BP | river | **call** | 64% | 37/58 |
| 4BP | flop | **call** | 66% | 35/53 |
| 4BP | river | **call** | 81% | 21/26 |
| DEF | flop | **call** | 62% | 33/53 |
| DEF | turn | **call** | 64% | 16/25 |

## カバレッジ集計

| 指標 | n |
|------|---:|
| 全 cell | 406 |
| PURE cell | 207 |
| Type 1 でカバーされる cell | 226 |
| Type 2 でカバーされる cell | 128 |
| Type 1 ∪ Type 2 (重複なし) | 281 |
| マクロルール数 | Type1: 38 + Type2: 30 + Type3: 7 = **75** |

## 暗記可能性の評価

- マクロルール **75 個** で 281/406 cells (69%) カバー
- Chen Formula (4 数値 + 6 修正係数) より rule 数多いが、構造化されているため
  pot × street × {カテゴリ or sub} の 3 軸暗記で済む
- 想定暗記時間: 1-2 時間 (Sklansky 8 hand groups と同等)

**結論**: PURE 349 cell の直接暗記は無理だが、マクロルール 75 個に圧縮すれば暗記可能。