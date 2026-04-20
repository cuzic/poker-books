# 06: ボーナスとペナルティの理論的根拠

検索日: 2026-04-19

## 概要

プリフロップ基本スコア式における各ボーナス・ペナルティの「なぜその値か」を理論的に裏付ける調査結果。
確率データ・エクイティデータを出典とともに記録し、暗記ではなく理解に基づく説明の基盤とする。

---

## 1. ペア +10 の根拠

### セットが入る確率（約12%）

ポケットペアでフロップにセットを作る確率は**約12%（7.5:1）**であることが複数ソースで確認された。

- 確率: 約 11.8%（1/8.5）
- 言い換え: 約8回に1回フロップでセットが入る
- 出典: [Upswing Poker: What Are The Odds of Flopping Poker Hands?](https://upswingpoker.com/odds-flopping-each-poker-hand/)（記事内Table参照）
- 出典: [GipsyTeam: Mining in Poker](https://www.gipsyteam.com/poker/set-mining-in-poker)
- 出典: [Upswing Poker: Set Mining Strategy](https://upswingpoker.com/set-mining-poker-tips/)

### ペア自体のショーダウンバリュー

ポケットペア vs 2枚のオーバーカードのエクイティ比較:

| マッチアップ | ペアのエクイティ |
|-------------|----------------|
| ポケットペア vs 2オーバーカード（一般） | 約 55% |
| QQ vs AKo | 約 57% |
| 55 vs AK | 約 54% |

- ペアはフロップを見る前の段階でも勝率優位を持つ（「コインフリップ」と呼ばれるが実際は55:45）
- 出典: [CardsChat: Pocket pair vs two overcards odds](https://www.cardschat.com/forum/learning-poker-57/pocket-pair-vs-two-overcards-odds-236958/)
- 出典: [PokerListings: Beginners Equity Guide](https://www.pokerlistings.com/poker-guides/beginners-equity-guide-to-standard-situations-in-no-limit-holdem)

### AAのプリフロップエクイティ

- AA vs ランダムハンド: 約85%
- AA vs KK: 約82%
- 出典: [CardFight: AA vs QQ Statistics](https://www.cardfight.com/AA_QQ.html)

### Sklansky Hand Groupsでのペアの位置付け

SklanksyとMalmuthによる「Hold 'em Poker for Advanced Players」のハンドグループ:

| グループ | ペアハンド |
|---------|-----------|
| グループ1 | AA, KK, QQ, JJ |
| グループ2 | TT |
| グループ4 | 99 |
| グループ5 | 88 |
| グループ6 | 77 |
| グループ7 | 66-55, 44-22 |

すべてのポケットペアがグループ1〜7に入る（不要牌なし）。
- 出典: [ThePokerBank: Sklansky and Malmuth Starting Hand Groups](https://www.thepokerbank.com/strategy/basic/starting-hand-selection/sklansky-groups/)
- 出典: [Wikipedia: Texas hold 'em starting hands](https://en.wikipedia.org/wiki/Texas_hold_%27em_starting_hands)

### +10という値の妥当性

- ペアはセット率（12%）＋ショーダウンバリュー（55%+）の二重の価値を持つ
- スーテッド（+2）やコネクター（+1）と比べ、圧倒的な期待値差を反映
- 整数10はスコア最大の差別化因子として機能する（次点の+2の5倍）

---

## 2. スーテッド +2 の根拠

### フロップでフラッシュドローが成立する確率

スーテッドハンドを持っているとき、フロップでフラッシュドローが成立する確率は**約11%**。

- フロップでフラッシュ完成: 約0.8%（118:1）
- フロップでフラッシュドロー成立: 約11%
- フロップ以降リバーまでのフラッシュ完成: **約35%**（ドロー成立後）
- 出典: [Upswing Poker: Odds of Hitting a Draw](https://upswingpoker.com/odds-hitting-draw-in-poker/)
- 出典: [888poker: Flush Poker Odds](https://www.888poker.com/how-to-play-poker/hands/flush-poker-hand-odds/)

### スーテッド vs オフスーツのエクイティ差

| マッチアップ | エクイティ差 |
|-------------|------------|
| AKs vs AA | 34% |
| AKo vs AA | 30% |
| エクイティ差 | 約4% |

スーテッドであることの一般的なエクイティ向上: **約3〜5%**（相手ハンドによる）。

- 出典: [CardFight: AKs vs AKo Statistics](https://www.cardfight.com/AKs_AKo.html)
- 出典: [CardFight: AKs Statistics](https://www.cardfight.com/AKs.html)
- 出典: [CardFight: AKo Statistics](https://www.cardfight.com/AKo.html)

### プレイアビリティ（ポストフロップの選択肢）

スーテッドハンドはポストフロップで以下の利点を持つ:

1. **ナッツフラッシュドローへの期待**: 両方のホールカードを使ったフラッシュは逆インプライドオッズが少ない
2. **ブラフ継続しやすい**: フラッシュドロー＋他のドローで半ブラフが強くなる
3. **ポットをコントロールしやすい**: ドロー系なので降りる判断も明確

- 出典: [BlackRain79: Flush Draw Strategy](https://www.blackrain79.com/2022/09/how-to-play-flush-draws.html)
- 出典: [SomuchPoker: Suited Hands Strategy](https://somuchpoker.com/poker-term/mastering-suited-hands-poker-strategy)

### +2という値の妥当性

- スーテッドはエクイティを3〜5%向上させるが、ペアの+10（12%セット確率＋ショーダウンバリュー）と比べると小さい
- 「+2」はエクイティ改善と暗算のしやすさのバランス点として妥当
- 要確認: スーテッドの純粋な期待値換算での+2の精度（GTO Wizard等の詳細分析が必要）

---

## 3. コネクター（差1）+1 の根拠

### フロップでのストレートドロー確率

コネクター（54〜JT）のフロップ確率:

| ドロータイプ | 確率 |
|-------------|-----|
| 何らかのストレートドロー | 26.2% |
| オープンエンドストレートドロー（OESD） | 9.6% |
| ガットショット | 16.6% |
| ストレート完成 | 1.3% |

- 出典: [PokerRailbird: Straight Draw Poker Odds by Connector Type](https://pokerrailbird.com/straight-draw-poker-odds/)
- 出典: [Upswing Poker: Odds of Flopping Poker Hands](https://upswingpoker.com/odds-flopping-each-poker-hand/)

### スーテッドコネクターのエクイティ

- 76sなどの低スーテッドコネクターのランダムハンドへのエクイティ: 約48%
- {98s, 87s, 76s}のレンジ vs ランダム相手: 48.04%
- 出典: [SplitSuit Poker: How Do Suited Connectors Hit](https://www.splitsuit.com/how-do-suited-connectors-perform/)

### コネクターとスーテッドの相乗効果

スーテッドコネクター（76sなど）は:
- フラッシュドロー（11%）とストレートドロー（26%）の両方が期待できる
- コンビネーションドロー（フラッシュ＋ストレートドロー）で大幅なエクイティ向上
- 出典: [PokerRailbird: Straight Draws & Suited Connectors](https://pokerrailbird.com/straight-draws-suited-connectors-in-poker/)
- 出典: [Upswing Poker: Suited Connectors Strategy](https://upswingpoker.com/suited-connectors-poker-strategy/)

### +1という値の妥当性

- コネクターはストレートドロー率でスーテッド（フラッシュドロー11%）より高い確率（OESD 9.6%）を持つが、フラッシュの方が価値が高い
- +1はスーテッド（+2）の半分として、ストレート形成の貢献度を適切に反映

---

## 4. ギャップ2以内（差2〜3）+0.5 の根拠

### 1-gapperと2-gapperのストレートドロー確率

| ハンドタイプ | ストレートドロー全体 | OESD | ガットショット |
|-------------|-------------------|------|-------------|
| コネクター（差0） | 26.2% | 9.6% | 16.6% |
| 1-gapper（差1） | 21.9% | 7.26% | 14.6% |
| 2-gapper（差2） | 17.9% | 4.47% | 13.5% |

- 出典: [PokerRailbird: Straight Draw Poker Odds](https://pokerrailbird.com/straight-draw-poker-odds/)
- 出典: [Primedope: Texas Hold'em Poker Odds](https://www.primedope.com/texas-holdem-poker-probabilities-odds/)

### コネクターに対するギャップハンドの相対比率

OESDの確率比較:
- 1-gapper: 7.26% / 9.6% = 約75.6%（コネクターの約75%）
- 2-gapper: 4.47% / 9.6% = 約46.6%（コネクターの約47%）

### 特定1-gapperの例（KJ, KT, QT）

KJ、KT、QTのようなハンドはギャップがあっても:
- ストレートのシーケンスを一定数作れる
- 高カード同士の組み合わせでショーダウンバリューも残る

- 出典: [Upswing Poker: Suited Gappers Cash Games](https://upswingpoker.com/suited-gappers-cash-games/)

### +0.5という値の意味

- +0.5は整数ではなく「境界判定」に使われる値
- コネクター（+1）の半分として、ストレート形成の期待値が中程度であることを示す
- 暗算では0.5の積み上げで整数と境界が分かれるため、判断の閾値として機能する

---

## 5. ギャップ3以上（差4+）−1 の根拠

### 広いギャップのストレート形成困難性

差が4以上（例: K8, Q7, J6）になるとストレートを作れる組み合わせが激減する。

- 2-gapperまで: ストレートドロー全体17.9%
- 3+-gapper: ストレートドローがほぼ成立しない（要確認: 正確な数値は個別計算が必要）
- 一般原則: カード間の距離が広がるほど直線上での連結が減少する
- 出典: [888poker: Straight Poker Odds](https://www.888poker.com/how-to-play-poker/hands/straight-poker-hand-odds/)

### エクイティへの影響

- 広いギャップのオフスーツハンド（例: K8o）はプリフロップエクイティが低い
- 「K8o」のような手は高カードの価値を持つが、ポストフロップで相手に制圧されやすい
- ストレート形成ルートが減るとブラフ継続の根拠も弱まる

### −1という値の意図

- +0.5（ギャップ2以内）と−1（ギャップ3以上）の間に+0と−0.5の中間層を作らず、急激なペナルティで「使えないカード同士」の組み合わせを排除
- ギャップが広い手は「ストレートポテンシャルがほぼゼロ」という性質の表現

---

## 6. 両方9未満 −1 の根拠

### 低いカードのショーダウン劣位

低いカード同士（例: 65, 74, 83）の弱点:

1. **キッカー負け**: フロップで相手がトップペアを作ると負けるケースが多い
2. **ペア負け**: 自分が低いペアを作っても相手の高いペアに負ける
3. **スプリットポット回避不可**: 高カードがないためボードで2ペアになったとき分けられる

### 65sの実際のエクイティ

- 65sのフロップ後パフォーマンス:
  - フロップでトップペアを作る確率: 約4%（しかも2番手・3番手ペアが多い）
  - フロップで2ペア以上: 約5.5%
  - ランダムハンドへのエクイティ: 約48%（高カードハンドより低い）
- 出典: [SplitSuit Poker: How Do Suited Connectors Hit](https://www.splitsuit.com/how-do-suited-connectors-perform/)

### 65sの強みはストレートであり、ショーダウンではない

65sは以下の理由でコネクターとして価値があるが、カード自体の数値が低いため:
- ストレートを作れるルートは {A2345, 23456, 34567, 45678} の4通り
- これに対してJTsは8通り（より多くのストレートが狙える）
- 低いストレートは相手に上位ストレートで負けるリスクもある

### 両方9未満の組み合わせにおける特定リスク

- **ドミネーション**: 8高以下で相手が9以上のペアを持つと常に劣位
- **「勝てる場面」が限定的**: ストレートかフラッシュを作るか、相手もミスしなければ勝ちにくい
- 出典: [Upswing Poker: Raw Equity vs Realized Equity](https://upswingpoker.com/raw-equity-vs-realized-equity/)

### −1という値の意図

- 低いカード同士の組み合わせは「価値があるが状況が限定的」という中程度のペナルティ
- −1にとどめているのは、スーテッドコネクター（65sなど）ではまだ価値があるため
- 極端なペナルティ（−3や−5）にしないのは、状況次第でプレイ可能な手が存在するから

---

## 7. 各ボーナス/ペナルティ値の相対性とバランス

### 値の比率と理論的意味

| ボーナス/ペナルティ | 値 | 根拠となる確率的優位 |
|-------------------|---|-------------------|
| ペア | +10 | セット率12% ＋ ショーダウンバリュー(55%+) ＋ Sklansky全グループカバー |
| スーテッド | +2 | フラッシュドロー11% ＋ エクイティ向上3〜5% ＋ プレイアビリティ |
| コネクター | +1 | ストレートドロー26% / OESD 9.6% |
| ギャップ2以内 | +0.5 | ストレートドロー17〜22% / OESD 4〜7% |
| ギャップ3以上 | −1 | ストレートポテンシャルがほぼゼロ |
| 両方9未満 | −1 | ショーダウンバリュー低下 ＋ ドミネーションリスク |

### 整数化の意図とトレードオフ

- +10はペアの圧倒的優位を「一桁大きい」値で表現
- +2/+1/+0.5は加算要素の相対的貢献度を段階的に表現
- −1は「あってほしくない性質」の最小ペナルティ単位

**暗算しやすさとのトレードオフ:**
- 実際のエクイティ差は連続値だが、整数化（0.5単位）により暗算が容易になる
- 精度よりも「方向性」が正しい値であることが重要（+10 >> +2 >> +1 >> 0 >> −1）
- 値の絶対的な精度よりも相対的な順序が実戦的意思決定を正しく導くことが目的

### 要確認事項

- 76s vs AA の正確なエクイティ（約22%という数値の出典確認）
- 3+-gapper のフロップストレートドロー確率の正確な数値
- 低いカード同士（9未満）の平均エクイティをランダムハンドと比較した具体的数値

---

## 本書への適用

- **第6章「ボーナスとペナルティの意味」**での活用:
  - 各ボーナス値の「なぜ」を確率データで説明する際の根拠として使用
  - セット率12%、フラッシュドロー11%、OESD 9.6% などの数値を本文に引用
  - Sklarsky Hand Groupsをペアの価値説明の補足根拠として使用
  - ギャップによるストレートドロー確率の段階的低下を表で可視化

- **表や図解の提案**:
  - ギャップ別ストレートドロー確率の棒グラフ
  - ペア/スーテッド/コネクターのエクイティ寄与を積み上げグラフで表現

---

## 参考URL一覧

| タイトル | URL | 参照内容 |
|---------|-----|---------|
| Upswing: Set Mining Strategy | https://upswingpoker.com/set-mining-poker-tips/ | セット率12%、セットマイニングの収益性 |
| Upswing: Odds of Flopping Poker Hands | https://upswingpoker.com/odds-flopping-each-poker-hand/ | フロップ確率テーブル全般 |
| Upswing: Odds of Hitting a Draw | https://upswingpoker.com/odds-hitting-draw-in-poker/ | フラッシュドロー・ストレートドロー確率 |
| Upswing: Suited Connectors Strategy | https://upswingpoker.com/suited-connectors-poker-strategy/ | スーテッドコネクターの戦略 |
| Upswing: Suited Gappers Cash Games | https://upswingpoker.com/suited-gappers-cash-games/ | ギャッパーの扱い方 |
| Upswing: Raw vs Realized Equity | https://upswingpoker.com/raw-equity-vs-realized-equity/ | エクイティとプレイアビリティの関係 |
| SplitSuit: How Suited Connectors Hit (2026) | https://www.splitsuit.com/how-do-suited-connectors-perform/ | スーテッドコネクターのフロップ成績 |
| PokerRailbird: Straight Draw Poker Odds | https://pokerrailbird.com/straight-draw-poker-odds/ | ギャップ別ストレートドロー確率比較 |
| PokerRailbird: Suited Connectors | https://pokerrailbird.com/straight-draws-suited-connectors-in-poker/ | スーテッドコネクターの解説 |
| 888poker: Flush Poker Odds | https://www.888poker.com/how-to-play-poker/hands/flush-poker-hand-odds/ | フラッシュ確率の詳細 |
| 888poker: Straight Poker Odds | https://www.888poker.com/how-to-play-poker/hands/straight-poker-hand-odds/ | ストレート確率の詳細 |
| CardFight: AKs vs AKo | https://www.cardfight.com/AKs_AKo.html | スーテッドエクイティ差 |
| CardFight: AKs Stats | https://www.cardfight.com/AKs.html | AKsの統計 |
| CardFight: AKo Stats | https://www.cardfight.com/AKo.html | AKoの統計 |
| ThePokerBank: Sklansky Groups | https://www.thepokerbank.com/strategy/basic/starting-hand-selection/sklansky-groups/ | ハンドグループ分類 |
| Wikipedia: Texas Hold'em Starting Hands | https://en.wikipedia.org/wiki/Texas_hold_%27em_starting_hands | ハンドランキング全般 |
| CardsChat: Pair vs Overcards | https://www.cardschat.com/forum/learning-poker-57/pocket-pair-vs-two-overcards-odds-236958/ | ペア vs オーバーカードのエクイティ |
| Primedope: TX Hold'em Odds | https://www.primedope.com/texas-holdem-poker-probabilities-odds/ | 確率テーブル詳細 |
| BlackRain79: Flush Draw Strategy (2022) | https://www.blackrain79.com/2022/09/how-to-play-flush-draws.html | フラッシュドロー戦略 |
| GipsyTeam: Set Mining | https://www.gipsyteam.com/poker/set-mining-in-poker | セットマイニング概要 |
| PokerListings: Beginners Equity Guide | https://www.pokerlistings.com/poker-guides/beginners-equity-guide-to-standard-situations-in-no-limit-holdem | 標準的エクイティガイド |
