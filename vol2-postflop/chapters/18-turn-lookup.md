# 第 18 章　TURN — 専用 lookup + split rule (2P+ → bet、 overpair → bet、 役なし bluff)

## 18.1 TURN は SRP X-X 後の polarization 開始点

SRP context で flop check-check 後の turn first action は **bet 率 39%** とやや控えめです。ですが cell 別に分解してみると、強 hand と完全 air の二極化が始まっていることが分かります。

| カテゴリ | dry | paired | wet |
|---|---:|---:|---:|
| **2P+** | **81%** ★ | **72%** ★ | **53%** ★ |
| TP+ | 50% | 43% | 44% |
| ミドル | 19% | 48% | 19% |
| エア | 35% | 43% | 37% |

bet 率 > 50% のセルは **2P+ の 3 cells のみ**です。

## 18.2 TURN 専用ルール (Score 公式の代わりに simple lookup + split rule)

```
① 2P+ (= 2P / set / trips / straight / flush / FH / quads / SF) → bet
② overpair (board の最高 rank より大きい pocket pair) → bet ★
③ no_made_hand (= 完全 air、 役にも high card にも到達せず) × paired/wet → bluff bet ★
④ それ以外 (TP / ミドル / エア with showdown value) → check
```

## 18.3 各ルールの data 裏付け

### ① 2P+ → bet (lookup 主体)

47K hands で全 2P+ cell が bet 率 > 50% となります。turn での value bet 機会は、強 hand に明確に集中しています。

### ② overpair → bet (split rule、 +1.2pp 改善)

TP+ × dry/wet は cell 平均で bet 率 50% boundary 付近です。中でも **overpair (QQ-AA on under-board) は確定 bet** がおすすめです。

- 元来「TP+ × dry → check 50%」の cell に overpair を分離追加します
- acc 64.27% → 64.94% (+0.67pp)、 avg loss 0.0173 → 0.0134 (**-22%**) ★

### ③ no_made_hand × paired/wet → bluff bet (polarization 入口)

実は驚くべき発見なのですが、**完全 air (役なし、 draw も完成不可) でも turn で 50.7% bet** が GTO です。

- no_made_hand × paired: 60.9% bet ★
- no_made_hand × wet: 45.6% bet
- no_made_hand × dry: 39.8% (採用しません、 boundary 以下)

これは GTO 理論の **polarization 戦略** の data 確証となります。turn から「強 hand bet + 完全 air bluff bet」 の二極化が始まります。

## 18.4 ストリート別 polarization の中間段階

完全 air × no_draw の bet 率推移を見てみましょう。

| ストリート | 完全 air の bet 率 | 段階 |
|---|---:|---|
| SRP flop | 6-32% | merged (bluff 抑制) |
| **TURN** | **50.7%** ★ | **polarization 入口** |
| RIVER | 56-74% | fully polarized |

turn は **「flop の merged 戦略から river の polarized 戦略への移行点」** です。強 hand bet と完全 air bluff の比率が同等程度になります。

## 18.5 効果 (data 検証)

| 指標 | Score 公式のまま | TURN 専用 lookup + split |
|---|---:|---:|
| Acc | 60.9% | **64.9%** (+4.0pp) |
| avg loss BB/hand | 0.0173 | **0.0134** (-22%) ★ |
| Cov | 94.0% | **100.0%** (D cell 消滅) |
| **MQS v6** | 77.8 | 75.7 (※) |
| **MQS v7 (実害)** | - | **90.6** ★ |

※ MQS v6 の機械的低下は outlier 数自体が減ったため (Outl F1 が分母縮小で下がります)。 v7 (avg loss ベース) では 90.6 と高評価です。

## この章で覚える項目 (4 items)

1. **2P+ → 確定 bet** (3 cells lookup)
2. **overpair → 確定 bet** (split rule)
3. **no_made_hand × paired/wet → bluff bet** (polarization 入口)
4. turn から polarization 戦略開始、 完全 air の bluff bet 50%
