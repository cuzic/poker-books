# 第 30 章　テーブルサイズ別調整 (6/8/9-max)

> 本書 MATCHA Score は **6-max** (6人テーブル) を想定して最適化されています。
> 8-max / 9-max では range structure と multiway 頻度が変わるため、 Score 閾値
> と公式適用に微調整が必要です。 本章では 3 つのテーブルサイズの違いを整理し、
> 各サイズでの MATCHA Score 補正を表 1 つにまとめます。

## 30.1 本章の位置づけ

ポーカーのテーブルサイズは大別して 3 種類です：

| サイズ | 席数 | 主流場面 |
|---|---:|---|
| 6-max | 6 | Online cash (NL50-NL500)、 short-handed MTT |
| 8-max | 8 | Online tournament (mid-stage)、 LIVE cash |
| 9-max | 9 | LIVE cash (1/2 NL)、 LIVE MTT、 home game |

本書のメイン想定は **6-max** で、 8-max/9-max では以下 7 つの観点で挙動が
異なります：

1. UTG (Under The Gun) の open range
2. range の structure (polar / merged)
3. 3-bet 頻度
4. multiway 頻度
5. 席選び効果の規模
6. average stack depth
7. pre-flop position 数

## 30.2 6-max — 本書のメイン想定

### UTG = 15-18% open

6-max の UTG は **3 席目** (= EP/MP/HJ/CO/BTN/SB/BB のうち HJ 相当) で、
position pressure が緩く広くオープンします：

- UTG: **15-18%** RFI
- HJ: 18-22%
- CO: 25-30%
- BTN: 45-50%
- SB: 35-40% (limp 戦略次第)
- BB: defense 38-45%

### range が polar 寄り

6-max では「手数が少なく強いハンドに偏る」傾向があり、range が **polar 化** します：

- 強いハンドと bluff の二極
- merged (中位ハンド多い) は少ない
- value bet / bluff catch の二択が明瞭です

### 3-bet 頻度高

6-max は 3-bet 頻度が **8-12%** と高めです：

- 強いハンド (QQ+, AK) は当然
- bluff 3-bet (A5s、 76s 等) も豊富
- 4-bet pot も SRP 比 18%

### multiway 頻度低

6-max の SRP は **HU rate 75%、 3-way 20%、 4+way 5%** です。公式の「単独 villain
前提」が大半で成立します。

### MATCHA Score 適用

**そのまま無調整** です。 154,216 spots audit の 80% 以上が 6-max のデータです。

## 30.3 8-max — 中間設定

### UTG = 13-15% open

8-max は UTG が **5 席目** (席数 + 2 = position pressure 中) です：

- UTG: **13-15%**
- UTG+1: 14-16%
- MP: 16-19%
- HJ: 18-21%
- CO: 24-28%
- BTN: 42-48%
- SB: 33-38%
- BB: defense 38-45%

### range が混在型

8-max は polar と merged の中間です：

- 強いハンドは polar 化
- 中位ハンド (KJo, A9o) は merged 化
- bluff catch range が広がります

### 3-bet 頻度中

3-bet 頻度は **6-9%** です。 6-max より控えめで、 9-max より積極的です。

### multiway 頻度中

8-max の SRP は HU rate **65%、 3-way 25%、 4+way 10%** です。公式の単独 villain
前提が 65% で成立し、残り 35% は注意が必要です。

### MATCHA Score 補正 (推奨)

- **t_call: 14 → 15〜16** (+1〜+2、 bluff catch やや厳格)
- **t_raise: 43 → 44〜45** (+1〜+2、 raise threshold やや上げ)
- 例外 11 ルールは共通適用です

8-max 用に厳密に再 audit したデータはありませんが、 MTT 中期 (8-max 主流) の audit
傾向から +1〜+2 補正が妥当と推定されます。

## 30.4 9-max — 最 tight 設定

### UTG = 10-12% open

9-max の UTG は **6 席目** (席数 + 3 = 最 tight) です：

- UTG: **10-12%** (KK+, AK のみ + 少数の suited broadway)
- UTG+1: 11-13%
- UTG+2: 13-15%
- MP: 14-17%
- LJ: 17-20%
- HJ: 20-24%
- CO: 26-30%
- BTN: 42-48%
- SB: 32-37%
- BB: defense 36-42%

### range が merged

9-max は「全員 tight、 弱いハンドは事前 fold」という傾向があり、range が **merged** します：

- top range は集中 (QQ+, AK 等)
- middle range は全員持っている (JJ, AK, KQ 等)
- bluff range は少ない (合理的なプレイヤーほど bluff が少ない)

### 3-bet 頻度低

3-bet 頻度は **4-7%** です。 9-max では tight player が多く、 3-bet bluff が EV- になりやすいです。

### multiway 頻度高

9-max の SRP は HU rate **55%、 3-way 30%、 4+way 15%** です。 **公式の単独 villain
前提が 45% で破綻** するため、 MW 5 原則の適用率を上げる必要があります。

### MATCHA Score 補正 (推奨)

- **t_call: 14 → 16〜17** (+2〜+3、 wide call 削減)
- **t_raise: 43 → 45〜46** (+2〜+3)
- **MW 警戒**: 3+way 頻度 45% で MW 5 原則 (第 24 章) を default 適用
- 例外 11 ルールは共通適用です

9-max では「raise したら multiway になる」確率が 6-max の 3 倍です。 t_open
(プリフロップ open 閾値) も Vol1 推奨値より +3 tight 化がおすすめです。

## 30.5 テーブルサイズ × MATCHA Score 補正 1 表

| テーブル | UTG RFI | range | 3-bet | MW 頻度 | t_call 補正 | t_raise 補正 |
|---|---:|---|---:|---:|---:|---:|
| **6-max** | 15-18% | polar | 8-12% | 25% | **0** | **0** |
| **8-max** | 13-15% | mixed | 6-9% | 35% | +1〜+2 | +1〜+2 |
| **9-max** | 10-12% | merged | 4-7% | 45% | +2〜+3 | +2〜+3 |

簡略版 (実戦覚え用)：

- **6-max**: 無調整
- **8-max**: +1
- **9-max**: +2

## 30.6 席選び効果の規模 (Vol3 ch15 連携)

席選びの重要度はテーブルサイズで増減します：

| テーブル | 席選び効果 | 理由 |
|---|---|---|
| 6-max | 中 | 全員と頻繁に対戦、 hero 左右の影響限定 |
| 8-max | 高 | 左右 2 人 + 対面 5 人、 左の player type が hero range に大影響 |
| 9-max | **最大** | 左右 3 人の player type で hero range が 30-40% 変動 |

9-max では「hero の **左の player type**」 (CS / TAG / ニット) が hero range
構築の主要 input となります。 Vol3 (MATCHA Exploits) ch15 で詳しく説明します。

## 30.7 range structure 差 — polar / mixed / merged

| テーブル | range structure | 意味 |
|---|---|---|
| 6-max | **polar** | 強ハンドと bluff の二極 |
| 8-max | mixed | 中位ハンドも含む |
| 9-max | **merged** | tight player による中位ハンド集中 |

polar (6-max) → merged (9-max) で、 MATCHA Score の Grid 値の解釈も微差が出ます：

- polar (6-max): 「相手は強いか弱いか」 → bluff catch 効率が良い
- merged (9-max): 「相手は中位が多い」 → 薄い value が効率的です(実は 9-max は thin value
  寄りなのに、 multiway リスクで補正が必要になります)

## 30.8 3-bet 頻度差の含意

3-bet 頻度差が hero の防御 range に影響します：

| テーブル | hero open vs 3-bet 受け頻度 |
|---|---|
| 6-max | 高 (BB の 4-bet 受け 12-15%) |
| 8-max | 中 (4-bet 受け 8-10%) |
| 9-max | 低 (4-bet 受け 5-7%) |

→ 9-max では 3-bet されたら「相手は強い」と読み、 4-bet range を tighter 化します。
MATCHA Score 上は 4BP pot 値は同じですが、 4BP に持ち込まれる頻度自体が 9-max で
低くなります。

## 30.9 multiway 頻度の計算

「open raise vs N-1 callers」で multiway になる確率を示します：

| テーブル | HU | 3-way | 4+way |
|---|---:|---:|---:|
| 6-max | 75% | 20% | 5% |
| 8-max | 65% | 25% | 10% |
| 9-max | **55%** | 30% | **15%** |

9-max では「hero が open したら 4-way になる」確率が 15% で、 6-max の 3 倍です。これが
9-max での「MW 5 原則 (第 24 章) を default 適用」の根拠になります。

## 30.10 テーブルサイズ × pot 種別 組合せ表

| テーブル × pot | 推奨 t_call | 推奨 t_raise | 注意点 |
|---|---:|---:|---|
| 6-max × SRP | 14 | 43 | 標準 |
| 6-max × 3BP | 14 | 43 | polar、 公式そのまま |
| 6-max × 4BP | 14 | 43 | huge 削減領域 |
| 8-max × SRP | 15 | 44 | mixed range 注意 |
| 8-max × 3BP | 15 | 44 | 公式 +1 |
| 8-max × 4BP | 15 | 44 | 公式 +1 |
| 9-max × SRP | 16 | 45 | MW 警戒 |
| 9-max × 3BP | 16 | 45 | 公式 +2、 MW |
| 9-max × 4BP | 16 | 45 | tight、 MW |
| 6-max × vs CR | 14 | 43 | 例外 3 適用 |
| 9-max × vs CR | 16 | 45 | 例外 3 + tight |

実戦では「テーブルサイズ補正 + pot 種別」を併用します。

## 30.11 spin & go (3-max) の補足

3-max (例: spin & go) は special な環境です：

- UTG (= BTN) = 80% 以上の広いオープン
- range は merged + polar の二極
- MW 頻度が低い (=2 way 全部)
- ante がなしまたは軽い
- MATCHA Score 推奨補正: **t_call: 14 → 12** (wide call)、 **t_raise: 43 → 40**

ただし spin & go は本書のスコープ外のため、概略のみとします。

## 30.12 暗記項目: テーブルサイズ × 補正一覧

```
6-max: 補正 0 (本書 default)
8-max: t_call +1〜+2 / t_raise +1〜+2 / MW 注意
9-max: t_call +2〜+3 / t_raise +2〜+3 / MW 5 原則 default
3-max: t_call −2 / t_raise −3 (参考、 spin & go)
```

実戦中は **「6=0、 8=+1、 9=+2」** だけ覚えれば十分です。

## Cash/MTT note

- **Cash**: 6-max が主流 (online NL50-NL500)、 9-max は LIVE cash 主流です
  - Cash 6-max: 本書公式そのまま
  - Cash 9-max LIVE: t_call +2 + LIVE 特有の弱 villain 補正 (Vol3 連携)
- **MTT**: 9-max が default (early stage)、 6-max は FT 突入後 (late stage) です
  - MTT 9-max early: t_call +2 + ante 補正 (本章と第 21 章併用)
  - MTT 6-max FT: 本書公式そのまま (ICM 補正は別途、 第 22 章)

→ 「9-max + LIVE Cash」と「9-max + early MTT」が最も補正の重い場面です。

## この章で覚える項目 (4 items)

1. テーブルサイズ補正: 6-max=0 / 8-max=+1 / 9-max=+2
2. 9-max は MW 5 原則を default 適用 (MW 頻度 45%)
3. range structure: 6-max polar / 8-max mixed / 9-max merged
4. 席選び効果: 9-max で最大 (Vol3 ch15 連携)
