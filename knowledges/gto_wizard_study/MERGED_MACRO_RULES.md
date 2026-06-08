# CORE 113 → 真のマクロルール抽出

「同じ action になる cells を wildcard マージ」で本質的ルール数を測定。
113 という数は「組合せ爆発による分割」が主因。本質的なルールは少ない。

## 圧縮プロセス

### Step 1: bet_size を wildcard 化 ("any bs")

- 元 CORE (5-key, n≥200, freq≥0.85): 101 rules
- bs を drop して unique (pot, st, sub, tier, eq) になる: 91 個
- うち bs 違いでも同 action: **9 個**

### Step 2: sub_family も wildcard 化 ("any sub")

- sub + bs 両方 drop して unique (pot, st, tier, eq): 41 個
- うち sub 違いでも同 action: **41 個** (= 本質マクロルール)

## 真のマクロルール (sub, bs ともに wildcard)

**41 ルール**で、これら CORE 5-key 113 ルールの大半をカバー。

| pot | street | tier | eq_bucket | action | 累計 n | sub 種数 |
|---|---|---|---|---|---:|---:|
| SRP | river | エア | trash_hands | **fold** | 6,963 | 5 |
| 4BP | flop | エア | weak_hands | **call** | 6,286 | 5 |
| SRP | turn | エア | trash_hands | **fold** | 5,229 | 4 |
| DEF | flop | エア | trash_hands | **fold** | 4,758 | 7 |
| 3BP | turn | エア | trash_hands | **fold** | 3,374 | 4 |
| 4BP | turn | エア | trash_hands | **fold** | 2,928 | 3 |
| DEF | turn | エア | trash_hands | **fold** | 2,336 | 5 |
| SRP | flop | エア | trash_hands | **fold** | 1,826 | 3 |
| 3BP | flop | ミドルペア | good_hands | **call** | 1,772 | 3 |
| SRP | river | ミドルペア | trash_hands | **fold** | 1,700 | 2 |
| 4BP | flop | トップペア以上 | good_hands | **raise** | 1,534 | 3 |
| 3BP | turn | エア | weak_hands | **fold** | 1,322 | 2 |
| SRP | turn | エア | weak_hands | **fold** | 1,114 | 3 |
| 4BP | turn | ミドルペア | weak_hands | **call** | 1,040 | 1 |
| 3BP | flop | エア | trash_hands | **fold** | 1,024 | 2 |
| 4BP | flop | ミドルペア | weak_hands | **call** | 987 | 2 |
| DEF | flop | トップペア以上 | good_hands | **call** | 934 | 3 |
| 4BP | turn | ミドルペア | good_hands | **raise** | 845 | 3 |
| DEF | flop | ミドルペア | good_hands | **call** | 731 | 3 |
| SRP | flop | ミドルペア | trash_hands | **fold** | 626 | 1 |
| 3BP | flop | エア | weak_hands | **call** | 619 | 2 |
| SRP | turn | トップペア以上 | good_hands | **call** | 609 | 2 |
| 4BP | flop | ストロング | best_hands | **call** | 557 | 2 |
| SRP | turn | ミドルペア | weak_hands | **fold** | 514 | 2 |
| 4BP | flop | ミドルペア | good_hands | **raise** | 504 | 1 |
| DEF | flop | ストロング | best_hands | **call** | 494 | 2 |
| 4BP | flop | エア | good_hands | **call** | 463 | 1 |
| 4BP | turn | トップペア以上 | good_hands | **raise** | 434 | 1 |
| 4BP | flop | トップペア以上 | best_hands | **raise** | 378 | 1 |
| DEF | flop | エア | good_hands | **call** | 354 | 1 |
| SRP | river | ストロング | weak_hands | **call** | 329 | 1 |
| SRP | turn | ミドルペア | good_hands | **call** | 287 | 1 |
| SRP | flop | トップペア以上 | trash_hands | **fold** | 264 | 1 |
| SRP | river | ストロング | good_hands | **call** | 257 | 1 |
| DEF | river | エア | trash_hands | **fold** | 247 | 1 |
| DEF | flop | トップペア以上 | weak_hands | **call** | 246 | 1 |
| 3BP | turn | トップペア以上 | good_hands | **call** | 216 | 1 |
| SRP | flop | ツーペア | trash_hands | **fold** | 215 | 1 |
| SRP | turn | トップペア以上 | weak_hands | **call** | 204 | 1 |
| SRP | flop | ナッツメイド | trash_hands | **fold** | 204 | 1 |
| SRP | flop | ミドルペア | good_hands | **call** | 203 | 1 |

## 評価結果 (macro + specific 階層)

| variant | rules | accuracy | avg loss | huge% |
|---|---:|---:|---:|---:|
| **マクロ+specific (本)** | 46 | **71.76%** | **0.4088 BB** | **1.90%** |
|  └ MACRO (sub/bs不問) | 41 | | | |
|  └ SPECIFIC (例外) | 1 | | | |
|  └ DEFAULT | 4 | | | |
| 3-tier (前) | 652 | 75.62% | 0.32 BB | 1.47% |

## source 別

| source | n | rows% | accuracy | avg loss |
|---|---:|---:|---:|---:|
| SPECIFIC | 301 | 0.2% | 86.05% | 0.0573 BB |
| MACRO | 103,566 | 67.2% | 79.03% | 0.1665 BB |
| DEFAULT | 50,349 | 32.6% | 56.74% | 0.9093 BB |

## 結論

- 113 CORE → 41 真のマクロルール + 1 例外
- マクロ 41 ルールだけで rows の 67% を 79% accuracy
- 「bet_size や sub_family は変わっても action は変わらない」spot が大半
- ユーザーの直感通り、CORE 113 は組合せ爆発で分割されていた

**書籍に書く真の暗記対象 = 41 マクロルール**