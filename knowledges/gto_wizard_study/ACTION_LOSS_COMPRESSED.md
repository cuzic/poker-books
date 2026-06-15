# Compressed Action Loss Formula (21 params)

Grid 24→9 cells + 補正 9→4 個に圧縮、過剰適合回避。

## 性能

| variant | accuracy | avg loss | huge% |
|---|---:|---:|---:|
| **v3 連続 (21 params)** | 68.67% | **0.4053 BB** | 1.54% |
| **v3 整数 (書籍向け)** | 63.57% | **0.6101 BB** | 3.14% |
| v1 整数 (24 grid + no correction) | 66.5% | 0.48 BB | 2.28% |
| v2 整数 (24 grid + 9 corrections) | 64.2% | 0.65 BB | 3.16% |
| 既存公式 v9b/v15 | 59.5% | 1.86 BB | 9.65% |

## Compressed Grid (3 カテゴリ × 3 board = 9 cells)

| カテゴリ | dry | paired | wet (connected/mono) |
|------|---:|---:|---:|
| **弱(MP/エア)** | 4 | 11 | 3 |
| **中(2P/TP+)** | 7 | 4 | 5 |
| **強(ナッツ/ストロング)** | 6 | 3 | 2 |

## 4 補正項

| 補正 | 整数 | 意味 |
|------|---:|------|
| **C1** | +6 | 強手 × wet/paired × SRP → raise 促進 |
| **C2** | -1 | TP+ × connected × SRP → raise 促進 |
| **C3** | -1 | エア × {overbet+ or 3-4BP 特殊board} → fold 促進 |
| **C4** | -8 | ミドル × dry × SRP → call 維持 |

## 公式 (整数版、書籍掲載可)

```
Score = 4 × tier_orig (0-5) + GridBase[tier_c][board_c]
      + 2 × DV + 1 × overcards
      + 3 × pot - 1 × bs + (-3)
      + 補正 (該当 spot のみ):
        if 強手 × wet/paired × SRP: +6
        if TP+ × connected × SRP: -1
        if エア × 大 bet/3-4BP 特殊: -1
        if ミドル × dry × SRP: -8

if Score >= 35: raise
elif Score >= 8: call
else: fold
```

## 暗記負荷

- Grid 9 cells (3×3 表)
- Base weights 6 個
- Corrections 4 個 (例外として暗記)
- 計 19 項目 (旧 v1 は 30+ 項目だった)