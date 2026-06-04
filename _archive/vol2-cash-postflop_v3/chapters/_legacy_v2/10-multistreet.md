# 第10章 Multistreet plan — 3 ストリートを通した計画

フロップ → ターン → リバーを 1 ストリートずつ独立して考えると、一貫性のない行動になりがちです。
本章では「3 ストリートを通した計画」の立て方を習得します。
主要ライン (cbet+barrel / cbet+check / check+probe) を TV × context の組み合わせで分類し、
各ラインで A モデルと D モデル (cash 版) をどう更新するかを整理します。
SPR とベット回数の関係を理解することで、リバーのポットコミット判定まで見通せます。

## マルチストリート設計の考え方

ポーカーの postflop は 3 ストリート (フロップ・ターン・リバー) で構成されています。
各ストリートは独立した選択に見えますが、実際には「前のストリートの判断が後を縛る」という連鎖があります。

**フロップの判断がターン・リバーを縛る理由**:
フロップで cbet を打つことで、相手に「IP は強い」というシグナルを送ります。
相手がコールすれば、ターンで再度 bet するかチェックするかを選ぶ必要があります。
フロップでチェックバックした場合は、ターンでのプローブやドンクベットが相手から来ることもあります。

**SPR と残りベット回数の関係**:
SPR (Stack to Pot Ratio) は「今のポットサイズに対して残りスタックが何倍あるか」を示します。

| SPR | 解釈 | 典型的残りベット回数 |
|---:|---|---:|
| ≥8 | 深い (3 ストリートフル) | 3 回 |
| 4-7 | 中程度 (ターン+リバー) | 2 回 |
| 2-3 | 浅い (リバーが厳しい) | 1-2 回 |
| <2 | コミット圏内 | オールイン検討 |

Cash 100bb の SRP では、フロップ前の SPR は 100bb / (3bb pot) ≈ 33 です。
フロップで 33% cbet を打つと、SPR は 約 16 に半減します。
ターンでさらに 33% 打つと SPR は 約 8 になります。
リバーでさらに 33% 打つと SPR は 約 4 でゲームが終わります。

## ライン 1: cbet → barrel (攻撃継続)

フロップで cbet を打ち、ターンでもバレルを継続するラインです。

**選択条件**:
- フロップ TV バンドが strong / nut (TV 7+)
- または TA+ ターンカードで TV が改善・維持された場合
- turn context の freq が 30%+ (strong/nut バンド)

**A モデルの更新**:
フロップ: cash context → LIGHT_V2_BASE["cash"][band]
ターン: turn context → LIGHT_V2_BASE["turn"][band]

ターンでロールが変わった場合 (例: セカンドペアがトップペアに昇格) は、MV を更新してから turn context を参照します。

**典型的な cbet → barrel ライン**:

フロップ K♠7♦2♣ で top_pair (TV 7, strong, 60% bet):
→ ターン Ac (TA+): MV = top_pair (変化なし)、turn context strong → 30% でバレル継続
→ ターン 3h (TA-): 30% よりさらに控えめ (20% 前後) を判断

**バレル後のリバー計画**:
ターンで bet した場合、リバーの SPR は約 4 前後になります。
strong / nut は「第 3 ブレット」を準備。
mid バンドは「チェックコール」が多い。
air は「ブラフ or フォールド」の二択。

### cbet → barrel ライン例

**例**: トップペア (top_pair) + ドローなし on Cash 100bb

1. HP = **7** (top_pair のバケット)
2. DP = **0** (ドローなし)
3. CBS = HP + DP = 7 + 0 = **7**
4. CBS バンド: 強ペア (TV 7-8)
5. base = LIGHT_V2_BASE[cash][strong] = **60%**
→ **連続 bet 頻度 ≈ 60%**

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

**例**: ツーペア (two_pair) + ドローなし on Turn 2nd barrel

1. HP = **9** (two_pair のバケット)
2. DP = **0** (ドローなし)
3. CBS = HP + DP = 9 + 0 = **9**
4. CBS バンド: ナッツ (TV 9+)
5. base = LIGHT_V2_BASE[turn][nut] = **40%**
→ **連続 bet 頻度 ≈ 40%**

## ライン 2: cbet → check-back (ギアチェンジ)

フロップで cbet を打ったが、ターンでチェックバックするラインです。
このラインは「range protection」と呼ばれ、IP がすべてベットするのを防ぐ役割があります。

**選択条件**:
- turn context の freq が 5-10% (air/weak/mid バンド)
- TA- ターンカードで TV が維持または悪化
- ナッツの一部をチェックバックに回して range をバランスする場合

**A モデルの適用**:
air / weak / mid バンドはターン context で 5-10% → ほぼチェックバックで正解。
strong バンド (30%) の一部もチェックバックに使い、range を守ります。

**チェックバック後のリバー計画**:
ターンでチェックバックした場合、リバーで相手からのベットを受けることが多くなります。
この場合は D モデルの continue freq を参照します。

| MV | リバー D モデル (cash 100bb 参考) | 判断 |
|---:|---:|---|
| 2 (air) | 40% | fold 寄り |
| 3 (weak) | 85% | call 主体 |
| 5 (mid) | 98% | call |
| 7+ (strong+) | 100% | call / CR |

**典型的な cbet → check-back ライン**:
フロップ T♠9♠8♦ で second_pair (TV 5, mid, 40% bet):
→ ターン 2h (TA-, TV 変化なし, turn context mid → 10%) → チェックバック
→ リバー相手ベット → MV=5 (mid) → D モデル 98% continue → call

### check-back 後のターン判断例

**例**: セカンドペア (second_pair) + ドローなし on Turn 2nd barrel

1. HP = **5** (second_pair のバケット)
2. DP = **0** (ドローなし)
3. CBS = HP + DP = 5 + 0 = **5**
4. CBS バンド: 中ペア (TV 5-6)
5. base = LIGHT_V2_BASE[turn][mid] = **10%**
→ **連続 bet 頻度 ≈ 10%**

**例**: Aハイ (ace_high) + OESD on Turn 2nd barrel

1. HP = **2** (ace_high のバケット)
2. DP = **2** (OESD)
3. CBS = HP + DP = 2 + 2 = **4**
4. CBS バンド: 弱ペア (TV 3-4)
5. base = LIGHT_V2_BASE[turn][weak] = **5%**
→ **連続 bet 頻度 ≈ 5%**

**例**: アンダーペア (underpair) + ドローなし on Turn 2nd barrel

1. HP = **3** (underpair のバケット)
2. DP = **0** (ドローなし)
3. CBS = HP + DP = 3 + 0 = **3**
4. CBS バンド: 弱ペア (TV 3-4)
5. base = LIGHT_V2_BASE[turn][weak] = **5%**
→ **連続 bet 頻度 ≈ 5%**

## ライン 3: check → probe / donk (OOP 先手)

フロップで IP がチェックバックした後、BB (OOP) がターンで先手 (probe bet) を打つラインです。
または BB がフロップで cbet に対してコールし、ターンでドンクベット (donk) するケースもあります。

**probe の条件 (フロップ check-back 後)**:
- TA- ターンカード (BB のレンジが強化される 2-6 等)
- BB の TV が strong / nut に改善した場合
- BB がフロップの IP チェックバックに対して強いレンジを見せる局面

**donk の条件 (フロップ cbet コール後)**:
- GTO ではほぼ 0% (フロップ cbet 後の BB donk は非推奨)
- 例外: board-pair ターンやストレート完成ターンでは 25-86% donk が GTO (第 9 章の例外)
- 本書 (base のみ) 版では「フロップ cbet 後のドンクは基本なし、例外局面のみ」と覚えます

**probe bet の暗算**:
BB がターンで先手を打つ場合の freq 目安は、cash context の 50-60% 程度 (強いレンジ限定)。
TV が strong (7-8) または nut (9+) の場合にプローブを選択します。
TV が mid 以下の場合はチェックが基本です。

**defense 側 (IP) の対応**:
BB のプローブに対して IP は、D モデル (cash 版) ではなく通常の cash context での判断に近い形で対応します。
MV=7+ は call / raise。MV=5 は call。MV=3 以下は fold が多い。

### probe 受け側 (IP) の defense 例

**例**: トップペア (top_pair) を cash_100bb で defense

1. HP = **7**
2. base = DCBS_BASE[cash_100bb][HP=7] = **100%**
→ **continue freq = 99%** (fold = 1%)

**例**: セカンドペア (second_pair) を cash_100bb で defense

1. HP = **5**
2. base = DCBS_BASE[cash_100bb][HP=5] = **98%**
→ **continue freq = 98%** (fold = 2%)

**例**: Aハイ (ace_high) を cash_100bb で defense

1. HP = **2**
2. base = DCBS_BASE[cash_100bb][HP=2] = **40%**
3. kicker offset (ace_high) = +5pt
→ **continue freq = 45%** (fold = 55%)

## リバーへの接続 — ポットコミット判定

ターン終了後、SPR が 2 以下になった場合はリバーでのポットコミット判定が近づきます。

**ポットコミットの目安**:
SPR < 2 → 「call 全部コミット」方向で考える。
リバーで相手がオールインしてきた場合、strong / nut バンドはほぼ自動コール。
mid バンドでも SPR < 1 ならコールが正解になることが多い。

**リバーの 3 バケット (本書 (base のみ) 版)**:
リバーでは TV の更新 (役が完成したか) を確認した後、3 バケットで判断します。

| リバー役 | 判断 |
|---|---|
| nut (フラッシュ / ストレート / フルハウス以上) | バリューベット (33-75%) |
| strong (トップペア / セット) | ベット or チェックコール |
| mid 以下 | ブラフ or フォールド |

**light ルール**: リバーで「どうしよう」と迷う局面のほとんどは、フロップ or ターンの計画で解決できます。
フロップで cbet して相手がコールした時点で、「ターンに何が来たらバレルするか」を決めておくことが重要です。

## 3 ストリート通し例題

2 つの代表例で、フロップ → ターン → リバーの計画を通して確認します。

**例題 A: K♠7♦2♣ → Th → Ac (ライン 1: cbet → barrel → river bet)**

フロップ K♠7♦2♣:
- 手牌が top_pair (MV=7, DV=0, TV=7, strong)
- cash context → 60% → cbet 推奨

ターン Th (TA+ ブロードウェイカード):
- MV は top_pair のまま (TV=7, strong)
- turn context → 30% → バレル継続

リバー Ac:
- Ac でトップペアが two_pair に昇格する場合: MV=9 (nut)
- リバーバリューベット推奨 (60-75%)

**例題 B: T♠9♠8♦ → 7h → Kd (ライン 2: cbet → check-back → river call)**

フロップ T♠9♠8♦:
- 手牌が second_pair (MV=5, DV=0, TV=5, mid)
- cash context → 40% → チェック / 境界ベット

ターン 7h (ストレート完成カード、TA-、例外処理対象):
- ストレートが完成したターン → freq -10pt
- turn context mid → 10% → -10pt → ほぼ 0% → チェックバック

リバー Kd:
- 手牌は second_pair のまま (MV=5)
- 相手からベットが来たら D モデル cash_100bb MV=5 → 98% continue → call

## まとめ

- フロップの TV バンドとターン context の 2 ステップで 3 ストリートの大枠が決まる。
- cbet → barrel: strong / nut バンドでターン TA+ の場合に継続。
- cbet → check-back: air / weak / mid バンドまたはターン TA- で多用。
- check → probe: TA- ターンで BB の TV が strong / nut に改善した場合のみ。
- SPR < 2 になったらポットコミット判定 → mid 以上はほぼコール。
- リバーで迷う局面は「フロップ計画の再確認」で 9 割解決する。
