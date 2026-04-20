# 01: プリフロップ重要性の定量データと専門家見解

検索日: 2026-04-19

## 概要

プリフロップはテキサスホールデムで**唯一、全ハンドで必ず下す決断のある街路**である。勝ち組プレイヤーのVPIP/PFRデータ、フロップ到達率の統計、GTO솔버によるEV分析、専門家の見解、および簡易式とGTOの比較を整理する。

---

## 1. プリフロップの頻度統計

### 1-1. 勝ち組プレイヤーのVPIP・PFR目安値

#### 6-max（6人打ち）

| 指標 | 目安値 | 補足 |
|------|--------|------|
| VPIP | 21% | BlackRain79が数百万ハンドのPokerTrackerデータから算出 |
| PFR  | 18% | VPIPとの差は約3ポイント以内が望ましい |
| VPIP上限（勝ち組） | 26% | これ以上はルーズすぎる傾向 |
| VPIP下限（勝ち組） | 18% | これ未満は機会損失 |

- 出典: [What is a Good PFR in Poker? | BlackRain79](https://www.blackrain79.com/2019/10/what-is-good-pfr-in-poker.html)（2019年、PokerCopilot統計も参照）

#### フルリング（9人打ち）

| 指標 | 目安値 |
|------|--------|
| VPIP | 15% |
| PFR  | 12% |

- 出典: 同上（BlackRain79, 2019）

**追加データ（2024-2025年）**: 大手オンラインルームのハンド履歴解析によると、長期勝ち組はVPIP 18–24%に集中し、大負けプレイヤーはVPIP 30%超かつPFRひと桁台に集中する傾向がある。
- 出典: [VPIP and PFR - Poker Statistics | PokerCopilot](https://pokercopilot.com/poker-statistics/vpip-pfr)（2024年）

#### VPIP-PFR差の重要性

VPIPとPFRの差が大きい（例：VPIP 30 / PFR 8）プレイヤーはパッシブなコーラーであり、長期的に不利。勝ち組は**この差を常に2〜4ポイント程度に維持**する。
- 出典: [PFR in Poker Explained | CardPlayer](https://www.cardplayer.com/rules-of-poker/glossary/pfr-in-poker)（2023年）

---

### 1-2. プリフロップ段階での折り畳み率

**「勝ち組プレイヤーの75%以上はプリフロップで折りたたむ」**（原文：*"The best poker players fold 75 percent or more of all starting hands before the betting even begins."*）

- 最もルーズな勝ち組でも折り畳み率は約70%
- 6-maxの勝ち組はVPIP 22–26%（フロップを見る割合）であり、裏を返すと**74〜78%のハンドをプリフロップで折りたたむ**
- 出典: [When to Fold in Poker | Upswing Poker](https://upswingpoker.com/when-to-fold-in-poker-before-after-flop/)（2023年）
- 出典: [What percentage of Poker hands are playable pre-flop? | Quora](https://www.quora.com/What-percentage-of-Poker-hands-are-playable-pre-flop)

---

### 1-3. フロップ・ターン・リバー到達率の段階的低下

**PokerCopilot統計（オンラインキャッシュ、複数レート）**:

> 「ポットの大多数はプリフロップで終了する。フロップを見るのはわずか17%のハンドに過ぎない。」
> （原文：*"The vast majority of pots do not go past preflop—only 17% of hands see the flop."*）

| 街路 | 到達率（概算） |
|------|---------------|
| フロップ | 約17–20% |
| ターン | 約8–10%（フロップの約半分） |
| リバー | 約4–6% |
| ショーダウン | 約2–3%（WTSD: 27–32%、ただしWTSDはフロップ到達ハンドに対する割合）

- 出典: [Essential Poker Statistics | PokerCopilot](https://pokercopilot.com/essential-poker-statistics)（2024年）
- 出典: [WTSD in Poker: Why This Statistic is So Important | GipsyTeam](https://www.gipsyteam.com/poker/wwsf-in-poker)（2023年）

**含意**: 全ハンドの80%超はプリフロップだけで決着する。プリフロップの判断の質がそのままハンド全体の質に直結する。

---

## 2. プリフロップのEV影響

### 2-1. GTO Wizard によるプリフロップ分析の位置づけ

GTO Wizardは公式ブログで次のように述べている：

> 「プリフロップは（収益改善の）最大のレバーである」
> （原文：*"Preflop serves as the foundation and the biggest lever towards increasing your win-rate on the felt."*）

GTO Wizard AIはプリフロップからリバーまでの各意思決定点において**最高EVとなるサイジングを自律的に推定**する。プリフロップ誤りは後続ストリートのEVに累積的に波及する仕組みになっている。

- 出典: [GTO Wizard Blog - How Solvers Work](https://blog.gtowizard.com/how-solvers-work/)（2023年）
- 出典: [Introducing Multiway Preflop Solving | GTO Wizard](https://blog.gtowizard.com/introducing-multiway-preflop-solving/)（2024年）

---

### 2-2. プリフロップ誤りの具体的なEVコスト

GTO Wizard公式記事「Understanding Which Mistakes Cost You the Most Money」から：

| 誤りの種類 | EVコスト | スケール換算 |
|-----------|---------|------------|
| レンジ境界で1ハンド誤る（例：A9o vs ATo の判断ミス） | 0.49bb/手 | 49bb/100の損失（繰り返した場合） |
| レンジ境界での1ポイントミス（マイナーエラー） | 0.14bb/手 | 14bb/100の損失（繰り返した場合） |
| フロップでのベットサイズ誤り（25% vs 50%ポット） | 0.31bb | 単発 |
| ターンでのベットサイズ誤り（同条件） | 0.87bb | 単発（フロップの約3倍） |

**重要な視点**: GTO Wizardは「コールの誤りは最もコストが高い」と分析する。コールしたポットは大きくなるため、誤った呼び込みは誤ったオープンよりもはるかに損失が大きい。

- 出典: [Understanding Which Mistakes Cost You the Most Money | GTO Wizard](https://blog.gtowizard.com/understanding-which-mistakes-cost-you-the-most-money/)（2023年）

---

### 2-3. プリフロップ誤りがポストフロップに連鎖するメカニズム

Jonathan Littleはこのテーマを繰り返し論じている：

> 「プリフロップで誤りを犯すと、フロップ・ターン・リバーでもその誤りを複利的に重ねていく」
> （原文：*"If you make mistakes preflop, you will compound these mistakes by making more on the flop, turn, and river."*）
> （出典：[CardPlayer - Preflop Mistakes Lead To Post-Flop Blunders](https://www.cardplayer.com/poker-news/29287-poker-strategy-with-jonathan-little-preflop-mistakes-lead-to-post-flop-blunders)）

> 「健全なプリフロップ戦略なくして、どれほどポストフロップが巧みでも損失は補えない」
> （原文：*"Without a sound preflop strategy, no amount of skill can make up for the losses."*）

**連鎖する典型例（Upswing Poker, 2023）**:
1. マルチウェイポットが増加 → 1手ずつの勝率が低下（3人ポットでAKの勝率は約30%まで低下）
2. 3ベットで heads-up に絞ると同じAKが約60%の勝率 → 差は30ポイント
3. アーリーポジションで広すぎるレンジ → アウト・オブ・ポジションでのポストフロップ守備問題が増加

- 出典: [12 Preflop Mistakes to Avoid at All Costs | Upswing Poker](https://upswingpoker.com/preflop-poker-mistakes-avoid-at-all-cost/)（2023年）
- 出典: [Strategies for avoiding compounding mistakes | Part Time Poker](https://www.parttimepoker.com/strategies-for-avoiding-cascading-errors)（2022年）

---

## 3. AJoのEV by position

### 3-1. ポジション別オープン範囲（6-max、100bb、NL）

| ポジション | オープン率（GTO目安） |
|-----------|---------------------|
| UTG | 約10〜17% |
| MP（HJ） | 約19〜22% |
| CO | 約25〜30% |
| BTN | 約40〜51% |
| SB | 約39〜47% |

- 出典: [Preflop Range Morphology | GTO Wizard](https://blog.gtowizard.com/preflop-range-morphology/)（2024年）
- 出典: [6-Max Opening Ranges | FreeBetRange](https://blog.freebetrange.com/article/preflop-charts-open-raise-in-6-max-poker-cash-games)（2024年）

---

### 3-2. AJoのポジション別判断

**GTO Wizard分析（NL500, 6max, 100bb）**:

- **UTG**: AJoはUTGの約10.1%オープンレンジに含まれるが、レンジ最弱クラス（KQoとAJoが最弱のオフスーツオープン）
- **HJ（MP）からUTGオープンへのコール**: HJからUTGオープンにコールする場合、AJoは「コール可能な最弱のオフスーツA」で +0.07bb と辛うじてプラス
- **A9oとの比較**: A9oでコールすると −0.42bb → AJo vs A9oの差は0.49bb（＝この判断を繰り返すと49bb/100の差）
- **BTN**: BTNではA2o以上の全オフスーツAをオープンする（51.3%レンジに含まれる）

**結論**:
- AJoはUTGでは「レンジの底辺」として辛うじて含まれるか、または混合戦略（一部折りたたみ）となる
- BTNではAJoは余裕でオープン対象
- 「UTGでは赤字、BTNでは黒字」という俗説の方向性は概ね正しいが、UTGでの正確なEVは場合によりわずかなプラスに留まるか混合戦略（要確認: ソルバーの具体的なEV数値はGTO Wizardの有料機能内に限定される）

- 出典: [Understanding Which Mistakes Cost You the Most Money | GTO Wizard](https://blog.gtowizard.com/understanding-which-mistakes-cost-you-the-most-money/)（HJからのコール分析として）（2023年）
- 出典: [Preflop Range Morphology | GTO Wizard](https://blog.gtowizard.com/preflop-range-morphology/)（2024年）
- 出典: [Doug Polk Answers Preflop Questions | Upswing Poker](https://upswingpoker.com/pre-flop-no-limit-poker-strategy-questions-answered-doug-polk/)（ポジション別Axの扱いについて）

---

### 3-3. オープンサイジングのポジション別標準（GTO Wizard）

GTO Wizard AIが推奨するオープンサイズは、旧来の常識とは逆で**アーリーポジションほど小さい**：

| ポジション | 推奨オープンサイズ |
|-----------|------------------|
| UTG | 2.0bb |
| CO | 2.3bb |
| BTN | 2.5bb |
| SB | 3.0bb |

理由：アーリーポジションは3ベットを受けにくい（強いレンジで参加しているため）。レイターポジションほど多様な相手に直面するため大きいサイズが最適。

---

## 4. 専門家の「プリフロップ重視」発言

### 4-1. Doug Polk（Upswing Poker 創設者）

> 「2017年の現在のタフなポーカー環境では、健全なプリフロップ戦略は長期的な成功のために必須だ」
> （原文：*"With the tough poker climate of 2017, a good pre-flop strategy is mandatory for long term success."*）

また、BTNからは全オフスーツAをオープンすべきとしつつ、SBではATs+, AJo+に絞ることを推奨する（ポジションによるAJoの扱いが変わる典型例）。

- 出典: [Doug Polk Answers Your 6 Best Questions About Pre-Flop Play | Upswing Poker](https://upswingpoker.com/pre-flop-no-limit-poker-strategy-questions-answered-doug-polk/)（2017年）

---

### 4-2. Jonathan Little（PokerCoaching.com 創設者）

> 「プリフロップの判断はすべてのポーカーハンドで必ず下さなければならない。だからこそ極めて重要だ」
> （原文：*"You make pre-flop decisions for every single poker hand, which makes them extremely important."*）

> 「プリフロップで誤りを犯すと、フロップ・ターン・リバーでも累積的に誤りを重ねることになる」
> （出典: [CardPlayer - Preflop Mistakes Lead To Post-Flop Blunders](https://www.cardplayer.com/poker-news/29287-poker-strategy-with-jonathan-little-preflop-mistakes-lead-to-post-flop-blunders)）

- 出典: [Poker Strategy With Jonathan Little: Mastering the Fundamentals – Preflop Strategy | Poker.org](https://www.poker.org/poker-videos/jonathan-little-mastering-the-fundamentals-preflop-strategy-agTuj6Z3Wp0x/)

---

### 4-3. Fedor Holz（PokerCode 創設者・世界トップクラスのMTTプロ）

> 「GTOを理解することは、正確な判断を下し、GTOを理解していない相手を搾取する能力の根幹だ」
> （原文：*"Understanding GTO is fundamental to being able to make accurate poker decisions and being able to exploit players who don't."*）

Fedor HolzのMTTマスタークラスでは、プリフロップの基礎確立を**最初のカリキュラム**として位置づけている。

- 出典: [GTO Poker Solvers in a Nutshell – Expert Tips by Fedor Holz | mypokercoaching.com](https://www.mypokercoaching.com/fedor-holz-poker-solvers/)（2023年）
- 出典: [GTO Poker 101 | PokerCode Blog](https://www.pokercode.com/blog/gto-poker)（2023年）

---

### 4-4. Phil Galfond（Run It Once 創設者）

Phil Galfondは自身のFoundationsコースにて：

> 「プリフロップチャートを丸暗記することは最悪の学習法だ。チャートは最初の拠り所（crutch）に過ぎず、深い理解に置き換えられるべき」
> （出典: [Foundations by Phil Galfond - Comprehensive Review | mypokercoaching.com](https://www.mypokercoaching.com/foundations-by-phil-galfond-review/)）

これは「チャート暗記ではなく、なぜそのレンジになるかの理解が重要」という、プリフロップ戦略の**質的な深さ**を強調する立場。

---

### 4-5. Matthew Janda（著書：Applications of No-Limit Hold'em, 2013）

Jandaは自著においてプリフロップレンジ構築を中心テーマに据え：

> 「特定のハンドを上手くプレイする方法を知っているだけでは不十分だ。自分のレンジ内の全ハンドをどうプレイするかを理解しなければならない」
> （原文：*"One of the most daunting moments in a poker player's career occurs when he realizes his knowledge of how to play a specific hand well is incomplete without the additional understanding of how to play every other hand in his range well."*）

- 出典: [Applications of No-Limit Hold'em | Amazon](https://www.amazon.com/Applications-No-Limit-Hold-Matthew-Janda/dp/1880685558)（2013年）、[Upswing Poker レビュー](https://upswingpoker.com/best-poker-training-theory-book-gto-applications-holdem-janda/)（2020年）

---

### 4-6. Michael Acevedo（著書：Modern Poker Theory, 2019）

> 「GTOを理解することは、正確なポーカーの決断を下し、GTOを理解しない相手を搾取するための根幹だ」

本書はプリフロップチャートを約300ページ割いており、GTO視点でのプリフロップ戦略を体系的に整理した最も包括的な現代書籍とされている。

- 出典: [Modern Poker Theory: Building an Unbeatable Strategy | Amazon](https://www.amazon.com/Modern-Poker-Theory-unbeatable-principles/dp/1909457892)（2019年）
- 出典: [Review of Modern Poker Theory | smartpokerpro.com](https://smartpokerpro.com/modern-poker-theory/)（2020年）

---

## 5. 簡易式 vs GTO

### 5-1. Chen Formula（チェン・フォーミュラ）

**開発者**: Bill Chen（数学者・ポーカープロ）
**掲載**: Lou Krieger著『Hold'em Excellence』（2000年）にて初出。後に『The Mathematics of Poker』（Chen & Ankenman, 2006年）で理論的背景が補強された。

#### 計算ルール

| ステップ | 内容 |
|---------|------|
| 1. 高カード評価 | A=10、K=8、Q=7、J=6、10〜2 = ランク÷2（端数は切り上げ）|
| 2. ペア補正 | 2枚同じ → ×2（最低5点フロア）|
| 3. スーテッドボーナス | +2点 |
| 4. ギャップペナルティ | 0ギャップ=0、1ギャップ=−1、2ギャップ=−2、3ギャップ=−4、4+ギャップ=−5 |
| 5. ストレートボーナス | クイーン以下で0〜1ギャップ → +1点 |

#### 主要ハンドのスコア例

| ハンド | スコア | 備考 |
|--------|--------|------|
| AA | 20 | 10×2 |
| KK | 16 | 8×2 |
| AKs | 12 | A(10)+suited(2)、ギャップ0 |
| AKo | 10 | A(10)、ギャップ0 |
| AJo | 9 | A(10)−1ギャップ(1) = 9 ※Jは6点だが高カードはAで評価 |
| 98s | 8 | 9(4.5→5)+suited(2)+0ギャップ+1ストレートボーナス = 8 |
| 22 | 5 | 2×2=4 → フロア5 |

- 出典: [Chen Formula in Poker | 888Poker](https://www.888poker.com/magazine/strategy/chen-formula)（2022年）
- 出典: [The Chen Formula | ThePokerBank](https://www.thepokerbank.com/strategy/basic/starting-hand-selection/chen-formula/)（2023年）

---

### 5-2. Sklansky-Malmuth Hand Groups（SHG / SMG）

**出典書籍**: David Sklansky & Mason Malmuth著『Hold'em Poker for Advanced Players』（1988年初版）
**対象**: 元来リミットホールデム向けに設計されており、ノーリミットへの直接適用は不適切とされる。

#### グループ一覧（グループ1が最強）

| グループ | 代表ハンド |
|---------|-----------|
| 1 | AA, AKs, KK, QQ, JJ |
| 2 | AK, AQs, AJs, KQs, TT |
| 3 | AQ, ATs, KJs, QJs, JTs, 99 |
| 4 | AJ, KQ, KTs, QTs, J9s, T9s, 98s, 88 |
| 5 | A9s-A2s, KJ, QJ, JT, Q9s, T8s, 97s, 87s, 77, 76s, 66 |
| 6 | AT, KT, QT, J8s, 86s, 75s, 65s, 55, 54s |
| 7 | K9s-K2s, J9, T9, 98, 64s, 53s, 44, 43s, 33, 22 |
| 8 | A9, K9, Q9, J8, J7s, T8, 96s, 87, 85s, 76, 74s, 65, 54, 42s, 32s |
| 9（その他） | それ以下のハンド |

**注目点**: AJoはグループ4、AKoはグループ2（sはsuited）

- 出典: [Sklansky and Malmuth Starting Hand Groups | ThePokerBank](https://www.thepokerbank.com/strategy/basic/starting-hand-selection/sklansky-groups/)（2023年）
- 出典: [Texas hold'em starting hands | Wikipedia](https://en.wikipedia.org/wiki/Texas_hold_%27em_starting_hands)

---

### 5-3. 現代GTOとの比較

#### 主な相違点

| 観点 | Chen式 / SHG | 現代GTO（ソルバー） |
|------|-------------|------------------|
| ポジション | ほぼ考慮しない | 最重要変数（AJoはUTGとBTNで戦略が別物） |
| スタックデプス | 考慮なし | 100bb vs 40bb では大幅にレンジが変わる |
| レーキ | 考慮なし | NL50とNL500ではレンジが異なる（NL50ではブロッカーハンドを重視） |
| 相手のレンジ | 固定 | 対戦相手の推定レンジに連動して動的に調整 |
| マルチウェイ | 考慮が浅い | マルチウェイポットでスーテッドコネクターの価値が上昇 |
| レンジ方向 | 簡易式でも「広げすぎない」設計 | GTOは**レンジを適正化**（広くも狭くもなく精緻化） |

#### GTOによるレンジの変化方向

- **アーリーポジション（UTG/MP）**: GTO的なレンジはSHGより若干**狭い**（ポジション不利・3ベットリスクを精緻計算するため）
- **レイトポジション（CO/BTN）**: GTOは積極的に**広げる**（A2o以上の全オフスーツAをBTNでオープン）
- **スーテッドコネクター**: GTOはSHGよりも高く評価する（プレイアビリティ・ブロック効果を加味）

> 「チェン式は初心者の訓練用の補助輪であり、優れたプレイヤーはポーカーの本質的な複雑さのために必ず手放すことになる」
> （原文：*"The formula functions as 'training wheels,' useful for beginners but abandoned by competent players due to poker's inherent complexity."*）

- 出典: [Chen Formula in Poker | 888Poker](https://www.888poker.com/magazine/strategy/chen-formula)（2022年）
- 出典: [GTO Wizard Blog – Preflop Range Morphology](https://blog.gtowizard.com/preflop-range-morphology/)（2024年）

---

## 本書への適用

| セクション | 活用方法 |
|-----------|---------|
| プリフロップの重要性論証 | 「75%以上が折りたたまれる」「フロップ到達は17%」の統計を冒頭に示し、プリフロップの重さを即視化する |
| VPIP/PFR解説 | 勝ち組の21/18（6max）・15/12（フルリング）を基準として提示し、読者が自分の位置を把握できるようにする |
| AJoの位置解説 |「UTGでは最弱クラス、BTNでは余裕のオープン対象」という具体例でポジションの重要性を示す |
| 簡易式からGTOへ | SHGとChen式を「歴史的文脈」として紹介し、現代GTOとの差を明示することで学習の進化を示す |
| プリフロップ誤りのコスト | A9o vs AToの 49bb/100 コストを使って「たった1ハンドの判断差が長期収支を変える」と訴求する |
| 専門家の声 | Jonathan LittleとDoug Polkの引用を権威付けとして使用（日本人読者にも認知度が高い） |

---

## 参考URL一覧

- [VPIP and PFR - Poker Statistics | PokerCopilot](https://pokercopilot.com/poker-statistics/vpip-pfr)（2024年）
- [What is a Good PFR in Poker? | BlackRain79](https://www.blackrain79.com/2019/10/what-is-good-pfr-in-poker.html)（2019年）
- [When to Fold in Poker | Upswing Poker](https://upswingpoker.com/when-to-fold-in-poker-before-after-flop/)（2023年）
- [Essential Poker Statistics | PokerCopilot](https://pokercopilot.com/essential-poker-statistics)（2024年）
- [Understanding Which Mistakes Cost You the Most Money | GTO Wizard](https://blog.gtowizard.com/understanding-which-mistakes-cost-you-the-most-money/)（2023年）
- [Preflop Range Morphology | GTO Wizard](https://blog.gtowizard.com/preflop-range-morphology/)（2024年）
- [Introducing Multiway Preflop Solving | GTO Wizard](https://blog.gtowizard.com/introducing-multiway-preflop-solving/)（2024年）
- [Punish the Unstudied: Preflop Mistakes & Sizing Tells | GTO Wizard](https://blog.gtowizard.com/punish_the_unstudied_preflop_mistakes_and_sizing_tells/)（2023年）
- [12 Preflop Mistakes to Avoid at All Costs | Upswing Poker](https://upswingpoker.com/preflop-poker-mistakes-avoid-at-all-cost/)（2023年）
- [Doug Polk Answers Preflop Questions | Upswing Poker](https://upswingpoker.com/pre-flop-no-limit-poker-strategy-questions-answered-doug-polk/)（2017年）
- [CardPlayer - Preflop Mistakes Lead To Post-Flop Blunders | Jonathan Little](https://www.cardplayer.com/poker-news/29287-poker-strategy-with-jonathan-little-preflop-mistakes-lead-to-post-flop-blunders)
- [Poker Strategy With Jonathan Little: Mastering the Fundamentals | Poker.org](https://www.poker.org/poker-videos/jonathan-little-mastering-the-fundamentals-preflop-strategy-agTuj6Z3Wp0x/)
- [GTO Poker 101 | PokerCode](https://www.pokercode.com/blog/gto-poker)（2023年）
- [Foundations by Phil Galfond - Review | mypokercoaching.com](https://www.mypokercoaching.com/foundations-by-phil-galfond-review/)（2023年）
- [Modern Poker Theory | Amazon](https://www.amazon.com/Modern-Poker-Theory-unbeatable-principles/dp/1909457892)（2019年）
- [Review of Modern Poker Theory | smartpokerpro.com](https://smartpokerpro.com/modern-poker-theory/)（2020年）
- [Applications of No-Limit Hold'em | Amazon](https://www.amazon.com/Applications-No-Limit-Hold-Matthew-Janda/dp/1880685558)（2013年）
- [Chen Formula in Poker | 888Poker](https://www.888poker.com/magazine/strategy/chen-formula)（2022年）
- [The Chen Formula | ThePokerBank](https://www.thepokerbank.com/strategy/basic/starting-hand-selection/chen-formula/)（2023年）
- [Sklansky-Malmuth Starting Hand Groups | ThePokerBank](https://www.thepokerbank.com/strategy/basic/starting-hand-selection/sklansky-groups/)（2023年）
- [Texas hold'em starting hands | Wikipedia](https://en.wikipedia.org/wiki/Texas_hold_%27em_starting_hands)
- [Strategies for avoiding compounding mistakes | Part Time Poker](https://www.parttimepoker.com/strategies-for-avoiding-cascading-errors)（2022年）
- [PFR in Poker Explained | CardPlayer](https://www.cardplayer.com/rules-of-poker/glossary/pfr-in-poker)（2023年）
- [The Ultimate Guide to 6-Handed Poker | Upswing Poker](https://upswingpoker.com/6-handed-max-poker-strategy/)（2023年）
- [6-Max Opening Ranges | FreeBetRange](https://blog.freebetrange.com/article/preflop-charts-open-raise-in-6-max-poker-cash-games)（2024年）
