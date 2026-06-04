# 第04章 板分類 ε——C3 軸で wet/dry の差を吸収

A モデルの C3 軸 (板分類 ε) は flop ボードを 4 family に分類し、
ctx_group (cash / mtt_srp / 3bp) ごとに頻度補正を加算します。
Dynamic 板 (wet) では cash で -21pt と大きく cbet を減らすのが本軸の中核です。

## 板分類の 4 family ロジック

1. **paired**: フロップ 3 枚に同ランクが含まれる
2. **dynamic**: モノトーン (3 枚同スート)、または (ストレート連結 + ツーフラ)
3. **dry_high**: 上記以外で、最高ランクが J 以上 (**baseline**、補正なし)
4. **low_dry**: 上記以外で、最高ランクが T 以下

フロップ 3 枚を見て、上から順に判定します。最初に該当した family を採用します。

paired は **ボード 3 枚に同ランクが含まれる** ボードです。例: 998 / KK4 / 422。
ペアボードでは相手のレンジから set/quads の出現確率が低く (相手は通常 pre で
raise しないため)、自分の overpair が相対的に強くなる構造です。

dynamic は **モノトーン (3 枚同スート)、または (ストレート連結 + ツーフラ)** です。
例: 8s7s6s (モノトーン)、9s8c7d (連結ツーフラ)。
Wet な board で draw が多く、相手の continue range が広くなり、自分のレンジが
heads down に弱くなる構造です。

dry_high は **paired / dynamic に該当せず、最高ランクが J 以上** です (**baseline**)。
例: AsKd4c / QcTh2s。プリフロップで自分がレンジ有利な典型ボードで、補正は 0 です。

low_dry は **paired / dynamic に該当せず、最高ランクが T 以下** です。
例: Tc6s2d / 8h4c3s。プリフロップで自分のレンジ有利が薄く、cbet を控えめに
する family です。

## ε 表——4 family × 3 ctx_group

### Board family × ctx_group の ε

| Board family | Cash | MTT SRP | 3-bet Pot |
|---|---:|---:|---:|
| Dry High (J 以上のハイカード dry) | +0pt | +0pt | +0pt |
| Paired (ペアボード) | +5pt | +2pt | -1pt |
| Dynamic (モノトーン or 連結ツーフラ) | -21pt | -11pt | -6pt |
| Low Dry (T 以下の dry) | -9pt | -9pt | -2pt |

ctx_group は context 13 を 3 つに集約したもので、cash (cash_100bb と turn_cash100)、
mtt_srp (MTT 4 スタックの flop と turn)、3bp (3-bet pot 4 スタック) です。
Vol3 全体で ε は 9 数値 (3 group × 3 non-baseline family) のみです。

この 9 数値を覚えれば、すべての context で板分類による頻度補正を加算できます。

## Dynamic 板の -21pt は何を意味するか (cash)

最も大きな ε は cash の dynamic 板で -21pt です。これは「Cash 100bb で
モノトーン板や連結ツーフラ板では、base から **21pt 下げて** cbet する」
ことを意味します。

例えば top_pair on 9s8s6s (dynamic, cash) の場合:

- base[cash][strong] = 57% (top_pair MV=7 → strong band)
- α[cash_100bb] = +2
- β[cash_100bb] · I(TV≥7) = -0 (TV=7、β=0)
- cat[default] = 0
- ε[dynamic][cash] = **-21**
- 合計 = 57 + 2 - 0 + 0 - 21 = **38%** → check 寄り

同じ top_pair でも dry_high 板 (AsKd7c) では 59% で bet 寄りでした。
板テクスチャだけで 21pt の差が出ます。

## MTT SRP / 3bp での ε は緩い

ε[dynamic][mtt_srp] = -11、ε[dynamic][3bp] = -6 と、cash の -21 より緩い値です。
これは「深いスタック (cash 100bb) ほど wet 板での cbet 削減が大きく、
浅いスタック (MTT / 3bp) では削減が緩い」という構造を示します。

深いスタックでは「ブラフをそのまま 3 ストリート続けるコスト」が大きいので、
wet 板では早めに check の選択肢を残します。浅いスタックでは「コミット判断が近い」
ため、wet 板でも protect bet として cbet を選ぶ頻度が高くなります。

## 板分類 ε 適用例

**例**: トップペア (top_pair) + ドローなし on `9s8s6s` (Cash 100bb)

1. MV = **7** (top_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = Cash 100bb → base = base[cash][strong] = **57%**
4. α[cash_100bb] (コンテキスト補正) = **+2pt**
5. β[cash_100bb]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dynamic (モノトーン or 連結ツーフラ) → ε[dynamic][cash] (ボード補正) = **-21pt**

→ **連続 bet 頻度 ≈ 38%**

**例**: トップペア (top_pair) + ドローなし on `AsKd7c` (Cash 100bb)

1. MV = **7** (top_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = Cash 100bb → base = base[cash][strong] = **57%**
4. α[cash_100bb] (コンテキスト補正) = **+2pt**
5. β[cash_100bb]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][cash] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 59%**

**例**: トップペア (top_pair) + ドローなし on `6h4c2d` (Cash 100bb)

1. MV = **7** (top_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = Cash 100bb → base = base[cash][strong] = **57%**
4. α[cash_100bb] (コンテキスト補正) = **+2pt**
5. β[cash_100bb]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Low Dry (T 以下の dry) → ε[low_dry][cash] (ボード補正) = **-9pt**

→ **連続 bet 頻度 ≈ 50%**

**例**: オーバーペア (overpair) + ドローなし on `7s7c2d` (3BP 50bb)

1. MV = **7** (overpair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = 3-bet pot IP → base = base[3bp][strong] = **70%**
4. α[mtt_3bp_50bb] (コンテキスト補正) = **+1pt**
5. β[mtt_3bp_50bb]·I(TV≥7) (強ハンド補正) = **+5pt**
6. cat[premium] (ハンドクラス補正) = **+7pt**
7. 板分類: Paired (ペアボード) → ε[paired][3bp] (ボード補正) = **-1pt**

→ **連続 bet 頻度 ≈ 82%**

## 板分類のコツ (3 秒で判定)

実戦での 3 秒判定は以下のフローです。

**ステップ A**: 3 枚に同ランクあり? → Yes → **paired**
**ステップ B**: モノトーン or (連結 + ツーフラ)? → Yes → **dynamic**
**ステップ C**: 最高ランク J 以上? → Yes → **dry_high** (baseline、ε=0)
**ステップ D**: それ以外 → **low_dry**

慣れれば 2-3 秒で判定できます。境界例 (連結だが ペアあり: 998 など) は
上位の paired が優先なので paired を選びます。
