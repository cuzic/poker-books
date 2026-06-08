# 暗算用 簡易スコア — 係数なしの「足し算 only」公式

ユーザー提案による値の pre-multiplication で、係数を消した暗算用 MATCHA 公式。
数学的には旧式と等価。

## 旧式 (係数あり)

```
Score = 1 × tier + 3 × eq + (-1) × bs + 2 × pot
```

## 新式 (係数なし、bs は引き算)

```
Score = tier + eq - bs + pot

tier:  ナッツ=5, ストロング=4, ツーペア=3, TP+=2, MP=1, エア=0
eq:    best=9, good=6, weak=3, trash=0       ← 旧 0/1/2/3 を 3 倍
bs:    small=0, 75%=1, 100%=2, over=3,        ← 引き算
       over185=4, allin=5
pot:   SRP=0, DEF=2, 3BP=2, 4BP=4             ← 旧 0/1/1/2 を 2 倍
```

## 評価結果 (旧式の閾値を維持)

| 閾値 | accuracy | avg loss | huge% |
|------|---:|---:|---:|
| T_call=3, T_raise=16 (旧式と同等) | 71.02% | 0.3413 BB | 1.22% |

## 新値での閾値最適化

| 基準 | T_call | T_raise | accuracy | avg loss | huge% |
|------|---:|---:|---:|---:|---:|
| バランス | 3 | 16 | 71.02% | 0.3413 BB | 1.22% |
| acc max  | 3 | 16 | 71.02% | 0.3413 BB | 1.22% |
| loss min | 3 | 9 | 69.12% | 0.3191 BB | 1.15% |

## 推奨公式 (バランス)

```
Score = tier + eq - bs + pot

tier:  ナッツ=5, ストロング=4, ツーペア=3, TP+=2, MP=1, エア=0
eq:    best=9, good=6, weak=3, trash=0
bs:    small=0, 75%=1, 100%=2, over=3, over185=4, allin=5  (引く)
pot:   SRP=0, DEF=2, 3BP=2, 4BP=4

if Score >= 16: raise
elif Score >= 3: call
else: fold
```

## 暗算の例題

### 例 1: SRP flop / TP+ / good eq / 相手 33% bet
Score = 2 + 6 - 0 + 0 = **8** → call

### 例 2: 4BP flop / TP+ / good eq / 相手 overbet
Score = 2 + 6 - 3 + 4 = **9** → call

### 例 3: SRP river / ナッツ / best eq / 相手 100% bet
Score = 5 + 9 - 2 + 0 = **12** → call (>=16 で raise)

### 例 4: 4BP / ナッツ / best / 100% bet
Score = 5 + 9 - 2 + 4 = **16** → raise

### 例 5: SRP / エア / trash / 相手 overbet 185%
Score = 0 + 0 - 4 + 0 = **-4** → fold

## 比較

| 式 | 操作 | 例: SRP TP+ good 33% |
|---|---|---|
| 旧式 | 1×2 + 3×2 + (-1)×0 + 2×0 = 8 | 4 個の乗算 + 4 個の加算 |
| **新式** | 2 + 6 - 0 + 0 = 8 | **0 乗算、3 加減算** |

→ 暗算負荷 ~70% 削減。Chen Formula 同様「数値を覚えて足すだけ」