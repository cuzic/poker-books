# Boundary Study Report — GTO Wizard 検証

生成日: 2026-05-25

## B-3: マルチウェイ SB donk × board (n=15)

仮説: 弱コネクト × middle range で 20-30%、その他 5-10%

| board | high | conn | suit | bet% | size% | note |
|-------|------|------|------|-----:|------:|------|
| `7d6s5c` | 7 | connected | rainbow | 2.1 | 33 | 3way HJ+SB+BB flop 765 connect |
| `6s5h4c` | 6 | connected | rainbow | 6.5 | 33 | 3way 654 connect mid |
| `5d4s3c` | 5 | connected | rainbow | 5.8 | 33 | 3way 543 connect low |
| `8h6c4d` | 8 | connected | rainbow | 23.0 | 33 | 3way 864 gap mid |
| `Th8c5d` | T | gap | rainbow | 16.3 | 33 | 3way T85 mixed |
| `Qc9s7d` | Q | gap | rainbow | 10.6 | 33 | 3way Q97 mid-high |
| `Jc8s5h` | J | gap | rainbow | 19.8 | 33 | 3way J85 |
| `Ah7c4d` | A | disconnected | rainbow | 17.7 | 33 | 3way A74 A-high |
| `Kh6s4c` | K | disconnected | rainbow | 23.3 | 33 | 3way K64 |
| `Qh4s2c` | Q | disconnected | rainbow | 26.0 | 33 | 3way Q42 air |
| `9h8s2c` | 9 | gap | rainbow | 9.7 | 33 | 3way 982 paired-style |
| `8h7s2c` | 8 | gap | rainbow | 21.5 | 33 | 3way 872 mid-conn-low |
| `Jh9s7c` | J | connected | rainbow | 14.4 | 33 | 3way J97 conn |
| `Ts9s7c` | T | connected | 2tone | 22.4 | 33 | 3way T97 2tone-conn |
| `Jh7s5c` | J | gap | rainbow | 33.8 | 33 | 3way J75 gap |

### 連結度別平均

| connectedness | avg bet% | n |
|----|-----:|--:|
| connected | 12.4% | 6 |
| gap | 18.6% | 6 |
| disconnected | 22.3% | 3 |


## B-4: XX-XX river BB lead × position (n=12)

仮説: BTN > CO > HJ > UTG の順で OOP river lead 率が高い

| position | board | river card | bet% | size% | note |
|----------|-------|------------|-----:|------:|------|
| UTG | `Ks7d2c5h3d` | 3d | 20.7 | 126 | UTGvBB XX-XX dry |
| UTG | `9h8s7d4c2d` | 2d | 25.5 | 126 | UTGvBB XX-XX wet 987 |
| UTG | `AhKd4s8c2h` | 2h | 28.6 | 126 | UTGvBB XX-XX AK4 mid |
| HJ | `9h8s7d4c2d` | 2d | 27.2 | 126 | HJvBB XX-XX wet |
| HJ | `AhKd4s8c2h` | 2h | 21.7 | 126 | HJvBB XX-XX AK4 |
| CO | `Ks7d2c5h3d` | 3d | 59.8 | 33 | COvBB XX-XX dry |
| CO | `9h8s7d4c2d` | 2d | 21.2 | 126 | COvBB XX-XX wet |
| CO | `Th9s8c4dAh` | Ah | 34.2 | 33 | COvBB XX-XX T98+A |
| BTN | `9h8s7d4c2d` | 2d | 48.6 | 33 | BTNvBB XX-XX wet |
| BTN | `AhKd4s8c2h` | 2h | 26.1 | 126 | BTNvBB XX-XX AK4 |
| BTN | `Th9s8c4dAh` | Ah | 27.4 | 33 | BTNvBB XX-XX T98+A |
| BTN | `QhJd4s7c2h` | 2h | 25.3 | 126 | BTNvBB XX-XX QJ4 |

### Position 別平均

| pos | avg bet% | n |
|----|-----:|--:|
| UTG | 24.9% | 3 |
| HJ | 24.4% | 2 |
| CO | 38.4% | 3 |
| BTN | 31.9% | 4 |


## B-1: ターン donk (b1_turn_donk) n=10

| line / board | check% | bet% | bet size |
|-----|------:|-----:|------:|
| `Ks7d2c5h` (BTNvBB turn after cbet-call Kx) | 99.9 | 0.1 | 257% |
| `9h8s7d4c` (BTNvBB turn 987) | 100.0 | 0.0 | 257% |
| `Td7c6s2h` (BTNvBB turn T76) | 100.0 | 0.0 | 257% |
| `QhJd4s7c` (BTNvBB turn QJ4) | 100.0 | 0.0 | 257% |
| `JdTs9c4h` (BTNvBB turn JT9) | 100.0 | 0.0 | 148% |
| `Ks7d2c5h` (COvBB turn Kxx) | 99.9 | 0.1 | 266% |
| `9h8s7d4c` (COvBB turn 987) | 100.0 | 0.0 | 266% |
| `AhKd4s8c` (COvBB turn AK4) | 100.0 | 0.0 | 153% |
| `Ks7d2c5h` (UTGvBB turn Kxx) | 100.0 | 0.0 | 276% |
| `9h8s7d4c` (UTGvBB turn 987) | 100.0 | 0.0 | 276% |


## B-1: ターン donk (b1_turn_donk_pair) n=2

| line / board | check% | bet% | bet size |
|-----|------:|-----:|------:|
| `Ks7d2cKh` (HJvBB turn K pair) | 74.5 | 25.5 | 33% |
| `Ks7d2c7c` (HJvBB turn 7 pair) | 51.9 | 48.1 | 33% |


## B-1: ターン donk (b1_turn_donk_str8) n=2

| line / board | check% | bet% | bet size |
|-----|------:|-----:|------:|
| `9h8s7d6c` (HJvBB turn 987 + 6 (str8 compl) | 100.0 | 0.0 | 276% |
| `Td7c6s8h` (HJvBB turn T76 + 8 (gut+str8)) | 82.9 | 17.1 | 33% |


## B-1: ターン donk (b1_turn_donk_flush) n=1

| line / board | check% | bet% | bet size |
|-----|------:|-----:|------:|
| `Ah4d2c9h` (HJvBB turn A42 + 9 wet) | 100.0 | 0.0 | 276% |


## B-1: ターン donk (b1_turn_donk_overcard) n=1

| line / board | check% | bet% | bet size |
|-----|------:|-----:|------:|
| `9h8s7dAd` (HJvBB turn 987 + A (overcard)) | 100.0 | 0.0 | 276% |


## B-1: ターン donk (b1_turn_donk_paired) n=2

| line / board | check% | bet% | bet size |
|-----|------:|-----:|------:|
| `QhJd4sQc` (HJvBB turn QJ4 + Q (top pair)) | 100.0 | 0.0 | 276% |
| `Td7c6s6h` (HJvBB turn T76 + 6 (bottom pai) | 46.9 | 53.1 | 33% |


## B-1: ターン donk (b1_turn_donk_mono) n=2

| line / board | check% | bet% | bet size |
|-----|------:|-----:|------:|
| `KsQs7s4s` (HJvBB turn mono complete) | 100.0 | 0.0 | 276% |
| `Kh7c2c5c` (HJvBB turn flush draw complete) | 100.0 | 0.0 | 276% |


## B-1 サマリ: 全ターン donk スポット (n=20)

- mean bet%: 7.21%
- max bet%: 53.13%  → board: Td7c6s6h
- min bet%: 0.01%
- bet% > 5% の spot: 4/20

### 5% 超過例外:

- `Ks7d2cKh` (b1_turn_donk_pair): 25.5%
- `Ks7d2c7c` (b1_turn_donk_pair): 48.1%
- `Td7c6s8h` (b1_turn_donk_str8): 17.1%
- `Td7c6s6h` (b1_turn_donk_paired): 53.1%
