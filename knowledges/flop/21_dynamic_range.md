# 第21章「相手のレンジを数式で動的に推定する」調査結果

検索日: 2026-04-20

## 概要

相手のアクションを観察するたびに、そのハンドの分布（レンジ）は確率的に更新される。
ベイズ推定の枠組みを使えば、「事前確率×尤度→事後確率」という繰り返しで、ストリートを経るごとにレンジを収束させることができる。
本章ではこのプロセスを、フロップの CBet・チェックという具体的なアクションに適用し、「相手のレンジをコンボ数で管理する」実践的な手法を解説する。

---

## 1. ベイズ的レンジ更新：初級者向け説明

### 考え方の核心

ベイズ推定では、新しい証拠（アクション）を観察するたびに事前の信念（レンジ）を更新する。

**基本式**

```
事後確率[ハンド] = 事前確率[ハンド] × P(そのアクション | そのハンド)
                   ÷ 全ハンドの分子の合計（正規化）
```

数式で書くと：

```
P(H | A) = P(A | H) × P(H)
           ──────────────────────
           Σ P(A | Hᵢ) × P(Hᵢ)
```

- `H` = 相手が持つハンドの仮説（例：AA, KQ, 87s…）
- `A` = 観察したアクション（例：フロップCBet）
- `P(H)` = 事前確率（プリフロップのレンジ構成比）
- `P(A|H)` = そのハンドがそのアクションを取る頻度（尤度）
- `P(H|A)` = アクション後の更新されたレンジ重み

### 初級者向け直感的説明

「100人の相手がいるとしたら、このアクションをするのは何人か？」

例：UTG がプリフロップでオープンしたとする。
- 100コンボのレンジを持つ
- フロップ CBet する頻度：プレミアムハンドで 90%、ミドルハンドで 60%、弱いハンドで 30%

CBet を観察したとき、相手の残りレンジは：
- プレミアム（当初40コンボ）→ 40 × 0.9 = 36コンボが残る
- ミドル（当初40コンボ）→ 40 × 0.6 = 24コンボが残る
- ウィーク（当初20コンボ）→ 20 × 0.3 = 6コンボが残る

合計 66コンボに正規化すると：
- プレミアム 36/66 ≈ 55%（当初40% → 上昇）
- ミドル 24/66 ≈ 36%（当初40% → 下降）
- ウィーク 6/66 ≈ 9%（当初20% → 大幅下降）

チェックを観察した場合は逆の更新が起きる。

**出典**: [Bayesian Decision-Making in Poker: A Simulation-Based Study - Medium](https://medium.com/@rishabghosh_96234/bayesian-decision-making-in-poker-a-simulation-based-study-b53744288df4)

### アクション別の尤度目安（シミュレーション例）

| アクション | プレミアム P(A|H) | ミドル P(A|H) | ウィーク P(A|H) |
|----------|---------------|------------|--------------|
| フロップ CBet | 0.90 | 0.60 | 0.30 |
| ターン バレル | 0.70 | 0.50 | 0.20 |
| リバー シャブ | 0.60 | 0.30 | 0.10 |

**出典**: [Bayesian Decision-Making in Poker - Medium](https://medium.com/@rishabghosh_96234/bayesian-decision-making-in-poker-a-simulation-based-study-b53744288df4)

---

## 2. アクション履歴からのレンジ収束

### 基本原則

プリフロップから始まったレンジは、各ストリートで観察されるアクションによって段階的に絞り込まれる。

- プリフロップのポジション・アクション → 開始レンジ（事前分布）を決める
- フロップ CBet or チェック → レンジを二分する最初の大きな分岐
- ターン以降 → さらに細分化、収束

### 重要な実践原則

1. **フロップ上のカードでコンボ数が減る**
   - フロップ K♠Q♥5♦ では、KK は 6コンボ → 3コンボに半減
   - KQ はボード上の K♠と Q♥ を使うため、16コンボ → 9コンボに減少

2. **アクション履歴で不可能なコンボを除外する**
   - UTG がプリフロップ 3-bet をコールしたなら、AA や KK は通常 4-bet するため除外できる
   - 相手が弱いレンジ（フラットコール）を示したならば、ナッツ候補のコンボは減少する

3. **ストリートをまたいで更新を積み重ねる**
   - 「前のストリートのアクションも含めた全アクション履歴」を考慮する
   - 途中の一アクションだけで判断しない

**出典**: [Narrow Down the Range at the Turn | Jurojin Poker](https://jurojinpoker.com/poker-course/poker-for-beginners/poker-hand-range)
**出典**: [Thinking About Ranges - Thinking Poker](https://www.thinkingpoker.net/articles/range-thinking/)

---

## 3. フロップでの CBet／チェックによるレンジ分化

### 3-1. CBet 側のレンジ：ポラライズ vs コンデンス

フロップのレンジ分化は**ボードテクスチャ**と**ナッツアドバンテージ**によって決まる。

#### ポラライズド CBet（大きいサイズ、頻度低め）

- **いつ使うか**: ドローが存在するボード、相手レンジにミドルハンドが多いとき
- **レンジ構成**:
  - バリュー側：セット、ツーペア、強いトップペア
  - ブラフ側：ナッツドローへの見込みがある低エクイティハンド（A7s バックドアフラッシュ等）
  - ミドルハンドは少ない（またはチェック）

**例：BTN on K♥J♥7♦**
BTN のレンジは強いハンド（AK, KQ, セット）と完全ミス（空振り）で構成され、ミドルハンドが少ないため、ポラライズド大きいサイズが最適。

#### コンデンス型 CBet（小さいサイズ、頻度高め）

- **いつ使うか**: ミドルハンドが多いボード、相手に保護が必要なとき
- **レンジ構成**:
  - ミドルハンドも全て含むマージドレンジ
  - ナッツは存在するが、ミドルを守るために小さいサイズを使用

**例：Q♦J♦T♦ フロップ**
ワンペアハンドがアンカーとなり、ナッツが大きく賭けることでミドルが搾取されるため、小さいサイズでコンデンス型に。

**例：KQ6r フロップ（UTG vs BTN）**
UTG がエクイティアドバンテージ（57%）を持ち、1/3ポット サイズで 100% CBet。

**出典**: [The Mechanics of C-Bet Sizing | GTO Wizard](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/)
**出典**: [Range Morphology | GTO Wizard](https://blog.gtowizard.com/range-morphology/)

#### GTO の CBet 頻度（UTG vs BTN 例）

GTOウィザードによれば、UTG は全フロップを通じて **72% チェック、28% CBet** というのが平均値。

| フロップテクスチャ | CBet 頻度 | サイズ | 理由 |
|----------------|----------|------|------|
| K♥Q♦6♣（レインボー高カード） | 100% | 1/3ポット | UTG エクイティ優位 |
| K♦4♠3♣ | 100% | 2/3ポット | BTN アンダーペアが多い |
| Q♥9♠6♦ | 0%（全チェック） | - | BTN エクイティ優位 |
| 4♣3♠2♦ | 0%（全チェック） | - | BTN が強いレンジ保有 |

**出典**: [C-Betting As the OOP Preflop Raiser | GTO Wizard](https://blog.gtowizard.com/c-betting-as-the-oop-preflop-raiser/)

### 3-2. チェック側のレンジ：ミドルハンドが主体

チェックするハンドのカテゴリ：

1. **強いハンド（GTO バランス用）**: セット、強いツーペアの一部 → チェックレイズ準備
2. **ミドルハンド（主流）**: セカンドペア、ウィークトップペア、オーバーペア（保護不要なら）
3. **バックドアドローあり低エクイティ**: チェックして相手にアクションを起こさせる

**OOP でチェックするとき**（UTG の例）：
- BTN をスタブさせてから **約18%のチェックレイズ** を打つ
- チェックレイズのレンジ：強いメイドハンド + ハイエクイティブラフ
- チェックコールのレンジ：ミドルストレングスのメイドハンドとドロー

**出典**: [C-Betting As the OOP Preflop Raiser | GTO Wizard](https://blog.gtowizard.com/c-betting-as-the-oop-preflop-raiser/)

---

## 4. 相手の行動から HandScore を推定する方法

本書の「HandScore（手の強さスコア）」を相手側に適用する際の考え方。

### 4-1. ベイズ更新を HandScore 分布に適用

各アクションは「ハンドの相対強度」情報を含む。

**CBet 観察後**：
- 相手の想定 HandScore 分布の中心が上方にシフト
- 低スコアハンドのウェイトが減少

**チェック観察後**：
- ミドルスコアハンドが増加（ナッツとゴミの両方が一部残る）
- 特にウィーク/ミドルの混在状態

**具体的な読みの例**：
- 相手が UTG からオープン → 事前レンジは強いハンドが多い（HandScore 高め）
- フロップで相手がチェック → ナッツ候補は一部残るが、ミドルも多い状態
- ターンで相手がベット → チェックレンジからのポラライズ（強い手 or ブラフが多い）

### 4-2. アクション別レンジ重み付け更新の実践手順

1. **プリフロップレンジを特定**（ポジション・アクション別）
2. **フロップカードで不可能コンボを除外**
3. **アクションの尤度で各コンボにウェイトを掛ける**
4. **ウェイトを正規化**して事後分布を得る
5. **平均 HandScore を計算**（ウェイト付き平均）

---

## 5. 本書の3式を相手側に適用する方法

### 5-1. 相手の HandScore 推定式

本書で自己の HandScore を計算するのと同じアプローチを相手レンジに適用する。

```
想定 HandScore_相手 = Σ (ウェイト[i] × HandScore[i]) / Σ ウェイト[i]
```

ここで、ウェイトはベイズ更新後の各コンボの事後確率比例値。

### 5-2. フロップでの相手レンジ再評価

フロップ前後の HandScore 変化を追う：

- **プリフロップ**: 全コンボに均等ウェイト（レンジ構成比による）
- **フロップ後**: CBet or チェックで大きく二分
- **ターン**: さらにウェイトが集中（バレルするかチェックするか）

**フロップ CBet を見た後の再評価**（例：A♠K♦7♣ フロップ）

| ハンドカテゴリ | 事前コンボ数 | CBet 尤度 | ウェイト後コンボ |
|-------------|-----------|---------|-------------|
| セット(AAA, KKK, 777) | 9 | 0.95 | 8.6 |
| AK（ツーペア） | 9 | 0.90 | 8.1 |
| AX（トップペア） | 48 | 0.70 | 33.6 |
| KX | 24 | 0.50 | 12.0 |
| ポケットペア（オーバー） | 12 | 0.60 | 7.2 |
| ブラフ/ドロー | 30 | 0.30 | 9.0 |
| 合計 | 132 | - | 78.5 |

CBet後、相手のレンジはナッツ寄りに凝縮。

---

## 6. コンバット数での簡易カウント

### 6-1. ナッツコンボ、バリューコンボ、ブラフコンボの数え方

**基本の数**：
- ポケットペア：6コンボ（スーツ違いの組み合わせ：C²₄ = 6）
- スーテッドハンド：4コンボ（同じスートの組み合わせ）
- オフスーテッドハンド：12コンボ
- 総コンボ数：1,326

**フロップで減少するコンボ**：
- ボード上のカードと重複するコンボを除外
- 例：K♠Q♥5♦フロップ → KK は K♠を使うため 6→3コンボに
- 例：KQ は K♠か Q♥を含む → 16→9コンボに

**出典**: [A Beginner's Guide to Poker Combinatorics | GTO Wizard](https://blog.gtowizard.com/a-beginners-guide-to-poker-combinatorics/)
**出典**: [Counting the Combos: An Exercise in Range Narrowing | PokerNews](https://www.pokernews.com/strategy/counting-the-combos-an-exercise-in-range-narrowing-33108.htm)

### 6-2. カテゴリ別の簡易カウント

**ナッツコンボ**（フロップ時点で最強クラス）：
- セット：3コンボ（ボード上のカードを使うため減少）
- フロップツーペア：使ったカードによって2〜9コンボ

**バリューコンボ**（払い戻し期待値がプラスの手）：
- トップペア：通常4〜12コンボ（キッカー込みで計算）
- オーバーペア：6コンボ（フロップの全カードより高いポケットペア）

**ブラフコンボ**（ナッツドロー等）：
- フラッシュドロー：9コンボ程度（スーテッド未完成）
- ストレートドロー：オープンエンドで最大8コンボ

**バリュー：ブラフ比率**（リバーの目安）：
- 約 2〜2.5 : 1 がバランスとされる
- フロップは比率が緩く（まだドローが価値を持つため）

**出典**: [Bluff value ratios and counting combos | Run It Once](https://www.runitonce.com/nlhe/bluff-value-ratios-and-counting-combos/)

---

## 7. 具体例（7ケース）

### ケース1: UTG がフロップをチェック

**シナリオ**：UTG がプリフロップオープン → BTN コール → フロップ K♦9♠4♣ → UTG チェック

**レンジ分析**：
- UTG がチェックしたことで、ナッツ候補（AA, KK, 99, 44, AK など）の一部はチェック範囲に残るが、CBetしないことで弱いハンドも残る
- しかしGTOソルバーによれば UTG は全フロップで72%チェックするため、チェック自体は強い手を排除しない
- チェックレイズの備えとして一部のセットやAKもチェックレンジに入る
- **結論**：UTG チェックは「強いハンドが絞られる」とは限らない。ミドルも強いハンドも混在する「コンデンストから少しポラライズした」状態

**出典**: [C-Betting As the OOP Preflop Raiser | GTO Wizard](https://blog.gtowizard.com/c-betting-as-the-oop-preflop-raiser/)

### ケース2: BB が CBet に対してフラット

**シナリオ**：BTN プリフロップレイズ → BB コール → フロップ T♦6♠4♥ → BTN CBet（1/3ポット）→ BB コール

**レンジ分析（BB の残りレンジ）**：
- **コールしやすいハンド**：ミドルペア、セカンドペア（T8s, 96s, 86s, 55-22）
- **コールするバリューハンド（スローすれば）**：6x, 4x のツーペア候補の一部
- **コールするドロー**：フラッシュドロー、ストレートドロー
- **除外されるハンド**：弱すぎるエア（即フォールド）、チェックレイズしたはずのセット
- **レンジの形状**：コンデンスト～マージド（極端に強いハンドと弱いハンドが少ない中間域）

**出典**: [How to Check-Raise Like a High Stakes Poker Pro - Upswing Poker](https://upswingpoker.com/check-raise-poker-strategy-flop-c-bet/)

### ケース3: BB が CBet に対してレイズ

**シナリオ**：BTN CBet → BB レイズ（チェックレイズ）

**レンジ分析（BB のチェックレイズ後）**：
- **バリュー側（ポラライズド強側）**：セット（T♦6♠4♥なら T, 6, 4 のセット）、強いツーペア
- **ブラフ側（ポラライズド弱側）**：ナッツドロー（フラッシュドロー、コンボドロー）、例えば 7♠5♠ のオープンエンダー
- **排除されるハンド**：ミドルペア、セカンドペア（これらはコールするかフォールドする）
- **レンジの形状**：明確にポラライズ（強いメイドハンド + 高エクイティブラフ）

**理論的根拠**：
「チェックレイズした後のあなたのレンジはポラライズになる。強いハンドとブラフ。相手はコンデンストなミドルストレングスのレンジでコールした」

**出典**: [How to Check-Raise Like a High Stakes Poker Pro - Upswing Poker](https://upswingpoker.com/check-raise-poker-strategy-flop-c-bet/)

### ケース4: IP プレイヤーの CBet（A73r ボード）

**シナリオ**：BTN がコールして IP → フロップ A♠7♣3♦ → BTN CBet

**分析**：
- BTN は A♠7♣3♦ ではマージドレンジ（小さいサイズ、高頻度）を使用する傾向
- A ヒットのハンドが多く、フォールドエクイティも高い
- チェックバックするハンド：AX の弱いキッカー（A4o など）、KK-JJ（チェックレイズを回避）

**出典**: [Flop Heuristics: IP C-Betting in Cash Games | GTO Wizard](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)

### ケース5: Q96r ボード で UTG が全チェック

**シナリオ**：UTG オープン → BTN コール → フロップ Q♥9♠6♦ → UTG チェック（100%）

**分析**：
- このボードは BTN がエクイティアドバンテージを持つ（約53%）
- UTG がチェックするのは BTN が強いレンジを保有しているため
- UTG はチェックレイズ作戦：BTN スタブ後に18%チェックレイズ
- UTG チェックレンジ：全ハンド（強い手も弱い手も混在）

**本書への示唆**：「エクイティ劣位のプレイヤーがチェックしても、それは弱さのシグナルとは限らない」

**出典**: [C-Betting As the OOP Preflop Raiser | GTO Wizard](https://blog.gtowizard.com/c-betting-as-the-oop-preflop-raiser/)

### ケース6: ターンカードによるコンボ消去（フラッシュドロー例）

**シナリオ**：BB フラットコール後、ターン A♦（ダイヤモンドが揃う）

**コンボ変化**：
- BB の K♦ 系フラッシュドロー（K♦Q♦, K♦J♦ etc.）：9コンボがナッツに変わる
- BTN のフラッシュドロー（スーテッドエース系）：大半が事前にフォールドしていたためコンボが激減
- このコンボ差がナッツアドバンテージとなる

**出典**: [Counting the Combos: An Exercise in Range Narrowing | PokerNews](https://www.pokernews.com/strategy/counting-the-combos-an-exercise-in-range-narrowing-33108.htm)

### ケース7: バリュー：ブラフ比率のチェックレイズ

**シナリオ**：T♦6♠4♥ ボード、BB チェックレイズ

**コンボカウント**：
- バリューコンボ：T6s(4), T4s(4), 64s(4), TT(3), 66(3), 44(3) = 約21コンボ（バリュー）
- ブラフコンボ：フラッシュドロー、オープンエンダー（87s, 75s など）≈ 8〜12コンボ

**バリュー：ブラフ = 約 2:1 → フロップ段階でバランスが取れている**

ブラフがドローを持つため、ターン・リバーで価値が変化する点が重要。

**出典**: [A Beginner's Guide to Poker Combinatorics | GTO Wizard](https://blog.gtowizard.com/a-beginners-guide-to-poker-combinatorics/)

---

## 8. 本書（第21章）への適用

### 章立て提案

1. **導入**：「相手の手は見えないが、確率で管理できる」
2. **ベイズ更新の直感的説明**（100人モデル）
3. **事前→尤度→事後の計算例**（フロップ CBet を例に）
4. **アクション別のレンジ分化マップ**
   - CBet → ポラライズ（強い手 + ブラフ）vs チェック → コンデンスト（ミドル主体）
   - チェックレイズ → 明確ポラライズ vs コール → ミドルレンジ残存
5. **コンボカウントで相手レンジを数値化**
   - ナッツ/バリュー/ブラフの3分類で計算
6. **本書の HandScore 式を相手レンジに適用**
7. **実戦例7ケース**の詳説

### 各章との連携

| 章 | 連携内容 |
|---|--------|
| 第8章（HandScore フロップ） | 自己 HandScore との対比で相手推定 HandScore を導入 |
| 第9章（CBet 統合式） | CBet 頻度を「相手視点」でも解釈 |
| 第12章（コールフォールド境界） | 相手レンジ推定を防御側の決断に接続 |
| 第20章（相手調整） | タイプ別の尤度テーブルで個人差を表現 |

---

## 参考文献・出典一覧

- [Bayesian Decision-Making in Poker: A Simulation-Based Study | Medium](https://medium.com/@rishabghosh_96234/bayesian-decision-making-in-poker-a-simulation-based-study-b53744288df4)
- [The Importance of Probability and Bayes' Theorem in Poker | Cornell INFO 2040](https://blogs.cornell.edu/info2040/2017/11/19/the-importance-of-probability-and-bayes-theorem-in-poker/)
- [Do I Call or Fold? How Bayes' Theorem Can Help Navigate Poker's Uncertainty | PokerNews](https://www.pokernews.com/strategy/call-or-fold-bayes-theorem-poker-uncertainty-2-24133.htm)
- [Range Morphology | GTO Wizard](https://blog.gtowizard.com/range-morphology/)
- [The Mechanics of C-Bet Sizing | GTO Wizard](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/)
- [C-Betting As the OOP Preflop Raiser | GTO Wizard](https://blog.gtowizard.com/c-betting-as-the-oop-preflop-raiser/)
- [Flop Heuristics: IP C-Betting in Cash Games | GTO Wizard](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)
- [Polarized Ranges vs Linear (Merged) Ranges Explained | Upswing Poker](https://upswingpoker.com/polarized-vs-linear-ranges/)
- [How to Check-Raise Like a High Stakes Poker Pro | Upswing Poker](https://upswingpoker.com/check-raise-poker-strategy-flop-c-bet/)
- [A Beginner's Guide to Poker Combinatorics | GTO Wizard](https://blog.gtowizard.com/a-beginners-guide-to-poker-combinatorics/)
- [Counting the Combos: An Exercise in Range Narrowing | PokerNews](https://www.pokernews.com/strategy/counting-the-combos-an-exercise-in-range-narrowing-33108.htm)
- [Bluff value ratios and counting combos | Run It Once](https://www.runitonce.com/nlhe/bluff-value-ratios-and-counting-combos/)
- [Narrow Down the Range at the Turn | Jurojin Poker](https://jurojinpoker.com/poker-course/poker-for-beginners/poker-hand-range)
- [Thinking About Ranges | Thinking Poker](https://www.thinkingpoker.net/articles/range-thinking/)
- [Equity Realization | Red Chip Poker](https://redchippoker.com/equity-realization/)
