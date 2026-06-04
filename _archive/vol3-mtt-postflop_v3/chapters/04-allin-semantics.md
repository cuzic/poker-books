# 第08章 「all-in の意味論」 — Cash と MTT で違う本質

Cash 100bb の "all-in" と MTT 50bb の "all-in" は同じ言葉でも意味が違います。
この章では「raise option の有無」が公式に与える本質的差異を解説し、Vol3 全体の理論を一段深い理解に進めます。

## 同じ言葉、違う意味

ポーカー用語で **"all-in"** は「持っているチップを全部ベットする」ですが、実は局面によって意味が変わります。

**Cash 100bb の River:**

- 例: pot 30 BB の状況で 90 BB shove (300% pot のオーバーベット)
- 残スタックがちょうど 90 BB なので all-in
- **でも相手は raise option を持っている**: 相手の残スタックが 100 BB なら、こちらの 90 BB shove に対して相手は 100 BB を call (raise option を実行) できる
- つまり厳密には all-in ではなく「**near-all-in overbet**」

**MTT 50bb の River:**

- 例: pot 14 BB の状況で 35 BB shove (250% pot)
- 残スタックが 35 BB ぴったり、これで commit
- **相手は raise option がない**: 相手も同等の残スタック (35 BB 程度) で、call するか fold するかのみ
- これが **「真の all-in」** (no further action)

この **raise option の有無** が公式に決定的な違いをもたらします。

## raise option の有無が変える戦略

Cash と MTT で all-in 相当の bet を受けたときの戦略的差異:

**Cash near-all-in vs MTT 真all-in 対応**

| こちらの mv | Cash 100bb (raise 可) | MTT 50bb (raise 不可) |
|------------|----------------------|----------------------|
| set / straight / flush | RAISE (raise option 行使) | **CALL のみ** |
| overpair / 2P | CALL | CALL |
| TP | CALL (bluff catch) | CALL (bluff catch) |
| A-high | mostly FOLD | mostly FOLD |
| air | FOLD | FOLD |

最大の違いは **「強いハンドの挙動」** です。

- **Cash**: set+/straight+ は raise option を行使して **value extract**
- **MTT**: raise option がないので **call のみ** → こちらの S が「raise しない」ではなく「raise できない」

これは行動の差ではなく **行動可能性の差**。Cash の v14 公式が「set+ × allin = RAISE」と書いているのは raise option がある前提で、MTT の v15 では同じセルが「CALL」になります。

## なぜ raise option があるなら raise すべきか (Cash)

Cash 100bb で near-all-in overbet (例 R89.6) を受けて set を持っている場合、なぜ raise すべきか?

**理由 1: value 最大化**

相手の near-all-in は polarized: ナッツ近辺 + 完全 bluff の二極化。こちらが set を持って raise (full all-in に push) すると:

- 相手の **ナッツ** (例: top set vs middle set) → call、こちらが勝ち full pot
- 相手の **bluff** → fold、こちらが取り
- 相手の **medium** → 既に near-all-in した時点で fold していない (commitした) → call/fold は微妙

raise によって value (こちらが勝つ pot) を最大化できる場面。

**理由 2: 相手の bluff を keep them honest**

raise すると相手の bluff も call せざるを得ない場面が出てくる (pot odds が良くなる)。bluff catch の確率が上がる。

**理由 3: stack 全体の commit**

both players が all-in に進む → pot 全体 で勝負が決まる、これが set+ 強ハンドにとって最大 EV。

これら全てが「raise option がある」を前提とする。MTT の真 all-in ではこの戦略が使えない。

## MTT の真 all-in での bluff catch の難しさ

MTT の真 all-in (相手が all-in shove で残スタックゼロ) を受けて bluff catch を試みるとき、Cash と何が違うか?

**Cash 100bb のbluff catch (例: TP × overbet):**

- 相手の near-all-in は polarized (ナッツ + 完全 bluff)
- bluff frequency が **30-40%** ある (相手も polarize して bluff を入れている)
- call すれば期待値 +EV

**MTT 50bb の bluff catch (例: TP × 真all-in):**

- 相手の真 all-in は **より polarized** (more nut, less bluff)
- 真 all-in は相手にとって commit 不可避 → リスク大、bluff frequency が **20-30%** に下がる
- その分こちらは tighter call が必要 → bluff catch threshold が上がる

検証データでも、MTT 50bb River の weak_hands × all-in での call frequency は Cash 100bb の同等局面より **10-15% 低い**。

## 公式の差を 1 ルールで表すと

Cash v14 と MTT v15 の最重要な差を 1 ルールで表すと:

```
Cash near-all-in (raise option 可):
  best_hands ∧ eqp > 0.85 → CALL
  best_hands ∧ mv ∈ {set, straight, flush, ...} → RAISE (raise option 行使)

MTT 真 all-in (raise option 不可):
  best_hands → CALL (eqp 関係なく)
  best_hands ∧ mv ∈ {set, straight, flush, ...} → CALL (RAISE できない)
```

この 1 行の違いだけで、River defense の huge_loss が:

- Cash 公式を MTT に適用 → 0.316 BB
- MTT 専用公式 → **0.038 BB**

という劇的差を生む。

## stack depth の grey zone

Cash 100bb と MTT 50bb の中間 (例 MTT 75bb, MTT 100bb) では all-in の意味がどう変わるか?

**MTT 100bb (= Cash 100bb の depth):**

- SPR は Cash と同程度 (~7-10)
- all-in も Cash 同様 (raise option がある場面が多い)
- Cash の v14 公式がほぼそのまま使える

**MTT 75bb (中間):**

- SPR ~5 で Cash と MTT 50bb の間
- turn defense は Cash 寄り (mv+dv), river は MTT 寄り (bucket + 真allin)
- 検証データが不足するため、本書では Cash v14 → MTT v15 のブレンドを推奨

**MTT 25bb (super short):**

- SPR 1-2 で完全に push/fold の世界
- turn 以降の判断はほぼ「shove or call all-in」のみ
- 詳細データなし (現サブスクで取得不可)、Vol4 のような simpler heuristic で扱うのが現実的

## 実戦での判別フロー

実戦中に「相手のベットは Cash の near-all-in か、MTT の真 all-in か」を判別するフロー:

1. **相手の残スタックを確認** — ベット後に相手のチップがゼロなら真 all-in
2. **自分の残スタックを確認** — call しきった後にこちらもゼロ近くなるか?
3. **両者共に残スタックゼロ or 微小 (3 BB 未満)** → **真 all-in 扱い** (= MTT 公式)
4. **どちらかに meaningful な残スタック (5+ BB)** → **near-all-in overbet 扱い** (= Cash 公式)

Cash 100bb でも turn で大きな pot になれば river は真 all-in になります。逆に MTT 100bb の早い段階では near-all-in overbet が起こります。本書の Cash/MTT 区分は **典型的な状況の言葉** であり、**実際は SPR + stack で判断** すべきです。

## 理論の一般化 — depth ではなく SPR で判断

本書の本当のメッセージは:

> **「Cash か MTT か」ではなく「SPR がどれだけ低いか」が公式を変える**

Cash 25bb (super short cash) と MTT 25bb はほぼ同じ公式を使える。Cash 200bb と MTT 200bb も同じ。Stack depth と game type を分けて考える必要はなく、**SPR と pot 構造だけが本質**。

実戦的には:

- **SPR ≥ 7 (Cash 100bb turn など)**: Cash v8 公式 (mv+dv 軸)
- **SPR 3-7 (Cash river, MTT 100bb turn, etc.)**: bucket + mv override 公式 (v14)
- **SPR ≤ 2 (MTT 50bb river, MTT 25bb turn 後)**: 真 all-in 公式 (v15)

この **SPR-based 公式選択** が Vol3 の最も普遍的な実用ルールです。

## 次の章へ

all-in の意味論を深く理解しました。次の ch09 では **3-bet pot** の defense を簡易扱いします。3bp は SPR がさらに下がるため、ICM ベースの判断が支配的になります。
