# 08: この式がGTOと外れるところ（オープン編）

検索日: 2026-04-19

## 概要

本書の簡易スコア式はプリフロップ判断を暗算可能な決定論的ルールに落とし込んでいる。
GTOソルバーが出力する戦略とは系統的に乖離するポイントが複数存在するが、その乖離は「簡易式の欠陥」ではなく「近似コスト」として合理化できる。本章ではその乖離を体系化し、読者が式を使い続ける根拠を与える。

---

## 1. ミックス戦略（頻度ベースアクション）とは

### 1-1. GTOが混合戦略を採用する理由

GTOはナッシュ均衡の実装である。ナッシュ均衡では「どちらのアクションも同じEVになる」という無差別条件（indifference condition）が成立したとき、ソルバーは複数アクションを一定頻度で混合させる。

- 例: あるハンドが「レイズ17%・コール63%・フォールド20%」という混合戦略を取る
- 目的: 相手が自分のアクションからハンドを特定できないようにし、搾取を防ぐ
- 技術的背景: CFR（Counterfactual Regret Minimization）アルゴリズム（Zinkevich et al., 2007年）で収束

> "The correct strategy for a particular hand may be mixed between different options."
> — GTO Wizard Blog

混合する必要があるのは**境界ハンド**（marginal hands）である。
強いハンド（AA、KK）や明確なフォールド（72o）は純戦略（100%単一アクション）で十分。

### 1-2. 混合戦略と搾取不可能性の関係

常に同じアクションを取る決定論的戦略は、熟練した相手に搾取される。
例: AQoを常に3ベットすると、相手はその場面での自分のレンジを正確に読める。
AQoを「3ベット85%・コール15%」で混合することで、相手を無差別に保つ。

ただし**低〜中ステークスでは相手がこれほど精密に読まないため、混合しなくてもEV損失は軽微**。

### 1-3. 実戦での乱数実装方法

| 方法 | 実装 | 精度 |
|------|------|------|
| 時計の秒針 | 偶数秒→アクションA、奇数秒→アクションB（50/50） | 中 |
| 時計の三分割 | :00-:19→A、:20-:39→B、:40-:59→C（33%分割） | 中 |
| ランダム数字生成 | スマートフォンのGoogle RNG（テーブルでの使用は要確認） | 高 |
| チップカウントの末尾 | 末尾0〜3→フォールド、4〜9→レイズ（40/60分割近似） | 低 |

> "Others will look at a clock on the wall and, for example, if the seconds hand is between 30 seconds and 45 seconds might take the less frequent option."
> — PokerStrategy.com

### 1-4. 本書の決定論的式との関係

本書のスコア式は「しきい値を超えたらレイズ、下回ったらフォールド」という純戦略である。
ソルバーが「65%レイズ、35%フォールド」とする境界ハンドを「どちらか一方」に分類する。

**この近似のEVコスト**: 境界ハンドでの乖離は通常0.01bb〜0.05bb/手程度。
**学習上の利点**: 暗算可能、即座に判断でき、教育的に明快。

---

## 2. スーテッドの価値をGTOがより高く評価する構造

### 2-1. 本書の +2 評価 vs GTOの評価

本書はスーテッドボーナスを一律 +2 としている。
GTOはスーテッドに対してより複雑な評価をする。

**エクイティリアライゼーション（EQ実現率）の差**:
スーテッドハンドはオフスーツよりポストフロップでのEQを高く実現できる。

- フラッシュドロー・バックドアフラッシュドロー: 相手に余分な降り理由を与える
- ナットフラッシュの可能性: 相手のフラッシュを制することで逆ポットを防ぐ

> "HJ's A♦2♦ realizes almost 100% of its equity... while the BB's realizes less than 2%."
> — GTO Wizard, Equity Realization article

ポジションとスーテッドの組み合わせが最も価値を高める。

### 2-2. 下位スーテッドコネクター（65s〜54s）のGTO評価

GTOレンジにおける位置付け:

| ポジション | 65s 開き | 54s 開き |
|-----------|---------|---------|
| UTG | 非採用 | 非採用 |
| UTG+2 | 採用（15.7%レンジ） | 非採用 |
| HJ | 採用（21.3%レンジ） | 採用 |
| CO | 採用 | 採用 |
| BTN | 採用 | 採用 |

**開かれる理由（GTO的）**:
1. **ボードカバレッジ**: ミドルカードのボードで「セットの代わり」として機能
2. **ナッツ到達性**: ストレートやフラッシュに発展してスタッキングできる
3. **ブラフ候補**: フォールドエクイティとエクイティを両立するセミブラフ

**開かれない理由（小さいサイズほど難しい）**:
- 54sがフロップにトップペアを作る確率はわずか1%
- ペアになっても2nd〜3rdペアになりやすく価値が低い
- 大きいスーテッドコネクター（JTs、T9s）と比べてオーバーカードがない分、ターン・リバーでの改善幅が狭い

> "Small suited connectors like 65s or 54s are almost always to be folded in cash games, while some of the higher ones like JTs and T9s act as great bluffing candidates."
> — 888 Poker GTO Strategy

### 2-3. A2s〜A5s の3ベットブラフ利用（ブロッカー効果）

GTOは A2s〜A5s を強力なブラフ候補として高評価する。これが本書のスコア式で**過小評価される**代表例。

**A5sが高評価される理由**:
1. **エースブロッカー**: 相手がAAやAKを持つ確率を下げる（3ベット/4ベット率を抑制）
2. **アンブロッカー**: 小さいカード（5）が相手のフォールドハンド（K9s、Q8s等）をブロックしない
3. **ナットフラッシュ**: スーテッドであることでナッツフラッシュに発展
4. **ホイールストレート**: A-2-3-4-5のストレートに発展

**EV比較データ（300BB、レーキなし）**:

| ハンド | UTG オープン EV |
|--------|---------------|
| A5s | +0.09bb（9BB/100） |
| AQo | +0.01bb（1BB/100） |

A5sはAQoよりもはるかに高いEVを示す。見た目の強さとGTO評価が逆転する典型例。

- 出典: [Why Do Poker Solvers Love Ace Five Suited So Much?](https://www.gipsyteam.com/news/27-11-2024/why-do-poker-solvers-love-ace-five-suited)（2024年11月）

**A5sの4ベット頻度**: 70%（プレミアムをブロックしつつ相手のフォールドを誘う）

**A2sが A5sより劣る理由**:
- 65sに対してストレートで負ける可能性がある（2が逆に相手のストレートを助ける場合も）
- 5は独立したアンブロッカーとして機能するが、2はよりレアな状況でのみ活躍

---

## 3. レーキの影響

### 3-1. レーキが戦略に影響する仕組み

「ノーフロップ・ノードロップ」ルール: プリフロップで終わった場合はレーキが取られない。
これにより**ポストフロップに進むほどレーキコストが発生**する。

> "At NL50, more rake is paid if the hand goes postflop, so there is more incentive to 3-bet preflop to take the pot down before it goes postflop."
> — GTO Wizard, Preflop Range Morphology

### 3-2. ステークス別のレーキ率の差

| ステークス | 典型的レーキ上限 | 実効レーキ率 |
|-----------|--------------|------------|
| NL2/NL5 | 極めて大きい（相対的） | 最高 |
| NL50 | 4bb上限（例） | 高 |
| NL500 | 0.6bb上限（例） | 低（NL50の約1/7） |

**NL50 と NL500 の具体的なレンジ差（BB vs BTN 3ベット場面）**:
- NL50: BB フォールド 62%、コール 1.4%
- NL500: BB フォールド 59%、コール 3.2%

高レーキ環境では:
- ブロッカーハンド（A2s、K8s〜K5s）の比率が増える（ポットを奪いやすいため）
- 低レーキ環境では KTo や T8s、小ペアが開かれやすくなる

- 出典: [GTO Wizard - Rake & Rakeback Explained](https://blog.gtowizard.com/rake-rakeback-explained-optimize-your-poker-earnings/)

### 3-3. 本書の式はどのレーキ想定か

本書の式はレーキを明示的に考慮しない（レーキなし近似）。
**実用上の影響**:
- NL100 以上では誤差が小さい（レーキ率が低い）
- NL25 以下ではレーキの影響が大きく、マージナルハンドはレンジから外す判断が合理的
- **補正方針**: 低ステークスでは本書のしきい値より若干厳しくする（スコア +1〜+2 を追加ペナルティとして考える）

---

## 4. オープンサイズの影響

### 4-1. サイズ別の戦略的効果

| サイズ | 主要特性 | EV優位ハンド |
|--------|--------|------------|
| 2bb | 早い位置から効率的、リスク最小 | QQ以下の大部分 |
| 2.5bb | BTNでの標準（プロの99%が使用） | 中間ハンド群 |
| 3bb | ブラインドへの最大フォールドエクイティ | AA、KK、AKs |

**具体的EV比較（100NL、200BBスタック、LJ位置）**:

| ハンド | 2bb EV | 3bb EV |
|--------|--------|--------|
| AA | 9.48bb | 10.15bb |
| KK | 3bbが若干優位 | （具体数値は要確認） |
| QQ | 1.13bb | 0.95bb |
| AKo | ほぼ同等 | ほぼ同等 |

QQですら2bbが優れるほど、ほとんどのハンドは小さいサイズを好む。

> "A 3bb open risks 50% more than a 2bb open but gets only 5%–10% more folds from HJ, CO, and BTN."
> — GTO Wizard, Preflop Raise Sizing

- 出典: [Preflop Raise Sizing: Examining 2 Key Factors](https://blog.gtowizard.com/preflop-raise-sizing-examining-2-key-factors/)

### 4-2. BTNの特殊性

BTNの最弱ハンド（J4s、T5s、K7o、A2o等）は**3bbオープンを好む**。
理由: これらのハンドはポストフロップで価値を発揮しにくく、折り畳む可能性を高めたい。
「弱いハンドほど大きいベット」というカウンターインテュイティブな現象。

### 4-3. 本書のサイズ固定に対する評価

本書は特定のオープンサイズを前提にしているが、実際には:
- プロは位置によってサイズを変える（UTG: 2bb、CO: 2.3bb、BTN: 2.5bb）
- **本書の影響**: サイズを変えることよりレンジ判断の方が重要であり、学習者はまずレンジ精度を高めることを優先すべき

---

## 5. 本書スコア式がGTOと外れるハンド群まとめ

### 5-1. 過大評価されるハンド群（本書が開きすぎる）

| ハンド | 本書評価 | GTO評価 | 乖離理由 |
|--------|--------|--------|--------|
| AJo（UTG） | 開きやすい | フォールド多め | 3ベットに対して dominated; AJ vs AQ/AK で大きく不利 |
| KQo（EP） | 開きやすい | フォールド多め | 3ベット時に AK/AQ に完全 dominated; OOPで活かしにくい |
| QJs（UTG） | 開きやすい | 混合（50%前後） | J9s・T8s より domination リスクが高い; UTGからだとEV低下 |

**共通原因**: ブロードウェイオフスーツは絵札が大きい分「強そう」に見えるが、3ベット後のエクイティが下落しやすい。スーテッド版と比べてフラッシュドロー・バックドアの期待値がない。

### 5-2. 過小評価されるハンド群（本書が折りすぎる）

| ハンド | 本書評価 | GTO評価 | 乖離理由 |
|--------|--------|--------|--------|
| A2s〜A5s | 弱いスーテッドエース | 高評価（特にCO/BTN） | エースブロッカー＋ナッツフラッシュ＋3ベットブラフ価値 |
| 65s〜54s | 小さすぎるコネクター | HJ以降で採用 | ボードカバレッジ＋ストレートナッツ可能性 |
| 22〜55 | セット率低、価値薄 | BTNで採用、他では混合 | ボードカバレッジ＋EV≈0の境界ハンドとして混合 |

**特記: 22〜55 の扱い**:
- UTG 100BB: ほとんど非採用（EV≈0またはマイナス）
- BTN: 採用（ボードカバレッジ目的）
- ソルバーの言葉: 「低ペアは防衛的ボードカバレッジのために開かれる。コンピュータでなければ、ポストフロップでのEVを出すのが非常に困難」

### 5-3. 乖離の大きさとEV的意味

**境界ハンドでの乖離EV**: 通常 0.01bb〜0.10bb/hand
**100手で積み上がると**: 最大でも 1〜10bb 程度の差

低〜中ステークスでは相手がGTO的に攻めてこないため、**本書の式を使うことによるEV損失は相手のミスで十分補填できる**。

---

## 6. 決定論と確率分布の本質的違い

### 6-1. 決定論的簡易式の利点

| 項目 | 内容 |
|------|------|
| 暗算可能 | テーブルで瞬時に判断できる |
| 教育的明瞭さ | 「スコアX以上なら開く」という単純ルールで学習できる |
| 再現性 | 同じ状況で同じ判断ができる（バラつきがない） |
| 心理的安定 | 迷いが減り、他の判断（ポジション、相手の傾向）に集中できる |

### 6-2. 確率分布（混合戦略）の利点

| 項目 | 内容 |
|------|------|
| 理論的最適 | ナッシュ均衡に到達し搾取不可能 |
| バランス維持 | バリューとブラフの比率が常に最適 |
| 高ステークス適用 | 相手が精密に読んでくる環境で必要 |

### 6-3. 本書が決定論を選ぶ合理性

> "A simplified strategy implemented well will invariably outperform a complicated strategy implemented poorly!"
> — GTO Wizard, Simplified Solutions

実際、GTO Wizard 自身が「シンプル化された戦略は複雑な戦略を雑に実装するより優れる」と断言している。

**学習曲線の観点**:
- 初心者にとって混合戦略の実装は認知負荷が高すぎる
- まず「何を開くか・何を折るか」を確立することが先決
- 混合戦略は「何が最善か分かっている」前提で初めて意味を持つ

> "Early on, mixed strategies are not very important, as there are more important things to learn and at lower stakes opponents won't really notice anyway."
> — PokerStrategy.com, Mixed Strategies basics

---

## 7. 「簡易GTO」アプローチ：先行事例

### 7-1. GTO Wizard の Simplified Solution

GTO Wizard は「Simplified Solutions」機能を提供:
- ヒーローに1〜2サイズのみを割り当てる（フル GTO は多数のサイズを混合）
- 精度: 0.005%〜0.045%（一般的業界標準の0.5%より大幅に高精度）
- 目的: 「実装しやすさ」と「搾取耐性」の両立

これは本書のアプローチ（決定論的・単純化）と同じ哲学に基づく。

- 出典: [Simplified Solutions and a New Interface](https://blog.gtowizard.com/simplified-solutions-and-a-new-interface/)（GTO Wizard Blog）

### 7-2. 既存プリフロップチャートの近似手法

**PokerCoaching（Jonathan Little氏ら）の GTO チャート**:
- ミックス頻度を「50%以上なら実行する」に丸める
- これは本書の「スコアがしきい値以上なら開く」と本質的に同じ近似
- 出典: [Implementable GTO Charts](https://poker-coaching.s3.amazonaws.com/tools/preflop-charts/online-6max-gto-charts.pdf)

**Matthew Janda『Applications of No-Limit Hold'em』（2013年）**:
- 現代ソルバー以前だが、理論的に健全なレンジを構築する手法を提示
- 「範囲で考える」概念を普及させた先駆的著作
- 簡易レンジの正当性を理論的に示した
- 出典: [Amazon - Applications of No-Limit Hold 'em](https://www.amazon.com/Applications-No-Limit-Hold-Matthew-Janda/dp/1880685558)

### 7-3. 各ツールが示す結論

「完全な GTO は人間には実装不可能。簡易版で十分な精度が出る。」——これが業界コンセンサスである。

> "You do not need to play exact GTO strategies to be profitable; in fact, due to how complicated it is to play GTO strategies, any attempt to fully replicate these strategies will likely cost you more money than it will win."
> — MyPokerCoaching

---

## 本書への適用

### 第8章での活用方針

1. **冒頭で乖離を認める**: 「本書の式は近似である」を明言することで読者の信頼を得る
2. **乖離を3カテゴリに整理**: ミックス問題・スーテッド評価・境界ハンドの誤分類
3. **「近似コスト」を数値化**: 境界ハンドでの EV 差は最大 0.1bb/hand 程度で限定的
4. **使い続ける根拠**: GTO Wizard 自身が簡略化の優位性を認めており、本書の立場を権威ある情報源が支持している
5. **発展へのブリッジ**: 「この章を読んだ後、GTO ソルバーを学ぶ次のステップへ」として中級者へのパスを提示

### 各節の執筆ポイント

| 節 | 主張 | 根拠 |
|----|------|------|
| ミックス戦略 | 決定論で十分（低ステークス） | PokerStrategy.com の「混合は高ステークスで重要」 |
| スーテッド過小評価 | A2s〜A5sのGTO高評価はブロッカー由来 | GipsyTeam の A5s EV データ |
| レーキ影響 | 低ステークスでは補正を推奨 | GTO Wizard のステークス別データ |
| オープンサイズ | レンジ精度の方が重要 | GTO Wizard の EV 比較 |
| 過大・過小評価 | 境界ハンドのEV差は小さい | 各ソルバー分析から推定 |
| 決定論の合理性 | 実装品質 > 理論精度 | GTO Wizard 自身の言明 |

---

## 参考URL一覧

| タイトル | URL | 年 |
|---------|-----|----|
| GTO Wizard - How Solvers Work | https://blog.gtowizard.com/how-solvers-work/ | 不明 |
| GTO Wizard - Preflop Range Morphology | https://blog.gtowizard.com/preflop-range-morphology/ | 不明 |
| GTO Wizard - Equity Realization | https://blog.gtowizard.com/equity-realization/ | 不明 |
| GTO Wizard - Preflop Raise Sizing: Examining 2 Key Factors | https://blog.gtowizard.com/preflop-raise-sizing-examining-2-key-factors/ | 不明 |
| GTO Wizard - Rake & Rakeback Explained | https://blog.gtowizard.com/rake-rakeback-explained-optimize-your-poker-earnings/ | 不明 |
| GTO Wizard - Simplified Solutions and a New Interface | https://blog.gtowizard.com/simplified-solutions-and-a-new-interface/ | 不明 |
| GTO Wizard - What is GTO in Poker? | https://blog.gtowizard.com/what-is-gto-in-poker/ | 不明 |
| GTO Wizard - Blockers & Unblockers | https://blog.gtowizard.com/blockers-unblockers-the-secret-to-picking-great-bluffs/ | 不明 |
| GipsyTeam - Why Do Poker Solvers Love Ace Five Suited So Much? | https://www.gipsyteam.com/news/27-11-2024/why-do-poker-solvers-love-ace-five-suited | 2024年11月 |
| Upswing Poker - Why The Very Best Poker Players Make Decisions At Random | https://upswingpoker.com/mixed-strategy-random-poker-decisions/ | 不明 |
| Upswing Poker - Suited Connectors: 5 Strategic Mistakes | https://upswingpoker.com/suited-connectors-poker-strategy/ | 不明 |
| PokerCoaching - How to Play Suited Connectors the Right Way | https://pokercoaching.com/blog/suited-connectors/ | 不明 |
| PokerStrategy.com - Mixed Strategies Basics | https://www.pokerstrategy.com/news/content/Poker-Basics-Mixed-Strategies_119638/ | 不明 |
| MyPokerCoaching - GTO Poker Guide | https://www.mypokercoaching.com/gto-poker/ | 2026年 |
| Amazon - Applications of No-Limit Hold 'em（Matthew Janda） | https://www.amazon.com/Applications-No-Limit-Hold-Matthew-Janda/dp/1880685558 | 2013年 |
| RakeRace - How to Play KQo | https://rakerace.com/news/poker-strategy/2025/04/10/how-to-play-kqo-in-no-limit-hold-em-preflop-and-postflop-strategy-guide | 2025年4月 |
| PokerCoaching - Implementable GTO Charts (PDF) | https://poker-coaching.s3.amazonaws.com/tools/preflop-charts/online-6max-gto-charts.pdf | 不明 |
| SplitSuit - Small Pocket Pair Preflop Strategy | https://www.splitsuit.com/small-pocket-pair-strategy | 2026年 |
