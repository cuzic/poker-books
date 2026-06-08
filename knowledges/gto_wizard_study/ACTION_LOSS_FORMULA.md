# Action Loss を直接最小化する公式

eq_bucket accuracy を経由せず、最終 action の loss (期待 EV 損失) を直接 minimize。

## 公式構造

```
Step 1: eq_score = GridBase[tier][board] + w_dv × DV + w_oc × overcards
Step 2: action_score = w_tier × tier + eq_score + w_pot × pot - w_bs × bs + intercept
Step 3: action: >= T_raise raise / >= T_call call / else fold
```

## 性能

| variant | accuracy | avg loss | huge% |
|---|---:|---:|---:|
| **Loss-optimized (連続)** | 68.77% | **0.3954 BB** | 1.50% |
| Acc-optimized (連続) | **70.61%** | 0.4189 BB | 1.78% |
| Loss-optimized (整数) | 66.49% | 0.4789 BB | 2.28% |
| (参考) tier+eq 旧式 (eq 真値) | 71.0% | 0.34 BB | 1.22% |
| (参考) 既存公式 v9b/v15 | 59.5% | 1.86 BB | 9.65% |

## Optimal Grid (loss-minimized、連続値)

| tier | dry | paired | connected | monotone |
|------|---:|---:|---:|---:|
| エア | 1.55 | 8.19 | 0.18 | 1.23 |
| ミドルペア | 4.10 | 10.00 | 1.96 | 5.29 |
| トップペア以上 | 7.52 | 0.63 | 5.71 | 3.84 |
| ツーペア | 4.31 | 9.33 | 0.78 | 2.90 |
| ストロング | 8.26 | 4.52 | 8.88 | 8.61 |
| ナッツメイド | 7.87 | 5.87 | 3.43 | 7.32 |

## 重み (loss-minimized)

| 係数 | 連続 | 整数 |
|------|---:|---:|
| w_tier | +2.948 | +3 |
| w_dv | +2.160 | +2 |
| w_oc | +1.518 | +2 |
| w_pot | +2.381 | +2 |
| w_bs | +1.389 | +1 |
| intercept | -1.606 | -2 |
| t_call | 6.39 | 6 |
| t_raise | 26.33 | 26 |