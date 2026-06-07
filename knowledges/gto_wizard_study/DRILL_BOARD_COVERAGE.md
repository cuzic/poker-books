# drill board coverage — dataset 不足 boards のリスト

drill の decision_cards で使われている board のうち、
`dataset_unified_v2.csv` に含まれていない boards を抽出。
これらを probe で取得すれば drill 全体を audit 可能になる。

## サマリー
- dataset 内 unique flops: **20**
- drill 使用 unique flops: **22**
- カバー済: **2**
- **未カバー (probe 必要): 20**

## dataset の既存 flops (audit 可能)
- `7d5s2c` — drill 使用 0 回
- `8h7h5d` — drill 使用 0 回
- `8s5d3h` — drill 使用 0 回
- `8s7d5c` — drill 使用 0 回
- `9c6d4s` — drill 使用 0 回
- `9c8d6s` — drill 使用 0 回
- `9c9s2d` — drill 使用 0 回
- `as9c4d` — drill 使用 0 回
- `jd9d6c` — drill 使用 0 回
- `jh8s8d` — drill 使用 0 回
- `jh9c7s` — drill 使用 0 回
- `js7s3s` — drill 使用 4 回
- `ks7d2c` — drill 使用 56 回
- `kskd2c` — drill 使用 0 回
- `qh7s3c` — drill 使用 0 回
- `qh9h3h` — drill 使用 0 回
- `th9c7s` — drill 使用 0 回
- `ts8s4s` — drill 使用 0 回
- `ts9d8c` — drill 使用 0 回
- `ts9s7c` — drill 使用 0 回

## drill が使うが dataset に無い flops (probe 候補)

| flop | drill 使用回数 | 例 card |
|------|---:|---|
| `9s8d7c` | 9 | matcha-framework-3bet-pot-decisions/mf3bp_007 |
| `7d4c2s` | 4 | matcha-framework-3bet-pot-decisions/mf3bp_004 |
| `kskd4c` | 4 | matcha-framework-3bet-pot-decisions/mf3bp_009 |
| `jsts4s` | 3 | matcha-framework-srp-flop-decisions/mfsrpf_002 |
| `js7s3h` | 3 | matcha-framework-srp-river-decisions/mfsrpr_011 |
| `as9d4c` | 2 | matcha-framework-4bet-pot-decisions/mf4bp_006 |
| `5d4c2s` | 1 | matcha-framework-4bet-pot-decisions/mf4bp_020 |
| `qhjd9c` | 1 | matcha-framework-srp-flop-decisions/mfsrpf_012 |
| `astd4c` | 1 | matcha-framework-srp-flop-decisions/mfsrpf_013 |
| `8s5d3c` | 1 | matcha-framework-srp-flop-decisions/mfsrpf_017 |
| `jsts8s` | 1 | matcha-framework-srp-river-decisions/mfsrpr_013 |
| `9c6d4h` | 1 | matcha-framework-srp-river-decisions/mfsrpr_021 |
| `8c5d3h` | 1 | matcha-framework-srp-river-decisions/mfsrpr_022 |
| `js7s3d` | 1 | matcha-framework-srp-turn-decisions/mfsrpt_010 |
| `ksqs4c` | 1 | matcha-framework-srp-turn-decisions/mfsrpt_011 |
| `qc9d4h` | 1 | matcha-framework-srp-turn-decisions/mfsrpt_012 |
| `ts8d4c` | 1 | matcha-framework-srp-turn-decisions/mfsrpt_013 |
| `8c7d3h` | 1 | matcha-framework-srp-turn-decisions/mfsrpt_014 |
| `jsts4c` | 1 | matcha-framework-srp-turn-decisions/mfsrpt_017 |
| `kh8h3c` | 1 | matcha-framework-srp-turn-decisions/mfsrpt_020 |

## probe 優先度提案

drill 使用回数 多い順:

 1. `9s8d7c` (9 使用) — top 1 probe で drill 70% カバー
 2. `7d4c2s` (4 使用) — top 2 probe で drill 74% カバー
 3. `kskd4c` (4 使用) — top 3 probe で drill 78% カバー
 4. `jsts4s` (3 使用) — top 4 probe で drill 81% カバー
 5. `js7s3h` (3 使用) — top 5 probe で drill 84% カバー
 6. `as9d4c` (2 使用) — top 6 probe で drill 86% カバー
 7. `5d4c2s` (1 使用) — top 7 probe で drill 87% カバー
 8. `qhjd9c` (1 使用) — top 8 probe で drill 88% カバー
 9. `astd4c` (1 使用) — top 9 probe で drill 89% カバー
10. `8s5d3c` (1 使用) — top 10 probe で drill 90% カバー
11. `jsts8s` (1 使用) — top 11 probe で drill 91% カバー
12. `9c6d4h` (1 使用) — top 12 probe で drill 92% カバー
13. `8c5d3h` (1 使用) — top 13 probe で drill 93% カバー
14. `js7s3d` (1 使用) — top 14 probe で drill 94% カバー
15. `ksqs4c` (1 使用) — top 15 probe で drill 95% カバー
16. `qc9d4h` (1 使用) — top 16 probe で drill 96% カバー
17. `ts8d4c` (1 使用) — top 17 probe で drill 97% カバー
18. `8c7d3h` (1 使用) — top 18 probe で drill 98% カバー
19. `jsts4c` (1 使用) — top 19 probe で drill 99% カバー
20. `kh8h3c` (1 使用) — top 20 probe で drill 100% カバー

## probe scripts への接続

各 missing flop に対し:
1. SRP flop (BTN open vs BB call) を取得
2. SRP turn / river (代表 turn/river card 各 1 枚)
3. 3BP flop / turn / river
4. 4BP flop / turn / river

GTO Wizard API 形式: `Cash6mTest_6mNL100R2` (Cash 100bb) + `MTTGeneral_8m` (MTT)
(`project_gtow_api_v4_postflop` memory 参照)