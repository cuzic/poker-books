# MTT 公式 v8a/v10/v14 既存データ適用結果

生成: `scripts/three_class_model/mtt_formula_audit.py`  
データ: `dataset_unified.csv`、行数=1,166,205

## 1. Pot-type サマリー

Cash100 ベースラインと MTT 各 depth での精度比較。

| street | 公式 | pot_type | n | n_huge | acc% | mean_loss | huge_loss |
|--------|------|----------|---|--------|------|-----------|-----------|
| flop | v8a | Cash100 | 10,469 | 1,626 | 69.2% | 0.094 BB | 0.241 BB |
| flop | v8a | MTT100 | 20,592 | 6,347 | 68.6% | 0.183 BB | 0.38 BB |
| flop | v8a | MTT25 | 28,224 | 3,134 | 60.6% | 0.203 BB | 0.163 BB |
| flop | v8a | MTT50 | 28,224 | 4,283 | 68.3% | 0.17 BB | 0.17 BB |
| flop | v8a | other | 3,004 | 469 | 64.4% | 0.136 BB | 0.421 BB |
| flop | v9b | Cash100 | 10,469 | 1,626 | 69.9% | 0.098 BB | 0.061 BB |
| flop | v9b | MTT100 | 20,592 | 6,347 | 72.0% | 0.143 BB | 0.129 BB |
| flop | v9b | MTT25 | 28,224 | 3,134 | 60.6% | 0.124 BB | 0.156 BB |
| flop | v9b | MTT50 | 28,224 | 4,283 | 68.0% | 0.094 BB | 0.163 BB |
| flop | v9b | other | 3,004 | 469 | 69.5% | 0.095 BB | 0.041 BB |
| turn | v10 | Cash100 | 7,554 | 4,611 | 88.0% | 0.048 BB | 0.048 BB |
| turn | v10 | MTT50 | 20,790 | 11,385 | 83.0% | 0.096 BB | 0.067 BB |
| river | v14 | Cash100 | 14,218 | 10,031 | 82.3% | 0.301 BB | 0.388 BB |
| river | v14 | MTT50 | 11,763 | 9,349 | 84.2% | 0.267 BB | 0.316 BB |
| river | v15 | Cash100 | 14,218 | 10,031 | 84.6% | 0.175 BB | 0.212 BB |
| river | v15 | MTT50 | 11,763 | 9,349 | 84.8% | 0.12 BB | 0.13 BB |

## 2. Cash 100bb vs MTT depth 差分

公式 huge_loss の Cash100 比 (= MTT - Cash100)。差分が大きいほど MTT 特有の補正が必要。

| street | 公式 | Cash100 | MTT25 | MTT50 | MTT100 | MTT200 |
|--------|------|---------|-------|-------|--------|--------|
| flop | v8a | 0.241 | 0.163 (-0.078) | 0.170 (-0.071) | 0.380 (+0.139) | — |
| flop | v9b | 0.061 | 0.156 (+0.095) | 0.163 (+0.102) | 0.129 (+0.068) | — |
| river | v14 | 0.388 | — | 0.316 (-0.072) | — | — |
| river | v15 | 0.212 | — | 0.130 (-0.082) | — | — |
| turn | v10 | 0.048 | — | 0.067 (+0.019) | — | — |

## 3. 境界 cell (huge_loss > 0.3 BB, n>=50)

全 671 cell 中、境界 cell = 185 件。

`mtt_boundary_cells.csv` に全件出力。以下 huge_loss 降順 top 20。

| street | pot_type | bf | mv | dv | bet_size | n | n_huge | huge_loss | mean_loss | modal_fold% | modal_call% | modal_raise% |
|--------|----------|----|----|----|----------|---|--------|-----------|-----------|-------------|-------------|--------------|
| flop | Cash100 | low_dry | no_made_hand | twocards_bdfd | — | 108 | 33 | 1.992 | 0.975 | 88.9% | 7.4% | 3.7% |
| flop | Cash100 | dry_high | no_made_hand | twocards_bdfd | — | 452 | 79 | 1.369 | 0.35 | 77.9% | 20.1% | 2.0% |
| flop | Cash100 | low_dry | king_high | twocards_bdfd | — | 64 | 22 | 1.312 | 0.657 | 65.6% | 32.8% | 1.6% |
| flop | Cash100 | dry_high | no_made_hand | onecard_bdfd | — | 102 | 12 | 1.296 | 0.165 | 31.4% | 50.0% | 18.6% |
| flop | Cash100 | dry_high | king_high | twocards_bdfd | — | 136 | 28 | 1.047 | 0.25 | 55.1% | 41.9% | 2.9% |
| flop | Cash100 | dynamic | low_pair | no_draw | — | 72 | 6 | 1.029 | 0.267 | 100.0% | 0.0% | 0.0% |
| flop | Cash100 | dynamic | low_pair | no_draw | — | 72 | 6 | 1.029 | 0.267 | 100.0% | 0.0% | 0.0% |
| flop | Cash100 | dry_high | king_high | onecard_bdfd | — | 78 | 10 | 0.943 | 0.136 | 24.4% | 70.5% | 5.1% |
| flop | Cash100 | low_dry | ace_high | onecard_bdfd | — | 60 | 9 | 0.911 | 0.176 | 35.0% | 58.3% | 6.7% |
| flop | Cash100 | low_dry | no_made_hand | gutshot | — | 73 | 6 | 0.863 | 0.131 | 38.4% | 45.2% | 16.4% |
| flop | Cash100 | dry_high | ace_high | onecard_bdfd | — | 150 | 18 | 0.763 | 0.159 | 34.7% | 48.0% | 17.3% |
| flop | Cash100 | dry_high | ace_high | twocards_bdfd | — | 124 | 9 | 0.739 | 0.115 | 37.9% | 54.0% | 8.1% |
| flop | Cash100 | dry_high | no_made_hand | gutshot | — | 284 | 17 | 0.62 | 0.896 | 7.7% | 61.6% | 30.6% |
| flop | Cash100 | dry_high | set | no_draw | — | 60 | 22 | 0.611 | 0.26 | 0.0% | 36.7% | 63.3% |
| flop | Cash100 | dry_high | set | no_draw | — | 60 | 22 | 0.611 | 0.26 | 0.0% | 36.7% | 63.3% |
| flop | Cash100 | dry_high | third_pair | no_draw | — | 273 | 60 | 0.546 | 0.593 | 11.7% | 83.2% | 5.1% |
| flop | Cash100 | dry_high | third_pair | no_draw | — | 273 | 60 | 0.546 | 0.593 | 11.7% | 83.2% | 5.1% |
| river | Cash100 | dry_high | fullhouse | no_draw | overbet | 86 | 83 | 8.094 | 7.825 | 0.0% | 3.5% | 96.5% |
| river | Cash100 | monotone | top_pair | no_draw | allin | 108 | 87 | 7.541 | 6.106 | 94.4% | 5.6% | 0.0% |
| river | Cash100 | dynamic | fullhouse | no_draw | overbet | 56 | 56 | 4.587 | 4.587 | 0.0% | 50.0% | 50.0% |

## 4. 境界 cell 内訳: pot_type × street 別件数

| pot_type | flop | turn | river |
|----------|------|------|-------|
| Cash100 | 17 | 4 | 21 |
| MTT100 | 46 | 0 | 0 |
| MTT25 | 34 | 0 | 0 |
| MTT50 | 30 | 9 | 19 |
| other | 5 | 0 | 0 |

## 5. Phase B fetch 推奨対象

- データ既存 cell (n≥50) で huge_loss が高い場合: **公式拡張で対応** (新規 fetch 不要)

- データ不足 cell (n<50): **Phase B fetch 対象**

- Cash と MTT で構造的に乖離する cell (差分 > 0.2 BB): **MTT 専用ルール検討**
