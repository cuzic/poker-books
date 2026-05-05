# scripts/ 索引

『迷わないポーカー』シリーズ用のリサーチ・検証・生成スクリプト群。

最終更新: 2026-05-05

---

## ビルド・公開系（TypeScript）

| Script | 役割 |
|--------|------|
| `build.ts` | 全巻 HTML/EPUB ビルド (`bun run scripts/build.ts --book <name>`) |
| `check-epub.ts` | EPUB 検査 |
| `generate-image-batch.ts` | 画像プロンプトバッチ生成 |
| `submit-image-batch.ts` | Gemini 画像生成バッチ送信 |
| `generate-kdp-metadata.ts` | KDP 公開用メタデータ生成 |
| `generate-range-tables.ts` | レンジ表 HTML 生成 |
| `download-images.py` | 完成画像をダウンロード |
| `check-batch-status.py` | 画像バッチ進捗確認 |
| `batch-improve.sh` | 一括テキスト改善 (lint:fix → 章ごと改善) |

---

## 検証系（verify / audit / accuracy）

### バレルスコア (Volume 4 第8章)

| Script | 検証対象 | 関連 knowledges |
|--------|---------|----------------|
| `barrel_score_verify.py` | FlopType×TurnCard 16セルの GTO 一致率 | `volume4/results/barrel_score_verify/` |

### HandScore / 役スコア / ドロー加点 (巻② 第9章 + 巻④)

| Script | 検証対象 |
|--------|---------|
| `handscore_bucket_verify.py` | H1/H2/H3 バケツ判定 |
| `handscore_boundary_v2.py` | バケツ境界の校正 |
| `handscore_fd_pair_verify.py` | FD + ペアハンドの加点検証 |
| `handscore_cbet_sweep.py` | CBet 頻度 sweep |
| `handscore_continuous_sweep.py` | 連続スコア sweep |
| `handscore_v2_evaluation.py` | v2 仕様の総合評価 |
| `handscore_calibrate_pokerbench.py` | PokerBench データで校正 |
| `role_score_verify.py` | tpgk/tpmk 等の役スコア検証 |
| `draw_bonus_verify.py` | OESD/FD/BDFD のドロー加点検証 |

### 後手スコア / C係数 (巻② 第13章 + 巻④)

| Script | 検証対象 |
|--------|---------|
| `ds_framework_recheck.py` | 後手スコア式の整合性 |
| `texassolver_c_coef_verify.py` | C 係数 (33%=3, 50%=4, 75%=6) 検証 |
| `texassolver_c_coef_srp_verify.py` | SRP での C 係数微調整 |
| `c33_boundary_check.py` | 33% ベット境界 |
| `c150_accuracy_eval.py` | 150% オーバーベット精度 |

### プリフロップ (巻① Score)

| Script | 検証対象 |
|--------|---------|
| `verify_preflop_score.py` | RFI Score の閾値検証 |
| `verify_3bet_score.py` | 3betスコア検証 |
| `refine_preflop_score.py` | Score 係数の微調整 |
| `verify_gto.py` | プリフロップ全体 GTO 整合 |

### フロップ全般

| Script | 検証対象 |
|--------|---------|
| `verify_flop_gto.py` | フロップ CBet GTO 整合 |
| `texassolver_accuracy_30.py` | 30 ボード精度 |
| `texassolver_extended_100.py` | 100 ボード拡張精度 |
| `texassolver_test_k72r.py` | K72r 単体テスト |
| `pokerbench_vs_texassolver.py` | PokerBench と TexasSolver の差分 |

### 3BP / マルチストリート

| Script | 検証対象 |
|--------|---------|
| `texassolver_3bp_verify.py` | 3BP 全体 |
| `texassolver_volume4_102.py` | 270 ターン CBet シナリオ (#102) |
| `texassolver_volume4_river.py` | リバー解析 |
| `texassolver_volume4_multistreet.py` | マルチストリート完全ツリー |

---

## 生成系（generate / TexasSolver runs）

### Volume 4 タスク別シナリオ生成

| Script | タスク |
|--------|------|
| `generate_volume4_102.py` | #102: 270 ターン CBet |
| `generate_volume4_103.py` | #103: リバーバリュー/ブラフ |
| `generate_volume4_104.py` | #104: ターン OB |
| `generate_volume4_105.py` | #105: ブロッカー |
| `generate_volume4_106.py` | #106: MDF 検証 |
| `generate_volume4_107.py` | #107: ベットサイズ |
| `generate_volume4_108.py` | #108: フック検証 |

### フロップ精度バリエーション

| Script | バリアント |
|--------|----------|
| `generate_flop_accuracy_30.py` | 標準 |
| `generate_flop_accuracy_30_no_overbet.py` | オーバーベット除外 |
| `generate_flop_accuracy_30_single33.py` | 単一 33% サイズ |
| `generate_flop_accuracy_30_tuning.py` | チューニング用 |

### その他生成

| Script | 役割 |
|--------|------|
| `texassolver_add_3boards.py` | 追加3ボード解析 |
| `collect_overbet_exclusion.py` | オーバーベット除外データ収集 |

---

## 校正・チューニング

| Script | 役割 |
|--------|------|
| `calibrated_solve.py` | 校正済みソルバー（README あり: README_calibrated_solver.md） |
| `train_correction_table.py` | 補正表学習 |
| `phase1_aggressor.py` | フェーズ1: 攻撃側校正 |
| `phase1_defender.py` | フェーズ1: 防御側校正 |
| `phase1_cr_response.py` | フェーズ1: CR 応答 |

---

## ユーティリティ・ライブラリ

| Script | 役割 |
|--------|------|
| `icm_calc.py` | ICM equity 計算（Malmuth-Harville、巻⑥用） |
| `hand_evaluator.py` / `hand_evaluator_v2.py` | ハンド評価器 |
| `board_classifier.py` | ボード分類器 |
| `boardscore_pokerbench.py` | PokerBench ボードスコア互換 |
| `bdm.py` | bet/dim マッチング（旧式） |
| `gto_query_volume4.py` | GTO データ抽出ヘルパー |
| `extract_gto_charts.py` | GTO チャート抽出 |
| `format_gto_markdown.py` | GTO データを Markdown に整形 |

---

## 命名規則の方針（2026-05-05 更新）

新規スクリプトは以下の prefix を使用:

- `verify_*.py` / `audit_*.py`: 既存実装の正しさを検証する
- `generate_*.py`: TexasSolver シナリオやデータを生成する
- `texassolver_*.py`: TexasSolver を直接呼び出す（生成 + 検証兼用）
- `calibrate_*.py` / `phase1_*.py`: 係数チューニング
- 接尾辞 `_v2.py` `_pokerbench.py` `_continuous.py` などは派生バリアント

既存スクリプトの大半は単発のリサーチ用途で書かれたため、すべて改名するのは
コストが大きい。新規追加時のみ上記命名に従う。

---

## 関連リポジトリ

- `poker-drill/scripts/`: ドリルカード生成 (CSV → TS)
  - `audit_card_consistency.py`: 全 deck answer↔formula 整合チェック (2026-05-05 追加)
  - `generate/<deck>.py`: 各 deck の生成スクリプト (CSV-driven)
  - `generate/core/`: 共通ライブラリ (calc, recorder, builder)

- `TexasSolver/`: ソルバー本体（外部リポジトリ）
  - バイナリ: `/home/cuzic/TexasSolver/build/console_solver`
