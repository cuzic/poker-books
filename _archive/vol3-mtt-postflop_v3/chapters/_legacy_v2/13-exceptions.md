# 第13章 境界ハンドと例外——A モデルの苦手領域

A モデルは 4 layer (base + α + β + cat + ε) で大半の場面を予測しますが、
完全には覆えない境界ハンドと例外があります。本章では low_pair (trash) の特殊性、
TV=7 境界の挙動、dynamic 板での polarize、そして公開 GTO データとの差異を扱います。

## A モデルの「例外的」要素まとめ

旧 5 軸モデル には 4 つの例外ルール (O4 型6 信頼度 up、O5 mono board、
O8 A-x range bet、O9 turn shift) がありましたが、A モデルではこれらの大部分を
4 layer に吸収しています。

| 旧 旧 5 軸モデルの例外 | A モデルでの扱い |
|---|---|
| O4 型6 信頼度 up | 不採用 (Confidence 軸自体を廃止) |
| O5 mono board | ε[dynamic][cash] = -21 で吸収 |
| O8 A-x range bet | 不採用 (Position 軸廃止、pos_lift +0.3pt のみで効果なし) |
| O9 turn shift | turn 専用 context (4 種) で吸収 |

代わりに A モデルで残る「実質的な例外」は以下の 3 つです。

## 例外 1: low_pair (trash) — context 共通 -14pt

low_pair (例: 22 on A73) は MV=3 で weak バンドに分類されますが、
cat_offset[trash] = **-14pt** が常時加算されます。

Vol2 では「low_pair に -10pt」、Vol3 では「-14pt」と少し厳しめになっています。

理由:
- **Showdown value がない**: ace_high や king_high はリバーまでチェックしても
  相手のブラフに勝てる場合がありますが、low_pair は相手のブラフを除いて
  ほぼ全てに負けています
- **チェックレイズに弱い**: ベットすると相手の任意のペアハンドの check-raise に
  対応できません
- **trash バケットの典型**: MV=3 の中で最も bet 適性が低い

実戦適用: cash_100bb で base[air]=44%、low_pair の場合 44 + 2 + 0 - 14 + 0 = **32%** で
check 寄り。Vol2 の light モデル (44 - 10 = 34%) と概ね一致します。

## 例外 2: TV=7 境界の β スイッチ

β は TV ≥ 7 のときのみ加算します。TV=6 と TV=7 の境界で β 値分の不連続が
発生する点に注意が必要です。

例: mtt_3bp_25bb (β=-15) で TV=6 と TV=7 の予測差は 15pt。
second_pair + OESD (MV=5 + DV=2 = TV=7) と third_pair + gutshot (MV=3 + DV=1 = TV=4)
では同じ「中ペア + ドロー」でも予測値が大きく違います。

実用上、TV=6 か TV=7 か迷うケース (例: top_pair + bdfd = MV=7 + DV=0 = TV=7) では
β を加算する側で判断します。境界での判断ミスを避けるには「強いペア = strong (TV≥7)」
と覚えて、ドローを含む組合せを丁寧に計算します。

## 例外 3: Dynamic 板での polarize

ε[dynamic][cash] = **-21pt** という大きな ε は、wet 板での cbet 削減を表しますが、
実戦では「leftover ベット部分を polarize (block bet または overbet)」する戦略と
組み合わせることが推奨されます。

A モデルは「small bet (33%) の頻度」を予測しますが、dynamic 板では一部
overbet (75-100%) で polarize するレンジが GTO 上で残ります。本書では
overbet 戦略は扱いませんが、dynamic 板で「予測 freq よりベット率が高い」
と感じたら、size 混合が要因の可能性があります。

対処は ch11 (Turn) や Vol4 (Tell) を参照してください。

## 境界ハンド集

実戦で判断を間違えやすい境界ハンドを context 別にまとめます。

| context | 境界ハンド | A モデル 推定 freq | 注意点 |
|---|---|---:|---|
| cash_100bb | second_pair + OESD | 約 45% | 50/50 の境界、状況依存 |
| mtt_25bb | top_pair on dry low | 約 89% | wide cbet、迷わず bet |
| mtt_100bb | mid band on dry_high | 約 65% | 構造的限界で ±15pt |
| mtt_3bp_25bb | set on dry | 約 55% | slowplay 顕著、check 50% |
| turn (any) | top_pair (2nd barrel) | 約 8% | base 7% に近い、check 優先 |

## 境界例題

**例**: セカンドペア (second_pair) + OESD on `9c8d6h` (Cash 100bb)

1. MV = **5** (second_pair)、DV = **2** (OESD)
2. TV = MV + DV = 5 + 2 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = Cash 100bb → base = base[cash][strong] = **57%**
4. α[cash_100bb] (コンテキスト補正) = **+2pt**
5. β[cash_100bb]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Low Dry (T 以下の dry) → ε[low_dry][cash] (ボード補正) = **-9pt**

→ **連続 bet 頻度 ≈ 50%**

**例**: トップペア (top_pair) + ドローなし on `8c5d2s` (MTT 25bb)

1. MV = **7** (top_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][strong] = **58%**
4. α[mtt_25bb] (コンテキスト補正) = **+36pt**
5. β[mtt_25bb]·I(TV≥7) (強ハンド補正) = **-5pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Low Dry (T 以下の dry) → ε[low_dry][mtt_srp] (ボード補正) = **-9pt**

→ **連続 bet 頻度 ≈ 81%**

**例**: セット (set) + ドローなし on `9c4d2s` (3BP 25bb)

1. MV = **9** (set)、DV = **0** (ドローなし)
2. TV = MV + DV = 9 + 0 = **9** → band: ナッツ (TV 9+)
3. ctx5 = 3-bet pot IP → base = base[3bp][nut] = **58%**
4. α[mtt_3bp_25bb] (コンテキスト補正) = **+3pt**
5. β[mtt_3bp_25bb]·I(TV≥7) (強ハンド補正) = **-15pt**
6. cat[slowplay] (ハンドクラス補正) = **+6pt**
7. 板分類: Low Dry (T 以下の dry) → ε[low_dry][3bp] (ボード補正) = **-2pt**

→ **連続 bet 頻度 ≈ 50%**

**例**: トップペア (top_pair) + ドローなし on `KsJd6c` (Turn Cash100)

1. MV = **7** (top_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = Turn 2nd barrel → base = base[turn][strong] = **7%**
4. α[cash_100bb_turn_btn] (コンテキスト補正) = **+1pt**
5. β[cash_100bb_turn_btn]·I(TV≥7) (強ハンド補正) = **-5pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][cash] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 3%**
