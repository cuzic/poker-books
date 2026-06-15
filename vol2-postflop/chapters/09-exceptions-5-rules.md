# 第 9 章　例外 11 ルール + DEF 閾値補正 (huge loss 回避)

## 9.1 例外ルールの設計思想

MATCHA Score 公式は 154,216 spots で avg loss 0.3587 BB の
高精度を達成しますが、 **huge loss (>5 BB) spots** が 1.49% 残ります。
n = 2,303 個の huge spots は **特定 pattern に集中** しており、 DEF 閾値補正 + 11 の例外ルールを
追加することで大部分を救済できます。

まず **DEF 閾値補正** を適用し、 次に例外ルールを 4 グループに分けて覚えます:

| グループ | ルール番号 | 説明 |
|---|---|---|
| **DEF 閾値補正** | — | vs CR / Donk 時は T_raise=49 (通常 43 から引き上げ)。 精度 DEF_all 80.0 |
| **huge_loss 5** | ex1〜ex5 | wet board 中心の最大損失スポット |
| **確実 cell 3** | ex6〜ex8 | 公式無視で確実 bet / check する特殊 board |
| **Turn CR 専用 2** | ex9〜ex10 | turn × vs CR のみ fold に変換 (⚠️ Donk 不可) |
| **River Donk 1** | ex11 | river × vs Donk × strong で value raise |

## 9.2 huge loss の Pred → Best confusion

公式 pred と GTO best の不一致パターン (n = 2,303) をみてみましょう:

| 公式 pred | GTO best | n | % |
|---|---|---:|---:|
| call | fold | 1,003 | 43.6% |
| fold | call | 528 | 22.9% |
| call | raise | 501 | 21.8% |
| raise | call | 133 | 5.8% |
| fold | raise | 102 | 4.4% |
| raise | fold | 36 | 1.6% |

「公式が call を出したが本当は fold」 が 43.6% で最多です。 これは「相手の overbet
受けでマージナルな TP+/2P+を過大評価」 する公式の癖を示しています。

## 9.3 例外 ex1〜ex5 (huge_loss 5 ルール)

### 例外 1: トップペア以上 × wet × flop × SRP → **fold**

- 公式 pred: `call` / GTO best: **`fold`**
- サンプル: n = 350、 平均 loss = 14.5 BB
- 理由: wet 板の TP+ は SRP オーバーベット受けで fold (TPR 含む)

**適用条件**: カテゴリ = トップペア以上、 board = wet、 street = flop、 pot = SRP が **すべて成立** し、 かつ公式 pred が `call` のとき。

### 例外 2: 2P+ × wet × river × SRP → **raise**

- 公式 pred: `call` / GTO best: **`raise`**
- サンプル: n = 258、 平均 loss = 15.4 BB
- 理由: river の wet × SRP は強ハンドで value raise

**適用条件**: カテゴリ = 2P+、 board = wet、 street = river、 pot = SRP が **すべて成立** し、 かつ公式 pred が `call` のとき。

### 例外 3: アンダーペア × wet × turn × vs CR → **fold**

- 公式 pred: `call` / GTO best: **`fold`**
- サンプル: n = 179、 平均 loss = 9.9 BB
- 理由: wet × turn × CR/donk 受けはアンダーペア fold

**適用条件**: カテゴリ = アンダーペア、 board = wet、 street = turn、 pot = vs CR が **すべて成立** し、 かつ公式 pred が `call` のとき。

### 例外 4: エア × wet × turn × 3BP → **call**

- 公式 pred: `fold` / GTO best: **`call`**
- サンプル: n = 159、 平均 loss = 9.5 BB
- 理由: 3BP × wet × turn は bluff catch (相手の bluff 多)

**適用条件**: カテゴリ = エア、 board = wet、 street = turn、 pot = 3BP が **すべて成立** し、 かつ公式 pred が `fold` のとき。

### 例外 5: 2P+ × wet × flop × SRP → **fold**

- 公式 pred: `call` / GTO best: **`fold`**
- サンプル: n = 125、 平均 loss = 12.5 BB
- 理由: 2P × wet 大ベット受けは諦める

**適用条件**: カテゴリ = 2P+、 board = wet、 street = flop、 pot = SRP が **すべて成立** し、 かつ公式 pred が `call` のとき。


## 9.4 例外 ex6〜ex8 (確実 cell 3 ルール)

### 例外 6: 2P+ × paired_low (board 最高 rank < 5) → 確実 bet

- 理由: paired_low (例: 2-2-4、 3-3-2) で 2P+ は相手の trips がレンジに入りません。 公式 Score 値に関係なく bet/raise 確定 (SD 8pp)
- **適用条件**: board 最高 rank が 4 以下の paired board で 2P+ カテゴリ。

### 例外 7: アンダーペア × monotone (3 同 suit) → 確実 check

- 理由: 3 同 suit board でアンダーペアは相手の flush 完成 range に完敗です。 Score 値に関わらず check (SD 6.5pp)
- **適用条件**: board が 3 同 suit (monotone) でアンダーペア カテゴリ。

### 例外 8: エア × monotone → check 寄り (bet 抑制)

- 理由: monotone でエアのブラフは相手の call range (flush 完成) が固く低 EV です。 公式 bet 判定を抑制します (SD 9pp)
- **適用条件**: board が 3 同 suit (monotone) でエア カテゴリ、 かつ公式 pred が bet/raise。

## 9.5 DEF 閾値補正 (vs CR / vs Donk 共通)

DEF 補正 (pot = 2、 +8 bonus) が **raise を誤発生**させる 2 パターン (ミドル×paired と TP+×dry) があります。
これらは例外ルールではなく、 **DEF 文脈での閾値変更** で対応します。

> **DEF 閾値補正**: vs CR または vs Donk のとき、 T_raise = **49** (通常 43 から引き上げ)

- ミドル × paired × DEF: Score = 40 + 8 = 48 → T=49 では **call**
- TP+ × dry × DEF: Score = 38 + 8 = 46 → T=49 では **call**
- 精度: DEF_all 80.0 Grade S (208K hands 検証)

## 9.6 例外 ex9〜ex10 (Turn CR 専用 2 ルール)

**⚠️ この 2 ルールは vs CR (チェックレイズ) 専用です。 vs Donk (ドンクベット) には適用しないでください。**

### 例外 9: (アンダーペア / TP+) × dry × turn × vs CR → fold に override

- アンダーペア: 公式 pred: `call` (Score ≈ 18 + 8 = 26) / GTO best: **`fold`** (GTO FOLD 71.5%、 RAISE 26.4%、 CALL 2.1%) — n = 144、 avg = 5.54 BB
- TP+: 公式 pred: `call` (Score ≈ 38 + 8 = 46) / GTO best: **`fold`** (GTO FOLD 56%) — n = 194、 avg = 2.13 BB
- サンプル計: n = 338、 平均 loss = 3.60 BB avg
- 理由: Turn vs CR で dry board × アンダーペア/TP+ は villain range が strong すぎ call 維持不可です。 dry × turn CR は「set/trips 確定」文脈です。
- **適用条件**: カテゴリ = アンダーペアまたはトップペア以上、 board = dry、 street = turn、 pot = vs CR のみ。 ⚠️ vs Donk 不可 (Donk turn × dry は call が正解)。

### 例外 10: トップペア以上 × wet × turn × vs CR → fold に override

- 公式 pred: `call` (Score ≈ 31 + 8 = 39) / GTO best: **`fold`** (GTO FOLD 62.3%、 CALL 37.0%)
- サンプル: n = 215、 平均 loss = 2.40 BB avg
- 理由: Turn vs CR で wet board × TP+ は villain range (straight/flush 完成 or set) に劣位です。
- **適用条件**: カテゴリ = トップペア以上、 board = wet、 street = turn、 pot = vs CR のみ。 ⚠️ vs Donk 不可 (Donk turn × TP+×wet は GTO CALL 87%)。

## 9.7 例外 ex11 (River Donk 専用 1 ルール)

### 例外 11: 2P+ (trips/FH/quads) × paired × river × vs Donk → raise (value)

- 公式 pred: `call` (Score = 28 + 8 = 36 or nearby) / GTO best: **`raise`** (GTO RAISE 100%)
- サンプル: n = 66、 平均 loss = 2.51 BB avg
- 理由: River vs Donk で paired board × trips 以上は villain の donk range が弱く value raise が正解です。
- **適用条件**: カテゴリ = 2P+ (trips/FH/quads)、 board = paired、 street = river、 pot = vs Donk のみ。

## 9.8 例外ルールの適用順序

1. vs CR / vs Donk のとき: **T_raise = 49** を使います (DEF 閾値補正)
2. 公式で Score を計算 → call / raise / fold の暫定アクション
3. カテゴリ / board / street / pot を例外 11 ルール表と照合
4. 該当があり、 公式 pred = 表の pred と一致 → 表の best にオーバーライド
5. 該当なし → 公式 pred を採用

ex6-8 は「公式 pred に関わらず」 強制 override する点にご注意ください。

## 9.9 例外 11 ルール採用効果と精度

7 context × 208,888 hands での総合精度をご紹介します:

| context | n | 正解率 | avg loss BB | 総合精度 |
|---|---:|---:|---:|---:|
| SRP flop | 39,736 | 79.3% | 0.007 | **94.6** ★S |
| 3BP flop | 47,040 | 84.9% | 0.019 | **94.8** ★S |
| 4BP flop | 47,040 | 65.7% | 0.120 | **84.0** ★S |
| TURN | 21,227 | 64.9% | 0.013 | **90.6** ★S |
| RIVER | 19,753 | 70.1% | 0.042 | **88.2** ★S |
| vs CR | 15,576 | 76.0% | 0.200 | **80.5** ★S |
| vs Donk | 18,516 | 68.7% | 0.141 | **82.7** ★S |
| **統合** | **208,888** | **74%** | **0.065** | **89.1 ★S** |

全 7 context が Grade S (≥ 80) 達成しました。

## 9.10 例外を覚える key word

- **DEF (vs CR/Donk)**: T_raise = **49** (通常 43 から引き上げ、 例外ではなく閾値補正)
  - ミドル×paired: Score=48 → T=49 で call。 TP+×dry: Score=46 → T=49 で call
- **wet × ?** → ex1〜ex5 候補 (wet board に集中)
- **monotone** → ex7/ex8 (check / 抑制)
- **paired_low** → ex6 (確実 bet)
- **turn × vs CR + call** → ex9/ex10 (fold に変換、 ⚠️ Donk 不可)
- **river × vs Donk + paired × strong** → ex11 (value raise)

## 9.8 outlier rule v3 (5 context 別の役ベース判別、 2026-06-11 追加)

例外 11 ルールに加えて、 174K hands 検証で **5 context 別の outlier 判別ルール** が data 駆動で確定しました。 これらは「公式判定が大きく外れる役 × board pattern」 を見つけて警告するルールです。

| context | Best Rule | F1 | precision | avg loss/hit |
|---|---|---:|---:|---:|
| **SRP** | set OR trips OR (overpair × dry) | 30.8% | 26.6% | 0.064 BB |
| **3BP** ★ | **TP+ カテゴリ 全 mv** (= top_pair 以上 or set/trips) | **45.2%** | 44.0% | 0.20 BB |
| **4BP** ★ | paired × (TP+/ミドル) OR エア × paired | 26.4% | 29.3% | 0.21 BB |
| **TURN** | TP+ × non-paired OR ミドル × paired OR overpair | 33.0% | 17.7% | 0.28 BB |
| **RIVER** | 役確定なので split rule (made/no_made → bet) で代替 | — | — | acc +25pp |

### 暗算フロー (5 context 統合)

```
Step 1: context 判別 (SRP/3BP/4BP/TURN/RIVER)
Step 2: context 別判定
  ├─ SRP/3BP → Score 公式 (Grid + DV + 補正)
  ├─ 4BP    → 4 cells lookup (第 17 章)
  ├─ TURN   → 3 cells lookup + overpair + bluff (第 18 章)
  └─ RIVER  → split rule (第 19 章)
Step 3: 役 × board で outlier rule 確認 (上記表)
```

### outlier rule の data 駆動裏付け

各 context の outlier (loss > 0.05 BB) の主要因 役単独 bet 率をご参考ください:

- **SRP** (outlier 2.6%): trips 34% / set 23% / overpair (dry) 22%
- **3BP** (outlier 13.5%): overpair 69% / straight 53% / trips 45% / top_pair 38%
- **4BP** (outlier 33.5%): top_pair 73% / second_pair 68% / 2P 47% / set 41%
- **TURN** (outlier ~18%): set 66% / FH 59% / overpair 37% / 2P 30%
- **RIVER** (outlier ~50%): set 100% / FH 98% / trips 97% / 2P 94% / straight 92%

各 context の outlier rule はこれらの高 bet 率の役を捕捉するよう data 駆動で設計されました。

## Cash/MTT note

例外 11 ルールは Cash と MTT で共通適用されます。 すべて wet 集中、 ante/rake の影響はほぼなし (huge spots は board structure 駆動)。 short stack MTT では例外 1, 3 を無効化 (committed) — 第 24 章。

## この章で覚える項目 (5 + 5 items)

1. 例外 1: wet × TP+ × flop × SRP → fold
2. 例外 2: wet × 2P+ × river × SRP → raise
3. 例外 3: wet × ミドル × turn × vs CR → fold
4. 例外 4: wet × エア × turn × 3BP → call (bluff catch)
5. 例外 5: wet × 2P+ × flop × SRP → fold

**outlier rule (オプション、 暗算負荷増)**:
6. SRP outlier: set/trips OR overpair × dry
7. 3BP outlier: TP+ カテゴリ 全 mv (覚えやすい広域 rule)
8. 4BP outlier: paired × TP+/ミドル + エア × paired
9. TURN outlier: TP+ × non-paired + ミドル × paired + overpair
10. RIVER: outlier rule 不要 (split rule で代替)
