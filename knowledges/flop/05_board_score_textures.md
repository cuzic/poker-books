# ボードテクスチャを数値化する（BoardScore）

検索日: 2026-04-20

---

## 概要

テキサスホールデムのフロップは理論上 C(52,3) = 22,100 通りあるが、スートの等価性を考慮した「戦略的に異なるフロップ」は **1,755 通り**に絞り込まれる。このフロップをいかに分類・数値化して素早く評価するかが、ポストフロップ戦略の出発点となる。ボードテクスチャとは、3枚のコミュニティカードがどれほど「繋がり（コネクティビティ）」と「同スート性（スーテッドネス）」を持つかを指す複合的な概念であり、ドロー可能性・レンジ有利性・CBet 頻度と密接に連動する。

---

## 主要な知見

### 知見1: 1,755 通りのフロップ分布

| カテゴリー | 実際の組み合わせ数 | 割合 |
|---|---|---|
| **レインボー**（3スート全異なる） | 7,804 | 39.76% |
| **ツートーン**（2枚同スート） | 10,944 | 55.84% |
| **モノトーン**（3枚全同スート） | 1,176 | 5.18% |（※要確認: 一部資料では 6.61% = 1,296 組み合わせ）|
| **ペアボード**（1ランクが2枚） | 3,744 | 19.10% |

- 出典: [Flop Heuristics: IP C-Betting in Cash Games - GTO Wizard](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)
- 出典: [The Top 5 Flop Textures to Optimise Your Poker Study - MTP Poker School](https://www.mttpokerschool.com/single-post/otb-048-the-top-5-flop-textures-to-optimise-your-poker-study)

**補足**: ツートーン（フラッシュドロー可能）ボードが過半数を占めることに注意。モノトーンはわずか約5%。

---

### 知見2: Gareth James の 12 カテゴリー分類（PokerListings）

Gareth James は 1,755 通りを **12 種類**に整理し、学習効率化を提案した。SplitSuit Poker の「Flop Texture Tool」もこの分類体系を採用している。

| # | カテゴリー | 例 | 頻度 |
|---|---|---|---|
| 1 | ABB boards（A + 2枚のブロードウェイ） | A-Q-J | 1.74% |
| 2 | ABx boards（A + ブロードウェイ + ローカード） | A-K-2 | 9.27% |
| 3 | Axy boards（A + 2枚のローカード） | A-8-4 | 8.11% |
| 4 | 2 broadway boards（K/Q/J/T + 1枚 + ローカード） | K-Q-3 | 13.90% |
| 5 | BBB boards（3枚のブロードウェイ） | K-Q-J | 1.16% |
| 6 | K/Q+2 boards（K or Q + 2枚のローカード） | K-8-3 | 16.22% |
| 7 | J/T+2 boards（J or T + 2枚のローカード） | J-7-2 | 13.61% |
| 8 | J/T connected boards（J or T + コネクテッド） | J-9-8 | 2.61% |
| 9 | Low connected boards（ローカードのコネクテッド） | 7-6-5 | 7.82% |
| 10 | Low unconnected boards（ローカードのアンコネクテッド） | 8-3-2 | 8.40% |
| 11 | Paired boards（ペアボード） | T-T-4 | 16.94% |
| 12 | Trips boards（トリップスボード） | J-J-J | 0.24% |

- 出典: [Poker Math by Gareth James: Types of Flop Texture - PokerListings](https://www.pokerlistings.com/poker-strategies/poker-math-by-gareth-james-types-of-flop-texture)

**学習優先度の提案（Gareth James）**: 頻度上位5カテゴリーに絞ると効率的。
1. Paired boards（16.94%）
2. K/Q+2 boards（16.22%）
3. 2 broadway boards（13.90%）
4. J/T+2 boards（13.61%）
5. ABx boards（9.27%）

**A-high ボード**は合計（ABB + ABx + Axy = 1.74 + 9.27 + 8.11 = **19.12%**）で最多頻度。ただしサブカテゴリーでプレイが大きく異なるため、まとめて学習するのは非推奨。

---

### 知見3: Upswing Poker の 6 分類（スート×コネクティビティの組み合わせ）

Upswing Poker は実践的な 6 分類を提示している。

| # | カテゴリー | 例 | CBet 戦略の概要 |
|---|---|---|---|
| 1 | **レインボー・ディスコネクテッド**（ドライ） | K♦7♥3♠, A♠9♣4♦ | マージドレンジで小サイズ（25-33%ポット）高頻度 |
| 2 | **ペアボード** | J♠J♣5♥, 9♣9♥7♣ | ドライ寄りで小サイズ高頻度 |
| 3 | **レインボー・コネクテッド** | K♠9♥5♦, J♣9♠6♥ | 大サイズ（50-66%ポット）でドロー牽制 |
| 4 | **ツートーン・ディスコネクテッド** | K♣8♣3♦, Q♥7♥3♣ | 小サイズで高頻度CBet |
| 5 | **ツートーン・コネクテッド** | J♠8♠6♥, T♦7♦5♣ | ポーラライズドで大サイズ |
| 6 | **モノトーン** | A♥T♥4♥, J♠6♠4♠ | チェック多用、セット＋フラッシュのみバリュー |

- 出典: [10 Fundamental Tips for The Most Common Types of Flops - Upswing Poker](https://upswingpoker.com/board-texture-tips/)

---

### 知見4: GTO 的「ドライ／ウェット」の境界と CBet 頻度

GTO ソルバー（GTO Wizard）のデータから、ボードテクスチャと CBet 戦略には明確なパターンがある。

#### 「ウェットネス・パラボラ」（GTO Wizard の知見）

CBet サイズはボードテクスチャに対して放物線を描く：

```
ドライ  → 小サイズ（33%ポット）  + 高頻度
中程度のウェット → 大サイズ（75-130%ポット）+ 中程度の頻度
超ウェット → 小サイズ（33%ポット）  + 低頻度
```

- **ドライボード例（Q♥Q♣6♦）**: CBet 頻度 100%、主サイズ 33%ポット、相手フォールド率 37%
- **中程度のウェット（K♥J♥7♦）**: 75%・125%ポットのオーバーベットが主力、フォールド率 62%
- **超ウェット（Q♦J♦T♦）**: チェック約50%、ベット時は 33%ポット、フォールド率 37%

根拠：超ウェットボードでは相手の継続レンジの 29.4% がストレート・フラッシュ（60%以上のエクイティ）で占められるため、大きいベットは意味がない。

- 出典: [The Mechanics of C-Bet Sizing - GTO Wizard](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/)
- 出典: [Flop Heuristics: IP C-Betting in Cash Games - GTO Wizard](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)

#### Upswing Poker クイズデータ（特定フロップの GTO CBet 頻度）

| フロップ | CBet 頻度 |
|---|---|
| K♥K♦5♣（ペアボード・ドライ） | 100% |
| Q♠Q♦7♠（ペアボード・ドライ） | 92% |
| 7♥7♦7♣（トリップスボード） | 100% |
| A♦K♥Q♠（ブロードウェイ・ドライ） | 76% |
| A♥K♥Q♣（ブロードウェイ・ツートーン） | 82% |
| A♦8♦4♣（A-high・ドライ） | 54% |
| K♦7♦6♣（K-high・ミッドレンジ） | 61% |
| 8♠7♥6♦（ロー・コネクテッド・ウェット） | 63% |
| J♦9♠7♠（コネクテッド・ツートーン） | 44% |
| T♠7♦6♦（コネクテッド・ツートーン） | 34% |

- 出典: [GTO C-Bet Frequency Quiz Answers - Upswing Poker](https://upswingpoker.com/gto-c-bet-quiz-answers/)

#### GTO Wizard のスーツ別 CBet 傾向（BTN vs BB SRP）

| スーツ構成 | CBet 傾向 |
|---|---|
| レインボー | 最高頻度（ドロー少なくレンジ優位維持しやすい） |
| ツートーン（フラッシュドロー可能） | やや低頻度、ポーラリティ若干上昇 |
| モノトーン | **大幅に低頻度・小サイズ**（フラッシュが相手のナッツ優位を損なう） |

- 出典: [Flop Heuristics: IP C-Betting in Cash Games - GTO Wizard](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)

---

### 知見5: ストレート可能性の計算

#### 連続3枚ボード（例: 9-8-7）でのドロー組み合わせ数

9-8-7 フロップでOESDを持つハンド：

| ハンド | OESDの形 | コンボ数（スーツ補正なし） |
|---|---|---|
| T-6 | 6-7-8-9-T | 16（4×4） |
| J-T | T-J に 9-8-7 | 16（4×4） |
| 6-5 | 5-6-7-8-9 | 16（4×4） |

ガットショット（4アウト）を持つハンド：

| ハンド | ガットショットの形 |
|---|---|
| J-6 | 6-7-8-9-10-J の中の一部 |
| T-5 | 6-7-8-9-10 |

**結論**: 9-8-7 ボードでは、相手が OESD を持つハンドが複数存在し、コンボ数の合計は 40-50+ に達しうる。これが「ウェットボードで CBet 頻度が下がる」理由の一つ。

- OESDは8アウト（フロップからリバーまで 31.5% の完成率）
- ガットショットは4アウト（フロップからリバーまで 18.7%）

- 出典: [What Are The Odds of Hitting a Draw in Poker? - Upswing Poker](https://upswingpoker.com/odds-hitting-draw-in-poker/)

#### 1ギャップボード（例: K-J-x）でのストレートドロー

K-J-9 のような 1 ギャップボードでは：
- Q-T（OESD）: 16 コンボ
- Q-8（ガットショット）: 16 コンボ
- K-Q（ガットショット）: ボードのK残り3枚で減少

プリフロップでの参考値：JT〜54 のスーテッドコネクターがフロップで何らかのストレートドローを持つ確率は **26.2%**（OESD 9.6%, ガットショット 16.6%）。

- 出典: [Straight Draws & Suited Connectors in Poker - PokerRailbird](https://pokerrailbird.com/straight-draws-suited-connectors-in-poker/)

---

### 知見6: フラッシュドロー・フラッシュ完成の影響

#### ツートーンフロップでの相手フラッシュドロー所持確率

- 2枚同スートのボードには、相手が保持しうるフラッシュドローのコンボは理論上 **55コンボ**（残り11枚のうち2枚の組み合わせ：C(11,2)=55）
- 弱いスーテッドハンド（92s, 53s 等）を除くと実質的なフラッシュドローコンボは **約30コンボ**程度
- スーテッドコネクター（76s 等）がフロップでフラッシュドローを持つ確率: **11%**
- スーテッドハンド一般が 2 枚同スートのボードでフラッシュドローを保有する確率: **約10.9%**

- 出典: [Counting Poker Hand Combos - SmartPokerStudy](https://smartpokerstudy.com/counting-poker-hand-combos-hand-reading-lab-part-7-podcast-080/)

#### フラッシュドロー完成確率

| タイミング | 完成確率 |
|---|---|
| ターンのみで完成 | 19.1%（9アウト計算） |
| リバーのみで完成 | 19.6% |
| ターン or リバーで完成 | **35%**（9アウト × 2ストリート） |

- 出典: [What Are The Odds of Hitting a Draw in Poker? - Upswing Poker](https://upswingpoker.com/odds-hitting-draw-in-poker/)

#### モノトーンフロップでの相手フラッシュ保有確率

GTO Wizard の分析（K♥9♥5♥ モノトーンフロップ, BTN vs BB SRP の例）：

| ポジション | フロップ時点でフラッシュを保有する割合 |
|---|---|
| BTN | 約 5% |
| BB | 約 6% |
| UTG（より広いオープンレンジで） | 約 4-6% |

- **ターン**でハートが来る確率: 約 20%（残り9枚のハート / 47枚）
- モノトーンボードではフラッシュが「ナッツ支配力」を大きく変えるため、IP プレイヤーの CBet が大幅に抑制される
- フラッシュ完成よりも「フラッシュドロー」の方がはるかに多く（25-30%の相手がフロップでドローを保有）、これが主要な戦略的考慮事項

- 出典: [Maximizing Value on Monotone Flops - GTO Wizard](https://blog.gtowizard.com/maximizing-value-on-monotone-flops/)

---

### 知見7: ペアボードの特殊性

#### ペアボードがドライ化する理由

1. **ドロー数の激減**: ペアのランクが2枚使われているため、そのランクを使うストレートドローのコンボ数が大幅に減少
2. **トリップスのコンボ数の少なさ**: ランクが2枚公開されているため、相手がトリップスを持てるハンドは残り2枚分（元のポケットペアのみ）に限られる
3. **ナッツ構造の単純化**: ペアボードでは両プレイヤーともにトリップスを持てる（ポケットペアが不要）が、その確率は低い

#### トリップス・フルハウス確率

ペアボードで相手が保有する強ハンドの確率（1対1のシナリオ）：

| 手役 | 確率 |
|---|---|
| 相手がトリップス以上を保有（1人） | **8.4%** |
| 相手がトリップス以上（2人のどちらか） | **16.5%** |
| ポケットペアからフロップでフルハウス | 0.98%（101-to-1） |
| スーテッドじゃないハンドからフロップでフルハウス | 0.09% |

- 出典: [PokerStrategy Forum - Odds of opponent flopping trips](https://www.pokerstrategy.com/forum/thread.php?threadid=185239)

#### ペアボード戦略（GTO の視点）

- **ペアボードは高頻度CBet**: ドローが少ないため、コンティニュエーションベットの頻度はアンペアードボードより高い
- **サイズは小**: トリップスが両レンジに存在するため「ナッツ優位」が限定的 → 大きいベットは不適切
- **GTO Wizard データ**: ペアボードでは 33% ポットのサイズが主力、ただし 130% ポットのオーバーベットも出現
- 888 Poker の分類では「Paired Dry（アグレッシブ小サイズ）」と「Paired Dynamic（やや低頻度で 50% ポットも使用）」の2種類に細分化

- 出典: [Poker Board Textures - 888 Poker](https://www.888poker.com/magazine/poker-board-textures)
- 出典: [Flop Heuristics: IP C-Betting in Cash Games - GTO Wizard](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)

#### セット vs トリップス の非対称性

ペアボードで重要な非対称性：

- **セット（ポケットペア + ボードの1枚）**: この状況ではボードにペアがあるときのみ発生しない通常のセットとは異なる文脈
- **トリップス（ボードのペア + ホールカード1枚）**: 相手がいかなるハンドでも該当ランクを1枚持てばトリップス
- **フルハウス**: トリップス保有者がペアのホールカードを持つか、ボードの別カードとペアを作る場合

ペアボードでは両プレイヤーともに「自然に」トリップスを持てるため、「ナッツ」の比較優位が消えやすい。これが小ベットサイズが選択される根本理由。

---

### 知見8: 代表的なフロップ 50 例（テクスチャ別）

#### ドライボード（高頻度CBet・小サイズ推奨）

| フロップ | 特徴 |
|---|---|
| K♦7♥2♠（K72r） | 典型的ドライ。フラッシュドローなし、ストレートドローなし |
| A♠8♣4♦（A84r） | A-high ドライ。Aの存在がプリフロップ有利者に大きなレンジ優位 |
| Q♣6♦2♥（Q62r） | 中程度のドライ |
| J♦5♠2♣（J52r） | J-high ドライ |
| T♠3♦2♣（T32r） | ロー・ドライ |
| A♠K♣2♦（AK2r） | 2ブロードウェイ + ローカード |
| K♠7♦2♣（K72r 別スート） | 典型的1 big + 2 small |
| A♣9♦3♥（A93r） | A-high、わずかにコネクテッド |
| Q♦7♣3♠（Q73r） | Q-high ドライ |
| 7♣3♦2♥（732r） | 3枚ローカード・ドライ |
| K♠K♦5♣（KK5） | ペアボード・ドライ |
| A♥A♣8♦（AA8） | ペアボード・ドライ |
| T♠T♦4♣（TT4） | ペアボード・ミッド |
| 8♥8♦3♠（883） | ペアボード・ロー |
| J♠J♦2♣（JJ2） | ペアボード・ロー |

#### セミウェット（ツートーンまたは中程度のコネクテッド）

| フロップ | 特徴 |
|---|---|
| K♠T♦5♥（KT5r） | コネクテッド要素あり、レインボー |
| J♣8♦4♠♠（J84r） | ガットショット可能性 |
| K♣8♣3♦（K83ss） | ツートーン・ディスコネクテッド |
| Q♥7♥3♣（Q73ss） | ツートーン・ディスコネクテッド |
| A♦J♦4♣（AJ4ss） | ツートーン + コネクテッド要素 |
| T♠8♦5♣（T85r） | 中程度コネクテッド |
| J♠9♦6♣（J96r） | コネクテッドボード |
| K♠9♦5♣（K95r） | 1ギャップ2箇所 |
| 9♣7♦3♠（973r） | ミッドレンジ・セミコネクテッド |
| A♣K♦Q♠（AKQr） | 3ブロードウェイ・ドライ気味 |
| J♦8♠7♣（J87r） | コネクテッド3枚 |
| T♦8♣5♦（T85ss） | ツートーン・コネクテッド |
| A♥9♥3♣（A93ss） | ツートーン + A-high |
| K♠J♦9♠（KJ9ss） | ツートーン + 2ギャップコネクテッド |
| Q♦T♠9♦（QT9ss） | ツートーン + コネクテッド |

#### ウェット（低頻度CBet・複雑なストラテジー）

| フロップ | 特徴 |
|---|---|
| 9♠8♦7♣（987r） | 典型的コネクテッドウェット。OESD多数 |
| T♠8♠6♦（T86ss） | ツートーン + コネクテッド |
| J♥T♦9♣（JT9r） | 連続3ブロードウェイ |
| 6♠5♠4♦（654ss） | ツートーン + ローコネクテッド |
| 7♥6♣5♦（765r） | ローコネクテッド・ウェット |
| K♠J♠9♦（KJ9ss） | ツートーン + ブロードウェイコネクテッド |
| Q♠J♦T♣（QJTr） | 3ブロードウェイ・超ウェット |
| 8♠7♠6♦（876ss） | ツートーン + コネクテッド |
| T♦9♠8♦（T98ss） | ツートーン + コネクテッド |
| J♠8♠6♦（J86ss） | ツートーン + 2ギャップ |
| A♥K♥Q♣（AKQss） | ツートーン + 3ブロードウェイ |
| 9♦8♦7♣（987ss 別スート） | ツートーン + コネクテッド |
| 5♠4♠3♦（543ss） | ツートーン + ローコネクテッド |

#### モノトーン（特別戦略が必要）

| フロップ | 特徴 |
|---|---|
| A♥T♥4♥（AT4モノトーン） | モノトーン + A-high |
| K♦9♦5♦（K95モノトーン） | モノトーン + K-high |
| 9♣7♣2♣（972モノトーン） | モノトーン + ミッドロー |
| Q♠J♠T♠（QJTモノトーン） | モノトーン + 超ウェット（最も難しい） |
| 7♥6♥5♥（765モノトーン） | モノトーン + コネクテッド |

---

### 知見9: ボードテクスチャの評価次元（BoardScore の要素）

学術的・商業的ツールで確立された「数値スコア」は存在しないが、以下の要素を組み合わせて評価する枠組みが業界標準となっている：

#### 評価次元1: コネクティビティ（Connectivity）

- **ランク差の最小値・最大値**: 3枚のランク差が小さいほどウェット
- **OESD 可能性**: 相手が OESD を持てるハンドの数
- **ガットショット可能性**: 単独ガットショットを持てるハンドの数
- **連番判定**: 差が1の連続（8-9-T）、1ギャップ（8-T-J）、2ギャップ（7-T-J）

#### 評価次元2: スーテッドネス（Suitedness）

- **0同スート（レインボー）**: フラッシュドローなし
- **2同スート（ツートーン）**: フラッシュドロー 55 コンボ（実質 30 コンボ）可能
- **3同スート（モノトーン）**: フラッシュ完成 5-8%、フラッシュドロー 25-30%

#### 評価次元3: ペアリング（Pairing）

- **アンペアード**: 3枚全て異なるランク
- **ペアード（ワンペア）**: トリップスコンボが減少、ドローが減少
- **トリップス**: 極めて稀（0.24%）

#### 評価次元4: ハイカードの存在（High Card Presence）

- **Aハイ**: プリフロップ有利者に最大レンジ優位
- **K/Qハイ**: 中程度のレンジ優位
- **Jハイ以下**: レンジ優位が縮小、BB の連続範囲と競合

#### 合成評価（定性的）

- 出典: [A Quick Way To Think About Flop Texture - Red Chip Poker](https://redchippoker.com/how-to-think-about-flop-texture/)
- 出典: [Poker Board Textures - 888 Poker](https://www.888poker.com/magazine/poker-board-textures)

---

### 知見10: Static vs Dynamic の軸

GTO コミュニティで重要な追加次元：

- **スタティックボード**: エクイティが次のストリートで大きく変動しない（例: K♠K♦5♣ モノトーン、A♠8♣4♦ レインボー）
- **ダイナミックボード**: ターン・リバーでエクイティが大きく変動する（例: J♥T♦9♣、T♦7♦5♣）

ダイナミックボードはドロー牽制のために大きいサイズのベットが有効で、スタティックボードは小サイズ高頻度が有効。

- 出典: [Static and Dynamic Board Textures - Tournament Poker Edge](https://www.tournamentpokeredge.com/static-and-dynamic-board-textures-in-poker/)

---

## 本書への適用

### 第5章: ボードテクスチャを数値化する（BoardScore）での活用

1. **12 カテゴリー分類**（Gareth James）を BoardScore の基盤として提示
   - 学習優先度の提示（頻度上位5カテゴリーから始める）
   - 各カテゴリーの代表的な例を図として示す

2. **4次元評価フレームワーク**を BoardScore の計算式として提案
   - コネクティビティスコア（ストレートドロー可能コンボ数）
   - スーテッドネススコア（0/2/3同スート）
   - ペアリングスコア（アンペアード/ペアード/トリップス）
   - ハイカードスコア（A/K・Q/J・T以下）

3. **代表50フロップ例**を「ドライ・セミウェット・ウェット・モノトーン」でグループ化した参照表を掲載

4. **GTO CBet 頻度との相関**を示す
   - ウェットネス・パラボラ（小→大→小）の概念を図解
   - 特定フロップの数値例（K72r→高頻度、QJTss→低頻度）

5. **第6-8章の橋渡し**として機能
   - 各フロップの BoardScore がプリフロップアグレッサーのアドバンテージをどう変えるか
   - ターン・リバーでのボードテクスチャ変化への応用

---

## 参考文献（出典一覧）

| 出典 | URL | 参照年 |
|---|---|---|
| GTO Wizard: Flop Heuristics IP C-Betting | https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/ | 2024-2026 |
| GTO Wizard: Mechanics of C-Bet Sizing | https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/ | 2024-2026 |
| GTO Wizard: Maximizing Value on Monotone Flops | https://blog.gtowizard.com/maximizing-value-on-monotone-flops/ | 2024-2026 |
| Upswing Poker: 10 Fundamental Tips for Common Flops | https://upswingpoker.com/board-texture-tips/ | 2024-2026 |
| Upswing Poker: GTO C-Bet Quiz Answers | https://upswingpoker.com/gto-c-bet-quiz-answers/ | 2024-2026 |
| Upswing Poker: Odds of Hitting a Draw | https://upswingpoker.com/odds-hitting-draw-in-poker/ | 2024-2026 |
| Upswing Poker: Monotone Flops Strategy | https://upswingpoker.com/monotone-flops-poker-strategy/ | 2024-2026 |
| PokerListings: Gareth James 12 Flop Types | https://www.pokerlistings.com/poker-strategies/poker-math-by-gareth-james-types-of-flop-texture | 2024-2026 |
| MTP Poker School: Top 5 Flop Textures | https://www.mttpokerschool.com/single-post/otb-048-the-top-5-flop-textures-to-optimise-your-poker-study | 2024-2026 |
| 888 Poker: Board Textures | https://www.888poker.com/magazine/poker-board-textures | 2024-2026 |
| SplitSuit Poker: Flop Texture Tool | https://www.splitsuit.com/poker-flop-types | 2024-2026 |
| SplitSuit Poker: Paired Boards | https://www.splitsuit.com/poker-paired-boards-textures | 2024-2026 |
| Tournament Poker Edge: Static and Dynamic | https://www.tournamentpokeredge.com/static-and-dynamic-board-textures-in-poker/ | 2024-2026 |
| Red Chip Poker: How to Think About Flop Texture | https://redchippoker.com/how-to-think-about-flop-texture/ | 2024-2026 |
| PokerStrategy Forum: Trips Probability | https://www.pokerstrategy.com/forum/thread.php?threadid=185239 | 2024-2026 |
| PokerRailbird: Straight Draws & Suited Connectors | https://pokerrailbird.com/straight-draws-suited-connectors-in-poker/ | 2024-2026 |
