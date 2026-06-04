# 第10章 ICM 補正 — バブル付近の判断 (理論方針のみ)

ICM (Independent Chip Model) はトーナメント特有の概念で、バブル付近やファイナルテーブルで判断が大きく変わります。
本書はデータ限界 (現サブスクで ICM 検証不可) のため、理論方針と簡易ルールを提示するのみとします。

## ICM とは何か

**ICM (Independent Chip Model)** は、トーナメントでの「**チップ価値 vs 賞金価値**」の関係を表すモデルです。

キャッシュゲームでは「1 BB = 1 BB の価値」が一定ですが、トーナメントでは:

- **大きな chip stack** は次の bust prevention に使える → **マージナルな価値**
- **小さな chip stack** は失うと bust 確定 → **絶対的な価値**

具体例 (5 人残り、賞金 1-2 位のみ):

- こちらが 1000 chips、相手も 1000 chips の状況で、こちらが 1000 chips を all-in shove
- call すれば 50% で 2000 chips (上位確定)、50% で bust (賞金ゼロ)
- 数学的期待値は「2000 chips × 50% = 1000 chips」だが、**ICM 的には call すべきでない**
- 理由: bust のリスクが大きすぎ、賞金確保のメリットを上回らない

この **「chip EV と $EV の乖離」** が ICM の本質です。

## ICM が公式に与える影響

ICM 圧力が高い局面 (バブル付近、FT 浅め) では、Vol3 の標準公式に **「タイト化」** の補正を加えます。

**大まかな補正方針:**

```
ICM 補正 (バブル付近、FT 浅め):

── all-in or near-all-in を受けたとき ──
Vol3 の通常公式 (bucket-based) の閾値を 1 段階厳しく:

best_hands ∧ eqp > 0.85 → CALL  (通常公式)
          ↓ ICM 補正
best_hands ∧ eqp > 0.92 → CALL  (より tighter)

good_hands → CALL (通常)
          ↓ ICM
good_hands ∧ eqp > 0.65 → CALL、else FOLD

weak_hands ∧ 強ドロー → CALL (通常)
          ↓ ICM
weak_hands ∧ 強ドロー ∧ implied odds 良好 → CALL、else FOLD

── shove (こちらが all-in する側) ──
通常公式の shove range を 1 段階 tighter に
例: 22% shove → 15-18%
```

これは **理論的な方針** であり、具体的な数値は ICM 計算ソフト (ICMIZER, HRC, etc.) で個別に算出する必要があります。

## ICM 圧力の強弱

ICM 圧力は局面によって大きく変わります。

**ICM 圧力の強弱**

| 局面 | ICM 圧力 | 補正の必要度 |
|------|----------|-------------|
| 早期 (大半が in the money 外) | **弱** | 補正不要、Cash 並みに play |
| バブル直前 (賞金ライン直前) | **強** | 大きな補正、特に short stack 同士 |
| バブル直後 (賞金確保後) | 中 | 軽い補正 |
| FT (final table) 浅め | **強** | 賞金階段の上昇大 |
| FT 終盤 (heads-up) | **弱** | チップが直接賞金に変換、Cash 並み |

最も補正が必要なのは **「バブル直前 + 自分 / 相手とも mid stack」** の状況。両者とも bust が痛いため tight な防御が GTO。

## 短スタック vs ビッグスタックの非対称

ICM 圧力は **stack 比** で非対称になります。

**Big stack の挙動:**

- bust リスクが小さい → call は relatively easy
- shove で short stack を脅す → fold equity 多い
- Vol3 の標準公式 + わずかな loosening (looser call、wider shove)

**Short stack の挙動:**

- bust リスクが大 → tight な call が必要
- shove は committed range (top 10-15% pre, top 25-30% in 3bp)
- 標準公式 + 大きな tightening

実戦中は **自分が short か big かを瞬時に判定** し、補正方向を決めます。

## 本書の limitation

本書 (Vol3) は ICM の詳細を扱いません。理由:

- **検証データ不足**: 現サブスクで ICM solutions (GTO Wizard の ICM gametype) にアクセスできない
- **個別性が高い**: ICM 補正は具体的な賞金分布、残りスタック分布、player count などで大きく変動
- **専門ツール推奨**: ICMIZER, Holdem Resources Calculator (HRC), DTO (Detroit Theory Outliner) などで個別計算が現実的

**代替方針:**

Vol3 の標準公式 (SPR-based、bucket-based) を基盤として、ICM 圧力が強い局面では **1 段階 tighter** に補正する、という大まかな原則のみ提示します。

本書を超えて ICM を深く学びたい方は:

- GTO Wizard の ICM trainer
- 「Modern Poker Theory」 (Michael Acevedo) の ICM 章
- ICMIZER の practice mode

などを推奨します。

## 実戦の判断フロー (簡易版)

MTT で ICM 圧力下にある局面の判断フロー:

1. **自分の stack 状況** を確認: 全 player の中で short / mid / big のどれか
2. **ICM 圧力の局面** か確認: バブル付近? FT 浅め?
3. **Vol3 標準公式** で本来のアクションを決める
4. **ICM 補正** を加味: 圧力強なら 1 段階 tighter、弱なら標準のまま
5. **アクション決定**

迷ったら **「standard よりちょっと tighter」** の方向で。ICM 局面で over-call は損失が大きい (bust リスク)、tight すぎる場合は機会損失だが手堅い。

## 次の章へ

ICM 補正の方針を学びました (詳細は専門ツールに委ねます)。次の ch11 では Vol3 全体の **50 問の練習問題** で詳細公式の反射確認をします。
