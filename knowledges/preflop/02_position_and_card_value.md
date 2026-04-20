# 02: ポジションとカード数値化の定量データ

検索日: 2026-04-19

## 概要

「ポジションは力なり（Position is Power）」の定量的根拠、6-maxポジション名称の由来と役割、
カード数値化の理論的背景、ポジション補正値の妥当性、SBの特殊性をまとめた素材集。

---

## 1. ポジションの定量的価値

### 1.1 ポジション別bb/100 実データ（参考値）

フォーラムで共有されているプレイヤーデータから、ポジション別のおおよその勝率レンジが確認できる：

| ポジション | 一般的な bb/100 レンジ（勝ち組の目安） |
|-----------|--------------------------------------|
| BTN       | +30 〜 +40 bb/100 |
| CO        | +24 〜 +28 bb/100 |
| MP        | +17 〜 +21 bb/100 |
| UTG       | +12 〜 +17 bb/100 |
| SB        | −10 〜 −20 bb/100 |
| BB        | −30 〜 −40 bb/100 |

注意：これはプレイヤーのデータ共有から得られた参考値。勝ち組のサンプルであり、GTO純粋値ではない。
ポジション別勝率の分析には各ポジション50,000手以上が必要とされる。
- 出典: [BB/100 by Position | Run It Once](https://www.runitonce.com/plo/bb100-by-position-data/)（2020年代）
- 出典: [Win-Rates by position | PokerVIP](https://www.pokervip.com/forum/general-discussion/win-rates-by-position)

### 1.2 BTN vs BB のEV差（GTO Wizard データ）

GTO Wizardの分析によると、BTN vs BB のスポットでは：
- BTN の平均エクイティ優位：**57.4%**（BB は 42.6%）
- BTN の平均勝得額：**4.04BB**（BB は 2.06BB）

この差はBTNが後から行動できる（IP）ことで、より多くの情報を得て意思決定できるためである。
- 出典: [Common Spots: BTN vs BB | PokerStrategy](https://www.pokerstrategy.com/news/content/Common-Spots:-BTN-vs-BB_128759/)

### 1.3 なぜIPが有利か：理論的根拠

IPプレイヤーが有利な理由は主に2点：

1. **情報優位**：相手のアクションを見てから行動できる。フォールド、コール、レイズの決定に追加情報が使える。
2. **レンジ強度**：一般的にIPプレイヤーはOOPより強いレンジを持つ傾向がある（ポジションでコールする戦略から）。

"The in-position (IP) player gets to make better decisions throughout the hand and also has a stronger range. The combination of the IP player's stronger range and ability to acquire more information than the out-of-position player allows the IP player to collect more EV than his equity shows."
- 出典: [Equity Realization | GTO Wizard](https://blog.gtowizard.com/equity-realization/)（2022年〜）

### 1.4 実現率（EQR: Equity Realization）のポジション別データ

EQR = 実際のポット期待シェア ÷ 生エクイティ

具体例（9♠-3♠-2♦ のボードでBTN vs BB）：
- **BB（OOP側）**：プリフロップエクイティ 46.5%、実現率 **79.1%**（EVは36.8%）
- **BTN（IP側）**：実現率 **118.1%**（エクイティ以上を獲得）

つまりIPプレイヤーはエクイティ以上の価値を実現し、OOPプレイヤーはエクイティを下回る価値しか実現できない。

「60%前後」という定説について：PokerNerveやUpswingの教材でBBやSBのEQRを60〜80%と説明する場合があるが、
これはボードやレンジ構成によって大きく変動する。GTO Wizard公式の定数値としての「IP 100%、OOP 60%」
という固定数値の一次ソースは確認できなかった。79.1%という実測値が最も信頼できる一次データ。

- 出典: [Equity Realization | GTO Wizard](https://blog.gtowizard.com/equity-realization/)
- 出典: [What is Equity Realization & How Does it Impact Strategy | Upswing Poker](https://upswingpoker.com/equity-realization-explained/)
- 出典: [Equity Realization (EQR) Glossary | GTO Wizard](https://pages.gtowizard.com/glossary/equity-realization-eqr/)

---

## 2. 6-maxポジション名称と役割

### 2.1 各ポジションの名称・由来・役割

| 略称 | 正式名 | 由来・語源 | 役割 |
|------|--------|-----------|------|
| LJ   | Lojack（ロージャック） | HJより「低い（Lo）」ポジション。HJと対比した造語 | 6-maxではUTGに相当。最も早いポジション |
| HJ   | Hijack（ハイジャック） | BTN・COより先に「ハイジャック」（奪取）する席 | 2番目に早い。BTNを狙って盗む感覚 |
| CO   | Cutoff（カットオフ） | かつてカード「カット」を担当した席に由来 | BTN直前。BTNに次ぐ有利な後位ポジション |
| BTN  | Button（ボタン） | ディーラーポジションを示すトークン（ボタン）から | 最後に行動できる最強ポジション |
| SB   | Small Blind（スモールブラインド） | 強制ベット（小）の席 | プリフロップのみ2番目に行動するが、ポストフロップは常にOOP |
| BB   | Big Blind（ビッグブラインド） | 強制ベット（大）の席 | プリフロップ最後に行動。ポストフロップはSBより良いが依然OOP |

- 出典: [Explaining Poker Sitting Position Names and Origins | LiveAbout](https://www.liveabout.com/poker-positions-and-seats-2728118)
- 出典: [Hijack Definition | PokerNews](https://www.pokernews.com/pokerterms/hijack.htm)
- 出典: [Under The Gun (UTG) | GTO Wizard Glossary](https://pages.gtowizard.com/en/glossary/under-the-gun-utg/)
- 出典: [Lojack Position | 888poker](https://www.888poker.com/magazine/strategy/the-lojack)

UTG（Under the Gun）の語源：「砲口の下（直接狙われている状態）」を意味する軍事スラングが起源とされる。
最初に行動しなければならないプレッシャーを表現している。
- 出典: [What is Under the Gun in Poker? | The Lodge Poker Club](https://thelodgepokerclub.com/what-is-under-the-gun-in-poker/)

### 2.2 9-max と 6-max の違い

9-max では UTG/UTG+1/UTG+2（3席）が存在するが、6-max ではこれらが存在しない。

**6-maxへの変換原則**：「6-maxのLJ（最初のポジション）は、9-maxのMP（ミドルポジション）相当として扱う」

"When you play in a 6-Max game just pretend that you are playing at a full ring table and the first three seats have been removed, so if you are first to act preflop in a 6-Max game, just pretend that you are playing a 9 handed game and three people have already folded before you."
- 出典: [The Ultimate Guide to 6-Handed Poker | Upswing Poker](https://upswingpoker.com/6-handed-max-poker-strategy/)

| 9-max | 6-max対応 | 備考 |
|-------|----------|------|
| UTG   | (なし) | 6-maxでは最も早い席でもMP相当の広さを持つ |
| UTG+1 | (なし) | |
| UTG+2 | LJ | 6-maxの最初のポジション |
| MP    | HJ | |
| HJ    | CO | |
| CO    | BTN | |
| BTN   | BTN（同） | 最強ポジションは変わらない |

### 2.3 各ポジションのRFI（レイズファーストイン）頻度

GTO推奨値（6-max 100bb、NL500相当）：

| ポジション | RFI頻度（GTO推奨） |
|-----------|-----------------|
| LJ（UTG相当） | 約17.6% |
| HJ          | 約21.4% |
| CO          | 約27.8% |
| BTN         | 約43.5% |
| SB          | 約39〜47%（3ベットorフォールド戦略込み）|

エクスプロイティブな参考値（ポジション解説で広く引用される数値）：
- UTG: 10.1%、UTG+1: 14.3%、HJ: 21.3%、CO: 27%、BTN: 51.3%

- 出典: [6 max 100bb Poker Charts | RangeConverter](https://rangeconverter.com/articles/poker-charts-6-max-100bb-no-limit-texas-holdem)
- 出典: [Preflop Charts: Open Raise in 6-max | FreeBetRange](https://blog.freebetrange.com/article/preflop-charts-open-raise-in-6-max-poker-cash-games)
- 出典: [6-Max Poker Strategy | Beasts of Poker](https://beastsofpoker.com/6-max-poker-strategy/)

---

## 3. カードの数値化

### 3.1 A=14〜2=2 のスケール（標準数値化）

テキサスホールデムにおけるカードランクの標準数値化：

| カード | 数値 |
|-------|-----|
| A     | 14 |
| K     | 13 |
| Q     | 12 |
| J     | 11 |
| T     | 10 |
| 9〜2  | 9〜2 |

Aが14である理由：Aはストレートの最高値（A-K-Q-J-T）と最低値（A-2-3-4-5）の両方に使える。
この二重性はゲームルールに由来し、最高のカード（14）として数値化されるのが自然。

このスケールはプログラム実装（評価アルゴリズム）でも標準的に採用される。
- 出典: [Texas hold 'em starting hands | Wikipedia](https://en.wikipedia.org/wiki/Texas_hold_%27em_starting_hands)
- 出典: [GitHub - poker hand evaluator (A=14スケール採用例)](https://github.com/danielpaz6/Poker-Hand-Evaluator)

### 3.2 Chen Formula との比較（なぜ別スケールを使うか）

Chen Formula（ビル・チェン考案、Lou Krieger著『Hold'em Excellence』掲載）は、
ハンドの「強さスコア」を計算するための独自スケールを採用：

| カード | Chen スコア |
|-------|------------|
| A     | 10 |
| K     | 8 |
| Q     | 7 |
| J     | 6 |
| T〜2  | カード値の半分（Tは5、9は4.5、等） |

**なぜ別スケールか：**
Chen Formulaの目的は「ハンドの相対的強さの近似スコア化」であり、
カードランク間の価値の非線形性（AとKの差は大きいが9と8の差は小さい）を
粗く表現するために独自のスケールを採用している。

A=14スケールが「識別子」であるのに対し、Chen Formulaは「実用的近似評価式」。

修正要素（ペア、スーテッド、コネクター）も加算・減算されるため、
スタンドアロンの数値（A=10, K=8）は別スケールと考えるべき。

例：AK の Chen スコア = A(10点) + ギャップなし(0) = **10点**

- 出典: [Chen Formula | 888poker](https://www.888poker.com/magazine/strategy/chen-formula)
- 出典: [The Chen Formula | The Poker Bank](https://www.thepokerbank.com/strategy/basic/starting-hand-selection/chen-formula/)

### 3.3 現代GTOにおけるAの特別扱い：ブロッカー効果

GTOにおいてAは数値（14）以上の価値を持つ。理由はブロッカー効果：

- **Aホールダーの影響**：Aを持つことでAAやAK、AQsなどのナッツコンボを相手が持つ確率が低下する。
- **3ベットブラフ選択**：A5s、A4sなどの「Aブロッカー付きハンド」は3ベットブラフとして優先される。
  例：高額トーナメントではA2s、A5sでのプリフロップブラフが標準的。
- **リバーブラフ**：Aハイのミスフラッシュドロー（バックドアフラッシュ）はリバーでのブラフ候補として高く評価される（Aがトップペアをブロックするため）。

"Hands like A5s and A4s are frequently used as 3-bet bluffs because they block premium hands like AA, AK, and AQ while maintaining equity when called."
- 出典: [Understanding Blockers in Poker | GTO Wizard](https://blog.gtowizard.com/understanding-blockers-in-poker/)
- 出典: [How to Use Blockers in Poker | PokerCoaching](https://pokercoaching.com/blog/blockers-in-poker/)

---

## 4. ポジション補正の根拠

### 4.1 「UTG −2、MP −1、CO 0、BTN +2、SB −1」補正値の妥当性評価

この補正体系をGTOデータと照合する：

**RFI頻度の相対差から逆算（6-max、CO基準）：**

| ポジション | GTO RFI | CO比 | 対数的差分 |
|-----------|---------|------|-----------|
| LJ（UTG相当） | 17.6% | −10.2pp | 大きなマイナス |
| HJ  | 21.4% | −6.4pp  | 中程度マイナス |
| CO  | 27.8% | 基準(0) | 基準 |
| BTN | 43.5% | +15.7pp | 大きなプラス |
| SB  | 39〜47%（RFI） | +11〜+19pp | 見かけ上プラスだが常にOOP |

注意：SBのRFIは高いが、ポストフロップで常にOOPになるため、実際のEVはCO以下になる。
GTOではSBのEVはCOより明確に低い。SBの「補正 −1」は妥当だが、
「RFIだけ見てSBが有利」という誤解を避ける説明が必要。

**BTNの優位性**：CO（基準）からBTNへのEV増加は大きい。
具体的にはBTNとCOのEV差はフォーラムデータで5〜10bb/100程度が見られる。
「BTN +2、CO 0」の補正はこの実態を単純化したものとして妥当。

**UTGの制限**：LJのRFI（17.6%）はCO（27.8%）の約63%。
「UTG −2」は弱すぎる可能性もあるが、スコアシステムへの入力として
「標準的な難易度差」を表す近似としては実用的範囲。

- 出典: [6 max 100bb Poker Charts | RangeConverter](https://rangeconverter.com/articles/poker-charts-6-max-100bb-no-limit-texas-holdem)
- 出典: [BB/100 by Position | PokerStrategy.com Forum](https://www.pokerstrategy.com/forum/thread.php?threadid=211912)

### 4.2 6-max vs 9-max での補正値調整

6-max では「最初のポジション（LJ）= 9-maxのMP相当」という原則から：
- 6-maxのLJは9-maxの「UTG+2〜MP」に近い広さを持つ
- 9-maxのUTGほどの制限は不要
- 補正値を9-maxから単純に流用する場合、6-maxではLJの「−2」は少し厳しすぎる可能性

6-max基準では「LJ −1.5〜−2、HJ −1、CO 0、BTN +2、SB −1」が
GTOデータとより整合的だが、シンプルさのために整数補正でも実用上は許容範囲。

- 出典: [The Ultimate Guide to 6-Handed Poker | Upswing Poker](https://upswingpoker.com/6-handed-max-poker-strategy/)

---

## 5. SBの特殊性

### 5.1 SBが常にOOPになる構造的理由

プリフロップ：SBはBBより先に行動（2番目に早い）
ポストフロップ：**フロップ以降は常に最初に行動**（最もOOP）

つまりSBはプリフロップの行動順序上の有利（相手の行動を2人分だけ観察できる）を持ちながら、
ポストフロップでは全員に対してOOPになるという構造的矛盾を抱えている。

"From the small blind, you will always be in the worst position postflop. We are going to be first to act in every round after the flop. Being out of position means that our opponents will get to see how we act before they do."
- 出典: [What is the Small Blind & How Should You Play From It? | Upswing Poker](https://upswingpoker.com/small-blind-poker-strategy-tips/)

**EQRへの影響**：
SBのエクイティ実現率は35〜38%程度まで落ちるケースが示されている（45%の生エクイティが35〜38%に低下）。
- 出典: [Small Blind Strategy | PokerVIP](https://www.pokervip.com/strategy-articles/texas-hold-em-no-limit-advanced/small-blind-poker-strategy)

### 5.2 GTOでSBのレンジがタイトになる理由

**3ベット頻度の増加**：
現代GTOにおいてSBはコールよりも「3ベットorフォールド」戦略を優先する。
理由：
1. SBはBBのスクイーズにさらされる（コール後にBBが3ベットする可能性）
2. フラットコールした場合、ポストフロップ全ストリートでOOPになる
3. 投入額（0.5bb）は戦略的に不十分で、1bb（BB）に比べてコールバリューが低い

推奨GTO頻度（SBがCOのオープンに直面した場合の参考値）：
- コールド・コール：約7%
- 3ベット：約8%
- フォールド：残り

- 出典: [Heads up! Exploiting SB's Preflop Mistakes | GTO Wizard](https://blog.gtowizard.com/heads-up-exploiting-sbs-preflop-mistakes/)
- 出典: [Our Small Blind Open Raise Gets 3bet | 888poker](https://www.888poker.com/magazine/sb-vs-bb-3bets-strategy)

### 5.3 SBのコンプリート（リンプ）が許容される場面

GTO的には3ベット推奨が多いが、コンプリートが許容されるケース：

- **ヘッズアップ（HU）の場合**：SBはBTNになり、ポストフロップでもIPになるため戦略が根本的に変わる。
- **BBだけが残った場合のコンプリート**：ポジション的に不利だが、スタックデプス・スポットによって条件次第でリンプが混合戦略に含まれる。
- **一部のGTOソリューション**でSBは70%コンプリートを含む混合戦略を採用する場合もある（出典確認が必要）。

ただし6-maxのNLHEキャッシュゲームの標準スポット（フルテーブルでの標準レイズ後）では、
SBのコールは推奨されず「3ベットorフォールド」が実践的なGTO近似として広く採用される。

- 出典: [Completing from the small blind | PokerVIP](https://www.pokervip.com/strategy-articles/texas-hold-em-no-limit-intermediate/completing-from-the-small-blind)
- 出典: [The Optimal Small Blind Strategy When Facing A Raise | PokerCoaching](https://pokercoaching.com/blog/small-blind-strategy-when-facing-a-raise/)

---

## 本書（第2章）への適用

- **セクション「ポジションを数値化する」**：RFI頻度表（LJ〜BTN）を表形式で掲載可能。BTN=43.5%、LJ=17.6%の数値が具体的裏付けになる。
- **補正値「UTG−2〜BTN+2」の説明**：「GTO的RFI頻度の差をシンプルに整数近似したもの」として提示できる。
- **実現率（EQR）の説明**：「IP側は118%を実現するのに対し、OOP側は79%しか実現できない（BTN vs BB の実例）」という具体数値で示せる。
- **Aのブロッカー効果**：「なぜAは14という数値以上の価値を持つか」を3ベット戦略との絡みで説明する材料として使える。
- **SBの説明**：「プリフロップは有利に見えるが、ポストフロップ全ストリートでOOPになる唯一のポジション」として強調する。

---

## 参考URL一覧

- [Equity Realization | GTO Wizard Blog](https://blog.gtowizard.com/equity-realization/)（2022年〜）
- [Equity Realization (EQR) Glossary | GTO Wizard](https://pages.gtowizard.com/glossary/equity-realization-eqr/)
- [Interpreting Equity Distributions | GTO Wizard](https://blog.gtowizard.com/interpreting-equity-distributions/)
- [Preflop Range Morphology | GTO Wizard](https://blog.gtowizard.com/preflop-range-morphology/)
- [Understanding Blockers in Poker | GTO Wizard](https://blog.gtowizard.com/understanding-blockers-in-poker/)
- [Heads up! Exploiting SB's Preflop Mistakes | GTO Wizard](https://blog.gtowizard.com/heads-up-exploiting-sbs-preflop-mistakes/)
- [BB/100 by Position data | Run It Once](https://www.runitonce.com/plo/bb100-by-position-data/)
- [The Ultimate Guide to 6-Handed Poker | Upswing Poker](https://upswingpoker.com/6-handed-max-poker-strategy/)
- [What is Equity Realization & How Does it Impact Strategy | Upswing Poker](https://upswingpoker.com/equity-realization-explained/)
- [Small Blind Strategy | Upswing Poker](https://upswingpoker.com/small-blind-poker-strategy-tips/)
- [6 max 100bb Poker Charts | RangeConverter](https://rangeconverter.com/articles/poker-charts-6-max-100bb-no-limit-texas-holdem)
- [Preflop Charts: Open Raise in 6-max | FreeBetRange](https://blog.freebetrange.com/article/preflop-charts-open-raise-in-6-max-poker-cash-games)
- [6-Max Poker Strategy 2026 | Beasts of Poker](https://beastsofpoker.com/6-max-poker-strategy/)
- [Chen Formula | 888poker](https://www.888poker.com/magazine/strategy/chen-formula)
- [The Chen Formula | The Poker Bank](https://www.thepokerbank.com/strategy/basic/starting-hand-selection/chen-formula/)
- [Under The Gun | GTO Wizard Glossary](https://pages.gtowizard.com/en/glossary/under-the-gun-utg/)
- [What is Under the Gun in Poker? | The Lodge Poker Club](https://thelodgepokerclub.com/what-is-under-the-gun-in-poker/)
- [Hijack Definition | PokerNews](https://www.pokernews.com/pokerterms/hijack.htm)
- [Lojack Position | 888poker](https://www.888poker.com/magazine/strategy/the-lojack)
- [Explaining Poker Position Names and Origins | LiveAbout](https://www.liveabout.com/poker-positions-and-seats-2728118)
- [Nomenclature for Table Position in Poker | RecPoker](https://rec.poker/announcements/blog/nomenclature-for-table-position-in-poker/)
- [Completing from the small blind | PokerVIP](https://www.pokervip.com/strategy-articles/texas-hold-em-no-limit-intermediate/completing-from-the-small-blind)
- [The Optimal Small Blind Strategy | PokerCoaching](https://pokercoaching.com/blog/small-blind-strategy-when-facing-a-raise/)
- [Common Spots: BTN vs BB | PokerStrategy](https://www.pokerstrategy.com/news/content/Common-Spots:-BTN-vs-BB_128759/)
- [BB/100 by position | PokerStrategy Forum](https://www.pokerstrategy.com/forum/thread.php?threadid=211912)
