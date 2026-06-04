# Boundary Study Report v4 — wide-board mapping

生成日: 2026-05-26

65 spot 試行（6 シナリオ）の境界精密測定

---

## B-3 拡張: マルチウェイ SB donk グラデーション (n=15)

**境界仮説**: 連結度（gap）× high card で donk 率

| board | high | gap | donk% | サイズ |
|------|------|----:|------:|-----:|
| `4h3s2c` | 4 | 2 | 12.9 | 33% |
| `8h7s6d` | 8 | 2 | 5.4 | 33% |
| `Th9s8c` | T | 2 | 11.0 | 33% |
| `Jh8s2c` | J | 9 | 13.7 | 33% |
| `Qh9s2c` | Q | 10 | 6.3 | 33% |
| `Kh9s2c` | K | 11 | 4.6 | 33% |
| `Ah9s2c` | A | 12 | 7.6 | 33% |
| `Th6s2c` | T | 8 | 11.1 | 33% |
| `Jh5s2c` | J | 9 | 24.7 | 33% |
| `Kh5s2c` | K | 11 | 17.3 | 33% |
| `Kc7s3d` | K | 10 | 13.8 | 33% |
| `Ah5s2c` | A | 12 | 8.9 | 33% |
| `Qc6s3d` | Q | 9 | 26.1 | 33% |
| `8h5s2c` | 8 | 6 | 27.7 | 33% |
| `9c6s2d` | 9 | 7 | 19.3 | 33% |

### high card 別

| high group | avg donk% | n |
|---|---:|--:|
| A | 8.3% | 2 |
| K | 11.9% | 3 |
| Q | 16.2% | 2 |
| J/T | 15.1% | 4 |
| 9/8 | 17.5% | 3 |
| <8 | 12.9% | 1 |


## B-7 拡張: Kxx ターン cbet サイズ × turn card (n=10)

**仮説**: Kxx+5=101%, Kxx+Q=276% の境界はどこ？

| flop | turn | bet% | サイズ | 解釈 |
|-----|------|------:|------:|-----|
| `Ks7d2c` | 3h | 28.3 | 276% | Kxx+3 (low) |
| `Ks7d2c` | 4h | 31.3 | 101% | Kxx+4 |
| `Ks7d2c` | 5h | 30.1 | 101% | Kxx+5 (実測 101%) |
| `Ks7d2c` | 6h | 31.2 | 101% | Kxx+6 |
| `Ks7d2c` | 8h | 35.1 | 101% | Kxx+8 |
| `Ks7d2c` | 9h | 36.9 | 101% | Kxx+9 |
| `Ks7d2c` | Th | 32.4 | 276% | Kxx+T |
| `Ks7d2c` | Jh | 35.3 | 276% | Kxx+J |
| `Ks7d2c` | Qh | 31.8 | 276% | Kxx+Q (実測 276%) |
| `Ks7d2c` | Ah | 51.9 | 101% | Kxx+A (実測 101%) |


## B-1 拡張: ターン donk 境界 (n=12)

| flop+turn | donk% | サイズ | 解釈 |
|----|------:|------:|-----|
| `Ks7d2c5c` | 0.6 | 33% | K72+5 (no pair |
| `QhJd4s2h` | 0.2 | 33% | QJ4+2 (low blank) |
| `QhJd4s8c` | 0.0 | 276% | QJ4+8 (mid blank) |
| `Td7c6s5c` | 0.1 | 276% | T76+5 (str8 complete) |
| `AhKd4s2c` | 11.0 | 20% | AK4+2 (low blank) |
| `AhKd4s9c` | 0.0 | 157% | AK4+9 (mid blank) |
| `AhKd4s4c` | 0.0 | 157% | AK4+4 (bot pair board pair) |
| `9h8s7d2c` | 0.0 | 276% | 987+2 (blank) |
| `9h8s7d8c` | 59.6 | 33% | 987+8 (mid pair) |
| `9h8s7d9c` | 47.9 | 33% | 987+9 (top pair) |
| `Td7c6sTc` | 0.2 | 33% | T76+T (top pair already 0%) |
| `JdTs9c9d` | 39.2 | 33% | JT9+9 (mid pair) |


## B-9 NEW: ペアフロップ完全未調査領域 (n=8)

| board | line | bet/donk/probe% | サイズ | 解釈 |
|------|------|------:|------:|-----|
| `KsKd7c2h` | pre=F-R2.2-F-F-F-C fl=X-R1.9-C tn= | 0.1 | 276% | KK7+2 turn (paired flop) |
| `AhAdKc8h` | pre=F-R2.2-F-F-F-C fl=X-R1.9-C tn= | 0.0 | 276% | AAK+8 turn |
| `7d7s4c2h` | pre=F-R2.2-F-F-F-C fl=X-R1.9-C tn= | 0.0 | 276% | 774+2 turn |
| `Qs6s6c2h` | pre=F-R2.2-F-F-F-C fl=X-R1.9-C tn= | 0.0 | 276% | Q66+2 turn |
| `8h8s3c2h` | pre=F-R2.2-F-F-F-C fl=X-R1.9-C tn= | 0.1 | 276% | 883+2 turn |
| `KsKd7c` | pre=F-R2.2-F-F-F-C fl= tn= | 0.0 | 158% | KK7 flop first act BB |
| `7d7s4c` | pre=F-R2.2-F-F-F-C fl= tn= | 19.0 | 34% | 774 flop first act BB |
| `AhAdKc` | pre=F-R2.2-F-F-F-C fl= tn= | 0.0 | 158% | AAK flop first act BB |


## B-10 NEW: モノフロップ完全未調査領域 (n=10)

| board | line | bet% | サイズ | 解釈 |
|------|------|------:|------:|-----|
| `KsQs7s2h` | fl=X-R1.9-C tn= | 0.0 | 276% | KQ7-mono+2 turn |
| `KsQs7s2s` | fl=X-R1.9-C tn= | 0.0 | 276% | KQ7-mono+2s turn (4 to flush) |
| `Js9s5s2h` | fl=X-R1.9-C tn= | 0.0 | 276% | J95-mono+2 |
| `AsTs5s2h` | fl=X-R1.9-C tn= | 0.2 | 33% | AT5-mono+2 |
| `QsTs6s2h` | fl=X-R1.9-C tn= | 0.3 | 33% | QT6-mono+2 |
| `8s6s4s2h` | fl=X-R1.9-C tn= | 0.0 | 276% | 864-mono+2 |
| `KsQs7s` | fl= tn= | 0.0 | 158% | KQ7-mono flop BB first |
| `Js9s5s` | fl= tn= | 0.1 | 34% | J95-mono flop BB first |
| `KsQs7s2h` | fl=X-X tn= | 22.2 | 101% | KQ7-mono+2 XX turn |
| `Js9s5s2h` | fl=X-X tn= | 20.9 | 101% | J95-mono+2 XX turn |


## B-8 拡張: probe near-zero 境界 (n=12)

| board | turn | probe% | サイズ | 解釈 |
|------|------|------:|------:|-----|
| `QhJd4s` | Jh | 0.2 | 34% | QJ4+J top pair vs IP |
| `KsQd4h` | Kh | 11.8 | 101% | KQ4+K top pair vs IP |
| `KsQd4h` | Qh | 0.1 | 372% | KQ4+Q mid pair |
| `KsQd4h` | Jh | 2.8 | 101% | KQ4+J str8 draw |
| `AhKd4s` | Qh | 9.6 | 101% | AK4+Q str8 reach |
| `AhKd4s` | Jh | 0.1 | 372% | AK4+J str8 reach |
| `KsJd4h` | Th | 0.0 | 372% | KJ4+T str8 reach |
| `KsJd4h` | Qh | 14.9 | 34% | KJ4+Q top pair |
| `JdTs8c` | 9h | 10.7 | 34% | JT8+9 str8 complete |
| `JdTs8c` | Qh | 0.1 | 372% | JT8+Q broadway-reach |
| `9h7s5d` | 6c | 92.0 | 34% | 975+6 str8 complete |
| `9h7s5d` | 8c | 66.0 | 34% | 975+8 str8 complete |
