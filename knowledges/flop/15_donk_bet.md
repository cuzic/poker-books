# ドンクベット対応（第15章「フロップ編」向け軽量化リサーチ）

検索日: 2026-04-20

---

## 概要

ドンクベット（donk bet）とは、OOP（アウト・オブ・ポジション）側がプリフロップレイザーより先にフロップでベットするアクションである。
本稿は「自分がドンクする戦略」ではなく、**打たれた時の対応**に焦点を絞ってまとめる。

---

## 主要な知見

### 1. ドンクベットの定義

- プリフロップコーラー（OOP）がプリフロップレイザーへチェックせずに先にベットすること。
- 用語の由来は英語の「donkey（ロバ）」＝愚かなベット、という皮肉から。ただし現代 GTO では一部ボードで理論上正当化される。
- 典型例：BTN オープン → BB コール → フロップで BB が先にベット。
- 出典: [What is a Donk Bet? | PokerCode Blog](https://www.pokercode.com/blog/donk-bet) （2024）

---

### 2. なぜ一般的に推奨されないか

| 問題点 | 説明 |
|--------|------|
| イニシアチブ放棄 | プリフロップアグレッサーが持つ「アグレッション」の優位を自ら相手に移す |
| レンジが読まれやすい | バランスを取ることが極めて難しく、エクイティの高い手に偏るためエクスプロイトされやすい |
| 次のアクション情報を献上 | 相手はレンジ情報を得てフォールド/コール/レイズを最適化できる |
| EV損失リスク | 下手なドンクベットで失う EV は、チェックで失うわずかな EV をはるかに上回る |

- 出典: [How to Deal with Donk Betting | PokerCoaching](https://pokercoaching.com/blog/donk-betting/) （2024）
- 出典: [ドンクベットとは？ダメな理由を解説 | PokerAcademy](https://pokeracademy.jp/donk-bet/) （2024）

---

### 3. 現代 GTO での扱い

GTO ソルバーはすべてのボードでチェックするよう指示するわけではない。以下の条件が揃う局面では**ドンクレンジが存在する**。

**ドンクが GTO 上許容される 3 条件（GTO Wizard 分析）**

1. 両プレイヤーのエクイティがほぼ拮抗し、プリフロップレイザーのCベット頻度が低下する
2. ボードがダイナミックで、ターン以降にエクイティが大きく変動しうる（プロテクション価値が高い）
3. BB（OOP 側）がナッツアドバンテージを保有する

**具体的なソルバー頻度例（GTO Wizard）**

| ボード | ドンクベット頻度（BB vs BTN/UTG） |
|--------|----------------------------------|
| 764 レインボー（20bb MTT） | ~60〜70%（近接レンジの大部分がドンク）|
| 654r / 754r / 543r 系 | 高頻度（ストレート可能性が豊富）|
| T85 / 987ss 系 | 中程度（コネクター・スート次第）|
| JT9r / AK7 系 | ほぼ 0%（ハイカードボードはレイザー優位）|
| **全ボード平均** | **約 2%**（集中はほぼローコネクター専用）|

- 出典: [Is Donk Betting for Donkeys? | GTO Wizard Blog](https://blog.gtowizard.com/is-donk-betting-for-donkeys/) （2024）
- 出典: [Should You Ever Donk-Bet On The Flop? | Upswing Poker](https://upswingpoker.com/donk-bet-lead-flop-strategy/) （2024）

---

### 4. ドンクが起こりやすい状況

**ボードテクスチャーの傾向**

- **ローボード（5〜9 ハイ）**: 6♠5♦4♣ のような最低位のコネクターボードでドンク頻度最大
- **コネクターボード**: ストレート完成・ドロー豊富（例: 8♦7♣5♣、9♦8♥6♣）
- **BB のナッツアドバンテージ確保ボード**: セット、ツーペア、ストレートが BB レンジに多く含まれるが レイザーには少ないボード

**スタック深度の影響**

- 100bb 深い場合はソルバーのドンク頻度がシャローの約 1/3 に低下
- スタック浅い（20bb MTT）ほどドンクが増える傾向

- 出典: [Is Donk Betting for Donkeys? | GTO Wizard Blog](https://blog.gtowizard.com/is-donk-betting-for-donkeys/) （2024）
- 出典: [ドンクベット再考――GTO と実戦が交わる戦略 | Taiga Poker Researcher on note](https://note.com/taiga_pkr/n/n68ac988336d8) （2024）

---

### 5. 打たれた時の対応（プリフロップレイザー視点）

#### 基本フレームワーク

| アクション | 条件 |
|-----------|------|
| **レイズ** | TP 強キッカー以上（ナッツドロー込みセミブラフも可） |
| **コール** | TP 〜中程度のドロー（ショーダウンバリューあり） |
| **フォールド** | 完全ミス・ボードに絡まない手 |

#### GTO Wizard の知見（ターンを含む一般化）

- 相手のドンクベットサイズが**小（〜1/4 ポット）**の場合: MDF（最小防御頻度）が高く、非常に広いレンジでコールすべき。Ace-high や King-high すら多くのケースでフォールドすべきでない。
- 相手のドンクベットサイズが**大（1/2 ポット以上）**の場合: ポーラーなレンジを示しているため、弱い手をフォールドしつつバリューハンドでレイズ頻度を上げる。
- レイズすると相手がフォールドエクイティを得るため、強いハンドでレイズすることでポットを大きくできる。
- 出典: [How to Defend Against Turn Donk Bets | GTO Wizard Blog](https://blog.gtowizard.com/how-to-defend-against-turn-donk-bets/) （2024）

#### 本書 HandScore 基準への対応案

| HandScore | 推奨アクション | 理由 |
|-----------|---------------|------|
| 20 以上（セット、ツーペア、TP 強キッカー+ドロー等） | **レイズ（2.5〜3x）** | ドンクレンジに強く、ポットを大きくする価値がある |
| 12〜19（TP 弱キッカー〜中程度ドロー） | **コール** | ショーダウンバリューあり、ただし相手のレンジに対しては不利 |
| 12 未満（ボード不絡み、弱オーバーカード等） | **フォールド** | 相手ドンクレンジには不利、フォールドが最善 |

---

### 6. 相手タイプ別対応

#### レクリエーションプレイヤーがドンクした場合

- **特徴**: バランスされたドンクレンジを持っていない。バリューヘビー（セット・ツーペア・フラッシュ）か、単純なドロー（中ストレートドロー・フラッシュドロー）のどちらかに偏る。
- **対応**: TP 以上でのレイズは有効。ただしボードが低くてコネクトしている場合（例: 987）は慎重に——相手がセット/ストレートを持っている確率が高い。
- **ほぼブラフでない**: 「レクリエーションはブラフしてドンクしない」が基本仮定。相手のドンクを「ほぼバリュー」として処理するのが安全。
- 出典: [How to Deal with Donk Betting | PokerCoaching](https://pokercoaching.com/blog/donk-betting/) （2024）

#### レギュラープレイヤー（GTO 志向）がドンクした場合

- **特徴**: 特定ボードで意図的にバランスされたレンジでドンクしている可能性がある。
- **対応**: ボード依存で判断する。ローコネクターボードで中程度サイズのドンクなら相手のレンジ戦略を考慮し、MDF を守りながらコール。レンジアドバンテージがある場合（ハイボードなど）はレイズで圧力をかける。
- 出典: [Is Donk Betting for Donkeys? | GTO Wizard Blog](https://blog.gtowizard.com/is-donk-betting-for-donkeys/) （2024）

---

### 7. フロップでドンクされた後の相手の典型ハンド構成

| 相手タイプ | 典型ハンド |
|-----------|-----------|
| レクリエーション | セット、ツーペア、トップペア、強フラッシュドロー（バリュー偏重） |
| GTO 志向レギュラー | セット〜TP 強 + セミブラフ（ストレートドロー、フラッシュドロー）のミックス |
| 下手なプレイヤー | 弱いペア、ミドルペア、単純なドロー（ドロー牽制目的）|

---

## 本書への適用（第15章「フロップ編」）

### 活用ポイント

1. **定義の提示**: 「ドンクベット＝OOP が先にベット」を一文で説明し、レクリエーションに多いアクションであることを示す。

2. **判断フロー（ドンクされた場合）**:
   ```
   ドンクベットを受けた
   ↓
   ハンドスコアを確認
   ├─ 20以上 → レイズ（バリュー/セミブラフレイズ）
   ├─ 12〜19 → コール
   └─ 12未満 → フォールド
   ```

3. **相手タイプの簡易識別**:
   - 初見・レクリエーション → バリューヘビーとして扱う（フォールドしすぎない、セット可能性を尊重）
   - レギュラー → ボードに応じてMDF考慮

4. **"GTO にもドンクは存在する" 豆知識**: ローコネクターボード（987ss、765r など）でBBがドンクするのは実は GTO 上も自然であることを一言補足すると、読者の「なんでドンクするんだ？」という疑問を解消できる。

5. **注意喚起**: ドンクされるとパニックしやすい初心者向けに「慌ててオールインしない」「相手レンジを読む」ことを強調。

### 推奨配置

- 第15章「フロップでよく直面するアクション」セクション内に「ドンクベットへの対応」として 400〜600 字程度で記載。
- ハンドスコア判断フローと相手タイプ別対応表を組み合わせたシンプルな図解が有効。

---

## 参考文献一覧

| タイトル | URL | 発行年 |
|----------|-----|-------|
| Is Donk Betting for Donkeys? | [GTO Wizard Blog](https://blog.gtowizard.com/is-donk-betting-for-donkeys/) | 2024 |
| How to Defend Against Turn Donk Bets | [GTO Wizard Blog](https://blog.gtowizard.com/how-to-defend-against-turn-donk-bets/) | 2024 |
| Responding to Donk-Bets at Final Tables | [GTO Wizard Blog](https://blog.gtowizard.com/responding-to-donk-bets-at-final-tables/) | 2024 |
| Exploiting BBs Who Never Donk-Bet | [GTO Wizard Blog](https://blog.gtowizard.com/exploiting-bbs-who-never-donk-bet/) | 2024 |
| Should You Ever Donk-Bet On The Flop? | [Upswing Poker](https://upswingpoker.com/donk-bet-lead-flop-strategy/) | 2024 |
| How to Deal with Donk Betting | [PokerCoaching Blog](https://pokercoaching.com/blog/donk-betting/) | 2024 |
| What is a Donk Bet? | [PokerCode Blog](https://www.pokercode.com/blog/donk-bet) | 2024 |
| ドンクベットとは？ダメな理由や対策を解説 | [PokerAcademy](https://pokeracademy.jp/donk-bet/) | 2024 |
| ドンクベット再考――GTO と実戦が交わる戦略 | [note: Taiga Poker Researcher](https://note.com/taiga_pkr/n/n68ac988336d8) | 2024 |
| Using GTO Strategy Solutions to Adapt to Wonky Donk Bets | [888poker Magazine](https://www.888poker.com/magazine/strategy/adapting-gto-strategy-donk-bets) | 2024 |
