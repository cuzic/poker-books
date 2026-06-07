# three_class_model pre-MATCHA archive (2026-06-07)

## 移行内容

MATCHA Framework 確立 (2026-06-07) を機に、UDG v1/v3 試行・旧公式系列 (v5〜v15) を `scripts/three_class_model/` から退避。

## 構成

```
_archive/three_class_model-pre-matcha-2026-06-07/
├── udg_legacy/           # UDG v1/v3 試行 (3 files)
└── legacy_formulas/      # 旧公式探索コード (141 files)
```

### udg_legacy/ (3 files)

| ファイル | 内容 | superseded by |
|---|---|---|
| `udg_v1.py` | UDG v1 試行 (4 tier、3 universal rule のみ) | `udg_v2.py` (MATCHA SSOT) |
| `udg_v3.py` | UDG v3 失敗試行 (IP modifier 過剰反応) | 教訓は `UDG_V3_LEARNINGS.md` に集約済 |
| `UDG_RESULTS.md` | v1 結果 | `UDG_V2_RESULTS.md` |

### legacy_formulas/ (141 files)

旧 v5〜v15 系列の探索コード。MATCHA Framework で吸収済:

| カテゴリ | 例 |
|---|---|
| 旧 formulas | `formulas_v{5..11}*.py`, `river_v{9..15}*.py`, `turn_v{8,9,10}*.py`, `flop_v{8,9}*.py` |
| Cash 3BP/4BP | `cash_3bp_*_v1.py`, `cash_4bp_*_v{1,2}.py` |
| MTT 旧公式 | `mtt50_*.py`, `mtt_depth_correction.py` |
| CR/donk | `cr_donk_defense_v1.py` |
| Verify | `verify_v{2..7}*.py`, `verify_defense*.py`, `verify_attack*.py` |
| Derive/design | `derive_defense_*.py`, `design_*.py` |
| 探索分析 | `analyze_*.py`, `huge_gap_*.py`, `residual_*.py` |
| Train (旧 ML) | `train_*.py`, `bucket_model.py`, `polarization_classifier.py` |
| 旧 report | `BUCKET_MODEL_REPORT.md`, `FRAMEWORK_V7_SUMMARY.md`, `DATA_DRIVEN_FRAMEWORK_REPORT.md` |
| 旧 dataset | `dataset_full.csv`, `dataset_gtow.csv`, `dataset_unified.csv` (旧版、v2 で superseded) |
| 各種 CSV | `attack_bet_size.csv`, `cell_with_confidence.csv` 等 |

## 現状の `scripts/three_class_model/` (8 files、MATCHA SSOT)

| ファイル | 役割 |
|---|---|
| `udg_v2.py` | MATCHA Framework SSOT (ファイル名 legacy) |
| `UDG_V2_RESULTS.md` | MATCHA audit 結果 |
| `UDG_V3_LEARNINGS.md` | UDG v3 試行教訓 (歴史参照) |
| `UNIFIED_DATASET_V2.md` | 統合データセット仕様書 |
| `dataset_unified_v2.csv` | 293K rows、probe phase 1-6 統合 |
| `NEW_FORMULA_AUDIT.md` | 11 専用公式の audit |
| `audit_new_formulas.py` | 公式 audit ツール |
| `mtt_formula_audit.py` | MTT formula audit (recent) |

## 復元方法

特定ファイルが必要になった場合:

```bash
mv _archive/three_class_model-pre-matcha-2026-06-07/legacy_formulas/<file> scripts/three_class_model/
```

または git history から復元:

```bash
git log --all -- scripts/three_class_model/<file>
git checkout <commit>^ -- scripts/three_class_model/<file>
```

## 関連

- MATCHA Framework SSOT: `scripts/three_class_model/udg_v2.py`
- 用語集: https://gistpreview.github.io/?dbb75f11330aff4346de987c4f4fb91b
- Memory: `project_matcha_series.md` (新)、旧 `project_vol2_postflop_udg.md` は削除済
