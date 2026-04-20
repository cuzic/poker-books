# 03: 式で覚えるアプローチの理論的根拠

検索日: 2026-04-19

## 概要

「レンジ表を暗記するのではなく、計算式で判断を再現するアプローチ」の正当性を、
期待値理論・認知科学・既存の簡易式・プロの証言・GTO理論・スタック深度の観点から論証する。

---

## 1. EVの基本式

### 1.1 数学的定義

期待値（Expected Value, EV）の基本式：

```
EV = (勝率 × 獲得額) − (敗率 × 損失額)
   = W% × $W − L% × $L
```

- `W%`：勝つ確率（0〜1）
- `$W`：勝ったときに得られる金額
- `L%`：負ける確率（1 − W%）
- `$L`：負けたときに失う金額

実例（ブラフEV計算）：
- $50 のブラフを $100 のポットに打つ
- 相手が 40% でフォールドすると想定
- `EV = 0.40 × $100 − 0.60 × $50 = $40 − $30 = +$10`
- 期待値 +$10 → このブラフは長期的に利益をもたらす

出典: [Poker Expected Value (EV) Formula | SplitSuit Poker](https://www.splitsuit.com/simple-poker-expected-value-formula)、[What is Expected Value in Poker? | GTO Wizard](https://blog.gtowizard.com/what-is-expected-value-in-poker/)

### 1.2 Sklanskyの「ポーカーの根本定理」

提唱者：David Sklansky
発表：1978年初版（"Poker Theory"）、1987年最終版

> 「もしあなたが相手の手を見て判断するのと同じ行動を取るなら、相手は損する。
> もし違う行動を取るなら、あなたが損する。」

定理の要点：
- すべてのポーカーの意思決定はEVの観点から分析できる
- **「最大EVの選択肢が常に正しい決断である」** という原則を体系化した
- Sklansky Dollars（理論的期待収益）モデルを導入し、EVの視覚化を可能にした

出典:
- [Fundamental theorem of poker - Wikipedia](https://en.wikipedia.org/wiki/Fundamental_theorem_of_poker)
- [The Theory of Poker - Wikipedia](https://en.wikipedia.org/wiki/The_Theory_of_Poker)
- [How David Sklansky Pioneered Modern Poker Strategy - Upswing Poker](https://upswingpoker.com/david-sklansky-poker-strategy/)

### 1.3 EVベース判断の意味

ポーカーでは個々の手の結果は運に左右されるが、長期的な平均（期待値）は戦略の質によって決まる。

> 「我々はポーカーにおいて長期を重視する。短期の結果は大きくぶれることがあるが、
> 長期的には数学が期待値に収束させてくれる。」

出典: [What is Expected Value in Poker? | MasterClass](https://www.masterclass.com/articles/what-is-expected-value-in-poker)

---

## 2. 暗記より計算が優れる理由（認知科学）

### 2.1 ワーキングメモリの限界

**Millerの法則（1956年）**
- George Miller（1956年）が発表した論文 "The Magical Number Seven, Plus or Minus Two"
- 人間のワーキングメモリは一度に **7 ± 2 チャンク**（5〜9個）しか保持できない
- この数字は「項目数」ではなく「意味のあるまとまり（チャンク）」の数

**Cowanの修正理論（2001年）**
- Nelson Cowan（2001年）が "The Magical Number 4 in Short-Term Memory" を発表
- ワーキングメモリの実容量はより少なく **4 ± 1 チャンク**（3〜5個）
- 後続研究（Cowan 2005, 2008）でも4チャンク説が支持された
- Millerの7という数字は、チャンキングが許容されるときの上限に相当

出典:
- [The Magical Number Seven, Plus or Minus Two - Wikipedia](https://en.wikipedia.org/wiki/The_Magical_Number_Seven,_Plus_or_Minus_Two)
- [The magical number 4 in short-term memory - PubMed](https://pubmed.ncbi.nlm.nih.gov/11515286/)
- [Modelling Working Memory Capacity | Journal of Cognition](https://journalofcognition.org/articles/10.5334/joc.387)

**ポーカーへの適用**

169種類のスターティングハンド × 6ポジション = **1,014マスの暗記**が理論上必要。
さらにスタック深度やアクション前の状況が加わると、暗記すべき組み合わせは指数関数的に増加する。
これはワーキングメモリの限界（3〜7チャンク）を遥かに超えており、純粋な暗記は機能しない。

### 2.2 エキスパートのチャンキング

チェスの研究（Chase & Simon, 1973）によれば、熟練チェスプレイヤーは盤面を個々の駒ではなく「意味のあるパターン（チャンク）」として認識する。ランダム配置の盤面では初心者と差がなくなることが、この知識ベースのチャンキングを実証した。

ポーカーへの示唆：
- 「UTGでは22%のハンドをオープン」という**チャンク**として記憶できる
- 個々の169ハンドを覚えるのではなく、**「ポジション × 条件 → 式」** というフレームでチャンク化できる
- 計算式はこのチャンキングを体系的に実現する手段

出典: [Unlocking the power of chunking: Reducing cognitive load | Pearson Schools](https://www.pearson.com/en-au/schools/insights-news/unlocking-the-power-of-chunking-reducing-cognitive-load/)

### 2.3 認知負荷理論（CLT）

- John Sweller が提唱した認知負荷理論（Cognitive Load Theory）
- **外在的認知負荷**（extraneous load）を減らすことで、学習効率が上がる
- 暗記は情報量が多すぎると外在的負荷を激増させ、本質的思考（intrinsic load）を妨げる
- 計算式は情報を圧縮し、外在的負荷を最小化する

> 「チャンキングは認知過負荷を軽減し、学習者の精神的記憶容量を増加させる。
> 従来の暗記と異なり、チャンキングは関連情報をまとめてグループ化するため、
> 想起が容易になるだけでなく、応用も可能になる。」

出典: [Cognitive load - Wikipedia](https://en.wikipedia.org/wiki/Cognitive_load)、[Chunking as a pedagogy | Paul G Moss](https://paulgmoss.com/2023/02/13/chunking-as-a-pedagogy/)

---

## 3. 既存の簡易式

### 3.1 Chen Formula（チェン式）

- 考案者：Bill Chen（数学者・ポーカープロ）
- 掲載書籍：Lou Krieger "Hold'em Excellence"
- 目的：スターティングハンドの強さを数値（スコア）で表現する

**採点ルール：**
| 要素 | 点数 |
|------|------|
| 最高位のカードのみをスコア化 | A=10, K=8, Q=7, J=6, 10〜2 = 牌値÷2 |
| ペア | スコア × 2（最低5点） |
| スーテッド | +2点 |
| ギャップ0 or 1かつQより低い | +1点 |
| ギャップ1（例：KJ） | −1点 |
| ギャップ2（例：KT） | −2点 |
| ギャップ3以上 | −4点 |

**評価：** 現代では実戦使用されることは少なく「歴史的遺産」とされるが、「手の強さを数値化して比較できる」という**計算式アプローチの原型**として重要。

出典: [The Chen Formula | The Poker Bank](https://www.thepokerbank.com/strategy/basic/starting-hand-selection/chen-formula/)、[Chen Formula in Poker | 888poker](https://www.888poker.com/magazine/strategy/chen-formula)

### 3.2 Sklansky Hand Groups（スクランスキー・ハンドグループ）

- 考案者：David Sklansky & Mason Malmuth
- 掲載書籍："Hold'em Poker for Advanced Players"（1976年〜）
- 構造：プレイ可能なスターティングハンドを **8つのグループ（Group 1〜8）** に分類

**概要：**
- Group 1（最強）：AA, KK, QQ, JJ, AKs（スーテッド）
- Group 2：TT, AQs, AJs, KQs, AKo
- Group 8（最弱のプレイ可能域）：低スートコネクター等
- Group 9以下：基本的にフォールド推奨

**使い方：** ポジションに応じてどのグループまでプレイするかを決める。

> 「グループ内の手は基本的に同じ方法でプレイできる」というチャンク化により、
> 169ハンドを8グループに圧縮した。

現代評価：GTO視点では粗い近似だが、「グループ化による判断の体系化」という発想は現代のレンジ思考の礎。

出典: [Sklansky and Malmuth Starting Hand Groups | The Poker Bank](https://www.thepokerbank.com/strategy/basic/starting-hand-selection/sklansky-groups/)

### 3.3 Phil Gordonのアプローチ

- 掲載書籍："Phil Gordon's Little Green Book"（2005年）
- 4と2のルール（Rule of 4 and 2）を重視：フロップ時は残りアウツ×4%、ターン時は×2%でフラッシュドロウ等の完成確率を近似
- スターティングハンドは「厳選された手のみプレイ」という保守的ルールを採用
- EVの概念と期待値計算を一般読者向けに解説した先駆的書籍

出典: [Phil Gordon's Little Green Book | Simon & Schuster](https://www.simonandschuster.com/books/Phil-Gordons-Little-Green-Book/Phil-Gordon/9781982109264)

---

## 4. 直感 vs 計算：プロの意思決定プロセス

### 4.1 Kahnemanのシステム1・システム2理論

Daniel Kahneman（ノーベル経済学賞・2002年）が著書 "Thinking, Fast and Slow"（2011年）で提唱。

| | システム1 | システム2 |
|--|-----------|-----------|
| 速度 | 速い・自動的 | 遅い・意識的 |
| 特性 | 直感・感情 | 論理・計算 |
| 負荷 | 低い | 高い（疲労する） |
| 例 | 顔認識・パターン把握 | 数学の問題・意思決定 |

重要知見：
- システム1は **「信頼性の高い環境で大量の経験を積んだ場合」** に正確に機能する
- エキスパートの「直感」は、実際にはシステム2での反復学習がシステム1に内面化されたもの
- ポーカーの直感も、計算の繰り返しによって形成される

> 「チェスの強手を見つけるといった一部のスキルは、特殊な専門家のみが習得できる。」
> — Kahneman

出典: [Thinking, Fast and Slow - Wikipedia](https://en.wikipedia.org/wiki/Thinking,_Fast_and_Slow)、[Daniel Kahneman Explains The Machinery of Thought | Farnam Street](https://fs.blog/daniel-kahneman-the-two-systems/)

### 4.2 Daniel Negreanuの証言

> 「テーブルに座る前に、自分がどう考えるかを考えることが非常に重要だ。
> 多くの変数があるので、何を考えたいかのアイデアが必要だ。
> 計算式があれば、何度もやるうちに呼吸するように自然になる。」
> — Daniel Negreanu（MasterClass）

Negreanuのプロセス：
1. 長年にわたって相手のレンジを **意識的に（システム2で）** 分析する
2. それが蓄積されることで、**無意識の直感（システム1）** へと内面化される
3. 感情（エモーション）が論理（ロジック）を上回ることを防ぐことを最優先とする

> 「感情に決断を支配させてはいけない。感情が論理より優先されてはならない。」
> — Daniel Negreanu

出典: [How to Think at the Poker Table | Daniel Negreanu - MasterClass](https://www.masterclass.com/classes/daniel-negreanu-teaches-poker/chapters/thinking-about-thinking)、[The Mathematics of Poker | Full Contact Poker](https://fullcontactpoker.com/mathematics-poker/)

### 4.3 Doyle Brunsonの証言

> 「ポーカーで唯一報酬が得られるのは、質の高い決断をすることだ。」
> — Doyle Brunson

Brunsonのアプローチ：
- ポットオッズの損益分岐計算（例：ハーフポットのコールには33%のエクイティが必要）をすべてのストリートで実施
- 「第六感（直感）」は実際には、過去の状況の無意識的な分析から来ると説明
- 心理学的読みを重視しつつも、その基盤には数学的フレームワークがある

出典: [Doyle Brunson and the Strategies That Shaped Modern Poker | Pokerology](https://www.pokerology.com/poker/features/doyle-brunson/)

---

## 5. GTO（確率分布）と簡易式（決定論）の関係

### 5.1 GTOのミックス戦略とは

GTO（ゲーム理論的最適戦略）は、境界ハンドに対して**頻度的なミックスアクション**を採用する。

例：
- あるハンドを「70%レイズ、30%フォールド」で扱うことで相手にパターンを読まれない
- ソルバーは 3-bet の頻度が特定のハンドで「70%レイズ・30%フォールド」と出力することがある
- セルはGTOチャートで複数色（レイズ色＋フォールド色）で表示される

この「ミックス」こそGTOが完全均衡を保つ機構。相手はどちらを仮定しても搾取できない。

出典: [GTO Preflop Charts Explained | BBZ Poker](https://bbzpoker.com/how-to-use-gto-charts/)、[Preflop Range Morphology | GTO Wizard](https://blog.gtowizard.com/preflop-range-morphology/)

### 5.2 簡易式（決定論）で十分な理由

> 「GTO戦略を簡略化する方法として、ミックス頻度と複数のベットサイズを省いた
> 『覚えやすいシンプルGTO』を推奨する。EVの低下はあるが、実装が格段にしやすくなる。」
> — GTO Wizard チーム

理論的根拠：
1. **ミックス戦略が必要な場面は境界ハンドのみ**：コアなバリューハンドとコアなフォールドハンドは100%アクションで問題ない
2. **初心者〜中級者の相手はGTOを実装していない**：相手がGTOから外れている限り、自分がGTOから微妙に外れていてもその差は小さい
3. **エクスプロイト可能性のトレードオフ**：純粋なGTOは対応力が高いが、弱い相手には搾取戦略の方がEVが高い
4. **境界ハンドの頻度より、大きなミスを避けることが優先**：100%フォールドまたは100%オープンでも、ミックスの理論的損失は数bb/100以下

出典: [GTO Poker Strategy vs. Exploitative Play | MyPokerCoaching](https://www.mypokercoaching.com/gto-poker-strategy-vs-exploitative-strategy/)、[How Solvers Work | GTO Wizard](https://blog.gtowizard.com/how-solvers-work/)

### 5.3 均衡と近似の関係

数学的に言えば：
- GTOはナッシュ均衡（Nash Equilibrium）を求める
- 簡易式はその均衡の「近似（approximation）」
- 近似の誤差が十分小さければ、実戦上の損失は無視できる
- 境界ハンドの1〜2bb/100の損失より、大局的なレンジ構築の正確さが重要

---

## 6. レンジ × ポジション × スタックによる近似

### 6.1 プリフロップEVの主要変数

プリフロップでの期待値は主に以下の3変数で近似できる：

| 変数 | 説明 | 影響 |
|------|------|------|
| ハンドのレンジ強度 | スターティングハンドのエクイティ | 基礎EV |
| ポジション | アクション順序の有利さ | EV増幅係数 |
| スタック深度 | 有効スタック（BB単位） | EV計算の範囲 |

GTO分析：
- UTGのオープンレンジ：約10.1%（66+, A9s+, KTs+, AQo+ など）
- BTNのオープンレンジ：約51.3%（幅広いスーテッドとコネクター含む）
- ポジションが後になるほどレンジが大幅に広がる

出典: [Preflop Strategy Guide: Mastering Position and Stack Depth | PokerCoaching](https://pokercoaching.com/blog/preflop-strategy-guide-mastering-position-and-stack-depth/)

### 6.2 スタック深度と戦略の変容

**浅いスタック（〜40BB）：**
- SPR（Stack-to-Pot Ratio）が低い → フロップで簡単にオールインレンジに到達
- ショートスタック戦略：プリフロップでの決着（Push or Fold）が増加
- ポストフロップの複雑性が減少 → プリフロップの選択が支配的
- ワンペアでもスタックオフが正当化されやすい

**中スタック（40〜80BB）：**
- SPRが中程度 → ポストフロップの柔軟性が増す
- トップペアは強いが自動スタックオフにはならない
- プリフロップとポストフロップのバランス

**深いスタック（80〜120BB以上）：**
- SPRが高い → ポストフロップスキルの重要性が増大
- スーテッドコネクターや小ペアの価値が上昇（隠れたモンスター価値）
- プリフロップだけでの決断より、ゲーム全体の戦略が重要

出典: [How Stack Sizes Change Your Range | GTO Wizard](https://blog.gtowizard.com/how-stack-sizes-change-your-range/)、[SPR Strategy And Concept | SplitSuit Poker](https://www.splitsuit.com/spr-poker-strategy)

### 6.3 100BBで標準化する理由

本書が100BBを前提とする根拠：

1. **業界標準**：6-max・9-max キャッシュゲームの標準バイインは100BB
2. **戦略の複雑さのバランス点**：ショートスタックほど単純でなく、ディープスタックほど複雑でない
3. **学習効率**：100BBでの戦略を習得することで、他のスタック深度への応用が容易になる
4. **最大多数のシナリオをカバー**：オンライン・ライブともに100BBが最頻出の初期スタック
5. **ポストフロップ能力の重要性が表れる**：純粋な暗記よりも「式で判断する能力」が活きる深度

> 「100BBでは、オールイン選択肢は基本的に使用しない。99BBをリスクにかけて5BBを獲得しようとする
> リスク/リワード比は著しく不均衡だからだ。」

出典: [Effective Stack Size | Upswing Poker](https://upswingpoker.com/effective-stack-size/)

---

## 7. 本章への適用

### 第3章「式で覚えるという発想」で使える論点

| 論点 | 根拠 | 使いどころ |
|------|------|----------|
| 1,014マスは暗記できない | Miller/Cowan の認知限界 | 冒頭・問題提起 |
| EVがすべての基礎 | Sklansky（1978年〜）の根本定理 | 式の正当性説明 |
| 計算が内面化されると直感になる | Kahneman + Negreanu証言 | 「なぜ式を学ぶのか」の答え |
| 既存の式も同じアプローチ | Chen式・Sklansky Groups | 先行事例として |
| GTO自体が近似でよいと認めている | GTO Wizard の公式解説 | 「完璧でなくていい」の根拠 |
| 3変数で9割の場面をカバー | Stack/Position/Rangeの理論 | 式の設計根拠 |

### 推奨フレーミング

「暗記を求めないのは怠慢ではない——認知科学的に正しいアプローチである。
人間のワーキングメモリが3〜7チャンクしか扱えない以上、1,014マスの完全暗記は不可能だ。
Sklanskyが1978年に示したように、ポーカーはEVの最大化が目標であり、
その目標を最も効率的に達成するのが計算式による判断である。
そしてNegreanuが実証したように、式を繰り返し使うことで直感として内面化される。」

---

## 参考URL一覧

### EV・根本定理
- [Fundamental theorem of poker - Wikipedia](https://en.wikipedia.org/wiki/Fundamental_theorem_of_poker)
- [The Theory of Poker - Wikipedia](https://en.wikipedia.org/wiki/The_Theory_of_Poker)
- [Poker Expected Value (EV) Formula | SplitSuit Poker](https://www.splitsuit.com/simple-poker-expected-value-formula)
- [What is Expected Value in Poker? | GTO Wizard](https://blog.gtowizard.com/what-is-expected-value-in-poker/)
- [How David Sklansky Pioneered Modern Poker Strategy | Upswing Poker](https://upswingpoker.com/david-sklansky-poker-strategy/)

### 認知科学
- [The Magical Number Seven, Plus or Minus Two - Wikipedia](https://en.wikipedia.org/wiki/The_Magical_Number_Seven,_Plus_or_Minus_Two)
- [The magical number 4 in short-term memory - PubMed](https://pubmed.ncbi.nlm.nih.gov/11515286/)
- [Modelling Working Memory Capacity | Journal of Cognition](https://journalofcognition.org/articles/10.5334/joc.387)
- [Cognitive load - Wikipedia](https://en.wikipedia.org/wiki/Cognitive_load)
- [Unlocking the power of chunking | Pearson Schools](https://www.pearson.com/en-au/schools/insights-news/unlocking-the-power-of-chunking-reducing-cognitive-load/)
- [Chunking (psychology) - Wikipedia](https://en.wikipedia.org/wiki/Chunking_(psychology))

### 既存の簡易式
- [The Chen Formula | The Poker Bank](https://www.thepokerbank.com/strategy/basic/starting-hand-selection/chen-formula/)
- [Chen Formula in Poker | 888poker](https://www.888poker.com/magazine/strategy/chen-formula)
- [Sklansky and Malmuth Starting Hand Groups | The Poker Bank](https://www.thepokerbank.com/strategy/basic/starting-hand-selection/sklansky-groups/)
- [Sklansky's Hand Rankings | Poker Wiki Fandom](https://poker.fandom.com/wiki/Sklansky%E2%80%99s_Hand_Rankings)
- [Phil Gordon's Little Green Book | Simon & Schuster](https://www.simonandschuster.com/books/Phil-Gordons-Little-Green-Book/Phil-Gordon/9781982109264)

### プロの証言・直感 vs 計算
- [Thinking, Fast and Slow - Wikipedia](https://en.wikipedia.org/wiki/Thinking,_Fast_and_Slow)
- [Daniel Kahneman Explains The Machinery of Thought | Farnam Street](https://fs.blog/daniel-kahneman-the-two-systems/)
- [How to Think at the Poker Table | Daniel Negreanu - MasterClass](https://www.masterclass.com/classes/daniel-negreanu-teaches-poker/chapters/thinking-about-thinking)
- [The Mathematics of Poker | Full Contact Poker](https://fullcontactpoker.com/mathematics-poker/)
- [Doyle Brunson and the Strategies That Shaped Modern Poker | Pokerology](https://www.pokerology.com/poker/features/doyle-brunson/)

### GTO・ミックス戦略
- [GTO Preflop Charts Explained | BBZ Poker](https://bbzpoker.com/how-to-use-gto-charts/)
- [Preflop Range Morphology | GTO Wizard](https://blog.gtowizard.com/preflop-range-morphology/)
- [What is GTO in Poker? | GTO Wizard](https://blog.gtowizard.com/what-is-gto-in-poker/)
- [GTO Poker Strategy vs. Exploitative Play | MyPokerCoaching](https://www.mypokercoaching.com/gto-poker-strategy-vs-exploitative-strategy/)

### レンジ・ポジション・スタック
- [How Stack Sizes Change Your Range | GTO Wizard](https://blog.gtowizard.com/how-stack-sizes-change-your-range/)
- [Preflop Strategy Guide: Mastering Position and Stack Depth | PokerCoaching](https://pokercoaching.com/blog/preflop-strategy-guide-mastering-position-and-stack-depth/)
- [SPR Strategy And Concept | SplitSuit Poker](https://www.splitsuit.com/spr-poker-strategy)
- [Effective Stack Size | Upswing Poker](https://upswingpoker.com/effective-stack-size/)
- [Short Stack Poker Strategy | PokerTube](https://www.pokertube.com/article/short-stack-poker)
