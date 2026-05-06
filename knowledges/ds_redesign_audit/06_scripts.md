# 調査06: scripts/ ツール群の HandScore 依存調査

実施日: 2026-05-05

## scripts/ の Python スクリプト数

総数: **57 ファイル**（scripts/*.py）

## HandScore 計算ロジックを実装しているスクリプト

### コア計算ライブラリ

| スクリプト | 機能 | スケール変更影響 |
|---|---|---|
| **`hand_evaluator.py` (v1)** | 旧 HandScore 計算（0〜30 スケール） | **大** |
| **`hand_evaluator_v2.py`** | v2 改訂版 HandScore (0〜30 スケール、閾値 H3≥14/H2≥7) | **大** |
| `handscore_calibrate_pokerbench.py` | PokerBench での HandScore キャリブレーション | 大 |
| `handscore_v2_evaluation.py` | v1 vs v2 比較評価 | 大 |
| `handscore_continuous_sweep.py` | HandScore 連続値スイープ | 大 |
| `handscore_cbet_sweep.py` | CBet 頻度予測スイープ | 大 |
| `handscore_boundary_v2.py` | バケツ境界検証 | 大 |
| `handscore_bucket_verify.py` | バケツ判定検証 | 大 |
| `handscore_fd_pair_verify.py` | FD+ペア検証 | 大 |

### 後手スコア / α 関連

| スクリプト | 機能 | 既存値 |
|---|---|---|
| **`ds_framework_recheck.py`** | 後手スコア検証（C 表ハードコード） | C_TABLE = {33: 3, 50: 4, 75: 6} （旧表） |
| `draw_bonus_verify.py` | ドロー加点検証 | `if ds >= 8:` 閾値 |
| `role_score_verify.py` | 役割スコア検証 | `if d >= 8:` 閾値 |
| `bdm.py` | BDM v5 計算（巻③ 精密 HandScore） | 大 |

### C/A/M 係数検証

| スクリプト | 検証対象 |
|---|---|
| `texassolver_c_coef_verify.py` | C 係数 (33%=3, 50%=5, 75%=7) ← 新表 |
| `texassolver_c_coef_srp_verify.py` | SRP での C 微調整 |
| `c33_boundary_check.py` | 33% 境界 |
| `c150_accuracy_eval.py` | 150% オーバーベット精度 |
| `barrel_score_verify.py` | バレルスコア検証 |

### ボード分類

| スクリプト | 機能 |
|---|---|
| `board_classifier.py` | ボード分類（A 値導出のため） |
| `boardscore_pokerbench.py` | PokerBench でのボードスコア検証（HS≥14 ハードコード） |
| `extract_gto_charts.py` | GTO チャート抽出 |

### TexasSolver 連携 (`generate_volume4_*.py` など)

```
generate_volume4_102.py 〜 generate_volume4_108.py (7 ファイル)
generate_flop_accuracy_30*.py (4 ファイル)
gto_query_volume4.py
calibrated_solve.py
collect_overbet_exclusion.py
```

これらは TexasSolver の解析結果を取り出すスクリプトで、**HandScore 計算は呼び出すが定義はしない**。

### その他

```
icm_calc.py            ← 巻⑥ ICM 計算（HandScore 非依存）
format_gto_markdown.py ← GTO Wizard チャート整形
phase1_aggressor.py    ← 巻④ phase1 攻撃側集計
phase1_defender.py     ← 巻④ phase1 防御側集計
```

## ハードコード値の集計

### 旧 C 表のハードコード（要更新）

```python
# scripts/ds_framework_recheck.py:22
C_TABLE = {33: 3, 50: 4, 75: 6}   ← 旧表。新表 {33:3, 50:5, 75:7, 100:9, 150:11} へ
```

### 閾値 ≥ 8（CR 検討の境界、旧スケール）

要書き換えの箇所:
- `scripts/draw_bonus_verify.py:159`: `if ds >= 8:`
- `scripts/role_score_verify.py:101`: `if d >= 8:`
- `scripts/ds_framework_recheck.py:40`: `if ds >= 8:`

### HandScore ≥ 14 の境界値（旧スケール H3 閾値）

- `scripts/boardscore_pokerbench.py:84,120`: `sub['hand_score'] >= 14`
- `scripts/hand_evaluator.py:254`: `if score >= 15:`
- `scripts/handscore_calibrate_pokerbench.py:119,120,121`: `>= 15`
- `scripts/hand_evaluator_v2.py:220`: `if score >= 14:`

新スケール（equity %）では閾値変更が必要。例: 
- 旧 ≥ 14 (H3) → 新 ≥ 70%（要再キャリブレーション）

## 入出力データ形式

### 既存の出力 JSON 形式

```json
{
  "hand": "AKs",
  "board": "K72r",
  "hand_score": 18,            // 旧スケール
  "bucket": "H3",
  "ds": 12,                     // 後手スコア
  "action": "CR"
}
```

### 新スケール対応の場合

選択肢 1: 既存 JSON を 0-100 スケールに変換するだけ:
```json
{
  "hand_score": 65,             // equity %
  "ds_equity": 35,              // %
  "action": "コール"            // 閾値が equity ベースで判定
}
```

選択肢 2: 旧/新を併記:
```json
{
  "hand_score_v2": 18,          // 旧 0-30 互換
  "hand_score_equity": 65,      // 新 0-100
}
```

## 影響量の見積

| 作業 | 件数 | 工数 |
|---|---:|---|
| `hand_evaluator_v2.py` の役スコア値・ドロー加点を equity ベースに書き換え | 1 ファイル / 全関数 | 4 時間 |
| `bdm.py` (巻③ 精密 HandScore) の改訂 | 1 ファイル | 2 時間 |
| C_TABLE 等のハードコード更新 | 5 ファイル | 30 分 |
| 閾値 (≥8, ≥14) の更新 | 8 ファイル | 1 時間 |
| データ I/O 形式の互換性確認・移行 | 全 generator スクリプト | 2 時間 |
| 新スケール用 unit test 追加 | 5 ファイル | 2 時間 |
| **合計** | | **約 12 時間 (≒ 1.5 日)** |

## 結論

- HandScore 計算のコア実装は `hand_evaluator_v2.py` 1 ファイルに集約 → **再設計の起点**
- 補助スクリプト 8〜10 ファイルでハードコード値の更新が必要
- TexasSolver 連携スクリプトは HandScore 計算を呼ぶだけ → **大きな変更不要**
- ICM 計算（`icm_calc.py`）は HandScore 非依存 → **影響なし**
- **再設計の主要ファイル: hand_evaluator_v2.py + bdm.py の 2 つに集約**
- これらを新式で書いたら他のスクリプトは数行のハードコード変更のみ
