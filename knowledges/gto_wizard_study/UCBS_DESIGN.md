# UCBS — Universal CBS for Cash and MTT

設計日: 2026-05-27
目的: cash と MTT の両方で使える統一 CBet 判定モデル

## 設計思想

CBS（MTT 用）と FCBL（cash 用）を統合し、**1 つの式で複数 context** を扱えるようにする。

```
UCBS = HP + DP の構造を維持
    + Confidence 計算ロジック維持
    + Size 軸追加 (cash の overbet 発見を反映)
    + Context パラメータで game type 切替
```

## 5 軸構造

| 軸 | 値 | 計算方法 | 共通/Context |
|---|---|---|---|
| **HP** (現在価値) | 1-9 | 手牌種別 → 表参照 | 共通 |
| **DP** (将来価値) | 0-3 | ドロー種別 → 表参照 | 共通 |
| **Confidence** | HIGH/MID/LOW | `f(|CBS - threshold|, board_type)` | 共通 |
| **Size** | SMALL(33%) / OVERBET(116%) | `polarize_class(board)` | Context |
| **Context** | cash/mtt_200/mtt_100/mtt_50/mtt_25 | 入力 | — |

## 決定フロー

```python
def ucbs_predict(hand_type, draw_type, board, scenario, context):
    # 1. CBS = HP + DP (共通)
    hp = HP_TABLE[hand_type]
    dp = DP_TABLE[draw_type]
    cbs = hp + dp
    
    # 2. Context-specific params
    threshold = CONTEXTS[context]["thresholds"][scenario]
    direction = (cbs >= threshold)
    
    # 3. Confidence (board_type で修飾)
    confidence = calc_confidence(cbs, threshold, board_type)
    
    # 4. Size (context で polarize 有効/無効)
    size = calc_size(board_features, context)
    
    # 5. Frequency (context × size 別)
    freq_table = CONTEXTS[context]["freq_small"] if size == 33 else CONTEXTS[context]["freq_overbet"]
    freq = freq_table[(confidence, direction)]
    
    return (cbs, confidence, direction, size, freq)
```

## Context 別パラメータ

### Cash 100bb (NL25R25 想定)

```yaml
thresholds: { UTG: 5, HJ: 5, CO: 5, BTN: 5, SB: 5 }
polarize_enabled: true
freq_small:
  (HIGH, bet):   0.75   (HIGH, check): 0.40
  (MID,  bet):   0.55   (MID,  check): 0.40
  (LOW,  bet):   0.45   (LOW,  check): 0.30
freq_overbet:
  (HIGH, bet):   0.55   (HIGH, check): 0.15
  (MID,  bet):   0.40   (MID,  check): 0.20
  (LOW,  bet):   0.35   (LOW,  check): 0.25
```

### MTT 200bb (deep stack)

```yaml
thresholds: { UTG: 5, HJ: 5, CO: 5, BTN: 5, SB: 7 }
polarize_enabled: false  # flop で overbet 少ない
freq_small:
  (HIGH, bet):   0.92   (HIGH, check): 0.50
  (MID,  bet):   0.78   (MID,  check): 0.45
  (LOW,  bet):   0.65   (LOW,  check): 0.35
```

### MTT 100bb / 50bb / 25bb

stack depth が浅くなるほど cbet 頻度を下げる傾向。詳細は `ucbs.py` 参照。

## Polarize board 判定（cash 用、context-enabled で発動）

```
polarize_class:
  1. Super-connected low: high <= 9 かつ gap <= 4 (876, 765, 975)
  2. K-broadway-mid: K + (J,Q,K) mid + gap >= 3 (KJ4, KQJ系)
  3. A-mid-wet: A + (8-J) mid + gap >= 4 (AJ4, AT5, A87)
  4. Q-mid-wet: Q + (8-J) mid + gap >= 4 (QT5, Q86, QJ6)
  5. J/T mid-wet: J or T + (6-9) mid + gap >= 3 (J75, T87)

それ以外、paired, mono → SMALL (33%)
```

## 検証結果（cash data 347 records）

| モデル | WRMSE | Size予測 |
|------|------:|------:|
| CBS v1 (MTT defaults) | 21.93% | なし |
| CBS v2 (cash-tuned) | 21.75% | あり |
| **UCBS (unified)** | **24.62%** | **あり、context aware** |

UCBS は cash 専用 v2 から +2.9pt のトレードオフを受け入れて、**1 つの式で MTT も予測可能**にしています。

## なぜ UCBS が価値あるか

| 観点 | 効果 |
|---|---|
| **学習者にとって** | 1 つの式を覚えれば cash も MTT も対応可 |
| **書籍構成** | 各巻で同じ用語、context 別の表を提示 |
| **コードベース** | 1 つの実装、context パラメータで切替 |
| **拡張性** | 新しい game type (ICM, PKO 等) を context 追加で対応 |

## 残るバイアスと改善余地

cash data 347 records での残バイアス:

| 手牌 | bias | 改善案 |
|----|---:|---|
| low_pair | +26% | HP=1 にすると改善するが MTT で逆効果 |
| king_high | -15% | Air も意外と打つ。Confidence 修飾子追加候補 |
| set | -13% | HP=9 にすると改善するが unified の妥協 |
| flush | +24% | board features に flush completion 検出追加候補 |

これらは context 別の HP_TABLE オーバーライド機能で改善可能。

## 書籍での提示方法

```
■ UCBS 暗算カード

Step 1: ハンド → HP (1-9)
  no_made/Ax_hi/Kx_hi → 2
  low_pair → 2
  underpair/third_pair → 3
  second_pair → 5
  top_pair/overpair → 7
  set/trips → 8
  two_pair/flush/straight/fullhouse → 9

Step 2: ドロー → DP (0-3)
  no_draw → 0
  gutshot → 1
  FD/OESD → 2
  combo → 3

Step 3: CBS = HP + DP

Step 4: 閾値 (game type 別表参照)
  Cash 100bb: 全 position = 5
  MTT 200bb: UTG/HJ/CO/BTN = 5, SB = 7
  ...

Step 5: Confidence (CBS と閾値の距離 + ボード型補正)

Step 6: Size 判定 (context + ボード)
  cash: polarize board なら 116%, それ以外 33%
  mtt 200bb: 一律 33%
  ...

Step 7: 頻度表で予測 cbet%
```

## ファイル

- 実装: `cash-postflop/ucbs.py`
- 検証: `cash-postflop/cbs_cash_eval.py`, `cash-postflop/cbs_cash_tune.py`
- データ: `cash-postflop/findings/cash_5cat_gto.json` (347 records)
- 関連: `mtt-postflop/findings/flop_attack_defense_unified.md` (CBS 元)
