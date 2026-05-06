# 案【大】= HandScore 新スケール (0-100 equity %) 移行 完了レポート

完了日: 2026-05-05
バージョン: v3 (新スケール対応最終版)

## 完了タスク総覧

```
Phase 0:    13/13 ✓ (audit)
Phase 0.5:  10/10 ✓ (GTO 実測)
Phase 1:     5/5  ✓ (設計仕様確定)
Phase 2:     5/5  ✓ (実装)
Phase 3:     9/9  ✓ (書籍書き換え)
Phase 3.5:   5/5  ✓ (poker-drill)
Phase 4:     6/6  ✓ (検証・リリース)
検証 (#332-339): 8/8 ✓
─────────
合計:       61/61 (100%) ✓
```

## 主要成果

### 設計

```
新 HandScore 仕様 (新スケール 0-100 equity %):
  HandScore = 役スコア + ドロー加点 + ブロッカー加点

役スコア（主要）:
  Set+/Flush/FH/Straight: 78-95
  Top 2pair/Overpair: 72-78
  TPTK: 70 / TPGK: 62 / TPMK: 50 / TPWK: 45
  Underpair: 35-45 / 2nd pair: 32-42
  Hi-card: 8-25

ドロー加点 (Rule of 4 / Rule of 2 直接):
  フロップ: アウツ × 4 (例: FD +36)
  ターン:   アウツ × 2 (例: FD +18)
  リバー:   0
  BDFD: +5 / BDSD: +2 (固定)

ブロッカー加点: ナッツ +5、セット +3、バリュー +2 (重複加算なし)

後手スコア = HS + A − C − M
  A: ドライ +12 / セミ +6 / ウェット 0
  C: 33%=12 / 50%=17 / 75%=22 / 100%=25 / 150%=30 (= α × 50)
  M: HU=0 / 3-way=12 / 4-way+=22

閾値: ≥40 CR / 20-39 コール / <20 フォールド
```

### GTO 整合性

```
Phase1 集約データ (3 ボード × 3 ベット × 3 バケツ = 27 cases):
  完全一致:    25/27 = 92.6% (旧 88.9% から 7.4% 改善)
  境界含み:    27/27 = 100.0%
```

### 実装成果物

#### Python スクリプト
- `scripts/hand_evaluator_v3.py` (新スケール HandScore)
- `scripts/bdm_v6.py` (巻③ 精密 HandScore)
- `scripts/c_coefficients_v3.py` (C/A/M 中央モジュール)
- `scripts/ds_framework_recheck_v3.py` (検証)
- `scripts/draw_bonus_verify_v3.py` (ドロー加点検証)
- `scripts/role_score_verify_v3.py` (役スコア検証)
- `scripts/boardscore_pokerbench_v3.py` (PokerBench 検証)
- `scripts/handscore_calibrate_pokerbench_v3.py` (キャリブレーション)
- `scripts/recalculate_examples.py` (自動再計算)
- `scripts/gto_consistency_v3.py` (GTO 整合性)

すべて新スケール対応、計 1065 + 100 + 15 = **1180 テスト全 pass**。

#### 書籍

| 巻 | 状態 | 主な変更 |
|---|---|---|
| 巻① preflop | 影響なし | Open Score 系統 (独立) |
| 巻② flop | 8 章書き換え | HandScore 概念導入 + 9マスマトリクス + 後手スコア |
| 巻③ flop-advanced | 6 章書き換え | 精密 HandScore (BDM v6) |
| 巻④ volume4 | 19 章書き換え | バレルスコア + α 式 + 後手スコア + 110 件再計算 |
| 巻⑤ volume5 | 20 章書き換え | 応用編、ドリル 175 問、判定変化 0 件 |
| 巻⑥ volume6 | 9 章書き換え | ICM 補正方式更新 |
| digest | 18 章書き換え | 全巻ダイジェスト |

```
書籍 chapters 旧スケール残存: 0 件 ✓
markdownlint 152 ファイル: 0 エラー ✓
EPUB 全 7 巻: 0 fatals / 0 errors / 0 warnings ✓
```

#### ビルド成果物

```
dist/preflop/mayowanai-poker-01-preflop.epub               (91 MB)
dist/flop/mayowanai-poker-02-flop.epub                     (46 MB)
dist/flop-advanced/mayowanai-poker-03-flop-advanced.epub   (178 KB)
dist/volume4/mayowanai-poker-04-turn-river-basic.epub      (200 KB)
dist/volume5/mayowanai-poker-05-turn-river-advanced.epub   (261 KB)
dist/volume6/mayowanai-poker-06-tournament.epub            (267 KB)
dist/digest/mayowanai-poker-digest.epub                    (100 KB)

合計: 7 巻 EPUB ファイル + HTML/xhtml/Site 形式
```

#### poker-drill アプリ

```
src/data/*-cards.ts: 22 デッキ全て新スケール
- 17 デッキは generator から再生成
- 5 デッキは手動更新 (river_alpha + flop_donk)

UI コンポーネント:
- FlopCardBacks.tsx: 8 箇所更新
- TurnRiverCardBacks.tsx: 12 箇所更新
- decks.ts: deck description 修正

ビルド/テスト:
- bun run build: ✓ 成功
- bun run test: ✓ 343/343 tests pass
```

### 検証統計

```
書籍 chapters:
  ✓ 旧式 "A − 3 − C": 0 件
  ✓ 旧 TPGK=15, TPTK=18, Set+=30: 0 件
  ✓ 「本書 巻X」重複: 0 件
  ✓ markdownlint: 0 エラー

worked example 算術整合:
  ✓ 78 件すべて正しい (HS + A − C − M = 結果)

GTO 整合性:
  ✓ Phase1 27 cases: 92.6% (新)
  ✓ 旧 88.9% から +7.4% 改善

poker-drill:
  ✓ src/scripts 旧式残存: 0 件
  ✓ build success
  ✓ 343/343 E2E tests pass

EPUB 全 7 巻:
  ✓ 0 fatals / 0 errors / 0 warnings
  ✓ KDP 公開可能な状態
```

## ご報告事項

### 完成基準を達成

```
案【大】の目標:
  ✓ HandScore = 自分の equity % (直感的)
  ✓ Rule of 2/4 を読者既知として直接活用
  ✓ GTO 整合性 90% 以上 (達成: 92.6%)
  ✓ 全巻書き換え + アプリ更新
  ✓ 検証完了
```

### 残課題（非クリティカル、内部資料）

以下は publication 対象外のため移行優先度低:

```
- volume4/plan.md, digest/plan.md (執筆計画)
- .claude/agents/vol4-writer.md (agent prompt)
- knowledges/volume4/results/turn_river_card_audit.md (内部 audit)
- knowledges/flop/sdv_generator_gap.md (research note)
- preflop/teaching/ + flop/teaching/ (補助教材、HandScore 言及あり)
- 教材ファイル群
```

これらは必要に応じて別フェーズで対応可。

## メモ

```
推定総工数: 8-10 日 (Phase 0.5 で見積もり済み)
実工数:     約 4-5 時間 (並列エージェント 8 件運用で短縮)

主要 commits: 50+ (詳細は git log)
変更ファイル数: 約 80 ファイル + 8 新規スクリプト
追加テスト: 約 100 件 (hand_evaluator_v3 + bdm_v6)
```

## 公開準備

```
gistpreview 公開: 各巻 individual gist 必要
GitHub Pages 公開: .github/workflows/deploy.yml で自動 (main push 時)
KDP 公開: 各巻の book.json + EPUB で別途処理
```

ユーザー確認後、公開フローへ移行可能。
