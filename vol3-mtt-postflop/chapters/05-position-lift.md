# 第05章 Position lift——SB/BTN/CO/HJ/UTG の補正

pos_lift はポジション別の cbet 頻度補正値です。BTN=0 を基準に、
SB は OOP のため大幅マイナス（-0.10〜-0.34）、CO/HJ/UTG は wide open のため
プラス補正（+0.10〜+0.17）が付きます。3BP と Turn context では pos_lift=0 です。

## 基準は BTN（0）——ポジション別の lift 一覧

Full UCBS-v2 では BTN（ボタン）を pos_lift=0 の基準に設定しています。
他のポジションはすべて BTN との相対値で表現します。

BTN が基準な理由: BTN は IP（インポジション）でのオープナーのうち、
最もレンジが広く（GTO 約 45%）かつ最も頻繁に使うポジションです。
BASE_FREQ 自体が BTN の act に最適化されており、補正なしで使えます。

SB は OOP（アウトオブポジション）であるため、BASE_FREQ から引き算します。
CO/HJ/UTG（本書では「wide ポジション」と総称）はレンジが狭いことで
フロップでのナッツ保有率が BTN より高くなるため、プラス補正が付きます。

### 13 context の pos_lift パラメータ（SB および CO/HJ/UTG）

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

## SB の特殊性——OOP opener はなぜ大幅マイナスか

SB lift がマイナスになる理由は 3 点です。

理由1「OOP 不利」:
SB はフロップ以降を常に BB に先行動する（アウトオブポジション）立場です。
IP の BTN は相手のアクションを見てから bet できますが、
SB は相手が動く前に bet するため、情報コスト分だけ cbet 頻度を下げる必要があります。

理由2「depth 依存の ICM プレッシャー」:
depth が増すほど SB のコール後の SPR が浅くなり、コミットリスクが高まります。
mtt_50bb（SB lift=-0.29）と mtt_200bb（SB lift=-0.34）の差はこの ICM 依存性を示しています。

理由3「GTO 実測の裏付け」:
GTO Wizard データで mtt_50bb での SB cbet 率は BTN 比で約 25〜30pt 低く、
-0.29 の補正がこの実測値に最もよく適合しています。

depth 別 SB lift の変化（Tier 1 SRP）:
mtt_25bb: -0.10（終盤では SPR が浅く OOP 不利が軽減される）
mtt_50bb: -0.29（中盤が最も敏感な ICM 水準）
mtt_100bb: -0.11（序盤は ICM 小さく抑制も小）
mtt_200bb: -0.34（深 SPR で OOP の情報不利が最大）

### SB vs BTN の実戦比較

### 同じ hand/board での SB vs BTN の差（mtt_50bb）

**例**: トップペア (top_pair) on `Ks7d2c` (BTN, context=mtt_50bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -4, β·I(CBS≥7) = +19, offset(default) = +0
→ **frequency = 83%**

**例**: トップペア (top_pair) on `Ks7d2c` (SB, context=mtt_50bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -4, β·I(CBS≥7) = +19, offset(default) = +0
→ **frequency = 54%**

**例**: トップペア (top_pair) on `Ks7d2c` (BTN, context=mtt_200bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -4, β·I(CBS≥7) = +11, offset(default) = +0
→ **frequency = 75%**

**例**: トップペア (top_pair) on `Ks7d2c` (SB, context=mtt_200bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -4, β·I(CBS≥7) = +11, offset(default) = +0
→ **frequency = 41%**

## Wide lift（CO/HJ/UTG）——レンジが広いほど bet が増える理由

CO/HJ/UTG（「wide ポジション」と総称）にプラス補正が付く理由を説明します。

CO/HJ/UTG は BTN より tight range でオープンします（CO≈28%、HJ≈22%、UTG≈15%）。
このため、フロップでナッツを保有する割合が BTN より高くなります。
例えば UTG の KK/QQ/AK の頻度は BTN より相対的に高く、
「ナッツ保有率の高さ」がフロップ cbet の根拠を強め、プラス補正につながります。

名称の「wide」は「BTN より広いレンジを持つ」という意味ではなく、
「BTN よりナッツ保有が wide（广 = 多い）」という意味で使っています。

mtt_100bb での wide lift = +0.17 が最大:
序盤（SBR≥100）では tight range ゆえのナッツ保有優位が最も鮮明に出ます。

mtt_50bb での wide lift = 0.00:
中盤は ICM 圧力によりポジション均等化が起きます。
CO/HJ/UTG の tight range 優位が ICM コストによって相殺され、
結果として BTN と同じ頻度に収束します。

## MTT depth 別の pos_lift 変動

depth によって pos_lift がどう変わるかをまとめます。

SB lift の傾向（深さの順ではなく ICM 感応度の順）:
mtt_50bb（-0.29）が最も ICM プレッシャーを受け、SB の抑制が最大です。
mtt_200bb（-0.34）は OOP の情報不利が最大で、SB lift の絶対値も最大です。
mtt_25bb（-0.10）は終盤で SPR が浅く、OOP 不利が相対的に軽減されます。
mtt_100bb（-0.11）は序盤で ICM が小さく、抑制が最小です。

wide lift の傾向:
mtt_100bb（+0.17）: 序盤の tight range 優位が最大。
mtt_25bb（+0.13）: 終盤でも wide lift あり。
mtt_200bb（+0.01）: 深スタックではほぼ BTN と同じ。
mtt_50bb（0.00）: 中盤は ICM 均等化で wide lift ゼロ。

## 3BP / Turn context は pos_lift=0（位置均一）

3BP（Tier 3）と Turn（Tier 4）では全ポジションで pos_lift=0 です。

3BP での理由:
3bet pot では SPR の影響が pos_lift を圧倒します。
また 3BP は通常 BTN vs CO や CO vs SB など特定のポジション対決が多く、
ポジション均一が最適化結果として導き出されました。
「3BP に入ったらポジションは関係ない」と覚えてください。

Turn での理由:
ターン 2nd barrel 時点では、フロップのアクション履歴が意思決定を支配します。
「フロップで bet/check したか」「ターンカードが何か」が主因となり、
オープンポジションの影響は軽微になります。
Turn context では β≈0 と合わせて、「全体 35pt down」でシンプルに計算できます。

## 3 つの position での比較——同 context で異なる position

### 同じ board/context × 異なる position（3 ケース）

**例**: セカンドペア (second_pair) on `Ks7d4c` (BTN, context=mtt_25bb)

1. HP = 5, DP = 0, CBS = **5**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +6, β·I(CBS≥7) = +0, offset(default) = +0
→ **frequency = 74%**

**例**: セカンドペア (second_pair) on `Ks7d4c` (SB, context=mtt_25bb)

1. HP = 5, DP = 0, CBS = **5**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +6, β·I(CBS≥7) = +0, offset(default) = +0
→ **frequency = 64%**

**例**: セカンドペア (second_pair) on `Ks7d4c` (CO, context=mtt_25bb)

1. HP = 5, DP = 0, CBS = **5**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +6, β·I(CBS≥7) = +0, offset(default) = +0
→ **frequency = 87%**

## 暗記ショートカット——pos_lift を 3 本柱で覚える

pos_lift の暗記は 3 本柱で整理します。

柱1「BTN は 0」:
全ての計算の出発点。BTN の頻度 = BASE_FREQ + α + β·I + offset。
pos_lift は加算なし（pos_lift=0）です。

柱2「SB は depth × minus（-10〜-34）」:
終盤 25bb: -10pt（軽い抑制）
中盤 50bb: -29pt（最大 ICM 感応）
序盤 100bb: -11pt（ICM 小さく抑制小）
深 200bb: -34pt（OOP 不利最大）
語呂: 「25 で -10、50 で -29、100 で -11、200 で -34」

柱3「wide は 100bb で +17、25bb で +13、50bb は 0」:
序盤 100bb: +17pt（tight range 優位最大）
終盤 25bb: +13pt（push 圏でも wide lift あり）
中盤 50bb: 0pt（ICM 均等化）
深 200bb: +1pt（ほぼなし）
語呂: 「100bb で最大 +17、25bb が +13、50bb と 200bb はほぼ 0」
