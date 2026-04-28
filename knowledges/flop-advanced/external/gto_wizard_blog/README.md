# GTO Wizard ブログから抽出した数値データ

巻③（フロップ応用編）の精密レンジスコア校正・係数検証用に、GTO Wizard 公式ブログ 15 記事から数値データを抽出した。

## 取得方法

### Phase C: 本文テキスト抽出（WebFetch）
- 各記事を WebFetch で取得し、本文中の数値を JSON 形式で抽出
- 結果: **約 160 データ点** → `extracted_data.json`

### Phase A: 画像 OCR（Read tool）
- 数値ラベル付き画像（CBet サイジング分布、ハンドクラス内訳など）を Read tool で OCR
- 結果: **画像 12 枚から ~80 細かい数値点** → `ocr_data.json`

## ファイル

| ファイル | 内容 | データ点数 |
| --- | --- | ---: |
| `extracted_data.json` | 本文中の数値抽出（記事ごと） | ~160 |
| `ocr_data.json` | 画像 OCR で得た詳細値 | ~80 |
| `manifest.json` | 全 267 画像の メタデータ | 267 |
| `images/` | ダウンロード済み記事画像 (267 枚 / 58MB) | - |
| `html/` | 記事 HTML キャッシュ (15 ファイル) | - |
| `fetch_articles.py` | HTML/画像取得スクリプト | - |

## 主要な校正用データポイント

### ボード型別 IP CBet 頻度（BTN vs BB SRP, 100bb）

| ボード型 | 例 | IP CBet 頻度 | 主サイズ |
| --- | --- | ---: | --- |
| ハイ × ドライ × ペア | QQ6 | **81.9%** | 33% pot |
| 全 flop 平均 | (1755 boards) | **53.2%** | 33% pot |
| ハイ × ウェット × 中間 | KJ7 | **49.3%** | 33% pot |
| ハイ × ウェット × broadway | QJT | **47.3%** | 125% overbet |

### ポジション別 CBet 頻度（記事 04, 06）

| シナリオ | 頻度 |
| --- | ---: |
| BTN vs BB caller | 75% |
| BTN vs SB caller | 50% |
| **UTG OOP 全平均** | **28%（チェック 72%）** |

### スート構造別の EV（記事 01）

| 構造 | EV (BTN vs BB SRP) |
| --- | ---: |
| Rainbow | 3.19 |
| 2-tone (Flush draw) | 3.11 |
| Monotone | 2.97 |

### 30bb / 40bb / 100bb の比較（複数記事）

詳細は `extracted_data.json` 参照。スタック深度別の頻度差が複数記事に散在。

## 抽出元記事リスト

1. [Flop Heuristics: IP C-Betting in Cash Games](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/)
2. [Flop Heuristics: IP C-Betting in MTTs](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-mtts/)
3. [Flop Heuristics: OOP C-Betting in MTTs](https://blog.gtowizard.com/flop-heuristics-oop-c-betting-in-mtts/)
4. [Flop Heuristics for Defending the Blinds in MTTs](https://blog.gtowizard.com/flop-heuristics-for-defending-the-blinds-in-mtts/)
5. [The Mechanics of C-Bet Sizing](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/) ← 最も数値豊富
6. [C-Betting As the OOP Preflop Raiser](https://blog.gtowizard.com/c-betting-as-the-oop-preflop-raiser/)
7. [C-Betting OOP in 3-Bet Pots](https://blog.gtowizard.com/c-betting-oop-in-3-bet-pots/)
8. [Aggregate Flop Strategy: SB C-Betting in SRP](https://blog.gtowizard.com/aggregate-flop-strategy-sb-c-betting-in-srp/)
9. [Maximizing Value on Monotone Flops](https://blog.gtowizard.com/maximizing-value-on-monotone-flops/)
10. [Attacking Paired Flops From the BB](https://blog.gtowizard.com/attacking-paired-flops-from-the-bb/)
11. [Exploiting Excessive C-Betting by IP](https://blog.gtowizard.com/exploiting-excessive-c-betting-by-ip/)
12. [Exploiting Excessive C-Betting by OOP](https://blog.gtowizard.com/exploiting-excessive-c-betting-by-oop/)
13. [Defending vs BB Check-Raise on Paired Flops](https://blog.gtowizard.com/defending-vs-bb-check-raise-on-paired-flops/)
14. [Why So Much? Larger-Than-Geometric Bet Sizing](https://blog.gtowizard.com/why-so-much-an-exploration-of-larger-than-geometric-bet-sizing/)
15. [Is Donk Betting for Donkeys?](https://blog.gtowizard.com/is-donk-betting-for-donkeys/)

## ライセンスと使用範囲

- **個人研究・書籍校正用途のみ**:GTO Wizard の利用規約は、コンテンツの**機械学習教師としての使用、再配布、商用転載**を禁止している
- 本書（巻③）の本文に数値を引用する際は、**出典 URL を明記**し、引用範囲を 1 記事から 3-5 数値以内に抑える（フェアユースの範囲）
- 蒸留モデル（poker-distill）の教師データには **使用しない**
- 全画像 (`images/`) はキャッシュであり再配布しない

## 用途

1. **精密レンジスコアの係数校正クロスチェック**:TexasSolver の系統誤差（-10〜15%）を、GTO Wizard の値で補正
2. **巻③ 第1章 / 第4章の数値検証**:本文の係数や代表値を実測ベンチマークと比較
3. **ボード分類の妥当性検証**:7 型 / 17 型の代表値 vs GTO Wizard 値

## 抽出日

2026-04-27
