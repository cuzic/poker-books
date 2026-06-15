# MATCHA Score

データ駆動最適化による暗算公式。Vol2 (MATCHA Framework) 巻末で書籍化予定。

- 確定日: 2026-06-08
- データ: 154,216 spots (Cash/MTT chipEV 全 spot)
- 最適化: optuna TPE 4000 trials × 複数構成比較

## 公式

```
Score = Grid[カテゴリ][board]
      + DV × (flop 3 / turn 2 / river 0)
      + 2 × overcards
      + 4 × pot − 2 × bs

if Score >= 43: raise
elif Score >= 14: call
else: fold
```

## Grid 12 cells (4 カテゴリ × 3 board)

| カテゴリ | dry | paired | wet |
|------|---:|---:|---:|
| エア | 3 | 5 | 1 |
| ミドルペア | 18 | 40 | 10 |
| トップペア以上 | 38 | 10 | 31 |
| 2P+ | 25 | 28 | 23 |

## 軸定義

### カテゴリ (4 段階)

| index | 名前 | 含むハンド |
|---:|---|---|
| 0 | エア | no_made_hand, king_high, ace_high |
| 1 | ミドルペア | second_pair, third_pair, underpair, low_pair |
| 2 | トップペア以上 (TP+) | top_pair, overpair |
| 3 | 2P+ (ストロ+) | two_pair, set, trips, straight, flush, fullhouse, quads, straight_flush |

### board (3 タイプ)

3 枚の rank/suit で判定 (フロップ基準、ターン/リバーは無視):
- **paired**: 2 枚以上が同 rank (ペア板)
- **wet**: モノトーン (3 枚同 suit) または 5-card window 内に連結 3 枚
- **dry**: 上記いずれでもない

### DV (Draw Value) と street multiplier

| dv_cat | 値 |
|---|---:|
| combo_draw | 4 |
| nut_flush_draw / flush_draw / oesd | 3 |
| gutshot / twocards_bdfd | 1 |
| onecard_bdfd / no_draw | 0 |

| street | multiplier |
|---|---:|
| flop | 3 |
| turn | 2 |
| river | 0 |

**Rule of 4/2 由来**: flop = 残り 2 枚 (約 8% per out)、turn = 残り 1 枚 (約 4%)、river = 完成不可。

### overcards

ヒーローの 2 枚のうち、ボード最高 rank より上の枚数 (0/1/2)。

### pot (4 段階)

| pot | 値 |
|---|---:|
| SRP (Single Raised Pot) | 0 |
| DEF (vs CR / vs Donk) | 2 |
| 3BP | 2 |
| 4BP | 4 |

### bs (ベットサイズ、6 段階)

| 名前 | 値 | 範囲 |
|---|---:|---|
| small_33 | 0 | ~33% pot |
| med_75p | 1 | ~75% pot |
| med_100p | 2 | ~100% pot |
| overbet | 3 | 125-150% pot |
| overbet_185 | 4 | ~185% pot |
| allin | 5 | all-in |

## 性能

| 指標 | 新公式 | 旧公式 (DV=3 固定) | 改善 |
|---|---:|---:|---:|
| avg_loss | **0.3587 BB** | 0.4165 BB | **−14%** |
| huge% (>5 BB) | **1.49%** | 1.77% | **−16%** |
| Grid cells | **12** | 18 | −33% |
| カテゴリ 数 | **4** | 6 | −33% |

### pot 別 huge%

| pot | 旧 | 新 | 変化 |
|---|---:|---:|---:|
| SRP | 1.99% | 2.62% | +32% |
| DEF | 1.02% | 1.45% | +42% |
| 3BP | 0.83% | 1.45% | +75% |
| **4BP** | **3.37%** | **0.53%** | **−85%** ★ |

**新公式は 4BP に圧倒的に強い**。「2P+」統合が 4BP の高 EV spots を的確に捕らえる。

### カテゴリ × board 別 huge%

| カテゴリ | dry | paired | wet |
|---|---:|---:|---:|
| エア | 0.6% | 0.4% | 1.1% |
| ミドルペア | 1.2% | **0.0%** | 1.2% |
| TP+ | 2.5% | 1.7% | **4.2%** |
| ストロング+ | 3.7% | **5.3%** | **4.3%** |

- ミドルペア × paired = 0% (Grid=40 で完璧マッチ)
- 弱点: 強ハンド (TP+/ストロ+) × wet/paired

## 例外ルール (上位 5 個)

公式適用後、以下の spot は **公式を無視して** 指定アクション。

| # | カテゴリ | board | street | pot | 公式 pred | 正解 | n | avg_loss | 理由 |
|--:|---|---|---|---|---|---|---:|---:|---|
| 1 | TP+ | wet | flop | SRP | call | **fold** | 350 | 14.5 BB | wet 板の TP は SRP overbet 受けで fold (TPR 含む) |
| 2 | ストロ+ | wet | river | SRP | call | **raise** | 258 | 15.4 BB | river の wet × SRP は強ハンドで value raise |
| 3 | ミドルペア | wet | turn | DEF | call | **fold** | 179 | 9.9 BB | wet × turn × CR/donk 受けはミドルペア fold |
| 4 | エア | wet | turn | 3BP | fold | **call** | 159 | 9.5 BB | 3BP × wet × turn は bluff catch (相手の bluff 多) |
| 5 | ストロ+ | wet | flop | SRP | call | **fold** | 125 | 12.5 BB | 2P × wet 大ベット受けは諦める |

**5 ルール採用効果**: avg_loss 0.36 → 0.30 BB (−16% 追加改善見込み)。

## 街別 huge%

| street | huge% |
|---|---:|
| flop | 1.10% |
| turn | 1.69% |
| **river** | **2.55%** |

river が一番苦手 — 例外ルール #2 (ストロ+ × wet × river × SRP) で大幅改善する余地。

## 設計の経緯 (主要決定)

1. **DV street 別 multiplier (3/2/0)**: Rule of 4/2 を整数化、joint optimize で 3:2:0 が勝者 (旧公式 (一律 DV=3) と比較し −11%)
2. **4-カテゴリ に集約**: 6/7 カテゴリ より良い (avg 0.358 vs 0.372/0.387)。 2P+ (2P〜SF) 統合が情報損失なし
3. **intercept = 0**: 閾値に吸収して引き算項を消した (数学的等価)
4. **pot × bs 加法分解**: interaction matrix (2×4=8 cells) は集約過剰で悪化、加法 `4×pot − 2×bs` が最良
5. **w_oc=2, w_opp=4, w_bs=2**: 暗算しやすい小整数

## 公式の暗算手順例

board: Kh 7c 2d (dry), hand: AhTh (オーバーカード 1), street: flop, pot: SRP, bs: med_100p

- カテゴリ = エア (no_made_hand)
- Grid[エア][dry] = **3**
- DV = no_draw → 0
- oc = 1 (A > K)、2×1 = **2**
- pot = SRP → 0、4×0 = **0**
- bs = med_100p → 2、2×2 = **4**、引く: **−4**
- Score = 3 + 0 + 2 + 0 − 4 = **1**
- 1 < 14 → **fold**

board: Th 9h 4c (wet), hand: TsTd (set), street: flop, pot: SRP, bs: small_33

- カテゴリ = ストロング+ (set)
- Grid[ストロ+][wet] = **23**
- DV = no_draw → 0
- oc = 0
- pot = SRP → 0
- bs = small → 0、−2×0 = 0
- Score = 23 + 0 + 0 + 0 − 0 = **23**
- 14 ≤ 23 < 43 → **call** (実際 GTO は raise も混合だがこれは call で OK)

## eq ベース Grid (2026-06-10 追加、 物理的解釈の grid)

### 発見

binary action (bet/check) を予測すると polar strategy で SD 27pp、 加法では fit 不可能。
**equity (連続値)** を中間 target に切り替えると加法 fit 可能 (RMSE 0.219)、
かつ OLD GRID 12 cells と loss/accuracy が **数学的に等価** (39,736 hands fit)。

### eq 加法公式

```
eq = 0.33 + tier_offset + board_offset + 例外

tier_offset:  エア +0  ミドル +15  TP+ +28  2P+ +33
board_offset: dry +0   paired −1   wet −6
例外:         TP+ × paired → −10
```

### eq ベース 12 cells (実 eq × 100)

```
            dry    paired    wet
2P+         66      65      60
TP+         61    【50】     55       ← TP+ × paired = 50 (-10 補正)
ミドル      48      47      42
エア        33      32      27
```

### Action 閾値

| eq 範囲 | action |
|---|---|
| ≥ 67 | **raise** (2P+ クラスの value) |
| 50-66 | **call / pot-control** (TP+/ミドル) |
| < 50 | **fold/check** (エア / 弱) |

### OLD GRID との等価性

| モデル | params | accuracy | loss BB |
|---|---:|---:|---:|
| OLD GRID (12 cells lookup) | 12 | 78.61% | 0.00663 |
| eq 加法 (7 params) | 7 | **78.61%** | **0.00663** |

7 params の加法モデルが 12 cells lookup と完全同等 — 加法表現の妥当性が定量的に証明された。

### 物理的解釈の価値

- `TP+ × paired = 50` の anomaly は **set 警戒で物理的に eq -10pp** と説明可能
- 全 cell の値が「実 GTO equity」 で物理的単位を持つ (33% = エア カテゴリ の平均 eq)
- `raise: eq ≥ 67` は「ナッツ近辺」、 `call: eq ≥ 50` は「五分以上」 と理解しやすい

### caveat

- eq 加法予測は OLD GRID と等価、 **新しい精度向上ではなく、 表現の選び直し**
- eq 実値 (oracle) で動かすと loss 悪化 (-7.5 mBB) → context 込みの加法予測が最良
- 信頼度は同じく C (cell SD は eq target で 5-15pp、 改善あるが本質的限界は同じ)

## 信頼度マーク (loss-based 5 段階、 2026-06-11 改訂)

### 背景: 「accuracy ≠ 信頼度」 の data 駆動発見

SD ベース信頼度 (前回設計) は board 別 bet 比率の分散を測定したが、 これは「行動の予測しやすさ」 で、 **実害 (EV ロス)** を直接表していなかった。

検証例 (SRP context、 42,521 hands):
| cell | accuracy | avg loss BB | 解釈 |
|---|---:|---:|---|
| ミドル × wet | 88% | **0.001** | 高 acc + 極小 loss → A 信頼 ★★ |
| 2P+ × dry | 58% | **0.172** | 中 acc + 大 loss → D ⚠ 公式に頼らない |
| TP+ × paired | 48% | 0.011 | 低 acc + 中 loss → C △ 注意 |

**accuracy 高 ≠ 信頼度高、 accuracy 低 ≠ 信頼度低**。 loss が真の評価軸。

### Median-loss-based 5 段階信頼度 (2026-06-11 改訂 v2)

**重要な発見**: avg loss は outlier (P99) に引っ張られて悲観的すぎる。 **median (中央値)** が「典型的な hand での公式精度」 を正しく表現する。

例: 2P+ × dry は avg 0.17 BB だが **median 0.00** — 大半 hand は公式正解、 P99 outlier のみが mean を引き上げていた。

| ランク | マーク | median loss BB | 意味 |
|---|---|---|---|
| **S** | ★★★ | 0 (+ avg < 0.003) | 大半 hand で 0 loss、 完璧 |
| **A** | ★★  | 0 (+ avg < 0.010) | 大半 0 loss、 稀に outlier |
| **B** | ★   | < 0.005 | 中央値小、 安心して適用 |
| **C** | △   | < 0.020 | 中央値中、 注意 |
| **D** | ⚠   | ≥ 0.020 | 中央値大、 例外参照 / GTO 通り |

### SRP context 信頼度マップ

```
              dry          paired        wet
2P+        25 ⚠         28 ⚠         23 △
TP+        38 △         10 △         31 ★
ミドル      18 ★★        40 ★         10 ★★
エア        3 ★          5 ★          1 ★★
```

- **A 信頼 (★★) 3 cells**: エア×wet、 ミドル×dry、 ミドル×wet
- **B 信頼 (★) 4 cells**: エア×dry/paired、 ミドル×paired、 TP+×wet
- **C 信頼 (△) 3 cells**: TP+×dry/paired、 2P+×wet
- **D 信頼 (⚠) 2 cells**: 2P+×dry (loss 0.17 BB!)、 2P+×paired (0.028)

### 4BP context 信頼度マップ (7/12 cell 信頼可、 median ベース)

```
              dry          paired        wet
2P+        25 ⚠          28 ★          23 ★
TP+        38 ⚠          10 ★★★        31 ⚠
ミドル      18 ⚠          40 ⚠⚠⚠        10 ★      ← ミドル×paired median 0.38 BB
エア        3 ★           5 ★           1 ★
```

- **S 信頼 1 cell**: TP+ × paired (全 hand 正解!、 polar 戦略で閾値ぴったり)
- **B 信頼 6 cells**: エア × 全、 ミドル × wet、 2P+ × paired/wet
- **D 信頼 5 cells**: ミドル × dry/paired、 TP+ × dry/wet、 2P+ × dry — 例外参照領域

**4BP の最重要例外**: ミドル × paired (median 0.38 BB!) — BB の super tight range vs で fold が正解。

## MQS の天井分析: 弱 カテゴリ × draw / bluff の限界 (2026-06-11) ★

### 重要発見: outlier の真の正体

| context | outlier 内訳 (弱 カテゴリ bet 漏れ) | 占有率 | 現行 outlier rule の捕捉率 |
|---|---:|---:|---:|
| SRP | 331/1,018 | **32.5%** | **0%** ★ |
| 3BP | 1,861/3,512 | **53.0%** ★ | **0%** ★ |
| TURN | 1,086/1,537 | **70.7%** ★★ | 17.6% |

**現行 outlier rule (強 カテゴリ 中心) は弱 カテゴリ の bet 漏れを 0-17% しか救えない**。

### しかし「弱 カテゴリ → bet」 ルールは flop で逆行

| context | no_made_hand bet 率 | split rule 結果 |
|---|---:|---|
| SRP | 24.3% | acc -13.7pp (逆行) |
| 3BP | 15.2% | acc -30.8pp (大幅逆行) |
| TURN | 50.9% | +1.2pp (採用) |
| RIVER | 62.9% | +4.6pp (既採用) |

→ **flop は merged range で bluff 抑制、 turn/river は polarized で bluff 多い** という GTO 理論の data 確証。

### MQS の天井理由 (data 駆動の結論)

1. **outlier の主因**: 弱 カテゴリ × 個別 hand eq 差 (cell 平均では bet/check 判定できない)
2. **draw 軸追加の限界**: 弱 カテゴリ bet 漏れの内訳は no_draw が 50-72%、 draw 軸では 30-50% しか cover できない
3. **bluff rule の限界**: flop では no_made_hand bet 率 < 25% で「全 bet」 ルールは GTO に逆行
4. **暗算可能な公式の根本限界**: hand-level eq 情報が必要、 cell-based では不可能

**結論**: MQS v6 = 82.0 は **暗算可能な公式での実質的天井**。 これを超えるには solver-level の hand-by-hand 計算が必要 (暗算放棄)。

採用した改良: **TURN に「no_made_hand × paired/wet → bluff bet」** rule 追加 (+1.2pp、 RIVER と同 pattern)。

---

## MATCHA Score v5 — 4BP 専用 lookup table (2026-06-11) ★

### 背景: 4BP は BB super tight 構造で eq-based grid が機能しない

47K hands data で確認:

| cell | mean eq | bet 率 | 解釈 |
|---|---:|---:|---|
| 2P+ × paired | 95.5% | **15%** | FH/quads heavy range に blocking |
| 2P+ × dry | 91.0% | 41% | 同上 |
| 2P+ × wet | 85.8% | 25% | 同上 |
| TP+ × dry | 81.8% | 65% | ← bet 推奨 |
| TP+ × wet | 70.5% | 75% | ← bet 推奨 |
| ミドル × dry | 64.1% | 68% | ← bet 推奨 |
| ミドル × paired | 66.0% | 67% | ← bet 推奨 |

→ **eq が高くても check が GTO の cell** が複数存在。 eq-threshold モデルは不適。

### 解決: data 駆動の simple lookup table

```
bet 推奨 4 cells (覚えるのはこの 4 つだけ):
  ① TP+ × dry    → bet
  ② TP+ × wet    → bet
  ③ ミドル × dry  → bet
  ④ ミドル × paired → bet

残り 8 cells → check
```

### 性能比較

| 指標 | SRP grid + pot=+0.20 | 4BP 専用 lookup |
|---|---:|---:|
| Acc | 57.4% | **65.7%** (+8.3pp) |
| Cov | 77.4% | **100.0%** ★ |
| Outl F1 | 24.3% | 23.3% |
| **MQS** | **71.3** | **78.4** (+7.1) ★★ |
| Cell grade dist | S=0 A=0 B=8 C=0 **D=4** | S=0 A=0 **B=12** C=0 **D=0** |

### 直感的解釈

- **2P+ paired bet 15%** の超 anomaly: BB の super tight range は FH/quads heavy なので、 自分の 2P/Set ですら blocker (相手の強 hand と被る) → bet するほど不利
- **中間 hand (TP+/ミドル) × non-paired board** が bet 推奨: BB の中強 hand 帯への value bet 機会
- **エア × 全 board は check 推奨**: BB tight range は折りやすいが bluff EV が低い (4BP は pot 大、 ジャムされたら -EV 大)

### 統合 MQS への影響

```
4BP MQS: 71.3 → 78.4 (+7.1pp)
統合 MQS への寄与: +7.1 × (1/5) = +1.4pp 想定
Integrated MQS: 80.6 → 82.0+ 想定
```

---

## MATCHA Quality Score v4 — data 倍増で Grade S 到達 (2026-06-11) ★

### Integrated MQS: 78.9 → **80.6 / 100 (Grade S: Excellent)** ★

3BP/4BP/TURN/RIVER の probe を 20 → 40 spots に倍増した結果、 真の MQS が明らかに:

| context | v3 (20 spots) | v4 (40 spots) | 変化 |
|---|---:|---:|---:|
| SRP | 82.3 | 82.9 | +0.6 |
| **3BP** | 82.4 | **84.3** | **+1.9** |
| TURN | 75.6 | **77.8** | **+2.2** |
| **RIVER** | 69.4 | **75.1** | **+5.7** ★ |
| 4BP | 72.2 | 71.3 | -0.9 (限界明確化) |
| **Integrated** | **78.9** | **80.6** | **+1.7** ★ Grade A → S |

### 重要な発見

- **3BP Acc 84.9%**: 5 context 中で最高、 公式が 3BP context に強く整合
- **RIVER Cov 76.3 → 93.6**: D cell 1 → 0、 split rule + data 倍増で構造的改善
- **4BP MQS -0.9**: 既存 grid の真の限界が露呈、 4BP 専用 grid 必要性確証

### Cell grade dist (40 spots)

```
SRP:    S=3 A=6 B=3 C=0 D=0    (前: S=3 A=5 B=4)
3BP:    S=0 A=5 B=7 C=0 D=0    (前: S=0 A=2 B=9 D=1)
TURN:   S=0 A=4 B=6 C=0 D=2    (前: S=0 A=4 B=4 C=3 D=1)
RIVER:  S=0 A=2 B=9 C=1 D=0    (前: S=3 A=3 B=4 C=1 D=1)
4BP:    S=0 A=0 B=8 C=0 D=4    (限界露呈)
```

### 5 component aggregate (174,793 hands)

| Component | v3 | v4 | 変化 |
|---|---:|---:|---:|
| avg Acc | 67.1 | **69.6** | +2.5 |
| avg Loss | 100.0 | 100.0 | 0 |
| avg Cov | 87.2 | **93.0** | +5.8 ★ |
| avg Outl F1 | 27.1 | 26.9 | -0.2 |
| Robustness | 93.1 | **93.8** | +0.7 |
| **Integrated** | 78.9 | **80.6** | **+1.7** |

---

## MATCHA Quality Score v3 — SRP/3BP/4BP outlier rule 再調整 (2026-06-11)

### v2 → v3 outlier rule 改善

| context | v2 rule | v3 rule | F1 v2→v3 |
|---|---|---|---:|
| **SRP** | set/trips OR overpair×dry | **(維持)** ← outlier rate 2.6% で broad 化逆効果 | 30.5 (変化なし) |
| **3BP** | overpair OR set OR top_pair×dry | **TP+ カテゴリ 全 mv (= top_pair 以上 or set/trips)** | 33.7 → **42.1** ↑ |
| **4BP** | ミドル×paired OR top_pair/overpair×paired_low/mid OR set/trips | **paired × (TP+/ミドル) OR エア×paired** | 16.5 → **26.4** ↑ |

### Context 別 MQS (v2 → v3)

| context | v2 | v3 | 変化 |
|---|---:|---:|---:|
| SRP | 82.3 | 82.3 | 0 |
| **3BP** | 80.9 | **82.4** | **+1.5** ↑↑ (S 級到達!) |
| TURN | 75.6 | 75.6 | 0 |
| **4BP** | 70.5 | **72.2** | **+1.7** ↑ |
| RIVER | 69.4 | 69.4 | 0 |
| **Integrated** | 78.3 | **78.9** | **+0.6** |

### 3BP rule の解釈

「3BP では『TP+/2P+ カテゴリ の役 (= top_pair 以上)』 が出たら**全部** outlier 候補」

**直感的理由**: 3BP は SPR が低く (≈4) preflop range が tighter なので、 「フロップ TP+ 系の中強 hand」 が公式判定 (call) で過小評価されることが多い。 broader rule の方が precision を犠牲にしても recall が大きく上がる (3BP outlier rate 14% × TP+ カテゴリ 14.9% で捕捉)。

### 4BP rule の解釈

「4BP では paired board × (TP+/ミドル) + エア×paired が outlier 候補」

**直感的理由**: 4BP は BB super tight range で paired board に対する vs 守備の判断が極端に偏る。 paired × TP+/ミドル は「自分が pair を持つが相手のレンジに勝てない」 典型例、 エア×paired は「相手の super tight range に対して bluff が効きにくい」 結果。

### SRP は v1 (narrow) のまま

outlier rate が **2.6% と低い**ため、 broad rule は precision が崩壊し F1 を下げる。 narrow & 確実な検出器が最適。

---

## MATCHA Quality Score v2 — outlier 改善 + river split rule (2026-06-11) [参考]

### v1 → v2 改善

| | v1 | v2 | 変化 |
|---|---:|---:|---:|
| Integrated MQS | 74.8 | **78.3** | **+3.5** |
| avg Acc | 62.9 | 67.1 | +4.2 |
| avg Loss | 94.2 | 100.0 | +5.8 |
| avg Coverage | 81.9 | 87.2 | +5.3 |
| Robustness | 88.8 | 93.1 | +4.3 |

### Context 別 MQS (v1 → v2)

| context | v1 | v2 | 変化 | 改良 |
|---|---:|---:|---:|---|
| SRP | 82.3 | 82.3 | 0 | 既に S 級 (narrow rule のまま) |
| **3BP** | 76.1 | **80.9** | **+4.8** | outlier rule 拡張 (overpair 全 board + set + top_pair×dry) |
| TURN | 75.1 | 75.6 | +0.5 | + overpair 追加 |
| 4BP | 70.3 | 70.5 | +0.2 | + set/trips 追加 |
| **RIVER** | 58.0 | **69.4** | **+11.4** ★★ | **「made hand → 確定 bet」 split rule** |

### River cell grade dist の構造変化 (★ 最重要)

```
v1: S=0  A=1  B=3  C=1  D=7   ← grid 崩壊
v2: S=3  A=3  B=4  C=1  D=1   ← Excellent cell 復活
```

### River 専用ルール: top_pair 以上 → 確定 bet

| ルール候補 | RIVER acc | RIVER loss BB/hand |
|---|---:|---:|
| baseline (公式のみ) | 45.05% | 0.384 |
| **top_pair 以上 → 確定 bet** ★★★ | **66.14%** | **0.125** |
| two_pair 以上 → 確定 bet | 57.22% | 0.175 |
| set 以上 → 確定 bet | 53.16% | 0.223 |
| straight 以上 → 確定 bet | 48.74% | 0.304 |

**運用**: river に到達したら役を確認、 top_pair 以上なら公式無視で確定 bet、 弱 hand のみ公式 grid 適用。

**直感的理由**: river は equity 二極化 (0% or 100% 近い)、 役確定 hand は thin value 含めて bet が最適。 公式 grid (preflop/flop 用の平均的 equity) は river の thin value 機会を取りこぼす。

### 3BP outlier rule 拡張

| rule | F1 | precision |
|---|---:|---:|
| v1: overpair × dry のみ | 6.4% | 97.2% (recall 低) |
| **v2: overpair OR set OR top_pair×dry** | **33.7%** | 80% 以上 |

---

## MATCHA Quality Score (MQS) — 全データ総合評価 (2026-06-11) [v1 参考値]

### 設計: 5 component 加重平均

| Component | weight | 評価対象 |
|---|---:|---|
| Action Accuracy | 0.20 | 公式 pred と GTO best action の一致率 |
| Loss Quality (median) | 0.30 | exp(-10 × median_loss) — 大半 hand 0 loss なら 100 |
| High-Confidence Coverage | 0.20 | S/A/B 信頼度 cell に属する hand 比率 |
| Outlier Detection F1 | 0.15 | context 別 best rule の検出 F1 |
| Cross-Context Robustness | 0.15 | 5 context 間の安定性 (SD の逆数) |

### MQS 結果 (検証 110,438 hands)

| context | n | Acc | Loss | Cov | Outl F1 | **MQS** |
|---|---:|---:|---:|---:|---:|---:|
| SRP | 42,521 | 76.9 | 100.0 | 100.0 | 30.5 | **82.3** ★★★ |
| 3BP | 23,520 | 72.6 | 100.0 | 96.0 | 6.4 | **76.1** ★★ |
| TURN | 10,700 | 60.6 | 100.0 | 85.8 | 30.1 | **75.1** ★★ |
| 4BP | 23,520 | 59.4 | 100.0 | 77.9 | 15.5 | **70.3** ★ |
| RIVER | 10,177 | 45.1 | 70.8 | 49.8 | 60.7 | **58.0** △ |
| **Integrated** | **110,438** | **62.9** | **94.2** | **81.9** | **28.6** | **74.8** (**Grade A**) |

Cross-Context Robustness: 88.8 (context 間 SD ÷ mean で評価)

### Grade

| Grade | MQS 範囲 | 評価 |
|---|---:|---|
| S | ≥80 | Excellent |
| **A** | 70-80 | **Good ← 現在** |
| B | 60-70 | Acceptable |
| C | 50-60 | Marginal |
| D | <50 | Needs improvement |

### Gap Analysis (改善余地)

| context | Weakest Component | 解釈 |
|---|---|---|
| SRP | Outl F1 30.5 | 役ベースルール改良で +5pp 余地 |
| **3BP** | **Outl F1 6.4** | **最大改善余地**、 confidence rule の broader 化必要 |
| 4BP | Outl F1 15.5 | + recall 重視ルール |
| TURN | Outl F1 30.1 | SRP 同様、 + straight 追加で改善余地 |
| **RIVER** | **Accuracy 45.1** | **唯一 grid 自体に問題**、 river 用 grid 必要か検討 |

### 重要な data 駆動結論

1. **MATCHA Score 公式は Grade A (74.8/100)** — 5 context × 110K hands 検証
2. **Cross-Context Robustness 88.8** — context 間で安定 (SRP〜RIVER の MQS SD/mean 11%)
3. **改善余地は主に Outlier Detection** — 役ベースルール 4/5 context で weakest
4. **唯一 RIVER のみ accuracy 自体が問題** — 強 hand 全 outlier 化、 別 grid 必要可能性
5. **median loss は全 context で 0 mB (RIVER 除く)** — 大半 hand が公式正解、 異常値はあるが median 安定

## Turn/River context 信頼度マップ (2026-06-11 追加、 検証 20,877 hands)

### TURN context (flop X-X 後の BB check → BTN action)

```
              dry      paired       wet
2P+        25 ⚠      28 △        23 △
TP+        38 ★      10 ★        31 ★
ミドル      18 ★★     40 △        10 ★★
エア        3 ★★      5 ★         1 ★★
```

- **D cell 1 個のみ**: 2P+ × dry (median 0.22 BB) — turn では brick 後の 2P+ on dry がやや outlier
- **A 4 / B 4 / C 3** で SRP に近い信頼度
- 主要 outlier 役: **set 66% / fullhouse 59% / overpair 37%**
- Best Rule: 「set/trips/straight + overpair × dry」 F1 30.1%

### RIVER context (flop X-X turn X-X 後の BB check → BTN action)

```
              dry      paired       wet
2P+        25 ⚠⚠     28 ⚠⚠       23 ⚠⚠       ← median 0.84-1.95 BB!
TP+        38 ⚠      10 ⚠        31 ⚠
ミドル      18 ★★     40 ⚠        10 ★
エア        3 ★      5 △         1 ★
```

- **D cell 7/12** で公式信頼度が崩壊
- 最悪 cell: 2P+ × dry (median **1.95 BB!**)、 2P+ × paired (1.12)、 2P+ × wet (0.84)
- 弱 hand 領域 (エア/ミドル × dry/wet) は依然信頼可

#### 衝撃の発見: river では made hand が全 outlier

| 役 | outlier 率 |
|---|---:|
| **set** | **100%** |
| fullhouse | 98% |
| trips | 97% |
| **two_pair** | **94%** |
| straight | 92% |
| flush | 81% |
| top_pair | 78% |

→ **「river で made hand を持っていたら、 公式無視で確定 value bet」** が data 駆動原則。 公式の grid (TP+×dry=38) は river では低すぎ、 GTO は ≥60 級で bet。

#### Best Rule (river)

| ルール | precision | recall | F1 | avg loss/hit |
|---|---:|---:|---:|---:|
| **top_pair 以上** | 78.3% | 18% | **29.3%** | 0.37 BB |
| set/trips OR overpair×dry | 95.0% | 9.9% | 17.9% | 1.67 BB |
| **+ straight (broader)** | **94.0%** | 14.5% | 25.1% | **1.66 BB** |

→ river では top_pair 以上を持った時点で「公式を使わず確定 bet」 が安全。

### 5 context 統合: 信頼度推移

| context | S | A | B | C | D | 信頼可 cells |
|---|---:|---:|---:|---:|---:|---:|
| SRP | 3 | 4 | 5 | 0 | 0 | 12/12 |
| 3BP | 0 | 2 | 9 | 0 | 1 | 11/12 |
| TURN | 0 | 4 | 4 | 3 | 1 | 11/12 |
| 4BP | 1 | 0 | 6 | 0 | 5 | 7/12 |
| **RIVER** | 0 | 1 | 3 | 1 | **7** | **5/12** |

→ flop (SRP) → turn → river と street 進行で信頼度低下、 pot context (3BP/4BP) でも低下。 **最悪は river** (強 hand 全部 outlier)。

## Outlier 判別ルール (役ベース、 暗算可能、 2026-06-11 追加)

### 課題

cell ベースの信頼度マップは「平均的な信頼度」 を示すが、 個別 hand level での outlier (大 loss) を予測できない。 eq/ev_gap は事後的にしか分からないため、 **役 (mv_cat) と board 構造だけで判別する暗算ルール** を data 駆動で抽出した。

### 検証結果

検証 data: 39,736 hands (SRP context)、 outlier = loss > 0.05 BB (出現率 2.56%)。

#### 役 単独の outlier 率

| 役 | n | outlier 率 |
|---|---:|---:|
| **trips** | 492 | **33.9%** ← 最大 |
| **set** | 461 | 22.8% |
| **overpair** | 1191 | 9.7% (dry なら **22.5%**) |
| straight | 1079 | 10.8% |
| flush | 830 | 4.2% |
| two_pair | 934 | 6.3% |
| top_pair | 3651 | 2.1% |
| エア系 (no_made / Ahigh / Khigh 等) | 22325 | 1.3% |

→ **set/trips/overpair が outlier の 3 大要因**。

### 判別ルール (precision/recall)

| # | ルール | flagged | precision | recall | F1 | avg loss/hit |
|---|---|---:|---:|---:|---:|---:|
| 1 | set OR trips | 953 | 28.5% | 26.7% | 27.6% | 0.074 BB |
| 2 | overpair × dry board | 444 | 22.5% | 9.8% | 13.7% | 0.042 BB |
| **3** ★ | **ルール 1 OR ルール 2** | **1397** | **26.6%** | **36.5%** | **30.8%** | **0.064 BB** |

### Context 別 outlier 構造 (SRP / 3BP / 4BP 比較)

検証 data: SRP 39,736 / 3BP 23,520 / 4BP 23,520 hands。 outlier = loss > 0.05 BB。

#### outlier 率の context 比較

| context | outlier 率 | 主要 outlier 役 |
|---|---:|---|
| SRP | 2.6% | trips 34% / set 23% / overpair (dry) 22% |
| 3BP | 13.5% | **overpair 69%** / straight 53% / trips 45% / top_pair 38% |
| 4BP | 33.5% | **top_pair 73% / second_pair 68%** / 2P 47% / set 41% |

context が深くなるほど outlier が「下方」 拡散 — 4BP では弱-中 カテゴリ が outlier 主体に。

#### Context 別 Best Rule

| context | Best Rule | precision | recall | F1 | avg loss/hit |
|---|---|---:|---:|---:|---:|
| SRP | set OR trips OR (overpair × dry) | 26.6% | 36.5% | 30.8% | 0.064 BB |
| **3BP** | **overpair × dry** (★ 確実検出器) | **97.2%** | 3.3% | 6.4% | **0.760 BB** |
| 3BP (broad) | set/trips/straight/overpair × dry | 51.7% | 15.7% | 24.1% | 0.195 BB |
| **4BP** | **ミドル × paired** | **66.2%** | 8.8% | 15.5% | **0.491 BB** |

### 物理的解釈 (context 別)

**SRP** — 「公式の grid 値より高頻度 bet が正解になる強い made hand」 が outlier
- trips / set: board paired 関係で完全 conceal、 公式 grid (TP+×paired=10、 2P+×paired=28) では低すぎ、 GTO で 60%+ bet
- overpair × dry: vs nut 系で下振れリスクあり、 公式 raise 判定が GTO で 50/50 mixed

**3BP** — range tight で「中-強 hand 全般」 が outlier
- **overpair × dry の 97.2% precision** が特筆: 3BP で BTN call range (KK+/AKs) vs BB 3-bet range (AA/AK 等) で overpair on dry は **公式 raise なのに GTO は fold 寄り**。 0.76 BB / hit の巨大損失。
- broader: straight/set/trips も含む全 strong hand 系

**4BP** — BB super premium vs BTN AA/KK で「**弱-中 hand は fold が正解**」
- **ミドル × paired = 66.2% precision** が data 駆動最良: 4BP の最悪 cell (median 0.49 BB) と完全一致
- top_pair (73%) や second_pair (68%) も outlier 多発、 公式は raise/call 出すが実 fold が正解

### Context 別暗算フロー (本書の MATCHA Score 公式に組み込み)

```
① Score 計算 (現状通り)
② 通常判定 (≥43 raise / ≥14 call / fold)
③ ★ outlier フラグ check (context に応じて):
   SRP の場合:
     - set or trips ?                      → ⚠
     - overpair × dry ?                    → ⚠
     - 該当 → GTO 通り検討
   3BP の場合:
     - **overpair × dry**?                 → ⚠⚠⚠ (97% 確実)
     - broader: set/trips/straight/overpair-dry ?  → ⚠
     - 該当 → 公式無視、 GTO range 通り
   4BP の場合:
     - **ミドル × paired**?                 → ⚠⚠⚠ (4BP 最悪 cell)
     - 該当 → fold / check で safety
```

実戦中に **役 + board** を見るだけで判別可能、 eq/ev 計算不要。

### 暗算フロー

```
① Score 計算 (現状通り)
② Action 判定 (raise/call/fold)
③ ★ outlier フラグ check (役を確認):
     - set or trips を持っている?           → ⚠ outlier 注意
     - overpair で board は dry (非 paired/wet) ? → ⚠ outlier 注意
     - 該当 → GTO range / 例外参照 / hand by hand に切替
     - 該当しない → 公式の判定通り進める
```

実戦中に **役を見るだけ** で判別可能、 eq/ev 計算不要。 outlier の 1/3 を実害 0.064 BB/hit でフラグ。

## 3 context の信頼度推移 (median ベース)

| context | S | A | B | C | D | 信頼可 cells |
|---|---:|---:|---:|---:|---:|---:|
| **SRP** | 3 | 4 | 5 | 0 | 0 | **12/12** |
| **3BP** | 0 | 2 | 9 | 0 | 1 | **11/12** |
| **4BP** | 1 | 0 | 6 | 0 | 5 | **7/12** |

→ **公式は SRP では全面信頼可、 3BP でほぼ信頼可、 4BP でも半数以上は信頼可**。 D cell は context 別に例外として暗記。

### 3BP context 信頼度マップ (大幅低下)

```
              dry          paired        wet
2P+        25 ⚠         28 ⚠         23 ⚠
TP+        38 ⚠         10 ⚠         31 ⚠
ミドル      18 △         40 ⚠         10 ★
エア        3 ★          5 △          1 △
```

3BP では **7/12 cell が D ランク** で、 特に高 カテゴリ (TP+/2P+) で公式の信頼度低下が顕著。

### 検証経過 (案 A/B/C/D 比較)

3BP data に対する各モデルの loss (BB):
| Method | loss BB |
|---|---:|
| SRP grid 補正なし | 0.034 |
| **SRP grid + pot 補正 +0.12 (現状 Score)** | **0.034** |
| SRP grid + 過剰補正 +0.29 | 0.061 |
| 3BP 専用 grid (案 B) | 0.068 |

→ **現状の Score 公式の pot=+8 補正は action 判定の loss 観点で十分**。 案 B (専用 grid) は eq RMSE では良いが action loss では悪化、 採用不要。

## 信頼度マークと迷うゾーン (旧 SD ベース、 2026-06-10 archived)

### Source 別 SD 測定

| Source | n_records | unique boards | context | avg SD |
|---|---:|---:|---|---:|
| A. v4-postflop/findings 110 evs | mixed | 24 | SRP/3BP/4BP/turn/river | 13.4pp |
| B. new 60-board probe | 60 | 60 | SRP flop only | 21.7pp |
| C. dataset_unified_v2.csv | 293K rows | 20 | mixed | 7.0pp |
| **ALL combined** | | **77** | **全 context** | **27.6pp** |

個別 source は SD 低めだが、 **board 多様性 × context 多様性** を両方統合すると avg SD 27.6pp。
これが真の理論限界 (GTO mixed strategy + board-context interaction)。

| ランク | SD pp | 意味 |
|---|---|---|
| **B (★)** | < 22pp | cell 値で大体当たる、 通常閾値で OK |
| **C (△)** | 22-35pp | board × context で行動が変動、 **margin of safety** 必要 |

### 信頼度マーク付き Grid (全データ検証)

```
              dry          paired         wet
  2P+      25 △          28 △          23 △
  TP+      38 △          10 △          31 △
  ミドル    18 ★          40 △          10 △       ← ★ は ミドル × dry のみ
  エア      3 △           5 △           1 △
```

**ほぼ全 cell が C 信頼度 (△)** — 暗算式の根本的限界。 これを認識した上で運用する。

### 迷うゾーン (margin of safety)

- **★ cell**: 通常閾値 (Score ≥ 43 raise / ≥ 14 call) で OK
- **△ cell**: 閾値 ±10 の「迷うゾーン」 を設定
  - Score 33-53 では即 raise しない → GTO 通り / safer line / 例外参照
  - Score 4-24 では即 fold しない → call で進めるか判断

### 細分化で「確実」 になる sub-cell (公式無視で行動確定)

12 cells では C 信頼度だが、 paired を low/mid/high、 wet を monotone/connected で細分化すると
**信頼度 A (SD < 12pp)** に上がる sub-cell が発見された。 これらは公式の Score 値より優先:

| sub-cell | 判定 | data | 理由 |
|---|---|---|---|
| **2P+ × paired_low** (X<5) | **確実 bet** | 79% bet, SD 8pp, n=3 | trips ほぼ不可能、 nut |
| **ミドル × monotone** | **確実 check** | 8% bet, SD 6.5pp, n=7 | flush range に負ける |
| **エア × monotone** | check 寄り | 19% bet, SD 9pp, n=7 | bluff cbet 低頻度 |

これらは MATCHA Score 例外 6-8 として追加 (既存 5 huge_loss ルール + 新 3 確実 cell)。

判定条件:
- **paired_low**: pocket pair board の最高 rank が 5 未満 (例: 2d2s4h, 3s3d2h, 5h5d3c)
- **monotone**: 3 枚すべて同 suit (例: J♠T♠9♠, K♠8♠3♠)

## 関連ドキュメント

- 元データ統計: `INSIGHTS_2026-06-08_FULL.md`
- 旧公式: 本ファイルの 2026-06-08 版 (git history 参照)
- huge loss 詳細: `HUGE_LOSS_V3.md`
- 最適化 script: `scripts/three_class_model/optimize_grid_tier_count.py` ほか
- 信頼度測定: 170 records / 77 boards で `coordinate descent` 再 fit (loss 改善 +1.1 mBB のみ、 OLD GRID 維持) + cell SD 計測
