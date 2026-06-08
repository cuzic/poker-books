# 暗算用 簡易スコア — 係数なしの「足し算 only」公式

ユーザー提案による値の pre-multiplication で、係数を消した暗算用 MATCHA 公式。
数学的には旧式と等価。

## 旧式 (係数あり)

```
Score = 1 × tier + 3 × eq + (-1) × bs + 2 × pot
```

## 新式 (係数なし、暗算楽)

```
Score = tier + eq + bs + pot  ← 足すだけ

tier:  ナッツ=5, ストロング=4, ツーペア=3, TP+=2, MP=1, エア=0
eq:    best=9, good=6, weak=3, trash=0       ← 旧 0/1/2/3 を 3 倍
bs:    small=0, 75%=-1, 100%=-2, over=-3,    ← 符号反転
       over185=-4, allin=-5
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
Score = tier + eq + bs + pot

tier:  ナッツ=5, ストロング=4, ツーペア=3, TP+=2, MP=1, エア=0
eq:    best=9, good=6, weak=3, trash=0
bs:    small=0, 75%=-1, 100%=-2, over=-3, over185=-4, allin=-5
pot:   SRP=0, DEF=2, 3BP=2, 4BP=4

if Score >= 16: raise
elif Score >= 3: call
else: fold
```

## 暗算の例題

### 例 1: SRP flop で TP+ + good eq + 相手 33% bet
- tier=2 (TP+) + eq=6 (good) + bs=0 (small) + pot=0 (SRP)
- Score = **8** → call

### 例 2: 4BP flop で TP+ + good eq + 相手 overbet
- tier=2 + eq=6 + bs=-3 (overbet) + pot=4 (4BP)
- Score = **9** → call

### 例 3: SRP river で ナッツ + best eq + 相手 100% bet
- tier=5 + eq=9 + bs=-2 + pot=0
- Score = **12** → call

## 比較

| 式 | 操作 | 例: SRP TP+ good 33% |
|---|---|---|
| 旧式 | 1×2 + 3×2 + (-1)×0 + 2×0 = 8 | 4 個の乗算 + 4 個の加算 |
| **新式** | 2 + 6 + 0 + 0 = 8 | **0 乗算、3 加算** |

→ 暗算負荷 ~70% 削減。Chen Formula 同様「数値を覚えて足すだけ」