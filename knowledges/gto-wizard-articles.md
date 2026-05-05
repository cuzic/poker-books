# GTO Wizard 記事まとめ

> 収集日: 2026-05-02

GTO Wizard ブログ（https://blog.gtowizard.com/）から、シリーズ各巻の執筆に活用できる記事を収集・整理した。

---

## 巻①：プリフロップ

### [Preflop Range Morphology](https://blog.gtowizard.com/preflop-range-morphology/)
**要点**:
- レンジの形態（モーフォロジー）は「リニア・ポーラード・コンデンスド・マージド」の4種に分類できる
- リニアレンジは top-down の強手で構成され、アグレッシブにベットすべき
- ポーラードレンジはナッツと弱いブラフで構成され、サイズを大きくする戦略が最適
- UTG オープンは 2bb、BTN は 2.5bb、SB は 3bb と、早いポジションほどサイズが小さい（ソルバーの実証）
- 高レーキ環境（NL50）では BTN 4-bet 頻度 39%、低レーキ（NL500）では 31% と、レーキがレンジ構造を変える

**書籍との関連**: 第6章「オープンレンジとサイズ」および第9章「3ベット・4ベット戦略」に活用できる。リニア・ポーラード・マージドの概念整理に使用する。

---

### [Preflop Raise Sizing: Examining 2 Key Factors](https://blog.gtowizard.com/preflop-raise-sizing-examining-2-key-factors/)
**要点**:
- レーキがある環境では、BBはミニレイズに対して**コール頻度が最大 40% 低下**し、3ベット頻度が上がる
- LJ など早いポジションでは AA/KK/AKs のみが 3bb で EV が改善、それ以外は 2bb が有利
- BTN は唯一の例外で、最弱ハンド（J4s、T5s 等）が 3bb でフォールドエクイティを稼ぐ
- 大きなオープンサイズはブラインドに多くフォールドさせる一方、IP プレイヤーにはほぼ追加フォールドが取れない（5〜10% 増しのみ）
- 実戦では「レーキ構造」「相手のコーリングテンダンシー」を加味して調整する必要がある（ソルバー解はあくまで均衡解）

**書籍との関連**: 第4章「オープンサイジングの根拠」に活用できる。なぜポジションによってサイズが異なるかの理論的裏付けになる。

---

### [Crush 3-Bet Pots OOP in Cash Games](https://blog.gtowizard.com/crush-3-bet-pots-oop-in-cash-games/)
**要点**:
- SB は「3ベット or フォールド」をほぼ徹底する（コールすると BBのスクイーズリスク＋OOP の不利が重なる）
- SB の 3ベット後のフロップチェック頻度は 33.9%（IP の 19.7% より大幅に高い）
- ブロードウェイフロップ（KQ2r）では 100% C-ベット、スモールコネクティッドフロップ（654r）ではレンジチェックが最適
- OOP での意思決定フレームワーク：①両レンジの構成 ②ボードが有利な側 ③レンジ全体戦略 ④当該ハンドの具体行動
- BB の 3ベットレンジはバリュー（TT+, AJs+, AQo+）＋コーリングレンジの底部ハンドでブラフを構成する

**書籍との関連**: 第11章「3ベットポットの OOP 戦略」に活用できる。フロップでのレンジチェック vs. C-ベット判断の基準として使用する。

---

## 巻②：フロップ基礎

### [Flop Heuristics: IP C-Betting in Cash Games](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)
**要点**:
- ハイカードフロップ（Kハイ〜8ハイ）は最も C-ベット頻度が高い。ただしエースハイフロップは BB がチェックレイズしやすいため頻度が下がる
- **ペアドボード**：ベット頻度が高く、サイズは小（33%ポット中心）
- **ディスコネクトボード（レインボー）**：最高頻度のベット、33% または 130% のサイズを混在
- **コネクティッドボード**：133% ポットのオーバーベットが最少（相手のフロップストレートを尊重）
- **モノトーンボード**：ベット頻度・サイズとも激減。フラッシュを持っていると相手のコーリングレンジをブロックしてしまい価値が取りにくい

**書籍との関連**: 第3章「C-ベット頻度とサイズの基準」に直接活用できる。ボードテクスチャ別の CBet ヒューリスティックとして章の核心データとなる。

---

### [The Mechanics of C-Bet Sizing](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/)
**要点**:
- サイジングの主要ドライバーは「ナッツアドバンテージ」と「フォールドエクイティの価値」で、レンジアドバンテージはベット頻度を決める
- **ドライボード（QQ6r）**：33% ポット中心。相手がフォールドしても弱いハンドしか落とせず、フォールドエクイティの価値が低い
- **ウェットボード（KJ7r）**：75〜125% のオーバーベット中心。強いハンド（トップペア等）をフォールドさせる価値が高い
- **スーパーウェットボード（QJTr）**：再び 33% 中心。相手もナッツ（ストレート・フラッシュ等）を多く持つため小ベットで価値を抽出しつつ中間ハンドを守る
- 「ウェットネスパラボラ」：乾燥→湿→超湿の三段階で最適サイズが山形に変化する

**書籍との関連**: 第4章「C-ベットサイジングの理論」に活用できる。ドライ・ウェット・スーパーウェットの 3 分類フレームワークが書籍の「ボードスコア」概念と直接対応する。

---

### [The Magic of Equity Buckets](https://blog.gtowizard.com/the-magic-of-equity-buckets/)
**要点**:
- エクイティバケツはハンドを「ベスト（スタックオフ可能）・グッド（バリューベット）・ウィーク（チープショーダウン）・トラッシュ（ブラフのみ）」の4段階に分類する認知フレームワーク
- 詳細版では 90-100% / 50-89% / 25-49% / 0-24% の4区間を使用
- K♦Q♣2♠ では BB が 57.6% のトラッシュハンドを持つため、レンジチェックフォールドパターンが予測できる
- K♦5♠5♣ では BB が 6.8% のナッツ（5-x コンボ）を持つだけで UTG のサイジングを小さくさせる（ナッツアドバンテージの逆転）
- 4段階抽象化ヒエラルキー：レンジ全体形状 → エクイティバケツ → ハンドクラス → 個別コンボ

**書籍との関連**: 第2章「ハンドスコアとレンジ分類」に活用できる。HandScore v2 の「バケツ境界」設計の理論的根拠として参照できる。

---

## 巻③：フロップ応用

### [How and Why You Should Use Turn Donk Bets](https://blog.gtowizard.com/how-and-why-you-should-use-turn-donk-bets/)
**要点**:
- フロップ C-ベットをコールした後、コーラーはアグレッサーと同等以上のエクイティを持つことが多い。これがターンドンクの正当性の源泉
- 有効なドンクターンカード：コーラーのレンジに多いドロー完成カード・低ボードのペアカード・コーラーが強化される 2 ペアカード
- 例：J♠5♣3♦ フロップ後、ターンが 2/3/4/5/6 のときドンクが最多（コーラーのストレート＋ペア完成）
- ドンクレンジは二極構造：ナッツに近いハンド＋薄いワンペアが主体、中間強度ハンドはほぼチェック
- BTN オープンに対するドンク頻度は UTG に比べて大幅に低下（例：18% → 7%）。相手レンジが広いほど優位性が薄れる
- ベットサイズの目安は約 20% ポット（バリュー兼プロテクションを兼ねる）

**書籍との関連**: 第1章「ドンクベットの論理」に直接活用できる。どのターンカードでドンクが有効かの具体的ヒューリスティックとして使用する。

---

### [Round Out Your Defense: The Power of Raising](https://blog.gtowizard.com/round_out_your_defense_the_power_of_raising/)
**要点**（WebSearch の情報を補完）:
- OOP のレイズはレンジを未キャップにし、相手の小ベット戦略を封じるための重要な防御ツール
- レイズレンジが存在することで相手はオートマチックな小ベットを多用できなくなる
- 適切なレイズ頻度を維持することがフロップ/ターンの防御効率を高める

**書籍との関連**: 第3章「フロップレイズと防御戦略」に活用できる。チェックレイズが戦略全体に与える構造的効果の説明に使用する。

---

## 巻④：ターン・リバー基礎

### [Principles of Turn Strategy](https://blog.gtowizard.com/principles-of-turn-strategy/)
**要点**:
- ターンは「ハンドバリューが静的になる」ストリート。フロップと違い、相対的強さが逆転しにくい
- K♠8♥4♦ の例：フロップは全レンジをスモールベット、ターンはチェック多数＋残り約 40% をオーバーベット（二極化）
- ミドルストレングス（トップペア・セカンドペア）はターンでポットコントロールのためチェックが主体
- ストロングハンド（2ペア・セット）はポットを積極的に育てるためベット
- ドローは「フォールドエクイティ vs エクイティリアリゼーション」の二律背反に直面する
- スタックが 20bb の場合：サイズは 50% ポットに圧縮、トップペアもストロング扱いでベット頻度が上がる

**書籍との関連**: 第5章「ターンのバレル判断基準」の核心データとして活用できる。「中間ハンドはチェック、強ハンドはオーバーベット」という二極化ルールの根拠として使用する。

---

### [Principles of River Play](https://blog.gtowizard.com/principles-of-river-play/)
**要点**:
- リバーはハンドバリューが固定され、レンジはポーラード構造（バリューとブラフのみ）に収束する
- バリューベットの必要条件：コールされたとき **50% 以上の勝率** が必要（IP の場合はポーラードレイズリスクを考慮しやや高め）
- OOP のブロッキングベット：相手の大ベットを防ぐため薄くベットできる（チェックすると大ベットを受けるリスク）
- ブラフキャッチャーの選択は手の強さより「ブロッカー構成」が重要。バリューをブロックしてブラフをアンブロックするハンドが最良
- 大ベットの例外：①ブラフの数が不足 ②ブロッカー効果でコール頻度が落ちる ③相手の過剰ブラフを誘う
- 前ストリートのアクション（チェック vs ベット）でリバーのレンジが根本的に変わるため、文脈把握が不可欠

**書籍との関連**: 第8章「リバーのバリューベットとブラフ頻度」に活用できる。α 式（最低要求エクイティ）の理論的裏付けとして直接使用する。

---

### [How To Analyze Turn Textures in Poker](https://blog.gtowizard.com/how-to-analyze-turn-textures-in-poker/)
**要点**:
- ターンテクスチャ分析の基本問い：「何が変わったか？」（どちらのレンジがこのカードで強化されたか）
- 2 つの優位性概念：**エクイティアドバンテージ**（レンジ全体の勝率分布）と **ナッツアドバンテージ**（最強ハンドの偏り）
- K♠8♠7♥ での例：スペードターンは UTG のナッツアドバンテージを削るため小ベット、ブロードウェイターンは UTG がエクイティを増やすため小ベット（より多くのバリューコンボを含む）
- フロップがチェックスルーのときターンドロー完成カードは「予期しないナッツ」として BB に大ベットを与える
- BB は「ナッツアドバンテージを得たターン限定」でドンクベットを使う

**書籍との関連**: 第6章「ターンカード分析とスコア更新」に活用できる。ターンカードごとにレンジの優位性がどう変化するかを分類する際の軸として使用する。

---

## 巻⑤：ターン・リバー応用

### [Understanding Blockers in Poker](https://blog.gtowizard.com/understanding-blockers-in-poker/)
**要点**:
- ブロッカーとは「自分が保有するカードが相手レンジの特定コンボを除外する効果」。その逆はアンブロッカー
- ハンドタイプ別ブロッカー戦略：バリューハンドはトラッシュをブロックしバリューをアンブロック、ブラフはバリューをブロックしトラッシュをアンブロック
- 具体例：T♠9♠ はブラフキャッチャーとして pure fold（9♠ が相手のブラフ K♠9♠, Q♠9♠ をブロックするため）、一方 T♦9♦ は常にコール
- ブロッカーが最も重要な 3 条件：①相手レンジが狭い ②ポーラード化している ③大きなベットサイズ
- ブロッカーは意思決定の第 3 優先事項（①ブラフに勝てるか ②相手の過不足ブラフ頻度 ③ブロッカー構成の順）
- GTO Wizard はブロッカースコア（0〜10）でバリュー除去とトラッシュ除去の影響を数値化している

**書籍との関連**: 第2章「ブロッカーの理論と実践」の理論基盤として活用できる。「いつブロッカーが重要か」の 3 条件が書籍のフレームワークに直接対応する。

---

### [Blockers & Unblockers: The Secret to Picking Great Bluffs](https://blog.gtowizard.com/blockers-unblockers-the-secret-to-picking-great-bluffs/)
**要点**:
- 優良ブラフの原則：「強いハンドをブロックし、フォールドしてほしいハンドをアンブロックする」
- プリフロップ：A5s〜A3s は AA/AK をブロック＋弱いキングやクイーン系をアンブロックするため最良のブラフ候補
- リバー例（A♠9♠6♥5♥2♦）：8♠4♠ や 7♠3♠ がナッツストレートをブロック＋ブロードウェイドロー（K♠Q♠ 等）をアンブロック→ pure bluff
- K8s はブラフとして不適：トラッシュを十分ブロックしていても相手のフォールドハンドをブロックしてしまいコール頻度が 0.5% 増加する
- バリュー除去スコア（高いほど強いハンドをブロック）とトラッシュ除去スコア（低いほどフォールドハンドをアンブロック）の 2 軸で評価
- 「あるプレイヤーにとって悪いアンブロッカーは相手にとって良いアンブロッカー」という相互性がある

**書籍との関連**: 第3章「ブラフ選択とブロッカー活用」に活用できる。プリフロップ〜リバーにかけてのブラフ最適化の具体例として章の事例研究に使用する。

---

### [Range Morphology](https://blog.gtowizard.com/range-morphology/)
**要点**:
- ポストフロップのレンジ形態：キャップド（ナッツなし）vs アンキャップド（ナッツあり）の区別が戦略の基盤
- ポーラードレンジのベット分布：75% 以上エクイティのベストハンド＋33% 未満のトラッシュで構成
- 完全ポーラードレンジの最適サイズはジオメトリックサイジング（各ストリート等比のポット割合）
- マージドレンジは「相手を不利なエクイティポジションに追い込みながら広いレイズ頻度を維持できる」という利点がある
- リニアベットはミドルハンドを過剰インクルードするため相手にシンプルなオーバーフォールドで対応される

**書籍との関連**: 第4章「レンジ形態とナッツ頻度分析」に活用できる。ナッツ頻度（Nut Frequency）がレンジ形態を決め、サイズ選択を規定するという論理チェーンの説明に使用する。

---

## 巻⑥：トーナメント

### [ICM Basics](https://blog.gtowizard.com/icm-basics/)
**要点**:
- ICM は「チップ枚数を賞金エクイティに変換する数学的モデル」（Mason Malmuth が 1987 年にポーカーへ応用）
- キャッシュゲームと違い、チップを 2 倍にしても賞金が 2 倍にはならない（ペイアウト構造の非線形性）
- **1位確率 = 自分のチップ ÷ 全体チップ**（2位以降は再帰計算が必要）
- 3人例（500/300/200 chips、$50/$30/$20 ペイアウト）：コールに必要なエクイティが 37.5%（ポットオッズ）ではなく **47%** になる（12% のリスクプレミアム）
- キーヒューリスティック：バブル付近は狭めにプレイ、ビッグスタックはショートスタックを脅かせる、マージナルスポットは+chipEV でも −$EV になりうる
- ICM の限界：スキル差・ポジション・ブラインド上昇を無視している

**書籍との関連**: 第1章「ICM の基礎と賞金エクイティ計算」の理論根拠として活用できる。ICM equity 計算式と「リスクプレミアム」の導出に直接使用する。

---

### [What is the Bubble Factor in Poker Tournaments?](https://blog.gtowizard.com/what-is-the-bubble-factor-in-poker-tournaments/)
**要点**:
- **バブルファクター（BF）= 負けたときの失う $EV ÷ 勝ったときの得る $EV**
- **コールに必要なエクイティ = BF ÷ (BF + 1)**
- 10人 SNG 例（$500/$300/$200 ペイアウト）：BF = 1.18、コール必要エクイティ = **54%**（キャッシュゲームの 50% より 4% 増）
- バブルファクターの高低：マネーバブル BF 1.6+、ファイナルテーブルバブル BF 1.7+（最高圧力ポイント）
- **スタック別の BF 分布**：中間スタックが最高（最大 1.93）、ビッグスタック・ショートスタックは低い（1.11〜1.47）
- ビッグスタック戦略：中間スタックをターゲット（その中間スタックはショートより先に飛ぶことを恐れる）
- PKO では BF が 1.0 を下回ることもあり（バウンティエクイティがリスクを上回る）

**書籍との関連**: 第3章「バブルファクターとスタック戦略」に直接活用できる。BF 計算式は書籍の「ICM 補正」式の核心であり、スタック別戦略調整の根拠として使用する。

---

### [How ICM Impacts Postflop Strategy](https://blog.gtowizard.com/how-icm-impacts-postflop-strategy/)
**要点**:
- ICM 下でのポストフロップは「Downward Drift」が発生：大ベット → 小ベット、小ベット → チェック/コール、チェック/コール → フォールド にシフト
- カバリングプレイヤーはポジション・レンジ強度に関係なくより積極的にプレイできる（ICM プレッシャーを相手に与えるため）
- 具体例（A♣8♦3♠ フロップ）：ChipEV では BTN が 100% ベット・多様なサイズ、ICM では BTN がほぼ 25% ポットのみ
- ターン（ブランクカード）：ChipEV では BB 100% チェック、ICM では BB が 25% 以上の頻度でドンクベット（カバー側が圧力をかける）
- ICM スポットでは 3ベット頻度がプリフロップ・ポストフロップともに低下する
- サイズを落とすことで「エリミネーションリスクを減らしつつポットを積める」バランスが最適化される

**書籍との関連**: 第5章「トーナメントのポストフロップ調整」に活用できる。ICM がポストフロップ戦略に与える具体的影響（Downward Drift）を解説する際の主要参考記事となる。

---

## 参考：収集した主な記事 URL 一覧

| 巻 | 記事タイトル | URL |
|----|------------|-----|
| ① | Preflop Range Morphology | https://blog.gtowizard.com/preflop-range-morphology/ |
| ① | Preflop Raise Sizing: Examining 2 Key Factors | https://blog.gtowizard.com/preflop-raise-sizing-examining-2-key-factors/ |
| ① | Crush 3-Bet Pots OOP in Cash Games | https://blog.gtowizard.com/crush-3-bet-pots-oop-in-cash-games/ |
| ② | Flop Heuristics: IP C-Betting in Cash Games | https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/ |
| ② | The Mechanics of C-Bet Sizing | https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/ |
| ② | The Magic of Equity Buckets | https://blog.gtowizard.com/the-magic-of-equity-buckets/ |
| ③ | How and Why You Should Use Turn Donk Bets | https://blog.gtowizard.com/how-and-why-you-should-use-turn-donk-bets/ |
| ③ | Round Out Your Defense: The Power of Raising | https://blog.gtowizard.com/round_out_your_defense_the_power_of_raising/ |
| ④ | Principles of Turn Strategy | https://blog.gtowizard.com/principles-of-turn-strategy/ |
| ④ | Principles of River Play | https://blog.gtowizard.com/principles-of-river-play/ |
| ④ | How To Analyze Turn Textures in Poker | https://blog.gtowizard.com/how-to-analyze-turn-textures-in-poker/ |
| ⑤ | Understanding Blockers in Poker | https://blog.gtowizard.com/understanding-blockers-in-poker/ |
| ⑤ | Blockers & Unblockers: The Secret to Picking Great Bluffs | https://blog.gtowizard.com/blockers-unblockers-the-secret-to-picking-great-bluffs/ |
| ⑤ | Range Morphology | https://blog.gtowizard.com/range-morphology/ |
| ⑥ | ICM Basics | https://blog.gtowizard.com/icm-basics/ |
| ⑥ | What is the Bubble Factor in Poker Tournaments? | https://blog.gtowizard.com/what-is-the-bubble-factor-in-poker-tournaments/ |
| ⑥ | How ICM Impacts Postflop Strategy | https://blog.gtowizard.com/how-icm-impacts-postflop-strategy/ |

---

*収集方法：https://blog.gtowizard.com/ の記事一覧ページおよびテーマ別 Web 検索（site:blog.gtowizard.com）により記事を特定し、各記事本文を取得・要約した。*
