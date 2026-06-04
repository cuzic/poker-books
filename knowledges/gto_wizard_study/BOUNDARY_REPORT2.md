# Boundary Study Report v2 — paired-turn / multiway / river card

生成日: 2026-05-25

46/48 spots (2 failed: duplicate cards in board)

---

## B-1 拡張: ペア化ターン / ストレート完成ターン の boundary

**仮説**: 一部の board pair turn / str8 turn で OOP donk が >20%

### Top pair turn (board pair) (n=5)

| flop | turn | donk% | check% | size |
|------|------|------:|------:|-----:|
| `Ks7d2c` | `Kh` | **25.5** | 74.5 | 33% |
| `QhJd4s` | `Qc` | **0.0** | 100.0 | 276% |
| `AhKd4s` | `Ac` | **71.6** | 28.4 | 20% |
| `Td7c6s` | `Th` | **0.0** | 100.0 | 276% |
| `JdTs9c` | `Jh` | **0.0** | 100.0 | 276% |

**Summary**: mean donk=19.4%, max=71.6%, min=0.0%

### Mid pair turn (n=4)

| flop | turn | donk% | check% | size |
|------|------|------:|------:|-----:|
| `Ks7d2c` | `7c` | **48.1** | 51.9 | 33% |
| `QhJd4s` | `Jh` | **0.1** | 99.9 | 276% |
| `AhKd4s` | `Kc` | **86.0** | 14.0 | 20% |
| `JdTs9c` | `Th` | **0.1** | 99.9 | 276% |

**Summary**: mean donk=33.5%, max=86.0%, min=0.1%

### Bottom pair turn (n=4)

| flop | turn | donk% | check% | size |
|------|------|------:|------:|-----:|
| `Ks7d2c` | `2h` | **38.5** | 61.5 | 33% |
| `QhJd4s` | `4c` | **39.7** | 60.3 | 33% |
| `Td7c6s` | `6h` | **53.1** | 46.9 | 33% |
| `9h8s7d` | `7c` | **61.6** | 38.4 | 33% |

**Summary**: mean donk=48.2%, max=61.6%, min=38.5%

### Straight completing / draw turn (n=6)

| flop | turn | donk% | check% | size |
|------|------|------:|------:|-----:|
| `9h8s7d` | `6c` | **0.0** | 100.0 | 276% |
| `Td7c6s` | `8c` | **0.0** | 100.0 | 276% |
| `JdTs9c` | `8c` | **0.0** | 100.0 | 276% |
| `QhJd4s` | `Th` | **0.0** | 100.0 | 276% |
| `Td7c6s` | `9d` | **16.6** | 83.4 | 33% |
| `Td7c6s` | `5d` | **18.9** | 81.1 | 33% |

**Summary**: mean donk=5.9%, max=18.9%, min=0.0%


### ターン donk > 5% の全例外リスト

| board | donk% | topic |
|------|------:|-------|
| `AhKd4sKc` | **86.0** | b1_pair_mid |
| `AhKd4sAc` | **71.6** | b1_pair_top |
| `9h8s7d7c` | **61.6** | b1_pair_bot |
| `Td7c6s6h` | **53.1** | b1_pair_bot |
| `Ks7d2c7c` | **48.1** | b1_pair_mid |
| `QhJd4s4c` | **39.7** | b1_pair_bot |
| `Ks7d2c2h` | **38.5** | b1_pair_bot |
| `Ks7d2cKh` | **25.5** | b1_pair_top |
| `Td7c6s5d` | **18.9** | b1_str8 |
| `Td7c6s9d` | **16.6** | b1_str8 |


## B-3 拡張: BTN/CO マルチウェイ SB donk

### HJ vs CO vs BTN open multiway 比較

| board | HJ pos donk% | CO pos donk% | BTN pos donk% |
|-------|-------------:|-------------:|-------------:|
| `5d4s3c` | 5.8 | - | - |
| `6s5h4c` | 6.5 | - | - |
| `7d6s5c` | 2.1 | 0.2 | 2.0 |
| `8h6c4d` | 23.0 | - | - |
| `8h7s2c` | 21.5 | - | - |
| `9h8s2c` | 9.7 | - | - |
| `9h8s7d` | - | - | 38.3 |
| `Ah7c4d` | 17.7 | 11.8 | 21.1 |
| `Jc8s5h` | 19.8 | - | 22.0 |
| `Jh7s5c` | 33.8 | 35.1 | - |
| `Jh9s7c` | 14.4 | - | - |
| `Kh6s4c` | 23.3 | 22.8 | 17.8 |
| `Qc9s7d` | 10.6 | - | - |
| `Qh4s2c` | 26.0 | 28.2 | 34.0 |
| `Td7c6s` | - | 25.1 | 29.3 |
| `Th8c5d` | 16.3 | - | - |
| `Ts9s7c` | 22.4 | - | - |

### Position別平均

| pos | avg donk% | n |
|----|-----:|--:|
| HJ | 16.9% | 15 |
| CO | 20.5% | 6 |
| BTN | 23.5% | 7 |


## B-5 拡張: turn give-up 後 river の card pattern

スポット数: 14

### Flop+Turn: `9h8s7d4c`

| river | lead% | size% | note |
|-------|------:|------:|------|
| `2d` | **77.6** | 33 | 987 + 2 wet 実測 78% |
| `4h` | **76.4** | 33 | 987 + 4 (pair board pair) |
| `Td` | **59.8** | 33 | 987 + T (str8 complete) |
| `9d` | **54.8** | 125 | 987 + 9 (pair top) |
| `Ad` | **25.8** | 125 | 987 + A (scare) |

### Flop+Turn: `Ks7d2c5h`

| river | lead% | size% | note |
|-------|------:|------:|------|
| `Kd` | **60.9** | 33 | Kxx5h + K (pair top river) |
| `Ad` | **44.2** | 33 | Kxx5h + A (scare overcard) |
| `Qd` | **38.0** | 125 | Kxx5h + Q (mid blank) |
| `3d` | **37.3** | 125 | Kxx5h + 3d (blank) 実測 37% |

### Flop+Turn: `QhJd4s7c`

| river | lead% | size% | note |
|-------|------:|------:|------|
| `7d` | **45.2** | 33 | QJ4+7+7 (pair board) |
| `Ah` | **44.2** | 33 | QJ4+7+A (scare) |
| `Td` | **43.3** | 33 | QJ4+7+T (str8 complete) |
| `2h` | **42.0** | 125 | QJ4+7+2 実測 42% |
| `Qd` | **27.7** | 125 | QJ4+7+Q (pair top) |

