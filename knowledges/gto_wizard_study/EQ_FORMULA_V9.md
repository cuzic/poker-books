# 暗算可能な eq 計算式 v9 — base + if-then 補正

線形 base + 主要 interaction の if-then 補正項を data 駆動で学習。

## 性能

| variant | accuracy |
|---|---:|
| **v9 連続** | **59.20%** |
| **v9 整数 (書籍向け)** | **53.71%** |
| (参考) Grid + 線形 (60.42%) | 60.42% |
| (参考) DT depth 5 | 64.32% |
| (参考) RF (上限) | 76.61% |

## 公式 (整数版)

```
Score = w_mv × MV + w_dv × DV − w_opp × OppR + intercept

MV (made カテゴリ):  ナッツ=9, ストロング=7, ツーペア=6,
                 TP+=4, MP=2, エア=0
DV (draw):       combo=4, NFD/FD/OESD=3, gutshot=1, BDFD=1, none=0
OppR (pot):      SRP=0, DEF=1, 3BP=2, 4BP=3

+ if-then 補正項:
  if air_wet            : +1
  if mp_dry             : -3
  if oc_dry             : +1
  if op_dry             : -2
  if strong_conn        : -1
  if strong_mono        : -3
  if strong_paired      : +2
  if tp_mono            : -2

if Score >= 6: best
elif Score >= 1: good
elif Score >= 0: weak
else: trash
```

## 全係数

| 係数 | 連続 | 整数 |
|------|---:|---:|
| intercept | -4.237 | -4 |
| w_2pair_paired | +0.325 | +0 |
| w_air_wet | +0.718 | +1 |
| w_dv | +1.629 | +2 |
| w_mp_dry | -3.413 | -3 |
| w_mv | +1.976 | +2 |
| w_oc_dry | +1.226 | +1 |
| w_oc_wet | -0.173 | +0 |
| w_op_dry | -2.038 | -2 |
| w_op_wet | -0.034 | +0 |
| w_opp | +0.000 | +0 |
| w_strong_conn | -1.375 | -1 |
| w_strong_mono | -3.209 | -3 |
| w_strong_paired | +2.374 | +2 |
| w_tp_mono | -2.048 | -2 |
| w_tp_paired | -0.010 | +0 |

閾値: t_weak=0, t_good=1, t_best=6