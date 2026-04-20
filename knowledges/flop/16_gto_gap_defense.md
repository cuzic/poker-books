# 対 CBet：GTO と本書簡易式の乖離ポイント

検索日: 2026-04-20

## 概要

本書の「実効エクイティ + 実現率 + MDF 感覚」による対 CBet 判断式は、
初学者が実行可能な近似として有効だが、GTO（ゲーム理論最適）とは
以下 7 点で体系的に外れる。
各乖離の内容・程度・本書での扱い方を整理する。

---

## 主要な知見

### 知見 1：レンジ全体でのディフェンス設計

**GTO の設計**

GTO はハンドを個別に判定せず、**レンジ全体として MDF を充足**させる。
ベット・コール・チェックレイズの配分は「レンジ中の各ハンドが相互に
どう機能するか」を解く Nash 均衡であり、個別ハンドの EV を最大化するのではない。

GTO Wizard の解析によれば、c-bet 戦略の主要ドライバーは
**ナッツアドバンテージ（nut advantage）とフォールドエクイティ**であり、
ベットサイズはレンジ全体の強度分布から逆算される。
ドライボードでは小さいベット（33%）、ウェットボードでは大きいベット（66〜130%）、
スーパーウェットでは再び小さいベットという「ウェットネス放物線」が典型。

**本書との乖離**

本書は「このハンドは続けるか？」という**個別ハンド判定**に徹する。
レンジ全体の MDF 充足は明示しない。

**影響範囲**

境界ハンド付近で「全フォールド」または「全コール」になりやすく、
レンジがアンバランスになるリスクがある。
ただし低〜中レベルのライブゲームでは相手もレンジを読まないため
実被害は限定的。

- 出典: [The Mechanics of C-Bet Sizing | GTO Wizard](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/)
- 出典: [Flop Heuristics: IP C-Betting in Cash Games | GTO Wizard](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)

---

### 知見 2：コール / レイズ / フォールドの混合戦略

**GTO の設計**

GTO では境界ハンドに**混合戦略（mixed strategy）**を出す。
たとえばあるハンドが「レイズ 17%・コール 38%・フォールド 45%」という
頻度で行動することが均衡解になる。
これにより相手が「このハンドは必ずコールする」という利用可能な情報を排除する。

混合戦略は「EV が同値になる複数のアクションが存在する場合に発生する」
ものであり、境界ハンドほど混合の比率が複雑になる。

**本書との乖離**

本書は「X ならコール、Y ならフォールド」という**決定論的判断**を採用する。
境界ハンドに周波数を割り当てない。

**影響範囲**

正確に「混合すべき」ハンドを純粋戦略で処理する誤差は生じるが、
EV 差は境界ハンドで小さいため実損は軽微。
また初学者には「乱数で行動を変える」運用は現実的でなく、
決定論で 90% 正解が現実的目標として妥当。

- 出典: [How Solvers Work | GTO Wizard](https://blog.gtowizard.com/how-solvers-work/)
- 出典: [GTO in Poker: Practical Game Theory Optimal Strategy with Charts - PokerTube](https://www.pokertube.com/article/gto-in-poker)

---

### 知見 3：チェックレイズ頻度の精密性

**GTO の推奨**

GTO ではフロップでのチェックレイズは**頻度が低く精密**に設計される。
OOP（ポジション外）でのウェットボード c-bet 対応において、
GTO ソルバーは「デフォルトはコール、チェックレイズ頻度は小さい」を示す。
具体的には：
- 小ベット（25%）に対し、約 70% 程度のレンジでコンティニュー
- 大ベット（67%）に対し、約 55% 程度でコンティニュー
- **チェックレイズはいずれの場合も小頻度**（二桁%未満）

MTT のウェットボードではスタック 40BB 時に CBet 頻度を約 20% に絞り、
チェックが主行動になる局面も多い。

**本書との乖離**

本書は「強ハンド＋ナッツドロー」のチェックレイズを推奨するが、
GTO が推奨するほど**頻度のキャリブレーション**は行わない。

**影響範囲**

チェックレイズが多すぎると相手に「ナッツのみ」と読まれてフォールドされ、
バリューが取れない。少なすぎると相手に継続されすぎる。
本書式はゼロよりは正しい方向だが頻度の精密性は欠く。

- 出典: [MTTs: GTO Strategy for C-Betting Out of Position on Wet Boards](https://www.mypokercoaching.com/mtts-gto-strategy-for-c-betting-out-of-position-on-wet-boards/)
- 出典: [Turn Check-Raise Heuristics | GTO Wizard](https://blog.gtowizard.com/turn-check-raise-heuristics/)

---

### 知見 4：フロートの概念

**GTO / 現代理論の定義**

フロート（float）とは「弱いハンドでフロップのベットをコールし、
ターンで相手がチェックしたときにブラフを打って pot を奪う」プレイ。
ポジション（IP）があることが必須条件で、マルチウェイでは成立しにくい。

理想的なフロートハンドは「2 枚のオーバーカード＋バックドアフラッシュドロー」
（KTs, ATs など）。単なるエクイティよりも**ターンでの実現可能なラインの有無**
が判断基準となる。

GTO 理論ではフロートもレンジバランスの一部として組み込まれ、
「IP でハーフポットベットに対し約 58〜72% のレンジでコール」の中に
意図的なフロートが含まれる。

**本書との乖離**

本書は「このハンドのエクイティは足りるか」という静的判断で対 CBet を扱い、
「ターンで奪いに行く意図を持ったコール」というフロートの概念を扱わない。

**影響範囲**

フロートを理解しないと IP でのコール判断が過度に保守的になりがち。
特に「エクイティは低いが IP でポジションがある」ハンドを誤ってフォールドする。

- 出典: [What is Floating in Poker | Beginner's Guide - Upswing Poker](https://upswingpoker.com/floating-poker-float-strategy/)
- 出典: [Float Definition | What is a Float in Poker? | PokerNews](https://www.pokernews.com/pokerterms/float.htm)

---

### 知見 5：BB vs IP の特殊なディフェンス構造

**GTO の要求**

BB はプリフロップに既に投資済みのため、IP のオープンに対してポットオッズが良く
**広いレンジでのコール**が推奨される。
BBのプリフロップコールレンジは通常 35〜50% と広い。

ただし GTO Wizard の分析では、BB は OOP でエクイティが劣後するため
**実際の GTO ディフェンス頻度は MDF より一貫して低い**。
「BB は全ベットサイズに対してフロップで MDF を下回るフォールド頻度を示す」
というソルバー検証がある。

また BB でのフロップ対 CBet ではコールが主体で、適切な頻度での 3bet
（チェックレイズ）を混ぜることがバランス上重要。

**本書との乖離**

本書の HandScore 基準（実効エクイティ＋実現率）は普遍的な閾値で機能するが、
BB の有利なポットオッズを活かした「広めのコール」の根拠を明示しない。
結果として BB での対 CBet 判断が**狭くなりがち**。

**影響範囲**

BB での過フォールドは相手の CBet を過度に利益的にしてしまう。
特に「エクイティは低いがポットオッズが良い」ハンドで損失が生じる。

- 出典: [MDF & Alpha | GTO Wizard](https://blog.gtowizard.com/mdf-alpha/)
- 出典: [Overcalling From the BB | GTO Wizard](https://blog.gtowizard.com/overcalling-from-the-bb/)

---

### 知見 6：SRP vs 3bet ポットでの対 CBet 違い

**GTO の違い**

3bet ポットでは SPR（スタック/ポット比）が大幅に低下し、
ターン・リバーでのオールインが現実的になる。
3bet ポットの典型的な CBet サイズは 33% 前後が多いが、
ソルバーはより小さいサイズの方が理論的に最適とすることもある。

3bet ポットでの防御側の最大の違いは：
- レンジが両者ともに**絞られている**（プレミアムハンド偏重）
- SPR が低いため中程度のハンドで簡単にコミットしてしまう
- MDF の「折りたたみ」がより直接的に機能する（ターンでオールインになる）

SRP（シングルレイズドポット）では SPR が 10 前後で余裕があるが、
3bet ポットでは 3〜5 になることが多く、ハンド判断の基準が変わる。

**本書との乖離**

本書の実効エクイティ式は SRP を主な想定として設計されており、
3bet ポットでの低 SPR による「コールがほぼコミット」という状況を扱わない。

**影響範囲**

3bet ポットで中程度のハンドを本書式で判断すると、
SPR を無視して「エクイティ的にコール」と判定してしまいスタックを溶かすケース
がある。SPR の注意書きが必要。

- 出典: [C-Betting IP in 3-Bet Pots | GTO Wizard](https://blog.gtowizard.com/c-betting-ip-in-3-bet-pots/)
- 出典: [C-Betting OOP in 3-Bet Pots | GTO Wizard](https://blog.gtowizard.com/c-betting-oop-in-3-bet-pots/)

---

### 知見 7：簡易式の利点と「決定論 90% 正解」の根拠

**GTO の複雑性**

GTO 戦略の完全実装は人間には不可能。ソルバーが示す混合戦略・頻度管理・
レンジ全体設計を暗記しリアルタイムで実行することは非現実的。

一方、GTO Wizard などの現代的ソルバー研究は以下を示している：
- 純粋戦略（強ハンドは常にコール、弱ハンドは常にフォールド）は
  境界ハンドで小さな EV 損失を生むが、大局的には機能する
- 「強いハンドで常にベット」という単純ルールは
  「上位 10% のハンドを 90% の頻度でベット」と同等の近似として機能
- 初心者には「レンジ全体を考えるよりハンド単位で判断する方が実行可能」

**初心者向け戦略としての妥当性**

ソルバー研究者も「beginner's GTO heuristic」として：
1. 強いハンドはベット/コール
2. 弱いハンドはフォールド
3. ドローはポットオッズで判断

という純粋戦略の近似が「中低レベルのゲームで 90% 程度の精度」を達成すると
評価している。これは本書の方針と合致する。

- 出典: [An Intro to GTO Poker: A Beginners GTO Strategy Guide](https://www.888poker.com/magazine/strategy/beginners-guide-gto-poker)
- 出典: [GTO Poker: Easy Guide for Beginners](https://www.pokersciences.com/en/articles/gto-poker-science-winning-1)
- 出典: [Exploitative Dynamics | GTO Wizard](https://blog.gtowizard.com/exploitative-dynamics/)

---

## 本書への適用

### 第16章「この式が GTO と外れるところ：対 CBet 編」の章構成案

| セクション | 内容 | 対応知見 |
|-----------|------|---------|
| 16-1 | レンジ設計 vs ハンド判定 | 知見1 |
| 16-2 | 混合戦略と決定論の差 | 知見2 |
| 16-3 | チェックレイズ頻度の精密性 | 知見3 |
| 16-4 | フロートとは何か | 知見4 |
| 16-5 | BB の広いディフェンスと本書式の狭さ | 知見5 |
| 16-6 | 3bet ポットでの注意点（SPR） | 知見6 |
| 16-7 | 簡易式の有効性と限界（90% 正解論） | 知見7 |

### 執筆時の推奨フレーミング

1. **乖離を否定しない**。本書式が GTO でないことを正直に提示する。
2. **乖離の「影響範囲」を明示**する。「低レベルでは問題ない」「中級以上では調整が必要」の区分を明確に。
3. **本書式の利点**（実行可能性・決定論・90% 精度）を積極的に説明する。
4. **ステップアップの道筋**として「GTO ソルバー学習」への誘導を章末に置く。

### 重要な注意書き（本文に必要）

- BB での CBet 対応：ポットオッズが良い局面での「広めのコール」を補足説明
- 3bet ポット：SPR が 3〜5 の場合は本書式ではなく「コールはほぼコミット」の
  意識で判断するよう注記
- フロート：「ターンで取りに行く意図を持ったコール」として IP コールの判断軸に追加

---

## 参考文献一覧

- [MDF & Alpha | GTO Wizard](https://blog.gtowizard.com/mdf-alpha/)
- [Flop Heuristics: IP C-Betting in Cash Games | GTO Wizard](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)
- [The Mechanics of C-Bet Sizing | GTO Wizard](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/)
- [C-Betting IP in 3-Bet Pots | GTO Wizard](https://blog.gtowizard.com/c-betting-ip-in-3-bet-pots/)
- [C-Betting OOP in 3-Bet Pots | GTO Wizard](https://blog.gtowizard.com/c-betting-oop-in-3-bet-pots/)
- [Overcalling From the BB | GTO Wizard](https://blog.gtowizard.com/overcalling-from-the-bb/)
- [Exploitative Dynamics | GTO Wizard](https://blog.gtowizard.com/exploitative-dynamics/)
- [Turn Check-Raise Heuristics | GTO Wizard](https://blog.gtowizard.com/turn-check-raise-heuristics/)
- [3 Spots You Should Actually Consider Minimum Defense Frequency - Upswing Poker](https://upswingpoker.com/mdf-vs-no/)
- [What is Floating in Poker | Beginner's Guide - Upswing Poker](https://upswingpoker.com/floating-poker-float-strategy/)
- [MTTs: GTO Strategy for C-Betting Out of Position on Wet Boards](https://www.mypokercoaching.com/mtts-gto-strategy-for-c-betting-out-of-position-on-wet-boards/)
- [Minimum Defense Frequency | PokerCoaching](https://pokercoaching.com/blog/mdf-poker/)
- [An Intro to GTO Poker: A Beginners GTO Strategy Guide](https://www.888poker.com/magazine/strategy/beginners-guide-gto-poker)
