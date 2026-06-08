# eq グリッド表 — 素人向け MATCHA 公式

equity 計算ができない初心者向けに、自分の手 (tier) × board の 24-cell grid で
eq_bucket を lookup する方式。

## 簡易公式

```
Score = eq - bs + pot

eq:   下のグリッド表で lookup
bs:   small=0, 75%=1, 100%=2, over=3, over185=4, allin=5  (引く)
pot:  SRP=0, DEF=2, 3BP=2, 4BP=4

if Score >= 12: raise
elif Score >= 0: call
else: fold
```

## eq グリッド (tier × board → eq_bucket)

| 自分の手役 | dry | paired | connected | monotone |
|-----------|-----|--------|-----------|----------|
| **ナッツメイド** | best=9 | best=9 | best=9 | best=9 |
| **ストロング** | best=9 | best=9 | best=9 | best=9 |
| **ツーペア** | best=9 | ? | trash=0 | good=6 |
| **トップペア以上** | good=6 | good=6 | good=6 | good=6 |
| **ミドルペア** | trash=0 | weak=3 | trash=0 | trash=0 |
| **エア** | trash=0 | trash=0 | trash=0 | trash=0 |

## 性能比較

| 方式 | rules | accuracy | avg loss | huge% | 暗算負荷 |
|------|---:|---:|---:|---:|---|
| **grid 経由 (素人向け)** | グリッド + 3 値 | 58.00% | 0.9291 BB | 4.93% | 低 |
| 直接 eq (中級者) | 3 値のみ | 70.18% | 0.4004 BB | 1.56% | 中 (eq 概算必要) |
| 旧式 (tier + eq) | 4 値 | 71.02% | 0.34 BB | 1.22% | 中 |

## 暗算の例題 (素人用グリッド経由)

### SRP / 自分 KKx2 (overpair) on Ks-7-2 (dry) / 相手 33% bet
- tier=`トップペア以上` × board=`dry` → eq=**good** (6 点)
- Score = 6 - 0 + 0 = **6** → **call**

### SRP / AA on 9-8-7 (connected) / 相手 100% bet
- tier=`トップペア以上` × board=`connected` → eq=**good** (6 点)
- Score = 6 - 2 + 0 = **4** → **call**

### SRP / 22 on K-7-2 (dry, 自分 underpair) / 相手 75% bet
- tier=`ミドルペア` × board=`dry` → eq=**trash** (0 点)
- Score = 0 - 1 + 0 = **-1** → **fold**

### 4BP / AsKs (TP) on As-7-2 / 相手 overbet
- tier=`トップペア以上` × board=`dry` → eq=**good** (6 点)
- Score = 6 - 3 + 4 = **7** → **call**

### SRP / エア on monotone / 相手 100% bet
- tier=`エア` × board=`monotone` → eq=**trash** (0 点)
- Score = 0 - 2 + 0 = **-2** → **fold**

## 利用フロー

```
1. 自分の手を見る → 6 tier のどれか判定 (e.g., overpair / TP+)
2. board を見る → 4 種類のどれか判定 (dry/paired/connected/monotone)
3. グリッド表で eq_bucket lookup
4. 相手の bet サイズ → bs 値 (0-5)
5. pot 種別 (SRP/3BP/4BP) → pot 値 (0/2/4)
6. Score = eq - bs + pot を計算
7. >= 16 raise / >= 3 call / それ未満 fold
```

## 中級者向け (eq 概算スキル獲得後)

自分の equity 概算ができれば、grid を skip:
- 70% 以上 → best=9
- 50-70%  → good=6
- 30-50%  → weak=3
- 30% 未満 → trash=0

性能: accuracy 70.2% / loss 0.400 BB
(grid 経由より若干高精度、暗算負荷は equity 概算分が上乗せ)