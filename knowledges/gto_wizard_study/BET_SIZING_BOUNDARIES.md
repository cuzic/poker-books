# Bet Sizing 境界の実測 — 77 boards data 由来

既存 probe data の action_solutions から sizing 別の頻度 / カテゴリ 配分を集計。

## sub-family ごとの sizing 使用パターン

| sub-family | small (~33%) | medium (~66%) | large (~100%+) | n |
|---|---:|---:|---:|---:|
| Ahigh_close | 43.9% | 0.0% | 0.0% | 1 |
| Ahigh_spread | 48.6% | 0.0% | 25.2% | 9 |
| Khigh_close | 46.0% | 0.0% | 21.7% | 2 |
| Khigh_spread | 48.0% | 0.0% | 0.0% | 6 |
| broadway_dry | 48.3% | 0.0% | 27.9% | 6 |
| connected_broadway | 40.1% | 0.0% | 17.5% | 3 |
| connected_low | 54.5% | 0.0% | 34.7% | 9 |
| connected_mid | 43.6% | 0.0% | 24.8% | 10 |
| low_dry | 0.0% | 0.0% | 33.9% | 2 |
| mid_dry | 0.0% | 0.0% | 33.3% | 7 |
| monotone | 36.2% | 0.0% | 15.0% | 3 |
| paired_broadway | 41.9% | 0.0% | 0.0% | 3 |
| paired_high | 41.1% | 0.0% | 0.0% | 5 |
| paired_low | 50.1% | 0.0% | 0.0% | 5 |
| paired_mid | 42.0% | 0.0% | 0.0% | 6 |

## sizing × カテゴリ の使用比率
(同じ カテゴリ 内で、どの sizing が選ばれるか)

| カテゴリ | small (~33%) | medium (~66%) | large (~100%+) |
|---|---|---|---|
| ナッツメイド | 0% | — | 0% |
| ストロング | 6% | — | 8% |
| ツーペア | 2% | — | 6% |
| トップペア以上 | 10% | — | 15% |
| ミドルペア | 19% | — | 6% |
| エア | 61% | — | 66% |

## 観察

- **small (1.9bb ~33%)**: dry / static board の標準。range advantage で wide attack
- **large (6.5bb ~100%+)**: wet / dynamic board の polar attack
- **medium はほぼ存在しない** → MATCHA の **2-カテゴリ sizing で十分** (small/large 二択)
- tier 別: ナッツメイド と エア は large 寄り (polar)、TP+ / ミドルペア は small 寄り (merged)

## drill / 書籍への反映

MATCHA の Bet Sizing 4 段階 (スモール / ミディアム / オーバー / オールイン) のうち、
**ミディアム (50%~) は実 GTO ではほぼ使われない** → 3 段階 (small / large / allin) に
簡略化可能。drill カードはこの 3 段階で問題ない。