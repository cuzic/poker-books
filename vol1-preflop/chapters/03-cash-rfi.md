# 第 3 章　Cash RFI（オープンレイズ）

## 3.1 ポジション別 T_open

```
係数: pair=13, suit=7, gap_cap=4, a_bonus=4
```

GTO データ（10 シナリオ）から算出した最適閾値：

| ポジション | T_open | 例: ちょうど T のハンド |
|---|---|---|
| UTG | 25 | 66, ATo, A4s |
| HJ | 23 | 55, A9o, A2s |
| CO | 21 | 44, A7o, KTo |
| BTN | 18 | A4o, K2s, Q3s |
| SB | 22 | A8o, K6s, Q7s |

## 3.2 計算手順

1. ハンドのスコアを計算する
2. ポジションの T_open と比較
3. Score ≥ T_open → オープンレイズ

**例: BTN で QTs を持ったとき**
```
H=12, L=10, gap=1, suited
Score = 12 + 10 + 7 - min(1,4) = 28
BTN T_open ≈ 18
28 ≥ 18 → オープン ✓
```

**例: UTG で K9o を持ったとき**
```
H=13, L=9, gap=3, offsuit
Score = 13 + 9 - min(3,4) = 19
UTG T_open ≈ 25
19 < 25 → フォールド ✗
```

## 3.3 境界ハンド一覧

### UTG: T_open = 25
プレイ側: 66, ATo, A4s, KQo
フォールド側: A3s, K8s, Q8s, J8s, T8s, 98s
### HJ: T_open = 23
プレイ側: 55, A9o, A2s, KJo, K7s, QJo
フォールド側: A8o, K6s, Q7s, J7s, T7s, 97s
### SB: T_open = 22
プレイ側: A8o, K6s, Q7s, J7s, T7s, 97s
フォールド側: 44, A7o, KTo, K5s, QTo, Q6s
### CO: T_open = 21
プレイ側: 44, A7o, KTo, K5s, QTo, Q6s
フォールド側: A6o, K4s, Q5s, J6s, T6s, 96s
### BTN: T_open = 18
プレイ側: A4o, K2s, Q3s, J4s, T5s, 95s
フォールド側: 22, A3o, K8o, Q8o, Q2s, J8o

## 3.4 SB からのオープン

SB は OOP（ポジション不利）のため BTN より tight。
ただしリンプも選択肢になる（GTO は混合戦略）。
本書では **raise or fold** に単純化。
T_open は BTN より +4 tight（GTO 実測: SB=22, BTN=18）。

### SB RFI の整合率は低め（76%）

実測 GTO の SB RFI を本式と照合すると、整合率は **76%**。
他のオープナー（UTG/HJ/CO/BTN）が 94〜97% なのに対して大きく低い。

理由は BvB の特殊性：
- 低ペア（22〜44, Score 17〜21）も GTO は **92〜96% で raise**
- 低スーテッドコネクター（53s, 54s, 65s 等, Score 14〜18）も **82〜97% で raise**
- ブラインド対 1 人なのでブロッカー・blocker bet の効果が大きい

本書では Score < T_open は fold に単純化するため、これらの「広い open」を取りこぼす。
ただし実戦的には fold しても EV 損失は限定的（混合戦略の境界帯）。

## 【GTO とのズレ】

**ズレが大きいハンド**: A2s〜A5s（GTO は 3-bet ブラフに使うが、
本式では score が高いためオープン推奨になる。実際はどちらでも可）。

**ズレが小さいハンド**: スーテッドコネクター系（JTs, T9s, 98s…）は
gap=0 でギャップペナルティがなく、GTO と一致しやすい。

**ポジション別整合率（実測）**: UTG 94.1% / HJ 97.0% / CO 95.9% / BTN 94.7% / **SB 76.3%**。
SB だけ突出して低いのは上記 §3.4 で説明した BvB の特性による。
