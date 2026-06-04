# タイミングテル・サイジングテル

検索日: 2026-04-21

## 概要

ポーカーにおける「テル」とは、相手が意図せず漏らす情報のことを指す。
フロップ上級編において、CBetサイズとアクションのタイミングは最も重要な情報源の一つである。
GTOソルバーが普及した現代でも、多くのプレイヤーは混合戦略を実践できず、サイズ選択に無意識のパターンを持っている。
本章では「サイジングテル」と「タイミングテル」の両軸から、相手の範囲を絞り込む技術を整理する。

---

## 1. サイジングテルの全体像

### なぜサイズに情報が漏れるか

GTOソルバーは複数のベットサイズを確率的に混合する「混合戦略 (mixed strategy)」を採用する。
たとえば同じボードで33%と75%を5:5の比率で使うように指示されても、多くの人間プレイヤーはどちらか一方を固定的に選んでしまう。
この一貫性の欠如こそが、サイジングテルの根本原因である。

**情報漏洩が起きやすい3つの場面**

1. **一貫性の欠如**: 強いハンドには大きく、弱いハンドには小さく打つパターンが染み付いている
2. **混合戦略の不在**: GTOソルバーが指示する頻度ベースの打ち方を人間が再現できない
3. **感情的なベット**: バッドビートの直後、精神的に不安定な状態でサイズが崩れる

**出典**: [The Mechanics of C-Bet Sizing | GTO Wizard](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/)

### サイズ選択の心理 — 「大きく打つ = 強い」の誤解と例外

多くのレクリエーショナルプレイヤーは「強い手を持っているから大きく打つ」という直感的なロジックを持つ。
しかし実戦では、逆のパターンも頻繁に見られる。

| よくある思い込み | 実際の意味 |
|----------------|----------|
| 大きいベット = 強い手 | バリューのこともあればブラフのことも多い（양極化） |
| 小さいベット = 弱い / ブラフ | 保護不要のナッツ、またはポットコントロール |
| 大きいベット = 「コールするな」のメッセージ | 多くの場合「もっとコールしてほしい」の逆説 |

**実戦例1**: ナット優位のドライボード（Ah-7d-2c）でIP側が33%ポットのスモールCBetを打った場合、GTOではこれが最適解である。しかしフィッシュには「小さく打った＝弱い」と映り、フロートやレイズを誘発する。このずれを利用できる。

**実戦例2**: ウェットボード（Jh-Td-9c）でフィッシュが75%以上のオーバーベットを打ってきた場合、多くの場面でセットか二ペアの過剰なバリューベットである。このサイズでブラフを打てるフィッシュはほぼいない。

**出典**: [Bet Sizing Strategy: 8 Rules for Choosing the Perfect Size - Upswing Poker](https://upswingpoker.com/bet-size-strategy-tips-rules/)

---

## 2. CBetサイズ別の示唆

GTOソルバーのアナリシスによると、CBetサイズの選択はナット優位性 (nut advantage) とポット勝率 (fold equity) が主要な決定因子となる。

**出典**: [Flop Heuristics: IP C-Betting in Cash Games | GTO Wizard](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)

### 33%ポット（スモールCBet）

**GTOの本来の意図**
- IP側がナット優位なドライボードでの高頻度小サイズ戦略
- レンジ全体でベットしてポットを積み上げる
- 相手のレンジを広く保ちながら EV を積み上げる

**実戦での典型的なずれ**
- Nit: スモールCBetはほぼ確実にミドルペア以下（チェックに回ったなら続けてプレッシャーをかけられる）
- TAG-fish: ドライボードでのルーティン自動CBet。コールして後のストリートで判断する
- Fish: 意味なく打っている可能性が高い。「しょぼいトップペア」か「完全なミス」のどちらか

**実戦例3**: BTN vs BB のシングルレイズポット、A-7-2 レインボー。BTN が33%を打ってきた場合、GTO的には適切だが、フィッシュの33%CBetはAx全体ではなく「一応打ってみた」程度のハンドが多い。ターンのカードとベット量を見てフロートか否かを決める。

---

### 50%ポット（ミッドCBet）

**GTOの本来の意図**
- 中程度の連結性があるボードでの標準サイズ
- バリューとブラフを程よくミックスできるサイズ

**実戦での典型的なずれ**
- Nit: 50%はNitにとっては「十分に大きい確認ベット」。トップペア以上がほとんど
- TAG: 最も読みにくい。GTOに近い思考をしているTAGは50%を広くミックスする
- LAG: 頻度高くブラフを混ぜているが、このサイズでも価値手とブラフが混在
- Fish: ランダムに50%を打つことが多い。直前のアクション（プリフロップのリム等）と合わせて判断

**実戦例4**: BTN vs CO のシングルレイズポット、K-9-4 モノトーン（CO がフラッシュスーツ保有）。CO が50%を打ってきた。NitならKxかナッツフラッシュドロー。Fishなら何でもあり得る。ここではCOのVPIPとAFを参照する。

---

### 75%ポット（ラージCBet）

**GTOの本来の意図**
- ウェットボード（コネクタ系、両面ストレートドローが存在）での保護ベット
- IP側がレンジ優位かつナット優位な場面でより大きいサイズを採用

**実戦での典型的なずれ**
- Nit: 75%は「ナッツかそれに準じる手」のシグナル。ほぼフォールドでよい
- TAG: ウェットボードではバランスを取ろうとしているが、75%のブラフ比率は低め
- LAG: ブラフが混じるが、75%ならレンジが絞れてきている
- Fish: 「いい手を持っているから大きく打つ」の直感が出やすいサイズ。フィッシュの75%CBetはバリューに偏っている

**実戦例5**: HJ vs BB、Jh-Td-8c フロップ。BB が75%をドンクベット（または HJ が75%CBet）。フィッシュがこのサイズを打つ場合、Jx や Tx のトップペア以上か、強いコンボドロー（OESD+フラッシュドロー等）がほとんど。純粋なブラフはまれ。

**出典**: [C-Betting in Poker – How to Build the Optimal Strategy](https://pokercoaching.com/blog/c-betting-in-poker/), [Sizing Your C-Bets: 3 Factors You Must Consider - Upswing Poker](https://upswingpoker.com/c-bet-sizing-strategy-continuation-bet/)

---

### オーバーベット（100%超）

**GTOの本来の意図**
- ナット優位が非常に高い場面でのみ使用
- 양극화（ナッツ＋ブラフ）したレンジ構成が前提
- リバーでのオーバーベットはナット優位の証明

**実戦での典型的なずれ**
- Nit: オーバーベット = 「コールしてほしくない」シグナル（逆説的だが）。ほぼナッツのみ
- TAG: 計算されたオーバーベットであれば양극化を理解した上での戦略的プレイ
- LAG: 積極的な LAG はブラフオーバーベットも混ぜてくる。過剰反応して降りるのは危険
- Fish: フィッシュのオーバーベットは「強い手が嬉しくて大きく打つ」パターンが圧倒的。ナッツや強いセットがほとんど

**実戦例6**: リバーにフラッシュ完成。フィッシュが2倍ポットのオーバーベット。フィッシュがブラフオーバーベットを打てる確率は低い。この状況ではほぼナッツフラッシュまたはフルハウス。フォールドが正解になる場面が多い。

**実戦例7**: 経験豊富なLAGが一貫してオーバーベットを使ってきた場合。ブラフ含有率が高い可能性がある。ブロッカーの有無（例：Aでナッツフラッシュをブロック）も判断材料に加える。

**出典**: [The Art of the Flop Overbet | GTO Wizard](https://blog.gtowizard.com/the_art_of_the_flop_overbet_and_why_youre_probably_doing_it_wrong/), [Overbet Poker Size | VIP-Grinders](https://www.vip-grinders.com/overbet-poker-size-overbets-correctly/)

---

## 3. サイジングテルの公開データ

### GTO Wizard・Upswing等からの知見

GTO ソルバーは、ナット優位が高い場面でベットサイズを大きくし、レンジ優位（でもナット優位は低い）場面では頻度を高めつつサイズを小さくする傾向を示す。
人間プレイヤーとのズレが生じやすい典型パターンを以下に整理する。

| # | 状況 | GTOの本来の戦略 | 実戦でのズレ（搾取ポイント） |
|---|------|----------------|---------------------------|
| 1 | ドライボード IP CBet | 高頻度スモール（33%） | フィッシュは50-75%でバリュー中心に打つ |
| 2 | ウェットボード IP CBet | 中低頻度ラージ（75%+） | Nitは強い手のみ大きく打つ |
| 3 | ペアボード IP CBet | 高頻度スモール | 多くのプレイヤーがチェックかスモールに偏る |
| 4 | 3ベットポット IP CBet | 大きい（67-100%）も選択肢 | TAG-fishはトップペア以上でのみ大きく打つ |
| 5 | OOP CBet ドライ | ミックス（チェック多い） | Nitはチェックが多く、強い手のみ打つ |
| 6 | OOP CBet ウェット | スモールチェックレイズ保留 | Fishは「打てばいい」と大きく打つ |
| 7 | ターン二枚目のバレル | 강化（ラージ） | 弱いプレイヤーはターンでサイズを落とす |
| 8 | リバーバリューベット | 相手のコール範囲に合わせたサイズ | フィッシュは「もっともらおう」で大きくなりすぎる |
| 9 | リバーブラフ | 適切なブロッカーを持つ手で打つ | フィッシュはリバーブラフをほとんど打たない |
| 10 | オーバーベット | 양극化レンジ（ナッツ＋ブラフ） | フィッシュのオーバーベットはほぼナッツのみ |
| 11 | チェックレイズ | バリュー：ブラフ = 適切比率 | Nitのチェックレイズは強い手のみ |
| 12 | スモールレイズ（ミニレイズ） | 一部ボードで最適 | 多くのフィッシュが「様子見」でミニレイズ |

**出典**: [The Five Imbalances of Exploitative Poker | GTO Wizard](https://blog.gtowizard.com/the-five-imbalances-of-exploitative-poker/), [Poker Patterns Explained | Pokerology](https://www.pokerology.com/poker/strategy/reading-betting-patterns/)

---

## 4. タイミングテル（オンライン）

オンラインポーカーでは物理的なボディランゲージは観察できないが、アクションの速さ（タイミング）が重要な情報源となる。

### インスタントベット（即時ベット）

**観察されるパターン**

- チェックアクションがクリックされた直後、ほぼ遅延なしにベットが来る
- 時間バンクをほとんど使わない

**意味の解釈**

インスタントベットは「事前に決断を済ませていた」ことを示す。これには2つの場合がある：

1. **事前決定ブラフ**: 「フロップが来たらどんなカードでも打つ」と決めていた。CBetブラフの一形態
2. **強い手での自動的な価値ベット**: 強い手を持ち、躊躇する理由がない

マルチテーブルをしているプレイヤーや、他のテーブルの操作をしながら決断している場合も「インスタント」になりやすい。

**実戦例8（オンライン）**: フロップで相手がインスタントCBet（33%）を打ってきた。この場合、相手が深く考えずに自動的にCBetしている可能性が高い。ターンでカードが変化して相手のベット頻度が落ちるか観察する。頻度が落ちればオートパイロットのCBetだったと確認できる。

### 長考後のベット（ディレイドベット）

**観察されるパターン**

- 通常のアクション時間を大幅に超える
- 時間バンクを使う
- その後に大きいベットやレイズが来ることが多い

**意味の解釈**

長考後のベット（特にレイズ）は「難しい判断をしている」または「逆を突こうとしている」を示す。

- 強い手でのスロープレイから「そろそろ打つか」の決断
- ブラフで「降りてもらえるか」を計算中
- 相手のリアクションを観察してから判断

一般的に、平均的なプレイヤーの場合、長考後の大きいベット/レイズは強い手を示すことが多い。

**実戦例9（オンライン）**: ターンで相手がタイムバンクをフルに使って2倍ポットオーバーベットを打ってきた。レクリエーショナルプレイヤーの場合、これはほぼ確実にナッツに近い手。正解はフォールド。経験豊富なプレイヤーの場合は、ブラフの可能性も考慮する。

### インスタントコール（即時コール）

**観察されるパターン**

- ベットに対してすぐにコール
- 全くの躊躇なし

**意味の解釈**

インスタントコールはしばしば「ドローを持っているが降りる気はない」「マージナルハンドでコール判断が楽」のどちらかを示す。

- フラッシュドローやストレートドロー：オッズが合うためすぐにコール
- ミドルペア以上のフロート：「まあコールしておこう」の自動判断
- 強いがナッツでない手：レイズするほどではないが確実にコール

**実戦例10（オンライン）**: フロップでインスタントコール→ターンでインスタントコール→リバーでチェック。この連続したインスタントコールはドロー（フラッシュかストレート）を持ちながら最終的にミスったパターンが多い。リバーで相手がベットしてきた場合は逆に強い。

### 長考後のコール（ディレイドコール）

**観察されるパターン**

- かなりの時間を費やしてからコール
- しぶしぶ感がある

**意味の解釈**

長考後のコールは「降りるかコールするかを迷った末のコール」を示す。

- 損切り思考：「ここまで払ったから（サンクコスト）コールしよう」
- オッズを計算した上でのタイトなコール
- 「この手でコールするのは正しいのか」を何度も自問している状態

このタイプのプレイヤーはターン・リバーで追加のバレルが効きやすい。

**出典**: [Poker Timing Tells and Betting Patterns | BlackRain79](https://www.blackrain79.com/2014/10/online-poker-timing-tells-and-betting.html), [Timing Tells in Online Poker | PokerArticles Blog](https://www.pokerarticles.blog/timing-tells-in-online-poker-how-to-read-and-use-timing-tells-in-online-poker-to-gain-insight-into-opponents-hands/), [The Hidden Power of Timing Tells | poker.academy](https://poker.academy/blog/post/the-hidden-power-of-timing-tells)

---

## 5. タイミングテル（ライブ）

ライブポーカーでは、オンラインに比べてはるかに多くの非言語情報が得られる。
ただし、物理的なテルは個人差が大きく、単独の観察では過信は禁物である。

### ボディランゲージ研究の概要

**Zachary Elwood の研究**

Zachary Elwoodは『Reading Poker Tells』をはじめとする三部作で、ライブポーカーにおける行動分析の体系的な手法を提示した。同著は8か国語に翻訳され、48,000部以上の販売実績を持つ（2025年時点）。
Elwoodの主な知見は対面ゲームが中心だが、タイミングやサイジングテルについてはオンラインにも応用可能な内容も含まれる。

**出典**: [Reading Poker Tells | readingpokertells.com](https://www.readingpokertells.com/), [Zachary Elwood | GipsyTeam](https://www.gipsyteam.com/poker/players/zachary-elwood)

**Joe Navarro の研究**

元FBI対敵情報工作員のJoe Navarroは2006年に『Read 'Em and Reap』（Phil Hellmuthとの共著）を出版。25年の行動分析の知見をポーカーに応用した。
続編『200 Poker Tells』では200種類の観察可能なテルをまとめた。

**出典**: [Joe Navarro Poker Tells | navarropoker.com](http://www.navarropoker.com/), [Chicago Poker Club | Joe Navarro](https://chicagopokerclub.net/blog-posts/strategy-discussion/219-joe-navarro-learning-to-read-poker-tells.html)

---

### ポットへの視線とチップへの視線

**行動パターン**

- フロップ公開後に素早くチップへ視線を落とす
- ポットを「値踏み」するように凝視する

**意味の解釈**

フロップや新しいコミュニティカードを見た直後にチップへ素早く視線を移す行動は、潜在意識的に「ベットしたい」という意欲を示す。脳が価値を感じると、資源（チップ）への注意が増すためと考えられている。

- フロップ後のチップ注視 → 強いハンドを持った可能性が高い
- ポットを長く見つめる → 「どのくらい取れるか」を計算中のバリューハンド

**実戦例11（ライブ）**: AKスートのハイカードボード（A-K-7）で相手がフロップを見た後に素早くチップに目を向けた。このシグナルがある場合、Ax または Kx を持っている可能性が上がる。こちらのブラフを控えるべきシグナルとなる。

**出典**: [Poker Tells & Chip Behavior | bluffingmonkeys.com](https://bluffingmonkeys.com/the-secret-language-of-poker-what-your-chips-and-face-really-say/), [Common Poker Tells | PokerNews](https://www.pokernews.com/strategy/10-hold-em-tips-5-common-poker-tells-to-look-for-25433.htm)

---

### チップ操作のパターン

**Joe Navarroが注目した行動**

- **チップへの手の接触**: フロップ後に自然な形でチップに触れる → ベット意欲あり（強い手）
- **カードシャッフル（カードシャトル）**: 親指と中指でカードを繰り返し横に動かす → フォールドを検討中
- **チップを積む/崩す**: 落ち着きなくチップを操作 → 不安や迷い

**行動の解釈上の注意**

個人によって「習慣的な癖」として行う場合もあるため、その人の平常時の行動（ベースライン）を把握した上で解釈する必要がある。

**実戦例12（ライブ）**: 大きいポットで相手がベット前にチップを整然と積み直す行動をとった。この行動が普段見られないものであれば、何かを「準備している」サインである可能性がある。強い手でのバリューベット準備の場合が多い。

**出典**: [Joe Navarro Poker Tells | navarropoker.com](http://www.navarropoker.com/)

---

### 呼吸のパターン

**観察される行動**

- ベット後に深い呼吸をする（ため息的な呼吸）
- 重要な場面で呼吸が浅くなる、または止まる
- 大きいベットを宣言した後の呼吸変化

**意味の解釈**

呼吸は意識的にコントロールするのが難しいため、比較的信頼性が高いテルとされる。

- ベット後の大きな呼吸（安堵の吐息）→ ブラフで「通れ」という緊張の解放
- 呼吸が止まる → 結果に強い関心がある（バリューかブラフか状況依存）
- 声が震える / かすれる → 強い興奮状態（ナッツ or 緊張したブラフ）

**実戦例13（ライブ）**: 相手がリバーでオーバーベットを宣言した直後に大きく息を吐いた。これが普段見られない行動であれば、ブラフで緊張から解放された可能性がある。コールの方向で検討する価値がある。

**出典**: [Body Language in Poker | 888poker](https://www.888poker.com/magazine/strategy/body-language-in-poker), [Reading Poker Faces | justpokertables.com](https://www.justpokertables.com/blogs/news/reading-poker-faces-understanding-tells-and-body-language)

---

### 微小表情と顔の反応

**観察される行動**

- フロップ公開の瞬間に0.5秒以下で表れる顔の変化
- 唇の片側が上がる（满足）または下がる（失望）
- 瞬きの増減

**意味の解釈**

微小表情は意識的なコントロールが難しく、一瞬だけ本当の感情が漏れる現象である。ポーカーでフロップを見た瞬間の反応が最も観察しやすい。

ただし、微小表情の読み取りには高度なスキルと注意深い観察が必要であり、日常的に使える技術として習得するには長期の練習が必要である。初心者はまずチップ注視やタイミングなどより観察しやすいテルに集中すべきである。

**出典**: [Understanding Poker Tells | pokerology.com](https://www.pokerology.com/poker/psychology/tells/)

---

### ライブ vs. オンラインの差異

| 観察できる情報 | ライブ | オンライン |
|--------------|--------|----------|
| ボディランゲージ | あり | なし |
| タイミング | 概算のみ | 秒単位で正確 |
| チップ操作 | あり | なし |
| 呼吸・微小表情 | あり | なし |
| ベットサイズパターン | あり | あり（HUDで追跡可） |
| 言語的テル | あり | なし（チャットのみ） |

ライブポーカーはテルの種類が豊富だが、オンラインはタイミングとサイジングのデータをHUDで蓄積・分析しやすいという利点がある。
戦略の中心は常にレンジシンキングとGTOベースの判断であり、テルはその補助情報として活用する。

---

## 6. テルの活用上の注意

### サンプル数の問題

**1〜2回の観察では過信しない**

1セッションで相手のテルを「確認した」と思っても、それは偶然である可能性が高い。
テルを統計的に意味のある情報として活用するには、複数回の観察と、ショーダウンによる裏付けが必要である。

| 観察回数 | 信頼性の目安 |
|---------|-----------|
| 1〜2回 | 参考程度（50%程度の信頼性） |
| 3〜5回 | 一定の根拠（ショーダウン確認があれば有効） |
| 5回以上（ショーダウン含む） | 比較的信頼できるパターン |

**実戦例14**: 相手が2回続けて「長考後にフォールド」したからといって、その相手が常にそうするとは限らない。それが習慣的な行動か、その場の特殊な状況によるものかを区別するには、さらなる観察が必要である。

**出典**: [Understanding Poker Tells | Pokerology](https://www.pokerology.com/poker/psychology/tells/), [Poker Tells | CoinPoker](https://coinpoker.com/strategy/live/poker-tells/)

---

### 逆利用（自分がテルを出していないか）

**自己テルの確認**

相手のテルを読む前に、まず自分のアクションパターンを振り返ることが重要である。

**よくある自己テル**

- 強い手のときだけCBetサイズを大きくしている
- ブラフのときにアクションが速い（迷いがない）
- 大きいポットで呼吸が変わる、チップに触れる

**改善方法**

- 全てのハンドで同じ時間をかけてアクションする習慣をつける
- ベットサイズのランダム化（同じ状況で複数のサイズを使い分ける）
- ライブでは常に同じ姿勢・表情を保つ練習をする

**実戦例15**: 自分が3ベットポットでIPからCBetを打つとき、「バリューのときは75%、ブラフのときは33%」という一定のパターンになっていないか確認する。このパターンがあると、相手に搾取される。

---

### メタゲーム（相手が逆を突いてくる）

**逆テル（Reverse Tell）の概念**

逆テルとは、相手が「テルを知った上で意図的に反対の行動を取る」戦略である。
経験豊富なプレイヤー相手では、テルの解釈を逆にする必要が出てくることがある。

**出典**: [What is a Reverse Tell in Poker? | Adda52](https://www.adda52.com/poker/reverse-tell-in-poker), [Understanding What is Reverse Tells | fortunegames.com](https://www.fortunegames.com/blog/understanding-what-is-reverse-tells-in-poker)

**メタゲームの階層**

| レベル | 思考 |
|-------|-----|
| レベル0 | 自分の手を見る |
| レベル1 | 相手の手を推測する |
| レベル2 | 相手が自分の手について何を思っているかを推測する |
| レベル3 | 相手がレベル2の思考を知っていることを前提に行動する |

テルを活用したメタゲームは、相手のレベルを正確に把握した上でのみ有効である。
初心者相手にメタゲームを仕掛けても、相手がそもそもテルを意識していなければ逆効果になる。

**実戦例16**: ベテランプレイヤーが「弱そうに見せかけてチップをぞんざいに扱う」動作をしてきた。この行動が意図的な逆テルである可能性を考慮する。ナビゲーションとして「このプレイヤーはどのレベルで思考しているか」を常に意識する。

**出典**: [Exploiting the Poker Metagame | GGPoker](https://ggpoker.com/blog/exploiting-the-poker-metagame/), [Poker Metagame Guide | Blue Lake Casino](https://www.bluelakecasino.com/poker-metagame/)

---

### テルの位置付け：補助情報として活用する

テルは単独で「コールすべきかフォールドすべきか」を決める根拠にはならない。
あくまでもレンジシンキング、ポットオッズ、ポジション、ボードテクスチャーといった一次的な判断の補助として活用するものである。

**テル活用の優先順位**

1. レンジシンキング（必須）
2. ポットオッズ・エクイティ（必須）
3. 相手の統計（VPIP / PFR / AF など）（重要）
4. ベットパターン・サイジングテル（有益）
5. タイミングテル（有益）
6. ライブのボディランゲージ（補助）

テルは補助情報の一つであり、「テルがあるから」という理由だけで数学的に明らかに誤ったプレイをすることは避ける。

---

## 本書（巻3 第III部）への適用

- **第14章「タイミングテル・サイジングテル」** の核心素材として本ファイルを使用
- セクション1・2はCBetサイジングの章（第6章・フロップ）との連携で深化
- セクション4はオンラインプレイヤー向けの実践的な読み方として独立コラム化を検討
- セクション5のライブテルは「ライブで勝つための補足」として巻末付録にも流用可
- セクション6（注意事項）は毎章の「まとめ」に共通して挿入できる原則として使用

---

## 著作権に関する注意事項

- **Zachary Elwood 著作**: 引用は「概念・考え方の要約」にとどめること。具体的な表現・図表は直接引用しない。
- **Joe Navarro 著作**: 同上。「元FBI捜査官の知見」として概念のみ参照すること。
- **GTO Wizard Blog**: パブリックに公開された記事だが、図・表の転載は避け、概念の説明に引用URLを併記すること。
- **Upswing Poker**: 商業的なコンテンツへのリンクは出典として明示するにとどめること。

Sources:
- [The Mechanics of C-Bet Sizing | GTO Wizard](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/)
- [Flop Heuristics: IP C-Betting in Cash Games | GTO Wizard](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)
- [The Art of the Flop Overbet | GTO Wizard](https://blog.gtowizard.com/the_art_of_the_flop_overbet_and_why_youre_probably_doing_it_wrong/)
- [The Five Imbalances of Exploitative Poker | GTO Wizard](https://blog.gtowizard.com/the-five-imbalances-of-exploitative-poker/)
- [Dynamic Sizing: A GTO Breakthrough | GTO Wizard](https://blog.gtowizard.com/dynamic-sizing-a-gto-breakthrough/)
- [Sizing Your C-Bets: 3 Factors You Must Consider | Upswing Poker](https://upswingpoker.com/c-bet-sizing-strategy-continuation-bet/)
- [Bet Sizing Strategy: 8 Rules | Upswing Poker](https://upswingpoker.com/bet-size-strategy-tips-rules/)
- [Reading Poker Tells | Zachary Elwood](https://www.readingpokertells.com/)
- [Zachary Elwood | GipsyTeam](https://www.gipsyteam.com/poker/players/zachary-elwood)
- [Joe Navarro Poker Tells | navarropoker.com](http://www.navarropoker.com/)
- [Poker Timing Tells and Betting Patterns | BlackRain79](https://www.blackrain79.com/2014/10/online-poker-timing-tells-and-betting.html)
- [The Hidden Power of Timing Tells | poker.academy](https://poker.academy/blog/post/the-hidden-power-of-timing-tells)
- [Timing Tells in Online Poker | PokerArticles Blog](https://www.pokerarticles.blog/timing-tells-in-online-poker-how-to-read-and-use-timing-tells-in-online-poker-to-gain-insight-into-opponents-hands/)
- [Poker Tells & Chip Behavior | bluffingmonkeys.com](https://bluffingmonkeys.com/the-secret-language-of-poker-what-your-chips-and-face-really-say/)
- [Common Poker Tells | PokerNews](https://www.pokernews.com/strategy/10-hold-em-tips-5-common-poker-tells-to-look-for-25433.htm)
- [Body Language in Poker | 888poker](https://www.888poker.com/magazine/strategy/body-language-in-poker)
- [What is a Reverse Tell in Poker? | Adda52](https://www.adda52.com/poker/reverse-tell-in-poker)
- [Exploiting the Poker Metagame | GGPoker](https://ggpoker.com/blog/exploiting-the-poker-metagame/)
