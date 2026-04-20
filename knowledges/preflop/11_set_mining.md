# 11: セットマイニング15倍ルールの理論と実践

検索日: 2026-04-19

## 概要

スモールペア（22〜66）でオープンレイズにコールしてフロップのセットを狙うプレイを「セットマイニング」という。フロップでセットが入る確率は約11.8%（7.5:1）と低いため、ポットオッズだけでは採算が取れない。インプライドオッズ（将来回収できる期待額）を加味してコールを正当化するのが15倍ルールの本質である。

本書の第4章では保守的な25倍ルールを紹介済み。第11章では実戦的な15倍ルールにフォーカスし、両者の使い分けを明確にする。

---

## 1. セットマイニングの数学

### フロップでセットが入る確率

ポケットペアを持ちフロップを見るとき、3枚のうち少なくとも1枚が同じランクである確率は以下のように計算される。

- 残り50枚のうち、同ランクのカードは2枚
- 1枚目がミスする確率: 48/50
- 2枚目がミスする確率: 47/49
- 3枚目がミスする確率: 46/48
- フロップ全体でミスする確率: (48 × 47 × 46) / (50 × 49 × 48) ≒ 88.2%
- セット以上が入る確率: 約 **11.8%（7.5:1）**

フルハウスやクワッドも含めた値であるが、実用上は「約12%」「7.5:1」と覚えればよい。

出典: [Set Mining 101: Do You Have the Right Odds to Hit Your Set? | PokerNews](https://www.pokernews.com/strategy/set-mining-101-do-you-have-the-right-odds-to-hit-your-set-35667.htm)（2024年）

### ポットオッズだけでは足りない理由

3BBオープンに対して3BBコールするとする。ポットは約7BBになり、コール額3BBに対するポットオッズは7:3 ≒ 2.3:1。これは7.5:1のオッズに到底届かない。したがってセットマイニングは「インプライドオッズ（セット完成後に追加で回収できる額）」がなければ成立しない。

出典: [Set Mining in Poker | 888poker Magazine](https://www.888poker.com/magazine/strategy/advanced/set-mining)（2023年）

---

## 2. 15倍ルールの導出

### 基本的な考え方

セットが入るのは約8回に1回（7.5:1）。残り7.5回はフロップを降りる（コール額を失う）。したがってブレイクイーブンには次の条件が必要になる。

```
コール額 × 8.5 ≦ セット完成時の回収額
```

ただしセット完成後に必ず相手のスタック全額を取れるわけではない。実戦では相手が弱いハンドでフォールドしたり、セット以外でも競りあって複数回の損失が発生する。経験則として「セット完成時に相手スタックの約60%を回収できる」と見積もると:

```
セット完成時の実際の回収額 = 相手有効スタック × 60%
```

ブレイクイーブン条件を代入すると:

```
コール額 × 8.5 = 相手スタック × 60%
相手スタック = コール額 × 8.5 / 0.6 ≒ コール額 × 14.2
```

切り上げてバッファを持たせた実用値が **15倍ルール** である。

出典: [Poker — set mining for fun and profit and the rule of 15/25/35 | Mike Fowlds, Medium](https://mikefowlds.medium.com/poker-set-mining-for-fun-and-profit-and-the-rule-of-15-25-35-bf0f8ba85eff)（2023年）; [Is Set Mining Profitable? | BlackRain79](https://www.blackrain79.com/2019/12/is-set-mining-profitable.html)（2019年）

### 15倍と25倍の違い

| ルール | 前提 | 適用場面 |
|--------|------|----------|
| **15倍ルール** | セット完成後に相手スタックの60%を回収できる（ポジションあり、ルースな相手） | インポジション、深スタック、インプライドオッズあり |
| **25倍ルール** | セット完成後に相手スタックの100%を取れる保証がない。さらにアウトオブポジションの不利を加算 | アウトオブポジション、保守的判断、相手を読みにくい状況 |

25倍ルールは「15倍より多くのバッファを持たせた保守的版」と解釈できる。アウトオブポジションだとセット完成後に相手にチェックバックされてポットが大きくならないリスクが高く、追加バッファが必要になる。

出典: [BlackRain79 - Is Set Mining Profitable?](https://www.blackrain79.com/2019/12/is-set-mining-profitable.html)（2019年）; 検索結果より「Out of position requires approximately 25x」という共通見解が複数ソースで確認。

---

## 3. 具体例

### 15倍ルール適用例

| コール額 | 必要な相手スタック（15倍） | 必要な相手スタック（25倍） |
|---------|--------------------------|--------------------------|
| 2.5BB   | 37.5BB以上               | 62.5BB以上               |
| 3BB     | 45BB以上                 | 75BB以上                 |
| 5BB     | 75BB以上                 | 125BB以上                |

実例（100NL、$1/$2）:

- 相手が$6（3BB）にオープン。有効スタック$100（50BB）。
  - 15倍チェック: $6 × 15 = $90。相手スタック$94 > $90 → コール可
  - 25倍チェック（OOPの場合）: $6 × 25 = $150。相手スタック$94 < $150 → 疑問

- 相手が$10（5BB）にオープン。有効スタック$200（100BB）。
  - 15倍チェック: $10 × 15 = $150。相手スタック$190 > $150 → コール可

- 相手が$6（3BB）にオープン。相手スタック$40（20BB）しかない。
  - 15倍チェック: $6 × 15 = $90。$34 < $90 → フォールド

出典: [Set Mining 101 | PokerNews](https://www.pokernews.com/strategy/set-mining-101-do-you-have-the-right-odds-to-hit-your-set-35667.htm); [When to Set Mine with a Pocket Pair | Natural8](https://www.natural8.com/en/blog/when-should-you-set-mine-with-a-pocket-pair)

---

## 4. セットマイニングが成立する状況

### 相手のスタックが十分に深い（100BB以上）

GTO Wizardの分析によれば、100BBでは22のセット価値が十分高く、UTGオープンレンジにも含まれる。スタックが深いほどセット完成後のインプライドオッズが大きく、コールが正当化されやすい。

出典: [How Stack Sizes Change Your Range | GTO Wizard Blog](https://blog.gtowizard.com/how-stack-sizes-change-your-range/)（2024年）

### 相手がペアやドローを過大評価するタイプ（Fish、ルースアグレッシブ）

相手がトップペア程度でスタックを入れてくる傾向があると、セット完成後の回収期待値が上昇する。ファッシュやルースプレイヤーが理想的なターゲット。

出典: [BlackRain79 - Is Set Mining Profitable?](https://www.blackrain79.com/2019/12/is-set-mining-profitable.html)（2019年）; [What is Set Mining in Poker? | Upswing Poker](https://upswingpoker.com/set-mining-poker-tips/)（2023年）

### インポジション（ボタンやカットオフ）

ポジションがあれば:
- フロップでのスチール機会（相手がチェックしたときのバレル）が増える
- 自分がアクトする前に相手の情報を得られる
- ポットコントロールが可能

これらの追加価値がインプライドオッズに上乗せされ、15倍ルールが機能しやすくなる。

出典: [What is Set Mining? | Upswing Poker](https://upswingpoker.com/set-mining-poker-tips/)（2023年）

---

## 5. セットマイニングが成立しない状況

### 相手のスタックが浅い（50BB以下）

GTO Wizardの分析では、50BBでは22はセットを狙うメリットが半減し、UTGからの開幕レンジに入らないケースが増える。30BBではUTGから33や22は完全に除外される。

計算例: 有効スタック40BB、コール3BBの場合。
- 15倍チェック: 3 × 15 = 45BB。有効スタック37BB < 45BB → 成立しない

出典: [How Stack Sizes Change Your Range | GTO Wizard Blog](https://blog.gtowizard.com/how-stack-sizes-change-your-range/)（2024年）

### タイトすぎる相手（フォールド率が高い）

相手がトップペア以上でなければフォールドするようなタイプは、セット完成時でも大きなポットを作らない。回収期待値が低下し、15倍ルールの「60%回収」前提が崩れる。

出典: [Is Set Mining Profitable? | BlackRain79](https://www.blackrain79.com/2019/12/is-set-mining-profitable.html)（2019年）; [Mailbag: Set Mining | Thinking Poker](https://www.thinkingpoker.net/2012/05/mailbag-set-mining/)（2012年）

### マルチウェイポット（3人以上）の注意点

一般に「マルチウェイはポットが大きくなりインプライドオッズが上がる」と言われるが、実際には:

- セットオーバーセットのリスクが増加する
- 相手1人から取れる額は増えないのに均等すると一人当たりが減ることがある
- スクイーズのリスクが上がる（コールしても後ろから3ベット）

マルチウェイでは77以上のペアにとどめ、22〜66のコールには慎重になる必要がある。

出典: [Set Mining in Poker | 888poker Magazine](https://www.888poker.com/magazine/strategy/advanced/set-mining)（2023年）

### アウトオブポジション（SB、BBからコール）

OOPではセット完成後にリードする必要があり、情報が少ない。相手がポットを抑えるプレイをするとインプライドオッズが下がるため、25倍ルールを適用するのが適切。

出典: [Is Set Mining Profitable? | BlackRain79](https://www.blackrain79.com/2019/12/is-set-mining-profitable.html)（2019年）

---

## 6. セット以外の価値（スプレッドされた価値）

セットマイニングを単純に「セットを狙う」だけと捉えると過小評価になる。22〜66には以下の追加価値がある。

### フロップでのコンティニュエーション機会

インポジションの場合、フロップで相手がチェックしたときに小ベットでポットを取れる。スモールペアでも「ペアがある」という強みは十分なショウダウンバリューになる。

### ストレートドロー発展の可能性

55-66程度のペアは、例えば 4-7-8 のフロップでオープンエンドストレートドローを持てることがある。こうしたボードでの二次的価値も加味する。

### ブロッカー効果

小ペアは中ロールのコネクターと組み合わさることでフロップレンジに幅を持たせ、ブロッカーとして機能する場合がある。GTOの観点では純粋なセット狙いよりもレンジ構成の一環として組み込まれる。

出典: [Set Mining Explained | PokerVIP](https://www.pokervip.com/strategy-articles/texas-hold-em-no-limit-intermediate/set-mining)（2023年）; [What is Set Mining? | Upswing Poker](https://upswingpoker.com/set-mining-poker-tips/)（2023年）

---

## 7. GTO推奨のスモールペア戦略

### ポジション別オープンレンジ（100BB、6-max）

GTO分析では、スモールペアのオープンは概ね以下の基準とされる。

| ポジション | オープン最小ペア（目安） |
|-----------|----------------------|
| UTG       | 66以上（55以下は高頻度フォールド） |
| HJ        | 55以上               |
| CO        | 33以上               |
| BTN       | 22以上（ほぼ全ペアオープン） |
| SB        | 22以上（ただし混合戦略） |

この根拠は「BTNはほぼ50%のハンドをオープンできるポジション」であり、インポジションの有利さがスモールペアのセット価値を引き上げるため。

出典: 検索結果（GTO preflop charts 2026、PokerGTOSolver.com, PokerCoaching.com 等複数ソース）; [2026 Preflop GTO Ranges | PokerGTO Solver](https://pokergtosolver.com/en/articles/preflop-gto-ranges)（2026年）

### 3ベット or フォールドの選択肢

現代GTOでは「コール vs 3ベット」の選択でコールが最適でないケースが増えている。特に:

- 相手のオープンが大きい（4BB以上）とき、スモールペアはコールEVが低くなりやすい
- スクイーズリスクがある場合（複数プレイヤーのアクション後）は3ベットかフォールドに二分される

30BB以下のショートスタックでは、GTOは22〜55をオールインにする（プッシュフォールドの観点）。

出典: [How Stack Sizes Change Your Range | GTO Wizard Blog](https://blog.gtowizard.com/how-stack-sizes-change-your-range/)（2024年）; [Poker Academy - Pocket Pairs](https://poker.academy/blog/post/how-to-play-your-pocket-pairs)（2025年）

### セットマイン目的のみのコールは許容されるか

GTO的には「純粋にセットだけ狙う」コールは過度に単純化されている。GTOが許容するスモールペアのコールには以下の要件が揃うことが前提:

1. インポジション
2. 有効スタック100BB以上
3. コール額が有効スタックの5%以下（5/10ルール）
4. 相手がバリューハンドでスタックを入れる傾向

これらが揃わない場合はフォールドまたは3ベットが優位になる。

出典: [Set Mining Explained | PokerVIP](https://www.pokervip.com/strategy-articles/texas-hold-em-no-limit-intermediate/set-mining)（2023年）; [Tips and Guidelines to Set-Mining Success | 888poker](https://www.888poker.com/magazine/strategy/advanced/set-mining)（2023年）

---

## 8. 実戦例10問

### Q1: 22 を UTG オープンに MP からコール（有効スタック100BB）

- UTGが3BBオープン、自分はMPにて22保有、100BB有効
- 15倍チェック: 3 × 15 = 45BB。有効スタック97BB > 45BB → 数学的にはコール可
- 注意点: MPはスクイーズを受けるリスクあり、後ろのプレイヤーのアクションを要確認
- **推奨: コール（ただし後ろにタイトなプレイヤーが多い場合はフォールド検討）**

### Q2: 22 を BTN オープンに BB からコール（有効スタック40BB）

- BTNが2.5BBオープン、BBで22保有、40BB有効
- 15倍チェック: 2.5 × 15 = 37.5BB。有効スタック37.5BB ≒ ちょうど境界線
- OOPを考慮すると25倍: 2.5 × 25 = 62.5BB。37.5BB < 62.5BB → 成立しない
- セット完成時にもOOPでの回収は難しい
- **推奨: フォールド（スタックが浅すぎ、OOPでセット価値が薄い）**

### Q3: 66 を CO オープンに BTN から（有効スタック100BB）

- COが2.5BBオープン、BTNで66保有、100BB有効
- 15倍チェック: 2.5 × 15 = 37.5BB。有効スタック97.5BB → 十分
- BTNはインポジション、セット以外のポストフロップ価値も高い
- GTOではBTNからCOオープンに対し66はほぼ100%コール（またはリレイズも検討）
- **推奨: コール（66は22より高く、エクイティ実現率が高い）**

### Q4: 55 を UTG オープンにコール（MP、有効スタック100BB）

- UTGが3BBオープン、MPで55保有、100BB有効
- 15倍チェック: 3 × 15 = 45BB。 → 通過
- UTGのレンジは強いため、セット完成時の回収期待値は高め
- スクイーズリスクがある
- **推奨: コール（スクイーズがなければ正当化される）**

### Q5: 33 を HJ オープンに BTN からコール（有効スタック100BB）

- HJが2.5BBオープン、BTNで33保有、100BB有効
- 15倍チェック: 2.5 × 15 = 37.5BB。 → 通過
- BTNインポジション、33はGTOでBTNからのコール候補
- **推奨: コール（ポジション有利、スタック十分）**

### Q6: 22 を BB からコール（SB から3BBオープン、有効スタック60BB）

- SBが3BBオープン、BBで22保有、60BB有効
- 15倍チェック: 3 × 15 = 45BB。60BB > 45BB → ギリギリ通過
- OOP（BB < SB）、セット完成後の回収が難しい
- 25倍チェック: 3 × 25 = 75BB。60BB < 75BB → 保守的には×
- **推奨: フォールドまたは検討（OOPかつスタックが浅め）**

### Q7: 44 を UTG オープンに対しCOからコール（有効スタック200BB）

- UTGが3BBオープン、COで44保有、200BB有効
- 15倍チェック: 3 × 15 = 45BB。200BB >> 45BB → 余裕で通過
- ディープスタックでセットの価値が最大化
- **推奨: コール（ディープスタックで価値高い）**

### Q8: 22 を3ベットポット（9BB）でコール（有効スタック100BB）

- 相手がCOから3BBオープン、BTNが9BBに3ベット、BBで22保有
- コール額9BB。15倍チェック: 9 × 15 = 135BB。有効スタック91BB < 135BB → 成立しない
- 3ベットポットでは必要スタックが跳ね上がる
- **推奨: フォールド（3ベットポットではスタックが不足）**

### Q9: 55 を BTN オープンに SB からコール（有効スタック100BB）

- BTNが2.5BBオープン、SBで55保有、100BB有効
- OOP。25倍チェック: 2.5 × 25 = 62.5BB。有効スタック97.5BB > 62.5BB → 通過
- SBはBBのスクイーズリスクも考慮
- 55はOOPでも若干のエクイティ実現価値がある
- **推奨: コール（25倍クリア、55ならOOPでも許容圏内）**

### Q10: 33 を EP オープンに対し短いスタック（40BB）でコール（MP）

- EPが3BBオープン、MPで33保有、40BB有効
- 15倍チェック: 3 × 15 = 45BB。有効スタック37BB < 45BB → 成立しない
- **推奨: フォールド（スタックが15倍に満たない）**

---

## 9. 25倍ルール（第4章）との整合性

第4章で紹介した25倍ルールは、次のような前提に基づく保守的ルール:

- アウトオブポジションを想定
- インプライドオッズが完全に実現しない（100%回収できない）ケースに備えた安全マージン
- 初心者・中級者が「コールしすぎ」を防ぐための目安

対して第11章の15倍ルールは:

- インポジションを前提とした実戦的ルール
- セット完成後に60%程度の回収を見込む現実的な計算
- 上級者やディープスタックの状況で精度を上げるための目安

どちらが「正しい」ではなく、状況に応じて使い分けるのが実戦では重要。

| 状況 | 推奨ルール |
|------|---------|
| BTN/COからのコール（IP） | 15倍ルール |
| BB/SBからのコール（OOP） | 25倍ルール |
| 不明・保守的に判断したい | 25倍ルール |
| ディープスタック（150BB以上） | 15倍でも余裕あり |

---

## 本書への適用

- **第4章（ポジションと基本戦略）**: 25倍ルールを紹介済みの流れで「25倍はOOPの安全基準」と位置付け
- **第11章（セットマイニング15倍ルール）**: インプライドオッズの計算過程、15倍の数学的導出、実戦例10問、GTOとの整合性を詳述
- **付録**: ポジション×スタック別「セットマイニング可否一覧表」を掲載

---

## 参考URL一覧

- [Poker — set mining for fun and profit and the rule of 15/25/35 | Mike Fowlds, Medium](https://mikefowlds.medium.com/poker-set-mining-for-fun-and-profit-and-the-rule-of-15-25-35-bf0f8ba85eff)（2023年）
- [Is Set Mining Profitable? Yes, But You Need to Do This | BlackRain79](https://www.blackrain79.com/2019/12/is-set-mining-profitable.html)（2019年）
- [What is Set Mining in Poker? And When Should You Set Mine? | Upswing Poker](https://upswingpoker.com/set-mining-poker-tips/)（2023年）
- [Set Mining 101: Do You Have the Right Odds to Hit Your Set? | PokerNews](https://www.pokernews.com/strategy/set-mining-101-do-you-have-the-right-odds-to-hit-your-set-35667.htm)（2024年）
- [Set Mining with Small-to-Medium Pocket Pairs | PokerNews](https://www.pokernews.com/strategy/set-mining-with-small-to-medium-pocket-pairs-19696.htm)（2022年）
- [Set Mining in Poker | 888poker Magazine](https://www.888poker.com/magazine/strategy/advanced/set-mining)（2023年）
- [Tips and Guidelines to Set-Mining Success | 888poker](https://www.888poker.com/magazine/strategy/advanced/set-mining)（2023年）
- [Set Mining Explained | PokerVIP](https://www.pokervip.com/strategy-articles/texas-hold-em-no-limit-intermediate/set-mining)（2023年）
- [When to Set Mine with a Pocket Pair | Natural8](https://www.natural8.com/en/blog/when-should-you-set-mine-with-a-pocket-pair)（2023年）
- [Mailbag: Set Mining | Thinking Poker](https://www.thinkingpoker.net/2012/05/mailbag-set-mining/)（2012年）
- [Visualizing implied odds | GTO Wizard Blog](https://blog.gtowizard.com/visualizing-implied-odds/)（2024年）
- [How Stack Sizes Change Your Range | GTO Wizard Blog](https://blog.gtowizard.com/how-stack-sizes-change-your-range/)（2024年）
- [2026 Preflop GTO Ranges | PokerGTO Solver](https://pokergtosolver.com/en/articles/preflop-gto-ranges)（2026年）
- [Small Pocket Pair Preflop Strategy In 2026 | SplitSuit](https://www.splitsuit.com/small-pocket-pair-strategy)（2026年）
- [The Science of Set Mining | Americas Cardroom](https://www.acrpoker.eu/how-to/poker-strategy/advanced/the-science-of-set-mining-when-to-play-small-pocket-pairs-in-texas-holdem/)（2023年）
- [スモールペアのインプライドオッズ | 木原直哉オフィシャルブログ](https://kihara-poker.hatenablog.com/entry/2018/04/16/165210)（2018年）
