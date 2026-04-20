# 13: この式がGTOと外れるところ（3bet編）

検索日: 2026-04-19

## 概要

本書の3betスコア式はプリフロップ判断を決定論的ルールに落とし込んでいる。GTOソルバーが出力する3bet戦略とは系統的に乖離するポイントが複数存在する。本ナレッジは第III部のまとめ章（第13章）に向けて、その乖離を8項目で体系化し、「なぜ本書の式で十分か」の根拠を整理する。

---

## 1. ポーラライズ vs リニアレンジ（対UTG vs 対BTN）

### 1-1. 2種類の3betレンジ構造

GTOは3betレンジを2種類の形で構成する。

| タイプ | 構成 | 使用場面 |
|--------|------|---------|
| **ポーラライズ** | プレミアム（AA〜TT、AK）＋ブロッカーブラフ（A5s/A4s等） | IP（インポジション）で相手がタイト（例：BTN vs UTG/HJ） |
| **リニア（マージド）** | 強い〜中強のハンドを連続的に上位から並べる | OOP（アウトオブポジション）で相手がワイド（例：SB vs BTN） |

**ポーラライズを使う理由（BTN vs UTG/HJ）**:
- UTGはタイトなレンジで開くため、フラットコール圏の中強ハンド（JJ〜TT、AQ）はIPからコールして充分に実現できる
- 3betは「ナッツ＋ブロッカーブラフ」に絞り、相手を4betか降りかに追い込む
- 例：BTN vs HJ（60BB）= QQ+/AKs + A5s/A4sをレイズ、JJ/TT/AQ/KQsはフラット

**リニアを使う理由（SB vs BTN）**:
- OOPではポストフロップで不利なため、3betで主導権を取るのが優先
- コールレンジが弱くなりすぎるのを防ぐため、強い中強ハンドも3betに含める
- SBはほぼフォールドか3betの2択に近い（コールが少ない）
- SB vs BTN（40〜60BB）の典型的リニア3betレンジ：88+ / AJo+ / ATs+ / A5s / KQs / KJs / QJs

> "When in position versus a tight early-position open, keep premiums in the 3-bet, flat mediums, and add blocker bluffs like A5s/A4s."
> — Raise the Right Hands: A Field Guide to Linear & Polar 3-Bets（poker.pro）

- 出典: [Raise the Right Hands: A Field Guide to Linear & Polar 3-Bets](https://www.poker.pro/strategy/raise-the-right-hands-a-field-guide-to-linear-polar-3-bets/)（2025年）

### 1-2. 本書スコア式との乖離

本書のスコア式はポジション補正を持つが、「ポーラライズとリニアの切り替え」を明示的に扱っていない。

| 状況 | 本書式の扱い | GTOの扱い | 乖離 |
|------|-------------|----------|------|
| BTN vs UTG、JJでの3bet | スコアが高ければ3bet | フラットが最善 | 本書が3betしすぎ |
| BTN vs UTG、A4sでの3bet | スコアが低くフォールド | 3betブラフ推奨 | 本書が折りすぎ |
| SB vs BTN、AJoでの3bet | スコアに依存 | リニアで3bet推奨 | 概ね整合 |

---

## 2. バリュー/ブラフ比の理論値

### 2-1. ポット比1:1（等量ベット）でのバランス

3betが相手に与えるポットオッズに基づいて、最適なバリュー：ブラフ比が決まる。

**基本公式**:
相手のコールポットオッズ = ベットサイズ ÷ (ポット + ベットサイズ × 2)

典型的な3betサイズ（2.5bb対1bbオープン、3bet = 8bb）:
- 相手が直面するポットオッズ ≈ 33%（3:1の比）
- 搾取不可能な比率: バリュー2：ブラフ1（bluff-to-value = 1:2）

**ストリート別のバリュー比率の変化**:

| ストリート | バリューハンドの割合 | 根拠 |
|-----------|-------------------|------|
| フロップ | 約1/3 | ナッツは少なくブラフが多い状態 |
| ターン | 約1/2 | バリューとブラフが拮抗 |
| リバー | 約2/3 | コンティニュエーションで絞られる |

> "A basic guideline is to use the ⅓ ½ ⅔ rule – you need about ⅓ value on the flop, ½ value on the turn, and ⅔ value on the river."
> — Metavault Poker（2025年）

- 出典: [Mastering the Balance Between Bluffing and Value Betting](https://metavault.poker/en/2025/07/03/bluff-valuebet-balance/)（2025年）
- 出典: [What is the Optimal Bluff-to-Value Ratio](https://www.getcoach.poker/articles/what-is-the-optimal-bluff-to-value-ratio-in-poker/)（getcoach.poker）

### 2-2. 本書式との乖離

本書の3betスコアはハンド強度を点数化するが、「バリュー：ブラフ比」を直接管理しない。

- GTOでは3betレンジに占めるブラフの比率が33〜50%に達する（3betサイズ次第）
- 本書のスコア式は主にバリュー候補を選別する機能を持ち、ブラフ選別の精度が低い
- **乖離の性質**: ブラフが少なすぎる方向に偏りやすい（3betレンジが強すぎて相手にコール・フォールドの正解を簡単に与える）

---

## 3. IP vs OOP での3bet頻度差

### 3-1. ポジション別の頻度差（ソルバーデータ）

| ポジション（3betする側） | 相手オープン位置 | 典型的3bet頻度 | レンジタイプ |
|------------------------|---------------|-------------|-----------|
| BTN（IP） | UTG/HJ | 9〜12% | ポーラライズ |
| CO（IP） | UTG | 8〜11% | ポーラライズ |
| SB（OOP） | BTN | 14〜18% | リニア |
| BB（OOP） | BTN | 10〜14% | リニア（ポーラも混合） |

OOPの3bet頻度がIPより高い（特にSB）のはカウンターインテュイティブだが、コールレンジを弱くしないための構造的必然である。

> "The solver 3-bets approximately 14–18% of hands in the SB vs BTN scenario."
> — Constructing 3-Bet And vs. 3-Bet Ranges（poker.pro）

- 出典: [Constructing 3-Bet And vs. 3-Bet Ranges](https://www.poker.pro/strategy/constructing-3-bet-and-vs-3-bet-ranges-33/)（poker.pro）
- 出典: [Understanding 3-Bet Ranges In 2026](https://www.splitsuit.com/understanding-3-bet-ranges)（SplitSuit、2026年）

### 3-2. ポストフロップでのIP/OOP差

OOPの3betターがポストフロップで直面するチェック頻度はIPより高い：
- OOP 3betター: 平均チェック頻度 33.9%（全フロップ）
- IP 3betター: 平均チェック頻度 19.7%（全フロップ）

これはOOPからの3betがポストフロップを難しくすることを示す。リニアレンジでスタック深めの優位をポストフロップで活かすことが重要。

- 出典: [C-Betting OOP in 3-Bet Pots](https://blog.gtowizard.com/c-betting-oop-in-3-bet-pots/)（GTO Wizard）

### 3-3. 本書式との乖離

本書のスコア式はポジション補正を持つが、「OOPではリニアで広く3bet」という頻度補正が含まれていない。

- SB vs BTNでの3bet頻度が低くなりすぎる可能性がある
- AJo、KQo等の「中強ハンド」をSBから3betするかフォールドするかの判断が本書では保守的に寄りやすい

---

## 4. 4bet耐性とスーテッドの強さ

### 4-1. なぜスーテッドブラフは4betに強いのか

3betブラフで4betを受けた場合、ハンドの処置は2択：
1. **フォールド**（フォールドエクイティの確定）
2. **5bet/コール**（エクイティが必要）

スーテッドハンドが4bet耐性を持つ理由：

| 要素 | 説明 |
|------|------|
| エクイティ残量 | A5sは4betレンジ（AA/KK/QQ/AK）に対して31%のエクイティ。A5oは約26% |
| フラッシュドロー | コールした場合にナッツフラッシュに発展する可能性がある |
| ホイールストレート | A-2-3-4-5でストレートが完成するため、相手のセットを上回れる |
| ブロッカー持続 | コール後もエースがAAをブロックし続ける |

**オフスーツハンドが4bet耐性に欠ける理由**:
- KJoやQTのような「準強ハンド」を4betブラフに使うと、相手のコンティニュ（4bet以上）にドミネートされる
- 相手が降りるべきハンドをブロックしてしまい、フォールドエクイティが下がる

> "Hands like KJs or QTs might tempt a player into a 4-bet, but they force the opposite reaction from your opponent — other players are likely to fold all worse holdings and continue only with hands that dominate them."
> — 888poker, 4-Bet Defense Strategy

- 出典: [Learn 4bet Defending Poker Strategy](https://www.888poker.com/magazine/strategy/4bet-defense-poker-strategy)（888poker）
- 出典: [What Top Poker Pros Already Know About 4-Betting](https://upswingpoker.com/4-bet-size-strategy/)（Upswing Poker）

### 4-2. 本書式との乖離

本書のスコア式における「スーテッドボーナス +2」はオープン編では適切に機能するが、3betの文脈では：

- A5s/A4sのブラフ価値（4bet耐性＋ブロッカー）が一律 +2 では過小評価
- K8s等のキングブロッカー付きスーテッドも3betブラフとして価値があるが、スコアが低い
- 「スーテッド × ブロッカー効果の組み合わせ」は非線形な価値であり、単純加算では捉えられない

---

## 5. ブロッカー効果の定量

### 5-1. エースブロッカーがAAコンボ数に与える影響

デッキに52枚の状態でAAは6コンボ存在する（C(4,2) = 6）。
A5sを保持している場合、相手のAAは **3コンボに半減**する（自分のAが1枚使用済み）。

**定量データ**:

| ハンド保持者 | 相手のAAコンボ数 | 相手のAKコンボ数 |
|-------------|--------------|--------------|
| 保持なし（通常） | 6コンボ | 16コンボ |
| Aを1枚保持（A5s等） | 3コンボ（50%減） | 12コンボ（25%減） |

**4bet頻度への影響**:
- AAとAKは相手が4betする主要ハンドである
- Aブロッカーを持つことで相手の4bet頻度が約1.2ポイント低下する
- これにより3betブラフのフォールドエクイティが実質的に増加する

**A5sのソルバー推奨アクション**:
- 4bet頻度：約70%（3betブラフとして使い、さらに4betブラフにも転用）
- A5sは「ソルバーが最も好む3betブラフ」として知られ、A2sよりも高い評価を受ける

> "Holding an ace removes exactly 3 combinations of AA (from 6 possible) and 12 combinations of AK (from 16 possible), which shifts opponent 4-bet frequencies by approximately 1.2 percentage points."

- 出典: [Why Do Poker Solvers Love Ace Five Suited So Much?](https://www.gipsyteam.com/news/27-11-2024/why-do-poker-solvers-love-ace-five-suited)（GipsyTeam、2024年11月）
- 出典: [Blockers in Poker: Turning the Tables on Your Opponents](https://www.888poker.com/magazine/strategy/using-blockers-as-part-of-your-poker-strategy)（888poker）
- 出典: [How to Play Ace-Five Suited in Cash Games](https://upswingpoker.com/ace-five-suited/)（Upswing Poker）

### 5-2. キングブロッカーの効果

KQs/KJsはAKをブロック（16→12コンボに削減）し、KKをブロック（6→3コンボに削減）する。
ただしAブロッカーほど効果が高くない理由：
- KKはAAより4betレンジ内頻度が低い
- KQs自体が「バリューに近い」ため、ブラフとして使う機会コストが高い

---

## 6. 本書3betスコア式がGTOと外れるハンド

### 6-1. 過小評価されるハンド（本書が折りすぎる）

| ハンド | 本書スコア | GTO評価 | 乖離内容 |
|--------|-----------|--------|---------|
| A2s〜A5s（CO/BTN/SB） | 低〜中（Aの価値 + スーテッドのみ） | 高評価（3betブラフ最優先） | ブロッカー効果・4bet耐性が未考慮 |
| A4s/A3s（BTN vs HJ/CO） | 低（スーテッドエースだが弱い） | ポーラライズ3betブラフとして推奨 | ブラフの文脈での価値が式に未反映 |
| K8s〜K5s（BTN vs CO） | 低（ブロードウェイにならず） | 高レーキ環境で3betブラフとして採用 | キングブロッカー価値を未考慮 |

### 6-2. 過大評価されるハンド（本書が3betしすぎる）

| ハンド | 本書スコア | GTO評価 | 乖離内容 |
|--------|-----------|--------|---------|
| JJ（BTN vs UTG） | 高い（強いペア） | フラットコール推奨（ポーラライズ戦略） | 3betすると弱いハンドを相手がフォールドし、強いハンドだけ残る |
| TT（CO vs UTG） | 中高（ペアボーナス） | ミックス（フラット寄り） | 同上。TT+に対してエクイティが35%程度 |
| AQo（SB vs CO、OOP） | 高い（ブロードウェイ） | リニアレンジで3bet（整合） | 概ね整合だが、GTOよりわずかに頻度が低い可能性 |
| KQo（UTG/HJ） | 高い | 3betを受けた場合に dominated | オープンは合理的だが3betには弱い。本書はオープン/3bet判断を混同しがち |

### 6-3. 整合するハンド群

| ハンド | 本書とGTOの整合性 |
|--------|----------------|
| AA/KK/QQ | 高い（バリュー3betで完全一致） |
| AKs/AKo | 高い（バリュー3bet推奨で一致） |
| AJs/KQs（SB vs BTN） | 中程度（リニアで3bet、本書も高スコアで整合） |

---

## 7. 低ステークスでのGTOとのズレ（相手のミスエクスプロイト）

### 7-1. 低ステークス特有の相手のミス

低ステークス（NL25〜NL50）では相手がGTOと大きく乖離した行動を取る。

| 相手のミス | 内容 | 本書式でのエクスプロイト方向 |
|-----------|------|---------------------------|
| 3betに対してフォールドしすぎ | 3bet頻度2〜5%程度で4betもほぼない | 3betをより頻繁に・広いレンジで使う |
| 3betに対してコールしすぎ | ポストフロップで弱いハンドでコールする | バリュー手を絞り込み、ブラフを減らす |
| 4betしない/ほぼしない | JJでもコールしてしまう | 3betのブラフ比率を上げられる |
| 位置を無視したプレイ | OOPでも広くコール | ポストフロップでのCbet成功率が高い |

> "GTO poker assumes you're playing against sophisticated thinking opponents who are playing well balanced ranges, but anyone who has sat down and played in a micro stakes poker game (2NL to 50NL online) knows this is simply not the case."
> — BlackRain79（2019年、2026年更新）

- 出典: [Why GTO Poker is Really Bad Advice](https://www.blackrain79.com/2019/12/gto-poker-strategy.html)（BlackRain79）

### 7-2. 低ステークスでの本書式の適用指針

相手が3betにフォールドしすぎる場合（フォールド率 > 65〜70%）:
- 本書スコアのしきい値を若干下げて3bet頻度を上げる
- ブラフに使うハンドの選定よりも「3betすること自体」が重要
- A5s/K8s等のブロッカーブラフは相手のミスで十分ペイする

相手が3betにコールしすぎる場合（フォールド率 < 40%）:
- バリューを絞り込む（スコアしきい値を上げる）
- ブラフの頻度を落とす
- これが低ステークスでの「GTO戦略から最も遠ざかる」乖離点

> "Learning GTO is extremely useful, but that doesn't mean you follow it blindly—GTO strategies teach the correct plays in theory, but with that knowledge, we can exploit key mistakes."
> — pokercoaching.com, GTO Preflop Basics

- 出典: [GTO Preflop Basics: Understand Core Principles and Profitable Deviations](https://pokercoaching.com/blog/gto-preflop-basics/)（PokerCoaching.com）
- 出典: [3 Money-Making Exploits That Work in 99% of Poker Games](https://upswingpoker.com/deviate-from-gto/)（Upswing Poker）

---

## 8. 簡易式で十分な根拠（GTO Wizard・Jandaの証言）

### 8-1. GTO Wizardによる簡易化の正当性

GTO Wizard自身が「Simplified Solutions」機能を提供している：
- ヒーローに1〜2サイズのみを割り当てる（フルGTOは多数のサイズを混合）
- 精度: 0.005%〜0.045%（業界標準0.5%を大幅に上回る高精度）
- 「実装しやすさ」と「搾取耐性」の両立を公式に提唱

> "A simplified strategy implemented well will invariably outperform a complicated strategy implemented poorly!"
> — GTO Wizard Blog, Simplified Solutions

- 出典: [Simplified Solutions and a New Interface](https://blog.gtowizard.com/simplified-solutions-and-a-new-interface/)（GTO Wizard）

### 8-2. Matthew Jandaの理論的根拠

Janda『Applications of No-Limit Hold'em』（2013年）はソルバー時代以前の先駆的著作だが：

- 「バランスされたレンジの構築」を理論的に示した
- 「目的は完璧なバランスではなく、ブラフすべき・バリューすべき・コールすべき・フォールドすべきスポットを認識する直感を養うことだ」と明言
- 簡易レンジが理論的に十分であることを間接的に支持している

> "Janda emphasizes repeatedly that the goal isn't to construct perfectly balanced ranges – that's generally beyond human capabilities – but rather to build intuition and to recognize spots where you should be bluffing, value betting, calling, or folding more than you currently are."
> — Upswing Poker review of Applications of No-Limit Hold'em

- 出典: [4 Crucial Things I Learned from the Best Poker Training Book](https://upswingpoker.com/best-poker-training-theory-book-gto-applications-holdem-janda/)（Upswing Poker）
- 出典: [Applications of No-Limit Hold 'em - Google Books](https://books.google.com/books/about/Applications_of_No_Limit_Hold_em.html?id=G3y_EAAAQBAJ)（2013年）

### 8-3. 簡易式で補いきれない部分の扱い方

本書の3betスコア式が補いきれない部分（ポーラライズ/リニア切替、バリュー：ブラフ比）に対しては：

1. **意識的なルール追加**: 「BTN vs UTG の場合、JJ/TT/AQはフラット優先」という補足ルールを設ける
2. **ブラフ枠の明示**: 「A5s/A4sは条件付き3betブラフとして別枠扱い」
3. **しきい値の調整**: OOP（SB）ではリニア思考でスコアのしきい値を1〜2下げる

---

## 本書への適用（第13章 執筆ポイント）

### 章の役割

本章は第III部（第9〜12章）のまとめとして機能する。ポットオッズ・実現率・セットマイニング・3betスコアの4つを統合し、「本書の式の限界と使い方」を明示する。

### 執筆構成案

| 節 | 内容 | キーメッセージ |
|----|------|-------------|
| 冒頭 | 本書3betスコア式の概要復習 | 「式はツールであり万能ではない」 |
| 1節 | ポーラライズ vs リニアの説明 | 「対UTGはポーラライズ、OOPはリニア」 |
| 2節 | バリュー：ブラフ比の理論 | 「3betレンジの1/3〜1/2はブラフが理想」 |
| 3節 | IP/OOP頻度差の実用化 | 「SBはフォールドより3betを選べ」 |
| 4節 | 4bet耐性とスーテッド | 「A5sを折るな。K8sも立派なブラフ候補」 |
| 5節 | ブロッカー効果の数値化 | 「Aを持つだけで相手のAAが半分になる」 |
| 6節 | 式が外れるハンドの一覧 | 具体的ハンド別の補正方針を示す |
| 7節 | 低ステークス応用 | 「相手のミスを最大化する方向に補正」 |
| 締め | 簡易式の正当性と次章へ | 「GTO WizardもJandaも簡易化を支持する」 |

### 数値で示す「近似コスト」

- ブラフ選別のズレ（JJをフラットすべき場面で3betする等）: 約0.05〜0.10bb/hand
- 低ステークスでは相手のミスが0.20〜0.50bb/hand以上の利得をもたらす
- よって本書の近似コストは**相手のミスで十分補填される**

---

## 参考URL一覧

| タイトル | URL | 年 |
|---------|-----|----|
| Raise the Right Hands: A Field Guide to Linear & Polar 3-Bets | https://www.poker.pro/strategy/raise-the-right-hands-a-field-guide-to-linear-polar-3-bets/ | 2025年 |
| Constructing 3-Bet And vs. 3-Bet Ranges | https://www.poker.pro/strategy/constructing-3-bet-and-vs-3-bet-ranges-33/ | 2025年 |
| Preflop Range Morphology（GTO Wizard） | https://blog.gtowizard.com/preflop-range-morphology/ | 不明 |
| C-Betting OOP in 3-Bet Pots（GTO Wizard） | https://blog.gtowizard.com/c-betting-oop-in-3-bet-pots/ | 不明 |
| Simplified Solutions and a New Interface（GTO Wizard） | https://blog.gtowizard.com/simplified-solutions-and-a-new-interface/ | 不明 |
| Understanding 3-Bet Ranges In 2026（SplitSuit） | https://www.splitsuit.com/understanding-3-bet-ranges | 2026年 |
| Polarized Ranges vs Linear Ranges Explained（Upswing） | https://upswingpoker.com/polarized-vs-linear-ranges/ | 不明 |
| 3-Bet Preflop Strategy & Range Charts（Upswing） | https://upswingpoker.com/3-bet-strategy-aggressive-preflop/ | 不明 |
| 3-Bet Bluff Range Construction（Upswing） | https://upswingpoker.com/building-bluffing-ranges-smarter-3-bets/ | 不明 |
| What is the Optimal Bluff-to-Value Ratio（getcoach.poker） | https://www.getcoach.poker/articles/what-is-the-optimal-bluff-to-value-ratio-in-poker/ | 不明 |
| Mastering the Balance Between Bluffing and Value Betting | https://metavault.poker/en/2025/07/03/bluff-valuebet-balance/ | 2025年 |
| How to Win More Chips with Your Bluff-to-Value Ratios（Upswing） | https://upswingpoker.com/what-is-bluff-to-value-ratio/ | 不明 |
| Why Do Poker Solvers Love Ace Five Suited So Much?（GipsyTeam） | https://www.gipsyteam.com/news/27-11-2024/why-do-poker-solvers-love-ace-five-suited | 2024年11月 |
| How to Play Ace-Five Suited in Cash Games（Upswing） | https://upswingpoker.com/ace-five-suited/ | 不明 |
| Understand How to Use Blockers the Right Way（PokerCode） | https://www.pokercode.com/blog/blockers-in-poker | 不明 |
| Blockers in Poker（888poker） | https://www.888poker.com/magazine/strategy/using-blockers-as-part-of-your-poker-strategy | 不明 |
| Learn 4bet Defending Poker Strategy（888poker） | https://www.888poker.com/magazine/strategy/4bet-defense-poker-strategy | 不明 |
| What Top Poker Pros Already Know About 4-Betting（Upswing） | https://upswingpoker.com/4-bet-size-strategy/ | 不明 |
| GTO Preflop Basics（PokerCoaching） | https://pokercoaching.com/blog/gto-preflop-basics/ | 不明 |
| 3 Money-Making Exploits That Work in 99% of Poker Games（Upswing） | https://upswingpoker.com/deviate-from-gto/ | 不明 |
| Why GTO Poker is Really Bad Advice（BlackRain79） | https://www.blackrain79.com/2019/12/gto-poker-strategy.html | 2019年（2026年更新） |
| 4 Crucial Things I Learned from the Best Poker Training Book（Upswing） | https://upswingpoker.com/best-poker-training-theory-book-gto-applications-holdem-janda/ | 不明 |
| Applications of No-Limit Hold 'em（Janda、Google Books） | https://books.google.com/books/about/Applications_of_No_Limit_Hold_em.html?id=G3y_EAAAQBAJ | 2013年 |
| SB vs BB 3bets: Best Strategies（888poker） | https://www.888poker.com/magazine/sb-vs-bb-3bets-strategy | 不明 |
