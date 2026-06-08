# Flop 状態空間の段階的 ablation 実験

ユーザー仮説の検証: Board / +Range / +Hero での精度差。

## Board 4 軸 (User 提案)

- high_card: A=3 / KQ=2 / JT=1 / Low=0
- connectivity: Connected=2 / Semi=1 / Disconnected=0
- suit: Monotone=2 / 2tone=1 / Rainbow=0
- pair: Trips=2 / Paired=1 / Unpaired=0
+ dynamicity: straight_outs, fd_possible, b_high/mid/low (連続値)

## 結果

| Mode | Model | val accuracy | size |
|------|-------|---:|---:|
| Board only | Logistic | 50.26% | 12 |
| Board only | DT d=5 | 50.33% | 18 |
| Board only | DT d=10 | 50.33% | 20 |
| Board only | DT d=None | 50.33% | 20 |
| Board only | RF n=100 | 50.33% | 100 |
| + Range | Logistic | 60.00% | 15 |
| + Range | DT d=5 | 63.21% | 32 |
| + Range | DT d=10 | 68.26% | 402 |
| + Range | DT d=None | 68.53% | 577 |
| + Range | RF n=100 | 68.53% | 100 |
| + Hero | Logistic | 63.77% | 25 |
| + Hero | DT d=5 | 64.32% | 32 |
| + Hero | DT d=10 | 74.78% | 776 |
| + Hero | DT d=None | 76.46% | 11679 |
| + Hero | RF n=100 | 76.61% | 100 |

## ユーザー仮説との比較

| mode | 予想 | 実測 (RF) |
|------|------|---:|
| Board only | 55-60% | 50.3% |
| + Range | 70% | 68.5% |
| + Hero (Nut) | 77% | 76.6% |
