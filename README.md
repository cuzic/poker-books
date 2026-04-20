# 『計算で勝つテキサスホールデム』シリーズ

テキサスホールデムを**暗算できる計算式**で判断する、初級者〜中級者向けの書籍シリーズ。

## 書籍一覧

### 第1巻　プリフロップは計算で勝つ

レンジ暗記に頼らない、簡易計算式で覚えるポーカー入門。

- **対象**：ポーカーを始めたばかり〜レンジ表の暗記で挫折した経験者
- **核となる式**：`Score = H + L + ボーナス − ペナルティ`（基本スコア式）、`Score₃ = H + 0.5L + B + S + C − G − R`（3ベットスコア式）
- **目次**：全 20 章 ＋ 付録 6 本（A〜F）
- **公開**：https://gistpreview.github.io/?a263151bbdee0ac9cbaa4a4e97483edb
- **ソース**：[`preflop/`](./preflop/)

### 第2巻　フロップは構造で勝つ（執筆中）

ボードを読み、式で判断するフロップ戦略。

- **対象**：プリフロップ編を読了した初級者
- **核となる式**：
  - `BoardScore`（0〜10、ドライ度指標）
  - `HandScore`（役 + アウツ数 × 1.5 + ブロッカー）
  - `CBet スコア = HandScore + (BoardScore − 5) + ポジション係数`
- **目次**：全 23 章 ＋ 付録 6 本（予定）
- **ソース**：[`flop/`](./flop/)

## 共通の設計思想

1. **暗算で回せる計算式**：Chen Formula、Sklansky Hand Groups の系譜を現代 GTO データで再設計
2. **境界暗記のハイブリッド**：式で 9 割、境界ハンドは GTO 最善手を暗記
3. **6-max、100BB、キャッシュゲーム**を基本想定
4. **各章末に【GTOとのズレ】コラム**：簡易式の限界を率直に示す

## ビルド方法

```bash
# プリフロップ編を HTML 化
bash scripts/build.sh preflop

# フロップ編を HTML 化
bash scripts/build.sh flop

# 両方一括
bash scripts/build.sh all
```

成果物は `dist/<book>/book.html`。pandoc による自己完結型 HTML（画像・CSS 埋め込み）。

## 執筆プロジェクトとしての詳細

執筆ワークフロー・リサーチ方針・品質基準は [`CLAUDE.md`](./CLAUDE.md) を参照。

## シリーズの位置づけ

本シリーズは以下の系譜に連なります。

- **Chen Formula**（Bill Chen、2000 年代）：ハンド数値化の原型
- **Sklansky-Malmuth Hand Groups**（1988 年）：チャンキング思考
- **Matthew Janda『Applications of No-Limit Hold'em』**（2013 年）：レンジ思考
- **Michael Acevedo『Modern Poker Theory』**（2019 年）：ソルバー時代の体系書
- **本シリーズ**：暗算で回せる形にアップデート

レンジ表の丸暗記で挫折した経験のあるすべてのプレイヤーへ。
