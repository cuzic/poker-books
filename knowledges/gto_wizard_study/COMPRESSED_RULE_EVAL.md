# 圧縮ルール (75 macro rules + default call) の精度評価

PURE 349 cell を圧縮した 75 マクロルールを階層適用、accuracy / loss を評価。

## ルール構造

| level | 識別子 | ルール数 |
|------|--------|----:|
| Type 1 (最優先) | (pot, street, カテゴリ) → action | 24 |
| Type 2 | (pot, street, sub_family) → action | 21 |
| Type 3 | (pot, street) → action | 5 |
| Default | call (defender MDF 想定) | 1 |
| **合計** | | **51** |

## 全体結果 (3 ルール群比較)

| 指標 | 圧縮ルール 75 | フル lookup 642 | 既存公式 v9b/v10/v15 |
|---|---:|---:|---:|
| ルール数 | **76** | 642 | ~50 数値+ロジック |
| Accuracy | **63.72%** | 71.64% | 59.46% |
| Avg loss | **0.8768 BB** | 0.5806 BB | 1.8595 BB |
| Huge loss (>5BB) | **3.43%** | 2.72% | 9.65% |

## rule source 別 breakdown

各 row がどのレイヤーで判定されたか + 各レイヤーの accuracy

| source | n | rows% | accuracy | avg loss |
|---|---:|---:|---:|---:|
| T1 | 96,219 | 62.4% | 71.94% | 0.4844 BB |
| T2 | 24,946 | 16.2% | 55.24% | 2.2231 BB |
| T3 | 15,017 | 9.7% | 44.50% | 1.0930 BB |
| DEFAULT | 18,034 | 11.7% | 47.64% | 0.9283 BB |

## pot type 別

| pot | n | accuracy | avg loss | huge% |
|---|---:|---:|---:|---:|
| SRP | 43,660 | 70.42% | 1.4444 BB | 4.65% |
| 3BP | 27,648 | 61.52% | 0.6215 BB | 2.93% |
| 4BP | 48,816 | 56.86% | 0.8573 BB | 3.78% |
| DEF | 34,092 | 66.75% | 0.3849 BB | 1.80% |

## 解釈

- **76 ルールだけで accuracy 63.7%、loss 0.877 BB/spot**
- フル lookup (642 cells) から +566 cells 削減しても accuracy はわずか +7.9pp 減
- 既存公式 (v9b/v10/v15) と比較:
  - avg loss **52.8% 改善** (1.860→0.877)
  - huge loss **64.4% 削減** (9.6→3.4%)

**結論**: 76 ルール暗記で公式 (40-50 ルール+演算) より高精度。
Chen Formula 系譜の "暗算可能な簡易式" として実用十分。