# research/v3-additional/

poker-drill v3 (2026-06 以降) の精度改善のための GTO Wizard 追加調査。
- 既存書籍値の検証
- 不足データの補完
- 境界判定の機械化

## タスク

### タスク A: Vol1 BB defense 境界帯混合戦略 (~120 spots)

BB vs UTG / HJ / CO / SB の各 30 ハンド (Score = T_call ± 2 帯) で
fold / call / 3-bet 頻度を取得。

**目的**:
- Phase 3.4 `v1_boundary_hands` の品質決定
- Phase 1.4 `v1_cash_defense` の EXCEPTIONS_BOUNDARY を全シナリオに広げる

**スクリプト**: `task_a_bb_boundary.py`
**出力**: `findings/task_a_bb_*.json`

### タスク B: Vol2 境界閾値統一 (~40 spots)

- overbet 閾値: 100 / 125 / 150 / 200 / 250% の行動分岐
- dynamic_2tone 判定: 連結 3 枚 vs 2-tone+1 連結
- board family top カード境界 (J-7-2 vs Q-7-2)

**目的**: Phase 3.6-3.10 の境界判定機械化
**スクリプト**: `task_b_v2_boundaries.py`
**出力**: `findings/task_b_*.json`

### タスク C: Vol1 スクイーズ N=2/3 (~30 spots)

BTN/SB/BB squeeze vs UTG/HJ/CO open + 1-2 callers の T_squeeze 実測。

**目的**: Phase 3.1 `v1_cash_multiway` の N=2/3 帯を概算値から実測値へ
**スクリプト**: `task_c_squeeze_n23.py`
**出力**: `findings/task_c_*.json`

## 使い方

```bash
# token は .env から読む (gitignore 済)
source .env

# 動作確認 (1 call)
python3 probe.py

# 各タスク実行
python3 task_a_bb_boundary.py
python3 task_b_v2_boundaries.py
python3 task_c_squeeze_n23.py
```

## 共通モジュール

`vol2-cash-postflop/gto_api.py` を sys.path 経由で参照。
Cash 100bb 6-max の game type は `Cash6mTest_6mNL100R2`。

## 結果の活用

各 JSON 結果を集計して、書籍値との差分レポートを作成 (`findings/diff_report.md`)。
反映先:
- Phase 3.4 `v1_boundary_hands` のハンドリスト
- Phase 3.1 `v1_cash_multiway` の generator 更新
- `scripts/generate/_common/types.py` の EXCEPTIONS_BOUNDARY (各シナリオ別)
