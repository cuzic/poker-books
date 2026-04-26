# 巻4 検証: poker-gto プロジェクトへの引き継ぎ

## 概要

巻4 の数値検証は **別プロジェクトの poker-gto** (Rust 製 GTO ソルバー) で実施します。作業の引き継ぎ資料は poker-gto 側に格納。

## 引き継ぎ資料の場所

**メイン資料**: `/home/cuzic/poker-gto/docs/volume4_verification_handoff.md`

内容:

- 巻4 の 8 検証論点
- 現状の SolverEngine API の限界 (レンジ対レンジ未対応)
- 必要な API 拡張 (`RangeVsRangeState`, プリセットレンジ, ベットサイズ別頻度)
- シナリオ JSON / 結果 JSON 形式
- 精度検証基準 (GTO Wizard 公開値との誤差 < 5%)
- 400 シナリオの実行規模と並列度想定
- Phase 1-4 のマイルストーン

## poker-books 側での対応

### 待機中

- タスク #102-#108 (ソルバー検証) は poker-gto 側の API 拡張待ち
- タスク #82 (検証スクリプト拡張) も依存
- タスク #84, #85, #99, #100 (巻4 執筆本体) は検証完了待ち

### 検証完了後の作業 (poker-books 側)

1. `knowledges/volume4/results/*.json` に結果 JSON を配置 (poker-gto 実行結果のコピー)
2. `scripts/analyze_volume4.py` を新規作成、JSON → 集計 → Markdown 素材生成
3. 生成された素材を元に 巻4 第I-III部 を執筆

## 成果物

### poker-gto 側 (すでに着手)

- `/home/cuzic/poker-gto/crates/poker-solver/examples/volume4_verify_smoke.rs` — 最小動作確認 (動作済み)

### poker-books 側 (準備済み)

- `knowledges/volume4/00_detailed_toc.md` — 巻4 詳細目次 19 章
- `knowledges/volume4/01-08_*.md` — 巻4 素材 8 ファイル (約 1,500 行)
- `knowledges/volume4/10_solver_setup.md` — 検証環境の選定結果
- `scripts/bdm.py` — 巻2/3 の Python モデル (対照用)

## 進捗追跡

poker-gto 側の作業が完了次第、下記のタスクを解除し執筆に入れる:

- #82 巻3-8 検証スクリプト拡張 (ターン・リバー対応)
- #102 ターン CBet 頻度 270 ケース
- #103 リバー V:B 比 30 シナリオ
- #104 マルチストリート EV 15 シナリオ
- #105 ブロッカー論 20 ケース
- #106 MDF 実測 20 シナリオ
- #107 ターンカード分類 妥当性
- #108 フック 6 個 個別検証
- #109 検証結果の統合
- #84, #85, #99, #100 巻4 執筆
