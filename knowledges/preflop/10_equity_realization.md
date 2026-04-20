# 10: 実現率という落とし穴

検索日: 2026-04-19

---

## 1. 実現率とは何か

### 定義と数式

実現率（Equity Realization, EQR）は、生エクイティ（ハンドが持つ生の勝率）が実際のEVにどの程度変換されるかを示す比率である。

```
EQR = 実際のポットシェア（EV） / (ポット × 生エクイティ)
```

言い換えると「ポットオッズ上は有利でも、実際にそのエクイティを全部取れるか？」という問いに答える指標である。EQR > 1.0 の場合は「over-realize（超過実現）」、EQR < 1.0 の場合は「under-realize（未達）」となる。

- 出典: [Equity Realization | GTO Wizard](https://blog.gtowizard.com/equity-realization/)
- 出典: [Equity Realization (EQR) – GTO Wizard Glossary](https://pages.gtowizard.com/glossary/equity-realization-eqr/)

### 直感的な説明

「生エクイティ」はチェックダウン（ノーベット）で全てのストリートを流した場合の勝率である。しかし実際のポーカーではベット・フォールドが発生し、特にOOPでは相手に押し付けられて折らされる機会が多い。

具体例：PIOSolverの分析で、9♠-3♠-2♦ フロップにおいてBBのレンジエクイティは46.5%。全員チェックダウンなら46.5%のポットを回収できるが、GTOプレイでは実際のEVは36.8%のポットシェアにとどまった。このギャップ（46.5% → 36.8%）がOOPにおける実現率低下の例である。

- 出典: [What is Equity Realization & How Does it Impact Strategy - Upswing Poker](https://upswingpoker.com/equity-realization-explained/)

### 本書での「実効勝率」への変換

```
実効勝率 = 生勝率 × 実現率（EQR）
```

この公式をプリフロップ判断の文脈で使うために、本書では以下の近似値を採用する。

| ポジション | EQR近似値 | 根拠 |
|-----------|-----------|------|
| IP（ポジション持ち） | 1.0 | 超過実現が期待できる場面も多く、平均的に1.0前後 |
| OOP（ポジションなし） | 0.6〜0.8 | ディープスタック時は0.6まで下がることもある |

---

## 2. 具体的な実現率データ

### ポジション別の実現率

GTO Wizardの集計レポートでは、BTN vs BB の一発コールポット（SRP）において以下のデータが確認されている。

- **BTN（IP）**: EQR ≈ 118%（生エクイティを超えてポットを回収する）
- **BB（OOP）**: EQR ≈ 79%（生エクイティの79%しか回収できない）

この数値は本書第2章でも参照済み。再確認として：BTNがIPであることによる情報優位・ポジション優位が、生エクイティを超えるEVを生み出す。

- 出典: [Aggregate Reports | GTO Wizard Help](https://help.gtowizard.com/aggregate-reports-guide/)
- 出典: [Equity Realization | GTO Wizard](https://blog.gtowizard.com/equity-realization/)

### SB（スモールブラインド）の実現率

SBはOOPかつレンジが弱い（3-betかフォールドが多いため）という二重の不利を抱える。一般的にSBのEQRはBBより低く、35〜60%という範囲が実務的な参照値として使われる。

理由：
1. SBはポストフロップでBTN・BBの両者にIPをとられる
2. SBのコールレンジは相手からすると「3-betしなかった弱いハンド」と見抜かれやすい（キャップされたレンジ）
3. 結果、継続ベットを打ちにくく、フォールドを余儀なくされる場面が多い

- 出典: [Equity Realization | GTO Wizard](https://blog.gtowizard.com/equity-realization/)
- 出典: [What is Equity Realization & How Does it Impact Strategy - Upswing Poker](https://upswingpoker.com/equity-realization-explained/)

### ハンドタイプ別の実現率傾向

| ハンドタイプ | EQR傾向 | 理由 |
|------------|---------|------|
| スーテッドコネクター（65s等） | 高い（100%超も） | フロップヒット率が高く、ドロー・ストレート・フラッシュで多様な継続が可能 |
| スーテッドエース（A5s等） | 高い | ナッツフラッシュドロー・ペア・ブラフの三役をこなせる |
| オフスーツブロードウェイ（KJo等） | 低い | フロップで弱いペアしか作れず、継続が難しい。ドロー力も低い |
| 弱いオフスーツコネクター（73o等） | 非常に低い | エクイティも実現率も両方低い |
| ポケットペア（77等） | スタック依存 | セットを引けばEQR高、外れれば低。期待値はインプライドオッズ次第 |

具体的データ：76sはフロップをヒットする確率が62.4%（76oは55.9%）。スーテッド性が6.5ポイントの差を生む。

- 出典: [Beyond Raw Equity: Unlocking the True Value of Your Poker Hands - Upswing Poker](https://upswingpoker.com/raw-equity-vs-realized-equity/)
- 出典: [What is Equity Realization & How Does it Impact Strategy - Upswing Poker](https://upswingpoker.com/equity-realization-explained/)

---

## 3. 本書での近似の妥当性

### OOP時 EQR ≈ 0.6 の根拠

「OOP × ディープスタック × 低プレイアビリティ」の組み合わせでは、EQRが60%程度まで落ちうるというのはソルバーデータと一致する。

Upswing Pokerの記述：「OOPで、高SPR（ディープスタック）で、プレイアビリティが低いハンドを持っている場合、最初の推定価値の62%程度しか実現できないことがある」。

これを丸めて「OOP時は0.6を掛ける」とするのは保守的かつ実用的な近似といえる。

ただし注意点：
- BBはOOPだが、スーテッドコネクターなどは0.7〜0.8程度の実現が見込める
- IPでも、キャップされたレンジ（コールのみ等）では1.0を下回ることもある
- スタックが浅くなるほど（SPRが低いほど）ポジションの差は縮まる

- 出典: [What is Equity Realization & How Does it Impact Strategy - Upswing Poker](https://upswingpoker.com/equity-realization-explained/)

### IP時 EQR ≈ 1.0 の根拠

BTNのEQR 118%というデータは「IPでは生エクイティを超えることもある」ことを示す。しかし全てのIPシチュエーションが118%ではなく、平均すると1.0前後に収まることが多い。よって「IPは約1.0」という近似は妥当である。

- 出典: [Equity Realization | GTO Wizard](https://blog.gtowizard.com/equity-realization/)

### 近似が使える範囲

| 条件 | 近似精度 |
|------|---------|
| BB vs BTN SRP、100bbスタック | 高い（最も分析データが豊富） |
| SB vs BTN SRP | やや低い（SBは0.6よりさらに低い場合あり） |
| マルチウェイポット | 低い（別途調整が必要） |
| 50bb以下のショートスタック | 低い（ポジション差が縮まる） |

---

## 4. 実現率が低下する具体的条件

### 条件1: OOP（ポジションなし）

最大の要因。OOPでは毎ストリート先にアクションを強いられ、相手は完全な情報を得た上でリスポンスできる。ブラフで折られやすく、バリューを取りにくい。

### 条件2: キャップされたレンジ（Capped Range）

3-betせずコールした場合、相手からは「プレミアムハンドはない」と見透かされる。BTNがBBにコールされた場合のBBは典型例。相手が積極的に攻めてくる状況で、弱いレンジは折りやすい。

- 出典: [Equity Realization | GTO Wizard](https://blog.gtowizard.com/equity-realization/)

### 条件3: 低プレイアビリティハンド

- オフスーツブロードウェイ（KJo、QTo等）：フロップで弱いトップペアや弱いセカンドペアしか作れない。継続困難。ドロー力も皆無。
- 弱いペア：フロップで上を踏まれやすく、コンティニュエーションベットを受け止める手段が少ない。

### 条件4: マルチウェイポット

参加者が増えると、個人のエクイティは薄まる上に、より強いレンジのプレイヤーが存在する確率が上がる。ブラフのリターンが下がり、バリューのしきい値が上がる。

GTO Wizardの記述：「大半のハンドはマルチウェイに行くと価値を失う」。オフスーツの非コネクターハンドは特に打撃を受ける。

- 出典: [7 Multiway Tactics You Should Know Going Into 2022 - Upswing Poker](https://upswingpoker.com/multiway-pot-concepts/)
- 出典: [10 Tips for Multiway Pots in Poker | GTO Wizard](https://blog.gtowizard.com/10-tips-multiway-pots-in-poker/)

### 条件5: ディープスタック

SPRが高くなるほど（スタックが深いほど）、ポストフロップでの意思決定ツリーが長くなり、IPプレイヤーの情報優位が複利的に積み上がる。結果としてOOPのEQRは低下する。

- 出典: [What is Equity Realization & How Does it Impact Strategy - Upswing Poker](https://upswingpoker.com/equity-realization-explained/)

---

## 5. 実現率が高まる具体的条件

### 条件1: IP（ポジション持ち）

毎ストリート最後にアクションするため、情報を最大限活用できる。ブラフの成功率も上がり、バリューも取りやすい。

### 条件2: アンクローズドレンジ（Uncapped Range）

3-betした場合など、相手が広くディフェンスしなければならない状況。相手のレンジが広がるほど、こちらの強いハンドが相対的に価値を増し、ブラフも通りやすい。

### 条件3: ナッツポテンシャルのあるハンド

- **スーテッドコネクター（65s, 87s等）**: ストレート・フラッシュドロー・コンボドローと多様な継続手段がある。フロップでの投資を正当化しやすい。
- **スーテッドエース（A5s, A2s等）**: ナッツフラッシュドロー＋ペア＋ブラフコンボとして機能。バックドアドロー込みで多くのフロップで継続可能。

GTO Wizardの例：6♥3♥は43%のエクイティを持ちつつ、EQRが90%超を実現できる。ナッツポテンシャルとスーテッド性がEQRを押し上げている。

- 出典: [Equity Realization | GTO Wizard](https://blog.gtowizard.com/equity-realization/)
- 出典: [Beyond Raw Equity: Unlocking the True Value of Your Poker Hands - Upswing Poker](https://upswingpoker.com/raw-equity-vs-realized-equity/)

### 条件4: スキルエッジがある場合

OOPでも高度なポストフロップスキルがあれば、EQRは改善する。逆にスキルが低いうちは、OOPでの実現率をより保守的に見積もるべきである。

- 出典: [How to understand equity realization (EQR)? | Poker Academy](https://poker.academy/blog/post/how-to-understand-equity-realisation-eqr)

---

## 6. BBディフェンスの罠

### BBが陥りやすい「ポットオッズの罠」

BBはすでに1bb投入済みなので、BTNの2.5bb オープンに対するポットオッズは非常に良い。計算上は約27%のエクイティがあれば損益分岐点となる。

**ポットオッズだけの計算では：**
- 72o の対BTNレンジエクイティ ≈ 30%
- 27%のしきい値を超えるため「コールできる」と判断してしまう

**しかし実際には：**
- 72oはOOPでのプレイアビリティが極めて低い
- フロップでヒットするパターンが限られ、ほとんどのフロップでフォールドを余儀なくされる
- 実効勝率 = 30% × 0.6（OOP EQR） ≈ 18% となり、ポットオッズを満たさない

この「生エクイティでは呼べるのに、実効勝率では呼べない」という落差がBBディフェンスの最大の罠。

- 出典: [Equity Realization | GTO Wizard](https://blog.gtowizard.com/equity-realization/)
- 出典: [BB defense strategy - Upswing Poker](https://upswingpoker.com/equity-realization-explained/)

### BBの正しいディフェンス基準

GTOのBBディフェンスでは、単純なポットオッズではなく以下を考慮する：

1. **スーテッド・コネクティビティを優先**: 72oよりも54sの方がEQRが高い
2. **オフスーツブロードウェイの下限を上げる**: KJoはコール可能だが、Q7oは危険
3. **マルチウェイ時は絞る**: ポットオッズが改善しても、OOPかつマルチウェイのEQR低下がそれを上回る

GTO Wizardの分析：BBはマルチウェイポット（コーラーが増えるほど）でポットオッズが改善するにも関わらず、実際にはコール頻度を下げ、フォールドを増やす傾向がある。これはEQRの低下がポットオッズの改善を相殺するためである。

- 出典: [Overcalling From the BB | GTO Wizard](https://blog.gtowizard.com/overcalling-from-the-bb/)
- 出典: [Mastering Big Blind Strategy: A Guide to Profitable Defence - PokerCoaching](https://pokercoaching.com/blog/mastering-big-blind-strategy-a-guide-to-profitable-defence/)

### BBのディフェンスレンジの考え方

BTNの2.5bb オープンに対してBBが直面するポットオッズ：
- 必要エクイティ = 1.5 / (1.5 + 3.5) = 27.3%（生エクイティ基準）
- OOP調整後 = 27.3% / 0.75（EQR 75% 想定） ≈ 36.4%（実効エクイティ基準）

この調整後のしきい値でフィルタリングすると、72oや63oはディフェンス不可と判断できる。

---

## 7. 具体例

### 例1: A9o を BTN オープンに BB からコール

- **生エクイティ**: A9o は BTNレンジ（約25%）に対して約52%のエクイティを持つ
- **実現率**: BBとしてOOP ≈ 0.75（A9oはオフスーツで中程度のプレイアビリティ）
- **実効勝率**: 52% × 0.75 ≈ 39%
- **ポットオッズ要求**: 約27%（2.5bbオープンに対して）
- **判断**: 実効勝率（39%）はポットオッズ（27%）を超えるため数値上はコール可能だが、継続ストリートでの判断が難しくなる。フロップでトップペア（Aヒット）以外のほとんどのボードでチェックフォールドを余儀なくされる。

対照的に、BTN側からA9oでオープンした場合はEQR ≈ 1.1以上になり、大きくプラスの期待値が出る。**ポジションによって同じハンドの価値が180度変わる**。

### 例2: 65s を BTN オープンに BB からコール

- **生エクイティ**: 65s は BTNレンジに対して約43〜45%のエクイティ（A9oより低い）
- **実現率**: OOPだが、スーテッドコネクターのため ≈ 0.85〜0.90
- **実効勝率**: 44% × 0.87 ≈ 38%
- **フロップでの継続力**: ストレートドロー、フラッシュドロー、コンボドローと多様な継続手段がある
- **判断**: 生エクイティはA9oより低いが、実効勝率はほぼ同等。かつフロップでの継続判断が容易でEVの振れ幅が小さい。

**要点**: 生エクイティが高くても、実現率が低いと期待値はマイナスになりうる。65sはA9oと生エクイティはほぼ同程度の実現価値を持ちながら、プレイの難易度が低く初心者に有利。

- 出典: [Equity Realization | GTO Wizard](https://blog.gtowizard.com/equity-realization/)
- 出典: [Beyond Raw Equity: Unlocking the True Value of Your Poker Hands - Upswing Poker](https://upswingpoker.com/raw-equity-vs-realized-equity/)

### 例3: 77 を UTG オープンに BB からコール（セットマイニング）

- **生エクイティ**: 77 対 UTGレンジ（約13%） ≈ 46〜50%
- **セット確率**: フロップで約11.8%（8回に1回）
- **セットマイニングEV計算の前提**: OOPでセットを引いた時のインプライドオッズが重要

セットマイニングが成立するための条件：
1. スタックが十分深い（100bb以上が望ましい）
2. 相手が強いハンドをオーバーバリューしてスタックを失う可能性がある
3. 自分がOOPであっても、セットのナッツハンドはEQRが高い（1.0以上）

**OOP × セット以外の場合**: UTGレンジはナローで強く、77がセット以外でエクイティを実現するのは困難。フロップでオーバーカードが出ると継続できない。

セットマイニングの損益分岐（目安）：コール額 × 15 ≦ 期待インプライドオッズ。100bbスタックで3bb コールなら 3bb × 15 = 45bb 以上のインプライドオッズが必要。

- 出典: [What is Set Mining in Poker? And When Should You Set Mine? - Upswing Poker](https://upswingpoker.com/set-mining-poker-tips/)
- 出典: [Visualizing implied odds | GTO Wizard](https://blog.gtowizard.com/visualizing-implied-odds/)

---

## 8. 実戦での実現率調整方法

### OOP時のコールラインの引き上げ

ポットオッズだけで計算したしきい値をEQRで調整することで、実効的な損益分岐を求められる。

```
調整後しきい値 = ポットオッズ要求エクイティ / EQR
```

例：BTNオープン2.5bbにBBがコールする場合
- ポットオッズ要求: 1.5 / 5.0 = 30%（生エクイティ）
- OOP EQR = 0.75 想定
- 調整後: 30% / 0.75 = 40%（実効エクイティ要求）

つまり、実際には40%以上の生エクイティが必要という基準になる。これはコールラインを5〜7%上げることに相当する。

### マルチウェイ時の調整

参加者が増えるほど：
1. 個人の直接エクイティは低下する
2. OOPでのEQRもさらに低下する（継続できるフロップが減る）
3. ハンド選択は「スーテッド×コネクテッド」に絞るべき

具体的には、3ウェイポットではOOP側のEQRを0.55〜0.65と見積もるのが適切。

- 出典: [Defending The Big Blind In Multi-Way Pots - PokerCoaching](https://pokercoaching.com/blog/defending-the-big-blind-multiway/)

### ブロッカー効果との相互作用

ブロッカー（相手の強いコンボをブロックするカード）を持つハンドはEQRが高くなる。例えば：
- Aを1枚持つ（A7o等）: 相手のAAやAKをブロックしており、フォールドを取りやすい
- 5を持つ（A5s等）: ホイールストレートをブロックしており、ナッツ阻害の価値がある

ただし、ブロッカー効果は中級〜上級の概念であり、本書の第10章では「ハンドのプレイアビリティ」という大枠の説明にとどめ、詳細はブロッカー専門章に委ねる。

---

## 本書への適用

### 第10章での活用ポイント

1. **「生エクイティ × 実現率 = 実効勝率」**という公式を早期に提示し、以後の章の基礎にする
2. **OOP ≈ 0.6〜0.8、IP ≈ 1.0** という近似値を「実用ツール」として読者に提供する
3. **72oのBBコール例** を使って「ポットオッズの罠」を示す
4. **65s vs A9o の比較** で「生エクイティより実現率が重要」を直感的に示す
5. セットマイニング（77のUTGコール例）で「インプライドオッズ × 実現率」の複合判断を紹介する

### 第9章（ポットオッズ）からの橋渡し

第9章で「ポットオッズ ≥ 生エクイティ → コール」という基本ルールを提示した後、第10章では「それだけでは不十分」という反例を示すことで読者の思考を深める。

この章の結論：**「どれだけ勝てるか（生エクイティ）ではなく、どれだけ取り切れるか（実効勝率）で判断せよ」**

---

## 参考URL一覧

- [Equity Realization | GTO Wizard](https://blog.gtowizard.com/equity-realization/) （主要参照）
- [Equity Realization (EQR) – GTO Wizard Glossary](https://pages.gtowizard.com/glossary/equity-realization-eqr/)
- [What is Equity Realization & How Does it Impact Strategy - Upswing Poker](https://upswingpoker.com/equity-realization-explained/)
- [Beyond Raw Equity: Unlocking the True Value of Your Poker Hands - Upswing Poker](https://upswingpoker.com/raw-equity-vs-realized-equity/)
- [Equity Realization | Red Chip Poker](https://redchippoker.com/equity-realization/)
- [How to understand equity realization (EQR)? | Poker Academy](https://poker.academy/blog/post/how-to-understand-equity-realisation-eqr)
- [Overcalling From the BB | GTO Wizard](https://blog.gtowizard.com/overcalling-from-the-bb/)
- [Mastering Big Blind Strategy: A Guide to Profitable Defence - PokerCoaching](https://pokercoaching.com/blog/mastering-big-blind-strategy-a-guide-to-profitable-defence/)
- [Defending The Big Blind In Multi-Way Pots - PokerCoaching](https://pokercoaching.com/blog/defending-the-big-blind-multiway/)
- [7 Multiway Tactics You Should Know Going Into 2022 - Upswing Poker](https://upswingpoker.com/multiway-pot-concepts/)
- [10 Tips for Multiway Pots in Poker | GTO Wizard](https://blog.gtowizard.com/10-tips-multiway-pots-in-poker/)
- [What is Set Mining in Poker? - Upswing Poker](https://upswingpoker.com/set-mining-poker-tips/)
- [Visualizing implied odds | GTO Wizard](https://blog.gtowizard.com/visualizing-implied-odds/)
- [Aggregate Reports | GTO Wizard Help](https://help.gtowizard.com/aggregate-reports-guide/)
- [Pot Odds, Equity, and Equity Realization in Poker — Steemit](https://steemit.com/gaming/@obliopoker/pot-odds-equity-and-equity-realization-in-poker)
- [Equity Realization - Playing From The Big Blind | PokerNerve](https://pokernerve.com/equity-realization/)
