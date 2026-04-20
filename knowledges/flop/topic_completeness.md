# フロップ戦略の主要トピック体系化

検索日: 2026-04-19

---

## 全トピック一覧（初級/中級/上級の分類）

### 凡例

- 初級 = ゼロから始める初心者が最初に学ぶべきもの
- 中級 = 基礎を踏まえた上で学ぶもの（本書のゴールライン付近）
- 上級 = ソルバー習熟・エクスプロイト精度が求められるもの

---

### A. ボードリーディング系

| トピック | レベル | 概要 |
|---------|--------|------|
| ボードテクスチャ分類（ドライ/ウェット） | 初級 | ドロー可能性の多さでボードを分類。Aハイドライ vs. 連続スーテッドの差 |
| フラッシュドロー・ストレートドローの認識 | 初級 | フロップ上の危険なドロー枚数を読む |
| ペアードボード vs. レインボー vs. モノトーン | 初級 | 3分類で覚えるボードの形 |
| コネクテッド vs. ディスコネクテッド | 初級 | ストレートドローの有無でCBet頻度が変わる |
| ターンカードによるボード変化（ランアウト） | 中級 | ターンが前ストリートの有利/不利を変える方向性 |
| フラッシュコンプリート/ストレートコンプリート | 中級 | ドローが完成する「脅威カード」の特定 |

### B. エクイティ計算系

| トピック | レベル | 概要 |
|---------|--------|------|
| アウツのカウント | 初級 | フラッシュドロー9枚、OESD 8枚など代表値を暗記 |
| Rule of 2 and 4 | 初級 | フロップ：アウツ×4、ターン：アウツ×2 でパーセント概算 |
| ポットオッズとの比較 | 初級 | 「オッズがあるか」を Rule of 2/4 × ポットオッズで判断 |
| コンボドロー（フラッシュ＋ストレート） | 中級 | 15アウツ級コンボドローの扱い。Rule of 4 の過大評価補正 |
| インプライドオッズ | 中級 | コールが損でも「将来稼げる額」で補正する概念 |
| エクイティリアライゼーション（EQR） | 上級 | EQR = EV / (ポット × エクイティ)。IP では過実現、OOP では過小実現 |

### C. CBet（継続ベット）系

| トピック | レベル | 概要 |
|---------|--------|------|
| CBetの定義と目的 | 初級 | PFRがフロップでベットする行為。2/3のフロップは相手に刺さらない |
| CBetサイジング（1/3 / 1/2 / 2/3 / フルポット） | 初級 | ドライボード→小サイズ、ウェットボード→大サイズの基本則 |
| CBet頻度（打つべき状況・避ける状況） | 初級 | ポジション、ボード、レンジアドバンテージで判断 |
| IP（インポジション）CBet | 初級 | レンジベットが有効なドライボードの条件 |
| OOP（アウトオブポジション）CBet | 中級 | OOP では頻度を下げ、強い手に絞る傾向 |
| レンジベット vs. マージナルベット | 中級 | ドライ高カードボードでレンジ全体を小サイズで打つ戦術 |
| ダブルバレル（2ストリート連続ベット）の伏線 | 中級 | フロップでベットしたあとターンでも打ち続ける際の選択肢を意識 |
| Delayed CBet（チェックバック後のターンベット） | 中級 | フロップでチェックバックしてターンで攻める戦術 |

### D. ディフェンス・カウンタープレー系

| トピック | レベル | 概要 |
|---------|--------|------|
| コール vs. フォールド vs. レイズの3択 | 初級 | フロップの基本的な意思決定フロー |
| チェックレイズ（OOP からの反撃） | 中級 | 強い手とブラフを混ぜる。サイジングは相手CBetの3倍が基本 |
| MDF（最低防衛頻度） | 中級 | MDF = 1 - 1/(1＋ポットオッズ比)。過剰フォールドを防ぐ下限値 |
| フロート（ブラフコール → ターンで奪取） | 中級 | IP でバックドアエクイティ付きのコール。次ストリートで奪取 |
| ドンクベット（OOP からアグレッサーへのリード） | 中級 | 本来は弱者のプレー。ただし特定ボードでGTO的に有効なケースもある |
| Probe Bet（チェックバック後に OOP からリード） | 中級 | 相手が見せた「弱さ」のサイン（チェックバック）を突く |

### E. レンジ・アドバンテージ系

| トピック | レベル | 概要 |
|---------|--------|------|
| レンジアドバンテージ | 初級〜中級 | PFR側がフロップで有利なレンジを持つ状況を認識する |
| ナッツアドバンテージ | 中級 | 最強手（ナッツ）の組み合わせ数で有利な側が大きく打てる |
| プリフロップからのレンジキャリーオーバー | 中級 | PFR/コーラーの典型的レンジがフロップでどう変化するかのイメージ |
| 3-betポット vs. シングルレイズドポット（SRP） | 中級〜上級 | 3-betポットはレンジが狭く、SPRが低く、戦略が変わる |

### F. SPR・コミットメント系

| トピック | レベル | 概要 |
|---------|--------|------|
| SPR（スタック・トゥ・ポット比） | 初級〜中級 | SPR ≤ 3でトップペアクラスでもコミット。SPR高いと多様な戦略が必要 |
| コミットメントしきい値 | 中級 | 「もはやフォールドできない」SPR水準の判断 |

### G. マルチウェイ特殊性

| トピック | レベル | 概要 |
|---------|--------|------|
| マルチウェイでのベット頻度削減 | 初級〜中級 | プレイヤー数が増えるほど相手の強い手確率が上がる |
| マルチウェイのサイジング（小〜中サイズ推奨） | 中級 | ヘッズアップと違い、フルポットベットはまずしない |
| レンジベット禁止の原則 | 中級 | マルチウェイでは「全レンジベット」が崩壊する |

### H. その他高度トピック

| トピック | レベル | 概要 |
|---------|--------|------|
| オーバーベット（ポット超え） | 上級 | ナッツアドバンテージが高い局面での偏ったレンジ使用 |
| ブロッカーを使ったブラフ選択 | 上級 | 相手のコール組み合わせを「ブロック」する手を選んでブラフ |
| ソルバーフリクエンシー（混合戦略） | 上級 | ソルバーが70%ベット/30%チェックを推奨する混合戦略 |
| フリーカード戦術（セミブラフレイズでターンを無料化） | 上級 | IP でドロー手をレイズして次ストリートを安くする古典戦術 |

---

## 初級者向け必須 10 項目

本書「第6章：フロップ」として、これだけ教えれば読者が実戦で迷わない最重要 10 項目。

### 1. ボードテクスチャの3分類（ドライ / ウェット / ペアード）

- 判断基準：フロップのドロー可能性（フラッシュ・ストレート）と高カードの有無
- 実用価値：CBet判断の出発点になる最重要フレーム
- 教え方：具体例3枚セットで「これはドライ/ウェット」と分類練習

### 2. アウツのカウントと Rule of 2 and 4

- フラッシュドロー＝9枚、OESD＝8枚、グットショット＝4枚を暗記
- フロップ：×4、ターン：×2 で完成確率を秒で計算
- 使用場面：「ドローなら追うべきか」を判断するすべての場面

### 3. ポットオッズとの比較（コールか否か）

- 「オッズが合う / 合わない」の1行判断
- Rule of 2/4 で出した%とポットオッズ%を比較するだけ
- これがなければドロー時の全コールが勘になる

### 4. CBetの基本（打つべき状況・止まる状況）

- 打つ：ドライボード、IP、ナッツアドバンテージあり
- 止まる：マルチウェイ、ウェットで相手レンジ有利、完全ブランク手
- 頻度の目安：IP × ドライなら高頻度、OOP × ウェットなら低頻度

### 5. CBetサイジング（小 / 中 / 大の使い分け）

- ドライ × IP → 33%（レンジベット）
- 湿 × ナッツあり → 66〜75%
- 「ドライは小、ウェットは大」の一行ルール
- 出典：GTO Wizard Flop Heuristics では paired/disconnected で33%が最頻値

### 6. SPR（スタック・トゥ・ポット比）の基礎

- SPR = 実効スタック ÷ フロップポット
- SPR ≤ 3：トップペア以上でコミット可
- SPR 6〜10：セット・ツーペア以上でないと危険
- 実用価値：「どこまで戦えるか」を数字で把握できる

### 7. IP（インポジション）の優位性

- ポストフロップで後から行動できる情報上の優位
- IP では EQR が 100%超え（つまり実際の EV > 生エクイティ）になりやすい
- 「ポジションがある＝薄い手でもコールできる」の直感を教える

### 8. レンジアドバンテージの直感

- 「PFRは A・K 系に強い」「コーラーは中低カードに強い」などのパターン
- 「このフロップは自分のレンジ有利か相手か」を直感で当てる練習
- 数式不要で感覚論から入れる

### 9. マルチウェイでの慎重さ（ベット頻度を下げる）

- プレイヤーが増えるほど強い手に当たる確率が上がる
- ヘッズアップで良いCBetでも、3wayでは危険
- 「相手が2人以上いるときはベットを絞る」の一行ルールで十分

### 10. コール / フォールド / レイズの3択基準

- 強い手 → レイズ（バリュー or プロテクション）
- 合うオッズのドロー → コール
- 合わないオッズ + 何もない手 → フォールド
- チェックレイズへの入り口としても使える意思決定ツリー

---

## 初級者には不要なトピック

「教えたくなるが複雑化を招く」ため、本書では触れないか脚注に留めるもの。

### 1. MDF（最低防衛頻度）の計算式

- 概念は使えるが、「fold frequency < 1/(1+ベット/ポット)」を暗記させるのは過負荷
- 代替案：「相手が毎回ブラフなら折れてはいけない」の感覚論で十分
- 数式は第11章（確率とオッズ）の補足欄で紹介にとどめる

### 2. ドンクベット・Probe bet の活用法

- 初級者がドンクベットを多用すると線が薄くなる
- まず「チェックして相手のアクションを見る」という受身の正しさを教える
- Probe は中級者向けの攻撃オプション

### 3. フロートプレー（ブラフコール → ターン奪取）

- 理解すべき概念だが、実行には「いつ諦めるか」の感覚が必要
- 初級者は単純コールと混同し、あらゆる手でフロートしがち
- 「バックドアエクイティがあるとき限定」の条件を正確に教えられないなら避ける

### 4. 3-betポットの特殊戦略

- SPRが低く、レンジが狭い特殊状況
- まずSRPをマスターしてから
- 3-betポストフロップは本書第15章（GTO）の範囲

### 5. オーバーベット（ポット超え）

- ナッツアドバンテージ・ポラライズドレンジの理解が前提
- 初級者が使うと「強い手がバレる」かつ「ブラフも高コスト」になる
- 上級者の武器として第15章で言及するにとどめる

### 6. ソルバーの混合戦略（ミックスフリクエンシー）

- 「70%ベット/30%チェック」のような確率的行動
- 初級者には「まず純粋戦略で判断基準を固める」方が優先
- 混合戦略は搾取されにくくするための上位概念

### 7. ブロッカーを使ったブラフ選択

- 「Aブロッカーを持っているからナッツブラフに最適」のような推論
- 組み合わせ数の理解が前提。初級者には抽象的すぎる
- 第12章（レンジ思考）の応用編として扱う

### 8. エクイティリアライゼーション（EQR）の数値計算

- 概念（IPで多く実現、OOPで少ない）は教えてよい
- しかし EQR = EV / (ポット × エクイティ) を手計算させるのは不要
- 感覚として「OOPはエクイティを割引く」で十分

---

## 既存の数式アプローチ（先行事例）

### Chen Formula（Bill Chen）

- **対象**: プリフロップ起動手評価のみ
- **内容**: 高い方のカード×2 + 低い方×1 ＋ スーテッド(+8) ＋ コネクター(+8) ＋ ペア補正
- **フロップ版は存在しない**: 調査した限り、Chen Formulaのフロップ拡張は公式に存在しない
- **出典**: [The Chen Formula | thepokerbank.com](https://www.thepokerbank.com/strategy/basic/starting-hand-selection/chen-formula/)

### IHR（Immediate Hand Rank）/ 7cHR

- **提唱者**: Darse Billings ほか（Alberta大学グループ）
- **内容**: IHR = (ahead + tied/2) / (ahead + tied + behind) でハンドエクイティを計算
- **7cHR**: リバーまで全カードを展開して平均アウトカムを計算
- **評価**: ソルバーの原型。「暗算」には向かない
- **出典**: [A Tool for the Direct Assessment of Poker Decisions - Alberta](https://poker.cs.ualberta.ca/publications/divat-icgaj.pdf)

### Rule of 2 and 4（暗算可能な唯一の公式）

- **内容**: アウツ × 4（フロップ）、アウツ × 2（ターン）
- **精度**: 10アウツ以下で誤差2%以内。10アウツ超で過大評価
- **補正式**: アウツが10以上の場合、アウツ × 3 + 9 の方が精度高い（拡張Rule）
- **評価**: 初級者が実戦で暗算できる唯一実用的な式
- **出典**: [Rule of 2 and 4 - thepokerbank.com](https://www.thepokerbank.com/strategy/mathematics/pot-odds/4-2/)、[Extending the 2/4 Rule - Medium](https://medium.com/@alexfiliakov/math-of-poker-extending-the-2-4-rule-9222de9645b7)

### GTO Wizard フロップヒューリスティック

- **対象**: ソルバー解析結果を人間が使えるルールに変換
- **主要知見**:
  - Paired/disconnected board → 33%サイズのレンジベットが最頻
  - Wet dynamic board → 66%以上の大サイズを選択的に使用
  - OOP C-bet はフロップでほぼ高頻度/低頻度の2択で運用
- **評価**: 「暗算できる式」ではなく「パターン辞書」。初級者には記憶コストが高い
- **出典**: [Flop Heuristics: IP C-Betting in Cash Games | GTO Wizard](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)

### ボードスコア / ハンドスコアの先行事例

- **調査結果**: 「ボードスコアを計算してEVを出す式」は商業出版・学術問わず確立されていない
- **近い試み**:
  - SplitSuit の「Flop Texture Tool」は1,755通りのフロップを12カテゴリに圧縮（ツール形式）
  - RedChip Poker では「フロップテクスチャ分類フレームワーク」を教授
  - いずれも「暗算できるスコア式」ではなくカテゴリ分類
- **結論**: **フロップ版Chenフォーミュラは存在しない**。ポストフロップはプリフロップより変数が多く、単一スコア式に還元できないというのが現在の通説

---

## 本書への適用

| 項目 | 章・節での活用方法 |
|------|------------------|
| ボードテクスチャ分類 | 第6章の冒頭フレームワーク。3分類×具体例で視覚化 |
| Rule of 2 and 4 | 第6章 or 第11章（確率とオッズ）で「実戦計算ツール」として紹介 |
| CBetの基本と頻度 | 第6章のメインコンテンツ。ドライ/ウェット × IP/OOP の2×2マトリクスで整理 |
| SPR | 第6章の「どこまで戦えるか」コーナー or 第10章（ベットサイズ理論）で補強 |
| レンジアドバンテージ | 第12章（レンジ思考）の導線として第6章で感覚的に紹介 |
| マルチウェイ | 第6章末尾のコラム or 注記として「3人以上いるときは慎重に」 |
| チェックレイズ | 第6章の「ディフェンス」節に入れるか、第8章（リバー）側で詳述 |
| フロート・Probe・ドンクベット | 第7章（ターン）の「中級者向け発展」節に移す |

---

## 参考URL一覧

- [Flop Heuristics: IP C-Betting in Cash Games | GTO Wizard](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)
- [Flop Heuristics: OOP C-Betting in MTTs | GTO Wizard](https://blog.gtowizard.com/flop-heuristics-oop-c-betting-in-mtts/)
- [When To Continuation Bet | Flop Texture Examples | thepokerbank](https://www.thepokerbank.com/strategy/plays/continuation-bet/when/)
- [Continuation Bet | How To Use The Continuation Bet | thepokerbank](https://www.thepokerbank.com/strategy/plays/continuation-bet/)
- [Check Raise Poker Strategy | PokerVIP](https://www.pokervip.com/strategy-articles/texas-hold-em-no-limit-intermediate/check-raise-poker-strategy)
- [Rule of 2 and 4 - thepokerbank](https://www.thepokerbank.com/strategy/mathematics/pot-odds/4-2/)
- [Rule of 2 and 4 - PokerStars School](https://www.pokerstarsschool.com/lessons/the-rule-of-two-and-four/)
- [Extending the 2/4 Rule | Medium](https://medium.com/@alexfiliakov/math-of-poker-extending-the-2-4-rule-9222de9645b7)
- [Equity Realization | GTO Wizard](https://blog.gtowizard.com/equity-realization/)
- [Equity Realization | Red Chip Poker](https://redchippoker.com/equity-realization/)
- [What is Delayed C-Bet | Upswing Poker](https://upswingpoker.com/delayed-continuation-bet-c-bet-strategy/)
- [Delayed C-Betting | GTO Wizard](https://blog.gtowizard.com/delayed-c-betting/)
- [Float - Poker Definition | 888poker](https://www.888poker.com/magazine/poker-terms/float)
- [10 Tips for Multiway Pots | GTO Wizard](https://blog.gtowizard.com/10-tips-multiway-pots-in-poker/)
- [When Should You Bet the Flop in Multi-Way Pots? | Upswing Poker](https://upswingpoker.com/multiway-pots-flop-bet-strategy/)
- [The Art of the Flop Overbet | GTO Wizard](https://blog.gtowizard.com/the_art_of_the_flop_overbet_and_why_youre_probably_doing_it_wrong/)
- [The Chen Formula | thepokerbank](https://www.thepokerbank.com/strategy/basic/starting-hand-selection/chen-formula/)
- [A Tool for the Direct Assessment of Poker Decisions | Alberta University](https://poker.cs.ualberta.ca/publications/divat-icgaj.pdf)
- [Flop Textures: Reading & Reacting to the Board | Red Chip Poker](https://redchippoker.com/flop-textures-reading-reacting-board/)
- [Overbetting The Flop in Cash Games | GTO Wizard](https://blog.gtowizard.com/overbetting-the-flop-in-cash-games/)
- [Poker Odds Calculator | PokerNews](https://www.pokernews.com/poker-tools/poker-odds-calculator.htm)
- [Beginner Poker Strategy Articles | Upswing Poker](https://upswingpoker.com/beginner-poker-strategy-articles/)
