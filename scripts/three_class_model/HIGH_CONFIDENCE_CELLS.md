# HIGH-Confidence Postflop Decision Cells

Generated from 613,131 rows (175 spots).
HIGH confidence = IQR < 10%, n ≥ 30. These are 'instant decision' cells.

## Summary
- Attack HIGH cells: **126** cells
- Defense HIGH cells: **104** cells

## Attack (acting first / facing no bet)

BET主体 = 80%+ bet、CHECK主体 = <20% bet、MIX = 混合

### BET主体 セル (always bet)

| board | bucket | MV | DV | size | median bet | n |
|---|---|---|---|---|---:|---:|
| dynamic_2tone | best_hands | overpair | gutshot | small (≤33%) | 100% | 92 |
| dynamic_2tone | best_hands | overpair | oesd | small (≤33%) | 98% | 150 |
| dynamic_2tone | good_hands | overpair | gutshot | small (≤33%) | 100% | 88 |
| low_dry | good_hands | overpair | no_draw | big (≥85%) | 100% | 138 |
| unknown | best_hands | top_pair | no_draw | small (≤33%) | 99% | 73 |

### CHECK主体 セル (always check)

| board | bucket | MV | DV | size | median bet | n |
|---|---|---|---|---|---:|---:|
| dry_high | best_hands | fullhouse | no_draw | small (≤33%) | 0% | 342 |
| dry_high | best_hands | straight | no_draw | big (≥85%) | 0% | 312 |
| dry_high | best_hands | top_pair | gutshot | big (≥85%) | 0% | 33 |
| dry_high | best_hands | top_pair | oesd | big (≥85%) | 0% | 55 |
| dry_high | good_hands | ace_high | gutshot | big (≥85%) | 0% | 32 |
| dry_high | good_hands | low_pair | gutshot | big (≥85%) | 0% | 48 |
| dry_high | good_hands | low_pair | no_draw | big (≥85%) | 0% | 1478 |
| dry_high | good_hands | low_pair | oesd | big (≥85%) | 0% | 96 |
| dry_high | good_hands | low_pair | onecard_bdfd | big (≥85%) | 0% | 159 |
| dry_high | good_hands | low_pair | no_draw | small (≤33%) | 0% | 77 |
| dry_high | good_hands | second_pair | gutshot | big (≥85%) | 0% | 138 |
| dry_high | good_hands | second_pair | oesd | big (≥85%) | 0% | 166 |
| dry_high | good_hands | third_pair | gutshot | big (≥85%) | 0% | 104 |
| dry_high | good_hands | third_pair | oesd | big (≥85%) | 0% | 122 |
| dry_high | good_hands | top_pair | gutshot | big (≥85%) | 0% | 123 |
| dry_high | good_hands | top_pair | no_draw | big (≥85%) | 0% | 637 |
| dry_high | good_hands | top_pair | oesd | big (≥85%) | 0% | 103 |
| dry_high | good_hands | two_pair | no_draw | big (≥85%) | 0% | 127 |
| dry_high | trash_hands | ace_high | gutshot | big (≥85%) | 0% | 48 |
| dry_high | trash_hands | ace_high | no_draw | big (≥85%) | 0% | 686 |
| dry_high | trash_hands | ace_high | oesd | big (≥85%) | 0% | 33 |
| dry_high | trash_hands | king_high | no_draw | big (≥85%) | 0% | 313 |
| dry_high | trash_hands | low_pair | no_draw | big (≥85%) | 0% | 212 |
| dry_high | trash_hands | no_made_hand | combo_draw | big (≥85%) | 0% | 41 |
| dry_high | trash_hands | no_made_hand | flush_draw | big (≥85%) | 0% | 38 |
| dry_high | trash_hands | no_made_hand | oesd | big (≥85%) | 0% | 991 |
| dry_high | weak_hands | ace_high | gutshot | big (≥85%) | 0% | 379 |
| dry_high | weak_hands | ace_high | oesd | big (≥85%) | 0% | 192 |
| dry_high | weak_hands | king_high | gutshot | big (≥85%) | 0% | 124 |
| dry_high | weak_hands | low_pair | gutshot | big (≥85%) | 0% | 156 |
| dry_high | weak_hands | low_pair | no_draw | big (≥85%) | 0% | 2495 |
| dry_high | weak_hands | low_pair | oesd | big (≥85%) | 0% | 108 |
| dry_high | weak_hands | no_made_hand | combo_draw | big (≥85%) | 0% | 92 |
| dry_high | weak_hands | second_pair | no_draw | big (≥85%) | 0% | 117 |
| dry_high | weak_hands | third_pair | gutshot | big (≥85%) | 0% | 44 |
| dry_high | weak_hands | third_pair | no_draw | big (≥85%) | 0% | 493 |
| dry_high | weak_hands | third_pair | oesd | big (≥85%) | 0% | 35 |
| dynamic | best_hands | fullhouse | no_draw | big (≥85%) | 0% | 67 |
| dynamic | best_hands | fullhouse | no_draw | small (≤33%) | 0% | 60 |
| dynamic | best_hands | trips | gutshot | big (≥85%) | 0% | 58 |
| dynamic | best_hands | trips | no_draw | big (≥85%) | 0% | 136 |
| dynamic | best_hands | trips | oesd | big (≥85%) | 0% | 58 |
| dynamic | best_hands | trips | gutshot | small (≤33%) | 0% | 48 |
| dynamic | best_hands | trips | oesd | small (≤33%) | 0% | 30 |
| dynamic | good_hands | low_pair | gutshot | big (≥85%) | 0% | 293 |
| dynamic | good_hands | low_pair | no_draw | big (≥85%) | 0% | 153 |
| dynamic | good_hands | low_pair | oesd | big (≥85%) | 0% | 312 |
| dynamic | good_hands | low_pair | gutshot | small (≤33%) | 0% | 96 |
| dynamic | good_hands | low_pair | no_draw | small (≤33%) | 0% | 36 |
| dynamic | good_hands | low_pair | oesd | small (≤33%) | 0% | 72 |
| dynamic | good_hands | second_pair | no_draw | small (≤33%) | 0% | 998 |
| dynamic | good_hands | set | no_draw | big (≥85%) | 0% | 90 |
| dynamic | good_hands | set | no_draw | small (≤33%) | 0% | 42 |
| dynamic | good_hands | straight | no_draw | big (≥85%) | 0% | 1024 |
| dynamic | good_hands | straight | no_draw | small (≤33%) | 0% | 508 |
| dynamic | good_hands | third_pair | no_draw | small (≤33%) | 0% | 826 |
| dynamic | good_hands | two_pair | no_draw | big (≥85%) | 0% | 730 |
| dynamic | good_hands | two_pair | no_draw | small (≤33%) | 0% | 323 |
| dynamic | trash_hands | ace_high | gutshot | big (≥85%) | 0% | 168 |
| dynamic | trash_hands | ace_high | no_draw | big (≥85%) | 0% | 697 |
| dynamic | trash_hands | king_high | gutshot | big (≥85%) | 0% | 444 |
| dynamic | trash_hands | king_high | oesd | big (≥85%) | 0% | 83 |
| dynamic | trash_hands | low_pair | no_draw | big (≥85%) | 0% | 661 |
| dynamic | trash_hands | no_made_hand | oesd | big (≥85%) | 0% | 1034 |
| dynamic | trash_hands | second_pair | no_draw | big (≥85%) | 2% | 88 |
| dynamic | trash_hands | second_pair | no_draw | small (≤33%) | 0% | 96 |
| dynamic | trash_hands | third_pair | no_draw | big (≥85%) | 0% | 222 |
| dynamic | weak_hands | ace_high | oesd | big (≥85%) | 0% | 144 |
| dynamic | weak_hands | ace_high | twocards_bdfd | big (≥85%) | 0% | 330 |
| dynamic | weak_hands | ace_high | oesd | small (≤33%) | 0% | 64 |
| dynamic | weak_hands | king_high | oesd | big (≥85%) | 0% | 344 |
| dynamic | weak_hands | low_pair | gutshot | big (≥85%) | 0% | 280 |
| dynamic | weak_hands | low_pair | no_draw | big (≥85%) | 0% | 1916 |
| dynamic | weak_hands | low_pair | oesd | big (≥85%) | 0% | 63 |
| dynamic | weak_hands | low_pair | gutshot | small (≤33%) | 0% | 192 |
| dynamic | weak_hands | overpair | no_draw | big (≥85%) | 0% | 36 |
| dynamic | weak_hands | second_pair | gutshot | big (≥85%) | 0% | 114 |
| dynamic | weak_hands | second_pair | no_draw | big (≥85%) | 0% | 476 |
| dynamic | weak_hands | second_pair | no_draw | small (≤33%) | 0% | 270 |
| dynamic | weak_hands | straight | no_draw | small (≤33%) | 0% | 60 |
| dynamic | weak_hands | third_pair | gutshot | big (≥85%) | 0% | 120 |
| dynamic | weak_hands | third_pair | no_draw | big (≥85%) | 0% | 583 |
| dynamic | weak_hands | third_pair | gutshot | small (≤33%) | 0% | 102 |
| dynamic | weak_hands | third_pair | no_draw | small (≤33%) | 0% | 291 |
| dynamic | weak_hands | top_pair | gutshot | big (≥85%) | 0% | 84 |
| dynamic | weak_hands | top_pair | no_draw | big (≥85%) | 0% | 480 |
| dynamic | weak_hands | top_pair | no_draw | small (≤33%) | 0% | 243 |
| dynamic | weak_hands | two_pair | no_draw | big (≥85%) | 0% | 90 |
| dynamic | weak_hands | two_pair | no_draw | small (≤33%) | 0% | 133 |
| dynamic_2tone | good_hands | low_pair | onecard_bdfd | big (≥85%) | 0% | 86 |
| dynamic_2tone | good_hands | low_pair | gutshot | small (≤33%) | 0% | 108 |
| dynamic_2tone | weak_hands | ace_high | twocards_bdfd | big (≥85%) | 0% | 41 |
| dynamic_2tone | weak_hands | king_high | twocards_bdfd | big (≥85%) | 2% | 30 |
| dynamic_2tone | weak_hands | low_pair | gutshot | big (≥85%) | 0% | 39 |
| dynamic_2tone | weak_hands | low_pair | no_draw | big (≥85%) | 0% | 315 |
| dynamic_2tone | weak_hands | low_pair | gutshot | small (≤33%) | 0% | 72 |
| dynamic_2tone | weak_hands | low_pair | no_draw | small (≤33%) | 0% | 297 |
| dynamic_2tone | weak_hands | third_pair | no_draw | small (≤33%) | 4% | 132 |
| low_dry | weak_hands | low_pair | no_draw | big (≥85%) | 0% | 291 |
| paired | best_hands | fullhouse | no_draw | big (≥85%) | 0% | 149 |
| paired | best_hands | second_pair | flush_draw | big (≥85%) | 0% | 33 |
| paired | best_hands | second_pair | no_draw | big (≥85%) | 0% | 307 |
| paired | best_hands | trips | no_draw | big (≥85%) | 0% | 650 |
| paired | best_hands | underpair | no_draw | big (≥85%) | 0% | 144 |
| paired | good_hands | king_high | no_draw | big (≥85%) | 0% | 229 |
| paired | good_hands | king_high | nut_flush_draw | big (≥85%) | 0% | 50 |
| paired | good_hands | no_made_hand | flush_draw | big (≥85%) | 0% | 51 |
| paired | good_hands | no_made_hand | gutshot | big (≥85%) | 0% | 60 |
| paired | good_hands | second_pair | no_draw | big (≥85%) | 0% | 531 |
| paired | good_hands | third_pair | no_draw | big (≥85%) | 0% | 825 |
| paired | trash_hands | no_made_hand | flush_draw | big (≥85%) | 0% | 63 |
| paired | trash_hands | no_made_hand | gutshot | big (≥85%) | 0% | 285 |
| paired | trash_hands | no_made_hand | no_draw | big (≥85%) | 0% | 1950 |
| paired | trash_hands | no_made_hand | oesd | big (≥85%) | 0% | 79 |
| paired | weak_hands | king_high | no_draw | big (≥85%) | 0% | 461 |
| paired | weak_hands | low_pair | no_draw | big (≥85%) | 0% | 123 |
| paired | weak_hands | no_made_hand | flush_draw | big (≥85%) | 0% | 133 |
| paired | weak_hands | no_made_hand | gutshot | big (≥85%) | 0% | 75 |
| paired | weak_hands | no_made_hand | no_draw | big (≥85%) | 0% | 1482 |
| paired | weak_hands | no_made_hand | flush_draw | small (≤33%) | 0% | 53 |
| paired | weak_hands | third_pair | no_draw | big (≥85%) | 0% | 86 |

## Defense (facing a bet)

### FOLD modal セル (always fold)

| board | bucket | MV | DV | bet_size | F | C | R | n |
|---|---|---|---|---|---:|---:|---:|---:|
| dry_high | trash_hands | ace_high | no_draw | small (≤33%) | 100% | 0% | 0% | 147 |
| dry_high | trash_hands | king_high | no_draw | mid (50%) | 100% | 0% | 0% | 98 |
| dry_high | trash_hands | king_high | no_draw | small (≤33%) | 100% | 0% | 0% | 233 |
| dry_high | trash_hands | no_made_hand | no_draw | mid (50%) | 100% | 0% | 0% | 938 |
| dry_high | trash_hands | no_made_hand | onecard_bdfd | mid (50%) | 98% | 2% | 0% | 225 |
| dry_high | trash_hands | no_made_hand | twocards_bdfd | mid (50%) | 97% | 3% | 0% | 231 |
| dry_high | trash_hands | no_made_hand | no_draw | small (≤33%) | 88% | 9% | 3% | 6442 |
| dry_high | weak_hands | low_pair | no_draw | mid (50%) | 92% | 8% | 0% | 36 |
| dry_high | weak_hands | no_made_hand | no_draw | mid (50%) | 83% | 13% | 4% | 286 |
| dynamic | good_hands | ace_high | no_draw | mid (50%) | 100% | 0% | 0% | 38 |
| dynamic | trash_hands | ace_high | no_draw | mid (50%) | 100% | 0% | 0% | 79 |
| dynamic | trash_hands | king_high | no_draw | mid (50%) | 100% | 0% | 0% | 150 |
| dynamic | trash_hands | low_pair | no_draw | small (≤33%) | 100% | 0% | 0% | 45 |
| dynamic | trash_hands | no_made_hand | gutshot | mid (50%) | 90% | 8% | 2% | 457 |
| dynamic | trash_hands | no_made_hand | no_draw | mid (50%) | 100% | 0% | 0% | 409 |
| dynamic | trash_hands | no_made_hand | oesd | mid (50%) | 86% | 12% | 2% | 66 |
| dynamic | trash_hands | no_made_hand | twocards_bdfd | mid (50%) | 100% | 0% | 0% | 108 |
| dynamic | trash_hands | no_made_hand | gutshot | small (≤33%) | 100% | 0% | 0% | 137 |
| dynamic | trash_hands | no_made_hand | no_draw | small (≤33%) | 100% | 0% | 0% | 647 |
| dynamic | weak_hands | ace_high | no_draw | mid (50%) | 96% | 4% | 0% | 300 |
| dynamic | weak_hands | king_high | no_draw | mid (50%) | 100% | 0% | 0% | 205 |
| dynamic | weak_hands | king_high | twocards_bdfd | mid (50%) | 83% | 17% | 0% | 69 |
| dynamic | weak_hands | low_pair | no_draw | mid (50%) | 100% | 0% | 0% | 120 |
| dynamic | weak_hands | no_made_hand | no_draw | mid (50%) | 100% | 0% | 0% | 31 |
| dynamic | weak_hands | third_pair | no_draw | small (≤33%) | 92% | 8% | 0% | 37 |
| dynamic_2tone | trash_hands | ace_high | no_draw | mid (50%) | 100% | 0% | 0% | 56 |
| dynamic_2tone | trash_hands | ace_high | onecard_bdfd | mid (50%) | 100% | 0% | 0% | 36 |
| dynamic_2tone | trash_hands | ace_high | gutshot | small (≤33%) | 89% | 8% | 3% | 42 |
| dynamic_2tone | trash_hands | king_high | no_draw | mid (50%) | 100% | 0% | 0% | 130 |
| dynamic_2tone | trash_hands | king_high | onecard_bdfd | mid (50%) | 100% | 0% | 0% | 36 |
| dynamic_2tone | trash_hands | no_made_hand | gutshot | mid (50%) | 83% | 13% | 5% | 441 |
| dynamic_2tone | trash_hands | no_made_hand | no_draw | mid (50%) | 100% | 0% | 0% | 286 |
| dynamic_2tone | trash_hands | no_made_hand | onecard_bdfd | mid (50%) | 94% | 5% | 1% | 166 |
| dynamic_2tone | trash_hands | no_made_hand | twocards_bdfd | mid (50%) | 96% | 3% | 0% | 39 |
| dynamic_2tone | trash_hands | no_made_hand | no_draw | small (≤33%) | 100% | 0% | 0% | 430 |
| dynamic_2tone | trash_hands | no_made_hand | onecard_bdfd | small (≤33%) | 91% | 9% | 0% | 288 |
| dynamic_2tone | weak_hands | ace_high | no_draw | mid (50%) | 97% | 3% | 0% | 202 |
| dynamic_2tone | weak_hands | king_high | no_draw | mid (50%) | 100% | 0% | 0% | 94 |
| dynamic_2tone | weak_hands | low_pair | no_draw | mid (50%) | 100% | 0% | 0% | 47 |
| dynamic_2tone | weak_hands | low_pair | onecard_bdfd | mid (50%) | 85% | 15% | 0% | 60 |
| dynamic_2tone | weak_hands | no_made_hand | onecard_bdfd | mid (50%) | 85% | 15% | 0% | 32 |
| dynamic_2tone | weak_hands | third_pair | no_draw | small (≤33%) | 85% | 15% | 0% | 40 |
| low_dry | trash_hands | king_high | no_draw | mid (50%) | 100% | 0% | 0% | 87 |
| low_dry | trash_hands | no_made_hand | no_draw | mid (50%) | 98% | 1% | 0% | 1639 |
| low_dry | trash_hands | no_made_hand | onecard_bdfd | mid (50%) | 88% | 5% | 7% | 378 |
| low_dry | trash_hands | no_made_hand | twocards_bdfd | mid (50%) | 90% | 3% | 6% | 340 |
| low_dry | weak_hands | king_high | no_draw | mid (50%) | 83% | 15% | 2% | 1089 |
| low_dry | weak_hands | low_pair | no_draw | mid (50%) | 100% | 0% | 0% | 72 |
| low_dry | weak_hands | no_made_hand | no_draw | mid (50%) | 90% | 8% | 3% | 926 |
| paired | trash_hands | no_made_hand | no_draw | small (≤33%) | 89% | 6% | 5% | 1663 |

### CALL modal セル (always call)

| board | bucket | MV | DV | bet_size | F | C | R | n |
|---|---|---|---|---|---:|---:|---:|---:|
| dry_high | best_hands | second_pair | flush_draw | small (≤33%) | 0% | 91% | 9% | 98 |
| dry_high | good_hands | ace_high | nut_flush_draw | mid (50%) | 0% | 96% | 4% | 32 |
| dry_high | good_hands | ace_high | onecard_bdfd | small (≤33%) | 0% | 92% | 8% | 101 |
| dry_high | good_hands | ace_high | twocards_bdfd | small (≤33%) | 0% | 98% | 2% | 72 |
| dry_high | good_hands | king_high | nut_flush_draw | small (≤33%) | 0% | 86% | 14% | 70 |
| dry_high | good_hands | second_pair | no_draw | mid (50%) | 4% | 91% | 5% | 494 |
| dry_high | good_hands | second_pair | onecard_bdfd | mid (50%) | 0% | 93% | 7% | 145 |
| dry_high | good_hands | second_pair | twocards_bdfd | mid (50%) | 0% | 100% | 0% | 78 |
| dry_high | good_hands | third_pair | onecard_bdfd | mid (50%) | 6% | 91% | 3% | 93 |
| dry_high | good_hands | third_pair | twocards_bdfd | mid (50%) | 0% | 98% | 2% | 104 |
| dry_high | good_hands | top_pair | twocards_bdfd | mid (50%) | 0% | 93% | 7% | 79 |
| dry_high | good_hands | top_pair | no_draw | small (≤33%) | 0% | 94% | 6% | 635 |
| dry_high | good_hands | top_pair | twocards_bdfd | small (≤33%) | 0% | 95% | 5% | 106 |
| dry_high | good_hands | underpair | onecard_bdfd | mid (50%) | 0% | 100% | 0% | 30 |
| dry_high | good_hands | underpair | no_draw | small (≤33%) | 0% | 91% | 9% | 438 |
| dry_high | weak_hands | third_pair | onecard_bdfd | small (≤33%) | 0% | 88% | 12% | 78 |
| dynamic | good_hands | ace_high | gutshot | small (≤33%) | 0% | 97% | 3% | 119 |
| dynamic | good_hands | second_pair | twocards_bdfd | mid (50%) | 1% | 95% | 3% | 82 |
| dynamic | good_hands | second_pair | gutshot | small (≤33%) | 0% | 98% | 2% | 91 |
| dynamic | good_hands | second_pair | oesd | small (≤33%) | 0% | 95% | 5% | 36 |
| dynamic | good_hands | second_pair | twocards_bdfd | small (≤33%) | 0% | 100% | 0% | 52 |
| dynamic | good_hands | third_pair | twocards_bdfd | mid (50%) | 0% | 98% | 2% | 50 |
| dynamic | good_hands | third_pair | gutshot | small (≤33%) | 12% | 88% | 0% | 86 |
| dynamic | good_hands | third_pair | oesd | small (≤33%) | 0% | 98% | 2% | 48 |
| dynamic | good_hands | top_pair | twocards_bdfd | mid (50%) | 0% | 91% | 9% | 86 |
| dynamic | good_hands | top_pair | twocards_bdfd | small (≤33%) | 0% | 98% | 1% | 56 |
| dynamic_2tone | good_hands | ace_high | gutshot | small (≤33%) | 0% | 98% | 2% | 82 |
| dynamic_2tone | good_hands | second_pair | flush_draw | mid (50%) | 0% | 97% | 3% | 35 |
| dynamic_2tone | good_hands | second_pair | gutshot | mid (50%) | 2% | 90% | 8% | 130 |
| dynamic_2tone | good_hands | second_pair | onecard_bdfd | mid (50%) | 14% | 84% | 3% | 127 |
| dynamic_2tone | good_hands | second_pair | gutshot | small (≤33%) | 4% | 91% | 5% | 81 |
| dynamic_2tone | good_hands | second_pair | oesd | small (≤33%) | 0% | 96% | 4% | 39 |
| dynamic_2tone | good_hands | second_pair | onecard_bdfd | small (≤33%) | 10% | 90% | 0% | 90 |
| dynamic_2tone | good_hands | third_pair | oesd | mid (50%) | 0% | 87% | 13% | 147 |
| dynamic_2tone | good_hands | third_pair | gutshot | small (≤33%) | 11% | 87% | 2% | 84 |
| dynamic_2tone | good_hands | third_pair | oesd | small (≤33%) | 0% | 95% | 5% | 48 |
| dynamic_2tone | good_hands | third_pair | onecard_bdfd | small (≤33%) | 0% | 100% | 0% | 42 |
| dynamic_2tone | good_hands | top_pair | onecard_bdfd | mid (50%) | 0% | 90% | 10% | 99 |
| dynamic_2tone | good_hands | top_pair | twocards_bdfd | mid (50%) | 0% | 91% | 9% | 43 |
| dynamic_2tone | good_hands | top_pair | onecard_bdfd | small (≤33%) | 0% | 99% | 1% | 63 |
| dynamic_2tone | weak_hands | no_made_hand | flush_draw | mid (50%) | 0% | 90% | 10% | 32 |
| dynamic_2tone | weak_hands | second_pair | onecard_bdfd | mid (50%) | 5% | 88% | 6% | 38 |
| dynamic_2tone | weak_hands | third_pair | twocards_bdfd | mid (50%) | 3% | 94% | 3% | 32 |
| low_dry | good_hands | ace_high | nut_flush_draw | mid (50%) | 0% | 94% | 6% | 54 |
| low_dry | good_hands | second_pair | flush_draw | mid (50%) | 0% | 87% | 13% | 66 |
| low_dry | good_hands | second_pair | onecard_bdfd | mid (50%) | 0% | 90% | 10% | 280 |
| low_dry | good_hands | second_pair | twocards_bdfd | mid (50%) | 0% | 96% | 4% | 150 |
| low_dry | good_hands | third_pair | onecard_bdfd | mid (50%) | 9% | 88% | 3% | 135 |
| low_dry | good_hands | third_pair | twocards_bdfd | mid (50%) | 0% | 97% | 3% | 197 |
| low_dry | good_hands | underpair | onecard_bdfd | mid (50%) | 0% | 90% | 10% | 48 |
| low_dry | weak_hands | third_pair | onecard_bdfd | mid (50%) | 16% | 83% | 1% | 48 |

### RAISE modal セル (always raise)

| board | bucket | MV | DV | bet_size | F | C | R | n |
|---|---|---|---|---|---:|---:|---:|---:|
| dynamic | good_hands | overpair | gutshot | mid (50%) | 0% | 0% | 100% | 36 |
| dynamic_2tone | good_hands | overpair | gutshot | mid (50%) | 0% | 6% | 94% | 36 |
| low_dry | best_hands | top_pair | no_draw | mid (50%) | 0% | 4% | 96% | 40 |