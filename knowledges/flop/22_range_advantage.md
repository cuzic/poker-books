# レンジアドバンテージとナッツアドバンテージの判定

検索日: 2026-04-20

## 概要

フロップ戦略の根幹をなす2つのアドバンテージ概念。レンジアドバンテージは「ベット頻度」を、ナッツアドバンテージは「ベットサイズ」を決定する。この2軸を正確に判定することで、GTO的なCベット戦略が実装できる。

---

## 主要な知見

### 1. レンジアドバンテージの定義

レンジアドバンテージとは、特定のボードテクスチャー上で、一方のプレイヤーの全ハンドレンジが相手レンジより高い平均エクイティを持つ状態を指す。個別のハンド強度ではなく、**レンジ全体のエクイティ分布**を比較する概念。

- 「自分のレンジがそのボードでどれだけ機能するか」を示す指標
- レンジアドバンテージが大きいほど、ベット頻度を高められる
- アドバンテージを持つ側は、相手のキャップされたレンジに圧力をかけられる

出典: [Range Advantage in Poker 2026: Board Texture & Frequencies](https://www.vip-grinders.com/poker-strategy/range-advantage/)

### 2. ナッツアドバンテージの定義

ナッツアドバンテージとは、ボード上で最強クラスのハンド（ツーペア以上）のコンビネーション数が、相手より多い状態を指す。**レンジの平均強度ではなく、最強ハンドの保有比率**で決まる。

- ナッツアドバンテージが大きいほど、ベットサイズを大きくできる
- 相手にフォールドかコールかの厳しい二択を迫ることができる
- ポジションがある場合はさらに効果が増幅する

出典: [Dominating with Nut Advantage: A Key Edge in Poker Strategy](https://pokercoaching.com/blog/dominating-with-nut-advantage-a-key-edge-in-poker-strategy/)

### 3. 両者の違いと関係

| 概念 | 判断基準 | 戦略への影響 |
|------|---------|------------|
| レンジアドバンテージ | レンジ全体の平均エクイティ | **ベット頻度**（多い → 高頻度ベット）|
| ナッツアドバンテージ | 最強ハンドのコンビネーション数 | **ベットサイズ**（多い → 大きなサイズ）|

重要な原則（GTO Wizard より）:
> 「レンジアドバンテージはベット頻度を決め、ナッツアドバンテージはベットサイズを決める。ポジションは両方を増幅させる。」

一方を持ち、もう一方を持たないケースも存在する（例：レンジアドバンテージはあるがナッツアドバンテージはない、など）。

出典: [The Mechanics of C-Bet Sizing | GTO Wizard](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/)

### 4. 判定方法の簡易化

実戦でソルバーを参照できない状況での簡易判定基準:

**ステップ1：プリフロップレンジ強度の比較**
- UTGオープン：タイトな線形レンジ（AA-22、AK-AJ、KQ等）
- BBディフェンス：幅広いレンジ（スーテッドコネクター、低スートカード含む）
- オープンレイザーは通常、コールプレイヤーより強いレンジを持つ

**ステップ2：ボードとの絡みやすさ**
- 高カード（A、K、Q）ボード → オープンレイザー有利
- 低・中カード連続ボード（9-8-7等）→ BB有利（スーテッドコネクター系が絡む）
- レインボー枯れたボード → レンジが強い方が有利
- フラッシュドロー・ストレートドロー豊富なボード → どちらのレンジが絡むか確認

**ステップ3：本書式判定（HandScore活用）**
- 対象ボード上での平均HandScoreを両レンジで比較
- 差が5点以上 → アドバンテージあり
- 差が10点以上 → 強いアドバンテージ（大きなサイズを検討）

出典: [Mastering Range Advantage: A Key to Winning Poker Strategy](https://pokercoaching.com/blog/range-advantage/), [Range Advantage in Poker 2026](https://www.vip-grinders.com/poker-strategy/range-advantage/)

---

### 5. 代表ボードでのアドバンテージ評価

#### K♠7♦2♣（レインボー）— UTG vs BB

| 項目 | 評価 |
|------|------|
| レンジアドバンテージ | UTG（大）|
| ナッツアドバンテージ | UTG（大）|
| 推奨Cベット頻度 | 76〜91% |
| 推奨サイズ | 33% pot（スモール）|
| 理由 | UTGのタイトレンジにKx・77・AA-QQが多数。BBはKで降り札を大量に持つ。ナッツもUTGが圧倒 |

UTGは両アドバンテージを保有するため「高頻度 × スモールサイズ」のレンジベットが正解。

出典: [Range Advantage in Poker 2026](https://www.vip-grinders.com/poker-strategy/range-advantage/), [Early Position Bets Facing The Big Blind](https://pokercoaching.com/blog/early-position-bets-facing-the-big-blind/)

#### T♠9♦8♣（コネクテッド）— UTG vs BB

| 項目 | 評価 |
|------|------|
| レンジアドバンテージ | BB有利（コネクテッドで逆転）|
| ナッツアドバンテージ | BB有利（JTやT9o、87o等でストレート・ツーペア多数）|
| 推奨Cベット頻度（UTG）| 約44%（低め）|
| 推奨サイズ | 33〜50% pot |
| 理由 | BBのディフェンスレンジにスーテッドコネクター系が多数含まれ、ストレート・ツーペアのコンボでナッツを制する |

UTGはプリフロップの強さがあるが、このボードではレンジ・ナッツ両方でBBに逆転される。

出典: [Interpreting Equity Distributions | GTO Wizard](https://blog.gtowizard.com/interpreting-equity-distributions/)

#### A♠7♦6♣（セミコネクテッド）— UTG vs BB

| 項目 | 評価 |
|------|------|
| レンジアドバンテージ | UTG（大・約66% vs 34%）|
| ナッツアドバンテージ | UTG（AA、AX、KK-QQが多数）|
| 推奨Cベット戦略 | レンジベット（全ハンドベット）|
| 推奨サイズ | 25〜30% pot |
| 理由 | UTGはAを大量保有。BBはAハイボードで多くのハンドがエクイティ不足。UTGが両アドバンテージを独占 |

K72との違いは中カード（6、7）がフラッシュドローやストレートドローの可能性を若干加えるが、依然UTGが両アドバンテージを持つ。

出典: [Early Position Bets Facing The Big Blind](https://pokercoaching.com/blog/early-position-bets-facing-the-big-blind/)

---

### 6. 3betポットでのアドバンテージ

3betポットでは3betした側（IP/OOP問わず）が、ほぼ全てのフロップで両アドバンテージを持つ傾向がある。

**3bet側の特徴:**
- タイトな3betレンジ（AA、KK、QQ、JJ、AK、AQ等）
- ビッグペアやブロードウェイカードが多く、ナッツアドバンテージを確保
- 相手のコールレンジはキャップされる（KK+/AK等を3betで排除される）

**3betポットでの戦略（IP側）:**
- ほぼ全フロップでCベット有利
- ナッツアドバンテージが高いため大きなサイズも検討可能
- スタックが浅いほど小さなサイズ（10〜25% pot）でストリート全体を設計

**3betポットでの戦略（OOP側）:**
- 高頻度のCベットが正解（ポジション不利を補う）
- 浅いスタックでより積極的にベット
- ブランクフロップでは特にCベット頻度が高まる

出典: [C-Betting IP in 3-Bet Pots | GTO Wizard](https://blog.gtowizard.com/c-betting-ip-in-3-bet-pots/), [C-Betting OOP in 3-Bet Pots | GTO Wizard](https://blog.gtowizard.com/c-betting-oop-in-3-bet-pots/)

---

### 7. BTN vs BB：ほぼフラット〜BB寄りの関係

BTN vs BBは全ポジション対決の中で最も均衡に近いが、それでもBTNが優位。

| 指標 | BTN | BB |
|------|-----|-----|
| プリフロップエクイティ | 57.4% | 42.6% |
| フロップでの優位性 | ほぼ全フロップで有利 | 中低カード連続ボードのみ有利 |
| 例外ボード | 654r（BB有利に近い）| 9♣7♠5♥等 |

BBが完全にレンジアドバンテージを取り返せるボードは稀で、最も有利なフロップ（654r）でもBBのエクイティは52%未満程度。そのためBTN側は幅広くCベットを検討でき、BBは基本的に全レンジをチェックする（Cベット率約2%）。

出典: [Range Advantage in Poker 2026](https://www.vip-grinders.com/poker-strategy/range-advantage/)

---

### 8. 本書式での判定基準（HandScoreベース）

本書では第8章で定義したHandScoreを応用し、ボード上のレンジアドバンテージを数値化する。

**判定フロー:**
1. 両プレイヤーの代表レンジをボード上でHandScore評価
2. 各レンジの平均HandScoreを算出
3. 差が5点以上 → アドバンテージあり（Cベット推奨）
4. 差が10点以上 → 強いアドバンテージ（大きなサイズも検討）
5. 差が5点未満 → ほぼイーブン（慎重なCベット）

**ナッツアドバンテージの数値判定:**
- ツーペア以上のコンボ数を比較
- 自分のコンボ数が相手の1.5倍以上 → ナッツアドバンテージあり（大きなサイズ推奨）
- ほぼ同数 → ナッツはイーブン（サイズは慎重に）

この数値判定は本書オリジナルの簡易化アプローチ。GTO Wizard等のソルバー参照を代替するものではなく、実戦判断の補助ツールとして位置づける。

---

## 本書への適用

- **第22章**でこのリサーチを主軸として使用
- レンジアドバンテージとナッツアドバンテージの2軸マトリクス（高/低 × 高/低の4象限）で戦略を分類
- K72・T98・A76の3ボード例を実戦演習として使用（UTG vs BB）
- HandScoreによる簡易判定法を「本書オリジナルの実戦ツール」として第22章で提示
- 3betポット vs フラットコールポットの違いを比較表で示す
- BTN vs BBは「基本的にBTN優位だが幅が小さい」ケースとして補足説明

---

## 参考文献一覧

- [Range Advantage in Poker 2026: Board Texture & Frequencies](https://www.vip-grinders.com/poker-strategy/range-advantage/)
- [Dominating with Nut Advantage: A Key Edge in Poker Strategy](https://pokercoaching.com/blog/dominating-with-nut-advantage-a-key-edge-in-poker-strategy/)
- [Mastering Range Advantage: A Key to Winning Poker Strategy](https://pokercoaching.com/blog/range-advantage/)
- [The Mechanics of C-Bet Sizing | GTO Wizard](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/)
- [Interpreting Equity Distributions | GTO Wizard](https://blog.gtowizard.com/interpreting-equity-distributions/)
- [C-Betting IP in 3-Bet Pots | GTO Wizard](https://blog.gtowizard.com/c-betting-ip-in-3-bet-pots/)
- [C-Betting OOP in 3-Bet Pots | GTO Wizard](https://blog.gtowizard.com/c-betting-oop-in-3-bet-pots/)
- [Early Position Bets Facing The Big Blind](https://pokercoaching.com/blog/early-position-bets-facing-the-big-blind/)
- [How to Use Positional, Range, and Nut Advantages to Maximize Profit](https://upswingpoker.com/nut-range-positional-advantage/)
- [Preflop Range Morphology | GTO Wizard](https://blog.gtowizard.com/preflop-range-morphology/)
