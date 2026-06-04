# 第11章 例題集 — cash 100bb 代表 20 スポット

本章は cash 100bb の代表的な 20 スポットで A モデルと D モデル (cash 版) の暗算フローを練習します。
Vol2 scope (IP cbet) 10 問・全 layer 参考 5 問・D モデル (OOP defense) 5 問の 3 部構成です。
各問に「TV 計算 → context → freq → 判断」の解答例を記載します。
全問を通すことで、本書の 3 つのフレームワークを cash context で横断的に確認できます。

## 例題の構成と解き方

本章の例題は 20 スポット、3 部構成です。

**部 1: A モデル — IP cbet 10 問**
Cash 100bb の SRP で IP が cbet するかどうかを判断します。
TV = MV + DV → TV バンド → LIGHT_V2_BASE["cash"][band] → freq → 判断の流れです。

**部 2: 旧 5 軸モデル 参考 — IP cbet 5 問**
旧 5 軸モデル (board テクスチャ・confidence・size 等) を使った詳細計算の例です。
A モデル との差分 (α, β項, offset) がどのように働くかを確認します。

**部 3: D モデル (cash 版) — OOP defense 5 問**
BB として IP の cbet を受けたとき、continue か fold かを MV 別 continue freq で判断します。

**解答フォーマット**:
各問に「手牌 / ボード / ポジション / context」を明示し、計算ステップを段階的に示します。
最後に「GTO 比較」として精度の参考値を示します。

## 部 1: A モデル — IP cbet 10 問

### A モデル 計算例 (IP cbet, cash context)

**例**: トップペア (top_pair) + ドローなし on Cash 100bb

1. HP = **7** (top_pair のバケット)
2. DP = **0** (ドローなし)
3. CBS = HP + DP = 7 + 0 = **7**
4. CBS バンド: 強ペア (TV 7-8)
5. base = LIGHT_V2_BASE[cash][strong] = **60%**
→ **連続 bet 頻度 ≈ 60%**

**例**: オーバーペア (overpair) + ドローなし on Cash 100bb

1. HP = **7** (overpair のバケット)
2. DP = **0** (ドローなし)
3. CBS = HP + DP = 7 + 0 = **7**
4. CBS バンド: 強ペア (TV 7-8)
5. base = LIGHT_V2_BASE[cash][strong] = **60%**
→ **連続 bet 頻度 ≈ 60%**

**例**: セット (set) + ドローなし on Cash 100bb

1. HP = **8** (set のバケット)
2. DP = **0** (ドローなし)
3. CBS = HP + DP = 8 + 0 = **8**
4. CBS バンド: 強ペア (TV 7-8)
5. base = LIGHT_V2_BASE[cash][strong] = **60%**
→ **連続 bet 頻度 ≈ 60%**

**例**: ツーペア (two_pair) + ドローなし on Cash 100bb

1. HP = **9** (two_pair のバケット)
2. DP = **0** (ドローなし)
3. CBS = HP + DP = 9 + 0 = **9**
4. CBS バンド: ナッツ (TV 9+)
5. base = LIGHT_V2_BASE[cash][nut] = **60%**
→ **連続 bet 頻度 ≈ 60%**

**例**: フラッシュ (flush) + ドローなし on Cash 100bb

1. HP = **9** (flush のバケット)
2. DP = **0** (ドローなし)
3. CBS = HP + DP = 9 + 0 = **9**
4. CBS バンド: ナッツ (TV 9+)
5. base = LIGHT_V2_BASE[cash][nut] = **60%**
→ **連続 bet 頻度 ≈ 60%**

**例**: セカンドペア (second_pair) + フラッシュドロー on Cash 100bb

1. HP = **5** (second_pair のバケット)
2. DP = **2** (フラッシュドロー)
3. CBS = HP + DP = 5 + 2 = **7**
4. CBS バンド: 強ペア (TV 7-8)
5. base = LIGHT_V2_BASE[cash][strong] = **60%**
→ **連続 bet 頻度 ≈ 60%**

**例**: アンダーペア (underpair) + ガットショット on Cash 100bb

1. HP = **3** (underpair のバケット)
2. DP = **1** (ガットショット)
3. CBS = HP + DP = 3 + 1 = **4**
4. CBS バンド: 弱ペア (TV 3-4)
5. base = LIGHT_V2_BASE[cash][weak] = **40%**
→ **連続 bet 頻度 ≈ 40%**

**例**: Aハイ (ace_high) + OESD on Cash 100bb

1. HP = **2** (ace_high のバケット)
2. DP = **2** (OESD)
3. CBS = HP + DP = 2 + 2 = **4**
4. CBS バンド: 弱ペア (TV 3-4)
5. base = LIGHT_V2_BASE[cash][weak] = **40%**
→ **連続 bet 頻度 ≈ 40%**

**例**: ロー・ポケットペア (low_pair) + ドローなし on Cash 100bb

1. HP = **2** (low_pair のバケット)
2. DP = **0** (ドローなし)
3. CBS = HP + DP = 2 + 0 = **2**
4. CBS バンド: エアー (TV 0-2)
5. base = LIGHT_V2_BASE[cash][air] = **45%**
6. low_pair の例外 offset: -10pt
→ **連続 bet 頻度 ≈ 35%**

**例**: ノーペア (no_made_hand) + コンボドロー on Cash 100bb

1. HP = **2** (no_made_hand のバケット)
2. DP = **3** (コンボドロー)
3. CBS = HP + DP = 2 + 3 = **5**
4. CBS バンド: 中ペア (TV 5-6)
5. base = LIGHT_V2_BASE[cash][mid] = **40%**
→ **連続 bet 頻度 ≈ 40%**

## 部 2: 旧 5 軸モデル 参考 — IP cbet 5 問

### 旧 5 軸モデル 計算例 (board × scenario, cash_100bb)

**例**: トップペア (top_pair) on `Ks7d2c` (BTN, context=cash_100bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +0, β·I(CBS≥7) = -2, offset(default) = +0
→ **frequency = 66%**

**例**: オーバーペア (overpair) on `Ks7d2c` (BTN, context=cash_100bb)

1. HP = 7, DP = 0, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +0, β·I(CBS≥7) = -2, offset(premium) = +15
→ **frequency = 81%**

**例**: セカンドペア (second_pair) on `Ts9s8d` (BTN, context=cash_100bb)

1. HP = 5, DP = 2, CBS = **7**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +0, β·I(CBS≥7) = -2, offset(default) = +0
→ **frequency = 66%**

**例**: Aハイ (ace_high) on `Ts9s8d` (BTN, context=cash_100bb)

1. HP = 2, DP = 2, CBS = **4**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **False**
4. size = **33%** (small)
5. base_freq[(HIGH, False, 33)] = **45%**
6. α = +0, β·I(CBS≥7) = +0, offset(default) = +0
→ **frequency = 45%**

**例**: セット (set) on `As7d2c` (BTN, context=cash_100bb)

1. HP = 8, DP = 0, CBS = **8**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **True**
4. size = **33%** (small)
5. base_freq[(HIGH, True, 33)] = **68%**
6. α = +0, β·I(CBS≥7) = -2, offset(slowplay) = +2
→ **frequency = 68%**

## 部 3: D モデル (cash 版) — OOP defense 5 問

### D モデル (cash 版) 守備例 (cash_100bb)

**例**: Aハイ (ace_high) を cash_100bb で defense

1. HP = **2**
2. base = DCBS_BASE[cash_100bb][HP=2] = **40%**
3. kicker offset (ace_high) = +5pt
→ **continue freq = 45%** (fold = 55%)

**例**: アンダーペア (underpair) を cash_100bb で defense

1. HP = **3**
2. base = DCBS_BASE[cash_100bb][HP=3] = **85%**
→ **continue freq = 85%** (fold = 15%)

**例**: セカンドペア (second_pair) を cash_100bb で defense

1. HP = **5**
2. base = DCBS_BASE[cash_100bb][HP=5] = **98%**
→ **continue freq = 98%** (fold = 2%)

**例**: トップペア (top_pair) を cash_100bb で defense

1. HP = **7**
2. base = DCBS_BASE[cash_100bb][HP=7] = **100%**
→ **continue freq = 99%** (fold = 1%)

**例**: ノーペア (no_made_hand) を cash_100bb で defense

1. HP = **2**
2. base = DCBS_BASE[cash_100bb][HP=2] = **40%**
3. kicker offset (no_made_hand) = -3pt
→ **continue freq = 37%** (fold = 63%)

## 各部のポイント解説

**部 1 解説 (A モデル)**:

問 1〜5 (strong/nut バンド): top_pair・overpair・set・two_pair・flush はいずれも TV 7+ で strong または nut バンドに入ります。
cash context の strong (60%) / nut (60%) が適用されます。
GTO との差は ±5-10pt 程度で A モデル WRMSE ~19% の範囲内です。

問 6〜10 (mid/air バンド): second_pair+fd は TV=7 (MV=5+DV=2) で strong バンド (60%) になります。
ドローが強いと TV が上がり、ベット推奨になる典型例です。
underpair+gutshot は TV=4 (MV=3+DV=1) で weak バンド (40%) → チェック寄り。
ace_high+oesd は TV=4 (MV=2+DV=2) で weak バンド (40%) → チェック寄り。
low_pair は MV=2 でエアーバンドに加え -10pt 補正 → 35% → チェック推奨。
no_made_hand+combo_draw は TV=5 (MV=2+DV=3) で mid バンド (40%) → チェック寄り。

**部 2 解説 (旧 5 軸モデル)**:

旧 5 軸モデル では board テクスチャ (polarize判定)・confidence (TV とthreshold の距離)・size (33% or 116%) が加わります。
K72r は型1 ドライ → polarize ボード → size=116%。
T98s は型4 連結 → non-polarize → size=33%。
Vol3 全 layer との差: K72r の top_pair は base のみ 60% vs 全 layer では α 補正で異なる値になります。
Vol3 全 layer は精度 WRMSE 16% (base のみ ~19%) と 2-3pt 精度が高い代わりに計算が複雑です。

**部 3 解説 (D モデル (cash 版))**:

ace_high (MV=2) は 40%+5pt=45% → fold 寄り (境界判断)。
underpair (MV=3) は 85% → call 推奨。
second_pair (MV=5) は 98% → virtually always call。
top_pair (MV=7) は 100% → 必ず continue (call or CR)。
no_made_hand (MV=2) は 40%-3pt=37% → fold 推奨。

3 フレームワーク比較:
A モデル は「打つか打たないか」を 60 秒 5 秒で決める。
A モデル は「何% の頻度で打つか」を厳密に計算する。
D モデルは「守備側の続けるか畳むか」を MV から素早く判断する。

## GTO との精度比較

本章の例題に使った各フレームワークの精度参考を示します。

| フレームワーク | 対象 | WRMSE (参考) | 暗算時間 |
|---|---|---:|---:|
| A モデル | IP cbet freq | ~19% | 5-7 秒 |
| 旧 5 軸モデル | IP cbet freq | 16.43% | 15-30 秒 |
| D モデル (cash 版) | OOP continue freq | ~15% | 3-5 秒 |

**解釈**:
A モデル は A モデル より 2-3pt 誤差が大きいですが、暗算 5 秒以内の代償として許容できます。
D モデルはシンプルな MV テーブル参照のみで精度 15% 前後を達成しています。
境界ハンド (TV=5-6 の mid バンド) では 3 フレームワークとも判断が難しく、GTO に近づけるには A モデル を使います。

**cash 100bb での境界ハンド**:
- second_pair (MV=5): base のみ 40% vs GTO ~35-45% (ボード依存)
- underpair (MV=3): base のみ 40% (weak) vs GTO ~30-50% (ターン計画依存)
- ace_high + draw: base のみは TV 合計で判断、GTO はドロー具体的な equity で判断

**推奨ワークフロー**:
実戦では A モデル (5 秒判断) を使い、学習時は A モデル で精密計算を確認します。
月 1 回程度、GTO Wizard で代表ボード 10 スポットを確認することを推奨します。

## turn context の追加例題 (問 19-20)

### Turn context 例題

**例**: トップペア (top_pair) + ドローなし on Turn 2nd barrel

1. HP = **7** (top_pair のバケット)
2. DP = **0** (ドローなし)
3. CBS = HP + DP = 7 + 0 = **7**
4. CBS バンド: 強ペア (TV 7-8)
5. base = LIGHT_V2_BASE[turn][strong] = **30%**
→ **連続 bet 頻度 ≈ 30%**

**例**: オーバーペア (overpair) + ドローなし on Turn 2nd barrel

1. HP = **7** (overpair のバケット)
2. DP = **0** (ドローなし)
3. CBS = HP + DP = 7 + 0 = **7**
4. CBS バンド: 強ペア (TV 7-8)
5. base = LIGHT_V2_BASE[turn][strong] = **30%**
→ **連続 bet 頻度 ≈ 30%**

**問 19 解説 (top_pair, turn)**:
TV=7 (strong), turn context → 30% → バレル継続を検討。
TA+ ターン (ブロードウェイ) なら 30% でバレル。TA- ターン (ロー) なら 20% 前後に下げてチェックバック寄り。

**問 20 解説 (overpair, turn)**:
TV=7 (strong), turn context → 30%。
overpair は top_pair と同バンドです。ターンでの扱いは同じく 30% 前後が目安。
フロップで cbet してターンでバレルする計画を立てていた場合はそのまま実行します。

## 3bp context の追加例題 (問 16-18)

### 3-bet pot context 例題

**例**: オーバーペア (overpair) + ドローなし on 3-bet pot IP

1. HP = **7** (overpair のバケット)
2. DP = **0** (ドローなし)
3. CBS = HP + DP = 7 + 0 = **7**
4. CBS バンド: 強ペア (TV 7-8)
5. base = LIGHT_V2_BASE[3bp][strong] = **70%**
→ **連続 bet 頻度 ≈ 70%**

**例**: セカンドペア (second_pair) + ドローなし on 3-bet pot IP

1. HP = **5** (second_pair のバケット)
2. DP = **0** (ドローなし)
3. CBS = HP + DP = 5 + 0 = **5**
4. CBS バンド: 中ペア (TV 5-6)
5. base = LIGHT_V2_BASE[3bp][mid] = **60%**
→ **連続 bet 頻度 ≈ 60%**

**例**: Aハイ (ace_high) + ドローなし on 3-bet pot IP

1. HP = **2** (ace_high のバケット)
2. DP = **0** (ドローなし)
3. CBS = HP + DP = 2 + 0 = **2**
4. CBS バンド: エアー (TV 0-2)
5. base = LIGHT_V2_BASE[3bp][air] = **45%**
→ **連続 bet 頻度 ≈ 45%**

**問 16 解説 (overpair, 3bp)**:
TV=7 (strong), 3bp context → 70% → ベット推奨。
3bp の strong バンドは cash (60%) より高い 70% です。コミット圧力を活かしてバリューを積みます。

**問 17 解説 (second_pair, 3bp)**:
TV=5 (mid), 3bp context → 60% → ベット推奨 (境界を超える)。
cash context の mid (40%) より大きく異なる点が 3bp の特徴です。
SPR が低いため、second pair でも積極的にポットを積むのが GTO に近い判断です。

**問 18 解説 (ace_high, 3bp)**:
TV=2 (air), 3bp context → 45% → チェック寄り (境界付近)。
3bp の air は cash と同じ 45% です。ブラフを選ぶ場合はドロー付き (gutshot, fd) を優先します。

## まとめ

- 20 スポット全問を通して A モデル (10 問) / 旧 5 軸モデル (5 問) / D モデル (5 問) を体験した。
- strong / nut バンドはどの context でも bet 推奨になる傾向がある。
- mid バンドが最も判断に幅があり、context と TA+/TA- で大きく変わる。
- 3bp context は cash より mid/strong が高い (コミット圧力の反映)。
- turn context は全バンドで大きく下がる (strong 30%, nut 40% が最大)。
- D モデルは MV=2 (air) の 40% のみが fold 領域、他はほぼ continue。
- 境界ハンドは 旧 5 軸モデル で精密計算するか GTO Wizard で確認する。
