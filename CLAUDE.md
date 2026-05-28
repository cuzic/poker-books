# 『迷わないポーカー』シリーズ執筆プロジェクト

## プロジェクト概要

テキサスホールデムを「暗算できる判断フロー」で決める書籍シリーズ。

## シリーズ構成（4 巻体制）

| 巻 | テーマ | ディレクトリ | 主要式 | 状態 |
|----|--------|------------|--------|------|
| Vol1 | プリフロップ完全版（Cash+MTT統合） | `vol1-preflop/` | Score_BB v7 | 初稿生成中 |
| Vol2 | キャッシュ ポストフロップ + 簡易版 | `vol2-cash-postflop/` | Light UCBS v2 + Light DCBS | 新規執筆 |
| Vol3 | MTT ポストフロップ + 精緻版 | `vol3-mtt-postflop/` | Full UCBS-v2 + Full DCBS | 新規執筆 |
| Vol4 | エクスプロイト（相手タイプ別） | `vol4-tell/` | プレイヤータイプ別補正 | 初稿完了 |

旧シリーズ・分割版は `_archive/` に移動済み（`cash-preflop/`, `mtt-preflop/` は vol1-preflop に統合済）。

## 共通の設計思想

1. **暗算で回せる計算式**：Chen Formula、Sklansky Hand Groups の系譜に連なる簡易式を現代 GTO データで再設計
2. **境界暗記のハイブリッド**：式で 9 割、境界ハンドは GTO 最善手を暗記
3. **章末【GTO とのズレ】コラム**：簡易式と理論最適のギャップを率直に示す
4. **6-max、100BB、キャッシュゲーム**を基本想定

## Directory Structure

```
poker-books/
├── vol1-preflop/         Vol1: プリフロップ完全版（Cash+MTT統合、4係数スコア式）
├── vol2-cash-postflop/   Vol2: キャッシュ ポストフロップ（Light UCBS v2 + Light DCBS）
├── vol3-mtt-postflop/    Vol3: MTT ポストフロップ（Full UCBS-v2 + Full DCBS、13 context）
├── vol4-tell/            Vol4: エクスプロイト（プレイヤータイプ別）
├── _archive/             旧シリーズ（cash-preflop/, mtt-preflop/, flop/, volume4-6/, digest/ 等）
├── scripts/
│   ├── build.ts            ビルドスクリプト（bun で実行）
│   └── generate/
│       └── preflop_book_generator.py  章原稿自動生成（GTO データから）
└── dist/           ビルド成果物
```

## ビルド

```bash
bun run scripts/build.ts vol1-preflop          # Vol1 のみ
bun run scripts/build.ts vol2-cash-postflop    # Vol2 のみ
bun run scripts/build.ts vol3-mtt-postflop     # Vol3 のみ
bun run scripts/build.ts vol4-tell             # Vol4 のみ
bun run scripts/build.ts all                   # 全巻
```

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

- Vol1 プリフロップ完全版: （旧 cash-preflop: https://gistpreview.github.io/?a263151bbdee0ac9cbaa4a4e97483edb）
- Vol2 キャッシュ ポストフロップ: https://gistpreview.github.io/?d50e33d174d918b1bbe9b7821ca8d1bb
- Vol3 MTT ポストフロップ: （未公開）
- Vol4 エクスプロイト: https://gistpreview.github.io/?519b2350329278e7be6f09e5be449cd9

旧シリーズ gist（参照用）：
- 旧②フロップ[基礎]: https://gistpreview.github.io/?5883292a2b687db842b4117f384c3aad
- 旧③フロップ[応用]: https://gistpreview.github.io/?e90c50f9dcdf09a311445db723c56fd6
- 旧④ターン・リバー[基礎]: https://gistpreview.github.io/?6c4006bb24b6350517a0ae8e5a52061a
- 旧⑤ターン・リバー[応用]: https://gistpreview.github.io/?f1c3973e0576af76f29ecf9a91fddb5b
- 旧⑥トーナメント編: https://gistpreview.github.io/?0923d0ef729f7a18aa11682402b3ef7b
- ダイジェスト版: https://gistpreview.github.io/?2abb4d163ac9e989333eb6db2a11f364

加えて GitHub Pages 経由で全巻を公開済み: <https://cuzic.github.io/poker-books/>
（`.github/workflows/deploy.yml` で main push 時に自動デプロイ）
