# 第10章 3BP IP SPR シリーズ——20/25/50/100bb の差

3-bet pot（3BP）の IP cbet は、SPR の違いが戦略を根本的に変えます。
20/25bb（低 SPR ≈ 2.5-2.7）は linear range の middle bet、
50bb（SPR ≈ 5.5）は polarize への転換点で WRMSE 8.62% の全 context 最高精度、
100bb（SPR ≈ 11）は premium 大幅 up の complete polarize です。
SPR が支配的である理由と 4 SPR の完全な数値を解説します。

## 3BP の SPR——4 深度の対応表

3-bet pot ではフロップ時のポットが大きく、SPR（スタック to ポット比）が急激に低くなります。

| Context | スタック深度 | SPR 目安 | 戦略タイプ |
|---|---:|---:|---|
| mtt_3bp_20bb | 20bb | ≈ 2.5 | Linear range（trash も一部 bet） |
| mtt_3bp_25bb | 25bb | ≈ 2.7 | Linear range（slowplay 最大抑制） |
| mtt_3bp_50bb | 50bb | ≈ 5.5 | Polarize への転換（★ 最高精度） |
| mtt_3bp_100bb | 100bb | ≈ 11 | Complete polarize（premium 全開） |

**SPR 計算の例（BTN 3BP pot）**:
- 100bb スタックで BTN が 2.5bb open → SB が 9bb 3-bet → BTN call
- フロップポット ≈ 18bb（9+9 + アンテ）
- 実効スタック残り ≈ 91bb
- SPR = 91 ÷ 18 ≈ 5.0（実際は about 5.5）

SPR ≈ 2.5（20bb）は「commit 圏（SPR < 3）」に近い領域です。
この低 SPR では「fold/raise」が主な選択肢となり、call の判断が変わります。
SPR ≈ 11（100bb）では十分な後の street があり、完全な polarize 戦略が成立します。

## 全 4 context のパラメータ比較表

### 全 context パラメータ（3BP 系列を含む）

| Context | α | β | slowplay | trash | premium | SB lift | wide lift | A-x lift |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| cash_100bb | +0 | -2 | +2 | -23 | +15 | -8 | +10 | +0 |
| mtt_25bb | +6 | +31 | -28 | -23 | +15 | -10 | +13 | +30 |
| mtt_50bb | -4 | +19 | -12 | -35 | +20 | -29 | +0 | +11 |
| mtt_3bp_20bb | +2 | +14 | -40 | -3 | -4 | +0 | +0 | +0 |
| mtt_3bp_25bb | +9 | +19 | -66 | -44 | -9 | +0 | +0 | +0 |
| mtt_3bp_50bb | +7 | +30 | -40 | -45 | +14 | +0 | +0 | +0 |
| mtt_3bp_100bb | +5 | +30 | -33 | -48 | +20 | +0 | +0 | +0 |
| mtt_25bb_turn_btn | -41 | +1 | -28 | -1 | +8 | +0 | +0 | +0 |
| mtt_50bb_turn_btn | -37 | -0 | -25 | -3 | +10 | +0 | +0 | +0 |
| mtt_100bb_turn_btn | -26 | -0 | -26 | -14 | +32 | +0 | +0 | +0 |
| cash_100bb_turn_btn | -37 | +0 | -27 | -8 | +22 | +0 | +0 | +0 |
| mtt_3bp_ip | +2 | +14 | -40 | -3 | -4 | +0 | +0 | +0 |
| mtt_200bb | -4 | +11 | -15 | -31 | +14 | -34 | +0 | +9 |
| mtt_100bb | +15 | +9 | -17 | -19 | +8 | -11 | +17 | +28 |

## 低 SPR（20/25bb）——linear range の middle bet

低 SPR（≤25bb）での 3BP は「linear range bet」が特徴です。

**mtt_3bp_20bb**（SPR ≈ 2.5）のパラメータ:

| パラメータ | 値 | 意味 |
|---|---:|---|
| α | +2pt | わずかに積極的 |
| β（CBS≥7） | +14pt | 強い役への小幅 lift |
| off_slowplay | -40pt | セット/ストレートは抑制 |
| off_trash（low_pair） | **-3pt** | **ほぼペナルティなし** |
| off_premium | -4pt | ペア系も小幅抑制 |
| WRMSE | 23.08% | 注意（精度低） |

off_trash = **-3pt** は特筆すべき値です。
SRP（通常ポット）では low_pair は -23〜-35pt という大きな抑制を受けますが、
低 SPR の 3BP では **-3pt のみ** ——つまり「trash も一部 bet」が GTO です。

理由: SPR 2.5 では「bet すれば commit に近い」ため、weak hand も含めて広くべットして fold equity を最大化する戦略が有効です。

**mtt_3bp_25bb**（SPR ≈ 2.7）のパラメータ:

| パラメータ | 値 | 意味 |
|---|---:|---|
| α | +9pt | 積極的 |
| β（CBS≥7） | +19pt | 強い役への中程度 lift |
| off_slowplay | **-66pt** | **全 context 中最大の抑制** |
| off_trash（low_pair） | -44pt | 大幅抑制（20bb の -3pt と対照的） |
| off_premium | -9pt | ペア系も抑制 |
| WRMSE | 18.65% | 注意（やや精度低） |

off_slowplay = **-66pt** は全 13 context 中で最大の絶対値です。
SPR 2.7 の 3BP ではセット/ストレート/フラッシュを「全力でチェックして相手を引きつける」戦略が GTO です。

25bb と 20bb で off_trash が -3pt vs -44pt と大きく異なる理由は興味深いです。
20bb は SPR 2.5 でほぼ commit 圏なので「trash も押し込む」戦略が有効ですが、
25bb は SPR 2.7 でわずかに commit 圏外なので「中間手は引き付けてから動く」戦略に切り替わります。

## 50bb（深 SPR）——polarize への転換点

mtt_3bp_50bb（SPR ≈ 5.5）は全 13 context 中で **最高精度 WRMSE 8.62%** を達成しています。

| パラメータ | mtt_3bp_50bb | 意味 |
|---|---:|---|
| α | +7pt | やや積極的 |
| β（CBS≥7） | **+30pt** | 強い役の大幅 lift |
| off_slowplay | -40pt | スローplayは抑制 |
| off_trash（low_pair） | -45pt | trash は大幅抑制 |
| off_premium | **+14pt** | ペア系の積極化 |
| WRMSE | **8.62%** | ★ 全 context 最高精度 |

**50bb が最高精度の理由**:

SPR ≈ 5.5 は「linear vs polarize の転換点」です。
このゾーンでは GTO 戦略が明確に分岐します：
- **強い役（top_pair/overpair）**: β=+30pt で高頻度 bet
- **trash（low_pair）**: -45pt で低頻度 bet（fold/check）
- **slowplay（set/straight）**: -40pt でチェック

この2極化した行動パターンが UCBS-v2 の「CBS ≥ T = bet、CBS < T = check」構造とよくマッチします。
結果として WRMSE が 8.62% という極めて低い誤差を達成しています。

**実戦での使い方**:
50bb 3BP では計算結果をほぼそのまま信頼できます。
特に CBS ≥ 7（top_pair/overpair）の積極 bet と CBS ≤ 5（middle hand/trash）のチェックが鮮明です。

## 100bb（deep polarize）——premium 全開

mtt_3bp_100bb（SPR ≈ 11）は「complete polarize」が完全に確立したコンテキストです。

| パラメータ | mtt_3bp_100bb | 比較（50bb） |
|---|---:|---:|
| α | +5pt | +7pt |
| β（CBS≥7） | **+30pt** | +30pt |
| off_slowplay | **-33pt** | -40pt |
| off_trash（low_pair） | **-48pt** | -45pt |
| off_premium | **+20pt** | +14pt |
| WRMSE | 13.37% | 8.62% |

off_premium = **+20pt** は 3BP 系列の最大値です。
SPR ≈ 11 では overpair/underpair が「3 streets で価値を取りきれる深さ」になるため、
これらのプレミアムペア役に +20pt の大幅 lift が加わります。

off_trash = **-48pt** も最大値です。
SPR が深いほど low_pair の fold equity が下がり（相手が簡単に fold しない）、
bet しても good outcome が得られないため、完全にチェック/fold 方向になります。

**100bb 3BP の直感的理解**:
「air はチェック、trash はチェック、middle hand はチェック、strong pair は bet、slowplay はチェック」
——結局 bet するのは strong pair（top_pair/overpair/underpair）とエアー（ブラフ）だけという完全 polarize です。

## 実戦例題——同じ手を 4 SPR で比較

同じハンドを 4 つの SPR コンテキストで比較することで、SPR の支配的影響を実感してください。
以下の 4 ケースは「top_pair on Ks7d2c」を 4 SPR で比較します。

### top_pair の SPR 別比較（Ks7d2c, BTN）

**例**: トップペア (top_pair) on `Ks7d2c` (BTN, context=mtt_3bp_20bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +2, β·I(CBS≥7) = +14, offset(default) = +0
→ **frequency = 84%**

**例**: トップペア (top_pair) on `Ks7d2c` (BTN, context=mtt_3bp_25bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +9, β·I(CBS≥7) = +19, offset(default) = +0
→ **frequency = 96%**

**例**: トップペア (top_pair) on `Ks7d2c` (BTN, context=mtt_3bp_50bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +7, β·I(CBS≥7) = +30, offset(default) = +0
→ **frequency = 98%**

**例**: トップペア (top_pair) on `Ks7d2c` (BTN, context=mtt_3bp_100bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +5, β·I(CBS≥7) = +30, offset(default) = +0
→ **frequency = 98%**

## slowplay の SPR 別比較

### set の SPR 別比較（Ks7d7c, BTN）

**例**: セット (set) on `Ks7d7c` (BTN, context=mtt_3bp_20bb)

1. HP = 8, DP = 0, CBS = **8**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +2, β·I(CBS≥7) = +14, offset(slowplay) = -40
→ **frequency = 44%**

**例**: セット (set) on `Ks7d7c` (BTN, context=mtt_3bp_25bb)

1. HP = 8, DP = 0, CBS = **8**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +9, β·I(CBS≥7) = +19, offset(slowplay) = -66
→ **frequency = 30%**

**例**: セット (set) on `Ks7d7c` (BTN, context=mtt_3bp_50bb)

1. HP = 8, DP = 0, CBS = **8**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +7, β·I(CBS≥7) = +30, offset(slowplay) = -40
→ **frequency = 65%**

**例**: セット (set) on `Ks7d7c` (BTN, context=mtt_3bp_100bb)

1. HP = 8, DP = 0, CBS = **8**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +5, β·I(CBS≥7) = +30, offset(slowplay) = -33
→ **frequency = 70%**

## 低 SPR ならではの trash bet

### low_pair の SPR 別比較（Ah7s3c, BTN）

**例**: ロー・ポケットペア (low_pair) on `Ah7s3c` (BTN, context=mtt_3bp_20bb)

1. HP = 2, DP = 0, CBS = **2**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **False**
4. size = **33%** (small)
5. base_freq[(HIGH, False, 33)] = **45%**
6. α = +2, β·I(CBS≥7) = +0, offset(trash) = -3
→ **frequency = 44%**

**例**: ロー・ポケットペア (low_pair) on `Ah7s3c` (BTN, context=mtt_3bp_50bb)

1. HP = 2, DP = 0, CBS = **2**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **False**
4. size = **33%** (small)
5. base_freq[(HIGH, False, 33)] = **45%**
6. α = +7, β·I(CBS≥7) = +0, offset(trash) = -45
→ **frequency = 7%**

**例**: ロー・ポケットペア (low_pair) on `Ah7s3c` (BTN, context=mtt_3bp_100bb)

1. HP = 2, DP = 0, CBS = **2**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **False**
4. size = **33%** (small)
5. base_freq[(HIGH, False, 33)] = **45%**
6. α = +5, β·I(CBS≥7) = +0, offset(trash) = -48
→ **frequency = 2%**

## 「SPR が支配的」という結論

3BP IP での cbet 判断において、SPR は最も重要な変数です。

**SPR 別の基本戦略サマリ**:

| SPR | 戦略 | 核心パラメータ |
|---:|---|---|
| ≤ 2.5 (20bb) | Linear range: trash も bet | off_trash = -3pt のみ |
| ≈ 2.7 (25bb) | 転換期: slowplay 最大抑制 | off_slowplay = -66pt（最大） |
| ≈ 5.5 (50bb) | Polarize 転換点: 最高精度 | WRMSE 8.62% |
| ≈ 11 (100bb) | Complete polarize: premium 全開 | off_premium = +20pt |

**判断木（実戦用）**:

```
3BP pot → SPR 確認
  SPR ≤ 3 (≈20bb) → linear: trash も一部 bet / slowplay は check
  SPR ≈ 2.7 (25bb) → slowplay は全力 check (-66pt) / trash は大幅抑制
  SPR ≈ 5.5 (50bb) → top_pair/overpair は積極 bet / それ以外は check
  SPR ≥ 10 (100bb+) → premium 全開 / trash/middle hand は完全 check
```

これが「SPR が支配的」の意味です。
同じ top_pair でも SPR が 2.5 か 11 かで bet 頻度が大きく変わります。
3BP を迎えたら**まず SPR を確認**し、その SPR に対応する context を選択してください。

**WRMSE まとめ**:
- mtt_3bp_20bb: 23.08%（注意）
- mtt_3bp_25bb: 18.65%（やや注意）
- **mtt_3bp_50bb: 8.62%（★ 全 context 最高）**
- mtt_3bp_100bb: 13.37%（良）

3BP での判断は 50bb が最も信頼できます。20bb の 23.08% は方向判断のみに使いましょう。

## まとめ：3BP IP の 5 原則

3BP IP 系列を実戦で使うための 5 原則をまとめます。

1. **まず SPR を確認**: 3BP では SPR が context 選択の第一基準。20/25/50/100bb で context が変わる。
2. **SPR ≤ 3 は linear range**: off_trash = -3pt のみで trash も一部 bet。fold equity 最大化が目的。
3. **SPR ≈ 5.5（50bb）は最高精度**: WRMSE 8.62% で計算を信頼できる。top_pair 以上は bet、それ以下は基本 check。
4. **SPR ≥ 10（100bb）は complete polarize**: premium（overpair/underpair）は +20pt で全開。trash は -48pt で完全 check。
5. **slowplay は 25bb で最強抑制**: off_slowplay = -66pt の 3bp_25bb が全 context 最大。SPR ≈ 2.7 の 3BP ではセット/ストレートを全力チェック。
