# 第03章 攻撃マトリックス — 自分が動く番のアクションを決める

自分が先にアクションを起こす局面 (相手のチェック後、あるいは自分が手番の先頭) では、5 × 3 マトリックスでベットするかチェックするかを決めます。
この章では Flop / Turn / River の街ごとに攻撃マトリックスの内容と理由を解説します。

## 攻撃マトリックスの全貌

攻撃側 (自分が動く番) で参照するマトリックスは以下です。サイズ軸が無いのは「自分が打つ」状況だからで、代わりに**街軸** (Flop/Turn/River) が入ります。

**攻撃マトリックス (BET or CHECK)**

| ハンド強さ | Flop | Turn | River |
|-----------|------|------|-------|
| **S** (Strong) | BET | CHECK (slowplay) | BET |
| **M** (Medium) | CHECK | CHECK | BET on dry / CHECK on dynamic |
| **W** (Weak) | CHECK | CHECK | CHECK |
| **A** (Air) | CHECK | CHECK | BET as bluff |
| **D** (Draw) | CHECK (semibluff 控えめ) | CHECK | — (D は river に存在しない) |

表を見ると、**攻撃側は基本 CHECK** が圧倒的多数で、BET は限定的なセルだけです。これは GTO の検証データに基づきます。Cash 100bb の攻撃側で「default CHECK + 7 セルだけ BET」という戦略が EV 損失 0.023 BB/decision という非常に小さい値に収まることが確認されています (詳細は付録)。

この章では各セルの意味と理由を街ごとに解説します。

## Flop attack — 7 つの BET セルと残り全部 CHECK

Flop の攻撃側は **default CHECK + 7 例外 BET** という構造です。マトリックス上は「**S → BET**」だけですが、その S の中身を詳しく見ると以下の 7 セルが BET になります (検証データから抽出)。

**Flop attack の 7 例外 BET セル**

| # | ハンド強さ | メイドハンド | ドロー | ボード | BET 頻度 |
|---|------------|-------------|--------|--------|----------|
| 1 | S (best) | overpair | gutshot | dynamic | 100% |
| 2 | S (best) | overpair | OESD | dynamic_2tone | 99% |
| 3 | S (good) | overpair | gutshot | dynamic_2tone | 100% |
| 4 | S (good) | overpair | no_draw | low_dry | 100% |
| 5 | S (good) | overpair | gutshot | dynamic | 100% |
| 6 | W (weak) | king_high | no_draw | paired | 95% |
| 7 | S (good) | underpair | no_draw | paired | 100% |

共通パターンは **overpair on dry/dynamic board** です。overpair (例: AA on K-7-2、KK on T-7-2) は **range advantage** (相手より強いハンドの密度が高い) があるため、small cbet (33%) で攻めるのが GTO 最適です。

ペアボード (#6, #7) は例外的に「弱いハンドでブラフ + 強いハンドでバリュー」の polarized 戦略になります。

その他のハンドはほぼ全て CHECK が正解です。 weak/air は当然として、TP や 2nd pair すら基本 CHECK が GTO です。

## Turn attack — 「常に CHECK」が GTO

Turn の攻撃側は **ほぼ全セル CHECK** が GTO です。検証データによれば、Cash 100bb で turn を「always CHECK」にしても EV 損失わずか **0.003 BB/decision** で済みます。これは事実上**ゼロ**と言える小ささです。

理由は以下です。

- **Flop で cbet → Turn でも続けて barrel** は range advantage を活かすが、相手の call range は既に bluff catcher 中心になっており、turn で更に攻めても薄い
- **Turn で check すると相手も check しがち** で showdown を見にいける
- **強いハンドは check raise を狙う** ことで slowplay できる

実戦的には「Flop で BET したら Turn は CHECK が原則」と覚えれば十分です。例外は overbet によるバリュー押し付けですが、本書は簡易版なので扱いません (Vol3 で詳説)。

## River attack — polarized (value + bluff)

River の攻撃側は **polarized 戦略** が GTO です。具体的には:

- **強いハンド (S)** → BET for value
- **完全 air (A)** → BET as bluff (blocker 付き)
- **中程度 (M/W)** → CHECK (showdown value で勝負)

これは「**value + bluff の polarized range で打つ**」という古典的なポーカー理論そのものです。

ただし**ボード次第**で M の挙動が変わります。

- **M × dry board** → BET (TP は dry board で十分強い)
- **M × dynamic board** → CHECK (draws が complete している恐れ)

理由は dynamic board (3-4 連結カードや 2 tone+turn) では多くの draws が river で complete し、TP のような medium ハンドは負けている確率が上がるためです。

## River attack マトリックス詳細

**River attack 詳細マトリックス**

| ハンド強さ | dry/low_dry | dynamic/monotone | paired |
|-----------|-------------|-------------------|--------|
| **S** (set+/straight/flush) | BET | BET | BET |
| **S** (overpair) | BET | BET | CHECK (相手にトリップス) |
| **M** (top pair) | BET | CHECK | CHECK |
| **M** (2nd/3rd pair) | CHECK | CHECK | CHECK |
| **W** (A-high) | CHECK | CHECK | CHECK |
| **A** (no_made_hand) | CHECK | **BET (bluff)** | CHECK |
| **A** (king_high) | BET (bluff) | BET (bluff) | CHECK |

この詳細マトリックスでは:

- **S は常に BET** が原則 (slowplay は dry board の set などで稀)
- **TP は dry のみ BET、dynamic は CHECK**
- **air bluff は dynamic board で no_made を使う**
- **K-high は良い bluff candidate** (K のブロッカーで相手の TPTK を fold させる)

## なぜ攻撃マトリックスはこれほど CHECK 寄りか

初心者から見ると「もっと積極的にベットすべきでは?」と思うかもしれません。しかし GTO データはむしろ「**default CHECK + 限定的 BET**」が最適と示しています。

理由は **range advantage** という概念です。

- **OOP (BB)** は preflop で BTN の open に対して call しただけなので、レンジは大半が medium 強度
- **IP (BTN)** は preflop で raise したのでナッツとブラフが両端の polarized range
- フロップで両者がチェックすると **range vs range** の戦いになるが、BB の range は medium 中心で「TP+ を bet」しても call/raise されることが多い
- 結果として「**TP は CHECK が EV 高い**」というカウンター直感的な結論になる

この理屈を完全に理解する必要はありません。実践的には「**迷ったら CHECK**」を原則として、上記の 7 例外と river polarization を加えるだけで十分です。

## 5 公理の再確認

攻撃マトリックスを 5 公理に照らすと:

- **公理 3「強いハンドは aggressive、弱いハンドは passive」** → S は BET、A は CHECK が基本 (river bluff は例外)
- **公理 5「完全 air は基本諦める」** → A は flop/turn で CHECK、river のみ bluff
- **公理 1, 2 (5 段階 / 4 段階)** → 攻撃側はサイズを自分で決めるが、本書は簡易のため**標準サイズ** (Flop 33%, River 75%) を推奨

攻撃時のサイズ選択は Vol3 で詳説します。本書では「BET したら 33% pot (Flop)、66-75% pot (River)」で十分です。

## 次の章へ

攻撃マトリックスを習得しました。次は **守備マトリックス** (ch04) で、相手のベットを受けたときの FOLD/CALL/RAISE を学びます。攻撃と守備の両マトリックスが揃えば、Cash 100bb のポストフロップ判断の **90% 以上** が自動化されます。
