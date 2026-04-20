# マルチウェイとICM：式が通用しない場面

検索日: 2026-04-19

## 概要

本書の簡易プリフロップ公式（ベーススコア＋ボーナス）はヘッズアップ〜2-wayポットを前提に設計されており、3人以上のマルチウェイポットとトーナメントICM局面では別のルールセットが必要になる。本章では「なぜ式が通用しないのか」を正面から説明し、読者が適切なリソースに接続できるよう道筋をつける。

---

## 1. マルチウェイポット（3人以上）

### 1-1. レンジ収縮の必要性

マルチウェイでは、コーラーが存在することで「強くなければコールしない」という情報が積み重なる。プリフロップで3-betを打たなかった各プレイヤーはレンジが上限キャップされており、ポストフロップに入る前からレンジ全体が圧縮される。また、大きなベットに対して全員が降りずに残る確率が下がるため、コンティニュエーションベットの成功率も低下する。

- プリフロップの最も多い誤りは「マルチウェイ局面でオープンレンジを広げすぎること」
- ポジションアドバンテージはマルチウェイで増幅する。後ろにプレイヤーがいる状況では参加コストが上昇する
- ベットサイズはマルチウェイで縮小が推奨される。大きなベットへの集団的ディフェンスにより、自分のエクイティリテンションが急速に低下するため
- 出典: [10 Tips for Multiway Pots in Poker | GTO Wizard](https://blog.gtowizard.com/10-tips-multiway-pots-in-poker/)
- 出典: [The Ultimate Guide to Preflop Multiway Pots (And Squeezing) - Upswing Poker](https://upswingpoker.com/multiway-pot-preflop-squeezing-leaks/)

### 1-2. オフスーツブロードウェイの価値低下

AKo・AQo・KQoなどのオフスーツブロードウェイはヘッズアップでは高いバリューを持つが、マルチウェイでは急速に価値が落ちる。

- AQoはマルチウェイでほぼ機能しない。フラッシュやストレートを作りにくく、「トップペア」の絶対強度がヘッズアップより大幅に低下するためである
- コーラーたちのレンジはヘッズアップ時より強く、AQoのトップペアが優位でなくなる場面が多い
- オフスーツ vs スーテッドのエクイティ差は約3〜4%だが、マルチウェイでは複数の対戦相手に対してその差がより顕著に現れる
- 推奨戦略：AQoはフィールドを2人に絞るための3-betブラフ/バリューとして機能させるのが最善。マルチウェイポットには持ち込まない
- 出典: [How to Play Ace-Queen Offsuit in Cash Games - Upswing Poker](https://upswingpoker.com/playing-ace-queen-offsuit/)
- 出典: [Troublesome Hands in Poker - hand2note](https://hand2note.com/Blog/Features/troublesome-hands-in-poker)

### 1-3. スーテッドコネクター・ポケットペアの相対的価値

マルチウェイでは「ナッツを作れる手」の価値が上昇するが、注意点がある。

**ポケットペア（小〜中）:**
- セットを作れば大きなポットを取れる強力なマルチウェイハンド
- セットになれば他のプレイヤーに負けることが少なく、フルハウスも狙える
- ポケットペアはスーテッドコネクターより信頼性が高いマルチウェイハンドとされる
- 出典: [5 Strategic Mistakes Poker Players Should Avoid with Suited Connectors - Upswing Poker](https://upswingpoker.com/suited-connectors-poker-strategy/)

**スーテッドコネクター（76s、87s等）:**
- 「マルチウェイに向いた手」という通説は一部誤りを含む
- GTOソルバーはボタンでレイズ後にコーラーが複数いる場合、中低スーテッドコネクターをフォールドと示すことが多い
- 正確には「マルチウェイで他の手より"悪化が小さい"」というだけで、マルチウェイ最適ハンドではない
- 「全てのハンドはマルチウェイで悪化する。スーテッドコネクターはその悪化が"小さい"だけ」
- ストレート・フラッシュが完成すれば大きなポットを取れる点は有効
- 出典: [Suited Connectors: 3 Myths and 3 Truths To Remember - PokerCoaching](https://pokercoaching.com/blog/suited-connectors-3-myths-and-3-truths-to-remember/)

**まとめ（マルチウェイでの相対的強さ）:**

| ハンドタイプ | ヘッズアップ | マルチウェイ | 評価変化 |
|---|---|---|---|
| AKo, AQo等 | 非常に強い | 弱化大 | 大幅マイナス |
| スーテッドコネクター | 普通 | やや弱化 | 小幅マイナス |
| 小〜中ポケットペア | 普通 | 相対的維持 | ほぼ中立〜小プラス |

### 1-4. スクイーズ（リレイズ）の扱い

スクイーズとは、1人のオープンレイザーと1人以上のコーラーがいる状況での3-bet。

**スクイーズが有効な理由:**
- オープンレイザーとコーラー双方を同時にプレッシャーにかけられる
- コーラーのレンジはキャップされているため、スクイーズに対して強い反撃が難しい

**スクイーズレンジ構築の原則:**
- バリューハンドはヘッズアップ3-betポットで機能する強い手（AQo等も含む）
- ブラフ成分にはポジションを活かしやすいスーテッドコネクターを少量加えてバランスを取る
- スクイーズレンジは「線形（バリュー中心）」で構成するのが基本。マルチウェイほどトップヘビーになる
- AQoはマルチウェイポットでは弱いが「スクイーズでフィールドを縮小する手段として」は有効
- 出典: [How To Construct a Squeezing Range | GTO Wizard](https://blog.gtowizard.com/how-to-construct-a-squeezing-range/)
- 出典: [The Squeeze Play: The Ultimate Guide to Squeezing in Poker - Upswing Poker](https://upswingpoker.com/squeeze-play-poker/)

---

## 2. ICM（独立チップモデル）の基本

### 2-1. ICMとは何か

ICM（Independent Chip Model）はトーナメントのチップに現金価値を割り当てる数学モデル。キャッシュゲームでは1チップ＝1円だが、トーナメントでは賞金構造により「チップの価値」が変動する。

- チップが増えるほど1チップあたりの価値は下がる（逆に持っていないと大きい）
- フォールドそのものが価値を持つ：フォールドすると他のプレイヤーが脱落する可能性が残り、自分の賞金期待値が上がる
- 出典: [Poker Strategy: ICM in tournament poker - RakeRace](https://rakerace.com/news/poker-strategy/2024/05/28/poker-strategy-icm-in-tournament-poker)
- 出典: [The Ultimate Guide to ICM in Poker - PokerOffer](https://thepokeroffer.com/icm-poker-strategy-guide/)

### 2-2. バブル近辺でのタイト化

バブルとは入賞圏まであと1人という状況。ここでICMプレッシャーは最大になる。

- バブルではフォールドEVが正になる場合がある。他のプレイヤーが先に脱落するのを待つ価値がある
- ICMプレッシャーはスタックサイズによって非対称に働く：
  - **ビッグスタック**：エリミネーションリスクが低いためリスクプレミアムが低く、chipEVより広くオープンできる
  - **ミディアムスタック**：最も価値を失いやすい危険なスタック。ショートスタックより先に脱落することを最も恐れる
  - **ショートスタック**：失うものが少ないためICMプレッシャーが最小。アグレッシブに動ける
- 出典: [Extreme ICM: How the Bubble Changes Your Poker Tournament Strategy | BBZ Poker](https://bbzpoker.com/extreme-icm-bubble-strategy/)
- 出典: [Bubble Factor Poker: Master Tournament Equity & ICM Strategy - SomuchPoker](https://somuchpoker.com/poker-term/bubble-factor-poker-tournament-strategy)

### 2-3. ファイナルテーブルでのICMプレッシャー

多くのプレイヤーはバブルでのICMを理解しているが、「ICMプレッシャーはファイナルテーブル近辺で最高潮に達する」ことを見落としている。

- 賞金の大部分がファイナルテーブルで配分されるため、1人の脱落ごとの金額インパクトが大きい
- ファイナルテーブル手前の段階では、小さなポケットペア（55、44）やスーテッドコネクター（76s、87s、98s）が最も価値を失う。インプライドオッズが実現しにくいため
- 出典: [ICM Strategy After the Bubble: How to Play Near the Final Table - PokerCoaching](https://pokercoaching.com/blog/icm-strategy-after-the-bubble-how-to-play-near-the-final-table/)
- 出典: [ICM Strategy in Tournament Poker: GTO vs Exploitative Play – GTO LAB](https://gtolab.com/tournament-poker-strategy/icm-strategy/)

---

## 3. MTT中盤以降の戦略

### 3-1. スタック別戦略

| スタック深度 | 推奨戦略 | 備考 |
|---|---|---|
| 25BB以上 | 通常プリフロップ + ポストフロップ | ChipEVベース |
| 15〜25BB | Push/Fold主体、強い手のみmin-raise | ICMを意識 |
| 10〜15BB | ほぼ全面Push/Fold | min-raise-fold例外あり |
| 10BB以下 | 完全Push/Fold | 特殊例外のみmin-raise |

- ポジションによる差が大きい：ボタン5BBでは45〜55%のハンドをプッシュ可能だが、UTGでは12〜15%にとどまる
- 出典: [10 Push Fold Charts for Poker Tournaments - Upswing Poker](https://upswingpoker.com/push-fold-tournament-strategy-charts/)
- 出典: [Short-Stacked Play in MTTs | GTO Wizard](https://blog.gtowizard.com/short-stacked-play-in-mtts/)

### 3-2. Push/Foldチャートの参考

Push/Foldチャートはスタックが15BB以下になった段階で参照する。主なチャートは以下のハンドクラスに基づく：

- ポケットペア（AA〜22）
- ビッグエース（AK、AQ、AJ等）
- スーテッドエース（A2s〜A9s等）
- ブロードウェイカード（KQ、KJ、QJ等）
- 一部スーテッドコネクター

ICMを考慮したチャートはChipEVチャートより全体的にタイトになる（特にバブル・ファイナルテーブル近辺）。

- 出典: [Push Fold Chart - The Best Poker End-Game Calculations For 2026 - MyPokerCoaching](https://www.mypokercoaching.com/push-fold-chart/)
- 出典: [Poker Tournament Push-Fold Charts | Red Chip Poker](https://redchippoker.com/poker-tournament-push-fold-charts/)

---

## 4. ICMソルバーの概要

### 4-1. ICMIZER 3

ICMIZERはトーナメントプレイヤー向けの代表的なICM計算ソフト。

**主な機能:**
- 最大500人残り選手のNashEquilibrium + ICM計算
- MTTコーチ（Push/Foldトレーナー）
- 自動ハンド履歴分析：実戦のハンド履歴からICM観点での採点が可能
- ブラウザ版とダウンロード版の両方で利用可能（7日間無料トライアルあり）

- 出典: [ICMIZER Suite — Professional Poker Software for tournament players](https://www.icmizer.com/icmizer/)
- 出典: [ICMIZER 3: Maximize Your Edge in Poker Tournaments - Upswing Poker](https://upswingpoker.com/icmizer-3/)

### 4-2. 通常GTO（ChipEV）とICM調整の違い

| 観点 | ChipEV（通常GTO） | ICM調整 |
|---|---|---|
| 前提 | 全チップが等価 | 賞金構造を考慮 |
| 適用局面 | 序盤〜中盤 | バブル、FT近辺、サテライト |
| レンジ傾向 | 相対的に広い | 相対的にタイト |
| ブラフ頻度 | 通常通り | 削減 |
| スモールペア・SCの扱い | 状況次第で有効 | インプライドオッズが実現しないためマイナス調整 |

ICMはユニフォームにタイトを要求するのではなく、スタックの大小によって非対称に働く。カバーするプレイヤーはかなりタイトになるが、カバーされたプレイヤーはそれほど影響を受けない場合もある。

- 出典: [How To Review ICM Preflop Ranges | GTO Wizard](https://blog.gtowizard.com/how-to-review-icm-preflop-ranges/)
- 出典: [How ICM Reshapes 3-Bet Pots (And Why You Can't Trust ChipEV) | GTO Wizard](https://blog.gtowizard.com/how-icm-reshapes-3-bet-pots-and-why-you-cant-trust-chipev/)
- 出典: [Theoretical Breakthroughs in ICM | GTO Wizard](https://blog.gtowizard.com/theoretical-breakthroughs-in-icm/)

---

## 5. 本書の簡易式が通用する範囲

### 5-1. 有効な局面

| 局面 | 簡易式の有効性 | 理由 |
|---|---|---|
| ヘッズアップ | 高い | 前提設計通り |
| 2-wayポット（1コーラー） | おおむね有効 | 大きな乖離は少ない |
| キャッシュゲーム全般 | 高い | ICMなし、チップ価値固定 |
| 3-wayポット | 要注意 | レンジ収縮とハンド選択の修正が必要 |
| 4-way以上 | 通用しない | 別のアプローチが必要 |
| MTTバブル・FT | 通用しない | ICMプレッシャーで全計算が変わる |
| Push/Fold局面（15BB以下） | 通用しない | 専用チャートが必要 |

### 5-2. 限界の明示

本書の公式は以下を前提とする：

1. **1対1（ヘッズアップ〜2-way）のポット**
2. **ICMプレッシャーがない（キャッシュゲームまたはMTT早期〜中盤）**
3. **十分なスタック深度（Push/Fold局面ではない）**

これらの前提が崩れた瞬間、式の精度は急落する。これは式の欠陥ではなく、適用範囲の問題である。

---

## 6. キャッシュゲーム vs MTTの主な戦略差

| 比較軸 | キャッシュゲーム | MTT |
|---|---|---|
| チップ価値 | 固定（1チップ＝1円） | 可変（ICMで変動） |
| スタック深度 | 通常100BB固定 | ブラインドが上がるにつれ減少 |
| フォールドの価値 | なし | バブル近辺でプラス |
| レンジの基準 | ChipEV | ChipEV + ICM調整 |
| アンティ | 基本なし | あり（プリフロップポットが大きくなる） |
| 目標 | 最大EV | 賞金期待値の最大化 |
| インプライドオッズ | 実現しやすい | FT近辺では実現しにくい |
| 難易度 | 比較的シンプル | ICM概念追加で複雑 |

- トーナメント戦略のマスターはキャッシュゲームより難しい。単純な＋EVプレイの積み重ねではなく、M比率・ICM・プッシュフォールドレンジなどの応用概念が必要
- 出典: [Poker Strategies: Tournaments vs. Cash Games | GTO Wizard](https://blog.gtowizard.com/poker-strategies-tournaments-vs-cash-games/)
- 出典: [Difference Between MTT Strategy and Cash Games | MosesBet](https://www.mosesbet.com/difference-between-mtt-strategy-and-cash-games/)

---

## 本書への適用

### 第17章「マルチウェイとICM：式が通用しない場面」での活用

1. **章の冒頭**：「本書の公式はヘッズアップ〜2-wayを前提に設計されている」と明示する。これまでの章で培った式の限界を正直に提示することで読者の信頼を得る。

2. **マルチウェイセクション**：
   - AKoなどオフスーツブロードウェイが「なぜ価値を失うか」を直感的に説明（トップペアの価値がマルチウェイでは相対的に下がる）
   - ポケットペアがセットになったときの強さを対比として使う
   - スクイーズを「マルチウェイを避ける積極的手段」として紹介する

3. **ICMセクション**：
   - フォールドが価値を持つ感覚を読者に伝える（「座っているだけで賞金が増える」）
   - バブルファクターの概念を平易な言葉で説明する
   - ICMIZERなどのツールを「次のステップ」として紹介する（本書での深掘りは不要）

4. **章末まとめ**：
   - 式が使える場面・使えない場面の一覧表を提示する
   - 読者に「自分がどのゲーム種別をプレイしているかを意識する」よう促す

### GTO Wizard 2025アップデートとの連携

GTO Wizardは2025年にマルチウェイポストフロップソリューションの提供を開始する予定であり、今後このトピックの精度が高いデータで検証できるようになる。現時点では「研究途上」であることも読者に伝えると誠実さが増す。
