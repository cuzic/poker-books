# CBet サイズの選択（33% / 75% / 150%）

検索日: 2026-04-20

## 概要

フロップ CBet のサイズ選択は、ナッツアドバンテージ・フォールドエクイティ・ボードテクスチャの3要素で決まる。現代 GTO では主に 33%（レンジベット）、66–75%（ポラライズ）、150%+（オーバーベット）の3サイズを使い分ける。「ベット回数が多いほどサイズを小さく」という原則が根底にある。

---

## 主要な知見

### 知見1：サイズ選択の根本原理

GTO Wizard の分析によると、CBet サイズを決める主要ドライバーは2つ：

1. **ナッツアドバンテージ**（主にサイズを決める）
   - 自分がナッツを多く持つ → 大きくベット
   - 相手がナッツを多く持つ → 小さくベット、またはチェック
2. **レンジアドバンテージ**（主に頻度を決める）
   - レンジ優位が大きいほどベット頻度が上がる

> "Nut advantage, however, along with fold equity, are the primary (but not the only) drivers of bet sizing."

- 出典: [The Mechanics of C-Bet Sizing | GTO Wizard](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/)（2023年）

---

### 知見2：33%（レンジベット・ドライボード）

**特性：**
- ドライ・非コネクテッドボードで全レンジを高頻度でベットする戦略
- ベット頻度 70–100%、サイズは 25–33% ポット
- 相手に不利なポットオッズを押しつけつつ、安価なブラフが可能

**適切な場面：**
- ドライハイカードボード（K72r、A83r）
- ペアードボード（AAx、KKx、99x）
- IP（インポジション）でのフラット・コール後

**GTO Wizard の原則：**
> "small bets go a long way—maximize fold equity without risking much"
> "The 33% c-bet-size is most effective on low and unconnected or low paired boards"

- 出典: [Flop Heuristics: IP C-Betting in Cash Games | GTO Wizard](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)
- 出典: [Picking the Proper C-Bet Sizing on Ace-High Boards | PokerCoaching](https://pokercoaching.com/blog/picking-the-proper-c-bet-sizing-on-ace-high-boards/)

---

### 知見3：66–75%（ウェットボード・ポラライズ）

**特性：**
- 強いドローが多いウェット・コネクテッドボードで、ドローのエクイティを否定する
- ベット頻度は下がるが（33–50%程度）、ベットする際のサイズは大きい
- レンジがポラライズ（強い手 + ブラフ、中間の手は少ない）

**適切な場面：**
- コネクテッドボード（T98、J97、876）
- ウェットツートーン（K♥J♥7♦）
- セミウェットボード

**データ：**
> "For wet, coordinated flops like T98, J97, the strategy gravitates heavily towards big sizing of around 71% of the pot"

**IP での具体例（A♠T♥9♥）：**
- サイズ：2/3 ポット
- 頻度：約 37%

- 出典: [Sizing Your C-Bets: 3 Factors You Must Consider | Upswing Poker](https://upswingpoker.com/c-bet-sizing-strategy-continuation-bet/)
- 出典: [Picking the Proper C-Bet Sizing on Ace-High Boards | PokerCoaching](https://pokercoaching.com/blog/picking-the-proper-c-bet-sizing-on-ace-high-boards/)

---

### 知見4：150%+ オーバーベット

**使いどころ：**
- 将来のストリートでハンドバリューが大きく低下する状況
- ナッツアドバンテージが圧倒的な時（相手のレンジにはほとんどナッツがない）
- BTN vs BB でハイボード（A/K/Q のカード）：AK、AQ、KK などが BTN にほぼ集中

**機能的な原理：**
> "Overbets become optimal when hand values deteriorate significantly on future streets. Rather than spreading value geometrically across remaining betting rounds, strong hands frontload their equity through larger-than-geometric bets."

**具体的な場面：**
- AK6r（BTN vs BB）：BBのレンジには弱いペア系が少ないため、オーバーベットがEVを最大化
- フォールド率：オーバーベット時は約 62% がフォールド

**注意：**
- AA や AKs はオーバーベットしない（将来のストリートでもバリューが保たれるため）
- オーバーベットするのは「価値が今のストリートに集中している」脆弱な強ハンド（88、JJ、TT等）

- 出典: [Why So Much? An Exploration of Larger-Than-Geometric Bet Sizing | GTO Wizard](https://blog.gtowizard.com/why-so-much-an-exploration-of-larger-than-geometric-bet-sizing/)

---

### 知見5：サイズと頻度のトレードオフ

**「ウェットネス放物線」の原則（GTO Wizard）：**
```
ドライボード    → 小さいベット（33%）
適度にウェット  → 大きいベット（66–75%）
非常にウェット  → 再び小さいベット（両レンジにナッツが存在、フォールドエクイティ低下）
```

**レンジタイプ別の対応：**

| レンジの性質 | 推奨サイズ | 推奨頻度 |
|------------|----------|--------|
| コンデンス（中間ハンド多） | 25–40% | 高頻度 |
| ポラライズ（ナッツ＋ブラフ） | 66–75% | 低頻度 |
| 中間的 | 50–60% | 中頻度 |

> "The bigger you bet, the more you concentrate your opponent's range around their strongest hands."

- 出典: [Sizing Your C-Bets: 3 Factors You Must Consider | Upswing Poker](https://upswingpoker.com/c-bet-sizing-strategy-continuation-bet/)
- 出典: [Overchoice: Making Sense of Multiple Sizings | GTO Wizard](https://blog.gtowizard.com/overchoice-making-sense-of-multiple-sizings/)

---

### 知見6：ボード別推奨サイズまとめ

#### 乾燥ハイカードボード（K72r、A83r）

- **IP CBet サイズ：1/3 ポット（33%）**
- **頻度：高（65–80%）**
- 理由：レンジアドバンテージは大きいが、ナッツアドバンテージは限定的（相手もKペア、Aペアを持てる）
- 出典: [Picking the Proper C-Bet Sizing on Ace-High Boards | PokerCoaching](https://pokercoaching.com/blog/picking-the-proper-c-bet-sizing-on-ace-high-boards/)

#### コネクテッドボード（T98、J97）

- **IP CBet サイズ：66–75%**
- **頻度：低（33%前後）**
- 理由：相手レンジにドローが多く、エクイティ否定のためのサイズが必要
- 出典: [Flop Heuristics: IP C-Betting in Cash Games | GTO Wizard](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)

#### モノトーン（ハート3枚）

- **CBet サイズ：小さいサイズ（25–33%）**
- **頻度：大幅に低下**
- 理由：フラッシュが両レンジに存在、ポットを膨らませるリスクが高い。フラッシュを持つとコールレンジをブロックしてしまう
- > "Monotone boards see a drastic decrease in betting frequency and sizing"
- 出典: [Maximizing Value on Monotone Flops | GTO Wizard](https://blog.gtowizard.com/maximizing-value-on-monotone-flops/)

#### ペアードボード（99x、K7K）

- **CBet サイズ：小さいサイズ（33%前後）**
- **頻度：高（AAx ≈ 100%、KKx ≈ 85%、TTx ≈ 70%）**
- 理由：ペアードボードでは両レンジにトリップスが存在→ナッツアドバンテージ限定的→小さいサイズで高頻度が最適
- 出典: [C-Betting On Paired Boards | PokerCoaching](https://pokercoaching.com/blog/c-betting-on-paired-boards/)

---

### 知見7：33% vs ハーフポット の論争

現代の GTO 分析では **33% が主流**。理由：

1. **レンジベット（全レンジで高頻度ベット）**のコストを下げる
2. ハーフポット（50%）は GTO 均衡において「中途半端なサイズ」になりがち
3. 3ベットポットでも 33% CBet が一般的（コスト削減）
4. ソルバーはドライボードで 33% を圧倒的に多用する

ただし **例外**：
- 相手のバリューレンジが 75% エクイティ以上に強い場合は 75% も選択肢
- OOP（アウトオブポジション）ではドライボードでも 66% を混ぜる場合がある

- 出典: [C-Betting IP in 3-Bet Pots | GTO Wizard](https://blog.gtowizard.com/c-betting-ip-in-3-bet-pots/)
- 出典: [What Flop C-Bet Size Should You Use in Cash Games? | Upswing Poker](https://upswingpoker.com/c-bet-sizing-flop-guide/)

---

### 知見8：サイズと期待値の関係

**ブレークイーブンフォールド率の計算式：**

```
ブレークイーブンフォールド率 = B ÷ (P + B)
```

- B：ベット額、P：ベット前のポット

**代表的なサイズ別ブレークイーブンフォールド率：**

| サイズ | ブレークイーブン | 相手の必要ディフェンス率 |
|--------|----------------|----------------------|
| 33% ポット | 25% | 75% |
| 50% ポット | 33% | 67% |
| 75% ポット | 43% | 57% |
| 100% ポット | 50% | 50% |
| 150% ポット | 60% | 40% |

**完全な EV 計算式（エクイティあり）：**

```
EV = (F × P) + (1 − F) × (E × (P + B) − (1 − E) × B)
```

- F = フォールド確率、E = コールされた時の勝率

**実践的含意：**
- 小さいベット → ブレークイーブンフォールド率が低い → ブラフが安価になる
- 大きいベット → より多くフォールドさせる必要がある → ナッツアドバンテージが必要

- 出典: [PokerVIP - EV Calculations: Fold Equity](https://www.pokervip.com/strategy-articles/expected-value-ev-calculations/ev-calculations-part-2-fold-equity)
- 出典: [The Value of Fold Equity - Experiment | GTO Wizard](https://blog.gtowizard.com/the-value-of-fold-equity-experiment/)

---

### 知見9：Jonathan Little のサイズ選択原則

Jonathan Little は「ハーフポットの思考停止ベット」を批判し、状況に応じたサイズ調整を推奨：

- 強いハンドで優位なボードには **より大きなサイズ**（700 など）でバリューを最大化
- レンジ全体でベットするならサイズは小さく
- マルチウェイポットではバリューベット中心、ドローも含めて

関連する一般原則（複数のソースから確認）：
> 「3ベットポットや大きなポットでは全体のベットサイズを下げる。ポットが大きくなるほど大きなベットで全チップをコミットする必要がなくなる」

要確認: Jonathan Little の「ベットする回数が多いほどサイズを小さく」という具体的な言葉はウェブ上では直接引用文が確認できなかった。ただし概念としては多数のソースが同様の内容を支持。

- 出典: [Jonathan Little's Weekly Poker Hand: Stop Mindlessly Betting Half-Pot! | PokerNews](https://www.pokernews.com/strategy/jonathan-little-s-weekly-poker-hand-stop-mindlessly-betting-36145.htm)

---

## ボード別クイックリファレンス表

| ボードタイプ | 代表例 | IP サイズ | IP 頻度 | 理由 |
|------------|--------|----------|---------|------|
| ドライハイカード | K72r、A83r | 33% | 高（65–80%） | レンジアドバンテージ大、ナッツアドバンテージ限定 |
| コネクテッド | T98、J97、876 | 66–75% | 低（30–40%） | ドロー否定、エクイティ保護 |
| モノトーン | K♥9♥5♥ | 25–33% | 大幅低下 | 両レンジにフラッシュ、ポット肥大リスク |
| ペアード | 99x、K7K、AAx | 33% | 高（70–100%） | 両レンジにトリップス、ナッツ差小 |
| ウェットツートーン | K♥J♥7♦ | 66–75% | 中（40–50%） | ドロー否定、ポラライズ |
| ロウカード乾燥 | 842r、532r | 66% | 中（50–65%） | レンジアドバンテージあり、ドロー少 |

---

## 本書への適用

- **第10章（CBet サイズの選択）** のメインコンテンツとして活用
  - 3サイズの概念説明（33% / 75% / 150%）
  - ボード別クイックリファレンス表を図解として掲載
  - ブレークイーブンフォールド率の計算式を「数式コーナー」として提示
- **「ウェットネス放物線」の概念**：ドライ→小、中程度ウェット→大、非常にウェット→小、の直感的な説明に使用
- **ナッツアドバンテージの図解**：各ボードタイプで誰がナッツを持ちやすいかを可視化
- **EV計算の実例**：33% vs 75% で同じブラフの採算性がどう変わるかを具体的に示す

---

## 出典一覧

- [The Mechanics of C-Bet Sizing | GTO Wizard](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/)
- [Flop Heuristics: IP C-Betting in Cash Games | GTO Wizard](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)
- [Why So Much? An Exploration of Larger-Than-Geometric Bet Sizing | GTO Wizard](https://blog.gtowizard.com/why-so-much-an-exploration-of-larger-than-geometric-bet-sizing/)
- [Overchoice: Making Sense of Multiple Sizings | GTO Wizard](https://blog.gtowizard.com/overchoice-making-sense-of-multiple-sizings/)
- [Maximizing Value on Monotone Flops | GTO Wizard](https://blog.gtowizard.com/maximizing-value-on-monotone-flops/)
- [The Value of Fold Equity - Experiment | GTO Wizard](https://blog.gtowizard.com/the-value-of-fold-equity-experiment/)
- [C-Betting IP in 3-Bet Pots | GTO Wizard](https://blog.gtowizard.com/c-betting-ip-in-3-bet-pots/)
- [C-Betting As the OOP Preflop Raiser | GTO Wizard](https://blog.gtowizard.com/c-betting-as-the-oop-preflop-raiser/)
- [What Flop C-Bet Size Should You Use in Cash Games? | Upswing Poker](https://upswingpoker.com/c-bet-sizing-flop-guide/)
- [Sizing Your C-Bets: 3 Factors You Must Consider | Upswing Poker](https://upswingpoker.com/c-bet-sizing-strategy-continuation-bet/)
- [Picking the Proper C-Bet Sizing on Ace-High Boards | PokerCoaching](https://pokercoaching.com/blog/picking-the-proper-c-bet-sizing-on-ace-high-boards/)
- [Picking a Proper C-Bet Sizing on Low-Card Boards | PokerCoaching](https://pokercoaching.com/blog/picking-a-proper-c-bet-sizing-on-low-card-boards/)
- [C-Betting On Paired Boards | PokerCoaching](https://pokercoaching.com/blog/c-betting-on-paired-boards/)
- [Jonathan Little's Weekly Poker Hand: Stop Mindlessly Betting Half-Pot! | PokerNews](https://www.pokernews.com/strategy/jonathan-little-s-weekly-poker-hand-stop-mindlessly-betting-36145.htm)
- [PokerVIP - EV Calculations: Fold Equity](https://www.pokervip.com/strategy-articles/expected-value-ev-calculations/ev-calculations-part-2-fold-equity)
