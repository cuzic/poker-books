# 第06章 Turn の特殊性 — slowplay 全面採用と overbet vs draws

Turn は SPR が下がり、判断のミスが大きな EV 損失につながりやすい街です。
攻撃側は「常に CHECK (slowplay 全面)」が GTO 最適、守備側は「draws の implied odds が消失する overbet には FOLD」が原則です。
本章では Turn 特有の重要パターンを 2 つの観点で解説します。

## Turn 攻撃 — 常に CHECK が最適

ch03 で簡単に触れましたが、Turn の攻撃側は **ほぼ全セル CHECK** が GTO です。

検証データ: Cash 100bb で turn を「always CHECK」にしたときの EV 損失は **0.003 BB/decision** という事実上ゼロの値です。「flop で cbet したら turn は check」を機械的に実行して問題ありません。

理由は以下です。

- **Flop で BET → call された** ということは、相手の hand range は medium 強度に絞られている
- **Turn でさらに BET (2nd barrel)** すると、相手の bluff catcher (TP, 2nd pair など) が call/raise してくる
- これらの medium hand に対して 2nd barrel BET は EV が悪い
- **CHECK して showdown を見にいく** ほうが安全

また「**強いハンドは slowplay**」も加わります。S (set, 2P, straight) を持っているなら、turn で check して相手に bluff させる方が EV が高いことが多い。

## Turn 攻撃の例外 (例: overbet 2nd barrel)

本書 (簡易版) では turn 攻撃の例外は扱いません。「always CHECK」で十分に EV を維持できます。

ただし高度な戦略として「**dry board で overbet 2nd barrel**」(例: K-7-2 → 2 turn で 200% pot push) があり、これは特定の draws を持つ相手を fold させる polarized 戦略です。Vol3 で詳説します。

本書では「Turn は常に CHECK」を原則として、シンプルに対応します。

## Turn 守備 — overbet vs draws が最重要

Turn 守備の最重要パターンは **「相手の overbet (≥100% pot) に対しては draws もフォールド」** という点です。

ch04 標準マトリックスでは D × o = FOLD と書いていますが、これは Turn では特に重要です。

### なぜ overbet で draws が fold すべきか

**数学的説明:**

- Flush draw は 9 outs → river で hit する確率 ≈ 19.6%
- 33% pot に対して call するには **約 25% の equity** で OK → flush draw は call できる
- 50% pot に対しては **33% equity** が必要 → flush draw はまだギリギリ call
- **100% pot に対しては 50% equity** が必要 → flush draw では足りない (19.6%)
- **200% overbet に対しては 67% equity** が必要 → 完全に足りない

**理論的説明:**

Cash 100bb の turn で相手が overbet を打つということは、相手のレンジは:
- **完全 polarized**: ナッツ近辺 (set+) または完全ブラフ (air)
- **中程度のバリュー (TP, 2P) ではない**

こちらが draws を持っていて river で hit したとしても、相手がナッツ (set+) なら勝てない可能性がある (例: set vs flush では set+full house に負ける確率)。

つまり **「implied odds が overbet で消える」** という現象です。

### Turn 守備の補正リスト

ch04 標準マトリックスに加えて、Turn では以下の補正があります。

**補正 1: vs overbet (185% pot 想定) で以下は FOLD**

- air (no_made) + flush_draw × dry_high → **FOLD**
- air + OESD × dynamic → **FOLD**
- dynamic 板 + top_pair (no_draw) → **FOLD** (TP が vulnerable)

**補正 2: vs medium (67% pot) で以下は FOLD (重要拡張)**

- **dynamic 板 + A/K-high + 弱ドロー (gutshot/BDFD) → FOLD** ⭐ 最大の改善要因
- dynamic 板 + 低/中ペア (low/under/3rd) + 弱ドロー → **FOLD**
- dynamic 板 + 弱メイド (上記含む) + OESD → **FOLD**

補正 2 の **「dynamic + A/K-high + 弱ドロー → FOLD」** が特に重要で、これ単独で Turn の huge_loss を **0.43 → 0.25 BB に圧縮 (84% → 91% 削減率)** します。

理由: A-high/K-high は本書 ch01 では W (Weak) 分類ですが、**dynamic 板の Turn で gutshot だけでは drawing equity 不足** (相手の completed straight/2P に負ける確率高、implied odds 弱)。Vol2 マトリックスの W × m = CALL を override する必要があります。

補正 1+2 の合計効果: Turn の huge_gap loss を **84% → 92% 削減** (検証済み、Cash 100bb)。残る 6% (Vol3 v8 の 98%) は詳細公式が必要。

## 実戦例: Turn の判断

**例 1: Flop K-7-2 でこちらは A♣J♣ (no_made + BDFD)、call。Turn が 2♣ (dynamic 化、flush draw 完成)**

新ボード: K-7-2-2 (paired + 1 flush draw)
こちらのハンド: A♣J♣ on K-7-2-2 = no_made + nut flush draw (A♣の completed FD) → **D (Draw)**

相手が overbet 200% pot (R18 vs pot ≈ 9) を打ってきた → サイズ **o**

1. マトリックス参照 → D × o = **FOLD** (標準)
2. 補正なし (これは標準 D × o の通り)
3. **アクション: FOLD**

Flush draw でも overbet には fold するのが GTO 正解。implied odds が消えているため。

**例 2: Flop T-9-8 (dynamic) でこちらは K♥Q♠ (gutshot to broadway, no_made)、call。Turn が 2♦**

新ボード: T-9-8-2 (まだ dynamic)
こちらのハンド: K♥Q♠ on T-9-8-2 = gutshot (Jx で straight 完成) + 2 over → **A (Air、gutshot は弱ドロー扱い)**

相手が medium 67% pot を打ってきた → サイズ **m**

1. マトリックス参照 → A × m = **FOLD** (標準)
2. Turn 補正 1: dynamic + 弱メイド (no_made) + 弱ドロー (gutshot) → **FOLD** (補正適用、同じ結論)
3. **アクション: FOLD**

**例 3: Flop A-K-7 でこちらは A♠T♠ (TP)、call。Turn が 3♣**

新ボード: A-K-7-3 (dry_high のまま、特に dynamic 化なし)
こちらのハンド: A♠T♠ = TP (A pair) → **M**

相手が standard 60% pot を打ってきた → サイズ **m**

1. マトリックス参照 → M × m = **CALL**
2. Turn 補正適用 → なし (board は dry のまま、M × m は標準 CALL のまま)
3. **アクション: CALL**

## Turn での「メイド + ドロー」

TP + draw (例: TP + FD) のような **made hand + draw** は、Turn でどう扱うか。

原則は ch01 通り「**メイドハンドで分類**」 → TP なら **M**。

ただし**実質的には強い** (TP value + FD outs)。M としての判断にプラスして:

- **D の代替判断も検討**: M × l (large bet) で fold するかどうか迷ったら、D × l (CALL) も加味して**call 寄り**にする
- **Overbet に対しては D × o = FOLD と一致** → 結局 fold

これは「TP + FD は M としては大きいが、overbet では諦める」という現実的なバランスです。

## Turn 攻撃の RAISE しない原則

Turn 守備マトリックスを見ると、S 行が全サイズで **CALL** (RAISE なし) になっています。これは**ターンでは強いハンドも slowplay する** という原則です。

理由:

- 強いハンドで turn raise すると、相手の bluff range が check に戻る → river で実りが減る
- Turn raise すると相手は強い hand 以外 fold → こちらの S が無駄になる
- **turn は call で繋いで river で爆発させる** ほうが EV 高い

例外: Cash の場合は raise する場面もある (s に対して RAISE して fold equity を取りに行く) が、本書では「**Turn の S は CALL**」を原則化します。

## 次の章へ

Turn の judgments を習得しました。次は River (ch07) で **polarization** と **bucket 軸** (相対強さ) の判断を学びます。
