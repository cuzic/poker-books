# 第02章 α/β layer——13 context の lift 表

A モデルの中核となる α (コンテキスト補正) と β (TV≥7 の追加 lift) を、
13 context すべてについて表で習得します。なぜ mtt_25bb の α が +36 と大きく、
mtt_3bp_25bb の β が -15 と大きく負なのか、構造的理由とともに理解します。

## α/β 表の全貌

### 13 context × α/β layer

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

α は「その context 全体で base からどれだけ lift するか」を表します。
正の α は「base より bet 寄り」、負の α は「base より check 寄り」を意味します。
β は TV ≥ 7 (strong または nut バンド) のときのみ追加で加算します。
TV が 6 以下のときは β は加算しません。

## α が大きい context (MTT 短スタック)

最も大きな α は **mtt_25bb の +36** と **mtt_100bb の +26** です。
この 2 つは Vol2 では「mtt_short と mtt_deep に統合」されていたものを
Vol3 で細分化したものです。

mtt_25bb の +36 は「ショートスタックでは wide cbet が GTO 最適」という
MTT 6m Simple tree の特性を反映しています。25bb スタックでは SPR が低く、
pot コミット判断が近いため、ブラフレンジ含めた cbet 率を base より大幅に上げます。

mtt_100bb の +26 も同様の構造です。MTT 100bb は cash 100bb と一見似ていますが、
MTT 特有のレンジ構成 (open range がややタイト) により、cbet 率が cash より高めに
なります。これは MTT 6m Simple tree が cash と異なる solver 設定で計算されている
ためで、本書では実測値に従って α を割り当てています。

mtt_50bb と mtt_200bb は α がほぼ 0 (それぞれ +0、-5) で、Vol2 の base 値とほぼ
同じ頻度になります。中程度のスタックでは特殊な lift が必要ないことを示しています。

## β が大きく負の context (3BP 浅スタック)

最も大きな負の β は **mtt_3bp_25bb の -15** と **mtt_3bp_20bb の -15** です。
これは「3BP の浅スタックでは strong / nut バンドのハンドで slowplay 傾向が顕著」
ということを反映しています。

3BP 浅 (SPR ~3) では、set や two_pair など TV≥7 のハンドを
むしろチェックバックして相手のブラフを誘発するのが GTO 最適な場合が多くなります。
ベットしてしまうとレンジが極端に強くなり、相手が安いハンドを fold してしまうためです。
β = -15 は「strong/nut バンドでは base から 15pt 下げてベットする」という意味です。

逆に **mtt_3bp_50bb の +5** と **mtt_3bp_100bb の +8** では β が正です。
深い 3BP では SPR が高く、ベットでより多くの value を取れるため、
strong/nut バンドを bet 寄りに lift します。

## Turn context の α/β は控えめ

Turn 4 context (mtt_25/50/100bb_turn_btn と cash_100bb_turn_btn) は
α/β とも比較的小さい値です (α: -2 〜 +13、β: -4 〜 -5)。

Turn では Vol2 base が既に 6-7% と非常に低く設定されているため、
追加の lift は不要に近い構造です。最も大きい mtt_100bb_turn_btn の α=+13 は
「MTT 100bb のターンでは想定より cbet 続行率が高い」ことを示します。

## α/β 適用例 (4 つの代表 context)

**例**: トップペア (top_pair) + ドローなし on `AsKd7c` (MTT 25bb)

1. MV = **7** (top_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = MTT 25-50bb → base = base[mtt_short][strong] = **58%**
4. α[mtt_25bb] (コンテキスト補正) = **+36pt**
5. β[mtt_25bb]·I(TV≥7) (強ハンド補正) = **-5pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 89%**

**例**: セカンドペア (second_pair) + OESD on `9c8d6h` (3BP 25bb)

1. MV = **5** (second_pair)、DV = **2** (OESD)
2. TV = MV + DV = 5 + 2 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = 3-bet pot IP → base = base[3bp][strong] = **70%**
4. α[mtt_3bp_25bb] (コンテキスト補正) = **+3pt**
5. β[mtt_3bp_25bb]·I(TV≥7) (強ハンド補正) = **-15pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Low Dry (T 以下の dry) → ε[low_dry][3bp] (ボード補正) = **-2pt**

→ **連続 bet 頻度 ≈ 56%**

**例**: オーバーペア (overpair) + ドローなし on `9h5c2s` (3BP 100bb)

1. MV = **7** (overpair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = 3-bet pot IP → base = base[3bp][strong] = **70%**
4. α[mtt_3bp_100bb] (コンテキスト補正) = **+0pt**
5. β[mtt_3bp_100bb]·I(TV≥7) (強ハンド補正) = **+8pt**
6. cat[premium] (ハンドクラス補正) = **+7pt**
7. 板分類: Low Dry (T 以下の dry) → ε[low_dry][3bp] (ボード補正) = **-2pt**

→ **連続 bet 頻度 ≈ 83%**

**例**: トップペア (top_pair) + ドローなし on `KdTh4s` (Turn MTT100)

1. MV = **7** (top_pair)、DV = **0** (ドローなし)
2. TV = MV + DV = 7 + 0 = **7** → band: 強ペア (TV 7-8)
3. ctx5 = Turn 2nd barrel → base = base[turn][strong] = **7%**
4. α[mtt_100bb_turn_btn] (コンテキスト補正) = **+13pt**
5. β[mtt_100bb_turn_btn]·I(TV≥7) (強ハンド補正) = **-4pt**
6. cat[default] (ハンドクラス補正) = **+0pt**
7. 板分類: Dry High (J 以上のハイカード dry) → ε[dry_high][mtt_srp] (ボード補正) = **+0pt**

→ **連続 bet 頻度 ≈ 16%**

## 暗記の優先順位

13 context すべての α/β を一気に覚えるのは大変です。優先順位は以下の通りです。

1. **cash_100bb (+2, +0)** — 最頻出 context。α/β とも小さいので「Vol2 と同じ」と覚えれば OK
2. **mtt_25bb (+36, -5)** — α が最大、確実に暗記
3. **mtt_100bb (+26, -6)** — α が大きい、確実に暗記
4. **mtt_3bp_25bb (+3, -15)** — β が最大の負、3BP 浅で重要
5. **mtt_3bp_50/100bb (+1/+0, +5/+8)** — β が正、深 3BP で覚える

残り 7 context は α/β とも 5pt 以下の小さい値なので、「微調整 ±5pt」と覚えて
実戦では Vol2 base に近い扱いで OK です。
