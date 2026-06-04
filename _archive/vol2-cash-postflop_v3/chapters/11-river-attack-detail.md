# 第11章 River attack 詳細 — polarization + slowplay の v7 公式

River attack は Cash/MTT 共通で polarized 戦略 (value + bluff) が基本です。
v7 公式 (5 ルール体系) で huge_loss を 0.16 BB まで圧縮。
ボード特性 (dry vs dynamic) で TP と strong made の挙動が逆転する興味深い構造を解説します。

## River attack v7 公式

```
River attack v7:

Rule 1 (CHECK): mv ∈ {set, trips, straight, flush, fullhouse, quads} ∧ board ∈ dry
  → 強メイド on dry → slowplay (CHECK)
  理由: dry 板で相手の call range が薄い、check-raise を狙う

Rule 2 (CHECK): mv = top_pair ∧ board ∈ dynamic
  → TP on dynamic → vulnerable, CHECK
  理由: dynamic 板で draws complete、TP は負けの確率上昇

Rule 3 (BET value): mv ∈ {top_pair, overpair, two_pair, set, trips, straight, flush+}
  → value bet
  ※ Rule 1, 2 で先に CHECK 判定済みのものを除外

Rule 4 (BET bluff): mv ∈ {no_made_hand, king_high}
  → bluff bet (polarized range の bluff 側)

Rule 5 (CHECK default): その他全て (M = 2nd/3rd pair, W = A-high/low_pair など)
```

## なぜ強メイドが dry で slowplay

Rule 1 は **「強メイド on dry board → CHECK (slowplay)」** という反直感ルール。

**理由:**

- dry board (K-7-2-3-5 など、connected なし) で相手の caller range は narrow
- bet すると相手の make hand (TP, 2P) が call、weak hand (no_made) が fold
- こちらの set+ は **bet によって value extract できる相手 range が薄い**
- 一方、CHECK すると相手が bluff してくれる可能性
- 結果: **CHECK の方が EV 高い** (相手の bluff frequency を取り込む)

**検証データ:**

- **set × no_draw × dry_high** (Cash 100bb): pred BET (mv = set は強いから), actual **CHECK 100%**, mean loss 1.00 BB
- **trips × no_draw × dry_high** (n=88 in Cash): pred BET, actual CHECK, mean loss 1.00 BB
- **straight × no_draw × dry_high** (n=80): pred BET, actual CHECK, mean loss 0.61 BB

これら全部「強メイド on dry → check が GTO」のパターン。Rule 1 で完全カバー。

## なぜ TP が dynamic で CHECK

Rule 2 は **「TP on dynamic → CHECK」** という Vol2 でも触れた重要パターン。

**理由:**

- dynamic board (T-9-8-2-A など) で多くの draws (straight, flush) が complete
- こちらの TP は **負けの確率が大幅上昇** (相手の completed straight や 2P に負ける)
- bet すると相手の strong hand に raise されて disaster
- CHECK で showdown を見るのが安全

**検証データ:**

- **top_pair × no_draw × dynamic** (Cash 100bb, n=168): pred BET, actual **CHECK 73%**, mean loss 1.23 BB
- dynamic 板で TP は実は M でも弱い側

## Rule 4 の bluff 設計

Rule 4: **「no_made_hand と king_high は bluff bet」** が GTO。

**なぜこの 2 つ?**

- **no_made_hand**: 完全 air で showdown では絶対勝てない → bluff のみが + EV
- **king_high**: K のブロッカーで相手の TPTK (AKx) を fold させる効果。さらに K-high は showdown でほぼ負ける → bluff 一択

**なぜ A-high はダメ?**

- A-high は showdown value がそれなりにあり、check で勝つ可能性がある
- bluff betすると call されたら確実に負ける + showdown win も失う → CHECK が EV 高い

**検証:**

- **no_made_hand × dynamic** (Cash): actual **BET 65%** (bluff として)
- **king_high × dynamic** (Cash): actual **BET 58%** (bluff)
- **ace_high × any**: actual **CHECK 80%+** (showdown 維持)

この設計が **polarization** (value + bluff range で BET、medium hand で CHECK) の核心。

## v7 公式の検証結果

**River attack 公式比較 (Cash 100bb)**

| 公式 | accuracy | mean loss | huge_loss |
|------|---------|-----------|-----------|
| always_CHECK | 51% | 0.194 | 0.535 |
| always_BET | 49% | 0.199 | (large) |
| v4 (pure polar) | 67.3% | 0.080 | 0.177 |
| **v7 (+ dry slowplay + TP dynamic)** | **65.1%** | **0.078** | **0.159** ⭐ |

v7 は v4 と accuracy では同程度 (むしろわずかに低い) ですが、huge_loss が **0.18 → 0.16** と改善。これは「accuracy より EV loss を優先」という Vol3 全体の設計思想を反映。

mean loss も 0.080 BB と非常に小さく、river attack は実質的に v7 で完成しています。

## MTT 50bb River attack の挙動

MTT 50bb の River attack も基本的に v7 を適用できます。SPR ~1 で違いはありますが、attack 側 (自分から動く) の polarization は universal。

**ただし MTT 50bb 特有のパターン:**

- **SPR ~1 で all-in が選択肢**: BET ではなく **shove (all-in)** がデフォルトになる場面が多い
- **shove は本質的に overbet polarization**: value + bluff range で all-in
- **TP on dynamic では check** が更に重要 (commit risk 大)

実戦的には Vol2 マトリックスの "River attack BET" を **「BET = shove」と読み替える** だけで MTT 50bb にも対応可。

## 実戦例: River attack の判断

**例 1: River K-7-2-3-5 (dry) でこちらは 2♣2♦ (set)、自分が IP で BB が check してきた**

- mv 判定: set of 2's on K-7-2-3-5 = set → **S**
- board: dry_high (K-7-2-3-5 = K-high dry, low cards 連結なし) → **dry**
- Rule 1 適用: 強メイド on dry → **CHECK** (slowplay)
- **アクション: CHECK**

理由: dry 板で相手が check してきた → 相手の hand range は wide weak。BET しても call されにくい。CHECK して相手の bluff bet を river で誘発、あるいは showdown で win を確保。

**例 2: River T-9-8-2-A (dynamic) でこちらは A♠T♠ (TP-A、A pair on river)、BB が check**

- mv 判定: TP-A → **M (TP)**
- board: dynamic → straight completed possible (J-Q for straight) + flush possible
- Rule 2 適用: TP on dynamic → **CHECK**
- **アクション: CHECK**

理由: dynamic 板で TP は vulnerable。BET したら相手の straight/flush に raise されて disaster。CHECK で showdown 確保。

**例 3: River K♠7♣2♦5♣A♦ (busted hi-low draws) でこちらは 4♣3♣ (no_made + busted flush draw)、BB が check**

- mv 判定: no_made_hand
- board: dry_high (5 cards に straight 完成なし、flush 完成なし)
- Rule 4: no_made → BET (bluff)
- **board check**: dry で no_made bluff は機能するか?
  - dry 板で相手のレンジは TP/2P 多 → no_made の bluff が成功する確率は低
  - v7 公式上は BET だが、実戦では fold equity 低いので **CHECK が妥当**
- **アクション: CHECK** (公式 vs 実戦の境界、本書は公式優先で BET でも OK)

**例 4: River T-9-8-2-A (dynamic) で K♥Q♣ (busted broadway gutshot, K-high)、BB が check**

- mv 判定: king_high
- board: dynamic
- Rule 4: king_high → **BET (bluff)**
- K のブロッカーで AKx, KQ の TP を fold させる効果 + dynamic 板で相手の hand range も busted draws 多い → bluff +EV
- **アクション: BET (bluff)**

## 覚え方

River attack v7 を覚えるコツ:

**「強メイド on dry → slowplay、TP on dynamic → check、それ以外は polarized」**

この 1 文に Rule 1, 2 とその他がまとまります。Rule 3, 4, 5 は polarization (value + bluff = BET、medium = CHECK) の標準形。

実戦中の判断フロー:

1. **強メイド (set+) ?** → board 確認 → dry なら CHECK、それ以外 BET
2. **TP ?** → board 確認 → dynamic なら CHECK、それ以外 BET
3. **no_made / K-high ?** → BET (bluff)
4. **その他 (M = 2nd/3rd pair, W = A-high)?** → CHECK

## 次の章へ

River attack を完成しました。次の ch08 では **「all-in の意味論」** を深掘りし、Cash と MTT の根本的差異を理解します。これは Vol3 の最重要な理論章の一つです。
