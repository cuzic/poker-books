# Huge Loss 分析 — MATCHA Score v2 (street 別 DV)

## 集計

- 全 spots: 154,216
- huge loss (>5 BB): **3,090 (2.00%)**
- 全体 avg loss: **0.4404 BB**
- huge spots の avg: **8.81 BB**

## v1 (DV=3 固定) との比較

| 指標 | v1 (DV=3) | **v2 (street 別)** | 変化 |
|------|---:|---:|---|
| huge% | 1.77% | **2.00%** | — |
| avg loss | 0.4165 BB | **0.4404 BB** | — |
| huge avg | 9.34 BB | **8.81 BB** | — |

## Pred → Best confusion

| 公式 pred | GTO best | n | % |
|---|---|---:|---:|
| fold | call | 1288 | 41.7% |
| call | raise | 848 | 27.4% |
| call | fold | 752 | 24.3% |
| fold | raise | 202 | 6.5% |

## Top 25 huge loss patterns

| カテゴリ | board | street | pot | pred | best | n | avg_loss |
|------|------|------|-----|------|------|--:|---:|
| エア | dry | flop | 4BP | fold | call | 386 | 6.72 BB |
| エア | wet | flop | 4BP | fold | call | 284 | 7.11 BB |
| ミドルペア | paired | turn | 4BP | call | raise | 260 | 5.94 BB |
| ストロング | wet | flop | SRP | call | fold | 216 | 14.73 BB |
| ミドルペア | wet | turn | DEF | call | fold | 179 | 9.88 BB |
| エア | paired | flop | 4BP | fold | call | 178 | 7.59 BB |
| ストロング | wet | river | SRP | call | raise | 164 | 15.70 BB |
| エア | wet | turn | 4BP | call | fold | 117 | 8.02 BB |
| エア | wet | turn | 4BP | fold | call | 116 | 7.44 BB |
| エア | wet | turn | 3BP | fold | call | 103 | 8.26 BB |
| ナッツメイド | wet | river | SRP | call | raise | 94 | 14.83 BB |
| ナッツメイド | paired | river | SRP | call | raise | 72 | 11.32 BB |
| ミドルペア | paired | flop | 4BP | call | raise | 69 | 5.41 BB |
| ミドルペア | dry | turn | DEF | call | fold | 69 | 7.00 BB |
| ナッツメイド | paired | flop | SRP | call | fold | 58 | 8.32 BB |
| エア | dry | flop | 4BP | fold | raise | 53 | 9.66 BB |
| エア | dry | turn | 4BP | fold | call | 48 | 6.36 BB |
| ストロング | dry | river | SRP | call | raise | 44 | 12.67 BB |
| エア | paired | flop | 3BP | fold | call | 39 | 5.76 BB |
| ミドルペア | dry | river | SRP | fold | call | 36 | 7.33 BB |
| エア | wet | flop | 3BP | fold | call | 35 | 5.85 BB |
| ツーペア | wet | turn | SRP | fold | call | 34 | 8.20 BB |
| エア | wet | turn | DEF | call | fold | 33 | 6.37 BB |
| ツーペア | dry | river | SRP | call | raise | 32 | 8.13 BB |
| エア | dry | turn | 4BP | fold | raise | 32 | 9.20 BB |

## street 別 huge loss

| street | huge / total | huge% |
|---|--:|---:|
| flop | 1,383 / 82,595 | 1.67% |
| turn | 1,217 / 50,468 | 2.41% |
| river | 490 / 21,153 | 2.32% |

## pot 別 huge loss

| pot | huge / total | huge% |
|---|--:|---:|
| SRP | 868 / 43,660 | 1.99% |
| DEF | 347 / 34,092 | 1.02% |
| 3BP | 229 / 27,648 | 0.83% |
| 4BP | 1,646 / 48,816 | 3.37% |

## DV > 0 spots での性能

- DV>0 huge: 488/41,798 (1.17%)
- DV>0 avg loss: 0.3360 BB

| street | DV>0 huge / total | huge% | avg loss |
|---|--:|---:|---:|
| flop | 37 / 26,966 | 0.14% | 0.2251 BB |
| turn | 451 / 14,832 | 3.04% | 0.5375 BB |