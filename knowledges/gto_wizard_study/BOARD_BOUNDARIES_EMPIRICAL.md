# Board 分類境界の実測導出 (probe data 21 boards)

MATCHA Framework の現行 heuristic 分類 (POLAR/MERGED/CONDENSED) を
GTO Wizard probe data の実行動から検証。

## 各 board の BTN cbet 行動データ

| flop | static (heuristic) | cbet% | check% | polariz | sizings | dom_size |
|------|-------------------|------:|------:|--------:|--------:|---------|
| `4s4d2c` | POLAR (dynamic) | 57% | 43% | 0.13 | 1 | 1.9bb (57%) |
| `ks8d2c` | MERGED (low_dry) | 50% | 50% | 0.00 | 1 | 1.9bb (50%) |
| `astd4c` | MERGED (low_dry) | 49% | 51% | 0.03 | 1 | 1.9bb (49%) |
| `9s8d7c` | POLAR (dynamic) | 48% | 52% | 0.03 | 1 | 1.9bb (48%) |
| `as9d4c` | MERGED (low_dry) | 48% | 52% | 0.03 | 1 | 1.9bb (48%) |
| `ks9d4c` | MERGED (low_dry) | 48% | 52% | 0.05 | 1 | 1.9bb (48%) |
| `kh9c5d` | MERGED (low_dry) | 46% | 54% | 0.08 | 1 | 1.9bb (46%) |
| `jstc4s` | MERGED (low_dry) | 44% | 56% | 0.12 | 1 | 1.9bb (44%) |
| `jsts4h` | MERGED (low_dry) | 44% | 56% | 0.12 | 1 | 1.9bb (44%) |
| `astd9c` | MERGED (low_dry) | 44% | 56% | 0.12 | 1 | 1.9bb (44%) |
| `kskd4c` | MERGED (paired) | 43% | 57% | 0.13 | 1 | 1.9bb (43%) |
| `jsts4s` | POLAR (monotone) | 34% | 66% | 0.32 | 1 | 1.9bb (34%) |
| `8s5d3c` | MERGED (low_dry) | 33% | 67% | 0.33 | 1 | 6.5bb (33%) |
| `kskd9c` | MERGED (paired) | 33% | 67% | 0.33 | 1 | 1.9bb (33%) |
| `7s4d2c` | MERGED (low_dry) | 33% | 67% | 0.34 | 1 | 6.5bb (33%) |
| `9s6d3c` | MERGED (low_dry) | 33% | 67% | 0.35 | 1 | 6.5bb (33%) |
| `8s6d3h` | MERGED (low_dry) | 33% | 67% | 0.35 | 1 | 6.5bb (33%) |
| `9s7d5c` | POLAR (dynamic) | 31% | 69% | 0.38 | 1 | 6.5bb (31%) |
| `js7s3h` | MERGED (low_dry) | 28% | 72% | 0.44 | 1 | 6.5bb (28%) |
| `9s8d6c` | POLAR (dynamic) | 27% | 73% | 0.46 | 1 | 6.5bb (27%) |
| `qhjd9c` | POLAR (dynamic) | 21% | 79% | 0.59 | 1 | 6.5bb (21%) |

## 実測導出境界 (案)

BTN の cbet 頻度を主軸に 3 クラスター:

### POLAR-style (cbet_freq < 40%, 選択的攻撃)
BTN は polar range で attack、check 過半。

| flop | cbet% | static MATCHA | 一致? |
|------|------:|---------------|------|
| `jsts4s` | 34% | POLAR (monotone) | ✓ |
| `8s5d3c` | 33% | MERGED (low_dry) | ⚠ |
| `kskd9c` | 33% | MERGED (paired) | ⚠ |
| `7s4d2c` | 33% | MERGED (low_dry) | ⚠ |
| `9s6d3c` | 33% | MERGED (low_dry) | ⚠ |
| `8s6d3h` | 33% | MERGED (low_dry) | ⚠ |
| `9s7d5c` | 31% | POLAR (dynamic) | ✓ |
| `js7s3h` | 28% | MERGED (low_dry) | ⚠ |
| `9s8d6c` | 27% | POLAR (dynamic) | ✓ |
| `qhjd9c` | 21% | POLAR (dynamic) | ✓ |

### MERGED-style (cbet_freq > 55%, 連発攻撃)
BTN range advantage 強、wide cbet。

| flop | cbet% | static MATCHA | 一致? |
|------|------:|---------------|------|
| `4s4d2c` | 57% | POLAR (dynamic) | ⚠ |

### CONDENSED-style (cbet_freq 40-55%, 混合)

| flop | cbet% | static MATCHA | 一致? |
|------|------:|---------------|------|
| `ks8d2c` | 50% | MERGED (low_dry) | ✓ |
| `astd4c` | 49% | MERGED (low_dry) | ✓ |
| `9s8d7c` | 48% | POLAR (dynamic) | ? |
| `as9d4c` | 48% | MERGED (low_dry) | ✓ |
| `ks9d4c` | 48% | MERGED (low_dry) | ✓ |
| `kh9c5d` | 46% | MERGED (low_dry) | ✓ |
| `jstc4s` | 44% | MERGED (low_dry) | ✓ |
| `jsts4h` | 44% | MERGED (low_dry) | ✓ |
| `astd9c` | 44% | MERGED (low_dry) | ✓ |
| `kskd4c` | 43% | MERGED (paired) | ✓ |

## 提案: 実 GTO 行動に基づくロジカル分類

【現行 MATCHA (heuristic)】
- POLAR = {dynamic, dynamic_2tone, monotone}
- MERGED = {dry_high, low_dry, paired}
- CONDENSED = その他

【実測導出案 (cbet 頻度ベース)】
- POLAR: BTN cbet < 40% (board が draws 多くて attack 抑制)
- CONDENSED: BTN cbet 40-55% (board が mid-heavy で混合)
- MERGED: BTN cbet > 55% (board が dry でwide attack)

【データから判明した不一致】
- 一致: 4/21
- 不一致: 17

| flop | static (現行) | empirical (実測) | cbet% |
|------|-------------|------------------|------:|
| `4s4d2c` | polar | merged | 57% |
| `ks8d2c` | merged | condensed | 50% |
| `astd4c` | merged | condensed | 49% |
| `9s8d7c` | polar | condensed | 48% |
| `as9d4c` | merged | condensed | 48% |
| `ks9d4c` | merged | condensed | 48% |
| `kh9c5d` | merged | condensed | 46% |
| `jstc4s` | merged | condensed | 44% |
| `jsts4h` | merged | condensed | 44% |
| `astd9c` | merged | condensed | 44% |
| `kskd4c` | merged | condensed | 43% |
| `8s5d3c` | merged | polar | 33% |
| `kskd9c` | merged | polar | 33% |
| `7s4d2c` | merged | polar | 33% |
| `9s6d3c` | merged | polar | 33% |
| `8s6d3h` | merged | polar | 33% |
| `js7s3h` | merged | polar | 28% |

## 次のステップ

1. drill cards の Hand Strength tier × board family 振る舞いも同様に実測導出
2. SPR 境界 (1/3/7) の実測検証 (現状: 計算ベース、行動の不連続性は未確認)
3. Bet Sizing 4 段階 → 実 GTO 2 段階 (small ~30% / big ~90%) との整合