# 数式スコアリング — 6 パラメータの公式

MATCHA 5 軸を線形結合 → 閾値判定で fold/call/raise。
Chen Formula 規模の暗算可能性を達成。

## スコア計算

```
Score = w_tier × カテゴリ + w_eq × eq + w_bs × bs + w_pot × pot

カテゴリ:  ナッツ=5, ストロング=4, ツーペア=3, TP+=2, MP=1, エア=0
eq:    best=3, good=2, weak=1, trash=0
bs:    small_33=0, med_75p=1, med_100p=2, overbet=3, overbet_185=4, allin=5
pot:   SRP=0, DEF=1, 3BP=1, 4BP=2

if Score >= T_raise: raise
elif Score >= T_call: call
else: fold
```

## grid search 結果

| 基準 | w_tier | w_eq | w_bs | w_pot | T_call | T_raise | accuracy | avg loss | huge% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **最高 accuracy** | 1 | 3 | -1 | 2 | 3 | 16 | 71.02% | 0.3413 BB | 1.22% |
| **最小 avg loss** | 1 | 4 | 0 | 2 | 8 | 13 | 70.28% | 0.2999 BB | 0.90% |
| **バランス (acc-10×loss)** | 1 | 3 | -1 | 2 | 3 | 16 | 71.02% | 0.3413 BB | 1.22% |

## 比較表

| variant | パラメータ数 | accuracy | avg loss | huge% |
|---|---:|---:|---:|---:|
| **数式 (バランス)** | **6** | **71.02%** | **0.3413 BB** | **1.22%** |
| 41 マクロルール | 41 | 71.76% | 0.41 BB | 1.90% |
| CORE 113 + FB 535 | 652 | 75.62% | 0.32 BB | 1.47% |
| 既存公式 v9b/v10/v15 | ~50 | 59.46% | 1.86 BB | 9.65% |

## バランス選定の公式 (推奨)

```
Score = 1 × カテゴリ + 3 × eq + (-1) × bs + (2) × pot

if Score >= 16: raise
elif Score >= 3: call
else: fold
```

## 結論

- **6 パラメータの式 1 本**で accuracy **71.02%**, loss **0.341 BB**
- 既存公式と比べ accuracy +11.6pp、loss -81.7%
- 41 マクロルールと比べ paramters 1/7、accuracy -0.74pp

**MATCHA Framework の真の暗算公式**: Chen Formula と同様、
数値だけ覚えれば spot 判定可能。