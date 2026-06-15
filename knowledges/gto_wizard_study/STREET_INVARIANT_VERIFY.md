# 6-param 公式は "street 不問" で機能する — 検証

MATCHA 公式 `Score = 1×カテゴリ + 3×eq + (-1)×bs + 2×pot` を
street ごとに評価し、「同じ式・同じ閾値で flop/turn/river を判定可能」
という主張を data で検証。

## 全体精度 (再掲)

- Accuracy: **71.02%**
- Avg loss: **0.3413 BB/spot**
- Huge loss (>5BB): 1.22%

## street 別の精度 (同じ式・同じ閾値)

| street | n | accuracy | avg loss | huge% |
|---|---:|---:|---:|---:|
| flop | 82,595 | 67.99% | 0.2724 BB | 0.64% |
| turn | 50,468 | 74.57% | 0.3893 BB | 1.66% |
| river | 21,153 | 74.37% | 0.4959 BB | 2.44% |

## (pot, street) breakdown

| pot | street | n | accuracy | avg loss |
|---|---|---:|---:|---:|
| SRP | flop | 8,237 | 80.13% | 0.1365 BB |
| SRP | turn | 17,210 | 79.47% | 0.1541 BB |
| SRP | river | 18,213 | 76.53% | 0.5326 BB |
| DEF | flop | 24,966 | 64.86% | 0.1606 BB |
| DEF | turn | 6,186 | 73.36% | 0.3513 BB |
| DEF | river | 2,940 | 61.02% | 0.2683 BB |
| 3BP | flop | 14,112 | 74.26% | 0.2081 BB |
| 3BP | turn | 13,536 | 78.11% | 0.3569 BB |
| 4BP | flop | 35,280 | 64.86% | 0.4090 BB |
| 4BP | turn | 13,536 | 65.34% | 0.7379 BB |

## (role, street) breakdown

| role | street | n | accuracy | avg loss |
|---|---|---:|---:|---:|
| attacker | flop | 57,629 | 69.35% | 0.3208 BB |
| attacker | turn | 44,282 | 74.74% | 0.3946 BB |
| attacker | river | 18,213 | 76.53% | 0.5326 BB |
| defender | flop | 24,966 | 64.86% | 0.1606 BB |
| defender | turn | 6,186 | 73.36% | 0.3513 BB |
| defender | river | 2,940 | 61.02% | 0.2683 BB |

## 解釈

- 同じ公式・同じ閾値で flop/turn/river すべて使用可能
- street ごとの **avg loss は 0.2-0.5 BB の範囲** で大差なし
- 理由: street 効果が他軸 (bs / pot / eq) に既に織り込まれている
  - turn の pot サイズ → bs / pot に反映
  - river の SPR 浅さ → bs (allin 多) に反映
  - street ごとの range 変化 → eq に反映
- **Chen Formula 系譜の "普遍スコア"** が postflop で実現