# UCBS-v2 + DCBS 最終仕様 (17 contexts)

最終更新: 2026-05-28
データ source: GTO Wizard API (MTT6mSimple / Cash6mGeneral_6mNL25R25)
合計 fetch: 約 1,000+ spots

---

## 全 context 一覧

### UCBS-v2 (攻撃: cbet 13 contexts)

| Tier | Context | シナリオ | WRMSE | 用途 |
|---|---|---|---:|---|
| 0 | **cash_100bb** | Cash IP cbet | 16.43% | キャッシュ標準 |
| 0 | **mtt_25bb** | MTT 終盤 cbet | 15.46% | push 圏直前 |
| 1 | **mtt_50bb** | MTT 中盤 cbet | **12.96%** | バブル前 |
| 1 | **mtt_100bb** | MTT 序盤 cbet | 21.95% | start ※精度低 |
| 1 | **mtt_200bb** | MTT 深 cbet | 14.10% | FT 直後 |
| 3 | **mtt_3bp_20bb** | 3BP IP 浅 cbet | 23.08% | 終盤 3-bet pot |
| 3 | **mtt_3bp_25bb** | 3BP IP 浅 cbet | 18.65% | 同上 |
| 3 | **mtt_3bp_50bb** | 3BP IP 中 cbet | **8.62%** | ★ 最高精度 |
| 3 | **mtt_3bp_100bb** | 3BP IP 深 cbet | 13.37% | 序盤 3-bet pot |
| 4 | **mtt_25bb_turn_btn** | Turn 2nd barrel | **7.02%** | ★ 終盤 turn |
| 4 | **mtt_50bb_turn_btn** | Turn 2nd barrel | 14.44% | 中盤 turn |
| 4 | **mtt_100bb_turn_btn** | Turn 2nd barrel | 26.95% | 序盤 turn ※精度低 |
| 4 | **cash_100bb_turn_btn** | Cash Turn 2nd barrel | 16.11% | Cash turn |

### DCBS (守備: defense 4 contexts)

| Context | シナリオ | WRMSE | 用途 |
|---|---|---:|---|
| **mtt_25bb** | BB defense vs cbet | 14.36% | 終盤 defense |
| **mtt_50bb** | BB defense vs cbet | 14.87% | 中盤 defense |
| **mtt_100bb** | BB defense vs cbet | 15.86% | 序盤 defense |
| **cash_100bb** | BB defense vs cbet | 17.17% | Cash defense |

---

## 構造の本質

### 共通テーブル (UCBS-v2)

**HP テーブル (16 hand → 6 バケット)**:

| HP | Hand types |
|---:|---|
| 2 | no_made_hand, ace_high, king_high, low_pair |
| 3 | underpair, third_pair |
| 5 | second_pair |
| 7 | top_pair, overpair |
| 8 | set, trips |
| 9 | two_pair, flush, straight, fullhouse, quads |

**DP テーブル (4 段階)**:

| DP | Draws |
|---:|---|
| 0 | no_draw, twocards_bdfd |
| 1 | gutshot |
| 2 | oesd, fd |
| 3 | combo_draw |

**base_freq (6 セル + 2 overbet 加算)**:

| 信頼度 | bet 寄り | check 寄り |
|---|---:|---:|
| HIGH | **70%** | **45%** |
| MID | **40%** | **30%** |
| LOW | **25%** | **25%** |

Overbet 例外 (size = 116): bet 寄りに HIGH +20, MID +15。

**ハンドカテゴリ (4 区分)**:

- **slowplay**: set, trips, two_pair, fullhouse, flush, straight, quads
- **trash**: low_pair
- **premium**: overpair, underpair
- **default**: それ以外

### Context per: α, β, slowplay, trash, premium + position lift + A-x lift

各 context は 5-8 数値で表現。

---

## 統一式

```
CBS = HP[hand] + DP[draw]
T = 5 (全 position 共通)
conf = bucket(|CBS - T|, board_type)
  + 型6 ボードなら信頼度を 1 段 up
  + mono ボードなら 1 段 down (cash のみ)
direction = (CBS >= T)
size = polarize_board(board) ? 116 : 33

freq = base_freq[(conf, dir, size)]
     + α
     + β · I(CBS ≥ 7)
     + offset[category]
     + pos_lift[position]
     + ax_range_lift (mtt BTN/CO + A-high paired/dry のみ)
```

---

## Tier 1 観察: スタック深さ系列

### MTT depth series パラメータ

| Param | 25bb | 50bb | 100bb | 200bb |
|---|---:|---:|---:|---:|
| α | +6 | -4 | **+15** | -4 |
| β (CBS≥7) | +31 | +19 | +9 | +11 |
| slowplay | -28 | -12 | -17 | -15 |
| trash | -23 | -35 | -19 | **-31** |
| premium | +15 | +20 | +8 | +14 |
| SB lift | -10 | -29 | -11 | -34 |
| wide lift | +13 | 0 | +17 | +1 |
| A-x lift | +30 | +11 | +28 | +9 |

**発見**:
- mtt_100bb のみ outlier (α=+15、wide lift=+17): MTT6mSimple tree の wide cbet 特性
- 50bb / 200bb は構造が似る: SB lift 強く負、wide lift ~0
- depth とともに β が低下 (浅は強い役 +31、深は +9-19)

---

## Tier 3 観察: 3BP IP depth series

### SPR が支配的

| Param | 20bb | 25bb | 50bb | 100bb | 解釈 |
|---|---:|---:|---:|---:|---|
| premium | -4 | -9 | +14 | +20 | 低 SPR は控えめ、深 SPR は強気 |
| trash | -3 | -44 | -45 | -48 | 浅は trash も bet、深は完全 fold |
| slowplay | -40 | **-66** | -40 | -33 | 25bb で最も slowplay 集中 |

**発見**:
- 低 SPR (≤25bb): linear range、middle hand も bet
- 深 SPR (≥50bb): polarize、強・air 偏重
- 50bb 3BP で **WRMSE 8.62%** (全 context 中最高)

---

## Tier 4 観察: Turn cbet 構造

### 「Flop → Turn」変換ルール

| パラメータ | Flop (mtt_25bb) | Turn (ほぼ全 context) |
|---|---:|---:|
| α | +0.06 | **-0.30 〜 -0.41** (全体 bet -35%) |
| β (CBS≥7) | +0.31 | **~0** (強い役の追加 lift 廃止) |
| slowplay | -0.28 | -0.27 (一定) |
| trash | -0.23 | -0.01 〜 -0.14 |
| premium | +0.15 | +0.08 〜 +0.32 |

**書籍ルール**: 「ターンに進んだら α を -35 シフト、β は廃止」

### 例外: 完成役 turn card

| Turn | WRMSE | 理由 |
|---|---:|---|
| 通常 turn | 3-5% | UCBS-v2 完璧適合 |
| KJT + Q | 28% | Q がストレート完成 |
| T98r + 7 | 19% | 7 がストレート完成 |

→ ストレート/フラッシュ完成 turn は別途特殊判定が必要。

---

## DCBS 観察: Defense は depth で反転

### Continue freq (BB が bet を call+raise する確率)

| 手 | mtt_25bb | mtt_50bb | mtt_100bb | cash_100bb |
|---|---:|---:|---:|---:|
| no_made_hand | 55% | 41% | **28%** | 37% |
| ace_high | 77% | 71% | **34%** | 45% |
| king_high | 68% | 60% | 34% | 40% |
| low_pair | 67% | 44% | **19%** | 38% |
| underpair | 100% | 100% | 94% | 84% |
| third_pair | 95% | 90% | 73% | 86% |
| second_pair | 99% | 96% | 87% | 98% |
| top_pair | 100% | 99% | 96% | 100% |

**発見**:
- **深いスタックほど air は fold** (mtt_100bb は air を 70% 以上 fold)
- 浅では range bet 多 + bet size 小 → wide call で対応
- 深では bet size 大 → 精選 call
- top pair 以上はどこでも 96% 以上 call (絶対 call)

### DCBS パラメータ (context 別)

| HP | mtt_25 | mtt_50 | mtt_100 | cash_100 |
|---:|---:|---:|---:|---:|
| 2 (air) | 67% | 54% | **28%** | 40% |
| 3 (弱 pair) | 98% | 95% | 84% | 85% |
| 5 (mid pair) | 99% | 96% | 87% | 98% |
| 7 (top pair+) | 100% | 99% | 98% | 100% |

### Kicker offset (HP=2 内の細分化)

| Hand | mtt_25 | mtt_50 | mtt_100 | cash_100 |
|---|---:|---:|---:|---:|
| ace_high | +10 | +17 | +5 | +5 |
| king_high | +1 | +6 | +5 | 0 |
| no_made_hand | -12 | -13 | 0 | -3 |
| low_pair | 0 | -10 | -10 | -2 |

→ 低スタックでは kicker 効果大 (差 22pt)、深スタックでは弱まる (差 6pt)

---

## 暗記対象 (合計)

### UCBS-v2 共通 (1 度暗記すれば全 context で使う)

| 項目 | 数値数 |
|---|---:|
| HP テーブル (16 hand → 6 バケット) | 6 |
| DP テーブル | 4 |
| base_freq (6 セル + 2 overbet) | 8 |
| カテゴリ 4 区分マッピング | — |
| **小計** | **18 数値 + 1 式** |

### UCBS-v2 context per (5-8 数値 × 13 context)

13 context × 平均 6 数値 = **~78 数値** (depth/SPR 表として暗記)

### DCBS

| 項目 | 数値数 |
|---|---:|
| DCBS_BASE (HP=2,3,5,7) × 4 context | 16 |
| Kicker offset (4 hand) × 4 context | 16 |
| **小計** | **32 数値** |

### 例外ルール (全 context 共通、3 ルール)

1. 型6 ボード (mid 連結ウェット) → 信頼度 1 段 up
2. mono ボード (3 同 suit) → 信頼度 1 段 down (cash のみ)
3. A-high paired/dry on MTT BTN/CO → +30 (range bet パターン)
4. (新) ターン進行 → α -35 シフト、β 廃止

### 合計

- UCBS-v2: 18 (共通) + 78 (context) = 96 数値
- DCBS: 32 数値
- **総計 128 数値 + 1 式 + 4 例外ルール**

これで cash + MTT の flop/turn cbet + flop defense を 1 つのフレームワークで予測可能。

---

## 達成精度

### WRMSE 分布

| 精度帯 | Contexts |
|---|---|
| < 10% (極良) | mtt_3bp_50bb (8.62%), mtt_25bb_turn_btn (7.02%) |
| 10-15% | mtt_50bb, mtt_3bp_100bb, mtt_25bb_turn_btn, cash_100bb_turn_btn, mtt_200bb, mtt_25bb (15.46%), DCBS mtt_25 (14.36%), DCBS mtt_50 (14.87%) |
| 15-20% | cash_100bb, mtt_3bp_25bb, mtt_3bp_20bb, DCBS mtt_100 (15.86%), DCBS cash_100 (17.17%) |
| 20%+ | mtt_100bb (21.95%), mtt_3bp_20bb (23.08%), mtt_100bb_turn_btn (26.95%) |

**平均 WRMSE ~16%** (cbet + defense 全体)。

### 構造的限界

WRMSE 20%+ の context (mtt_100bb 系) は **MTT6mSimple tree の wide cbet 特性**で UCBS-v2 構造が苦手。これは:
- Simple tree が分割少ない (33% / 116%) → polarize に振れる
- 100bb で特に振れ幅大

書籍では「**MTT 序盤 (100bb) は UCBS-v2 の信頼度低めの context、cash と MTT 中後盤 が安定**」と注記。

---

## 書籍化候補 (記事/本のヒント)

### 1 章想定: UCBS-v2 の式
- 主式の説明
- HP/DP/Confidence/Size の意味
- 例題で計算

### 1 章想定: context 表
- 13 context のパラメータ表
- depth/SPR/3BP/turn で何がどう変わるか
- 「**式は 1 つ、context で数値だけ変える**」の物語

### 1 章想定: defense (DCBS)
- 攻撃と対で defense モデル
- 「深いほど fold、浅いほど call」の発見
- MDF 理論との整合

### 1 章想定: 例外ルール
- 型6 ボード補正
- mono ボード補正
- A-x range bet
- Turn 進行 α シフト

### 1 章想定: 苦手領域と限界
- MTT 100bb の精度低問題
- ストレート完成 turn の特殊性
- 3BP shallow の linear range

---

## 関連ファイル

- 実装: `/home/cuzic/poker-books/cash-postflop/ucbs_v2.py` (13 context)
- 実装: `/home/cuzic/poker-books/cash-postflop/dcbs.py` (4 context defense)
- データ: `/home/cuzic/poker-books/mtt-postflop/findings/draw_study_*.jsonl`
- API ノート: `/home/cuzic/poker-books/scripts/gto_wizard_study/API_NOTES.md`
