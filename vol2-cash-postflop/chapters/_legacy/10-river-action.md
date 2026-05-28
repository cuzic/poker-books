---
chapter: "10"
title: "リバー: 先手・後手とXX-XX経路の OOP lead"
section: "リバー編"
target_kchar: 10
decks: [river_first, river_defense, river_xx_xx]
status: revised
gto_source: "GTO Wizard MTT6mSimple 30+ river spots (2026-05-26)"
---

# 第10章　リバー: 先手・後手とXX-XX経路の OOP lead

リバーは全5枚のコミュニティカードが出揃い、ドローが完成または失敗に終わる最終ストリートです。
エクイティが確定するため、先手は3バケット（バリュー/マージナル/エアー）で打ち分け、後手は HandScore と MDF を照合してコールかフォールドを決めます。

本章は伝統的な「IP barrel → river bet」ライン（cbet→bet→bet）だけでなく、GTO Wizard 30+ spots の解析で新たに判明した **XX-XX 経路（フロップ・ターン両者 check）後の OOP リバー lead** を加えた完全版です。

## 10-1　3バケット（バリュー/マージナル/エアー）

> **フロップのバリュー/マージナル/エアーとリバーのバケットの対応**：リバーでは DrawBonus=0 のため HS の意味が変わります。フロップでバリュー（HS≥65）だったハンドはリバーでバリューバケット（HS≥70）に対応し、フロップのマージナルがマージナルバケット（HS 35〜69）に、エアーがエアーバケット（HS<35）に相当します。同じ数値でも「フロップ時のHS」と「リバー時のHS」では含まれるドロー加点が異なるため直接比較はできませんが、大まかな対応関係として覚えておいてください。

| HandScore | バケット | 先手方針 |
|---|---|---|
| 70〜100 | バリュー | ベット（サイズ問わず） |
| 35〜69 | マージナル | ボードとサイズで判断 |
| 0〜34 | エアー（ブラフ候補） | ベット or チェック（ブラフ検討） |

### マージナルバケットの詳細判断

```
マージナルバケット（HS35〜69）リバー先手判断
├─ HS 55〜69（マージナル上位）
│   ├─ ドライボード（型1・型3） → ベット33%（薄いバリュー）
│   ├─ ウェットボード（型2・型4） → チェック（逆選択回避）
│   └─ 相手がウィーク（チェックバック連続等）→ ベット33%
└─ HS 35〜54（マージナル下位）
    ├─ 相手のレンジが弱い（リバーチェック後）→ ベット33%（薄バリュー）
    └─ 相手がポット管理中 → チェック（ショーダウン優先）
```

## 10-2　後手 MDF と overbet 対応

| 相手ベットサイズ | コール条件（HandScore） | α |
|---|---|---|
| 33%（α=25%）| HS≥45 が目安 | 0.25 |
| 50%（α=33%）| HS≥50 が目安 | 0.33 |
| 75%（α=43%）| HS≥60 が目安 | 0.43 |
| 100%（α=50%）| HS≥65（バリュー）必要 | 0.50 |
| **126% (overbet)** | **HS≥70** | 0.56 |
| **372% (huge overbet)** | **HS≥80** | 0.79 |

リバーでは DrawBonus=0 のため HS ≈ エクイティ%に近づきます。
コール基準のHS値は実際のエクイティ%の目安として読んでください。

**新サイズ層**: XX-XX 経路で頻出する 126% overbet と、dry board polarized で稀に出る 372% huge overbet を追加。126% に対するブラフキャッチは HS70 以上のバリューハンドのみ、372% は HS80 以上（ナッツ近辺）のみとなります。

## 10-3　XX-XX 経路の OOP リバー lead（新発見）

GTO Wizard 30+ spots で判明した重要な発見が、**フロップとターン両方が両者 check（XX-XX）になった後の OOP（BB）のリバー lead 行動** です。これは旧来の戦略書で抜け落ちていた領域です。

### Position 効果: CO > BTN > HJ/UTG

XX-XX 経路の後、BB のリバー lead 頻度は **open position に依存**します。

| open ポジション | BB の river lead 平均 | サンプル |
|--------------|----------------:|--------:|
| UTG vs | 24.9% | 3 |
| HJ vs | 24.4% | 2 |
| **CO vs** | **38.4%（peak）** | 3 |
| BTN vs | 31.9% | 4 |

CO 開きが最大、HJ/UTG が最小という非単調な分布になります。
理由は「CO は range が中庸（HJ ほどタイトでなく BTN ほど広くない）で、XX-XX 連続 check はレンジ弱体化が最も顕著」だからです。

### River card 効果

board × river card の組合せで BB lead 率は **0% から 92% まで変動**します。

#### 連続 wet board (例: 9h 8s 7d 4c) の river

| river card | BB lead 率 |
|----------|---------:|
| blank (2d) | **77.6%** |
| board pair (4h) | **76.4%** |
| str8 complete (Td) | 59.8% |
| pair top (9d) | 54.8% |
| **scare A (Ad)** | **25.8%** |

#### dry board (例: Kxx 5h) の river

| river card | BB lead 率 |
|----------|---------:|
| pair top river (Kd) | 60.9% |
| scare A (Ad) | 44.2% |
| mid blank (Qd) | 38.0% |
| blank (3d) | 37.3% |

#### connected high board (例: QJ4+7) の river

| river card | BB lead 率 |
|----------|---------:|
| board pair (7d) | 45.2% |
| scare A (Ah) | 44.2% |
| str8 complete (Td) | 43.3% |
| blank (2h) | 42.0% |
| **pair top (Qd)** | **27.7%** |

### 法則のまとめ

```
■ XX-XX 後 river BB lead 判定

1. board × river の組合せ評価
   ├─ wet board + board pair river → 65-78% lead
   ├─ wet board + blank → 50-78%
   ├─ wet board + scare A → 15-30% (大幅減)
   ├─ dry board + pair top → 60% lead
   ├─ connected high + pair top → 25-30% (IP も持つ)
   └─ IP の broadway 完成 turn → 0% lead

2. サイズ二極化
   ├─ wet board + 連結 river → 33% pot
   └─ dry board polarized → 126% overbet
```

## 10-4　turn give-up 後の river: 別ライン

XX-XX 経路と並んで重要なのが、**「フロップ X-cbet-Call → ターン X-X」（IP が turn を諦め）** ライン後のリバーです。BB のリバー lead は board と river card に強く依存します。

### Wet board (例 987 + 4): scare A で激減

| river card | BB lead 率 |
|----------|---------:|
| 2 (blank) | **77.6%** |
| 4 (board pair) | **76.4%** |
| T (str8 complete) | 59.8% |
| 9 (pair top) | 54.8% |
| **A (scare)** | **25.8%** |

### Dry board (例 Kxx + 5h): pair top で peak

| river card | BB lead 率 |
|----------|---------:|
| K (pair top) | **60.9%** |
| A (scare) | 44.2% |
| Q (mid blank) | 38.0% |
| 3 (blank) | 37.3% |

### Connected high (例 QJ4 + 7): top pair で減

| river card | BB lead 率 |
|----------|---------:|
| 7 (board pair) | 45.2% |
| A (scare) | 44.2% |
| T (str8 complete) | 43.3% |
| 2 (blank) | 42.0% |
| Q (pair top) | **27.7%** (IP も Q 多保有) |

**ZERO lead spot**: IP の broadway 完成 turn（例 Kxx+J→T で IP の KJ/QJ/KQ が完成）では BB lead 0%。

## 10-5　チェックビハインドとブラフキャッチ

### チェックビハインド（IP）

ベット権をあえて使わず、SDV ハンドや弱手でポット管理します。

| 状況 | チェックビハインド推奨理由 |
|---|---|
| マージナルバケット（HS 35〜64） | ベット → 弱手のみコールの逆選択を避ける |
| ボードが相手レンジ有利 | ブラフ期待値 < チェックバック期待値 |
| 相手が CR しやすいスタック | 被 CR 時の損失 > ベット収益 |
| XX-XX 経路で IP がチェックバックした後 | OOP がリードを取る → IP は flexibility 失う |

**重要**: IP が turn でチェックバックを選ぶと、OOP が river リードを取る確率が高くなる（特に CO/BTN 開き）。IP のレンジが SDV 中心になるため、river OOP lead に対するブラフキャッチは慎重に。

### ブラフキャッチ（OOP）

相手のベットをブラフと判断してコールすることです。
33%の小ベットはV:B=3:1のためブラフが約25%含まれており、相手のブラフ頻度が高くキャッチしやすいです。
逆に126% overbet はブラフが約44%（α=56%）含まれますが、ベット自体のサイズが大きいため慎重な判断が必要です。

## 10-6　例題（auto-generated）

**先手:**

| ハンド | ボード | HS（バケット）| 経路 | 答え |
|---|---|---|---|---|
| A♥K♣ | A♠K♦7♣2♥9♠ | 78（バリュー）| 通常 IP barrel ライン | BET 50% |
| A♥J♦ | A♠K♦7♣2♥9♠ | 64（マージナル）| 通常 IP barrel ライン | CHECK（チェックバック） |
| Q♥J♦ | 9♥8♠7♦4♣2♦ | 30（エアー）| XX-XX 後 BB first | **LEAD 33% pot（77% 頻度）** |
| K♣J♠ | K♠7♦2♣5♥K♦ | 70（バリュー）| XX-XX 後 BB first | **LEAD 33%（pair top river）** |

**後手:**

| ハンド | ボード | HS（バケット）| 状況 | 答え |
|---|---|---|---|---|
| K♥Q♣ | A♠K♦7♣2♥9♠ vs 100% | 65 | 通常 defense | CALL |
| K♥Q♣ | A♠K♦7♣2♥9♠ vs **126% overbet** | 65 | XX-XX 後 BB lead | **FOLD（HS<70）** |
| A♥K♣ | A♠K♦7♣2♥9♠ vs **126% overbet** | 78 | 同上 | CALL |
| Q♥J♦ | A♠K♦7♣2♥9♠ vs 50% | 20 | 通常 defense | FOLD |

**解説**

例題①〜② は通常の IP barrel ライン（旧来通り）。

例題③ Q♥J♦ on 9♥8♠7♦4♣2♦ XX-XX 後: **wet board + blank river**。BB の lead 率は 77.6% に達する spot。Q♥J♦ は HS 30 のエアーだが、レンジ全体ではリードを取りに行く局面。33% pot で打ち、ブラフキャッチに勝負します。

例題④ K♣J♠ on K♠7♦2♣5♥K♦ XX-XX 後: **dry board + pair top river**。BB の lead 率 60.9% の peak スポット。K♣J♠ は K-pair に昇格しており、33% で薄くバリューを取ります。

例題⑤ K♥Q♣ vs 100% pot bet: 通常 MDF で HS≥65 必要、ぎりぎりコール。

例題⑥ 同じ K♥Q♣ vs **126% overbet**: HS70 必要なので **FOLD**。XX-XX 経路の overbet には HS65 では足りません。

例題⑦ A♥K♣ ツーペア vs 126% overbet: HS78 でコール可。

## 10-7　全ストリート統合フロー（改訂版）

```
プリフロップ → フロップ → ターン → リバー の総合判断

1. プリフロップ: Score ≥ T_open → オープン
   Score_BB ≥ T_3bet → 3ベット候補

2. フロップ: HS + ボード型 → CBetサイズ決定 (IP)
   OOP: MDF と HS でディフェンス

3. ターン: TA+/TA- 判定 → サイズ二極化（101%/276%）
   OOP: defense / probe / donk の 3 ライン分岐（第8章）

4. リバー:
   - IP barrel ライン: 3バケット → 50-75% ベット
   - XX-XX 経路 BB lead: position × river card で 0-77%
   - turn give-up 後 BB lead: board × river card で 25-78%
   - 後手: HS ≥ MDF閾値 → コール（126% overbet は HS≥70）
```

## 10-8　XX-XX 経路と turn give-up 経路の使い分け

実戦でこの2つを混同しないことが重要です。

| 経路 | 状況 | BB の river lead レンジ |
|----|----|--------------------|
| XX-XX (fl X-X / tn X-X) | IP が flop も turn も check back | 「IP のレンジが SDV 弱体化」を活用、polarized |
| turn give-up (fl X-cbet-C / tn X-X) | IP が flop cbet 後 turn を諦め | 「IP の barrel range が turn で消えた」を活用、bluff catch 誘発 |

XX-XX は **両者共通の弱体化**（フロップから誰も主張しない）、turn give-up は **IP の cbet range の中での turn 引き下げ**（IP の主導権放棄）。両者で BB の優位の質が異なります。

### 実戦判断のコツ

```
■ Step 1: フロップ→ターンの両者アクション履歴を確認
   ├─ X-X / X-X → XX-XX 経路（10-3節）
   ├─ X-cbet-C / X-X → turn give-up 経路（10-4節）
   └─ X-cbet-C / cbet-C → 通常 IP barrel ライン（10-1, 10-2節）

■ Step 2: River card を見る
   ├─ Board pair → 大半の経路で lead +20-30pt
   ├─ Scare A on wet → lead -30pt
   ├─ Pair top on dry → lead +25pt
   └─ IP の broadway 完成 turn → lead 0% (絶対 check)

■ Step 3: サイズ選択
   ├─ Wet + connected river → 33% pot
   ├─ Dry polarized → 126% overbet
   └─ 「ナッツ+air 極化」spot → 372% huge overbet (稀)
```

## 10-9　ポット管理の原則

リバーを含む全ストリートで「ポット管理」は重要なスキルです。

**大きなポットを好む場面（バリューバケット）：**
- セット以上のナッツクラスを保有
- 相手がコールを選びやすい（マージナルで粘っている）
- ドライボード × 薄バリュー（KQ 等）

**小さなポットを好む場面（マージナルバケット）：**
- 自分のマージナルハンドが逆選択リスクを抱えている
- ウェットボードで相手のドローが完成した可能性が高い
- 3BPなど深い局面でコミットを避けたい

XX-XX 経路で BB がリードする場合は、サイズ二極化により「33% pot で広く value+ブラフ」または「126% overbet でナッツ+air 極化」のどちらかを選びます。中間サイズ（50-75%）は使わないのが GTO 整合的です。

## 10-10　ドロー別リバーアクション早見表

| ドロー状態 | リバーアクション | HandScore | 先手方針 |
|---|---|---|---|
| NFD完成（ナッツフラッシュ） | バリューベット | HS≈95 | ベット50〜75% |
| フラッシュ完成（非ナッツ） | バリューベット | HS≈85 | ベット50% |
| OESD完成（ストレート） | バリューベット | HS≈90 | ベット50〜75% |
| ガットショット完成 | バリューベット | HS≈85 | ベット50% |
| NFD失敗（空振り） | ブラフ候補 | HS≈0〜5 | ブラフ条件確認 |
| OESD失敗（空振り） | ブラフ候補 | HS≈0〜5 | ブラフ条件確認 |
| ガットショット失敗 | ブラフ候補 | HS≈0〜5 | ブラフ上限で判断 |

「完成 → バリュー」と「失敗 → ブラフ候補」という変化はリバー判断の核心です。
XX-XX 経路では「フロップ・ターンで打たなかったドロー」がリバーで完成しても、bet サイズは 33%（薄く value+ブラフ）が GTO 整合的です。

---

### 【GTOとのズレ】

リバーの GTO 解析は、本書のような単純化した3バケット + HS閾値モデルでは捉えきれない複雑さを持ちます。特に大きな乖離は：

1. **XX-XX 経路の OOP lead の position 依存性**: CO 開きが peak (38%) で BTN/HJ が中程度。本書はこれを「open position が広い = OOP lead 多い」と近似していますが、CO ピークの理由（range balance）は完全に表現できていません。

2. **River card 効果の細粒度**: 「board pair river → +30pt」「scare A on wet → -30pt」「IP broadway 完成 turn → 0%」というルールは GTO 実測の近似であり、ボードによっては誤差が出ます。

3. **126% overbet と 372% huge overbet の使い分け**: 本書は二極化として簡略化していますが、GTO は board × hand category で複雑なミックスを使います。

4. **ブロッカー効果**: 同じ HS 値でも保有カードのブロッカー（A♠ や ナッツフラッシュブロッカー）によって判断が変わる場面があります。本書はブロッカー個別評価を省略しています。

これらの精緻化は本書を一通り習得した後の応用ステップとして取り組んでください。本章のフローチャート（XX-XX / turn give-up / 通常 barrel の3ライン分岐）を頭に入れるだけで、90% のリバー判断で GTO 整合的な選択ができます。
