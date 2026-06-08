# Board family の実 GTO 境界 (42 boards probe data)

## サマリー: cbet 頻度 vs 構造

| flop | high | paired | mono | connect | cbet% | dom_size | empirical_cluster |
|------|------|:------:|:----:|:-------:|------:|--------:|-------------------|
| `4s4d2c` | 4 | P | R | C | 57% | 1.9bb | 高頻度 (MERGED-style) |
| `as7d2c` | A | - | R | - | 50% | 1.9bb | 高頻度 (MERGED-style) |
| `ks2d3c` | K | - | R | - | 50% | 1.9bb | 高頻度 (MERGED-style) |
| `ks7d2c` | K | - | R | - | 50% | 1.9bb | 高頻度 (MERGED-style) |
| `ks8d2c` | K | - | R | - | 50% | 1.9bb | 高頻度 (MERGED-style) |
| `as9d2c` | A | - | R | - | 50% | 1.9bb | 高頻度 (MERGED-style) |
| `astd4c` | A | - | R | - | 49% | 1.9bb | 高頻度 (MERGED-style) |
| `9s8d7c` | 9 | - | R | C | 48% | 1.9bb | 高頻度 (MERGED-style) |
| `6s7d8c` | 8 | - | R | C | 48% | 1.9bb | 高頻度 (MERGED-style) |
| `as9d4c` | A | - | R | - | 48% | 1.9bb | 高頻度 (MERGED-style) |
| `ks9d4c` | K | - | R | - | 48% | 1.9bb | 中頻度 (CONDENSED-style) |
| `as9d6c` | A | - | R | - | 47% | 1.9bb | 中頻度 (CONDENSED-style) |
| `kh9c5d` | K | - | R | - | 46% | 1.9bb | 中頻度 (CONDENSED-style) |
| `2s2d4c` | 4 | P | R | C | 45% | 1.9bb | 中頻度 (CONDENSED-style) |
| `8s8d4c` | 8 | P | R | - | 45% | 1.9bb | 中頻度 (CONDENSED-style) |
| `5s5d4c` | 5 | P | R | C | 45% | 1.9bb | 中頻度 (CONDENSED-style) |
| `jstc4s` | J | - | T | - | 44% | 1.9bb | 中頻度 (CONDENSED-style) |
| `jsts4h` | J | - | T | - | 44% | 1.9bb | 中頻度 (CONDENSED-style) |
| `astd9c` | A | - | R | - | 44% | 1.9bb | 中頻度 (CONDENSED-style) |
| `kskd4c` | K | P | R | - | 43% | 1.9bb | 中頻度 (CONDENSED-style) |
| `kskd4c` | K | P | R | - | 43% | 1.9bb | 中頻度 (CONDENSED-style) |
| `asad4c` | A | P | R | - | 42% | 1.9bb | 中頻度 (CONDENSED-style) |
| `6s4d2c` | 6 | - | R | C | 41% | 6.5bb | 中頻度 (CONDENSED-style) |
| `ahkdqc` | A | - | R | C | 40% | 1.9bb | 中頻度 (CONDENSED-style) |
| `9s5d2c` | 9 | - | R | - | 39% | 6.5bb | 低頻度 (POLAR-style) |
| `8s9dtc` | T | - | R | C | 39% | 1.9bb | 低頻度 (POLAR-style) |
| `7s5d2c` | 7 | - | R | - | 35% | 6.5bb | 低頻度 (POLAR-style) |
| `4s3d2c` | 4 | - | R | C | 34% | 6.5bb | 低頻度 (POLAR-style) |
| `2s3d4c` | 4 | - | R | C | 34% | 6.5bb | 低頻度 (POLAR-style) |
| `jsts4s` | J | - | M | - | 34% | 1.9bb | 低頻度 (POLAR-style) |
| `8s5d3c` | 8 | - | R | - | 33% | 6.5bb | 低頻度 (POLAR-style) |
| `kskd9c` | K | P | R | - | 33% | 1.9bb | 低頻度 (POLAR-style) |
| `7s4d2c` | 7 | - | R | - | 33% | 6.5bb | 低頻度 (POLAR-style) |
| `9s6d3c` | 9 | - | R | - | 33% | 6.5bb | 低頻度 (POLAR-style) |
| `8s6d3h` | 8 | - | R | - | 33% | 6.5bb | 低頻度 (POLAR-style) |
| `4s5d6c` | 6 | - | R | C | 32% | 6.5bb | 低頻度 (POLAR-style) |
| `9s7d5c` | 9 | - | R | C | 31% | 6.5bb | 低頻度 (POLAR-style) |
| `js7s3h` | J | - | T | - | 28% | 6.5bb | 極端低頻度 (POLAR extreme) |
| `9s8d6c` | 9 | - | R | C | 27% | 6.5bb | 極端低頻度 (POLAR extreme) |
| `ks9d8c` | K | - | R | - | 22% | 6.5bb | 極端低頻度 (POLAR extreme) |
| `tsjdqc` | Q | - | R | C | 21% | 6.5bb | 極端低頻度 (POLAR extreme) |
| `qhjd9c` | Q | - | R | C | 21% | 6.5bb | 極端低頻度 (POLAR extreme) |

## empirical クラスター (cbet 頻度ベース)

### 中頻度 (CONDENSED-style) (n=14)
- `ks9d4c` cbet=48% — K-high
- `as9d6c` cbet=47% — A-high
- `kh9c5d` cbet=46% — K-high
- `2s2d4c` cbet=45% — paired connected low_board
- `8s8d4c` cbet=45% — paired
- `5s5d4c` cbet=45% — paired connected low_board
- `jstc4s` cbet=44% — plain
- `jsts4h` cbet=44% — plain
- `astd9c` cbet=44% — A-high
- `kskd4c` cbet=43% — paired K-high
- `kskd4c` cbet=43% — paired K-high
- `asad4c` cbet=42% — paired A-high
- `6s4d2c` cbet=41% — connected low_board
- `ahkdqc` cbet=40% — connected A-high

### 低頻度 (POLAR-style) (n=13)
- `9s5d2c` cbet=39% — plain
- `8s9dtc` cbet=39% — connected
- `7s5d2c` cbet=35% — low_board
- `4s3d2c` cbet=34% — connected low_board
- `2s3d4c` cbet=34% — connected low_board
- `jsts4s` cbet=34% — monotone
- `8s5d3c` cbet=33% — plain
- `kskd9c` cbet=33% — paired K-high
- `7s4d2c` cbet=33% — low_board
- `9s6d3c` cbet=33% — plain
- `8s6d3h` cbet=33% — plain
- `4s5d6c` cbet=32% — connected low_board
- `9s7d5c` cbet=31% — connected

### 極端低頻度 (POLAR extreme) (n=5)
- `js7s3h` cbet=28% — plain
- `9s8d6c` cbet=27% — connected
- `ks9d8c` cbet=22% — K-high
- `tsjdqc` cbet=21% — connected
- `qhjd9c` cbet=21% — connected

### 高頻度 (MERGED-style) (n=10)
- `4s4d2c` cbet=57% — paired connected low_board
- `as7d2c` cbet=50% — A-high
- `ks2d3c` cbet=50% — K-high
- `ks7d2c` cbet=50% — K-high
- `ks8d2c` cbet=50% — K-high
- `as9d2c` cbet=50% — A-high
- `astd4c` cbet=49% — A-high
- `9s8d7c` cbet=48% — connected
- `6s7d8c` cbet=48% — connected
- `as9d4c` cbet=48% — A-high

## 構造的パターン (発見した規則性)

### 1. **Paired board**: 常に 42-45% cbet (CONDENSED-style)
- `4s4d2c` cbet=57% (pair rank: 4)
- `2s2d4c` cbet=45% (pair rank: 4)
- `8s8d4c` cbet=45% (pair rank: 8)
- `5s5d4c` cbet=45% (pair rank: 5)
- `kskd4c` cbet=43% (pair rank: K)
- `kskd4c` cbet=43% (pair rank: K)
- `asad4c` cbet=42% (pair rank: A)
- `kskd9c` cbet=33% (pair rank: K)

**ルール**: paired board は pair height に関わらず CONDENSED 寄り (42-45%)

### 2. **High-card dry (A/K-high、非 connected、非 paired)**: 47-50% cbet (MERGED-style)
- `as7d2c` cbet=50% — A-high dry
- `ks2d3c` cbet=50% — K-high dry
- `ks7d2c` cbet=50% — K-high dry
- `ks8d2c` cbet=50% — K-high dry
- `as9d2c` cbet=50% — A-high dry
- `astd4c` cbet=49% — A-high dry
- `as9d4c` cbet=48% — A-high dry
- `ks9d4c` cbet=48% — K-high dry
- `as9d6c` cbet=47% — A-high dry
- `kh9c5d` cbet=46% — K-high dry
- `astd9c` cbet=44% — A-high dry
- `ks9d8c` cbet=22% — K-high dry

**ルール**: A/K-high で connected でない board は MERGED (BTN range advantage)

### 3. **Connected boards (gap1≤2 + gap2≤2)**: 20-50% cbet (POLAR-style)
- `9s8d7c` cbet=48% — connected (9-high)
- `6s7d8c` cbet=48% — connected (8-high)
- `6s4d2c` cbet=41% — connected (6-high)
- `ahkdqc` cbet=40% — connected (A-high)
- `8s9dtc` cbet=39% — connected (T-high)
- `4s3d2c` cbet=34% — connected (4-high)
- `2s3d4c` cbet=34% — connected (4-high)
- `4s5d6c` cbet=32% — connected (6-high)
- `9s7d5c` cbet=31% — connected (9-high)
- `9s8d6c` cbet=27% — connected (9-high)
- `tsjdqc` cbet=21% — connected (Q-high)
- `qhjd9c` cbet=21% — connected (Q-high)

**ルール**: connected board は POLAR (small cbet 多用、draw-heavy)

### 4. **Low dry rainbow (7-high以下、非 connected、非 paired、rainbow)**: 33% cbet (POLAR/CONDENSED 境界)
- `7s5d2c` cbet=35%
- `7s4d2c` cbet=33%

## ロジカル境界 (データ駆動の提案)

**現行 MATCHA の heuristic 分類** ⇒ **データ駆動の改訂版**

```
def classify_board(board: list[str]) -> str:
    s = structure(board)
    if s.monotone or s.connected:
        return "POLAR"   # cbet < 40%、選択的 attack
    if s.paired:
        return "CONDENSED"  # cbet 42-45%、混合 protection
    if s.high_idx >= 11 and not s.connected:
        return "MERGED"  # A/K-high dry、cbet 47-50%、wide attack
    if s.low_board:
        return "POLAR"   # low dry 系も cbet < 40%、polar
    return "CONDENSED"  # その他、cbet 40-45%
```

## 現行 MATCHA からの修正点

| board family | 現行 MATCHA | データ駆動 | 修正理由 |
|--------------|-----------|----------|---------|
| low_dry (7s4d2c 等) | MERGED | **POLAR** | 実 cbet 33%、selective polar attack |
| dynamic (9s8d6c 等) | POLAR | POLAR | ✓ 整合 (cbet 27%) |
| dynamic_low (4s4d2c) | POLAR (paired override) | **MERGED** | paired low、cbet 57% |
| paired (KsKd4c 等) | MERGED | **CONDENSED** | cbet 43%、中頻度 |
| broadway connected (TJQ) | POLAR | POLAR extreme | cbet 21% ◎ |
| K-high connected (Ks9d8c) | POLAR ? | POLAR (連動チェック多) | cbet 22% |
| A-high dry (As7d2c) | MERGED | MERGED | ✓ cbet 50% |

## 次の境界調査必要トピック

1. **Hand strength tier の境界**: TPTK vs TPGK vs TPMK は cbet 行動が変わるか?
2. **Bet sizing 境界**: 33% (1.9bb) と 100% (6.5bb) の 2 段階に集約? それとも 4 段階維持?
3. **SPR 境界**: SPR<1, 1-3, 3-7, >7 で実 GTO 行動が不連続変化するか?
4. **Equity bucket 境界**: best/good/weak/trash の閾値は API per-combo で決まるが、人間判断可能な ranges に divide できるか?