# プリフロップ トーナメント編 — GTO Wizard 調査計画

**作成日**: 2026-05-19
**方針**: 仮説値・先入観を持たず、GTO Wizard の実測データから式とルールをすべて導く。
**対象ゲーム**: MTT × 9-max（ライブトーナメント標準）をメインとする。

---

## 1. 調査の全体像

### GTO Wizard で使うタイプの対応

| SBR 帯 | GTO Wizard タイプ | 理由 |
|---|---|---|
| 8〜20BB | **Short** | ショートスタック専用ツリー（オールイン頻度が変わる） |
| 20〜40BB | **Classic** | 通常のオープン/コール/3bet ツリー |
| 20〜40BB | **Ante** | アンテあり版（Classic との差を実測する） |
| ICM フェーズ | **Classic / Short** + ICM モード | バブル・FT 専用ソリューション |

### プレイヤー数

- **9-max メイン**（UTG/UTG+1/UTG+2/HJ/CO/BTN/SB/BB）
- **6-max サブ**（キャッシュゲームとの比較用、必要に応じて）

### 調査フェーズ一覧

```
Phase 0  API・ゲームタイプ確認          ← 最初に実施
Phase 1  Push/Fold ゾーン (8〜20BB)     ← 書籍の核心、最優先
Phase 2  Open-Raise ゾーン (20〜40BB)   ← Push/fold との接続
Phase 3  ICM フェーズ（バブル・FT）      ← チップEV との差を実測
Phase 4  アンテ効果                     ← Classic vs Ante を実測
Phase 5  MW N≥3（序盤多人数ポット）      ← トーナメント固有
Phase 6  オープンサイズ効果             ← 2BB vs 2.5BB
```

---

## Phase 0: API・ゲームタイプ確認

**目的**: 利用可能なゲームタイプと API パラメータを把握する。先入観なく実際の設定を確認する。

### 確認事項

1. トーナメント系ゲームタイプの一覧取得
   ```
   GET https://api.gtowizard.com/v2/game-modes/
   ```

2. SBR 指定方法（`depth=` パラメータ or 専用 gametype 名に BB が含まれる形式か）

3. ICM モード（バブル・FT）の有効化方法とパラメータ

4. アンテ設定（Classic vs Ante の gametype 名の違い）

5. Short タイプの対応 SBR 範囲

6. リンプあり/なし、オープンサイズ選択肢

### 出力
```
raw_ranges_tournament/
├── game_types.json        # 利用可能ゲームタイプ一覧
└── api_spec.md            # パラメータ仕様メモ
```

---

## Phase 1: Push/Fold ゾーン（SBR 8〜20BB）★★★

**目的**: 各 SBR × ポジション × アクションの実際のレンジを測定し、
スコア式でどう表現できるか（または表現できないか）を実測から判断する。

### 対象 SBR

8BB / 10BB / 12BB / 15BB / 17BB / 20BB の 6 段階。
（SBR の切れ目は実際のデータを見てから調整する）

### 収集シナリオ（各 SBR）

**RFI（push or min-raise or fold）:**
```
UTG_RFI / UTG1_RFI / UTG2_RFI / HJ_RFI / CO_RFI / BTN_RFI / SB_RFI
```

**BB defense（vs 各ポジションの raise/push）:**
```
BB_vs_UTG / BB_vs_HJ / BB_vs_CO / BB_vs_BTN / BB_vs_SB
```

**vs push (commit 判断):**
```
BB_vs_BTN_push / BB_vs_CO_push / SB_vs_BTN_push / BTN_vs_CO_push
```

**3-bet ポット（SBR が浅いと 3-bet = commit になる）:**
```
BTN_vs_UTG / CO_vs_UTG / HJ_vs_UTG  （各 SBR で commit 境界を確認）
```

1 SBR あたり約 20 シナリオ × 6 SBR = **約 120 シナリオ**

### 計測する指標

- 各ハンドの raise / call / fold 頻度（GTO Wizard の strategy データ）
- スコア式で正しく分類できたか（HU キャッシュゲームの verify_formula.py と同様のスクリプト）
- push/fold の境界スコアが各 SBR × ポジションでどう変化するか

### 分析で明らかにすること（仮説を持たず実測する）

- T_push(UTG, SBR=10) = ?、T_push(BTN, SBR=10) = ?
- SBR が変化したとき T_push はどう変化するか（線形か、非線形か）
- BB call-off（コミット）閾値の SBR 依存性
- スコア式が push/fold に適用可能か、または別の指標が必要か

### 出力
```
raw_ranges_tournament/sbr8/ *.json
raw_ranges_tournament/sbr10/ *.json
raw_ranges_tournament/sbr12/ *.json
raw_ranges_tournament/sbr15/ *.json
raw_ranges_tournament/sbr17/ *.json
raw_ranges_tournament/sbr20/ *.json
```

---

## Phase 2: Open-Raise ゾーン（SBR 20〜40BB）★★

**目的**: レンジ戦略が有効な SBR 帯でのプリフロップ解を取得し、
キャッシュゲーム（100BB）の閾値表との差を実測する。

### 対象 SBR

25BB / 30BB / 40BB の 3 段階。
（20BB は Phase 1 の上限と重複するため Phase 1 で取得済み）

### 収集シナリオ

キャッシュゲームと同一の 20 シナリオ構造（9-max 分はポジションを拡張）:

**RFI（各ポジション）:**
```
UTG / UTG1 / UTG2 / HJ / CO / BTN / SB
```

**対 RFI（3-bet / call / fold）:**
```
HJ_vs_UTG / CO_vs_UTG / CO_vs_HJ / BTN_vs_UTG / BTN_vs_HJ / BTN_vs_CO
SB_vs_UTG / SB_vs_HJ / SB_vs_CO / SB_vs_BTN
BB_vs_UTG / BB_vs_HJ / BB_vs_CO / BB_vs_BTN / BB_vs_SB
```

1 SBR あたり約 22 シナリオ × 3 SBR = **約 66 シナリオ**

### 計測する指標

- 各ハンドの 3-bet / call / fold 頻度
- スコア式の精度（verify_formula.py で定量化）
- キャッシュゲーム閾値との差（ΔT = T_tournament - T_cash）
  ← 差がいくつかは実測後に初めて言える。先入観を持たない。

### 分析で明らかにすること

- T_open が SBR に応じてどう変化するか
- 「SBR ≥ 40BB でキャッシュゲームと同等」は本当か
- 3-bet / call の境界スコアの SBR 依存性
- 9-max ポジション拡張（UTG+1, UTG+2）でスコア式がどう機能するか

---

## Phase 3: ICM フェーズ（バブル・ファイナルテーブル）★★

**目的**: チップ EV と ICM ($EV) の差を実測し、
ICM による閾値変化をスコア式で表現可能かを確認する。

**重要**: "バブルでは何点タイト" などの補正値は、実測後に初めて導出する。

### シナリオ種別

**マネーバブル（チップ EV → ICM 移行点）:**
```
残 n 人 / money は n-1 位まで（tight な賞金分布）
スタック設定: Big / Average / Short スタックの各視点
```

**ファイナルテーブルバブル（大きなペイジャンプ直前）:**
```
残 10 人 / money は 9 位まで
各スタック分布パターン
```

**ファイナルテーブル残 3〜5 人:**
```
大差のある賞金分布（1st が 2nd の 2-3 倍以上）
```

**ICM なし（チップ EV のみ）vs ICM あり の比較:**
```
同一 SBR × 同一ポジション で ICM あり/なしを比較し、差分を実測
```

各状況 × コアシナリオ（RFI + BB defense）= **約 40〜60 シナリオ**

### 計測する指標

- ICM なし vs あり での raise / call / fold 頻度の変化
- ハンド別に「ICM による参加率低下」を定量化
- スコア式で「ICM 補正 = X 点のオフセット」として近似できるか、
  またはスコア式では再現できない非線形な変化があるか

---

## Phase 4: アンテ効果（Classic vs Ante）★

**目的**: BB アンテの有無がプリフロップレンジに与える影響を実測する。

**重要**: アンテによる閾値変化は実測後に初めて値を決める。

### 比較設計

同一 SBR (25BB / 40BB) × 同一ポジション × 同一シナリオ を
Classic（アンテなし）と Ante（BB ante あり）で取得し、差分を計算する。

**収集シナリオ（各 SBR × タイプ）:**
```
RFI: UTG / HJ / CO / BTN / SB
BB defense: vs UTG / vs HJ / vs CO / vs BTN / vs SB
```

2 SBR × 2 タイプ × 10 シナリオ = **約 40 シナリオ**（うち 20 は Phase 2 流用可能）

### 計測する指標

- Classic vs Ante での各ハンドの参加率差（Δentr_rate per hand）
- アンテによる RFI 閾値変化（ΔT_open が各ポジションで一定か否か）
- BB defense での変化

---

## Phase 5: MW 多人数ポット（N≥3）★

**目的**: キャッシュゲーム編でスコープ外とした N≥3 シナリオのルールを実測から確立する。

### 対象シナリオ（SBR 50-100BB、序盤深スタック想定）

**N=2（cold callers 2 人）:**
```
UTG open + HJ call + CO call → BTN の判断
UTG open + HJ call + CO call → SB の判断
UTG open + HJ call + CO call → BB の判断
UTG open + CO call + BTN call → SB / BB の判断
```

**N=3（cold callers 3 人）:**
```
UTG open + HJ + CO + BTN call → SB / BB の判断
```

**Limp pot（トーナメント序盤の典型）:**
```
UTG limp + HJ limp → CO / BTN / SB の判断
UTG limp + HJ limp + CO limp → BTN / SB / BB の判断
BB vs multiple limpers: iso-raise range
```

**約 15〜20 シナリオ**

### 計測する指標

- N=2, 3 での SC / suited / offsuit 参加率変化
- BB 例外ルール（diff ≤ max(0, 2-N)）の N=3 での妥当性検証
- Limp pot での参加・アイソレート閾値

---

## Phase 6: オープンサイズ効果（2BB vs 2.5BB）★

**目的**: トーナメントで多い min-raise (2BB) とキャッシュゲーム標準 (2.5BB) の
レスポンスレンジへの影響を実測する。

### 比較

同一シナリオ × 2BB open vs 2.5BB open で取得し差分を計算。

- RFI 相手の 3-bet / call / fold 境界の変化
- BB defense での変化

**約 10〜15 シナリオ**

---

## 5. 総シナリオ数・優先順位

| フェーズ | シナリオ数（目安） | 優先度 |
|---|---|---|
| Phase 0（確認） | — | ★★★ 最初 |
| Phase 1（push/fold） | ~120 | ★★★ コア |
| Phase 2（open-raise） | ~66 | ★★ |
| Phase 3（ICM） | ~50 | ★★ |
| Phase 4（ante） | ~20 追加 | ★ |
| Phase 5（MW N≥3） | ~20 | ★ |
| Phase 6（size） | ~15 | ★ |
| **合計** | **~291** | — |

---

## 6. データ保存構造

```
poker-drill/scripts/precompute/raw_ranges_tournament/
├── api_spec.md
├── game_types.json
├── sbr8/
│   ├── UTG_RFI.json
│   ├── BB_vs_UTG.json
│   └── ...
├── sbr10/ ... sbr40/
├── icm_money_bubble/
│   ├── big_stack_BTN_RFI.json
│   ├── short_stack_BTN_RFI.json
│   └── ...
├── icm_ft_bubble/
├── ante_sbr25/
│   ├── classic_UTG_RFI.json
│   └── ante_UTG_RFI.json
└── multiway_n3/
```

---

## 7. 分析スクリプト方針

- `verify_formula_tournament.py` をキャッシュゲーム版 `verify_formula.py` から派生させる
- 入力: gametype 別 JSON + スコア式 + 閾値表
- 出力: 精度スコア + 境界ハンド一覧
- Phase ごとに分析 → 閾値表草案 → 次フェーズへ という反復サイクル

---

## 8. 書籍構成（調査完了後に確定）

**現時点では未確定。すべての章タイトル・数値は調査後に決める。**

想定する問いに答える形で章を構成する：

1. 同じスコア式はトーナメントでも使えるか？
2. SBR が変わると閾値はどう変わるか？
3. push/fold ゾーンへの移行は何 BB か？
4. ICM があると何が変わるか？
5. アンテが入ると何が変わるか？
6. 9-max の追加ポジション（UTG+1/+2）をどう扱うか？
