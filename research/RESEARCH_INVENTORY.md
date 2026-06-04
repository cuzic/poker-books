# GTO 研究データ Inventory (集約版 / 2026-06-04)

**目的**: Claude / 作業者が既存データを再取得しないための、ディレクトリ単位の網羅サマリ。

詳細な個別ファイル一覧は `RESEARCH_INVENTORY_DETAIL.md` 参照。

**合計 JSON ファイル数**: 896

## ディレクトリ別カバー範囲

### `research/v3-additional/findings/`

- **概要**: Preflop hand-level 追加調査 (2026-06-04)
- **シナリオ**: BB defense 5 シナリオ + squeeze N=1/2 13 シナリオ
- **書籍参照**: Vol1 ch04 §4.1 + ch05 §5.2-§5.3
- **ファイル数**: 20 / **合計サイズ**: 783 KB
- **データレベル**: preflop-hand-level (169)=20
- **例ファイル**: order_probe2_bb_vs_utg.json, probe_bb_vs_btn.json, task_a_BB_vs_BTN.json, task_a_BB_vs_CO.json, task_a_BB_vs_HJ.json...

### `vol2-cash-postflop/findings/`

- **概要**: Vol2 Cash 100bb 6m postflop の集約データ
- **シナリオ**: 5 ポジ (UTG/HJ/CO/BTN/SB) × 7 board type × cbet/defense
- **書籍参照**: Vol2 ch03-05 (Tier 1 マトリックス) の根拠データ
- **ファイル数**: 6 / **合計サイズ**: 335 KB
- **データレベル**: per-5cat (jp)=2, aggregate=2, per-5cat (V/BC/WD/Air)=2
- **例ファイル**: cash_5cat_gto.json, cash_board_wide_gto.json, cash_defense_gto.json, cash_flop_detail_gto.json, cash_pairwise_gto.json...

### `vol3-mtt-postflop/findings/`

- **概要**: Vol3 MTT postflop 雑多 / md + 一部 json
- **シナリオ**: GTO 分析の中間ファイル + design notes
- **書籍参照**: Vol3 全章の根拠
- **ファイル数**: 138 / **合計サイズ**: 12309 KB
- **データレベル**: per-mv-cat (16 役)=53, preflop-hand-level (169)=46, aggregate=37, postflop-hand-level (action_solutions)=2
- **例ファイル**: diagnose_Ks7d2c_25.json, mtt_check_raise_SBR20.json, mtt_check_raise_SBR25.json, mtt_flop_cbet_SBR20_BTN_BB.json, mtt_flop_cbet_SBR25_BTN_BB.json...

### `vol3-mtt-postflop/findings/3bp100_raw/`

- **概要**: Cash 100bb 3-bet pot postflop raw
- **シナリオ**: BTN_BB / CO_BB × 8 board の hand-level
- **書籍参照**: Vol3 ch07 3BP の Cash 100bb 比較
- **ファイル数**: 24 / **合計サイズ**: 12150 KB
- **データレベル**: postflop-hand-level (action_solutions)=24
- **例ファイル**: BTN_BB_742_fd.json, BTN_BB_742_rain.json, BTN_BB_765_fd.json, BTN_BB_765_rain.json, BTN_BB_A72_fd.json...

### `vol3-mtt-postflop/findings/3bp25_raw/`

- **概要**: MTT 25bb 3-bet pot postflop raw
- **シナリオ**: BTN_BB / CO_BB × 8 board (742/765/A72/K72/...) の hand-level
- **書籍参照**: Vol3 ch07 3BP の SBR=25
- **ファイル数**: 24 / **合計サイズ**: 12169 KB
- **データレベル**: postflop-hand-level (action_solutions)=24
- **例ファイル**: BTN_BB_742_fd.json, BTN_BB_742_rain.json, BTN_BB_765_fd.json, BTN_BB_765_rain.json, BTN_BB_A72_fd.json...

### `vol3-mtt-postflop/findings/3bp50_raw/`

- **概要**: MTT 50bb 3-bet pot postflop raw
- **シナリオ**: BTN_BB / CO_BB × 8 board の hand-level
- **書籍参照**: Vol3 ch07 3BP の SBR=50
- **ファイル数**: 24 / **合計サイズ**: 12144 KB
- **データレベル**: postflop-hand-level (action_solutions)=24
- **例ファイル**: BTN_BB_742_fd.json, BTN_BB_742_rain.json, BTN_BB_765_fd.json, BTN_BB_765_rain.json, BTN_BB_A72_fd.json...

### `vol3-mtt-postflop/findings/cash50bb_raw/`

- **概要**: Cash 50bb postflop (limited, BTN_BB K72_rain のみ)
- **シナリオ**: 1 ボードのみ、補助参考
- **書籍参照**: Cash 50bb の参考データ
- **ファイル数**: 1 / **合計サイズ**: 356 KB
- **データレベル**: postflop-hand-level (action_solutions)=1
- **例ファイル**: BTN_BB_K72_rain.json

### `vol3-mtt-postflop/findings/def_cash100_bb_raw/`

- **概要**: Cash 100bb BB defense flop raw
- **シナリオ**: BTN_BB × 8 board (742_rain/fd, 765_rain/fd, A72_rain/fd, K72, T98)
- **書籍参照**: Vol3 ch05 BB defense Cash 100bb
- **ファイル数**: 24 / **合計サイズ**: 9258 KB
- **データレベル**: postflop-hand-level (action_solutions)=24
- **例ファイル**: 742_fd.json, 742_rain.json, 765_fd.json, 765_rain.json, A72_fd.json...

### `vol3-mtt-postflop/findings/def_cash100_bb_river_raw/`

- **概要**: Cash 100bb BB defense River raw
- **シナリオ**: K72 / KJT 等ボード × 複数 turn/river cards
- **書籍参照**: Vol3 ch03 River defense Cash 100bb
- **ファイル数**: 36 / **合計サイズ**: 13291 KB
- **データレベル**: postflop-hand-level (action_solutions)=36
- **例ファイル**: K72-7-4_R16.json, K72-7-Q_R16.json, K72-K-5_R16.json, K72-K-9_R16.json, KJT-9-2_R89.6.json...

### `vol3-mtt-postflop/findings/def_cash100_bb_turn_raw/`

- **概要**: Cash 100bb BB defense Turn raw
- **シナリオ**: K72 ボードベース × 複数 turn cards (3/7/A/K)
- **書籍参照**: Vol3 ch02 Turn defense Cash 100bb
- **ファイル数**: 18 / **合計サイズ**: 6949 KB
- **データレベル**: postflop-hand-level (action_solutions)=18
- **例ファイル**: K52-5p_R16.8.json, K72-3_R16.8.json, K72-7_R6.1.json, K72-A_R16.8.json, K72-K_R6.1.json...

### `vol3-mtt-postflop/findings/def_mtt100_bb_raw/`

- **概要**: MTT 100bb BB defense flop raw
- **シナリオ**: BTN_BB × 8 board の hand-level
- **書籍参照**: Vol3 ch05 depth 別比較
- **ファイル数**: 24 / **合計サイズ**: 11906 KB
- **データレベル**: postflop-hand-level (action_solutions)=24
- **例ファイル**: 742_fd.json, 742_rain.json, 765_fd.json, 765_rain.json, A72_fd.json...

### `vol3-mtt-postflop/findings/def_mtt25_bb_raw/`

- **概要**: MTT 25bb BB defense flop raw
- **シナリオ**: BTN_BB × 8 board の hand-level
- **書籍参照**: Vol3 ch05 depth 別 fold 率
- **ファイル数**: 24 / **合計サイズ**: 14355 KB
- **データレベル**: postflop-hand-level (action_solutions)=24
- **例ファイル**: 742_fd.json, 742_rain.json, 765_fd.json, 765_rain.json, A72_fd.json...

### `vol3-mtt-postflop/findings/def_mtt50_bb_raw/`

- **概要**: MTT 50bb BB defense flop raw
- **シナリオ**: BTN_BB × 8 board の hand-level
- **書籍参照**: Vol3 ch05 + ch02 Turn defense の前準備
- **ファイル数**: 24 / **合計サイズ**: 14218 KB
- **データレベル**: postflop-hand-level (action_solutions)=24
- **例ファイル**: 742_fd.json, 742_rain.json, 765_fd.json, 765_rain.json, A72_fd.json...

### `vol3-mtt-postflop/findings/def_mtt50_bb_river_raw/`

- **概要**: MTT 50bb BB defense River raw
- **シナリオ**: ボード × turn/river cards の hand-level
- **書籍参照**: Vol3 ch03 MTT 50bb River v15
- **ファイル数**: 13 / **合計サイズ**: 6054 KB
- **データレベル**: postflop-hand-level (action_solutions)=13
- **例ファイル**: K72-7-4_R13.7.json, K72-7-Q_R13.7.json, K72-K-5_R35.5.json, K72-K-9_R35.5.json, Q83-8-5_R35.5.json...

### `vol3-mtt-postflop/findings/def_mtt50_bb_turn_raw/`

- **概要**: MTT 50bb BB defense Turn raw
- **シナリオ**: ボード × turn cards の hand-level
- **書籍参照**: Vol3 ch02 MTT 50bb Turn v9
- **ファイル数**: 22 / **合計サイズ**: 11374 KB
- **データレベル**: postflop-hand-level (action_solutions)=22
- **例ファイル**: K52-5p_R10.6.json, K72-3_R10.6.json, K72-5_R10.6.json, K72-7_R2.3.json, K72-9_R10.6.json...

### `vol3-mtt-postflop/findings/mtt100bb_raw/`

- **概要**: (未注記)
- **シナリオ**: ?
- **書籍参照**: ?
- **ファイル数**: 120 / **合計サイズ**: 47943 KB
- **データレベル**: postflop-hand-level (action_solutions)=120
- **例ファイル**: BTN_BB_742_fd.json, BTN_BB_742_rain.json, BTN_BB_765_fd.json, BTN_BB_765_rain.json, BTN_BB_A72_fd.json...

### `vol3-mtt-postflop/findings/mtt200bb_raw/`

- **概要**: (未注記)
- **シナリオ**: ?
- **書籍参照**: ?
- **ファイル数**: 120 / **合計サイズ**: 60345 KB
- **データレベル**: postflop-hand-level (action_solutions)=120
- **例ファイル**: BTN_BB_742_fd.json, BTN_BB_742_rain.json, BTN_BB_765_fd.json, BTN_BB_765_rain.json, BTN_BB_A72_fd.json...

### `vol3-mtt-postflop/findings/mtt50bb_raw/`

- **概要**: (未注記)
- **シナリオ**: ?
- **書籍参照**: ?
- **ファイル数**: 120 / **合計サイズ**: 60349 KB
- **データレベル**: postflop-hand-level (action_solutions)=120
- **例ファイル**: BTN_BB_742_fd.json, BTN_BB_742_rain.json, BTN_BB_765_fd.json, BTN_BB_765_rain.json, BTN_BB_A72_fd.json...

### `vol3-mtt-postflop/findings/pairwise/`

- **概要**: (未注記)
- **シナリオ**: ?
- **書籍参照**: ?
- **ファイル数**: 1 / **合計サイズ**: 117 KB
- **データレベル**: per-mv-cat (16 役)=1
- **例ファイル**: mtt_pairwise.jsonl

### `vol3-mtt-postflop/findings/turn_cash100_btn_raw/`

- **概要**: (未注記)
- **シナリオ**: ?
- **書籍参照**: ?
- **ファイル数**: 30 / **合計サイズ**: 10344 KB
- **データレベル**: postflop-hand-level (action_solutions)=30
- **例ファイル**: AA7_2.json, AA7_5.json, AA7_7.json, AA7_A.json, AA7_K.json...

### `vol3-mtt-postflop/findings/turn_mtt100_btn_raw/`

- **概要**: (未注記)
- **シナリオ**: ?
- **書籍参照**: ?
- **ファイル数**: 23 / **合計サイズ**: 10103 KB
- **データレベル**: postflop-hand-level (action_solutions)=23
- **例ファイル**: K72r_2.json, K72r_7.json, K72r_8.json, K72r_A.json, K72r_K.json...

### `vol3-mtt-postflop/findings/turn_mtt25_btn_raw/`

- **概要**: (未注記)
- **シナリオ**: ?
- **書籍参照**: ?
- **ファイル数**: 30 / **合計サイズ**: 15755 KB
- **データレベル**: postflop-hand-level (action_solutions)=30
- **例ファイル**: AA7_2.json, AA7_5.json, AA7_7.json, AA7_A.json, AA7_K.json...

### `vol3-mtt-postflop/findings/turn_mtt50_btn_raw/`

- **概要**: (未注記)
- **シナリオ**: ?
- **書籍参照**: ?
- **ファイル数**: 30 / **合計サイズ**: 15717 KB
- **データレベル**: postflop-hand-level (action_solutions)=30
- **例ファイル**: AA7_2.json, AA7_5.json, AA7_7.json, AA7_A.json, AA7_K.json...

