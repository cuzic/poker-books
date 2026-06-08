# eq 計算式 v2 — 30 特徴量 + optuna

## 性能

- 連続係数版: **52.18%**
- 整数係数版: **51.45%**
- 参考: 8-feature 版 (前回): 58.84%
- 参考: 24-cell grid: 58.0%

## 重要特徴量 (|weight| 上位)

| 特徴量 | 連続係数 | 整数 |
|--------|---:|---:|
| b_high | -2.882 | -3 |
| hero_low_match | +2.860 | +3 |
| hero_high_K | +2.708 | +3 |
| ace | -2.697 | -3 |
| hero_tp_kicker | +2.655 | +3 |
| total_gap | +2.446 | +2 |
| hero_low | -2.443 | -2 |
| hero_broadway | +2.272 | +2 |
| hero_set | -2.111 | -2 |
| monotone | +2.027 | +2 |
| b_low | -1.936 | -2 |
| hero_overpair | -1.884 | -2 |
| hero_overcards | -1.873 | -2 |
| paired | -1.701 | -2 |
| twotone | +1.423 | +1 |
| broadway_count | -1.339 | -1 |
| connected | -1.271 | -1 |
| hero_undercards | -1.200 | -1 |
| hero_top_match | -1.146 | -1 |
| b_r | -1.132 | -1 |
| **intercept** | +9.087 | +9 |

閾値: t_weak=5, t_good=10, t_best=11
