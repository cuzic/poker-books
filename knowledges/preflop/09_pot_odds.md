# 09: ポットオッズの基本と応用

検索日: 2026-04-19

---

## 1. ポットオッズの基本公式

### 期待値からの導出

コール時の期待値（EV）がゼロ（損益分岐点）になる勝率 Q を求める。

- 勝った場合の利益 = W（コール後ポット全体 − 自分のコール額）
- 負けた場合の損失 = L（コール額）

```
EV = Q × W − (1 − Q) × L = 0
→ Q × W = (1 − Q) × L
→ Q × W = L − Q × L
→ Q × (W + L) = L
→ Q = L / (W + L)
```

W + L はコール後のポット全体（相手のベット + コール前のポット + 自分のコール額）に等しいため：

**必要勝率（損益分岐エクイティ）= コール額 ÷ コール後の最終ポット**

- 出典: [What are Pot Odds in poker? | GTO Wizard](https://blog.gtowizard.com/what-are-pot-odds-in-poker/)
- 出典: [Pot odds - Wikipedia](https://en.wikipedia.org/wiki/Pot_odds)
- 出典: [ポーカーにおけるポットオッズとは何か？ note](https://note.com/grid_poker/n/n3994a69ab7ea)

### 公式の二表記

**厳密版（推奨）**

```
必要勝率 = コール額 ÷ (コール前ポット + 相手ベット額 + コール額)
         = コール額 ÷ 最終ポット
```

**近似版（暗算用）**

コール額がポットに比べて小さい場合、分母のコール額を省略して近似できる。

```
必要勝率 ≈ コール額 ÷ (コール前ポット + 相手ベット額)
```

例: ポット $30、ベット $10
- 厳密: 10 / (30 + 10 + 10) = 10 / 50 = **20%**
- 近似: 10 / (30 + 10) = 10 / 40 = **25%**（約 5% 過大評価）

コール額がポットの 20% 以下なら近似誤差は数% 程度で実用的。コール額が大きい場合は厳密版を使う。

### オッズ比との対応

```
オッズ比 = (最終ポット − コール額) : コール額
         = (コール前ポット + 相手ベット額) : コール額
```

例: ポット $30、ベット $10 → オッズ比 = 40:10 = 4:1
→ 必要勝率 = 1 / (4+1) = 20%

---

## 2. サイズ別必要勝率早見表

### プリフロップ：BBからコールする場合（SBフォールド想定）

| オープンサイズ | コール前ポット | コール額 | 最終ポット | 必要勝率 |
|--------------|-------------|---------|-----------|---------|
| 2bb オープン | 2bb(OR) + 0.5bb(SB) + 1bb(BB) = 3.5bb | 1bb (BBは1bb投入済みなので差額) | 4.5bb | **22%** |
| 2.5bb オープン | 2.5bb + 0.5bb + 1bb = 4bb | 1.5bb | 5.5bb | **27%** |
| 3bb オープン | 3bb + 0.5bb + 1bb = 4.5bb | 2bb | 6.5bb | **31%** |
| 4bb オープン | 4bb + 0.5bb + 1bb = 5.5bb | 3bb | 8.5bb | **35%** |

計算確認（2.5bb の例）:
- コール前ポット = オープン 2.5bb + SB 0.5bb + BB投入済み 1bb = 4bb
- BBの追加コール額 = 2.5bb − 1bb（投入済み）= 1.5bb
- 最終ポット = 4bb + 1.5bb = 5.5bb
- 必要勝率 = 1.5 / 5.5 ≈ 27%

- 出典: [Should You Be Using Preflop Pot Odds Calculations? - 888poker](https://www.888poker.com/magazine/strategy/should-you-be-using-preflop-poker-odds-calculations)
- 出典: [Pot Odds - How to Calculate Pot Odds in Poker - Upswing Poker](https://upswingpoker.com/pot-odds-step-by-step/)

### プリフロップ：SBからコールする場合

| オープンサイズ（BTNから）| コール前ポット | コール額 | 最終ポット | 必要勝率 |
|------------------------|-------------|---------|-----------|---------|
| 2.5bb オープン（BTN） | 2.5bb + 0.5bb(SB) + 1bb(BB) = 4bb | 2bb（SBは0.5bb投入済み） | 6bb | **33%** |
| 3bb オープン（BTN） | 3bb + 0.5bb + 1bb = 4.5bb | 2.5bb | 7bb | **36%** |

SBはポジション劣位（OOP）のため、ポットオッズで有利でも実現率が低い。SBからのコールは基本的に3betか3betかフォールドが推奨される。

### ポストフロップ：ベットサイズ別早見表（参考）

| ベットサイズ（ポット比） | 必要勝率 |
|------------------------|---------|
| 1/4 pot (25%) | 17% |
| 1/3 pot (33%) | 20% |
| 1/2 pot (50%) | 25% |
| 2/3 pot (67%) | 29% |
| 3/4 pot (75%) | 30% |
| 1x pot (100%) | 33% |
| 2x pot (200%) | 40% |

- 出典: [Pot Odds in Poker (How to Never Miss a Profitable Call) - PokerCoaching](https://pokercoaching.com/blog/pot-odds-in-poker/)

---

## 3. 暗算のコツ

### 基本的なイメージ

「コール額がコール後ポットの何分の一か」を直感でつかむ。

| 目安 | 必要勝率 | 意味 |
|------|---------|------|
| 1/6 | ≈ 17% | コール額がポットの 1/5 程度 |
| 1/5 | 20% | コール額がポットの 1/4 程度 |
| 1/4 | 25% | ハーフポットベット |
| 1/3 | 33% | ポットサイズベット |
| 2/5 | 40% | ダブルポットベット |

### プリフロップ特有：「投入済みブラインド」の扱い

BBとSBはすでにチップを投入しているため、**追加コール額（差額）** で計算する。

```
BBの追加コール額 = オープンサイズ − 1bb（BB投入済み）
SBの追加コール額 = オープンサイズ − 0.5bb（SB投入済み）
```

コール前ポットには **自分の投入済み額を含める**。

例: 3bb オープン vs BB
- コール前ポット = 3bb（OR） + 0.5bb（SB） + 1bb（BB投入済み） = 4.5bb
- 追加コール額 = 3 − 1 = 2bb
- 最終ポット = 4.5 + 2 = 6.5bb
- 必要勝率 = 2 / 6.5 ≈ 31%

「3bbオープンにBBからコールは約30%の勝率が必要」と暗記しやすい。

### 「1/3、1/4、1/5」イメージで素早く判断

- BBが 2bb オープンにコール: コール1bb、ポット4.5bb → 「ポットの1/4.5 ≈ 1/5」 → 必要勝率 22% ≈ 「約1/5」
- BBが 3bb オープンにコール: コール2bb、ポット6.5bb → 「ポットの1/3.25 ≈ 1/3」 → 必要勝率 31% ≈ 「約1/3」
- BBが 4bb オープンにコール: コール3bb、ポット8.5bb → 「ポットの1/2.8 ≈ 1/3」 → 必要勝率 35% ≈ 「約1/3弱」

- 出典: [Easy Poker Math: Pot Odds - SplitSuit Poker](https://www.splitsuit.com/easy-poker-pot-odds)

---

## 4. プリフロップ具体例10問

以下、6人テーブル（6-max）・100bb スタック・レーキなし想定で計算。

### 問1: UTG 2.5bb オープン → BB コール（SBフォールド）

- コール前ポット: 2.5 + 0.5 + 1 = 4bb
- BBの追加コール額: 2.5 − 1 = 1.5bb
- 最終ポット: 5.5bb
- **必要勝率: 1.5 / 5.5 ≈ 27%**

UTGはレンジが強いため、BBはこの必要勝率以上のエクイティを持つハンドのみコール。

### 問2: CO 3bb オープン → BTN コール（SB・BBフォールド）

- コール前ポット: 3 + 0.5 + 1 = 4.5bb
- BTNのコール額: 3bb（投入なし）
- 最終ポット: 7.5bb
- **必要勝率: 3 / 7.5 = 40%**

BTNはIPなので実現率が高いが、直接のポットオッズは厳しい。インプライドオッズで補完。

### 問3: BTN 3bb オープン → SB コール（BBフォールド）

- コール前ポット: 3 + 0.5 + 1 = 4.5bb
- SBの追加コール額: 3 − 0.5 = 2.5bb
- 最終ポット: 7bb
- **必要勝率: 2.5 / 7 ≈ 36%**

SBはOOPのため実現率が低く、このポットオッズよりさらに高いエクイティが実質的に必要。

### 問4: BTN 2bb オープン → BB コール（SBフォールド）

- コール前ポット: 2 + 0.5 + 1 = 3.5bb
- BBの追加コール額: 2 − 1 = 1bb
- 最終ポット: 4.5bb
- **必要勝率: 1 / 4.5 ≈ 22%**

最も安価なコール。BBはかなり広くディフェンスできる。

### 問5: UTG 3bb オープン → BB コール（SBフォールド）

- コール前ポット: 3 + 0.5 + 1 = 4.5bb
- BBの追加コール額: 2bb
- 最終ポット: 6.5bb
- **必要勝率: 2 / 6.5 ≈ 31%**

UTGの強いレンジに対して31%が必要。OOPのためGTOでの実際の防衛レンジはこれより絞られる。

### 問6: BTN 2.5bb オープン → BB コール（SBフォールド）

- コール前ポット: 2.5 + 0.5 + 1 = 4bb
- BBの追加コール額: 1.5bb
- 最終ポット: 5.5bb
- **必要勝率: 1.5 / 5.5 ≈ 27%**

BTNのレンジは広い（約40%）ため、BBは多くのハンドでコールできる。

### 問7: CO 2.5bb オープン → BTN コール、BB コール（SBフォールド）

#### BTNのコール

- コール前ポット: 2.5 + 0.5 + 1 = 4bb（まだBBはコールしていない）
- BTNのコール額: 2.5bb
- 暫定ポット: 6.5bb
- BTNから見た必要勝率: 2.5 / 6.5 ≈ **38%**（BBのアクション前）

#### BBがスクイーズせずコールする場合

- コール前ポット: 2.5(CO) + 2.5(BTN) + 0.5(SB) + 1(BB) = 6.5bb
- BBの追加コール額: 2.5 − 1 = 1.5bb
- 最終ポット: 8bb
- **必要勝率: 1.5 / 8 ≈ 19%**（マルチウェイのためポットオッズが改善）

マルチウェイはポットオッズが改善するが、エクイティの実現率が低下する。

### 問8: HJ 3bb オープン → BTN 9bb 3bet → HJ コール

- HJのコール前ポット: 9(3bet) + 3(HJオープン) + 0.5 + 1 = 13.5bb
- HJの追加コール額: 9 − 3 = 6bb
- 最終ポット: 19.5bb
- **必要勝率: 6 / 19.5 ≈ 31%**

3betに対するコールでも計算手順は同じ。ただしHJはOOPでポストフロップの不利があるため、実際にはより高いエクイティが必要。

### 問9: BTN 3bb オープン → BB 10bb 3bet → BTN コール

- BTNのコール前ポット: 10(3bet) + 3(BTNオープン) + 0.5(SB) + 1(BB) = 14.5bb
- BTNの追加コール額: 10 − 3 = 7bb
- 最終ポット: 21.5bb
- **必要勝率: 7 / 21.5 ≈ 33%**

BTNはIP（3betコールの場合）。インプライドオッズで追加利益が見込めるスーテッドコネクターなどが候補。

### 問10: BTN 3bb オープン → BB 10bb 3bet → BTN 25bb 4bet → BB オールインコール（100bb スタック）

- BBの追加コール額: 100 − 10 = 90bb
- コール前ポット: 25(4bet) + 10(3bet) + 3 + 0.5 + 1 = 39.5bb
- BBのコール額: 90bb（残スタック）
- 最終ポット: 129.5bb + 90bb = 200bb
- 正確には: BBは10bbすでに出しており 90bb 追加 → コール前ポット = 25 + 10 + 0.5 + 1 = 36.5bb、BBの追加コール: 100 − 10 = 90bb → 最終ポット = 36.5 + 25(4bet残) ... 

簡略計算（4betオールインコール）:
- スタック 100bb、4bet サイズ 25bb vs 3bet 10bb
- BBの残スタック = 90bb をコール
- 最終ポット = 200bb（スタック全量×2）
- **必要勝率: 90 / 200 = 45%**（近似: スタックの約半分が必要）

オールインは「最終アクション」のため、ポットオッズのみで判断できる数少ないプリフロップシチュエーション。

- 出典: [Should You Be Using Preflop Pot Odds Calculations? - 888poker](https://www.888poker.com/magazine/strategy/should-you-be-using-preflop-poker-odds-calculations)
- 出典: [Pot Odds - Upswing Poker](https://upswingpoker.com/pot-odds-step-by-step/)

---

## 5. ポットオッズだけで決まらない要素

### 実現率（エクイティ・リアライゼーション）

**定義**: 手持ちの生エクイティが実際の期待値にどれだけ変換されるかの比率。

```
EQR = 実際のEV / (ポット × エクイティ)
```

ポジション・ハンドの特性・相手のレンジによって大きく変動する。

**主な影響要素**:
- **ポジション**: IP（後手）はEQR > 1 になりやすい。OOP（先手）はEQR < 1 になりやすい
- **ハンドの特性**: スーテッドコネクターはブロードウェイオフスートより実現率が高い
- **マルチウェイ**: プレイヤー数が増えると各ハンドの実現率が下がる

**具体例（GTO Wizardのデータ）**:
- BB（OOP）の A♦2♦ は J♥T♦9♥ フロップでエクイティが約40%あっても EQR が著しく低い
- 98s（ボトムペア+OESD）はOOPで生エクイティの約25%しか実現できない

**実用的な調整目安**:
- OOP コール: 純ポットオッズ必要勝率 + 5〜7% 追加でエクイティが必要
- IP コール: 純ポットオッズ必要勝率とほぼ一致（インプライドオッズで相殺）

- 出典: [Equity Realization | GTO Wizard](https://blog.gtowizard.com/equity-realization/)
- 出典: [What is Equity Realization & How Does it Impact Strategy - Upswing Poker](https://upswingpoker.com/equity-realization-explained/)

### インプライドオッズとリバースインプライドオッズ

**インプライドオッズ**: 将来のストリートで追加的に獲得できる額を加味したオッズ。
- 例: 4bb のポットオッズが合わなくてもスーテッドコネクターは将来大きなポットを取れる可能性
- ナッツドロー・スーテッドハンドはインプライドオッズが高い

**リバースインプライドオッズ**: 将来のストリートで追加的に失う期待額。
- 例: KQo が相手の 4bet（JJ+/AK レンジ）に対して直接ポットオッズを満たしていても、ポストフロップでドミネートされやすい
- KQo の場合: 4bet レンジへのエクイティ 25.4% > 必要勝率 23.4% だがフォールド推奨

- 出典: [Should You Be Using Preflop Pot Odds Calculations? - 888poker](https://www.888poker.com/magazine/strategy/should-you-be-using-preflop-poker-odds-calculations)

### ブロッカー効果

相手のレンジの形成に影響するカードを保持していると、エクイティ計算に影響が出る。
- 例: Aを持っていると相手が AA を持つ可能性が半減する
- ブロッカーはエクイティ計算に組み込まれるため、単純なポットオッズ比較よりレンジ対レンジのエクイティ計算が重要

### スタック深度

- ディープスタック（200bb以上）: インプライドオッズが増大するため、スーテッドコネクターなど「ナッツを作れるハンド」のコール価値が上がる
- ショートスタック（50bb以下）: インプライドオッズが減少するため、より直接のポットオッズに近い判断になる
- オールイン状況: 追加ストリートがないため、ポットオッズ単独で判断できる

### ポストフロップスキル差

自分が相手より大きくポストフロップを上回るスキルを持つ場合、エクイティの実現率が改善する（エクスプロイタブルな相手には有効）。GTO前提では考慮不要。

---

## 6. MDF（最低防衛頻度）との関係

### MDF の基本公式

MDF（Minimum Defense Frequency）は、相手のブラフが純利益にならないために必要な「コールまたはレイズする最低頻度」。

```
MDF = ポットサイズ ÷ (ポットサイズ + ベット額)
    = 1 − α（アルファ）

α（アルファ、相手のブラフ損益分岐点）= ベット額 ÷ (ポットサイズ + ベット額)
```

例: ポット 100、ベット 50
```
MDF = 100 / (100 + 50) = 67%（レンジの67%をディフェンス）
α  = 50 / (100 + 50)  = 33%（相手のブラフは33%フォールドで収支±0）
```

### ポットオッズとMDFの数値的違い

同じ状況（ポット 100、ベット 100）で：

| 指標 | 計算 | 数値 | 意味 |
|------|------|------|------|
| ポットオッズ必要勝率 | 100 / (100 + 100 + 100) | **33%** | コールするハンドに必要なエクイティ |
| MDF | 100 / (100 + 100) | **50%** | レンジの何%をディフェンスすべきか |

**2つは異なる指標**。50% がレンジの防衛頻度で、その中の各ハンドが平均 33% のエクイティを持つことでGTO均衡が成立する。

- 出典: [Poker — minimum defence frequency vs pot odds | Mike Fowlds | Medium](https://mikefowlds.medium.com/poker-minimum-defence-frequency-vs-pot-odds-88289b64249c)

### BB ディフェンスにおける MDF の目安

よく見られるベットサイズと、BBが守るべきレンジの頻度目安：

| ベットサイズ（ポット比） | α（相手のブラフ損益分岐） | MDF（BBのディフェンス頻度） |
|------------------------|--------------------------|---------------------------|
| 1/3 pot | 25% | **75%** |
| 1/2 pot | 33% | **67%** |
| 2/3 pot | 40% | **60%** |
| 3/4 pot | 43% | **57%** |
| 1x pot | 50% | **50%** |

例: 3bbオープンに対するBBのディフェンス（コール + 3bet）
- ポット（相手から見た）: 3bb(OR) + 0.5bb(SB) = 3.5bb（BBのアクション前）
- α = 3 / (3.5 + 3) = 46%
- MDF ≈ 54% → BBはレンジの約54%をディフェンスする

### GTOとの関係

**GTO はMDFを常に満たすわけではない。**

GTO Wizardの研究によれば:
- フロップのCBetに対してBBは理論的MDFを下回るフォールド頻度を示すことが多い
- 理由: ブラフが「0エクイティ」の仮定に基づくMDFの公式は、実際のセミブラフ（ドローエクイティを持つブラフ）には機能しない
- つまり、相手のブラフが残エクイティを持つ場合、GTO では MDF より多くフォールドしても相手のブラフが利益にならない

**実用指針**:
- **ポットオッズ**: 個別ハンドのコール判断（「このハンドでコールすべきか」）
- **MDF**: レンジ全体の構成学習・オフテーブル分析（「レンジとしてどれだけ広く守るか」）
- GTO ソルバー学習では MDF を参照点として使いながら、個別ハンドはポットオッズとエクイティ実現率で判断する

- 出典: [MDF & Alpha | GTO Wizard](https://blog.gtowizard.com/mdf-alpha/)
- 出典: [Minimum Defense Frequency vs Pot Odds in Poker - Upswing Poker](https://upswingpoker.com/minimum-defense-frequency-vs-pot-odds/)
- 出典: [Mathematical Misconceptions in Poker | GTO Wizard](https://blog.gtowizard.com/mathematical-misconceptions-in-poker/)

---

## 7. GTOとポットオッズ単独判断の乖離

### 「ポットオッズが良いのにフォールドする」ケース

GTO では以下の理由でポットオッズを満たすハンドをフォールドすることがある。

1. **エクイティ実現率の低さ**
   - OOPで将来のストリートでプレッシャーを受け続ける
   - ハンドの特性（ミドルペア+キッカー弱）でポストフロップの選択肢が限られる

2. **リバースインプライドオッズ**
   - 相手の強いレンジに対してドミネートされるリスクが高い
   - 例: KQo は 4bet レンジ（JJ+/AK）へのエクイティは 25%（必要勝率 23% を超える）がフォールド推奨
   - 理由: AK・KK がKQoを大幅に上回る確率でポストフロップも不利

3. **ブロッカー考慮によるエクイティ再計算**
   - 特定のカードを持つことで相手のナッツ頻度が変わる

### 「ポットオッズが悪いのにコールする」ケース（インプライドオッズ）

- スーテッドコネクター（例: 65s）は直接ポットオッズが厳しくても将来のストリートでナッツを作れる
- 例: ポットオッズが 15% 必要なのに 65s のエクイティが 12% でも、ディープスタックならコール可

### GTO防衛頻度のポットオッズとの関係

プリフロップのオープン vs BBのコール：

| オープンサイズ | ポットオッズ必要勝率 | GTO BBコール範囲（目安） |
|--------------|-------------------|------------------------|
| 2bb | 22% | 約55%（非常に広い） |
| 2.5bb | 27% | 約45% |
| 3bb | 31% | 約40% |
| 4bb | 35% | 約30% |

ポットオッズの必要勝率と GTO コール頻度は直接対応しない。GTO コール頻度はレンジ全体の中での適切な混合（コール・3bet・フォールド）で決まる。

- 出典: [GTO Preflop Basics - PokerCoaching](https://pokercoaching.com/blog/gto-preflop-basics/)
- 出典: [Preflop Range Morphology | GTO Wizard](https://blog.gtowizard.com/preflop-range-morphology/)

---

## 本書への適用

- **第9章メイン**: ポットオッズの公式と早見表（セクション1・2・3）
- **第9章具体例**: 10問の計算演習（セクション4）
- **第9章発展**: ポットオッズを超えた判断基準として実現率を紹介し、次章（実現率）につなぐ（セクション5）
- **第15章 GTO基礎**: MDFとの関係、GTOと単純ポットオッズ判断の乖離（セクション6・7）

執筆時の注意点:
- BBの「投入済み1bb」の扱いを必ず明示する（初心者が最も混乱するポイント）
- 「コール後のポット」で割ることを繰り返し強調する（「現在のポット」で割る誤りが多い）
- オールイン状況はポットオッズ単独で判断できる例外ケースとして位置づける

---

## 参考URL一覧

- [What are Pot Odds in poker? | GTO Wizard](https://blog.gtowizard.com/what-are-pot-odds-in-poker/)
- [Pot Odds - How to Calculate Pot Odds in Poker | Upswing Poker](https://upswingpoker.com/pot-odds-step-by-step/)
- [Minimum Defense Frequency vs Pot Odds in Poker | Upswing Poker](https://upswingpoker.com/minimum-defense-frequency-vs-pot-odds/)
- [MDF & Alpha | GTO Wizard](https://blog.gtowizard.com/mdf-alpha/)
- [Mathematical Misconceptions in Poker | GTO Wizard](https://blog.gtowizard.com/mathematical-misconceptions-in-poker/)
- [Equity Realization | GTO Wizard](https://blog.gtowizard.com/equity-realization/)
- [Pot Odds in Poker (How to Never Miss a Profitable Call) | PokerCoaching](https://pokercoaching.com/blog/pot-odds-in-poker/)
- [Should You Be Using Preflop Pot Odds Calculations? | 888poker](https://www.888poker.com/magazine/strategy/should-you-be-using-preflop-poker-odds-calculations)
- [Pot odds | Wikipedia](https://en.wikipedia.org/wiki/Pot_odds)
- [Poker — minimum defence frequency vs pot odds | Mike Fowlds | Medium](https://mikefowlds.medium.com/poker-minimum-defence-frequency-vs-pot-odds-88289b64249c)
- [ポーカーにおけるポットオッズとは何か？ | note](https://note.com/grid_poker/n/n3994a69ab7ea)
- [ポーカーのオッズ計算・必要勝率の考え方 | ゼロポーカー](https://zero-poker.com/texasholdem-odds/)
- [Minimum Defense Frequency – Learn How to Use MDF | PokerCoaching](https://pokercoaching.com/blog/mdf-poker/)
- [GTO Preflop Basics: Understand Core Principles | PokerCoaching](https://pokercoaching.com/blog/gto-preflop-basics/)
- [Preflop Range Morphology | GTO Wizard](https://blog.gtowizard.com/preflop-range-morphology/)
