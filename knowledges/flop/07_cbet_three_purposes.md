# CBet の3つの目的（バリュー／ブラフ／プロテクション）

検索日: 2026-04-20

## 概要

継続ベット（Continuation Bet、以下 CBet）とは、プリフロップで最後にアグレッシブなアクションを取ったプレイヤー（プリフロップレイザー）が、フロップで最初にベットするプレイのこと。ハンドがボードに刺さったかどうかに関わらず実行される、現代ポーカーの基本戦略の一つである。

CBet には大きく3つの目的があり、それぞれ使う場面・サイズ・頻度が異なる。現代 GTO 理論では「何のためにベットするか」を意識しながらレンジ全体でバランスを取ることが求められる。

---

## 主要な知見

### 知見1：CBet の定義

継続ベットとは、プリフロップレイザーがフロップで打つ最初のベットのこと。自分のハンドが改善しているかどうかに関わらず実行される。最も頻繁に直面するポストフロップの意思決定の一つであり、攻守両面での意味を持つ。

- 出典: [Continuation bet (c-bet) – GTO Wizard Glossary](https://pages.gtowizard.com/en/glossary/continuation-bet-cbet/)
- 出典: [What Are Continuation Bets in Poker? – MasterClass](https://www.masterclass.com/articles/what-are-continuation-bets-in-poker)

---

### 知見2：CBet の3つの目的

#### (1) バリュー CBet（Value C-Bet）

強いハンドでポットを膨らませる目的で打つ。相手がより弱いハンドでコールしてくれることを期待する。

- 狙い：より弱いハンドからのコール、または降りられた場合にポットを取る
- 対象ハンド：ツーペア以上、トップペアのトップキッカーなど
- サイズ：ボードのウェット度によって 50〜100%+ ポット（ドローがある場合は大きめ）
- GTO では、バリューハンドを核として戦略を構築する「Value First」アプローチが推奨される

バリューレンジの底は AK 程度（3ストリートバレルを打ち続けられるハンドが基準）。

- 出典: [C-Betting in Poker – How to Build the Optimal Strategy – PokerCoaching](https://pokercoaching.com/blog/c-betting-in-poker/)
- 出典: [Advanced C-Bet Strategy – Metavault Poker (2025-08-15)](https://metavault.poker/en/2025/08/15/c-bet-practice/)

#### (2) ブラフ CBet（Bluff C-Bet）

フロップでハンドが改善しなかった、またはショーダウンバリューが低い場合に、相手をフォールドさせるために打つ。レンジアドバンテージが重要な判断材料になる。

- 狙い：相手をフォールドさせてポットを取る
- 対象ハンド：ミスしたオーバーカード、スーテッドコネクター（ドロー込み）、バックドアドロー
- サイズ：33〜50% ポット（安くブラフを仕掛けリスクを最小化）
- 有効条件：自分のレンジがボードと相性が良い（レンジアドバンテージあり）、相手レンジが弱い

フロップは「ほとんどのハンドがボードを外す」ため、最初にベットした側が有利になりやすい。ブラフ CBet はこの原理を利用した戦略。

- 出典: [5 Components of Successful Bluff Continuation Betting on the Flop – Hand2Note](https://hand2note.com/Blog/Features/5-components-of-successful-bluff-continuation-betting-on-the-flop)
- 出典: [Cbet or Get Beat: 3 Rules to Bluff the Flop More – Smart Poker Study](https://smartpokerstudy.com/cbet-or-get-beat-3-rules-to-bluff-the-flop-more/)

#### (3) プロテクション CBet（Protection C-Bet / Equity Denial）

勝っているが脆弱なハンドを持つとき、相手にタダでドローを踏ませないために打つ。エクイティデナイアル（相手のエクイティを奪う）とも呼ばれる。

- 狙い：相手のフラッシュドロー・ストレートドローが完成する前に取りに行く
- 対象ハンド：トップペア（キッカー弱め）、オーバーペア（ウェットボード）、セット（ドロー多数）
- サイズ：66〜75% ポット程度（相手のドローにオッズを与えない）
- 前提：現在は勝っているが、ターン・リバーで逆転される可能性が高い

エクイティデナイアルはプロテクションと同義で、相手のアウツを「正しいオッズで踏ませない」ことが目的。

- 出典: [4 Poker Betting Strategies: Value, Bluff, Protection, Balance – PokerPower](https://pokerpower.com/4-poker-betting-strategies-value-bluffs-protection-and-balance/)
- 出典: [Flop Heuristics: IP C-Betting in Cash Games – GTO Wizard](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)

---

### 知見3：Range CBet の概念

高頻度・小サイズでレンジ全体にわたってベットする戦略。ドライボードで特に有効。

- ベットサイズ：25〜33% ポット（クォーターポット〜サードポット）
- 頻度：レンジのほぼ全体（70〜90%+）
- 有効な状況：ドライ・レインボーボード、ペアボード、相手が弱いレンジを持つ場合

Range CBet の論理：
- 小さいベットは安くブラフができる
- 相手がどんなハンドでもコールしにくい（フォールドエクイティが高い）
- バランスが自然に保たれる（全ハンドで同じ頻度・サイズ）

Jonathan Little による指針：「ベットするハンドが多いほど、CBet サイズは小さくすべき。レンジ全体でベットするなら 25〜35% ポットが適切」

- 出典: [When and How Much to Continuation Bet – Jonathan Little](https://jonathanlittlepoker.com/cbet/)
- 出典: [Sizing Your C-Bets: 3 Factors You Must Consider – Upswing Poker](https://upswingpoker.com/c-bet-sizing-strategy-continuation-bet/)

---

### 知見4：CBet の頻度（GTO 推奨）

GTO ソルバーが示すフロップ CBet 頻度の目安：

| 状況 | 推奨頻度 | 備考 |
|------|---------|------|
| ドライボード（IP）| 70〜90% | ペアボード・レインボーが最高頻度 |
| ウェットボード（IP）| 30〜50% | ドローが多く慎重に |
| ドライボード（OOP）| 40〜60% | 小サイズ多用 |
| ウェットボード（OOP）| 20〜35% | チェックレイズ重視 |
| 3-Bet ポット（IP）| 80%+ | レンジアドバンテージが強大 |
| マルチウェイ | 30%以下 | 全員に刺さるレンジが必要 |

ヘッズアップポットでの「バランスが取れた CBet 頻度」は 45〜60%。70% を超えるとオーバーブラフになりやすい。

プリフロップの「レンジアドバンテージ」（誰のレンジがボードに合っているか）が、CBet 頻度の主要な決定要因。ナットアドバンテージ（誰が最強ハンドを持ちやすいか）はサイズの決定要因。

- 出典: [How Often Should You CBet? – BlackRain79](https://www.blackrain79.com/2020/02/how-often-should-you-cbet-poker.html)
- 出典: [The Mechanics of C-Bet Sizing – GTO Wizard (2024-07-09)](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/)
- 出典: [Poker C-Bet Strategy 2026 – PokerOffer](https://thepokeroffer.com/poker-c-bet-strategy-guide-2026/)

---

### 知見5：IP vs OOP の CBet 頻度差

#### IP（イン・ポジション）の CBet

- ポジションの優位性（後から行動できる情報アドバンテージ）により、広いレンジでの CBet が可能
- 相手のチェックを受けてから適切に反応できるため、より多くのハンドでベットを選択できる
- 3-Bet ポットで BTN vs CO などでは 80%+ の頻度でベット（GTO ソルバーデータ）

#### OOP（アウト・オブ・ポジション）の CBet

- 情報アドバンテージがないため、より慎重なアプローチが必要
- チェックレイズをレンジに組み込むことが重要な戦術
- ダイナミックなフロップでは約 35% 程度のベット頻度（GTO Wizard データ）
- ソルバーは OOP の戦略を「ほぼ全ハンドがミックス戦略（混合）」として示す。これは OOP が構造的に難しい立場であることを意味する

Phil Galfond（Run It Once 創設者）の見解：フロップより **ターン CBet** の方が難しく重要であり、Range vs Range の思考が不可欠。Galfond はポーカー史上初めて「レンジ全体でのバランス」を体系的に教えたトレーナーの一人として知られる。

- 出典: [When to Continuation Bet in Poker – C-Betting In Position vs Out of Position – Upswing Poker](https://upswingpoker.com/continuation-bet-c-bet-strategy-position/)
- 出典: [C-Betting As the OOP Preflop Raiser – GTO Wizard (2024-01-22)](https://blog.gtowizard.com/c-betting-as-the-oop-preflop-raiser/)
- 出典: [Turn C-Bet Opportunities in SRP's – Phil Galfond / Run It Once](https://www.runitonce.com/poker-training/videos/phil-galfond-plo-poker-reviewing-turn-cbet-spots-in-vision/)

---

### 知見6：CBet サイズの一般的指針

| サイズ | ポット比率 | 使用場面 |
|--------|-----------|---------|
| 小（Small） | 25〜33% | ドライボード、Range CBet、OOP 時 |
| 中（Medium） | 50〜66% | 標準的なバリュー・ウェットボード |
| 大（Large） | 75〜100% | ウェットボード、強いバリュー、セミブラフ |
| オーバーベット | 100%+ | 特殊状況（ナットアドバンテージが極大） |

Doug Polk（Upswing Poker 創設者）による推奨：
「クォーターポット（25%）から 66〜75% まで全てが有効な選択肢。大きいサイズを使う場合はハンドがよりポーライズ（両極化）していることが条件。中程度のハンドで大きいサイズは使わない」

- 出典: [Upswing Poker – Doug Polk On C-Bet Sizing – CardPlayer](https://www.cardplayer.com/poker-news/21174-upswing-poker-doug-polk-on-c-bet-sizing)
- 出典: [What Flop C-Bet Size Should You Use in Cash Games? – Upswing Poker](https://upswingpoker.com/c-bet-sizing-flop-guide/)
- 出典: [The Mechanics of C-Bet Sizing – GTO Wizard (2024-07-09)](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/)

---

### 知見7：CBet してはいけないフロップ（チェックが優位な状況）

以下の条件が重なると、CBet は EV マイナスになりやすい。

#### 相手レンジがボードに刺さっている場合

- 例：ビッグブラインドが広い範囲でコール → 低いコネクテッドボード（例：6-7-8 レインボー）は BB のレンジに有利
- 相手がコールしやすいボードへの CBet は「お金を渡す」行為になる

#### ウェット・コーディネートボード（弱いハンドで）

- フラッシュドロー・ストレートドローが多い場合、弱いトップペアや中程度ハンドでの CBet は危険
- セミブラフレイズを誘発し、自分が降りざるを得なくなる

#### OOP でのマルチウェイポット

- 複数の相手がいると CBet のフォールドエクイティが激減
- 1人がコールするだけで IP にナッツを持たれるリスク

#### 自分のレンジが弱いボード（レンジディスアドバンテージ）

- 例：UTG がレイズして BB がコール → T-9-8 のような低いコネクテッドボードは BB のレンジが有利
- レンジに弱い側はチェック頻度を高くすべき

「ドライボードは常に CBet すべき」は誤り。常に CBet しているとチェックバックした際の手が分かりやすくなり、相手に読まれる（Red Chip Poker の警告）。

- 出典: [Five Reasons Not to Continuation Bet – PokerNews](https://www.pokernews.com/strategy/five-reasons-not-to-continuation-bet-in-no-limit-hold-em-25481.htm)
- 出典: [Always C-Bet Dry Flops? Probably Not – Red Chip Poker](https://redchippoker.com/cbet-dry-flops-strategy/)
- 出典: [MTTs: GTO Strategy for C-Betting Out of Position on Wet Boards – MyPokerCoaching](https://www.mypokercoaching.com/mtts-gto-strategy-for-c-betting-out-of-position-on-wet-boards/)

---

### 知見8：プロコーチの見解

#### Doug Polk（Upswing Poker）

「ベットサイズは、使えるオプションの中で 25%（クォーターポット）から 66〜75% まで全てが合理的。選択の基準はハンドのポーラリティ（両極化度）。ミドルストレングスのハンドで大きいサイズは使わない」

- 出典: [Upswing Poker – Doug Polk On C-Bet Sizing – CardPlayer](https://www.cardplayer.com/poker-news/21174-upswing-poker-doug-polk-on-c-bet-sizing)
- 出典: [Sizing Your C-Bets: 3 Factors You Must Consider – Upswing Poker](https://upswingpoker.com/c-bet-sizing-strategy-continuation-bet/)

#### Jonathan Little（PokerCoaching.com）

「ベットするハンドの割合が多いほど、サイズは小さくすべき。レンジ全体でベットするなら 25〜35% が適切。逆に強いバリューと大きいブラフだけを選んで打つなら 65% 以上のサイズが理にかなう」

「CBet はポジション、相手のタイプ、ボードテクスチャーを考慮して決める。マルチウェイでは強いバリューハンドとプレミアムブラフのみに絞る」

- 出典: [When and How Much to Continuation Bet – Jonathan Little](https://jonathanlittlepoker.com/cbet/)
- 出典: [C-Betting in Poker – How to Build the Optimal Strategy – PokerCoaching](https://pokercoaching.com/blog/c-betting-in-poker/)

#### Phil Galfond（Run It Once）

ポーカー界でのレンジ vs レンジ分析の先駆者の一人。「CBet をするかどうかは、特定ハンド単体で考えるのでなく、レンジ全体でどう振る舞うかを考えるべき」という思想を普及させた。「バリューファースト」の原則：まずバリューハンドを中心に戦略を構築し、そこからブラフのバランスを考える。

- 出典: [Phil Galfond Poker Strategy – PokerVIP](https://www.pokervip.com/strategy-articles/poker-mental-game-and-planning/phil-galfond-poker-strategy)
- 出典: [Turn C-Bet Opportunities in SRP's – Run It Once](https://www.runitonce.com/poker-training/videos/phil-galfond-plo-poker-reviewing-turn-cbet-spots-in-vision/)

---

## 重要概念の整理

### レンジアドバンテージ vs ナットアドバンテージ

GTO Wizard の分析による核心的原則：

- **レンジアドバンテージ**（Range Advantage）：両者のレンジ全体でどちらがボードに合っているかの指標。CBet の**頻度**を決定する
- **ナットアドバンテージ**（Nut Advantage）：誰が最強クラスのハンドを持ちやすいかの指標。CBet の**サイズ**を決定する

例：AAA-2-2 のようなペアボードは PFR がレンジアドバンテージを持つが、ナットアドバンテージは限定的 → 高頻度・小サイズ CBet が適切

- 出典: [The Mechanics of C-Bet Sizing – GTO Wizard (2024-07-09)](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/)

### バリューとブラフのバランス比率

GTO 推奨：フロップではバリュー 2〜3 に対してブラフ 1 の比率（2:1 〜 3:1）
- 例：バリューハンドが 9 コンボなら、ブラフは 3〜4 コンボが目安
- フォールドエクイティが高いほどブラフの比率を増やせる

---

## 本書への適用

### 第7章（フロップ編）での活用

1. **CBet の3目的を冒頭で整理する表**：バリュー・ブラフ・プロテクションを縦軸に、ハンド例・サイズ・狙い・ボード条件を横軸にした早見表として掲載

2. **Range CBet の実戦例**：ドライボードでの 33% CBet がなぜ有効かを、「ほとんどのハンドがボードを外す」原理から説明

3. **してはいけない場面のチェックリスト**：相手のレンジがボードに合っている時・マルチウェイ・OOP でのウェットボードなど

4. **Doug Polk の命名ルール引用**：「ポーライズしたレンジには大きいサイズ、レンジ全体ベットには小さいサイズ」を読者向けの簡易ルールとして提示

5. **レンジアドバンテージの概念**：第12章（レンジ思考）の伏線として、「なぜプリフロップレイザーが有利なのか」をフロップ段階で意識させる

### 第6章（GTO 導入）との接続

- 「バリューファースト」（Galfond の原則）をここで紹介し、GTO 章で深める構成にする
- レンジアドバンテージ・ナットアドバンテージの用語をここで定義し、以降の章で繰り返し使う

### 付録への展開

- ボードテクスチャー別 CBet 頻度・サイズ一覧表（ドライ/ウェット × IP/OOP のマトリクス）
