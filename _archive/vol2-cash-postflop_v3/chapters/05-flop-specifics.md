# 第05章 Flop の特殊性 — board family と低ペア例外

Flop は最初の判断であり、相手のレンジも自分のレンジもまだ広い段階です。
この章では「board family による微調整」と「low_pair / 3rd_pair の特別な扱い」を学びます。

## Flop で意識すべき 4 つの board family

Flop の board (3 枚) は以下の 4 種類に分類できます。同じハンドでも board が違えば最適アクションが変わることがあるため、まず board family を読みます。

**4 つの board family**

| family | 特徴 | 例 |
|--------|------|-----|
| **dry_high** | high card (J 以上) + 連結なし + ペアなし | K-7-2 rainbow / A-9-4 rainbow |
| **low_dry** | low card (T 以下) + 連結なし | 8-4-3 rainbow / 9-6-2 rainbow |
| **dynamic** | 連結 3 枚 (straight 可能性高) または 2-tone+connect | T-9-8 rainbow / 7-6-5 two-tone |
| **paired** | ボードペアあり | K-7-2 with another K → K-K-7 |

monotone (3 枚同じスート) は本書では dynamic 扱いとします。

## 板タイプ別の戦略的意味

### dry_high (例: K-7-2 rainbow)

**特徴**: 連結なし、ペアなし、high card 1 枚

**両者のレンジ:**

- BTN (open) は high card や pocket pair で広く open、K-high は多く持つ
- BB (call) は high card や connector で広く defend、K-high は少ない

**戦略:**

- BTN は **range advantage** (high card 密度の優位) で small cbet 推奨
- BB は K-high には到底届かないので、low pair や mid pair でブラフキャッチが基本
- 守備マトリックスの W (low pair) は dry_high の medium/large bet に対してさらにタイトに (FOLD 寄り)

### low_dry (例: 8-4-3 rainbow)

**特徴**: low card のみ、連結なし

**両者のレンジ:**

- BTN の hand range は high card 中心なので、low_dry でヒットしにくい
- BB は wider range で defend、low_dry とも connect しやすい (8-4 のような combo)
- **レンジ的には BB がやや有利**

**戦略:**

- BTN の cbet は減る (range disadvantage)
- BB は積極的にコール、たまに check-raise も
- 守備マトリックスは大きく変わらないが、**low pair on low_dry は通常 CALL** (top pair 扱いに近い)

### dynamic (例: T-9-8 rainbow / 7-6-5 two-tone)

**特徴**: 連結 3 枚、straight 可能性高、draws 多い

**両者のレンジ:**

- 両者とも middling cards で多く hit
- **draws (OESD, FD) が多い** ためボラタイル
- レンジ的には拮抗

**戦略:**

- cbet 頻度は両者で小さくなる傾向 (check が多くなる)
- **draws (D) の優先度が上がる** — 守備マトリックスで D × m は CALL、D × o (overbet) は FOLD
- top pair は実は弱い (straight draws やフラッシュドローに負ける)
- 守備マトリックスの M × dynamic では追加のタイト化を検討 (ch06 Turn で詳説)

### paired (例: K-K-7 / 7-7-2)

**特徴**: ボードペアあり、相手のトリップス警戒

**両者のレンジ:**

- **BTN は K のキッカーを多く持つ** (KQ, KJ など) → 強い K のキッカーで TPTK 相当
- **BB は K のキッカーが少ない** → トリップスはあるが K のキッカーは弱い

**戦略:**

- BTN は small cbet で攻めやすい (相手は full house を作れないので overpair 強い)
- BB は K kicker 持ちで bluff catch、K-high の値はそこまで強くない (K-7 のような完全な top kicker 以外)
- **K-high + paired board の組み合わせは BTN が BET、BB は call** という polarized 形

## ch04 守備マトリックスの Flop 補正 (3 つの重要ルール)

ch04 の標準マトリックスに、Flop では以下の 3 つの補正を加えます。これら 3 つを覚えるだけで、huge_gap loss が **49% → 84% 削減** に跳ね上がります (GTO 検証済み)。

### 補正 1: W (low_pair / 3rd_pair) × no_draw × dry/dynamic_2tone → FOLD

標準マトリックスでは W × m は CALL ですが、Flop の dry 板ではタイト寄りに修正します。

理由: dry_high (K-7-2 など) や dynamic_2tone (T-9-8 with 2 same suit) では、
- 相手のレンジは high card 中心
- こちらの 22 や 33 のような low_pair はキッカーが極端に弱く、ほぼ確実に負け
- 安く showdown を見ても勝てない

### 補正 2: A-high / K-high × no_draw → FOLD (Flop 上の重要例外)

Vol2 ch01 では A-high / K-high を **W (Weak)** に分類しましたが、**Flop に限り A (Air) 扱いで FOLD** にします (River では W のままで bluff catch)。

理由: Flop の cbet を受けた段階で、こちらの A-high には引きしろがない (TP まで 3 outs)。BTN の cbet range は high card 中心で、こちらの A-high はほぼ確実に負け。安く showdown を見ても勝てない。

この補正だけで **huge_loss が 1.0-1.4 BB/decision 削減** されるセル (king_high × dry_high など) が大量にあり、最大の改善要因です。

### 補正 3: overpair → RAISE

標準マトリックスでは S × m = CALL (slowplay) ですが、overpair に限り **RAISE で value 取り** に行きます。

理由: overpair (AA, KK on T-7-2) は **range advantage** を持つので、turn で逆転されるリスクを下げるために RAISE で commit。set/2P 等は依然 CALL (slowplay) で OK。

### 3 補正の合計効果

- **補正 1 単独**: huge_gap loss 約 49% → 52% (微増)
- **補正 2 (A/K-high → A) 追加**: 52% → **84%** (主要因)
- **補正 3 (overpair RAISE) 追加**: 84% → 84% (ほぼ寄与なし)

**したがって Flop 補正 1+2 の組み合わせが本書の Flop defense の核心** です。

**補正 2: その他は標準マトリックス通り**

flop の他の補正は本書 (簡易版) では扱いません。Vol3 で詳説します。

## 実戦例: Flop の判断フロー

具体的なフロップで判断フローを練習します。

**例 1: K-7-2 rainbow (dry_high) で AKo (TP top kicker) を持っている、相手が cbet 33% (m)**

1. ハンド強さ判定 → AKo on K-7-2 = TP + AK kicker → **M (Medium、TPTK)**
2. サイズ判定 → 33% pot = **m** (medium、本書では 33% は s と m の境界、ここでは標準 m と扱う)
3. マトリックス参照 → M × m = **CALL**
4. Flop 補正適用 → なし (M は補正対象外)
5. **アクション: CALL**

**例 2: K-7-2 rainbow で 22 (low_pair) を持っている、相手が cbet 33%**

1. ハンド強さ判定 → 22 on K-7-2 = ボトムペア → **W (Weak)**
2. サイズ判定 → **m** (medium)
3. マトリックス参照 → W × m = **CALL** (標準)
4. Flop 補正適用 → W × no_draw × dry_high → **FOLD** (補正 1 適用)
5. **アクション: FOLD**

**例 3: T-9-8 rainbow (dynamic) で T♣9♣ (TP + OESD) を持っている、相手が cbet 50% (m)**

1. ハンド強さ判定 → T-9 on T-9-8 = top pair + 2nd pair = **2P** → **S (Strong)** (実は 2P over の TPTK)
   - 注: TP + open-ender だが優先は 2P (より強い役)
2. サイズ判定 → 50% = **m**
3. マトリックス参照 → S × m = **CALL**
4. **アクション: CALL** (RAISE も検討可だが simple ruleでは CALL)

## boardの読み — paired/monotone の例外

**paired board** で自分が K-high (kicker のみ) を持っている特殊ケース:

- 通常 K-high は W だが、paired board では K-K-2 のような場合、K-high kicker は実質ほぼ「TP」と同等の強さ
- 守備マトリックスでは W ではなく **M (Medium)** として扱う
- これは攻撃側 ch03 の 7 BET セルの 1 つにも対応 (W kicker × paired → BET)

**monotone board** (3 枚同スート) で自分が high card のフラッシュ:

- 通常 flush は S だが、monotone board では「nut flush 以外は注意」
- A♥ のキッカーがある A-high flush なら S、それ以外は M 扱いも検討

ただしこれら細かい例外は本書では深追いせず、Vol3 で詳説します。本書の中核は「標準マトリックス + 1 つの Flop 補正 (low_pair on dry → FOLD)」だけです。

## 次の章へ

Flop の判断ができるようになりました。次は Turn (ch06) で「slowplay 全面採用」と「overbet vs draws」を学びます。
