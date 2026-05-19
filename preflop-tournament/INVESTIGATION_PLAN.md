# プリフロップ トーナメント編 — GTO Wizard 調査計画

**作成日**: 2026-05-19
**目的**: 『迷わないポーカー プリフロップ トーナメント編』の執筆に必要な
GTO データを系統的に収集し、キャッシュゲーム版のスコア式をトーナメントに拡張する。

---

## 1. キャッシュゲームとの根本的違い

| 項目 | キャッシュゲーム | トーナメント |
|---|---|---|
| 判断基準 | Chip EV | ICM ($EV / survival value) |
| スタック | 固定 100BB | SBR（スタック/ブラインド比）が局面を支配 |
| プリフロップ構造 | レンジ × 閾値 | SBR ゾーン × ICM × アンテ |
| MW 頻度 | 低い (N≤2) | 序盤は N≥3 が頻発 |
| アンテ | なし | BB ante / button ante が標準 |
| オープンサイズ | 2.5BB | 2BB min-raise が主流 |

**核心命題**: キャッシュゲームのプリフロップスコア式（同一）を使い、
SBR 別の閾値表と ICM 補正ルールで拡張できるか？

---

## 2. 書籍コンセプト（仮）

**タイトル案**: 迷わないポーカー プリフロップ トーナメント編
**サブタイトル案**: ―スタック深度と ICM で変わる判断フロー―

### 5 部構成案

| 部 | テーマ | SBR 範囲 |
|---|---|---|
| 第 I 部 | Push/Fold 判断 | 8〜20BB |
| 第 II 部 | Open-Raise ゾーン | 20〜40BB |
| 第 III 部 | ICM 補正 | バブル / FT |
| 第 IV 部 | アンテ補正 | BB ante あり |
| 第 V 部 | MW 多人数ポット (N≥3) | 序盤深スタック |

---

## 3. 調査フェーズ一覧

```
Phase 0  GTO Wizard トーナメント対応確認       ← まず実施
Phase 1  Push/Fold 閾値（コア）                ← 最優先
Phase 2  Open-Raise ゾーン (20-40BB)
Phase 3  ICM 効果（バブル / FT）
Phase 4  アンテ効果
Phase 5  MW N≥3（トーナメント序盤）
Phase 6  オープンサイズ効果 (2BB vs 2.5BB)
```

---

## Phase 0: GTO Wizard トーナメント対応確認

**目的**: 利用可能なゲームタイプ・API パラメータを把握する。

### 確認事項

1. トーナメント専用ゲームタイプの一覧取得
   ```
   GET https://api.gtowizard.com/v2/game-modes/
   ```
   キャッシュ: `Cash6mGeneral_6mNL25R25`, `Cash6m500zGeneral25Open3betV2`
   トーナメント: `MTT*`, `SNG*`, `PKO*` 系が存在するか確認

2. SBR（スタック深度）パラメータの確認
   - `depth=` パラメータで BB 換算スタック深度が指定可能か
   - または専用の `stack=` パラメータが存在するか

3. ICM モデルパラメータの確認
   - バブル係数、賞金分布の指定方法

4. アンテ設定の確認
   - BB ante あり/なしの切り替え方法

### 出力
- 利用可能なゲームタイプ一覧 → `raw_ranges_tournament/game_types.json`
- API パラメータ仕様メモ → `raw_ranges_tournament/api_spec.md`

---

## Phase 1: Push/Fold 閾値（コア ★★★）

**目的**: SBR 8〜20BB での各ポジション push/fold 境界スコアを確定する。

### 対象 SBR

| SBR | 意味 |
|---|---|
| 8BB | 超短スタック — ほぼ全て push/fold |
| 10BB | 短スタック標準 |
| 12BB | push/fold 上限付近 |
| 15BB | 重要な境界（min-raise も選択肢） |
| 17BB | min-raise 主体に移行 |
| 20BB | 上限（open-raise ゾーンに接続） |

### 収集シナリオ（各 SBR × ポジション）

```
RFI:
  UTG_push / HJ_push / CO_push / BTN_push / SB_push

vs RFI (BB defense):
  BB_vs_UTG / BB_vs_HJ / BB_vs_CO / BB_vs_BTN / BB_vs_SB

vs push from IP (call or fold — コミット判断):
  BB_vs_BTN_push / BB_vs_CO_push / SB_vs_BTN_push
```

各 SBR で計 13 シナリオ × 6 SBR = **78 シナリオ**

### 期待される発見

- スコア閾値が SBR に比例してタイトになるか
- push/fold 境界スコアの SBR 依存式: `T_push(pos, SBR) = ?`
- BB call-off range の SBR 依存性

### 書籍への落とし込みイメージ

```
【Push/Fold チャート】
SBR  | UTG  | HJ   | CO   | BTN  | SB
8BB  |  26  |  24  |  22  |  18  |  16
10BB |  25  |  23  |  21  |  17  |  15
12BB |  24  |  22  |  20  |  16  |  14
15BB |  24  |  22  |  20  |  18  |  18  ← キャッシュゲームに近づく
（数値は仮。GTO データ取得後に確定）
```

---

## Phase 2: Open-Raise ゾーン（20〜40BB ★★）

**目的**: レンジ戦略が有効な SBR 20〜40BB でキャッシュゲームとのズレを定量化する。

### 対象 SBR

20BB / 25BB / 30BB / 40BB

### 収集シナリオ

キャッシュゲームと同一構造（20 シナリオ × 4 SBR = **80 シナリオ**）:
- RFI: UTG/HJ/CO/BTN/SB
- 対 RFI: HJ vs UTG, CO vs UTG/HJ, BTN vs UTG/HJ/CO, SB vs UTG/HJ/CO/BTN
- BB defense: vs UTG/HJ/CO/BTN/SB

### 期待される発見

- SBR 40BB でキャッシュゲーム閾値表がほぼ流用可能か
- 「3-bet = commit 問題」(SBR 20-25BB で 3-bet すると pot commit になる) の境界
- BB defense での差異（ICM 圧力なしでの純粋な SBR 効果）

### 書籍への落とし込みイメージ

```
【SBR 別 閾値補正表】
SBR  | T_open(UTG) | T_3bet | T_call | 備考
40BB |     24      |   32   |   29   | キャッシュ同等
30BB |     24      |   30   |   27   | 3-bet タイト
25BB |     24      |   28   |   25   | 3-bet = commit 注意
20BB |     —       |   —    |   —    | push/fold 推奨
```

---

## Phase 3: ICM 効果（バブル / FT ★★）

**目的**: ICM による閾値タイト化を定量化し、シンプルな補正ルールに変換する。

### シナリオ種別

| 状況 | ICM 圧力 | 想定 |
|---|---|---|
| 非バブル（中盤） | なし | SBR 依存のみ |
| マネーバブル | 中 | 賞金圏まで残り数人 |
| FT バブル (10→9) | 高 | ペイジャンプ大 |
| FT 残 3 人 | 最高 | 大差のある賞金分布 |
| PKO バブル | 特殊 | バウンティ計算あり |

### 収集シナリオ

各状況 × コア 10 シナリオ = **約 40〜50 シナリオ**

SBR は比較用に 25BB / 40BB を使用（open-raise ゾーン）。

### 期待される発見

- ICM バブル補正値: `T_open_ICM = T_open + ΔT_ICM`
- ΔT_ICM の近似値（マネーバブル: +2〜+3, FT バブル: +3〜+5 程度を仮説）
- スタック依存性（ビッグスタックは ICM タイト化が少ない）

---

## Phase 4: アンテ効果（BB ante ★）

**目的**: BB ante あり/なしでの RFI レンジ差を定量化し、閾値補正値を導出する。

### 比較設定

| 設定 | ante |
|---|---|
| キャッシュゲーム | なし |
| MTT 典型 | BB ante = 1BB |
| MTT 典型 | BB ante = 0.5BB |

### 収集シナリオ

RFI + BB defense を ante なし vs あり で比較。計 **20〜30 シナリオ**。

### 期待される発見

- アンテ 1BB あり → `T_open -= 2` 程度か（pot odds 改善によるレンジ拡大）
- アンテ補正がポジションによって差があるか（BTN 大 / UTG 小 など）

---

## Phase 5: MW 多人数ポット N≥3（トーナメント序盤 ★）

**目的**: キャッシュゲームでスコープ外とした N≥3 シナリオのルールを確立する。

### 対象シナリオ

```
N=3 (5-way pot):
  UTG open + HJ call + CO call → BTN/SB/BB の判断
  UTG open + HJ call + BTN call → SB/BB の判断

N=4 (6-way pot):
  UTG open + HJ call + CO call + BTN call → SB/BB の判断

Limp pot (トーナメント序盤で典型):
  UTG limp + HJ limp + CO limp → BTN/SB/BB の判断
  UTG limp + ... + BB raises: isolate raise
```

**計 10〜15 シナリオ**。SBR は 50-100BB（序盤深スタック想定）。

### 期待される発見

- BB 例外2 の N=3,4 での縮小度合い（diff ≤ max(0, 2-N) の検証）
- SC/suited の relative value が N=3,4 でどう変化するか
- Limp pot での BB isolate raise 閾値

---

## Phase 6: オープンサイズ効果（2BB vs 2.5BB ★）

**目的**: トーナメントで多い min-raise (2BB) vs キャッシュゲーム標準 (2.5BB) の影響確認。

### 比較

- 2.5BB open（キャッシュゲーム）vs 2BB open（トーナメント標準）
- レスポンスレンジへの影響（3-bet サイズが相対的に大きくなる）

### 収集

主要 5〜10 シナリオで 2BB vs 2.5BB を比較。**10〜15 シナリオ**。

---

## 4. 総シナリオ数と優先順位

| フェーズ | シナリオ数 | 優先度 |
|---|---|---|
| Phase 0 (対応確認) | — | ★★★ まず実施 |
| Phase 1 (push/fold) | ~78 | ★★★ 書籍コア |
| Phase 2 (open-raise) | ~80 | ★★ |
| Phase 3 (ICM) | ~45 | ★★ |
| Phase 4 (ante) | ~25 | ★ |
| Phase 5 (MW N≥3) | ~15 | ★ |
| Phase 6 (size) | ~12 | ★ |
| **合計** | **~255** | — |

キャッシュゲーム調査（34 シナリオ）の約 7.5 倍規模。
トークン消費量を考慮し、Phase 1 → 2 → 3 の順に段階的に実施する。

---

## 5. データ保存構造

```
poker-drill/scripts/precompute/raw_ranges_tournament/
├── api_spec.md                     # API パラメータ仕様メモ
├── game_types.json                 # 利用可能ゲームタイプ一覧
├── sbr8/                           # SBR=8BB
│   ├── UTG_push.json
│   ├── BB_vs_UTG.json
│   └── ...
├── sbr10/
├── sbr12/
├── sbr15/
├── sbr17/
├── sbr20/
├── sbr25/
├── sbr30/
├── sbr40/
├── icm_bubble/
│   ├── money_bubble_BTN_RFI.json
│   └── ...
├── ante/
│   ├── no_ante_BTN_RFI.json
│   ├── bb_ante_1BB_BTN_RFI.json
│   └── ...
└── multiway_n3/
    ├── BTN_vs_UTG_HJ_CO.json
    └── ...
```

---

## 6. 書籍への落とし込み — 核心式の拡張

### 既存式（キャッシュゲーム）

```
Score = H + L + ペア+10 + スーテッド+3 + コネクター(差1+1/差2-3+0.5)
      + ブロッカー(A+3/K+2/AK+4) − ペナルティ(差4以上−1/両9未満−1)
```

### トーナメント版（仮説）

式そのものは変えず、**閾値を SBR と ICM で調整**する。

```
T_open_tournament(pos, SBR, ICM) = T_open_cash(pos) × SBR補正 + ICM補正

SBR補正 = SBR が低いほど T_open を上げる（タイトに）
         SBR ≥ 40BB → 補正 0（キャッシュゲームと同等）
         SBR = 20BB → 補正 −1〜−2
         SBR = 15BB → push/fold 移行

ICM補正 = バブル +2〜+5（タイト）
         FT ショート +3〜+6（さらにタイト）
         ビッグスタック 0〜−1（若干ルース）
```

### アンテ補正（仮説）

```
T_open_ante = T_open − 1〜−2  （アンテ 1BB あり）
```

---

## 7. 実施スケジュール案

```
Step 1: Phase 0（API 確認）         → 1 セッション
Step 2: Phase 1（push/fold）        → 2〜3 セッション（78 シナリオ）
Step 3: Phase 1 データ分析 + 閾値表 → 1 セッション
Step 4: Phase 2（open-raise zone）  → 2〜3 セッション
Step 5: Phase 2 分析 + キャッシュ比較 → 1 セッション
Step 6: Phase 3/4（ICM/ante）       → 2 セッション
Step 7: Phase 5（MW N≥3）           → 1 セッション
Step 8: 書籍 generator 設計         → 1 セッション
Step 9: 執筆                        → n セッション
```

---

## 8. 関連ファイル

- キャッシュゲーム仕様: `preflop/PREFLOP_SCORE_SPEC.md`
- キャッシュゲーム GTO データ: `poker-drill/scripts/precompute/raw_ranges_3betv2/`
- MW データ: `poker-drill/scripts/precompute/raw_ranges_multiway/`
- 検証スクリプト: `poker-drill/scripts/precompute/verify_formula.py`
