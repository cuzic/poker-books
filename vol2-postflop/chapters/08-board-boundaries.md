# 第 8 章　境界ボード集 — Range Morphology の修正

## 8.1 現行 heuristic と実 GTO の一致率 19%

GTO ソルバーの 13 sub-family × cbet 平均 (BTN attacker、 Cash100 SRP):

| empirical class | sub-family | cbet 平均 | 範囲 |
|---|---|---:|---|
| **MERGED** (>45%) | paired_low | 50.1% | 45-57% |
| | Khigh_spread | 48.0% | 44-50% |
| | Ahigh_spread | 46.0% | 25-50% |
| **CONDENSED** (40-45%) | broadway_dry | 44.9% | 28-52% |
| | paired_mid | 42.0% | 40-45% |
| | paired_high | 41.1% | 33-43% |
| | connected_low | 41.3% | 32-59% |
| **POLAR** (30-40%) | low_dry | 33.9% | 33-35% |
| | mid_dry | 33.3% | 28-39% |
| | connected_broadway | 32.5% | 17-40% |
| **POLAR extreme** (<30%) | monotone | 29.2% | 15-38% |
| | connected_mid | 28.5% | 21-48% |

旧 heuristic との一致率: **4/21 (19%)** → 修正が必要です。

## 8.2 paired board の特殊性

実は、paired board は 1 種類ではありません。sub-family によって挙動が大きく異なります。

### paired_low (例: 7-7-2)

- cbet 50%+ (MERGED 系)
- 相手の range が wide なので、hero attacker は cbet を強行します
- アンダーペア × paired_low = 40 (Grid 値そのまま)

### paired_mid (例: 8-8-K)

- cbet 42% (CONDENSED 系)
- ボードが適度に固まっていて、hero の condense range が活きます

### paired_high (例: K-K-2)

- cbet 41% (CONDENSED 系)
- TP+ range advantage が hero (attacker) にあります
- paired × TP+ = 10 ですが、ボード K にヒットしたペアは別物として扱う必要があります

→ Score 公式は **paired を 1 種類で扱い** ますが、paired_high と paired_low の
差は **oc** と **DV** で部分的に吸収されます。

## 8.3 paired × 2P = 0% の発見

paired board で hero が 2P を持っているとき (例: K-K-7 で K7):

- 実 GTO 上の bet 頻度: **0% 近辺** です
- 理由: 相手の K (any kicker) と相互勝ち負けで、set / FH に常時負けるからです
- 推奨: check call ベース (本書では Score < 43 → call)

これは Grid「2P+ × paired = 28」 + Score < 43 → call で正しく
表現されています (28 + 0 + ... < 43)。

## 8.4 paired × overpair が wet 寄り

paired board で hero が overpair (例: T-T-2 で QQ):

- TP+ 扱いですが、ボードのペア化で「相手の T range」に弱体化します
- 実 GTO では wet board 並みの controlled play になります
- Grid「TP+ × paired = 10」で低めに評価されていて、これが適切です

## 8.5 low_dry の修正

旧 heuristic では low_dry は dry の 1 種でしたが、実 GTO データを見ると:

- cbet 33-35% (POLAR 系) で wet/paired_low より低いです
- 相手の range が **ほぼ flat** で fold equity が低いです
- 推奨: bet サイズ大、頻度低 (polarized strategy)

Score 公式上は「low_dry も dry カテゴリ」として吸収します。例外的に「low_dry × エア
× SRP」では bs を上げて bluff 比率を下げる調整をしています。

## 8.6 wet 内の sub-family

wet と一括りにしていますが、実は sub-family が 4 つあります。

| sub-family | 特徴 | 推奨対応 |
|---|---|---|
| dynamic_2tone (例: T98 2 tone) | 強い connected | Grid wet を厳格適用します |
| monotone (例: T98hhh) | 3 mono | DV を高めに、oc を厳しめに調整します |
| straight-heavy connector (例: 765) | 4-connected | wet 中の最も wet です |
| connected_broadway (例: QJT) | 高い connector | wet ですが range が equity を共有しています |

これらは Grid「wet」1 種で扱い、DV と例外 11 ルールで救済しています。

## 8.7 77 boards cross-tab から抜粋した outlier ~15 個

| board | 旧分類 | 修正 | 理由 |
|---|---|---|---|
| 7-7-2 (paired_low) | paired | paired (MERGED) | cbet 50%、wide attack |
| 9-9-K (paired_mid) | paired | paired (CONDENSED) | TP+ で対応 |
| K-K-2 (paired_high) | paired | paired (CONDENSED) | TP+ adv |
| 6-5-4 (connected_low) | wet | wet+ (CONDENSED) | cbet 41% |
| Q-J-T (connected_broadway) | wet | wet (POLAR) | 32.5% |
| T-8-7 (connected_mid) | wet | wet (POLAR extreme) | 28.5% |
| 7-5-2 (mid_dry) | dry | dry (POLAR) | 33.3%、polar |
| A-7-2 (Ahigh_spread) | dry | dry (MERGED) | A blocker effect |
| K-8-3 (Khigh_spread) | dry | dry (MERGED) | 48% |
| K-Q-J (broadway_dry) | dry | dry (CONDENSED) | 44.9% |
| 9-8-7 hhh (mono) | wet | wet (POLAR extreme) | mono 警戒 |
| 4-3-2 (low_dry) | dry | dry (POLAR) | 33% |
| T-9-2 (mid + connector) | wet | wet 寄り | gap 1 |
| A-K-2 (broadway dry) | dry | dry (CONDENSED) | A blocker |
| 8-7-2 (mid + connector, gap 1) | wet | wet (CONDENSED) | gap で wet 判定 |

→ Score 公式上は **3 タイプ集約で十分** と判明しました。sub-family の細かい差は
audit で「Grid 12 → Grid 18」への分離試行で性能向上せず、集約のメリットの方が
勝ちました。

## Cash/MTT note

境界 board は Cash/MTT 共通です。paired board の wide attack は MTT で更に強く (ante でレンジが wider)。low_dry は Cash で出やすく、MTT 後期では dynamic_2tone (wet 系) が増えます。

## この章で覚える項目 (4 items)

1. 旧 heuristic 一致率 19% → 集約は data 駆動で判断
2. paired_low / paired_mid / paired_high の sub-family
3. paired × 2P = 0% (slowplay)
4. low_dry は実は POLAR (旧 dry より bet 低頻度)
