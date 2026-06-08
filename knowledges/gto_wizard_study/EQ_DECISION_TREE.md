# eq_bucket 予測 — Decision Tree / Random Forest / GBM

線形モデル (60% 限界) を非線形で超えられるか検証。

## 結果 (Train / Validation)

| モデル | train | val | n_leaves/trees |
|--------|---:|---:|---:|
| DT depth=3 | 61.01% | 60.93% | 8 |
| DT depth=5 | 64.36% | 64.26% | 32 |
| DT depth=7 | 69.25% | 69.40% | 127 |
| DT depth=10 | 74.83% | 74.64% | 787 |
| DT depth=15 | 79.69% | 77.33% | 5506 |
| DT depth=None | 80.74% | 76.49% | 11592 |
| RF depth=5 | 62.53% | 62.44% | 100 |
| RF depth=10 | 74.40% | 74.13% | 100 |
| RF depth=None | 80.73% | 76.64% | 100 |
| GBM depth=3 n=100 | 71.73% | 71.67% | 100 |

## 比較 (val accuracy)

| 方式 | val accuracy |
|------|---:|
| Decision Tree (depth 3) | 60.93% |
| Decision Tree (depth 5) | 64.26% |
| Decision Tree (depth 10) | 74.64% |
| Decision Tree (unlimited) | 76.49% |
| Random Forest (100 trees) | 76.64% |
| Gradient Boosting | 71.67% |
| (参考) 線形最高 (grid+linear) | 60.42% |

## Random Forest の feature importance (上位 15)

| feature | importance |
|---------|---:|
| mv_idx | 0.229 |
| opp_r | 0.179 |
| dv | 0.076 |
| a_r | 0.069 |
| b_r | 0.059 |
| hero_gap | 0.053 |
| b_low | 0.035 |
| b_high | 0.035 |
| hero_suits_on_board | 0.034 |
| hero_top_match | 0.026 |
| b_mid | 0.026 |
| hero_mid_match | 0.023 |
| hero_low_match | 0.018 |
| hero_suited | 0.017 |
| hero_undercards | 0.016 |
