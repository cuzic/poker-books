# 第 20 章　ストリート別 polarization — 完全 air が river で 74% bet する理由

## 20.1 GTO 理論の data 駆動の絵

ポストフロップにおける GTO 戦略は、 ストリート進行とともに **merged から polarized へ移行** していきます。 この理論は教科書 (Matthew Janda『Applications of No-Limit Hold'em』、 Michael Acevedo『Modern Poker Theory』) で定性的に語られてきましたが、 本書では **174K hands の data で初めて定量化** することができました。

## 20.2 完全 air × no_draw の bet 率 (全 context 横断)

「役なし、 draw 完成不可、 call されたら 100% 負け確定」 の hand の bet 率をまとめてみました:

| context | × dry | × paired | × wet | 段階 |
|---|---:|---:|---:|---|
| **SRP flop** | 13.4% | 9.6% | 6.3% | merged (bluff 抑制) |
| **3BP flop** | 14.8% | 16.8% | 22.0% | merged |
| **4BP flop** | 32.5% | 21.7% | 32.4% | merged (SPR 1.5 で aggression up) |
| **TURN** ★ | 39.8% | **60.9%** | 45.6% | **polarization 入口** |
| **RIVER** ★★ | 56.1% | 64.2% | **74.2%** | **fully polarized** |

### 解釈

- **flop (SRP/3BP)**: bluff bet 6-22% で **公式の check 推奨は GTO 平均的に正しい** ことがわかります
- **4BP flop**: SPR 1.5 と低いため bluff 頻度がやや上がっていきます
- **turn**: paired board で 60.9% bet が始まり、 polarization への入口となります
- **river**: 全 board で 56-74% bet、 完全に polarized した状態になります

## 20.3 なぜ river で完全 air が 74% bet するのか

直感的には「役なし、 draw なし、 call されたら 100% 負け確定」 の hand を bet するのは無謀に思えます。 ですが GTO は polarization のために bet を要求しています:

### bluff frequency 維持の必要性

相手の bluff catcher (中間 hand) を fold させるには、 bet レンジ内に十分な bluff combo を含める必要があります。

- 自分の **value range** (TP+ 以上) が bet → 相手 fold すると EV 損失
- **bluff range** (完全 air) も bet → 相手の bluff catcher を fold させて EV 獲得
- value : bluff の最適比率は **pot odds 由来** (例: 1/2 pot bet なら 2:1)

完全 air は call されたら 100% 負けますが、 **相手が中間 hand で fold する確率が高い** ため、 期待値プラスの bluff になります。

### 完全 air を bet する具体例

board: A♠ K♦ 5♣ T♥ 2♣ (river)
自分: 7♣ 6♣ (no_made_hand、 high card は 7)

- showdown まで進めば 100% 負けてしまいます (相手の king_high にも負けます)
- でも相手の low_pair (= ace_high より弱い bluff catcher) を fold させれば pot 獲得できます
- → 74% の頻度で bet するのが GTO の考え方です

## 20.4 ストリート別の戦略変化

| ストリート | 戦略 | 完全 air の扱い |
|---|---|---|
| **flop** | **merged**: 強 hand は thin value + medium hand mix | check 主体 (公式) |
| **turn** | **transition**: polarization 開始、 paired board から air bet 増 | 部分的 bluff bet |
| **river** | **polarized**: 強 hand value bet + 弱 hand bluff bet | **高頻度 bluff bet** |

## 20.5 暗算では何を覚えるか

この発見は MATCHA 公式に既に組み込み済みです:

- **flop (SRP/3BP)**: Score 公式の check 判定が GTO 平均的に正しい → 何もしなくて大丈夫です
- **TURN**: 「no_made_hand × paired/wet → bluff bet」 ルール (第 18 章)
- **RIVER**: 「no_made_hand → bluff bet」 ルール (第 19 章)

実戦では特に意識せず、 各 context の lookup/split rule に従えば自動的に polarization 戦略が実現されていきます。

## 20.6 教科書理論の data 確証

| 教科書 | 提唱内容 | data 確証 |
|---|---|---|
| Matthew Janda (2013) | 「river で bluff frequency 維持」 | RIVER bluff 56-74% ★ |
| Michael Acevedo (2019) | 「ストリート別 polarization 移行」 | flop 6-32% → river 74% |
| Will Tipton (2018) | 「polarization は equity 分布で決まる」 | river equity 二極化を確認 |

本書はこれらを **暗算可能な lookup/split rule に翻訳** することができました。

## この章で覚える項目 (3 items)

1. **flop は merged、 turn は transition、 river は fully polarized**
2. **river の完全 air は 74% bet** (相手の bluff catcher を fold させる)
3. 公式は既に polarization を組み込み済み (第 18/19 章)、 意識せず lookup に従えば OK
