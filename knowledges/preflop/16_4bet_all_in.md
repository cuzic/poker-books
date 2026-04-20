# 4bet・オールインの簡易EV式

検索日: 2026-04-19

## 概要

第16章「全部覚えなくていい章」のコア内容。4betの目的・レンジ構成・サイジング・ショートスタックのオールイン判断を最低限の知識に絞って提供する。「QQ+とAKだけで8割正解」の裏付けとFE込みEV式を整理した。

---

## 主要な知見

### 知見1：4betの目的とレンジ構成

#### バリュー4bet

4betはプレミアムハンドで相手の劣ったハンドにコールさせる、またはフォールドエクイティを獲得することを目的とする。

**コア・バリューレンジ（常に4bet）**
- AA / KK：プリフロップでスタックを投入したい最強手。例外なく4bet。
- QQ / AK：ポジションと相手の傾向に応じてコール/4betをミックス。

**QQ+AKが「8割正解」の妥当性**
- 100BBの標準スタックでは、4betはほぼ AA/KK/QQ/AK のみで構成される（Ratio 2 の相手を基準とした場合）。
- 上記4コンボは全4betハンドの約7〜8割を占める。JJや TT は一部ポジション（SB vs BB 等）で加わることがあるが、EPからの4betにはほぼ登場しない。
- 「QQ+とAKだけ」に絞ることで捨てるEVは小さく、ミスの回避効果が大きい（初心者向けの近似として妥当）。
- 出典: [Upswing Poker: 4-Bet Size Strategy](https://upswingpoker.com/4-bet-size-strategy/) / [Blackrain79: Defend Against 4Bets](https://www.blackrain79.com/2017/02/how-to-defend-against-4bets.html)

#### ブラフ4bet

ブラフ4betは、相手の強いレンジをブロックしつつコールされても一定のエクイティを保つハンドを使う。

**最良のブラフ候補**
- A5s / A4s / A3s / A2s（スーテッド・ホイール・エース）
  - 相手のAA/AKをブロック（除去効果が高い）
  - コールされても約35〜40%のエクイティを確保
  - コールできるほど強くなく、フォールドするには惜しい（3betに対してコール/フォールドのどちらも難しい位置にある）
- 避けるべき手：KJs、QJs（支配されやすく除去効果が低い）
- 出典: [Upswing Poker: 4-Bet Size Strategy](https://upswingpoker.com/4-bet-size-strategy/) / [PokerCoaching: 4-Betting Strategy](https://pokercoaching.com/blog/4-betting-strategy/)

---

### 知見2：FE込みEV公式

#### 基本形式

```
EV（4bet）= (Fold% × ポット) + (Call% × (Equity × (ポット + コール額) − (1 − Equity) × コール額))
```

初心者向けに「折りたたんだ」簡易形：

```
EV ≈ (相手が降りる確率 × 現在のポット) − (コールされた確率 × 期待損失)
```

#### 具体例（100BB、6max、BTN vs BB）

- BTN が 2.5BB オープン → BB が 11BB に 3bet → BTN が 25BB に 4bet
- BB の推定フォールド率：60%
- 4bet 時点のポット：36.5BB（BTN 25BB + BB 11BB + SB 0.5BB）
- BTN がすでに投じた額：25BB

**降りてもらえた場合の獲得：** 36.5BB − 25BB = **+11.5BB の回収**（投資済み分を除いた純利益は ≒ 11BB の3bet分）

- コールされた場合、QQ+/AK vs ブラフレンジでのエクイティは約60〜65%

この公式は「何%降りれば4betはペイするか」を計算する際に使う。ブラフ4betのブレークイーブン降り率：

```
必要フォールド率 = リスク額 / (ポット + リスク額)
```

例：4bet に 14BB 追加リスク、現ポット 11BB の場合 → 14 / (11 + 14) ≈ 56% のフォールドが必要。

- 出典: [GTO Wizard: Expected Value in Poker](https://blog.gtowizard.com/what-is-expected-value-in-poker/) / [PokerNews: Fold Equity & EV](https://www.pokernews.com/strategy/foldequity-expectedvalue-ev-42297.htm)

---

### 知見3：4betサイジングの目安

| ポジション | 推奨サイジング（3betの倍率） | 理由 |
|---|---|---|
| IP（インポジション） | 2.2〜2.5x | ポジション優位があるため小さく可。相手に狭いコール範囲を強いる |
| OOP（アウトオブポジション） | 2.5〜3x | ポジション不利を補うため大きめに設定 |

**実際の目安（100BB スタック）**

- IP での典型 4bet：約 20〜25BB
- OOP での典型 4bet：約 25〜30BB

3betが大きい（BB vs BTN など）場合は相対的なサイジングで調整。絶対値でなく「3betの何倍」を意識する。

- 出典: [Upswing Poker: 4-Bet Size Strategy](https://upswingpoker.com/4-bet-size-strategy/) / [Rakerace: 4-Betting Sizes 2024](https://rakerace.com/news/poker-strategy/2024/07/17/choosing-our-bet-sizes-preflop-3-betting-and-4-betting)

---

### 知見4：ショートスタック（≤20BB）のオールイン戦略

#### プッシュorフォールドの適用範囲

- **〜10BB**：ほぼすべての状況でプッシュorフォールドが最善（中間ベットサイズはスタックが薄すぎて機能しない）
- **11〜15BB**：プッシュorフォールドが基本。一部のハンドはミニレイズが最適になりうる
- **16〜20BB**：プッシュorフォールドを基本にしつつ、ポストフロップが得意なら通常レイズを混ぜ始める

#### ポジション別プッシュ早見表（Nash均衡ベース）

**UTG（6max）**

| スタック | プッシュ範囲の目安 |
|---|---|
| 10BB | 22+, A2s+, A9o+, KQs（約12〜16%） |
| 15BB | 66+, A2s+, ATo+, KQs（約10〜12%） |
| 20BB | 88+, AJs+, AQo+（約6〜8%） |

**BTN（6max）**

| スタック | プッシュ範囲の目安 |
|---|---|
| 10BB | 22+, A2s+, A2o+, KTs+, QTs+, JTs（約33〜38%） |
| 15BB | 33+, A2s+, A7o+, KQs, KJs（約25〜30%） |
| 20BB | 44+, A2s+, A9o+, KQs（約20〜22%） |

**重要注意**：弱いオフスーテッドAX（A2o〜A7o）はUTGや中間ポジションでは10BBでも不採算。同じ手でもポジションで判断が逆転する。

- 出典: [Upswing Poker: Push Fold Tournament Charts](https://upswingpoker.com/push-fold-tournament-strategy-charts/) / [GTO Charts: Nash Equilibrium](https://gtocharts.com/nash/)

---

### 知見5：「4betに対してQQ以外は降りる」ルール

#### JJ vs 4bet の分析

4bet に対するJJの処理は位置と相手の4betレンジの広さによる。

**フォールド推奨のケース（典型的な100BB EP vs MP）**
- 相手の4betレンジ：QQ+/AK（Ratio 2）
- JJ のエクイティ：≒ 33%（約2対1アンダードッグ）
- コール額が有効スタックの25%超 → セットバリューのインプライドオッズなし
- 結論：フォールドが数学的に正解

**コール可能なケース**
- 相手の4betレンジが広い（Ratio 3〜4、ブラフ込み）
- IP でスタックが深い（150BB+）
- 4betサイジングが小さい（2.2x 以下）

**BTN vs SB など後ポジション同士では**
- JJはレンジにコールが含まれることがある（GTO ソルバーはJJを一部コールする）

#### QQ vs 4bet（境界線）

- QQ は通常の100BB 6max では 5bet ジャムまたはコールのミックス。フォールドはほぼ誤り。
- SB vs UTG など、最もタイトな状況でも QQ は5bet ジャムが標準（≒ AA/KK/QQ/AK vs AA/KK という比較）
- QQ のエクイティ vs {AA,KK}：≒ 18%（大きなアンダードッグ）
- QQ のエクイティ vs {AA,KK,AK}：≒ 42%（AKが含まれるため改善）
- QQ のエクイティ vs {QQ+,AK}：≒ 47%（ほぼ互角 → ジャムが有効）

出典: [Fearless River: JJ vs 4-Bet](https://app.fearlessriver.com/blog/jj-vs-a-4-bet-what-do-you-do-here/) / [888poker: 4bet Defense Strategy](https://www.888poker.com/magazine/strategy/4bet-defense-poker-strategy)

---

### 知見6：対5bet戦略

5betはオールインを意味する（100BB スタックの場合、ほぼ必ずスタック投入）。

#### 標準的な対5bet応答

**5betジャム（コール）すべき手**
- AA / KK：常にコール。相手の5betレンジに対して常に優位または互角以上。
- QQ：多くの状況でコール。相手の5betレンジに{AK}が含まれる場合、エクイティ約47%でコール有利。
- AK：相手の5betレンジが{AA,KK,QQ,AK}の場合エクイティ≒43〜46%。微妙だがポット規模からコールが必要。

**フォールドすべき手（原則）**
- JJ / TT：相手の5betレンジ（AA/KK/QQ）に対して大きなアンダードッグ。フォールド推奨。
- AQ / KQ：ドミネートリスクが高い。

**ポイント**：5betジャムに対して必要な「勝率の閾値」はポット規模で計算する。

例：ポット125BBで75BBのコールが必要な場面 → 必要エクイティ = 75 / (125 + 75) ≈ **38%** でコール有利。
このため AK は多くの場合コール可能。

- 出典: [Upswing Poker: 4-bet 5-bet Strategy](https://upswingpoker.com/4-bet-5-bet-preflop-strategy/) / [888poker: 4bet Defense](https://www.888poker.com/magazine/strategy/4bet-defense-poker-strategy)

---

### 知見7：AKの扱い（4bet後のオールインコール）

#### AKのエクイティ比較

| 相手の5betレンジ | AKのエクイティ |
|---|---|
| AA のみ | ≒ 7% |
| KK のみ | ≒ 30% |
| {AA, KK} | ≒ 18% |
| {AA, KK, QQ} | ≒ 43% |
| {AA, KK, QQ, AK} | ≒ 46% |

#### 判断の分岐

**4bet後に5betジャムを受けた場合のAK**

- 相手が「QQ+のみ」で5bet → コールすると約43%。ポット規模次第でコール有利（上記の38%閾値を超える）。
- 相手が「KK+のみ」で5bet → エクイティ約18%。ほぼ必ずフォールド。
- 相手の5bet レンジが不明 → 「QQ+/AK」と仮定してコール（リスクは受け入れる）。

**4betに対するAKの初期判断**

- IP（BTN等）：AKs はコールも有力。AKo は4betが標準。
- OOP：4betが標準（ポストフロップの不利を避ける）。
- 5betジャムには基本的にコール（必要エクイティを満たすケースが多い）。

- 出典: [Blackrain79: Should You Go All In With AK](https://www.blackrain79.com/2019/11/should-you-go-all-in-with-ak.html) / [GTO Wizard: EV in Poker](https://blog.gtowizard.com/what-is-expected-value-in-poker/)

---

## 本書（第16章）への適用

### 章の位置づけ

「全部覚えなくていい章」として、以下の最小セットだけを読者に渡す。

### 読者に渡す3つのルール

1. **バリュー4betはQQ+とAKだけ（8割正解）**
   - AA/KK/QQ/AK に絞ることで大きなEVを失わずミスを激減させる
   - ブラフ4betはA5s/A4s（覚えたい人向けのオプション）

2. **4betサイズはIP:約2.3x、OOP:約2.6x**
   - 具体的には「4betされたら20〜30BBが目安」と言い換えられる

3. **4bet返し（5bet）に対してはQQ以上でコール、JJは降りる**
   - QQの境界：エクイティ上ほぼ互角のため続行
   - JJの境界：約2対1アンダードッグ、インプライドオッズも出ないためフォールド
   - AKのオールインコール：必要エクイティ38%前後 → 相手の5betレンジが{QQ+/AK}想定ならコール可

### ショートスタック特記事項

- ≤15BB では「すべてオールインかフォールド」で統一（ポストフロップ後の残りスタックが少なすぎる）
- BTNなら A2o〜A9o/22+はほぼ全部プッシュ。UTGなら A2o〜A7o はフォールド側。
- 「Nash均衡チャートを丸暗記しなくていい。ポジションが遅いほど広く、早いほど狭く」で近似できる。

### 執筆上の注意

- EV公式は「EV = (折りさせる確率 × ポット) − (コールされる確率 × 損失)」に単純化して提示する
- 「計算は省略でいい、重要なのは境界を覚えること（QQ=コール、JJ=フォールド）」というメッセージを強調
- ブラフ4betは「上級者向けオプション」として軽く触れる程度でよい

---

## 参照元一覧

- [Upswing Poker: 4-Bet Size Strategy](https://upswingpoker.com/4-bet-size-strategy/)
- [Upswing Poker: 4-Bet & 5-Bet Preflop Strategy](https://upswingpoker.com/4-bet-5-bet-preflop-strategy/)
- [Upswing Poker: Push Fold Tournament Strategy Charts](https://upswingpoker.com/push-fold-tournament-strategy-charts/)
- [PokerCoaching: 4-Betting Strategy](https://pokercoaching.com/blog/4-betting-strategy/)
- [GTO Wizard: Expected Value in Poker](https://blog.gtowizard.com/what-is-expected-value-in-poker/)
- [GTO Wizard: 4-Bet Pots OOP as Preflop Caller](https://blog.gtowizard.com/4-bet-pots-oop-as-the-preflop-caller/)
- [Blackrain79: Defend Against 4Bets (Data-Driven)](https://www.blackrain79.com/2017/02/how-to-defend-against-4bets.html)
- [Blackrain79: Should You Go All In With AK](https://www.blackrain79.com/2019/11/should-you-go-all-in-with-ak.html)
- [888poker: 4bet Defense Strategy](https://www.888poker.com/magazine/strategy/4bet-defense-poker-strategy)
- [Fearless River: JJ vs a 4-Bet](https://app.fearlessriver.com/blog/jj-vs-a-4-bet-what-do-you-do-here/)
- [PokerNews: Fold Equity & Expected Value](https://www.pokernews.com/strategy/foldequity-expectedvalue-ev-42297.htm)
- [GTO Charts: Nash Equilibrium Push/Fold](https://gtocharts.com/nash/)
- [Bluffaces: 4-Bet Ranges by Position](https://bluffaces.com/articles/4-bet-in-poker-introducing-ranges-for-each-position/)
- [Rakerace: 4-Betting Sizes (2024)](https://rakerace.com/news/poker-strategy/2024/07/17/choosing-our-bet-sizes-preflop-3-betting-and-4-betting)
