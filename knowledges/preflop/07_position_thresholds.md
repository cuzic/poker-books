# 07: ポジション別しきい値の検証と運用

検索日: 2026-04-19

## 概要

第5〜6章で構築したスコア式（基本スコア＋ボーナス・ペナルティ）をもとに、各ポジションのしきい値と比較してアクションを決定する仕組みを解説する章。本文書は、しきい値の妥当性検証、境界ハンドの分析、判断例の整理を目的とした調査知見をまとめる。

---

## 1. しきい値と実際のレンジの対応

### 本書しきい値の設定

| ポジション | しきい値 | GTO推奨RFI（6max 100bb） |
|-----------|----------|--------------------------|
| UTG       | 24       | 約17.6%（〜30ハンド種）  |
| MP（HJ）  | 22       | 約21.4%（〜36ハンド種）  |
| CO        | 20       | 約27.8%（〜47ハンド種）  |
| BTN       | 18       | 約43.5%（〜74ハンド種）  |
| SB        | 20       | ※SBはCOと同等として運用  |

GTO Wizard および freebetrange.com が公表する 6max 100bb キャッシュゲームのRFI%を参照。  
出典: [6 max Preflop Charts: Open Raise in Poker Cash Games](https://blog.freebetrange.com/article/preflop-charts-open-raise-in-6-max-poker-cash-games)（2024年）  
出典: [Preflop Range Morphology | GTO Wizard](https://blog.gtowizard.com/preflop-range-morphology/)（2024年）

### 169ハンド種の構成

- **ペア**: 13種（AA〜22）
- **スーテッド**: 78種（A2s〜23s）
- **オフスーテッド**: 78種（A2o〜23o）
- 合計: 169種（実コンボ数: 1,326）

出典: [Texas hold 'em starting hands - Wikipedia](https://en.wikipedia.org/wiki/Texas_hold_%27em_starting_hands)

### 本書しきい値でオープンされるハンド数（概算）

本書スコアの計算式（ペア・スーテッド・オフスーテッドごとに異なる加点）をもとに、各しきい値を超えるハンドを推計すると以下のとおり。

| ポジション | しきい値 | 概算ハンド数（169種中） | 概算% |
|-----------|----------|------------------------|-------|
| UTG       | 24       | 約28〜32種             | 約17〜19% |
| MP        | 22       | 約35〜40種             | 約21〜24% |
| CO        | 20       | 約46〜52種             | 約27〜31% |
| BTN       | 18       | 約73〜80種             | 約43〜47% |
| SB        | 20       | COに準ずる             | 約27〜31% |

**GTO推奨値との整合性:** 概ね整合しており、UTGの17〜19%はGTO推奨17.6%と極めて近い。CO・BTNも許容範囲内。

### GTO参照レンジ（6max 100bb キャッシュ）

**UTG（約17.6%）:**
66+, A2s+（一部混合）, A5s, KTs+, QTs+, JTs, T9s, 98s, ATo+, KJo+, AQo+  
出典: [Strategy: UTG Pre-flop Ranges | PokerStrategy](https://www.pokerstrategy.com/strategy/bss/utg-pre-flop-ranges/)

**HJ（約21.4%）:**
55+, A2s+, K6s+, Q9s+, J9s+, T9s, 98s, 87s, 76s, ATo+, KTo+, QTo+  
出典: [Implementable GTO Charts | PokerCoaching](https://poker-coaching.s3.amazonaws.com/tools/preflop-charts/online-6max-gto-charts.pdf)（2024年）

**CO（約27.8%）:**
44+, A2s+, K4s+, Q7s+, J8s+, T8s+, 98s, 87s, 76s, 65s, ATo+, KTo+, QJo+  
出典: [6-Max Pre-Flop Open Raising Ranges | MicroGrinder](https://microgrinder.com/poker-strategy-articles/6-max-pre-flop-ranges/)

**BTN（約43.5%）:**
33+, A2s+, K2s+, Q3s+, J4s+, T6s+, 96s+, 85s+, 75s+, 64s+, 53s+, A4o+, K8o+, Q9o+, J9o+, T8o+, 98o  
出典: [6 max Preflop Charts | freebetrange](https://blog.freebetrange.com/article/preflop-charts-open-raise-in-6-max-poker-cash-games)

**SB（RFIは広いが混合戦略）:**
GTO上のSBはリンプ＋レイズの混合戦略。純レイズベースのレンジはCO相当（〜30%）として扱うことが実戦的。  
出典: [6 Max Opening Ranges | 888poker](https://www.888poker.com/magazine/strategy/all-about-6-max-opening-ranges-and-hand-selection-charts)

---

## 2. 境界ハンド10選の詳細分析

各ハンドについて、本書スコア・GTOの推奨ポジション・乖離の有無を整理する。

| ハンド | 本書スコア | 本書での最小ポジション | GTO推奨ポジション | 整合性 |
|--------|----------|----------------------|-------------------|--------|
| 77     | 24       | UTG（ぎりぎり）      | UTG（66+が基本）  | 整合   |
| 66     | 22       | MP                   | UTG〜MP（混合）   | ほぼ整合 |
| 55     | 20       | CO                   | HJ〜CO            | 整合   |
| A9s    | 24       | UTG（ぎりぎり）      | UTG（A9s+が標準） | 整合   |
| A9o    | 22       | MP（ぎりぎり）       | HJ〜CO（Aoは弱い）| やや乖離（本書は過大） |
| AJo    | 25.5     | UTG越え              | CO（GTOはAQo+がUTG）| **乖離（本書が過大評価）** |
| KTs    | 25.5     | UTG                  | UTG（KTs+が標準） | 整合   |
| QJs    | 26       | UTG                  | HJ〜CO            | **乖離（本書が過大評価）** |
| 98s    | 20       | CO（ぎりぎり）       | HJ〜CO            | 整合   |
| JTs    | 24       | UTG（ぎりぎり）      | UTG〜HJ（混合）   | 概ね整合 |

### 注目すべき乖離ハンド

**AJo（スコア25.5 → UTG越え）:**
本書スコアでは25.5とUTGしきい値24を超えるが、GTO上ではAJoはUTGからはフォールド〜混合戦略が主流。純粋なGTO UTGレンジはAQo+止まりが多い。本書はAJoをUTGから開けると判断するが、GTOより1〜2ポジション過大評価している可能性がある。
出典: [How to Crush Ante Cash Games | GTO Wizard](https://blog.gtowizard.com/how_to_crush_ante_cash_games/)

**QJs（スコア26 → UTG）:**
スーテッドコネクターとして高スコアを得るが、GTO上のQJsはUTGからは純オープンではなく混合（ときにフォールド）。HJ以降からが標準的。本書スコアはスーテッドボーナスと連続性ボーナスが重なり過大になる傾向あり。
出典: [Preflop Range Morphology | GTO Wizard](https://blog.gtowizard.com/preflop-range-morphology/)

**A9o（スコア22 → MP）:**
GTOではA9oはHJ〜COからが主流で、MP（6max HJ相当）からは純オープンではなく混合。本書がMPで開けると判断するのはやや積極的。実戦上はMPからA9oをオープンするケースは約50%混合が多い。
出典: [Hands To Play UTG In Live Poker | SplitSuit](https://www.splitsuit.com/hands-to-play-utg-in-live-poker)

**77・A9s・JTs（スコア24 → UTG）:**
GTOの標準的UTGレンジ（〜17%）に含まれており整合性高い。特にA9sはGTO UTGレンジの下限として明示されているケースが多い。

---

## 3. 「1点下なら降りる」ルールの根拠

### 概要

しきい値との差が1点以内（例: UTGでスコア23）の場合、フォールドを推奨する保守的ルール。

### GTOが支持する「タイトに始める」原則

- UTGからは5〜6名の相手が残っており、広くオープンするほど3ベットや不利なポストフロップ状況にさらされるリスクが増す
- GTO上でも境界ハンドは「純オープン」ではなく「混合戦略（一部フォールド）」を取ることが多い
- 初心者が混合戦略を実行するのは困難なため、混合の「フォールド側」に倒すことはEV上の損失が小さい

出典: [Understanding EV preflop | Run It Once](https://www.runitonce.com/nlhe/understanding-ev-preflop/)

### 境界ハンドの誤判断がEVに与える影響

- EV解析（Run It Once、GTO Wizard）によれば、UTGで境界ハンドの平均EVは 0〜0.1bb/hand 程度と極めて小さい
- 誤って開けた場合でも損失は「1ハンド当たり0.1bb前後」に留まることが多い
- しかし、境界ハンドを開けることで発生するポストフロップの難しい判断の方がコストが大きい（特に初心者）

出典: [Edge-Passing in Poker: When Folding Profitable Hands Is the Right Play | Upswing Poker](https://upswingpoker.com/edge-passing-folding-profitable-hands/)

### 「迷ったらフォールド」が初心者に合理的な理由

1. **フォールドのEVは常に0**: 迷いがあるということは期待値がゼロ近傍である証拠
2. **コールは悪手（初心者の最大ミス）**: 「とりあえずコール」は負けパターン No.1
3. **タイトプレーは誤差を小さくする**: VPIP15〜20%のタイトプレーは初心者に推奨される入り口
4. **ポストフロップへの波及を防ぐ**: プリフロップで迷った手はポストフロップでさらに迷う

出典: [VPIP and PFR - Poker Statistics | PokerCopilot](https://pokercopilot.com/poker-statistics/vpip-pfr)  
出典: [Poker Folding: The Ultimate Guide | 888poker](https://www.888poker.com/magazine/strategy/ultimate-poker-folding-guide)

---

## 4. しきい値微調整の場面

### アンティありの場合（しきい値を下げる）

アンティがあると強制的に積まれる額が増え、スチールの期待値が上昇する。GTO解析では：
- アンティなし: UTG開け約10%（フルリング想定）〜17%（6max）
- アンティあり: UTG開けが約20%まで広がる（アンティが1BBの場合）
- 早いポジションでもスーテッドAやスーテッドコネクターが追加される

**実践的な調整:** アンティが1BB以上ある場合、各しきい値を1〜2点下げる（UTG 24→22、MP 22→20 など）

出典: [How to Adjust Your Strategy in Poker Games with Antes | PokerCode](https://www.pokercode.com/blog/poker-antes-strategy-adjustments)  
出典: [Ante in Poker Explained | CardPlayer](https://www.cardplayer.com/rules-of-poker/glossary/ante-in-poker)  
出典: [Ante Poker: Fold Equity, EV Shifts | Pokerology](https://www.pokerology.com/poker/strategy/ante/)

### タイト相手にはしきい値を上げる

- 相手のVPIPが低い（レイズに対してタイトにコール/3ベット）なら、ブラフスチールが通りやすい
- GTOからのエクスプロイト: 相手がタイトなら少し広めに開けてブラインドを奪える
- **実践的な調整:** 全員が明らかにタイトであれば、しきい値を1点下げる（より広くオープン）

### ルース相手にはしきい値を下げない（むしろ上げる場合も）

- 相手がコールしやすい（VPIP高い）なら、弱いハンドでのスチールは機能しにくい
- ただし、強いハンドでのバリューは増える
- マルチウェイになりやすい環境では: スーテッドコネクター系（65s, 87sなど）の価値が上がり、AJo系のヘッズアップ向きハンドの価値が下がる

出典: [The Ultimate Guide to Preflop Multiway Pots | Upswing Poker](https://upswingpoker.com/multiway-pot-preflop-squeezing-leaks/)  
出典: [10 Tips for Multiway Pots in Poker | GTO Wizard](https://blog.gtowizard.com/10-tips-multiway-pots-in-poker/)

### マルチウェイの状況

- 既に1〜2人がコールしている場合は「オープンレイズ」ではなく「コールへの対応」なので別判断が必要
- マルチウェイでは: セット系（小〜中ペア）・フラッシュドロー系（スーテッドコネクター）の相対評価が上がる
- AJo, KQoなどオフスーテッドブロードウェイはマルチウェイで価値が下がる

出典: [4 Ways to Improve Your Results in Multi-Way Pots | Upswing Poker](https://upswingpoker.com/multi-way-pots-strategies-tips/)

---

## 5. 判断例10問

各例のフォーマット: ハンド・ポジション→スコア計算→しきい値比較→アクション

---

### 問1: AJo UTGから？

**スコア計算:**
- 基本スコア（A+J, オフスーテッド）= 推定25.5
- ボーナス/ペナルティなし
- **合計: 25.5**

**しきい値比較:** UTGしきい値24 → スコア25.5 > 24

**本書の判断:** オープンレイズ

**GTO視点の注意点:** GTOではAJoはUTGでは混合〜フォールドが主流（AQo+がUTG標準）。本書スコアがAJoを過大評価している可能性がある。実戦では「UTGのAJoはギリギリ開けられる」ではなく「UTGのAJoは慎重に」と補足するとよい。

---

### 問2: AJo COから？

**スコア計算:**
- 同上: 25.5

**しきい値比較:** COしきい値20 → スコア25.5 > 20

**本書の判断:** オープンレイズ（余裕あり）

**GTO視点:** COからAJoは標準的なオープンハンド。整合性あり。

---

### 問3: 66 MPから？

**スコア計算:**
- 基本スコア（ペア6）= 推定22
- **合計: 22**

**しきい値比較:** MPしきい値22 → スコア22 = 22（ぎりぎり）

**本書の判断:** オープンレイズ（ちょうど）

**GTO視点:** GTOでは66はHJ（MP相当）でオープンする場合と混合でフォールドする場合がある。「1点下ならフォールド」ルールを厳格適用するなら、スコアがちょうどしきい値のケースは「オープン可」として扱う（しきい値ぴったりはパス）。

---

### 問4: K9s HJから？

**スコア計算:**
- 基本スコア（K+9, スーテッド）= 推定21〜22（K高め、9低め、スーテッドボーナスあり）
- **合計: 約21〜22**

**しきい値比較:** MPしきい値22 → スコア21〜22（ギリギリまたは1点下）

**本書の判断:** しきい値を1点下回る可能性があればフォールド推奨

**GTO視点:** K9sはHJからは混合戦略（一部オープン）。COからは標準オープン。本書の判断（HJでフォールドまたは混合）はGTOと概ね整合。

---

### 問5: 87s COから？

**スコア計算:**
- 基本スコア（8+7, スーテッド）= 推定20（連続性ボーナス含む）
- **合計: 約20**

**しきい値比較:** COしきい値20 → スコア20 = 20（ちょうど）

**本書の判断:** オープンレイズ可

**GTO視点:** COから87sはGTO標準レンジに含まれる。整合性あり。

---

### 問6: A2s UTGから？

**スコア計算:**
- 基本スコア（A+2, スーテッド）= 推定18〜20（低い2がペナルティ）
- **合計: 約18〜20**

**しきい値比較:** UTGしきい値24 → スコア18〜20 < 24

**本書の判断:** フォールド

**GTO視点:** A2sはGTOでもUTGからは一般的にフォールド。A5s程度からが標準UTGレンジの下限。整合性あり。

---

### 問7: QTs MPから？

**スコア計算:**
- 基本スコア（Q+T, スーテッド）= 推定23〜24（連続性ボーナス込み）
- **合計: 約23〜24**

**しきい値比較:** MPしきい値22 → スコア23〜24 > 22

**本書の判断:** オープンレイズ

**GTO視点:** QTsはGTOでHJ（MP相当）から標準オープン。整合性あり。

---

### 問8: JJ SBから？

**スコア計算:**
- 基本スコア（ペアJ）= 推定32〜34
- **合計: 約32〜34**

**しきい値比較:** SBしきい値20 → スコア32〜34 >> 20

**本書の判断:** オープンレイズ（余裕あり）

**GTO視点:** JJはどのポジションからも標準オープン。問題なし。SBからは特にレイズが推奨される（リンプは価値を失う）。

---

### 問9: T9s BTNから？

**スコア計算:**
- 基本スコア（T+9, スーテッド）= 推定22〜23（連続性ボーナス込み）
- **合計: 約22〜23**

**しきい値比較:** BTNしきい値18 → スコア22〜23 > 18

**本書の判断:** オープンレイズ（余裕あり）

**GTO視点:** BTNからT9sは標準オープン。整合性あり。

---

### 問10: 44 BTNから？

**スコア計算:**
- 基本スコア（ペア4）= 推定18〜19
- **合計: 約18〜19**

**しきい値比較:** BTNしきい値18 → スコア18〜19（ぎりぎり〜1点上）

**本書の判断:** オープンレイズ可（ぎりぎり）

**GTO視点:** GTOではBTNから44はオープンする場合とフォールドの混合。22〜33は混合がより増える。本書の判断（ぎりぎりオープン）はGTOと整合的。

---

## 6. ポジション別オープンチャート詳細（GTO参照）

### UTG（〜17.6%）
標準ハンド: 66+, A2s+（A5sまたはA9s+で部分的に混合）, KTs+, QTs+, JTs, T9s, 98s, ATo+, KJo+, AQo+  
※A5sはナッツフラッシュドローバリューあり、A2s〜A4sは一部混合

出典: [Hands To Play UTG In Live Poker | SplitSuit](https://www.splitsuit.com/hands-to-play-utg-in-live-poker)

### HJ（MP相当、〜21.4%）
UTGに加えて: 55, K9s+（K6s〜K8sは混合）, Q9s+, J9s+, 87s, 76s, ATo+（ATsを追加）, KTo+  
出典: [Implementable GTO Charts | PokerCoaching](https://poker-coaching.s3.amazonaws.com/tools/preflop-charts/online-6max-gto-charts.pdf)

### CO（〜27.8%）
HJに加えて: 44+（→33,22は混合）, A2s〜A9s（全スーテッドエース）, K4s+, Q7s+, J8s+, T8s+, 87s, 76s, 65s, KTo+, QJo+  
出典: [6-Max Pre-Flop Open Raising Ranges | MicroGrinder](https://microgrinder.com/poker-strategy-articles/6-max-pre-flop-ranges/)

### BTN（〜43.5%）
33+, A2s+, K2s+, Q3s+, J4s+, T6s+, 96s+, 85s+, 75s+, 64s+, 53s+, A4o+, K8o+, Q9o+, J9o+, T8o+, 98o  
出典: [6 max Preflop Charts | freebetrange](https://blog.freebetrange.com/article/preflop-charts-open-raise-in-6-max-poker-cash-games)

### SB（混合戦略、実質RFI〜30%程度）
GTO上はリンプ+レイズの混合。レイズベースで見るとCO相当（〜30%）。  
出典: [6 Max Opening Ranges | 888poker](https://www.888poker.com/magazine/strategy/all-about-6-max-opening-ranges-and-hand-selection-charts)

### 本書しきい値との主なギャップ

| ポジション | ギャップの方向 | 具体例 |
|-----------|--------------|--------|
| UTG       | 本書がやや広め | AJo, QJs をUTGオープンと判定 |
| MP        | 概ね整合       | A9oのMP開けはGTOでは混合 |
| CO        | 整合           | 87s, 98s の扱いが一致 |
| BTN       | 整合           | 44, T9s の扱いが一致 |
| SB        | 概ね整合       | 混合戦略の表現が単純化されている |

---

## 本書への適用

- **第7章本文の核心:** スコア計算→しきい値比較→アクション決定の「最後のステップ」として位置づける
- **境界ハンドの補足:** AJo・QJsについては「本書しきい値では開けると判定されるが、GTO上はUTGでは慎重」と注釈を入れる
- **「1点下なら降りる」ルール:** EVが小さい境界ハンドの誤判断コストは低いが、ポストフロップへの悪影響を防ぐため採用を推奨
- **しきい値の微調整:** アンティあり時・相手タイプ・マルチウェイの3パターンで調整方法を練習問題として示す

---

## 参考URL一覧

| 出典 | URL | 発行年 |
|------|-----|--------|
| 6 max Preflop Charts: Open Raise in Poker Cash Games | https://blog.freebetrange.com/article/preflop-charts-open-raise-in-6-max-poker-cash-games | 2024 |
| Preflop Range Morphology | GTO Wizard | https://blog.gtowizard.com/preflop-range-morphology/ | 2023 |
| Implementable GTO Charts | PokerCoaching | https://poker-coaching.s3.amazonaws.com/tools/preflop-charts/online-6max-gto-charts.pdf | 2024 |
| Strategy: UTG Pre-flop Ranges | PokerStrategy | https://www.pokerstrategy.com/strategy/bss/utg-pre-flop-ranges/ | 2023 |
| 6-Max Pre-Flop Open Raising Ranges | MicroGrinder | https://microgrinder.com/poker-strategy-articles/6-max-pre-flop-ranges/ | 2023 |
| Hands To Play UTG In Live Poker | SplitSuit | https://www.splitsuit.com/hands-to-play-utg-in-live-poker | 2024 |
| The Ultimate Guide to 6-Handed Poker | Upswing Poker | https://upswingpoker.com/6-handed-max-poker-strategy/ | 2024 |
| How to Adjust Your Strategy in Poker Games with Antes | PokerCode | https://www.pokercode.com/blog/poker-antes-strategy-adjustments | 2024 |
| Ante Poker: Fold Equity, EV Shifts | Pokerology | https://www.pokerology.com/poker/strategy/ante/ | 2024 |
| Ante in Poker Explained | CardPlayer | https://www.cardplayer.com/rules-of-poker/glossary/ante-in-poker | 2023 |
| How to Crush Ante Cash Games | GTO Wizard | https://blog.gtowizard.com/how_to_crush_ante_cash_games/ | 2024 |
| The Ultimate Guide to Preflop Multiway Pots | Upswing Poker | https://upswingpoker.com/multiway-pot-preflop-squeezing-leaks/ | 2024 |
| 10 Tips for Multiway Pots in Poker | GTO Wizard | https://blog.gtowizard.com/10-tips-multiway-pots-in-poker/ | 2024 |
| Edge-Passing in Poker | Upswing Poker | https://upswingpoker.com/edge-passing-folding-profitable-hands/ | 2024 |
| Understanding EV preflop | Run It Once | https://www.runitonce.com/nlhe/understanding-ev-preflop/ | 2023 |
| VPIP and PFR - Poker Statistics | PokerCopilot | https://pokercopilot.com/poker-statistics/vpip-pfr | 2024 |
| Poker Folding: The Ultimate Guide | 888poker | https://www.888poker.com/magazine/strategy/ultimate-poker-folding-guide | 2024 |
| Texas hold 'em starting hands | Wikipedia | https://en.wikipedia.org/wiki/Texas_hold_%27em_starting_hands | 2025 |
| 6 Max Opening Ranges | 888poker | https://www.888poker.com/magazine/strategy/all-about-6-max-opening-ranges-and-hand-selection-charts | 2024 |
| Preflop RFI Strategy | Upswing Poker | https://upswingpoker.com/preflop-open-strategy-rfi-explained/ | 2024 |
