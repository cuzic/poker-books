# 第 6 章　12 cells grid の完全解説 ★本書の魔法核心

> **本章は本書の最大の難所であり、最大の発見です。**
> 12 cells grid は **線形ではありません**。「役が強いほど値が大きい」でも「dry board ほど
> 値が大きい」でもありません。hand × board の **複雑な interaction** で値が増減する、
> 直感に反する数値表です。この interaction を「12 の物語」として理解することが
> 本書の核心となります。

## 6.1 12 cells grid の全表

|           | dry | paired | wet |
|-----------|----:|-------:|----:|
| エア | 3 | 5 | 1 |
| アンダーペア | 18 | 40 | 10 |
| トップペア以上 | 38 | 10 | 31 |
| 2P+ | 25 | 28 | 23 |

最高値は **アンダーペア × paired = 40** です。直感に反する位置にあります。

## 6.2 直感に反する 6 つの発見

### 発見 1: ミドル × paired = 40 が最高値

直感: アンダーペアは中位の手、paired board は trip 警戒 → 値は低いはず。

**真実**: paired board では相手の range が **wide で air-heavy** に偏ります。
相手がペア板を bet するときは bluff 率が高く、また value 側はトリップス〜FH
に偏ります。hero がアンダーペアであれば「相手の bluff には勝つ」という位置に
立ち、range 中の上位として value 取り可能です。結果 40 という驚異的な値になります。

paired board × アンダーペア × bet 受けの huge% は audit で **0.0%** (n=4,776)です。
公式予測がほぼ完璧にマッチします。

### 発見 2: TP+ × paired = 10 (中位の低値)

直感: TP+ は強い手、どこでも価値あるはず。

**真実**: paired board では TP+ は **trip range に直接負ける** ハンドです。
A-K-K で AK を持っていても、相手の K (any kicker) には負けます。paired board
での TP+ は「アンダーペアとほぼ同価値 (10)」という大幅減になります。

### 発見 3: 2P+ × dry = 25 < 2P+ × paired = 28

直感: dry こそ強い手の主戦場のはず。

**真実**: dry では over-protection 不要です (相手の draw が少ない)。一方 paired
では 2P〜FH range で **取りに行く価値が高い** (相手のキッカー range が広い)です。
このため paired の値がわずかに高くなります。

### 発見 4: 2P+ × wet = 23 が最低の2P+値

直感: 2P+ は wet でも強いはず。

**真実**: wet board の draw 完成 / set / straight / flush で **互角の range**
ができ、厚すぎる value bet は逆効果です。23 は「無理せず call ベース」という
signal になります。例外 2 (river × SRP × wet × 2P+ → raise) でカバーします。

### 発見 5: エア × dry = 3 < エア × paired = 5

直感: dry の方が hero エアでも勝機あり (board 弱)。

**真実**: paired board では **相対 range** で意外と call できます。相手も air
が多いため、hero エアでも「相手より弱くない」局面があり、5 の小さなプラスが
重要になります。

### 発見 6: TP+ × dry = 38 vs TP+ × wet = 31 (差はわずか 7)

直感: TP+ は dry だけ強く、wet では大幅弱体化のはず。

**真実**: wet でも TP+ は **相手の draw range に対し range advantage** を持続します。
draw は完成確率 30-40%、hero TP+ は eq 60%+ です。wet で 31 と高値維持されます。

## 6.3 12 cells の 4 つの暗記原則

各 cell の数値はランダムではなく、4 つの原則の組合せで覚えられます。

### 原則 1: paired board の wide-range effect

相手の range が広がる → 中位 hand (ミドル / エア) の相対価値↑、強 hand
(TP+ / 2P+) の相対価値↓。

- ミドル × paired = 40 (最大)
- エア × paired = 5 (dry より +2)
- TP+ × paired = 10 (大幅減)

### 原則 2: dry board の polarization effect

相手の range が分極化 → TP+ 一辺倒で最強、中位は不利になります。

- TP+ × dry = 38 (準最大)
- ミドル × dry = 18 (paired の半分)
- エア × dry = 3 (base)

### 原則 3: wet board の equity sharing

draw の存在で eq が共有 → 2P+ の value↓、TP+ の defense は持続。

- 2P+ × wet = 23 (最低の2P+値)
- TP+ × wet = 31 (dry 比 −7、まだ高値)
- ミドル × wet = 10 (paired の 1/4)

### 原則 4: エアの flat pattern

どの board でも 1-5 の low range、sizing / oc / pot で補正します。

- エア × dry = 3
- エア × paired = 5
- エア × wet = 1

エアの Grid は「base 補正」程度の役割で、主な変動は加算項 (DV / oc / pot / bs)
で決まります。

## 6.4 12 cells すべての数値の覚え方

| キー | 値 | 連想 |
|---|---:|---|
| ミドル × paired | **40** | 最高峰、paired の bluff range 例外 |
| TP+ × dry | **38** | TPTK 王道、dry polarization |
| TP+ × wet | 31 | 一の位 1 = "still strong" |
| 2P+ × paired | 28 | FH potential、2P 取り |
| 2P+ × dry | 25 | 5×5、set / 2P default |
| 2P+ × wet | 23 | dry 比 −2 = draw sharing |
| ミドル × dry | 18 | paired の半分弱 |
| ミドル × wet | 10 | wet で半減 |
| TP+ × paired | 10 | trip 警戒で陥落 |
| エア × paired | 5 | wide range premium |
| エア × dry | 3 | base |
| エア × wet | 1 | floor |

「40 / 38 / 31 / 28 / 25 / 23 / 18 / 10 / 10 / 5 / 3 / 1」を一列で覚えると、
それぞれの行と列の位置に当てはめるだけで済みます。

## 6.5 カテゴリ × board 別 huge%

audit (n=154,216) での huge% (>5 BB):

| カテゴリ | dry | paired | wet |
|---|---:|---:|---:|
| エア | 0.6% | 0.4% | 1.1% |
| アンダーペア | 1.2% | **0.0%** ★ | 1.2% |
| TP+ | 2.5% | 1.7% | 4.2% |
| 2P+ | 3.7% | 5.3% | 4.3% |

- アンダーペア × paired = **0.0%** (Grid=40 で完璧マッチ)
- 弱点: 2P+ × paired (5.3%)、wet 全般

弱点は例外 11 ルール (第 9 章) で大部分救済します。

## 6.6 12 cells の最適化過程

- 4 カテゴリ × 3 board の 12 自由度を Optuna TPE で全 154,216 spots に最適化
- 旧 6 カテゴリ × 3 board (Grid 18) との比較で **集約しても性能向上** が確定
  - Grid 18: avg 0.3722 BB
  - **Grid 12: avg 0.3587 BB ★**
- 「ミドル × paired = 40」は data から発見された値で、GTO 理論から演繹的に導出する
  のは困難です。→ これこそが本公式の **最大価値**

詳細経緯は付録 B を参照してください。

## 6.7 数値暗記法 ★mnemonic — 12 cells を 5 分で覚える

12 個の整数 (3 / 5 / 1 / 18 / 40 / 10 / 38 / 10 / 31 / 25 / 28 / 23) を
丸暗記するのは大変です。本節では **構造化暗記** / **物語アンカー** /
**古典役名アンカー** / **連想数式** の 4 つの mnemonic 手法で、5 分で
12 cells が定着するようにしています。

### 6.7.1 構造化暗記 — 数値を 4 group に分ける

12 cells を「値の高低」で 4 group に分けると暗記負荷が激減します。

| group | 値 | cells | 共通点 |
|---|---|---|---|
| **最高 group** | 40 / 38 / 31 / 28 / 25 / 23 | ミドル×paired (40) / TP+×dry (38) / TP+×wet (31) / 2P+×paired (28) / 2P+×dry (25) / 2P+×wet (23) | **value 主役**、raise 閾値 (43) に近づく |
| **中位 group** | 18 | ミドル×dry (18) | 唯一の中位、dry の中ペア |
| **低位 group** | 10 / 10 / 5 / 3 / 1 | ミドル×wet (10) / TP+×paired (10) / エア×paired (5) / エア×dry (3) / エア×wet (1) | call 閾値 (14) 未満が多い |

### 6.7.2 物語アンカー — 各 cell に短い物語

| cell | 値 | 物語 |
|---|---:|---|
| ミドル × paired | **40** | 「ペア板の王様」 — 相手の bluff range で大儲け、paired board の予想外スター |
| TP+ × dry | **38** | 「TPTK の王道」 — dry の支配者、polar range で最強 |
| TP+ × wet | 31 | 「TPTK 健在」 — wet でも range advantage 持続、31 の "1" は "still strong" |
| 2P+ × paired | 28 | 「FH potential」 — 2P から FH への伸びしろ |
| 2P+ × dry | 25 | 「5 × 5、set の default」 — dry で set / 2P が安定 value |
| 2P+ × wet | 23 | 「draw に分け前」 — wet では draw 完成で互角に、控えめに |
| ミドル × dry | 18 | 「中ペアの dry 限定」 — paired (40) の半分弱 |
| ミドル × wet | 10 | 「wet で半減」 — paired の 1/4 |
| TP+ × paired | 10 | 「trip 警戒で陥落」 — TPTK が paired でミドル並みに |
| エア × paired | 5 | 「wide range premium」 — 相手も air、air でも call できる |
| エア × dry | 3 | 「base」 — エアの基準、何もない |
| エア × wet | 1 | 「floor」 — エアの最低、draw 期待のみ |

物語は **語呂的に短く** が肝心です。例えば「ミドル paired は王様 40、TP+ dry は王道 38、
TP+ wet は健在 31、...」と読み上げると 30 秒で 12 cells が浮かびます。

### 6.7.3 古典役名アンカー — 旧用語と新カテゴリを結ぶ

旧来のポーカー文献 (Sklansky、Janda 等) で使われる古典役名と、本書 4 カテゴリの対応:

| 本書 カテゴリ | 古典役名 | アンカー連想 |
|---|---|---|
| 2P+ | "monster"、セット以上 | 古典の「strong made hand」、値 23-28 (Grid 3 cells 平均 ~25) |
| TP+ | "TPTK"、トップペア・トップキッカー | TP+ × dry 38 は「TPTK の王道」、旧文献の "premium TP" |
| アンダーペア | "mid pair"、セカンドペア | 旧文献の "marginal pair"、paired 板で例外的に強い (40) |
| エア | "nothing hand"、air、high card | 旧文献の "drawing dead 寸前"、すべて 1-5 の low |

「TPTK = 38 (王道)」「monster = 23-28 (Grid 3 cells で 25 平均)」と古典役名で
セルを呼ぶ習慣が付くと、暗算中に Grid を引き直す手間が消えます。

### 6.7.4 連想数式 — 数字同士の関係で覚える

12 cells の数値は完全にランダムではなく、連想数式で導出可能なものがあります。

| 関係 | 計算 | cells |
|---|---|---|
| ミドル paired から ミドル dry | **40 ÷ 2 − 2 = 18** | 40, 18 |
| 2P+ dry から 2P+ wet | **25 − 2 = 23** (draw sharing) | 25, 23 |
| エア paired から エア wet | **5 ÷ 5 = 1** (1/5 化) | 5, 1 |
| エア paired から エア dry | **5 − 2 = 3** | 5, 3 |
| TP+ dry から TP+ wet | **38 − 7 = 31** (一の位 1 = still strong) | 38, 31 |
| 2P+ paired = 2P+ dry + 3 | **25 + 3 = 28** (FH potential) | 25, 28 |
| TP+ paired = エア paired × 2 | **5 × 2 = 10** (trip discount) | 5, 10 |
| ミドル wet = TP+ paired | **両方 10** (paired と wet の TP+/ミドル境界) | 10, 10 |

特に「**両方 10**(ミドル wet と TP+ paired)」は試験対策の鉄板で、一気に
2 cells が定着します。

### 6.7.5 暗記の優先順位 — どれから覚えるべきか

12 cells を全部一気に覚えなくても、優先度の高い 3 cells から始めれば
80% の場面に対応できます。

#### Tier 1 (最重要、3 cells)

| cell | 値 | 重要度の理由 |
|---|---:|---|
| **ミドル × paired** | **40** | 最高値、paired board の bluff range で頻発、audit huge% 0.0% |
| **TP+ × dry** | **38** | TPTK の主戦場、最頻出 spot (SRP dry 30%) |
| **エア × wet** | **1** | 最低値、fold 判断の anchor、wet × air は 8% spots |

→ 3 cells 覚えるだけで 50%+ の spots に対応できます。

#### Tier 2 (重要、4 cells)

| cell | 値 | 重要度の理由 |
|---|---:|---|
| 2P+ × dry | 25 | dry の value 主役、raise 閾値判定によく出る |
| 2P+ × paired | 28 | paired board の FH potential、例外候補 |
| 2P+ × wet | 23 | 例外 2 で raise 変換 (wet × river × SRP) |
| TP+ × wet | 31 | 例外 1 で fold 強制 (wet × flop × SRP)、注意必須 |

→ Tier 1 + 2 で 7 cells、75% の spots カバーできます。

#### Tier 3 (補助、5 cells)

| cell | 値 | 重要度の理由 |
|---|---:|---|
| ミドル × dry | 18 | dry の中ペア、borderline call/fold |
| ミドル × wet | 10 | 例外 3 で fold 強制 (wet × turn × vs CR) |
| TP+ × paired | 10 | paired × TP+ の trip discount、ミドル wet と同値 |
| エア × paired | 5 | wide range premium、paired での bluff catch |
| エア × dry | 3 | エアの base、SRP dry で fold base |

### 6.7.6 5 分暗記プロトコル

実践的な暗記手順です。焦らず少しずつ進めていきましょう。

1. **30 秒**: Tier 1 の 3 cells を読み上げ (40 / 38 / 1)
2. **1 分**: Tier 2 の 4 cells を物語アンカーで結合 (FH 28 / set 25 / 健在 31 / 控えめ 23)
3. **1 分**: Tier 3 の 5 cells を「両方 10」で覚える (ミドル wet と TP+ paired)
4. **1 分**: 連想数式で確認 (40÷2−2=18、5−2=3、5÷5=1)
5. **30 秒**: 12 cells 全部を一気に読み上げ self-test

5 分で 90% 定着、翌日 reviewing で 99% 定着します。反復は **poker-drill** アプリの
「grid 暗記 deck」 (https://poker-drill.vercel.app) でしましょう。

## Cash/MTT note

12 cells grid は Cash と MTT chipEV で共通最適化です。154,216 spots の audit で huge 1.49% です。ante / sizing 差は Score 値に内包 (bs/pot 軸が吸収) されます。grid 値自体は両者で同じ整数を使います。

## この章で覚える項目 (16 items)

1〜12. 12 cells のすべての数値 (Tier 1 → 2 → 3 の優先順で)
13. 直感に反する 6 つの発見 (paired で逆転する場面)
14. 原則 1: paired の wide-range effect
15. 原則 2: dry の polarization effect
16. 原則 3: wet の equity sharing
