# Outs Direct Formula (DV テーブル廃止)

読者は outs を知っている前提で、outs を直接 score に加算。
DV テーブル (combo=4, FD=3, etc) を覚える必要なし。

## 性能比較

| variant | 連続 acc | 連続 loss | huge% | 整数 acc | 整数 loss | huge% |
|---|---:|---:|---:|---:|---:|---:|
| w_outs 自由 (18 cells) | 69.52% | 0.4032 | 1.65% | 68.94% | 0.4457 | 1.94% |
| **w_outs=1 固定 (18 cells)** | 69.67% | **0.3963** | 1.63% | 68.30% | **0.5167** | 2.62% |
| (参考) 18 cells + DV 5段階 | — | — | — | 69.44% | **0.4165** | 1.77% |
| (参考) v1 (24 cells + DV) | — | — | — | 66.5% | 0.4789 | 2.28% |

## w_outs=1 公式 (整数版)

```
Score = 5 × tier + Grid[tier][board]
      + 1 × outs (読者が計算)
      + 0 × overcards
      + 3 × pot - 2 × bs + (-10)

outs lookup (読者が暗算):
  combo draw (FD+OESD): 15
  flush draw / NFD:     9
  OESD:                 8
  gutshot:              4
  BDFD (2 cards):       2
  no draw:              0

if Score >= 26: raise
elif Score >= -10: call
else: fold
```

## Grid (w_outs=1 整数版)

| tier | dry | paired | wet |
|------|---:|---:|---:|
| エア | -7 | -5 | -8 |
| ミドルペア | 17 | 2 | -6 |
| トップペア以上 | 13 | 8 | -5 |
| ツーペア | 16 | 15 | -5 |
| ストロング | -6 | -8 | 1 |
| ナッツメイド | 0 | 5 | -2 |

## 暗記項目

| version | 軸の値 | grid | weights | 合計項目 |
|---|---:|---:|---:|---:|
| 旧 (DV 5段階) | tier 6 + DV 5 + bs 6 + pot 4 = 21 | 18 | 5 | **44** |
| **新 (outs 直接)** | tier 6 + bs 6 + pot 4 = 16 | 18 | 5 | **39** ← 5 項目減 |