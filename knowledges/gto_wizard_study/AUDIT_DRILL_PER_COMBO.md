# drill audit per-combo (1326 combo enumeration、GTO Wizard API データ)

## サマリー
- total cards: 99, matched: 15 (15.2%)
- accuracy (drill_action == gto_best per-combo): **26.7%**
- avg loss / decision: **0.462 BB**
- huge mistakes (>5 BB): 1 (6.7%)
- avg huge_loss: **5.023 BB**

## per-deck
| deck | n | matched | acc | avg_loss | huge |
|------|---:|---:|---:|---:|---:|
| matcha-framework-3bet-pot-decisions | 20 | 0 | N/A | N/A | N/A |
| matcha-framework-4bet-pot-decisions | 20 | 0 | N/A | N/A | N/A |
| matcha-framework-srp-flop-decisions | 17 | 8 | 38% | 0.64BB | 1 |
| matcha-framework-srp-river-decisions | 22 | 4 | 25% | 0.03BB | 0 |
| matcha-framework-srp-turn-decisions | 20 | 3 | 0% | 0.57BB | 0 |

## worst predictions (top 20)
| deck | card | hand | drill | drill_ev | GTO | GTO_ev | loss | answer |
|------|------|------|-------|--------:|-----|-------:|----:|--------|
| matcha-framework-srp-flop | mfsrpf_007 | AhQd | FOLD | -0.0 | CALL | 5.023 | 5.023 | FOLD |
| matcha-framework-srp-turn | mfsrpt_007 | 8s7d | CALL | 0.0 | CHECK | 0.868 | 0.868 | コール (slowplay) |
| matcha-framework-srp-turn | mfsrpt_015 | AhKs | FOLD | -0.0 | CALL | 0.746 | 0.746 | FOLD |
| matcha-framework-srp-turn | mfsrpt_005 | KhKd | CHECK | 0.0 | CALL | 0.096 | 0.096 | チェック (give up frequency 高) |
| matcha-framework-srp-rive | mfsrpr_011 | AdQh | FOLD | 0.0 | CALL | 0.084 | 0.084 | FOLD |
| matcha-framework-srp-flop | mfsrpf_012 | KsKd | BET | 3.151 | CHECK | 3.221 | 0.07 | ベット スモール (33%) または チェック |
| matcha-framework-srp-rive | mfsrpr_006 | Jh6h | BET | 1.324 | CHECK | 1.343 | 0.019 | ベット オーバー (100-130%) |
| matcha-framework-srp-flop | mfsrpf_017 | AhAd | RAISE | 10.526 | CALL | 10.536 | 0.01 | チェックレイズ |
| matcha-framework-srp-flop | mfsrpf_003 | KhKs | BET | 2.493 | CHECK | 2.502 | 0.008 | ベット ミディアム (50%) or チェック (40/60) |
| matcha-framework-srp-flop | mfsrpf_008 | Th6h | RAISE | 0.0 | FOLD | 0.0 | 0.0 | チェックレイズ |
| matcha-framework-srp-rive | mfsrpr_012 | Ks8s | BET | 0.0 | FOLD | -0.0 | -0.0 | ベット ミディアム (66-75%) |