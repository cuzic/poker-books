# 『迷わないポーカー』MATCHA シリーズ執筆プロジェクト

## プロジェクト概要

テキサスホールデムを「暗算できる判断フロー」で決める書籍シリーズ。
シリーズ通底のフレームワーク名: **MATCHA** (Math Algorithm of Twelve-Cell Hold'em Action)。
全 3 巻が同じ acronym を共有し、巻ごとに **Formula / Framework / Exploits** の役割 suffix で識別する。

## シリーズ構成（3 巻体制、2026-06-07 改定）

| 巻 | サブブランド | テーマ | ディレクトリ | 主要式 | 状態 |
|----|-----|--------|------------|--------|------|
| Vol1 | **MATCHA Formula** | プリフロップ完全版（Cash+MTT統合、ICM/PKO preflop range含む） | `vol1-preflop/` | Score_BB v7 (ポジションティア + コンテキストキャリブレーション) | 初稿生成中 |
| Vol2 | **MATCHA Framework** | ポストフロップ完全版（Cash 100bb + MTT chipEV 25-200bb 統合） | `vol2-postflop/` | 5 つの判定軸 + TEA グリッド + 3 モード + 3 補正 | 設計完了・執筆待ち |
| Vol3 | **MATCHA Exploits** | エクスプロイト・テル（相手タイプ別） | `vol3-tell/` | 5 つの逸脱軸で MATCHA 判定軸を歪める | 初稿完了 (旧 Vol4)、MATCHA 用語で再執筆予定 |

**MATCHA acronym 解釈** (シリーズ共通):
- **M**ath **A**lgorithm — 数学アルゴリズム (暗算 philosophy)
- **T**welve-**C**ell — 12 マス (4 カテゴリ × 3 board の判定グリッド、シリーズ全体を貫く核心)
- **H**old'em **A**ction — ホールデムのアクション (Vol1: プレ vs フォールド / Vol2: ベット/レイズ/コール/フォールド / Vol3: タイプ別最適アクション)

**3 巻構成の決定経緯 (2026-06-07)**:
- MATCHA Framework (旧 UDG v2) で Cash 100bb と MTT chipEV (100bb) のポストフロップ判断が **完全同一公式** で扱えると確認 (293K rows audit、acc 同等差 ≤2pp)
- 旧 Vol2 (Cash) + 旧 Vol3 (MTT) の内容が 8 割重複 → 統合書 1 冊で十分
- ICM/PKO postflop は GTO Wizard API tier 制限 (403) で取得不可 → 将来別冊 (Vol2.5/Vol3.5 想定) で対応
- 旧 Vol4 (エクスプロイト) を Vol3 にリネーム、MATCHA 用語で再執筆

旧シリーズ・廃棄版は `_archive/` に移動済み:
- `_archive/cash-preflop/`, `_archive/mtt-preflop/` は vol1-preflop に統合済
- `_archive/vol2-cash-postflop_v3/`, `_archive/vol3-mtt-postflop_v3/` は **2026-06-02 廃棄** (S/M/W/A/D マトリックス・UCBS-v2/v3 系の旧ロジック)
- `_archive/knowledges/volume{3..6}/`: 旧シリーズ名の knowledge
- `_archive/specs_v2/`: 旧 UCBS-v2 spec YAML
- `_archive/scripts/ucbs_book_generator.py`: 旧 generator

**Vol2 (MATCHA Framework) の中核** (2026-06-07 確立、書籍化準備完了):

**MATCHA** = **M**ath **A**lgorithm for **T**welve-**C**ell **H**old'em **A**ction

- **Layer 1: 5 つの判定軸** (`scripts/three_class_model/udg_v2.py` が SSOT、コード変数は英語維持)
  - レンジ分布 (`board_polar_tier`): 2極化型 / 混在型 / 密集型
  - ハンドストレングス (`hand_strength_tier`): ナッツメイド / ストロング / ツーペア / トップペア以上 / ミドルペア / エア
  - ベットサイジング (`bet_size_tier`): スモールベット / ミディアムベット / オーバーベット / オールイン
  - SPR (`spr_tier`): オールインSPR / ローSPR / ミディアムSPR / ディープSPR
  - エクイティバケット (`equity_aware_tier`): モンスターハンド / 良ハンド / 弱ハンド / ブラフハンド
- **Layer 2: TEA グリッド** (カテゴリ × Edge = Action) — 5 軸 → 形勢 (優勢 / 五分五分 / 劣勢) を導出する中央装置
- **Layer 3: 3 つのモード** (形勢ごとの行動原則)
  - 優勢 → バリューモード
  - 五分五分 → ショーダウンモード
  - 劣勢 → ブラフキャッチモード
- **Layer 4: 3 つの補正**
  - チェックレイズ補正 (vs CR)
  - ドンクベット補正 (vs Donk Bet)
  - オープナー補正 (CO/HJ open river のみ)
- 検証: `scripts/three_class_model/UDG_V2_RESULTS.md` (huge_loss 11 専用公式比 -62%)
- 設計過程: `scripts/three_class_model/UDG_V3_LEARNINGS.md` (v3 試行で equity_bucket の重要性発見)
- データ: `scripts/three_class_model/dataset_unified_v2.csv` (293K rows、phase 1-6 統合)
- **用語集 (HTML)**: https://gistpreview.github.io/?dbb75f11330aff4346de987c4f4fb91b

旧 Vol2/Vol3 の現行ロジック (2026-06-01 確立、MATCHA で吸収済) は `BOOK_DESIGN_2026-06-01.md` に記録。

**Vol3 (エクスプロイト) と MATCHA の接続**:
- エクスプロイト = **5 つの逸脱軸** (Five Imbalances: レンジ逸脱 / 頻度逸脱 / サイズ逸脱 / ポジション逸脱 / 判断逸脱) を読み、MATCHA の判定軸を歪めて形勢を変える技術
- プレイタイプ 5 分類: ニット / TAG / LAG / コーリングステーション / マニアック

## 共通の設計思想

1. **暗算で回せる計算式**：Chen Formula、Sklansky Hand Groups の系譜に連なる簡易式を現代 GTO データで再設計
2. **境界暗記のハイブリッド**：式で 9 割、境界ハンドは GTO 最善手を暗記
3. **章末【GTO とのズレ】コラム**：簡易式と理論最適のギャップを率直に示す
4. **6-max、100BB、キャッシュゲーム**を基本想定

## Directory Structure

```
poker-books/
├── vol1-preflop/         Vol1: プリフロップ完全版（Cash+MTT統合、4係数スコア式）
├── vol2-postflop/        Vol2: ポストフロップ完全版 (MATCHA Framework、Cash+MTT chipEV統合)
├── vol3-tell/            Vol3: エクスプロイト・テル（MATCHA 判定軸の歪め方、旧 Vol4）
├── _archive/             旧シリーズ・廃棄版
│   ├── vol2-cash-postflop_v3/  廃棄 (S/M/W/A/D マトリックス系)
│   ├── vol3-mtt-postflop_v3/   廃棄 (旧 SPR-axis-switching 系)
│   ├── cash-preflop/, mtt-preflop/  vol1-preflop に統合済
│   ├── knowledges/             旧 volume{3..6} 知識
│   ├── specs_v2/               旧 UCBS-v2 spec YAML
│   └── scripts/                旧 generator
├── scripts/
│   ├── build.ts            ビルドスクリプト（bun で実行、Vol1/Vol2/Vol3 対応）
│   ├── three_class_model/  ポストフロップ MATCHA Framework 実装 (`udg_v2.py` が SSOT、ファイル名は legacy)
│   └── generate/
│       ├── preflop_book_generator.py  Vol1 章原稿自動生成
│       └── specs/         Vol2 spec (vol2_ch{NN}_*.yaml、MATCHA ベース) は今後作成
├── BOOK_DESIGN_2026-06-01.md  旧 Vol2/Vol3 設計書 (UDG v2 で吸収済、参照用)
└── dist/           ビルド成果物
```

## ビルド

```bash
bun run scripts/build.ts vol1-preflop          # Vol1 のみ
bun run scripts/build.ts vol2-postflop         # Vol2 のみ (執筆開始後)
bun run scripts/build.ts vol3-tell             # Vol3 (旧 Vol4 リネーム)
bun run scripts/build.ts all                   # 全巻
```

Vol2 は spec/generator 設計待ち、MATCHA Framework 公式 (`scripts/three_class_model/udg_v2.py` — ファイル名は legacy、内容は MATCHA SSOT) を generator から呼び出す予定。

## 執筆ワークフロー（全巻共通）

1. **目次起草**：`<book>/toc.md` に詳細目次＋3式の定義
2. **リサーチ並列化**：章ごとに Researcher エージェントを投入し、`knowledges/<book>/*.md` に保存
3. **執筆**：`<book>/chapters/XX-*.md` に本文を書く
4. **レビュー**：Reviewer で Devil's Advocate レビュー、`knowledges/<book>/reviews/` に保存
5. **ファクトチェック**：計算・エクイティ値・出典 URL を全数検証
6. **境界ハンド集**：付録 F にまとめて暗記推奨リスト化
7. **HTML ビルド**：`bash scripts/build.sh <book>`
8. **gistpreview 公開**：`gh gist create --public dist/<book>/book.html`

## 文体・品質基準

- ですます調で統一
- 1文 150 字以内、読点 3 個以内
- 専門用語は初出時に簡易定義を併記
- 数値は具体的に（「多い」ではなく「約 70%」）
- 出典 URL を `knowledges/<book>/` に明記

## シリーズの思想的系譜

- **Chen Formula**（Bill Chen、2000 年代）：ハンド数値化の原型
- **Sklansky-Malmuth Hand Groups**（1988 年）：チャンキング思考の先駆け
- **Matthew Janda『Applications of No-Limit Hold'em』**（2013 年）：レンジ思考の現代版
- **Michael Acevedo『Modern Poker Theory』**（2019 年）：ソルバー時代の体系書
- **本シリーズ**：上記の系譜を「初心者が暗算で回せる形」にアップデート

## コード品質・ファイル命名規則

### 章ファイル

```
<book>/chapters/NN-slug-name.md
例: preflop/chapters/05-base-score-formula.md
    flop/chapters/07-cbet-integration-formula.md
```

- `NN` は 2 桁のゼロ埋め章番号（00〜21 or 00〜23）
- `slug-name` はケバブケースの英語短縮

### リサーチファイル

```
knowledges/<book>/NN_topic_name.md
例: knowledges/preflop/05_base_score_formula.md
```

- `NN` は対応する章番号と一致させる

### レビューファイル

```
knowledges/<book>/reviews/review_<scope>.md
例: knowledges/preflop/reviews/review_part1_ch1-7.md
```

## ライセンスと公開

各巻の gist URL は書籍固有（`book.json` 内の `identifier` とは別）。現行シリーズの gist：

- Vol1 プリフロップ完全版 (**MATCHA Formula**): （旧 cash-preflop: https://gistpreview.github.io/?a263151bbdee0ac9cbaa4a4e97483edb）
- Vol2 ポストフロップ完全版 (**MATCHA Framework**): **執筆待ち** (旧 Vol2/Vol3 廃棄、MATCHA で統合再執筆)
- Vol3 エクスプロイト (**MATCHA Exploits**、旧 Vol4): https://gistpreview.github.io/?519b2350329278e7be6f09e5be449cd9 (MATCHA 用語で再執筆予定)
- **MATCHA シリーズ用語集**: https://gistpreview.github.io/?dbb75f11330aff4346de987c4f4fb91b

旧シリーズ gist（参照用）：
- 旧②フロップ[基礎]: https://gistpreview.github.io/?5883292a2b687db842b4117f384c3aad
- 旧③フロップ[応用]: https://gistpreview.github.io/?e90c50f9dcdf09a311445db723c56fd6
- 旧④ターン・リバー[基礎]: https://gistpreview.github.io/?6c4006bb24b6350517a0ae8e5a52061a
- 旧⑤ターン・リバー[応用]: https://gistpreview.github.io/?f1c3973e0576af76f29ecf9a91fddb5b
- 旧⑥トーナメント編: https://gistpreview.github.io/?0923d0ef729f7a18aa11682402b3ef7b
- ダイジェスト版: https://gistpreview.github.io/?2abb4d163ac9e989333eb6db2a11f364

加えて GitHub Pages 経由で全巻を公開済み: <https://cuzic.github.io/poker-books/>
（`.github/workflows/deploy.yml` で main push 時に自動デプロイ）
