# 第08章 D モデル (cash 100bb 版) — 守備の暗算式

BB が IP の cbet を受けたとき、continue (call + raise) か fold かを
MV 別 continue freq 表から即判断します。
cash 100bb では MV=2 (air) が 40%、MV=3 (weak pair) が 85%、
MV=5 (second pair) が 98%、MV=7+ (top pair 以上) が 100% continue です。
MV=2 内はキッカー補正 (ace_high +5pt、no_made_hand -3pt) で細分化します。
暗算 3-5 ステップで MDF 整合の守備判断が完了します。

## なぜ D モデルが必要か

BB として IP の cbet を受けたとき、どこまで守るべきかは難しい判断です。

旧システムでは HandScore (HS) 閾値テーブルで守備判断をしていました。
D モデル (cash 版) v2 では **MV 別 continue freq 表** に切り替えます。
MV は TV の構成要素 (MV + DV) なので、計算の流れが統一されます。

「攻撃 (A モデル) も守備 (D モデル) も MV テーブルから」という一貫性が本書の強みです。
攻撃側で使った MV 値をそのまま守備判断に転用できます。

## cash 100bb の continue freq 表

cash 100bb SRP でのフロップ cbet (33%) に対する continue freq は以下の通りです。

| MV | 役の種類 | continue freq | fold freq |
|---:|---|---:|---:|
| 2 | air (ノーペア系) | 40% | 60% |
| 3 | underpair, third_pair | 85% | 15% |
| 5 | second_pair | 98% | 2% |
| 7 | top_pair, overpair | 100% | 0% |
| 8 | set, trips | 100% | 0% |
| 9 | two_pair 以上 | 100% | 0% |

**読み方**: MV が 5 以上なら virtually always continue (98-100%) です。
MV=3 (weak pair) も 85% で continue するため、弱いペアでもほぼ守ります。
判断が必要なのは MV=2 (air) だけです。40% は fold 寄りです。

## Kicker offset — MV=2 の細分化

MV=2 (air) のグループには「ノーペア系」が広く含まれます。
手牌の強さには幅があるため、キッカー補正で細分化します。

| hand | offset | 最終 continue freq | 判断 |
|---|---:|---:|---|
| ace_high | +5pt | 45% | fold 寄り (境界) |
| king_high | +0pt | 40% | fold 推奨 |
| no_made_hand | -3pt | 37% | fold 推奨 |
| low_pair | -2pt | 38% | fold 推奨 |

**適用条件**: kicker offset は MV=2 のハンドにのみ適用します。
MV=3 以上は kicker offset = 0 で基本 freq をそのまま使います。

ace_high は 45% でちょうど境界付近です。ボードのテクスチャや相手の傾向によって call/fold を決めます。
no_made_hand (67o on K72r のような完全ミス) は 37% で fold 推奨です。

## D モデル テーブル — 全 4 context 比較

### D モデル (cash 版) — context 別 continue freq

### DCBS HP 別 base continue freq

| HP | mtt_25bb | mtt_50bb | mtt_100bb | cash_100bb |
|---:|---:|---:|---:|---:|
| 2 | 67% | 54% | 28% | 40% |
| 3 | 98% | 95% | 84% | 85% |
| 5 | 99% | 96% | 87% | 98% |
| 7 | 100% | 100% | 98% | 100% |
| 8 | 100% | 100% | 100% | 100% |
| 9 | 100% | 100% | 100% | 100% |

### DCBS Kicker offset (HP=2 内の細分化)

| Hand | mtt_25bb | mtt_50bb | mtt_100bb | cash_100bb |
|---|---:|---:|---:|---:|
| Aハイ | +10pt | +17pt | +5pt | +5pt |
| Kハイ | +1pt | +6pt | +5pt | +0pt |
| ノーペア | -12pt | -13pt | +0pt | -3pt |
| ロー・ポケットペア | +0pt | -10pt | -10pt | -2pt |

## 暗算 3-5 ステップフロー

実戦での判断手順は以下の通りです。

```
[D モデル (cash 版) 暗算フロー]

Step 1: MV 確認
  hand type → MV テーブル → MV 値 (2/3/5/7/8/9)

Step 2: context 確認
  cash 100bb (Vol2 の主役) を選択

Step 3: base continue freq 参照
  D モデル_BASE[cash_100bb][MV] → base freq

Step 4: kicker offset (MV=2 のみ)
  MV=2 なら: ace_high +5 / king_high 0 / no_made_hand -3 / low_pair -2
  MV≥3 なら: offset = 0

Step 5: 判断
  continue_freq ≥ 50% → call (ときに CR 候補)
  continue_freq < 50% → fold
```

所要時間: 5 秒以内を目標にします。
MV テーブル参照だけで 90% の判断が完了します。

## MDF との整合確認

33% cbet に対する理論 MDF (Minimum Defense Frequency) は **75%** です。
式: MDF = pot ÷ (pot + bet) = 100 ÷ (100 + 33) ≈ 75%。

D モデル テーブルの MV 別 continue freq を加重平均すると約 76% になります。

| MV | continue freq | 推定頻度 | 寄与 |
|---:|---:|---:|---:|
| 2 (air) | 40% | 35% | 14% |
| 3 (weak) | 85% | 20% | 17% |
| 5 (mid) | 98% | 20% | 20% |
| 7+ (strong+) | 100% | 25% | 25% |
| 合計 | — | 100% | **76%** |

MDF の 75% とほぼ一致します。
これは「D モデル テーブルが GTO ベースで設計されている」証拠です。
実戦では D モデル テーブルを暗記するだけで MDF 計算は不要です。

## call vs check-raise の使い分け

continue が確定した後、call か check-raise (CR) かを選びます。

**MV=7+ (top pair 以上) でのバリュー CR**:
相手のバレル計画を崩すため、call 70% / CR 30% 程度が目安です。
ナッツ比率によって CR 頻度は変動します。

**MV=5 (second pair) での call 主体**:
call 90% / CR 10% 程度。強いドローが付いた場合のみ CR を検討します。

**MV=3 (weak pair) はほぼ call**:
CR は稀です。ペアが改善した場合 (turn でセットなど) に小さい CR があります。

**MV=2 (air, continue) の限定 CR**:
ほぼ call です。CR はブラフになるため、combo_draw (oesd + fd → DV=3) を持つハンドに限定します。

**CR 候補ハンドの選び方**:
1. TP + gut/FD があり、バックドアも付く (nut potential 大)
2. 2 ペア以上でバリュー CR → 相手のバレル抑止
3. 完全な air での ブラフ CR → MV=2 + combo_draw のみ

## 計算例 — cash 100bb での守備判断

### D モデル (cash 版) 守備例 (cash_100bb)

**例**: Aハイ (ace_high) を cash_100bb で defense

1. HP = **2**
2. base = DCBS_BASE[cash_100bb][HP=2] = **40%**
3. kicker offset (ace_high) = +5pt
→ **continue freq = 45%** (fold = 55%)

**例**: Kハイ (king_high) を cash_100bb で defense

1. HP = **2**
2. base = DCBS_BASE[cash_100bb][HP=2] = **40%**
→ **continue freq = 40%** (fold = 60%)

**例**: ノーペア (no_made_hand) を cash_100bb で defense

1. HP = **2**
2. base = DCBS_BASE[cash_100bb][HP=2] = **40%**
3. kicker offset (no_made_hand) = -3pt
→ **continue freq = 37%** (fold = 63%)

**例**: アンダーペア (underpair) を cash_100bb で defense

1. HP = **3**
2. base = DCBS_BASE[cash_100bb][HP=3] = **85%**
→ **continue freq = 85%** (fold = 15%)

**例**: セカンドペア (second_pair) を cash_100bb で defense

1. HP = **5**
2. base = DCBS_BASE[cash_100bb][HP=5] = **98%**
→ **continue freq = 98%** (fold = 2%)

## 4 context 比較 — MTT depth との違い

Vol2 では cash_100bb を主軸にしますが、MTT depth との違いを把握しておくと役立ちます。

| context | air (MV=2) continue |
|---|---:|
| mtt_25bb | 67% |
| mtt_50bb | 54% |
| mtt_100bb | 28% |
| cash_100bb | 40% |

MTT depth が深いほど air の continue freq が下がります。
deep stack では将来ストリートでの損失が大きくなるため、air を早めに整理します。
cash_100bb は mtt_100bb (28%) より高い 40% で、よりルーズに守る設計です。

mtt_25bb では air が 67% と高く、スタックが浅いためフォールドコストが相対的に高いためです。

全 4 context の詳細な使い分けは Vol3 (D モデル) で扱います。

## まとめ

- MV テーブル参照だけで 90% の判断が完了する。
- MV=2 のみ kicker offset (ace_high +5, no_made_hand -3, low_pair -2)。
- MV≥5 は virtually always continue (98-100%)。
- MDF ≈ 75% と D モデル テーブルは整合している (設計根拠)。
- CR は MV=7+ のバリュー CR + MV=5 以下の稀なブラフ CR のみ。
- MTT depth 別比較 (mtt_25bb/50bb/100bb) は付録または Vol3 を参照。
