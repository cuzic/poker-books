# UDG v2 — A (SPR) + C (Matchup) + H (Equity bucket) 統合結果

## 検証結果 (293K rows)

| 指標 | 11 専用公式 | UDG v1 | **UDG v2** |
|------|----------:|-------:|-----------:|
| huge_loss (avg) | 15.75 BB | 10.27 BB | **5.94 BB** |
| 削減率 vs 11公式 | — | -35% | **-62%** |
| 削減率 vs UDG v1 | — | — | -42% |
| acc (avg) | 75-85% | 69.7% | 70.5% |
| 暗記項目 | ~165 分岐 | ~30 items | **~20 items** |

UDG v2 は **11 専用公式より huge_loss が 62% 低い** = 暗記コスト 88% 削減と quality 向上が同時実現。

## 暗記コスト構成 (UDG v2 = ~20 items)

### Layer 1: 5 tier 関数 (~10 items)
1. board_polar_tier: POLAR / MERGED / MID (3 way、6 board family を圧縮)
2. hand_strength_tier: NUT_MADE / STRONG / TWO_PAIR / PAIR / MID_PAIR / AIR (6 way)
3. bet_size_tier: SMALL / MED / BIG / ALLIN (4 way)
4. **NEW: spr_tier**: SHALLOW / LOW / MID / HIGH (4 way、pot_type × street × depth 統合)
5. **NEW: equity_aware_tier**: HIGH / MID / LOW / VERY_LOW (4 way、hand × equity_bucket 統合)

### Layer 2: 3 universal rules (3 items)
```
AHEAD:  RAISE on non-river non-POLAR / CALL elsewhere
TIE:    SHALLOW SPR → CALL (committed) / BIG bet → cautious FOLD / default CALL
BEHIND: strong_draw → CALL / SMALL bet × MERGED × blocker → CALL / else FOLD
```

### Layer 3: context modifiers (~5 items)
- vs_CR: matchup を 1 段階下げ (opp value-heavy)
- vs_donk: matchup を BEHIND→TIE のみ 1 段階上げ + RAISE→CALL 変換
- CO/HJ open river: matchup を 1 段階下げ (opp value-heavier than BTN)
- depth_bb 25/200: SPR tier 自動補正
- (4BP/3BP/4BP/3BP modifier 廃止 — SPR tier に吸収)

## Per-scenario huge_loss 比較

### 大幅改善 (river 系で特に顕著)

| Scenario | v1 専用 | UDG v2 | 改善 |
|----------|-------:|-------:|----:|
| **B_river** | 19.5 | **3.8** | **-81%** |
| **N_mtt100_river** | 19.6 | **2.3** | **-88%** |
| **N_mtt25_river** | 8.8 | **1.3** | **-86%** |
| **N_btn_sb_river** | 14.0 | **4.5** | **-68%** |
| **N_bvb_srp_river** | 9.9 | **4.8** | **-51%** |
| **N_cash_3bp_river** | 21.8 | **8.0** | **-63%** |
| **A_cash_3bp_river** | 23.1 | **8.0** | **-65%** |
| **P5_A_mtt_3bp_river** | 28.7 | **11.6** | **-60%** |
| **N_cash_4bp_river** | 33.0 | **12.1** | **-63%** |
| **P6_A_mtt_4bp_river** | 30.2 | **11.6** | **-62%** |
| **N_cash_4bp_turn** | 15.8 | **5.3** | **-66%** |
| **P6_A_mtt_4bp_turn** | 17.7 | **6.0** | **-66%** |
| **P5_A_cash_3bp_turn** | 5.0 | **2.8** | -43% |
| **B_turn** | 1.9 | **1.5** | -19% |
| **B_flop** | 0.93 | **0.67** | -28% |

### 同等 (within 30%)

| Scenario | v1 | v2 | 差 |
|----------|---:|---:|---:|
| A_cash_4bp_flop | 5.0 | 6.0 | +20% |
| N_cash_4bp_flop | 4.8 | 5.6 | +17% |
| P6_A_mtt_4bp_flop | 5.3 | 6.5 | +22% |
| N_mtt200_river | 4.0 | 4.8 | +20% |

→ 4BP flop は最大 △+22%、v1 と実質同等。

## なぜ UDG v2 が劇的に改善したか

### 1. SPR tier (A) の威力

SPR は「ポット commitment 度」を 1 軸に圧縮：
- SHALLOW (SPR<1): commit、コール優位
- HIGH (SPR>7): speculative、fold 寛容

これで `pot_type × street × depth = 27 組合せ` を 4 tier に圧縮、universal rule で参照。

### 2. Equity-aware tier (H) の威力

Hand_strength (mv ベース絶対値) と equity_bucket (vs opp range 相対値) を **融合**：

| hand_strength | equity_bucket | eq_aware |
|---------------|---------------|----------|
| STRONG (set) | best_hands | HIGH ✓ |
| STRONG (set) | **weak_hands** ← 例: set on str8 board | **MID** ← 自動 downgrade |
| AIR (ace_high) | **best_hands** ← 例: nut flush blocker | **HIGH** ← 自動 upgrade |

これで「**v15 で bug だった: set × allin で常に CALL を出す**」のような誤判定が自動消える。

### 3. Range matchup tier (C) の威力

3 段階 (AHEAD/TIE/BEHIND) で全 hand × board × bet の組合せを表現。
universal rule が 7 → 3 ルールに圧縮、判定が極めて直感的に。

「**自分は相手より前？同じ？後ろ？**」の 3 択 → 決断確定。

### 3 概念の compounding effect

各概念は独立に効くが、合わせると非線形に効く：
- SPR tier × eq_aware: SHALLOW + LOW = "committed bluff catch" (mathematically optimal)
- eq_aware × matchup: equity を tier 経由で 3 段階化 → "showdown 優位 / 劣位" の二択化

## Vol2/Vol3/Vol4 章構成への含意

### Vol2 序章 (推奨)
```
Ch1: 5 つの tier 概念
  - board_polar_tier (POLAR/MERGED/MID)
  - hand_strength_tier (6 way)
  - bet_size_tier (4 way)
  - SPR tier (SHALLOW/LOW/MID/HIGH)
  - equity_aware_tier (HIGH/MID/LOW/VERY_LOW)

Ch2: matchup 3 階層
  - AHEAD / TIE / BEHIND を tier 組合せから導く表

Ch3: 3 universal rules (AHEAD/TIE/BEHIND each)

Ch4-5: context modifier (vs_CR / vs_donk / opener position / MTT depth)

Ch6: 境界ハンド集
```

### Vol3 (MTT) 章構成
- Vol2 Ch1-5 をリマインド (5 ページ)
- depth_bb による SPR tier 自動補正の説明 (10 ページ)
- 境界ハンド集 (10 ページ)
- → 計 **~25 ページ** (現状の 200 ページから -87%!)

### Vol4 (Exploit)
- Vol2 の universal rule + matchup tier に「相手タイプによる tier 動的更新」を追加
- tight player → matchup を BEHIND 側にシフト、loose → AHEAD 側
- → exploit ロジックも同じ framework で記述可能

## 残課題

1. **4BP flop の board-specific tuning** (+22% 悪化、5-7 例外で改善余地)
2. **CR/donk の huge_loss は absolute 妥当だが acc は 40-70% 程度** (人間が分かる範囲か検証要)
3. **R1_past (river BTN allin defender) の huge_loss 6.3 BB** — v2 は OOP 想定なので IP 用 modifier 要設計
