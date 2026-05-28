# 付録 A: 13 context パラメータ完全表

Full UCBS-v2 を実戦で使うための数値リファレンスです。
13 context すべてのパラメータを Tier 別に整理しました。
本文（ch01〜ch13）と併せて参照し、必要な数値をすぐ引けるようにしてください。

## UCBS-v2 共通テーブル（HP / DP / BASE_FREQ）

以下の 3 表はすべての context で共通です。context を切り替えても HP・DP・base_freq の定義は変わりません。

### HP テーブル（6 バケット）

| HP | 含まれる役 |
|---:|---|
| 2 | ノーペア, Aハイ, Kハイ, ロー・ポケットペア |
| 3 | アンダーペア, サードペア |
| 5 | セカンドペア |
| 7 | トップペア, オーバーペア |
| 8 | セット, トリップス |
| 9 | ツーペア, フラッシュ, ストレート, フルハウス, クアッズ |

### DP テーブル（4 段階）

| DP | ドロー種別 |
|---:|---|
| 0 | ドローなし, BDFD |
| 1 | ガットショット |
| 2 | OESD, フラッシュドロー |
| 3 | コンボドロー |

### ハンドカテゴリ（offset 区分）

| カテゴリ | 含まれる役 |
|---|---|
| slowplay | ツーペア, フラッシュ, ストレート, セット, トリップス, フルハウス, クアッズ |
| trash | ロー・ポケットペア |
| premium | アンダーペア, オーバーペア |
| default | ノーペア, Aハイ, Kハイ, サードペア, セカンドペア, トップペア |

**BASE_FREQ（clamp 前）**

| Confidence | Direction | size=33% | size=116% |
|---|---:|---:|---:|
| HIGH | bet | 68% | 89% |
| HIGH | check | 46% | 44% |
| MID | bet | 40% | 55% |
| MID | check | 33% | 30% |
| LOW | bet | 25% | 27% |
| LOW | check | 30% | 28% |

bet 寄り (Direction=true) で HIGH: +20pt / MID: +15pt が overbet 加算値（上表は加算後）。
MTT context は polarize_enabled=False のため size は常に 33%。

## Tier 0 + Tier 1: cash_100bb と MTT depth 5 context

以下の表は cash_100bb（基準）と MTT depth 4 種（25/50/100/200bb）の 5 context です。
α はベース freq への均一加算、β は CBS≥7（強い役帯）への追加 lift を表します。
SB lift は OOP 先行者のハンデ補正、wide lift は CO/HJ/UTG のレンジの広さへの補正です。

### 13 context 全パラメータ表（数値は小数点なし ±%pt）

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

## Tier 3: 3BP IP 4 context のポイント

3BP IP の 4 context（mtt_3bp_20bb / 25bb / 50bb / 100bb）は、すべて pos_lift=0 かつ ax_range_bet=0 です。
代わりに SPR によって off_slowplay と off_trash が大きく変動します。

| Context | SPR目安 | off_slowplay | off_trash | 特徴 |
|---|---:|---:|---:|---|
| mtt_3bp_20bb | ≈2.5 | −40pt | −3pt | 浅SPR、trash も一部 bet |
| mtt_3bp_25bb | ≈2.7 | −66pt | −44pt | slowplay 最強抑制 |
| mtt_3bp_50bb | ≈5.5 | −40pt | −45pt | 最高精度 WRMSE 8.62% |
| mtt_3bp_100bb | ≈11 | −33pt | −48pt | 深SPR、premium 大幅 up (+20pt) |

## Tier 4: Turn cbet 4 context のポイント

Turn 4 context（mtt_25/50/100bb_turn + cash_100bb_turn）の共通特徴は α ≈ −35pt と β ≈ 0 です。
フロップ比で全体 bet 率が約 35pt 低下し、強い役への追加 lift（β）は廃止されます。

| Context | α | off_trash | WRMSE | 特記 |
|---|---:|---:|---:|---|
| mtt_25bb_turn | −41pt | −1pt | 7.02% | 最高精度、trash も相対的に bet |
| mtt_50bb_turn | −37pt | −3pt | 14.44% | 標準的ターン挙動 |
| mtt_100bb_turn | −26pt | −14pt | 26.95% | 最低精度（要注意） |
| cash_100bb_turn | −37pt | −8pt | 16.11% | cash ターンの基準 |

ターン context では SB lift・ax_range_bet ともに 0 です（ポジション補正なし）。
