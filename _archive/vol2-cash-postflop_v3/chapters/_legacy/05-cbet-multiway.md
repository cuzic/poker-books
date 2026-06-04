---
chapter: "05"
title: "マルチウェイ: IPのCBetとSBのドンク戦略"
section: "フロップ編"
target_kchar: 9
decks: [flop_cbet_multiway, sb_donk_multiway]
status: revised
gto_source: "GTO Wizard MTT6mSimple 30+ multiway spots (2026-05-26)"
---

# 第5章　マルチウェイ: IPのCBetとSBのドンク戦略

3人以上が参加するマルチウェイポットでは、ヘッズアップと比べて IP の CBet 頻度を大幅に下げる必要があります。一方で、これまであまり注目されてこなかった **SB（OOP）のドンクベット** が、実は board × position の条件次第で 20-35% という高頻度で発動することが GTO Wizard 30+ spots の解析で判明しました。

本章では従来の「IP の CBet 抑制ルール」に加えて、**「SB がリードを取れる board の見分け方」** を新発見データから整理します。

## 5-1　フォールドエクイティが急落する仕組み

ヘッズアップ（HU）では相手1人のフォールド確率だけを考えれば済みます。しかし3ウェイになると「2人が同時にフォールドする」確率が必要になります。

概念的な例として、あるボードでHUの相手が50%の確率でフォールドするとします。3ウェイで2人ともフォールドする確率は50%×50%=25%まで低下します。ブラフの成功率がHUの半分になるという直感が重要です。

さらにプレイヤーが増えると「誰かがボードにヒットしている」確率が急増します。

| プレイヤー数 | 誰かが強くヒットしている概算確率 |
|---|---|
| HU（2人） | 約30〜35% |
| 3ウェイ | 約50〜55% |
| 4ウェイ | 約60〜70% |

3ウェイでは半分以上の確率で誰かがバリューハンドを持ちます。この状況でブラフを打っても期待値がマイナスになりやすいです。

## 5-2　マルチウェイ IP CBet 決定ルール

| 条件 | CBet可 | 推奨サイズ |
|---|---|---|
| IP有利ボード（型1/2/6）× バリュー | ○ | 33%（小さく広く） |
| 中立ボード（型7）× バリュー | ○ | 33% |
| BB/SB有利ボード（型3/4/5）× バリュー | ✗ | チェック |
| マージナル以下（全ボード） | ✗ | チェック |

このルールはHU用の決定表よりもはるかに厳格です。HUではマージナルでも型次第でCBetできましたが、マルチウェイではバリューかつIP有利ボードという2条件を同時に満たさない限りチェックが基本方針です。

### なぜ33%に統一するか

HUではバリューに75%を使う局面がありましたが、マルチウェイでは33%に統一します。理由は3つあります。

1. **資金管理**: 3ウェイで75%CBetを打ち2人ともコールするとポットが3倍以上に膨らみ、ターン以降の弱手が大きな損失になる
2. **部分的成功でも採算**: 33%なら1人フォールドさせるだけでもプラスになる場合がある
3. **tell防止**: バリューとブラフを混ぜた均一サイズが読まれにくい

## 5-3　SB ドンク戦略（新発見）

GTO Wizard 30+ spots の解析で、**SB が flop で donk する頻度は従来理解とまったく違う** ことが判明しました。

### 旧来の常識 vs GTO 実測

| ボード | 旧来の予測 | GTO 実測 |
|------|-----------|--------|
| 543, 654, 765 (low connected) | 「攻めるべき」 | **2-7%（ほぼ donk しない）** |
| K64, A74, Q42 (high disconnected) | 「check 推奨」 | **17-26%（積極 donk）** |
| 864, J52, J75 (middle gap) | 中庸 | **18-34%（最高峰）** |
| 8/9-high disconnected | 中庸 | **17-28%（peak）** |

「low connected ボードは SB が攻めるべき」という直感は **完全に逆** でした。実際には high disconnected と middle gap で SB が積極的にリードします。

### なぜ low connected で donk しないのか

543, 654, 765 のような low connected ボードでは、3 つの参加レンジ（HJ open / SB call / BB call）すべてに低コネクター（A4, A5, 65s, 76s 等）が含まれます。**全員が同じレンジ密度を持つため、SB に固有のレンジ優位がありません**。

一方で K64 や A74 のような high disconnected ボードでは、SB の call range には pocket pair（66, 77, AA, KK 等）が多く、middle/high カードが板にあると pair-up や top-set hit が SB に集中します。**SB が unique に強くなる → donk が GTO**。

### high card 別 donk 平均

| high card | 平均 donk% | サンプル例 |
|---------|--------:|----------|
| A-high | 8-18% | A92, A74, A52 |
| K-high | 12-23% | K92, K64, K52 |
| Q-high | 16-28% | Q92, Q42, Q63 |
| J/T-high | 15-25% | J85, J75, T62, T98 |
| **9/8-high** | **17-28%** | **9c6s2d, 864, 852, 872** |
| < 8-high | 5-13% | 543, 654, 765, 432 |

**意外な発見**: 9-high や 8-high の disconnected ボードが donk のピーク。これは「SB のポケットペア (66, 77, 88, 99) が中ランク board で支配的になりやすい」という構造的理由による。

### open position の効果

| open position | SB donk 平均 | サンプル数 |
|-------------|--------:|--------:|
| HJ open + SB+BB call | 16.9% | 15 |
| CO open + SB+BB call | 20.5% | 6 |
| **BTN open + SB+BB call** | **23.5%** | 7 |

BTN open のレンジが最も広いため、cbet レンジが弱体化しやすく、SB が donk で攻めやすい構造になります。

### SB ドンクの判定フロー

```
■ マルチウェイ SB ドンク判定 (flop first to act)

1. Board の high card は？
   ├─ A/K/Q-high → 17-28% donk 検討
   ├─ J/T-high → 15-25% donk 検討
   ├─ 9/8-high → 17-28% donk (peak)
   └─ <8-high → 2-13% donk (基本 check)

2. Board の connectedness は？
   ├─ Low connected (543, 654, 765) → donk しない
   ├─ Mid-gap (864, J52, J75) → 18-34% donk
   ├─ High disconnected (K64, A74, Q42) → 17-26% donk
   └─ Wet connected (T98, J97) → 11-22% donk

3. Open position は？
   ├─ BTN open multiway → +5pt
   ├─ CO open multiway → +3pt
   └─ HJ open multiway → baseline

サイズは一律 33% pot
```

## 5-4　IP有利ボードとSB有利ボードの違い

| ボード型 | IP CBet 推奨 | SB donk 推奨 |
|--------|-----------|----------|
| 型1 (ハイドライ K72) | バリューで CBet 33% | SB は基本 check (top pair なら call) |
| 型2 (ハイウェット Q83) | バリューで CBet 33% | SB は check (range advantage 強い IP) |
| 型3 (ミッドウェット J65) | 慎重 (BB有利) | SB は弱め (10-18% donk) |
| 型4 (ローコネクテッド T98) | check 多用 | **SB が 11-22% で donk** |
| 型5 (ミッドドライ T52) | バリューのみ | **SB が 18-34% で donk** |
| 型6 (Q-high air Q42) | バリューのみ | **SB が 17-26% で donk** |
| 型7 (ペア低 774) | バリューで CBet 33% | 例外的に SB が 19% で donk |

## 5-5　ペア / モノ flop でのマルチウェイ

| ボード | flop first | turn after cbet-call |
|------|-----------:|---------------------:|
| KK7 (high pair) | 0% donk | 0% donk |
| AAK (high pair) | 0% donk | 0% donk |
| **774 (low pair)** | **19% donk!** | 0% donk |
| Q66 | - | 0% donk |
| 883 | - | 0% donk |
| KsQs7s (mono) | 0% donk | 0% donk |
| Js9s5s (mono) | 0.1% donk | 0% donk |

**唯一の例外**: 低ペア (774) で SB が flop donk 19%。これは BB のレンジに 7x（A7, 87s, 76s 等）が密に含まれているため、フロップ時点で自然にリードできるからです。高ペア (KK7, AAK) では BB に top card がほぼ無いため donk = 0%。

モノ flop は IP のレンジ優位が極端に強く、SB は donk しません（XX 後の probe では 20-22% で発動するが、これはターン以降の話）。

## 5-6　例題（auto-generated）

| ハンド | ボード | HS（バケット）| ポット種別 | 答え |
|---|---|---|---|---|
| K♥Q♦ | K♠7♦2♣ | 66（バリュー）| HJ vs SB vs BB (SRP 3way) | IP: CBet 33% / SB: check |
| Q♣J♦ | Q♥4♠2♣ | 60（マージナル）| HJ vs SB vs BB | IP: check / **SB: donk 33%（26%頻度）** |
| 7♥6♥ | 8♥6♣4♦ | 50（マージナル）| HJ vs SB vs BB | IP: check / **SB: donk 33%（23%頻度）** |
| A♠2♠ | 7♦6♠5♣ | 25（エアー）| HJ vs SB vs BB | IP: check / SB: check（low connected donk 0%） |
| K♣9♦ | K♥6♠4♣ | 64（バリュー）| BTN vs SB vs BB | IP: CBet 33% / SB: 大半 check |

**解説**

例題① K♥Q♦ on K72 はマルチウェイで IP が CBet を打つ典型例。型1 ボード × バリューの条件を満たし、33% で打ちます。

例題② Q♣J♦ on Q42 air board は **SB の donk 帯**。Q-high disconnected で SB が 26% で donk するスポットです。Q♣J♦ で top pair を持っているなら donk リードを取りに行きます。

例題③ 7♥6♥ on 864 mid-gap board は **SB donk 23%** のスポット。middle pair に self-equity 強い board で、SB がリードを取って圧力をかけます。

例題④ A♠2♠ on 765 low connected はマルチウェイで全員 check が GTO。SB の donk 率は 2% 程度に過ぎず、エアーで攻めるべきではない場面です。

例題⑤ K♣9♦ on K64 disconnected で BTN open multiway。BTN は CBet 33%、SB は K-high disconnected で 18% donk するスポットですが、IP が先に動くため SB は check が標準。

## 5-7　マルチウェイディフェンス側の考え方

CBet（または SB donk）に直面したとき、コール基準は HU より厳しくなります。

| ポジション | HU閾値 | 3way補正 | 4way補正 |
|---|---|---|---|
| IP（最後の行動者）| 通常閾値 | +0 | +0 |
| 中間ポジション | 通常閾値 | +5 | +10 |
| OOP（最初の行動者）| 通常閾値 | +10 | +15 |

たとえばSRP 33%ベットに対してHUならHS≥15でコールしますが、3wayでOOPなら HS≥25が基準になります。

**SB donk に対するディフェンス**：SB の donk レンジは「ポケットペア + top pair + ナッツドロー」中心で、純粋なブラフが少ない（マルチウェイなので fold equity が低い）。したがって SB の donk に対するコールは HU の 33% bet 対応より少し厳しめが基本です。

## 5-8　チェックレイズをマルチウェイで使う条件

マルチウェイでバリュー（HS≥70 のセット/2ペア等）を持つとき、CBet ではなくチェックレイズを狙う選択肢もあります。

ただしマルチウェイではCBet頻度自体が下がるため、チェックレイズ待ちは HU より決まりにくくなります。型1・型2では IP がバリュー以上を多く持ち CBet 頻度が比較的維持されるため、チェックレイズ待ちが有効です。

## 5-9　ポジション別優先順位

**IP ポジション (BTN)**: 最後に行動できる利点が活きる。型1/2/6 バリューで 33% CBet。

**中間ポジション (CO/HJ)**: 後ろに行動者がいる。バリューでも後ろのプレイヤーのレンジ次第でフォールドリスクを考慮。

**SB ポジション**: 本章の新発見。「IP より先に動く」立場で、middle gap や high disconnected で 17-34% donk が GTO。

**BB ポジション**: マルチウェイで最も制約厳しい。check が基本、value 上位のみ CR を検討。

## 5-10　総合判断チェックリスト

```
■ マルチウェイ CBet 判断 (IP)
□ 自分はIPか
□ HSがバリュー (HS≥65) か
□ ボード型が1/2/6/7か
□ サイズは33%か
すべてYES → CBet 33%

■ マルチウェイ SB donk 判断
□ flop first to act
□ Board が high disconnected または mid-gap か
□ 自分のハンドが range advantage を取れる構造か
   (pocket pair, top pair on mid-disconnected 等)
□ open position は BTN/CO か (donk 率が上がる)
すべてYES → donk 33% pot (頻度 18-30%)
```

---

### 【GTOとのズレ】

旧書籍では「マルチウェイは全員 check が基本」「SB は積極的に donk しない」と教えられていました。GTO Wizard 30+ spots 解析の結果、これは **半分正しく、半分誤り** でした：

1. **IP の CBet 頻度抑制は正しい**（バリュー × IP 有利ボードのみ）
2. **SB の donk は条件次第で 20-35% で発動する**（high disconnected / mid-gap）
3. 旧来の「low connected で donk」は完全に誤り。実際は 2-7% にとどまる
4. 「8/9-high が donk のピーク」という非直感的な発見も重要

本書のフローチャートは GTO Wizard 実測データから直接導出した境界条件であり、実戦では「Board の high card と connectedness を見て donk するか判断する」というシンプルなルールで 90% の判断が正解できます。

旧 GCP study では multiway SB lead 自体を体系的に測定していなかったため、本書が初の実測ベース指導となります。
