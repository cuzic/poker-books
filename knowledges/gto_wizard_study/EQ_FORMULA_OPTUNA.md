# eq を求めるための計算式 — optuna 最適化

ハンド (mv_cat, dv_cat) + board (paired/mono/connected/high) の特徴量から
eq_bucket (best/good/weak/trash) を予測する公式。

## 公式

```
EqScore = w_tier × tier_strength
        + w_draw × draw_strength
        - w_over × overcards_count
        - w_pair × board_paired (not your trips)
        - w_mono × board_monotone (not your flush)
        - w_conn × board_connected (not your straight)
        - w_2tone × board_twotone (not your flush)
        + w_high × board_high_card
        + intercept

EqScore >= T_best → best_hands (9 pts)
        >= T_good → good_hands (6 pts)
        >= T_weak → weak_hands (3 pts)
        else      → trash_hands (0 pts)
```

## 入力値

### tier_strength (mv_cat 別)

- straight_flush: 10
- quads: 9
- fullhouse: 8
- straight: 7
- flush: 7
- set: 6
- trips: 6
- two_pair: 5
- overpair: 4
- top_pair: 3
- second_pair: 2
- third_pair: 1
- underpair: 1
- low_pair: 1
- no_made_hand: 0
- king_high: 0
- ace_high: 0

### draw_strength (dv_cat 別)

- fd+oesd: 4
- fd+gutshot: 3
- combo_draw: 3
- oesd: 2
- fd: 2
- gutshot: 1
- no_draw: 0

## 最適パラメータ (連続値)

| 係数 | 値 |
|------|---:|
| w_tier | 3.177 |
| w_draw | 2.529 |
| w_over | 2.716 |
| w_pair | 1.126 |
| w_mono | 2.325 |
| w_conn | 2.622 |
| w_2tone | 0.944 |
| w_high | -0.093 |
| intercept | -1.035 |
| t_best | 13.542 |
| t_good | 3.700 |
| t_weak | -0.302 |

## 整数係数版 (書籍向け)

| 係数 | 値 |
|------|---:|
| w_tier | 3 |
| w_draw | 3 |
| w_over | 3 |
| w_pair | 1 |
| w_mono | 2 |
| w_conn | 3 |
| w_2tone | 1 |
| w_high | 0 |
| intercept | -1 |
| t_best | 14 |
| t_good | 4 |
| t_weak | 0 |

## 性能

| 方式 | accuracy |
|------|---:|
| 連続係数版 | **58.84%** |
| 整数係数版 | **58.31%** |
| (参考) tier × board grid | 58.0% (eq 推定後) |
| (参考) 直接 eq | 100% (eq そのまま使用) |

## 比較: MATCHA 最終公式での使用

```
1. EqScore を計算 (上の公式)
2. eq_bucket を判定 (best/good/weak/trash)
3. Score = eq_value (9/6/3/0) - bs + pot
4. 判定: >= 16 raise / >= 3 call / else fold
```

EqScore 公式が accuracy 約 60-70% で eq_bucket を当てる → MATCHA 公式に流す