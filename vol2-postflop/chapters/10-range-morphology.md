# 第 10 章　Range Morphology — board 分類の data 裏付け

> 本章以降は **公式の理論的背景** です。公式だけ使う読者は読み飛ばしていただいても大丈夫です。

## 10.1 Board を 3 つのタイプに分類

board は以下の 3 つのタイプに分類されます：

| タイプ | 特徴 | 例 |
|---|---|---|
| dry | dry | K-7-2 / 7-5-2 |
| wet | wet | T-8-5 / T-9-8 / 9-7-3 |
| paired | paired | 7-7-2 |

このシンプルな 3 分類が、詳細な sub-family 分析と比べても **最良のバランス** を実現します。

## 10.2 3 タイプ分類の背景

詳細な sub-family 分類よりも、3 つの大カテゴリに **集約と Grid による相互作用** でアプローチする方が、暗算しやすく、かつ高精度です。実 GTO は単純な heuristic では説明しきれない複雑な振る舞いをするため、「分類を細かくするのではなく、Grid 値で sub-family の差を表現する」という戦略が有効です。

## 10.3 data-driven な 3 タイプ集約

集約のキーは「Grid 12 cells の hand × board interaction で sub-family の差を吸収」する設計です。つまり sub-family を board 軸ではなく Grid 値で表現するということです。

例を挙げてみます：
- paired_low (cbet 50%) と paired_high (cbet 41%) の差
  → Grid「アンダーペア × paired = 40」vs「TP+ × paired = 10」で表現されます
- low_dry と broadway_dry の差
  → oc 値の差 (broadway は oc 1-2、low_dry は oc 0) で表現されます

「軸を増やすより interaction を高めた方が暗算しやすい」という決定となります。

## 10.4 sub-family × カテゴリ の cross-tab (15 × 6 = 90 cell の発見)

膨大なデータの中で発見された outlier (audit)：

| sub-family | カテゴリ | bet 頻度 | outlier 度 |
|---|---|---:|---|
| paired × 2P | 2P+ | 0-30% | 🟢 強 (slowplay) |
| connected_mid × ミドル | ミドル | 73% | 🟡 高 (SPR=1.3) |
| paired_high × overpair | TP+ | 50%+ | 🟡 mid |
| monotone × FD | 2P+ | 65%+ | 🟢 強 (nut flush) |
| broadway_dry × ace_high | エア | 35%+ | 🟡 mid (oc 効果) |

これら outlier の大半は Grid 12 cells に吸収されています。残りは例外 11 ルールで救済されます。

## 10.5 なぜ 3 タイプで Score 公式に十分か

board 分類の詳細度と公式精度の関係を分析した結果、3 つのタイプ分類が **最適なバランス** であることが分かりました。

細かすぎる分類は過学習に陥り、逆に粗すぎると重要な情報が損失します。3 タイプ × 4 カテゴリの Grid は、情報量と暗記コストの最良バランスを実現します。

## Cash/MTT note

Range Morphology の 3 タイプは Cash/MTT 共通です。ただし 9-max (LIVE Cash / MTT early) は merged 寄り、6-max (online Cash / MTT FT) は polar 寄りになります。詳細は第 25 章でご説明します。

## この章で覚える項目 (2 items)

1. board は dry / wet / paired の 3 タイプに分類される
2. sub-family の差は Grid 値で表現される
