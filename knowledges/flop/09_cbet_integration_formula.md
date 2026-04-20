# CBet 統合式の全体像

検索日: 2026-04-20

## 概要

本章で提示する CBet 統合式「CBet スコア = HandScore + (BoardScore − 5) + ポジション係数（IP +3、OOP 0）」の妥当性を、GTO Wizard の実証データ、Jonathan Little のフローチャート、Doug Polk の判断体系と照合した。統合式の変数選択・しきい値・限界はいずれも現行の GTO 研究と整合している。

---

## 主要な知見

### 1. 先行事例：統合判断フレームワーク

#### Jonathan Little の Flop C-Betting Flowchart（PokerCoaching）

Jonathan Little は「Flop C-Betting Decision Making Flowchart for cash games」を無料公開している。
フローの分岐軸は (1) レンジアドバンテージ、(2) ボードテクスチャ（ドライ vs ウェット）、(3) ポジション（IP vs OOP）、(4) マルチウェイか否かの 4 軸であり、本書統合式の変数選択と一致する。
具体的な点数化やしきい値は非公開（動画講座内）だが、構造的な骨格は同一。

- 出典: [Flop C-Betting Decision Flowchart](https://pages.pokercoaching.com/flopcbetting) (Jonathan Little / PokerCoaching, 2021)
- 出典: [When and How Much to Continuation Bet](https://jonathanlittlepoker.com/cbet/) (Jonathan Little, 2021)

#### Doug Polk（Upswing Poker）の体系

Polk は「レンジ強度が上回るなら頻度を上げ、ナッツアドバンテージが上回るならサイズを上げる」という 2 軸分離を明示している。
具体的には K62r のような高カードドライボードは「頻度高・小サイズ」、QJT のような高ナッツアドバンテージボードは「頻度低・大サイズ」と区別する。
フローチャートではなく原則ベースだが、BoardScore の高低をベットの方向に変換するロジックは統合式と対応する。

- 出典: [Upswing Poker — Doug Polk On C-Bet Sizing](https://www.cardplayer.com/poker-news/21174-upswing-poker-doug-polk-on-c-bet-sizing) (CardPlayer, 2017)

#### PokerCoaching（Alex Fitzgerald 監修）

「フィット・オア・フォールドボードでは小サイズ、マルチウェイではバックドアドロー以上がなければ CB しない」という実用則を提示。
変数の体系化より状況別の適用に重点を置いたアプローチで、統合式の「限界」節（マルチウェイ別扱い）を裏付ける。

- 出典: [Continuation Betting 101](https://pokercoaching.com/blog/continuation-betting-101/) (PokerCoaching)
- 出典: [C-Betting in Poker – How to Build the Optimal Strategy](https://pokercoaching.com/blog/c-betting-in-poker/) (PokerCoaching)

---

### 2. CBet 判断の主要変数（GTO Wizard の見解）

GTO Wizard は複数の記事で CBet の 2 大変数を明確に定義している。

**レンジアドバンテージ → 頻度（frequency）を決める**
- 「Range advantage tends to influence the frequency of bets, with greater range advantage leading to more frequent betting.」
- プリフロップレイザーはほぼ全ボードでレンジアドバンテージを持つため、頻度は高めに設定できる。
- 特に BTN が BB に対して SRP でプリフロップを開いた場合、GTO Wizard の集計データでは全 1,755 種のフロップを通じて BTN の CB 頻度は約 53〜64%（ソルバー設定により差異あり）。

**ナッツアドバンテージ → サイズを決める**
- 「Nut advantage, however, along with fold equity, are the primary (but not the only) drivers of bet sizing.」
- ウェットボードでナッツアドバンテージが高い側がオーバーベット（75〜125% ポット）を打つ。
- ドライボードでナッツアドバンテージが低い場合は 33% ポットが最適。

**ポジション（IP vs OOP）**
- IP プレイヤーは範囲を広げて CB できる。OOP プレイヤーは絞る必要がある。
- GTO Wizard の記事では OOP（UTG として 3bet ポットなし SRP の例）で「チェック 72%、CB 28%」という値が明示されている。
- これは IP と比べて約 25〜35 ポイント低い頻度であり、統合式の「IP +3」ボーナスがこのギャップの方向性を正しく捉えていることを示す。

- 出典: [Flop Heuristics: IP C-Betting in Cash Games](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/) (GTO Wizard)
- 出典: [The Mechanics of C-Bet Sizing](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/) (GTO Wizard)
- 出典: [C-Betting As the OOP Preflop Raiser](https://blog.gtowizard.com/c-betting-as-the-oop-preflop-raiser/) (GTO Wizard)

---

### 3. IP +3 の妥当性

**GTO データによる IP/OOP 頻度差の実測**

| 状況 | GTO CB 頻度（概算） | 出典 |
|------|-------------------|------|
| BTN（IP）vs BB SRP 全フロップ平均 | 53〜64% | GTO Wizard Aggregate |
| UTG（OOP）vs BB SRP 全フロップ平均 | ~28%（UTG 視点） | GTO Wizard OOP 記事 |
| SB（OOP）vs BB SRP 全フロップ平均 | 小サイズが支配的、大半はチェック | GTO Wizard SB 記事 |

OOP と IP の CB 頻度差は平均 25〜35%pt 程度存在する。これを統合式の 20 点満点スケールに換算すると、各ポイントが約 1.5〜2%pt の頻度差に対応する計算になる。IP +3 点は約 4.5〜6%pt の頻度上昇に相当し、「IP は広く、OOP は絞る」という方向性は正確に反映している。

**ただし**、IP +3 の絶対値は理論的というよりも教育的設計値であり、「スコア閾値で 75%/33%/チェックを区別する」枠組みの中でボードスコアや HandScore と整合するよう調整された値とみなすべきである。

- 出典: [C-Betting As the OOP Preflop Raiser](https://blog.gtowizard.com/c-betting-as-the-oop-preflop-raiser/) (GTO Wizard)
- 出典: [Aggregate Flop Strategy: SB C-Betting in SRP](https://blog.gtowizard.com/aggregate-flop-strategy-sb-c-betting-in-srp/) (GTO Wizard)

---

### 4. しきい値の妥当性検証

#### GTO ソルバーで「75% CB」になるボードとハンド

GTO Wizard の分析によると、高頻度 CB（75% 前後）が正当化される条件は以下のとおり。

- **ドライ高カードボード（K72r、A62r など）**: レンジアドバンテージが最大化し、相手はフォールドしやすい
- **ペアボード（K66、Q55 など）**: 「Paired flops are bet significantly more often than unpaired flops」
- **レインボー disconnected ボード**: 「Rainbow flops are bet most frequently」

これらのボードは本書の BoardScore が 8〜10 に相当し、統合式スコアが 20 以上になりやすい。

#### 「33% CB」の境界

- **Ace-high ウェットボード（A♥T♥8♦ など）**: Ace-high ではフォールドエクイティが低下し頻度は抑制される。小サイズで頻度高、が正しいパターン。
- **接続ミッドカードボード（987ss など）**: 相手レンジがよく当たり、CB は絞って大サイズ。
- GTO Wizard は K44 フロップで BTN の CB 頻度 42.8%、J75r で 40%、632r で 62.5% と明示している。これらは本書の BoardScore 3〜6 レンジに該当し、統合式スコア 13〜19 の境界域と一致する傾向がある。

#### チェックの境界

- **モノトーンボード**: 「DRASTIC decrease in both frequency and sizing」— 本書 BoardScore 1〜2 相当
- **接続ウェットボード（987、JT8 など）**: ナッツアドバンテージが双方に存在し、CB 頻度は最も低い
- OOP プレイヤーが CB 28% という GTO 実測値は、スコア <13 でチェックを選ぶ境界の根拠となる。

- 出典: [Exploiting Excessive C-Betting by IP](https://blog.gtowizard.com/exploiting-excessive-c-betting-by-ip/) (GTO Wizard)
- 出典: [The Mechanics of C-Bet Sizing](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/) (GTO Wizard)

---

### 5. 代表例の CBet スコア計算と GTO との整合性

#### 例 1: KQ on K72r IP（スコア = 15 + 5 + 3 = 23 → 75%）

- GTO Wizard の K72r ボードは「IP では 100% CB」（Run It Once フォーラムの引用）とされる報告がある
- 本書スコア 23 → 75% は GTO 的に「積極的に CB すべき」という方向性と一致
- ただし GTO は「100% CB 小サイズ（33% ポット）」を示す場合が多く、サイジングの教示は別途必要
- 要確認: このボードの GTO サイズはおそらく 33〜50% が最適であり、「75% の頻度で打つ」というより「全ての QQ+ KX 系で CB」が正確な表現

#### 例 2: AT on 987ss IP（スコア = 12 + (3-5) + 3 = 10 → チェック）

- 987ss はウェット接続スートedボード。GTO では CB 頻度が最も低い部類
-「Connected boards: least frequent c-betting」（GTO Wizard IP 記事）
- AT は OESD を持たず、ボードは相手レンジに直撃する → チェックが正当
- 統合式スコア 10 → チェックは GTO 方向性と整合

#### 例 3: 77 on K72r IP（アンダーペア、スコア = 6 + 5 + 3 = 14 → 33%）

- 77 はアンダーペアで K72r では勝率は中程度。GTO では混合戦略（CB と check-back の混合）
- GTO Wizard K44 フロップでの BTN CB 頻度 42.8% は 77/K72r の近似ケースとして参考になる
- スコア 14 → 33% は「CB するが積極的ではない」という方向性で整合的
- 要確認: GTO では 77 の check-back 頻度が高い可能性があり、「33% CB」は学習用に簡略化された値として位置付けるべき

---

### 6. 統合式の限界

#### 限界 1: レンジ全体の考慮が欠落する

統合式はハンド個別のスコアを計算するが、GTO が重視する「レンジ全体のバランス」（value/bluff 比率、保護のためのチェック）を反映しない。
GTO Wizard: 「There are few flops where SB takes a single action with their entire range」（SB CBet 記事）。
実戦では、同じ HandScore のハンドでも、レンジのブロッカー構成や保護の必要性により CB/チェックが異なる。

#### 限界 2: マルチウェイでは別扱い

GTO Wizard（10 Tips for Multiway Pots）: 「Stop rangebetting. Give up more often with trash. Tighten your value betting thresholds. Check back more medium hands.」

ヘッズアップ CB 頻度 70% に対し、3way では最大 50%、4way 以上では強いバリューかナッツドロー以外はチェックが推奨される。
統合式はヘッズアップ SRP を前提として設計されており、マルチウェイには直接適用できない。

- 出典: [10 Tips for Multiway Pots in Poker](https://blog.gtowizard.com/10-tips-multiway-pots-in-poker/) (GTO Wizard)

#### 限界 3: 3bet ポットで係数調整が必要

3bet ポットでは SPR が 3.5〜5 程度まで下がり、OOP の不利が縮小する。GTO Wizard: 「high continuation betting frequencies are typically correct even when out of position in a three-bet pot.」
また OOP 3bettor は相手のコール範囲より強いレンジを持つため、OOP 0 の係数は 3bet ポットでは過小評価になる可能性がある。

実戦的には「3bet ポットでは OOP でも +1〜+2 点を加算」などの補正を加えると精度が上がる（要確認・実証が必要）。

- 出典: [C-Betting OOP in 3-Bet Pots](https://blog.gtowizard.com/c-betting-oop-in-3-bet-pots/) (GTO Wizard)

---

## 本書への適用

- **第9章「CBet 統合式の全体像」**: 統合式の根拠として GTO Wizard の「レンジアドバンテージ→頻度、ナッツアドバンテージ→サイズ」の 2 軸分離を引用する
- **IP +3 の説明**: GTO データで OOP 28%、IP 53〜64% という実測値を示し、方向性の妥当性を裏付ける
- **しきい値の根拠**: K44（42.8%）、J75r（40%）、632r（62.5%）の GTO 実測値を参照しながら、≥20/13-19/<13 の境界が GTO の頻度帯と概ね対応することを説明する
- **限界節**: マルチウェイ・3bet ポットの調整必要性を明示し、統合式をヘッズアップ SRP 向けのヒューリスティックとして位置付ける
- **Jonathan Little フローチャート**: 先行事例として言及し、本書統合式が数値化によって同じ構造をより体系的に扱うことを強調する

---

## 参考文献一覧

| タイトル | 著者/サイト | URL | 発行年 |
|---------|-----------|-----|-------|
| Flop C-Betting Decision Flowchart | Jonathan Little / PokerCoaching | https://pages.pokercoaching.com/flopcbetting | 2021 |
| When and How Much to Continuation Bet | Jonathan Little | https://jonathanlittlepoker.com/cbet/ | 2021 |
| Doug Polk On C-Bet Sizing | Upswing Poker / CardPlayer | https://www.cardplayer.com/poker-news/21174-upswing-poker-doug-polk-on-c-bet-sizing | 2017 |
| Flop Heuristics: IP C-Betting in Cash Games | GTO Wizard | https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/ | 2022-2023 |
| The Mechanics of C-Bet Sizing | GTO Wizard | https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/ | 2022-2023 |
| C-Betting As the OOP Preflop Raiser | GTO Wizard | https://blog.gtowizard.com/c-betting-as-the-oop-preflop-raiser/ | 2022-2023 |
| Aggregate Flop Strategy: SB C-Betting in SRP | GTO Wizard | https://blog.gtowizard.com/aggregate-flop-strategy-sb-c-betting-in-srp/ | 2023 |
| Exploiting Excessive C-Betting by IP | GTO Wizard | https://blog.gtowizard.com/exploiting-excessive-c-betting-by-ip/ | 2023 |
| C-Betting OOP in 3-Bet Pots | GTO Wizard | https://blog.gtowizard.com/c-betting-oop-in-3-bet-pots/ | 2023 |
| 10 Tips for Multiway Pots in Poker | GTO Wizard | https://blog.gtowizard.com/10-tips-multiway-pots-in-poker/ | 2023 |
| C-Betting in Poker – How to Build the Optimal Strategy | PokerCoaching | https://pokercoaching.com/blog/c-betting-in-poker/ | 2023 |
| Continuation Betting 101 | PokerCoaching | https://pokercoaching.com/blog/continuation-betting-101/ | 2022 |
| Sizing Your C-Bets: 3 Factors You Must Consider | Upswing Poker | https://upswingpoker.com/c-bet-sizing-strategy-continuation-bet/ | 2022 |
