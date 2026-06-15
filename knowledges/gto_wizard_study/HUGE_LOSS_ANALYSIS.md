# Huge Loss (>5 BB) 分類 — 公式の苦手 spot

整数公式 (accuracy 66.5% / avg loss 0.48 BB / huge 2.28%)
の huge loss (>5 BB) を発生 spot で分類。

## 集計

- 全 spots: 154,216
- huge loss spots: 3,510 (2.28%)
- huge spots の avg loss: 9.34 BB

## Top 30 huge loss patterns (カテゴリ × board × pot × pred→best)

| カテゴリ | board | pot | pred | best | n | avg_loss |
|------|-------|-----|------|------|--:|---:|
| エア | dry | 4BP | call | fold | 384 | 8.06 BB |
| ミドルペア | paired | 4BP | call | raise | 329 | 5.83 BB |
| エア | connected | 4BP | call | fold | 301 | 7.87 BB |
| エア | dry | DEF | call | fold | 242 | 9.02 BB |
| トップペア以上 | connected | SRP | call | fold | 237 | 14.46 BB |
| ストロング | connected | SRP | call | raise | 179 | 15.73 BB |
| ミドルペア | connected | DEF | call | fold | 179 | 9.88 BB |
| ストロング | connected | SRP | call | fold | 171 | 15.10 BB |
| エア | paired | 3BP | call | fold | 150 | 6.66 BB |
| エア | paired | 4BP | call | fold | 117 | 5.56 BB |
| エア | monotone | 4BP | call | fold | 117 | 8.02 BB |
| エア | dry | 4BP | fold | call | 109 | 5.58 BB |
| ナッツメイド | monotone | SRP | call | raise | 96 | 15.15 BB |
| ミドルペア | dry | SRP | fold | call | 87 | 6.40 BB |
| エア | connected | DEF | call | fold | 87 | 7.03 BB |
| ナッツメイド | paired | SRP | call | raise | 72 | 11.32 BB |
| ミドルペア | dry | DEF | call | fold | 69 | 7.00 BB |
| ナッツメイド | paired | SRP | call | fold | 58 | 8.32 BB |
| エア | connected | 3BP | fold | call | 47 | 6.29 BB |
| ストロング | monotone | SRP | call | fold | 45 | 13.34 BB |
| ストロング | dry | SRP | call | raise | 44 | 12.67 BB |
| ミドルペア | dry | 3BP | fold | call | 42 | 7.83 BB |
| ツーペア | connected | SRP | fold | call | 34 | 8.20 BB |
| ツーペア | dry | SRP | call | raise | 32 | 8.13 BB |
| トップペア以上 | connected | DEF | call | fold | 31 | 5.62 BB |
| トップペア以上 | dry | 4BP | call | raise | 26 | 5.21 BB |
| ミドルペア | connected | 4BP | call | fold | 24 | 6.61 BB |
| トップペア以上 | monotone | SRP | call | fold | 21 | 12.94 BB |
| ツーペア | monotone | SRP | call | fold | 20 | 7.68 BB |
| トップペア以上 | connected | SRP | call | raise | 19 | 23.97 BB |

## Huge loss by pot type

| pot | huge / total | huge% |
|-----|--:|---:|
| SRP | 1,181 / 43,660 | 2.70% |
| DEF | 645 / 34,092 | 1.89% |
| 3BP | 266 / 27,648 | 0.96% |
| 4BP | 1,418 / 48,816 | 2.90% |

## Predicted → Best confusion (huge loss spots のみ)

| 公式予測 | GTO best | n | 解釈 |
|---------|---------|---:|------|
| call | fold | 2268 | 公式 call だが fold が正解 (痛い call) |
| call | raise | 865 | 公式 call だが raise が正解 |
| fold | call | 334 | 公式 fold だが call が正解 |
| fold | raise | 37 | 公式 fold だが raise が正解 (大きな機会損失) |
| raise | call | 6 | 公式 raise だが call が正解 (over-aggression) |

## 主要な苦手パターン (n ≥ 100)

- **エア × dry board × 4BP**: 公式 `call` だが GTO `fold` (384 cases, avg 8.06 BB loss)
- **ミドルペア × paired board × 4BP**: 公式 `call` だが GTO `raise` (329 cases, avg 5.83 BB loss)
- **エア × connected board × 4BP**: 公式 `call` だが GTO `fold` (301 cases, avg 7.87 BB loss)
- **エア × dry board × DEF**: 公式 `call` だが GTO `fold` (242 cases, avg 9.02 BB loss)
- **トップペア以上 × connected board × SRP**: 公式 `call` だが GTO `fold` (237 cases, avg 14.46 BB loss)
- **ストロング × connected board × SRP**: 公式 `call` だが GTO `raise` (179 cases, avg 15.73 BB loss)
- **ミドルペア × connected board × DEF**: 公式 `call` だが GTO `fold` (179 cases, avg 9.88 BB loss)
- **ストロング × connected board × SRP**: 公式 `call` だが GTO `fold` (171 cases, avg 15.10 BB loss)
- **エア × paired board × 3BP**: 公式 `call` だが GTO `fold` (150 cases, avg 6.66 BB loss)
- **エア × paired board × 4BP**: 公式 `call` だが GTO `fold` (117 cases, avg 5.56 BB loss)
- **エア × monotone board × 4BP**: 公式 `call` だが GTO `fold` (117 cases, avg 8.02 BB loss)
- **エア × dry board × 4BP**: 公式 `fold` だが GTO `call` (109 cases, avg 5.58 BB loss)
