# UDG (Universal Defense Grid) v1 — Results Summary

## Overall

| 指標 | v1 (11 公式) | UDG v1 | 削減 |
|------|------------:|-------:|----:|
| huge_loss (avg) | 15.75 BB | **10.27 BB** | **-35%** |
| acc (avg) | 75-85% | 69.7% | -10pp |
| 暗記項目 | ~165 分岐 | ~**30** items | **-82%** |

## 暗記コスト構成

UDG の **暗記すべき総項目**:

- **Layer 1 (3 tier 関数)**: ~10 items
  - board_polar_tier: POLAR/MERGED/MID の board family 分類 (6 family を 3 tier)
  - hand_strength_tier: 6 階層 (NUT_MADE/STRONG/TWO_PAIR/PAIR/MID_PAIR/AIR + DRAW dv)
  - bet_size_tier: 4 階層 (SMALL/MED/BIG/ALLIN)
- **Layer 2 (universal rule)**: 7 ルール
- **Layer 3 (modifiers)**: 6 種類 × 平均 2-3 例外 = ~15 items

→ **計 ~30 items** vs 11 公式 × 平均 15 分岐 = ~165 items

## Per-scenario verdict (huge_loss)

### ✓ UDG が v1 を上回る (14 scenarios)

| scenario | v1 | UDG | 改善 |
|----------|---:|----:|----:|
| A_cash_3bp_river | 23.1 | 11.1 | -52% |
| B_river | 19.5 | 7.3 | **-62%** |
| N_btn_sb_river | 14.0 | 5.7 | -59% |
| N_bvb_srp_river | 9.9 | 6.6 | -33% |
| N_cash_3bp_river | 21.8 | 7.2 | **-67%** |
| N_cash_4bp_river | 33.0 | 10.7 | **-68%** |
| N_cash_4bp_turn | 15.8 | 12.0 | -24% |
| N_mtt100_river | 19.6 | 5.2 | **-73%** |
| N_mtt25_river | 8.8 | 2.0 | **-77%** |
| N_mtt200_river | 4.0 | 4.2 | ±0% |
| N_mtt200_turn | 2.7 | 2.7 | ±0% |
| P5_A_mtt_3bp_river | 28.7 | 13.4 | -53% |
| P5_B_3bp_river_extra | 22.5 | 6.6 | **-71%** |
| P5_B_4bp_river_traj | 38.6 | 23.5 | -39% |
| P6_A_mtt_4bp_river | 30.2 | 2.5 | **-92%** |
| P6_A_mtt_4bp_turn | 17.7 | 12.6 | -29% |

### △ 同等 (within 30%) (5 scenarios)
B_turn / P5_C_co_open_turn / P5_C_hj_open_turn / P5_A_cash_3bp_turn / P5_A_mtt_3bp_turn

### ✗ UDG が v1 より劣る (主に flop, 6 scenarios)

| scenario | v1 | UDG | 悪化 |
|----------|---:|----:|----:|
| A_cash_4bp_flop | 5.0 | 9.6 | +90% |
| N_cash_4bp_flop | 4.8 | 9.2 | +90% |
| P6_A_mtt_4bp_flop | 5.3 | 10.1 | +91% |
| N_cash_3bp_flop | 2.1 | 3.9 | +84% |
| N_mtt_3bp_flop | 2.6 | 4.6 | +79% |
| B_flop | 0.93 | 1.27 | +36% |

→ **flop は board-specific pattern が多くて universal rule では不足**。  
書籍では「**flop 章だけ 5-7 例外を別途暗記**」する形にすれば対応可能。

### — baseline 比較不可 (Tier C / R1)

CR/donk (5 scenarios) と R1_past は v1 baseline がないため絶対値のみ:

| scenario | UDG huge_loss |
|----------|--------------:|
| A_cash_cr_def_full | 2.07 |
| A_cash_donk_def_full | 1.13 |
| N_cash_cr_def | 1.94 |
| N_cash_donk_def | 1.33 |
| P5_D_turn_cr_def | 4.54 |
| P5_D_turn_donk_def | 1.99 |
| P5_D_river_donk_def | 3.22 |
| R1_past | 29.02 |

R1 (BB river allin 防御) の 29 BB は専用公式が必要かも (現状 universal rule は OOP defender 想定)。

## Vol2/Vol3/Vol4 章構成への含意

### 序章 (Vol2/Vol3 共通)
- Layer 1: 3 tier 概念の導入 (~10 ページ)
- Layer 2: 7 universal rule のフロー図 (~5 ページ)

### Vol2 章構成 (Cash)
| 章 | 内容 | ページ数想定 |
|----|------|----:|
| 1-2 | SRP postflop = Universal rule そのまま | ~30 |
| 3-4 | 3BP modifier (2-3 例外) | ~15 |
| 5-6 | 4BP modifier (4-5 例外) | ~20 |
| 7 | flop 用 board-specific 例外 (5-7 件) | ~15 |
| 8 | CR/donk modifier | ~15 |
| 9 | 境界ハンド集 | ~10 |
| **計** | | **~105** |

vs 現状の 11 公式各章方式の想定 ~180 ページ → **約 40% 短縮**

### Vol3 章構成 (MTT)
| 章 | 内容 |
|----|------|
| 1 | Vol2 と同じ universal rule のリマインド |
| 2 | MTT depth modifier (3 ルール: ≤25 / 50-100 / ≥200) |
| 3-4 | Vol2 modifier との差分 |
| 5 | MTT 境界ハンド集 |

vs Vol2 と独立に書く現状方式 → **半分のページ数で書ける**

### Vol4 章構成 (Exploit)
- opp_polarization tier の概念は Vol2 で済んでいる
- exploit は「相手タイプに応じて tier を動的に更新する」(tight player は POLAR 寄り、loose は MERGED 寄り)
- → exploit ロジックも universal rule + 動的 tier 更新で書ける

## トレードオフの整理

| 観点 | 現状 (11 専用公式) | UDG (3層) |
|------|------------------|----------|
| 暗記項目 | ~165 | ~30 (**-82%**) |
| huge_loss | 15.75 BB | 10.27 BB (**-35%**) |
| acc | 75-85% | 69.7% |
| 4BP flop の精度 | acc 75% | acc 50% |
| river の精度 | acc 80% | acc 80% (同等) |
| 書籍ページ数 (推定) | ~180 + 200 (Vol2+Vol3) | ~105 + 60 |
| 読者の学習コスト | 高 | 大幅低減 |

## 推奨

1. **書籍ベース公式は UDG を採用** (Vol2/Vol3 統一フォーマット)
2. **flop の精度が必要な読者向けに付録 A** で「flop 板別細則」を提供
3. **Vol4 (exploit) は UDG の tier 動的更新として設計**
