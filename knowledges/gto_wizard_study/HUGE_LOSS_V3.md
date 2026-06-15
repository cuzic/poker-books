# Huge Loss 分析 — MATCHA Score v3 (4-カテゴリ-B + Grid 12)

## 公式

```
Score = Grid[カテゴリ][board] + DV × (flop 3 / turn 2 / river 0)
      + 2 × overcards + 4 × pot − 2 × bs

if Score >= 43: raise
elif Score >= 14: call
else: fold
```

## Grid 12 cells

| カテゴリ | dry | paired | wet |
|------|---:|---:|---:|
| エア | 3 | 5 | 1 |
| ミドルペア | 18 | 40 | 10 |
| TP+ | 38 | 10 | 31 |
| ストロング+ | 25 | 28 | 23 |

## 集計

- 全 spots: 154,216
- huge loss (>5 BB): **2,303 (1.49%)**
- 全体 avg loss: **0.3587 BB**
- huge spots avg: **10.58 BB**

## Pred → Best confusion

| 公式 pred | GTO best | n | % |
|---|---|---:|---:|
| call | fold | 1003 | 43.6% |
| fold | call | 528 | 22.9% |
| call | raise | 501 | 21.8% |
| raise | call | 133 | 5.8% |
| fold | raise | 102 | 4.4% |
| raise | fold | 36 | 1.6% |

## Top 25 huge loss patterns

| カテゴリ | board | street | pot | pred | best | n | avg_loss |
|------|------|------|-----|------|------|--:|---:|
| TP+ | wet | flop | SRP | call | fold | 350 | 14.46 BB |
| ストロング+ | wet | river | SRP | call | raise | 258 | 15.38 BB |
| ミドルペア | wet | turn | DEF | call | fold | 179 | 9.88 BB |
| エア | wet | turn | 3BP | fold | call | 159 | 9.52 BB |
| ストロング+ | wet | flop | SRP | call | fold | 125 | 12.48 BB |
| エア | wet | turn | 4BP | call | fold | 117 | 8.02 BB |
| エア | dry | flop | 4BP | fold | call | 109 | 5.58 BB |
| ストロング+ | dry | river | SRP | call | raise | 88 | 12.05 BB |
| ストロング+ | paired | river | SRP | call | raise | 78 | 11.00 BB |
| TP+ | dry | flop | DEF | raise | call | 75 | 8.39 BB |
| ミドルペア | dry | turn | DEF | call | fold | 69 | 7.00 BB |
| ストロング+ | paired | flop | SRP | call | fold | 58 | 8.32 BB |
| エア | wet | flop | 3BP | fold | call | 47 | 6.29 BB |
| エア | wet | turn | 3BP | fold | raise | 45 | 10.69 BB |
| エア | paired | flop | 3BP | fold | call | 39 | 5.76 BB |
| ミドルペア | dry | river | SRP | fold | call | 36 | 7.33 BB |
| TP+ | dry | river | DEF | raise | call | 36 | 6.77 BB |
| エア | dry | turn | 3BP | fold | call | 33 | 8.21 BB |
| TP+ | wet | turn | DEF | call | fold | 31 | 5.62 BB |
| TP+ | dry | flop | DEF | raise | fold | 27 | 9.95 BB |
| ミドルペア | wet | turn | 4BP | call | fold | 27 | 6.50 BB |
| エア | paired | turn | 3BP | fold | call | 27 | 9.79 BB |
| エア | wet | turn | SRP | fold | call | 24 | 6.35 BB |
| エア | wet | turn | DEF | call | fold | 21 | 5.49 BB |
| TP+ | wet | turn | DEF | raise | call | 18 | 6.80 BB |

## street 別 huge loss

| street | huge / total | huge% |
|---|--:|---:|
| flop | 909 / 82,595 | 1.10% |
| turn | 855 / 50,468 | 1.69% |
| river | 539 / 21,153 | 2.55% |

## pot 別 huge loss

| pot | huge / total | huge% |
|---|--:|---:|
| SRP | 1,146 / 43,660 | 2.62% |
| DEF | 496 / 34,092 | 1.45% |
| 3BP | 400 / 27,648 | 1.45% |
| 4BP | 261 / 48,816 | 0.53% |

## カテゴリ × board 別 huge%

| カテゴリ | dry | paired | wet |
|---|---|---|---|
| エア | 182/30752 (0.6%) | 81/18068 (0.4%) | 421/38579 (1.1%) |
| ミドルペア | 127/10902 (1.2%) | 0/4776 (0.0%) | 224/18699 (1.2%) |
| TP+ | 168/6709 (2.5%) | 9/534 (1.7%) | 427/10104 (4.2%) |
| ストロング+ | 91/2474 (3.7%) | 144/2739 (5.3%) | 429/9880 (4.3%) |