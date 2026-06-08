# エッジケース 12 spots の GTO 実測

MATCHA 公式の判定が直感に反する瞬間を data で確認。
各 spot で specific hand のアクション分布を実測。

## A. 過大評価リスク (強い tier だが equity 低い)

### A1_66_low_connected_pre_cbet

**BB pre-cbet, 66 overpair on 5-4-2**
- board: `5d4c2s`
- hero: `6s6h`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 87.9% |
| RAISE | 6.5bb | 12.1% |

**Hero tier 推定**: overpair

**Tier `overpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 27.1% |
| RAISE | 6.5bb | 72.9% |

### A2_JJ_KT9_mono_vs_cbet

**BB facing cbet, JJ overpair on KTh-mono**
- board: `KhTh9h`
- hero: `JsJd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 29.9% |
| CALL | 1.9bb | 66.7% |
| RAISE | 10.3bb | 3.5% |

**Hero tier 推定**: 2nd pair

**Tier `second_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 92.1% |
| FOLD | 0bb | 0.1% |
| RAISE | 10.3bb | 7.9% |

**Tier `third_pair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 61.2% |
| FOLD | 0bb | 0.1% |
| RAISE | 10.3bb | 38.7% |

### A3_TT_A72_vs_cbet

**BB facing cbet, TT (mid pocket) vs A-high**
- board: `As7d2c`
- hero: `TsTd`

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

### A4_AA_987_vs_cbet

**BB facing cbet, AA overpair on connected 9-8-7**
- board: `9s8d7c`
- hero: `AsAd`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 27.3% |
| CALL | 1.9bb | 61.7% |
| RAISE | 5bb | 11.0% |

**Hero tier 推定**: overpair

**Tier `overpair` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 23.2% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 76.8% |

### A5_KK_A72_vs_cbet

**BB facing cbet, KK overpair with A overcard**
- board: `As7d2c`
- hero: `KsKd`

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

## B. 過小評価リスク (弱い tier だが equity 高い)

### B6_65s_456_pre_cbet

**BB pre-cbet, 65s = TP+OESD on 6-5-4**
- board: `6d5c4s`
- hero: `6h5h`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 98.1% |
| RAISE | 6.5bb | 1.9% |

**Hero tier 推定**: ?

**Tier `no_made_hand` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 43.7% |
| RAISE | 6.5bb | 56.3% |

**Tier `ace_high` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 68.1% |
| RAISE | 6.5bb | 31.9% |

**Tier `king_high` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CHECK | 0bb | 53.5% |
| RAISE | 6.5bb | 46.5% |

### B8_54h_678h_mono_vs_cbet

**BB facing cbet, 5h4h = combo draw on monotone 678h**
- board: `6h7h8h`
- hero: `5h4h`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 29.6% |
| CALL | 1.9bb | 54.5% |
| RAISE | 5bb | 15.9% |

**Hero tier 推定**: ?

**Tier `no_made_hand` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 18.4% |
| FOLD | 0bb | 49.4% |
| RAISE | 5bb | 32.1% |

**Tier `ace_high` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 28.3% |
| FOLD | 0bb | 46.1% |
| RAISE | 5bb | 25.6% |

**Tier `king_high` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 23.5% |
| FOLD | 0bb | 52.2% |
| RAISE | 5bb | 24.3% |

## C. Counterfeit / board interaction

### C10_QQ_88A_vs_cbet

**BB facing cbet, QQ on paired A-high**
- board: `8s8dAh`
- hero: `QsQd`

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

### C11_TT_T22_vs_cbet

**BB facing cbet, TT = top set + FH on T22**
- board: `Tc2d2s`
- hero: `TsTh`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 28.9% |
| CALL | 1.9bb | 64.7% |
| RAISE | 10.3bb | 6.4% |

**Hero tier 推定**: trips/set

**Tier `trips` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 27.4% |
| FOLD | 0bb | 0.0% |
| RAISE | 10.3bb | 72.6% |

**Tier `set` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 0.0% |
| FOLD | 0bb | 0.0% |
| RAISE | 10.3bb | 0.0% |

**Tier `fullhouse` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 7.5% |
| FOLD | 0bb | 0.0% |
| RAISE | 10.3bb | 92.5% |

**Tier `quads` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 91.6% |
| FOLD | 0bb | 0.0% |
| RAISE | 10.3bb | 8.4% |

### C9_A2s_227_vs_cbet

**BB facing cbet, A2s = trip 2 + A kicker**
- board: `2c2d7s`
- hero: `As2h`

**Aggregate actions (range 全体):**

| action | size | freq |
|---|---:|---:|
| FOLD | 0bb | 32.3% |
| CALL | 1.9bb | 45.1% |
| RAISE | 5bb | 22.6% |

**Hero tier 推定**: ?

**Tier `no_made_hand` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 16.6% |
| FOLD | 0bb | 60.3% |
| RAISE | 5bb | 23.2% |

**Tier `ace_high` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 57.7% |
| FOLD | 0bb | 0.0% |
| RAISE | 5bb | 42.3% |

**Tier `king_high` の行動分布:**

| action | size | freq |
|---|---:|---:|
| CALL | 1.9bb | 54.5% |
| FOLD | 0bb | 26.5% |
| RAISE | 5bb | 18.9% |
