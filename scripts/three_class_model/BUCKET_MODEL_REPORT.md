# Equity-Bucket Decision Model

Source: 209071 rows / 384 spots

## 1. Bet frequency by equity bucket (overall)

| bucket | n_rows | bet_freq_median | bet_freq_mean |
|---|---:|---:|---:|
| best_hands | 26080 | 60.0% | 53.2% |
| good_hands | 39160 | 27.3% | 36.6% |
| weak_hands | 33864 | 21.3% | 33.6% |
| trash_hands | 109967 | 0.5% | 24.3% |

## 2. Bucket × context

### flop/IP/srp (n=60626)

| bucket | n | bet_freq_median |
|---|---:|---:|
| best_hands | 9459 | 75.9% |
| good_hands | 17236 | 53.7% |
| weak_hands | 17737 | 47.3% |
| trash_hands | 16194 | 52.6% |

### flop/IP/srp_3bet (n=1001)

| bucket | n | bet_freq_median |
|---|---:|---:|
| best_hands | 36 | 58.2% |
| good_hands | 111 | 90.7% |
| weak_hands | 87 | 0.1% |
| trash_hands | 767 | 12.1% |

### flop/OOP/limped (n=3166)

| bucket | n | bet_freq_median |
|---|---:|---:|
| best_hands | 189 | 93.7% |
| good_hands | 318 | 91.6% |
| weak_hands | 256 | 80.6% |
| trash_hands | 2403 | 77.1% |

### flop/OOP/srp (n=19899)

| bucket | n | bet_freq_median |
|---|---:|---:|
| best_hands | 746 | 19.3% |
| good_hands | 2428 | 21.9% |
| weak_hands | 3068 | 14.2% |
| trash_hands | 13657 | 1.9% |

### river/OOP/srp (n=23199)

| bucket | n | bet_freq_median |
|---|---:|---:|
| best_hands | 3563 | 89.5% |
| good_hands | 2578 | 99.6% |
| weak_hands | 1691 | 30.4% |
| trash_hands | 15367 | 7.5% |

### turn/IP/srp (n=12782)

| bucket | n | bet_freq_median |
|---|---:|---:|
| best_hands | 2513 | 84.8% |
| good_hands | 1969 | 0.2% |
| weak_hands | 1222 | 0.4% |
| trash_hands | 7078 | 15.7% |

### turn/OOP/srp (n=87494)

| bucket | n | bet_freq_median |
|---|---:|---:|
| best_hands | 9560 | 6.8% |
| good_hands | 14506 | 0.0% |
| weak_hands | 9801 | 0.0% |
| trash_hands | 53627 | 0.1% |

### turn/OOP/srp_3bet (n=904)

| bucket | n | bet_freq_median |
|---|---:|---:|
| best_hands | 14 | — |
| good_hands | 14 | — |
| weak_hands | 2 | — |
| trash_hands | 874 | 29.1% |

## 3. Bucket × board family (overall)

### dry_high (n=103782)

| bucket | n | bet_freq_median |
|---|---:|---:|
| best_hands | 14473 | 57.3% |
| good_hands | 15895 | 13.8% |
| weak_hands | 15356 | 19.3% |
| trash_hands | 58058 | 0.9% |

### dynamic (n=67357)

| bucket | n | bet_freq_median |
|---|---:|---:|
| best_hands | 7699 | 65.8% |
| good_hands | 14512 | 34.8% |
| weak_hands | 10491 | 14.7% |
| trash_hands | 34655 | 0.5% |

### dynamic_2tone (n=2702)

| bucket | n | bet_freq_median |
|---|---:|---:|
| best_hands | 197 | 72.0% |
| good_hands | 976 | 51.3% |
| weak_hands | 672 | 34.8% |
| trash_hands | 857 | 31.9% |

### low_dry (n=5008)

| bucket | n | bet_freq_median |
|---|---:|---:|
| best_hands | 499 | 73.3% |
| good_hands | 960 | 41.1% |
| weak_hands | 1259 | 40.7% |
| trash_hands | 2290 | 12.7% |

### monotone (n=15375)

| bucket | n | bet_freq_median |
|---|---:|---:|
| best_hands | 1617 | 31.6% |
| good_hands | 3960 | 11.4% |
| weak_hands | 2729 | 0.1% |
| trash_hands | 7069 | 0.0% |

### paired (n=14847)

| bucket | n | bet_freq_median |
|---|---:|---:|
| best_hands | 1595 | 84.6% |
| good_hands | 2857 | 56.5% |
| weak_hands | 3357 | 63.1% |
| trash_hands | 7038 | 0.1% |

## 4. Bucket pattern at HIGH EV gap (>0.5 — clear best action)

n=55931 (26.8% of data)

| bucket | n | bet_freq_median |
|---|---:|---:|
| best_hands | 4346 | 0.1% |
| good_hands | 8544 | 0.0% |
| weak_hands | 6376 | 0.0% |
| trash_hands | 36665 | 0.0% |
