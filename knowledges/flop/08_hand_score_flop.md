# HandScore：フロップでの手の強さを数値化

検索日: 2026-04-20

## 概要

フロップでの手の相対的な強さは、絶対的なハンドランキングではなく、
相手のレンジに対するエクイティ・将来の期待値（EV）・エクイティ実現率（EQR）
の組み合わせで評価される。
本章では、セット〜アンダーペアまでの各手の実戦的価値と、
フラッシュドロー・コンボドローのエクイティ、ブロッカーの定量的影響を整理する。

---

## 主要な知見

### 1. フロップでの役の相対価値（エクイティ比較）

| ハンド | 相手 | エクイティ | 備考 |
|--------|------|-----------|------|
| セット | トップペア | **約96%** | ほぼ確実な勝利 |
| セット | フラッシュドロー+ストレートドロー（コンボ） | **約58%** | コンボドローでも依然優位 |
| セット | 単フラッシュドローまたはOESD | **約75%** | 3:1のファボリット |
| トップペア（TPTK） | フラッシュドロー | **約55%** | FD側は45%エクイティ保持 |
| トップペア（TPTK） | OESD | **約67%** | ストレードロー側は33% |
| トップペア（TPTK） | 下位ペア | **約80%** | 上位ペアが強い支配 |
| TPTK vs 弱キッカーTP | キッカーの差 | **約87%** | AK vs KQ on K84 |
| オーバーペア | アンダーペア | **約80%** | 基本的な支配率 |
| QQ vs 広いレンジ（35%） | Aハイフロップ | **約60%** | オーバーカードでEV激減 |
| QQ vs 広いレンジ（35%） | Kハイフロップ | **約68%** | やや改善 |
| QQ vs 広いレンジ（35%） | Qハイフロップ | **約95%** | 最大強度 |

- 出典: [Beginners Equity Guide to Standard Situations in No-Limit Hold'em – PokerListings](https://www.pokerlistings.com/poker-guides/beginners-equity-guide-to-standard-situations-in-no-limit-holdem)
- 出典: [Developing a Feel for Equities in No-Limit Hold'em Part 5: Hitting Pairs – FlopTurnRiver](https://flopturnriver.com/poker-strategy/developing-feel-equities-in-no-limit-holdem-part-5-hitting-pairs-20478/)

---

### 2. TPTK（Top Pair Top Kicker）の強さ

#### AK on Kハイボード（TPTK）の統計的特徴

- **コーリングレンジに対するエクイティ**: 一般に **70〜80%**
- AKはフロップで約**29%の確率**でTPTKを形成する
  （AフロップまたはKフロップで常にTPTK）
- ドライボード（A♣7♦2♠など）では極めて強力
- コネクテッドボード（A♦J♦T♠など）では大幅に弱体化

#### ボードテクスチャによるEV変化の例（Upswing Poker調査）

| ボード | 手 | EV（チップ） | 備考 |
|--------|-----|------------|------|
| T-9-3 レインボー | AT (TPTK) | **67.8** | ドライで強力 |
| T-9-8 コネクテッド | AT (TPTK) | **37.9** | ほぼ半分に減少 |

コネクテッドボードではTPTKの価値は約半分になる。

- 出典: [How to Play Top Pair Top Kicker in Cash Games – Upswing Poker](https://upswingpoker.com/top-pair-top-kicker/)
- 出典: [How Does Ace King Hit The Flop – SplitSuit Poker](https://www.splitsuit.com/how-does-ace-king-hit-flops)

#### TPTK戦略上の基本原則

- ドライボードでは積極的にベット（ほとんど常にベット推奨）
- コネクテッドボードでは50%以上の頻度でチェック
- マルチウェイポットでは小さいベットサイズを使用
- 出典: [Upswing Poker TPTK Guide](https://upswingpoker.com/top-pair-top-kicker/)

---

### 3. オーバーペアのリスクと「オーバーペア病」

#### オーバーカードが落ちる確率

| ハンド | フロップにオーバーカードが落ちる確率 |
|--------|--------------------------------------|
| KK | 23%（Aが落ちる） |
| QQ | **43%** |
| JJ | **59%** |
| TT | **71%** |
| 99 | **81%** |

JJを持っているときの約60%のフロップで何らかのオーバーカードが存在する。

- 出典: [5 Easy Ways to Stop Overplaying Your Overpairs – BlackRain79](https://www.blackrain79.com/2019/01/overplay-overpair.html)
- 出典: [How to Play Overpairs Out-of-Position in Cash Games – PokerCoaching](https://pokercoaching.com/blog/how-to-play-overpairs-out-of-position-in-cash-games/)

#### JJ on K82 など「上位カードが落ちたオーバーペア」の戦略的評価

JJがKハイボード（例：K-8-2）で直面する問題:

1. **レンジ劣位**: 相手はKxを多く含み、ヒットしている
2. **ナッツアドバンテージなし**: 相手がセットやTPTKを持ちうる状況で、JJは「ベストハンドではない」
3. **GTO Wizardソルバーによれば**: KKはある種のポジションから88%の頻度でチェックすることが最適
4. **対処法**: チェック/コールを基本とし、大きな抵抗には降りる

「オーバーペア病（entitlement tilt）」: プリフロップで最強だったからといって、ポストフロップでも強いと誤信して大きなポットを形成してしまう傾向。

> "Overpairs on dangerous boards — check/call most of the time, check/fold in some cases."
> ― BlackRain79

- 出典: [5 Easy Ways to Stop Overplaying Your Overpairs – BlackRain79](https://www.blackrain79.com/2019/01/overplay-overpair.html)
- 出典: [Checking Flops with Overpairs: When Should You Do It? – Upswing Poker](https://upswingpoker.com/when-to-check-overpairs/)
- 出典: [Jonathan Little: When Is It Time to Fold Your Overpair? – PokerNews](https://www.pokernews.com/strategy/jonathan-little-weekly-poker-hand-hero-fold-overpair-36222.htm)

---

### 4. 各ドローのエクイティ（フロップ版）

#### フロップでの2枚残りエクイティ（基本計算: アウツ×4）

| ドローの種類 | アウツ | エクイティ概算 | vs TPTKでの実勢値 |
|-------------|--------|--------------|-----------------|
| ナッツフラッシュドロー | 9 | 36% | **約35〜45%** |
| OESD（両面ストレートドロー） | 8 | 32% | **約33%** |
| ガットショット | 4 | 16% | 約16% |
| ガットショットストレートフラッシュドロー | 12 | 48% | オーバーペアにほぼ五分 |
| OESD + フラッシュドロー（コンボ） | 15 | 60% | **約54〜60%**（TPに対し有利） |

重要な区分:

- **シンプルなFDまたはOESD**: 30〜35%エクイティ → 単独ではアンダードッグ
- **コンボドロー（FD+OESD）**: 50%以上 → 1ペア相手では**ファボリット**
  - 最も弱いコンボドロー（ガットショットSFD、12アウツ）でもオーバーペアにほぼ五分
  - オールインを合理的に受け入れられる

- 出典: [How to Play Combo Draws on the Flop – PokerListings](https://www.pokerlistings.com/strategy/playing-combo-draws-on-the-flop)
- 出典: [Beginners Equity Guide to Standard Situations – PokerListings](https://www.pokerlistings.com/poker-guides/beginners-equity-guide-to-standard-situations-in-no-limit-holdem)
- 出典: [Calling an All-In with a Flush Draw – Jonathan Little](https://jonathanlittlepoker.com/allinwithflushdraw/)

#### GTO Wizardによるエクイティ実現率（EQR）

同じエクイティでも、手によってEVへの変換効率（EQR）が大きく異なる:

| ハンド | EQR | 理由 |
|--------|-----|------|
| セット・ストレート・フラッシュ | **100%超** | 強くベットしてポットを拡大できる |
| 中程度のメイドハンド（セカンドペアなど） | **大幅に下回る** | ベットすると上位に負け、チェックすると追い出されない |
| ナッツドロー | **100%前後** | 積極的にポットに参加できる |
| 弱いドロー（OOP） | **87%程度** | 相手のベットに押し出されやすい |

> "The hands in the middle suffer most from betting — they risk either putting money in against better hands or folding inferior ones."
> ― GTO Wizard, Equity Realization Article

- 出典: [Equity Realization – GTO Wizard Blog](https://blog.gtowizard.com/equity-realization/)

---

### 5. ブロッカーの価値（フロップ版）

#### ナッツブロッカーの基本概念

ブロッカーとは、自分の手札がある特定のハンドを相手が持つ可能性を排除するカードのこと。

**例: スペード3枚ボードでA♠を持つ場合**

- 相手がナッツフラッシュ（Aハイフラッシュ）を持つことが**不可能**になる
- 相手のコール・レイズレンジが軽くなり、ブラフの成功率が上昇
- 「フォールドエクイティ」が上昇する

ブロッカーの利用原則（GTO Wizard）:

- **バリューベット時**: 相手の弱いハンド（コールしてくるゴミ）をブロックしない、相手の強いハンド（バリュー）をブロックしない → コールが取れる構成
- **ブラフ時**: 相手の強いハンド（バリュー）をブロックする、相手の弱いハンド（ゴミ）はブロックしない → フォールドが取れる構成

#### 定量的な影響（GTO Wizard分析）

GTO Wizard はブロッカースコアを0〜10のスケールで定量化:

- **バリュー除去スコア（Value Removal）**: 相手のバリューハンドをどれだけブロックするか
- **ゴミ除去スコア（Trash Removal）**: 相手のブラフをどれだけブロックするか

ブラフ時の理想: 高いバリュー除去 + 低いゴミ除去

フロップでは多くの可能なハンドが存在するため、1枚のブロッカーの影響は限定的。
リバーでは保有コンボが絞られ、ブロッカー効果が最も大きくなる。

**経験則**: A♠を持つことで相手がA♠絡みのナッツフラッシュを持つ確率を除外できる。
これはフォールドエクイティに換算すると状況依存だが、
ブロッカー保有により相手の強ハンドコンボ数を最大**12.7%削減**できる
（相手のデッキから1枚を除いた効果）。

- 出典: [Understanding Blockers in Poker – GTO Wizard Blog](https://blog.gtowizard.com/understanding-blockers-in-poker/)
- 出典: [Blockers & Unblockers: The Secret to Picking Great Bluffs – GTO Wizard Blog](https://blog.gtowizard.com/blockers-unblockers-the-secret-to-picking-great-bluffs/)
- 出典: [Blockers in Poker Guide – SplitSuit Poker](https://www.splitsuit.com/blockers-in-poker-guide)

---

### 6. 相対スコアリングの先行事例

#### Effective Hand Strength (EHS) アルゴリズム（Billings et al., 1998）

**コンピュータ科学的なハンド強度計算**:

```
EHS = HS × (1 − NPOT) + (1 − HS) × PPOT
```

- **HS**: 現在の手の強さ（全相手コンボ中の勝率パーセンタイル）
- **PPOT**: ポジティブポテンシャル（負けている手が改善して勝つ確率）
- **NPOT**: ネガティブポテンシャル（勝っている手が負けに転じる確率）

フロップでは1,081通りの相手の2枚コンビネーションが存在し、
それぞれに対して現在の手が勝ち・負け・引き分けを数え、
将来のボードを全列挙して計算する。

- 出典: [Effective Hand Strength Algorithm – Wikipedia](https://en.wikipedia.org/wiki/Effective_hand_strength_algorithm)
- 出典: [5.2 Hand Strength – University of Alberta (Papp, 1998)](https://webdocs.cs.ualberta.ca/~jonathan/PREVIOUS/Grad/papp/node38.html)

#### 実戦的なハンドカテゴリ分類（業界標準）

主要なポーカー教育プラットフォームで用いられる分類体系:

| カテゴリ | 代表的なハンド | 行動方針 |
|---------|------------|---------|
| **モンスター** | セット、ストレート、フラッシュ | 積極的にベット、ポットを拡大 |
| **ストロングバリュー** | TPTK、オーバーペア（ドライボード） | バリューベット、3ストリート可 |
| **ミディアム** | TPWK、セカンドペア、オーバーペア（ウェット） | 2ストリートバリュー、ポットコントロール |
| **ウィーク** | ミドルペア、アンダーペア | ショーダウンバリュー、小さいベット |
| **ドロー** | FD、OESD、コンボドロー | セミブラフ候補、エクイティ依存 |

- 出典: [Poker Hand Strength: Just How Good is your Hand? – PokerProfessor](https://www.pokerprofessor.com/university/how-to-win-at-poker/poker-hand-strength/)
- 出典: [Matthew Janda, Applications of No-Limit Hold'em (2013)](https://www.amazon.com/Applications-No-Limit-Hold-Matthew-Janda/dp/1880685558)
  - トピック索引に「value hands」「flush draws」「top pair」「strong hands」等が列挙される

#### 相対的な手の強さの原則（Thinking Poker）

絶対的なハンドランキングより、**相手のレンジに対するエクイティ**が重要:

- AA vs 特定のドローレンジ: 17%エクイティ
- セット(4s) vs 同レンジ: 18%エクイティ
- ナッツフラッシュドロー vs 同レンジ: **31%エクイティ**（最も高い）

後者の例はメイドハンドより強いドローがありうることを示す。
単純なハンドランキングではなく、レンジとの相互作用が本質。

- 出典: [Relative Hand Strength – Thinking Poker](https://www.thinkingpoker.net/articles/relative-hand-strength-poker/)

---

### 7. TP弱キッカー・セカンドペア・アンダーペアの実戦評価

#### 7-1. トップペア弱キッカー（TPWK）: K5 on K72

- 弱いキッカー（9以下）を伴うトップペアはTPTKより大幅に価値が低い
- **3ストリートのバリューベット不可**: 基本は2ストリートまで
- ポジション別推奨アクション（Upswing Poker調査）:

| 状況 | 推奨 |
|------|------|
| IP（プリフロップレイザー） | チェックバック（レンジ保護） |
| OOP（プリフロップレイザー） | チェック/コール |
| 3ベットポット（どちらのポジションでも） | ベット（SPR小さいため） |
| BBディフェンダー | チェック/コール |

- K-5 on K-7-2: 「弱いTP（TPWK）」として分類
- K72ボードで継続ラインの境界: **3番目以上のキッカー（≒上位3分の1）でベット可**
- 出典: [How to Play Top Pair Weak Kicker – Upswing Poker](https://upswingpoker.com/top-pair-weak-kicker/)
- 出典: [Playing Top-Pair/Weak-Kicker – PokerStars Learn](https://pokerstarslearn.com/poker/learn/strategies/playing-top-pair-weak-kicker/)

#### 7-2. セカンドペア（ミドルペア）の評価

- ドライボードでのセカンドペアは**意外に強力**
- 相手がTPを保持している確率は**約33%**（逆に言えば67%で勝っている）
- 実戦での手強さ（ランダムフィールド対比）: **約17%の勝率**（多人数場合）
- 戦略:
  - ドライボード vs タイトな相手: 積極的なベット可
  - コネクテッドボード: チェック基本
  - コールされた後のターン: 改善しなければ基本シャットダウン
  - 大きなアクションへの対応: 「強いハンドか強いドロー以外でここに投資しない」

- 出典: [Poker Trouble Spot: How to Play Second Pair on the Flop – PokerListings](https://www.pokerlistings.com/strategy/poker-trouble-spots-second-pair-part-1)
- 出典: [Should I Check or Bet Second Pair? – SplitSuit Poker](https://www.splitsuit.com/should-i-check-or-bet-second-pair)

#### 7-3. アンダーペア: 8-8 on K72

アンダーペアとは「フロップの最低カードより小さいポケットペア」（例: 22〜55 on K-J-6）。

ただし8-8 on K72は「アンダーペア」ではなく**「セカンドペア相当の弱いオーバーペア」**に近い位置づけだが、Kの下では相手のベストハンドに負けるリスクが高い。

状況別推奨（Upswing Pokerのアンダーペアガイド）:

| 状況 | 推奨 |
|------|------|
| ダブルブロードウェイフロップ（K-Q-7型） | フラッシュドロー有無でCbet可 |
| シングルブロードウェイフロップ（Q-8-7型） | 22・33のみCbet、高いペアはチェック |
| ローフロップ（9-5-4型） | 基本チェックバック |
| 3ベットポット | **常にCbet**（レンジアドバンテージ大） |

- 出典: [How To Play Underpairs in Cash Games – Upswing Poker](https://upswingpoker.com/underpairs/)
- 出典: [The Correct Way To Play An Underpair – Card Player Magazine](https://www.cardplayer.com/cardplayer-poker-magazines/66517-global-poker-36-13/articles/24846-the-correct-way-to-play-an-underpair)

---

## HandScoreシステムの設計指針（本書オリジナル）

上記の調査を元に、本章で使う「HandScore（0〜100点）」の骨格:

| スコア帯 | ハンドカテゴリ | 代表例 |
|---------|------------|------|
| 90〜100 | モンスター | セット、フラッシュ、ストレート |
| 70〜89 | ストロングバリュー | TPTK（ドライ）、オーバーペア（ドライ） |
| 50〜69 | ミディアムバリュー | TPWK、オーバーペア（ウェット）、TPTK（ウェット） |
| 30〜49 | ショーダウンバリュー | セカンドペア、アンダーペア |
| 10〜29 | ドロー/弱ハンド | FD単独、OESD単独 |
| ±3 補正 | ブロッカー調整 | ナッツブロッカー保有で+3 |

**ブロッカー補正の根拠**:
ナッツブロッカー（例: Aスペードを保有してスペード3枚ボード）を持つことで、
相手のナッツコンボを除外し実質的なフォールドエクイティが上昇する。
GTO Wizardのブロッカースコア概念を参照し、
フロップでの実用的影響として±3点を設定（要確認: より精密な計算は今後の課題）。

---

## 本書（フロップ編 第8章）への適用

1. **HandScore概念の導入**: セット=95点、TPTK=75点、コンボドロー=55点等の数値で「手の強さを見える化」
2. **ドロー vs メイドハンドの逆転ポイント**: コンボドローは1ペアに対して有利になり得ることを数値で示す
3. **オーバーペア病の警告**: JJ on K82での数値的弱体化（オーバーカード確率59%）を可視化
4. **弱キッカーの価値劣化**: K5 vs KJ on K72のエクイティ比較（87%対13%のキッカー差）
5. **ブロッカーの+3補正**: ナッツブロッカー保有で小さく加点するルールの実戦的説明
6. **第6章（エクイティ基礎）との連動**: ドローのアウツ→エクイティ→HandScoreという流れで接続

---

## 参照文献一覧

- [Beginners Equity Guide to Standard Situations in No-Limit Hold'em – PokerListings](https://www.pokerlistings.com/poker-guides/beginners-equity-guide-to-standard-situations-in-no-limit-holdem)
- [How to Play Top Pair Top Kicker in Cash Games – Upswing Poker](https://upswingpoker.com/top-pair-top-kicker/)
- [How to Play Top Pair Weak Kicker In Cash Games – Upswing Poker](https://upswingpoker.com/top-pair-weak-kicker/)
- [How To Play Underpairs in Cash Games – Upswing Poker](https://upswingpoker.com/underpairs/)
- [5 Easy Ways to Stop Overplaying Your Overpairs – BlackRain79](https://www.blackrain79.com/2019/01/overplay-overpair.html)
- [Overplaying Top Pair Hands – BlackRain79](https://www.blackrain79.com/2012/01/overplaying-top-pair-hands.html)
- [How to Play Overpairs Out-of-Position in Cash Games – PokerCoaching](https://pokercoaching.com/blog/how-to-play-overpairs-out-of-position-in-cash-games/)
- [Checking Flops with Overpairs: When Should You Do It? – Upswing Poker](https://upswingpoker.com/when-to-check-overpairs/)
- [How to Play Combo Draws on the Flop – PokerListings](https://www.pokerlistings.com/strategy/playing-combo-draws-on-the-flop)
- [Understanding Blockers in Poker – GTO Wizard Blog](https://blog.gtowizard.com/understanding-blockers-in-poker/)
- [Blockers & Unblockers: The Secret to Picking Great Bluffs – GTO Wizard Blog](https://blog.gtowizard.com/blockers-unblockers-the-secret-to-picking-great-bluffs/)
- [Equity Realization – GTO Wizard Blog](https://blog.gtowizard.com/equity-realization/)
- [Effective Hand Strength Algorithm – Wikipedia](https://en.wikipedia.org/wiki/Effective_hand_strength_algorithm)
- [5.2 Hand Strength – University of Alberta (Papp, 1998)](https://webdocs.cs.ualberta.ca/~jonathan/PREVIOUS/Grad/papp/node38.html)
- [Relative Hand Strength – Thinking Poker](https://www.thinkingpoker.net/articles/relative-hand-strength-poker/)
- [Jonathan Little: When Is It Time to Fold Your Overpair? – PokerNews](https://www.pokernews.com/strategy/jonathan-little-weekly-poker-hand-hero-fold-overpair-36222.htm)
- [Poker Trouble Spot: How to Play Second Pair on the Flop – PokerListings](https://www.pokerlistings.com/strategy/poker-trouble-spots-second-pair-part-1)
- [The Correct Way To Play An Underpair – Card Player Magazine](https://www.cardplayer.com/cardplayer-poker-magazines/66517-global-poker-36-13/articles/24846-the-correct-way-to-play-an-underpair)
- [Dominating with Nut Advantage: A Key Edge in Poker Strategy – PokerCoaching](https://pokercoaching.com/blog/dominating-with-nut-advantage-a-key-edge-in-poker-strategy/)
- [Developing a Feel for Equities in No-Limit Hold'em Part 5 – FlopTurnRiver](https://flopturnriver.com/poker-strategy/developing-feel-equities-in-no-limit-holdem-part-5-hitting-pairs-20478/)
- [Calling an All-In with a Flush Draw – Jonathan Little](https://jonathanlittlepoker.com/allinwithflushdraw/)
- [Should I Check or Bet Second Pair? – SplitSuit Poker](https://www.splitsuit.com/should-i-check-or-bet-second-pair)
- [Matthew Janda, Applications of No-Limit Hold'em (2013) – Amazon](https://www.amazon.com/Applications-No-Limit-Hold-Matthew-Janda/dp/1880685558)
