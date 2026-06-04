# Full UCBS-v2 公式——書籍向け整形版

作成日: 2026-05-28
ソース: UCBS_V2_DCBS_FINAL.md (2026-05-28) / vol2-cash-postflop/ucbs_v2.py
用途: Vol3 ch01-ch05 / 付録 A の執筆 source

---

## 1. 統一式

```
CBS = HP[hand] + DP[draw]          # 足し算だけ

T = 5                               # 全 context / 全ポジション共通閾値

conf = bucket(|CBS - T|, board_type)
  ↑ 型6 ボードなら信頼度を 1 段 up (LOW→MID / MID→HIGH)
  ↑ mono ボードなら 1 段 down (cash のみ、HIGH→MID / MID→LOW)

direction = (CBS >= T)             # true = bet 寄り、false = check 寄り

size = polarize_board(board) ? 116 : 33
  ↑ polarize_enabled=True は cash_100bb のみ。MTT は常に 33。

freq = base_freq[(conf, dir, size)]
     + α                           # context uniform lift
     + β · I(CBS ≥ 7)             # 強い役帯の追加 lift
     + offset[category]           # 役柄カテゴリ補正
     + pos_lift[position]         # ポジション補正
     + ax_range_lift               # A-x range bet (MTT BTN/CO のみ)

freq = clamp(freq, 0.02, 0.98)
```

---

## 2. HP テーブル（16 hand → 6 バケット）

| HP 値 | 手の種類 |
|---:|---|
| 2 | no_made_hand, ace_high, king_high, low_pair |
| 3 | underpair, third_pair |
| 5 | second_pair |
| 7 | top_pair, overpair |
| 8 | set, trips |
| 9 | two_pair, flush, straight, fullhouse, quads |

**暗記のポイント**: 2 / 3 / 5 / 7 / 8 / 9 の 6 値。閾値 T=5 を挟んで「5 以下 = check 寄り、5 超 = bet 寄り」が基本方向。

---

## 3. DP テーブル（4 段階）

| DP 値 | ドローの種類 |
|---:|---|
| 0 | no_draw, twocards_bdfd |
| 1 | gutshot |
| 2 | oesd, fd（フラッシュドロー） |
| 3 | combo_draw（oesd + fd など） |

**特例（Air Paradox）**: no_made_hand + oesd → CBS = HP - 2（強いドローだが役なしの矛盾を補正）。

---

## 4. BASE_FREQ テーブル（6 セル + 2 overbet 加算）

| Confidence | Direction | Size | base_freq |
|---|---:|---:|---:|
| HIGH | bet (true) | 33% | **68%** |
| HIGH | bet (true) | 116% | **89%** |
| HIGH | check (false) | 33% | **46%** |
| HIGH | check (false) | 116% | 44% |
| MID | bet (true) | 33% | **40%** |
| MID | bet (true) | 116% | **55%** |
| MID | check (false) | 33% | **33%** |
| MID | check (false) | 116% | 30% |
| LOW | bet (true) | 33% | **25%** |
| LOW | bet (true) | 116% | 27% |
| LOW | check (false) | 33% | 30%* |
| LOW | check (false) | 116% | 28%* |

*LOW + check はデータ不足、フォールバック値。

**Overbet 加算**: bet 寄り (true) に限り HIGH: +20pt / MID: +15pt 加算（上記表は加算後）。

---

## 5. Confidence 判定ルール

| 条件 | Confidence |
|---|---|
| distance ≥ 3 | HIGH |
| 型1 かつ distance ≤ 2 | HIGH（型1 は HIGH 有利） |
| 型7 かつ distance = 0 | HIGH |
| 型7 かつ distance = 1 | LOW |
| distance = 2 | MID |
| 型5 | MID（モノトーン固定） |
| 型3 または 型4 | LOW |
| 上記以外 | MID |

*distance = |CBS - T|（T=5 固定）*

---

## 6. ハンドカテゴリ（4 区分）

| カテゴリ | 手の種類 | 意味 |
|---|---|---|
| **slowplay** | set, trips, two_pair, fullhouse, flush, straight, quads | 強い役だが GTO で check 多い |
| **trash** | low_pair | 弱く bet が少ない |
| **premium** | overpair, underpair | ペア系の強い役 |
| **default** | その他（ace_high, king_high, no_made_hand, third_pair, second_pair, top_pair） | 補正なし（offset=0） |

---

## 7. 13 context パラメータ完全表

### Tier 0 + Tier 1: cash + MTT depth series

| パラメータ | cash_100bb | mtt_25bb | mtt_50bb | mtt_100bb | mtt_200bb |
|---|---:|---:|---:|---:|---:|
| **α** | 0.00 | +0.06 | -0.04 | **+0.15** | -0.04 |
| **β (CBS≥7)** | -0.02 | +0.31 | +0.19 | +0.09 | +0.11 |
| **off_slowplay** | +0.02 | -0.28 | -0.12 | -0.17 | -0.15 |
| **off_trash** | -0.23 | -0.23 | **-0.35** | -0.19 | **-0.31** |
| **off_premium** | +0.15 | +0.15 | +0.20 | +0.08 | +0.14 |
| **SB lift** | -0.08 | -0.10 | **-0.29** | -0.11 | **-0.34** |
| **wide lift** (CO/HJ/UTG) | +0.10 | +0.13 | 0.00 | **+0.17** | +0.01 |
| **ax_range_bet** | 0.00 | **+0.30** | +0.11 | +0.28 | +0.09 |
| **polarize_enabled** | **True** | False | False | False | False |
| **mono_conf_down** | **True** | False | False | False | False |
| WRMSE | 16.43% | 15.46% | **12.96%** | 21.95% | 14.10% |

**depth 系列の発見**:
- mtt_100bb: α=+15 が突出（MTT6mSimple の wide cbet 特性、精度低）
- mtt_50bb / mtt_200bb: 構造が類似（SB lift 強く負、wide lift ≈ 0）
- depth が浅いほど β が高い（25bb: +31 → 200bb: +11、強い役の lift 減衰）

---

### Tier 3: 3BP IP depth series

| パラメータ | mtt_3bp_20bb | mtt_3bp_25bb | mtt_3bp_50bb | mtt_3bp_100bb |
|---|---:|---:|---:|---:|
| **α** | +0.02 | +0.09 | +0.07 | +0.05 |
| **β (CBS≥7)** | +0.14 | +0.19 | +0.30 | +0.30 |
| **off_slowplay** | -0.40 | **-0.66** | -0.40 | -0.33 |
| **off_trash** | -0.03 | -0.44 | -0.45 | **-0.48** |
| **off_premium** | -0.04 | -0.09 | +0.14 | **+0.20** |
| **SB lift** | 0.00 | 0.00 | 0.00 | 0.00 |
| **ax_range_bet** | 0.00 | 0.00 | 0.00 | 0.00 |
| **SPR** | ≈2.5 | ≈2.7 | ≈5.5 | ≈11 |
| WRMSE | 23.08% | 18.65% | **8.62%** | 13.37% |

**3BP 系列の発見**:
- 低 SPR (≤25bb): trash の off が -3〜-44 の幅（浅は trash も一部 bet）
- 深 SPR (≥50bb): premium が大幅 up（完全 polarize）
- 25bb の off_slowplay=-0.66: 最強の slowplay 集中（set は全力 check）
- 50bb が全 context 中最高精度（WRMSE 8.62%）

---

### Tier 4: Turn cbet 2nd barrel series

| パラメータ | mtt_25bb_turn | mtt_50bb_turn | mtt_100bb_turn | cash_100bb_turn |
|---|---:|---:|---:|---:|
| **α** | **-0.41** | -0.37 | -0.26 | -0.37 |
| **β (CBS≥7)** | +0.01 | 0.00 | 0.00 | 0.00 |
| **off_slowplay** | -0.28 | -0.25 | -0.26 | -0.27 |
| **off_trash** | -0.01 | -0.03 | -0.14 | -0.08 |
| **off_premium** | +0.08 | +0.10 | **+0.32** | +0.22 |
| **SB lift** | 0.00 | 0.00 | 0.00 | 0.00 |
| **ax_range_bet** | 0.00 | 0.00 | 0.00 | 0.00 |
| WRMSE | **7.02%** | 14.44% | 26.95% | 16.11% |

**Turn 系列の発見**:
- 全 context で α ≈ -0.35（フロップ比 -35pt の全体 bet 率低下）
- 全 context で β ≈ 0（ターンでは強い役への追加 lift 廃止）
- off_trash: フロップ (-0.23〜-0.35) → ターン (-0.01〜-0.14)（low_pair が相対的に bet 増）
- mtt_25bb_turn が最高精度（WRMSE 7.02%）
- mtt_100bb_turn は最低精度（WRMSE 26.95%、フロップ 100bb と同様）

---

## 8. Full DCBS: 4 context × HP base + kicker offset 完全表

### DCBS base 表（HP バケット別 continue freq）

| HP | 意味 | mtt_25bb | mtt_50bb | mtt_100bb | cash_100bb |
|---:|---|---:|---:|---:|---:|
| 2 | air（役なし系） | **67%** | 54% | **28%** | 40% |
| 3 | 弱ペア（underpair/third_pair） | 98% | 95% | 84% | 85% |
| 5 | 中ペア（second_pair） | 99% | 96% | 87% | **98%** |
| 7 | 強ペア（top_pair/overpair） | 100% | 99% | 98% | 100% |
| 8+ | set/trips/two_pair 以上 | 100% | 100% | 100% | 100% |

**発見**: depth が増すほど air は fold（mtt_25bb: 67% → mtt_100bb: 28%）。top_pair 以上は全 context で 96%+ call。

### Kicker offset 表（HP=2 内の細分化）

| 手の種類 | mtt_25bb | mtt_50bb | mtt_100bb | cash_100bb |
|---|---:|---:|---:|---:|
| ace_high | **+10%** | **+17%** | +5% | +5% |
| king_high | +1% | +6% | +5% | 0% |
| no_made_hand | **-12%** | **-13%** | 0% | -3% |
| low_pair | 0% | -10% | -10% | -2% |

**発見**: 浅スタック (25/50bb) でのキッカー効果が大（ace_high vs no_made_hand の差 22pt）。深スタック (100bb) では差が縮まる（最大 5pt）。

### DCBS 計算式

```
continue_freq = base_dcbs[context][HP]
              + kicker_offset[context][hand]  (HP=2 の場合のみ)

fold_freq = 1.0 - continue_freq
```

---

## 9. Polarize board 判定条件（cash のみ使用）

以下のいずれかを満たすボードが polarize 対象（overbet 116% 適用）:

1. **mid-rank connected**: top ≤ 9 かつ gap（top - low）≤ 4
2. **K-high J+ mid, wide spread**: high=K かつ mid ≥ J かつ gap ≥ 3
3. **K-high 9+ mid, very wide**: high=K かつ mid ≥ 9 かつ gap ≥ 5
4. **A-high 8-J mid, spread**: high=A かつ mid ∈ [8,9,T,J] かつ gap ≥ 4
5. **Q-high 8-J mid, spread**: high=Q かつ mid ∈ [8,9,T,J] かつ gap ≥ 4
6. **JT-high 6-9 mid, spread**: high ∈ {J,T} かつ mid ∈ [6,7,8,9] かつ gap ≥ 3

**除外**: paired board または mono（3 同スーツ）は polarize 対象外。

---

## 10. A-x range bet 判定（MTT BTN/CO のみ）

```python
def is_ax_dry_or_paired(board):
    if high_card != "A":
        return False
    return paired OR gap >= 8
```

**適用条件**: MTT context（25/50/100/200bb） かつ ポジションが BTN または CO かつ ボードが A-high paired or A-high dry（gap ≥ 8）。
**効果**: ax_range_bet 値を freq に加算（25bb: +30pt、50bb: +11pt、100bb: +28pt、200bb: +9pt）。

---

## 11. 精度サマリ（WRMSE 分布）

| 精度帯 | Contexts |
|---|---|
| **< 10%** (極良) | mtt_3bp_50bb (8.62%), mtt_25bb_turn_btn (7.02%) |
| **10-15%** (良) | mtt_50bb (12.96%), mtt_3bp_100bb (13.37%), mtt_200bb (14.10%), mtt_50bb_turn (14.44%), mtt_25bb (15.46%), DCBS mtt_25 (14.36%), DCBS mtt_50 (14.87%) |
| **15-20%** (許容) | cash_100bb (16.43%), cash_turn (16.11%), DCBS mtt_100 (15.86%), DCBS cash (17.17%), mtt_3bp_25bb (18.65%) |
| **20%+** (注意) | mtt_100bb (21.95%), mtt_3bp_20bb (23.08%), mtt_100bb_turn (26.95%) |

**平均 WRMSE ≈ 16%**（cbet + defense 全体）。

---

## 12. 暗記対象カウント

| 項目 | 数値数 |
|---|---:|
| HP テーブル（6 バケット） | 6 |
| DP テーブル（4 段階） | 4 |
| BASE_FREQ（8 セル、overbet 含む） | 8 |
| カテゴリ 4 区分マッピング | — |
| **UCBS-v2 共通 小計** | **18 数値** |
| context per（α/β/off×3/SB/wide/ax）× 13 | ~78 数値 |
| **UCBS-v2 合計** | **96 数値** |
| DCBS base（HP×4 context） | 16 |
| DCBS kicker（4 hand × 4 context） | 16 |
| **DCBS 合計** | **32 数値** |
| **総計** | **128 数値 + 1 式 + 4 例外** |
