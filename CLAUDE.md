# 『迷わないポーカー』シリーズ執筆プロジェクト

## プロジェクト概要

テキサスホールデムを「暗算できる判断フロー」で決める書籍シリーズ。

## シリーズ構成（新体制）

| 巻 | テーマ | ディレクトリ | 状態 |
|----|--------|------------|------|
| vol1 | キャッシュ プリフロップ | `cash-preflop/` | 初稿完了 |
| vol2 | キャッシュ ポストフロップ | `cash-postflop/` | 初稿完了 |
| vol3 | MTT プリフロップ | `mtt-preflop/` | 初稿完了 |
| vol4 | MTT ポストフロップ | `mtt-postflop/` | 執筆中 |
| vol5 | エクスプロイト（相手タイプ別） | `tell/` | 初稿完了 |

旧シリーズ（①〜⑥ + ダイジェスト）は `_archive/` に移動済み。

## 共通の設計思想

1. **暗算で回せる計算式**：Chen Formula、Sklansky Hand Groups の系譜に連なる簡易式を現代 GTO データで再設計
2. **境界暗記のハイブリッド**：式で 9 割、境界ハンドは GTO 最善手を暗記
3. **章末【GTO とのズレ】コラム**：簡易式と理論最適のギャップを率直に示す
4. **6-max、100BB、キャッシュゲーム**を基本想定

## Directory Structure

```
poker-books/
├── cash-preflop/    vol1: キャッシュ プリフロップ
├── cash-postflop/   vol2: キャッシュ ポストフロップ
├── mtt-preflop/     vol3: MTT プリフロップ
├── mtt-postflop/    vol4: MTT ポストフロップ（執筆中）
├── tell/            vol5: エクスプロイト
├── _archive/        旧シリーズ（flop/volume4-5/volume6/digest 等）
├── scripts/
│   └── build.ts    ビルドスクリプト（bun で実行）
└── dist/           ビルド成果物
```

## ビルド

```bash
bun run scripts/build.ts cash-preflop   # vol1 のみ
bun run scripts/build.ts mtt-preflop    # vol3 のみ
bun run scripts/build.ts all            # 全巻
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

- vol1 キャッシュ プリフロップ: https://gistpreview.github.io/?a263151bbdee0ac9cbaa4a4e97483edb
- vol2 キャッシュ ポストフロップ: https://gistpreview.github.io/?d50e33d174d918b1bbe9b7821ca8d1bb
- vol3 MTT プリフロップ: https://gistpreview.github.io/?e59b0bf5d62ac0e84f0176b390c50ca7
- vol4 MTT ポストフロップ: （未公開）
- vol5 エクスプロイト: https://gistpreview.github.io/?519b2350329278e7be6f09e5be449cd9

旧シリーズ gist（参照用）：
- 旧②フロップ[基礎]: https://gistpreview.github.io/?5883292a2b687db842b4117f384c3aad
- 旧③フロップ[応用]: https://gistpreview.github.io/?e90c50f9dcdf09a311445db723c56fd6
- 旧④ターン・リバー[基礎]: https://gistpreview.github.io/?6c4006bb24b6350517a0ae8e5a52061a
- 旧⑤ターン・リバー[応用]: https://gistpreview.github.io/?f1c3973e0576af76f29ecf9a91fddb5b
- 旧⑥トーナメント編: https://gistpreview.github.io/?0923d0ef729f7a18aa11682402b3ef7b
- ダイジェスト版: https://gistpreview.github.io/?2abb4d163ac9e989333eb6db2a11f364

加えて GitHub Pages 経由で全巻を公開済み: <https://cuzic.github.io/poker-books/>
（`.github/workflows/deploy.yml` で main push 時に自動デプロイ）
