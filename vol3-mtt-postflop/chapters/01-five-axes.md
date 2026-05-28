# 第01章 Full UCBS-v2 の 5 軸——HP・DP・Confidence・Size・Context

Full UCBS-v2 は HP（役の強さ）・DP（ドローの価値）・Confidence（信頼度）・
Size（ベットサイズ）・Context（状況）の 5 軸で cbet 頻度を決定するシステムです。
本章では 5 軸をひとつずつ数値込みで解説し、最後に統一式でまとめます。

## 第1軸: HP——役の強さを 2-9 で表す

HP（Hand Power）はフロップでの「役の強さ」を整数で表したスコアです。
16 種類の hand type を 6 バケット（2/3/5/7/8/9）に集約します。
閾値 T=5 を基準に「HP≥5 なら bet 寄り、HP<5 なら check 寄り」という
大まかな方向が決まります。
second_pair（HP=5）がちょうど閾値に位置するのが覚えやすいポイントです。

### HP テーブル（16 hand → 6 バケット）

| HP | 含まれる役 |
|---:|---|
| 2 | ノーペア, Aハイ, Kハイ, ロー・ポケットペア |
| 3 | アンダーペア, サードペア |
| 5 | セカンドペア |
| 7 | トップペア, オーバーペア |
| 8 | セット, トリップス |
| 9 | ツーペア, フラッシュ, ストレート, フルハウス, クアッズ |

暗記のポイントは 2/3/5/7/8/9 の 6 値です。
T=5 を挟んで「5 以下は check 寄り、5 超は bet 寄り」が基本方向です。
no_made_hand・ace_high・king_high・low_pair はすべて HP=2 と同じバケットです。
set（HP=8）と two_pair 以上（HP=9）の違いは 1 しかありませんが、
後述する slowplay カテゴリ補正で大きく扱いが変わります。

## 第2軸: DP——ドローの期待価値を 0-3 で表す

DP（Draw Power）はドローの「改善可能性」を整数で表したスコアです。
combo_draw（oesd + fd）が最大の DP=3 で、gutshot は DP=1 と控えめです。

特例として「Air Paradox」があります。
no_made_hand（HP=2）に oesd がついた場合、CBS = HP - 2 と補正されます。
通常は CBS = HP + DP = 2 + 2 = 4 となるところを CBS = 0 に調整します。
これはハンドが弱くてもドローが強い矛盾を補正するための例外ルールです。

### DP テーブル（4 段階）

| DP | ドロー種別 |
|---:|---|
| 0 | ドローなし, BDFD |
| 1 | ガットショット |
| 2 | OESD, フラッシュドロー |
| 3 | コンボドロー |

## 第3軸: Confidence——T=5 からの距離でボード読みの信頼度を測る

Confidence（信頼度）は distance = |CBS - T| と board_type（型1-7）から決まる
3 段階（HIGH/MID/LOW）の判定値です。
HIGH なら base_freq が高く（bet 寄り 68%）、LOW なら低い（25%）となります。

基本ルールは「distance ≥ 3 なら常に HIGH」です。
これは CBS が 2（最弱）または 8 以上（最強）のとき distance=3+ となり、
どちらも信頼度が高くなることを意味します。
中間帯（CBS=3〜7）は board_type によって HIGH/MID/LOW が変わります。
詳細な分類ルールは ch02 で解説します。

## 第4軸: Size——33% か 116% か

bet size は 33%（ポットの約 1/3）と 116%（オーバーbet）の 2 択です。
MTT では polarize_enabled=False のため、常に size=33% を使います。
cash_100bb のみ polarize_enabled=True で、特定の条件を満たすボードで 116% が適用されます。

33% と 116% で BASE_FREQ テーブルの参照セルが変わります。
bet 寄りかつ HIGH の場合: 33% で 68%、116% で 89%（+21pt の効果）。
bet 寄りかつ MID の場合: 33% で 40%、116% で 55%（+15pt の効果）。
check 方向ではサイズによる差がほぼないため、overbet の恩恵は「強い手で bet」の場合のみです。
MTT でオーバーbet を使わない理由の詳細は ch03 で解説します。

## 第5軸: Context——13 種類のスイッチング

Context は「どの状況か」を決定するスイッチで、13 種類あります。

Tier 0（cash_100bb）: キャッシュ 100bb の基準 context です。α=0 でほかのすべての context がここからの偏差として解釈できます。

Tier 1（mtt_25/50/100/200bb）: MTT SRP の depth 別 context です。
depth が浅いほど β（強い役の追加 lift）が高く（25bb: +0.31 → 200bb: +0.11）、
depth が深いほど SB lift が大きく負になります（25bb: -0.10 → 200bb: -0.34）。

Tier 3（mtt_3bp_20/25/50/100bb）: 3bet pot IP 専用の 4 context です。
SPR が支配するため、SBR でなく SPR で context を選びます。

Tier 4（turn 4 種）: フロップ cbet 後にターン 2nd barrel を検討するときに使います。
フロップ context の α を約 -35pt シフトし、β を 0 にした variant です。
context の詳細な使い分けは ch04 で解説します。

### Full UCBS-v2 13 context パラメータ一覧

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

## 統一式——5 軸をひとつの式にまとめる

CBS = HP[hand] + DP[draw]

T = 5 は全 context・全ポジション共通の閾値です。

distance = |CBS - T|

conf = Confidence（HIGH/MID/LOW）← ch02 で詳説

direction = (CBS >= T)    # true = bet 寄り

size = polarize_board(board) ? 116 : 33    ← MTT は常に 33

freq = base_freq[(conf, direction, size)]
     + α                                   ← context uniform lift
     + β · I(CBS ≥ 7)                      ← 強い役帯の追加 lift
     + offset[category]                    ← slowplay/trash/premium/default
     + pos_lift[position]                  ← ポジション補正
     + ax_range_lift                       ← A-x range bet（MTT BTN/CO のみ）

freq = clamp(freq, 0.02, 0.98)

この式の各項の意味を以下にまとめます。
base_freq は Confidence × direction × size の 6 セルから引く基礎頻度です。
α は context 全体を均一に上下させる lift で、25bb では +6pt、100bb では +15pt です。
β · I(CBS≥7) は CBS が 7 以上（top_pair 以上）のときだけ追加される lift で、25bb では +31pt です。
offset は役柄カテゴリ別の補正で、slowplay は大きく負（set が mtt_25bb で -28pt）になります。
pos_lift はポジション補正で、SB は OOP のため大きく負（50bb で -29pt）です。
ax_lift は A-high dry/paired の MTT BTN/CO のみ適用される range bet 補正です。

## ハンドカテゴリ——4 区分と offset の役割

### ハンドカテゴリ（4 区分）

| カテゴリ | 含まれる役 |
|---|---|
| slowplay | ツーペア, フラッシュ, ストレート, セット, トリップス, フルハウス, クアッズ |
| trash | ロー・ポケットペア |
| premium | アンダーペア, オーバーペア |
| default | ノーペア, Aハイ, Kハイ, サードペア, セカンドペア, トップペア |

カテゴリの意味を覚えることが大切です。

slowplay（set/trips/two_pair/fullhouse/flush/straight/quads）は
HP が高い（8〜9）にもかかわらず GTO で check が多い役です。
オーバーポットに対してコールされるリスクが低く、
逆に check でブラフを引き出す効率が高いため check が最善になります。
mtt_25bb での off_slowplay = -0.28 は特に強烈で、セットはほぼ check が最善です。

trash（low_pair）は HP=2 の弱いペアで、bet 頻度が大きく下がります。
mtt_50bb での off_trash = -0.35 は全 context 中で最も強い trash 抑制です。

premium（overpair/underpair）はペア系の強い役で、プラス補正が付きます。
default（ace_high/king_high/no_made_hand/third_pair/second_pair/top_pair）は補正なし（offset=0）です。

## 計算例——cash_100bb と mtt_25bb の対比

### フルフロー計算例（5 ケース）

**例**: トップペア (top_pair) on `Ks7d2c` (BTN, context=cash_100bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +0, β·I(CBS≥7) = -2, offset(default) = +0
→ **frequency = 66%**

**例**: トップペア (top_pair) on `Ks7d2c` (BTN, context=mtt_25bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +6, β·I(CBS≥7) = +31, offset(default) = +0
→ **frequency = 98%**

**例**: セット (set) on `Ah7d2c` (BTN, context=mtt_25bb)

1. HP = 8, DP = 0, CBS = **8**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +6, β·I(CBS≥7) = +31, offset(slowplay) = -28
→ **frequency = 98%**

**例**: オーバーペア (overpair) on `9c7d2s` (SB, context=mtt_50bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = -4, β·I(CBS≥7) = +19, offset(premium) = +20
→ **frequency = 74%**

**例**: ロー・ポケットペア (low_pair) on `Ks7h2h` (CO, context=mtt_100bb)

1. HP = 2, DP = 2, CBS = **4**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **False**
4. size = **33%** (small)
5. base_freq[(HIGH, False, 33)] = **45%**
6. α = +15, β·I(CBS≥7) = +0, offset(trash) = -19
→ **frequency = 58%**

## 暗算ステップ（実戦 10〜12 秒）

実戦での計算手順を整理します。

① context を選ぶ（SRP か 3BP か Turn か、depth は何 bb か）
② HP = hand type から 6 バケット（HP_TABLE 参照）
③ DP = draw type から 4 段階（DP_TABLE 参照）
④ CBS = HP + DP（Air Paradox 注意）
⑤ direction = CBS ≥ T（T=5）?
⑥ distance = |CBS - T|
⑦ conf = HIGH/MID/LOW（ch02 の分類表で判定）← 型6/mono 例外に注意
⑧ size = 33%（MTT は固定）
⑨ base = BASE_FREQ テーブルの対応セルを参照
⑩ freq = base + α + β·I(CBS≥7) + offset + pos_lift + ax_lift
⑪ clamp(freq, 0.02, 0.98)

慣れれば 10〜12 秒で計算できます。
最初は ch02 の Confidence 判定フローを手元に置きながら練習してください。
