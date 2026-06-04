---
chapter: "08"
title: "ターンディフェンス: ドンク・プローブ・MDF"
section: "ターン編"
target_kchar: 12
decks: [turn_defense, turn_donk, turn_probe]
status: revised
gto_source: "GTO Wizard MTT6mSimple 268 spots (2026-05-26)"
---

# 第8章　ターンディフェンス: ドンク・プローブ・MDF

ターンでの判断ミスは「今この瞬間だけを考えてしまう」ことから生まれます。
本章では、ターンで OOP（一般に BB）が直面する **3 種類の状況** を分けて整理します。GTO Wizard 268 spots の解析で明らかになった新発見、特に「ターン donk = 0% は誤り」「プローブベットは board × turn card で 0-92% 変動する」という事実を中心に、ターンの OOP 行動を再構築します。

## 8-1　OOPのターン三択

フロップでのアクションによって、ターン開始時の状況は3シナリオに分岐します。

| シナリオ | フロップ展開 | ターン開始時の OOP の役回り |
|--------|----------|-----------------------|
| **A. defense** | IP cbet → OOP コール → ターン IP 主導 | IP のバレルに対するコール/フォールド/CR |
| **B. probe** | IP cbet → OOP コール → ターン IP チェック → OOP 行動 / または IP X-back → ターン OOP 主導 | OOP がリードを取る判断 |
| **C. donk** | IP cbet → OOP コール → ターン OOP 主導 (最近の新発見) | OOP がフロップ cbet コール後、ターンで先頭リード |

ライン C の「ターン donk」は旧来の戦略書では「donk = 0%」と教えられてきましたが、GTO Wizard の実測では **board × turn card 次第で 25-86% に達する** ことが判明しました。本章はこの 3 シナリオを順に解説します。

## 8-2　ライン C: ターン donk フローチャート（新発見）

### donk が発動する条件

GTO Wizard 268 spots study で確認された、**board pair turn での OOP donk 率**：

| Flop | Turn | donk率 | 解釈 |
|------|------|------:|-----|
| **Ah Kd 4s** | Kc (mid pair) | **86.0%** | EXTREME — BBがKを持つ稀少 |
| **Ah Kd 4s** | Ac (top pair) | **71.6%** | EXTREME |
| 9h 8s 7d | 7c (bot pair) | 61.6% | 連結ボード bot pair |
| Td 7c 6s | 6h (bot pair) | 53.1% | 同上 |
| 9h 8s 7d | 8c (mid pair) | 59.6% | mid pair on connected |
| 9h 8s 7d | 9c (top pair) | 47.9% | top pair on connected |
| Kc 7d 2c | 7c (mid pair) | 48.1% | high disconnected の mid pair |
| Qh Jd 4s | 4c (bot pair) | 39.7% | Q/J board の bot pair |
| Jd Ts 9c | 9d (mid pair) | 39.2% | JT9 board の 9 |
| Kc 7d 2c | 2h (bot pair) | 38.5% | 高 dry の bot pair |
| Kc 7d 2c | Kh (top pair) | 25.5% | high dry の top pair |
| **Qh Jd 4s** | Qc (top pair) | **0%** | IP も Q 多保有 |
| **Td 7c 6s** | Th (top pair) | **0%** | IP も T 多保有 |
| **Jd Ts 9c** | Jh (top pair) | **0%** | IP も J 多保有 |
| 全ての blank turn | — | **0-2%** | 普遍的に check |

### 判定フロー

```
■ ターン donk 判定（IPのcbetをコール後、turnでOOPが先頭）

Turn = board のいずれかの rank と同じ？
├ YES (board pair turn)
│  ├ AK系 board (A-high + K-high の pair flop)? 
│  │  └─ → donk **70-86%**（top も mid も）
│  ├ 9-high 以下 connected (987, T76, JT9)?
│  │  └─ → donk **40-60%**（top/mid/bot 問わず）
│  ├ Kxx 等 high-disconnected dry?
│  │  ├─ bottom/mid pair → **38-48%** donk
│  │  └─ top pair (Kxx + K) → **25%** donk
│  └ Q/J/T-high connected (QJ4, T76, JT9)?
│     ├─ top pair → **0%**（IP も保有）
│     └─ mid/bot pair → 0-40%
└ NO (blank/str8/flush) → **0-2%** donk
```

### サイズ

ターン donk のサイズは概ね **33% pot**（連結 board の bottom/mid pair）または **101% pot overbet**（一部 dry board）。
EXTREME donk (AK4+K) では **20% pot** の小サイズで頻繁にバリューを取り続けます。

### 「donk = 0%」が誤りである理由

旧書籍では「ターンの先頭は必ず check し、IP のバレルに反応する」と教えていました。これは **blank turn では正しい** が、**board pair turn では完全に間違い** です。

board pair turn では BB のレンジに 7x, 6x, 8x（ボードの中ランクとペアになるサイドカード）が密に含まれており、turn でその rank がペアになると BB はトリップス・ツーペアに自然に昇格します。一方で IP の cbet レンジは overpair / top pair 中心で、中ランクへのヒットは限定的。BB のレンジが unique に強くなる → リードが GTO 解。

**実戦的覚え方：**
「フロップの 2 枚目・3 枚目のランクがターンでペアになったら、自分のレンジが強くなったか考える。9-high 以下の連結板や AK 系なら donk」

## 8-3　ライン B: プローブベット（probe）の board × turn マトリクス

### probe spot の決定要因

フロップ XX 後にターン OOP が先頭に来るスポットでは、BB の probe 率が **0% から 92% まで board × turn card で激変** します。GTO Wizard で 47 spots を解析した結果が次の表です。

### HIGH probe (50-92%): 連結 wet board × BB hit turn

| Flop + Turn | probe% | サイズ | 解釈 |
|-----------|------:|------|----|
| **9h 7s 5d + 6c** (str8 complete) | **92%** | 33% | BB がストレートを多保有 |
| 9h 7s 5d + 8c (str8 complete) | 66% | 33% | 同上 |
| Td 7c 6s + 8c (str8 complete) | 59% | 33% | 同上 |
| 9h 8s 7d + Td (overcard+str8) | 54% | 33% | BB の T 多 |
| 9h 8s 7d + 9c (top pair on wet) | 51% | 101% | BB が 9x 保有多 |

### MID probe (20-35%)

| Flop + Turn | probe% | サイズ |
|-----------|------:|------|
| Td 7c 6s + 8c (str8) | 30% | 33% |
| AhKd4s + 2c (low blank) | 33% | 101% |
| Ah4d2c + 3h (wheel str8) | 29% | 101% |
| KQ7s mono + 2h (XX 経由) | **22%** | 101% |
| Js9s5s mono + 2h | **21%** | 101% |

### ZERO probe (<5%): 「IP のレンジを直撃する turn」

| Flop + Turn | probe% | 解釈 |
|-----------|------:|----|
| Ah Kd 4s + Kc | **0.1%** | BB に K ほぼ無し |
| Qh Jd 4s + Th | **0.1%** | IP の AKJ/AQJ 完成 |
| Qh Jd 4s + Jh | **0.2%** | IP も J 多 |
| Ks Qd 4h + Qh | **0.1%** | IP も Q 多 |
| Ks Jd 4h + Th | **0%** | IP の KQJT 完成 |
| Jd Ts 8c + Qh | **0.1%** | IP broadway 強化 |
| Ah Kd 4s + Jh | **0.1%** | IP の AKJ 完成 |

### サイズ層

- **33% pot**: wet board + connected/str8 turn（薄め value + ブラフ多）
- **101% pot**: 標準 overbet
- **372% pot**: dry board polarized（ナッツ+ブラフ極化）

### 判定フロー

```
■ ターン probe 判定（フロップ XX 後、OOPが先頭）

1. 「板が IP のレンジを直撃する turn」か？
   例: AK4+K, QJ4+T/J, KQ4+Q, KJ4+T, JT8+Q
   → YES → **probe 0%（必ず check）**

2. wet/connected board + BB hit turn か？
   例: 987+9, T76+8, 9h7s5d+6/8, 987+T
   → YES → **probe 50-92%（積極リード、33% pot）**

3. 連結ボードの blank/scare overcard か？
   例: 987+A scare, T76+J overcard
   → 10-25% probe（控えめ）

4. dry high board の各種 turn か？
   例: Kxx + 各ランク
   → 5-20% probe（基本 check）

5. mono フロップ + blank turn (XX 経由)
   → 20-22% probe (中程度)
```

## 8-4　ライン A: ターン defense と MDF

### MDF と overbet 対応

ターンでの IP cbet サイズは **101% / 157% / 276% の三層構造**（第7章参照）。OOP の MDF はサイズに応じて変化します。

| 相手ベットサイズ | 古典MDF (理論) | OOP fold% (実測) | HSフォールド閾値 |
|:---:|:---:|:---:|:---:|
| 33% pot ※存在しない | 25% | — | — |
| 50% pot | 33% | 33-43% | HS ≥ 35 |
| 75% pot | 43% | 49-53% | HS ≥ 45 |
| **101% pot (regular overbet)** | **50%** | 50-55% | **HS ≥ 50** |
| **157% pot (mid overbet)** | **61%** | 60-65% | **HS ≥ 60** |
| **276% pot (huge overbet)** | **73%** | 70-75% | **HS ≥ 70** |

**重要：** MTT6mSimple では IP のターン cbet サイズは 101% 以上の overbet 主流です。古典的な「vs 33% → fold 25%」の判断は **フロップ cbet defense** で使う数値であり、ターンでは 101% / 157% / 276% への対応が中心になります。

### ターン HS フォールド閾値テーブル（修正版）

| サイズ | SRP の HS 閾値 | 3BP の HS 閾値 |
|:---:|:---:|:---:|
| 101% bet | **HS ≥ 50** | HS ≥ 55 |
| 157% bet | **HS ≥ 60** | HS ≥ 65 |
| 276% bet | **HS ≥ 70**（バリュー以上のみ） | HS ≥ 75 |

ターンの閾値がフロップより 10-15 高い理由は、フロップCBetをコールしたことでレンジが絞られているためです。
フロップでエアーのほとんどがフォールドしているため、ターン開始時の OOP レンジは HS20〜65 のマージナル以上が中心になります。
この分布の中で上位 MDF% を守ると HS 閾値が上昇します。

### バリュー・マージナル・エアー別の対応

| 状況 | アクション |
|---|---|
| 101% bet × バリュー（HS≥65） | コール、状況により CR |
| 101% bet × マージナル（HS50-64） | コール（SDV 期待） |
| 101% bet × エアー | フォールド |
| 276% bet × バリュー（HS≥70） | コール（ただしブラフキャッチは避ける） |
| 276% bet × マージナル | フォールド（過大サイズに対し HS<70 は降りる） |
| 276% bet × エアー | フォールド |

### マージナルでのコール/フォールド判断フロー（改訂）

マージナル（HS35〜64）はターン最大の判断難所です。サイズ別に判断します：

```
マージナルのターンディフェンス判断（サイズ別）

vs 101% bet（regular overbet）:
├─ SPR ≥ 6（SRP） → HS ≥ 50 でコール
├─ SPR 3〜5（3BP） → HS ≥ 55 でコール
└─ SPR < 3（4BP） → HS ≥ 60 でコール（コミット気味）

vs 157% bet（AK系 mid-overbet）:
├─ SPR ≥ 6 → HS ≥ 60 でコール
└─ SPR < 6 → HS ≥ 65 でコール

vs 276% bet（dry/broadway overbet）:
└─ HS ≥ 70 のみコール（バリューのみ、マージナルは降りる）
```

276% bet に対する応戦は厳しいですが、相手のレンジが「ナッツ+air」に極化されているため、ブラフキャッチで勝てる頻度が下がります。HS 65 程度のマージナルでも降りるのが GTO 整合です。

## 8-5　レンジ逆算とリバー計画

ターンの defense / probe / donk すべてに共通するのは「次のストリート（リバー）で何をしたいか」を先に決めるアプローチです。

### フロップアクション別レンジ推定（目安）

| フロップ展開 | ターン開始時の IP レンジ | OOP レンジ |
|---|---|---|
| IP CBet → OOP コール | マージナル以上（バリュー中心） | マージナル以上（HS≥35） |
| IP チェックバック | SDV中心（HS 35〜55） | 全レンジ残存 |
| IP CBet → OOP CR | バリュー必要 | バリューのみ |
| IP CBet → OOP フォールド | マージナル以上（バリュー中心） | （降りた） |

### リバー計画と本ターンアクション

ターンでコールすると、ほぼ確実にリバーでのベットに直面します。
フロップCBet→ターンバレルと打ってきた相手がリバーで突然チェックするケースは全体の30%未満にとどまります。

リバー計画の選択肢：
- **リバーバリュー狙い** → ターンで CR してポット拡大、または call で受けて river も call
- **SDV 狙い** → ターン call、river 相手 check なら check-down
- **ブラフキャッチ撤退** → ターン fold（マージナル下位ハンド）

特に **276% overbet を受けた場合**、リバーでもさらに overbet が来ると pot は元の 7-10 倍に膨張します。HS 70 未満のハンドはターン時点で降りるのが期待値を守ります。

## 8-6　例題（auto-generated）

| ハンド | ボード | HS（バケット）| ボード型 | ポット種別 | 答え |
|---|---|---|---|---|---|
| A♥K♦ | K♠7♦2♣-3♥ | 70（強（バリュー））| 型1: ハイ×ドライ | SRP（HU, SPR≈18） | CHECK（TA-だがバリュー、選択的CBet可） |
| K♣J♠ | A♠K♦4♣-K♥ | 75（強（バリュー））| AK系 | SRP（HU, SPR≈18） | **DONK 86%** |
| 8♥7♦ | 9♥8♠7♦-8c | 65（バリュー）| 型4: コネクテッド | SRP（HU, SPR≈18） | **DONK 60%**（mid pair on wet） |
| Q♥J♦ | Q♥J♦4♠-Q♣ | 88（強）| 型2 | SRP | CHECK（top pair on Q-high → IP も持つ） |
| J♠T♠ | 9♥7♠5♦-6♣（XX後） | 65 | 連結 | SRP | **PROBE 92%**（str8 complete on wet） |
| 9♣9♦ | K♠7♦2♣-J♥ | 30（エアー）| 型1 vs 276% bet | SRP | **FOLD**（276% overbet, マージナル下位） |

**解説**

例題① A♥K♦ on K72-3 ブランクは TA-、ターン donk もありません（Kxx + blank → 0%）。バリューなら選択的 CBet で打てますが、ここはチェックでショーダウンを目指します。

例題② K♣J♠ on AK4-K は **AK系 EXTREME TA+** の典型。OOP donk **86%** で打つのが GTO。20% pot のスモールサイズでバリューを取り尽くします。

例題③ 8♥7♦ on 987-8 は wet connected の mid pair turn。OOP donk **60%** で打ちます。BB のレンジには 8x（87s, T8s, 8♠8♣ 等）が密にあり、IP より range advantage を持つため。

例題④ Q♥J♦ on QJ4-Q は **top pair on Q/J board → donk 0%**。理由は IP の cbet レンジに Qx も豊富で、turn の Q が IP も強化する → BB は unique 優位を持たない。Check して IP の barrel に対応する形が GTO。

例題⑤ J♠T♠ on 975-6 (XX 経由) は **probe 92%** の最強リードスポット。str8 を完成させ、BB のレンジは strs8 を多保有。33% pot small bet でブラフキャッチを誘発します。

例題⑥ 9♣9♦ on K72-J vs 276% overbet。9♣9♦ は HS 30 のエアー寄り。276% overbet に対する MDF は fold 73% で、HS 70 未満は降りるのが GTO。

## 8-7　まとめ：ターンの3シナリオ判断フロー

```
■ OOPのターン判断（3シナリオ分岐）

Step 1: フロップでの最後のアクションを確認
├─ IP cbet → OOP コール → IP turn first → ライン A (defense)
├─ IP cbet → OOP コール → OOP turn first → ライン C (donk)
└─ flop X-X → ターン両者まだ → ライン B (probe)

ライン A: defense
├─ サイズ確認 (101% / 157% / 276%)
├─ HS 閾値判定 (HS ≥ 50/60/70)
├─ バリュー → コール or CR
├─ マージナル → SPR 依存
└─ エアー → フォールド

ライン C: donk
├─ Turn は board pair?
│  ├─ YES + AK系 → 86% donk
│  ├─ YES + 連結 board → 40-60% donk
│  ├─ YES + dry mid/bot pair → 38-48% donk
│  ├─ YES + top pair on Q/J/T board → 0% donk (check)
│  └─ NO (blank/str8) → 0% donk
└─ サイズ: 33% pot (連結) or 101% (dry)

ライン B: probe
├─ Turn は IP のレンジ直撃 (AK4+K, QJ4+T 等)?
│  └─ YES → 0% probe (check)
├─ Wet connected + BB hit turn?
│  └─ YES → 50-92% probe (33% pot)
├─ Mid blank on wet?
│  └─ 20-35% probe (101% pot)
├─ Dry board?
│  └─ 5-20% probe
└─ Mono flop XX 後?
   └─ 20-22% probe
```

この3ライン分岐を頭に入れておくと、ターンでの「何をすべきか」が一瞬で分かります。

---

### 【GTOとのズレ】

GTO Wizard 268 spots study によって、ターン OOP の戦略が劇的に書き換わりました。旧来の「OOP turn donk = 0%」「probe spot は wet で多用」という大雑把な指導は、実際の GTO 解とは大きく乖離しています。

特に重要な訂正点：

1. **ターン donk は board pair turn で 25-86% が GTO**。「常に check」は誤り
2. **probe spot は 0% から 92% まで board × turn card で変動**。一律の頻度はない
3. **AK4 系の top/mid pair turn では donk 70-86%** という極端な高頻度
4. **「IP のレンジ直撃 turn」(AK4+K, QJ4+T 等) では probe = 0%** が GTO

これらは GTO Wizard 解析を通じて初めて定量化された境界です。本書のフローチャートは 268 spots の境界データから直接導出した判定ルールであり、実戦では「board × turn card」のパターン認識で 9 割の判断が即時に可能になります。
