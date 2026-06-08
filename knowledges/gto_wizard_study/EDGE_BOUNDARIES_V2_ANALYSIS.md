# エッジケース 12 spots の GTO 実測

MATCHA 公式の判定が直感に反する瞬間を data で確認。
各 spot で specific hand のアクション分布を実測。

## 1b. overpair 格下げ境界 (2/3 overcards)

### 66_AKQ

**66 on A-K-Q (3 overcards broadway)**
- board: `AsKdQc`
- hero: `6s6d`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 32.6% |
| CALL | 1.9bb | 64.5% |
| RAISE | 5bb | 2.9% |

**Hero tier 推定**: underpair

**Tier `underpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 0.0% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 0.0% |

**Tier `low_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 99.9% |
| FOLD | 0bb | 0.1% |
| RAISE | 5bb | 0.0% |

### 66_KQ3

**66 on K-Q-3**
- board: `KsQd3c`
- hero: `6s6d`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 30.1% |
| CALL | 1.9bb | 64.5% |
| RAISE | 10.3bb | 5.4% |

**Hero tier 推定**: underpair

**Tier `underpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 0.0% |
| FOLD | 0bb | 0.0% |
| RAISE | 10.3bb | 0.0% |

**Tier `low_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 99.9% |
| FOLD | 0bb | 0.0% |
| RAISE | 10.3bb | 0.1% |

### 88_KQ3

**88 on K-Q-3 (2 overcards)**
- board: `KsQd3c`
- hero: `8s8d`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 30.1% |
| CALL | 1.9bb | 64.5% |
| RAISE | 10.3bb | 5.4% |

**Hero tier 推定**: underpair

**Tier `underpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 0.0% |
| FOLD | 0bb | 0.0% |
| RAISE | 10.3bb | 0.0% |

**Tier `low_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 99.9% |
| FOLD | 0bb | 0.0% |
| RAISE | 10.3bb | 0.1% |

### 99_AT2

**99 on A-T-2 (2 overcards)**
- board: `AsTd2c`
- hero: `9s9d`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 28.9% |
| CALL | 1.9bb | 65.1% |
| RAISE | 10.3bb | 6.0% |

**Hero tier 推定**: underpair

**Tier `underpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 99.9% |
| FOLD | 0bb | 0.0% |
| RAISE | 10.3bb | 0.1% |

**Tier `low_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 0.0% |
| FOLD | 0bb | 0.0% |
| RAISE | 10.3bb | 0.0% |

## 2b. AA on wet/monotone board

### aa_T98_2tone

**AA on T-9-8 (connected 2tone)**
- board: `Ts9d8s`
- hero: `AsAd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 29.1% |
| CALL | 1.9bb | 60.6% |
| RAISE | 5bb | 10.4% |

**Hero tier 推定**: overpair

**Tier `overpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 29.3% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 70.7% |

## 3. low overpair の sizing 境界

### low_66_pre_jam

**66 on 5-4-2, pot vs 100% cbet**
- board: `5d4c2s`
- hero: `6s6h`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 62.3% |
| CALL | 6.5bb | 22.1% |
| RAISE | 17.8bb | 15.6% |

**Hero tier 推定**: overpair

**Tier `overpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 6.5bb | 56.4% |
| FOLD | 0bb | 0.0% |
| RAISE | 17.8bb | 43.6% |

### low_77_pre_jam

**77 on 5-4-2, vs 100% cbet**
- board: `5d4c2s`
- hero: `7s7d`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 62.3% |
| CALL | 6.5bb | 22.1% |
| RAISE | 17.8bb | 15.6% |

**Hero tier 推定**: overpair

**Tier `overpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 6.5bb | 56.4% |
| FOLD | 0bb | 0.0% |
| RAISE | 17.8bb | 43.6% |

### low_88_pre_jam

**88 on 5-4-2, vs 100% cbet**
- board: `5d4c2s`
- hero: `8s8d`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 62.3% |
| CALL | 6.5bb | 22.1% |
| RAISE | 17.8bb | 15.6% |

**Hero tier 推定**: overpair

**Tier `overpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 6.5bb | 56.4% |
| FOLD | 0bb | 0.0% |
| RAISE | 17.8bb | 43.6% |

### low_TT_pre_jam

**TT on 5-4-2, vs 100% cbet**
- board: `5d4c2s`
- hero: `TsTd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 62.3% |
| CALL | 6.5bb | 22.1% |
| RAISE | 17.8bb | 15.6% |

**Hero tier 推定**: overpair

**Tier `overpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 6.5bb | 56.4% |
| FOLD | 0bb | 0.0% |
| RAISE | 17.8bb | 43.6% |

## 4. BTN attacker 側

### attk_66_K72

**BTN attacker 66 on K72 (pre-cbet)**
- board: `Ks7d2c`
- hero: `6s6d`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 95.3% |
| RAISE | 6.5bb | 4.7% |

**Hero tier 推定**: underpair

**Tier `underpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 99.4% |
| RAISE | 6.5bb | 0.6% |

**Tier `low_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 0.0% |
| RAISE | 6.5bb | 0.0% |

### attk_66_KQ3

**BTN attacker 66 on KQ3 (pre-cbet)**
- board: `KsQd3c`
- hero: `6s6d`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 97.3% |
| RAISE | 6.5bb | 2.7% |

**Hero tier 推定**: underpair

**Tier `underpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 0.0% |
| RAISE | 6.5bb | 0.0% |

**Tier `low_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 99.5% |
| RAISE | 6.5bb | 0.5% |

### attk_AhKh_876

**BTN attacker AhKh on 876 (overcards+BD)**
- board: `8s7d6c`
- hero: `AhKh`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 95.9% |
| RAISE | 6.5bb | 4.1% |

**Hero tier 推定**: ?

**Tier `no_made_hand` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 36.6% |
| RAISE | 6.5bb | 63.4% |

**Tier `ace_high` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 73.1% |
| RAISE | 6.5bb | 26.9% |

**Tier `king_high` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 68.4% |
| RAISE | 6.5bb | 31.6% |

### attk_QQ_KQ3

**BTN attacker QQ on KQ3 (TPTK)**
- board: `KsQd3c`
- hero: `QsQd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 97.3% |
| RAISE | 6.5bb | 2.7% |

**Hero tier 推定**: trips

**Tier `trips` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 0.0% |
| RAISE | 6.5bb | 0.0% |

**Tier `set` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 7.3% |
| RAISE | 6.5bb | 92.7% |

**Tier `fullhouse` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 0.0% |
| RAISE | 6.5bb | 0.0% |

**Tier `quads` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 0.0% |
| RAISE | 6.5bb | 0.0% |

## 6. JJ の board cross 比較

### jj_222

**JJ on 2-2-2 (paired low)**
- board: `2c2d2s`
- hero: `JsJd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 30.2% |
| CALL | 1.9bb | 47.9% |
| RAISE | 5bb | 21.9% |

**Hero tier 推定**: overpair

**Tier `overpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 0.0% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 0.0% |

### jj_A72

**JJ on A-7-2 (1 over, dry)**
- board: `As7d2c`
- hero: `JsJd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 27.6% |
| CALL | 1.9bb | 64.7% |
| RAISE | 10.3bb | 7.7% |

**Hero tier 推定**: 2nd pair

**Tier `second_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 95.6% |
| FOLD | 0bb | 0.0% |
| RAISE | 10.3bb | 4.4% |

**Tier `third_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 64.6% |
| FOLD | 0bb | 0.0% |
| RAISE | 10.3bb | 35.4% |

### jj_K22

**JJ on K-2-2 (paired, K over)**
- board: `Kc2d2s`
- hero: `JsJd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 33.8% |
| CALL | 1.9bb | 42.4% |
| RAISE | 5bb | 23.7% |

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
| CALL | 1.9bb | 0.0% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 0.0% |

### jj_T22

**JJ on T-2-2 (paired, 1 over)**
- board: `Tc2d2s`
- hero: `JsJd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 28.9% |
| CALL | 1.9bb | 64.7% |
| RAISE | 10.3bb | 6.4% |

**Hero tier 推定**: overpair

**Tier `overpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 99.1% |
| FOLD | 0bb | 0.0% |
| RAISE | 10.3bb | 0.9% |

### jj_T98

**JJ on T-9-8 (connected, 1 over)**
- board: `Ts9d8c`
- hero: `JsJd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 28.4% |
| CALL | 1.9bb | 64.4% |
| RAISE | 10.3bb | 7.1% |

**Hero tier 推定**: overpair

**Tier `overpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 33.5% |
| FOLD | 0bb | 0.0% |
| RAISE | 10.3bb | 66.5% |

## 8. TPTK の格下げ

### AK_AT5

**AKo TPTK on A-T-5**
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
