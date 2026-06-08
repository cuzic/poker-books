# エッジケース 12 spots の GTO 実測

MATCHA 公式の判定が直感に反する瞬間を data で確認。
各 spot で specific hand のアクション分布を実測。

## 1. overpair vs 2nd pair 境界

### ov_77_K72

**77 on K-high (pair of 7s in board overlap)**
- board: `Ks7d2c`
- hero: `7s7d`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 29.7% |
| CALL | 1.9bb | 58.6% |
| RAISE | 5bb | 11.7% |

**Hero tier 推定**: trips

**Tier `trips` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 0.0% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 0.0% |

**Tier `set` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 6.0% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 94.0% |

**Tier `fullhouse` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 0.0% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 0.0% |

**Tier `quads` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 0.0% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 0.0% |

### ov_88_T72

**88 on T-high — 2 overcards**
- board: `Ts7d2c`
- hero: `8s8d`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 27.9% |
| CALL | 1.9bb | 62.9% |
| RAISE | 10.3bb | 9.3% |

**Hero tier 推定**: 2nd pair

**Tier `second_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 99.9% |
| FOLD | 0bb | 0.0% |
| RAISE | 10.3bb | 0.1% |

**Tier `third_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 63.7% |
| FOLD | 0bb | 0.0% |
| RAISE | 10.3bb | 36.2% |

### ov_JJ_Q72

**JJ on Q-high — overpair? 2nd pair?**
- board: `Qs7d2c`
- hero: `JsJd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 28.2% |
| CALL | 1.9bb | 65.5% |
| RAISE | 10.3bb | 6.3% |

**Hero tier 推定**: 2nd pair

**Tier `second_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 90.2% |
| FOLD | 0bb | 0.0% |
| RAISE | 10.3bb | 9.8% |

**Tier `third_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 57.8% |
| FOLD | 0bb | 0.0% |
| RAISE | 10.3bb | 42.2% |

### ov_QQ_K72

**QQ on K-high — overpair? 2nd pair?**
- board: `Ks7d2c`
- hero: `QsQd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 29.7% |
| CALL | 1.9bb | 58.6% |
| RAISE | 5bb | 11.7% |

**Hero tier 推定**: 2nd pair

**Tier `second_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 66.9% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 33.1% |

**Tier `third_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 49.4% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 50.6% |

### ov_TT_J72

**TT on J-high**
- board: `Js7d2c`
- hero: `TsTd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 28.3% |
| CALL | 1.9bb | 64.2% |
| RAISE | 10.3bb | 7.5% |

**Hero tier 推定**: 2nd pair

**Tier `second_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 99.5% |
| FOLD | 0bb | 0.0% |
| RAISE | 10.3bb | 0.5% |

**Tier `third_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 62.7% |
| FOLD | 0bb | 0.0% |
| RAISE | 10.3bb | 37.3% |

### ov_TT_K72

**TT on K-high — 1 overcard**
- board: `Ks7d2c`
- hero: `TsTd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 29.7% |
| CALL | 1.9bb | 58.6% |
| RAISE | 5bb | 11.7% |

**Hero tier 推定**: 2nd pair

**Tier `second_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 66.9% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 33.1% |

**Tier `third_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 49.4% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 50.6% |

## 2. AA の slowplay 境界 (board の wet 度別)

### aa_dry_K72

**AA on dry K-high — TPTK like**
- board: `Ks7d2c`
- hero: `AsAd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 29.7% |
| CALL | 1.9bb | 58.6% |
| RAISE | 5bb | 11.7% |

**Hero tier 推定**: overpair

**Tier `overpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 20.1% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 79.9% |

### aa_mid_876

**AA on mid connected**
- board: `8s7d6c`
- hero: `AsAd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 27.7% |
| CALL | 1.9bb | 57.7% |
| RAISE | 5bb | 14.6% |

**Hero tier 推定**: overpair

**Tier `overpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 28.8% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 71.2% |

### aa_paired_KK4

**AA on paired K — overpair**
- board: `KsKd4c`
- hero: `AsAd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 30.5% |
| CALL | 1.9bb | 52.9% |
| RAISE | 5bb | 16.7% |

**Hero tier 推定**: overpair

**Tier `overpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 98.3% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 1.7% |

## 4. counterfeit / paired board 境界

### cf_77_7_7_2

**77 on paired 7 — quads**
- board: `7s7d2c`
- hero: `7c7h`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 31.0% |
| CALL | 1.9bb | 49.5% |
| RAISE | 5bb | 19.6% |

**Hero tier 推定**: trips/set

**Tier `trips` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 27.4% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 72.6% |

**Tier `set` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 0.0% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 0.0% |

**Tier `fullhouse` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 28.2% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 71.8% |

**Tier `quads` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 22.2% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 77.8% |

### cf_88_8_8_A

**88 on paired 8 with A — quads**
- board: `8s8dAh`
- hero: `8c8h`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 32.2% |
| CALL | 1.9bb | 51.5% |
| RAISE | 5bb | 16.3% |

**Hero tier 推定**: trips

**Tier `trips` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 29.8% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 70.2% |

**Tier `set` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 0.0% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 0.0% |

**Tier `fullhouse` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 27.4% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 72.6% |

**Tier `quads` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 13.9% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 86.1% |

### cf_JJ_8_8_A

**JJ on paired 8 with A overcard**
- board: `8s8dAh`
- hero: `JsJd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 32.2% |
| CALL | 1.9bb | 51.5% |
| RAISE | 5bb | 16.3% |

**Hero tier 推定**: 2nd pair

**Tier `second_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 0.0% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 0.0% |

**Tier `third_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 66.9% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 33.0% |

### cf_QQ_8_8_4

**QQ on paired 8 low — clean overpair**
- board: `8s8d4c`
- hero: `QsQd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 30.7% |
| CALL | 1.9bb | 52.2% |
| RAISE | 5bb | 17.0% |

**Hero tier 推定**: overpair

**Tier `overpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 69.4% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 30.6% |

### cf_QQ_K_K_4

**QQ on paired K-high — under quads**
- board: `KsKd4c`
- hero: `QsQd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 30.5% |
| CALL | 1.9bb | 52.9% |
| RAISE | 5bb | 16.7% |

**Hero tier 推定**: underpair

**Tier `underpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 54.6% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 45.4% |

**Tier `low_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 0.0% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 0.0% |

## 5. combo draw 境界

### draw_FD_only

**98h on Kh7h2c — FD only (low)**
- board: `Kh7h2c`
- hero: `9h8h`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 28.9% |
| CALL | 1.9bb | 63.7% |
| RAISE | 10.3bb | 7.4% |

**Hero tier 推定**: ?

**Tier `no_made_hand` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 15.6% |
| FOLD | 0bb | 59.9% |
| RAISE | 10.3bb | 24.5% |

**Tier `ace_high` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 63.1% |
| FOLD | 0bb | 0.2% |
| RAISE | 10.3bb | 36.7% |

**Tier `king_high` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 0.0% |
| FOLD | 0bb | 0.0% |
| RAISE | 10.3bb | 0.0% |

### draw_gutshot_FD

**J9h on QhTh2c — gutshot + FD**
- board: `QhTh2c`
- hero: `Jh9h`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 29.6% |
| CALL | 1.9bb | 63.0% |
| RAISE | 10.3bb | 7.3% |

**Hero tier 推定**: ?

**Tier `no_made_hand` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 10.6% |
| FOLD | 0bb | 70.1% |
| RAISE | 10.3bb | 19.3% |

**Tier `ace_high` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 60.9% |
| FOLD | 0bb | 0.1% |
| RAISE | 10.3bb | 38.9% |

**Tier `king_high` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 35.3% |
| FOLD | 0bb | 23.3% |
| RAISE | 10.3bb | 41.3% |

## 6. Pot type で格下げ

### pot_AKo_AT5_srp

**AKo TPTK on A-T-5 in SRP — baseline**
- board: `AsTd5c`
- hero: `AhKd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 28.6% |
| CALL | 1.9bb | 65.6% |
| RAISE | 10.3bb | 5.8% |

**Hero tier 推定**: ?

**Tier `no_made_hand` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 13.5% |
| FOLD | 0bb | 55.1% |
| RAISE | 10.3bb | 31.4% |

**Tier `ace_high` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 0.0% |
| FOLD | 0bb | 0.0% |
| RAISE | 10.3bb | 0.0% |

**Tier `king_high` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 84.4% |
| FOLD | 0bb | 0.5% |
| RAISE | 10.3bb | 15.1% |

## 7. 浅 SPR の overpair

### spr_AA_4bp

**AA in 4BP on low board**
- board: `5d4c2s`
- hero: `AsAd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 45.4% |
| RAISE | 72bb | 54.6% |

**Hero tier 推定**: overpair

**Tier `overpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 78.9% |
| RAISE | 72bb | 21.1% |

### spr_JJ_4bp

**JJ in 4BP on low board (deep SPR comparison)**
- board: `5d4c2s`
- hero: `JsJd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 45.4% |
| RAISE | 72bb | 54.6% |

**Hero tier 推定**: overpair

**Tier `overpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 78.9% |
| RAISE | 72bb | 21.1% |
