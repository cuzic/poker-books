# 第23章「20問ドリル：3秒でフロップ判断」問題ネタ集

検索日: 2026-04-20

## 概要

フロップ判断ドリル20問の設計素材。GTO Wizard・Upswing Poker・888poker等のソルバーベース研究から
典型シチュエーションを抽出し、推奨アクションと理由を整理した。

---

## 問題素材一覧

### 問題1：TPTK on ドライボード（CBet 75%）

| 項目 | 内容 |
|------|------|
| ポジション | BTN（IP） |
| プリフロップ | BTN RFI → BB コール |
| ハンド | A♠K♦ |
| ボード | A♥7♣2♦（レインボー、ドライ） |
| 推奨アクション | CBet 75%ポット（~75%頻度） |
| EV評価 | チェックより+EV（フォールドエクイティ高い） |

**理由**: ドライレインボーボードはIPがレンジ優位を持つ。TPTKはナッツアドバンテージを持ち、
BBは7xや2xを除きほとんどヒットしない。75%サイズでフォールドエクイティを最大化しながらバリューを取る。

出典: [The Mechanics of C-Bet Sizing | GTO Wizard](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/)

---

### 問題2：TPTK on ウェットボード（CBet 75%）

| 項目 | 内容 |
|------|------|
| ポジション | BTN（IP） |
| プリフロップ | BTN RFI → BB コール |
| ハンド | K♠Q♦ |
| ボード | K♥J♥7♦（ツートーン、ウェット） |
| 推奨アクション | CBet 75%〜100%ポット |
| EV評価 | 大きなベットでドローをフォールドアウトし最大EV |

**理由**: ウェットボードではフォールドエクイティが特に価値を持つ。相手はフラッシュドロー・
ストレートドローを多く保有しており、大きなベットでこれらを畳む。TPTKはバリュー兼プロテクションで大きく打つ。

出典: [The Mechanics of C-Bet Sizing | GTO Wizard](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/)

---

### 問題3：オーバーペア on ドライボード（CBet 33%）

| 項目 | 内容 |
|------|------|
| ポジション | BTN（IP） |
| プリフロップ | BTN RFI → BB コール |
| ハンド | Q♠Q♥ |
| ボード | 7♦4♣2♥（レインボー、ドライ） |
| 推奨アクション | CBet 33%ポット（高頻度） |
| EV評価 | スモールベット高頻度でEV最大化 |

**理由**: ドライボードではフォールドエクイティの価値が低い（折らせたい手はほぼ持っていない）。
33%サイズでレンジ全体をベットする戦略が適合。小さく打つことでキャッチアップを防ぎつつバリューを積む。

出典: [GTO flop strategy - Cheat Sheet | GTO Charts](https://gtocharts.com/a-simplified-gto-flop-strategy/), [Flop Heuristics: IP C-Betting in Cash Games | GTO Wizard](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)

---

### 問題4：オーバーペア on ウェットボード（チェック or ラージベット）

| 項目 | 内容 |
|------|------|
| ポジション | BTN（IP） |
| プリフロップ | BTN RFI → BB コール |
| ハンド | Q♠Q♥ |
| ボード | J♦T♦8♣（コネクテッド、ウェット） |
| 推奨アクション | チェック（またはポットベット前後） |
| EV評価 | ミックス戦略。ベットなら大きく打つ |

**理由**: 非常にウェットなボードでは相手もナッツ候補を多く持ち、IPのナッツアドバンテージが消える。
レンジ全体でスモールCBetは適さない。強い手はポット〜オーバーベット、脆弱な手はチェックで分ける。

出典: [The Mechanics of C-Bet Sizing | GTO Wizard](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/)

---

### 問題5：TPGK on ドライボード（CBet 33%）

| 項目 | 内容 |
|------|------|
| ポジション | BTN（IP） |
| プリフロップ | BTN RFI → BB コール |
| ハンド | A♦J♠ |
| ボード | A♣8♦2♥（レインボー、ドライ） |
| 推奨アクション | CBet 33%ポット（高頻度） |
| EV評価 | スモールで広くバリュー取り |

**理由**: AJoはTPGK（グッドキッカー）でドライボード。BBのレンジはほとんどヒットしておらず、
フォールドエクイティは低い。33%サイズで高頻度にベットして累積EV。ターン・リバーで追加バリューを狙う。

出典: [GTO flop strategy - Cheat Sheet | GTO Charts](https://gtocharts.com/a-simplified-gto-flop-strategy/)

---

### 問題6：TP 弱キッカー（チェック寄り）

| 項目 | 内容 |
|------|------|
| ポジション | BTN（IP） |
| プリフロップ | BTN RFI → BB コール |
| ハンド | A♥5♠ |
| ボード | A♣8♦2♥（レインボー、ドライ） |
| 推奨アクション | チェックバック（~50%頻度）またはスモールCBet |
| EV評価 | チェックでショーダウンバリュー確保が優先 |

**理由**: A5oは弱キッカーのTP。チェックレイズに対し脆弱で、AK/AQ/AJに大きく負けている。
相手BBのレンジはA5oをドミネートする多くのAx手を持つ。チェックバックでエクイティを実現しつつ、
ショーダウンへ向かう方が期待値が高い。

出典: [Flop Heuristics: IP C-Betting in Cash Games | GTO Wizard](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)

---

### 問題7：ナッツフラッシュドロー（セミブラフ CBet）

| 項目 | 内容 |
|------|------|
| ポジション | BTN（IP） |
| プリフロップ | BTN RFI → BB コール |
| ハンド | A♥K♥ |
| ボード | J♥T♦2♥（ツートーン） |
| 推奨アクション | チェックバック（~50%）またはCBet 75% |
| EV評価 | ナッツFDはエクイティが高すぎ、ブラフより実現優先 |

**理由**: AKhh（コンボドロー）は約67%エクイティを持ち、ポットを取りにいく必要性が低い。
GTO Wizard分析では「強すぎてブラフに適さない」とされ、チェックバックして自然にエクイティを実現する。
ベットするなら大きいサイズで相手のミディアムハンドをフォールドアウトする。

出典: [Picking the Right Semi-Bluffs | GTO Wizard](https://blog.gtowizard.com/picking-the-right-semi-bluffs/)

---

### 問題8：OESD（セミブラフCBet）

| 項目 | 内容 |
|------|------|
| ポジション | BTN（IP） |
| プリフロップ | BTN RFI → BB コール |
| ハンド | K♠Q♣ |
| ボード | J♥T♦2♣（レインボー） |
| 推奨アクション | CBet 66%〜75%（高頻度でセミブラフ） |
| EV評価 | 8アウト＋ヒット時大きなポテンシャル |

**理由**: OESDはフラッシュドローを持たない分、GTO的にはより積極的にブラフする適切な手。
KQoはストレートドロー8アウトで30%以上のエクイティ。相手がフォールドすれば即利益、
コールされてもターンでストレート完成が狙える。

出典: [Picking the Right Semi-Bluffs | GTO Wizard](https://blog.gtowizard.com/picking-the-right-semi-bluffs/)

---

### 問題9：空振りハイカード（レンジCBet）

| 項目 | 内容 |
|------|------|
| ポジション | BTN（IP） |
| プリフロップ | BTN RFI → BB コール |
| ハンド | K♠J♠ |
| ボード | 7♦4♣2♥（ドライ、BTNレンジミス） |
| 推奨アクション | CBet 33%（レンジCBet、高頻度） |
| EV評価 | 相手もほぼミス、フォールドエクイティで利益 |

**理由**: ドライローボードはBTNレンジに有利。BBはこのボードで強いハンドをほとんど持てない。
空振り手でも33%スモールCBetで高頻度にベットすることがGTOの推奨。相手は広いレンジを
フォールドせざるを得ない。

出典: [GTO flop strategy - Cheat Sheet | GTO Charts](https://gtocharts.com/a-simplified-gto-flop-strategy/)

---

### 問題10：セット on ドライボード（CBet 大きく）

| 項目 | 内容 |
|------|------|
| ポジション | BTN（IP） |
| プリフロップ | BTN RFI → BB コール |
| ハンド | 7♦7♣ |
| ボード | 7♥4♣2♦（レインボー、ドライ） |
| 推奨アクション | CBet 75%〜100%ポット |
| EV評価 | ナッツに近い手でフォールドエクイティを活用 |

**理由**: セットはほぼナッツ。ドライボードではスモールCBetが基本だが、セット等の強い手は
相手のドローしやすい手（ポケットペア等）からバリューを取るため大きなベットを混ぜる。
ドローを断つほどのプロテクションも不要なため、バリューに特化した大きいサイズを選択。

出典: [Flop Heuristics: IP C-Betting in Cash Games | GTO Wizard](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)

---

### 問題11：セット on ウェットボード（プロテクション 100%）

| 項目 | 内容 |
|------|------|
| ポジション | BTN（IP） |
| プリフロップ | BTN RFI → BB コール |
| ハンド | J♦J♣ |
| ボード | J♥T♥8♣（コネクテッド、ウェット） |
| 推奨アクション | CBet 100%〜125%ポット（オーバーベット） |
| EV評価 | 脆弱なナッツは今すぐ最大ベットが最高EV |

**理由**: ウェットボードのセットは高いエクイティを持つが、ターンで価値が急落するリスクがある。
GTOは「脆弱な強ハンドは前倒しでベット」を推奨。ストレート・フラッシュドローを高いオッズで
フォールドアウトしながら最大バリューを取る。

出典: [The Mechanics of C-Bet Sizing | GTO Wizard](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/)

---

### 問題12：BB対BTN CBetでのフラット

| 項目 | 内容 |
|------|------|
| ポジション | BB（OOP） |
| プリフロップ | BTN RFI → BB コール |
| ハンド | T♠9♠ |
| ボード | K♦7♣2♥（ドライ、レインボー） |
| 相手アクション | BTN CBet 33% |
| 推奨アクション | フラットコール |
| EV評価 | チェックレイズの根拠なし、コールでエクイティ実現 |

**理由**: BBはこのボードでレンジ劣位。T9sはバックドアドロー持ちで6〜8アウト相当のエクイティがある。
BTNの33%CBetに対し、レイズの根拠（ナッツ手がない）もなく、フォールドするほど弱くもない。
コールが基本アクション。チェックレイズは2バリュー：1ブラフの比率で構成するが、この手はブラフ候補。

出典: [Upswing Poker - 5 Winning Check-Raising Strategies](https://upswingpoker.com/check-raising-strategies/)

---

### 問題13：BB対UTG CBetでのフォールド

| 項目 | 内容 |
|------|------|
| ポジション | BB（OOP） |
| プリフロップ | UTG RFI → BB コール |
| ハンド | 8♦5♦ |
| ボード | A♣K♥6♣（ツートーン） |
| 相手アクション | UTG CBet 75% |
| 推奨アクション | フォールド |
| EV評価 | 必要エクイティ（~43%）を満たせずフォールドEV |

**理由**: UTGのレンジはAx/Kxを多く含む強いレンジ。BB対UTGでBBはさらにレンジ劣位。
8♦5♦はこのボードでほぼ0の強いハンドと接続しておらず、バックドアフラッシュドローのみ。
75%CBetに対し必要エクイティ約43%を確保できない。フォールドが明確。

出典: [Flop Heuristics for Defending the Blinds in MTTs | GTO Wizard](https://blog.gtowizard.com/flop-heuristics-for-defending-the-blinds-in-mtts/)

---

### 問題14：BB対CO CBetでのチェックレイズ

| 項目 | 内容 |
|------|------|
| ポジション | BB（OOP） |
| プリフロップ | CO RFI → BB コール |
| ハンド | 7♣6♣ |
| ボード | 7♦5♥4♣（コネクテッド、レインボー） |
| 相手アクション | CO CBet 33% |
| 推奨アクション | チェックレイズ（3×前後） |
| EV評価 | ナッツアドバンテージあり、レイズで最大化 |

**理由**: 765ボードはBBがセットや2ペアを持てるがCOは保有しにくいナッツアドバンテージがある。
7♣6♣はTP+OESD+バックドアFDで高エクイティ。このようなボードでBBが強い手を持つとき、
小さなCBetに対してチェックレイズが正当化される。コールより大きなEVが期待できる。

出典: [Check-Raising a Single Pair | GTO Wizard](https://blog.gtowizard.com/check-raising-a-single-pair/), [10 Tips for Multiway Pots | GTO Wizard](https://blog.gtowizard.com/10-tips-multiway-pots-in-poker/)

---

### 問題15：マルチウェイでのTP

| 項目 | 内容 |
|------|------|
| ポジション | BTN（IP） |
| プリフロップ | BTN RFI → CO コール → BB コール（3way） |
| ハンド | A♦J♥ |
| ボード | A♣8♦2♥（ドライ） |
| 推奨アクション | スモールCBetまたはチェック（慎重） |
| EV評価 | マルチウェイでTP価値は大幅低下 |

**理由**: マルチウェイではフォールドエクイティが激減する。複数相手の中には強いAx（AK、AQ）も含まれる。
TPは価値ある手だが、「ナッツ手でない限りチェックバックを増やす」がGTOの方向性。
スモールCBetで情報収集しつつポットを膨らませすぎない。

出典: [10 Tips for Multiway Pots in Poker | GTO Wizard](https://blog.gtowizard.com/10-tips-multiway-pots-in-poker/)

---

### 問題16：3betポット IPでのCBet

| 項目 | 内容 |
|------|------|
| ポジション | BTN（IP、3bet側） |
| プリフロップ | CO RFI → BTN 3bet → CO コール |
| ハンド | K♠K♥ |
| ボード | 9♣5♦2♥（ドライ、BTNがレンジ優位） |
| 推奨アクション | CBet 25〜33%（高頻度、スモールサイズ） |
| EV評価 | 3betポットはIPがレンジ支配、小さく広くが高EV |

**理由**: 3betポットでIPは大きなレンジアドバンテージを持つ。低ボードはCOレンジをほぼヒットせず、
KKはナッツに近い。スタックが深いため大きく打つとSPRが崩れるリスクがある。
25〜33%スモールCBetで高頻度にベットし、ポットを管理しながらターンでサイズアップ。

出典: [C-Betting IP in 3-Bet Pots | GTO Wizard](https://blog.gtowizard.com/c-betting-ip-in-3-bet-pots/)

---

### 問題17：3betポット OOP でのチェック

| 項目 | 内容 |
|------|------|
| ポジション | SB（OOP、3bet側） |
| プリフロップ | BTN RFI → SB 3bet → BTN コール |
| ハンド | A♥Q♣ |
| ボード | K♠J♦7♥（BTNのKJヒットが多い） |
| 推奨アクション | チェック（大半の頻度） |
| EV評価 | OOPでナッツアドバンテージなし、チェックが安全 |

**理由**: 3betポットOOPでもSBはレンジ上優位だが、KJ7ボードはBTNが多くのKx/JxでヒットしEV差が縮まる。
AQはノーペア。ベットアウトすると相手のKx/JxにコールされてOOPで苦しい。
チェックしてBTNのベットを見てから対応（コールやチェックレイズ）が安全。

出典: [C-Betting OOP in 3-Bet Pots | GTO Wizard](https://blog.gtowizard.com/c-betting-oop-in-3-bet-pots/)

---

### 問題18：ドンクベット対応

| 項目 | 内容 |
|------|------|
| ポジション | BTN（IP、CBet期待側） |
| プリフロップ | BTN RFI → BB コール |
| ハンド | Q♥Q♦ |
| ボード | 6♦5♣4♥ |
| 相手アクション | BB ドンクベット 50%ポット |
| 推奨アクション | フラットコール（スローラフ） |
| EV評価 | コールで相手のブラフターンを誘う |

**理由**: BBのドンクベットはストレート完成・2ペア・セット等、ナッツ候補が多いレンジ。
QQはオーバーペアだが654ボードではストレートや2ペアに負ける。フラットコールで相手のレンジを
絞りつつ、ターンでBBがブラフを続けた場合に対応する。レイズはブラフを追い出してしまう。

出典: [Using GTO Strategy Solutions to Adapt to Wonky Donk Bets | 888poker](https://www.888poker.com/magazine/strategy/adapting-gto-strategy-donk-bets)

---

### 問題19：ウェットモノトーン on チェックバック

| 項目 | 内容 |
|------|------|
| ポジション | BTN（IP） |
| プリフロップ | BTN RFI → BB コール |
| ハンド | K♠Q♠ |
| ボード | 9♠6♠2♠（モノトーン） |
| 推奨アクション | チェックバック（ほぼ全頻度）またはスモールCBet |
| EV評価 | モノトーンはベット頻度・サイズが急減 |

**理由**: モノトーンボードでは両者がフラッシュを持てるため、ナッツアドバンテージが著しく低下する。
K♠Q♠は高いブロッカー価値を持つが、スペードフラッシュなしではポットを膨らませるリスクが高い。
GTOはモノトーンフロップでのCBet頻度とサイズを大幅に削減する。

出典: [Maximizing Value on Monotone Flops | GTO Wizard](https://blog.gtowizard.com/maximizing-value-on-monotone-flops/)

---

### 問題20：オーバーペア対大きなCBet

| 項目 | 内容 |
|------|------|
| ポジション | BB（OOP） |
| プリフロップ | BTN RFI → BB コール |
| ハンド | J♠J♥ |
| ボード | K♣8♦3♠（ドライ） |
| 相手アクション | BTN CBet 75%ポット |
| 推奨アクション | フォールドまたはコール（ミックス） |
| EV評価 | Kxに圧倒的不利、コールEVは微マイナス〜トントン |

**理由**: JJはKx（KQ, KJ, KT等）を多く含むBTNレンジに対してアンダーカードオーバーペア。
75%CBetに対しJJのエクイティは30〜35%程度でありコールの必要エクイティ（~43%）を下回る。
GTOはフォールドを優先するが、相手がオーバーCBetする傾向があれば搾取的にコールを増やせる。

出典: [The Mechanics of C-Bet Sizing | GTO Wizard](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/), [Flop Heuristics for Defending the Blinds in MTTs | GTO Wizard](https://blog.gtowizard.com/flop-heuristics-for-defending-the-blinds-in-mtts/)

---

## 本書への適用

### 第23章「20問ドリル：3秒でフロップ判断」構成案

各問題は次の形式で出題する：

```
【問題X】
ポジション: BTN（IP） / プリフロップ: BTN RFI→BB コール
ハンド: ●● / ボード: ●●●

→ あなたの判断は？（3秒以内）

A. CBet 33%  B. CBet 75%  C. チェック  D. オーバーベット
```

### 問題カバレッジ表

| # | テーマ | キーポイント | 難易度 |
|---|--------|------------|--------|
| 1 | TPTK / ドライ | 75%で押す | 易 |
| 2 | TPTK / ウェット | ドローに対し大きく | 易 |
| 3 | OP / ドライ | 33%高頻度レンジCBet | 易 |
| 4 | OP / ウェット | チェックか大きく | 中 |
| 5 | TPGK / ドライ | 33%スモールCBet | 易 |
| 6 | TP弱キッカー | チェックバック優先 | 中 |
| 7 | ナッツFD | エクイティ高すぎてチェック | 難 |
| 8 | OESD | 積極的セミブラフ | 中 |
| 9 | 空振りハイカード | レンジCBet33% | 中 |
| 10 | セット / ドライ | バリュー大きく | 易 |
| 11 | セット / ウェット | 前倒しオーバーベット | 中 |
| 12 | BB vs BTN CBet / フラット | コールで実現 | 中 |
| 13 | BB vs UTG CBet / フォールド | 必要エクイティ未達 | 易 |
| 14 | BB / チェックレイズ | ナッツアドバンテージ活用 | 難 |
| 15 | マルチウェイTP | 慎重にスモールorチェック | 難 |
| 16 | 3betポット IP | スモールCBet高頻度 | 中 |
| 17 | 3betポット OOP | チェックで誘導 | 難 |
| 18 | ドンクベット対応 | スローラフコール | 難 |
| 19 | モノトーン | ベット頻度・サイズ激減 | 中 |
| 20 | OP vs 大CBet | フォールド閾値の理解 | 難 |

---

## 主要参考ソース

- [The Mechanics of C-Bet Sizing | GTO Wizard](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/)
- [Flop Heuristics: IP C-Betting in Cash Games | GTO Wizard](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)
- [C-Betting IP in 3-Bet Pots | GTO Wizard](https://blog.gtowizard.com/c-betting-ip-in-3-bet-pots/)
- [C-Betting OOP in 3-Bet Pots | GTO Wizard](https://blog.gtowizard.com/c-betting-oop-in-3-bet-pots/)
- [Picking the Right Semi-Bluffs | GTO Wizard](https://blog.gtowizard.com/picking-the-right-semi-bluffs/)
- [Maximizing Value on Monotone Flops | GTO Wizard](https://blog.gtowizard.com/maximizing-value-on-monotone-flops/)
- [10 Tips for Multiway Pots in Poker | GTO Wizard](https://blog.gtowizard.com/10-tips-multiway-pots-in-poker/)
- [Flop Heuristics for Defending the Blinds in MTTs | GTO Wizard](https://blog.gtowizard.com/flop-heuristics-for-defending-the-blinds-in-mtts/)
- [GTO flop strategy - Cheat Sheet | GTO Charts](https://gtocharts.com/a-simplified-gto-flop-strategy/)
- [5 Winning Check-Raising Strategies | Upswing Poker](https://upswingpoker.com/check-raising-strategies/)
- [Using GTO Strategy Solutions to Adapt to Wonky Donk Bets | 888poker](https://www.888poker.com/magazine/strategy/adapting-gto-strategy-donk-bets)
- [Check-Raising a Single Pair | GTO Wizard](https://blog.gtowizard.com/check-raising-a-single-pair/)
