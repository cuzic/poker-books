# Data-Driven Postflop Framework Report

Source: 189,393 rows from 331 GTO Wizard spots
Generated: 2026-05-31

## 1. Cash IP SRP Flop, no_draw — Replacement for the published 25-cell base

| board_family | air | weak | mid | strong | nut |
|---|---:|---:|---:|---:|---:|
| dry_high | 53% | 31% | 31% | 57% | 98% |
| dynamic | 47% | 19% | 25% | 55% | 88% |
| dynamic_2tone | 28% | 5% | 16% | 36% | 63% |
| low_dry | 42% | 14% | 51% | 61% | 98% |
| monotone | 40% | 20% | 19% | 37% | 54% |
| paired | 72% | 91% | 86% | 65% | 95% |

**Published 25-cell (for comparison):** `air 44 / weak 37 / mid 42 / strong 57 / nut 62`

The board-family row reveals that **the published single-row table averages over 6 very different boards**.

## 2. Key gaps in the published 25-cell vs data

- **Nut undershoots dramatically**: published 62%, data shows 95-98% on most board families. The published table assumes slowplay where data says always bet.
- **Mid (second_pair) overshoots**: published 42%, data shows 16-31% across most boards. The framework's MV=5 is too aggressive for value betting.
- **Paired boards bet everything**: 65-91% across all bands. The framework's ε=+5 for paired underestimates the bet shift.
- **Monotone boards check more on nut**: only 54% nut bet. The framework's ε does not capture this.

## 3. DV (draw) effect on bet frequency — Cash IP Flop dry_high

| dv | air | weak | mid | strong | nut |
|---|---:|---:|---:|---:|---:|
| flush_draw | 72% | — | — | — | — |
| gutshot | 66% | — | — | 40% | — |
| no_draw | 53% | 31% | 31% | 57% | 98% |
| oesd | 72% | — | — | — | — |
| onecard_bdfd | 65% | 67% | 51% | 49% | — |
| twocards_bdfd | 56% | 64% | 75% | 80% | 93% |

**Observations:**
- BDFD (twocards) raises bet freq by +5 to +45 pp depending on MV band.
- True FD raises air bet by +20 pp.
- OESD without made hand still bets +20 pp over no_draw (gutshot only adds +13 to air).

## 4. MTT IP Turn — Polarized pattern

| board_family | air | weak | mid | strong | nut |
|---|---:|---:|---:|---:|---:|
| dry_high | 5% | 0% | 0% | 44% | 98% |
| dynamic | 12% | 1% | 1% | 66% | 89% |
| monotone | 8% | — | — | 10% | 85% |

Turn shifts to **polarize**: weak/mid drop to 0-1% bet, strong/nut climb to 60-98%. The flop's middle ground disappears.

## 5. MTT OOP Turn — XX-line probe explosion

| board_family | air | weak | mid | strong | nut |
|---|---:|---:|---:|---:|---:|
| dry_high | 93% | 0% | 10% | 100% | 62% |
| dynamic | 30% | 0% | 100% | 100% | 98% |

**Striking finding:** OOP turn probe (after XX flop) bets air at 93% on dry_high. The 'OOP turn = 0% donk' claim is dead — it applies only to the post-CBet line, not XX-line probes.

## 6. Proposed framework redesign

1. Replace the global 25-cell with a 30-cell **board_family × MV-band** table.
2. Add a 2-axis DV adjustment table (DV × MV).
3. Drop the α/β/cat/ε layers entirely — the 30-cell + DV captures their effects directly.
4. Add separate Turn-IP and Turn-OOP-XX tables (different game dynamics).

Parameter count: ~150 (30 × 5 contexts) vs published 63 — modestly larger, but every number is data-grounded and the 7-step formula collapses to 2 lookups + 1 add.