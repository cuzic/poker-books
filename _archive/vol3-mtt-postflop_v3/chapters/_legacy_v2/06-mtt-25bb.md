# 第06章 MTT 25bb——wide cbet 特性 (α=+36)

MTT 25bb スタックは α=+36 という Vol3 で最も大きな lift を持つ context です。
ショートスタックで pot コミット圏が近いため、ブラフレンジ含めた wide cbet が
GTO 最適となります。β=-5、cat_offset 共通、板分類 ε で総合判断します。

## mtt_25bb の固有パラメータ

A モデル mtt_25bb で適用する補正は以下の通りです。

| layer | 値 | 意味 |
|---|---:|---|
| α (コンテキスト補正) | **+36pt** | wide cbet (Vol3 最大の α) |
| β (TV≥7 のみ) | **-5pt** | 強い役は base+α から少し抑える |
| cat_offset[slowplay] | +6pt | 共通 |
| cat_offset[trash] | -14pt | 共通 |
| cat_offset[premium] | +7pt | 共通 |
| ε[dynamic][mtt_srp] | -11pt | wet 板で 11pt 抑制 |
| ε[paired][mtt_srp] | +2pt | ペア板でやや上げる |
| ε[low_dry][mtt_srp] | -9pt | low_dry 板で 9pt 抑制 |

WRMSE は 17.6%。Vol3 全体の WRMSE 18.32% より良好です。

## α=+36 の意味

mtt_25bb の α=+36 は Vol3 で最大値です。25bb ショートスタックでは
SPR が約 4 と低く、pot コミット圏が近いため、ブラフレンジ含めた wide cbet が
GTO 最適となります。

例えば cash_100bb で 42% (mid band base) のハンドが、mtt_25bb では:

- base[mtt_short][mid] = 35%
- α[mtt_25bb] = +36
- cat[default] = 0
- ε[dry_high] = 0

合計 71% でほぼ常時 cbet となります。

この「mid band でも 70% bet」が mtt_25bb の最大特徴です。Cash 100bb の感覚で
「mid はチェック寄り」と判断すると、MTT 25bb で大きく外します。

## β=-5 と slowplay の関係

β = -5 は TV≥7 で 5pt 抑制ですが、これは「α=+36 で底上げした分のうち
strong/nut バンドは少し抑える」という構造です。

slowplay カテゴリ (set/two_pair/straight/flush) は cat_offset で +6 加算されますが、
β=-5 と相殺してネット +1pt のみ。「ナッツ系も平均的な頻度で bet」となります。

premium カテゴリ (overpair/underpair) は cat_offset +7 + β -5 = +2pt。
ほぼ base+α と同じ頻度で bet し、value 重視のシンプル戦略です。

## MTT 25bb の実戦例題

### MTT 25bb で 6 つの代表局面

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

**例**: ロー・ポケットペア (low_pair) + ドローなし on `Ah7s3c` (MTT 25bb)

1. MV = **3** (low_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 3 + 0 = **3** → band: 弱ペア (TV 3-4)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][weak] = **30%**
4. α[mtt_25bb] (コンテキスト補正) = **+36pt**
5. β[mtt_25bb]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[trash] (ハンドクラス補正) = **-14pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 52%**

**例**: セット (set) + ドローなし on `Ks7d7c` (MTT 25bb)

1. MV = **9** (set)、DV = **0** (ドローなし)
2. TV = MV + DV = 9 + 0 = **9** → band: ナッツ (TV 9+)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][nut] = **73%**
4. α[mtt_25bb] (コンテキスト補正) = **+36pt**
5. β[mtt_25bb]·I(TV≥7) (強ハンド補正) = **-5pt**
6. cat[slowplay] (ハンドクラス補正) = **+6pt**
7. 板分類: Paired (ペアボード) → ε[paired][mtt_srp] (ボード補正) = **+2pt**

→ **連続 bet 頻度 ≈ 98%**

**例**: Aハイ (ace_high) + フラッシュドロー on `Jd8c3d` (MTT 25bb)

1. MV = **2** (ace_high)、DV = **2** (フラッシュドロー)
2. TV = MV + DV = 2 + 2 = **4** → band: 弱ペア (TV 3-4)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][weak] = **30%**
4. α[mtt_25bb] (コンテキスト補正) = **+36pt**
5. β[mtt_25bb]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 66%**

**例**: セカンドペア (second_pair) + ガットショット on `Kh8d5c` (MTT 25bb)

1. MV = **5** (second_pair)、DV = **1** (ガットショット)
2. TV = MV + DV = 5 + 1 = **6** → band: 中ペア (TV 5-6)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][mid] = **35%**
4. α[mtt_25bb] (コンテキスト補正) = **+36pt**
5. β[mtt_25bb]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 70%**

## Dynamic 板での例外

### dynamic 板では ε=-11 で慎重に

**例**: トップペア (top_pair) + ドローなし on `9s8s6s` (MTT 25bb)

1. MV = **7** (top_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][strong] = **58%**
4. α[mtt_25bb] (コンテキスト補正) = **+36pt**
5. β[mtt_25bb]·I(TV≥7) (強ハンド補正) = **-5pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dynamic (モノトーン or 連結ツーフラ) → ε[dynamic][mtt_srp] (ボード補正) = **-11pt**

→ **連続 bet 頻度 ≈ 79%**

**例**: トップペア (top_pair) + フラッシュドロー on `KsQsTs` (MTT 25bb)

1. MV = **7** (top_pair)、DV = **2** (フラッシュドロー)
2. TV = MV + DV = 7 + 2 = **9** → band: ナッツ (TV 9+)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][nut] = **73%**
4. α[mtt_25bb] (コンテキスト補正) = **+36pt**
5. β[mtt_25bb]·I(TV≥7) (強ハンド補正) = **-5pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dynamic (モノトーン or 連結ツーフラ) → ε[dynamic][mtt_srp] (ボード補正) = **-11pt**

→ **連続 bet 頻度 ≈ 94%**

## mtt_25bb の 4 原則

mtt_25bb context を実戦で使うための原則は以下の通りです。

1. **mid バンドでも bet 寄り**: α=+36 で底上げされるため、「Cash の感覚」より
   大幅に高い頻度で cbet します。second_pair でも 70% bet となるのが典型です。
2. **strong/nut も大きく上げない**: β=-5 と cat_offset の組合せで、強い役も
   平均的な頻度で bet。slowplay は積極的に検討しない。
3. **low_pair (trash -14)**: cat_offset -14 で大きく抑制。「showdown value がない
   弱ペア」は check の選択肢を優先。
4. **Dynamic 板で ε=-11 を引く**: モノトーン板や連結ツーフラ板では、α=+36 で
   上げた分から 11pt 抑制。それでも base+α-11+0 = base + 25 で十分 wide。
