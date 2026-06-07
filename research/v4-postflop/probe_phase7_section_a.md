# Probe Phase 7 — Section A 既存データ分析結果

## A1: MTT200 HIGH SPR 分析

対象: N_mtt200_river (6,486 rows)
      N_mtt200_turn  (6,768 rows)

### Per-board huge_loss (MTT200)

| scenario | board_label | n | acc | huge_loss |
|---|---|---:|---:|---:|
| N_mtt200_river | d2t_T97 | 1,081 | 76.4% | 6.42 |
| N_mtt200_river | dry_K72 | 1,081 | 82.2% | 5.68 |
| N_mtt200_river | dyn_T97 | 1,081 | 74.7% | 3.77 |
| N_mtt200_river | low_853 | 1,081 | 78.3% | 4.12 |
| N_mtt200_river | mono_Js | 1,081 | 80.9% | 6.12 |
| N_mtt200_river | pair_KK2 | 1,081 | 87.8% | 6.93 |
| N_mtt200_turn | d2t_T97 | 1,128 | 80.3% | 1.81 |
| N_mtt200_turn | dry_K72 | 1,128 | 64.8% | 1.13 |
| N_mtt200_turn | dyn_T97 | 1,128 | 76.6% | 1.58 |
| N_mtt200_turn | low_853 | 1,128 | 67.5% | 2.70 |
| N_mtt200_turn | mono_Js | 1,128 | 73.3% | 1.53 |
| N_mtt200_turn | pair_KK2 | 1,128 | 68.6% | 0.58 |

### MTT200 river での UDG誤判定パターン

最頻 mismatch (UDG action vs GTO best_action):

| mv_cat | board_family | UDG | GTO best | count |
|---|---|---|---|---:|
| second_pair | low_dry | FOLD | CALL | 89 |
| fullhouse | low_dry | CALL | RAISE | 83 |
| fullhouse | paired | CALL | RAISE | 27 |
| fullhouse | monotone | CALL | RAISE | 25 |
| two_pair | dry_high | CALL | RAISE | 18 |
| king_high | low_dry | FOLD | RAISE | 16 |
| straight | dynamic | CALL | RAISE | 16 |
| straight | dynamic_2tone | CALL | RAISE | 16 |
| set | dry_high | CALL | RAISE | 15 |
| straight | monotone | CALL | RAISE | 9 |
| top_pair | monotone | FOLD | RAISE | 9 |
| ace_high | low_dry | FOLD | RAISE | 9 |
| straight | dynamic | FOLD | CALL | 8 |
| second_pair | monotone | FOLD | CALL | 6 |
| overpair | low_dry | FOLD | CALL | 3 |
| set | dynamic | FOLD | CALL | 3 |
| top_pair | monotone | FOLD | CALL | 3 |
| quads | low_dry | CALL | RAISE | 2 |
| quads | monotone | CALL | RAISE | 1 |
| quads | paired | CALL | RAISE | 1 |

### 推定原因 (要 v3 設計指針)
HIGH SPR (MTT200) で UDG v2 の `TIE → CALL` rule が overpressed。
deep stack では bluff catcher の閾値が tighter になる傾向 (read protect)。
→ v3 改善案: SPR=HIGH × TIE × BIG bet で FOLD を増やす

---

## A2: R1 (IP river allin) 分析

対象: R1_past (29,531 rows) — BTN IP defender vs BB allin

UDG v2 acc: 92.1%
huge_loss: 6.29 BB (1,367 rows)

### Per-board breakdown

| board_family | n | acc | huge_loss |
|---|---:|---:|---:|
| dry_high | 5,684 | 91.9% | 3.93 |
| dynamic | 5,571 | 91.9% | 10.20 |
| dynamic_2tone | 4,230 | 92.6% | 8.69 |
| low_dry | 1,530 | 82.2% | 3.09 |
| monotone | 7,254 | 93.7% | 5.82 |
| paired | 5,262 | 92.7% | 1.81 |

### UDG 誤判定の頻発パターン

| mv_cat | bucket | UDG | GTO best | count |
|---|---|---|---|---:|
| flush | weak_hands | FOLD | CALL | 192 |
| top_pair | weak_hands | FOLD | CALL | 145 |
| top_pair | trash_hands | FOLD | CALL | 125 |
| second_pair | weak_hands | FOLD | CALL | 112 |
| trips | weak_hands | CALL | FOLD | 58 |
| trips | weak_hands | FOLD | CALL | 53 |
| straight | weak_hands | FOLD | CALL | 43 |
| third_pair | weak_hands | FOLD | CALL | 34 |
| overpair | weak_hands | FOLD | CALL | 34 |
| third_pair | trash_hands | FOLD | RAISE | 27 |
| two_pair | weak_hands | CALL | FOLD | 26 |
| second_pair | trash_hands | FOLD | RAISE | 26 |
| fullhouse | weak_hands | FOLD | CALL | 23 |
| set | weak_hands | FOLD | CALL | 21 |
| overpair | trash_hands | FOLD | RAISE | 18 |

### 推定原因
R1 = BTN IP が BB の river allin shove を受ける line。
UDG v2 は OOP defender 想定 → IP の equity bucket 解釈がズレる可能性。
→ v3 改善案: hero_role (IP/OOP) を tier に追加、または IP modifier 専用 rule

---

## A3: Per-combo blocker effect

### Ace blocker on monotone board

hero が Ax of suit を持つ場合、opp の nut flush combos は半減 → bluff catch wider 期待

With A blocker (n=1,675): GTO CALL = **50.9%**
Without (n=28,827): GTO CALL = **23.7%**

差: **+27.2pp**

### King blocker on paired board (KK2)

With K blocker (n=3,254): GTO CALL = **75.9%**
Without (n=34,864): GTO CALL = **34.0%**
差: **+41.9pp**

### 結論
blocker effect が GTO action freq に与える影響を定量化。
UDG v3 で `blocker_aware` tier を追加すべきか判断材料。

---

## A4: 4BP board variance

対象: 4BP flop scenarios (n=28,224 rows)

### Per-board breakdown (4BP flop)

| board_label | board_family | n | UDG acc | UDG huge | v1 huge |
|---|---|---:|---:|---:|---:|
| d2t_875 | dynamic_2tone | 1,176 | 26.9% | 7.17 | 4.54 |
| d2t_J96 | dynamic_2tone | 1,176 | 26.0% | 10.10 | 6.11 |
| d2t_T97 | dynamic_2tone | 2,352 | 39.2% | 8.04 | 4.79 |
| dry_A94 | dry_high | 1,176 | 40.1% | 3.49 | 5.97 |
| dry_K72 | dry_high | 2,352 | 44.6% | 3.78 | 5.45 |
| dry_Q73 | dry_high | 1,176 | 35.4% | 3.99 | 5.83 |
| dyn_875 | dynamic | 1,176 | 24.8% | 7.38 | 4.27 |
| dyn_986 | dynamic | 1,176 | 32.3% | 8.37 | 5.14 |
| dyn_T97 | dynamic | 2,352 | 34.9% | 8.70 | 4.78 |
| low_752 | low_dry | 1,176 | 38.4% | 5.15 | 5.51 |
| low_853 | low_dry | 2,352 | 38.0% | 4.52 | 5.09 |
| low_964 | low_dry | 1,176 | 40.6% | 4.99 | 5.09 |
| mono_Js | monotone | 2,352 | 46.2% | 5.31 | 1.71 |
| mono_Qh | monotone | 1,176 | 53.3% | 7.08 | 1.57 |
| mono_Ts | monotone | 1,176 | 48.7% | 5.66 | 1.88 |
| pair_992 | paired | 1,176 | 33.4% | 3.24 | 4.83 |
| pair_J88 | paired | 1,176 | 33.7% | 4.29 | 5.89 |
| pair_KK2 | paired | 2,352 | 27.6% | 2.76 | 4.74 |

### 推定構造 (要 phase 7 fetch で検証)
MERGED tier 内で Ace-high board は opp の AA/AK が直接 hit するため:
- 期待: dry_A94 は **opp value heavier** で defender tighten
- 期待: dry_K72 は AA overpair が標準、value 構造同等
- 期待: low_dry (8s5d3h) は **opp range 全部 miss** で defender widest

→ Section B (B1: 4BP flop board variance) で 18 boards × 4BP fetch して検証

---

