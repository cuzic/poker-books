# 第16章 例題集——MTT 各 depth × SBR スイッチ練習

Full UCBS-v2 の計算を実戦スピードで回せるようになるための例題集です。
context 選択 → CBS 計算 → Confidence 判定 → freq 算出の 4 ステップを繰り返し練習します。
SRP 25bb / SRP 50bb / 3BP / Turn cbet の 4 カテゴリから合計 20 問を用意しました。
各問には Full UCBS-v2 の計算過程と GTO の方向比較を示します。

## 問題の使い方——4 ステップ計算フロー

Full UCBS-v2 を実戦で使うには、以下の 4 ステップを素早くこなす練習が必要です。

```
Step 1: Context 選択
        SRP か 3BP か Turn か？ → depth（25/50/100/200bb）で context を決める

Step 2: CBS 計算
        CBS = HP[hand] + DP[draw]
        HP: no_made_hand/ace_high/king_high/low_pair=2, underpair/third_pair=3,
            second_pair=5, top_pair/overpair=7, set/trips=8, two_pair+以上=9
        DP: no_draw/bdfd=0, gutshot=1, oesd/fd=2, combo=3

Step 3: Confidence 判定
        distance = |CBS - 5|
        HIGH: distance≥3 or 型1 or（型7 + distance=0）
        LOW:  型3/型4 or（型7 + distance=1）
        MID:  上記以外 / 型5 固定

Step 4: freq 計算
        base_freq[(conf, dir, 33%)] + α + β·I(CBS≥7) + offset + pos_lift + ax_lift
```

各例題には解答（Full UCBS-v2 計算値）と方向解説を掲載しています。
計算を先に自分で試し、答え合わせをする形で使ってください。

## 問題 1〜5: SRP 25bb（終盤）

SBR ≈ 25 の終盤 SRP（シングルレイズポット）です。
context は `mtt_25bb`（α=+6、β=+31、WRMSE 15.46%）を使います。

**α=+6 で全体的に積極的、β=+31 で強い役の追加 lift 大、slowplay=-28 でセット等は check 傾向**が特徴です。

### 問題 1〜5 解答（mtt_25bb）

**例**: トップペア (top_pair) on `Ks7d2c` (BTN, context=mtt_25bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +6, β·I(CBS≥7) = +31, offset(default) = +0
→ **frequency = 98%**

**例**: オーバーペア (overpair) on `Jd8c3s` (BTN, context=mtt_25bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +6, β·I(CBS≥7) = +31, offset(premium) = +15
→ **frequency = 98%**

**例**: Aハイ (ace_high) on `Qh8d4c` (BTN, context=mtt_25bb)

1. HP = 2, DP = 2, CBS = **4**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **False**
4. size = **33%** (small)
5. base_freq[(HIGH, False, 33)] = **45%**
6. α = +6, β·I(CBS≥7) = +0, offset(default) = +0
→ **frequency = 51%**

**例**: セット (set) on `7s7d2c` (BTN, context=mtt_25bb)

1. HP = 8, DP = 0, CBS = **8**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +6, β·I(CBS≥7) = +31, offset(slowplay) = -28
→ **frequency = 77%**

**例**: ロー・ポケットペア (low_pair) on `Ah5s3c` (BTN, context=mtt_25bb)

1. HP = 2, DP = 0, CBS = **2**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **False**
4. size = **33%** (small)
5. base_freq[(HIGH, False, 33)] = **45%**
6. α = +6, β·I(CBS≥7) = +0, offset(trash) = -23
→ **frequency = 58%**

**問題 1〜5 のポイント解説**:

- **問1（top_pair on Ks7d2c）**: 型1（A-high ではなく K-high ドライ）。distance=|7-5|=2 → MID。bet 方向（CBS=7≥5）。α+6、β+31（CBS≥7）。高い頻度になります。
- **問2（overpair on Jd8c3s）**: 型3/4 系の中程度連結ボード。Confidence = LOW。overpair は premium（+15）。
- **問3（ace_high + fd on Qh8d4c）**: CBS = 2+2 = 4。distance=|4-5|=1 → MID。check 方向（CBS<5）。FD があっても ace_high は default。
- **問4（set on 7s7d2c）**: set = HP 8。CBS=8、HIGH confidence。bet 方向だが slowplay=-28 で大幅に check 寄り。
- **問5（low_pair on Ah5s3c）**: A-high dry board（gap = A-5 = 9 ≥ 8）。ax_range_bet=+30 を BTN/CO で適用。low_pair は trash（-23）。両方向の補正が拮抗。

## 問題 6〜10: SRP 50bb（中盤）

SBR ≈ 50 の中盤 SRP です。
context は `mtt_50bb`（α=-4、β=+19、WRMSE 12.96%）を使います。

**全 context 中最高精度（12.96%）、low_pair は -35 で徹底 check、SB lift -29 が最大の特徴**です。

### 問題 6〜10 解答（mtt_50bb）

**例**: セカンドペア (second_pair) on `Kh8d3s` (BTN, context=mtt_50bb)

1. HP = 5, DP = 0, CBS = **5**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -4, β·I(CBS≥7) = +0, offset(default) = +0
→ **frequency = 64%**

**例**: ロー・ポケットペア (low_pair) on `Ah7s2c` (BTN, context=mtt_50bb)

1. HP = 2, DP = 0, CBS = **2**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **False**
4. size = **33%** (small)
5. base_freq[(HIGH, False, 33)] = **45%**
6. α = -4, β·I(CBS≥7) = +0, offset(trash) = -35
→ **frequency = 17%**

**例**: トップペア (top_pair) on `As8d4c` (CO, context=mtt_50bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -4, β·I(CBS≥7) = +19, offset(default) = +0
→ **frequency = 94%**

**例**: アンダーペア (underpair) on `Kd8c5s` (BTN, context=mtt_50bb)

1. HP = 3, DP = 0, CBS = **3**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **False**
4. size = **33%** (small)
5. base_freq[(HIGH, False, 33)] = **45%**
6. α = -4, β·I(CBS≥7) = +0, offset(premium) = +20
→ **frequency = 61%**

**例**: フラッシュ (flush) on `Qh9h3h` (BTN, context=mtt_50bb)

1. HP = 9, DP = 0, CBS = **9**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -4, β·I(CBS≥7) = +19, offset(slowplay) = -12
→ **frequency = 71%**

**問題 6〜10 のポイント解説**:

- **問6（second_pair on Kh8d3s）**: second_pair = HP 5。CBS=5、distance=0。型1（K-high ドライ、高カード差大）。型1 + distance≤2 → HIGH。bet 方向（CBS≥5）。高い頻度になります。
- **問7（low_pair on Ah7s2c）**: low_pair = trash（-35）。mtt_50bb での -35 は全 context 最大のマイナス補正。A-high dry かつ BTN なら ax_range_bet +11 も加わるが、相殺されて check 寄り。
- **問8（top_pair + CO on As8d4c）**: CO の wide lift = 0（mtt_50bb は wide lift なし）。ax_range_bet +11（CO + A-high dry）は加わる。
- **問9（underpair on Kd8c5s）**: underpair = premium（+20）。CBS=3、distance=2 → MID。check 方向（CBS<5）。
- **問10（flush on Qh9h3h）**: flush = slowplay（-12）。モノトーン（mono）ボードだが MTT は mono_conf_down=False。CBS=9、HIGH。slowplay 補正で check 方向に傾く。

## 問題 11〜15: 3BP（SPR 別）

3-bet pot（3BP）の IP cbet です。
SPR によって context が変わります。SPR を先に確認してから選択してください。

| SBR（スタック） | 3BP SPR（目安） | Context |
|---|---|---|
| 20bb | ≈2.5 | mtt_3bp_20bb（α=+2、WRMSE 23.08%） |
| 25bb | ≈2.7 | mtt_3bp_25bb（α=+9、WRMSE 18.65%） |
| 50bb | ≈5.5 | mtt_3bp_50bb（α=+7、WRMSE 8.62%） |
| 100bb | ≈11  | mtt_3bp_100bb（α=+5、WRMSE 13.37%） |

### 問題 11〜15 解答（3BP、SPR 別）

**例**: トップペア (top_pair) on `Ks9d4c` (BTN, context=mtt_3bp_50bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +7, β·I(CBS≥7) = +30, offset(default) = +0
→ **frequency = 98%**

**例**: オーバーペア (overpair) on `Jd8c3s` (BTN, context=mtt_3bp_100bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +5, β·I(CBS≥7) = +30, offset(premium) = +20
→ **frequency = 98%**

**例**: セット (set) on `9s9d4c` (BTN, context=mtt_3bp_25bb)

1. HP = 8, DP = 0, CBS = **8**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +9, β·I(CBS≥7) = +19, offset(slowplay) = -66
→ **frequency = 30%**

**例**: ロー・ポケットペア (low_pair) on `Kh8d7c` (BTN, context=mtt_3bp_50bb)

1. HP = 2, DP = 2, CBS = **4**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **False**
4. size = **33%** (small)
5. base_freq[(HIGH, False, 33)] = **45%**
6. α = +7, β·I(CBS≥7) = +0, offset(trash) = -45
→ **frequency = 7%**

**例**: Aハイ (ace_high) on `Qd7s3c` (BTN, context=mtt_3bp_20bb)

1. HP = 2, DP = 0, CBS = **2**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **False**
4. size = **33%** (small)
5. base_freq[(HIGH, False, 33)] = **45%**
6. α = +2, β·I(CBS≥7) = +0, offset(default) = +0
→ **frequency = 47%**

**問題 11〜15 のポイント解説**:

- **問11（top_pair、3BP 50bb）**: mtt_3bp_50bb は全 context 中最高精度（8.62%）。top_pair = HP 7、CBS=7。HIGH confidence（distance=2、型1系）。beta+30（CBS≥7）加算で高頻度。
- **問12（overpair、3BP 100bb）**: mtt_3bp_100bb の premium = +20。CBS=7。3BP 深スタックでは premium の up が大きい特徴。
- **問13（set、3BP 25bb）**: mtt_3bp_25bb の off_slowplay = -66（最強の slowplay 抑制）。set は slowplay。CBS=8、HIGH confidence だが -66 で大幅 check 寄り。SPR ≈2.7 の浅い 3BP では set を trap する戦略。
- **問14（low_pair + oesd、3BP 50bb）**: CBS = 2+2 = 4。distance=1 → MID。check 方向。off_trash = -45。OESD があってもチェック寄りが続く。
- **問15（ace_high、3BP 20bb）**: mtt_3bp_20bb の off_trash = -3（浅い 3BP では trash もほぼ bet）。ただし WRMSE 23.08% で方向参考のみ。

## 問題 16〜20: Turn cbet（α シフト確認）

フロップでベットした後のターン 2nd barrel です。
context を Turn 版（Tier 4）に切り替えます。

**α シフトルール**: フロップの context から α を -35pt 引いた値が Turn context の α になります。
β は廃止（≒ 0）、off_trash は大幅に軽減（-23 → -0〜-14）が特徴です。

| フロップ context | ターン context | α 変化 |
|---|---|---|
| mtt_25bb（α=+6） | mtt_25bb_turn_btn（α=-41） | -47 |
| mtt_50bb（α=-4） | mtt_50bb_turn_btn（α=-37） | -33 |
| mtt_100bb（α=+15） | mtt_100bb_turn_btn（α=-26） | -41 |
| cash_100bb（α=0） | cash_100bb_turn_btn（α=-37） | -37 |

### 問題 16〜20 解答（Turn cbet）

**例**: トップペア (top_pair) on `Ks7d2c` (BTN, context=mtt_25bb_turn_btn)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -41, β·I(CBS≥7) = +1, offset(default) = +0
→ **frequency = 28%**

**例**: セカンドペア (second_pair) on `Kh8d3s` (BTN, context=mtt_50bb_turn_btn)

1. HP = 5, DP = 1, CBS = **6**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -37, β·I(CBS≥7) = +0, offset(default) = +0
→ **frequency = 31%**

**例**: オーバーペア (overpair) on `Jd8c5h` (BTN, context=mtt_100bb_turn_btn)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -26, β·I(CBS≥7) = +0, offset(premium) = +32
→ **frequency = 74%**

**例**: ロー・ポケットペア (low_pair) on `Ah7s4c` (BTN, context=mtt_25bb_turn_btn)

1. HP = 2, DP = 0, CBS = **2**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **False**
4. size = **33%** (small)
5. base_freq[(HIGH, False, 33)] = **45%**
6. α = -41, β·I(CBS≥7) = +0, offset(trash) = -1
→ **frequency = 3%**

**例**: フラッシュ (flush) on `Qh8h3h` (BTN, context=mtt_50bb_turn_btn)

1. HP = 9, DP = 0, CBS = **9**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -37, β·I(CBS≥7) = +0, offset(slowplay) = -25
→ **frequency = 6%**

**問題 16〜20 のポイント解説**:

- **問16（top_pair、Turn 25bb）**: mtt_25bb_turn_btn は最高精度（7.02%）。α=-41 で全体的に大幅 check 寄り。top_pair = HP 7、CBS=7。β≈0 なので強い役の追加 lift なし。フロップより大幅に頻度が低くなる。
- **問17（second_pair + gutshot、Turn 50bb）**: CBS = 5+1 = 6。distance=1 → MID。bet 方向（CBS≥5）。α=-37 で大きく引かれる。gutshot のドロー価値が direction を bet 方向に保つ。
- **問18（overpair、Turn 100bb）**: mtt_100bb_turn_btn（WRMSE 26.95%）は最低精度のターン context。方向参考のみ。α=-26 はターン中で最小の下落（フロップ 100bb が α=+15 と高いため）。
- **問19（low_pair、Turn 25bb）**: mtt_25bb_turn_btn の off_trash = -1（フロップ -23 から大幅軽減）。ターンでは low_pair も bet 頻度が上がる（相対的に）。ただし α=-41 の影響は残る。
- **問20（flush、Turn 50bb）**: flush = slowplay（-25）。ターンで完成フラッシュを持った場合の trap 戦略。α=-37 も相まってほとんど check になる。ターンでもスロープレイを維持する傾向。

## まとめ：例題集で学んだ 5 つのパターン

本章の例題を通じて確認した重要パターンを 5 点にまとめます。

1. **mtt_25bb は β=+31 が支配的**: 強い役（CBS≥7）への追加 lift が大きく、top_pair/overpair は高頻度 bet になる。slowplay は -28 で check 傾向が逆転。
2. **mtt_50bb の low_pair は実質 check**: off_trash = -35 は全 MTT depth context 最大。low_pair が bet に向かう状況は稀。
3. **3BP SPR は決定的**: 25bb（slowplay=-66）と 50bb（premium=+14）では全く異なる戦略。SPR を先に確認してから context を選ぶ。
4. **ターンは α が全てを制する**: α=-26〜-41 で全体 bet が大幅減。β 廃止で強い役の追加 lift もなし。β への依存から脱却して考える。
5. **WRMSE が高い context は方向のみ**: mtt_100bb_turn（26.95%）や mtt_3bp_20bb（23.08%）は exact 値より「bet か check か」の方向判断に絞る。
