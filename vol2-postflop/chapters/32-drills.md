# 第 32 章　ドリル抜粋 (12 問)

## 32.1 本章の位置づけ

本書全体から **代表 12 問** を抜粋しました。 各部 (公式 / 境界 / 4 軸 / pot / 深度 /
ICM・MW) から 2 問ずつ取り上げています。

詳細な 200+ cards のドリルは **poker-drill アプリ** で提供しています:

- <https://poker-drill.vercel.app>
- 基本 (32 例題)
- ヒント大 (60 spots、 軸判定済み + 表参照)
- 応用 (60 spots、 シナリオから軸判定)
- 境界 spot ドリル (50 spots)

本書のドリルは「公式の使い方を体感する」ためのものです。 反復練習はアプリで行うことをおすすめします。

## 32.2 ドリル 12 問

### 問 1 (公式)

**問題**: board: Kh 7c 2d (dry)、 hand: AhTh、 street: flop、 pot: SRP、 bs: med_100p (oc=1)。 Score と判定は?

**計算**: カテゴリ=エア、 Grid[エア][dry]=3、 DV=0、 oc=1 → 2、 pot=0、 bs=2 → −4。 Score = 3 + 0 + 2 + 0 − 4 = **1**

**解答**: **fold** (1 < 14)

### 問 2 (公式)

**問題**: board: Th 9h 4c (wet)、 hand: TsTd (set)、 street: flop、 pot: SRP、 bs: small_33。 Score と判定は?

**計算**: カテゴリ=2P+、 Grid[2P+][wet]=23、 DV=0、 oc=0、 pot=0、 bs=0。 Score = 23

**解答**: **call** (14 ≤ 23 < 43)

### 問 3 (境界)

**問題**: アンダーペア × paired × flop × SRP × small_33 (oc=0、 DV=0)。 Score と判定は?

**計算**: Grid[ミドル][paired]=40、 他項 0。 Score = **40**

**解答**: **call** (14 ≤ 40 < 43)。 paired board の最強 cell です

### 問 4 (例外)

**問題**: hero: AQs on Ts9s8c-2c (turn)、 pot: 3BP、 bs: med_75。 公式と例外で判定が変わるでしょうか?

**計算**: カテゴリ=エア、 Grid[エア][wet]=1、 DV=0 (no draw)、 oc=2 → 4、 pot=2 → 8、 bs=1 → −2。 Score = 1 + 0 + 4 + 8 − 2 = **11** → fold

**解答**: **call** (例外 4: エア × wet × turn × 3BP → call で override します)

### 問 5 (4 軸)

**問題**: SPR=1.3 (4BP)、 hand: 77 on K-7-2 (set)、 board=dry。 実 GTO bet 頻度は?

**計算**: 第 12 章および第 13 章: SPR=1.3 で set の bet 頻度 = **4%** (slowplay)。

**解答**: **slowplay (check)**。 Score 公式上は Grid 25 + 16 = 41 で call も整合しています

### 問 6 (4 軸)

**問題**: hero: J9 on K-Q-T (paired board ではなく wet) で gutshot を持っています。 DV と Score は?

**計算**: K-Q-T は span 3 (K=13, T=10、 13−10=3) ≤ 4 → wet。 hand J9 (no pair) + gutshot (J9 → JT9 完成可)。 カテゴリ=エア、 DV=1 (gutshot)。 Grid[エア][wet]=1、 + DV×3=3、 + oc 0、 pot 0、 bs (vs small_33) 0。 Score = 1 + 3 = **4**

**解答**: **fold** (4 < 14)。 gutshot だけでは eq が不足しています

### 問 7 (pot)

**問題**: 4BP × dry × flop × hero K9s on K-7-2 (TPGK)、 bs: med_100p (oc=0)。 Score と判定は?

**計算**: カテゴリ=TP+、 Grid[TP+][dry]=38、 + 4×4=16、 − 2×2=−4。 Score = 38 + 16 − 4 = **50**

**解答**: **raise** (50 ≥ 43)

### 問 8 (pot)

**問題**: vs CR × wet × turn × hero 99 on Q-J-T-2 (ミドル)、 bs: med_75 (oc=0)。 Score と判定は?

**計算**: カテゴリ=ミドル、 Grid[ミドル][wet]=10、 + 4×2=8、 − 2×1=−2。 Score = 10 + 8 − 2 = **16** → call

**解答**: **fold** (例外 3: ミドル × wet × turn × vs CR → fold で override します)

### 問 9 (深度)

**問題**: short stack (20bb effective)、 hero 55 on K-7-2 × turn × vs CR、 bs: med_75。 committed range として判定は?

**計算**: Score: Grid[ミドル][dry]=18、 + 4×2=8、 − 2=6、 Score = 18 + 0 + 0 + 8 − 2 = **24** → call。 short stack 補正 T_call=12 で更に call 寄りになります

**解答**: **call** (committed range)

### 問 10 (深度)

**問題**: deep stack (200bb)、 hero KQs on A-K-T (turn 2P 完成 board) × SRP × overbet。 Score と判定は?

**計算**: hand KQs → AKT で KQ → TP (K) + Q kicker = top_pair です。 カテゴリ=TP+。 board AKT は span 4 (A=14, T=10、 14−10=4) ≤ 4 → wet。 Grid[TP+][wet]=31、 + 0 (DV) + 0 (oc、 A は board)、 + 0 (SRP)、 − 2 × 3 = −6。 Score = 31 − 6 = **25** → call。 deep stack 補正 T_call 16 でも call になります

**解答**: **call** (25 ≥ 14)

### 問 11 (ICM)

**問題**: バブル × short stack (12bb)、 hero AJo BTN open vs SB jam。 chipEV では call でしょうか?

**計算**: chipEV では BTN AJo vs SB short jam は call wide (Score ≥ 14) になります。 バブル補正 T_call 14 → 22 (+8)。 AJo の Score 推定 ≈ 18 で call 閾値ぎりぎりです。

**解答**: **fold** (バブル ICM 補正で T_call 22 を下回ります)

### 問 12 (MW)

**問題**: 3way pot、 hero KQo on K-7-2 (TPGK)、 SRP、 vs 2 villains call。 公式値で raise するか?

**計算**: HU 想定 Score: Grid[TP+][dry]=38、 + 0 + 0 + 0 = 38 → call。 MW 補正 T_call +10 → 24。 38 ≥ 24 → call です。 raise はしません (MW 原則 1)

**解答**: **call** (薄い value、 MW では raise は禁止です)


## 32.3 ドリルの解き方手順

すべての問題で以下の手順を踏むことをおすすめします:

1. **カテゴリ 判定** (エア / ミドル / TP+ / 2P+)
2. **board 判定** (dry / paired / wet)
3. **Grid 値を Lookup** (12 cells のどれか)
4. **加算項を計算** (DV × mult + 2 × oc + 4 × pot)
5. **減算項を引く** (− 2 × bs)
6. **Score と閾値 14 / 43 で比較**
7. **例外 11 ルールチェック** (wet × … パターン)

慣れれば 5-10 秒で判定できるようになります。 反復で身につけていきましょう。

## Cash/MTT note

ドリル 12 問のうち、 ICM (#11)、 MW (#12) は MTT 専用です。 残り 10 問は Cash/MTT 共通シナリオです。 poker-drill アプリでは Cash/MTT 別 deck も用意しています。

## この章で覚える項目 (反復ドリル、 新規 0)

(本章は実戦練習章のため、 新規暗記項目なし)
