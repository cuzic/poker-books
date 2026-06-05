# Probe Priority Report v2 (formula-aware)

生成: probe_priority.py / scenarios=11 / all_rows=54505 / elapsed=4s

CORE_BOARDS 6 枚 (各 family 1 枚) × turn/river 動的選択で各 scenario を probe。公式 v9b/v10/v15 を applicable な hand 全てに適用し formula_loss を直接測定。

**判定基準**:
- `formula_huge_loss` 大 (≥0.3 BB) → 公式が大きく外す = **追加 fetch 価値 大**
- `formula_acc` 低 (<70%) → 公式が GTO best と一致しない頻度 大
- `bimodal_pct` 大 (>15%) → 単一 action 出力では原理的に miss、閾値判定 必要
- BASELINE 行と比較: probe 値が既存 fit と乖離 → out-of-domain の証拠

**注意**: 3BP/4BP は SPR/pot 単位が SRP と違うため formula_huge_loss の絶対値比較に注意。代わりに `formula_huge_pct` で「公式 miss 率」として相対比較してください。

## ランキング (formula_huge_loss 降順)

| Rank | ID | Target | GT/depth | n_combos | f_acc% | f_mean_loss | **f_huge_loss** | f_huge% | bimodal% | mean_gap | F/C/R% | ok/fail |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | **N_cash_3bp_river** | river_def_oop | Cash6mTest/100 | 6486 | 79.7 | 3.892 | **21.829** | 17.8 | 5.1% | 24.579 | 70.4/29.6/0.0% | 6/0 |
| 2 | **N_mtt100_river** | river_def_oop | MTTGeneral/100 | 6486 | 86.0 | 1.838 | **19.562** | 9.3 | 4.7% | 23.418 | 76.9/22.1/1.0% | 6/0 |
| 3 | **B_river** (BASELINE) | river_def_oop | Cash6mTest/100 | 3709 | 81.3 | 2.0 | **19.472** | 10.2 | 7.7% | 19.168 | 73.9/19.8/6.3% | 6/0 |
| 4 | **N_mtt25_river** | river_def_oop | MTTGeneral/25 | 5050 | 79.6 | 1.074 | **8.803** | 12.0 | 6.8% | 8.522 | 61.5/38.5/0.0% | 6/0 |
| 5 | **N_cash_4bp_flop** | flop_def_oop | Cash6mTest/100 | 7056 | 43.9 | 2.135 | **4.816** | 43.8 | 21.4% | 15.842 | 17.0/57.4/25.6% | 6/0 |
| 6 | **N_mtt200_turn** | turn_def_oop | MTTGeneral/200 | 4512 | 71.6 | 0.483 | **2.785** | 16.7 | 8.6% | 6.0 | 57.6/37.8/4.7% | 4/0 |
| 7 | **N_cash_3bp_flop** | flop_def_oop | Cash6mTest/100 | 7056 | 66.6 | 0.328 | **2.066** | 14.7 | 19.9% | 5.127 | 36.9/51.7/11.4% | 6/0 |
| 8 | **B_turn** (BASELINE) | turn_def_oop | Cash6mTest/100 | 3900 | 71.3 | 0.234 | **1.883** | 10.9 | 8.8% | 3.989 | 66.6/29.1/4.3% | 6/0 |
| 9 | **B_flop** (BASELINE) | flop_def_oop | Cash6mTest/100 | 3996 | 71.7 | 0.058 | **0.926** | 3.8 | 26.9% | 1.44 | 40.9/45.5/13.6% | 6/0 |
| 10 | **N_cash_cr_def** | flop_def_ip_cr | Cash6mTest/100 | 3127 | — | — | — | — | 14.9% | 4.64 | 45.0/51.1/3.8% | 6/0 |
| 11 | **N_cash_donk_def** | flop_def_ip_donk | Cash6mTest/100 | 3127 | — | — | — | — | 20.7% | 1.904 | 46.7/44.9/8.4% | 6/0 |

## Baseline 検証 (probe calibration)

既存 dataset_unified.csv で測定された値と probe 値を比較。近い → probe が正しく公式 fit を再現できている。乖離大 → board sample 偏り。

| ID | 既存 huge_loss | probe formula_huge_loss | 乖離 |
|---|---:|---:|---:|
| B_flop | 0.061 | 0.926 | +0.865 |
| B_turn | 0.048 | 1.883 | +1.835 |
| B_river | 0.212 | 19.472 | +19.260 |

## 詳細 (formula_huge_loss 降順)

### N_cash_3bp_river: Cash100 3BP river × BB def
- GT=Cash6mTest_6mNL100R2 depth=100 target=river_def_oop
- spots OK=6 FAIL=0 n_combos=6486
- ev_gap: mean=24.579, p90=80.091, max=139.1
- GTO huge_loss (公式非依存): 26.482
- **formula**: acc=79.7%, mean_loss=3.892, huge_loss=21.829, huge%=17.8%
- modal split: FOLD=70.4% CALL=29.6% RAISE=0.0%, bimodal_combo%=5.1%
- per-board huge_loss: dyn_T97=33.208 (n=1081), dry_K72=20.973 (n=1081), mono_Js=19.806 (n=1081), d2t_T97=31.487 (n=1081), pair_KK2=22.639 (n=1081), low_853=30.743 (n=1081)

### N_mtt100_river: MTT100 SRP river × BB def (depth diff vs MTT50 fit)
- GT=MTTGeneral_8m depth=100 target=river_def_oop
- spots OK=6 FAIL=0 n_combos=6486
- ev_gap: mean=23.418, p90=68.062, max=131.1
- GTO huge_loss (公式非依存): 24.888
- **formula**: acc=86.0%, mean_loss=1.838, huge_loss=19.562, huge%=9.3%
- modal split: FOLD=76.9% CALL=22.1% RAISE=1.0%, bimodal_combo%=4.7%
- per-board huge_loss: dyn_T97=36.682 (n=1081), dry_K72=18.64 (n=1081), mono_Js=7.319 (n=1081), d2t_T97=37.249 (n=1081), pair_KK2=20.465 (n=1081), low_853=30.24 (n=1081)

### B_river: [BASELINE] Cash100 SRP river × BB def (v15 in-domain)
- GT=Cash6mTest_6mNL100R2 depth=100 target=river_def_oop
- spots OK=6 FAIL=0 n_combos=3709
- ev_gap: mean=19.168, p90=56.453, max=125.5
- GTO huge_loss (公式非依存): 19.948
- **formula**: acc=81.3%, mean_loss=2.0, huge_loss=19.472, huge%=10.2%
- modal split: FOLD=73.9% CALL=19.8% RAISE=6.3%, bimodal_combo%=7.7%
- per-board huge_loss: dyn_T97=29.943 (n=608), dry_K72=27.147 (n=624), mono_Js=7.443 (n=629), d2t_T97=8.456 (n=608), pair_KK2=6.897 (n=617), low_853=39.923 (n=623)

### N_mtt25_river: MTT25 SRP river × BB def (short stack)
- GT=MTTGeneral_8m depth=25 target=river_def_oop
- spots OK=6 FAIL=0 n_combos=5050
- ev_gap: mean=8.522, p90=25.97, max=37.9
- GTO huge_loss (公式非依存): 10.946
- **formula**: acc=79.6%, mean_loss=1.074, huge_loss=8.803, huge%=12.0%
- modal split: FOLD=61.5% CALL=38.5% RAISE=0.0%, bimodal_combo%=6.8%
- per-board huge_loss: dyn_T97=10.923 (n=842), dry_K72=10.183 (n=846), mono_Js=10.739 (n=837), d2t_T97=10.491 (n=842), pair_KK2=10.716 (n=848), low_853=12.812 (n=835)

### N_cash_4bp_flop: Cash100 4BP flop × BB def (SPR ~1)
- GT=Cash6mTest_6mNL100R2 depth=100 target=flop_def_oop
- spots OK=6 FAIL=0 n_combos=7056
- ev_gap: mean=15.842, p90=44.511, max=86.327
- GTO huge_loss (公式非依存): 17.67
- **formula**: acc=43.9%, mean_loss=2.135, huge_loss=4.816, huge%=43.8%
- modal split: FOLD=17.0% CALL=57.4% RAISE=25.6%, bimodal_combo%=21.4%
- per-board huge_loss: dyn_T97=18.736 (n=1176), dry_K72=18.261 (n=1176), mono_Js=17.005 (n=1176), d2t_T97=17.337 (n=1176), pair_KK2=18.202 (n=1176), low_853=16.737 (n=1176)

### N_mtt200_turn: MTT200 SRP turn × BB def (deep)
- GT=MTTGeneral_8m depth=200 target=turn_def_oop
- spots OK=4 FAIL=0 n_combos=4512
- ev_gap: mean=6.0, p90=13.161, max=125.908
- GTO huge_loss (公式非依存): 6.52
- **formula**: acc=71.6%, mean_loss=0.483, huge_loss=2.785, huge%=16.7%
- modal split: FOLD=57.6% CALL=37.8% RAISE=4.7%, bimodal_combo%=8.6%
- per-board huge_loss: dry_K72=3.901 (n=1128), dyn_T97=4.521 (n=1128), low_853=12.755 (n=1128), d2t_T97=4.524 (n=1128)

### N_cash_3bp_flop: Cash100 3BP flop × BB def (3bettor OOP)
- GT=Cash6mTest_6mNL100R2 depth=100 target=flop_def_oop
- spots OK=6 FAIL=0 n_combos=7056
- ev_gap: mean=5.127, p90=13.284, max=50.641
- GTO huge_loss (公式非依存): 6.328
- **formula**: acc=66.6%, mean_loss=0.328, huge_loss=2.066, huge%=14.7%
- modal split: FOLD=36.9% CALL=51.7% RAISE=11.4%, bimodal_combo%=19.9%
- per-board huge_loss: dyn_T97=6.033 (n=1176), dry_K72=7.194 (n=1176), mono_Js=6.091 (n=1176), d2t_T97=5.885 (n=1176), pair_KK2=7.033 (n=1176), low_853=6.013 (n=1176)

### B_turn: [BASELINE] Cash100 SRP turn × BB def (v10 in-domain)
- GT=Cash6mTest_6mNL100R2 depth=100 target=turn_def_oop
- spots OK=6 FAIL=0 n_combos=3900
- ev_gap: mean=3.989, p90=8.925, max=62.12
- GTO huge_loss (公式非依存): 4.621
- **formula**: acc=71.3%, mean_loss=0.234, huge_loss=1.883, huge%=10.9%
- modal split: FOLD=66.6% CALL=29.1% RAISE=4.3%, bimodal_combo%=8.8%
- per-board huge_loss: dyn_T97=5.649 (n=639), dry_K72=5.974 (n=656), mono_Js=2.841 (n=661), d2t_T97=3.071 (n=639), pair_KK2=2.807 (n=649), low_853=7.357 (n=656)

### B_flop: [BASELINE] Cash100 SRP flop × BB def (v9b in-domain)
- GT=Cash6mTest_6mNL100R2 depth=100 target=flop_def_oop
- spots OK=6 FAIL=0 n_combos=3996
- ev_gap: mean=1.44, p90=3.792, max=27.69
- GTO huge_loss (公式非依存): 2.323
- **formula**: acc=71.7%, mean_loss=0.058, huge_loss=0.926, huge%=3.8%
- modal split: FOLD=40.9% CALL=45.5% RAISE=13.6%, bimodal_combo%=26.9%
- per-board huge_loss: dyn_T97=1.931 (n=655), dry_K72=3.147 (n=672), mono_Js=2.335 (n=677), d2t_T97=1.917 (n=655), pair_KK2=4.434 (n=665), low_853=1.865 (n=672)

### N_cash_cr_def: Cash100 SRP flop × BTN def (vs BB CR)
- GT=Cash6mTest_6mNL100R2 depth=100 target=flop_def_ip_cr
- spots OK=6 FAIL=0 n_combos=3127
- ev_gap: mean=4.64, p90=13.302, max=48.656
- GTO huge_loss (公式非依存): 6.576
- **formula**: 適用外 (CR/donk/IP defender — 専用公式なし)
- modal split: FOLD=45.0% CALL=51.1% RAISE=3.8%, bimodal_combo%=14.9%
- per-board huge_loss: dyn_T97=10.366 (n=510), dry_K72=4.508 (n=529), mono_Js=3.362 (n=531), d2t_T97=8.3 (n=510), pair_KK2=7.324 (n=512), low_853=3.364 (n=535)

### N_cash_donk_def: Cash100 SRP flop × BTN def (vs BB donk)
- GT=Cash6mTest_6mNL100R2 depth=100 target=flop_def_ip_donk
- spots OK=6 FAIL=0 n_combos=3127
- ev_gap: mean=1.904, p90=4.887, max=25.601
- GTO huge_loss (公式非依存): 2.983
- **formula**: 適用外 (CR/donk/IP defender — 専用公式なし)
- modal split: FOLD=46.7% CALL=44.9% RAISE=8.4%, bimodal_combo%=20.7%
- per-board huge_loss: dyn_T97=2.699 (n=510), dry_K72=3.856 (n=529), mono_Js=2.567 (n=531), d2t_T97=2.634 (n=510), pair_KK2=6.452 (n=512), low_853=2.227 (n=535)


## 推奨フォローアップ

`formula_huge_loss >= 0.3 BB` かつ `n_combos >= 100` を Tier1 候補とする。
CR/donk (formula N/A) は `huge_loss + bimodal_pct` で判定。

### Tier 1 (即 fetch):
- **N_cash_3bp_river** (formula_huge_loss=21.829): Cash100 3BP river × BB def
- **N_mtt100_river** (formula_huge_loss=19.562): MTT100 SRP river × BB def (depth diff vs MTT50 fit)
- **N_mtt25_river** (formula_huge_loss=8.803): MTT25 SRP river × BB def (short stack)
- **N_cash_4bp_flop** (formula_huge_loss=4.816): Cash100 4BP flop × BB def (SPR ~1)
- **N_mtt200_turn** (formula_huge_loss=2.785): MTT200 SRP turn × BB def (deep)
- **N_cash_3bp_flop** (formula_huge_loss=2.066): Cash100 3BP flop × BB def (3bettor OOP)

### Tier 2 (CR/donk 専用):
- **N_cash_cr_def** (huge_loss=6.576, bimodal=14.9%): Cash100 SRP flop × BTN def (vs BB CR)
- **N_cash_donk_def** (huge_loss=2.983, bimodal=20.7%): Cash100 SRP flop × BTN def (vs BB donk)
