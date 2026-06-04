# 第03章 Category offset——slowplay / trash / premium

A モデルの category offset は hand category 別の頻度補正です。
slowplay (+6)、trash (-14)、premium (+7) の 3 つで、context を問わず適用します。
本章では各カテゴリの定義と適用例を扱います。

## Category offset 表

### hand category × offset

| Category | 含まれる役 | ハンドクラス補正 |
|---|---|---:|
| default | 通常 (top_pair / second_pair / 等) | +0pt |
| slowplay | set / trips / two_pair / fullhouse / flush / straight / quads | +6pt |
| trash | low_pair | -14pt |
| premium | overpair / underpair | +7pt |

Category offset は context 共通です。13 context どれでも同じ値を加算します。
4 カテゴリ (default / slowplay / trash / premium) は MV テーブルの hand type から
機械的に判定できるので、追加の判断ステップは不要です。

## slowplay カテゴリ (+6pt)

slowplay カテゴリには **set / trips / two_pair / fullhouse / flush / straight / quads**
が含まれます。MV は 8-9 (strong/nut バンド) です。

offset +6 は「nut に近い役は base より +6pt bet する」という意味です。
Vol2 では nut バンドに value bet 寄りの値が既に設定されていますが、
Vol3 ではさらに「特に強い役 (slowplay 候補) を識別」して微調整します。

ただし 3BP 浅 (mtt_3bp_25bb 等) では β = -15 が同時に効くため、
slowplay +6 と β -15 の合計で -9pt 程度の slowplay 傾向になります。
「ナッツ系を持っているからベットせよ」とは限らない、相手のレンジ構成に
合わせた判断が必要です。

## trash カテゴリ (-14pt)

trash カテゴリは **low_pair** (MV=3) のみです。22-55 の低ペア (ボードに対して
アンダーペアでも highest pair に届かない) が該当します。

offset -14 は「low_pair は base より 14pt 下げてベットする」という意味です。
Vol2 の low_pair 例外 -10pt より少し厳しめの値です。

理由は ch02 (Vol2) で扱った通り、「showdown value がない」「チェックレイズに弱い」
ためです。Vol3 ではこの傾向が context 共通で見られることを confirm しています。

## premium カテゴリ (+7pt)

premium カテゴリには **overpair / underpair** が含まれます。

overpair はボードの最高ランクより高い pocket pair (例: 88 on 752)、
underpair はボードの最高ランクより低いが top pair より高い pocket pair (例: 88 on T75) です。

offset +7 は「オーバーペア系は強気に value bet」を意味します。
これらのハンドは pot コミットしてしまえば多くのワーストハンドから call が取れるため、
base より bet 寄りに調整します。

ただし dry な板 (paired ε=+5、low_dry ε=-9) と dynamic な板 (ε=-21) で
条件が異なるため、ε と組み合わせて最終判断します。

## default カテゴリ (offset なし)

slowplay / trash / premium に含まれないハンドはすべて default として扱い、
offset 0 (補正なし) で base 値そのまま使います。

具体的には top_pair / second_pair / third_pair / ace_high / king_high /
no_made_hand など、MV=2-7 のうち category 指定がないものが該当します。

default カテゴリの判定は「**まず category を確認し、該当しなければ default**」という
順序で行います。

## Category offset 適用例

**例**: セット (set) + ドローなし on `9s9c4d` (Cash 100bb)

1. MV = **9** (set)、DV = **0** (ドローなし)
2. TV = MV + DV = 9 + 0 = **9** → band: ナッツ (TV 9+)
3. ctx5 = Cash 100bb → base = base[cash][nut] = **62%**
4. α[cash_100bb] (コンテキスト補正) = **+2pt**
5. β[cash_100bb]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[slowplay] (ハンドクラス補正) = **+6pt**
7. 板分類: Paired (ペアボード) → ε[paired][cash] (ボード補正) = **+5pt**

→ **連続 bet 頻度 ≈ 75%**

**例**: ロー・ポケットペア (low_pair) + ドローなし on `AsKd7c` (Cash 100bb)

1. MV = **3** (low_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 3 + 0 = **3** → band: 弱ペア (TV 3-4)
3. ctx5 = Cash 100bb → base = base[cash][weak] = **37%**
4. α[cash_100bb] (コンテキスト補正) = **+2pt**
5. β[cash_100bb]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[trash] (ハンドクラス補正) = **-14pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][cash] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 26%**

**例**: オーバーペア (overpair) + ドローなし on `8s5c2d` (MTT 50bb)

1. MV = **7** (overpair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][strong] = **58%**
4. α[mtt_50bb] (コンテキスト補正) = **+0pt**
5. β[mtt_50bb]·I(TV≥7) (強ハンド補正) = **-3pt**
6. cat[premium] (ハンドクラス補正) = **+7pt**
7. 板分類: Low Dry (T 以下の dry) → ε[low_dry][mtt_srp] (ボード補正) = **-9pt**

→ **連続 bet 頻度 ≈ 54%**

**例**: ツーペア (two_pair) + ドローなし on `KsJd6c` (3BP 50bb)

1. MV = **8** (two_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 8 + 0 = **8** → band: 強ペア (TV 7-8)
3. ctx5 = 3-bet pot IP → base = base[3bp][strong] = **70%**
4. α[mtt_3bp_50bb] (コンテキスト補正) = **+1pt**
5. β[mtt_3bp_50bb]·I(TV≥7) (強ハンド補正) = **+5pt**
6. cat[slowplay] (ハンドクラス補正) = **+6pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][3bp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 82%**

## Size 軸を採用しない理由

旧 Vol3 (旧 5 軸モデル) では「33% small bet vs 116% overbet」の Size 軸を
扱っていました。A モデルでは Size 軸を廃止し、すべてのケースで 33% small bet
を前提とした頻度予測のみを行います。

理由は 2 つあります。第 1 に、Size 軸を導入しても WRMSE が大きく改善しない
ことが実測で判明したためです (band 集約後は Size 別の差が小さくなる)。
第 2 に、Size 判断は別の章 (Vol2 ch05) で扱う方が読者の負担が少ないためです。

Overbet (116%) を使うべき場面については Vol2 ch05 で polarized board の分類で扱います。
本書 ch11 (Turn) でも overbet 系の議論を行います。
