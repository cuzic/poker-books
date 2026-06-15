# 第 4 章　DV と street multiplier — Rule of 4/2 の整数化

## 4.1 DV (Draw Value) の値

ヒーローが持っている draw の強さを 0〜4 の整数で表します。

| draw 種類 | dv_cat | 値 |
|---|---|---:|
| コンボドロー (FD + SD) | combo_draw | **4** |
| フラッシュドロー (FD / NFD) | flush_draw / nut_flush_draw | **3** |
| OESD (オープンエンド) | oesd | **3** |
| ガットショット | gutshot | **1** |
| BDFD (バックドアフラッシュドロー、 2 枚) | twocards_bdfd | **1** |
| BDFD (1 枚) / no draw | onecard_bdfd / no_draw | **0** |

## 4.2 street multiplier

street ごとに DV にかかる倍率です。

| street | multiplier | 由来 |
|---|---:|---|
| flop | **×3** | Rule of 4 (out × ~8% per out × 2 残り street) |
| turn | **×2** | Rule of 2 (out × ~4% per out × 1 残り street) |
| **river** | **×0** | draw 完成不可 (board confirmed) |

## 4.3 Rule of 4/2 との関係

ポーカーで古典的に知られる **Rule of 4/2** をご紹介します。

- フロップで完成までの確率 ≈ outs × 4 (%)
- ターンで完成までの確率 ≈ outs × 2 (%)

これを整数化したのが本書の DV × mult 系です。OESD (8 outs) でフロップの場合を見てみましょう。

- 古典 Rule of 4: 8 × 4 = 32% 完成
- 本書: DV(3) × mult(3) = 9 points 加算

9 points は Score 14 → 23 への押し上げで、マージナルな call/fold の境界を跨ぐ大きさです。つまり「Rule of 4 を Score 単位に置換」という関係になっています。

## 4.4 river で DV = 0 になる根拠

river では board の 5 枚が確定し、draw は完成しないため DV の意味はゼロです。audit でも `mult[river] = 0` 以外の値は性能を悪化させます。

ただし river では **made hand の絶対価値** がそのまま勝負を決めるため、Grid 値そのものが効きます。river での Grid 値が高いカテゴリ (TP+ × dry = 38、2P+ ハンド × dry = 25) はそのまま value range になっています。

## 4.5 DV をなぜカテゴリに統合しないか

「draw 込みでカテゴリを 1 段上げれば良くないか?」と思うかもしれません。しかし draw と made hand は **独立次元** で、統合すると以下の問題が起きます。

- OESD + TP は「TP+ カテゴリ」でも「2P+ カテゴリ」でもありません
- combo draw (FD + SD) はエアですが Score 上は TP+ 並みに強いです
- river では draw の意味が消える → カテゴリベースだと river を別扱いにする必要があります

そのため DV は独立項として加算する設計が最良です。

## 4.6 DV 判定の実例

board: Th 9h 4c (wet flop)

| hand | 役 (mv) | DV |
|---|---|---:|
| Th Ts (set) | 2P+ | 0 (made 完成、draw 不要) |
| Kh Jh (FD + gutshot) | エア | combo_draw = 4 |
| Qh Jh (FD + OESD) | エア | combo_draw = 4 |
| Ah 2h (NFD) | エア | flush_draw = 3 |
| J 8 (OESD) | エア | oesd = 3 |
| K Q (gutshot) | エア | gutshot = 1 |
| A K (BDFD with Ah) | エア | twocards_bdfd = 1 |
| 7 6 (no draw) | エア | no_draw = 0 |

注意点として、combo_draw は **FD と OESD/SD が両立** している場合のみです。OESD のみ、FD のみの場合は値 3 になります。

## 4.7 DV とカテゴリの合算ルール

ある hand に複数の判定がつく場合 (例: TP + FD)、カテゴリと DV は **両方加算** されます。

- top_pair (カテゴリ 2) + flush_draw (DV 3) on flop
- Grid[TP+][?] + DV(3) × mult(3) = Grid + 9

つまり draw 込みの強さは Score にちゃんと反映されます。

## Cash/MTT note

DV 値と street mult は Cash/MTT 共通です。ただし MTT short stack では river まで届く確率が低く、DV ×3 (flop) の implied 価値が「実 EV」として強く効きます (commit 寄り)。これは deep Cash 200bb と逆の動きになっています。

## この章で覚える項目 (4 items)

1. DV 値: combo=4 / FD or OESD=3 / gutshot or BDFD=1 / no draw=0
2. street multiplier: flop=3 / turn=2 / river=0
3. Rule of 4/2 の整数化版
4. DV とカテゴリは独立加算
