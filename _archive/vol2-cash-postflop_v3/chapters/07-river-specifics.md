# 第07章 River の特殊性 — polarization と showdown 価値

River はドローが残らない最終街です。ハンドの強さが**確定**しているため、判断は「相手のレンジに対してこのハンドが勝てるか」を冷静に評価することになります。
この章では River 特有の polarization (value + bluff) と、特定セルでの bluff catch の判断を学びます。

## River で最も重要な事実 — ドローが残らない

River は **5 枚目のコミュニティカードが出た最終街** であり、6 枚目はありません。つまり:

- **D (Draw) のカテゴリーは存在しない** (もう次のカードが来ない)
- すべてのハンドは S / M / W / A の 4 段階に分類される
- ハンド強さは**確定的** (確率的要素なし)
- 「相手のレンジに対する勝率」が判断の基準

これは **ドローが残っている flop/turn と本質的に異なる判断軸** を要求します。具体的には「自分の確定したハンド強さ vs 相手のレンジ強さ」の比較になります。

## River 攻撃 — polarized (value + bluff)

River の攻撃側は **polarized 戦略** が GTO です。これはポーカーの古典的理論そのものです。

**BET するハンド (2 種類):**

- **Value bet**: 相手が weaker hand で call してくれる強いハンド → S (set+, straight, flush, TP on dry board, overpair など)
- **Bluff bet**: 相手が stronger hand で fold してくれる完全 air → A (no_made_hand, K-high など、ブロッカー付きが望ましい)

**CHECK するハンド (中程度):**

- **M (Medium = TP/2nd/3rd pair)** は showdown value で勝負
- **W (Weak = A-high, low pair)** も showdown value で見にいく
- BET しても call されないし、call されたら負ける確率が高い → **CHECK が EV 高い**

この「**両端 (very strong + very weak) で BET、中央 (medium) で CHECK**」の構造を **polarization** と呼びます。

### River 攻撃マトリックス詳細

**River attack (BET or CHECK)**

| ハンド強さ | dry/low_dry | dynamic/monotone | paired |
|-----------|-------------|-------------------|--------|
| **S** (set+/straight/flush/overpair) | BET | BET | BET |
| **M** (top pair) | BET | **CHECK** | CHECK |
| **M** (2nd/3rd pair, underpair) | CHECK | CHECK | CHECK |
| **W** (A-high, low pair) | CHECK | CHECK | CHECK |
| **A** (no_made_hand) | CHECK | **BET (bluff)** | CHECK |
| **A** (king_high) | **BET (bluff)** | **BET (bluff)** | CHECK |

**重要パターンの理由:**

- **TP × dry → BET**: dry board (K-7-2-3-5 など) では相手のレンジに draws が完成しておらず、TP はまだ強い
- **TP × dynamic → CHECK**: dynamic board では straight や flush の draws が完成している可能性、TP は vulnerable
- **no_made × dynamic → BET (bluff)**: dynamic board で相手のレンジが弱い (busted draws) なら、blocker 付きの air bluff が通る
- **K-high → BET (bluff)**: K blocker で相手の TPTK (AKx) を fold させる効果あり

## River 守備 — bucket 軸 (相対強さ) が支配的

River 守備でも ch04 標準マトリックスが基本ですが、River 特有のパターンがあります。

最重要な発見は **「相対強さ (bucket) で判断する」** ことです。

**bucket の概念:**

- **best_hands** (相対強さ上位 25%): 自分のハンドは相手のレンジに対して **強い側 25%** に入る
- **good_hands** (上位 25-50%): やや強い側
- **weak_hands** (下位 25-50%): やや弱い側
- **trash_hands** (下位 25%): 弱い側

これは「絶対強さ (TP/2P など)」ではなく **「相手のレンジに対してどう位置するか」** という相対判断です。

実戦中の bucket 推定は経験で慣れますが、ざっくり以下で考えます:

- **set+ / straight / flush** は基本 best_hands
- **TPTK / overpair** は best_hands or good_hands
- **TP weaker kicker / 2nd pair** は good_hands or weak_hands
- **3rd pair / underpair / A-high** は weak_hands
- **no_made_hand** は trash_hands

### River 守備の重要例外

ch04 標準マトリックスに加えて、River では以下のパターンが特に重要です。

**例外 1: dynamic board × TP/2P (weak_hands bucket) × overbet → CALL (bluff catch)**

標準マトリックスでは W × o = FOLD ですが、River の dynamic board に限り「TP/2P + overbet → CALL」を推奨します。

理由: dynamic board で相手が overbet を打つのは completed draws (made flush, made straight) または完全 bluff のどちらかが主体。busted draws が bluff range に多いため、TP/2P の bluff catcher で十分 +EV になります。

**例外 2: dry board × TP × overbet → CALL (bluff catch)**

dry board (K-7-2-3-5 など、draws complete なし) で相手が overbet を打ってきたら、相手のバリューは限定的 (sets, AK の TPTK) で、bluff range が広い → **TP で CALL** が +EV。

**例外 3: straight / flush / trips (絶対強さ) → bucket 関係なく CALL**

straight や flush は相手の通常レンジに対してほぼ確実に勝つ絶対強さ。「bucket では weak だが絶対強さでは強い」というケースで、bucket を無視して **CALL** が正解。

**例外 4: 真の all-in (raise 不可) でも CALL の閾値が下がる**

相手が all-in (raise option なし) を打ってきた場合、こちらは call か fold の二択。
- **eqp > 65%** (簡易的に「ベター 25% の中の中位以上」) なら CALL
- それ以下は FOLD

※ これは Vol3 で詳説する高度な判断。本書では「ナッツ近辺は CALL、それ以外は基本 FOLD」で十分。

## River 守備マトリックス例

**River 守備のセル別 (簡易版)**

| ハンド強さ \ サイズ | s (≤33%) | m (50-75%) | l (≈100%) | o (≥150%) |
|---------------------|----------|------------|-----------|-----------|
| **S** (set+/straight/flush) | RAISE (med 100% 以下) | CALL | CALL | CALL |
| **S** (overpair) | RAISE | CALL | CALL | CALL |
| **M** (TP) on dry | CALL | CALL | CALL | **CALL (bluff catch)** |
| **M** (TP) on dynamic | CALL | CALL | **CALL (bluff catch)** | FOLD or **CALL** |
| **M** (2nd/3rd pair) | CALL | CALL | FOLD | FOLD |
| **W** (A-high, low pair) | CALL | CALL | FOLD | FOLD |
| **A** (no_made) | CALL or FOLD | FOLD | FOLD | FOLD |

標準マトリックスと比べると **TP の bluff catch 閾値が高くなっている** のが分かります。これは River で相手の overbet レンジが polarized になっているため、bluff catcher として TP が機能しやすいからです。

## 実戦例: River の判断

**例 1: River K-7-2-3-A (dry) でこちらは A♠T♠ (TP-A、A pair on river)、相手が overbet 200% pot**

ハンド強さ判定: TP on dry → **M (Medium)**、ただし TP + dry × overbet は **CALL (bluff catch)** ルール適用。

1. マトリックス参照 → M × o (overbet) = 標準で **FOLD**
2. River 例外 2 適用: dry + TP + overbet → **CALL**
3. **アクション: CALL**

理由: dry board で相手が overbet するなら、busted draws の bluff が多い (T-9 のような OESD で straight 完成せず)。A pair の TP で十分 bluff catch できる。

**例 2: River T-9-8-2-A (dynamic) でこちらは A♠T♠ (TP-A)、相手が overbet 150% pot**

ハンド強さ判定: TP on dynamic = **M**

1. マトリックス参照 → M × o = 標準で **FOLD**
2. River 例外 1 適用: dynamic + TP + overbet → **CALL** (bluff catch)
3. **アクション: CALL** (bucket-based の判断、相手の overbet bluff range あり)

ただし dynamic で TP の bluff catch は dry より難しい (相手の straight が完成している可能性)。実際の頻度は CALL/FOLD 半々で迷う場面。**本書ではマトリックス例外通り CALL を推奨**。

**例 3: River で straight を持っている、相手が overbet**

ハンド強さ判定: straight = **S (Strong)**

1. マトリックス参照 → S × o = **CALL** (RAISE は raise option がない場合除く)
2. **アクション: CALL**

もし相手の bet がまだ overbet ではなく、raise option がある場合は **RAISE** も検討。具体的には:
- **bet が 100% pot 以下** で straight on dynamic → **RAISE for value**
- **bet が overbet/all-in** → **CALL** (raise の余地が少ない、または相手が更に強い可能性)

## 次の章へ

River の特殊性 (polarization、bucket、bluff catch) を学びました。次は **ch08 練習問題** で全マトリックスを反射的に使えるかを自己診断します。
