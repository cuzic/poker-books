# 第15章 Turn Donk Lead — BB が turn で先制する戦略

Vol2 のマトリックスでは BB は自分のターンが来たら「check 後の相手の bet を待つ」が default でした。
しかし GTO 検証によれば、**MTT 100bb の BB は turn で 16% donk lead する** (Cash 100bb は 5%)。
本章では polarized donk と semibluff donk のパターン、ポジション・ボード・depth による差異を解説します。

## 「Donk bet」とは

Donk bet (ドンクベット) は、**preflop で aggressor でなかった OOP プレイヤーが、次のストリート開始時に先制 bet を打つ行為** です。

**典型的なシナリオ:**

- Preflop: BTN open 2.5x → BB call (BB は call で受け身)
- Flop: BB check → BTN cbet → BB call (BB は check-call で受け身)
- **Turn: BB lead (donk)** ← ここが donk

BB は flop で受け身だったのに、turn で先制する → **「IP (BTN) のラインを乱す」** 効果があります。

古典的なポーカー戦略では「donk は弱者の手」と忌避されましたが、**modern GTO は polarized donk** を最適戦略として推奨します。

## Depth × board family 別 donk 頻度

**BB Turn donk 頻度 (全体平均)**

| Scenario | 全体 donk % | paired | dynamic | dry_high |
|----------|-------------|--------|---------|----------|
| Cash 100bb | 5.2% | **16.8%** | 0.0% | 4.8% |
| MTT 25bb | 1.5% | 0.2% | 4.1% | 0.1% |
| MTT 50bb | 5.3% | 8.2% | 5.6% | 4.1% |
| **MTT 100bb** | **16.0%** | (高) | 14.4% | 16.8% |

**重要な発見:**

- **MTT 100bb の Turn donk が圧倒的に高い (16%)** — Cash 100bb の 3 倍
- **Cash 100bb の paired turn で 16.8% donk** — paired board の特殊性
- **MTT 25bb はほぼ donk しない (1.5%)** — short stack で donk は coordination 必要

なぜ MTT 100bb で donk が多いのか?

- **MTT 100bb の Flop cbet は EP で 80%+, BTN で 65%** (前章) — Flop で BB はかなり広く defend している
- Turn で IP が check すれば、BB の range は依然 polarized → donk で polarization を活用

## ハンド別 donk パターン (Cash 100bb)

**Cash 100bb BB Turn donk 頻度 by mv**

| mv_cat | donk % (BET-modal) | n |
|--------|--------------------|---|
| **fullhouse** | **32%** | 262 |
| **underpair** | 15% | 96 |
| **set** | 9% | 102 |
| **no_made** | 9% | 3418 |
| **king_high** | 5% | 828 |
| **trips** | 5% | 414 |
| **A-high** | 4% | 1764 |
| **TP** | 3% | 1113 |
| **3rd pair** | 4% | 903 |
| **2nd pair** | 0% | 1139 |
| **low_pair** | 0% | 975 |
| **straight** | 0% | 817 |
| **2P** | 0% | 455 |

**観察:**

- **fullhouse 32% donk** — board が paired + over でフルハウス完成、絶対的に強いので donk for value
- **underpair 15%** — ポケットペアでフロップ受け身、turn で表現
- **no_made 9%** — air の bluff donk (low frequency)
- **2P/straight 0%** — 強すぎて check-raise の方が EV 高い

**polarized donk pattern:**

```
BET レンジ:
  - 確定 nuts (fullhouse, quads)
  - bluffs (no_made, K-high)

CHECK レンジ:
  - 強すぎる (straight, 2P) → check-raise 狙い
  - 中程度 (TP, 2nd/3rd pair) → showdown 維持
  - 弱すぎる (low_pair) → check-fold or check-call
```

## 重要な訂正: 「polarized」は不正確

ポーカー古典理論では Turn donk = "value + bluff polarized" と言われますが、
GTO 検証データ (MTT 100bb, 18.9k 行) は **より複雑な構造** を示します。

**MTT 100bb donk 頻度 by mv 強さ**

| カテゴリ | mv | donk % | 戦略意味 |
|--------|----|---------|--------|
| **Nuts** | fullhouse | **45%** | VALUE donk |
| **Nuts** | trips | **52%** | VALUE donk |
| **Strong slowplay** | straight | 10.5% | CHECK 主体 (CR/trap) |
| **Strong slowplay** | set | **5%** | CHECK 主体 (slowplay) |
| **Strong slowplay** | 2P | 5.8% | CHECK 主体 |
| **Medium balance** | TP | 14.2% | mix |
| **Medium balance** | 2nd pair | 14.8% | mix |
| **Medium balance** | 3rd pair | 17.2% | mix |
| **Special** | underpair | **36.7%** | 反直感 (overpair-like value) |
| **Weak/Air** | A-high | 18.2% | bluff balance |
| **Weak/Air** | K-high | 12.9% | bluff balance |
| **Weak/Air** | no_made | 17.3% | bluff balance |

**真の Modern GTO Donk Strategy:**

1. **Nuts (fullhouse, trips) → VALUE donk** (45-52%)
2. **Strong-but-not-nuts (set, straight, 2P) → CHECK で slowplay** (5-10%)
3. **Medium (TP, 2nd/3rd pair) → CHECK balance** (14-17%)
4. **Underpair → donk 多 (反直感)** (37%) — overpair-like で value donk
5. **Air (A-high, K-high, no_made) → CHECK balance + 少数 bluff donk** (12-18%)

古典の「value + bluff polarized」と違い、**強さ中間の "strong slowplay" 帯**が存在します。これは modern solver 特有の発見です。

「set/straight で donk しない」は「これらを check して BTN にバレル続けてもらう」 = trap 戦略。Vol3 ch04 (MTT Turn defense) の "best/good × overbet → RAISE" と整合します (BTN がオーバーベットしてきたら、BB は強ハンドで RAISE = check したからこそ pot 大きくできる)。

## MTT 50bb donk パターン (Top 10 cell)

**MTT 50bb BB Turn donk top cells (cell-level)**

| # | mv × dv × board | donk % | n |
|---|------------------|--------|---|
| 1 | quads × no_draw × paired | **55%** | 52 |
| 2 | no_made × FD × dry_high | **38%** | 48 |
| 3 | king_high × gutshot × dynamic | **37%** | 192 |
| 4 | fullhouse × no_draw × paired | 24% | 435 |
| 5 | overpair × no_draw × dry_high | 20% | 90 |
| 6 | king_high × no_draw × paired | 20% | 580 |
| 7 | overpair × gutshot × dynamic | 14% | 42 |
| 8 | no_made × no_draw × dynamic | 13% | 1936 |
| 9 | trips × no_draw × dry_high | 12% | 480 |
| 10 | low_pair × no_draw × dynamic | 12% | 894 |

**興味深いパターン:**

- **quads × paired**: 55% donk (絶対 nuts) — full-line value extraction
- **no_made × FD × dry_high**: 38% donk (semibluff) — turn で FD 完成しないと bluff
- **king_high × gutshot × dynamic**: 37% donk (semibluff with blocker) — K blocker で fold 引き出し

**共通テーマ: polarized donk = nuts または bluff candidate**

中程度のハンド (M = TP, 2nd pair) は donk しない。これは Vol2 の attack マトリックスとも一致 (S と A だけが BET、M は CHECK)。

## donk size の意味

Donk のサイズも重要なシグナルです。

**Cash 100bb の typical donk size:**

- **small (25-33% pot)**: 弱い donk → IP は wider continue
- **medium (50-67% pot)**: 標準 donk
- **overbet (100%+)**: polarized donk (nuts or bluff)

MTT 50bb では:

- Turn pot が小さい (~9 BB) ので、small donk = 2-3 BB
- Overbet donk = 10+ BB (commit 寄り)

**実戦的なガイド:**

自分が donk する場合:
- **fullhouse / quads** → overbet donk (commit 寄り)
- **semibluff (FD/OESD on dry)** → medium donk
- **bluff (K-high blocker)** → small-medium donk
- **その他 (TP, 2P, etc.)** → check (Vol3 ch07 通り)

## BB donk への対応 (IP defense)

BB が turn で donk してきたら、IP (BTN) はどう対応するか?

Donk lead は **polarized signal** なので:

- **small donk (≤33% pot)**: BB の range は中程度〜weak、IP は標準的に call/raise
- **medium donk (50-75%)**: BB の range は polarized (value + bluff)、IP の strong made hands は call
- **overbet donk (100%+)**: BB の range は **nuts + bluff 二極化** → IP の TP/2P でも fold 寄り、強い made (set+) のみ continue

**IP の対応 default:**

- 自分の M (TP) で donk 受けたら、サイズ次第で call (small) or fold (overbet)
- 自分の S (set+, 2P+) で donk 受けたら call、raise option もあるが pot odds 重視で call が安全

これは Vol3 ch04 の MTT 50bb Turn defense 公式とほぼ同じ判断軸 (bucket-based)。

## ポジション別 donk 頻度 (理論予測)

本書のデータは「BB が donk」に集中しています (BTN open vs BB call 想定)。他のポジションの donk 頻度はデータ不足ですが、理論的に予測できます:

- **SB call vs BTN open** での SB donk: BB donk より低い (~5% vs 16%、SB は overall passive)
- **BB call vs CO open** での BB donk: ほぼ同じ (BTN と CO の open range が似ているため)
- **BB call vs EP open** での BB donk: BB donk より低い (EP range が strong で BB の polarization 弱い)

実戦的には:

- **BTN/CO open vs BB call** → Turn donk は normal (5-16%)
- **EP open vs BB call** → Turn donk は rare (3-5%)
- **SB call vs BTN open** → SB donk は rare (3-5%)

## 実戦例: Turn donk の判断

**例 1: Cash 100bb で BTN open vs BB call、K-7-2 flop、BTN cbet, BB call、turn 2 (paired)**

ボード: K-7-2-2 (paired turn)
BB の hand: 2♣2♥ (quads on river potential, currently 222 trips)

- mv = trips on paired turn → **fullhouse 候補**
- Turn donk patterns: fullhouse 32% donk in Cash 100bb
- **アクション: donk (medium 50-67% pot)** as polarized value
- サイズ: 50% pot で IP の continue range を広く取る

**例 2: MTT 50bb で K-7-2-5 (turn 5、4-flush 可能性), BB の hand: A♣J♣ (no_made + FD)**

- mv = no_made, dv = flush_draw
- Board: dry_high (K-7-2-5、最後の card が brick)、ただし 4-flush 可能性なし (suits 分散)
- Donk pattern: no_made × FD × dry_high で 38% donk
- **アクション: donk small** (semibluff, fold equity + draw equity)

**例 3: MTT 100bb で T-9-8-2 (dynamic turn), BB の hand: K♣Q♠ (gutshot + 2 over)**

- mv = king_high, dv = gutshot
- Board: dynamic
- Donk pattern: king_high × gutshot × dynamic で 37% donk
- **アクション: donk medium** (bluff with blocker)
- K blocker で BTN の AKx (TPTK) を fold させる効果 + gutshot で hit したら ナッツ straight

## Vol2 マトリックスへの統合

Vol2 の attack マトリックスは「自分が動く番のアクション」を扱いますが、**donk は実質「Turn 自分が先手の attack」** です。

Vol2 の Turn attack マトリックスを思い出すと:

```
Turn attack: 常に CHECK (Vol2 ch03)
```

これは IP の場合の話。**OOP (BB) の Turn donk は別の判断軸が必要**。

Vol3 の理解で Vol2 マトリックスを拡張すると:

```
Turn attack:
  IP: 常に CHECK (Vol2 通り)
  OOP (donk):
    fullhouse / quads → BET (value)
    no_made + FD/OESD (semibluff) → BET 30%+
    K-high + blocker (bluff) → BET 30%+
    その他 → CHECK
```

この「OOP donk 戦略」を Vol2 ユーザーが知ると、turn でより多くの EV を取れます。

## まとめ

Turn donk lead は以下のパターン:

- **polarized**: nuts (fullhouse) + bluffs (K-high, semibluff)
- **paired turn で活発化** (range advantage shift)
- **MTT 100bb で 16% と最頻** (Cash 100bb の 3 倍)
- **MTT 25bb はほぼ donk なし** (short stack の coordination 困難)

実戦的には:

- 自分が BB で turn を見た → **fullhouse/quads → donk**, **semibluff (FD/OESD on dry) → donk**, **K-high bluff → donk**, **それ以外 → check**
- 自分が IP で BB の donk を受けた → **size に応じて Vol2/Vol3 マトリックスで対応**

## 次の章へ

Turn donk を学びました。次の ch16 では **3-bet pot の詳細** を扱います。既存の defense_study findings から導出された「IP のトラップ戦略」「OOP の強気 CR」「トリップス挙動の逆転」などの重要パターンを解説します。
