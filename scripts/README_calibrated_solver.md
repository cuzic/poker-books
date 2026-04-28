# Calibrated TexasSolver Wrapper

TexasSolver の系統誤差（ボード型依存）を 17 型別補正テーブルで吸収し、GTO Wizard 相当値を返すラッパー。

## 構成

```
scripts/
├── board_classifier.py         ボード文字列 → 17 型分類
├── train_correction_table.py   30 ボード dataset から補正テーブル学習
├── calibrated_solve.py         ラッパー CLI (raw TS → calibrated)
└── README_calibrated_solver.md 本ファイル

knowledges/flop-advanced/
└── correction_table.json       学習済み補正テーブル
```

## 仕組み

```
TexasSolver 出力
    ↓
ボード文字列を 17 型に分類
    ↓
型別補正テーブル参照 (mean_offset, stdev)
    ↓
calibrated = raw_ts + offset  (∈ [0, 100] にクランプ)
    ↓
信頼区間 [calibrated ± stdev] と confidence 情報も返す
```

これは「**蒸留 (distillation) の最小実装**」とも言えます。GTO Wizard を教師、TexasSolver を生徒、type-based correction を蒸留関数とした、極小（30 サンプル）データセットで過学習を避けた構成。

## 性能 (Leave-One-Out)

| 指標 | 補正なし | 補正あり |
| --- | ---: | ---: |
| MAE | 15.44 | **10.52** |
| 改善率 | – | **31.9%** |
| 型一致率 | – | 16/29 (55%) |

残り 13/29 ボードは型サンプル N=1 のため LOOCV では fallback したが、本番では型サンプルが既に学習済みの状態なので fallback は減る。

## 使い方

### 1. 単発呼び出し

```bash
python3 scripts/calibrated_solve.py \
  --board K72r \
  --ts-cbet-pct 78.1 \
  --format table
```

```
Board      Type      Raw TS  Offset Calibrated Band             N Fallback
K72r       1b          78.1   +17.6       95.7 [91.7,99.7]      7 -
```

### 2. JSON 出力（プログラム連携用）

```bash
python3 scripts/calibrated_solve.py --board K72r --ts-cbet-pct 78.1
```

```json
{
  "board": "K72r",
  "type_code": "1b",
  "type_name": "high-dry-rainbow",
  "raw_ts": 78.1,
  "offset": 17.6,
  "offset_stdev": 4.0,
  "calibrated": 95.7,
  "calibrated_clamped": 95.7,
  "confidence_band": [91.7, 99.7],
  "n_training_samples": 7,
  "fallback_used": false
}
```

### 3. バッチ処理

```bash
echo '[
  {"board": "K72r", "ts_cbet_pct": 78.1},
  {"board": "Q63r", "ts_cbet_pct": 70.0}
]' > /tmp/boards.json

python3 scripts/calibrated_solve.py --batch /tmp/boards.json --format table
```

## TexasSolver との連携 (典型パターン)

```python
import json
import subprocess
from pathlib import Path

# 1. TexasSolver で生 CBet 頻度を取得
ts_output = run_texassolver(board="Kc7d2s", ip_range=..., oop_range=..., pot=7, stack=97)
ts_cbet = ts_output["aggregate_cbet_pct"]

# 2. ラッパーで補正
result = subprocess.check_output([
    "python3", "scripts/calibrated_solve.py",
    "--board", "K72r",
    "--ts-cbet-pct", str(ts_cbet),
])
calibrated = json.loads(result)
print(f"Raw: {calibrated['raw_ts']}%, Calibrated: {calibrated['calibrated']}%")
```

または直接 import:

```python
import sys
sys.path.insert(0, "scripts")
from calibrated_solve import calibrate

result = calibrate(board="K72r", ts_cbet_pct=78.1)
print(result["calibrated"])  # 95.7
```

## 補正テーブルの再学習

新しいボードを 30 ボード dataset に追加したら:

```bash
# 1. 新ボードを texassolver_accuracy_30.py に追加して再 solve
python3 scripts/texassolver_accuracy_30.py

# 2. correction_table.json を再生成
python3 scripts/train_correction_table.py --loocv
```

LOOCV の `improvement_pct` が前回より上がっていれば成功。

## 制限事項と将来拡張

### 現状の制限

1. **型サンプル N=1 が多い**:17 型のうち約 11 型が N=1。これらは LOOCV では使えず、新規ボードでの汎化力が弱い
2. **型分類が決定論的**:境界ボード（max_diff=4 や middle=T）で分類が硬直する可能性
3. **TS 値の絶対値依存**:offset は固定。TS が極端に高い/低いケースで補正が破綻する可能性
4. **scenario 固定**:BTN vs BB SRP, 100bb のみ。3-bet pot, 異なる position では再学習必要

### 改善方向

#### A. データ拡張（推奨）
- 30 ボード → 100 ボード（17 型 × 6 ボード均等サンプル、TexasSolver で一晩生成）
- 各型 N=5+ になれば stdev が安定し、補正の信頼性が上がる

#### B. 特徴量回帰モデル
- 現状の「型 → offset」を「(top_card, max_diff, is_2tone, is_broadway, ...) → offset」の線形回帰に拡張
- N=1 型でも特徴量空間で補間可能
- scikit-learn `LinearRegression` で実装容易

#### C. TS 値も入力に
- 現状: offset = f(features)
- 拡張: offset = f(features, ts_value) — TS が極端な値のとき補正を弱める
- データ次第ではモード崩壊を防げる

#### D. Cross-scenario 学習
- 同じボードの SRP / 3-bet / 4-bet pot で別補正テーブル
- もしくは scenario を特徴量に含める

## ライセンス

書籍プロジェクト『迷わないポーカー』の研究用途。
GTO Wizard 値は同社の利用規約に従い、参照値の出所を明記すること。
