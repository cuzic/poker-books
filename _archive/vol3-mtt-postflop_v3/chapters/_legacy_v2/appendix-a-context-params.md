# 第付録A章 A モデル 全パラメータ完全表

A モデルを実戦で使うための数値リファレンスです。
Vol2 base 25 セル + 13 context α/β + cat_offset + ε board family のすべてを
本付録にまとめます。本文 (ch01〜ch14) と併せて参照してください。

## 共通テーブル (MV / DV / hand category)

以下の 3 表はすべての context で共通です。

### MV テーブル (6 バケット)

| HP | 含まれる役 |
|---:|---|
| 2 | ノーペア, Aハイ, Kハイ, ロー・ポケットペア |
| 3 | アンダーペア, サードペア |
| 5 | セカンドペア |
| 7 | トップペア, オーバーペア |
| 8 | セット, トリップス |
| 9 | ツーペア, フラッシュ, ストレート, フルハウス, クアッズ |

### DV テーブル (4 段階)

| DP | ドロー種別 |
|---:|---|
| 0 | ドローなし, BDFD |
| 1 | ガットショット |
| 2 | OESD, フラッシュドロー |
| 3 | コンボドロー |

### Hand カテゴリ (cat_offset の区分)

| カテゴリ | 含まれる役 |
|---|---|
| slowplay | ツーペア, フラッシュ, ストレート, セット, トリップス, フルハウス, クアッズ |
| trash | ロー・ポケットペア |
| premium | アンダーペア, オーバーペア |
| default | ノーペア, Aハイ, Kハイ, サードペア, セカンドペア, トップペア |

## Layer 1: Vol2 と共通の 25 セル base

Vol2 で覚えた 25 セル base 表 (5 context × 5 band)。Vol3 でもそのまま使います。

### base[ctx5][band]

| Context | air (TV 0-2) | weak (3-4) | mid (5-6) | strong (7-8) | nut (9+) |
|---|---:|---:|---:|---:|---:|
| Cash 100bb | 44% | 37% | 42% | 57% | 62% |
| MTT 25-50bb | 37% | 30% | 35% | 58% | 73% |
| MTT 100-200bb | 42% | 41% | 41% | 58% | 61% |
| 3-bet pot IP | 46% | 50% | 61% | 70% | 58% |
| Turn 2nd barrel | 6% | 6% | 3% | 7% | 7% |

## Layer 2: α / β layer (13 context)

α は context コンテキスト補正、β は TV≥7 のときの追加 lift です。

### α[ctx13] / β[ctx13]

| Context | α (コンテキスト補正) | β (強ハンド補正、TV≥7) |
|---|---:|---:|
| Cash 100bb | +2 | -0 |
| MTT 25bb | +36 | -5 |
| MTT 50bb | +0 | -3 |
| MTT 100bb | +26 | -6 |
| MTT 200bb | -5 | -4 |
| 3BP 20bb | -2 | -15 |
| 3BP 25bb | +3 | -15 |
| 3BP 50bb | +1 | +5 |
| 3BP 100bb | +0 | +8 |
| Turn MTT25 | -2 | -4 |
| Turn MTT50 | +1 | -4 |
| Turn MTT100 | +13 | -4 |
| Turn Cash100 | +1 | -5 |

## Layer 3: Category offset (context 共通)

### cat_offset[hand_category]

| Category | 含まれる役 | ハンドクラス補正 |
|---|---|---:|
| default | 通常 (top_pair / second_pair / 等) | +0pt |
| slowplay | set / trips / two_pair / fullhouse / flush / straight / quads | +6pt |
| trash | low_pair | -14pt |
| premium | overpair / underpair | +7pt |

## Layer 4: Board family ε (C3 軸)

ε は板テクスチャ × ctx_group 別の補正。3 ctx_group (cash / mtt_srp / 3bp)。

1. **paired**: フロップ 3 枚に同ランクが含まれる
2. **dynamic**: モノトーン (3 枚同スート)、または (ストレート連結 + ツーフラ)
3. **dry_high**: 上記以外で、最高ランクが J 以上 (**baseline**、補正なし)
4. **low_dry**: 上記以外で、最高ランクが T 以下

### ε[board_family][ctx_group]

| Board family | Cash | MTT SRP | 3-bet Pot |
|---|---:|---:|---:|
| Dry High (J 以上のハイカード dry) | +0pt | +0pt | +0pt |
| Paired (ペアボード) | +5pt | +2pt | -1pt |
| Dynamic (モノトーン or 連結ツーフラ) | -21pt | -11pt | -6pt |
| Low Dry (T 以下の dry) | -9pt | -9pt | -2pt |

## 7-step 計算手順

実戦での計算順序は以下の通りです。

1. MV (役の強さ) を 6 バケットから判定 (2/3/5/7/8/9)
2. DV (ドロー価値) を 4 段階から判定 (0/1/2/3)
3. TV = MV + DV を計算してバンド分類 (air/weak/mid/strong/nut)
4. context を確定 (13 種から 1 つ)
5. base[ctx5][band] を 25 セル表から lookup
6. α + β·I(TV≥7) + cat_offset を加算
7. 板分類 → ε を加算 → 最終 freq

## 精度マップ

13 context の WRMSE と参照優先度。

| context | WRMSE | 信頼度 |
|---|---:|---|
| mtt_25bb_turn_btn | 7.5% | ★★★ |
| mtt_3bp_50bb | 9.3% | ★★★ |
| mtt_3bp_100bb | 13.9% | ★★ |
| mtt_50bb_turn_btn | 14.5% | ★★ |
| mtt_3bp_25bb | 15.4% | ★★ |
| cash_100bb_turn_btn | 15.6% | ★★ |
| mtt_50bb | 17.6% | ★★ |
| mtt_25bb | 17.6% | ★★ |
| cash_100bb | 18.8% | ★★ |
| mtt_200bb | 19.9% | ★★ |
| mtt_3bp_20bb | 21.4% | ★ |
| mtt_100bb | 25.0% | × |
| mtt_100bb_turn_btn | 25.7% | × |
| **全体** | **18.3%** | |

× の context は ch14 で扱う構造的限界。実戦では計算結果 ±20pt の幅を想定。
