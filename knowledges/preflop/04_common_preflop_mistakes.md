# 04: 初心者がやりがちなプリフロップミス集

検索日: 2026-04-19

## 概要

プリフロップでの判断ミスは、ポストフロップのどんな好プレーよりも根深くEVを蝕む。なぜなら、悪いスタートポジションから生じる不利は、フロップ以降のスキルで完全には取り戻せないからだ。本章の目的は、読者が「自分もやっている」と気づき、本書を自分ごととして読み進めるきっかけを作ることにある。以下に、GTO分析・ソルバーデータ・専門サイトの知見を総合して整理した代表的ミスを示す。

---

## 1. ミスのランキング（EV損失の重大度順）

| 順位 | ミスの内容 | EV損失の目安 | 深刻度 |
|------|-----------|-------------|--------|
| 1 | オープンリンプ（早～中ポジション） | 約 -120bb/100（ロジャック位置での実測値） | 最重大 |
| 2 | ポジション逆転（UTGでルース・BTNでタイト） | 数十bb/100 | 重大 |
| 3 | 弱いAxをUTGから開く（A9o以下のオフスート） | -0.49bb/手（A9oの実測例） | 重大 |
| 4 | SBからのコール過多（OOPでフラットしすぎ） | 数十bb/100 | 重大 |
| 5 | スーテッドを過信（K3s〜K6s等を早いポジで開く） | 中程度 | 中程度 |
| 6 | 3ベットへの誤った対応（AQoを4ベットに対し降りない等） | 中程度 | 中程度 |
| 7 | 小ペアの扱いミス（UTGで捨てすぎ・セットマインの過用） | 中程度 | 中程度 |
| 8 | ビッグペアのスロープレイ（AAをリンプで罠にかける） | 小〜中程度 | 軽中程度 |
| 9 | スタック・ポットサイズの不一致（エフェクティブスタック無視） | 状況による | 中程度 |

---

## 2. 個別ミス詳細

### 2-1. オープンリンプ

**どんな状況で起きるか**
「ハンドが弱くて自信がない」「様子を見たい」という心理から、ブラインドをコールするだけで手を進める。

**なぜ間違いなのか**
- ポットを取るチャンスを自ら放棄する（レイズなら相手が全員フォールドすれば即獲得できる）
- イニシアチブを失い、フロップ以降の選択肢が狭まる
- 後ろのプレイヤーに安く見る権利を与える（エクイティ放棄）
- 5人でフロップを見れば勝率は約20%まで下落する
- ロジャック（6maxでは中ポジ）でのリンプの実測損失は **約 -120bb/100**（要注意：これは極端なケースの数値）

**GTOが推奨するリンプの場面（例外）**
- ヘッズアップ（HU）のSBや浅いスタック（14bb以下）では、ソルバーが一定のリンプ戦略を採用する
- ただし100bb前後のキャッシュゲームで早〜中ポジからリンプするのはGTO的に存在しない

**正しい判断**
- 入る手には必ずオープンレイズ（2〜3bb）をかける
- プレイする価値がなければフォールドする
- 「コールかフォールド」でなく「レイズかフォールド」で考える

- 出典: [Why Limping is Usually Bad (And When It's Actually Good) - Upswing Poker](https://upswingpoker.com/why-limping-in-poker-is-bad/) (2024)
- 出典: [The Curious Case of Open-Limping Buttons - GTO Wizard](https://blog.gtowizard.com/curious-case-of-open-limping-buttons/) (2024)
- 出典: [Poker: limping in early position and other lousy strategies - Mike Fowlds, Medium](https://mikefowlds.medium.com/poker-limping-in-early-position-and-other-lousy-strategies-57c5aa931dae)

---

### 2-2. 弱いAxをUTGから開く

**どんな状況で起きるか**
「Aがあるから強い」という固定観念でA5o、A7o、A9oなどをUTGからオープンする。

**なぜ間違いなのか**
UTGの標準オープンレンジはGTO的に全ハンドの約17.6%。この17.6%に含まれるのはATs+、AJo+など上位のAxのみ。A2o〜A9oのオフスートは基本的に全フォールドが正解。

- **A9o**：第1章データ再利用 → 1手あたり約 **-0.49bb** の損失（＝49bb/100相当）
- **A7o、A5o**：A9o以上に弱く、UTGでのオープンEVはさらにマイナス
- A3sやA5sはボードカバレッジのためにギリギリ含まれる場合があるが、**オフスートは別物**

**スタック深さの影響**
エフェクティブスタックが深いほどポストフロップで引いた場合に大きなポットを取れるが、UTGからの多人数対応では不利が大きすぎる。ソルバーは「A9o非推奨」を一貫して示す。

**正しい判断**
- UTGからのAx: ATs+・AJo+ のみをオープン
- A2s〜A9s: ポジションによっては含む（CO以降から検討）
- A2o〜A9o: 全ポジションで原則フォールド（BTNでのみA9o以上が条件付きで入る）

- 出典: [Preflop Range Morphology - GTO Wizard](https://blog.gtowizard.com/preflop-range-morphology/) (2024)
- 出典: [Hands To Play UTG In Live Poker - SplitSuit Poker](https://www.splitsuit.com/hands-to-play-utg-in-live-poker) (2025)
- 出典: [Strategy: UTG Pre-flop Ranges - PokerStrategy](https://www.pokerstrategy.com/strategy/bss/utg-pre-flop-ranges/)

---

### 2-3. スーテッドを過信する（K3s、Q4s、J3s）

**どんな状況で起きるか**
「スーテッドだから少し強い」という感覚で、K3sやQ4sをUTGや早いポジションから開く。「スーテッドなら+2点」式の点数計算に依存するプレイヤーに多い。

**なぜ間違いなのか**
スーテッドであることのボーナスは「フラッシュドローが成立しやすくなる」「フラッシュ完成時のポテンシャルが高い」という点に限られる。それだけでは弱いキッカーのリスクを補えない。

- **K3s〜K6s**: GTOでUTG〜ロジャックからオープン対象外（Kがあっても相手のKヒットで常にリードされる）
- K7s〜K8s: ハイジャック（HJ）からようやく検討範囲に入る
- Q4s、J3s: カットオフ（CO）以降でも多くのGTOチャートで非採用

**ポジション別のKxs採用ライン（GTO標準）**

| ポジション | 採用開始のKxs |
|-----------|-------------|
| UTG〜LJ  | K採用なし（強いKsはKQsのみ） |
| HJ       | K8s〜K7s から |
| CO       | K6s〜K5s から |
| BTN      | K2s まで全採用 |
| SB       | K2s まで全採用 |

- 出典: [How to Play King-X Suited Hands in Cash Games - Upswing Poker](https://upswingpoker.com/king-x-suited/) (2024)
- 出典: [Preflop Range Morphology - GTO Wizard](https://blog.gtowizard.com/preflop-range-morphology/) (2024)

---

### 2-4. OOPからのコール過多（BBディフェンス・SBのリンプコール）

**どんな状況で起きるか**
「ポットオッズが良いから」という理由でBBやSBから広くコールする。特にSBから「フォールドするのがもったいない」という心理でコールを続ける。

**なぜ間違いなのか**

**BBディフェンス**
- BBは既に1bb投資済みなので相手のオープン（2.5bb等）に対するポットオッズは良い
- ただし「OOPでフロップを見ること」のコストは、ポットオッズ以上に重い
- GTO的なBB守備頻度（MDF: Minimum Defense Frequency）は約50〜60%だが、単純にコールし続ければ良いわけではない
- 弱いオフスートブロードウェイ（K9o、QJo等）のコールが典型的な損失源

**SBからのコール**
- SBはフロップ以降にBBの後ろから常にOOPで行動する必要がある（最も不利なポジション）
- SBからは基本的に「3ベットかフォールド」の戦略を取るべき
- コールすると「キャップされたレンジ（上限ある弱いハンド）」と見られ、BBからスクイーズを受ける危険もある
- 弱い3ベットブラフ（OOP）として使う手: A8o、KTo、K9o、K7sなど
- これらをコールで処理すると、ポストフロップのエクイティ実現が著しく下がる

**正しい判断**
- SBからは3ベットかフォールドを基本とする（コールは原則避ける）
- BBのMDFを意識しつつ、ハンドの実際の性質（OOPでの実現エクイティ）を考慮する
- 「ポットオッズが良い」だけでなく「このハンドでOOPの長いプレイに耐えられるか」を問う

- 出典: [Heads up! Exploiting SB's Preflop Mistakes - GTO Wizard](https://blog.gtowizard.com/heads-up-exploiting-sbs-preflop-mistakes/) (2024)
- 出典: [12 Preflop Mistakes to Avoid at All Costs - Upswing Poker](https://upswingpoker.com/preflop-poker-mistakes-avoid-at-all-cost/) (2024)

---

### 2-5. BTNでタイトすぎる・UTGでルースすぎる

**どんな状況で起きるか**
「ボタンは最後なんだからどうせ」と考えてタイト（40%未満）に構えたり、「早い番だから弱くても試してみよう」とUTGからルース（20%超）にオープンする。ポジションの重要性を知っていながら逆転した思考を持つプレイヤーに多い。

**GTO的な各ポジションのオープン頻度（100bb・6maxキャッシュの標準値）**

| ポジション | GTO推奨オープン頻度 | 典型的ミス |
|-----------|------------------|-----------|
| UTG       | 約17〜18%        | 20%超でオープン |
| HJ        | 約22〜25%        | UTG並みにタイト |
| CO        | 約27〜30%        | ± なし（中間） |
| BTN       | 約43〜51%        | 40%未満でタイト |
| SB        | 約40〜45%（3ベット戦略込み） | コール多用 |

**BTNで51%の根拠**
BTNはフロップ以降に常にIPで行動できるため、エクイティの実現効率が最高。GTO標準では22+、A2s+、K2s+、Q2s+、J6s+、T6s+、96s+、85s+、75s+、64s+などを含む幅広いレンジを採用する。

**UTGでのルースオープンの損失構造**
UTGには残り6〜8人のプレイヤーが待ち構えており、どの手も6〜8人に「降りてもらう必要がある」。弱いハンドはその過程でドミネートされたり、ポストフロップで不利な状況に追い込まれる。

**正しい判断**
- ポジションが良いほど広く、悪いほど狭く
- BTNでは「これはフォールドすべきか」ではなく「これを入れてもポジションで十分カバーできるか」を問う
- UTGで「弱いけど試してみよう」はGTO的に存在しない思考

- 出典: [Preflop Range Morphology - GTO Wizard](https://blog.gtowizard.com/preflop-range-morphology/) (2024)
- 出典: [12 Preflop Mistakes to Avoid at All Costs - Upswing Poker](https://upswingpoker.com/preflop-poker-mistakes-avoid-at-all-cost/) (2024)

---

### 2-6. 小ペア（22〜66）の扱いミス

**どんな状況で起きるか**
パターンA: 「弱いペアだから」とUTGから22〜55を捨てすぎる
パターンB: 「セットが入れば大きなポットが取れる」と浅いエフェクティブスタックで広くコールしすぎる

**なぜ間違いなのか**

**パターンA（捨てすぎ）**
- アンティがある場合、UTGからでも22+を全部オープンするのが有利
- アンティなしのケースでは22〜44をUTGでは捨てるが、55〜66は条件付きで含む
- UTGで小ペアを全部捨てるとレンジが見え透いてしまう（ペアが一切ない）

**パターンB（セットマインの過用）**
セットマインが成立する数学的条件:
- フロップでセットが入る確率: 約12%（8回に1回）
- セットが入った際に「プリフロップのコールの8倍以上」をスタックから回収できないと長期的に損
- エフェクティブスタックが20〜25倍以下（例: 2.5bbコールなら50bb未満）ではセットマインはEV的に赤字
- **ルール: セットマインはエフェクティブスタックがコール額の約25倍以上必要**（例: 5bbコールなら125bb以上）

**短いスタックへの対応ミス**
相手が50bbしか持っていないのに22でコールしてセットを狙う行為は、100bbの場合に比べてインプライドオッズが半減しており典型的な損失行動。

**正しい判断**
- アンティあり: 全ペア（22+）をほぼ全ポジションからオープン
- アンティなし: 55〜66はCO以降から、22〜44はBTN以降を目安に
- セットマイン: エフェクティブスタック × 1/25 以上のコールは損失（逆算: 100bbなら最大4bbのコールまで）
- コールする相手の3ベットレンジの広さを考慮（タイトな相手ほどセット完成後にスタックを取りやすい）

- 出典: [What is Set Mining in Poker? And When Should You Set Mine? - Upswing Poker](https://upswingpoker.com/set-mining-poker-tips/) (2024)
- 出典: [How Stack Sizes Change Your Range - GTO Wizard](https://blog.gtowizard.com/how-stack-sizes-change-your-range/) (2024)
- 出典: [Small Pocket Pair Preflop Strategy - SplitSuit Poker](https://www.splitsuit.com/small-pocket-pair-strategy) (2025)
- 出典: [Poker — set mining for fun and profit and the rule of 15/25/35 - Mike Fowlds, Medium](https://mikefowlds.medium.com/poker-set-mining-for-fun-and-profit-and-the-rule-of-15-25-35-bf0f8ba85eff)

---

### 2-7. 3ベットへの誤った対応

**どんな状況で起きるか**
「せっかくレイズしたのにもったいない」と3ベットに対して広くコールする。AQoやKQsで判断に迷い、不適切な行動を取る。

**なぜ間違いなのか**
3ベットが10bb（標準的な2.5bbレイズへの3ベット）の場合、コールには32.6%のエクイティが必要。ライブゲームで3ベットが18〜20bbになる場合は40%以上が必要。多くのハンドはこの閾値を下回る。

**具体的な境界ハンドの処理**

| ハンド | 3ベットへの対応（IP/OOP） | 4ベットへの対応 |
|-------|------------------------|---------------|
| AQo  | IPでコール、OOPで3ベット返しまたはフォールド | 基本フォールド（レンジが広い場合を除く） |
| AQs  | IPコール or 4ベット bluff/value | フラット（IP）またはフォールド（OOP） |
| KQs  | IPコール可（高性能コールハンド） | 基本フォールド |
| KQo  | OOPではほぼフォールド対象 | フォールド |
| JJ   | IP4ベット or コール、OOPでは状況次第 | タイトな相手にはフォールドも |

**「もったいない」からコールの問題点**
コールすると「キャップされたレンジ」として見られる。3ベットに対して4ベットしないということは「AAもKKもない」というシグナルを出すことになり、ポストフロップでの攻撃を受けやすくなる。

**正しい判断**
- 3ベットに対する選択肢は「コール」「4ベット」「フォールド」の3択
- OOP（特にSBからBTNへの3ベット後など）では強くコールしにくい
- AQoは強く見えるが、相手の3ベットレンジ（AK、QQ+）にほぼ全てドミネートされている
- KQsは最もバランスが取れたコールハンドの一つ（IP限定）

- 出典: [How to Play Versus Preflop 3-Bets In & Out of Position - Upswing Poker](https://upswingpoker.com/vs-3-bet-pre-flop-position-strategy-revealed/) (2024)
- 出典: [How to Play Ace-Queen Offsuit in Cash Games - Upswing Poker](https://upswingpoker.com/playing-ace-queen-offsuit/) (2024)
- 出典: [Should You Ever Cold Call a 3-Bet? - GTO Wizard](https://blog.gtowizard.com/should-you-ever-cold-call-a-3-bet/) (2024)

---

### 2-8. ビッグペアの過剰プレイ・スロープレイ

**どんな状況で起きるか**
- AAやKKをリンプして「罠にかけよう」とするスロープレイ
- QQで相手の4ベットに対して降りられない
- AKやAQを「プレミアムハンドだから」と過剰評価する

**なぜ間違いなのか**

**AAのスロープレイ**
- リンプすることで相手全員に安く見る権利を与える
- ポットを膨らませることができず、最大価値を引き出せない
- 現代GTO戦略では「スロープレイはほとんど存在しない」（チェックするのはミドルペアが中心）
- 「悪いターンカードが来ると、フロップでベットしていれば取れたアクションを失う」

**QQの4ベット対応**
- UTGなど早いポジションからの4ベットは、AA/KKに偏ったタイトなレンジを示す
- タイトな相手の4ベットにQQでコールし続けることは数学的に損
- ただし「相手の4ベットレンジが広い」と判断できる場合はコール・5ベットも選択肢

**AKの扱い**
- AKは超強力だが「インプロヴド（フロップでトップペア以上）しなければ0ペアのハンド」
- 相手の4ベットに対しては「常にコール以上で続ける」が基本（AKはフォールドしない）
- ただしポストフロップでの慎重な判断が必要

**正しい判断**
- AA/KK: 常にレイズ、スロープレイ禁止。3ベットに対しては4ベット
- QQ: 早いポジションからの4ベットには状況次第でフォールド検討
- AK: 4ベットに対し常にコール以上（フォールドしない）

- 出典: [12 Preflop Mistakes to Avoid at All Costs - Upswing Poker](https://upswingpoker.com/preflop-poker-mistakes-avoid-at-all-cost/) (2024)
- 出典: [How to Play Ace-King in Cash Games - Upswing Poker](https://upswingpoker.com/how-to-play-ace-king-big-slick/) (2024)

---

### 2-9. エフェクティブスタックを見ない問題

**どんな状況で起きるか**
自分のスタックだけを見て行動し、相手の残りスタック（エフェクティブスタック）を考慮しない。特にセットマインや深いポットを想定した行動計画で発生する。

**なぜ問題か**

エフェクティブスタック（有効スタック）= 自分と相手の「少ない方」のスタック

例: 自分が200bb、相手が50bbの場合
- エフェクティブスタックは50bb
- 22でセットを引いても相手からは最大50bbしか取れない
- 22でのコール（3〜5bb）に対するインプライドオッズ: 50 ÷ 5 = 10倍
- セットマイン成立には最低25倍必要 → **明確に損失行動**

**ルール整理**
- 100bbエフェクティブ: 2.5bbコールまでセットマイン可
- 50bbエフェクティブ: セットマインはほぼ断念
- 200bbエフェクティブ: 5bbコールまで条件付きでOK

**オフスートブロードウェイの過信**
KJo、QJoなどをミドルポジションからオープンするのも関連ミス。「スーテッドの方が良い」という感覚がある通り、98sはKJoより多くの局面で有利になる。

- 出典: [What Is Effective Stack Size & Why Does It Matter? - Upswing Poker](https://upswingpoker.com/effective-stack-size/) (2024)
- 出典: [12 Preflop Mistakes to Avoid at All Costs - Upswing Poker](https://upswingpoker.com/preflop-poker-mistakes-avoid-at-all-cost/) (2024)

---

## 3. 章の執筆への適用

### 読者の自己認識を促すフレーミング案

- 「あなたはリンプしていないか？→ 実は-120bb/100の赤字行動」
- 「Aのついたハンドを全部開いていないか？→ A9oで-0.49bb/手の損失」
- 「BTNでタイトにしていないか？→ 本来51%を開くべきポジション」
- 「セットマイン目的でコールしすぎていないか？→ エフェクティブスタック25倍ルール」

### 各ミスに「診断チェック」形式を入れると効果的

例:
```
チェック: あなたはSBから「ポットオッズがいいから」でコールしていますか？
→ それは今すぐ改める必要があります
```

### 第4章での優先順位

1. リンプ禁止（最もインパクトが大きく、初心者全員に刺さる）
2. ポジション × レンジの逆転（BTNで広く、UTGで狭く）
3. 弱いAxのUTGオープン（A9oの損失データを第1章と連動させる）
4. スーテッド過信（K3sの位置別ルール）
5. セットマインの25倍ルール（数学的根拠で説得力を持たせる）

---

## 参考URL一覧

- [12 Preflop Mistakes to Avoid at All Costs - Upswing Poker](https://upswingpoker.com/preflop-poker-mistakes-avoid-at-all-cost/)
- [Punish the Unstudied: Preflop Mistakes & Sizing Tells - GTO Wizard](https://blog.gtowizard.com/punish_the_unstudied_preflop_mistakes_and_sizing_tells/)
- [Preflop Range Morphology - GTO Wizard](https://blog.gtowizard.com/preflop-range-morphology/)
- [GTO Preflop Basics: Understand Core Principles and Profitable Deviations - PokerCoaching](https://pokercoaching.com/blog/gto-preflop-basics/)
- [3 Preflop Poker Mistakes You Are Making - PokerCoaching](https://pokercoaching.com/blog/3-unprofitable-preflop-mistakes-you-are-making/)
- [Why Limping is Usually Bad (And When It's Actually Good) - Upswing Poker](https://upswingpoker.com/why-limping-in-poker-is-bad/)
- [The Curious Case of Open-Limping Buttons - GTO Wizard](https://blog.gtowizard.com/curious-case-of-open-limping-buttons/)
- [Is Limping Pimping? - GTO Wizard](https://blog.gtowizard.com/is-limping-pimping/)
- [How to Play King-X Suited Hands in Cash Games - Upswing Poker](https://upswingpoker.com/king-x-suited/)
- [Heads up! Exploiting SB's Preflop Mistakes - GTO Wizard](https://blog.gtowizard.com/heads-up-exploiting-sbs-preflop-mistakes/)
- [How Stack Sizes Change Your Range - GTO Wizard](https://blog.gtowizard.com/how-stack-sizes-change-your-range/)
- [What is Set Mining in Poker? And When Should You Set Mine? - Upswing Poker](https://upswingpoker.com/set-mining-poker-tips/)
- [Small Pocket Pair Preflop Strategy - SplitSuit Poker](https://www.splitsuit.com/small-pocket-pair-strategy)
- [Poker — set mining for fun and profit and the rule of 15/25/35 - Mike Fowlds](https://mikefowlds.medium.com/poker-set-mining-for-fun-and-profit-and-the-rule-of-15-25-35-bf0f8ba85eff)
- [How to Play Versus Preflop 3-Bets - Upswing Poker](https://upswingpoker.com/vs-3-bet-pre-flop-position-strategy-revealed/)
- [How to Play Ace-Queen Offsuit in Cash Games - Upswing Poker](https://upswingpoker.com/playing-ace-queen-offsuit/)
- [Should You Ever Cold Call a 3-Bet? - GTO Wizard](https://blog.gtowizard.com/should-you-ever-cold-call-a-3-bet/)
- [How to Play Ace-King in Cash Games - Upswing Poker](https://upswingpoker.com/how-to-play-ace-king-big-slick/)
- [What Is Effective Stack Size & Why Does It Matter? - Upswing Poker](https://upswingpoker.com/effective-stack-size/)
- [Hands To Play UTG In Live Poker - SplitSuit Poker](https://www.splitsuit.com/hands-to-play-utg-in-live-poker)
- [Poker: limping in early position and other lousy strategies - Mike Fowlds, Medium](https://mikefowlds.medium.com/poker-limping-in-early-position-and-other-lousy-strategies-57c5aa931dae)
