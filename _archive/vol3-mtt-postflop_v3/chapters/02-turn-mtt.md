# 第04章 Turn defense 詳細 — MTT 50bb (bucket 軸、v9)

MTT 50bb の Turn defense は SPR ~3 で **bucket (相対強さ)** 軸が支配的です。
Cash の mv+dv 軸が機能しなくなり、bucket-based 公式 v9 で huge_loss を 0.057 BB まで圧縮できます。
SPR-axis-switching の最も劇的な実例です。

## なぜ MTT 50bb で bucket 軸に切り替わるか

Cash 100bb と MTT 50bb の最大の違いは **SPR (Stack-to-Pot Ratio)** です。

**Cash 100bb vs MTT 50bb の SPR**

| 局面 | Cash 100bb | MTT 50bb |
|------|-----------|----------|
| Preflop | 100 BB / 1 BB = **100** | 50 BB / 1 BB = **50** |
| Flop 開始 | 約 18 | 約 9 |
| Turn 開始 (flop cbet 後) | **~7** | **~3** |
| River 開始 | ~3 | ~1 |

MTT 50bb の Turn は SPR ~3 — Cash 100bb の **River** と同じです。実際、ベットサイズも **二極化** します。

- **Cash 100bb Turn**: 25% / 67% / 185% の 3 段階
- **MTT 50bb Turn**: 25% / 117% の **2 段階のみ** (R2.3 と R10.6)

67% pot の "medium" サイズが MTT 50bb の solver tree に存在しないのです。なぜなら SPR が小さいため、相手が medium bet を打つと残スタックで raise しきれない (commit 不可能) → solver は二択を最適化。

結論: MTT 50bb Turn は **「small block bet」 (R2.3 = 25%) と「commit-or-fold size」 (R10.6 = 117%)** の二択。中間サイズの mv+dv ベース判断は機能しません。

## MTT 50bb Turn 公式 v9 — pure bucket

MTT 50bb Turn は **equity bucket** だけで判断します。

```
MTT 50bb Turn defense v9 (pure bucket):

── best_hands (相対強さ上位 25%) ──
vs overbet (R10.6 = 117% pot):
  強メイド (set/2P+/straight/flush+) ∧ 非monotone → RAISE
  その他 → CALL
vs small (R2.3 = 25% pot):
  全て CALL

── good_hands (上位 25-50%) ──
vs overbet: 強メイド ∧ 非monotone → RAISE、その他 → CALL
vs small: 全て CALL

── weak_hands (下位 25-50%) ──
vs overbet:
  強ドロー (OESD/FD/combo) ∧ 非monotone → CALL
  その他 → FOLD
vs small: 全て CALL

── trash_hands (下位 25%) ──
vs overbet: FOLD
vs small:
  強ドロー ∧ 非monotone → CALL
  その他 → FOLD
```

## bucket の実戦判定

実戦で **「自分の hand は best/good/weak/trash のどれか?」** を瞬時に判定する必要があります。GTO Wizard の bucket 計算は relative equity vs villain range で複雑ですが、実用的な近似は以下です。

**bucket の実用近似 (MTT 50bb Turn)**

| bucket | 典型的な hand |
|--------|-----------|
| best_hands | set / 2P / straight / flush / overpair (board に対して強い), nut FD |
| good_hands | TPTK / weaker overpair / strong draws (combo, OESD+FD) |
| weak_hands | TP weaker kicker / 2nd-3rd pair / OESD / FD alone |
| trash_hands | A-high / K-high / low pair / no_made + no_draw |

重要: bucket は **相手のレンジ依存** なので、同じ TP でも板や preflop action で bucket が変わります。例えば:

- **K-7-2 + AK (TPTK)** vs BTN cbet range → **best_hands** (BTN の cbet range の上位 25%)
- **K-7-2 + KQ (TP weaker kicker)** vs BTN cbet range → **good_hands**
- **A-7-2 + 77 (set)** vs BTN cbet range → **best_hands**

慣れるまでは「**Vol2 マトリックスの S は best、M は good、W は weak、A は trash**」と単純対応すれば 80% 正解できます。

## 二極化サイズの意味

MTT 50bb Turn の 2 つのサイズには明確な意味があります。

**R2.3 (small block bet, 25% pot):**

- 相手の意図: 「showdown を見たい、安く済ませたい」or 「cheap value with weak hand」
- 相手のレンジ: **wide** (mid pair, A-high まで含む)
- こちらの対応: **広く call** (pot odds 良い)
- **公式: bucket weak 以上は call、trash は FOLD or 強ドローで call**

**R10.6 (commit-or-fold size, 117% pot):**

- 相手の意図: 「commit する」「ナッツでバリュー押し付け」or 「polarized bluff」
- 相手のレンジ: **polarized** (very strong + bluff)
- こちらの対応: **best/good で CALL、weak は強ドロー以外 fold**
- **公式: bucket best/good は強メイドで RAISE (commit)、その他 CALL or FOLD**

この二極化が「MTT 50bb は commit-or-fold の世界」と呼ばれる所以です。

## monotone 板の例外

MTT 50bb Turn v9 では **monotone (3-flush board) で RAISE 抑制** が特徴です。

**理由:**

- monotone 板で相手の overbet → こちらに ♠ flush 持ちでも、相手の higher flush に逆転される確率あり
- RAISE すると相手の re-raise で commit 強制、こちらの flush が下位の場合 disaster
- **CALL で安全に value 取りに行く** ほうが EV 高い

**検証:** flush × overbet × monotone (n=18): actual CALL 67% / RAISE 33% → mostly CALL が正解

monotone 補正は次の Cash River でも出てきますが、MTT 50bb Turn では特に重要。

## Cash v8 を MTT に適用したら何が起きるか

SPR-axis-switching の実証として、**Cash v8 を MTT 50bb に適用** すると何が起きるかを見てみます。

**MTT 50bb Turn defense: 公式比較**

| 公式 | accuracy | mean loss | huge_loss |
|------|---------|-----------|-----------|
| Cash v8 (mv+dv) を MTT に適用 | 78.4% | 0.157 BB | **0.133 BB** |
| **MTT v9 (pure bucket)** | **83.8%** | **0.057** | **0.057** ⭐ |
| MTT v10 (bucket + hybrid layer) | 84.1% | 0.057 | 0.062 |

Cash v8 を MTT に適用すると huge_loss が **3.6 倍** 悪化 (0.037 → 0.133)。一方、bucket-based MTT v9 だと **0.057** で収まります。

これは「MTT は SPR が小さく、bucket 軸が支配的」という事実の最も直接的な実証です。

## 実戦例: MTT 50bb Turn の判断

**例 1: K-7-2-3 (turn) で AKo (TPTK)、相手が turn overbet 117%**

- bucket 判定: AKo on K-7-2 = TPTK → BTN range に対して **good_hands** (上位 25-50%)
- サイズ: overbet
- 公式 v9 適用: good × overbet → 強メイド (TPTK は強メイドだが set/2P+ ではない) → **CALL**
- **アクション: CALL**

注: Vol2 では AKo + overbet は M × o = FOLD と判断するが、MTT 50bb Turn では TPTK は call 余地あり (相手の polarized range で bluff catch 機能)。

**例 2: T-9-8-2 (dynamic) で 6♠5♠ (gutshot のみ、no_made)、相手が overbet 117%**

- bucket: no_made + weak draw = **trash_hands**
- サイズ: overbet
- 公式 v9: trash × overbet → **FOLD**
- **アクション: FOLD**

**例 3: T-9-8-2 で 7♣6♣ (OESD, no_made)、相手が small 25%**

- bucket: no_made + strong draw (OESD) = **weak_hands** (OESD は equity 32% で weak 域)
- サイズ: small
- 公式 v9: weak × small → CALL (small だから call 広く)
- **アクション: CALL**

**例 4: T-9-8-2 で 6♣5♣ (set... これは 6 のセットだが flopped 6 はない → no_made + OESD with completed 7)**

待って、複雑なので別例を:

**例 4 (修正): K♣7♣2♦5♣ (turn が 5、3 ♣ になった) で A♣J♦ (nut flush + completed FD)、相手が overbet 117%**

- bucket: nut flush = **best_hands**
- サイズ: overbet
- 公式 v9: best × overbet → 強メイド (flush) × 板は monotone-flush (3 flush) → monotone 補正で **CALL** (RAISE しない)
- **アクション: CALL**

## 次の章へ

Cash と MTT で軸が劇的に変わる様子を見ました。次の ch05-06 では **River defense** に進み、Cash の bucket+mv ベース v14、MTT の真allin aware v15 を解説します。
