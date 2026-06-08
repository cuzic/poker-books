# drill audit via probe data (high-level、per-action summary)

ロジック未知の検算者は、各カード裏面の reference 表を見て答えに辿れるが、
そもそも drill 推奨答え自体が GTO と一致するかの monetization audit。

## サマリー
- total cards: 99
- matched: 20
- accuracy: **15.0%**

## per-deck
| deck | total | matched | acc |
|------|---:|---:|---:|
| matcha-framework-3bet-pot-decisions | 20 | 2 | 0% |
| matcha-framework-4bet-pot-decisions | 20 | 3 | 0% |
| matcha-framework-srp-flop-decisions | 17 | 8 | 25% |
| matcha-framework-srp-river-decisions | 22 | 4 | 25% |
| matcha-framework-srp-turn-decisions | 20 | 3 | 0% |

## wrong predictions (top 20)
| deck | card | drill | GTO | freq | size | answer |
|------|------|-------|-----|---:|------|--------|
| matcha-framework-3bet-pot-decisions | mf3bp_007 | CALL | CHECK | 60% | 0 | コール (CR は overplay) |
| matcha-framework-3bet-pot-decisions | mf3bp_011 | RAISE | CHECK | 60% | 0 | チェックレイズ (stack off) |
| matcha-framework-4bet-pot-decisions | mf4bp_006 | FOLD | RAISE | 55% | 11.3 | FOLD (dry_A は KK でも厳しい) |
| matcha-framework-4bet-pot-decisions | mf4bp_011 | RAISE | CHECK | 60% | 0 | チェックレイズ |
| matcha-framework-4bet-pot-decisions | mf4bp_019 | FOLD | RAISE | 55% | 11.3 | FOLD |
| matcha-framework-srp-flop-decisions | mfsrpf_003 | BET | CHECK | 52% | 0 | ベット ミディアム (50%) or チェック (40/60) |
| matcha-framework-srp-flop-decisions | mfsrpf_007 | FOLD | CALL | 62% | 1.9 | FOLD |
| matcha-framework-srp-flop-decisions | mfsrpf_008 | RAISE | CALL | 62% | 1.9 | チェックレイズ |
| matcha-framework-srp-flop-decisions | mfsrpf_012 | BET | CHECK | 79% | 0 | ベット スモール (33%) または チェック |
| matcha-framework-srp-flop-decisions | mfsrpf_016 | FOLD | CALL | 53% | 1.9 | FOLD |
| matcha-framework-srp-flop-decisions | mfsrpf_017 | RAISE | FOLD | 58% | 0 | チェックレイズ |
| matcha-framework-srp-river-decisions | mfsrpr_006 | BET | CHECK | 52% | 0 | ベット オーバー (100-130%) |
| matcha-framework-srp-river-decisions | mfsrpr_012 | BET | FOLD | 57% | 0 | ベット ミディアム (66-75%) |
| matcha-framework-srp-river-decisions | mfsrpr_018 | FOLD | CALL | 53% | 1.9 | FOLD |
| matcha-framework-srp-turn-decisions | mfsrpt_005 | CHECK | FOLD | 57% | 0 | チェック (give up frequency 高) |
| matcha-framework-srp-turn-decisions | mfsrpt_007 | CALL | CHECK | 52% | 0 | コール (slowplay) |
| matcha-framework-srp-turn-decisions | mfsrpt_015 | FOLD | CALL | 62% | 1.9 | FOLD |