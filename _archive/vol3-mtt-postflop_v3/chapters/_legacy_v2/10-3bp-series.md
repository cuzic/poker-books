# 第10章 3-bet pot シリーズ——SPR 別の β 大反転

3-bet pot 4 context (20/25/50/100bb) は β が **-15 から +8 まで 23pt の差** という
大きな分散を持つ context 群です。SPR の違いで strong/nut の slowplay 比率が
劇的に変わる構造を理解します。

## 3BP 4 context のパラメータ

A モデルで 3-bet pot は 4 つに細分化されています。

| context | α | β (TV≥7) | 特徴 |
|---|---:|---:|---|
| mtt_3bp_20bb | -2 | **-15** | 極浅、slowplay 顕著 |
| mtt_3bp_25bb | +3 | **-15** | 浅 3BP の標準 |
| mtt_3bp_50bb | +1 | **+5** | β が正に転じる |
| mtt_3bp_100bb | +0 | **+8** | 最も bet 寄り |

α は -2 から +3 で大きく変わりませんが、β は **-15 から +8 まで 23pt の差** が
あります。3BP では strong/nut バンドの扱いが SPR で大きく変わる構造です。

## β=-15 の意味 (浅 3BP)

mtt_3bp_20bb と mtt_3bp_25bb の β=-15 は、「浅い 3BP では強い役 (TV≥7) を
slowplay する比率が高い」ことを示します。

浅 3BP では SPR が 3 前後と非常に低く、ベットすると pot コミット圏に入ります。
強い役を持っていると相手が早期 fold してしまい、追加 value が取れません。
逆にチェックバックして相手のブラフを誘発する方が EV が高くなります。

cat_offset[slowplay] = +6 と組み合わせると、合計で -9pt の slowplay 補正に
なります。「set でも 50% は check」というレンジ構成です。

## β=+8 の意味 (深 3BP)

mtt_3bp_100bb の β=+8 は、「深い 3BP では強い役で **多めに** bet」を示します。

深い 3BP では SPR が高く (約 8-10)、ベットしても 3 ストリート構築の余裕があり、
相手の lighter な call から value を取れます。strong/nut バンドを wide に bet し、
slowplay 比率を下げる構造です。

cat_offset[slowplay] = +6 と組み合わせると、合計で +14pt の lift。
「set / two_pair はほぼ常時 bet」というレンジ構成です。

## β 反転の数値例

同じ set on Ks7d2c で 4 つの 3BP を比較します。

| context | base | α | β | cat[slowplay] | ε[dry_high] | 合計 |
|---|---:|---:|---:|---:|---:|---:|
| mtt_3bp_20bb | 58% (3bp/nut) | -2 | -15 | +6 | 0 | **47%** |
| mtt_3bp_25bb | 58% | +3 | -15 | +6 | 0 | **52%** |
| mtt_3bp_50bb | 58% | +1 | +5 | +6 | 0 | **70%** |
| mtt_3bp_100bb | 58% | +0 | +8 | +6 | 0 | **72%** |

同じ set でも SPR 別で 25pt の差。3BP では「スタックサイズを確認してから
bet/check を決める」が必須です。

## 3BP の実戦例題

### mtt_3bp_25bb (β=-15、slowplay 顕著)

**例**: セット (set) + ドローなし on `Ks7d2c` (3BP 25bb)

1. MV = **9** (set)、DV = **0** (ドローなし)
2. TV = MV + DV = 9 + 0 = **9** → band: ナッツ (TV 9+)
3. ctx5 = 3-bet pot IP → base = base[3bp][nut] = **58%**
4. α[mtt_3bp_25bb] (コンテキスト補正) = **+3pt**
5. β[mtt_3bp_25bb]·I(TV≥7) (強ハンド補正) = **-15pt**
6. cat[slowplay] (ハンドクラス補正) = **+6pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][3bp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 52%**

**例**: トップペア (top_pair) + ドローなし on `Ks7d2c` (3BP 25bb)

1. MV = **7** (top_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = 3-bet pot IP → base = base[3bp][strong] = **70%**
4. α[mtt_3bp_25bb] (コンテキスト補正) = **+3pt**
5. β[mtt_3bp_25bb]·I(TV≥7) (強ハンド補正) = **-15pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][3bp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 58%**

**例**: オーバーペア (overpair) + ドローなし on `9c4d2s` (3BP 25bb)

1. MV = **7** (overpair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = 3-bet pot IP → base = base[3bp][strong] = **70%**
4. α[mtt_3bp_25bb] (コンテキスト補正) = **+3pt**
5. β[mtt_3bp_25bb]·I(TV≥7) (強ハンド補正) = **-15pt**
6. cat[premium] (ハンドクラス補正) = **+7pt**
7. 板分類: Low Dry (T 以下の dry) → ε[low_dry][3bp] (ボード補正) = **-2pt**

→ **連続 bet 頻度 ≈ 63%**

**例**: ロー・ポケットペア (low_pair) + ドローなし on `Jd8c3s` (3BP 25bb)

1. MV = **3** (low_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 3 + 0 = **3** → band: 弱ペア (TV 3-4)
3. ctx5 = 3-bet pot IP → base = base[3bp][weak] = **50%**
4. α[mtt_3bp_25bb] (コンテキスト補正) = **+3pt**
5. β[mtt_3bp_25bb]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[trash] (ハンドクラス補正) = **-14pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][3bp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 39%**

### mtt_3bp_100bb (β=+8、深 3BP)

**例**: セット (set) + ドローなし on `Ks7d2c` (3BP 100bb)

1. MV = **9** (set)、DV = **0** (ドローなし)
2. TV = MV + DV = 9 + 0 = **9** → band: ナッツ (TV 9+)
3. ctx5 = 3-bet pot IP → base = base[3bp][nut] = **58%**
4. α[mtt_3bp_100bb] (コンテキスト補正) = **+0pt**
5. β[mtt_3bp_100bb]·I(TV≥7) (強ハンド補正) = **+8pt**
6. cat[slowplay] (ハンドクラス補正) = **+6pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][3bp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 72%**

**例**: ツーペア (two_pair) + ドローなし on `KsJd6c` (3BP 100bb)

1. MV = **8** (two_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 8 + 0 = **8** → band: 強ペア (TV 7-8)
3. ctx5 = 3-bet pot IP → base = base[3bp][strong] = **70%**
4. α[mtt_3bp_100bb] (コンテキスト補正) = **+0pt**
5. β[mtt_3bp_100bb]·I(TV≥7) (強ハンド補正) = **+8pt**
6. cat[slowplay] (ハンドクラス補正) = **+6pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][3bp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 84%**

**例**: オーバーペア (overpair) + ドローなし on `8s5c2d` (3BP 100bb)

1. MV = **7** (overpair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = 3-bet pot IP → base = base[3bp][strong] = **70%**
4. α[mtt_3bp_100bb] (コンテキスト補正) = **+0pt**
5. β[mtt_3bp_100bb]·I(TV≥7) (強ハンド補正) = **+8pt**
6. cat[premium] (ハンドクラス補正) = **+7pt**
7. 板分類: Low Dry (T 以下の dry) → ε[low_dry][3bp] (ボード補正) = **-2pt**

→ **連続 bet 頻度 ≈ 83%**

**例**: トップペア (top_pair) + OESD on `9c8d6h` (3BP 100bb)

1. MV = **7** (top_pair)、DV = **2** (OESD)
2. TV = MV + DV = 7 + 2 = **9** → band: ナッツ (TV 9+)
3. ctx5 = 3-bet pot IP → base = base[3bp][nut] = **58%**
4. α[mtt_3bp_100bb] (コンテキスト補正) = **+0pt**
5. β[mtt_3bp_100bb]·I(TV≥7) (強ハンド補正) = **+8pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Low Dry (T 以下の dry) → ε[low_dry][3bp] (ボード補正) = **-2pt**

→ **連続 bet 頻度 ≈ 65%**

## 3BP の 4 原則

1. **SPR で context を確定**: 3BP に入ったらまず 20/25/50/100bb の判定。
   β が ±15pt 範囲で動くため、context ミスは致命的。
2. **浅 3BP は slowplay 優先**: β=-15、cat[slowplay]=+6 で合計 -9pt。
   set / two_pair は check が標準。
3. **深 3BP は value bet 優先**: β=+8、cat[slowplay]=+6 で合計 +14pt。
   set / two_pair は wide に bet。
4. **板分類 ε[3bp] は緩い**: paired -1 / dynamic -6 / low_dry -2 で
   SRP より小さい振れ幅。
