# 第11章 Turn cbet 4 context——α=-0.35 シフトと context 別調整

ターン 2nd barrel は「フロップ比 α -35pt シフト + β 廃止」が基本ルールです。
4 turn context（mtt_25bb_turn_btn / mtt_50bb_turn_btn / mtt_100bb_turn_btn / cash_100bb_turn_btn）は
いずれも α ≈ -0.30〜-0.41、β ≈ 0 という共通構造を持ちます。
最高精度は mtt_25bb_turn_btn（WRMSE 7.02%）、最低精度は mtt_100bb_turn_btn（WRMSE 26.95%）です。

## Flop → Turn 変換ルール——α -35、β 廃止

フロップで cbet を打った後、ターンカードが落ちて 2nd barrel を検討する際は、
フロップ context から turn context へ切り替えます。
この切り替えで 2 つの変換が自動的に行われます。

**変換ルール①: α を約 -35pt シフト**。
フロップで α=+6pt だった mtt_25bb は、ターンで α=-41pt となります（差 -47pt）。
この変換は「ターン全体の bet 頻度がフロップより約 35pt 低下する」というGTO実測値に対応しています。
GTO 実測ではフロップ平均 bet 頻度が約 55% なのに対し、ターンは 35〜45% 程度に減少します。

**変換ルール②: β ≈ 0（β 廃止）**。
フロップでは強い役（CBS≥7）に β による追加 lift が与えられましたが、
ターンでは β がほぼゼロになります。
これは「ターンでは役の絶対的な強さよりも、ターンカードとのレンジ相性が支配的になる」ためです。
CBS が高くても、ターンカードが相手のレンジを強化する場合は bet 頻度が落ちます。

context 切り替えの実装は単純で、mtt_25bb で計算していた場合は mtt_25bb_turn_btn に、
mtt_50bb なら mtt_50bb_turn_btn に切り替えるだけです。
ポジション補正（pos_lift）はターン context では全ポジション 0 となり、
A-x range bet（ax_range_bet）も 0 です。

## 4 context 比較——WRMSE と α の違い

4 turn context の α 値を比較すると、mtt_25bb_turn が -0.41 と最も大きく（最も控えめ）、
mtt_100bb_turn が -0.26 と最も小さい（相対的に bet 寄り）という傾向があります。
これはフロップ context の特性を引き継いでいる部分があり、
mtt_100bb の wide cbet 特性がターンでも α のシフト量を小さくしています。

精度面では mtt_25bb_turn_btn が WRMSE 7.02% と全 13 context 中最高精度を誇ります。
一方 mtt_100bb_turn_btn は WRMSE 26.95% と最低精度であり、フロップ mtt_100bb（WRMSE 21.95%）同様、
注意が必要な context です。

### Turn 4 context パラメータ比較（full_context_params の turn 系列）

| Context | α | β | slowplay | trash | premium | SB lift | wide lift | A-x lift |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| cash_100bb | +0 | -2 | +2 | -23 | +15 | -8 | +10 | +0 |
| mtt_25bb | +6 | +31 | -28 | -23 | +15 | -10 | +13 | +30 |
| mtt_50bb | -4 | +19 | -12 | -35 | +20 | -29 | +0 | +11 |
| mtt_3bp_20bb | +2 | +14 | -40 | -3 | -4 | +0 | +0 | +0 |
| mtt_3bp_25bb | +9 | +19 | -66 | -44 | -9 | +0 | +0 | +0 |
| mtt_3bp_50bb | +7 | +30 | -40 | -45 | +14 | +0 | +0 | +0 |
| mtt_3bp_100bb | +5 | +30 | -33 | -48 | +20 | +0 | +0 | +0 |
| mtt_25bb_turn_btn | -41 | +1 | -28 | -1 | +8 | +0 | +0 | +0 |
| mtt_50bb_turn_btn | -37 | -0 | -25 | -3 | +10 | +0 | +0 | +0 |
| mtt_100bb_turn_btn | -26 | -0 | -26 | -14 | +32 | +0 | +0 | +0 |
| cash_100bb_turn_btn | -37 | +0 | -27 | -8 | +22 | +0 | +0 | +0 |
| mtt_3bp_ip | +2 | +14 | -40 | -3 | -4 | +0 | +0 | +0 |
| mtt_200bb | -4 | +11 | -15 | -31 | +14 | -34 | +0 | +9 |
| mtt_100bb | +15 | +9 | -17 | -19 | +8 | -11 | +17 | +28 |

### mtt_25bb_turn_btn——WRMSE 7.02%（全 context 最高精度）

mtt_25bb_turn_btn の特徴は α=-0.41 という最も大きな下方シフトです。
これは 25bb という浅いスタックでは、ターン移行後のコミット判断が明確になるため、
bet/check の分岐がよりシンプルになり、モデルの精度が上がることを意味します。
β=+0.01 はほぼゼロであり、強い役への追加 lift はありません。
off_trash=-0.01 はフロップ(-0.23)より大幅に緩和されており、
low_pair でもターンでは一部 bet 有力になっています。

### mtt_50bb_turn_btn——WRMSE 14.44%

mtt_50bb_turn_btn は α=-0.37、β=0.00 の標準的なターン構造です。
off_slowplay=-0.25 はフロップ(-0.12)より強まり、ターンではセット等が check 傾向が増します。
off_premium=+0.10 でオーバーペア・アンダーペアは bet 有力です。

### mtt_100bb_turn_btn——WRMSE 26.95%（要注意）

mtt_100bb_turn_btn は α=-0.26 と他のターン context より α のシフトが小さいです。
しかし WRMSE 26.95% という精度の低さが示すように、100bb context のターンは
モデルの予測精度が最も低い領域です。フロップ mtt_100bb（WRMSE 21.95%）の精度問題が
ターンでも継続しており、100bb のターンでは「参考程度に使う」意識が重要です。
off_premium=+0.32 が突出して高く、ターンではオーバーペアの bet 頻度が高まる特徴があります。

### cash_100bb_turn_btn——WRMSE 16.11%

cash_100bb_turn_btn は α=-0.37 で mtt_50bb_turn と同じ水準です。
フロップ cash_100bb は polarize_enabled=True でしたが、
ターン context では polarize_enabled=False となり、常に 33% サイズで計算します。
off_trash=-0.08 は mtt_50bb_turn(-0.03)より少し厳しく、low_pair の bet 頻度は低めです。

## Trash（low_pair）のターン変化

フロップでの off_trash は -0.23〜-0.35 と大きく bet を抑制していましたが、
ターン context では -0.01〜-0.14 と大幅に緩和されています。

この変化は「low_pair がターンでは相対的に bet 有力になる」ことを示します。
ターンで low_pair が bet 有力になる理由は主に 2 つです。
第一に、フロップで check-back した後にターンで bet するプローブ的な意味があります。
第二に、ターンのカードが low_pair のレンジを若干強化する場合があります。

最も緩和されているのは mtt_25bb_turn(-0.01)で、
25bb ターンでは low_pair もほぼ通常の bet 頻度となります。
逆に mtt_100bb_turn(-0.14)は off_trash がターン中で最も大きく、
100bb ターンでも low_pair はまだ控えめです。

## 完成役 turn card の例外処理

UCBS-v2 のターン context において、ターンカードがストレートまたはフラッシュを完成させる場合、
モデルの予測精度が著しく低下します。

具体的に確認された事例は以下の通りです。

| Turn パターン | WRMSE | 説明 |
|---|---:|---|
| KJT + Q（ストレート完成） | 28% | Q で多数の hand がストレート完成 |
| T98r + 7（ストレート完成） | 19% | 7 でストレート完成 |
| 通常 turn card | 3-5% | UCBS-v2 が高精度適合 |

このような「完成役 turn card」では UCBS-v2 による計算を放棄し、
「手の絶対強度」で判断することを推奨します。
具体的には「自分がストレート/フラッシュを完成させているかどうか」を確認し、
完成ならば value bet、未完成ならばボード全体との相性で判断します。
この苦手領域については第 14 章で詳述します。

## 実戦例題

## Slowplay のターン変化

フロップでの off_slowplay（セット/ツーペア/フラッシュ等）は、ターンでも大きく維持されます。
mtt_25bb_turn: -0.28（フロップと同じ）、mtt_50bb_turn: -0.25（フロップ -0.12 より増大）。
ターンでもセット等の強い役は check が有力です。

一方 off_premium（オーバーペア/アンダーペア）はターンで若干上昇します。
mtt_100bb_turn では off_premium=+0.32 と突出しており、
100bb ターンではオーバーペアが積極的に bet する傾向が GTO データで確認されています。
これはターンカードがボードを変化させた後、オーバーペアの相対強度が上がりやすいためと考えられます。

## Turn context 選択の実戦フロー

実戦でのターン 2nd barrel 判断は以下のフローで行います。

**Step 1**: フロップで使用した context を確認する（例: mtt_50bb）。
**Step 2**: `_turn_btn` を末尾に付けて turn context に切り替える（mtt_50bb_turn_btn）。
**Step 3**: 通常通り CBS = HP + DP を計算する。ターンカードで手が変化した場合は更新する。
**Step 4**: board は 4 枚（フロップ 3 枚 + ターン 1 枚）で Confidence を判定する。
**Step 5**: UCBS-v2 の通常式で freq を算出する（α は自動的に turn context の値が使われる）。
**Step 6**: 完成役 turn card（ストレート/フラッシュ完成）を確認し、该当すれば手の絶対強度で判断する。

ターンカードで役が強化された場合（例: set を持ってターンで full_house になった）は
HP を更新します（set HP=8 → fullhouse HP=9）。
ただしターンでの HP 更新後も off_slowplay が適用されるため、
フルハウスでもターン 2nd barrel は抑制される傾向があります。

### Turn cbet 計算例

**例**: トップペア (top_pair) on `Ks7d2c5h` (BTN, context=mtt_25bb_turn_btn)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -41, β·I(CBS≥7) = +1, offset(default) = +0
→ **frequency = 28%**

**例**: セカンドペア (second_pair) on `Jd8c3s6h` (BTN, context=mtt_50bb_turn_btn)

1. HP = 5, DP = 0, CBS = **5**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -37, β·I(CBS≥7) = +0, offset(default) = +0
→ **frequency = 31%**

**例**: ロー・ポケットペア (low_pair) on `As7h2d9c` (BTN, context=mtt_100bb_turn_btn)

1. HP = 2, DP = 1, CBS = **3**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **False**
4. size = **33%** (small)
5. base_freq[(HIGH, False, 33)] = **45%**
6. α = -26, β·I(CBS≥7) = +0, offset(trash) = -14
→ **frequency = 5%**

**例**: オーバーペア (overpair) on `9s4d2c8h` (BTN, context=cash_100bb_turn_btn)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -37, β·I(CBS≥7) = +0, offset(premium) = +22
→ **frequency = 53%**

**例**: セット (set) on `Th5c2s5d` (BTN, context=mtt_25bb_turn_btn)

1. HP = 8, DP = 0, CBS = **8**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -41, β·I(CBS≥7) = +1, offset(slowplay) = -28
→ **frequency = 2%**

**例**: Aハイ (ace_high) on `Td8s4c7h` (BTN, context=mtt_50bb_turn_btn)

1. HP = 2, DP = 2, CBS = **4**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **False**
4. size = **33%** (small)
5. base_freq[(HIGH, False, 33)] = **45%**
6. α = -37, β·I(CBS≥7) = +0, offset(default) = +0
→ **frequency = 8%**

## まとめカード

- **Turn context の選択**: フロップ context の末尾に `_turn_btn` を付けて切り替える
- **α -35pt シフト**: 全ターン context で共通。フロップ比 35pt の bet 率低下
- **β ≈ 0**: ターンでは強い役（CBS≥7）への追加 lift がなくなる
- **off_trash 緩和**: フロップの -0.23〜-0.35 → ターンの -0.01〜-0.14（low_pair が相対的に bet 増）
- **WRMSE 目安**: mtt_25bb_turn=7%（最高）、mtt_100bb_turn=27%（最低、慎重に）
- **完成役 turn card は UCBS-v2 非対応**: ストレート/フラッシュ完成 turn は手の絶対強度で判断
