# 深堀り inventory: 全 findings ファイルの実際の中身を抽出

**スキャン完了: 成功 896 / 失敗 0 ファイル**

## Phase 別

| Phase | ファイル数 |
|-------|---------|
| turn | 530 |
| river | 202 |
| preflop | 164 |

## Depth 別

| Depth | ファイル数 |
|-------|---------|
| 100 bb | 301 |
| 50 bb | 234 |
| ? bb | 159 |
| 200 bb | 120 |
| 25 bb | 80 |
| 40 bb | 1 |
| 20 bb | 1 |

## Actor 別 (誰の番か)

| Actor | ファイル数 |
|-------|---------|
| BB | 300 |
| ? | 158 |
| BTN | 149 |
| CO | 72 |
| HJ | 72 |
| LJ | 72 |
| SB | 72 |
|  | 1 |

## Opener 別 (誰がオープンしたか)

| Opener | ファイル数 |
|--------|---------|
| BTN | 450 |
| ? | 130 |
| SB | 78 |
| CO | 74 |
| HJ | 74 |
| UTG | 73 |
| BB | 17 |

## Player Count

- 0 players: 159 files
- 1 players: 3 files
- 2 players: 734 files

## 3BP / 4BP シナリオ


## Donk / lead シナリオ (BB が postflop で先手)

- **BB lead at turn**: 96 files
    - vol3-mtt-postflop/findings/def_mtt25_bb_raw/K72_fd.json
    - vol3-mtt-postflop/findings/def_mtt25_bb_raw/765_rain.json
    - vol3-mtt-postflop/findings/def_mtt25_bb_raw/742_rain.json
    - ... (93 more)
- **BB lead at river**: 202 files
    - vol3-mtt-postflop/findings/turn_mtt100_btn_raw/K72r_7.json
    - vol3-mtt-postflop/findings/turn_mtt100_btn_raw/Q83_8.json
    - vol3-mtt-postflop/findings/turn_mtt100_btn_raw/K98r_7.json
    - ... (199 more)

## シナリオパターン TOP 30

| シナリオ | ファイル数 | 例 |
|---------|---------|----|
| `BTN open → BB act (N_callers=0, depth=100)` | 156 | `K72r_7.json` |
| `? open → ? act (N_callers=0, depth=?)` | 125 | `cash_pairwise_gto.json` |
| `BTN open → BB act (N_callers=0, depth=50)` | 89 | `Q83-Q-J_R35.5.json` |
| `BTN open → BB act (N_callers=0, depth=25)` | 54 | `K72_fd.json` |
| `BTN open → BTN act (N_callers=0, depth=50)` | 49 | `BTN_BB_K72_rain.json` |
| `BTN open → BTN act (N_callers=0, depth=100)` | 48 | `BTN_BB_KJT_fd.json` |
| `CO open → CO act (N_callers=0, depth=100)` | 24 | `CO_BB_K98_fd.json` |
| `HJ open → HJ act (N_callers=0, depth=100)` | 24 | `HJ_BB_K98_rain.json` |
| `UTG open → LJ act (N_callers=0, depth=100)` | 24 | `UTG_BB_K72_fd.json` |
| `SB open → SB act (N_callers=0, depth=100)` | 24 | `SB_BB_742_rain.json` |
| `CO open → CO act (N_callers=0, depth=200)` | 24 | `CO_BB_K98_fd.json` |
| `BTN open → BTN act (N_callers=0, depth=200)` | 24 | `BTN_BB_KJT_fd.json` |
| `HJ open → HJ act (N_callers=0, depth=200)` | 24 | `HJ_BB_K98_rain.json` |
| `UTG open → LJ act (N_callers=0, depth=200)` | 24 | `UTG_BB_K72_fd.json` |
| `SB open → SB act (N_callers=0, depth=200)` | 24 | `SB_BB_742_rain.json` |
| `BTN open → BTN act (N_callers=0, depth=25)` | 24 | `BTN_BB_KJT_fd.json` |
| `CO open → CO act (N_callers=0, depth=50)` | 24 | `CO_BB_K98_fd.json` |
| `HJ open → HJ act (N_callers=0, depth=50)` | 24 | `HJ_BB_K98_rain.json` |
| `UTG open → LJ act (N_callers=0, depth=50)` | 24 | `UTG_BB_K72_fd.json` |
| `SB open → SB act (N_callers=0, depth=50)` | 24 | `SB_BB_742_rain.json` |
| `BB open → ? act (N_callers=0, depth=?)` | 17 | `preflop_study_BB_def_BTN_20.json` |
| `SB open → ? act (N_callers=0, depth=?)` | 6 | `preflop_study_SB_def_BTN_25.json` |
| `BTN open → ? act (N_callers=0, depth=?)` | 6 | `mtt_flop_cbet_SBR25_BTN_BB.json` |
| `? open → BTN act (N_callers=0, depth=25)` | 2 | `mtt_preflop_probe_SBR25.json` |
| `HJ open → ? act (N_callers=0, depth=?)` | 2 | `defense_study_HJ_BB_SRP20.jsonl` |
| `CO open → ? act (N_callers=0, depth=?)` | 2 | `defense_study_CO_BB_SRP20.jsonl` |
| `? open → BTN act (N_callers=0, depth=40)` | 1 | `mtt_preflop_probe_SBR40.json` |
| `? open → BTN act (N_callers=0, depth=20)` | 1 | `mtt_preflop_probe_SBR20.json` |
| `? open →  act (N_callers=0, depth=?)` | 1 | `hs_validation.jsonl` |
| `UTG open → BB act (N_callers=0, depth=100)` | 1 | `order_probe2_bb_vs_utg.json` |

