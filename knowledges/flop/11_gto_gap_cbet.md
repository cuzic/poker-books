# GTO と本書 CBet 式の乖離パターン

検索日: 2026-04-20

## 概要

本書の CBet 統合式（HandScore + BoardScore + ポジション）は決定論的なルールベースである。
GTO ソルバーが出力する戦略とは、複数の側面で構造的に異なる。
本章では「どこがどう外れるか」と「それでも初級者に十分な理由」を明確にする。

---

## 主要な知見

### 知見1：混合戦略（ミックス戦略）と決定論の違い

GTO はしばしば「同一ハンドをベット60%・チェック40%でミックスする」。
これは**2つのアクションの EV が等しい（無差別条件）**ときに発生する。
混合戦略の目的は、相手に「チェックを見てハンド読みする」機会を与えないことである。

- GTO での混合は EV 均等点で生じる。どちらを選んでも EV 損失はゼロに近い
- 「純粋戦略（必ずベット or 必ずチェック）」への逸脱が大きな損失を生むのは、
  相手が完璧な GTO を実装している場合のみ
- 現実の低〜中レベルのゲームでは相手も GTO を実装しておらず、
  「混合をサボる」ことのペナルティは理論値より大幅に小さい
- Run It Once の研究によれば、toy game における**対称的な逸脱**（あるハンドを
  予定より多くベットし別のハンドを同量少なくベット）は EV 損失なし。
  ただし複数ストリートにわたる実際のゲームでは累積 EV 損失が生じる
- 出典: [Theory: Symmetrical Deviations from Mixed Betting Frequencies](https://www.runitonce.com/nlhe/theory-do-symmetrical-deviations-from-mixed-betting-frequencies-lose-ev-in-gto/)、Run It Once

**本書との乖離まとめ**：本書式は「HandScore ≥ 閾値ならベット」という純粋戦略。
GTO との EV ギャップは存在するが、混合のエラーコスト（実装ミス）より小さい。

---

### 知見2：Range CBet と本書式の違い

GTO では特定の条件下で「レンジ全体を 33% 小サイズでベット」する戦略が最適となる。
これを **Range CBet（レンジベット）** と呼ぶ。

**Range CBet が成立する条件**（Upswing Poker, GTO Wizard）:
- ドライなキング・ハイボード（IP から）
- ダブルブロードウェイボード（SB から）
- ハイペアードボード（IP から、または SB から）
- エース・ハイフロップ（SB から）
- 共通点：プリフロップレイザーがナッツアドバンテージを持つ
- ベットサイズ：ポットの約 1/3（33%）

**本書との乖離**:
- 本書式は HandScore の高低でベット/チェックを切り分けるため、
  Range CBet 条件でも弱いハンドはチェックしてしまう
- HandScore 低いハンドも含めてレンジ全体で 33% ベットすべき局面で、
  本書ではチェックバックが多くなる
- この乖離は「Range CBet 時に相手を防御コストで圧迫する機会の損失」だが、
  同時に「チェックバックしてもポットを膨らませない安全」でもある

- 出典: [10 Spots to Continuation Bet 100%](https://upswingpoker.com/when-to-c-bet-everything/)、Upswing Poker（2024年アクセス）
- 出典: [Aggregate Flop Strategy: SB C-Betting in SRP](https://blog.gtowizard.com/aggregate-flop-strategy-sb-c-betting-in-srp/)、GTO Wizard

---

### 知見3：ボードテクスチャ × プリフロップレンジの相互作用

GTO Wizard の研究によれば、**CBet 戦略の主ドライバーはプリフロップレンジ、
ボードテクスチャは従ドライバー**である。

> "Pre-flop range dynamics, not board texture, are the primary drivers of
> continuation betting strategy."
> — GTO Wizard, Flop Heuristics: IP C-Betting in Cash Games

- レンジアドバンテージ（レンジ全体での形勢）がベット**頻度**を決める
- ナッツアドバンテージ（強いハンドの偏り）がベット**サイズ**を決める
- ボードテクスチャは「プリフロップで確立されたアドバンテージを拡大or縮小」するが、
  それを逆転させることは少ない

**本書との乖離**:
- 本書の BoardScore はテクスチャ（ドライ/ウェット、モノトーン等）を直接評価する
- プリフロップレンジとの相互作用を明示的にモデル化していない
- 結果として「テクスチャは良いがレンジ不利」な局面でオーバーベットする可能性がある
  （例：BTN vs BB でミドルカードコネクテッドフロップ）

- 出典: [Flop Heuristics: IP C-Betting in Cash Games](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)、GTO Wizard

---

### 知見4：特殊ボードでの乖離

#### モノトーンフロップ

GTO（GTO Wizard 分析）のモノトーンフロップでの CBet 戦略:
- **小サイズで高頻度ベット**が最適（IP プリフロップレイザー視点）
- 実際にフロップでフラッシュが完成している確率は 5〜6% 程度と低い
- フラッシュ未完成の強いハンドで積極的にバリューを取る
- フラッシュブロッカーを持つハンドはコーリングレンジを絞るため、大きく張れない

**本書との乖離**:
- BoardScore の評価でモノトーンは「フラッシュ可能性が高い危険ボード」として
  スコアを下げる設計が多い → チェックバック頻度が高くなる
- GTO は「危険だからこそ小サイズで頻度ベット」する。本書は「危険だからチェック」
- EV 損失：モノトーンで IP 有利ハンドをチェックバックする機会損失

- 出典: [Maximizing Value on Monotone Flops](https://blog.gtowizard.com/maximizing-value-on-monotone-flops/)、GTO Wizard

#### ペアードフロップ（特にハイペアード）

GTO でのペアードフロップ CBet 頻度（GTO Wizard データ）:
- **エース・エース・X ボード**：小サイズ（〜1/3pot）で近 100% CBet
- KK-X：約 90%、QQ-X：約 80%、JJ-X：約 70%、TT-X：約 50〜60%
- 「相手（BB等）がトリップスを持つ確率が低い」ため、レイザーのレンジアドバンテージ大

**本書との乖離**:
- ペアードボードは BoardScore を低く設定しがちだが（コミュニティカードがペアで「弱い」）、
  GTO 視点では相手の強いハンドが絞られるためアドバンテージが大きい
- 本書式が低 BoardScore のためチェックバックする場面で、GTO は高頻度でベットする

- 出典: [C-Betting On Paired Boards](https://pokercoaching.com/blog/c-betting-on-paired-boards/)、PokerCoaching.com
- 出典: [Flop Heuristics: IP C-Betting in Cash Games](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)、GTO Wizard

---

### 知見5：マルチウェイポットでは式が通用しない

GTO Wizard「マルチウェイポット 10 のヒント」の核心原則：

> "Stop rangebetting. Give up more often with trash.
>  Tighten your value betting thresholds."

- ヘッズアップでは相手が広く守備しなければ搾取されるが、
  **マルチウェイでは防御コストが複数プレイヤーに分散**される
- 各プレイヤーは個別に狭い守備で済む → ブラフの EV が大幅低下
- CBet 頻度はヘッズアップの 50〜70% 程度から 20〜30% 程度へ急落
- バリューハンドと質の高いブラフのみでベットレンジを構成する
- 2025年、GTO Wizard は 3-way ポストフロップソルバーをリリース

**本書との乖離**:
- 本書式はヘッズアップを前提に HandScore + BoardScore を評価する
- マルチウェイでは同じスコアでもベットが不採算になるケースが多い
- 第18章（マルチウェイ）で明示的に調整を加える必要がある

- 出典: [10 Tips for Multiway Pots](https://blog.gtowizard.com/10-tips-multiway-pots-in-poker/)、GTO Wizard

---

### 知見6：初級者に決定論で十分な理由

GTO Wizard の原則と exploitative ダイナミクス研究が示す根拠：

1. **相手も GTO を実装していない**
   - 低〜中レベルのゲームで GTO からの逸脱が大きな損失を生むのは、
     相手が完璧な GTO を実行している場合のみ
   - 相手が suboptimal なら、シンプルな戦略でも正の EV を確保できる
   - 出典: [Exploitative Dynamics](https://blog.gtowizard.com/exploitative-dynamics/)、GTO Wizard

2. **混合戦略の実装エラーコスト**
   - GTO では「60% ベット、40% チェック」を乱数で実行すべきだが、
     人間がこれを正確に実装するのは困難
   - 「なんとなく混合」は GTO でも純粋戦略でもない最悪のパターンになりがち
   - 純粋戦略（決定論）は実装が完全になるため、エラーがない

3. **EV ギャップは小さい（ミックスノードの特性）**
   - GTO でミックスが発生するのは「2つのアクションの EV がほぼ等しい」とき
   - つまりどちらを選んでも EV 差はわずか（多くは 0.5〜2bb 程度）
   - 出典: [Principles of GTO](https://blog.gtowizard.com/principles-of-gto/)、GTO Wizard

---

### 知見7：Simplified GTO の考え方（GTO Wizard の思想）

GTO Wizard は 2024〜2025 年にかけて **Single Size Solutions** と
**Simplified Solutions** を整備。この方針が本書の方向性と合致する。

**GTO Wizard の Single Size Solutions（2025年リリース）**:
- 「各スポットで最高 EV の 1 サイズのみ」を提示
- Multiple sizes（2〜3 サイズ）vs Single size の EV 差は最小化されている
- 「Using 2 sizes vs 3 sizes: EV is the same as long as you choose appropriate sizes」
- ライブラリを **50倍以上**に拡大。無料プランでもアクセス可能
- 目的：「faster learning」「better execution at the table」

**GTO Wizard の Simplified Solutions の設計思想**:
- 複雑な multi-size 戦略から「各ボードで最重要な 1〜2 サイズ」を
  EV regret アルゴリズムで選択
- 複雑さを減らすことで、実テーブルでの実装精度が上がり
  トータル EV が向上するという実証的な立場

> "Taking out mixed frequencies and multiple bet sizes will result in a
> drop in EV, but it will make the strategy much easier to implement,
> giving you an advantage at the tables."
> — PokerGTO Solver / GTO Wizard の公式見解に近い表現

- 出典: [Single Size Solutions Are Live](https://blog.gtowizard.com/single-size-solutions-are-live-new-pricing-50x-more-solutions/)、GTO Wizard（2025年）
- 出典: [All You Need to Know About Our Solutions](https://blog.gtowizard.com/all-you-need-to-know-about-our-solutions/)、GTO Wizard

---

## 本書への適用

### 第11章「この式が GTO と外れるところ：CBet 編」構成案

| 節 | 内容 | GTO 乖離ポイント |
|----|------|----------------|
| 11-1 | GTO の混合戦略とは何か | 純粋戦略との EV 差は小さい |
| 11-2 | Range CBet の条件 | 本書はハイペアード・ドライボードで Range CBet を見逃す |
| 11-3 | プリフロップレンジが主ドライバー | BoardScore 単体評価の限界 |
| 11-4 | モノトーンボードの逆説 | 本書はチェック推奨、GTO は小頻度ベット |
| 11-5 | ペアードボードのアドバンテージ | 本書の BoardScore 低評価 vs GTO 高頻度ベット |
| 11-6 | 初級者に決定論で十分な 3 つの理由 | 実装エラー > 混合の理論 EV |
| 11-7 | Simplified GTO という潮流 | GTO Wizard 自身もシンプル化を推奨 |

### 重要メッセージ（執筆の核心）

- 本書式は GTO ではないが「正しく外れている」：外れる方向が初級者に有利
- GTO との乖離が最大の弱点：マルチウェイポット（→第18章で対処）
- 「GTO を知りながらシンプルにする」のと「知らずにシンプルにする」は違う
  本章でその違いを明示することで、読者の理解が深まる

---

## 補足：CBet 統合式の具体的乖離マップ

```
ボードタイプ         本書式          GTO          乖離の方向
-----------         ------          ---          ----------
ドライ・レインボー    中頻度ベット    高頻度・小サイズ  本書が少なめ
モノトーン           低頻度ベット    中頻度・小サイズ  本書が少なすぎ★
ハイペアード(AA-X)   低〜中頻度     ~100%・小サイズ  本書が少なすぎ★
ウェット・コネクテッド 中〜高頻度    中頻度・大サイズ  本書がサイズ小
マルチウェイ          式をそのまま   大幅減少         本書が多すぎ★★
```

★：第11章で「本書の限界」として解説
★★：第18章（マルチウェイ）で対処
