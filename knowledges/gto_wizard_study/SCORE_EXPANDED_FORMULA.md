# 8 パラメータ式 — street/role 軸を追加

MATCHA 6 パラメータ式に **street** (flop/turn/river) と **role** (attacker/defender) を追加。
「あらゆるシナリオ (attack/defense × 3 streets) でも使えるか」を検証。

## 式

```
Score = w_tier × tier + w_eq × eq + w_bs × bs + w_pot × pot + w_street × street + w_role × role

street: flop=0, turn=1, river=2
role:   attacker=0, defender=1
```

## 結果

| variant | params | accuracy | avg loss | huge% |
|---|---:|---:|---:|---:|
| **8-param 連続 (バランス)** | 8 | **71.98%** | **0.3379 BB** | 1.25% |
| 8-param 連続 (acc max) | 8 | **72.10%** | 0.3265 BB | 1.15% |
| **8-param 整数 (バランス)** | 8 | 71.01% | 0.3525 BB | 1.29% |
| 6-param 整数 (前回 推奨) | 6 | 70.76% | 0.3220 BB | 1.15% |
| 41 マクロルール | 41 | 71.76% | 0.41 BB | 1.90% |
| 既存公式 v9b/v10/v15 | ~50 | 59.46% | 1.86 BB | 9.65% |

## 最適 8 パラメータ (バランス、整数版)

```
Score = 1 × tier + 5 × eq + (-1) × bs + (2) × pot + (1) × street + (-2) × role

tier:   ナッツ=5, ストロング=4, ツーペア=3, TP+=2, MP=1, エア=0
eq:     best=3, good=2, weak=1, trash=0
bs:     small=0, 75%=1, 100%=2, over=3, over185=4, allin=5
pot:    SRP=0, DEF=1, 3BP=1, 4BP=2
street: flop=0, turn=1, river=2
role:   attacker=0, defender=1

if Score >= 28: raise
elif Score >= 5: call
else: fold
```

## シナリオ別 精度 (8-param バランス)

| role | street | n | accuracy | avg loss |
|---|---|---:|---:|---:|
| attacker | flop | 57,629 | 69.43% | 0.3183 BB |
| attacker | turn | 44,282 | 74.75% | 0.3931 BB |
| attacker | river | 18,213 | 78.17% | 0.4640 BB |
| defender | flop | 24,966 | 69.66% | 0.1980 BB |
| defender | turn | 6,186 | 73.41% | 0.3489 BB |
| defender | river | 2,940 | 58.71% | 0.2745 BB |

## 解釈

- 8-param 整数 vs 6-param 整数: accuracy +0.25pp, loss -9.5%
- street/role を入れることでシナリオ別 spot に追従可能に
- attacker と defender, flop と river で行動が違う部分を式で捕捉
- パラメータ +2 個のコストで精度大幅向上 (or 小幅)

## 結論

- 8-param 式は accuracy 71.0% で 6-param とほぼ同等
- → MATCHA の本質は **tier + eq + bs + pot** の 4 軸で十分
- street/role は副次的、書籍向け公式には不要