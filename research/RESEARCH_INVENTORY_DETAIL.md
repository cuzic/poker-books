# GTO 研究データ Inventory (2026-06-04 自動生成)

**目的**: 既存の GTO Wizard 研究データを Claude / 作業者が再取得しないための網羅リスト。

各ファイルが何のシナリオ・ボード・フェーズ・データレベルをカバーしているかを記載。

**合計 JSON ファイル数**: 894

## データレベル別集計

| データレベル | ファイル数 | 説明 |
|------------|---------|------|
| hand-level | 798 | 169 starting hands の個別頻度 |
| per-mv-cat | 54 | 16 役 (mv) 別の集約頻度 |
| aggregate | 39 | 全体集約 (cbet_pct 等) |
| per-5cat | 2 | 5-category (V/BC/WD/Air) 別の集約 |
| per-5cat-jp | 1 | 5-category (バリュー/ブラフキャッチャー/エアー) 日本語 |

## research/v3-additional/findings/

**ファイル数**: 20

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `order_probe2_bb_vs_utg.json` | 273KB | hand-level | - | - | 1 |
| `probe_bb_vs_btn.json` | 276KB | hand-level | - | - | 1 |
| `task_a_BB_vs_BTN.json` | 13KB | hand-level | - | BB_vs_BTN | 0 |
| `task_a_BB_vs_CO.json` | 13KB | hand-level | - | BB_vs_CO | 0 |
| `task_a_BB_vs_HJ.json` | 13KB | hand-level | - | BB_vs_HJ | 0 |
| `task_a_BB_vs_SB.json` | 13KB | hand-level | - | BB_vs_SB | 0 |
| `task_a_BB_vs_UTG.json` | 13KB | hand-level | - | BB_vs_UTG | 0 |
| `task_c_BB_sq_vs_BTN_N1_sb.json` | 13KB | hand-level | - | BB_sq_vs_BTN_N1_sb | 0 |
| `task_c_BB_sq_vs_UTG_N1_bn.json` | 13KB | hand-level | - | BB_sq_vs_UTG_N1_bn | 0 |
| `task_c_BB_sq_vs_UTG_N1_co.json` | 13KB | hand-level | - | BB_sq_vs_UTG_N1_co | 0 |
| `task_c_BB_sq_vs_UTG_N1_hj.json` | 13KB | hand-level | - | BB_sq_vs_UTG_N1_hj | 0 |
| `task_c_BB_sq_vs_UTG_N2_co_bn.json` | 13KB | hand-level | - | BB_sq_vs_UTG_N2_co_bn | 0 |
| `task_c_BB_sq_vs_UTG_N2_hj_co.json` | 13KB | hand-level | - | BB_sq_vs_UTG_N2_hj_co | 0 |
| `task_c_BTN_sq_vs_HJ_N1_co.json` | 13KB | hand-level | - | BTN_sq_vs_HJ_N1_co | 0 |
| `task_c_BTN_sq_vs_UTG_N1_co.json` | 13KB | hand-level | - | BTN_sq_vs_UTG_N1_co | 0 |
| `task_c_BTN_sq_vs_UTG_N1_hj.json` | 13KB | hand-level | - | BTN_sq_vs_UTG_N1_hj | 0 |
| `task_c_BTN_sq_vs_UTG_N2.json` | 13KB | hand-level | - | BTN_sq_vs_UTG_N2 | 0 |
| `task_c_SB_sq_vs_HJ_N1_co.json` | 13KB | hand-level | - | SB_sq_vs_HJ_N1_co | 0 |
| `task_c_SB_sq_vs_UTG_N1_co.json` | 13KB | hand-level | - | SB_sq_vs_UTG_N1_co | 0 |
| `task_c_SB_sq_vs_UTG_N1_hj.json` | 13KB | hand-level | - | SB_sq_vs_UTG_N1_hj | 0 |

## vol2-cash-postflop/findings/

**ファイル数**: 6

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `cash_5cat_gto.json` | 69KB | per-mv-cat | - | BTN_BB,CO_BB,HJ_BB,SB_BB,UTG_BB | 7 |
| `cash_board_wide_gto.json` | - | aggregate | - | - | 0 |
| `cash_defense_gto.json` | 73KB | per-5cat | - | BTN_BB,CO_BB,HJ_BB,SB_BB,UTG_BB | 7 |
| `cash_flop_detail_gto.json` | 84KB | per-5cat | - | 3BP_IP,3BP_OOP,SRP_IP,SRP_OOP | 0 |
| `cash_pairwise_gto.json` | 107KB | per-5cat-jp | - | 3BP_IP,3BP_OOP,SRP_IP,SRP_OOP | 0 |
| `cash_preflop_gto_summary.json` | 2KB | aggregate | - | - | 0 |

## vol3-mtt-postflop/findings/

**ファイル数**: 136

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `diagnose_Ks7d2c_25.json` | 954KB | hand-level | 25bb | - | 1 |
| `mtt_check_raise_SBR20.json` | 41KB | aggregate | - | SRP BTN vs BB (Middle(SBR20)) | 0 |
| `mtt_check_raise_SBR25.json` | 46KB | aggregate | - | SRP BTN vs BB (Middle-Deep(SBR25)) | 0 |
| `mtt_flop_cbet_SBR20_BTN_BB.json` | 41KB | aggregate | - | SRP BTN vs BB (Middle(SBR20)) | 0 |
| `mtt_flop_cbet_SBR25_BTN_BB.json` | 44KB | aggregate | - | SRP BTN vs BB (Middle-Deep(SBR25)) | 0 |
| `mtt_preflop_gto_SBR15_rfi.json` | - | aggregate | - | - | 0 |
| `mtt_preflop_gto_SBR20_multiway.json` | 446KB | hand-level | - | - | 0 |
| `mtt_preflop_gto_SBR20_rfi.json` | 209KB | hand-level | - | - | 0 |
| `mtt_preflop_gto_SBR20_vs_3bet.json` | 44KB | aggregate | - | - | 0 |
| `mtt_preflop_gto_SBR20_vs_4bet.json` | 8KB | aggregate | - | - | 0 |
| `mtt_preflop_gto_SBR20_vs_5bet.json` | - | aggregate | - | - | 0 |
| `mtt_preflop_gto_SBR20_vs_open.json` | 419KB | hand-level | - | - | 0 |
| `mtt_preflop_gto_SBR25_multiway.json` | 536KB | hand-level | - | - | 0 |
| `mtt_preflop_gto_SBR25_rfi.json` | 209KB | hand-level | - | - | 0 |
| `mtt_preflop_gto_SBR25_vs_3bet.json` | 48KB | aggregate | - | - | 0 |
| `mtt_preflop_gto_SBR25_vs_4bet.json` | 15KB | aggregate | - | - | 0 |
| `mtt_preflop_gto_SBR25_vs_5bet.json` | - | aggregate | - | - | 0 |
| `mtt_preflop_gto_SBR25_vs_open.json` | 420KB | hand-level | - | - | 0 |
| `mtt_preflop_gto_SBR40_all.json` | 208KB | hand-level | - | - | 0 |
| `mtt_preflop_gto_SBR40_multiway.json` | 654KB | hand-level | - | - | 0 |
| `mtt_preflop_gto_SBR40_vs_3bet.json` | 90KB | aggregate | - | - | 0 |
| `mtt_preflop_gto_SBR40_vs_4bet.json` | 38KB | aggregate | - | - | 0 |
| `mtt_preflop_gto_SBR40_vs_5bet.json` | - | aggregate | - | - | 0 |
| `mtt_preflop_gto_SBR40_vs_open.json` | 421KB | hand-level | - | - | 0 |
| `mtt_preflop_probe_SBR20.json` | 131KB | hand-level | - | - | 1 |
| `mtt_preflop_probe_SBR25.json` | 131KB | hand-level | - | - | 1 |
| `mtt_preflop_probe_SBR40.json` | 118KB | hand-level | - | - | 1 |
| `mtt_sb_bb_SBR20.json` | 76KB | aggregate | - | SRP SB vs BB (Middle(SBR20)) | 0 |
| `mtt_sb_bb_SBR25.json` | 78KB | aggregate | - | SRP SB vs BB (Middle-Deep(SBR25)) | 0 |
| `mtt_turn_barrel_SBR20.json` | 8KB | aggregate | - | SRP BTN vs BB (Middle(SBR20)) | 0 |
| `mtt_turn_barrel_SBR25.json` | 8KB | aggregate | - | SRP BTN vs BB (Middle-Deep(SBR25)) | 0 |
| `preflop_hand_map.json` | 5KB | aggregate | - | - | 0 |
| `preflop_study_BB_def_BTN_15.json` | 26KB | hand-level | - | BB_def_BTN_15 | 0 |
| `preflop_study_BB_def_BTN_20.json` | 26KB | hand-level | - | BB_def_BTN_20 | 0 |
| `preflop_study_BB_def_BTN_200.json` | 26KB | hand-level | - | BB_def_BTN_200 | 0 |
| `preflop_study_BB_def_BTN_25.json` | 26KB | hand-level | 25bb | BB_def_BTN_25 | 0 |
| `preflop_study_BB_def_BTN_30.json` | 26KB | hand-level | - | BB_def_BTN_30 | 0 |
| `preflop_study_BB_def_HJ_200.json` | 26KB | hand-level | - | BB_def_HJ_200 | 0 |
| `preflop_study_BTN_RFI_15.json` | 25KB | hand-level | - | BTN_RFI_15 | 0 |
| `preflop_study_BTN_RFI_20.json` | 25KB | hand-level | - | BTN_RFI_20 | 0 |
| `preflop_study_BTN_RFI_200.json` | 25KB | hand-level | - | BTN_RFI_200 | 0 |
| `preflop_study_BTN_RFI_25.json` | 25KB | hand-level | 25bb | BTN_RFI_25 | 0 |
| `preflop_study_BTN_RFI_30.json` | 25KB | hand-level | - | BTN_RFI_30 | 0 |
| `preflop_study_CO_RFI_15.json` | 25KB | hand-level | - | CO_RFI_15 | 0 |
| `preflop_study_CO_RFI_20.json` | 25KB | hand-level | - | CO_RFI_20 | 0 |
| `preflop_study_CO_RFI_200.json` | 25KB | hand-level | - | CO_RFI_200 | 0 |
| `preflop_study_CO_RFI_25.json` | 25KB | hand-level | 25bb | CO_RFI_25 | 0 |
| `preflop_study_CO_RFI_30.json` | 25KB | hand-level | - | CO_RFI_30 | 0 |
| `preflop_study_HJ_RFI_15.json` | 25KB | hand-level | - | HJ_RFI_15 | 0 |
| `preflop_study_HJ_RFI_20.json` | 25KB | hand-level | - | HJ_RFI_20 | 0 |
| `preflop_study_HJ_RFI_200.json` | 25KB | hand-level | - | HJ_RFI_200 | 0 |
| `preflop_study_HJ_RFI_25.json` | 25KB | hand-level | 25bb | HJ_RFI_25 | 0 |
| `preflop_study_HJ_RFI_30.json` | 25KB | hand-level | - | HJ_RFI_30 | 0 |
| `preflop_study_LJ_RFI_15.json` | 25KB | hand-level | - | LJ_RFI_15 | 0 |
| `preflop_study_LJ_RFI_20.json` | 25KB | hand-level | - | LJ_RFI_20 | 0 |
| `preflop_study_LJ_RFI_200.json` | 25KB | hand-level | - | LJ_RFI_200 | 0 |
| `preflop_study_LJ_RFI_25.json` | 25KB | hand-level | 25bb | LJ_RFI_25 | 0 |
| `preflop_study_LJ_RFI_30.json` | 25KB | hand-level | - | LJ_RFI_30 | 0 |
| `preflop_study_SB_RFI_15.json` | 26KB | hand-level | - | SB_RFI_15 | 0 |
| `preflop_study_SB_RFI_20.json` | 26KB | hand-level | - | SB_RFI_20 | 0 |
| `preflop_study_SB_RFI_200.json` | 26KB | hand-level | - | SB_RFI_200 | 0 |
| `preflop_study_SB_RFI_25.json` | 26KB | hand-level | 25bb | SB_RFI_25 | 0 |
| `preflop_study_SB_RFI_30.json` | 26KB | hand-level | - | SB_RFI_30 | 0 |
| `preflop_study_SB_def_BTN_20.json` | 26KB | hand-level | - | SB_def_BTN_20 | 0 |
| `preflop_study_SB_def_BTN_200.json` | 26KB | hand-level | - | SB_def_BTN_200 | 0 |
| `preflop_study_SB_def_BTN_25.json` | 26KB | hand-level | 25bb | SB_def_BTN_25 | 0 |
| `defense_study_3BP20_IP.jsonl` | 38KB | per-mv-cat | - | 3BP20_IP | 1 |
| `defense_study_3BP20_OOP.jsonl` | 35KB | per-mv-cat | - | 3BP20_OOP | 1 |
| `defense_study_3BP25_SB_IP.jsonl` | 35KB | per-mv-cat | - | 3BP25_SB_IP | 1 |
| `defense_study_3BP25_SB_OOP.jsonl` | 44KB | per-mv-cat | - | 3BP25_SB_OOP | 1 |
| `defense_study_CO_BB_SRP20.jsonl` | 44KB | per-mv-cat | - | CO_BB_SRP20 | 1 |
| `defense_study_CO_BB_SRP25.jsonl` | 72KB | per-mv-cat | - | CO_BB_SRP25 | 1 |
| `defense_study_EP1_BB_SRP20.jsonl` | 44KB | per-mv-cat | - | EP1_BB_SRP20 | 1 |
| `defense_study_EP2_BB_SRP20.jsonl` | 48KB | per-mv-cat | - | EP2_BB_SRP20 | 1 |
| `defense_study_EP3_BB_SRP20.jsonl` | 47KB | per-mv-cat | - | EP3_BB_SRP20 | 1 |
| `defense_study_EP3_BB_SRP25.jsonl` | 46KB | per-mv-cat | - | EP3_BB_SRP25 | 1 |
| `defense_study_HJ_BB_SRP20.jsonl` | 44KB | per-mv-cat | - | HJ_BB_SRP20 | 1 |
| `defense_study_HJ_BB_SRP25.jsonl` | 45KB | per-mv-cat | - | HJ_BB_SRP25 | 1 |
| `defense_study_SRP20_OOP.jsonl` | 42KB | per-mv-cat | - | SRP20_OOP | 1 |
| `defense_study_SRP20_SB_IP.jsonl` | 45KB | per-mv-cat | - | SRP20_SB_IP | 1 |
| `defense_study_SRP20_SB_OOP.jsonl` | 42KB | per-mv-cat | - | SRP20_SB_OOP | 1 |
| `defense_study_SRP25_OOP.jsonl` | 42KB | per-mv-cat | - | SRP25_OOP | 1 |
| `defense_study_SRP25_SB_IP.jsonl` | 50KB | per-mv-cat | - | SRP25_SB_IP | 1 |
| `defense_study_SRP25_SB_OOP.jsonl` | 44KB | per-mv-cat | - | SRP25_SB_OOP | 1 |
| `draw_study_3BP100.jsonl` | 17KB | per-mv-cat | 100bb | BTN_BB | 1 |
| `draw_study_3BP20.jsonl` | 161KB | per-mv-cat | - | 3BP20 | 1 |
| `draw_study_3BP25.jsonl` | 17KB | per-mv-cat | - | BTN_BB | 1 |
| `draw_study_3BP25_SB.jsonl` | 168KB | per-mv-cat | - | 3BP25_SB | 1 |
| `draw_study_3BP50.jsonl` | 17KB | per-mv-cat | - | BTN_BB | 1 |
| `draw_study_CASH50BB.jsonl` | - | per-mv-cat | 100bb | BTN_BB | 1 |
| `draw_study_DEF_CASH100_BB.jsonl` | 22KB | per-mv-cat | 100bb | - | 1 |
| `draw_study_DEF_MTT100_BB.jsonl` | 22KB | per-mv-cat | 100bb | - | 1 |
| `draw_study_DEF_MTT25_BB.jsonl` | 25KB | per-mv-cat | - | - | 1 |
| `draw_study_DEF_MTT50_BB.jsonl` | 25KB | per-mv-cat | - | - | 1 |
| `draw_study_LIMP20_SB.jsonl` | 476KB | per-mv-cat | - | LIMP20_SB | 1 |
| `draw_study_LIMP25_SB.jsonl` | 485KB | per-mv-cat | - | LIMP25_SB | 1 |
| `draw_study_MTT100BB.jsonl` | 83KB | per-mv-cat | 100bb | UTG_BB | 1 |
| `draw_study_MTT200BB.jsonl` | 85KB | per-mv-cat | - | UTG_BB | 1 |
| `draw_study_MTT50BB.jsonl` | 85KB | per-mv-cat | - | UTG_BB | 1 |
| `draw_study_SBR25.jsonl` | 111KB | aggregate | - | - | 1 |
| `draw_study_SRP20.jsonl` | 281KB | per-mv-cat | - | SRP20 | 1 |
| `draw_study_SRP20_CO.jsonl` | 241KB | per-mv-cat | - | SRP20_CO | 1 |
| `draw_study_SRP20_SB.jsonl` | 365KB | per-mv-cat | - | SRP20_SB | 1 |
| `draw_study_SRP20_SB_cc.jsonl` | 282KB | per-mv-cat | - | SRP20_SB_cc | 1 |
| `draw_study_SRP25.jsonl` | 305KB | per-mv-cat | - | SRP25 | 1 |
| `draw_study_SRP25_SB.jsonl` | 402KB | per-mv-cat | - | SRP25_SB | 1 |
| `draw_study_SRP25_SB_cc.jsonl` | 308KB | per-mv-cat | - | SRP25_SB_cc | 1 |
| `draw_study_TURN_CASH100_BTN.jsonl` | 20KB | per-mv-cat | 100bb | - | 1 |
| `draw_study_TURN_MTT100_BTN.jsonl` | 16KB | per-mv-cat | 100bb | - | 1 |
| `draw_study_TURN_MTT25_BTN.jsonl` | 21KB | per-mv-cat | - | - | 1 |
| `draw_study_TURN_MTT50_BTN.jsonl` | 22KB | per-mv-cat | - | - | 1 |
| `equity_study_SBR25.jsonl` | 27KB | aggregate | - | - | 1 |
| `hs_validation.jsonl` | 180KB | aggregate | - | - | 1 |
| `phase1_btn_bb_srp.jsonl` | 3KB | aggregate | - | - | 1 |
| `phase1_btn_cbet.jsonl` | 6KB | aggregate | - | BTN_CBet_after_BBcheck | 1 |
| `phase2_icm_stages.jsonl` | - | aggregate | - | - | 1 |
| `river_defense_3BP20_OOP_river.jsonl` | 7KB | aggregate | - | 3BP20_OOP_river | 0 |
| `river_defense_SRP20_BTN.jsonl` | 22KB | aggregate | - | SRP20_BTN | 0 |
| `river_defense_SRP25_BTN.jsonl` | 25KB | per-mv-cat | - | SRP25_BTN | 0 |
| `s1_bb_cbet_response.jsonl` | - | aggregate | - | S1_bb_response | 1 |
| `s2_board_types.jsonl` | 12KB | aggregate | - | S2 | 1 |
| `s2_board_types_cbet.jsonl` | 3KB | aggregate | - | S2_cbet | 1 |
| `s4_turn_barrel.jsonl` | 2KB | aggregate | - | - | 1 |
| `s4_turn_barrel_q83.jsonl` | 1KB | aggregate | - | - | 1 |
| `s6_sb_vs_bb_v2.jsonl` | 1KB | aggregate | - | S6 | 1 |
| `sbr_depth_LIMP40_SB.jsonl` | 395KB | per-mv-cat | - | LIMP40_SB | 1 |
| `sbr_depth_SRP40_SB.jsonl` | 309KB | per-mv-cat | - | SRP40_SB | 1 |
| `ta_flopsize_comparison.jsonl` | 1KB | aggregate | - | - | 1 |
| `ta_oop_turn.jsonl` | 1KB | aggregate | - | - | 1 |
| `ta_validation_boardtypes.jsonl` | 3KB | aggregate | - | - | 1 |
| `turn_defense_3BP20_IP_turn.jsonl` | 17KB | per-mv-cat | - | 3BP20_IP_turn | 0 |
| `turn_defense_3BP20_OOP_turn.jsonl` | 4KB | aggregate | - | 3BP20_OOP_turn | 0 |
| `turn_defense_3BP25_SB_OOP_turn.jsonl` | 30KB | per-mv-cat | - | 3BP25_SB_OOP_turn | 0 |
| `turn_defense_SRP20_BTN.jsonl` | 27KB | per-mv-cat | - | SRP20_BTN | 0 |
| `turn_defense_SRP25_BTN.jsonl` | 29KB | per-mv-cat | - | SRP25_BTN | 0 |
| `turn_defense_SRP25_SB_OOP_turn.jsonl` | 25KB | per-mv-cat | - | SRP25_SB_OOP_turn | 0 |

## vol3-mtt-postflop/findings/3bp100_raw/

**ファイル数**: 24

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `BTN_BB_742_fd.json` | 508KB | hand-level | - | - | 1 |
| `BTN_BB_742_rain.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_765_fd.json` | 508KB | hand-level | - | - | 1 |
| `BTN_BB_765_rain.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_A72_fd.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_A72_rain.json` | 505KB | hand-level | - | - | 1 |
| `BTN_BB_A94_fd.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_A94_rain.json` | 505KB | hand-level | - | - | 1 |
| `BTN_BB_AA7_rain.json` | 504KB | hand-level | - | - | 1 |
| `BTN_BB_J73_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_J73_rain.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_K72_fd.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_K72_rain.json` | 505KB | hand-level | - | - | 1 |
| `BTN_BB_K98_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_K98_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_KJT_fd.json` | 502KB | hand-level | - | - | 1 |
| `BTN_BB_KJT_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_KK8_rain.json` | 505KB | hand-level | - | - | 1 |
| `BTN_BB_Q83_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_Q83_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_T74_fd.json` | 508KB | hand-level | - | - | 1 |
| `BTN_BB_T74_rain.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_T98_fd.json` | 508KB | hand-level | - | - | 1 |
| `BTN_BB_T98_rain.json` | 507KB | hand-level | - | - | 1 |

## vol3-mtt-postflop/findings/3bp25_raw/

**ファイル数**: 24

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `BTN_BB_742_fd.json` | 508KB | hand-level | - | - | 1 |
| `BTN_BB_742_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_765_fd.json` | 510KB | hand-level | - | - | 1 |
| `BTN_BB_765_rain.json` | 509KB | hand-level | - | - | 1 |
| `BTN_BB_A72_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_A72_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_A94_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_A94_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_AA7_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_J73_fd.json` | 508KB | hand-level | - | - | 1 |
| `BTN_BB_J73_rain.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_K72_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_K72_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_K98_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_K98_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_KJT_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_KJT_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_KK8_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_Q83_fd.json` | 508KB | hand-level | - | - | 1 |
| `BTN_BB_Q83_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_T74_fd.json` | 508KB | hand-level | - | - | 1 |
| `BTN_BB_T74_rain.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_T98_fd.json` | 508KB | hand-level | - | - | 1 |
| `BTN_BB_T98_rain.json` | 507KB | hand-level | - | - | 1 |

## vol3-mtt-postflop/findings/3bp50_raw/

**ファイル数**: 24

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `BTN_BB_742_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_742_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_765_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_765_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_A72_fd.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_A72_rain.json` | 505KB | hand-level | - | - | 1 |
| `BTN_BB_A94_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_A94_rain.json` | 505KB | hand-level | - | - | 1 |
| `BTN_BB_AA7_rain.json` | 504KB | hand-level | - | - | 1 |
| `BTN_BB_J73_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_J73_rain.json` | 505KB | hand-level | - | - | 1 |
| `BTN_BB_K72_fd.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_K72_rain.json` | 505KB | hand-level | - | - | 1 |
| `BTN_BB_K98_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_K98_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_KJT_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_KJT_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_KK8_rain.json` | 505KB | hand-level | - | - | 1 |
| `BTN_BB_Q83_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_Q83_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_T74_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_T74_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_T98_fd.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_T98_rain.json` | 505KB | hand-level | - | - | 1 |

## vol3-mtt-postflop/findings/cash50bb_raw/

**ファイル数**: 1

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `BTN_BB_K72_rain.json` | 356KB | hand-level | - | - | 1 |

## vol3-mtt-postflop/findings/def_cash100_bb_raw/

**ファイル数**: 24

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `742_fd.json` | 391KB | hand-level | - | - | 1 |
| `742_rain.json` | 393KB | hand-level | - | - | 1 |
| `765_fd.json` | 389KB | hand-level | - | - | 1 |
| `765_rain.json` | 391KB | hand-level | - | - | 1 |
| `A72_fd.json` | 385KB | hand-level | - | - | 1 |
| `A72_rain.json` | 384KB | hand-level | - | - | 1 |
| `A94_fd.json` | 382KB | hand-level | - | - | 1 |
| `A94_rain.json` | 381KB | hand-level | - | - | 1 |
| `AA7_rain.json` | 377KB | hand-level | - | - | 1 |
| `J73_fd.json` | 390KB | hand-level | - | - | 1 |
| `J73_rain.json` | 388KB | hand-level | - | - | 1 |
| `K72_fd.json` | 387KB | hand-level | - | - | 1 |
| `K72_rain.json` | 386KB | hand-level | - | - | 1 |
| `K98_fd.json` | 384KB | hand-level | - | - | 1 |
| `K98_rain.json` | 383KB | hand-level | - | - | 1 |
| `KJT_fd.json` | 382KB | hand-level | - | - | 1 |
| `KJT_rain.json` | 381KB | hand-level | - | - | 1 |
| `KK8_rain.json` | 382KB | hand-level | - | - | 1 |
| `Q83_fd.json` | 388KB | hand-level | - | - | 1 |
| `Q83_rain.json` | 387KB | hand-level | - | - | 1 |
| `T74_fd.json` | 390KB | hand-level | - | - | 1 |
| `T74_rain.json` | 388KB | hand-level | - | - | 1 |
| `T98_fd.json` | 385KB | hand-level | - | - | 1 |
| `T98_rain.json` | 384KB | hand-level | - | - | 1 |

## vol3-mtt-postflop/findings/def_cash100_bb_river_raw/

**ファイル数**: 36

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `K72-7-4_R16.json` | 388KB | hand-level | - | - | 1 |
| `K72-7-Q_R16.json` | 384KB | hand-level | - | - | 1 |
| `K72-K-5_R16.json` | 380KB | hand-level | - | - | 1 |
| `K72-K-9_R16.json` | 379KB | hand-level | - | - | 1 |
| `KJT-9-2_R89.6.json` | 340KB | hand-level | - | - | 1 |
| `KJT-9-5_R89.6.json` | 338KB | hand-level | - | - | 1 |
| `KJT-9-A_R4.3.json` | 373KB | hand-level | - | - | 1 |
| `KJT-9-J_R16.json` | 374KB | hand-level | - | - | 1 |
| `KJT-A-3_R13.7.json` | 377KB | hand-level | - | - | 1 |
| `KJT-A-7_R13.7.json` | 375KB | hand-level | - | - | 1 |
| `KJT-A-9_R13.7.json` | 373KB | hand-level | - | - | 1 |
| `KJT-A-J_R13.7.json` | 373KB | hand-level | - | - | 1 |
| `KJT-A-Q_R13.7.json` | 352KB | hand-level | - | - | 1 |
| `Q83-8-5_R16.json` | 386KB | hand-level | - | - | 1 |
| `Q83-8-K_R16.json` | 384KB | hand-level | - | - | 1 |
| `Q83-Q-4_R16.json` | 383KB | hand-level | - | - | 1 |
| `Q83-Q-J_R16.json` | 381KB | hand-level | - | - | 1 |
| `T97m-2-4_R89.6.json` | 346KB | hand-level | - | - | 1 |
| `T97m-2-5_R89.6.json` | 344KB | hand-level | - | - | 1 |
| `T97m-2-A_R16.json` | 378KB | hand-level | - | - | 1 |
| `T98-2-4_R16.json` | 386KB | hand-level | - | - | 1 |
| `T98-2-5_R16.json` | 384KB | hand-level | - | - | 1 |
| `T98-2-7_R16.json` | 380KB | hand-level | - | - | 1 |
| `T98-2-A_R89.6.json` | 338KB | hand-level | - | - | 1 |
| `T98-2-J_R16.json` | 376KB | hand-level | - | - | 1 |
| `T98-2-K_R89.6.json` | 340KB | hand-level | - | - | 1 |
| `T98-3-J_R16.json` | 376KB | hand-level | - | - | 1 |
| `T98-3-K_R89.6.json` | 339KB | hand-level | - | - | 1 |
| `T98-4-5_R16.json` | 384KB | hand-level | - | - | 1 |
| `T98-4-A_R89.6.json` | 338KB | hand-level | - | - | 1 |
| `T98-4-K_R89.6.json` | 339KB | hand-level | - | - | 1 |
| `T98-J-2_R16.json` | 384KB | hand-level | - | - | 1 |
| `T98-J-3_R16.json` | 384KB | hand-level | - | - | 1 |
| `T98-J-A_R16.json` | 376KB | hand-level | - | - | 1 |
| `T98-T-3_R16.json` | 383KB | hand-level | - | - | 1 |
| `T98-T-K_R16.json` | 376KB | hand-level | - | - | 1 |

## vol3-mtt-postflop/findings/def_cash100_bb_turn_raw/

**ファイル数**: 18

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `K52-5p_R16.8.json` | 390KB | hand-level | - | - | 1 |
| `K72-3_R16.8.json` | 388KB | hand-level | - | - | 1 |
| `K72-7_R6.1.json` | 390KB | hand-level | - | - | 1 |
| `K72-A_R16.8.json` | 385KB | hand-level | - | - | 1 |
| `K72-K_R6.1.json` | 386KB | hand-level | - | - | 1 |
| `K72-Q_R16.8.json` | 384KB | hand-level | - | - | 1 |
| `KJT-2_R16.8.json` | 387KB | hand-level | - | - | 1 |
| `KJT-9_R6.1.json` | 381KB | hand-level | - | - | 1 |
| `KJT-A_R2.3.json` | 377KB | hand-level | - | - | 1 |
| `Q83-2_R16.8.json` | 393KB | hand-level | - | - | 1 |
| `Q83-8_R6.1.json` | 389KB | hand-level | - | - | 1 |
| `Q83-J_R16.8.json` | 383KB | hand-level | - | - | 1 |
| `Q83-Q_R6.1.json` | 386KB | hand-level | - | - | 1 |
| `T97-mono_R6.1.json` | 389KB | hand-level | - | - | 1 |
| `T98-2_R6.1.json` | 386KB | hand-level | - | - | 1 |
| `T98-3_R6.1.json` | 386KB | hand-level | - | - | 1 |
| `T98-J_R6.1.json` | 385KB | hand-level | - | - | 1 |
| `T98-T_R6.1.json` | 384KB | hand-level | - | - | 1 |

## vol3-mtt-postflop/findings/def_mtt100_bb_raw/

**ファイル数**: 24

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `742_fd.json` | 498KB | hand-level | - | - | 1 |
| `742_rain.json` | 502KB | hand-level | - | - | 1 |
| `765_fd.json` | 498KB | hand-level | - | - | 1 |
| `765_rain.json` | 494KB | hand-level | - | - | 1 |
| `A72_fd.json` | 497KB | hand-level | - | - | 1 |
| `A72_rain.json` | 497KB | hand-level | - | - | 1 |
| `A94_fd.json` | 496KB | hand-level | - | - | 1 |
| `A94_rain.json` | 495KB | hand-level | - | - | 1 |
| `AA7_rain.json` | 490KB | hand-level | - | - | 1 |
| `J73_fd.json` | 500KB | hand-level | - | - | 1 |
| `J73_rain.json` | 499KB | hand-level | - | - | 1 |
| `K72_fd.json` | 497KB | hand-level | - | - | 1 |
| `K72_rain.json` | 497KB | hand-level | - | - | 1 |
| `K98_fd.json` | 496KB | hand-level | - | - | 1 |
| `K98_rain.json` | 495KB | hand-level | - | - | 1 |
| `KJT_fd.json` | 486KB | hand-level | - | - | 1 |
| `KJT_rain.json` | 482KB | hand-level | - | - | 1 |
| `KK8_rain.json` | 491KB | hand-level | - | - | 1 |
| `Q83_fd.json` | 499KB | hand-level | - | - | 1 |
| `Q83_rain.json` | 496KB | hand-level | - | - | 1 |
| `T74_fd.json` | 500KB | hand-level | - | - | 1 |
| `T74_rain.json` | 500KB | hand-level | - | - | 1 |
| `T98_fd.json` | 499KB | hand-level | - | - | 1 |
| `T98_rain.json` | 502KB | hand-level | - | - | 1 |

## vol3-mtt-postflop/findings/def_mtt25_bb_raw/

**ファイル数**: 24

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `742_fd.json` | 600KB | hand-level | - | - | 1 |
| `742_rain.json` | 598KB | hand-level | - | - | 1 |
| `765_fd.json` | 601KB | hand-level | - | - | 1 |
| `765_rain.json` | 601KB | hand-level | - | - | 1 |
| `A72_fd.json` | 598KB | hand-level | - | - | 1 |
| `A72_rain.json` | 596KB | hand-level | - | - | 1 |
| `A94_fd.json` | 597KB | hand-level | - | - | 1 |
| `A94_rain.json` | 596KB | hand-level | - | - | 1 |
| `AA7_rain.json` | 596KB | hand-level | - | - | 1 |
| `J73_fd.json` | 601KB | hand-level | - | - | 1 |
| `J73_rain.json` | 600KB | hand-level | - | - | 1 |
| `K72_fd.json` | 597KB | hand-level | - | - | 1 |
| `K72_rain.json` | 596KB | hand-level | - | - | 1 |
| `K98_fd.json` | 598KB | hand-level | - | - | 1 |
| `K98_rain.json` | 598KB | hand-level | - | - | 1 |
| `KJT_fd.json` | 595KB | hand-level | - | - | 1 |
| `KJT_rain.json` | 596KB | hand-level | - | - | 1 |
| `KK8_rain.json` | 590KB | hand-level | - | - | 1 |
| `Q83_fd.json` | 599KB | hand-level | - | - | 1 |
| `Q83_rain.json` | 597KB | hand-level | - | - | 1 |
| `T74_fd.json` | 602KB | hand-level | - | - | 1 |
| `T74_rain.json` | 600KB | hand-level | - | - | 1 |
| `T98_fd.json` | 601KB | hand-level | - | - | 1 |
| `T98_rain.json` | 602KB | hand-level | - | - | 1 |

## vol3-mtt-postflop/findings/def_mtt50_bb_raw/

**ファイル数**: 24

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `742_fd.json` | 596KB | hand-level | - | - | 1 |
| `742_rain.json` | 591KB | hand-level | - | - | 1 |
| `765_fd.json` | 595KB | hand-level | - | - | 1 |
| `765_rain.json` | 593KB | hand-level | - | - | 1 |
| `A72_fd.json` | 592KB | hand-level | - | - | 1 |
| `A72_rain.json` | 589KB | hand-level | - | - | 1 |
| `A94_fd.json` | 590KB | hand-level | - | - | 1 |
| `A94_rain.json` | 588KB | hand-level | - | - | 1 |
| `AA7_rain.json` | 588KB | hand-level | - | - | 1 |
| `J73_fd.json` | 590KB | hand-level | - | - | 1 |
| `J73_rain.json` | 599KB | hand-level | - | - | 1 |
| `K72_fd.json` | 589KB | hand-level | - | - | 1 |
| `K72_rain.json` | 588KB | hand-level | - | - | 1 |
| `K98_fd.json` | 590KB | hand-level | - | - | 1 |
| `K98_rain.json` | 589KB | hand-level | - | - | 1 |
| `KJT_fd.json` | 595KB | hand-level | - | - | 1 |
| `KJT_rain.json` | 595KB | hand-level | - | - | 1 |
| `KK8_rain.json` | 589KB | hand-level | - | - | 1 |
| `Q83_fd.json` | 590KB | hand-level | - | - | 1 |
| `Q83_rain.json` | 589KB | hand-level | - | - | 1 |
| `T74_fd.json` | 598KB | hand-level | - | - | 1 |
| `T74_rain.json` | 597KB | hand-level | - | - | 1 |
| `T98_fd.json` | 599KB | hand-level | - | - | 1 |
| `T98_rain.json` | 599KB | hand-level | - | - | 1 |

## vol3-mtt-postflop/findings/def_mtt50_bb_river_raw/

**ファイル数**: 13

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `K72-7-4_R13.7.json` | 516KB | hand-level | - | - | 1 |
| `K72-7-Q_R13.7.json` | 517KB | hand-level | - | - | 1 |
| `K72-K-5_R35.5.json` | 438KB | hand-level | - | - | 1 |
| `K72-K-9_R35.5.json` | 429KB | hand-level | - | - | 1 |
| `Q83-8-5_R35.5.json` | 440KB | hand-level | - | - | 1 |
| `Q83-8-K_R35.5.json` | 436KB | hand-level | - | - | 1 |
| `Q83-Q-4_R35.5.json` | 438KB | hand-level | - | - | 1 |
| `Q83-Q-J_R35.5.json` | 432KB | hand-level | - | - | 1 |
| `T98-2-4_R35.5.json` | 439KB | hand-level | - | - | 1 |
| `T98-2-J_R35.5.json` | 434KB | hand-level | - | - | 1 |
| `T98-J-2_R13.7.json` | 512KB | hand-level | - | - | 1 |
| `T98-T-3_R13.7.json` | 508KB | hand-level | - | - | 1 |
| `T98-T-5_R13.7.json` | 515KB | hand-level | - | - | 1 |

## vol3-mtt-postflop/findings/def_mtt50_bb_turn_raw/

**ファイル数**: 22

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `K52-5p_R10.6.json` | 519KB | hand-level | - | - | 1 |
| `K72-3_R10.6.json` | 521KB | hand-level | - | - | 1 |
| `K72-5_R10.6.json` | 519KB | hand-level | - | - | 1 |
| `K72-7_R2.3.json` | 517KB | hand-level | - | - | 1 |
| `K72-9_R10.6.json` | 507KB | hand-level | - | - | 1 |
| `K72-A_R10.6.json` | 516KB | hand-level | - | - | 1 |
| `K72-J_R10.6.json` | 503KB | hand-level | - | - | 1 |
| `K72-K_R10.6.json` | 518KB | hand-level | - | - | 1 |
| `K72-Q_R10.6.json` | 518KB | hand-level | - | - | 1 |
| `Q83-2_R10.6.json` | 522KB | hand-level | - | - | 1 |
| `Q83-5_R10.6.json` | 519KB | hand-level | - | - | 1 |
| `Q83-8_R10.6.json` | 519KB | hand-level | - | - | 1 |
| `Q83-A_R10.6.json` | 519KB | hand-level | - | - | 1 |
| `Q83-J_R10.6.json` | 518KB | hand-level | - | - | 1 |
| `Q83-Q_R10.6.json` | 520KB | hand-level | - | - | 1 |
| `Q83-T_R10.6.json` | 519KB | hand-level | - | - | 1 |
| `T97-mono_R10.6.json` | 520KB | hand-level | - | - | 1 |
| `T98-2_R10.6.json` | 520KB | hand-level | - | - | 1 |
| `T98-3_R10.6.json` | 518KB | hand-level | - | - | 1 |
| `T98-4_R10.6.json` | 515KB | hand-level | - | - | 1 |
| `T98-J_R2.3.json` | 513KB | hand-level | - | - | 1 |
| `T98-T_R2.3.json` | 514KB | hand-level | - | - | 1 |

## vol3-mtt-postflop/findings/mtt100bb_raw/

**ファイル数**: 120

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `BTN_BB_742_fd.json` | 423KB | hand-level | - | - | 1 |
| `BTN_BB_742_rain.json` | 422KB | hand-level | - | - | 1 |
| `BTN_BB_765_fd.json` | 420KB | hand-level | - | - | 1 |
| `BTN_BB_765_rain.json` | 419KB | hand-level | - | - | 1 |
| `BTN_BB_A72_fd.json` | 419KB | hand-level | - | - | 1 |
| `BTN_BB_A72_rain.json` | 419KB | hand-level | - | - | 1 |
| `BTN_BB_A94_fd.json` | 419KB | hand-level | - | - | 1 |
| `BTN_BB_A94_rain.json` | 419KB | hand-level | - | - | 1 |
| `BTN_BB_AA7_rain.json` | 417KB | hand-level | - | - | 1 |
| `BTN_BB_J73_fd.json` | 432KB | hand-level | - | - | 1 |
| `BTN_BB_J73_rain.json` | 419KB | hand-level | - | - | 1 |
| `BTN_BB_K72_fd.json` | 419KB | hand-level | - | - | 1 |
| `BTN_BB_K72_rain.json` | 419KB | hand-level | - | - | 1 |
| `BTN_BB_K98_fd.json` | 416KB | hand-level | - | - | 1 |
| `BTN_BB_K98_rain.json` | 415KB | hand-level | - | - | 1 |
| `BTN_BB_KJT_fd.json` | 417KB | hand-level | - | - | 1 |
| `BTN_BB_KJT_rain.json` | 417KB | hand-level | - | - | 1 |
| `BTN_BB_KK8_rain.json` | 414KB | hand-level | - | - | 1 |
| `BTN_BB_Q83_fd.json` | 421KB | hand-level | - | - | 1 |
| `BTN_BB_Q83_rain.json` | 420KB | hand-level | - | - | 1 |
| `BTN_BB_T74_fd.json` | 420KB | hand-level | - | - | 1 |
| `BTN_BB_T74_rain.json` | 419KB | hand-level | - | - | 1 |
| `BTN_BB_T98_fd.json` | 418KB | hand-level | - | - | 1 |
| `BTN_BB_T98_rain.json` | 417KB | hand-level | - | - | 1 |
| `CO_BB_742_fd.json` | 399KB | hand-level | - | - | 1 |
| `CO_BB_742_rain.json` | 398KB | hand-level | - | - | 1 |
| `CO_BB_765_fd.json` | 396KB | hand-level | - | - | 1 |
| `CO_BB_765_rain.json` | 395KB | hand-level | - | - | 1 |
| `CO_BB_A72_fd.json` | 397KB | hand-level | - | - | 1 |
| `CO_BB_A72_rain.json` | 403KB | hand-level | - | - | 1 |
| `CO_BB_A94_fd.json` | 394KB | hand-level | - | - | 1 |
| `CO_BB_A94_rain.json` | 393KB | hand-level | - | - | 1 |
| `CO_BB_AA7_rain.json` | 394KB | hand-level | - | - | 1 |
| `CO_BB_J73_fd.json` | 407KB | hand-level | - | - | 1 |
| `CO_BB_J73_rain.json` | 403KB | hand-level | - | - | 1 |
| `CO_BB_K72_fd.json` | 404KB | hand-level | - | - | 1 |
| `CO_BB_K72_rain.json` | 396KB | hand-level | - | - | 1 |
| `CO_BB_K98_fd.json` | 392KB | hand-level | - | - | 1 |
| `CO_BB_K98_rain.json` | 391KB | hand-level | - | - | 1 |
| `CO_BB_KJT_fd.json` | 394KB | hand-level | - | - | 1 |
| `CO_BB_KJT_rain.json` | 393KB | hand-level | - | - | 1 |
| `CO_BB_KK8_rain.json` | 391KB | hand-level | - | - | 1 |
| `CO_BB_Q83_fd.json` | 397KB | hand-level | - | - | 1 |
| `CO_BB_Q83_rain.json` | 397KB | hand-level | - | - | 1 |
| `CO_BB_T74_fd.json` | 404KB | hand-level | - | - | 1 |
| `CO_BB_T74_rain.json` | 403KB | hand-level | - | - | 1 |
| `CO_BB_T98_fd.json` | 394KB | hand-level | - | - | 1 |
| `CO_BB_T98_rain.json` | 393KB | hand-level | - | - | 1 |
| `HJ_BB_742_fd.json` | 379KB | hand-level | - | - | 1 |
| `HJ_BB_742_rain.json` | 379KB | hand-level | - | - | 1 |
| `HJ_BB_765_fd.json` | 378KB | hand-level | - | - | 1 |
| `HJ_BB_765_rain.json` | 378KB | hand-level | - | - | 1 |
| `HJ_BB_A72_fd.json` | 378KB | hand-level | - | - | 1 |
| `HJ_BB_A72_rain.json` | 377KB | hand-level | - | - | 1 |
| `HJ_BB_A94_fd.json` | 378KB | hand-level | - | - | 1 |
| `HJ_BB_A94_rain.json` | 378KB | hand-level | - | - | 1 |
| `HJ_BB_AA7_rain.json` | 376KB | hand-level | - | - | 1 |
| `HJ_BB_J73_fd.json` | 378KB | hand-level | - | - | 1 |
| `HJ_BB_J73_rain.json` | 377KB | hand-level | - | - | 1 |
| `HJ_BB_K72_fd.json` | 380KB | hand-level | - | - | 1 |
| `HJ_BB_K72_rain.json` | 380KB | hand-level | - | - | 1 |
| `HJ_BB_K98_fd.json` | 376KB | hand-level | - | - | 1 |
| `HJ_BB_K98_rain.json` | 375KB | hand-level | - | - | 1 |
| `HJ_BB_KJT_fd.json` | 375KB | hand-level | - | - | 1 |
| `HJ_BB_KJT_rain.json` | 375KB | hand-level | - | - | 1 |
| `HJ_BB_KK8_rain.json` | 374KB | hand-level | - | - | 1 |
| `HJ_BB_Q83_fd.json` | 380KB | hand-level | - | - | 1 |
| `HJ_BB_Q83_rain.json` | 380KB | hand-level | - | - | 1 |
| `HJ_BB_T74_fd.json` | 378KB | hand-level | - | - | 1 |
| `HJ_BB_T74_rain.json` | 377KB | hand-level | - | - | 1 |
| `HJ_BB_T98_fd.json` | 377KB | hand-level | - | - | 1 |
| `HJ_BB_T98_rain.json` | 376KB | hand-level | - | - | 1 |
| `SB_BB_742_fd.json` | 437KB | hand-level | - | - | 1 |
| `SB_BB_742_rain.json` | 436KB | hand-level | - | - | 1 |
| `SB_BB_765_fd.json` | 433KB | hand-level | - | - | 1 |
| `SB_BB_765_rain.json` | 432KB | hand-level | - | - | 1 |
| `SB_BB_A72_fd.json` | 432KB | hand-level | - | - | 1 |
| `SB_BB_A72_rain.json` | 431KB | hand-level | - | - | 1 |
| `SB_BB_A94_fd.json` | 430KB | hand-level | - | - | 1 |
| `SB_BB_A94_rain.json` | 430KB | hand-level | - | - | 1 |
| `SB_BB_AA7_rain.json` | 427KB | hand-level | - | - | 1 |
| `SB_BB_J73_fd.json` | 438KB | hand-level | - | - | 1 |
| `SB_BB_J73_rain.json` | 433KB | hand-level | - | - | 1 |
| `SB_BB_K72_fd.json` | 432KB | hand-level | - | - | 1 |
| `SB_BB_K72_rain.json` | 432KB | hand-level | - | - | 1 |
| `SB_BB_K98_fd.json` | 430KB | hand-level | - | - | 1 |
| `SB_BB_K98_rain.json` | 429KB | hand-level | - | - | 1 |
| `SB_BB_KJT_fd.json` | 430KB | hand-level | - | - | 1 |
| `SB_BB_KJT_rain.json` | 430KB | hand-level | - | - | 1 |
| `SB_BB_KK8_rain.json` | 428KB | hand-level | - | - | 1 |
| `SB_BB_Q83_fd.json` | 433KB | hand-level | - | - | 1 |
| `SB_BB_Q83_rain.json` | 432KB | hand-level | - | - | 1 |
| `SB_BB_T74_fd.json` | 437KB | hand-level | - | - | 1 |
| `SB_BB_T74_rain.json` | 432KB | hand-level | - | - | 1 |
| `SB_BB_T98_fd.json` | 431KB | hand-level | - | - | 1 |
| `SB_BB_T98_rain.json` | 430KB | hand-level | - | - | 1 |
| `UTG_BB_742_fd.json` | 375KB | hand-level | - | - | 1 |
| `UTG_BB_742_rain.json` | 373KB | hand-level | - | - | 1 |
| `UTG_BB_765_fd.json` | 372KB | hand-level | - | - | 1 |
| `UTG_BB_765_rain.json` | 371KB | hand-level | - | - | 1 |
| `UTG_BB_A72_fd.json` | 371KB | hand-level | - | - | 1 |
| `UTG_BB_A72_rain.json` | 370KB | hand-level | - | - | 1 |
| `UTG_BB_A94_fd.json` | 371KB | hand-level | - | - | 1 |
| `UTG_BB_A94_rain.json` | 370KB | hand-level | - | - | 1 |
| `UTG_BB_AA7_rain.json` | 374KB | hand-level | - | - | 1 |
| `UTG_BB_J73_fd.json` | 373KB | hand-level | - | - | 1 |
| `UTG_BB_J73_rain.json` | 372KB | hand-level | - | - | 1 |
| `UTG_BB_K72_fd.json` | 373KB | hand-level | - | - | 1 |
| `UTG_BB_K72_rain.json` | 374KB | hand-level | - | - | 1 |
| `UTG_BB_K98_fd.json` | 374KB | hand-level | - | - | 1 |
| `UTG_BB_K98_rain.json` | 369KB | hand-level | - | - | 1 |
| `UTG_BB_KJT_fd.json` | 372KB | hand-level | - | - | 1 |
| `UTG_BB_KJT_rain.json` | 372KB | hand-level | - | - | 1 |
| `UTG_BB_KK8_rain.json` | 371KB | hand-level | - | - | 1 |
| `UTG_BB_Q83_fd.json` | 375KB | hand-level | - | - | 1 |
| `UTG_BB_Q83_rain.json` | 375KB | hand-level | - | - | 1 |
| `UTG_BB_T74_fd.json` | 372KB | hand-level | - | - | 1 |
| `UTG_BB_T74_rain.json` | 371KB | hand-level | - | - | 1 |
| `UTG_BB_T98_fd.json` | 371KB | hand-level | - | - | 1 |
| `UTG_BB_T98_rain.json` | 370KB | hand-level | - | - | 1 |

## vol3-mtt-postflop/findings/mtt200bb_raw/

**ファイル数**: 120

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `BTN_BB_742_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_742_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_765_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_765_rain.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_A72_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_A72_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_A94_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_A94_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_AA7_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_J73_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_J73_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_K72_fd.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_K72_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_K98_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_K98_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_KJT_fd.json` | 509KB | hand-level | - | - | 1 |
| `BTN_BB_KJT_rain.json` | 508KB | hand-level | - | - | 1 |
| `BTN_BB_KK8_rain.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_Q83_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_Q83_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_T74_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_T74_rain.json` | 508KB | hand-level | - | - | 1 |
| `BTN_BB_T98_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_T98_rain.json` | 507KB | hand-level | - | - | 1 |
| `CO_BB_742_fd.json` | 507KB | hand-level | - | - | 1 |
| `CO_BB_742_rain.json` | 506KB | hand-level | - | - | 1 |
| `CO_BB_765_fd.json` | 507KB | hand-level | - | - | 1 |
| `CO_BB_765_rain.json` | 507KB | hand-level | - | - | 1 |
| `CO_BB_A72_fd.json` | 507KB | hand-level | - | - | 1 |
| `CO_BB_A72_rain.json` | 506KB | hand-level | - | - | 1 |
| `CO_BB_A94_fd.json` | 507KB | hand-level | - | - | 1 |
| `CO_BB_A94_rain.json` | 506KB | hand-level | - | - | 1 |
| `CO_BB_AA7_rain.json` | 506KB | hand-level | - | - | 1 |
| `CO_BB_J73_fd.json` | 507KB | hand-level | - | - | 1 |
| `CO_BB_J73_rain.json` | 506KB | hand-level | - | - | 1 |
| `CO_BB_K72_fd.json` | 506KB | hand-level | - | - | 1 |
| `CO_BB_K72_rain.json` | 506KB | hand-level | - | - | 1 |
| `CO_BB_K98_fd.json` | 507KB | hand-level | - | - | 1 |
| `CO_BB_K98_rain.json` | 506KB | hand-level | - | - | 1 |
| `CO_BB_KJT_fd.json` | 509KB | hand-level | - | - | 1 |
| `CO_BB_KJT_rain.json` | 508KB | hand-level | - | - | 1 |
| `CO_BB_KK8_rain.json` | 507KB | hand-level | - | - | 1 |
| `CO_BB_Q83_fd.json` | 507KB | hand-level | - | - | 1 |
| `CO_BB_Q83_rain.json` | 506KB | hand-level | - | - | 1 |
| `CO_BB_T74_fd.json` | 507KB | hand-level | - | - | 1 |
| `CO_BB_T74_rain.json` | 508KB | hand-level | - | - | 1 |
| `CO_BB_T98_fd.json` | 507KB | hand-level | - | - | 1 |
| `CO_BB_T98_rain.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_742_fd.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_742_rain.json` | 506KB | hand-level | - | - | 1 |
| `HJ_BB_765_fd.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_765_rain.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_A72_fd.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_A72_rain.json` | 506KB | hand-level | - | - | 1 |
| `HJ_BB_A94_fd.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_A94_rain.json` | 506KB | hand-level | - | - | 1 |
| `HJ_BB_AA7_rain.json` | 506KB | hand-level | - | - | 1 |
| `HJ_BB_J73_fd.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_J73_rain.json` | 506KB | hand-level | - | - | 1 |
| `HJ_BB_K72_fd.json` | 506KB | hand-level | - | - | 1 |
| `HJ_BB_K72_rain.json` | 506KB | hand-level | - | - | 1 |
| `HJ_BB_K98_fd.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_K98_rain.json` | 506KB | hand-level | - | - | 1 |
| `HJ_BB_KJT_fd.json` | 509KB | hand-level | - | - | 1 |
| `HJ_BB_KJT_rain.json` | 508KB | hand-level | - | - | 1 |
| `HJ_BB_KK8_rain.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_Q83_fd.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_Q83_rain.json` | 506KB | hand-level | - | - | 1 |
| `HJ_BB_T74_fd.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_T74_rain.json` | 508KB | hand-level | - | - | 1 |
| `HJ_BB_T98_fd.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_T98_rain.json` | 507KB | hand-level | - | - | 1 |
| `SB_BB_742_fd.json` | 486KB | hand-level | - | - | 1 |
| `SB_BB_742_rain.json` | 485KB | hand-level | - | - | 1 |
| `SB_BB_765_fd.json` | 486KB | hand-level | - | - | 1 |
| `SB_BB_765_rain.json` | 488KB | hand-level | - | - | 1 |
| `SB_BB_A72_fd.json` | 489KB | hand-level | - | - | 1 |
| `SB_BB_A72_rain.json` | 488KB | hand-level | - | - | 1 |
| `SB_BB_A94_fd.json` | 489KB | hand-level | - | - | 1 |
| `SB_BB_A94_rain.json` | 488KB | hand-level | - | - | 1 |
| `SB_BB_AA7_rain.json` | 485KB | hand-level | - | - | 1 |
| `SB_BB_J73_fd.json` | 489KB | hand-level | - | - | 1 |
| `SB_BB_J73_rain.json` | 485KB | hand-level | - | - | 1 |
| `SB_BB_K72_fd.json` | 488KB | hand-level | - | - | 1 |
| `SB_BB_K72_rain.json` | 487KB | hand-level | - | - | 1 |
| `SB_BB_K98_fd.json` | 489KB | hand-level | - | - | 1 |
| `SB_BB_K98_rain.json` | 485KB | hand-level | - | - | 1 |
| `SB_BB_KJT_fd.json` | 489KB | hand-level | - | - | 1 |
| `SB_BB_KJT_rain.json` | 488KB | hand-level | - | - | 1 |
| `SB_BB_KK8_rain.json` | 485KB | hand-level | - | - | 1 |
| `SB_BB_Q83_fd.json` | 489KB | hand-level | - | - | 1 |
| `SB_BB_Q83_rain.json` | 488KB | hand-level | - | - | 1 |
| `SB_BB_T74_fd.json` | 489KB | hand-level | - | - | 1 |
| `SB_BB_T74_rain.json` | 485KB | hand-level | - | - | 1 |
| `SB_BB_T98_fd.json` | 486KB | hand-level | - | - | 1 |
| `SB_BB_T98_rain.json` | 487KB | hand-level | - | - | 1 |
| `UTG_BB_742_fd.json` | 507KB | hand-level | - | - | 1 |
| `UTG_BB_742_rain.json` | 506KB | hand-level | - | - | 1 |
| `UTG_BB_765_fd.json` | 507KB | hand-level | - | - | 1 |
| `UTG_BB_765_rain.json` | 507KB | hand-level | - | - | 1 |
| `UTG_BB_A72_fd.json` | 507KB | hand-level | - | - | 1 |
| `UTG_BB_A72_rain.json` | 506KB | hand-level | - | - | 1 |
| `UTG_BB_A94_fd.json` | 507KB | hand-level | - | - | 1 |
| `UTG_BB_A94_rain.json` | 506KB | hand-level | - | - | 1 |
| `UTG_BB_AA7_rain.json` | 506KB | hand-level | - | - | 1 |
| `UTG_BB_J73_fd.json` | 507KB | hand-level | - | - | 1 |
| `UTG_BB_J73_rain.json` | 506KB | hand-level | - | - | 1 |
| `UTG_BB_K72_fd.json` | 506KB | hand-level | - | - | 1 |
| `UTG_BB_K72_rain.json` | 506KB | hand-level | - | - | 1 |
| `UTG_BB_K98_fd.json` | 507KB | hand-level | - | - | 1 |
| `UTG_BB_K98_rain.json` | 506KB | hand-level | - | - | 1 |
| `UTG_BB_KJT_fd.json` | 509KB | hand-level | - | - | 1 |
| `UTG_BB_KJT_rain.json` | 508KB | hand-level | - | - | 1 |
| `UTG_BB_KK8_rain.json` | 507KB | hand-level | - | - | 1 |
| `UTG_BB_Q83_fd.json` | 507KB | hand-level | - | - | 1 |
| `UTG_BB_Q83_rain.json` | 506KB | hand-level | - | - | 1 |
| `UTG_BB_T74_fd.json` | 507KB | hand-level | - | - | 1 |
| `UTG_BB_T74_rain.json` | 508KB | hand-level | - | - | 1 |
| `UTG_BB_T98_fd.json` | 507KB | hand-level | - | - | 1 |
| `UTG_BB_T98_rain.json` | 507KB | hand-level | - | - | 1 |

## vol3-mtt-postflop/findings/mtt50bb_raw/

**ファイル数**: 120

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `BTN_BB_742_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_742_rain.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_765_fd.json` | 508KB | hand-level | - | - | 1 |
| `BTN_BB_765_rain.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_A72_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_A72_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_A94_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_A94_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_AA7_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_J73_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_J73_rain.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_K72_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_K72_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_K98_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_K98_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_KJT_fd.json` | 508KB | hand-level | - | - | 1 |
| `BTN_BB_KJT_rain.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_KK8_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_Q83_fd.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_Q83_rain.json` | 506KB | hand-level | - | - | 1 |
| `BTN_BB_T74_fd.json` | 508KB | hand-level | - | - | 1 |
| `BTN_BB_T74_rain.json` | 507KB | hand-level | - | - | 1 |
| `BTN_BB_T98_fd.json` | 508KB | hand-level | - | - | 1 |
| `BTN_BB_T98_rain.json` | 507KB | hand-level | - | - | 1 |
| `CO_BB_742_fd.json` | 508KB | hand-level | - | - | 1 |
| `CO_BB_742_rain.json` | 507KB | hand-level | - | - | 1 |
| `CO_BB_765_fd.json` | 508KB | hand-level | - | - | 1 |
| `CO_BB_765_rain.json` | 507KB | hand-level | - | - | 1 |
| `CO_BB_A72_fd.json` | 507KB | hand-level | - | - | 1 |
| `CO_BB_A72_rain.json` | 506KB | hand-level | - | - | 1 |
| `CO_BB_A94_fd.json` | 507KB | hand-level | - | - | 1 |
| `CO_BB_A94_rain.json` | 506KB | hand-level | - | - | 1 |
| `CO_BB_AA7_rain.json` | 506KB | hand-level | - | - | 1 |
| `CO_BB_J73_fd.json` | 508KB | hand-level | - | - | 1 |
| `CO_BB_J73_rain.json` | 507KB | hand-level | - | - | 1 |
| `CO_BB_K72_fd.json` | 507KB | hand-level | - | - | 1 |
| `CO_BB_K72_rain.json` | 506KB | hand-level | - | - | 1 |
| `CO_BB_K98_fd.json` | 507KB | hand-level | - | - | 1 |
| `CO_BB_K98_rain.json` | 506KB | hand-level | - | - | 1 |
| `CO_BB_KJT_fd.json` | 508KB | hand-level | - | - | 1 |
| `CO_BB_KJT_rain.json` | 508KB | hand-level | - | - | 1 |
| `CO_BB_KK8_rain.json` | 506KB | hand-level | - | - | 1 |
| `CO_BB_Q83_fd.json` | 507KB | hand-level | - | - | 1 |
| `CO_BB_Q83_rain.json` | 506KB | hand-level | - | - | 1 |
| `CO_BB_T74_fd.json` | 508KB | hand-level | - | - | 1 |
| `CO_BB_T74_rain.json` | 507KB | hand-level | - | - | 1 |
| `CO_BB_T98_fd.json` | 508KB | hand-level | - | - | 1 |
| `CO_BB_T98_rain.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_742_fd.json` | 508KB | hand-level | - | - | 1 |
| `HJ_BB_742_rain.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_765_fd.json` | 508KB | hand-level | - | - | 1 |
| `HJ_BB_765_rain.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_A72_fd.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_A72_rain.json` | 506KB | hand-level | - | - | 1 |
| `HJ_BB_A94_fd.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_A94_rain.json` | 506KB | hand-level | - | - | 1 |
| `HJ_BB_AA7_rain.json` | 506KB | hand-level | - | - | 1 |
| `HJ_BB_J73_fd.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_J73_rain.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_K72_fd.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_K72_rain.json` | 506KB | hand-level | - | - | 1 |
| `HJ_BB_K98_fd.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_K98_rain.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_KJT_fd.json` | 508KB | hand-level | - | - | 1 |
| `HJ_BB_KJT_rain.json` | 508KB | hand-level | - | - | 1 |
| `HJ_BB_KK8_rain.json` | 506KB | hand-level | - | - | 1 |
| `HJ_BB_Q83_fd.json` | 508KB | hand-level | - | - | 1 |
| `HJ_BB_Q83_rain.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_T74_fd.json` | 508KB | hand-level | - | - | 1 |
| `HJ_BB_T74_rain.json` | 507KB | hand-level | - | - | 1 |
| `HJ_BB_T98_fd.json` | 508KB | hand-level | - | - | 1 |
| `HJ_BB_T98_rain.json` | 507KB | hand-level | - | - | 1 |
| `SB_BB_742_fd.json` | 487KB | hand-level | - | - | 1 |
| `SB_BB_742_rain.json` | 486KB | hand-level | - | - | 1 |
| `SB_BB_765_fd.json` | 487KB | hand-level | - | - | 1 |
| `SB_BB_765_rain.json` | 486KB | hand-level | - | - | 1 |
| `SB_BB_A72_fd.json` | 485KB | hand-level | - | - | 1 |
| `SB_BB_A72_rain.json` | 486KB | hand-level | - | - | 1 |
| `SB_BB_A94_fd.json` | 486KB | hand-level | - | - | 1 |
| `SB_BB_A94_rain.json` | 486KB | hand-level | - | - | 1 |
| `SB_BB_AA7_rain.json` | 486KB | hand-level | - | - | 1 |
| `SB_BB_J73_fd.json` | 486KB | hand-level | - | - | 1 |
| `SB_BB_J73_rain.json` | 486KB | hand-level | - | - | 1 |
| `SB_BB_K72_fd.json` | 487KB | hand-level | - | - | 1 |
| `SB_BB_K72_rain.json` | 484KB | hand-level | - | - | 1 |
| `SB_BB_K98_fd.json` | 486KB | hand-level | - | - | 1 |
| `SB_BB_K98_rain.json` | 487KB | hand-level | - | - | 1 |
| `SB_BB_KJT_fd.json` | 487KB | hand-level | - | - | 1 |
| `SB_BB_KJT_rain.json` | 487KB | hand-level | - | - | 1 |
| `SB_BB_KK8_rain.json` | 487KB | hand-level | - | - | 1 |
| `SB_BB_Q83_fd.json` | 488KB | hand-level | - | - | 1 |
| `SB_BB_Q83_rain.json` | 487KB | hand-level | - | - | 1 |
| `SB_BB_T74_fd.json` | 488KB | hand-level | - | - | 1 |
| `SB_BB_T74_rain.json` | 487KB | hand-level | - | - | 1 |
| `SB_BB_T98_fd.json` | 487KB | hand-level | - | - | 1 |
| `SB_BB_T98_rain.json` | 487KB | hand-level | - | - | 1 |
| `UTG_BB_742_fd.json` | 508KB | hand-level | - | - | 1 |
| `UTG_BB_742_rain.json` | 507KB | hand-level | - | - | 1 |
| `UTG_BB_765_fd.json` | 508KB | hand-level | - | - | 1 |
| `UTG_BB_765_rain.json` | 507KB | hand-level | - | - | 1 |
| `UTG_BB_A72_fd.json` | 507KB | hand-level | - | - | 1 |
| `UTG_BB_A72_rain.json` | 506KB | hand-level | - | - | 1 |
| `UTG_BB_A94_fd.json` | 507KB | hand-level | - | - | 1 |
| `UTG_BB_A94_rain.json` | 506KB | hand-level | - | - | 1 |
| `UTG_BB_AA7_rain.json` | 506KB | hand-level | - | - | 1 |
| `UTG_BB_J73_fd.json` | 507KB | hand-level | - | - | 1 |
| `UTG_BB_J73_rain.json` | 507KB | hand-level | - | - | 1 |
| `UTG_BB_K72_fd.json` | 507KB | hand-level | - | - | 1 |
| `UTG_BB_K72_rain.json` | 506KB | hand-level | - | - | 1 |
| `UTG_BB_K98_fd.json` | 507KB | hand-level | - | - | 1 |
| `UTG_BB_K98_rain.json` | 507KB | hand-level | - | - | 1 |
| `UTG_BB_KJT_fd.json` | 508KB | hand-level | - | - | 1 |
| `UTG_BB_KJT_rain.json` | 508KB | hand-level | - | - | 1 |
| `UTG_BB_KK8_rain.json` | 506KB | hand-level | - | - | 1 |
| `UTG_BB_Q83_fd.json` | 508KB | hand-level | - | - | 1 |
| `UTG_BB_Q83_rain.json` | 507KB | hand-level | - | - | 1 |
| `UTG_BB_T74_fd.json` | 508KB | hand-level | - | - | 1 |
| `UTG_BB_T74_rain.json` | 507KB | hand-level | - | - | 1 |
| `UTG_BB_T98_fd.json` | 508KB | hand-level | - | - | 1 |
| `UTG_BB_T98_rain.json` | 507KB | hand-level | - | - | 1 |

## vol3-mtt-postflop/findings/pairwise/

**ファイル数**: 1

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `mtt_pairwise.jsonl` | 117KB | per-mv-cat | - | - | 1 |

## vol3-mtt-postflop/findings/turn_cash100_btn_raw/

**ファイル数**: 30

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `AA7_2.json` | 343KB | hand-level | - | - | 1 |
| `AA7_5.json` | 342KB | hand-level | - | - | 1 |
| `AA7_7.json` | 339KB | hand-level | - | - | 1 |
| `AA7_A.json` | 332KB | hand-level | - | - | 1 |
| `AA7_K.json` | 339KB | hand-level | - | - | 1 |
| `K72r_2.json` | 351KB | hand-level | - | - | 1 |
| `K72r_7.json` | 347KB | hand-level | - | - | 1 |
| `K72r_8.json` | 350KB | hand-level | - | - | 1 |
| `K72r_A.json` | 345KB | hand-level | - | - | 1 |
| `K72r_K.json` | 347KB | hand-level | - | - | 1 |
| `K98r_2.json` | 348KB | hand-level | - | - | 1 |
| `K98r_7.json` | 348KB | hand-level | - | - | 1 |
| `K98r_A.json` | 342KB | hand-level | - | - | 1 |
| `K98r_K.json` | 344KB | hand-level | - | - | 1 |
| `K98r_T.json` | 346KB | hand-level | - | - | 1 |
| `KJT_2.json` | 347KB | hand-level | - | - | 1 |
| `KJT_9.json` | 343KB | hand-level | - | - | 1 |
| `KJT_A.json` | 340KB | hand-level | - | - | 1 |
| `KJT_K.json` | 343KB | hand-level | - | - | 1 |
| `KJT_Q.json` | 339KB | hand-level | - | - | 1 |
| `Q83_2.json` | 351KB | hand-level | - | - | 1 |
| `Q83_8.json` | 349KB | hand-level | - | - | 1 |
| `Q83_A.json` | 345KB | hand-level | - | - | 1 |
| `Q83_K.json` | 348KB | hand-level | - | - | 1 |
| `Q83_Q.json` | 347KB | hand-level | - | - | 1 |
| `T98r_2.json` | 349KB | hand-level | - | - | 1 |
| `T98r_7.json` | 347KB | hand-level | - | - | 1 |
| `T98r_A.json` | 343KB | hand-level | - | - | 1 |
| `T98r_J.json` | 345KB | hand-level | - | - | 1 |
| `T98r_T.json` | 345KB | hand-level | - | - | 1 |

## vol3-mtt-postflop/findings/turn_mtt100_btn_raw/

**ファイル数**: 23

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `K72r_2.json` | 442KB | hand-level | - | - | 1 |
| `K72r_7.json` | 438KB | hand-level | - | - | 1 |
| `K72r_8.json` | 442KB | hand-level | - | - | 1 |
| `K72r_A.json` | 440KB | hand-level | - | - | 1 |
| `K72r_K.json` | 437KB | hand-level | - | - | 1 |
| `K98r_2.json` | 439KB | hand-level | - | - | 1 |
| `K98r_7.json` | 440KB | hand-level | - | - | 1 |
| `K98r_A.json` | 440KB | hand-level | - | - | 1 |
| `K98r_K.json` | 434KB | hand-level | - | - | 1 |
| `K98r_T.json` | 432KB | hand-level | - | - | 1 |
| `KJT_9.json` | 436KB | hand-level | - | - | 1 |
| `KJT_K.json` | 436KB | hand-level | - | - | 1 |
| `KJT_Q.json` | 442KB | hand-level | - | - | 1 |
| `Q83_2.json` | 446KB | hand-level | - | - | 1 |
| `Q83_8.json` | 439KB | hand-level | - | - | 1 |
| `Q83_A.json` | 441KB | hand-level | - | - | 1 |
| `Q83_K.json` | 441KB | hand-level | - | - | 1 |
| `Q83_Q.json` | 438KB | hand-level | - | - | 1 |
| `T98r_2.json` | 445KB | hand-level | - | - | 1 |
| `T98r_7.json` | 437KB | hand-level | - | - | 1 |
| `T98r_A.json` | 441KB | hand-level | - | - | 1 |
| `T98r_J.json` | 443KB | hand-level | - | - | 1 |
| `T98r_T.json` | 434KB | hand-level | - | - | 1 |

## vol3-mtt-postflop/findings/turn_mtt25_btn_raw/

**ファイル数**: 30

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `AA7_2.json` | 525KB | hand-level | - | - | 1 |
| `AA7_5.json` | 527KB | hand-level | - | - | 1 |
| `AA7_7.json` | 525KB | hand-level | - | - | 1 |
| `AA7_A.json` | 520KB | hand-level | - | - | 1 |
| `AA7_K.json` | 525KB | hand-level | - | - | 1 |
| `K72r_2.json` | 524KB | hand-level | - | - | 1 |
| `K72r_7.json` | 523KB | hand-level | - | - | 1 |
| `K72r_8.json` | 525KB | hand-level | - | - | 1 |
| `K72r_A.json` | 524KB | hand-level | - | - | 1 |
| `K72r_K.json` | 524KB | hand-level | - | - | 1 |
| `K98r_2.json` | 525KB | hand-level | - | - | 1 |
| `K98r_7.json` | 525KB | hand-level | - | - | 1 |
| `K98r_A.json` | 523KB | hand-level | - | - | 1 |
| `K98r_K.json` | 526KB | hand-level | - | - | 1 |
| `K98r_T.json` | 525KB | hand-level | - | - | 1 |
| `KJT_2.json` | 524KB | hand-level | - | - | 1 |
| `KJT_9.json` | 527KB | hand-level | - | - | 1 |
| `KJT_A.json` | 524KB | hand-level | - | - | 1 |
| `KJT_K.json` | 527KB | hand-level | - | - | 1 |
| `KJT_Q.json` | 523KB | hand-level | - | - | 1 |
| `Q83_2.json` | 525KB | hand-level | - | - | 1 |
| `Q83_8.json` | 522KB | hand-level | - | - | 1 |
| `Q83_A.json` | 524KB | hand-level | - | - | 1 |
| `Q83_K.json` | 524KB | hand-level | - | - | 1 |
| `Q83_Q.json` | 526KB | hand-level | - | - | 1 |
| `T98r_2.json` | 529KB | hand-level | - | - | 1 |
| `T98r_7.json` | 526KB | hand-level | - | - | 1 |
| `T98r_A.json` | 529KB | hand-level | - | - | 1 |
| `T98r_J.json` | 530KB | hand-level | - | - | 1 |
| `T98r_T.json` | 529KB | hand-level | - | - | 1 |

## vol3-mtt-postflop/findings/turn_mtt50_btn_raw/

**ファイル数**: 30

| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |
|---------|-------|------------|-------|---------|---------|
| `AA7_2.json` | 519KB | hand-level | - | - | 1 |
| `AA7_5.json` | 520KB | hand-level | - | - | 1 |
| `AA7_7.json` | 524KB | hand-level | - | - | 1 |
| `AA7_A.json` | 517KB | hand-level | - | - | 1 |
| `AA7_K.json` | 520KB | hand-level | - | - | 1 |
| `K72r_2.json` | 519KB | hand-level | - | - | 1 |
| `K72r_7.json` | 521KB | hand-level | - | - | 1 |
| `K72r_8.json` | 526KB | hand-level | - | - | 1 |
| `K72r_A.json` | 521KB | hand-level | - | - | 1 |
| `K72r_K.json` | 522KB | hand-level | - | - | 1 |
| `K98r_2.json` | 525KB | hand-level | - | - | 1 |
| `K98r_7.json` | 520KB | hand-level | - | - | 1 |
| `K98r_A.json` | 525KB | hand-level | - | - | 1 |
| `K98r_K.json` | 520KB | hand-level | - | - | 1 |
| `K98r_T.json` | 526KB | hand-level | - | - | 1 |
| `KJT_2.json` | 529KB | hand-level | - | - | 1 |
| `KJT_9.json` | 526KB | hand-level | - | - | 1 |
| `KJT_A.json` | 524KB | hand-level | - | - | 1 |
| `KJT_K.json` | 530KB | hand-level | - | - | 1 |
| `KJT_Q.json` | 526KB | hand-level | - | - | 1 |
| `Q83_2.json` | 525KB | hand-level | - | - | 1 |
| `Q83_8.json` | 524KB | hand-level | - | - | 1 |
| `Q83_A.json` | 524KB | hand-level | - | - | 1 |
| `Q83_K.json` | 522KB | hand-level | - | - | 1 |
| `Q83_Q.json` | 524KB | hand-level | - | - | 1 |
| `T98r_2.json` | 528KB | hand-level | - | - | 1 |
| `T98r_7.json` | 529KB | hand-level | - | - | 1 |
| `T98r_A.json` | 528KB | hand-level | - | - | 1 |
| `T98r_J.json` | 527KB | hand-level | - | - | 1 |
| `T98r_T.json` | 526KB | hand-level | - | - | 1 |

