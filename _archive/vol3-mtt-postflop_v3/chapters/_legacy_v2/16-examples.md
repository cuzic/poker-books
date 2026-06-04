# 第16章 例題集——MTT 各 depth × SBR スイッチ練習

A モデルの計算を実戦スピードで回せるようになるための例題集です。
context 選択 → TV 計算 → band 判定 → α/β/cat/ε 加算 → freq 算出の 7 ステップを繰り返し練習します。
SRP 25bb / SRP 50bb / 3BP / Turn cbet の 4 カテゴリから合計 20 問を用意しました。
各問には A モデルの計算過程と GTO の方向比較を示します。

## 問題の使い方——7 ステップ計算フロー

A モデルを実戦で使うには、以下の 7 ステップを素早くこなす練習が必要です。

```
Step 1: MV/DV 判定
        MV: no_made_hand/ace_high/king_high=2, low_pair/underpair/third_pair=3,
            second_pair=5, top_pair/overpair=7, set/trips=8, two_pair+以上=9
        DV: no_draw/bdfd=0, gutshot=1, oesd/fd=2, combo=3

Step 2: TV = MV + DV → band 判定 (air/weak/mid/strong/nut)

Step 3: context 選択 (13 種から 1 つ)

Step 4: base[ctx5][band] を 25 セル表から lookup

Step 5: α + β·I(TV≥7) + cat_offset を加算

Step 6: 板分類 (paired/dynamic/dry_high/low_dry)

Step 7: ε[family][ctx_group] を加算 → 最終 freq
```

各例題には解答 (A モデル 計算値) と方向解説を掲載しています。
計算を先に自分で試し、答え合わせをする形で使ってください。

## 問題 1〜5: SRP 25bb（終盤）

SBR ≈ 25 の終盤 SRP (シングルレイズポット) です。
context は `mtt_25bb` (α=+36、β=-5、WRMSE 17.6%) を使います。

**α=+36 で全体的に大幅 wide cbet (Vol3 最大の α)、β=-5 と cat[slowplay]=+6 で
strong/nut は中庸、cat[trash]=-14 で low_pair は大幅 check 寄り**が特徴です。

### 問題 1〜5 解答（mtt_25bb）

**例**: トップペア (top_pair) + ドローなし on `Ks7d2c` (MTT 25bb)

1. MV = **7** (top_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][strong] = **58%**
4. α[mtt_25bb] (コンテキスト補正) = **+36pt**
5. β[mtt_25bb]·I(TV≥7) (強ハンド補正) = **-5pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 89%**

**例**: オーバーペア (overpair) + ドローなし on `Jd8c3s` (MTT 25bb)

1. MV = **7** (overpair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][strong] = **58%**
4. α[mtt_25bb] (コンテキスト補正) = **+36pt**
5. β[mtt_25bb]·I(TV≥7) (強ハンド補正) = **-5pt**
6. cat[premium] (ハンドクラス補正) = **+7pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 96%**

**例**: Aハイ (ace_high) + フラッシュドロー on `Qh8d4c` (MTT 25bb)

1. MV = **2** (ace_high)、DV = **2** (フラッシュドロー)
2. TV = MV + DV = 2 + 2 = **4** → band: 弱ペア (TV 3-4)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][weak] = **30%**
4. α[mtt_25bb] (コンテキスト補正) = **+36pt**
5. β[mtt_25bb]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 66%**

**例**: セット (set) + ドローなし on `7s7d2c` (MTT 25bb)

1. MV = **9** (set)、DV = **0** (ドローなし)
2. TV = MV + DV = 9 + 0 = **9** → band: ナッツ (TV 9+)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][nut] = **73%**
4. α[mtt_25bb] (コンテキスト補正) = **+36pt**
5. β[mtt_25bb]·I(TV≥7) (強ハンド補正) = **-5pt**
6. cat[slowplay] (ハンドクラス補正) = **+6pt**
7. 板分類: Paired (ペアボード) → ε[paired][mtt_srp] (ボード補正) = **+2pt**

→ **連続 bet 頻度 ≈ 98%**

**例**: ロー・ポケットペア (low_pair) + ドローなし on `Ah5s3c` (MTT 25bb)

1. MV = **3** (low_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 3 + 0 = **3** → band: 弱ペア (TV 3-4)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][weak] = **30%**
4. α[mtt_25bb] (コンテキスト補正) = **+36pt**
5. β[mtt_25bb]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[trash] (ハンドクラス補正) = **-14pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 52%**

**問題 1〜5 のポイント解説**:

- **問1 (top_pair on Ks7d2c)**: dry_high 板で ε=0。base 58 + α 36 + β -5 = **89%**。MTT 短スタックでは top_pair は ほぼ常に bet。
- **問2 (overpair on Jd8c3s)**: dynamic 板で ε=-11。base 58 + α 36 + β -5 + cat[premium] +7 + ε -11 = **85%**。dynamic でも premium は強気。
- **問3 (ace_high + fd on Qh8d4c)**: TV=2+2=4 → weak band。dynamic 板で ε=-11。base 30 + α 36 + ε -11 = **55%**。draw を含む弱手でも mtt_25bb は wide cbet 圏。
- **問4 (set on 9s9c4d)**: paired 板で ε=+2。base 73 (nut) + α 36 + β -5 + cat[slowplay] +6 + ε +2 = **98%** (clamp)。短スタックではナッツ系を slowplay せず value bet。
- **問5 (low_pair on Ah5s3c)**: dry_high 板で ε=0。base 30 + α 36 + cat[trash] -14 = **52%**。trash でも mtt_25bb の wide cbet で 50/50。

## 問題 6〜10: SRP 50bb（中盤）

SBR ≈ 50 の中盤 SRP です。
context は `mtt_50bb` (α=+0、β=-3、WRMSE 17.6%) を使います。

**α=+0 で Vol2 mtt_short base 値をほぼそのまま使う、cat[trash]=-14 で low_pair は控えめ、
板分類 ε で paired +2/dynamic -11/low_dry -9 と微調整**するのが特徴です。

### 問題 6〜10 解答（mtt_50bb）

**例**: セカンドペア (second_pair) + ドローなし on `Kh8d3s` (MTT 50bb)

1. MV = **5** (second_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 5 + 0 = **5** → band: 中ペア (TV 5-6)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][mid] = **35%**
4. α[mtt_50bb] (コンテキスト補正) = **+0pt**
5. β[mtt_50bb]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 35%**

**例**: ロー・ポケットペア (low_pair) + ドローなし on `Ah7s2c` (MTT 50bb)

1. MV = **3** (low_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 3 + 0 = **3** → band: 弱ペア (TV 3-4)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][weak] = **30%**
4. α[mtt_50bb] (コンテキスト補正) = **+0pt**
5. β[mtt_50bb]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[trash] (ハンドクラス補正) = **-14pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 17%**

**例**: トップペア (top_pair) + ドローなし on `As8d4c` (MTT 50bb)

1. MV = **7** (top_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][strong] = **58%**
4. α[mtt_50bb] (コンテキスト補正) = **+0pt**
5. β[mtt_50bb]·I(TV≥7) (強ハンド補正) = **-3pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 56%**

**例**: アンダーペア (underpair) + ドローなし on `Kd8c5s` (MTT 50bb)

1. MV = **3** (underpair)、DV = **0** (ドローなし)
2. TV = MV + DV = 3 + 0 = **3** → band: 弱ペア (TV 3-4)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][weak] = **30%**
4. α[mtt_50bb] (コンテキスト補正) = **+0pt**
5. β[mtt_50bb]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[premium] (ハンドクラス補正) = **+7pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 38%**

**例**: フラッシュ (flush) + ドローなし on `Qh9h3h` (MTT 50bb)

1. MV = **9** (flush)、DV = **0** (ドローなし)
2. TV = MV + DV = 9 + 0 = **9** → band: ナッツ (TV 9+)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][nut] = **73%**
4. α[mtt_50bb] (コンテキスト補正) = **+0pt**
5. β[mtt_50bb]·I(TV≥7) (強ハンド補正) = **-3pt**
6. cat[slowplay] (ハンドクラス補正) = **+6pt**
7. 板分類: Dynamic (モノトーン or 連結ツーフラ) → ε[dynamic][mtt_srp] (ボード補正) = **-11pt**

→ **連続 bet 頻度 ≈ 66%**

**問題 6〜10 のポイント解説**:

- **問6 (second_pair on Kh8d3s)**: dry_high 板で ε=0。base 35 (mid) + α 0 = **35%**。Vol2 base 値そのまま。
- **問7 (low_pair on Ah7s2c)**: dry_high 板で ε=0。base 37 (weak) + α 0 + cat[trash] -14 = **23%**。trash で大幅 check 寄り。
- **問8 (top_pair + CO on As8d4c)**: dry_high 板。base 58 + α 0 + β -3 = **55%**。mtt_50bb では position 補正なし。
- **問9 (underpair on Kd8c5s)**: dry_high 板。base 30 (weak) + α 0 + cat[premium] +7 = **37%**。premium でも TV=3 では check 寄り。
- **問10 (flush on Qh9h3h)**: dynamic 板で ε=-11。base 73 + α 0 + β -3 + cat[slowplay] +6 + ε -11 = **65%**。dynamic で slowplay 偏向。

## 問題 11〜15: 3BP（SPR 別）

3-bet pot (3BP) の IP cbet です。
SPR によって context が変わります。SPR を先に確認してから選択してください。

| SBR (スタック) | 3BP SPR (目安) | Context (α, β, WRMSE) |
|---|---|---|
| 20bb | ≈2.5 | mtt_3bp_20bb (α=-2、β=-15、WRMSE 21.4%) |
| 25bb | ≈2.7 | mtt_3bp_25bb (α=+3、β=-15、WRMSE 15.4%) |
| 50bb | ≈5.5 | mtt_3bp_50bb (α=+1、**β=+5**、WRMSE 9.3%) |
| 100bb | ≈11  | mtt_3bp_100bb (α=+0、**β=+8**、WRMSE 13.9%) |

**特徴**: 浅 (20/25bb) では β が大きく負で slowplay 顕著、深 (50/100bb) では β が正に転じて value bet 重視。

### 問題 11〜15 解答（3BP、SPR 別）

**例**: トップペア (top_pair) + ドローなし on `Ks9d4c` (3BP 50bb)

1. MV = **7** (top_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = 3-bet pot IP → base = base[3bp][strong] = **70%**
4. α[mtt_3bp_50bb] (コンテキスト補正) = **+1pt**
5. β[mtt_3bp_50bb]·I(TV≥7) (強ハンド補正) = **+5pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][3bp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 77%**

**例**: オーバーペア (overpair) + ドローなし on `Jd8c3s` (3BP 100bb)

1. MV = **7** (overpair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = 3-bet pot IP → base = base[3bp][strong] = **70%**
4. α[mtt_3bp_100bb] (コンテキスト補正) = **+0pt**
5. β[mtt_3bp_100bb]·I(TV≥7) (強ハンド補正) = **+8pt**
6. cat[premium] (ハンドクラス補正) = **+7pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][3bp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 85%**

**例**: セット (set) + ドローなし on `9s9d4c` (3BP 25bb)

1. MV = **9** (set)、DV = **0** (ドローなし)
2. TV = MV + DV = 9 + 0 = **9** → band: ナッツ (TV 9+)
3. ctx5 = 3-bet pot IP → base = base[3bp][nut] = **58%**
4. α[mtt_3bp_25bb] (コンテキスト補正) = **+3pt**
5. β[mtt_3bp_25bb]·I(TV≥7) (強ハンド補正) = **-15pt**
6. cat[slowplay] (ハンドクラス補正) = **+6pt**
7. 板分類: Paired (ペアボード) → ε[paired][3bp] (ボード補正) = **-1pt**

→ **連続 bet 頻度 ≈ 51%**

**例**: ロー・ポケットペア (low_pair) + OESD on `Kh8d7c` (3BP 50bb)

1. MV = **3** (low_pair)、DV = **2** (OESD)
2. TV = MV + DV = 3 + 2 = **5** → band: 中ペア (TV 5-6)
3. ctx5 = 3-bet pot IP → base = base[3bp][mid] = **61%**
4. α[mtt_3bp_50bb] (コンテキスト補正) = **+1pt**
5. β[mtt_3bp_50bb]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[trash] (ハンドクラス補正) = **-14pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][3bp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 48%**

**例**: Aハイ (ace_high) + ドローなし on `Qd7s3c` (3BP 20bb)

1. MV = **2** (ace_high)、DV = **0** (ドローなし)
2. TV = MV + DV = 2 + 0 = **2** → band: エアー (TV 0-2)
3. ctx5 = 3-bet pot IP → base = base[3bp][air] = **46%**
4. α[mtt_3bp_20bb] (コンテキスト補正) = **-2pt**
5. β[mtt_3bp_20bb]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][3bp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 44%**

**問題 11〜15 のポイント解説**:

- **問11 (top_pair、3BP 50bb)**: dry_high 板。base 70 (3bp/strong) + α 1 + β +5 = **76%**。深 3BP で top_pair は強気 bet。
- **問12 (overpair、3BP 100bb)**: dry_high 板。base 70 + α 0 + β +8 + cat[premium] +7 = **85%**。100bb 3BP の β=+8 と premium の合計で高頻度。
- **問13 (set、3BP 25bb)**: paired 板で ε=-1。base 58 (nut) + α 3 + β -15 + cat[slowplay] +6 + ε -1 = **51%**。SPR ≈2.7 の浅い 3BP では set を 50% slowplay。
- **問14 (low_pair + oesd、3BP 50bb)**: low_dry 板で ε=-2。TV = 2+2 = 4 weak band。base 50 + α 1 + cat[trash] -14 + ε -2 = **35%**。trash + low_dry で check 寄り。
- **問15 (ace_high、3BP 20bb)**: dry_high 板。base 50 (3bp/weak) + α -2 = **48%**。3BP 浅で trash でない ace_high は中庸な頻度。

## 問題 16〜20: Turn cbet（α シフト確認）

フロップでベットした後のターン 2nd barrel です。
context を Turn 版に切り替えます。

**Turn base[turn] 5 値**: air 6 / weak 6 / mid 3 / strong 7 / nut 7。フロップ base
(cash 44-62%) より大幅に低い値で、ターン全体が低頻度であることを base 自体が表現
しています。α/β はその上での微調整です。

| ターン context | α | β | WRMSE |
|---|---:|---:|---:|
| mtt_25bb_turn_btn | -2 | -4 | 7.5% |
| mtt_50bb_turn_btn | +1 | -4 | 14.5% |
| mtt_100bb_turn_btn | **+13** | -4 | 25.7% |
| cash_100bb_turn_btn | +1 | -5 | 15.6% |

mtt_100bb_turn_btn のみ α=+13 と突出。フロップ mtt_100bb (α=+26) の続行率
高めの傾向がターンにも残る構造です。

### 問題 16〜20 解答（Turn cbet）

**例**: トップペア (top_pair) + ドローなし on `Ks7d2c` (Turn MTT25)

1. MV = **7** (top_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = Turn 2nd barrel → base = base[turn][strong] = **7%**
4. α[mtt_25bb_turn_btn] (コンテキスト補正) = **-2pt**
5. β[mtt_25bb_turn_btn]·I(TV≥7) (強ハンド補正) = **-4pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 2%**

**例**: セカンドペア (second_pair) + ガットショット on `Kh8d3s` (Turn MTT50)

1. MV = **5** (second_pair)、DV = **1** (ガットショット)
2. TV = MV + DV = 5 + 1 = **6** → band: 中ペア (TV 5-6)
3. ctx5 = Turn 2nd barrel → base = base[turn][mid] = **3%**
4. α[mtt_50bb_turn_btn] (コンテキスト補正) = **+1pt**
5. β[mtt_50bb_turn_btn]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 5%**

**例**: オーバーペア (overpair) + ドローなし on `Jd8c5h` (Turn MTT100)

1. MV = **7** (overpair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = Turn 2nd barrel → base = base[turn][strong] = **7%**
4. α[mtt_100bb_turn_btn] (コンテキスト補正) = **+13pt**
5. β[mtt_100bb_turn_btn]·I(TV≥7) (強ハンド補正) = **-4pt**
6. cat[premium] (ハンドクラス補正) = **+7pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 23%**

**例**: ロー・ポケットペア (low_pair) + ドローなし on `Ah7s4c` (Turn MTT25)

1. MV = **3** (low_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 3 + 0 = **3** → band: 弱ペア (TV 3-4)
3. ctx5 = Turn 2nd barrel → base = base[turn][weak] = **6%**
4. α[mtt_25bb_turn_btn] (コンテキスト補正) = **-2pt**
5. β[mtt_25bb_turn_btn]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[trash] (ハンドクラス補正) = **-14pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 2%**

**例**: フラッシュ (flush) + ドローなし on `Qh8h3h` (Turn MTT50)

1. MV = **9** (flush)、DV = **0** (ドローなし)
2. TV = MV + DV = 9 + 0 = **9** → band: ナッツ (TV 9+)
3. ctx5 = Turn 2nd barrel → base = base[turn][nut] = **7%**
4. α[mtt_50bb_turn_btn] (コンテキスト補正) = **+1pt**
5. β[mtt_50bb_turn_btn]·I(TV≥7) (強ハンド補正) = **-4pt**
6. cat[slowplay] (ハンドクラス補正) = **+6pt**
7. 板分類: Dynamic (モノトーン or 連結ツーフラ) → ε[dynamic][mtt_srp] (ボード補正) = **-11pt**

→ **連続 bet 頻度 ≈ 2%**

**問題 16〜20 のポイント解説**:

- **問16 (top_pair、Turn 25bb)**: dry_high 板で ε=0。base 7 (turn/strong) + α -2 + β -4 = **2%** (clamp)。ターン続行は極稀。
- **問17 (second_pair + gutshot、Turn 50bb)**: dry_high 板。TV=6 mid band。base 3 + α 1 = **4%** (clamp)。ターン 2nd barrel の素地は極めて低い。
- **問18 (overpair、Turn 100bb)**: dry_high 板。base 7 + α 13 + β -4 + cat[premium] +7 = **23%**。α=+13 の lift で premium が 20%+。
- **問19 (low_pair、Turn 25bb)**: dry_high 板。base 6 (weak) + α -2 + cat[trash] -14 = **2%** (clamp)。ターンで low_pair 続行は zero に近い。
- **問20 (flush、Turn 50bb)**: dynamic 板で ε=-11。base 7 (nut) + α 1 + β -4 + cat[slowplay] +6 + ε -11 = **2%** (clamp)。dynamic でナッツでもターンはほぼ check。

## まとめ：例題集で学んだ 5 つのパターン

本章の例題を通じて確認した重要パターンを 5 点にまとめます。

1. **mtt_25bb は α=+36 で wide cbet**: 全 band で大幅 lift。top_pair/overpair は 80%+ bet、low_pair (trash -14) でも 50% 程度。Cash 感覚では mid band check しがちなので注意。
2. **mtt_50bb は base そのまま**: α=+0 で Vol2 mtt_short 値がそのまま使える。ε のみ慎重に。
3. **3BP の β 反転は決定的**: 浅 (20/25bb) β=-15、深 (50/100bb) β=+5〜+8。同じ set でも SPR 別で 25pt の差。SPR を先に確認してから context を選ぶ。
4. **ターンは base[turn] が 6-7% と低い**: フロップ 6-7 倍の差。Turn 続行は例外的選択であることを base で表現。
5. **限界 context は方向のみ**: mtt_100bb (25%)、mtt_100bb_turn_btn (25.7%) は exact 値より「bet か check か」の方向判断に絞る。
