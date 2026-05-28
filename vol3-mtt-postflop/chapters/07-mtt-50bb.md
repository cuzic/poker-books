# 第07章 MTT 50bb 中盤 cbet——バブル前の主戦場

MTT 中盤の 50bb（SBR 約 40-60）はバブルまでの主戦場です。
mtt_50bb は WRMSE 12.96% で MTT depth 系列中の最高精度 context です。
α=-4、β=+19 という保守的な設定と SB lift -29pt の強烈な OOP 抑制が特徴的です。

## mtt_50bb context の全パラメータ

mtt_50bb はゲームの中心となるスタック帯です。
プレイヤーはまだ「pressure をかけられる深さ」を保ちながら、ICM（独立チップモデル）への意識が高まる局面です。

| パラメータ | 値 | 意味 |
|---|---:|---|
| α（全体 lift） | **-4pt** | 全体的にやや控えめ |
| β（CBS≥7 追加 lift） | **+19pt** | 強い役に中程度の追加 |
| off_slowplay | **-12pt** | スローplayは穏やかに抑制 |
| off_trash（low_pair） | **-35pt** | low_pair は実質チェック方向 |
| off_premium（overpair/underpair） | **+20pt** | ペア系強化役は積極的 |
| SB lift | **-29pt** | SB からのベットは大幅に控えめ |
| wide lift（CO/HJ/UTG） | **0pt** | ポジション均等化（BTN との差なし） |
| A-x range bet | **+11pt** | Aハイドライ/ペアボードで小幅 up |

WRMSE は **12.96%** で、MTT depth 系列中の**最高精度**です。
また全 UCBS-v2 context の中でも「10-15%帯（良）」の上位に位置します。

## SB lift -29pt の衝撃——なぜここまで控えめか

mtt_50bb の SB lift = **-29pt** は depth 系列の中で最も大きな負値の一つです（200bb の -34pt に次ぐ）。

BTN（0pt）と SB（-29pt）では **29pt** の大きな差があります。
つまり同じ top_pair でも、BTN から cbet するのと SB から cbet するのでは約 29pt の頻度差が生じます。

この大きな差には 2 つの理由があります。

**理由 1: OOP の構造的不利**
SB は全ポジションの中で最も OOP でポストフロップを戦うポジションです。
ターン・リバーに向けて情報的不利が積み重なるため、GTO はベット頻度を絞ります。

**理由 2: ICM プレッシャーの増大**
50bb スタックはバブル前後に多い深さです。
ICM プレッシャーが最大化する局面でSB がリスクを取りにくくなります。
フォールドした方がサバイバル価値が守られるケースが増えます。

**実戦への示唆**:
SB から 50bb でフロップを迎えた場合、チェックバックを積極的に活用してください。
ポット勝利が見込めるケースでも、BTN なら bet する手でも SB ではチェックが GTO 推奨になるケースが多いです。

## Trash -35pt——low_pair の実質チェック化

mtt_50bb の off_trash = **-35pt** は MTT depth 系列で最大の負値です（25bb: -23pt、100bb: -19pt）。

low_pair（HP=2）の base から -35pt が引かれると、多くのケースで freq が 20% を下回ります。
これは「LOW confidence + check 方向」の base_freq が 25% であることを考えると、ほぼ fold/check が正解になることを意味します。

**なぜ 50bb で trash が最も抑制されるのか**

50bb は「サイズが中程度」のゾーンです。
- 浅いスタック（25bb）では bet/fold という2択が成立し、low_pair も一部 bet できます。
- 深いスタック（100bb/200bb）では MDF の関係で low_pair も call されにくくなります。
- **50bb はその中間**：bet すると相手が頻繁に call してくる深さがあり、low_pair では非常に bad continuation bet になります。

このため mtt_50bb では low_pair を bet するくらいなら「フォールドアウト」が GTO 的に正解です。

## Wide lift 0pt——ポジション均等化の理由

mtt_50bb の wide lift（CO/HJ/UTG）= **0pt** は、BTN との差がゼロであることを意味します。

これは mtt_25bb（+13pt）や mtt_100bb（+17pt）と比較して特異的な設定です。

50bb ではポジション別のレンジ幅の違いが「ベット頻度の差」としてあまり現れません。
理由としては、50bb ではすべてのポジションが similar な continuation bet 頻度を採用する GTO が観察されているためです。

一方で SB の -29pt は依然として大きい点に注意してください。
「SB vs non-SB」の差は大きく、「BTN vs CO vs HJ vs UTG」の差は小さい、というのが 50bb の構造です。

## WRMSE 12.96%——最高精度の意味

mtt_50bb は MTT depth 系列（25/50/100/200bb）の中で **最高精度 WRMSE 12.96%** を達成しています。

この高精度の理由は以下です。

1. **50bb のゲームツリーが比較的シンプル**: MTT6mSimple tree は 50bb 近辺で GTO 行動が安定しやすい
2. **extreme な outlier が少ない**: 100bb の wide cbet 異常値のような特異動作が 50bb では少ない
3. **ドロー補正が効く深さ**: DP の影響が適切に現れる SPR 帯（≈8-9）

実戦での活用として、**mtt_50bb での判断は計算結果をそのまま信頼** できます。
±10pt 程度の誤差しか期待されないため、境界値（40-60%）付近でも比較的信頼できます。

## 実戦例題 7 問

mtt_50bb context の計算例です。
各ケースで alpha、beta、offset、pos_lift がどのように合算されるかを確認してください。

### BTN からの標準 cbet

**例**: トップペア (top_pair) on `Ks7d2c` (BTN, context=mtt_50bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -4, β·I(CBS≥7) = +19, offset(default) = +0
→ **frequency = 83%**

**例**: オーバーペア (overpair) on `Jd8c3s` (BTN, context=mtt_50bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -4, β·I(CBS≥7) = +19, offset(premium) = +20
→ **frequency = 98%**

**例**: ロー・ポケットペア (low_pair) on `Ah7s3c` (BTN, context=mtt_50bb)

1. HP = 2, DP = 0, CBS = **2**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **False**
4. size = **33%** (small)
5. base_freq[(HIGH, False, 33)] = **45%**
6. α = -4, β·I(CBS≥7) = +0, offset(trash) = -35
→ **frequency = 17%**

**例**: セット (set) on `Ks7d7c` (BTN, context=mtt_50bb)

1. HP = 8, DP = 0, CBS = **8**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -4, β·I(CBS≥7) = +19, offset(slowplay) = -12
→ **frequency = 71%**

**例**: Aハイ (ace_high) on `Jd8c3d` (BTN, context=mtt_50bb)

1. HP = 2, DP = 2, CBS = **4**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **False**
4. size = **33%** (small)
5. base_freq[(HIGH, False, 33)] = **45%**
6. α = -4, β·I(CBS≥7) = +0, offset(default) = +0
→ **frequency = 41%**

**例**: セカンドペア (second_pair) on `Kh8d5c` (CO, context=mtt_50bb)

1. HP = 5, DP = 1, CBS = **6**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -4, β·I(CBS≥7) = +0, offset(default) = +0
→ **frequency = 64%**

**例**: トップペア (top_pair) on `As4c2d` (BTN, context=mtt_50bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -4, β·I(CBS≥7) = +19, offset(default) = +0
→ **frequency = 94%**

## SB ポジションでの差

### SB（-29pt）の影響を確認

**例**: オーバーペア (overpair) on `Jd8c3s` (SB, context=mtt_50bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -4, β·I(CBS≥7) = +19, offset(premium) = +20
→ **frequency = 74%**

**例**: トップペア (top_pair) on `Ks7d2c` (SB, context=mtt_50bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -4, β·I(CBS≥7) = +19, offset(default) = +0
→ **frequency = 54%**

## まとめ：mtt_50bb の 5 原則

mtt_50bb context を実戦で使うための 5 原則をまとめます。

1. **最高精度（WRMSE 12.96%）を信頼**: MTT depth 系列では最も信頼できる。計算結果を素直に採用してよい。
2. **SB では大幅にベットを絞る**: -29pt の補正はすべてのハンドに適用。BTN なら bet する手でも SB ではチェックが正解のことが多い。
3. **low_pair はほぼチェック**: -35pt で低頻度。よほど fold しやすいボード以外では bet 禁止。
4. **トップペア/オーバーペアは積極的 bet**: β=+19pt + off_premium=+20pt で BTN から高頻度 bet。
5. **wide lift=0pt でポジション均等**: CO/HJ/UTG からでも BTN と同じ頻度が基本（SBのみ大幅 down）。
