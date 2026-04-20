# SBとBBの特殊性：ブラインドポジションの戦略

検索日: 2026-04-19

## 概要

SB（スモールブラインド）とBB（ビッグブラインド）は、ポーカーにおいて最も戦略的に複雑なポジションである。SBはアクション上のポジション不利（常にアウトオブポジション）とBBスクイーズリスクを抱え、BBはポットオッズの恩恵を受けつつもポジション不利という相反する特性を持つ。現代GTOソルバーはこれらの特性を精密に反映したレンジを提示する。

---

## 1. SB戦略の基本

### 1-1. 3betかフォールドが基本となる理由

SBは他のプレイヤーからのオープンレイズに対して、コールよりも3bet-or-foldが推奨される。理由は構造的である。

**スクイーズリスク**
- SBがコールすると、BBがまだアクションを持つ
- BBはSBのコールレンジがキャップされていることを知っており、広いレンジでスクイーズしやすくなる
- スクイーズを受けると、SBのコールレンジは最悪のポジションで難しいスポットに追い込まれる

**エクイティ実現率の低さ**
- SBはポストフロップで常にOOP（アウトオブポジション）でプレイする
- フォールド以外の全てのストリートで先にアクションしなければならない
- 例えば27%のエクイティを持つハンドでも、実際には22%程度しか実現できないケースがある
- コールは「ポジション不利で範囲が限定されたまま、難しいフロップ後のプレイを余儀なくされる」（出典: PokerCoaching）

**イニシアティブの重要性**
- 3betすることでイニシアティブを取り戻し、相手の範囲を絞り、SPR（スタック対ポット比）を低下させる
- フロップ前にポットを取れる可能性が生まれる

ソルバーは「ビッグブラインド以外の全ポジションで3bet-or-foldを推奨する」（出典: Upswing Poker）。

### 1-2. GTO推奨：コールド・コール約7%、3bet約8%

GTOソルバーの解では、SBの典型的なプリフロップアクション分布は以下のようになる（6max, 100bb, vsボタンオープン例）。

| アクション | 頻度（目安） |
|-----------|------------|
| フォールド | 約85% |
| コールド・コール | 約7% |
| 3bet | 約8% |

**コールが存在する理由**
- BBは既に1BBを投資しており、最後のアクション権を持つ（マルチウェイポットのリスクなし）
- SBはBBと比較してコールレンジが大幅に狭い
- ソルバーはSBのコールを「ほぼ排除」する傾向があり、3bet cold callの頻度は0.14%程度に過ぎない（出典: GTOBase Blog）
- コールが残るのは、非常にポット勝率の高い特定のハンドに限られる

**注意**: 具体的な数値はレーキ、オープンサイズ、相手ポジションにより変動する。7%/8%はあくまで目安であり、要確認。

### 1-3. SBコンプリートNG・リンプ対応

**キャッシュゲームでのSBコンプリート（リンプ）**

6maxキャッシュゲームの100bb標準設定では、SBのオープンリンプはGTOソルバーでほぼ採用されない。理由は以下の通り。

- リンプするとBBが安くフォールドでき、ブラインドスチールの機会を逃す
- 1BBのみをポットに加えた状態でOOPにさらされる
- BBのオプションにより自由にポットをコントロールされる

**BBのリンプ対応（SBがリンプしてきた場合）**

BBはSBのリンプに対して：
- 広いレンジでレイズ（アイソレーション）を選択できる
- SBリンプレンジはキャップされており、BBが強いハンドでオーバーコールする必要はない
- BBのチェック頻度よりSBのリンプレンジの方が強い傾向（SBはプレミアムをトラップ目的でリンプすることがある）

### 1-4. SB vs BTN の 3bet-or-fold

BTNはオープン頻度が最も高い（約42%）ポジション。SBはBTNのオープンに対して特に積極的な3betが求められる。

**SB vs BTN の構造的特徴**
- BTNが最も広くオープンするため、ブラフ3betの期待値が高い
- SBはBTNに対してほぼコールを持たない（「SBはBTNオープンに対してほとんどコールしない」 出典: GTOBase）
- 3betのサイズは標準的にオープンの3x〜4x（OOP時は大きめ）

**SB vs BTN の3betレンジ例（100bb, 6max）**

バリューレンジ:
- AA, KK, QQ, JJ, TT（純粋3bet）
- AKs, AKo, AQs, AJs（高頻度3bet）

ブラフレンジ（マージドレンジの一部）:
- A8o〜A9o（ボーダーライン、混合戦略）
- KTo, K9o（スーテッドの場合高頻度）
- スーテッドコネクター（Q9s, J8s等、フォールドエクイティと形成力を持つ）

---

## 2. BBディフェンス戦略

### 2-1. BBディフェンスレンジ（MDF視点）

**MDFの基本計算**

MDF（最小ディフェンス頻度）= ポット ÷ (ベット + ポット)

または: MDF = 1 ÷ (s + 1)（s = ベット/ポット比）

| ベットサイズ | MDF |
|------------|-----|
| 1/3ポット | 75% |
| 1/2ポット | 67% |
| 2/3ポット | 60% |
| 3/4ポット | 57% |
| ポット | 50% |
| 1.5倍ポット | 40% |

**MDFの重要な誤解**
- MDFはフォールドエクイティを0にするための理論値
- 実際のBBプリフロップディフェンス頻度はMDFそのものではない
- 「ソルバーはBBがMDFよりも広くディフェンスする場合があることを示している」（出典: GTO Wizard blog, MDF & Alpha）
- ポストフロップのエクイティ実現率や相手のcbet頻度によって最適頻度は変動する

### 2-2. 広いBBディフェンスの根拠（ポットオッズが良い）

BBが広くディフェンスできる最大の理由はポットオッズである。

**ポットオッズ計算例（BTN 2.5bbオープン）**

- ポット: SB(0.5) + BB(1) + BTN(2.5) = 4bb
- BBのコールコスト: 1.5bb
- ポットオッズ: 1.5 ÷ (4 + 1.5) = 約27%のエクイティ必要
- つまりBBは「27%以上のエクイティがあれば理論上コール可能」

**BBの独自アドバンテージ**
- 既に1BB投資済み（割引でコールできる）
- 最後のアクション権（BBのみ再オープン可能）
- マルチウェイポットのリスクが低い（コールはヘッズアップになる）
- SBがフォールドしていれば相手はBTN1人のみ

出典: [Poker Blind Strategy: Defending Your Blinds | Jurojin Poker](https://jurojinpoker.com/poker-course/poker-for-beginners/poker-blind)

### 2-3. ただし実現率低下（エクイティ実現の問題）

BBは「広くディフェンスできる」が「全てのハンドを同等に実現できる」わけではない。

**エクイティ実現率（EQ実現率）の問題**
- BBはポストフロップで常にOOP
- 相手はIPでフロップのチェックバック権を持つ
- ブラフには強く（防御しなければ搾取される）、バリューベットには弱い（コールしなければ損）
- OOPではポットコントロールが難しく、エクイティ実現率が下がる

**具体的な影響**
- 第10章（エクイティ実現）と連動する概念
- スーテッドコネクターはIPより実現率が20〜30%低下することもある
- ハイカードのブロードウェイハンドは実現率が相対的に高い

出典: [Raise Your Edge: How to Defend Your Big Blind](https://www.raiseyouredge.com/how-to-defend-your-big-blind-5-tips)

---

## 3. 現代GTOでのSBリンプ採用

### 3-1. SBが一定頻度でリンプする場面

現代GTOでは特定の条件下でSBリンプが最適戦略として登場する。

**100bb 6maxキャッシュゲーム**
- 純粋な3bet-or-foldが主流
- リンプはほぼGTOソルバーで採用されない
- 「SBのオープンはリンプなし（no limp）」が標準設定（出典: GTOBase Blog）

**MTT（トーナメント）でのSBリンプ登場条件**
- GTOソルバーはMTTの特定スポットでリンプを採用
- 特にアンテがある場合、ポットオッズが改善されるためリンプの価値が変化
- 「アンテ付きトーナメントでは、必要エクイティが約36%から28.5%に低下」（出典: Upswing Poker）

### 3-2. 浅いスタックやHU（ヘッズアップ）でのリンプ採用

**浅いスタック（20〜25bb）**

スタックが浅くなると、SBリンプが戦略の一部として登場する。

- 約25bb: A9oはリンプ65%、レイズ3.3x約25%、オールイン約10%という混合戦略
- 約20bb: リンプが選択肢として存在（特定のハンドで有効）
- 約14bb: 明確なリンプレンジが形成される（GTO Wizard ソルバーデータ）

**リンプが有効な理由（浅いスタック）**
1. より広いレンジをプレイできる（A4s, 55等の限界ハンドを含められる）
2. 3betされるリスク低下: オープン2bbなら相手は4.5bbを獲得できるが、リンプなら3.5bbに減少し、3betショブの収益性が低下する
3. ポット拡大なしにフロップを見られる

出典: [How Stack Sizes Change Your Range | GTO Wizard](https://blog.gtowizard.com/how-stack-sizes-change-your-range/)

**ヘッズアップ（HU）**
- HUでのSBはBTN兼任であり、全ポジション中で最も有利
- HU GTOソルバーはSBリンプを相当頻度で採用する
- GTO Wizard AI HU Preflop Solverがこれらを解析（出典: GTO Wizard Blog）

出典: [Isolating Limpers in Short Stack HU | GTO Wizard](https://blog.gtowizard.com/isolating_limpers_in_short_stack_hu/)

---

## 4. vs BTN オープンの SBレンジ

**SB vs BTN の状況整理**
- BTNのオープン頻度: 約42%（最も広い）
- SBのアクション: ほぼ3bet-or-fold（コールは限定的）

**SB 3betレンジ vs BTN オープン（100bb, 6max）**

バリュー（純粋3bet）:
- TT, JJ, QQ, KK, AA
- AQs+, AKo

準バリュー〜ブラフ（混合戦略）:
- 99（混合）
- AJs, ATs（高頻度3bet）
- A8o, A9o（ブランケット・混合）
- KQo（中頻度）
- スーテッドギャッパー（T8s, 97s等、一部採用）

**重要**: GTO推奨は「マージドレンジ」に近く、非常に強いハンドから中程度のハンドまで混合される（出典: Upswing Poker, 3-bet strategy）

出典: [SB vs BTN standard GTO calling range | Run It Once](https://www.runitonce.com/nlhe/sb-vs-btn-standard-gto-calling-range-compering-to-poker-snowie/)

---

## 5. vs UTG、MP、CO オープンの BBレンジ

### BBのポジション別ディフェンス頻度

BBのディフェンス頻度は相手のオープンポジションによって大きく異なる。

| オープンポジション | 相手オープン率（目安） | BB推奨ディフェンス頻度（キャッシュ） |
|----------------|----------------------|--------------------------------------|
| UTG | 約14〜17% | 約17〜20%（非常にタイト） |
| MP | 約18〜22% | 約25〜30% |
| CO | 約25〜28% | 約35〜38% |
| BTN | 約40〜42% | 約38〜40%（2.5bbオープン時） |

**根拠**
- UTGは最も狭くオープンするため（約14〜17%）、BBのコールは不利
- 「キャッシュゲームでUTGオープン対応時、正しいディフェンスレンジはわずか17%」（出典: PokerCoaching.com）
- 「トーナメントではUTGオープンに対してもレンジの40%近くでディフェンスする」（同）
- BTNのオープンに対して2.5bb時、「BBは40%未満でディフェンス」（出典: PokerCoaching.com）

出典:
- [Early Position Bets Facing The Big Blind | PokerCoaching](https://pokercoaching.com/blog/early-position-bets-facing-the-big-blind/)
- [How To Defend From The BB: GTO-Approved! | YouTube](https://www.youtube.com/watch?v=3VM6zNRkkMU)

### BBのコールレンジ構成（ポジション別の変化）

**vs UTG（超タイト）**
- 相手レンジ: TT+, AQs+, AKo, KQs等（約14〜17%）
- BBのコールレンジ: ブロードウェイ系、スーテッドの中〜高コネクター
- A3o, K2oなどのウィーカーハンドはフォールド推奨

**vs BTN（広い）**
- 相手レンジ: 約40〜42%（非常に広い）
- BBのコールレンジ: A3o, K2oなどのオフスーツでもコール可能になる
- 「レートポジション（CO/BTN）のオープンには、A3oやK2oなどのオフスーツでも広くディフェンスできる」（出典: Raise Your Edge）
- スーテッドワンギャッパー（T8s, 97s等）が有効なブラフ3bet素材になる

**3bet頻度**
- BBはSBと異なり、コールレンジが広いため3betレンジはより選別される
- vs UTG: 3bet約3〜5%（バリューのみ）
- vs BTN: 3bet約6〜8%（バリュー＋ブラフ）

---

## 6. ブラインドスチール率の目安

### スチール成功率の基準

**ポジション別スチール期待値**
- BTNからのスチール: 最も有利。SB+BBが共にフォールドする確率 = SB折り率 × BB折り率
- COからのスチール: BTNより条件が悪い（BTNが残っている）
- SBからのスチール: 1BBのみ獲得できるが、OOPになるリスクが高い

**SB/BBのFold to Steal率（マイクロ〜スモールステークス目安）**

| ポジション | 平均的Fold to Steal率 |
|-----------|----------------------|
| SB | 約70〜90% |
| BB | 約60〜80% |
| SB + BB 合計 | 約72%（例: SB 90% × BB 80%） |

「マイクロリミットでSBは90%、BBは80%折る」（出典: MyHoldemPokerTips）

**スチール成功率と採算性**

| 採算ライン | 条件 |
|-----------|------|
| 2倍ポットベット（4xオープン） | 折り率75%以上が必要 |
| ミニレイズ（2xオープン） | 折り率30%以上で利益 |
| 各成功スチール | 約1.5BBの純利益 |

「2回のブラインドスチール成功は、100ハンドでブレイクイーブンとの差を生む」（出典: MyHoldemPokerTips）

**適切なスチール範囲の調整**

| 相手のFold to Steal率 | 推奨スチール範囲 |
|----------------------|----------------|
| 65%以上 | ほぼ全ての2カードでスチール可能 |
| 65〜85% | 上位40%のハンド |
| 55〜65% | 上位30%のハンド |

出典:
- [Poker HUD Stat: Stealing Blinds | MyHoldemPokerTips](https://www.myholdempokertips.com/hud-stats-stealing-blinds)
- [Blind Stealing Guide | Poker Copilot](https://pokercopilot.com/blindstealingguide)
- [ATS in Poker | GipsyTeam](https://www.gipsyteam.com/poker/ats-in-poker)

---

## 7. まとめ：SBとBBの根本的違い

| 比較項目 | SB | BB |
|---------|----|----|
| 投資額 | 0.5BB | 1BB |
| ポストフロップのポジション | 常にOOP（最悪） | OOP（でも2番目に行動） |
| 標準戦略 | 3bet-or-fold | コール許容（広いレンジ） |
| オープンリンプ | 原則NG（100bb/6max） | 関係なし（BBはリンプできない） |
| ディフェンス幅 | 非常に狭い（約15〜16%合計） | 比較的広い（vs BTN 40%前後） |
| スクイーズリスク | 高い | 低い（最後のアクション権） |

---

## 本書への適用

- **第15章「SBとBBの特殊性」**: この調査の全内容が直接適用可能
  - 3bet-or-fold原則とその理由（スクイーズ・エクイティ実現）
  - MDFの計算とBBポットオッズの優位性
  - ポジション別のBBディフェンス頻度（UTG vs BTN）
  - 浅いスタック・MTTでのSBリンプの例外
  - ブラインドスチール率の目安と対策
- **第10章「エクイティ実現率」との連動**: OOPでのエクイティ実現率低下を相互参照
- **第12章「3betスコア」との連動**: SBからの3betレンジの算定に活用

---

## 出典一覧

- [Upswing Poker: Small Blind Strategy Tips](https://upswingpoker.com/small-blind-poker-strategy-tips/) (2024)
- [Upswing Poker: 3-Bet Preflop Strategy & Range Charts](https://upswingpoker.com/3-bet-strategy-aggressive-preflop/) (2024)
- [GTO Wizard Blog: MDF & Alpha](https://blog.gtowizard.com/mdf-alpha/) (2024)
- [GTO Wizard Blog: Heads Up - Exploiting SB's Preflop Mistakes](https://blog.gtowizard.com/heads-up-exploiting-sbs-preflop-mistakes/) (2024)
- [GTO Wizard Blog: Playing Limped Pots as the SB in MTTs](https://blog.gtowizard.com/playing-limped-pots-as-sb-in-mtts/) (2024)
- [GTO Wizard Blog: How Stack Sizes Change Your Range](https://blog.gtowizard.com/how-stack-sizes-change-your-range/) (2024)
- [GTO Wizard Blog: Isolating Limpers in Short Stack HU](https://blog.gtowizard.com/isolating_limpers_in_short_stack_hu/) (2024)
- [GTOBase Blog: Overview of GTO Solutions in the 6-max Cash Library](https://blog.gtobase.com/theory/overview-of-the-new-gto-poker-solutions-in-the-6-max-cash-library/) (2024)
- [PokerCoaching: Small Blind Strategy When Facing a Raise](https://pokercoaching.com/blog/small-blind-strategy-when-facing-a-raise/) (2024)
- [PokerCoaching: Early Position Bets Facing The Big Blind](https://pokercoaching.com/blog/early-position-bets-facing-the-big-blind/) (2024)
- [PokerCoaching: MDF Poker](https://pokercoaching.com/blog/mdf-poker/) (2024)
- [Upswing Poker: MDF vs No MDF](https://upswingpoker.com/mdf-vs-no/) (2024)
- [Raise Your Edge: How to Defend Your Big Blind](https://www.raiseyouredge.com/how-to-defend-your-big-blind-5-tips) (2024)
- [Run It Once: SB vs BTN standard GTO calling range](https://www.runitonce.com/nlhe/sb-vs-btn-standard-gto-calling-range-compering-to-poker-snowie/) (2024)
- [888 Poker: The Ultimate Guide for Small Blind](https://www.888poker.com/magazine/strategy/small-blind) (2024)
- [MyHoldemPokerTips: Poker HUD Stat Stealing Blinds](https://www.myholdempokertips.com/hud-stats-stealing-blinds) (2024)
- [Poker Copilot: Blind Stealing Guide](https://pokercopilot.com/blindstealingguide) (2024)
- [GipsyTeam: ATS in Poker](https://www.gipsyteam.com/poker/ats-in-poker) (2024)
- [Jurojin Poker: Poker Blind Strategy](https://jurojinpoker.com/poker-course/poker-for-beginners/poker-blind) (2024)
- [GTO Wizard Glossary: MDF](https://pages.gtowizard.com/glossary/minimum-defense-frequency-mdf/) (2024)
