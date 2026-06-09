# Huge Loss 分析 — MATCHA Score Final (18 cells)

## 集計

- 全 spots: 154,216
- huge loss (>5 BB): **2,732 (1.77%)**
- 全体 avg loss: **0.4165 BB**
- huge spots の avg: **9.34 BB**

## Pred → Best confusion (huge loss spots)

| 公式 pred | GTO best | n | % | 解釈 |
|---|---|---:|---:|------|
| call | fold | 1044 | 38.2% | 公式 call だが fold が正解 (痛い bluff catch) |
| call | raise | 844 | 30.9% | 公式 call だが raise が正解 (機会損失) |
| fold | call | 726 | 26.6% | 公式 fold だが call が正解 (MDF 不足) |
| fold | raise | 96 | 3.5% | 公式 fold だが raise が正解 (大 blunder) |
| raise | call | 22 | 0.8% | 公式 raise だが call が正解 (過剰 aggression) |

## Top 25 huge loss patterns

| tier | board | pot | pred | best | n | avg_loss |
|------|------|-----|------|------|--:|---:|
| エア | wet | 4BP | fold | call | 341 | 6.84 BB |
| ミドルペア | paired | 4BP | call | raise | 329 | 5.83 BB |
| エア | dry | DEF | call | fold | 242 | 9.02 BB |
| ストロング | wet | SRP | call | fold | 216 | 14.73 BB |
| ストロング | wet | SRP | call | raise | 189 | 15.79 BB |
| ミドルペア | wet | DEF | call | fold | 179 | 9.88 BB |
| エア | wet | 3BP | fold | call | 123 | 7.22 BB |
| エア | wet | 4BP | call | fold | 117 | 8.02 BB |
| エア | dry | 4BP | fold | call | 109 | 5.58 BB |
| ナッツメイド | wet | SRP | call | raise | 96 | 15.15 BB |
| エア | wet | DEF | call | fold | 87 | 7.03 BB |
| ナッツメイド | paired | SRP | call | raise | 72 | 11.32 BB |
| ミドルペア | dry | DEF | call | fold | 69 | 7.00 BB |
| ナッツメイド | paired | SRP | call | fold | 58 | 8.32 BB |
| ストロング | dry | SRP | call | raise | 44 | 12.67 BB |
| ツーペア | dry | SRP | fold | call | 41 | 23.61 BB |
| ミドルペア | dry | SRP | fold | call | 36 | 7.33 BB |
| ツーペア | wet | SRP | fold | call | 34 | 8.20 BB |
| エア | dry | 3BP | fold | call | 32 | 6.02 BB |
| ツーペア | dry | SRP | call | raise | 32 | 8.13 BB |
| トップペア以上 | wet | DEF | call | fold | 31 | 5.62 BB |
| ミドルペア | wet | 4BP | call | fold | 27 | 6.50 BB |
| トップペア以上 | dry | 4BP | call | raise | 26 | 5.21 BB |
| トップペア以上 | wet | SRP | fold | raise | 21 | 7.46 BB |
| エア | wet | 4BP | fold | raise | 20 | 9.58 BB |

## Huge loss by pot type

| pot | huge / total | huge% |
|-----|--:|---:|
| SRP | 906 / 43,660 | 2.08% |
| DEF | 653 / 34,092 | 1.92% |
| 3BP | 190 / 27,648 | 0.69% |
| 4BP | 983 / 48,816 | 2.01% |

## tier × bs (huge spots)

| tier | bs | n |
|------|-----|--:|
| エア | overbet | 540 |
| エア | med_75p | 329 |
| ミドルペア | overbet_185 | 293 |
| ミドルペア | med_75p | 259 |
| エア | overbet_185 | 234 |
| ストロング | allin | 233 |
| ナッツメイド | med_100p | 169 |
| ストロング | med_100p | 105 |
| ツーペア | overbet_185 | 90 |
| ストロング | overbet | 72 |
| ミドルペア | overbet | 69 |
| ナッツメイド | allin | 68 |
| トップペア以上 | overbet_185 | 44 |
| ミドルペア | allin | 42 |
| ストロング | med_75p | 38 |

## 旧公式との比較

| 公式 | huge% | avg loss | huge avg |
|------|---:|---:|---:|
| v1 (24 cells, eq accuracy 最適化) | 2.28% | 0.48 BB | ~11 BB |
| **MATCHA Score Final (18 cells)** | **1.77%** | **0.4165 BB** | **9.34 BB** |

## 主要な「公式の例外」候補 (n ≥ 50)

- **エア × wet × 4BP**: 公式 `fold` → GTO `call` (341 cases, avg 6.84 BB)
- **ミドルペア × paired × 4BP**: 公式 `call` → GTO `raise` (329 cases, avg 5.83 BB)
- **エア × dry × DEF**: 公式 `call` → GTO `fold` (242 cases, avg 9.02 BB)
- **ストロング × wet × SRP**: 公式 `call` → GTO `fold` (216 cases, avg 14.73 BB)
- **ストロング × wet × SRP**: 公式 `call` → GTO `raise` (189 cases, avg 15.79 BB)
- **ミドルペア × wet × DEF**: 公式 `call` → GTO `fold` (179 cases, avg 9.88 BB)
- **エア × wet × 3BP**: 公式 `fold` → GTO `call` (123 cases, avg 7.22 BB)
- **エア × wet × 4BP**: 公式 `call` → GTO `fold` (117 cases, avg 8.02 BB)
- **エア × dry × 4BP**: 公式 `fold` → GTO `call` (109 cases, avg 5.58 BB)
- **ナッツメイド × wet × SRP**: 公式 `call` → GTO `raise` (96 cases, avg 15.15 BB)
- **エア × wet × DEF**: 公式 `call` → GTO `fold` (87 cases, avg 7.03 BB)
- **ナッツメイド × paired × SRP**: 公式 `call` → GTO `raise` (72 cases, avg 11.32 BB)
- **ミドルペア × dry × DEF**: 公式 `call` → GTO `fold` (69 cases, avg 7.00 BB)
- **ナッツメイド × paired × SRP**: 公式 `call` → GTO `fold` (58 cases, avg 8.32 BB)
