# 第12章 Full DCBS——4 context の守備 continue freq

Full DCBS（Defense CBS）は BB の cbet に対する continue freq を HP × context で予測するモデルです。
UCBS-v2（攻撃）と DCBS（守備）は別モデルです。
4 context（mtt_25bb / mtt_50bb / mtt_100bb / cash_100bb）でスタック深度が深いほど air は fold し、
top_pair 以上は全 context で 96%+ call するという深度反転の構造が核心です。

## DCBS の構造——HP バケット × context の 2 段テーブル

DCBS の計算式はシンプルです。

```
continue_freq = base_dcbs[context][HP]
              + kicker_offset[context][hand]  (HP=2 の場合のみ)
fold_freq = 1.0 - continue_freq
```

UCBS-v2 が CBS（HP+DP）、Confidence、Size、α/β/offset など多数のパラメータを使うのに対し、
DCBS は HP のみで base を引き、HP=2（air 系）に限り手別の kicker_offset で細分化します。

攻撃（UCBS-v2）と守備（DCBS）が別モデルである理由は、defense の判断基準が攻撃と異なるためです。
defense は「相手の bet に対してコールかフォールドか」を決める問題であり、
ボードとの相性（Confidence）よりも「自分の手の絶対的な強さ（HP）」と
「スタック深度（context）」が支配的です。
DP（ドロー点）は defense でも考慮されますが、DCBS では単純化のため HP のみを使います。

### Full DCBS 4 context 完全表

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

## depth で反転する defense 戦略——「深いほど fold」

DCBS の最重要発見は「スタック深度が深いほど air を fold する」という反転構造です。

HP=2（air 系: no_made_hand / ace_high / king_high / low_pair）の base continue freq:
- mtt_25bb: **67%**（浅い → air も 3 回に 2 回はコール）
- mtt_50bb: **54%**（中間）
- cash_100bb: **40%**（Cash は 4 割コール）
- mtt_100bb: **28%**（深い → air は 4 分の 1 しかコールしない）

mtt_25bb と mtt_100bb の差は 67% vs 28% で 2.4 倍の開きがあります。

この反転が起きる理由は以下の通りです。
浅いスタック（25bb）では相手の bet サイズが pot の 33% 程度と小さく、
MDF（最低守備頻度）が高いため air でも fold するとエクスプロイトされます。
また push/fold 圏に近く、air でコールしてターン・リバーで勝負する意味があります。
深いスタック（100bb）では bet サイズも大きく、air でコールし続けると多くのチップを失います。
相手のバレル戦略に対して early fold が EV 的に有利になります。

一方、top_pair 以上（HP=7 以上）は全 context で 96%+ のコール頻度を示します。
mtt_100bb の top_pair でも 98% コールです。これは「強い手は depth に関係なく fight する」
というGTO的な整合性を示しています。

### mtt_25bb——浅スタックの広い defense

mtt_25bb の base continue freq は全 context 中最も高く、air でも 67% コールします。
push/fold 圏（SBR 15-25）に近い状況では、フロップでのコミットが重要です。
top_pair は 100% コール（push 方向）、third_pair / underpair も 98% コールします。
WRMSE 14.36% は 4 context 中 2 番目に高い精度です。

### mtt_50bb——中盤の standard defense

mtt_50bb は air=54% で「コールよりも少し fold 寄り」の中間的な守備です。
low_pair の kicker_offset が -0.10 と大きく、low_pair は base(54%) - 10% = 44% コールと
かなりタイトになります。
ace_high の kicker_offset は +0.17 で最も高く、Aハイは 25bb より middle 効果が大きいです。
WRMSE 14.87% は安定した精度です。

### mtt_100bb——深スタックの厳しい defense

mtt_100bb は air=28% と最も厳しい base freq です。
HP=3（弱ペア: underpair / third_pair）でも 84% とやや低く、
HP=5（second_pair）で 87% とスタックが深いほど middle ハンドも慎重になります。
kicker_offset は全体的に小さく（ace_high: +5%、king_high: +5%）、
depth が増すと kicker の影響が減衰します。
WRMSE 15.86% は許容範囲内の精度です。

### cash_100bb——Cash の defense 特性

cash_100bb は air=40% で mtt_100bb の 28% よりも高く、
cash では air を若干広くコールします。
second_pair の base が 98% と high く（mtt_100bb の 87% より大幅高）、
cash の second_pair はほぼ必ずコールする傾向があります。
kicker_offset は ace_high: +5%、king_high: 0%、no_made_hand: -3%、low_pair: -2% と
mtt に比べて kicker 効果が一様に小さいです。
WRMSE 17.17% は 4 context 中最も低い精度ですが許容範囲内です。

## Kicker offset——HP=2 内の ace_high / king_high 細分化

HP=2 の中には no_made_hand（ノーペア）、ace_high（Aハイ）、king_high（Kハイ）、
low_pair（ローペア）の 4 種類が含まれます。
これらを HP のみで扱うと「Aハイも ノーペアも同じコール頻度」となり、
GTO データとの乖離が生じます。
kicker_offset はこの HP=2 内の細分化を担います。

浅スタック（25/50bb）では ace_high の kicker 効果が大きく、
mtt_50bb では ace_high が +17pt と突出しています。
これは 50bb ではバックドアエクイティ込みで Aハイのコールが頻繁に正当化されるためです。
深スタック（100bb）では ace_high と no_made_hand の差が最大 5pt に縮まり、
kicker の影響が减衰します。

## DCBS の実戦運用——5 秒で continue を決める

実戦での DCBS 運用フローは以下の通りです。

**Step 1**: 自分の手の HP を確認する。
- HP=2: no_made_hand / ace_high / king_high / low_pair
- HP=3: underpair / third_pair
- HP=5: second_pair
- HP=7: top_pair / overpair
- HP=8+: set / trips / two_pair / flush / straight 以上

**Step 2**: 現在の context（スタック深度）を確認する。
- mtt_25bb（SBR ≈ 12-15）: push/fold 圏直前
- mtt_50bb（SBR ≈ 25-30）: 中盤バブル前
- mtt_100bb（SBR ≈ 50+）: 序盤 / FT 直後
- cash_100bb: キャッシュゲーム

**Step 3**: base 表を引く。HP=2 なら kicker_offset を加算する。

**Step 4**: 算出した continue_freq が 50% 以上ならコール、未満ならフォールド。
（ただしレイズオプションがある場合はチェックレイズを別途検討する。）

最も重要な判断ポイントは HP=2（air 系）の context 別分岐です。
25bb ならば「3 回に 2 回はコール」、100bb ならば「4 回に 1 回しかコールしない」という
直感的なルールを覚えておくと実戦で即座に判断できます。

## DCBS vs MDF——GTO 根拠の確認

MDF（Minimum Defense Frequency）は pot bet のサイズから算出される最低守備頻度です。
相手が pot の 33% をベットした場合：MDF = ポット ÷ (ポット + bet) = 1 ÷ (1 + 0.33) ≈ 75%

MDF は全体レンジの守備頻度を示しますが、DCBS は個々の手の continue freq を示します。
DCBS の全体的な continue freq がおおよそ MDF と整合しているかを確認することで、
レンジ全体のバランスを確認できます。

たとえば mtt_50bb では HP=2 が 54%（範囲内の手の大半）、HP=3 が 95%、HP=5+ が 96%+ であり、
加重平均すると全体の continue freq は概ね 70〜75% 程度となり、MDF と整合しています。
DCBS は MDF の考え方を HP 別に細分化したモデルと理解できます。

## 実戦例題

### DCBS continue freq 計算例（4 context）

**例**: Aハイ (ace_high) を mtt_25bb で defense

1. HP = **2**
2. base = DCBS_BASE[mtt_25bb][HP=2] = **67%**
3. kicker offset (ace_high) = +10pt
→ **continue freq = 77%** (fold = 23%)

**例**: ノーペア (no_made_hand) を mtt_50bb で defense

1. HP = **2**
2. base = DCBS_BASE[mtt_50bb][HP=2] = **54%**
3. kicker offset (no_made_hand) = -13pt
→ **continue freq = 41%** (fold = 59%)

**例**: ロー・ポケットペア (low_pair) を mtt_100bb で defense

1. HP = **2**
2. base = DCBS_BASE[mtt_100bb][HP=2] = **28%**
3. kicker offset (low_pair) = -10pt
→ **continue freq = 18%** (fold = 82%)

**例**: トップペア (top_pair) を cash_100bb で defense

1. HP = **7**
2. base = DCBS_BASE[cash_100bb][HP=7] = **100%**
→ **continue freq = 99%** (fold = 1%)

**例**: セカンドペア (second_pair) を mtt_25bb で defense

1. HP = **5**
2. base = DCBS_BASE[mtt_25bb][HP=5] = **99%**
→ **continue freq = 99%** (fold = 1%)

**例**: Kハイ (king_high) を mtt_50bb で defense

1. HP = **2**
2. base = DCBS_BASE[mtt_50bb][HP=2] = **54%**
3. kicker offset (king_high) = +6pt
→ **continue freq = 60%** (fold = 39%)

## まとめカード

- **DCBS 式**: continue_freq = base[HP] + kicker_offset[hand]（HP=2 のみ kicker 適用）
- **depth 反転の核心**: air(HP=2)は浅い(25bb)=67% → 深い(100bb)=28%（2.4倍の差）
- **top_pair 以上は depth 不問**: 全 context で 98%+ のコール
- **kicker 効果は深さで减衰**: 浅(ace vs no_made 差 22pt) → 深(5pt)
- **UCBS-v2 とは別モデル**: 攻撃と守備は設計が異なる（HP のみ使用）
- **MDF 整合**: DCBS の加重平均 ≈ 33% bet に対する MDF 75% 程度と整合
