# 『迷わないポーカー』シリーズ執筆プロジェクト

## プロジェクト概要

テキサスホールデムを「暗算できる判断フロー」で決める書籍シリーズ。

## シリーズ構成

| 巻 | 書名 | ディレクトリ | 状態 |
|----|-----|------------|------|
| ① | 迷わないポーカー① プリフロップ | `preflop/` | 公開済み |
| ② | 迷わないポーカー② フロップ[基礎] | `flop/` | 公開済み |
| ③ | 迷わないポーカー③ フロップ[応用] | `flop-advanced/` | 公開済み |
| ④ | 迷わないポーカー④ ターン・リバー[基礎] | `volume4/` | 公開済み |
| ⑤ | 迷わないポーカー⑤ ターン・リバー[応用] | `volume5/` | 公開済み |
| ⑥ | 迷わないポーカー⑥ トーナメント | `volume6/` | 公開済み |

## 共通の設計思想

1. **暗算で回せる計算式**：Chen Formula、Sklansky Hand Groups の系譜に連なる簡易式を現代 GTO データで再設計
2. **境界暗記のハイブリッド**：式で 9 割、境界ハンドは GTO 最善手を暗記
3. **章末【GTO とのズレ】コラム**：簡易式と理論最適のギャップを率直に示す
4. **6-max、100BB、キャッシュゲーム**を基本想定

## Directory Structure

```
poker-books/                     ルートディレクトリ
├── preflop/                      プリフロップ編
│   ├── chapters/                # 本文（00〜21）
│   ├── toc.md                   # 目次・執筆ガイド
│   ├── book.json                # 書誌
│   ├── source.txt               # 原典メモ
│   └── CLAUDE.md                # 編固有の方針
│
├── flop/                         フロップ編
│   ├── chapters/                # 本文（執筆中）
│   ├── toc.md
│   ├── book.json
│   ├── source.txt
│   └── CLAUDE.md
│
├── knowledges/                   リサーチ成果
│   ├── preflop/                 # プリフロップ編リサーチ
│   │   ├── 01_*.md 〜 20_*.md
│   │   └── reviews/
│   └── flop/                    # フロップ編リサーチ
│       └── reviews/
│
├── scripts/
│   └── build.sh                 # 書籍指定式ビルドスクリプト
│
├── dist/                         ビルド成果物
│   ├── preflop/book.html
│   └── flop/book.html
│
├── CLAUDE.md                     このファイル（プロジェクト全体）
└── README.md                     シリーズ紹介
```

## ビルド

```bash
bash scripts/build.sh preflop    # プリフロップ編のみ
bash scripts/build.sh flop       # フロップ編のみ
bash scripts/build.sh all        # 両方
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

各巻の gist URL は書籍固有（`book.json` 内の `identifier` とは別）。公開済みの gist：

- プリフロップ編: https://gistpreview.github.io/?a263151bbdee0ac9cbaa4a4e97483edb
- フロップ編[基礎]: （未公開）
- フロップ編[応用]: （未公開）
- ターン・リバー[基礎]: （未公開）
- ターン・リバー[応用]: （未公開）
- トーナメント編: （未公開）
- ダイジェスト版: （未公開）

加えて GitHub Pages 経由で全巻を公開済み: <https://cuzic.github.io/poker-books/>
（`.github/workflows/deploy.yml` で main push 時に自動デプロイ）
