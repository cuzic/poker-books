# 12: 3betスコア式とブロッカー強化の根拠

検索日: 2026-04-19

## 概要

3ベット（リレイズ）はプリフロップで最も攻撃力の高いアクションであり、GTO的な均衡戦略においてバリューハンドとブラフハンドを組み合わせたレンジ構成が求められる。本章では本書の3betスコア式（Score₃）の各要素が、GTO理論・ブロッカー計算・ポジション別レンジ構成とどのように整合しているかを検証する。

---

## 1. 3ベットの目的

### 1-1. バリュー3ベット

QQ+、AKなど強いハンドで3ベットすることで、ポットを大きくして価値を取ることが主目的。

- 「3-betting increases the pot with your strongest hands (think QQ+, AK) – a core value-betting principle」
- 出典: [3-Bet Preflop Strategy & Range Charts - Upswing Poker](https://upswingpoker.com/3-bet-strategy-aggressive-preflop/)

### 1-2. ブラフ3ベット（ブロッカー付き）

A5s、KTsなど弱〜中程度のハンドでブラフ3ベットを行うことでレンジバランスを維持する。

- 「3-betting weak hands preflop is an important component of GTO balanced play since it prevents the 3-bet range from becoming overly strong」
- ブラフ3ベットによりフロップ以降のレンジにエア（ブラフ）コンボが確保され、リバーでの二極化レンジが成立する
- 出典: [Understanding 3-Bet Ranges In 2026 | SplitSuit Poker](https://www.splitsuit.com/understanding-3-bet-ranges)

### 1-3. ポーラライズ vs リニアレンジ

| レンジ型 | 構成 | 適用場面 |
|---------|------|---------|
| ポーラライズ | 超強ハンド + ブロッカー付きブラフ | IP、対タイトな序盤オープン |
| リニア（マージ） | 強〜中堅の良質ハンド群 | OOP、コールが多い相手 |

「Position: OOP – linear. IP – polar (esp. vs tight EP)」

具体例（BTN vs HJ 60BB）:
- 3bet対象: QQ+、AK、A5s/A4s（ブロッカーブラフ）
- コール対象: TT-JJ、AQ、KQs（中堅ハンドはフラット）

- 出典: [Raise the Right Hands: A Field Guide to Linear & Polar 3-Bets](https://www.poker.pro/strategy/raise-the-right-hands-a-field-guide-to-linear-polar-3-bets/)
- 出典: [Polarized Ranges vs Linear (Merged) Ranges Explained - Upswing Poker](https://upswingpoker.com/polarized-vs-linear-ranges/)

---

## 2. ブロッカー効果の定量

### 2-1. Aホールドによるブロッカー効果（AA への影響）

通常の組み合わせ数:
- AA: 6通り（4×3÷2 = 6）
- AK: 16通り（4枚×4枚 = 16）

A1枚を保有している場合:
- AA: 3通りに半減（3×2÷2 = 3）
- AK: 12通りに減少（3枚Ace × 4枚King = 12）

「When you hold an ace as a blocker, the formula for pocket aces goes down to (3*2)/2 for a total of 3 combos, cutting the total number of pocket aces combos in half」

- 出典: [A Beginner's Guide to Poker Combinatorics | GTO Wizard](https://blog.gtowizard.com/a-beginners-guide-to-poker-combinatorics/)
- 出典: [Poker Combos & Blockers 101 In 2026 | SplitSuit Poker](https://www.splitsuit.com/poker-combos-blockers)

### 2-2. Kホールドによるブロッカー効果（KK・AKへの影響）

K1枚を保有している場合:
- KK: 3通りに半減
- AK: 12通りに減少（4枚Ace × 3枚King = 12）

KK（2枚保有）の場合:
- KK: 0通り（自分が持っているため）
- AK: 8通りに減少（4枚Ace × 2枚King = 8）

「While KK blocks half of the combos of AK, there are still 8 combos of AK available（KK保有時）」

- 出典: [Poker Combos & Blockers 101 In 2026 | SplitSuit Poker](https://www.splitsuit.com/poker-combos-blockers)

### 2-3. AKo のダブルブロッカー性

AKoを保有している場合:
- AA: 3通り（Ace1枚ブロック）
- KK: 3通り（King1枚ブロック）
- AK: 4通り（自分がAK保有 → 残りは3枚Ace×3枚King-自組み合わせ... 実質4通り）

「When holding AK, you are blocking AA and KK by 50%」

AKが4ベットブラフに最も強い理由として、AA・KK・AKすべてをブロックし、相手の4ベット頻度を大きく下げられる点が挙げられる。

- 出典: [Understand How to Use Blockers the Right Way | Pokercode Blog](https://www.pokercode.com/blog/blockers-in-poker)

### 2-4. 実践的影響の定量評価

- Aブロッカー保有により相手の4ベット頻度が約1.2ポイント低下
- 10,000ハンド分の試算では、その差が$140の節約に相当
- ただし「hand playability matters three times more than blockers for cash game 3bet success」

つまりブロッカーはあくまでボーナスファクターであり、ハンドのプレイアビリティ（フロップ以降の実現価値）の方が重要度が高い。

- 出典: [Poker 3Bet Range Strategy for Cash Games - Betting Data Lab](https://betting-data-lab.com/poker-3bet-range-strategy-for-cash-games-what-actually-works/)

### 2-5. スコア式 B項（ブロッカーボーナス）の根拠整合性

| スコア式 | 根拠 |
|---------|------|
| A含む: +3 | AAを3→3通り半減、AKを16→12に削減。相手の4ベット頻度を下げる効果大 |
| K含む: +2 | KKを半減、AKも削減。Aより効果やや小（AKKKなど相手のバリューレンジへの影響がAより少ない） |
| A・K両方: +4（重複減衰） | AKはAA/KK両方をブロック。+3+2=5にしないのは、両ブロックが同時に機能しても上限があるため |

---

## 3. 各ポジションのGTO 3ベットレンジ

### 3-1. 3ベット頻度（GTO近似値）

| 状況 | 3bet頻度 | コール頻度 |
|------|---------|---------|
| BTN vs CO オープン | 約12% | 約5% |
| BTN vs UTG オープン | 約7.5% | 約8.2% |
| BB vs UTG オープン | 約5.2% | 中程度 |
| SB vs BTN オープン | 高頻度3bet（コールはほぼなし） | ほぼなし |

「Against a CO open, BTN will 3-bet ~12% of hands, while calling only 5%」
「Against a UTG open, there are more calls than 3-bets (8.2% calls, 7.5% 3-bets)」

- 出典: [Constructing 3-Bet And vs. 3-Bet Ranges - Poker.Pro](https://www.poker.pro/strategy/constructing-3-bet-and-vs-3-bet-ranges-33/)

### 3-2. BB vs BTN（OOP最重要スポット）

BBはポジション不利のため、3ベットの比率を上げてレンジを守る必要がある。

ブラフ3ベットゾーン（BBからBTNへ）:
- A8o、KTo、K9o、K7s、J8s、T7s など

対照的にIPでは:
- A7o、A6o、A2o、K8o、K7o、J8s、T3s など（よりワイド）

- 出典: [Big Blind 3betting vs IP Opponents: Best Practices and Strategy | 888poker](https://www.888poker.com/magazine/big-blind-3betting-oop-strategy)

### 3-3. SB vs BTN（OOP ポーラライズ）

SBはBTNオープンに対してほぼコールしない（スクイーズリスクとOOP不利のため）。
3ベットかフォールドの二択が基本戦略。

「The SB barely calls anything when facing a BTN open-raise. Instead, they almost exclusively 3-bet or fold」

- 出典: [PKO Versus Classic: Responding to 3-Bets | GTO Wizard](https://blog.gtowizard.com/pko-versus-classic-responding-to-3-bets/)

### 3-4. BTN vs UTG（IP ポーラライズ）

UTGのレンジが狭いため、BTNからのポーラライズ3ベットが有効。

典型的3ベットレンジ（BTN vs UTG）:
- バリュー: AA、KK、QQ、AKs、AKo
- ブロッカーブラフ: A5s、A4s（ブロッカー付き）
- コール: JJ、TT、AQs、KQs（中堅フラット）

- 出典: [3-Bet Preflop Strategy & Range Charts - Upswing Poker](https://upswingpoker.com/3-bet-strategy-aggressive-preflop/)

---

## 4. 3ベットサイジング

### 4-1. 基本サイズ

| ポジション | 推奨サイズ |
|---------|---------|
| IP（イン・ポジション） | 2.5x〜3x（相手のオープンサイズ比） |
| OOP（アウト・オブ・ポジション） | 3x〜4x（相手のオープンサイズ比） |

「In Position: 2.5x – 3x the open raise size. Out of Position: 3x – 4x the open raise size」

OOPで大きくする理由: ポジション不利を補うためスペキュレイティブハンドでのコールを制限する。

- 出典: [How to Size Your 3-Bets Correctly in Poker: The GTO and Live Player Guide](https://www.poker.pro/strategy/how-to-size-your-3-bets-correctly-in-poker-the-gto-and-live-player-guide/)

### 4-2. ライブゲームでの典型サイズ

ライブゲームではオープンサイズ自体が大きくなる傾向があるため、3ベットサイズも相対的に大きくなる。

- ライブ$1/$2や$1/$3ではオープンが5〜8bbになることが多く、3ベットは15〜25bb程度になる
- 4ベットのOOP推奨サイズは「2.6〜2.8x their 3-bet size（ライブ）」

- 出典: [The Fundamentals of 3-bet Sizing - Tournament Poker Edge](https://www.tournamentpokeredge.com/the-fundamentals-of-3-bet-sizing/)

### 4-3. ショートスタックでの調整

- 20BB時点では3ベットがほぼオールインとなるため、A5sが主なブラフとなる
- 「At 20BB effective stacks where the 3-bet is a shove, board coverage doesn't matter and A5s becomes the main bluff」

- 出典: [Why Do Poker Solvers Love Ace Five Suited So Much? | GipsyTeam](https://www.gipsyteam.com/news/27-11-2024/why-do-poker-solvers-love-ace-five-suited)

---

## 5. 代表ハンド検証

### 5-1. A5s（スコア式: 21.5、MP〜COで3bet）

A5sはソルバーが最も好むブラフ3bet候補として知られる「ソルバーハンド」。

理由:
1. Aブロッカー: 相手のAA・AKを削減（4ベットリスク低下）
2. フラッシュドロー: 3betが通らなくてもナットフラッシュドロー可能
3. ホイールストレートドロー: A-2-3-4-5 の最低ストレートに発展可能
4. 「unblocks a lot of weaker hands that fold like K9s–K5s, QTs–Q8s」（相手のフォールドを促す）

ソルバーの挙動:
- 「From the button against a UTG open, the solver mixes 3-bets 60% of the time and calls 40% with A5s」

スコア式との整合: Score = 14 + 0.5×5 + 3 + 2 = 21.5 → MP・CO闘値（21/19）をほぼクリア。合理的。

- 出典: [Why Do the Pros Love Ace-Five Suited? GTO Wizard Explains | PokerNews](https://www.pokernews.com/strategy/why-do-the-pros-love-ace-five-suited-47439.htm)
- 出典: [Blockers & Unblockers: The Secret to Picking Great Bluffs | GTO Wizard](https://blog.gtowizard.com/blockers-unblockers-the-secret-to-picking-great-bluffs/)

### 5-2. KTs（スコア式: 23、強い3bet候補）

- Kブロッカーを持ち、相手のKK・AKを削減
- スーテッドによりフラッシュドロー可能
- コネクター（差1）によりストレートドロー可能
- 「In polarized 3-bet ranges, the solver includes... middling hands like 99–77 and high suited cards like KTs and T9s」

スコア式との整合: Score = 13 + 0.5×10 + 2 + 2 + 1 = 23 → 全ポジション闘値をクリア。BTNからはほぼ全ての状況で3bet候補。合理的。

- 出典: [Understanding 3-Bet Ranges In 2026 | SplitSuit Poker](https://www.splitsuit.com/understanding-3-bet-ranges)

### 5-3. QJo（スコア式: 17.5、コール寄り）

- ブロッカーなし（A・Kなし）
- オフスーテッドのためフラッシュ価値なし
- コネクターでストレートドロー可能だが3ベット後の単独価値が低い

スコア式との整合: Score = 12 + 0.5×11 = 17.5 → 全ポジション闘値（18〜23）未満。コールが正解。
QJoはBTN vs COなどのIPでもコール寄りが一般的。合理的。

### 5-4. 76s（スコア式: 12、3bet不適）

なぜ3ベット対象でないか:
1. ブロッカーなし（A・Kを保有しない）
2. 低カード（両方9未満）によりペナルティ -1
3. 「Low pocket pairs are the most obvious hands that suffer from poor equity realization（3bet後）」
4. SPR（スタックポット比）が下がる3ベットポットでは、スモールコネクターの含意オッズが消える
5. 3ベット後のコールでも、OOPまたはマルチウェイポットで真価を発揮する傾向

推奨アクション: 「Hands like 98s, 87s, and 76s could sometimes be played as cold calls... they rarely make dominated hands and have strong implied odds」

スコア式との整合: Score = 7 + 0.5×6 + 2 + 1 − 1 = 12 → 全ポジション闘値を大幅に下回る。合理的。

- 出典: [Cold Calling in Poker: Top 3 Do's and Don'ts | 888poker](https://www.888poker.com/magazine/strategy/cold-calling-poker-dos-and-donts)

### 5-5. AKo（スコア式: 24.5、全ポジションで3bet）

AKoはダブルブロッカー（A・K両方）を持つ最強プリフロップハンドの一つ。

- AA・KK・AKすべてをブロック
- 「It is generally considered correct to 3-bet AK against late-position opens」
- 対UTGなど序盤オープンではコールが一部混入するケースも（GTOミックス）
- 「the larger the size of the opponent's open-raise, the less inclined a player should be to 3-bet AK」

スコア式との整合: Score = 14 + 0.5×13 + 4 = 24.5 → 対UTG闘値23を超過。全ポジションで3bet正当化。合理的。

- 出典: [Ace King: Call Or 3Bet Preflop? | Red Chip Poker](https://redchippoker.com/ace-king-3bet-vs-call-preflop/)

---

## 6. 対UTG vs 対BTNの構造差

### 6-1. 対UTG: ポーラライズが基本

- UTGのレンジは狭い（AA〜JJ、AKs〜AQs、KQs等の強ハンドに集中）
- 中程度のハンド（TT、AQ等）はコールが優勢（フラット）
- 3ベットレンジ: バリュー（AA/KK/QQ/AK）+ ブラフ（A5s/A4s のブロッカー付き）のポーラライズ

### 6-2. 対BTN: リニア（マージ）かつ広い

- BTNのレンジは広い（全ハンドの約45〜50%でオープン）
- 広いレンジに対してはより多くのハンドが3ベットEV+となる
- 「The BTN's value range is much wider than the HJ's value range, and this wider value range allows the BTN to 3-bet more bluffs」
- マージレンジ（強〜中堅の連続的なレンジ）で3ベット頻度が増加

| 要素 | 対UTG | 対BTN |
|------|-------|-------|
| 相手レンジ | 狭く強い | 広く弱い |
| 3ベット型 | ポーラライズ | リニア/ワイド |
| 3ベット頻度 | 低（7.5%前後） | 高（12%前後） |
| フラット適切 | TT-JJ、AQ | 少なめ |

- 出典: [3-Betting 101 for Beginners: Linear versus Polarized Ranges - MicroGrinder](https://microgrinder.com/poker-strategy-articles/3-betting-101/)

---

## 7. 4ベット耐性

### 7-1. 3ベット後に4ベットされた場合の基本対応

| ハンド | 4ベットへの対応 |
|-------|-------------|
| AA/KK | 5ベット（コール/ジャム）。4ベットに喜んでコール |
| QQ/AK | ミックス（コール or 5ベット）。状況依存 |
| A5s（ブラフ3ベット） | フォールド。ブラフの役割を果たした後はディスカード |

### 7-2. A5sを使った3ベットブラフの論理

3ベットが通れば: ブラインドを奪い期待値プラス
3ベットがコールされた場合: フロップでナットフラッシュドロー、ホイールドロー継続可能
4ベットされた場合: Aブロッカーにより相手のAAが3通りしかなく4ベットが少なめ → それでもフォールドが正解

- 「suited wheel Ax will almost always have at least 35% equity against a 4-bet calling range」
- しかし4ベットポットでは基本的にフォールドが最適（4betブラフとして5ベットする場合は別）

- 出典: [There's Big Money in 4-Bet & 5-Bet Pots - Upswing Poker](https://upswingpoker.com/4-bet-5-bet-preflop-strategy/)

### 7-3. AKoの4ベット対応

- AKoは対AA・KK相手でも35〜45%のエクイティを保持
- 「Even 'value hands' like AKo and JJ are usually equity underdogs against a 5bet jam」
- 純粋なバリューハンドとしての扱いはKK+のみで、AKo/AKsはセミバリュー扱いが適切
- 4ベットに対してコールまたは5ベットジャム

- 出典: [Mastering 3-Bet and 4-Bet Poker Strategies | BluffTheSpot](https://www.bluffthespot.com/blog/mastering-3-bet-and-4-bet-poker-strategies)

---

## 8. スコア式の妥当性検証

### 8-1. GTO頻度との整合性評価

| ハンド | Score₃ | しきい値 | GTO推奨 | 整合性 |
|-------|--------|---------|---------|--------|
| AKo | 24.5 | 全ポジション可 | 全ポジション3bet | 良好 |
| KTs | 23.0 | 全ポジション可 | BTN〜CO推奨、UTGミックス | 良好 |
| A5s | 21.5 | MP〜CO以降 | BTN vs UTGで60%の確率で3bet | 良好 |
| QJo | 17.5 | 全ポジション不可 | コール寄り | 良好 |
| 76s | 12.0 | 全ポジション不可 | コールまたはフォールド | 良好 |

### 8-2. スコア式が過大評価する可能性のあるハンド

- **KQo（仮）**: Kブロッカー+Kの高い値でスコアが上がりやすいが、オフスーテッドで支配されやすい
- **A2o〜A4o**: Aブロッカーは+3だが、ローカード両方9未満ペナルティ-1、オフスーテッドでスーテッドボーナスなし → バランスされている

### 8-3. スコア式が過小評価する可能性のあるハンド

- **JJ**: ペア（H+Lの計算で両方同じ値）でスコアが低めになる可能性。ただしペアは別処理の可能性あり（要確認）
- **T9s**: コネクター+スーテッドは評価されるが、ブロッカーなしでスコアが低め。実際はGTOでも一部3ベット候補

### 8-4. スコア式の強み

1. 計算がシンプルで手動実行可能
2. ブロッカー効果を+3/+2/+4で定量化（GTO理論と整合）
3. スーテッド・コネクターボーナスがプレイアビリティを反映
4. ポジション別闘値（18〜23）がGTO頻度データと整合

---

## 本書への適用

- **第12章全体**: スコア式の説明と各要素の理論的根拠として活用
- **ブロッカー項（B）**: セクション2のAA/KK/AK組み合わせ計算を図解に使用
- **代表ハンド5選**: セクション5の各ハンド分析をそのまま実例として活用
- **ポーラライズvs リニア**: 対UTG・対BTNの構造差の説明に使用
- **4ベット耐性**: 3ベット後のシナリオツリーとして提示

---

## 参考URL一覧

- [Understanding 3-Bet Ranges In 2026 | SplitSuit Poker](https://www.splitsuit.com/understanding-3-bet-ranges)
- [3-Bet Preflop Strategy & Range Charts - Upswing Poker](https://upswingpoker.com/3-bet-strategy-aggressive-preflop/)
- [Navigating Range Disadvantage as the 3-Bettor | GTO Wizard](https://blog.gtowizard.com/navigating-range-disadvantage-as-the-3-bettor/)
- [Blockers & Unblockers: The Secret to Picking Great Bluffs | GTO Wizard](https://blog.gtowizard.com/blockers-unblockers-the-secret-to-picking-great-bluffs/)
- [Preflop Range Morphology | GTO Wizard](https://blog.gtowizard.com/preflop-range-morphology/)
- [A Beginner's Guide to Poker Combinatorics | GTO Wizard](https://blog.gtowizard.com/a-beginners-guide-to-poker-combinatorics/)
- [Why Do the Pros Love Ace-Five Suited? GTO Wizard Explains | PokerNews](https://www.pokernews.com/strategy/why-do-the-pros-love-ace-five-suited-47439.htm)
- [Why Do Poker Solvers Love Ace Five Suited So Much? | GipsyTeam](https://www.gipsyteam.com/news/27-11-2024/why-do-poker-solvers-love-ace-five-suited)
- [Ace King: Call Or 3Bet Preflop? | Red Chip Poker](https://redchippoker.com/ace-king-3bet-vs-call-preflop/)
- [Raise the Right Hands: A Field Guide to Linear & Polar 3-Bets](https://www.poker.pro/strategy/raise-the-right-hands-a-field-guide-to-linear-polar-3-bets/)
- [Polarized Ranges vs Linear (Merged) Ranges Explained - Upswing Poker](https://upswingpoker.com/polarized-vs-linear-ranges/)
- [Understand How to Use Blockers the Right Way | Pokercode Blog](https://www.pokercode.com/blog/blockers-in-poker)
- [Poker Combos & Blockers 101 In 2026 | SplitSuit Poker](https://www.splitsuit.com/poker-combos-blockers)
- [Constructing 3-Bet And vs. 3-Bet Ranges - Poker.Pro](https://www.poker.pro/strategy/constructing-3-bet-and-vs-3-bet-ranges-33/)
- [Big Blind 3betting vs IP Opponents: Best Practices and Strategy | 888poker](https://www.888poker.com/magazine/big-blind-3betting-oop-strategy)
- [3-Betting 101 for Beginners: Linear versus Polarized Ranges - MicroGrinder](https://microgrinder.com/poker-strategy-articles/3-betting-101/)
- [How to Size Your 3-Bets Correctly in Poker | Poker.Pro](https://www.poker.pro/strategy/how-to-size-your-3-bets-correctly-in-poker-the-gto-and-live-player-guide/)
- [The Fundamentals of 3-bet Sizing - Tournament Poker Edge](https://www.tournamentpokeredge.com/the-fundamentals-of-3-bet-sizing/)
- [There's Big Money in 4-Bet & 5-Bet Pots - Upswing Poker](https://upswingpoker.com/4-bet-5-bet-preflop-strategy/)
- [Mastering 3-Bet and 4-Bet Poker Strategies | BluffTheSpot](https://www.bluffthespot.com/blog/mastering-3-bet-and-4-bet-poker-strategies)
- [Cold Calling in Poker: Top 3 Do's and Don'ts | 888poker](https://www.888poker.com/magazine/strategy/cold-calling-poker-dos-and-donts)
- [PKO Versus Classic: Responding to 3-Bets | GTO Wizard](https://blog.gtowizard.com/pko-versus-classic-responding-to-3-bets/)
- [Poker 3Bet Range Strategy for Cash Games - Betting Data Lab](https://betting-data-lab.com/poker-3bet-range-strategy-for-cash-games-what-actually-works/)
- [3-Bet Bluff Range Construction, Strategy & Charts - Upswing Poker](https://upswingpoker.com/building-bluffing-ranges-smarter-3-bets/)
