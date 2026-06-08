# Optuna 最適スコアリング式 — 6 パラメータ MATCHA 公式

optuna TPE sampler で 500 trials × 3 objective を探索。
実数係数の最適解 + 書籍向け整数版両方を提示。

## 探索結果 (実数係数)

| 基準 | w_tier | w_eq | w_bs | w_pot | T_call | T_raise | accuracy | avg loss | huge% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| バランス (-acc+10loss+5huge) | 1.29 | 3.07 | -1.13 | 2.70 | 3.89 | 10.71 | 70.68% | 0.3091 BB | 1.09% |
| acc max | 1.42 | 3.56 | -1.38 | 2.82 | 3.13 | 24.82 | 71.11% | 0.3418 BB | 1.23% |
| loss min | 0.54 | 2.64 | -0.28 | 2.11 | 4.22 | 8.92 | 70.80% | 0.2773 BB | 0.87% |

## 整数係数版 (書籍向け、暗算可能)

| 基準 | w_tier | w_eq | w_bs | w_pot | T_call | T_raise | accuracy | avg loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| バランス | 1 | 3 | -1 | 3 | 4 | 11 | 70.76% | 0.3220 BB |
| acc max | 1 | 4 | -1 | 3 | 3 | 25 | 65.94% | 0.4305 BB |
| loss min | 1 | 3 | 0 | 2 | 4 | 9 | 57.96% | 0.6323 BB |

## 全比較表

| variant | パラメータ数 | accuracy | avg loss | huge% |
|---|---:|---:|---:|---:|
| **optuna 実数版 (バランス)** | 6 | **57.96%** | **0.6323 BB** | 3.30% |
| grid search 整数版 | 6 | 71.02% | 0.3413 BB | 1.22% |
| 41 マクロルール | 41 | 71.76% | 0.41 BB | 1.90% |
| CORE 113 + FB 535 | 652 | 75.62% | 0.32 BB | 1.47% |
| 既存公式 v9b/v10/v15 | ~50 | 59.46% | 1.86 BB | 9.65% |

## 推奨 MATCHA 公式 (バランス、暗算可能整数版)

```
Score = 1 × tier_value + 3 × eq_value + (-1) × bs_pressure + (3) × pot_pressure

tier_value:    ナッツ=5, ストロング=4, ツーペア=3, TP+=2, MP=1, エア=0
eq_value:      best=3, good=2, weak=1, trash=0
bs_pressure:   small_33=0, med_75p=1, med_100p=2, overbet=3, overbet_185=4, allin=5
pot_pressure:  SRP=0, DEF=1, 3BP=1, 4BP=2

if Score >= 11: raise
elif Score >= 4: call
else: fold
```

→ accuracy 70.76%, avg loss 0.322 BB (per spot)

## 結論

- **6 パラメータの整数公式 1 本**で accuracy 70.8%, loss 0.322 BB
- Chen Formula 系譜の「数値だけで判断」を達成
- 既存公式 (50+ パラメータ) より +11.3pp 精度向上
- 41 マクロルールとほぼ同等の精度 (パラメータ 1/7)