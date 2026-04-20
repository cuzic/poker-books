# アウツとエクイティ（Rule of 2 and 4）

検索日: 2026-04-20

## 概要

フロップ以降の意思決定の根幹となる「アウツ計算」と「エクイティ推定」の知識を整理する。
Rule of 2 and 4 の数学的根拠・精度限界・拡張公式、主要ドローの正確な確率値、
ダーティアウツの割り引き、エクイティ実現（EQR）の概念を網羅する。

---

## 1. Rule of 2 and 4 の定義と歴史

### 定義

- **Rule of 4（フロップ段階・両ストリート残り）**: アウツ数 × 4 ≒ 完成確率（%）
- **Rule of 2（ターン段階・1ストリート残り）**: アウツ数 × 2 ≒ 完成確率（%）

### 発祥・命名者

Rule of 4 and 2 という名称を最初に活字にしたのは **Phil Gordon** とされる。
Gordon 自身が「この名称を最初に本に記した」とコメントしており、
彼の著書 *Poker: The Real Deal* および *Phil Gordon's Little Green Book*（Simon Spotlight, 2005）で広まった。

- 出典: [Phil Gordon's Little Green Book（Library of Congress）](https://catdir.loc.gov/catdir/toc/ecip0511/2005010872.html)
- 出典: [The Rule Of 4 And 2 | The 2/4 Pot Odds Shortcut – The Poker Bank](https://www.thepokerbank.com/strategy/mathematics/pot-odds/4-2/)（Phil Gordon coined the term と明記）

### 数学的根拠

フロップ段階では未知カードが 47 枚存在する。

```
1 アウツあたりの確率（ターン） = 1/47 ≒ 2.128%
1 アウツあたりの確率（リバー） = 1/46 ≒ 2.174%
```

ターン＋リバー 2 ストリートで 1 アウツが完成する確率（正確値）:

```
P = 1 - (46/47) × (45/46) = 1 - 45/47 ≒ 4.26%
```

これを丸めると「アウツ × 4」が成立する。
「52 ÷ 100 ≒ 2 倍」という別の説明もあるが、実質的には同じ近似。

### 精度（何 outs まで妥当か）

| アウツ数 | Rule of 4（%） | 実際（%） | 誤差 |
|---------|--------------|----------|-----|
| 4 | 16 | 16.5 | +0.5 |
| 6 | 24 | 24.1 | +0.1 |
| 8 | 32 | 31.5 | -0.5 |
| 9 | 36 | 35.0 | -1.0 |
| 12 | 48 | 45.0 | -3.0 |
| 15 | 60 | 54.1 | -5.9 |
| 16 | 64 | 57.0 | -7.0 |

**結論**: 9 アウツ以下では誤差 1〜2% 以内で実用的。
10 アウツ以上になると過大推定が顕著になる（-5〜7% の乖離）。

- 出典: [Rule of 2 and 4 – Limitations | CasinoReviews](https://www.casinoreviews.net/blog/game-strategies-tips/rule-of-4-and-2-limitations-specifity-of-this-texas-holdem-poker-principle/)
- 出典: [Rule of 2 and 4 Poker – Poker Skill](https://www.pokerskill.com/poker-glossary/rule-of-2-and-4/)

---

## 2. 拡張版公式

### (A) 高アウツ向け補正式（10 outs 以上向け）

```
エクイティ（%） = (アウツ × 4) − (アウツ − 8)
```

例: 15 アウツ → (15 × 4) − (15 − 8) = 60 − 7 = **53%**（実際値 54.1% に近い）

- 出典: [Counting Outs in Poker – PokerCoaching](https://pokercoaching.com/blog/outs-in-poker/)
- 出典: [Poker Outs 101 – Pokerati（2025）](https://pokerati.com/2025/05/poker-outs/)

### (B) Alex Filiakov の Medium 記事（"outs × 3 + 9" 方式）

Alex Filiakov（ACAS）が Medium に投稿した *"Math of Poker: Extending the 2/4 Rule"* では、
両ストリートの合算エクイティを 1 つの式で近似する方法が提案されている。
記事はメンバー限定のため全文確認不可だが、検索で言及される要旨は以下の通り。

- 基本アイデア: 2 つの別々な乗数（×2 と ×4）を状況別に使い分けるのではなく、
  「フロップ段階でのドロー価値」を単一式で近似する。
- アウツ数が大きい（≥10）ケースでの精度改善が目的。

**要確認**: 記事全文は Medium 有料記事のため、式の詳細は未確認。

- 出典: [Math of Poker: Extending the 2/4 Rule – Alex Filiakov, ACAS | Medium](https://medium.com/@alexfiliakov/math-of-poker-extending-the-2-4-rule-9222de9645b7)

### (C) Smart Poker Study の "Revised 4-2 Rule"

Turn 計算では「アウツ × 2 + 1」とすると若干精度が上がることが指摘されている。

- 出典: [Revised 4-2 Rule – Smart Poker Study Podcast #111](https://smartpokerstudy.com/4-2-rule-flop-value-raises-oversized-bets-111/)

---

## 3. 主要ドローのアウツ数と確率

### 正確な確率値一覧

| ドロー | アウツ | ターン完成（%） | リバー完成（%） | 2 ストリート合計（%） |
|-------|-------|--------------|--------------|------------------|
| フラッシュドロー（FD） | 9 | 19.1 | 19.6 | 35.0 |
| OESD（オープンエンドストレートドロー） | 8 | 17.0 | 17.4 | 31.5 |
| ダブルガットショット | 8 | 17.0 | 17.4 | 31.5 |
| 2 オーバーカード | 6 | 12.8 | 13.0 | 24.1 |
| ガットショット | 4 | 8.5 | 8.7 | 16.5 |
| FD + OESD（モンスタードロー） | 15 | 31.9 | 32.6 | 54.1 |
| バックドアフラッシュドロー（BDFD） | — | 約 4%（加算値） | — | — |
| バックドアストレートドロー（BDSD） | — | 約 2%（加算値） | — | — |

**注**: BDFD・BDSD は通常のアウツとして計算できない（2 ストリート連続ヒットが必要）。
単独では 4% 程度の加算エクイティとして扱う。

#### ダブルガットショットの補足

ダブルガットショット（Double Belly Buster / Double Gutshot）は、
2 か所の「内側の穴」を持つ形で、必要なカードが 2 種類 × 4 枚 = 8 アウツとなる。
そのため OESD と同等の確率になる。

例: 手札 T-7、ボード 9-6-4 → 8 で下のストレート、J で上のストレート（各 4 枚）

- 出典: [What Are The Odds of Hitting a Draw in Poker – Upswing Poker](https://upswingpoker.com/odds-hitting-draw-in-poker/)
- 出典: [Poker Drawing Odds & Outs Explained – Upswing Poker](https://upswingpoker.com/poker-drawing-odds-outs-explained/)
- 出典: [Definition of Double Gutshot – PokerZone](https://www.pokerzone.com/dictionary/double-gutshot)
- 出典: [Basic Poker Odds and Outs – CardPlayer](https://www.cardplayer.com/poker-tools/odds-and-outs)

---

## 4. バックドアドロー（BDFD・BDSD）の実効アウツ

バックドアドローはターンとリバーの 2 枚連続ヒットが必要なため、
通常のアウツとして数えられない。実効エクイティへの寄与は以下の通り。

| ドロー種別 | 実質加算エクイティ | 扱い |
|----------|----------------|-----|
| BDFD（バックドアフラッシュドロー） | +約 4%（≒ 2 アウツ相当） | 0.5〜1 アウツとして簡易換算する流派もある |
| BDSD（バックドアストレートドロー） | +約 2% | 0.5 アウツ程度 |

**本書では「+1.5 アウツ」または「+2%」の加算を提案している。**
（Rule of 2 の 1 ストリート分の換算として ×2 = 4%、安全マージンとして 3% 程度）

- 出典: [What Are Backdoor Flush/Straight Draws – Upswing Poker](https://upswingpoker.com/backdoor-flush-straight-draw-tips/)

---

## 5. ダーティアウツ（Dirty Outs）とディスカウント

### 定義

「ダーティアウツ（Dirty Outs）」とは、手を改善するカードであるが、
同時に相手の手をさらに強くしてしまうカードのこと。
別名「デッドアウツ（Dead Outs）」とも呼ぶが、
厳密には「Dead Out = すでに相手に使われているカード」「Dirty Out = 自分を助けても相手も助けるカード」と区別する場合もある。

### ディスカウントの例

**例 1: フラッシュドロー vs 相手のフラッシュドロー**
- 自分: K♠ 9♠（スペードのフラッシュドロー、9 アウツ想定）
- 相手: A♠ 7♠（同じスペードのフラッシュドロー）
- フラッシュ完成カードが来ても相手がナッツフラッシュ → そのアウツは「勝ち」に貢献しない
- 実効アウツ: 9 アウツから 2〜4 アウツを削減して計算すべき

**例 2: ストレートドローが相手のフラッシュを完成させる場合**
- ボードがツートーンで自分はストレートドロー
- あるアウツが来てボードに 3 枚目の同スート → 相手がフラッシュ完成の可能性
- 該当カード（1〜2 枚）をアウツから除外または 0.5 アウツとして計算

### ディスカウントの実務

- 相手のハンドレンジを想定し、「このカードが来たら負けるか」を問う
- 疑わしければ 1〜2 アウツを差し引く
- 過剰なディスカウントも危険（実際は勝てるアウツを除外してしまう）

- 出典: [Poker Outs 101 – Pokerati（2025）](https://pokerati.com/2025/05/poker-outs/)
- 出典: [Counting Outs in Poker – PokerCoaching](https://pokercoaching.com/blog/outs-in-poker/)

---

## 6. 実効エクイティ vs 生エクイティ（Equity Realization）

### 定義

**生エクイティ（Raw Equity）**: ハンドが勝つ確率（ドロー完成確率）の単純計算値。

**実効エクイティ（Effective Equity）/ エクイティ実現率（EQR）**:
「実際にどれだけポットを獲得できるか」を生エクイティに対する比率で示したもの。

```
EV = エクイティ × EQR × ポット
```

GTO Wizard の定義: 「EQR はプレイアビリティ（対戦での実用性）を測る指標。
特定の状況でハンドが理論エクイティに対してどれだけ機能するかを示す。」

### ポジションと EQR

| 状況 | EQR の傾向 |
|-----|-----------|
| IP（インポジション） | 100% 以上に過実現しやすい |
| OOP（アウトオブポジション） | 100% を下回り、過少実現になりやすい |
| OOP 弱ドロー・中程度メイド | 25〜50% 程度しか実現できないケースも |
| OOP でも強いドロー（ナッツ系） | 90%+ 実現可能 |

**具体例（GTO Wizard の分析）**:
J♥T♦9♥ ボードで HJ（IP）の A♦2♦ はほぼ 100% のエクイティを実現するが、
同じボードで BB（OOP）の同ハンドは 2% 未満しか実現できない、という極端な例も存在する。

### OOP でエクイティを実現できない理由

1. **先手番の不利**: ベットしにくい、チェックしたら無料カードを与えてしまう
2. **フォールドを強いられる**: 相手のベットに対してコールできない状況が多い
3. **バリューベット機会の損失**: 後手番なのでベットサイズ・タイミングを制御されてしまう

### インプライドオッズによる補填

OOP でのエクイティ損失は、インプライドオッズ（将来のストリートで獲得できる追加価値）で一部補填できる。
ただし以下の条件が必要:
- ナット（最強手）可能性があるドロー
- 相手のスタックが十分に深い
- 完成時に相手をバリューベットに誘導できるレンジ構成

- 出典: [Equity Realization – GTO Wizard Blog](https://blog.gtowizard.com/equity-realization/)
- 出典: [What is Equity in Poker – GTO Wizard Blog](https://blog.gtowizard.com/what-is-equity-in-poker/)
- 出典: [Equity Realization – Upswing Poker](https://upswingpoker.com/equity-realization-explained/)

---

## 7. 本書の「アウツ × 1.5」方式の妥当性

### 本書 HandScore の設計意図

本書では HandScore として「ドロー系ハンドのフロップでの評価に +1.5 加点」を採用している。
この 1.5 という係数の根拠を Rule of 2/4 との対応で整理する。

### Rule of 2 との連動

- Rule of 2 = 「ターン段階で 1 ストリート分の確率 ≒ アウツ × 2%」
- 本書 HandScore の +1.5 = 「1 アウツあたり +1.5 点」

フラッシュドロー（9 アウツ）を例に取ると:
- Rule of 2 の示す 1 ストリート完成確率 = 9 × 2 = 18%
- HandScore の加点 = 9 × 1.5 = 13.5 点

### 1.5 にした合理性（安全マージン仮説）

| 係数 | 特徴 |
|-----|-----|
| × 2.0 | Rule of 2 と直接対応。1 ストリートの正確な確率に近い |
| × 1.5 | 約 25% の保守マージン。OOP でのエクイティ実現損失（EQR < 100%）を考慮 |
| × 1.0 | 過小評価。ドローの価値を著しく過小評価 |

**結論**: × 1.5 は「Rule of 2 の 1 ストリート分（× 2）」に対して、
OOP プレイ・ダーティアウツ・インプライドオッズ未達などのリスクを
25% の割り引きとして内包した実用係数として解釈できる。
GTO Wizard の EQR 研究でも OOP ドローが 75〜90% のエクイティ実現にとどまるケースが多いことと整合的。

**要確認**: × 1.5 が執筆段階での暫定値か確定値かを Writer に確認。

---

## 主要ソース一覧

| 内容 | URL |
|-----|-----|
| Phil Gordon's Little Green Book（Library of Congress 目次） | https://catdir.loc.gov/catdir/toc/ecip0511/2005010872.html |
| Rule of 4 and 2 解説（The Poker Bank） | https://www.thepokerbank.com/strategy/mathematics/pot-odds/4-2/ |
| Alex Filiakov 拡張公式（Medium、要確認） | https://medium.com/@alexfiliakov/math-of-poker-extending-the-2-4-rule-9222de9645b7 |
| ドロー確率テーブル（Upswing Poker） | https://upswingpoker.com/odds-hitting-draw-in-poker/ |
| ドロー確率テーブル詳細（Upswing Poker） | https://upswingpoker.com/poker-drawing-odds-outs-explained/ |
| バックドアドロー戦略（Upswing Poker） | https://upswingpoker.com/backdoor-flush-straight-draw-tips/ |
| アウツとエクイティ計算（PokerCoaching） | https://pokercoaching.com/blog/outs-in-poker/ |
| アウツ解説 2025（Pokerati） | https://pokerati.com/2025/05/poker-outs/ |
| Rule of 4 and 2 精度分析（CasinoReviews） | https://www.casinoreviews.net/blog/game-strategies-tips/rule-of-4-and-2-limitations-specifity-of-this-texas-holdem-poker-principle/ |
| Equity Realization（GTO Wizard） | https://blog.gtowizard.com/equity-realization/ |
| EQR 解説（Upswing Poker） | https://upswingpoker.com/equity-realization-explained/ |
| Smart Poker Study Revised Rule（Podcast #111） | https://smartpokerstudy.com/4-2-rule-flop-value-raises-oversized-bets-111/ |

---

## 本書への適用

| 章 | 活用方法 |
|---|---------|
| 第 6 章（フロップ） | Rule of 2 and 4 の基礎と精度限界、主要ドロー確率表、セミブラフの数理的根拠 |
| 第 11 章（確率とオッズ） | Rule of 4 の補正式（高アウツ向け）、正確な確率計算との比較 |
| 第 12 章（レンジ思考） | 実効エクイティ vs 生エクイティ、EQR とポジションの関係 |
| HandScore システム | × 1.5 係数の根拠を Rule of 2 + EQR 割り引きで説明 |
