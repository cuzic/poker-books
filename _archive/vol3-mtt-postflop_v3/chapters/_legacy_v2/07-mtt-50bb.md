# 第07章 MTT 50bb——base 同等の標準 context

MTT 50bb は α=+0、β=-3 で、Vol2 の mtt_short base 値とほぼ同じ頻度になる context です。
Vol3 13 context の中で「base への補正が最も小さい」context で、Vol2 知識をほぼそのまま
使えます。本章では mtt_25bb との対比で「補正が要らない理由」を理解します。

## mtt_50bb のパラメータ

A モデル mtt_50bb の補正は以下の通りです。

| layer | 値 | 意味 |
|---|---:|---|
| α (コンテキスト補正) | **+0pt** | base そのまま |
| β (TV≥7 のみ) | **-3pt** | 強い役で少し抑制 |
| cat_offset | 共通 (+6/-14/+7) | slowplay/trash/premium |
| ε[dynamic][mtt_srp] | -11pt | wet 板 |
| ε[paired][mtt_srp] | +2pt | ペア板 |
| ε[low_dry][mtt_srp] | -9pt | low_dry 板 |

WRMSE は 17.6%。base[mtt_short] の 5 値だけで実戦判断の 80% は決まります。

## α=+0 が意味すること

mtt_50bb の α=+0 は、Vol2 で覚えた mtt_short base 値 (air 37 / weak 30 / mid 35 /
strong 58 / nut 73) がそのまま mtt_50bb の予測値になる、ということです。

この context は「Vol2 の知識だけで実戦可能な最小 layer」と考えてください。
25bb (α=+36) と異なり、wide cbet 戦略が要らない理由は、50bb スタックでは
SPR が 7-9 まで上がり、相手の continue 後にも余裕があるためです。

## mtt_25bb との対比

mtt_25bb (α=+36) と mtt_50bb (α=+0) で、同じ top_pair on dry_high の頻度を
比較してみます。

| layer | mtt_25bb | mtt_50bb |
|---|---:|---:|
| base[mtt_short][strong] | 58% | 58% |
| α | +36 | +0 |
| β·I(TV≥7) | -5 | -3 |
| cat[default] | 0 | 0 |
| ε[dry_high][mtt_srp] | 0 | 0 |
| **合計** | **89%** | **55%** |

同じハンドでも 34pt 違う計算結果になります。MTT で「スタックサイズの違いを
意識する」とはこの差を意識することです。

## mtt_50bb の実戦例題

### mtt_50bb で 6 つの代表局面

**例**: トップペア (top_pair) + ドローなし on `Ks7d2c` (MTT 50bb)

1. MV = **7** (top_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][strong] = **58%**
4. α[mtt_50bb] (コンテキスト補正) = **+0pt**
5. β[mtt_50bb]·I(TV≥7) (強ハンド補正) = **-3pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 56%**

**例**: オーバーペア (overpair) + ドローなし on `Jd8c3s` (MTT 50bb)

1. MV = **7** (overpair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][strong] = **58%**
4. α[mtt_50bb] (コンテキスト補正) = **+0pt**
5. β[mtt_50bb]·I(TV≥7) (強ハンド補正) = **-3pt**
6. cat[premium] (ハンドクラス補正) = **+7pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 63%**

**例**: セカンドペア (second_pair) + OESD on `9c8d6h` (MTT 50bb)

1. MV = **5** (second_pair)、DV = **2** (OESD)
2. TV = MV + DV = 5 + 2 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][strong] = **58%**
4. α[mtt_50bb] (コンテキスト補正) = **+0pt**
5. β[mtt_50bb]·I(TV≥7) (強ハンド補正) = **-3pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Low Dry (T 以下の dry) → ε[low_dry][mtt_srp] (ボード補正) = **-9pt**

→ **連続 bet 頻度 ≈ 47%**

**例**: セット (set) + ドローなし on `9s9c4d` (MTT 50bb)

1. MV = **9** (set)、DV = **0** (ドローなし)
2. TV = MV + DV = 9 + 0 = **9** → band: ナッツ (TV 9+)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][nut] = **73%**
4. α[mtt_50bb] (コンテキスト補正) = **+0pt**
5. β[mtt_50bb]·I(TV≥7) (強ハンド補正) = **-3pt**
6. cat[slowplay] (ハンドクラス補正) = **+6pt**
7. 板分類: Paired (ペアボード) → ε[paired][mtt_srp] (ボード補正) = **+2pt**

→ **連続 bet 頻度 ≈ 79%**

**例**: ロー・ポケットペア (low_pair) + ドローなし on `AsKd7c` (MTT 50bb)

1. MV = **3** (low_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 3 + 0 = **3** → band: 弱ペア (TV 3-4)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][weak] = **30%**
4. α[mtt_50bb] (コンテキスト補正) = **+0pt**
5. β[mtt_50bb]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[trash] (ハンドクラス補正) = **-14pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 17%**

**例**: Aハイ (ace_high) + フラッシュドロー on `Jd8c3d` (MTT 50bb)

1. MV = **2** (ace_high)、DV = **2** (フラッシュドロー)
2. TV = MV + DV = 2 + 2 = **4** → band: 弱ペア (TV 3-4)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][weak] = **30%**
4. α[mtt_50bb] (コンテキスト補正) = **+0pt**
5. β[mtt_50bb]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 31%**

## mtt_50bb の 3 原則

1. **base そのまま使う**: α=+0 なので Vol2 で覚えた mtt_short base 5 値が
   そのまま予測値です。新たな数値は不要です。
2. **板分類で補正**: ε のみ慎重に。dry_high なら 0、low_dry/dynamic で -9/-11。
   paired で +2。
3. **cat_offset で +/-**: slowplay +6、trash -14、premium +7 は共通なので、
   手の種類別の微調整として加算します。
