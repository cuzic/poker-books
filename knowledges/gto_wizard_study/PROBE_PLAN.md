# Probe targets plan — drill audit + 境界 spot 検証

出力 JSON: `knowledges/gto_wizard_study/PROBE_TARGETS.json`

## サマリー

| 目的 | spec 数 | 内容 |
|------|--------:|------|
| (A) drill audit | 29 | drill が使うが dataset 未カバーの (flop, scenario) |
| (B) boundary validation | 18 | 板タイプ境界 spot で分類精度検証 |
| **合計** | **47** | |

## (A) drill audit targets (優先度順、drill 使用回数 = 重要度)

| priority | flop | scenario_type | drill cards | 例 |
|---------:|------|---------------|-----------:|-----|
| P3 | `7d4c2s` | 3BP | 3 | matcha-framework-3bet-pot-decisions/mf3bp_004, matcha-framework-3bet-pot-decisio |
| P3 | `JsTs4s` | SRP_flop | 3 | matcha-framework-srp-flop-decisions/mfsrpf_002, matcha-framework-srp-flop-decisi |
| P3 | `9s8d7c` | SRP_flop | 3 | matcha-framework-srp-flop-decisions/mfsrpf_003, matcha-framework-srp-flop-decisi |
| P3 | `9s8d7c` | 3BP | 2 | matcha-framework-3bet-pot-decisions/mf3bp_007, matcha-framework-3bet-pot-decisio |
| P3 | `As9d4c` | 4BP | 2 | matcha-framework-4bet-pot-decisions/mf4bp_006, matcha-framework-4bet-pot-decisio |
| P3 | `Js7s3h` | SRP_river | 2 | matcha-framework-srp-river-decisions/mfsrpr_011, matcha-framework-srp-river-deci |
| P3 | `9s8d7c` | SRP_turn | 2 | matcha-framework-srp-turn-decisions/mfsrpt_007, matcha-framework-srp-turn-decisi |
| P3 | `KsKd4c` | 3BP | 1 | matcha-framework-3bet-pot-decisions/mf3bp_009 |
| P3 | `7d4c2s` | 4BP | 1 | matcha-framework-4bet-pot-decisions/mf4bp_009 |
| P3 | `9s8d7c` | 4BP | 1 | matcha-framework-4bet-pot-decisions/mf4bp_011 |
| P3 | `KsKd4c` | 4BP | 1 | matcha-framework-4bet-pot-decisions/mf4bp_012 |
| P3 | `5d4c2s` | 4BP | 1 | matcha-framework-4bet-pot-decisions/mf4bp_020 |
| P3 | `QhJd9c` | SRP_flop | 1 | matcha-framework-srp-flop-decisions/mfsrpf_012 |
| P3 | `AsTd4c` | SRP_flop | 1 | matcha-framework-srp-flop-decisions/mfsrpf_013 |
| P3 | `KsKd4c` | SRP_flop | 1 | matcha-framework-srp-flop-decisions/mfsrpf_016 |
| P3 | `8s5d3c` | SRP_flop | 1 | matcha-framework-srp-flop-decisions/mfsrpf_017 |
| P3 | `9s8d7c` | SRP_river | 1 | matcha-framework-srp-river-decisions/mfsrpr_006 |
| P3 | `JsTs8s` | SRP_river | 1 | matcha-framework-srp-river-decisions/mfsrpr_013 |
| P3 | `KsKd4c` | SRP_river | 1 | matcha-framework-srp-river-decisions/mfsrpr_018 |
| P3 | `9c6d4h` | SRP_river | 1 | matcha-framework-srp-river-decisions/mfsrpr_021 |
| P3 | `8c5d3h` | SRP_river | 1 | matcha-framework-srp-river-decisions/mfsrpr_022 |
| P3 | `Js7s3h` | SRP_turn | 1 | matcha-framework-srp-turn-decisions/mfsrpt_005 |
| P3 | `Js7s3d` | SRP_turn | 1 | matcha-framework-srp-turn-decisions/mfsrpt_010 |
| P3 | `KsQs4c` | SRP_turn | 1 | matcha-framework-srp-turn-decisions/mfsrpt_011 |
| P3 | `Qc9d4h` | SRP_turn | 1 | matcha-framework-srp-turn-decisions/mfsrpt_012 |
| P3 | `Ts8d4c` | SRP_turn | 1 | matcha-framework-srp-turn-decisions/mfsrpt_013 |
| P3 | `8c7d3h` | SRP_turn | 1 | matcha-framework-srp-turn-decisions/mfsrpt_014 |
| P3 | `JsTs4c` | SRP_turn | 1 | matcha-framework-srp-turn-decisions/mfsrpt_017 |
| P3 | `Kh8h3c` | SRP_turn | 1 | matcha-framework-srp-turn-decisions/mfsrpt_020 |

## (B) 板タイプ境界 spot targets

MATCHA レンジ分布判定 (POLAR / MERGED / CONDENSED) の境界に位置する spots:

| boundary | flop | category | 検証目的 |
|----------|------|----------|---------|
| ace_high boundary | `as9d4c` | ace_high_dry | A-high dry |
| ace_high boundary | `astd4c` | ace_high_kicker | A-T-x, broadway |
| ace_high boundary | `astd9c` | ace_high_broadway | A-T-9 broadway |
| dry_high boundary | `ks8d2c` | dry_high_kicker | K8x、少し connectivity |
| dry_high boundary | `ks9d4c` | dry_high_mid | K9x、middle range |
| dry_high boundary | `kh9c5d` | merged_high | K9x rainbow、merged 寄り |
| dynamic vs medium | `9s8d7c` | dynamic_clear | 完全 connected straight 可 |
| dynamic vs medium | `9s8d6c` | dynamic_oneOff | 1 ギャップ、まだ dynamic 寄り |
| dynamic vs medium | `9s7d5c` | medium_dynamic | 2 ギャップ、grayzone |
| dynamic vs medium | `9s6d3c` | spread_medium | 3 ギャップ、もう dynamic でない |
| low_dry boundary | `7s4d2c` | very_low_dry | very low |
| low_dry boundary | `8s6d3h` | low_dynamic | ややconnected low |
| monotone vs 2-tone | `jsts4s` | monotone_3spade | 3-spade、明確 monotone |
| monotone vs 2-tone | `jsts4h` | two_tone | 2-spade、 FD あり |
| monotone vs 2-tone | `jstc4s` | two_tone_spread | JT 2-tone, 完全 2 tone |
| paired boundary | `kskd4c` | paired_high | K-paired |
| paired boundary | `kskd9c` | paired_high_connector | KK + 9 (TP draw) |
| paired boundary | `4s4d2c` | paired_low | low pair-bottom |

## probe 実行プラン (推定)

各 (flop, scenario_type) ペアに対し:
- SRP scenarios: GTO Wizard `Cash6mTest_6mNL100R2` 100bb
- 3BP / 4BP: 各 pot_type で対応
- MTT: `MTTGeneral_8m` (25 / 100 / 200bb)

API call estimation:
- (A) drill missing: 29 (flop, scenario_type) ペア
- (B) boundary: 18 flops × ~3 pot_types = ~54 ペア
- **合計: ~83 API calls**

各 API call で ~500-1000 rows (hand combos × bet sizes) 取得可能。
→ 期待 dataset 拡張: ~30,000-100,000 rows

## 次手

1. quota 確認: `scripts/gto_wizard_study/.token` の認証状態 + 残 quota
2. probe スクリプト準備: `PROBE_TARGETS.json` を input に `fetch_smart.py` で投入
3. データ統合: 既存 `aggregate_*.py` 流用 → dataset_unified_v2.csv に追記 (or 新 csv)
4. audit 再実行: `audit_drill_extensions.py` で match 率上昇を確認