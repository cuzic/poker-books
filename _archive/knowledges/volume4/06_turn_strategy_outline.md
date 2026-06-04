# 巻3 第II部 ターン戦略 — 論点リスト

検索日: 2026-04-21

## 概要

本書巻3 第II部（全7章）でターン戦略を体系的に扱うための論点整理。
各章について「何を教えるか」「実戦例の必要数」「根拠とする GTOデータ」
「巻2 D3 / 9マスマトリクスとの接続点」を明記する。

巻2 で既出の概念には [→巻2] タグを付け、重複執筆を避ける。

---

## 第II部 全体の設計方針

### ターンの本質的な特性 (GTOの示す3原則)

GTO Wizard ブログ「Principles of Turn Strategy」より:

1. **ハンドバリューの明確化**: フロップより手の強さが確定に近づき、
   各ハンドが「強い / 中程度 / ブラフ」の役割を明確に持ち始める。
2. **エクイティ駆動の行動**: エクイティが高いほどベット意欲が高まる。
   ナッツアドバンテージがあるほど大サイズが選択される。
3. **中程度ハンドのチェックシフト**: ミディアムハンドはフロップで保護済み
   であり、ターンでのベット動機が減る。バリューかブラフに二極化が進む。

出典: [Principles of Turn Strategy - GTO Wizard](https://blog.gtowizard.com/principles-of-turn-strategy/)

### 巻2 との分担境界

| 概念 | 巻2 で扱う範囲 | 巻3 で扱う範囲 |
|------|--------------|--------------|
| D3 ボードスコア | フロップの分類基準 [→巻2] | ターンカードへの拡張 |
| 9マスマトリクス | フロップ CB判断の3×3マス [→巻2] | ターンでの行列シフト |
| SPR | フロップ CBのコミット閾値 [→巻2] | ターン後の残りSPRと行動 |
| HandScore | フロップ判定式 [→巻2] | ターンでの再計算ロジック |
| MDF | フロップコール/フォールドの理論値 [→巻2] | ターンでの更新計算 |

---

## 第1章 ターンカードの分類

### 何を教えるか

フロップの3枚に1枚が加わることでボードテクスチャが変化する。
その変化を「オーバー / ブランク / コネクティング / スートコンプリート」の
4カテゴリーに分類し、各カテゴリーが戦略に与える影響を解説する。

#### 4カテゴリーの定義

| カテゴリー | 定義 | 代表例 |
|-----------|------|--------|
| **オーバーカードターン** | フロップの最高カードより大きいランク | フロップ T87 にKが落ちる |
| **ブランクターン** | どちらのレンジにもほぼ影響しないカード | フロップ KT5 に2が落ちる |
| **コネクティングターン** | ストレートやドローを強化・完成させるカード | フロップ J97 に8が落ちる |
| **フラッシュコンプリーティングターン** | フラッシュドローを完成させるカード | フロップ K♥T♥4♣ に♥が落ちる |

#### GTOが示すターンカード評価の非直感性

GTO Wizard「The Worst Turn Card」より:
- ピュアなオーバーカードターン（A, K の高ランク）は、
  フロップでのブラフの多くをミスさせるため、
  **IP 側（プリフロップレイザー）のレンジ下位20%に位置する**。
- 逆説として、「良いターンカード」はコネクティング系（ストレート完成）
  やブリックだが、IP が弱くなるわけではなく「構造が変化する」。

出典: [The Worst Turn Card - GTO Wizard](https://blog.gtowizard.com/the-worst-turn-card/),
[How To Analyze Turn Textures In Poker - GTO Wizard](https://blog.gtowizard.com/how-to-analyze-turn-textures-in-poker/)

#### 巻2 D3 との接続

D3 スコアはフロップ3枚の組み合わせを評価する [→巻2]。
ターン1枚を加えた際の「スコア更新ルール」を本章で定義する:

- ブランク: D3スコアほぼ変化なし
- コネクティング: TextureCost が増加 → CBet頻度を下方修正
- オーバーカード: ナッツアドバンテージが IP に移動 → CBet戦略を更新

#### 9マス接続

フロップ9マス（役割 × ボード評価）の行が「ターンでどこにシフトするか」を
図解する。例: 「フロップでブラフセミ」のコンボは、
ブランクターンで「チェックバック or 小ベット継続」にシフト。

### 実戦例の必要数

4〜5問 (各カテゴリー1問 + 複合問題1問)

### GTOデータの根拠

- GTO Wizard「Principles of Turn Strategy」(ターンの役割明確化)
- GTO Wizard「How To Analyze Turn Textures In Poker」(4分類)
- GTO Wizard「The Worst Turn Card」(オーバーカードの非直感性)

---

## 第2章 フロップ → ターンのレンジ遷移

### 何を教えるか

フロップで双方のレンジがどう変化しているかを「エクイティバケット」で
可視化し、ターン戦略の前提を整理する。

#### レンジ遷移の主要メカニズム

GTO Wizard「Interpreting Equity Distributions」「The Magic of Equity Buckets」より:

1. **ブラフの自然消滅**: フロップCBet後にコールされた相手のレンジは
   強化済み。IP 側のブラフは「アウツが減る or 残る」に二極化。
2. **中程度ハンドの固定化**: TP/2P系はターンで大きく強弱が変わらない。
   チェックで「保護不要」という判断が増える。
3. **BB の逆転現象**: フロップで大量フォールドした後のBBレンジは
   ターンでは相対的に強化される。GTO では「BB がターンで
   IP を上回るエクイティを持つ場合がある」。

出典: [Interpreting Equity Distributions - GTO Wizard](https://blog.gtowizard.com/interpreting-equity-distributions/),
[The Magic of Equity Buckets - GTO Wizard](https://blog.gtowizard.com/the-magic-of-equity-buckets/),
[Principles of Turn Strategy - GTO Wizard](https://blog.gtowizard.com/principles-of-turn-strategy/)

#### ハンドバリューの変化の具体例

「オーバーペアがセカンドナッツ以下になる」典型ケース:

- フロップ T87 で QQ を持つ IP: TP 以上の強ハンド
- ターン J: QQ は依然として強いが、KQ / 96 / J9 が多数ストレート完成
  → QQ の「コンティニュー判断」がより慎重になる

#### 巻2 D3 / 9マス接続

フロップ9マスで「強バリュー」に分類されたコンボが
ターンでどう変化するかを1つの移行表で示す [→巻2 第X章 9マスの使い方]。

#### 本章固有の教え方

**HandScore の再計算**: ターンカードが落ちた後に HandScore を更新する
ステップを導入 [→巻2 HandScore 計算式]。
ターンでは「メイドハンドのグレード」に加え「ドローの残りアウツ」を
再評価することが核心。

### 実戦例の必要数

3〜4問 (フロップ別に異なるターン遷移のパターン)

### GTOデータの根拠

- GTO Wizard「Interpreting Equity Distributions」
- GTO Wizard「Principles of Turn Strategy」
- GTO Wizard「The Art of Turn Probing: Exploiting Checked Flops」

---

## 第3章 ダブルバレル (2nd CBet) の論理

### 何を教えるか

フロップで CBet した後、ターンでも再度 CBet する「ダブルバレル」の
成否を決める条件を体系的に整理する。これが巻3 第II部の中核章。

#### ダブルバレルの平均頻度

GTO 平均値（SRP、BTN vs BB 想定）:

| フロップ CBet サイズ | ターン継続率 (GTOデータ) |
|--------------------|----------------------|
| 33% CBet 後 | 約 50〜60% |
| 50% CBet 後 | 約 45〜55% |
| 75% CBet 後 | 約 40〜50% |
| 全体平均 | 約 50〜70% |

注: 巻2 第25章「ダブルバレルの頻度 GTO では約 50〜70%」と整合 [→巻2]。
本章ではなぜ頻度が変動するかの**条件分岐**を詳解する。

出典: [Turn Barreling in 3-Bet Pots - GTO Wizard](https://blog.gtowizard.com/turn-barreling-in-3-bet-pots/),
[When Should You Continue Barreling on a Brick Turn Card? - Upswing Poker](https://upswingpoker.com/c-bet-turn-barreling-bricks/)

#### バレル継続の判断フロー (3条件)

```
ターンカードが落ちた
    ↓
[条件A] 自分のレンジを強化するか？
    YES → バレル継続の動機大
    ↓
[条件B] 相手のレンジを弱化するか？
    YES → バレル継続の動機さらに大
    ↓
[条件C] フォールドエクイティは十分か？
    NO → チェックバックを検討
    YES → バレル継続
```

#### ダブルバレル成功率の決め手

GTO Wizard 分析より:
- **ナッツアドバンテージ**: 相手が強いハンドで対抗できない時に成功率高
- **フォールドエクイティの評価**: ターンでのベット1回で相手が
  TP相当をフォールドしうるか
- **ブラフの選択**: コネクテッドブラフ（バックドアドロー付き）が
  ブリックターンでも継続できる理由

「バレルの数学」: マルチストリートブラフのEV計算式
EV_double_barrel = P(fold_turn) × pot + P(call_turn) × EV_river_barrel

出典: [The Math of Multi-Street Bluffs - GTO Wizard](https://blog.gtowizard.com/the-math-of-multistreet-bluffs/),
[The Value of Fold Equity - GTO Wizard](https://blog.gtowizard.com/the-value-of-fold-equity-experiment/)

#### 打たない条件（ギブアップ）

- ターンカードが相手のコールレンジを強化する（コネクティング系）
- ブラフのアウツが枯渇している
- バリューバレルの数に対してブラフが過多になる

GTO Wizard: ターンでミスしたドローをすべてバレルすると
「オーバーブラフ」になり相手にエクスプロイトされる。
**バリュー : ブラフ = 1 : 1** が理論的最適比率 (ターン時点)。

出典: [Delayed C-Betting - GTO Wizard](https://blog.gtowizard.com/delayed-c-betting/)

#### 巻2 D3 / 9マス接続

フロップ9マスの「CBet判断セル」がターンでどう引き継がれるか [→巻2]:
- バリューCBet → ターンも条件付き継続
- プロテクションCBet → ターンは手役進化に依存
- ブラフCBet → ターンは「アウツ残存か否か」で二分岐

### 実戦例の必要数

5〜6問 (ブランク/コネクティング/オーバーカードターン各2問)

### GTOデータの根拠

- GTO Wizard「Turn Barreling in 3-Bet Pots」
- GTO Wizard「The Math of Multi-Street Bluffs」
- GTO Wizard「Delayed C-Betting」
- Upswing Poker「When Should You Continue Barreling on a Brick Turn Card?」

---

## 第4章 ターンディフェンス (コール / レイズ / フォールド)

### 何を教えるか

OOP（BB 等）でターンの相手ベットに直面した際の防御戦略。
コール・チェックレイズ・フォールドの使い分け基準を整理する。

#### ターンチェックレイズの頻度と条件

GTO Wizard「Turn Check-Raise Heuristics」より:
- フロップのチェックレイズは10〜15% [→巻2 第14章]
- ターンのチェックレイズはフロップより**使用頻度が下がる**傾向
- 理由: ターンでは双方のレンジが固まり、チェックレイズ後の
  コンティニュー率が上がるためリスクが大きくなる

**チェックレイズの主な使い所**:
- セット / ツーペアへの成長 (バリューCR)
- ナッツドロー（フラッシュドロー + ペア等）のセミブラフ
- ターンカードで自分のレンジが大幅に強化されたとき

出典: [Turn Check-Raise Heuristics - GTO Wizard](https://blog.gtowizard.com/turn-check-raise-heuristics/),
[Check-Raising a Single Pair - GTO Wizard](https://blog.gtowizard.com/check-raising-a-single-pair/)

#### MDF (最低防御頻度) のターンへの適用

[→巻2 MDF の定義と計算]:
ターンでのポット規模は拡大しているため、MDF は変わらないが、
「コールで防御するか、チェックレイズで防御するか」の内訳が変化する。

一般則:
- ベットサイズが小 (33% pot 以下): チェックコール多用
- ベットサイズが大 (75% pot 以上): チェックレイズを組み込む必要

出典: [MDF & Alpha - GTO Wizard](https://blog.gtowizard.com/mdf-alpha/),
[Round Out Your Defense: The Power of Raising - GTO Wizard](https://blog.gtowizard.com/round_out_your_defense_the_power_of_raising/)

#### フォールド基準の変化

ターンでのフォールドは「ブラフキャッチャーを手放す」行為。
フロップより合理的にフォールドできる基準:

- 残りドローが1アウツ以下
- SPR がコミットライン未満で、勝てるハンドがほぼない
- ターン CB が明確なナッツライン（セットの強さを示す）

#### 巻2 D3 / 9マス接続

巻2 の「防御9マス」（OOPのコール/CR/フォールドの分類）の
ターン版アップデート。フロップより「各セルの手強さ基準が上がる」ことを図示。

### 実戦例の必要数

4問 (コール正解/CR正解/フォールド正解/複合問題 各1問)

### GTOデータの根拠

- GTO Wizard「Turn Check-Raise Heuristics」
- GTO Wizard「MDF & Alpha」
- GTO Wizard「Defending vs BB Check-Raise on Paired Flops」

---

## 第5章 ターンチェックバック・誘発戦略

### 何を教えるか

IP プレイヤーがフロップ CBet 後にターンをあえてチェックバックし、
リバーで有利な状況を作る戦略。また OOP のプローブベット（誘発）への対処。

#### チェックバックの論理

GTO Wizard「Delayed C-Betting」より:
- IP のフロップチェックバック後のターン CBet 頻度: **約50〜60%**
  (= チェックバックする40〜50%がチェックバック戦略)
- チェックバックが有効な状況:
  - ミディアムハンド（2nd ペア等）でポットを膨らませたくない
  - ブラフキャッチャー目的でリバーのショウダウンを目指す
  - 相手のリバーブラフを誘う

出典: [Delayed C-Betting - GTO Wizard](https://blog.gtowizard.com/delayed-c-betting/),
[Attacking Aggressive Opponents When They Check Back Flop - GTO Wizard](https://blog.gtowizard.com/attacking-aggressive-opponents-when-they-check-back-flop/)

#### OOP プローブベットへの対処 (IP 側)

GTO Wizard「The Turn Probe Bet」「The Art of Turn Probing」より:
- GTO では OOP はターンの**約 17% の頻度でリード**する
  (= 83% はチェックして IP の行動を待つ)
- OOP がリードしやすいターンカード: コネクティング系（ストレート完成）、
  ブリック系（IPのチェックバックレンジを弱めるカード）
- OOP がリードしにくいカード: A, K, Q, 8, 7（IP のチェックバックレンジを強化）

**IP の対処**:
- 強ハンドはコール or 3-ベット
- ミディアムハンドはコール多用
- フロップのブラフ残存はフォールドを検討

出典: [The Turn Probe Bet - GTO Wizard](https://blog.gtowizard.com/the-turn-probe-bet/),
[The Art of Turn Probing: Exploiting Checked Flops - GTO Wizard](https://blog.gtowizard.com/the-art-of-turn-probing-exploiting-checked-flops/)

#### Delayed CBet (遅延CBet) の実装

[→巻2 第25章 Delayed CBet の概念紹介]:
本章で「なぜ遅らせるか」の論理と「どのハンドで遅らせるか」を詳解:
- フロップでナッツアドバンテージがない → チェックバックで情報収集
- ターンで相手がチェックを見せた → レンジが弱いシグナル → ベット
- 最適な Delayed CBet ハンド: 強いミディアム手 + バックドアドロー

GTO Wizard ソリューション: Delayed CBet スポットでは
3サイズを使用 (20%, 56%, 122%)。

### 実戦例の必要数

4問 (チェックバック正解/Delayed CBet/プローブ対処/誘発完成)

### GTOデータの根拠

- GTO Wizard「Delayed C-Betting」
- GTO Wizard「The Turn Probe Bet」
- GTO Wizard「The Art of Turn Probing: Exploiting Checked Flops」

---

## 第6章 ターン専用のベットサイズ論

### 何を教えるか

フロップより大きなサイズ選択が推奨されるターン固有のベット戦略。
オーバーベット（>100%ポット）の条件と実装を含む。

#### ターンのサイズ選択の一般則

GTO の基本傾向:
- ダブルバレル時は **66%ポット以上**の大サイズが推奨
  (Upswing Poker より)
- ターンでのベットは「バリュー or ブラフ」に二極化し始めるため、
  サイズも小 (ミディアムレンジでチェック) 大 (ポーラライズ) に分化

| ポジション / 状況 | 推奨サイズ |
|------------------|-----------|
| IP ダブルバレル (ナッツアドバンテージあり) | 66〜100% |
| IP ダブルバレル (標準) | 50〜66% |
| OOP プローブベット | 33〜50% |
| オーバーベット条件充足時 | 100〜170% |

出典: [Bet Sizing Strategy: 8 Rules - Upswing Poker](https://upswingpoker.com/bet-size-strategy-tips-rules/),
[Why So Much? An Exploration of Larger-Than-Geometric Bet Sizing - GTO Wizard](https://blog.gtowizard.com/why-so-much-an-exploration-of-larger-than-geometric-bet-sizing/),
[Turn Barreling in 3-Bet Pots - GTO Wizard](https://blog.gtowizard.com/turn-barreling-in-3-bet-pots/)

#### オーバーベット (>100%) の使い所

GTO 条件（GTO Wizard「Overchoice」「Why So Much?」より）:

1. **明確なナッツアドバンテージ**: 自分だけが最強ハンドを持てる
2. **ポーラライズされたレンジ**: 強ハンドとブラフのみ、ミディアムはなし
3. **相手がレイズしにくい**: ナッツアドバンテージが「再レイズ封じ」になる
4. **具体例**:
   - フロップ A♥ T♥ 4♣ → ターン 2♥ (フラッシュ完成): フラッシュを持つ IP はオーバーベット可
   - K♠ Q♠ 3♦ → ターン K♦ (ボードペア): KKx トリップスを IP が持つ

**オーバーベットブラフの条件**:
- 相手の強ハンドをブロックしているコンボを選ぶ (ナッツブロッカー)
- 例: フラッシュ完成ボードでA♥ 保有 → 相手のナッツフラッシュをブロック

出典: [Why So Much? - GTO Wizard](https://blog.gtowizard.com/why-so-much-an-exploration-of-larger-than-geometric-bet-sizing/),
[Overchoice: Making Sense of Multiple Sizings - GTO Wizard](https://blog.gtowizard.com/overchoice-making-sense-of-multiple-sizings/),
[Pot Geometry - GTO Wizard](https://blog.gtowizard.com/pot-geometry/)

#### 幾何学的サイズ (Geometric Sizing) の概念

2ストリート残り (ターン + リバー) での幾何学的ベット:
理論的に相手をコミットさせるサイズ = √(最終ポット / 現在ポット) - 1

例: 現在ポット 30bb、スタック 70bb なら:
幾何学サイズ ≒ 45% (ターン) × 45% (リバー) で相手をオールインコミット

出典: [Pot Geometry - GTO Wizard](https://blog.gtowizard.com/pot-geometry/)

#### 巻2 CBet サイズ論との接続

[→巻2 第10章 ベットサイズ理論]:
フロップのサイズ (33% / 50% / 75%) がターンのサイズ選択に与える影響:
- フロップ 33% → ターンは大サイズで補完が効果的
- フロップ 75% → ターンは継続か完全ギブアップの二択

### 実戦例の必要数

3〜4問 (標準バレル/オーバーベット/ジオメトリック/ギブアップ)

### GTOデータの根拠

- GTO Wizard「Why So Much? An Exploration of Larger-Than-Geometric Bet Sizing」
- GTO Wizard「Pot Geometry」
- GTO Wizard「Overchoice: Making Sense of Multiple Sizings」
- GTO Wizard「Turn Barreling in 3-Bet Pots」(3サイズの構成)

---

## 第7章 ターン実戦例 20問

### 何を教えるか

第1〜6章で学んだ理論を統合した実戦演習。ハンドを与えて
「ターンのアクションとその根拠」を答える形式。

#### 問題の分類 (20問の構成)

| カテゴリー | 問題数 | 学習ポイント |
|-----------|--------|------------|
| ターンカード分類の判断 | 3問 | オーバー/ブランク/コネクティングの識別 |
| ダブルバレル判断 | 5問 | 継続 vs ギブアップの境界 |
| OOP ディフェンス | 4問 | コール/チェックレイズ/フォールド |
| チェックバック・Delayed CBet | 3問 | IP の誘発・待機戦略 |
| ベットサイズ選択 | 3問 | 標準/大サイズ/オーバーベット |
| 総合演習 (難問) | 2問 | 複数要素が絡む局面 |

#### 実戦例の形式

各問:
1. ゲーム状況 (スタック、ポジション、プリフロップアクション)
2. フロップの結果 (ボード + 双方のアクション)
3. ターンカード (問題)
4. 正解アクションとGTO的理由
5. よくある誤答とその欠点

#### 巻2 実戦例との連続性

巻2 の第23章「フロップドリル」の問題に続く形式 [→巻2 第23章]:
「フロップをこう打ったら、このターンが来た」という
連続ハンド形式で巻2〜巻3 の橋渡しを作る。

### 実戦例の必要数

20問 (本章の全量)

### GTOデータの根拠

- 各問の解説に上記第1〜6章のGTOデータを参照
- GTO Wizard AI トレーナーの公開ハンドレビューを出典として活用

---

## 補足: 収集した GTO データ一覧

### 数値データ

| 項目 | 数値 | 出典 |
|------|------|------|
| IP のフロップCBet後ターン継続率 (平均) | 50〜70% | GTO Wizard / Upswing |
| IP のDelayed CBet頻度 (フロップCB後) | 50〜60% | GTO Wizard |
| OOP のターンリード頻度 | 約17% | GTO Wizard |
| OOP のターンチェック率 | 約83% | GTO Wizard |
| ターン最適バリュー:ブラフ比 | 約1:1 | GTO Wizard |
| リバー最適バリュー:ブラフ比 | 2:1 | GTO Wizard |
| ダブルバレル時推奨最小サイズ | 66%ポット | Upswing Poker |
| GTO Wizard ターンベットサイズ設定 | 25〜30%, 70〜80%, 140〜170% | GTO Wizard |
| Delayed CBet サイズ設定 | 20%, 56%, 122% | GTO Wizard |
| オーバーカードターンのレンジ位置 | 下位20% | GTO Wizard |

### 引用記事一覧 (本知識ファイルで参照)

1. [Principles of Turn Strategy - GTO Wizard](https://blog.gtowizard.com/principles-of-turn-strategy/)
2. [How To Analyze Turn Textures In Poker - GTO Wizard](https://blog.gtowizard.com/how-to-analyze-turn-textures-in-poker/)
3. [The Worst Turn Card - GTO Wizard](https://blog.gtowizard.com/the-worst-turn-card/)
4. [Turn Barreling in 3-Bet Pots - GTO Wizard](https://blog.gtowizard.com/turn-barreling-in-3-bet-pots/)
5. [Delayed C-Betting - GTO Wizard](https://blog.gtowizard.com/delayed-c-betting/)
6. [The Turn Probe Bet - GTO Wizard](https://blog.gtowizard.com/the-turn-probe-bet/)
7. [The Art of Turn Probing: Exploiting Checked Flops - GTO Wizard](https://blog.gtowizard.com/the-art-of-turn-probing-exploiting-checked-flops/)
8. [Turn Check-Raise Heuristics - GTO Wizard](https://blog.gtowizard.com/turn-check-raise-heuristics/)
9. [The Math of Multi-Street Bluffs - GTO Wizard](https://blog.gtowizard.com/the-math-of-multistreet-bluffs/)
10. [Interpreting Equity Distributions - GTO Wizard](https://blog.gtowizard.com/interpreting-equity-distributions/)
11. [The Magic of Equity Buckets - GTO Wizard](https://blog.gtowizard.com/the-magic-of-equity-buckets/)
12. [Why So Much? An Exploration of Larger-Than-Geometric Bet Sizing - GTO Wizard](https://blog.gtowizard.com/why-so-much-an-exploration-of-larger-than-geometric-bet-sizing/)
13. [Pot Geometry - GTO Wizard](https://blog.gtowizard.com/pot-geometry/)
14. [Overchoice: Making Sense of Multiple Sizings - GTO Wizard](https://blog.gtowizard.com/overchoice-making-sense-of-multiple-sizings/)
15. [MDF & Alpha - GTO Wizard](https://blog.gtowizard.com/mdf-alpha/)
16. [Check-Raising a Single Pair - GTO Wizard](https://blog.gtowizard.com/check-raising-a-single-pair/)
17. [When Should You Continue Barreling on a Brick Turn Card? - Upswing Poker](https://upswingpoker.com/c-bet-turn-barreling-bricks/)
18. [Bet Sizing Strategy: 8 Rules - Upswing Poker](https://upswingpoker.com/bet-size-strategy-tips-rules/)
19. [How To Play Overcard Turns After Check-Raising the Flop - Upswing Poker](https://upswingpoker.com/check-raised-flop-part-3/)
20. [Attacking Aggressive Opponents When They Check Back Flop - GTO Wizard](https://blog.gtowizard.com/attacking-aggressive-opponents-when-they-check-back-flop/)

---

## 本書への適用

- 第II部 第1章でターンカード分類を教え、巻2 D3 スコアとの連続性を示す
- 第II部 第3章（ダブルバレル）が最重要章。実戦例も最多 (5〜6問)
- 第II部 全体を通じ「バリュー:ブラフ比の維持」が共通テーマ
- 巻2 第25章の橋渡し内容（Delayed CBet, Double Barrel, SPR）を
  前提知識として明示的に参照し、重複説明を回避する

---

*Researcher: 2026-04-21 調査・整理*
