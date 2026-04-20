# フロップ編 第3章：プリフロップから受け継ぐレンジ

検索日: 2026-04-20

---

## 概要

フロップ戦略の根幹は「どのレンジを持ってフロップを迎えるか」にある。プリフロップのアクション（RFI、コール、3ベット、4ベット）によってレンジの形（幅・強さ・キャップの有無）が決まり、それがフロップ以降の打ち方を完全に規定する。本章では各シナリオのレンジ構成を定量的に示す。

---

## 1. ポジション別オープンレンジ（RFI）— 6-max、100BB

GTO ソルバー（GTO Wizard / FreeBetRange）の 6-max NL キャッシュ 100BB 標準解。レイズサイズは UTG〜CO が 2〜2.3bb、BTN が 2.5bb、SB が 3bb。

### UTG（17〜18%）

```
ペア:     TT+（66+ は要確認、GTO Wizard では TT+ をコア、66-99 は混合頻度あり）
スーテッド: ATs+, A5s, KTs+, QTs+, JTs, T9s, 98s
オフスート: AJo+, KQo
```

- 後ろに 5 人残るため最もタイト。A3s〜A9s の一部は混合頻度。
- 出典: [Preflop Range Morphology | GTO Wizard](https://blog.gtowizard.com/preflop-range-morphology/) （2024年1月10日）
- 出典: [6 max Preflop Charts | FreeBetRange](https://blog.freebetrange.com/article/preflop-charts-open-raise-in-6-max-poker-cash-games)

### MP / HJ（21〜22%）

```
ペア:     55+
スーテッド: A2s+, K6s+, Q9s+, J9s+, T9s, 98s, 87s, 76s
オフスート: ATo+, KTo+, QTo+
```

### CO（27〜28%）

```
ペア:     33+
スーテッド: A2s+, K3s+, Q6s+, J8s+, T7s+, 97s+, 87s, 76s
オフスート: A8o+, KTo+, QTo+, JTo
```

### BTN（43〜45%）

```
ペア:     33+（22 は混合頻度）
スーテッド: A2s+, K2s+, Q3s+, J4s+, T6s+, 96s+, 85s+, 75s+, 64s+, 53s+
オフスート: A4o+, K8o+, Q9o+, J9o+, T8o+, 98o
```

- 最も広い IP ポジション。スーテッドコネクター群を広くカバー。

### SB（39〜47%）

```
ペア:     22+
スーテッド: A2s+, K2s+, Q2s+, J2s+, T3s+, 94s+, 84s+, 74s+, 63s+, 53s+, 43s
オフスート: A2o+, K4o+, Q5o+, J7o+, T7o+, 96o+, 86o+, 76o
```

- BTN 同等かやや広い（ただし常に OOP）。GTO ソルバーは SB の「リンプ」を排除し 3ベット or フォールドを推奨するケースが多い（低レーキ環境では混合コールあり）。
- 出典: [6-Max Pre-Flop Open Raising Ranges | MicroGrinder](https://microgrinder.com/poker-strategy-articles/6-max-pre-flop-ranges/)

### ポジション別 RFI サマリー

| ポジション | RFI% | レンジの性格 |
|-----------|------|------------|
| UTG | 17〜18% | リニア、最強ハンドのみ |
| MP/HJ | 21〜22% | リニア、Broadway + 中ペア |
| CO | 27〜28% | リニア、スーテッド帯を拡張 |
| BTN | 43〜45% | ほぼ全スーテッド + 広いオフスート |
| SB | 39〜47% | BTN 同等、OOP のためレーキ依存で変動 |

---

## 2. BB ディフェンスレンジ

BB は唯一「コール」という選択肢が GTO 上も有力なポジション。プリフロップで既に 1BB 投資済みであること、最後に行動できることが理由。

### 対 UTG オープン（17〜20% ディフェンス）

- **コール主体**（約 12〜15%）: ポケットペア 22〜99、スーテッドAx（A2s〜A9s）、スーテッドコネクター（76s〜JTs）、KQs/KJs/QJs、一部ブロードウェイオフスート
- **3ベット**（約 5〜7%）: QQ+, AKs, AKo（バリュー）+ A5s, A4s, A3s（ブラフ）
- **フォールド**（約 80%）: 弱いオフスートと中途半端なハンド（A7o, K8o 等）

UTG のタイトなレンジに対し、BB も極端に守備範囲を絞る。2.5bb レイズに対し BB のポットオッズは 3.5:1.5 ≈ 2.3:1 となるため、約 30〜35% の手でコールが数学的に許される。

- 出典: [The Ultimate Guide to 6-Handed Poker | Upswing Poker](https://upswingpoker.com/6-handed-max-poker-strategy/)
- 出典: [BBZ Fundamentals: Big Blind Defense vs UTG](https://bbzpoker.com/product/bb-defense/)

### 対 BTN オープン（38〜40% ディフェンス）

- **コール主体**（約 25〜30%）: 22〜JJ の大部分、スーテッドAx 全域、スーテッドコネクター（43s〜T9s）、Broadway スーテッド、弱めのオフスート Broadway
- **3ベット**（約 10〜14%）: QQ+, AKs, AKo（バリュー）+ A5s〜A2s, KJs, QJs, スーテッドコネクター上位（ブラフ）
- BTN の広いレンジに対し、BB は大幅に守備範囲を拡張する

- 出典: [Round Out Your Defense | GTO Wizard](https://blog.gtowizard.com/round_out_your_defense_the_power_of_raising/)
- 出典: [Responding to BB Squeezes | GTO Wizard](https://blog.gtowizard.com/responding-to-bb-squeezes/)

---

## 3. SB・BTN コールドコールレンジ

### SB コールドコール（対各ポジションオープン、約 7%）

GTO ソルバーでは SB のコールドコールは極めて限定的。主な理由は：
1. OOP でのポストフロップが不利
2. BB のスクイーズリスクがある
3. 3ベットの方がより高い EV を持つケースが多い

SB がコールドコールを行う場合の代表的な構成：
```
ポケットペア: 22〜99（JJ+は3ベット）
スーテッドAx: A2s〜A9s（A5s, A4s 等は3ベットブラフの方が好まれる場合も）
スーテッドコネクター: 87s, 76s, 65s（ナッツポテンシャルが高い）
スーテッドBroadway: KJs, QJs, KTs（ブロッカー価値 + プレイアビリティ）
```

実際には GTO 主流ソリューションは SB のコールドコールを「3ベット or フォールド」に近い形で扱うケースが多い（フルリング・低レーキ環境では例外あり）。

- 出典: [Cold Calling Ranges - Run It Once](https://www.runitonce.com/nlhe/cold-calling-ranges/)
- 出典: [Preflop Range Morphology | GTO Wizard](https://blog.gtowizard.com/preflop-range-morphology/)

### BTN コールドコール（対 CO オープン）

BTN は CO オープンに対して 3ベット（約 12%）とコール（約 5%）を組み合わせる混合戦略を採用。

- **コール代表ハンド**: 99〜JJ の一部（3ベットと混合）、AQo, AJs（コールと3ベットの混合）、KQs, スーテッドコネクター（87s, 98s, T9s）
- **戦略的意義**: CO は BTN の後ろでオープンしているため、BTN は常に IP で戦える。BTN のコールレンジはポジション優位を活かしたプレイアビリティ重視で構成される

> 注記：「3ベットか、コールか」の判断は BTN ではほぼ全ハンドで混合戦略となり、「純粋コール」ハンドは少ない（AKo, QQ も一定頻度でコール）。

- 出典: [Playing Calls From the Button in Cash Games | GTO Wizard](https://blog.gtowizard.com/playing-calls-from-the-button-in-cash-games/)

---

## 4. 3ベットポットのレンジ構成

### 3ベッター（アグレッサー）のレンジ

#### ポーラライズド 3ベット（IP から、または相手がフォールド率高い場合）

```
バリュー: QQ+, AKs, AKo（相手に対してレンジ上位）
ブラフ:   A5s, A4s, A3s（ブロッカー効果 + ナッツフラッシュポテンシャル）
         スーテッドコネクター: 76s, 65s, 87s の一部
         KJs の一部（高ブロッカー価値）
```

ポーラライズドレンジでは「中間強度のハンド（TT, JJ, AQ 等）はフラットコール」に回す。

#### リニア 3ベット（OOP から、または相手がコールしやすい場合）

```
バリュー層: AA, KK, QQ, JJ, TT, AKs, AKo, AQs
（相手がフォールドしない場合は強いハンドだけで構成する）
```

- 出典: [3-Betting 101: Linear vs Polarized | MicroGrinder](https://microgrinder.com/poker-strategy-articles/3-betting-101/)
- 出典: [3-Bet Preflop Strategy | Upswing Poker](https://upswingpoker.com/3-bet-strategy-aggressive-preflop/)
- 出典: [Understanding 3-Bet Ranges | SplitSuit Poker](https://www.splitsuit.com/understanding-3-bet-ranges)

### オープンレイザーのコールレンジ（キャップされたレンジ）

3ベットに対してオープンレイザーがコールすると、そのレンジは「キャップ（capped）」された状態になる：

```
コールレンジ例（UTG オープン、BBから3ベットに対して）:
  ペア:     TT〜QQ の一部（QQ は3ベット/コール混合）
  スーテッド: AJs, ATs, KQs, QJs
  セット目的: 77〜99（ポットオッズ次第）
```

**QQ+, AK を含まない理由**: これらはほぼ全頻度で 4ベットされるべきハンドであり、コールに回すと EV を大きく損失する。プリフロップで最大のポット構築機会を逃すことになる。

> ポイント：オープンレイザーのコールレンジは「ナッツが存在しない（=キャップされた）」状態でフロップを迎える。

- 出典: [How to Play vs Preflop 3-Bets | Upswing Poker](https://upswingpoker.com/vs-3-bet-pre-flop-position-strategy-revealed/)
- 出典: [Crush 3-Bet Pots OOP in Cash Games | GTO Wizard](https://blog.gtowizard.com/crush-3-bet-pots-oop-in-cash-games/)

---

## 5. 4ベットポットのレンジ

### 4ベット側のレンジ

```
バリュー: AA, KK, QQ（一部混合）, AKs, AKo
ブラフ:   A5s, A4s（ブロッカー AK/AA を持つスーテッドAx）
         KJs（スーテッドK でナッツブロッカー価値）
```

4ベット率は通常 3〜6%。バリューのみで構成すると非常にエクスプロイタブルになるためブラフコンボが必要。

### 4ベットに対するコールレンジ（5ベットフォールド）

```
5ベット（オールイン）: KK, AA（ほぼ 100%）、AKs（高頻度）
コール:               QQ（スタック・ポット比による）、JJ の一部
```

コールする場合（例: QQ が 4ベットコール）のレンジは極めてタイト。「AK よりもボードを選ぶ」ペアハンドはポストフロップで 100BB 以下のスタックを有効に戦える。

### 5ベット側のレンジ

```
KK+（ほぼ純粋バリュー）
AKs の一部（スタック比次第）
```

- 出典: [4-Bet Pots OOP as the Preflop Caller | GTO Wizard](https://blog.gtowizard.com/4-bet-pots-oop-as-the-preflop-caller/)
- 出典: [What Top Poker Pros Know About 4-Betting | Upswing Poker](https://upswingpoker.com/4-bet-size-strategy/)
- 出典: [Poker: 4-bet pots | Mike Fowlds / Medium](https://mikefowlds.medium.com/poker-4-bet-pots-aff8f9149d39)

---

## 6. 各レンジの平均 HandScore（フロップでの「当たり」度）

GTO Wizard が公開している「エクイティ分布（Equity Distribution）」分析に基づく定性評価。

| シナリオ | レンジ特性 | フロップでのエクイティ目安 |
|---------|-----------|----------------------|
| UTG オープン vs BB | UTG: 17% リニア、BB: ディフェンスレンジ | UTG が平均エクイティ 54〜56%（要確認） |
| BTN オープン vs BB | BTN: 43% 広いレンジ、BB: 38% ディフェンス | ほぼ 50/50 に近い |
| 3ベットポット（3ベッター IP） | 3ベッター: ポーラライズ、コーラー: キャップ | 3ベッター側が平均エクイティ有利 |
| 4ベットポット | 両者ともタイト（QQ+/AK 中心） | フロップでの差は主にナッツハンド密度に依存 |

**フロップヒット率の概念**:
- ポケットペア（例: 88）: フロップでセット完成約 11.8%（約 8.5 回に 1 回）
- スーテッドAx（例: ATs）: ペア+ナッツフラッシュドロー+バックドア など複合的なエクイティを保有
- オフスートブロードウェイ（例: KQo）: 対 UTG レンジでの平均エクイティが低く、フロップで「空気」になりやすい

GTO Wizard の実際のエクイティバケット数値は有料ソルバーアクセスが必要なため、上記は定性的な参考値。

- 出典: [Interpreting Equity Distributions | GTO Wizard](https://blog.gtowizard.com/interpreting-equity-distributions/)
- 出典: [The Magic of Equity Buckets | GTO Wizard](https://blog.gtowizard.com/the-magic-of-equity-buckets/)

---

## 7. レンジキャップの概念

### 定義

「キャップされたレンジ（Capped Range）」とは、**ナットハンド（最強クラスの手）が存在しないレンジ**のこと。

### 発生メカニズム

| シナリオ | キャップされる側 | 含まれないハンド |
|---------|--------------|--------------|
| 3ベットポット（コール側） | オープンレイザー | QQ+, AKs, AKo |
| シングルレイズポット（IP コーラー） | BTN コーラー | AA, KK（3ベットすべき） |
| 4ベットポット（コール側） | 3ベッター | AA, KK（5ベットすべき） |

### ポストフロップへの影響

**1. ベット・オーバーベットの機会**
キャップされていない側（アンキャップドレンジ）は、相手がナットハンドを持てないことを知っているため、オーバーベット（125〜200% ポット）を使って最大プレッシャーをかけられる。

**2. レンジチェックの強制**
キャップされた側はナットハンドの「ふり」ができないため、大きいベットに対してコールし続けることが困難になる。

**3. ナッツアドバンテージとレンジアドバンテージの区別**
- **レンジアドバンテージ**: 平均エクイティが高い
- **ナッツアドバンテージ**: ナットハンドの密度が高い（キャップがない）

> 例: 3ベットポット（3ベッター BB、コーラー CO）で 8♥5♦4♠ フロップが来た場合、
> 3ベッター（BB）はレンジ平均では優位かもしれないが、88/55/44 のセットと 76s のストレートは CO 側に多く存在する。
> この「ナッツアドバンテージ」の逆転が、3ベッターを受動的（チェック多め）にさせる。

**4. フロップ Cベット戦略の変化**
- アンキャップドレンジ側（3ベッター IP）: レンジ全体でスモールベット可能
- キャップされたレンジ側（OOP コーラー）: 強いハンドと弱いハンドが混在、大きいベットへの抵抗力が低い

- 出典: [Navigating Range Disadvantage as the 3-Bettor | GTO Wizard](https://blog.gtowizard.com/navigating-range-disadvantage-as-the-3-bettor/)
- 出典: [Poker Ranges & Range Reading | SplitSuit Poker](https://www.splitsuit.com/poker-ranges-reading)
- 出典: [Range Morphology | GTO Wizard](https://blog.gtowizard.com/range-morphology/)

---

## 本書への適用

### 第3章（フロップ編）での活用方針

1. **レンジ紹介の順序**: RFI → BB ディフェンス → 3ベット/4ベットポットの順に提示し、「各シナリオでどのレンジを持ってフロップを迎えるか」を図解

2. **キャップの概念の視覚化**: シングルレイズポット・3ベットポット・4ベットポットの 3 つで「レンジの形（アンキャップド vs キャップド）」を図で比較

3. **実戦例への接続**: 具体的なハンド（例: KQo で UTG コール範囲に入らない理由）をチャートと照合させる

4. **読者への実践提案**: GTO Wizard や FreeBetRange でポジション別レンジを自分で確認するよう誘導

### 想定する読者の誤解

- 「BB はなんでも守れる」→ 実際は対 UTG で約 80% をフォールドする
- 「AA/KK はフロップで強い」→ 3ベットポットではコール側のレンジに AA/KK はほぼ存在しない
- 「3ベットされたら全部フォールドでいい」→ キャップされた状態でも正しいコールレンジがある

---

## 参考文献一覧

| タイトル | URL | 発行年 |
|---------|-----|-------|
| Preflop Range Morphology | GTO Wizard | https://blog.gtowizard.com/preflop-range-morphology/ | 2024 |
| Range Morphology | GTO Wizard | https://blog.gtowizard.com/range-morphology/ | 2024 |
| 6 max Preflop Charts | FreeBetRange | https://blog.freebetrange.com/article/preflop-charts-open-raise-in-6-max-poker-cash-games | 2023 |
| 6-Max Pre-Flop Open Raising Ranges | MicroGrinder | https://microgrinder.com/poker-strategy-articles/6-max-pre-flop-ranges/ | 2022 |
| Playing Calls From the Button | GTO Wizard | https://blog.gtowizard.com/playing-calls-from-the-button-in-cash-games/ | 2024 |
| Crush 3-Bet Pots OOP | GTO Wizard | https://blog.gtowizard.com/crush-3-bet-pots-oop-in-cash-games/ | 2024 |
| Navigating Range Disadvantage as the 3-Bettor | GTO Wizard | https://blog.gtowizard.com/navigating-range-disadvantage-as-the-3-bettor/ | 2024 |
| 4-Bet Pots OOP as the Preflop Caller | GTO Wizard | https://blog.gtowizard.com/4-bet-pots-oop-as-the-preflop-caller/ | 2024 |
| 3-Betting 101: Linear vs Polarized | MicroGrinder | https://microgrinder.com/poker-strategy-articles/3-betting-101/ | 2022 |
| 3-Bet Preflop Strategy | Upswing Poker | https://upswingpoker.com/3-bet-strategy-aggressive-preflop/ | 2023 |
| Understanding 3-Bet Ranges | SplitSuit Poker | https://www.splitsuit.com/understanding-3-bet-ranges | 2026 |
| How to Play vs Preflop 3-Bets | Upswing Poker | https://upswingpoker.com/vs-3-bet-pre-flop-position-strategy-revealed/ | 2023 |
| Poker Ranges & Range Reading | SplitSuit Poker | https://www.splitsuit.com/poker-ranges-reading | 2026 |
| Interpreting Equity Distributions | GTO Wizard | https://blog.gtowizard.com/interpreting-equity-distributions/ | 2024 |
| The Magic of Equity Buckets | GTO Wizard | https://blog.gtowizard.com/the-magic-of-equity-buckets/ | 2024 |
| The Ultimate Guide to 6-Handed Poker | Upswing Poker | https://upswingpoker.com/6-handed-max-poker-strategy/ | 2023 |
| BBZ Fundamentals: BB Defense vs UTG | BBZ Poker | https://bbzpoker.com/product/bb-defense/ | 2023 |
| 4-Bet Pots: Composition | Mike Fowlds / Medium | https://mikefowlds.medium.com/poker-4-bet-pots-aff8f9149d39 | 2023 |
