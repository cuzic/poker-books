# 第11章 Turn 4 context——2nd barrel の判断

Turn 2nd barrel は cash と MTT 3 スタックの 4 context です。
Vol2 で覚えた base[turn] (全 band 6-7%) を共通基準とし、
context 別に α=-2〜+13、β=-4 で微調整します。

## Turn 4 context のパラメータ

A モデルで Turn は 4 context に分かれます。

| context | α | β (TV≥7) | base[turn] |
|---|---:|---:|---|
| cash_100bb_turn_btn | +1 | -5 | air 6 / weak 6 / mid 3 / strong 7 / nut 7 |
| mtt_25bb_turn_btn | -2 | -4 | (同上) |
| mtt_50bb_turn_btn | +1 | -4 | (同上) |
| mtt_100bb_turn_btn | **+13** | -4 | (同上) |

共通の特徴は「全 band で 6-7%」という極めて低い base 値です。
フロップで 1 度 cbet を打った後、ターンでも続行するのは例外的な選択であることを
base で表現しています。

## なぜ base が 6-7% なのか

Vol2 で覚えた turn context の base が「全 band でほぼ同じ 6-7%」となっているのは、
ターン 2nd barrel の頻度が GTO 上で「ハンド強度を問わず低い」という構造を
反映しています。

理由は 2 つあります。第 1 に、フロップで 1 度 cbet を打った時点で
「ベットレンジ」と「チェックレンジ」が分離されており、ターンでベットを続けるには
フロップから turn にかけて状況が好転している必要があるためです (例: 自分の役が
improve、bluff の equity が拡大、相手レンジが weaken)。

第 2 に、ターン全体での bet 頻度を 50% に抑えることで polarized な構造を
維持できます。Vol2 ch09 で扱った通り、turn 2nd barrel は「6 ベット中 4 check、
2 bet」の比率が標準です。

## mtt_100bb_turn_btn の α=+13

4 context の中で mtt_100bb_turn_btn のみ α=+13 と突出しています。
これは「MTT 100bb で flop cbet 後にターンに進む場合、続行率が想定より高い」
ことを示します。

MTT 100bb の場合、相手 BB の continue range がやや tight (cash より tight) なため、
フロップで cbet → call されて turn に進む場合、相手が確実に手を持っている可能性が
高くなります。逆に言えば「自分の continue 判断は wider に取れる」構造です。

この α=+13 を見落とすと、MTT 100bb で「ターンは check 一辺倒」となりがちで、
実際の GTO 戦略 (continued cbet が多め) からズレます。

## Turn 例題

### cash_100bb_turn_btn の代表例

**例**: トップペア (top_pair) + ドローなし on `KdTh4s` (Turn Cash100)

1. MV = **7** (top_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = Turn 2nd barrel → base = base[turn][strong] = **7%**
4. α[cash_100bb_turn_btn] (コンテキスト補正) = **+1pt**
5. β[cash_100bb_turn_btn]·I(TV≥7) (強ハンド補正) = **-5pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][cash] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 3%**

**例**: オーバーペア (overpair) + ドローなし on `9c4d2s` (Turn Cash100)

1. MV = **7** (overpair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = Turn 2nd barrel → base = base[turn][strong] = **7%**
4. α[cash_100bb_turn_btn] (コンテキスト補正) = **+1pt**
5. β[cash_100bb_turn_btn]·I(TV≥7) (強ハンド補正) = **-5pt**
6. cat[premium] (ハンドクラス補正) = **+7pt**
7. 板分類: Low Dry (T 以下の dry) → ε[low_dry][cash] (ボード補正) = **-9pt**

→ **連続 bet 頻度 ≈ 2%**

**例**: セット (set) + ドローなし on `Ks7d7c` (Turn Cash100)

1. MV = **9** (set)、DV = **0** (ドローなし)
2. TV = MV + DV = 9 + 0 = **9** → band: ナッツ (TV 9+)
3. ctx5 = Turn 2nd barrel → base = base[turn][nut] = **7%**
4. α[cash_100bb_turn_btn] (コンテキスト補正) = **+1pt**
5. β[cash_100bb_turn_btn]·I(TV≥7) (強ハンド補正) = **-5pt**
6. cat[slowplay] (ハンドクラス補正) = **+6pt**
7. 板分類: Paired (ペアボード) → ε[paired][cash] (ボード補正) = **+5pt**

→ **連続 bet 頻度 ≈ 14%**

### mtt_100bb_turn_btn (α=+13、続行率高め)

**例**: トップペア (top_pair) + ドローなし on `KdTh4s` (Turn MTT100)

1. MV = **7** (top_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = Turn 2nd barrel → base = base[turn][strong] = **7%**
4. α[mtt_100bb_turn_btn] (コンテキスト補正) = **+13pt**
5. β[mtt_100bb_turn_btn]·I(TV≥7) (強ハンド補正) = **-4pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 16%**

**例**: オーバーペア (overpair) + ドローなし on `9c4d2s` (Turn MTT100)

1. MV = **7** (overpair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = Turn 2nd barrel → base = base[turn][strong] = **7%**
4. α[mtt_100bb_turn_btn] (コンテキスト補正) = **+13pt**
5. β[mtt_100bb_turn_btn]·I(TV≥7) (強ハンド補正) = **-4pt**
6. cat[premium] (ハンドクラス補正) = **+7pt**
7. 板分類: Low Dry (T 以下の dry) → ε[low_dry][mtt_srp] (ボード補正) = **-9pt**

→ **連続 bet 頻度 ≈ 14%**

**例**: セカンドペア (second_pair) + フラッシュドロー on `KsJd6s` (Turn MTT100)

1. MV = **5** (second_pair)、DV = **2** (フラッシュドロー)
2. TV = MV + DV = 5 + 2 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = Turn 2nd barrel → base = base[turn][strong] = **7%**
4. α[mtt_100bb_turn_btn] (コンテキスト補正) = **+13pt**
5. β[mtt_100bb_turn_btn]·I(TV≥7) (強ハンド補正) = **-4pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 16%**

## Turn の 3 原則

1. **base[turn] = 全 band 6-7% を覚える**: ターン 2nd barrel は基本的に低頻度。
   「ターンに来たら check を考える」がデフォルト。
2. **mtt_100bb_turn_btn のみ α=+13 を意識**: 他 3 context は α が小さく、
   base 値そのままで概ね予測可能。
3. **β=-4 と cat_offset で微調整**: strong/nut バンドは少し抑制し、
   premium / slowplay 系で少し上げる。
