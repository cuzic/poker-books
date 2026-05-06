# v3 スクリプト索引 (新スケール対応)

作成日: 2026-05-05
仕様元: knowledges/ds_redesign_v2/SPEC_OTHER_FORMULAS.md / SPEC_HANDSCORE.md

新スケール (0-100 equity %) 対応の検証スクリプト一覧。
旧版は scripts/ にそのまま残し、v3 として別ファイルで新規作成した。

## 作成ファイル

| 新ファイル | 旧版 | 役割 |
|---|---|---|
| `scripts/c_coefficients_v3.py` | (新規) | C / A / M 表 + 閾値の単純定義モジュール |
| `scripts/ds_framework_recheck_v3.py` | `ds_framework_recheck.py` | 後手スコア 27-case 再検証 (phase1 CSV 入力) |
| `scripts/draw_bonus_verify_v3.py` | `draw_bonus_verify.py` | ドロー加点 TexasSolver raw からの DS 整合確認 |
| `scripts/role_score_verify_v3.py` | `role_score_verify.py` | 役スコア値 K72r SRP raw 整合確認 |
| `scripts/boardscore_pokerbench_v3.py` | `boardscore_pokerbench.py` | PokerBench で per-board / per-type strong/weak bet 率 |
| `scripts/handscore_calibrate_pokerbench_v3.py` | `handscore_calibrate_pokerbench.py` | HandScore vs PokerBench GTO action のキャリブレーション |

## 共通インポート

すべての v3 スクリプトは `c_coefficients_v3` から定数とヘルパーを import する:

```python
from c_coefficients_v3 import (
    C_TABLE, A_TABLE, M_TABLE, HS_REP,
    DS_TH_RAISE, DS_TH_CALL,
    HS_TH_H3, HS_TH_H2,
    defender_score, predict_defender,
    attacker_score, predict_attacker,
    bucket,
)
```

`hand_evaluator_v3` (新スケール HandScore 計算) は既に存在しており、
`boardscore_pokerbench_v3` と `handscore_calibrate_pokerbench_v3` はこれを使う。
（API は `evaluate_v3(combo, board, street="flop")` の形式）

## 主要変更点 (旧 → 新)

### C 表
```
旧: {33:3, 50:5, 75:7, 100:9, 150:11}
新: {33:12, 50:17, 75:22, 100:25, 150:30}
```

### A 表 (ボード補正)
```
旧: dry=3 / semi=2 / wet=1   (ベースライン -3 を別計算)
新: dry=12 / semi=6 / wet=0   (-3 補正は A 値に吸収)
```

### M 表 (マルチウェイ補正、新規)
```
新: HU=0 / 3-way=12 / 4-way+=22
```

### 後手スコア式
```
旧: DS = HS + A - 3 - C
新: DS = HS + A - C - M
```

### 後手スコア閾値
```
旧: >= 8 RAISE / >= 0 CALL / < 0 FOLD
新: >= 40 RAISE / >= 20 CALL / < 20 FOLD
```

### バケツ閾値
```
旧: H3 >= 14 / H2 >= 7 / H1 < 7
新: H3 >= 65 / H2 >= 35 / H1 < 35
```

### バケツ代表 HS
```
旧: H3=17 / H2=11 / H1=4
新: H3=70 / H2=50 / H1=28
```

### 役スコア値 (主要)
```
旧 → 新:
  set+        :  30 → 88-92
  two_pair    :  18 → 75
  TPTK        :  18 → 70
  TPGK        :  15 → 62
  TPMK        :   8 → 50
  TPWK        :   6 → 45
  bottom_pair :   4 → 32
  air         :   0 → 8-25
```

### ドロー加点 (フロップ Rule of 4)
```
旧 → 新:
  FD          : +13 → +36
  OESD        : +14 → +32
  GS          :  +6 → +16
  BDFD        :  +4 →  +5
  BDSD        :  +1 →  +2
```

## 動作確認結果

| スクリプト | 結果 |
|---|---|
| `c_coefficients_v3.py` | 自己検証 OK: 仕様書の例 1/例 2 の DS 値が一致 |
| `ds_framework_recheck_v3.py` | 27 ケース処理: 一致 24/27 = 88.9% (境界 2、不一致 1) |
| `draw_bonus_verify_v3.py` | BDFD on K72r / OESD on T98r ともに既存 raw JSON で動作確認 |
| `role_score_verify_v3.py` | K72r 33%/75% で 8 役 × 2 サイズ = 16 ケース処理 OK |
| `boardscore_pokerbench_v3.py` | PokerBench 全件処理 OK (per-board / per-type 17 型集約) |
| `handscore_calibrate_pokerbench_v3.py` | threshold sweep 25-95 / 高HS=65, 低HS=25 で不一致集計 OK |

## 既知のキャリブレーション課題

`role_score_verify_v3.py` の K72r 33% CBet で TPGK / TPMK / TPWK が
"DS RAISE 予測" だが GTO は "CALL" となるケースがあり、これは
SPEC_HANDSCORE.md §6 で言及されている既知の境界課題。
本スクリプトはあくまで仕様値での検証ツールであり、不一致の存在は
仕様の今後の調整余地を示す（スクリプト自体のバグではない）。

## 旧版との並行運用

旧版 (`hand_evaluator.py`, `hand_evaluator_v2.py`, `ds_framework_recheck.py` 等) は
そのまま残し、巻③以前の reproduce 用に保持する。
新スケールの本書 (巻②③④⑤⑥) では v3 を使用する。
