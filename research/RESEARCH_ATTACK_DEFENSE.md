# attack / defense / mixed の網羅性検証

**Postflop ファイル数**: 732

## 1. spot_type × actor 集計

| Actor | attack | defense | mixed | ? | 合計 |
|-------|--------|---------|-------|---|------|
| BB | 113 | 185 | 0 | 0 | 298 |
| BTN | 146 | 0 | 0 | 0 | 146 |
| CO | 72 | 0 | 0 | 0 | 72 |
| HJ | 72 | 0 | 0 | 0 | 72 |
| LJ | 72 | 0 | 0 | 0 | 72 |
| SB | 72 | 0 | 0 | 0 | 72 |

## 2. SB が actor (postflop)

ファイル数: 72

| Phase | Depth | attack | defense | mixed | ? |
|-------|-------|--------|---------|-------|---|
| flop | 50bb | 24 | 0 | 0 | 0 |
| flop | 100bb | 24 | 0 | 0 | 0 |
| flop | 200bb | 24 | 0 | 0 | 0 |

## 3. SB が pot に参加 (postflop、actor は問わない)

ファイル数: 0

| SB chips_on_table | ファイル数 | 推定 |
|-------------------|---------|------|

## 4. SB-BB BvB SRP postflop (SB open ~2.5BB, BB call)

ファイル数: 0

| Phase | Depth | attack | defense | mixed |
|-------|-------|--------|---------|-------|

## 5. defense ファイル (185)

| Defender (actor) | ファイル数 |
|------------------|---------|
| BB | 185 |

| Phase | defense ファイル数 |
|-------|------------------|
| flop | 96 |
| river | 49 |
| turn | 40 |

