# 第14章 A モデルの限界——MTT 100bb 系の構造的制約

A モデルは約 18% の平均 WRMSE で動作しますが、すべての context が同精度では
ありません。特に MTT 100bb (25%) と MTT 100bb turn (26%) は構造的限界に
当たります。本章では限界を率直に示し、実戦での対処法を提示します。

## context 別精度マップ

A モデル 13 context の WRMSE 分布は以下の通りです。

| 精度帯 | WRMSE | 該当 context |
|---|---:|---|
| ★★★ 高精度 | < 10% | mtt_25bb_turn_btn (7.5%)、mtt_3bp_50bb (9.3%) |
| ★★ 中精度 | 10-20% | cash_100bb (18.8%)、mtt_50bb (17.6%)、mtt_200bb (19.9%)、mtt_3bp_25bb (15.4%)、mtt_3bp_100bb (13.9%)、mtt_50bb_turn_btn (14.5%)、turn_cash100 (15.6%) |
| ★ 注意 | 20-25% | mtt_25bb (17.6%)、mtt_3bp_20bb (21.4%) |
| × 限界 | > 25% | **mtt_100bb (25.0%)、mtt_100bb_turn_btn (25.7%)** |

mtt_100bb 系の 2 つは 旧 5 軸モデル (100+ 数値) でも 22% / 27% で、
band 集約構造そのものの限界に当たっています。

## mtt_100bb の構造的限界

なぜ mtt_100bb で WRMSE が 25% を超えるのか。原因は MTT 6m Simple tree の
cbet 分布の特殊性です。

MTT 6m Simple solver は同じ band でも、ボードのテクスチャ細部 (具体的なランク、
kicker、scenario の組合せ) によって cbet 率が 30%-90% まで散らばります。
A モデルは band 単位で予測するため、この分散を捉えきれません。

ε[board_family] で paired/dynamic/dry_high/low_dry の 4 分類はしていますが、
family 内でも cbet 率が散らばるため、4 family の粒度では不十分です。

## 限界 context での実戦対処

限界 context で A モデルを使うときの心得:

1. **±20pt の誤差を想定**: 計算結果 70% なら「50-90%」の幅、40% なら「20-60%」と
   考える。境界 (40-60%) ではどちらの選択でも極端な loss は出ない
2. **boundary 板を識別**: dry_high と low_dry の境界 (例: T7c3s や J7d3c) は
   family 分類が曖昧。実戦では両方の ε を確認して中間値を取る
3. **GTO Wizard で確認**: 限界 context の特定 spot は GTO Wizard で実値を見る
4. **Confidence を高めるシグナル**: 自分の hand が clear value bet 候補なら
   予測 +10pt、明確な bluff 候補なら -10pt と直感補正する

## A モデルで扱わない領域

本書のスコープ外の領域:

- **River frequencies**: 本書は flop / turn のみ。river は Vol4 (Tell) で扱う
- **Multiway pot**: 3 人以上の pot は base が大きく異なる
- **River 板変化**: river overcard、3rd flush 等は別モデル
- **Overbet (75-100% sizing)**: 本書の cbet は small bet (33%) 前提
- **Donk bet**: BB から flop で先制 bet するレンジ。本書では非対応
- **ICM 補正**: バブル / FT は Vol4 を参照

これらの領域は本書だけで判断せず、別シリーズや GTO 確認を併用してください。

## 限界を知った上での使い方

A モデルは「9 割の場面で 5-7 秒で判断できる」ことを目標としたフレームワークです。
残り 1 割の難所では、計算結果に頼りすぎず以下の判断補正を行います。

- **時間制限のある実戦**: 計算値そのまま採用 (±20pt 誤差を許容)
- **重要 spot のスタディ**: GTO Wizard で実値確認、A モデルと比較
- **新しい context との遭遇**: 最も近い ctx13 を選び、±10pt の余裕を見る

限界を知ることがフレームワークを正しく使う第一歩です。
