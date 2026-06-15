# 付録 A. MATCHA Score 公式 + Grid 早見

## A.1 公式 1 行

```
Score = Grid[カテゴリ][board] + DV × mult[street] + 2 × oc + 4 × pot − 2 × bs

≥ 43: raise / ≥ 14: call / else: fold
```

## A.2 Grid 12 cells

|           | dry | paired | wet |
|-----------|----:|-------:|----:|
| エア | 3 | 5 | 1 |
| アンダーペア | 18 | 40 | 10 |
| トップペア以上 | 38 | 10 | 31 |
| 2P+ | 25 | 28 | 23 |

## A.3 各軸の値早見

### カテゴリ (4 段階)

| index | 名前 | 含むハンド |
|---:|---|---|
| 0 | エア | no_made / king_high / ace_high |
| 1 | アンダーペア | 2nd / 3rd / under / low pair |
| 2 | TP+ | top_pair / overpair |
| 3 | 2P+ | 2P / set / trips / straight / flush / FH / quads / SF |

### board (3 タイプ)

| 名前 | 条件 |
|---|---|
| paired | 同 rank 2+ |
| wet | span ≤ 4 (connected) または mono |
| dry | 上記以外 |

### DV (Draw Value)

| dv_cat | 値 |
|---|---:|
| combo_draw | 4 |
| flush_draw / nut_flush_draw / oesd | 3 |
| gutshot / twocards_bdfd | 1 |
| onecard_bdfd / no_draw | 0 |

### street mult

| street | mult |
|---|---:|
| flop | 3 |
| turn | 2 |
| river | 0 |

### pot (係数 4)

| pot | 値 | 補正 |
|---|---:|---:|
| SRP | 0 | 0 |
| vs CR | 2 | +8 |
| 3BP | 2 | +8 |
| 4BP | 4 | +16 |

### bs (係数 −2)

| name | 値 | 補正 |
|---|---:|---:|
| small_33 | 0 | 0 |
| med_75p | 1 | −2 |
| med_100p | 2 | −4 |
| overbet | 3 | −6 |
| overbet_185 | 4 | −8 |
| allin | 5 | −10 |

### overcards (係数 2)

| oc | 補正 |
|---:|---:|
| 0 | 0 |
| 1 | +2 |
| 2 | +4 |

## A.4 例外 11 ルール

| # | カテゴリ | board | street | pot | 公式 pred → 真の解 |
|--:|---|---|---|---|---|
| 1 | TP+ | wet | flop | SRP | call → **fold** |
| 2 | 2P+ | wet | river | SRP | call → **raise** |
| 3 | ミドル | wet | turn | vs CR | call → **fold** |
| 4 | エア | wet | turn | 3BP | fold → **call** |
| 5 | 2P+ | wet | flop | SRP | call → **fold** |

## A.5 stack 補正

| stack | T_call | T_raise |
|---|---:|---:|
| ≤ 25bb | 12 | 40 |
| 100bb | **14** | **43** |
| 200bb+ | 16 | 45 |
| バブル (ICM) | +5〜+10 (定性) | 同 |
| MW (3+ way) | +10〜+15 (定性) | 同 |
