# Vol2/Vol3 目次草案 (2026-05-12)

## 状態: DRAFT — GTO 調査結果待ち
## 最終確定: pot10 study + CR/river study 完了後

---

## Vol2: 迷わないポーカー② フロップ[基礎]

**コンセプト:** SRP フロップで「なぜ、どう動くか」のロジックと計算式を習得する。
アクション判断のフローを暗算できる形に圧縮。

**想定読者:** フロップを感覚でやっている初中級者。式を覚えて次の一手を決めたい人。

**GTO データ依存:** 主に accuracy30 ボード 30 枚 (pot10 study)

---

### 目次

| 章 | タイトル | 核心コンテンツ | 必要 GTO データ |
|---|---------|-------------|--------------|
| 序 | フロップを制するとは | SRP 標準状況 (BTN vs BB, pot=6bb) の解説 | — |
| 01 | ボードを7タイプに分ける | Board Score B の9ルール | pot10: BS × board count |
| 02 | ハンドスコアを計算する | HS = role_score + draw_bonus + 2OC_bonus | — |
| 03 | T1/T2/T3 ティアシステム | T1≥65, T2≥20, T3<20. H1/H2/H3 からの改善点 | pot10: HS 分布 |
| 04 | CBet 判断の黄金律 | T1常時, T2→B≥58, T3→B≥67 | pot10: CBet freq × tier |
| 05 | CBet サイズ選択 | paired_high/mono→50%, 他→75% | pot10: size dist. |
| 06 | OOP のフォールド閾値 | base + texture correction テーブル | pot10: oop_fold_vs33/75 |
| 07 | C値: どれだけ押すか | C = α × 50, 33%→12, 75%→22 | — |
| 08 | Check-raise の基礎 | OOP がなぜ check-raise するか (概要) | CR study: oop_cr_vs33/75 |
| 09 | Check-check と弱いゲーム | IP check-back の意味, flop SD value | — |
| 10 | 実戦フロー図 | T1/T2/T3 × B threshold の統合フロー | 全 GTO データ |
| 付録A | 代表30ボード参照表 | CBet 推奨・サイズ・フォールド閾値一覧 | pot10 accuracy30 |
| 付録B | ハンドスコア計算例 | 30 hands × 5 boards 計算例 | — |

**章数合計:** 10章 + 2付録

---

### 核心式

```
Board Score B:
  mono → 70, paired_high(T+) → 83, paired_low → 71
  2tone_AK → 56, 2tone → 50
  rainbow_connected(spread≤3, top≥J) → 67
  rainbow_AK → 62, rainbow_Q → 58, rainbow → 55

Hand Score HS:
  HS = role_score + draw_bonus + 2OC_bonus
  draw_bonus: NFD=+36, FD=+32, OESD=+28, GS=+12, BDFD=+6
  2OC_bonus: +24 if both hole cards > max(board)

Tier:
  T1 ≥ 65, T2 ≥ 20, T3 < 20

CBet decision:
  T1 → always
  T2 → B ≥ 58
  T3 → B ≥ 67

Fold threshold:
  vs33% → 15, vs50% → 25, vs75% → 35
  +5 (2tone), -5 (mono), -10 (paired)
```

---

## Vol3: 迷わないポーカー③ フロップ[応用]

**コンセプト:** レンジ思考とフロップの深掘り。相手のレンジを読みながらアクションを選択。
Check-raise・ドンクベット・ブラフ構築の原理。

**想定読者:** Vol2 修了者。レンジという概念を実戦に活かしたい中級者。

**GTO データ依存:** pot10 study (CB by category) + CR study (check-raise)

---

### 目次

| 章 | タイトル | 核心コンテンツ | 必要 GTO データ |
|---|---------|-------------|--------------|
| 序 | レンジで考える | BTN open range / BB defend range の基礎 | — |
| 01 | フロップでのレンジ優位 | Nut advantage, Equity advantage | — |
| 02 | ハンドカテゴリ別 CBet 分析 | overpair/TP/2OC/air の CBet 率 GTO 実測値 | pot10: cbet_overpair/top_pair/2OC/air |
| 03 | ボードテクスチャ × CBet 精度 | 30 ボードでの CBet 精度 (GTO との比較) | pot10: accuracy30 |
| 04 | Check-raise 詳細 | いつ・何で・どのサイズで CR するか | CR study: oop_cr × hand_cat |
| 05 | Check-raise レンジ構成 | Made hands + Draws のバランス | CR study: CR breakdown |
| 06 | ドンクベット | OOP ドンクの GTO 頻度と使いどころ | CR study: oop_donk_pct |
| 07 | OOP コーリングレンジ | Check-call vs Check-fold の境界 | pot10: oop_fold/oop_call |
| 08 | サイズ・テル | IP サイズ変化から相手レンジを推定 | pot10: IP size distribution |
| 09 | マルチストリート展望 | フロップでターンを計画する (SPR) | — |
| 10 | ブラフ選択原則 | ブロッカー × エクイティ × ポジション | — |
| 付録A | ハンドカテゴリ別 CBet 参照表 | 30 ボード × 4 カテゴリの GTO 実測値 | pot10 accuracy30 |
| 付録B | Check-raise 参照表 | 15 ボード × OOP CR 頻度一覧 | CR study |

**章数合計:** 10章 + 2付録

---

### 核心式

```
C値 (aggression factor):
  C = α × 50  (α = bet_size / (pot + bet_size))
  33%→C=12, 50%→C=17, 75%→C=22, 100%→C=25, 150%→C=30

Check-raise sizing:
  vs33% CBet → 3× bet = pot × 0.33 × 3 ≈ pot size (effective CR ≈ pot)
  vs75% CBet → 3× bet ≈ 2.25× pot (larger, more polarized)

OOP defense frequency (MDF):
  MDF = 1 - α
  vs33% → MDF=75%  vs75% → MDF=57%

V:B ratio at river (α-based):
  α=25% → 3:1, α=33% → 2:1, α=50% → 1:1, α=60% → 3:2
```

---

## GTO 調査進捗 (この目次に必要なもの)

| データ | 調査状況 | 用途 |
|-------|---------|-----|
| pot10 accuracy30 (CBet freq) | 🔄 実行中 (8/38 完了) | Vol2 ch01-07, Vol3 ch03 |
| pot10 CBet by hand category | 🔄 実行中 | Vol3 ch02 |
| pot10 OOP fold rates | 🔄 実行中 | Vol2 ch06 |
| CR study (OOP check-raise) | 🔄 実行中 (0/15 完了) | Vol2 ch08, Vol3 ch04-05 |
| CR study (OOP donk) | 🔄 実行中 | Vol3 ch06 |
| River study | 🔄 実行中 (0/12 完了) | Vol5 ch02-05 |
| Turn probe/OOP barrel | ❌ 未調査 | Vol4 ch07 |

## 執筆前に最終確認が必要な項目

1. **2OC bonus +24 の境界確認:** AQo on K72r (HS=25, T2) は GTO でも CBet 推奨か?
   → pot10 結果で `cbet_two_overcards` を確認

2. **Check-raise サイズ分布:** OOP がどのサイズで CR するか (min-raise? 3×? pot?)
   → CR study 結果で確認

3. **ドンクベット頻度:** GTO でどのボードで OOP ドンクが多いか
   → CR study `oop_donk_pct` で確認

4. **T3 CBet 閾値 B≥67 の精度:** GTO 168board で 85.2% → accuracy30 でも確認
   → pot10 の T3 シナリオで確認
