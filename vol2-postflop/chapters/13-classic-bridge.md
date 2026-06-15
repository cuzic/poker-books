# 第 13 章　旧来のポーカー理論との橋渡し ★暗記補助

> 本章は **MATCHA Score の数値・分類を、 既知のポーカー古典理論にアンカー** する
> ことで暗記負荷を下げる橋渡し章です。 Rule of 4/2 / Sklansky Hand Groups /
> Theory of Poker / Range Morphology / Pot Odds / MDF など、 ポーカー文献で
> 標準的な概念と、 本書 4 カテゴリ × 3 board × 12 cells Grid の対応を整理します。
>
> **既知の理論にアンカーすることで、 12 cells や 5 例外を「丸暗記」 ではなく
> 「既存知識の再構成」 として吸収できる** ようになります。

## 13.1 Outs と Rule of 4/2 (Petriv et al.) — DV multiplier の整数化根拠

ポーカーで最も古典的な暗算ルールが **Rule of 4/2** (Phil Gordon、 Anton Petriv 等
が広めました)。 本書の `DV × mult[street]` はこの整数化です。

### 各 draw の outs カウント表

| draw 種類 | outs | dv_cat | DV 値 |
|---|---:|---|---:|
| combo (FD + OESD) | 12-15 | combo_draw | 4 |
| flush draw (FD/NFD) | 9 | flush_draw | 3 |
| OESD (オープンエンド) | 8 | oesd | 3 |
| gutshot (ガットショット) | 4 | gutshot | 1 |
| BDFD (2枚) | 2 | twocards_bdfd | 1 |
| BDFD (1枚) / no draw | 0-1 | onecard_bdfd / no_draw | 0 |

### Rule of 4 / Rule of 2 の定義

- **Rule of 4** (フロップで完成までの確率): `outs × 4 (%)` ≈ flop → river の 2 枚 ヒット確率
- **Rule of 2** (ターンで完成までの確率): `outs × 2 (%)` ≈ turn → river の 1 枚 ヒット確率

例: OESD (8 outs)
- flop: 8 × 4 = **32% 完成**
- turn: 8 × 2 = **16% 完成**

### DV multiplier (flop ×3 / turn ×2 / river ×0) が Rule of 4/2 の整数化である理由

本書の Score 公式:
```
DV × mult[street]
flop: ×3
turn: ×2
river: ×0
```

OESD (DV = 3) の場合:
- flop: 3 × 3 = **9 points 加算** (Score 14 → 23 の閾値跨ぎ可能)
- turn: 3 × 2 = 6 points
- river: 3 × 0 = 0

これは Rule of 4/2 を「Score 単位の整数」 に置換したもの:
- 8 outs × 4% ≈ 32% 完成、 これを 9 points (Score 単位) に変換
- 9 / 32% ≈ 0.28 (= 1 point per ~3.5% equity)

→ **公式の DV 計算は Rule of 4/2 を整数で覚えるだけです**。 draw 計算を
暗算可能な整数に変換した結果が DV × mult。

### river で DV ×0 になる根拠

river では board が確定し、 draw は完成しません:
- outs × 0% = 0% (Rule of 0)
- ただし made hand の Grid 値はそのまま効きます (TP+ × dry = 38 等)

→ river の判断は「made hand の絶対 value」 のみで決まり、 DV は無視。

## 13.2 古典ボード 7 分類 → MATCHA 3 分類 集約マトリックス

### 古典 7 分類 (Janda "Applications"、 Acevedo "Modern Poker Theory")

| 古典分類 | 典型 | 古典戦略 |
|---|---|---|
| Dry rainbow | Kh 7c 2d | small cbet 多用、 polar |
| Dry connected (低 gap) | 7-5-2 (span 5) | small cbet、 やや tight |
| Wet | T-9-8 | big cbet 低頻度、 protection |
| Monotone | 9h 7h 3h | small cbet、 flush 警戒 |
| Two-tone | Th 9h 4c | mixed、 span で connected 判定 |
| Paired high | K-K-7 | small cbet 多用、 TP+ adv |
| Paired low | 7-7-2 | small cbet 多用、 MERGED |

### MATCHA 3 分類への集約

| 古典 7 | MATCHA 3 | 根拠 |
|---|---|---|
| Dry rainbow / Dry connected | **dry** | unpaired + span > 4 (非 connected) |
| Wet / Monotone / Two-tone (connected) | **wet** | span ≤ 4 または mono |
| Paired high / Paired low | **paired** | 同 rank 2+ |

### 例 board の対応詳細

| board | 古典 | MATCHA | Score 影響 |
|---|---|---|---|
| K-7-2 rainbow | Dry rainbow | **dry** | Grid TP+ × dry = 38 |
| Q-9-8 ss | Wet (connected) | **wet** | Grid TP+ × wet = 31 |
| A-8-5 ds | Dry rainbow | **dry** | Grid TP+ × dry = 38 |
| J-7-2 ss | Two-tone (span 9) | **dry** | span 9 > 4 で connected ではない |
| K-K-7 | Paired high | **paired** | Grid TP+ × paired = 10 |
| T-9-8 ss | Wet 2-tone | **wet** | span 2 ≤ 4 で wet |
| 9h 7h 3h | Monotone | **wet** | mono で wet |
| 7-7-2 | Paired low | **paired** | Grid ミドル × paired = 40 |

→ 古典 7 分類で「どこに該当するか」 を判定したら、 集約 column を見るだけです。

### 集約根拠 (data 検証)

audit (n=154,216) の結果 (詳細は第 10 章):

| 構成 | Grid cells | avg loss |
|---|---:|---:|
| 7 分類 × 4 カテゴリ | 28 | 0.3611 BB |
| 6 分類 × 4 カテゴリ | 24 | 0.3654 BB |
| **3 分類 × 4 カテゴリ (本書)** | **12** | **0.3587 BB ★** |
| 2 分類 × 4 カテゴリ | 8 | 0.3892 BB |

→ 3 分類で最良、 集約により情報損失がありません。 sub-family の差は **Grid 値の hand×board
interaction** (例えば「ミドル × paired = 40 vs ミドル × wet = 10」) で吸収されます。

## 13.3 6 階層 Hand Strength → MATCHA 4 カテゴリ 対応

### 伝統的な 6 階層の定義 (Sklansky-Malmuth)

| 階層 | 名前 | 含むハンド (例) |
|---:|---|---|
| 5 | ナッツメイド | FH / quads / SF |
| 4 | ストロング | set / flush / straight / 2P (3 系統合) |
| 3 | ツーペア | (独立扱い) |
| 2 | トップペア以上 | TP / overpair |
| 1 | アンダーペア | second / third / underpair |
| 0 | エア | high / king / ace high |

### MATCHA 4 カテゴリ への集約

| 旧 6 階層 | MATCHA 4 カテゴリ | 集約根拠 |
|---|---|---|
| ナッツメイド | **2P+** | 4BP で 2P 以上同挙動です |
| ストロング | **2P+** | dry で value bet 強行同一 |
| ツーペア | **2P+** | paired で slowplay 同様 |
| トップペア以上 | **トップペア以上 (TP+)** | 維持 |
| アンダーペア | **アンダーペア** | 維持 |
| エア | **エア** | 維持 |

### mv_cat (17 種) → 4 カテゴリ 対応表

GTO ソルバー 内部の `mv_cat` (made-value category) との対応:

```
2P+ (8 mv_cat):
  two_pair / set / trips / straight / flush
  fullhouse / quads / straight_flush

トップペア以上 (2 mv_cat):
  top_pair / overpair

アンダーペア (4 mv_cat):
  second_pair / third_pair / underpair / low_pair

エア (3 mv_cat):
  no_made_hand / king_high / ace_high
```

合計 17 mv_cat → 4 カテゴリ 集約です。

### ツーペアを 2P+ に統合した根拠

ツーペア以上のハンドは 4BP（4 bet pot）では同じ戦略を取ります：

| MATCHA 4 カテゴリ | 特徴 |
|---|---|
| **2P+ (ナッツメイド / ストロング / ツーペア 統合)** | 4BP で強行 value、slowplay なし |
| TP+ | value と protect のバランス |
| ミドル | 形勢に応じて判断 |
| エア | draw や air での判定 |

「2P 以上は 4BP では強行 value」 という単純規則が MATCHA Score の設計に反映されています。



## 13.4 SPR 理論 (Flynn "Professional No-Limit Hold'em")

Ed Miller、 Sunny Mehta、 Matt Flynn 著 "Professional No-Limit Hold'em" (2007)
で確立された SPR (Stack-to-Pot Ratio) 理論。

### 古典 SPR 切り分け (1-3-7)

| 古典 SPR | 範囲 | 古典戦略 |
|---|---|---|
| Low SPR | < 1 | jam-or-fold |
| Mid SPR | 1-3 | commit decision (3BP 主流) |
| High SPR | 3-7 | post-flop play、 turn 計画 |
| Very high SPR | > 7 | deep stack、 implied odds |

### MATCHA 4 段階

| MATCHA SPR | 範囲 | 典型 |
|---|---|---|
| オールインSPR | < 1 | 4BP、 short stack push |
| ローSPR | 1-3 | 3BP、 短スタック |
| ミディアムSPR | 3-7 | SRP の turn 後 |
| ディープSPR | > 7 | Cash 100bb の flop、 200bb |

古典 4 段階と MATCHA 4 段階はほぼ同一定義です。 境界の **1 / 3 / 7** が共通。

### SPR=3 が GTO 戦略反転点 — 同 K72 × SPR variation

audit で同 board (Ks 7d 2c) × SPR variation の cbet 頻度:

| カテゴリ | SPR 1.3 (4BP) | SPR 3.4 (3BP) | SPR 8 (Cash50) | SPR 16 (Cash100) |
|---|---:|---:|---:|---:|
| 2P+ (set) | **4%** | 41% | 69% | **96%** |
| ツーペア | 18% | 80% | 97% | 83% |
| トップペア以上 | 61% | 70% | 68% | 61% |
| アンダーペア | **73%** | 49% | 43% | 55% |
| エア | 41% | 46% | 46% | 44% |

SPR < 3 と SPR > 3 で挙動が **真逆**:
- SPR < 3: set 4% (slowplay)、 ミドル 73% (jam)
- SPR > 3: set 96% (fastplay)、 ミドル 55% (抑制)

これは古典 SPR 理論の「1-3-7 境界」 の **3** が反転点である data 駆動裏付けです。

### 公式が SPR を pot 軸で吸収する仕組み

MATCHA Score は SPR を **直接** 持たず、 `4 × pot` で間接表現します:

| pot | 値 | Score 補正 | 典型 SPR |
|---|---:|---:|---|
| SRP | 0 | 0 | 17 (ディープ) |
| vs CR | 2 | +8 | 4-5 (ミディアム) |
| 3BP | 2 | +8 | 4-5 (ミディアム) |
| 4BP | 4 | +16 | 1.5-2 (オールイン境界) |

pot 補正により、 SPR が低い場面 (3BP / 4BP) では Score が押し上げられ、 強気判断
(call / raise) に偏ります。 SPR を直接軸に取らずに済むのは「pot 種別が SPR を
ほぼ決める」 という data 検証された関係に基づいています。

## 13.5 Pot Odds と MDF (Minimum Defense Frequency)

ポーカーの古典定理: コール判断は **pot odds** で、 ベット側の bluff 抑制は
**MDF** で測られます。

### Pot Odds の定義

```
pot_odds = bet / (pot + 2 × bet)
必要 eq = pot_odds × 100 (%)
```

### MDF (Minimum Defense Frequency) の定義

ベット側が bluff を profitable にしないために、 受け側が必要な最低 defense 頻度:

```
MDF = 1 − pot / (pot + 2 × bet)
    = (pot + bet) / (pot + 2 × bet)
```

または「bet サイズ別 MDF」:
- 33% bet: MDF = 1 − 1/(1+2/3) = 60% (= bet 0.33pot vs pot 1.33+0.66)
- 75% bet: MDF = 1 − 1/(1+1.5) = 67%
- 100% bet: MDF = 1 − 1/3 = 67%
- 150% (overbet): MDF = 1 − 1/4 = 75%

### bs 別 pot odds 表

| bs key | pot 比 | pot odds | 必要 eq | MDF |
|---|---|---|---:|---:|
| small_33 | 33% | 1.66/4.66 | **25.4%** | 60% |
| med_75p | 75% | 3.75/8.75 | **30.0%** | 67% |
| med_100p | 100% | 5/12 | **33.3%** | 67% |
| overbet | 125-150% | 6.25/13.75 | **35-38%** | 67-75% |
| overbet_185 | 185% | 9.25/17.45 | **41%** | 73% |
| allin | 100%+ | varies | 33-50% | 67-100% |

### 公式閾値 ≥14 call、 ≥43 raise の意味づけ (MDF と Score の関係)

MATCHA Score の閾値 **14 と 43** は、 audit 駆動で決まった整数値ですが、 解釈すると MDF / pot odds と整合します:

- **Score 14 (call 閾値)**: 必要 eq ≈ 25-33% に相当 (small-med bet で defend 可能)
- **Score 43 (raise 閾値)**: 必要 eq ≈ 50%+、 value range 確定

これは **MDF と公式 Score の関係**:
- Score が高い → MDF を満たす hand range で defense 可能
- Score が低い → fold (相手の bluff も含めて勝てない)

「Score 14 = pot odds 25% = small bet 受けの最低 defense 線」 と覚えると暗算が
自然に意味づきます。

## 13.6 Range Morphology (Janda "Applications"、 Sweeney "Quantum Poker")

Matthew Janda "Applications of No-Limit Hold'em" (2013) と Will Tipton "Expert
Heads Up No-Limit Hold'em" 等で確立された range structure 理論。 Pat Sweeney
"Quantum Poker" (2010) でも論じられます。

### 伝統用語の定義

| 伝統用語 | 定義 | 例 |
|---|---|---|
| **polarized** | 強い hand と bluff の二極構造 | river bet range = nut + air |
| **linear (merged)** | 中位 hand 中心の合算構造 | 早めの street、 value heavy |
| **capped** | 上限がある構造 (nut 含まない) | call back range、 weak |

### MATCHA との対応

| MATCHA レンジ分布 | 伝統用語 | 本書での扱い |
|---|---|---|
| **2 極化型** | polarized | dry board の cbet range、 polar value + bluff |
| **混在型** | linear / merged | wet board、 中位 hand 多 |
| **密集型** | capped | wet board の call back range |

### 各 morphology に対する MATCHA の対応

| morphology | MATCHA Score での扱い |
|---|---|
| polarized | dry board × Grid 値 (TP+ 38、 エア 3) で対応 |
| linear | wet board × Grid 値 (TP+ 31、 2P+ 23) |
| capped | 例外 5 ルール (wet × SRP など) で表現 |

MATCHA は伝統的な range morphology 概念を board × カテゴリ × Grid に **吸収**
しています。 「相手のレンジを読む」 という抽象判断を Grid 12 cells の数値に
ダウンキャストしたのが本書のアプローチです。

## 13.7 Sklansky Hand Groups (1976 "Hold'em Poker")

David Sklansky の preflop hand groups (8 群、 後に Sklansky-Malmuth で 9 群)。
preflop 分類ですが、 postflop カテゴリ の **系譜** として理解できます。

### 群 1-8 の定義 (preflop、 一部抜粋)

| 群 | 例 hand | 古典評価 |
|---|---|---|
| 群 1 | AA / KK / QQ / AKs | premium |
| 群 2 | JJ / TT / AQs / AKo | very strong |
| 群 3 | 99 / JTs / QJs / KQs | strong |
| 群 4 | 88 / KJs / QTs / AJo | standard |
| 群 5 | 77 / 65s / 76s / KTs / QJo | playable |
| 群 6 | 66 / A9s / A2s | marginal |
| 群 7 | 55 / 44 / K9s / Q9s | weak playable |
| 群 8 以下 | 33 / 22 / J9o / 87o | weak |

### postflop カテゴリ (本書) との対応

Sklansky は preflop の group ですが、 hit したときの postflop カテゴリ は:

| Sklansky 群 | postflop カテゴリ (hit したとき) | 連想 |
|---|---|---|
| 群 1-2 (AA / KK / AKs) | **2P+** | set / flush / 強 overpair |
| 群 3-4 (JJ / TT / AQs / KQs) | **トップペア以上** | TP / mid overpair |
| 群 5-7 (mid SC / mid suited) | **アンダーペア** | second/third pair、 OESD |
| 群 8 以下 (rag) | **エア** | no pair、 weak draw |

→ Sklansky の preflop 群が高いほど、 postflop で2P+/TP+ に化ける確率が高いです。

### 「Sklansky は preflop だが、 postflop カテゴリ の系譜」

Sklansky-Malmuth はあくまで preflop の暗算ルール (Chen Formula と並ぶ古典)
ですが、 「ハンドを階層化する」 という発想は本書 MATCHA Score の preflop 版 (Vol1)
にも、 postflop 版 (本書) にも生きています。

Vol1 (MATCHA Formula、 preflop) は Chen Formula と Sklansky Hand Groups の現代版です。
Vol2 (本書、 postflop) はその postflop 拡張、 と理解してください。

## 13.8 Theory of Poker (Sklansky 1987)

David Sklansky "The Theory of Poker" (1987) の **Fundamental Theorem of Poker**:

### 定義

> 「相手のカードを見ながらプレイした場合と、 知らずにプレイした場合の EV ギャップが、
> 自分が間違うことで相手に与えた利益、 または相手が間違うことで自分が得た利益である」

要するに、 「**もし相手の手札が全部見えていたら何 EV か**」 と「実プレイの EV」 の差が
「自分の誤り」 で測られる、 という定理です。

### MATCHA Score がこのギャップを整数近似で最小化する仕組み

MATCHA Score の audit は:

```
avg loss = E[ EV(GTO best action) − EV(formula action) ]
        = 0.3587 BB (per spot)
```

これは Theory of Poker の「自分の誤り」 を 0.3587 BB に近似的に抑える、 という
ことです。 「相手の手札を見たら GTO best action が分かる、 公式はその近似」。

### 「公式は Theory of Poker の暗算実装」

Theory of Poker は理論であり、 実プレイでは「相手の hand を読む」 こと自体が
困難です。 MATCHA Score は **整数化された カテゴリ × board × DV × pot × bs** で
「読む量」 を 5 軸の重み付け和に圧縮し、 「読む手間」 を 5-10 秒に短縮しました。

→ **公式は Theory of Poker の暗算実装版**。 Sklansky の理論を「実戦で 5 秒で
回せる形」 に落としたもの、 と理解してください。

## 13.9 Bet Sizing 理論 (modern GTO)

modern GTO 理論 (PIO Solver、 GTO ソルバー、 Acevedo "Modern Poker Theory") で
確立された bet sizing の意味づけ。

### 各 sizing の意味づけ

| sizing | 名前 | 意味 |
|---|---|---|
| **33%** | small (range cbet、 protection) | range advantage 利用、 wide range で bluff も含む |
| **75%** | medium polar | value heavy、 bluff も含む polar 構造 |
| **100%** | polar (nut advantage) | range advantage + nut advantage、 polar value |
| **overbet 125-185%** | super polar (capped opponent) | 相手 capped、 polar value + over-bluff |
| **all-in** | commit | committed range、 jam-or-fold |

### MATCHA bs 6 段階の根拠

本書の bs key は modern GTO の bet sizing 理論に基づきます:

| bs key | 古典 sizing | 値 | 補正 |
|---|---|---:|---:|
| small_33 | range cbet | 0 | 0 |
| med_75p | medium polar | 1 | −2 |
| med_100p | polar (nut adv) | 2 | −4 |
| overbet | super polar | 3 | −6 |
| overbet_185 | very super polar | 4 | −8 |
| allin | commit | 5 | −10 |

各 sizing で「hero の必要 eq」 が変わるため、 Score に `−2 × bs` の減算項で
正確に反映されます。

### bet sizing 戦略の MATCHA 対応

| 状況 | MATCHA 公式 |
|---|---|
| dry board + range adv | bs=0、 補正 0 (33% small) |
| wet board + nut adv | bs=2、 補正 −4 (100% polar) |
| capped opp + nut adv | bs=3、 補正 −6 (150% overbet) |
| short stack push | bs=5、 補正 −10 (all-in) |

MATCHA Score は bet sizing 理論を **数値の引き算** で吸収します。 戦略を覚える代わりに
公式で計算するだけで対応可能です。

## 13.10 暗記項目: 古典理論と MATCHA の対応 1 ページ早見表

詳細は **付録 B (古典理論との橋渡し早見表)** に再掲します。 ここでは 9 つの主要対応を
1 ページに集約:

| 古典理論 | MATCHA 対応 |
|---|---|
| Outs と Rule of 4/2 | DV × mult[street] (flop ×3 / turn ×2 / river ×0) |
| 古典ボード 7 分類 | 3 タイプ集約 (dry / paired / wet) |
| 6 階層 Hand Strength (Sklansky-Malmuth) | 4 カテゴリ 集約 (上位 3 つを 2P+統合) |
| SPR 1-3-7 切り分け | MATCHA 4 段階 (オールイン / ロー / ミディアム / ディープ)、 SPR=3 反転点 |
| Pot Odds / MDF | bs 別 pot odds (25-41%)、 Score 閾値 14/43 |
| Range Morphology (polar/linear/capped) | 2 極化型 / 混在型 / 密集型、 Grid 値で吸収 |
| Sklansky Hand Groups (preflop) | postflop カテゴリ の系譜、 群 1-2 → 2P+ |
| Theory of Poker (Sklansky) | Score 公式が EV ギャップを整数近似で最小化 |
| Bet Sizing 理論 (modern GTO) | bs 6 段階、 −2 × bs で補正 |

古典理論を学んだ読者は、 この対応表 1 つで MATCHA Score の各要素が「既知の概念の
再構成」 として理解できるはずです。

## Cash/MTT note

古典理論との対応は Cash / MTT chipEV で共通です。 Sklansky / Janda / Flynn の古典
文献は主に Cash 100bb / heads-up を想定していましたが、 本書の 4 カテゴリ × 3 board ×
Grid 12 cells は **Cash 100bb と MTT chipEV (25/50/100/200bb) で同公式**です。

ただし、 古典理論の前提 (deep stack、 no ante、 chipEV) は MTT 後期 / バブル
では崩れます。 第 21-23 章での補正は古典理論の **拡張** として理解
してください。

## この章で覚える項目 (9 items)

1. Rule of 4/2 → DV × mult (flop ×3 / turn ×2 / river ×0)
2. 古典ボード 7 分類 → MATCHA 3 分類 (dry / paired / wet)
3. 6 階層 Hand Strength → MATCHA 4 カテゴリ (2P+統合)
4. 古典 SPR 1-3-7 → MATCHA 4 段階、 SPR=3 反転点
5. Pot Odds: bs 33%→25% / 75%→30% / 100%→33% / overbet→38%
6. MDF と Score 閾値の対応 (14 = pot odds 25% / 43 = 50%+)
7. Range Morphology: polar / linear / capped → MATCHA 2極化 / 混在 / 密集
8. Sklansky 群 1-2 = 2P+、 群 3-4 = TP+、 群 5-7 = ミドル、 群 8 = エア
9. Theory of Poker (Sklansky 1987) = Score 公式が EV ギャップを整数近似で最小化
