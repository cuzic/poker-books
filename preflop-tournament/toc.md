# 迷わないポーカー MTTプリフロップ編 — 目次・執筆ガイド

**対象**: 8-max MTT、BB アンテあり、SBR 8〜40BB  
**スコア式**: v4（MTT 専用 — キャッシュゲーム式とは別物）  
**データソース**: GTO Wizard MTTGeneral 実測 (2026-05-19)

---

## 核心フレームワーク（全章共通の参照軸）

### MTT スコア式 v4

```
非ペア:
  基本       : H + L
  スーテッド  : +5
  オフスーツ  : -3（L < 10 のみ。KJo/ATo/QJo など L≥10 は無罰）
  gap=1      : +2
  gap=2      : +1
  gap=3      : -0.5
  gap=4      : -1.5, gap=5: -2, gap≥6: -3（A 以外）
  A-ブロッカー: +3（L≤3 はさらに -2）
  低カード補正: H<9 かつ L<9 → -1

ペア: H + L + 10（AA は +3, KK は +2 追加）
```

### ゾーン定義

| ゾーン | SBR 範囲 | 主な行動 |
|--------|---------|---------|
| **Zone P** | 8〜14BB | Push / Fold（min-raise ほぼなし） |
| **Zone T** | 14〜20BB | Push + min-raise 混在（移行帯） |
| **Zone O** | 20〜40BB | min-raise 主体（push は一部のみ） |

### T_open 早見表（非ペア閾値・v4 スコア）

| SBR | UTG  | UTG1 | UTG2 | HJ   | CO   | BTN  |
|-----|------|------|------|------|------|------|
| 20  | 23.5 | 23   | 21   | 19   | 17   | 14   |
| 25  | 22.5 | 22   | 21   | 17   | 15   | 14   |
| 30  | 22   | 21   | 19   | 17   | 17   | 13   |
| 40  | 21   | 21   | 17   | 17   | 15   | 13   |

### 最低オープンペア表（ペアはスコア計算不要・直接参照）

| SBR | UTG | UTG1 | UTG2 | HJ  | CO  | BTN |
|-----|-----|------|------|-----|-----|-----|
| 8   | 22+ | 22+  | 22+  | 22+ | 22+ | 22+ |
| 10  | 44+ | 33+  | 22+  | 22+ | 22+ | 22+ |
| 12  | 55+ | 44+  | 33+  | 22+ | 22+ | 22+ |
| 14  | 66+ | 55+  | 44+  | 22+ | 22+ | 22+ |
| 17  | 66+ | 66+  | 66+  | 55+ | 22+ | 22+ |
| 20  | 66+ | 66+  | 55+  | 55+ | 44+ | 22+ |
| 25  | 55+ | 55+  | 44+  | 44+ | 44+ | 44+ |
| 30  | 44+ | 44+  | 33+  | 33+ | 33+ | 33+ |
| 40  | 44+ | 33+  | 22+  | 33+ | 33+ | 22+ |

---

## 章構成（17 章 + 3 付録 = 20 ファイル）

### Part I: 基礎（2 章）

#### Ch00: はじめに — MTT プリフロップ判断の特殊性
`chapters/00-introduction.md`

**主要トピック**:
- キャッシュゲームとの 3 つの違い（スタック深度の変動・ICM 圧力・BB アンテ効果）
- 本書の使い方（ゾーン判定 → 該当章を参照）
- GTO Wizard MTTGeneral データについて（8-max, BB ante, chip EV）

**字数目安**: 3,000 字

---

#### Ch01: MTT スコア式（v4）
`chapters/01-score-formula.md`

**主要トピック**:
- v4 フォーミュラの設計思想（なぜキャッシュと別式が必要か）
- 非ペア計算手順（H+L → suited/offsuit補正 → gap補正 → ブロッカー → 低カード補正）
- ペアの扱い（スコア不要・最低ペア表を直接参照）
- 主要境界ハンドのスコア例（T8s=24, K7s=22, A9o=23 など）
- 式の精度（UTG 96%, HJ 87%, CO 85%）と限界（BTN は 2 段階ルール推奨）

**核心式**:
- score_mtt(h) = H + L [+ suited bonus] [± gap/blocker/low adjustments]

**字数目安**: 5,000 字

---

### Part II: ゾーンシステム（1 章）

#### Ch02: ゾーン P/T/O — スタック深度で判断を切り替える
`chapters/02-zone-system.md`

**主要トピック**:
- Zone P（SBR ≤ 14BB）の特徴: min-raise がほぼ存在しない push/fold 世界
- Zone T（SBR 14〜20BB）の特徴: push と min-raise が混在する移行帯
- Zone O（SBR 20〜40BB）の特徴: min-raise 主体、push は AA/KK 等のごく一部
- SBR の計算方法（自分のチップ ÷ BB サイズ）
- 実戦での判断フロー（SBR を見る → ゾーン確認 → 該当フレームワーク適用）
- BB アンテがゾーン境界に与える影響

**字数目安**: 4,000 字

---

### Part III: Zone P — ショートスタック Push/Fold（3 章）

#### Ch03: Zone P 全体像 — ペア表と T_push 閾値（SBR 8〜14）
`chapters/03-zone-p-overview.md`

**主要トピック**:
- Push/Fold の基本原則（コールされる手でも全額投入）
- ペアの push 境界（最低オープンペア表の読み方）
  - SBR=10: UTG は 44+ / BTN は 22+ （全ペア）
  - SBR=12: UTG は 55+ / BTN は 22+
- 非ペアの T_push（全ポジション × SBR 表）
- UTG の特殊性（T_push=27 at SBR=12 vs BTN=14）
- 精度の現実（EP は 93-99%、LP は 60-76%）

**字数目安**: 5,000 字

---

#### Ch04: EP の Push 判断（UTG/UTG1）
`chapters/04-ep-push.md`

**主要トピック**:
- UTG T_push の SBR 別変化（SBR=8: 22 → SBR=12: 27 → SBR=14: 25）
- SBR=8 の特殊パターン（T=22 だが K8s/T8s は折れる → "Ax 全手 + KJo+ + JTs/QTs + 22+" で暗記）
- SBR=14: push vs min-raise の分岐（AJo/KQs は push、A9s/T9s は min-raise）
- 非ペア push 確定リスト（SBR=10, 12, 14 別）
- UTG1 との差（UTG より 1-2 ポイント広め）
- 【GTO とのズレ】コラム: ICM バブル・FT では EP さらに tight

**字数目安**: 5,500 字

---

#### Ch05: LP の Push 判断（CO/BTN/SB）
`chapters/05-lp-push.md`

**主要トピック**:
- CO/BTN は SBR=8〜12 でほぼ全手 push（T_push ≈ 13-15）
- BTN の実用ルール（「ゴミ hand 以外は全部 push」）
- SB の 2 モード: push vs limp（T_push は純 push 閾値、リンプは別節）
- SB リンプ罠（Limp Trap）: SBR≤12 でプレミアム手（AA/KK/AKs/QQ/JTs 等）はリンプ
  - 理由: push ではフォールドエクイティが小さく、BB 誘い込みでスタック全額取りを狙う
- BB ディフェンス vs push（push に直面した BB の判断）
  - call: 22/33, 弱いスーテッド
  - re-push: 44+ 以上のペア、Ax 全般
  - fold: 純ゴミ手のみ

**字数目安**: 5,500 字

---

### Part IV: Zone T — 移行帯（1 章）

#### Ch06: Zone T — push と min-raise が混在する SBR 14〜20
`chapters/06-zone-t-transition.md`

**主要トピック**:
- SBR=14 の構造: EP は strong hand を push、中程度を min-raise
  - push確定: AKo/AQo/KQs/KJs/KTs/QJs/JTs/AJo（score≥28）
  - min-raise: A9s/A8s/A7s/A5s/T9s/K9s
  - fold: A3s 以下、QJo 以下
- SBR=17 の変化: 全ポジションで push がほぼ消え min-raise 主体に
- SBR=14〜20 の T_open（K-3 表）
- 移行帯でのペア判断（SBR=14 で UTG は 88 を push、SBR=17 では min-raise）
- SB のリンプ比率変化（SBR=14 で 53%、SBR=20 後も継続）

**字数目安**: 4,500 字

---

### Part V: Zone O — オープンレイズゾーン（3 章）

#### Ch07: Zone O — 全ポジション T_open と基本判断（SBR 20〜40）
`chapters/07-zone-o-open.md`

**主要トピック**:
- オープンサイズの変化（SBR≤20: R2 / SBR=25-30: R2.1 / SBR=40: R2.3）
- T_open 全ポジション × SBR 表（H-3 表の書籍版）
- MTT の T_open がキャッシュより低い理由（BB ante 効果で pot odds が改善）
  - UTG: MTT=21 vs キャッシュ=24（差-3）
  - HJ: MTT=17 vs キャッシュ=22（差-5）
  - BTN: MTT=14 vs キャッシュ=18（差-4）
- ペア別最低オープン表（スコア計算不要）
- BTN のほぼ全手参加（T=14 ≈ 弱いオフスーツ以外すべて）
- K-ブロッカーの限界（K7s がスコア高くても折れる — RFI では blocker 価値が低い）
- 【GTO とのズレ】コラム: アンテなし・9-maxへの調整

**字数目安**: 5,500 字

---

#### Ch08: BB ディフェンス（vs 各ポジション）
`chapters/08-bb-defense.md`

**主要トピック**:
- BB の基本方針: 「fold は最低限のゴミ手のみ、3-bet は価値ハンドと少数ブラフのみ、残りはコール」
- フォールド条件（スーテッドは常にコール、low connector もコール）
  - T_fold ≈ 12 vs UTG / 8 vs BTN
- T_3bet_value = 27〜28（ATo/KQo 以上の非ペア）
- 3-bet 確定リスト vs UTG（4 手）と vs BTN（14 手）
- ブラフ 3-bet の補完（vs BTN: T9s/T8s/98s + K6-7s）
- ペアの判断（99+ → 3-bet vs UTG; 22+ → 3-bet/push vs BTN）
- BB vs SB open の特殊性（SB は大きいサイズで開く → T_call が低い=広くコール）
- SBR 別変化（SBR=17/20/25/30 の T_fold・T_3bet 表）
- MW での BB 参加縮小（cold caller が増えるほど Axo/Kxo 弱が fold 転換）

**字数目安**: 6,000 字

---

#### Ch09: SB ディフェンス（vs BTN オープン）
`chapters/09-sb-defense.md`

**主要トピック**:
- SB の特殊性: OOP のため fold 65%（キャッシュより tight）
- 3-bet 28 手の構成（Ax suited / Ax offsuit strong / Broadway / KQo-KJo）
- コール 19 手の構成（K5-KJs / suited connector gap≤4 / Broadway offsuit / A7-8s 例外）
- ペアは全部 push（22-AA）
- fold 109 手（全体の 65%）
- 記憶補助: "3-bet = Ax か strong Broadway、コール = K-suited か suited mid connector か Broadway offsuit"
- SBR 別コール範囲の変化（SBR=17: 11手 → SBR=25: 19手）
- SB vs 他ポジションオープン（UTG/HJ/CO への 3-bet 閾値）

**字数目安**: 5,500 字

---

### Part VI: IP の行動パターン（3 章）

#### Ch10: IP コールドコール（HJ/CO/BTN/SB が先行オープンに直面）
`chapters/10-ip-cold-call.md`

**主要トピック**:
- IP コールドコールの価値（position + pot odds）
- T_3bet(IP) ≈ 30 vs UTG（全ポジション共通 — BB より tight）
  - vs HJ/CO は緩む: BTN は T_3bet=16、SB は T_3bet=14
- 代表的な IP 3-bet ハンド（AA/KK/AKs/AKo 確定、QQ/JJ/AQo 混在）
- BTN コールドコール vs UTG の 2 段階ルール:
  - スーテッド/ペア: score ≥ 20
  - オフスーツ: score ≥ 27 (かつ L ≥ 10)
- HJ cold call の注意（SBR<25 ではツリー未計算 = 実戦でも稀なシナリオ）
- BTN vs HJ/CO の広いコール（T_3bet が低く = cold callが多い）
- BB vs SB: T_call=7-10（SB の大きいオープンサイズで BB は広くコール）

**字数目安**: 5,500 字

---

#### Ch11: 3-bet に直面したら（fold/call/shove）
`chapters/11-facing-3bet.md`

**主要トピック**:
- Zone O での 4-bet: サイズなし → fold/call/shove（オールイン）のみ
- UTG vs BB 3-bet（SBR=25 T_shove=27, T_call=22）
  - shove: KK/AKs/AKo（6 手）
  - call: AA + QQ/JJ/TT 一部 + AQs/AQo（22 手）
  - fold: UTG の残りオープンレンジ（T9s など低スコアのほとんど）
- BTN vs BB 3-bet（T_shove=16, T_call=16 → T=16 以上で shove or call）
  - UTG より大幅に広い対処（51 手）
- CO/HJ vs 3-bet（中間の閾値）
- SBR 別安定性（UTG T_shove=26-27 across SBR=20/25/30）
- 実戦フロー（T_shove と T_call の 2 閾値で 3 分割）
- 【GTO とのズレ】コラム: ICM バブルでは fold が増える

**字数目安**: 5,500 字

---

#### Ch12: スクイーズ（オープン + コールドコールへの参入）
`chapters/12-squeeze.md`

**主要トピック**:
- スクイーズの有利性（cold caller が手の強さを絞り込んでいる + pot が大きい）
- BTN スクイーズ（UTG/HJ 絡み）: T_sq ≈ 27-28（高い要件）
  - 代表手: AA/KK/AK/AQ/JJ+
- SB スクイーズ（UTG 起点）: T_sq ≈ 25-26
- SB スクイーズ（CO/HJ 起点）: T_sq ≈ 20-22（ポットが小さくより入りやすい）
- BB 2 つのモード:
  1. Tight（UTG/HJ 起点）: T_sq=22-26, 価値ハンドのみ
  2. Wide/Polar（BTN+SB）: T_sq=14, 広いポーラー range（ペア全部 + Axo ブラフ）
- SBR 別安定性（SB T_sq は SBR によらず 24-25.5 で安定）
- スクイーズ vs 単純コール/fold の選択基準

**字数目安**: 5,000 字

---

### Part VII: 多人数ポット（1 章）

#### Ch13: MW（多人数ポット）での BB/SB 参加基準
`chapters/13-multiway.md`

**主要トピック**:
- MW の基本原則（cold caller の増加で参加範囲を絞る）
- BB の MW 縮小パターン（HU: 82% → UTG+HJ+CO: 60.4%）
  - fold 転換する手: Ax offsuit 弱、Qx offsuit、Kx offsuit 弱、Jx offsuit 弱
  - ルール: "MW Level 1（cold caller 2人以上）では弱いオフスーツ全般を fold"
- BB の 3-bet サイズ拡大（HU=R7.5 → MW 2 callers=R8.6 スクイーズ効果）
- SB の MW 参加縮小（SB vs UTG+BTN: T_sq=25.5 安定）
- BTN のコールドコール範囲 MW 調整（既存 caller がいれば fold ポイントが上がる）
- MTTMRonly との比較（SB リンプあり vs なしで cold call 構造が変わる）

**字数目安**: 4,500 字

---

### Part VIII: 総括とドリル（1 章）

#### Ch14: 実戦フロー確認と境界ハンド一覧
`chapters/14-drill.md`

**主要トピック**:
- 意思決定フロー全体像（SBR → ゾーン → ポジション → スコア計算 → 閾値比較）
- 各ゾーン境界ハンドの確認問題（SBR=10 UTG で A9o は？ / SBR=25 BTN で T8s は？）
- よくある判断ミス Top 5（SB リンプ trap 忘れ、BTN が広すぎる push など）
- GTO Wizard との精度ギャップの受け入れ方

**字数目安**: 4,000 字

---

### 付録

#### 付録 A: MTT スコア v4 早見表（主要 169 手）
`chapters/appendix-a-score-table.md`

**内容**: 全 169 手のスコア一覧表（スーテッド/オフスーツ別）
**字数目安**: 2,500 字

---

#### 付録 B: SBR 別参照カード（Zone P/O の閾値まとめ）
`chapters/appendix-b-reference-cards.md`

**内容**:
- Zone P: T_push 表 + 最低オープンペア表（SBR=8/10/12/14）
- Zone O: T_open 表（SBR=20/25/30/40）+ BB/SB defense 要約
**字数目安**: 3,000 字

---

#### 付録 C: 境界ハンドリスト（暗記推奨）
`chapters/appendix-c-boundary-hands.md`

**内容**:
- SBR=25 UTG: 最低オープン非ペア（98s, T8s, K8s あたり）
- SBR=25 BTN: スーテッド score=14 境界
- SBR=12 SB: リンプ trap 対象ハンド
- BB 3-bet 確定リスト（vs UTG / vs BTN）
- SB コール 19 手リスト
**字数目安**: 2,500 字

---

## 全章文字数見通し

| Part | 章数 | 目安字数 |
|------|-----|---------|
| I 基礎 | 2 | 8,000 |
| II ゾーンシステム | 1 | 4,000 |
| III Zone P | 3 | 16,000 |
| IV Zone T | 1 | 4,500 |
| V Zone O | 3 | 17,000 |
| VI IP 行動 | 3 | 16,000 |
| VII MW | 1 | 4,500 |
| VIII ドリル | 1 | 4,000 |
| 付録 | 3 | 8,000 |
| **合計** | **18** | **82,000** |

---

## 執筆上の注意事項

1. **式の表記統一**: スコア変数は `score_mtt(h)` で統一（キャッシュの `preflop_score` とは別）
2. **SBR 表記**: 常に「SBR=25BB」ではなく「SBR=25」（BB は省略）
3. **ポジション表記**: 8-max を前提。UTG=UTG、UTG1、UTG2、HJ、CO、BTN、SB、BB
4. **精度表記**: 「式の精度は 96%（誤分類 6/169 手）」のように具体的に
5. **GTO とのズレ コラム**: 各章末に設置。ICM 補正（Elite 必要）の注意書きを記載
6. **Zone P は SBR 前後の BB アンテ有無に注意**: SBR=8 は depth=8.125 (BB ante 0.125)
7. **SB のリンプ**: MTTGeneral では SB のリンプが存在する（MTTMRonly はリンプなし）

---

## データソース一覧

- `preflop-tournament/PHASE1_2_FINDINGS.md`: Section A-K（Zone P/O/T 全データ）
- `preflop-tournament/PHASE1_2_FINDINGS.md`: Section L-N（IP cold call / 3-bet / squeeze）
- `preflop-tournament/PHASE3_5_FINDINGS.md`: Section B（MW データ）
- `poker-drill/scripts/precompute/verify_formula_tournament.py`: 分析スクリプト（再現可能）
- `poker-drill/scripts/precompute/fetch_tournament.py`: データ収集スクリプト
