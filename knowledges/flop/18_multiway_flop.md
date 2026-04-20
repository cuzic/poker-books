# マルチウェイのフロップ戦略

検索日: 2026-04-20

## 概要

マルチウェイポット（3人以上がフロップを見る状況）では、ヘッズアップとは根本的に異なる戦略が必要になる。防衛負担の分散、エクイティの希釈、ナッツ優位性の重要性上昇により、CBet頻度・ベットサイズ・ハンド選択のすべてで大幅な調整が求められる。

---

## 主要な知見

### 知見1: CBet 頻度の激減（理論値）

GTO Wizardのソルバーデータによると、ヘッズアップ対BBと比較して、同じオープナーがBB+SB（マルチウェイ）に対峙するとき、チェック頻度が **+11%** 増加する。

また、ヘッズアップでは18%使用されていた「ポットサイズのCBet」は、マルチウェイではわずか **1.3%** まで激減する。

ハンドによっては、4ウェイボードでKKやKQすらベットの根拠を失い、KsJsのようなハンドもブラフ候補から外れる。

- 出典: [Playing In Position Against Two Callers | GTO Wizard](https://blog.gtowizard.com/playing-in-position-against-two-callers/)
- 出典: [10 Tips for Multiway Pots in Poker | GTO Wizard](https://blog.gtowizard.com/10-tips-multiway-pots-in-poker/)

### 知見2: ナッツ必要性の上昇

GTO Wizardは「**Nut potential is King**（ナッツポテンシャルが王者）」と表現している。マルチウェイではスタックオフレンジが極めて限定されるため、ナッツまたはナッツに近いドローを持つことの重要性が劇的に増加する。

Galfondのソルバー分析では、4人がコールしたK-T-6フロップでAAを保有していても、「誰かがトップペア以上を持つ確率は69%」に達し、AAで75%ポットベットして1回コールされただけで「約40%の確率でビート済み」という結果が示されている。

マルチウェイでは複数の相手レンジがナッツを保有しうるため、「ナッツ比率（nut ratio）が高まるほど最適ベットサイズは下がる」という原則が直接的に表れる。

- 出典: [Mastering Multi-Way Pots - Phil Galfond](https://www.philgalfond.com/articles/mastering-multi-way-pots)
- 出典: [Multiway Muscle: Big-Bet Windows Revealed by GTO Wizard](https://www.poker.pro/strategy/multiway-muscle-big-bet-windows-revealed-by-gto-wizard/)

### 知見3: 合算防衛レンジが強くなる（防衛負担の分散）

マルチウェイでは防衛の義務が複数プレイヤーに分散されるため、各プレイヤーは非常にタイトに防衛できる。その結果、コールしてきた相手のレンジはヘッズアップよりも大幅に強くなる。

Upswing Pokerは「ベットへのコールがあった場合、コーラーのレンジはヘッズアップより著しく強い」と指摘し、KQoやAJoがマルチウェイで価値を失う理由として、「トップペアを作っても弱いハンドを過度にフォールドさせ、より強いハンドだけを残してしまう」逆選択問題を挙げている。

- 出典: [The Ultimate Guide to Preflop Multiway Pots | Upswing Poker](https://upswingpoker.com/multiway-pot-preflop-squeezing-leaks/)
- 出典: [10 Tips for Multiway Pots in Poker | GTO Wizard](https://blog.gtowizard.com/10-tips-multiway-pots-in-poker/)

### 知見4: プレイヤー数によるエクイティの急落

プレイヤー数が増えるにつれ、強いハンドのエクイティは急落する。具体的なデータは以下の通り。

**AK のエクイティ推移（対ランダムハンド）:**
- ヘッズアップ（2人）: 約65%
- 3ウェイ（3人）: 約50%
- 4ウェイ（4人）: 約40%（4ウェイではエクイティが約24.5%台まで落ちるケースも）

Upswing Pokerは「AKのエクイティは3人の相手に対して26ポイント近く低下する」と報告している。

**AA のエクイティ推移（一般的推計）:**
- ヘッズアップ: 約85%
- 3ウェイ: 約73%
- 4ウェイ: 約64%

この原則は「プレイヤーごとに約12%のエクイティ低下」という経験則として表せる（ただし対戦ハンドによって変動）。

- 出典: [When Should You Bet the Flop in Multi-Way Pots? | Upswing Poker](https://upswingpoker.com/multiway-pots-flop-bet-strategy/)
- 出典: [Poker Equity: Calculate Your Win Percentage | Pokertube](https://www.pokertube.com/article/poker-equity)

### 知見5: オフスーツブロードウェイ（AQo、KQo）がほぼ機能しない

AQoはマルチウェイポットで非常に機能しにくい手として複数のソースが一致して指摘している。

理由:
1. フラッシュ・ストレートを完成させにくく（スーツがない）、ナッツを作る頻度が低い
2. トップペアを作っても、多人数が残る状況では相対的に弱い
3. フロップからターンにかけてのエクイティ低下幅が大きい

Upswing Pokerは「**AQo should not be played in multiway pots**（AQoはマルチウェイでプレイすべきでない）」と断言している。また「AQoはヘッズアップの3ベットポットでは価値を維持するが、マルチウェイでは劣化する」とも述べており、本来の強みがヘッズアップ限定であることを示している。

同様にKQoも「トップペアを作っても逆選択が起きる」問題があり、ヘッズアップでの80%エクイティが3ウェイで60%に低下するという例示がある。

- 出典: [How to Play Ace-Queen Offsuit in Cash Games | Upswing Poker](https://upswingpoker.com/playing-ace-queen-offsuit/)
- 出典: [The Ultimate Guide to Preflop Multiway Pots | Upswing Poker](https://upswingpoker.com/multiway-pot-preflop-squeezing-leaks/)

### 知見6: 小〜中ペア・スーテッドコネクターの相対価値上昇

マルチウェイでは「**Tight is Right**（タイトが正解）」だが、相対的に価値が上がるハンドがある。

**スモールペア・ミドルペア:**
- セットヒット時は複数ストリートにわたって価値ベットが成立する
- GTO Wizardの「大ベット窓」の条件として「ナッツを保有している場合」が挙げられており、セットがその代表格
- Andrew Brokos（ポーカーコーチ）は「スモールペアはマルチウェイで文句なしに優良なハンド」と評価

**スーテッドコネクター:**
- ストレートやフラッシュ（特にナッツフラッシュ）が完成する可能性を持つ
- Brokos評: 「スーテッドコネクターは（オフスーツブロードウェイより）"less worse"（悪化の度合いが小さい）」
- 複数プレイヤーがポットに参加することで配当が増え、セットマイニング・ドロー完成時のリターンが大きくなる
- ナッツフラッシュドロー（Ace-high flushドロー）は「ナッツドロー」としてマルチウェイでの数少ない強ブラフ候補になる

- 出典: [10 Tips for Multiway Pots in Poker | GTO Wizard](https://blog.gtowizard.com/10-tips-multiway-pots-in-poker/)
- 出典: [Suited Connectors Poker Hand Guide | CoinPoker](https://coinpoker.com/guides/poker-hands/suited-connectors/)
- 出典: [Mastering Multi-Way Pots - Phil Galfond](https://www.philgalfond.com/articles/mastering-multi-way-pots)

### 知見7: ベットサイズを小さく（25〜50% ポット）

マルチウェイでの最適ベットサイズについて、複数ソースが一致して「小ベット」を推奨している。

**数値の根拠:**
- 「33%ポットベットがほとんどのマルチウェイボードで十分」（GTO Wizard/Upswing Poker）
- 33%ポットベットでは相手はそれぞれ約半分のレンジをフォールドする必要があり、最小リスクで十分なフォールドエクイティを獲得できる
- BTNは最小ベットサイズ（クォーターポット）を56.2%の頻度で使用する（GTO Wizard 3ウェイデータ）
- ポットサイズCBetはヘッズアップ18%使用 → マルチウェイ1.3%まで激減

**大ベットが有効な例外条件（GTO Wizard）:**
1. ナッツ/レンジアドバンテージが明確（セット、トップツーペアなど）
2. 最後にアクション（ポジションアドバンテージ）
3. SPRが低い状況

上記3条件が2つ以上揃う場合に60〜80%ポット程度の大ベットが正当化される。

- 出典: [Playing In Position Against Two Callers | GTO Wizard](https://blog.gtowizard.com/playing-in-position-against-two-callers/)
- 出典: [Monkey in the Middle: 3-Way Pot Heuristics | GTO Wizard](https://blog.gtowizard.com/monkey-in-the-middle-3-way-pot-heuristics/)
- 出典: [Multiway Muscle: Big-Bet Windows Revealed by GTO Wizard](https://www.poker.pro/strategy/multiway-muscle-big-bet-windows-revealed-by-gto-wizard/)
- 出典: [How to Play Multi-Way Pots At The Poker Table | PokerCoaching](https://pokercoaching.com/blog/how-to-play-multi-way-pots-at-the-poker-table/)

### 知見8: ブラフのフォールドエクイティの劇的低下

マルチウェイブラフの成功確率は乗算で計算される。例えばV1が70%フォールドし、V2が40%フォールドする場合、ブラフがポットを取る確率は 0.70 × 0.40 = **28%** にすぎない。この乗算効果により、純粋なブラフはマルチウェイで著しく非効率になる。

- 出典: [C-Betting Bluffs On Multi-Way Flops | SplitSuit Poker](https://www.splitsuit.com/betting-bluffs-multi-way-flops)

---

## 補足: 3ウェイでのポジション別変化

GTO Wizardの「Monkey in the Middle」記事によれば、3ウェイポットでの「真ん中」の位置（OOPで1人、IPで1人）では独自の問題が生じる。T♠7♥4♠のフロップでクォーターポットCBetに対応する場合、BTNのフォールド頻度はヘッズアップの約10%からマルチウェイの約31%に上昇する。これはレイズでエクイティ否定を行う動機と、第三プレイヤーの存在が重なった結果である。

- 出典: [Monkey in the Middle: 3-Way Pot Heuristics | GTO Wizard](https://blog.gtowizard.com/monkey-in-the-middle-3-way-pot-heuristics/)

---

## 本書への適用

- **第18章「マルチウェイのフロップ」** の核心理論として活用
  - CBet頻度激減（+11%チェック増、ポットサイズCBet 18% → 1.3%）を冒頭で示す
  - AKのエクイティ推移（65% → 50% → 40%程度）を図解で示す
  - AQo/KQoが機能しない理由を「逆選択問題」として説明
  - 小ペア・スーテッドコネクターの相対的優位を「ナッツポテンシャル」概念と結びつける
  - ベットサイズ原則として「33%ポットが基準、例外条件3点」を整理
  - フォールドエクイティの乗算（0.70 × 0.40 = 28%）を実戦例で示す

---

## 要確認事項

- AKのエクイティ具体数値（65%→50%→40%程度）は複数ソースの傍証から推計しており、ソルバーデータによる厳密な確認が望ましい。特に「3ウェイで50%」「4ウェイで40%」という数値はUpswing/PokerNewsの記述から導出した近似値である。
- 「プレイヤーごとに約12%エクイティ低下」は経験則であり、対戦ハンドや状況によって変動する。
