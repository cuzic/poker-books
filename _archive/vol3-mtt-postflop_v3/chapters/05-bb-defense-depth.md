# 第14章 BB Defense — Depth で fold 閾値が大きく変わる現象

BB の Flop defense は depth (25/50/100bb) で fold 頻度が大幅に変わります。
特に low_pair の fold 率は 25bb 33% → 100bb 81% と劇的に違う。
本章では SPR-axis-switching の追加証拠としてこの現象を解説します。

## Depth 別 fold/call/raise 全体傾向

MTT 25/50/100bb の BB Flop defense 全体傾向を比較します。

**BB Flop defense 全体 (MTT depth 別)**

| depth | FOLD % | CALL % | RAISE % |
|-------|--------|--------|---------|
| **25bb** | **25.3%** | 57.2% | 17.5% |
| **50bb** | 34.2% | 51.8% | 14.1% |
| **100bb** | **49.3%** | 39.2% | 11.5% |

**観察:**

- **25bb では fold が 25%** しかない (call/raise が 75%)
- **100bb では fold が 49%** — call/raise は 51% に減る
- **stack 深いほど BB は tighter defense** = よく fold する

これは 5 公理 4「サイズが 1 段階大きいほど 1 段階タイトに」の depth 版とも言える普遍法則。

## ハンド別 fold 率 (depth 比較)

ハンドのカテゴリー別で fold 率を比較すると、depth 依存性の大きさが明確になります。

**BB Flop defense fold 率: hand × depth**

| mv_cat | 25bb fold | 50bb fold | 100bb fold |
|--------|-----------|-----------|-----------|
| **set / straight / 2P / trips / overpair** | 0% | 0% | 0% |
| **TP** | 0% | 1% | 4% |
| **2nd pair** | 1% | 4% | 13% |
| **3rd pair** | 5% | 10% | **27%** |
| **low_pair** | **33%** | 56% | **81%** ⚠️ |
| **ace_high** | 23% | 29% | **66%** |
| **king_high** | 32% | 40% | 67% |
| **no_made** | 45% | 59% | 72% |

## low_pair の劇的な変化

**low_pair の fold 率は 25bb で 33%、100bb で 81% と 2.5 倍** に増えます。これは Vol3 ch02 で扱った「low_pair × no_draw × dry → FOLD」公式の depth 依存性を示します。

**公式の depth 別調整:**

- **MTT 25bb** (SPR ~4): low_pair × dry → **CALL** (67%)
  - 理由: SPR 低くてコミット圏近い、low_pair でも showdown まで進める価値
- **MTT 50bb** (SPR ~9): low_pair × dry → **FOLD** (56%, borderline)
  - Vol3 v7 公式の「FOLD」は正しいが境界
- **MTT 100bb** (SPR ~18): low_pair × dry → **FOLD** (81%, clear)
  - Vol3 v7 公式の「FOLD」が完全に正解

**実戦的な depth-aware ルール:**

| depth | low_pair × no_draw × dry の判断 |
|-------|------------------------------|
| ≤25bb | CALL (SPR 低くてコミット価値) |
| 50bb | borderline (Vol3 v7 公式 FOLD でほぼ正解) |
| ≥100bb | FOLD (Vol3 v7 公式そのまま) |

## ace_high / king_high の挙動変化

A-high と K-high も depth で挙動が大きく変わります。

**A-high fold 率:**
- 25bb: 23% (call 77%)
- 50bb: 29%
- 100bb: **66%** (FOLD majority)

**理由:**

- 25bb で BTN の cbet レンジは strong (TT+, AKs+ で 60%+) だが、SPR が低くて BB のコミット価値が高い → A-high でもコール余地
- 100bb で BTN の cbet レンジは wider (~40% of opened range) だが、A-high は相手の TPTK に負ける確率高 + drawing odds 弱い → FOLD

これは Vol3 ch02 で「A-high + no_draw → FOLD」を Vol2 マトリックスから引き継いだ公式の妥当性を **depth 100bb で確認**し、**25bb では公式が間違い** (CALL 寄り) であることを示します。

## 強いハンド (set/straight/2P/trips/overpair) は全 depth で 0% fold

table の最上段が示す通り、これら強いハンドは **どの depth でも 0% fold** です。これは:

- 絶対的に強い (相手のレンジに対してほぼ確実に勝つ)
- SPR 関係なく commit する価値
- drawing odds や bluff catch の判断不要

Vol3 v7 公式の「強いハンドは default CALL or RAISE」が depth 不変に正しいことを示します。

## 実戦への帰結 — depth-aware defense

この章の発見を実戦に応用すると:

**MTT 25bb の BB defense (深く考えず):**

- 完全 air (no_made + no_draw) のみ FOLD (45%)
- 弱ペア (low_pair, 3rd_pair) は CALL (33% / 5% fold)
- 中-強ハンドは CALL or RAISE
- **「ほぼ全部 call」** が GTO 近い (SPR 低くてコミット圏)

**MTT 50bb の BB defense (Vol3 v7 公式):**

- low_pair × no_draw × dry → FOLD (56%, borderline)
- 3rd_pair × no_draw × dry → CALL (10% fold)
- 中-強は全部 call

**MTT 100bb の BB defense (Vol3 v7 公式厳格適用):**

- low_pair × no_draw × dry → FOLD (81%, clear)
- 3rd_pair × no_draw × dry → CALL or FOLD (27% fold, borderline)
- 中-強は call、TP は 4% fold (ほぼ call)

**Vol3 v7 公式は depth 50-100bb で最も正確、25bb では loose 寄りに補正必要。**

## Vol2 マトリックスへのフィードバック

Vol2 の 5×4 マトリックス (W × m = CALL、ただし dry では補正で FOLD) は **Cash 100bb および MTT 100bb で正確**、MTT 50bb で borderline、**MTT 25bb では loose 寄りに修正必要**。

Vol2 ユーザーが MTT 25bb をプレイする場合の補正:

- Vol2 マトリックスの「W × m × dry → FOLD」を **「W × m × dry × MTT short stack → CALL」** に変更
- 短スタック特化の戦略書 (Vol4 の予定章) で詳述するべきメッセージ

## SPR-axis-switching の追加観点

Vol3 ch01 で導入した SPR-axis-switching は **「軸が切り替わる」** と言いましたが、もう一段深い理解は:

> **「同じ軸でも閾値が SPR で動く」**

具体的には:

- mv 軸の絶対強さ判定は同じ (low_pair はどの depth でも low_pair)
- **しかし fold/call の閾値が SPR でシフト**
- 低 SPR: 弱ハンドでもコミット価値 → CALL 寄り
- 高 SPR: 弱ハンドは将来の commit 困難 → FOLD 寄り

この「閾値シフト」が depth 別の fold 率分布として観察される。

## 次の章へ

BB Defense の depth 依存性を学びました。次の ch15 では **BB Turn donk lead** という攻撃側の重要パターンを解説します。MTT 100bb で 16% donk するという驚きの GTO 戦略を明らかにします。
