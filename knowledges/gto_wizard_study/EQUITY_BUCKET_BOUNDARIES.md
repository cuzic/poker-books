# Equity Bucket 境界の実測 — 293K rows data

dataset_unified_v2.csv の equity_bucket / eq_percentile に基づく
GTO 行動分布の集計。MATCHA の equity 4 段階 (best/good/weak/trash) を data 裏付け。

## bucket ごとの GTO 行動

| bucket | n | 平均 equity | 平均 percentile | fold% | call% | raise% |
|---|--:|---:|---:|---:|---:|---:|
| best_hands | 23,100 | 87.3% | 0.9 | 0.0% | 75.7% | 24.3% |
| good_hands | 44,022 | 60.3% | 0.8 | 4.1% | 71.0% | 24.8% |
| weak_hands | 78,752 | 39.5% | 0.5 | 42.6% | 51.3% | 6.1% |
| trash_hands | 147,445 | 19.5% | 0.2 | 86.0% | 12.1% | 2.0% |

## eq_percentile 10% bin ごとの GTO 行動

| percentile bin | n | fold% | call% | raise% | avg eq |
|---|--:|---:|---:|---:|---:|
| 0-10 | 80,960 | 97.3% | 1.4% | 1.2% | 18.0% |
| 1-11 | 27,079 | 88.5% | 7.5% | 4.0% | 26.6% |
| 2-12 | 22,785 | 81.1% | 13.9% | 5.0% | 26.8% |
| 3-13 | 30,816 | 77.9% | 18.0% | 4.1% | 24.4% |
| 4-14 | 17,581 | 48.1% | 47.1% | 4.9% | 37.2% |
| 5-15 | 18,410 | 28.3% | 66.7% | 5.0% | 39.1% |
| 6-16 | 22,628 | 10.3% | 83.3% | 6.4% | 41.8% |
| 7-17 | 25,480 | 2.9% | 86.0% | 11.2% | 50.0% |
| 8-18 | 26,058 | 0.5% | 69.9% | 29.6% | 65.4% |
| 9-19 | 21,522 | 0.0% | 72.2% | 27.8% | 84.5% |

## bucket 間の境界 (隣接差)

| transition | fold 差 | call 差 | raise 差 | 境界明確性 |
|---|---:|---:|---:|---|
| best_hands → good_hands | +4.1% | -4.7% | +0.5% | 🔴 弱い |
| good_hands → weak_hands | +38.5% | -19.8% | -18.7% | 🟢 明確 |
| weak_hands → trash_hands | +43.3% | -39.2% | -4.1% | 🟢 明確 |

## 観察

- equity_bucket は GTO Wizard 側の分類 (best/good/weak/trash)
- percentile bin 別に見ると、行動境界が連続的か離散的か判定可能
- MATCHA で「equity 50% 以上はバリュー」「30% 以下はブラフキャッチ」
  のような閾値が data で裏付けされるかを percentile bin から読み取る