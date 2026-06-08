# Action Loss 公式 v2 — 9 個の補正項追加

v1 (avg loss 0.48 BB) に huge loss の主要 spot に対する補正項を追加。

## 性能比較

| variant | accuracy | avg loss | huge% |
|---|---:|---:|---:|
| **v2 連続** | 68.25% | **0.4774 BB** | 2.07% |
| **v2 整数** | 64.18% | **0.6475 BB** | 3.16% |
| v1 整数 (前回) | 66.5% | 0.48 BB | 2.28% |
| 既存公式 v9b/v15 | 59.5% | 1.86 BB | 9.65% |

## 9 つの補正項 (整数)

| 補正 | 値 | 効果 |
|------|---:|------|
| c_air_bigbet | -2 | エア × bs ≥ overbet → fold 促進 |
| c_air_mono_4bp | +0 | エア × monotone × 4BP → fold 促進 |
| c_air_paired_3bp | -5 | エア × paired × 3BP → fold 促進 |
| c_air_paired_4bp | -4 | エア × paired × 4BP → fold 促進 |
| c_mid_dry_srp | -2 | ミドルペア × dry × SRP → call 維持 |
| c_strong_dry_srp | +1 | ストロング/ナッツ × dry × SRP → raise 促進 |
| c_strong_paired_srp | +15 | ストロング/ナッツ × paired × SRP → raise 促進 |
| c_strong_wet_srp | +6 | ストロング/ナッツ × wet × SRP → raise 促進 |
| c_tp_conn_srp | +18 | TP+ × connected × SRP → raise 検討 |

## 公式 (整数版)

```
Score = 2 × tier_idx + GridBase[tier][board]
      + 2 × DV + 2 × overcards
      + 2 × pot - 0 × bs + (-8)
      + 補正項 (該当する spot のみ):
        if エア × bs ≥ overbet → fold 促進: -2
        if エア × paired × 3BP → fold 促進: -5
        if エア × paired × 4BP → fold 促進: -4
        if ミドルペア × dry × SRP → call 維持: -2
        if ストロング/ナッツ × dry × SRP → raise 促進: +1
        if ストロング/ナッツ × paired × SRP → raise 促進: +15
        if ストロング/ナッツ × wet × SRP → raise 促進: +6
        if TP+ × connected × SRP → raise 検討: +18

if Score >= 24: raise
elif Score >= 2: call
else: fold
```

## Grid 表 (整数)

| tier | dry | paired | connected | monotone |
|------|---:|---:|---:|---:|
| エア | 3 | 8 | 2 | 1 |
| ミドルペア | 4 | 4 | 0 | 6 |
| トップペア以上 | 10 | 1 | 7 | 3 |
| ツーペア | 5 | 2 | 0 | 7 |
| ストロング | 0 | 1 | 7 | 10 |
| ナッツメイド | 5 | 2 | 1 | 3 |
