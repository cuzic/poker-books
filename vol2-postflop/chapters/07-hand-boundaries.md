# 第 7 章　境界ハンド集 — Hand Strength の outlier

## 7.1 逆 U 字パターンの発見

GTO ソルバーの 6 カテゴリ × 42 boards 集計 (BTN attacker、 cbet 平均):

| カテゴリ | avg cbet | 隣接差 |
|------|---:|---:|
| ナッツメイド (FH / quads) | 9% | — (slowplay base) |
| ストロング (set / flush) | 29% | +20% |
| **ツーペア** | **67%** | +38% (peak) |
| トップペア以上 | 52% | −15% |
| アンダーペア | 24% | −28% |
| エア (bluff) | 37% | +13% (逆転) |

**山型 (逆 U 字) パターン: ツーペアが最高頻度 (67%)** になります。

直感的には「ナッツが一番 bet される」と思いがちですが、実は GTO では
**ツーペアが peak** なんです。これは:

- ナッツメイド (FH / quads): slowplay (trap)で、相手の bluff を引き出すため check
- 2P: 相対 nut として、bet で value を最大化
- TP: 値 52% は protection bet で、ある程度 thin value を含む
- アンダーペア: 24% は bluff catch range の中位
- エア: 37% は bluff catch / 純 bluff

本書ではこの分布を 4 カテゴリ (エア / ミドル / TP+ / 2P+) に集約し、
Grid 12 cells で吸収しています。 ツーペア peak は 「2P+ × paired = 28」
「2P+ × wet = 23」 で間接的に表現されています。

## 7.2 ツーペア 67% peak の意味

paired board では意外にも 2P は最も bet されにくい傾向が見られます (per board family):

| board | 2P bet 頻度 |
|---|---|
| dry | 70%+ |
| wet | 60-70% |
| paired | **0-30%** (極端な減少) |

paired board × 2P が低頻度の理由をご説明します:
- paired board で 2P は **set / FH に勝てない**
- 相手の trip range が広くなる → bet で価値を取りに行けない
- slowplay 化 (call → showdown ベース)

→ 例外 5 (2P+ × wet × flop × SRP → fold) と関連があり、paired での 2P
扱いは別の例外候補となる可能性があります。

## 7.3 ボトムペア vs アンダーペアの境界

ボード K-7-2 の例で見てみましょう:

| ペアの種類 | カテゴリ | 例 |
|---|---|---|
| top_pair (K) | TP+ | AK、 KQ、 KJ、 K9s |
| second_pair (7) | アンダーペア | A7、 87、 76s |
| third_pair (2) | アンダーペア | A2、 32 |
| underpair (≤6) | アンダーペア | 66、 55、 44、 33 |

注意として、**ポケットペアでボード最低 rank と並ぶ** (例: K72 で 77) は second_pair
扱いになります (board 上の 7 と並ぶ → セット化はしていません)。

## 7.4 mv_cat 別 outlier 一覧

### top_pair のキッカー強弱

| キッカー強さ | mv_cat | 実 GTO 扱い |
|---|---|---|
| TPTK (top kicker) | top_pair | TP+ 完全相当 |
| TPGK (good kicker、 例: K72 で KQ) | top_pair | TP+ |
| TPWK (weak kicker、 例: K72 で K6) | top_pair | TP+ ですがリバーで弱体化します |
| TP no kicker (例: K7 で K7) | top_pair | TP+ ですが罠になりやすい |

Score 公式は **キッカー強弱を無視** します。これは audit で「キッカー分離は
情報過多」という結果が出たためで、マージナル境界では他軸 (oc / pot / bs)
で吸収しています。

### second_pair vs third_pair

両方アンダーペアですが、second は third より +3〜+5 BB の avg gain があります。ただし
Grid 集約上は同じカテゴリ (18 / 40 / 10) として扱っています。

## 7.5 境界ハンド ~15 個の暗記リスト

公式から外れる代表ハンド (各 spot の追加調整がおすすめな場合):

| ハンド | spot | 補正 | 理由 |
|---|---|---|---|
| A2s on A82 | TP+ × dry | -2 | TPWK、 weak kicker |
| K9 on K72 | TP+ × dry | -1 | TPGK |
| 88 on K72 | ミドル × dry | +2 | underpair 高め |
| 77 on K72 | ミドル × dry | +3 | second pair |
| 55 on K72 | ミドル × dry | -1 | underpair 低め |
| A7s on AA7 | TP+ × paired | +5 | 2P 化、 2P+ 候補 |
| TT on T87 | 2P+ × wet | -2 | set ですが wet |
| 65 on 998 | エア × paired | +3 | OESD あり (DV で吸収) |
| Q8s on T98 | エア × wet | +1 | gutshot + 2 over |
| A5s on K72 | エア × dry | +2 | bdfd + nut blocker |
| KQ on AKQ | TP+ × wet | -3 | 2nd pair top kicker |
| 99 on T87 | ミドル × wet | -2 | underpair on wet |
| AQ on Q72 (mono Q) | TP+ × wet | -3 | mono で flush 警戒 |
| JJ on AQT | ミドル × wet | -3 | underpair + scary |
| 76s on 985 | エア × wet | +4 | OESD + bdfd (DV で大半吸収) |

これらは「公式値 ± 補正」で覚えていただくといいでしょう。補正値は本書の audit が「ほぼ Grid 内に
吸収できる」と示しているため、多くの場合は無視しても大丈夫です。

## Cash/MTT note

境界ハンドは Cash/MTT 共通です。ただし MTT short stack (25bb) では TPWK でも committed range で fold 不可となるため、境界 hand の挙動が「常に call 寄り」に偏ります。deep Cash では境界 hand を厳密に判定することがおすすめです。

## この章で覚える項目 (5 items)

1. 逆 U 字パターン (ツーペア 67% peak)
2. paired × 2P = 0% 近辺 (slowplay)
3. キッカー強弱は公式は無視 (oc / pot で吸収)
4. underpair はアンダーペア カテゴリ
5. 境界ハンド ~15 個の補正 (大半は無視可能、 例外 5 で救済)
