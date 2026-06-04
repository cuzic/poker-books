# 第05章 サイズ判別 — 33% vs Overbet

cbet サイズは「33% バランスベット」と「116% overbet (ポーラーベット)」の 2 択です。
polarize ボードを 5 条件で素早く見抜き、正しいサイズを 3 秒で選択します。
overbet は cash の IP cbet にのみ適用し、OOP や MTT では 33% 統一が原則です。

## 2 サイズの意味

フロップでのベットサイズは原則 2 択です。

**33% バランスベット**はポットの 3 分の 1 を賭けるサイズです。
wide range (TV 3 以上の strong も mid も含む) で打てるため、ブラフのコストも低く抑えられます。
相手の MDF (Minimum Defense Frequency) は 75% なので守りやすく、マルチストリート戦略を維持できます。
迷ったら 33% が最善手です。

**116% overbet (ポーラーベット)**はポット超えを賭けるサイズです。
nuts / air の 2 極化ハンドだけで構成するレンジで打ちます。
相手の MDF は 46% まで下がるため、ブラフ頻度が低くても採算が取れます。
EV 最大化には有効ですが、適用できる局面は限られます。

**使い分けの原則**: polarize ボード → overbet 候補、それ以外 → 33% 固定。

## polarize ボードの 5 条件

polarize ボードとは「ナッツアドバンテージが顕著で、かつドロー枚数が少ない」ボードです。
以下の 5 条件のいずれか 1 つに該当すれば polarize ボードと判定します。

**条件 1: super-connected low (spread≤2 の 3 枚)**
例: T♠9♦8♣、9♠8♦7♣。
ストレート有無の 2 極化が最大になります。
ただし BB のレンジも連結しやすいため overbet の効果は限定的です。

**条件 2: K-broadway-mid (K♠+broadway+中牌)**
例: K♠Q♦7♣、K♠J♦4♣。
KK / KQ のナッツハンドと完全ミスの 2 極化が起きます。

**条件 3: A-mid-wet (A-high + 中程度 connected)**
例: A♠7♦6♣、A♠8♦5♣。
AA / AK vs 完全ミスの 2 極化が顕著です。

**条件 4: Q-mid-wet (Q♠+中牌+connected)**
例: Q♠8♦7♣、Q♠9♦5♣。
QQ / Q ヒットと完全ミスの 2 極化です。

**条件 5: J-T-mid-wet (J や T の middle connected)**
例: J♠T♦3♣、T♠9♦4♣。
broadway フラッシュドロー + ストレートの組み合わせで 2 極化します。

**確認手順**: 型6か? → 型2か? → Aハイミッドウェットか? → Q/J/Tミッドコネクテッドか? → spread≤2 か?
この順に 5 秒以内に確認し、いずれか Yes なら overbet 候補です。

## overbet 例外補正

overbet の base サイズは 116% ポットです。
さらに board texture によって補正を加える場合があります。

**HIGH bet 寄り補正 (+20%)**:
型6 (ペア高) や型2-High の「セット or nuts のみが際立つ」場合に適用します。
実効サイズは 116% × 1.2 ≈ 120-130% 相当で、暗算では **125%** に丸めます。
例: A♠A♦K♣ (型6的なペアボード) ではセット有無の 2 極化が最大になります。

**MID bet 寄り補正 (+15%)**:
型2-A-mid や Q-mid で「ドローが多くバランスが崩れる」場合に適用します。
実効サイズは 116% × 1.15 ≈ 115% で、実質変化はほぼありません。
例: A♠7♦6♣ (connected draw 多め) では通常の 116% が適切です。

**非 polarize ボードには補正なし**: 補正は polarize ボード限定です。

## cash 限定ルール

overbet (116%+) は **cash の IP cbet にのみ** 使用します。

MTT ではスタック depth と ICM 圧力の関係で overbet は避けます。
スタックが短いほどポット超えベットはオールイン圧力になり、判断が複雑化します。

OOP からの overbet (donk / lead) は Vol3 の上級トピックです。
本章の overbet ルールは「IP がフロップ cbet を打つ場面」だけに限定して適用してください。

## TV バンドとサイズ選択の組み合わせ

サイズを決めた後、A モデルの 25 セル表で freq を確認します。
サイズ選択と freq 判断は独立したステップです。

| TV バンド | 推奨サイズ | 備考 |
|---|---|---|
| air (0-2) | 33% | ブラフとして打つならコスト抑制 |
| weak (3-4) | 33% | バランスベット |
| mid (5-6) | 33% | mid は 33% が標準 |
| strong (7-8) | 33% or overbet | polarize ボードなら overbet 候補 |
| nut (9+) | overbet 推奨 | polarize ボードは overbet、非 polarize は 33% |

freq ≥ 50% → 選択したサイズでベット。
freq < 50% → チェック (サイズは関係なし)。

## 暗算 3 秒判定フロー

実戦での判断手順をまとめます。

```
[サイズ判定 3 秒フロー]

Step A: polarize チェック (5 条件)
  → いずれか Yes → overbet 候補
  → 全て No   → 33% 固定

Step B: TV バンド確認
  → strong / nut → overbet を実行 (polarize ボードの場合)
  → mid / weak / air → 33% に戻す

Step C: freq 確認 (25 セル表)
  → freq ≥ 50% → ベット
  → freq < 50% → チェック
```

cash + IP + polarize ボード + strong/nut バンド の 4 条件が揃ったとき overbet が最善です。

## 計算例

### 33% vs Overbet 判断例

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

**例**: Aハイ (ace_high) + フラッシュドロー on Cash 100bb

1. HP = **2** (ace_high のバケット)
2. DP = **2** (フラッシュドロー)
3. CBS = HP + DP = 2 + 2 = **4**
4. CBS バンド: 弱ペア (TV 3-4)
5. base = LIGHT_V2_BASE[cash][weak] = **40%**
→ **連続 bet 頻度 ≈ 40%**

**例**: ツーペア (two_pair) + ドローなし on Cash 100bb

1. HP = **9** (two_pair のバケット)
2. DP = **0** (ドローなし)
3. CBS = HP + DP = 9 + 0 = **9**
4. CBS バンド: ナッツ (TV 9+)
5. base = LIGHT_V2_BASE[cash][nut] = **60%**
→ **連続 bet 頻度 ≈ 60%**

## まとめ

- **原則 33%**。polarize 5 条件を満たせば overbet 候補。
- overbet は **cash + IP cbet 限定**。MTT・OOP には適用しない。
- TV バンド mid (5-6) は 33% 推奨。high bet は strong / nut 限定。
- 型6 は最も overbet が有効 (セット有無の 2 極化が最大)。
- super-connected (T98/987 等) は BB 有利なので overbet の効果は限定的。
- overbet を打つ場合も air ブラフを一定比率混ぜること (GTO 的均衡)。
