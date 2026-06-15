# DV 係数を street 別最適化

Rule of 4 and 2 を data で検証 + DV を street 別に係数化。

## 性能比較

| variant | accuracy | avg loss | huge% |
|---|---:|---:|---:|
| **DV 街別 連続** | 71.09% | **0.3573** | 1.29% |
| **DV 街別 整数** | 69.68% | **0.4404** | 2.00% |
| (旧) 18 cells 統一 DV=3 | 69.44% | 0.4165 BB | 1.77% |

## street 別 DV 係数

| street | 連続 w_dv | 整数 w_dv | Rule 4/2 ratio |
|---|---:|---:|---|
| flop | 6.558 | 7 | (基準) |
| turn | 3.380 | 3 | 1.94x の比 |
| river | -0.496 | 0 | (draw 完成不可) |

Rule of 4/2 期待: flop/turn ratio = 2.0、river = 0

## 整数公式

```
Score = 5 × カテゴリ + Grid[カテゴリ][board]
      + DV × (flop 7 / turn 3 / river 0)
      + 2 × overcards
      + 3 × pot - 2 × bs + (-14)

if Score >= 32: raise
elif Score >= -5: call
else: fold
```