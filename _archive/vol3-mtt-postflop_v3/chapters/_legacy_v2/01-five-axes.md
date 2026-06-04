# 第01章 A モデル統一式——base+α+β+cat+ε の 7 ステップ

Vol3 で使う A モデルは Vol2 の 25 セル base に
4 つの補正 layer を追加して 13 context をカバーする統一式です。
本章では「Vol2 の知識をそのまま使う」階層構造を理解し、
7 ステップの暗算手順を体に染み込ませます。

## A モデルの式

Vol3 で扱うすべての場面 (cash / MTT 各スタック / 3bp / turn) は
以下の統一式で予測します。

```
freq = base[ctx5][band]                    ← Vol2 と同じ 25 セル
     + α[ctx13]                            ← コンテキスト補正
     + β[ctx13] · I(TV ≥ 7)               ← 強ハンド補正 (TV≥7 のとき)
     + cat_offset[hand_category]           ← ハンドクラス補正 (slowplay/trash/premium)
     + ε[board_family][ctx_group]          ← ボード補正
```

Vol2 読者は最初の項 base[ctx5][band] のみで判断していました。
Vol3 では残り 4 項を加算するだけで、13 context すべてに対応できます。
Vol2 で覚えた 25 セル表は **そのまま使える** ので、Vol3 で新たに覚えるのは
α/β/cat/ε の 38 数値のみです。

## 7 ステップの暗算手順

実戦での 7 ステップは以下の通りです。

**ステップ 1**: MV (役の強さ) を 6 バケットから判定 (2/3/5/7/8/9)
**ステップ 2**: DV (ドロー価値) を 4 段階から判定 (0/1/2/3)
**ステップ 3**: TV = MV + DV を計算してバンド分類 (air/weak/mid/strong/nut)
**ステップ 4**: context (cash_100bb / mtt_25bb / ... 13 種類のどれか) を確定
**ステップ 5**: base[ctx5][band] を 25 セル表から lookup (Vol2 と同じ)
**ステップ 6**: α + β·I(TV≥7) + cat_offset を加算
**ステップ 7**: 板分類 (paired/dynamic/dry_high/low_dry) で ε を加算 → 最終 freq

ステップ 1-3 は Vol2 と完全に同じです。ステップ 4-7 が Vol3 で追加される部分です。

## 5 軸式 (旧 5 軸モデル) からの変更点

旧 Vol3 は 5 軸式 (MV・DV・Confidence・Size・Context) で 100+ 数値を必要としました。
A モデルは階層型に再設計したことで、5 軸を以下のように整理しました。

| 旧 5 軸 | A モデルでの扱い |
|---|---|
| MV / DV | base の入力 (Vol2 と共通、TV バンドに集約) |
| Confidence | **廃止** (band 集約後に独立寄与なし、+0pt) |
| Size | **廃止** (Vol2 ch05 で扱う、本章では頻度のみ予測) |
| Context | α + β + ε に分解 (13 context × 3 layer) |

Confidence 軸は MV − DV の符号で表される「made-leaning / draw-leaning」の判別ですが、
band 集約後は α/β/cat layer に吸収済みで、独立軸として追加しても WRMSE が改善しません。
Size 軸は本書では小サイズ (33%) を基本としており、必要に応じて ch05 で扱います。

## 13 context の俯瞰

Vol3 で扱う 13 context は以下の通りです。Vol2 の 5 context 群 (cash / mtt_short /
mtt_deep / 3bp / turn) を細分化したものです。

| ctx5 グループ (Vol2) | ctx13 (Vol3) |
|---|---|
| cash | cash_100bb |
| mtt_short | mtt_25bb / mtt_50bb |
| mtt_deep | mtt_100bb / mtt_200bb |
| 3bp | mtt_3bp_20bb / 25bb / 50bb / 100bb |
| turn | mtt_25bb_turn_btn / 50bb / 100bb / cash_100bb_turn_btn |

Vol2 では「mtt_25bb と mtt_50bb は同じ mtt_short」として扱いましたが、
Vol3 では α/β/ε で context 別に補正します。

## 7 ステップ計算例

**例**: トップペア (top_pair) + ドローなし on `AsKd7c` (Cash 100bb)

1. MV = **7** (top_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = Cash 100bb → base = base[cash][strong] = **57%**
4. α[cash_100bb] (コンテキスト補正) = **+2pt**
5. β[cash_100bb]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][cash] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 59%**

**例**: オーバーペア (overpair) + ドローなし on `9c4d2s` (MTT 25bb)

1. MV = **7** (overpair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][strong] = **58%**
4. α[mtt_25bb] (コンテキスト補正) = **+36pt**
5. β[mtt_25bb]·I(TV≥7) (強ハンド補正) = **-5pt**
6. cat[premium] (ハンドクラス補正) = **+7pt**
7. 板分類: Low Dry (T 以下の dry) → ε[low_dry][mtt_srp] (ボード補正) = **-9pt**

→ **連続 bet 頻度 ≈ 88%**

**例**: セット (set) + ドローなし on `9s9c4d` (3BP 50bb)

1. MV = **9** (set)、DV = **0** (ドローなし)
2. TV = MV + DV = 9 + 0 = **9** → band: ナッツ (TV 9+)
3. ctx5 = 3-bet pot IP → base = base[3bp][nut] = **58%**
4. α[mtt_3bp_50bb] (コンテキスト補正) = **+1pt**
5. β[mtt_3bp_50bb]·I(TV≥7) (強ハンド補正) = **+5pt**
6. cat[slowplay] (ハンドクラス補正) = **+6pt**
7. 板分類: Paired (ペアボード) → ε[paired][3bp] (ボード補正) = **-1pt**

→ **連続 bet 頻度 ≈ 69%**

**例**: ロー・ポケットペア (low_pair) + ドローなし on `Jh8h6h` (Cash 100bb)

1. MV = **3** (low_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 3 + 0 = **3** → band: 弱ペア (TV 3-4)
3. ctx5 = Cash 100bb → base = base[cash][weak] = **37%**
4. α[cash_100bb] (コンテキスト補正) = **+2pt**
5. β[cash_100bb]·I(TV≥7) (強ハンド補正) = **+0pt**
6. cat[trash] (ハンドクラス補正) = **-14pt**
7. 板分類: Dynamic (モノトーン or 連結ツーフラ) → ε[dynamic][cash] (ボード補正) = **-21pt**

→ **連続 bet 頻度 ≈ 5%**

## 次章以降の構成

ch02 では α/β layer の 13 context 表を完全に習得します。
ch03 では category offset (slowplay / trash / premium) の意味と適用条件を扱います。
ch04 では C3 軸 (板分類 ε) のロジックと数値を扱います。
ch05 では context 切り替えフロー (どの ctx13 を選ぶか) を整理します。
ch06-09 では MTT 各スタック (25/50/100/200bb) の固有特性を扱います。
ch10 では 3-bet pot 4 文脈の SPR 別差異を扱います。
ch11 では turn 2nd barrel の 4 context を扱います。
ch12 では D モデル (BB 守備頻度) を扱います。
ch13 では境界例外と最終 quiz を行います。
