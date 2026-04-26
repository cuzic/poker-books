# 6-max 100BB GTO Preflop Charts リファレンス

> 本ファイルは poker-coaching の **Implementable GTO Charts** （Jonathan Little 監修、6-max 100BB Cash） を画像から抽出した GTO プリフロップレンジの再利用可能なリファレンス。
>
> - 出典: <https://www.pokercoaching.com/> Implementable GTO Charts（公開 PDF）
> - 抽出スクリプト: `scripts/extract_gto_charts.py`
> - 構造化データ: `knowledges/preflop/gto-charts.json`
>
> **6-max ↔ 9-max のポジション対応**
> - LJ (Lojack) = UTG（6-max では最早ポジション）
> - HJ (Hijack) = MP（6-max のミドル）
> - CO / BTN / SB / BB は同じ

## 想定条件

- **スタック**: 100BB ディープ
- **ベットサイズ**:
  - RFI: SB 以外は 2.5BB、SB は 3BB
  - 3bet IP: 3.5x、3bet OOP: 4x
  - BB vs SB Limp: 3.5x
  - 4bet IP: 2.3x、4bet OOP: 2.5x
- **戦略**: 「Implementable」の名の通り、純粋 GTO の混合戦略をできるだけ単一行動に丸めた版（混合 33% でも 1 ハンド代表に集約）

---

## 目次

- [Raise First In (RFI)](#raise-first-in-rfi)
- [Facing RFI: In Position (IP 3bet)](#facing-rfi-in-position-ip-3bet)
- [Facing RFI: Out of Position (OOP)](#facing-rfi-out-of-position-oop)
- [Blind vs Blind](#blind-vs-blind)

---

## Raise First In (RFI)

### LJ_RFI

_Lojack RFI (= UTG in 6-max)_

**頻度 (combos / 1326)**:

- Fold: **1100** combos (83.0%)
- Raise (オープン / 3bet): **226** combos (17.0%)

#### Raise (オープン / 3bet)

- **ペア**: AA, KK, QQ, JJ, TT, 99, 88, 77, 66
- **Axs**: AKs, AQs, AJs, ATs, A9s, A8s, A7s, A6s, A5s, A4s, A3s
- **Kxs**: KQs, KJs, KTs, K9s, K8s
- **Qxs**: QJs, QTs, Q9s
- **Jxs**: JTs, J9s
- **Txs**: T9s
- **Axo**: AKo, AQo, AJo, ATo
- **Kxo**: KQo, KJo
- **Qxo**: QJo

---

### HJ_RFI

_Hijack RFI (= MP in 6-max)_

**頻度 (combos / 1326)**:

- Fold: **1042** combos (78.6%)
- Raise (オープン / 3bet): **284** combos (21.4%)

#### Raise (オープン / 3bet)

- **ペア**: AA, KK, QQ, JJ, TT, 99, 88, 77, 66, 55
- **Axs**: AKs, AQs, AJs, ATs, A9s, A8s, A7s, A6s, A5s, A4s, A3s, A2s
- **Kxs**: KQs, KJs, KTs, K9s, K8s, K7s, K6s
- **Qxs**: QJs, QTs, Q9s, Q8s
- **Jxs**: JTs, J9s
- **Txs**: T9s
- **9xs**: 98s
- **8xs**: 87s
- **7xs**: 76s
- **Axo**: AKo, AQo, AJo, ATo
- **Kxo**: KQo, KJo, KTo
- **Qxo**: QJo, QTo

---

### CO_RFI

_Cutoff RFI_

**頻度 (combos / 1326)**:

- Fold: **940** combos (70.9%)
- Raise (オープン / 3bet): **386** combos (29.1%)

#### Raise (オープン / 3bet)

- **ペア**: AA, KK, QQ, JJ, TT, 99, 88, 77, 66, 55, 44
- **Axs**: AKs, AQs, AJs, ATs, A9s, A8s, A7s, A6s, A5s, A4s, A3s, A2s
- **Kxs**: KQs, KJs, KTs, K9s, K8s, K7s, K6s, K5s, K4s, K3s
- **Qxs**: QJs, QTs, Q9s, Q8s, Q7s, Q6s
- **Jxs**: JTs, J9s, J8s
- **Txs**: T9s, T8s, T7s
- **9xs**: 98s, 97s
- **8xs**: 87s
- **7xs**: 76s
- **Axo**: AKo, AQo, AJo, ATo, A9o, A8o
- **Kxo**: KQo, KJo, KTo
- **Qxo**: QJo, QTo
- **Jxo**: JTo
- **4xo**: 43o
- **3xo**: 32o

---

### BTN_RFI

_Button RFI_

**頻度 (combos / 1326)**:

- Fold: **724** combos (54.6%)
- Raise (オープン / 3bet): **602** combos (45.4%)

#### Raise (オープン / 3bet)

- **ペア**: AA, KK, QQ, JJ, TT, 99, 88, 77, 66, 55, 44
- **Axs**: AKs, AQs, AJs, ATs, A9s, A8s, A7s, A6s, A5s, A4s, A3s, A2s
- **Kxs**: KQs, KJs, KTs, K9s, K8s, K7s, K6s, K5s, K4s, K3s, K2s
- **Qxs**: QJs, QTs, Q9s, Q8s, Q7s, Q6s, Q5s, Q4s, Q3s
- **Jxs**: JTs, J9s, J8s, J7s, J6s, J5s, J4s
- **Txs**: T9s, T8s, T7s, T6s
- **9xs**: 98s, 97s, 96s
- **8xs**: 87s, 86s, 85s
- **7xs**: 76s, 75s
- **6xs**: 65s, 64s
- **5xs**: 54s, 53s
- **4xs**: 43s
- **Axo**: AKo, AQo, AJo, ATo, A9o, A8o, A7o, A6o, A5o, A4o, A3o
- **Kxo**: KQo, KJo, KTo, K9o, K8o
- **Qxo**: QJo, QTo, Q9o
- **Jxo**: JTo, J9o
- **Txo**: T9o, T8o
- **9xo**: 98o
- **4xo**: 43o
- **3xo**: 32o

---

### SB_RFI

_Small Blind RFI (raise + limp 混合)_

**頻度 (combos / 1326)**:

- Limp / Call: **504** combos (38.0%)
- Fold: **500** combos (37.7%)
- Raise (オープン / 3bet): **322** combos (24.3%)

#### Limp / Call

- **ペア**: AA, TT, 99, 88, 77, 66, 55, 44
- **Axs**: AQs, AJs, A6s, A4s, A3s, A2s
- **Kxs**: KQs, K9s, K7s, K6s, K4s
- **Qxs**: Q9s, Q8s, Q7s, Q6s
- **Jxs**: J9s, J8s, J3s, J2s
- **Txs**: T8s, T7s, T4s, T3s
- **9xs**: 98s, 97s, 95s, 94s
- **8xs**: 87s, 86s, 85s, 84s
- **7xs**: 76s, 75s, 74s
- **6xs**: 63s
- **4xs**: 43s
- **Axo**: AKo, ATo, A9o, A5o, A3o, A2o
- **Kxo**: KQo, KTo, K6o, K5o, K4o
- **Qxo**: QJo, QTo, Q8o, Q7o, Q6o, Q5o
- **Jxo**: JTo, J8o, J7o
- **Txo**: T9o, T7o
- **9xo**: 97o
- **8xo**: 87o, 86o
- **7xo**: 76o

#### Raise (オープン / 3bet)

- **ペア**: KK, QQ, JJ, 33, 22
- **Axs**: AKs, ATs, A9s, A8s, A7s, A5s
- **Kxs**: KJs, KTs, K8s, K5s, K3s, K2s
- **Qxs**: QJs, QTs, Q5s, Q4s, Q3s, Q2s
- **Jxs**: JTs, J7s, J6s, J5s, J4s
- **Txs**: T9s, T6s, T5s
- **9xs**: 96s
- **6xs**: 65s, 64s
- **5xs**: 54s, 53s
- **Axo**: AQo, AJo, A8o, A7o, A6o, A4o
- **Kxo**: KJo, K9o, K8o, K7o
- **Qxo**: Q9o
- **Jxo**: J9o
- **Txo**: T8o
- **9xo**: 98o

---


## Facing RFI: In Position (IP 3bet)

### HJ_vs_LJ

_Hijack vs Lojack RFI (3bet IP)_

**頻度 (combos / 1326)**:

- Fold: **1218** combos (91.9%)
- Raise (オープン / 3bet): **108** combos (8.1%)

#### Raise (オープン / 3bet)

- **ペア**: AA, KK, QQ, JJ, TT, 99
- **Axs**: AKs, AQs, AJs, ATs, A5s
- **Kxs**: KQs, KJs, KTs
- **Qxs**: QJs
- **Axo**: AKo, AQo
- **Kxo**: KQo

---

### CO_vs_LJ

_Cutoff vs Lojack RFI (3bet IP)_

**頻度 (combos / 1326)**:

- Fold: **1212** combos (91.4%)
- Raise (オープン / 3bet): **114** combos (8.6%)

#### Raise (オープン / 3bet)

- **ペア**: AA, KK, QQ, JJ, TT, 99, 88
- **Axs**: AKs, AQs, AJs, ATs, A5s
- **Kxs**: KQs, KJs, KTs
- **Qxs**: QJs
- **Axo**: AKo, AQo
- **Kxo**: KQo

---

### CO_vs_HJ

_Cutoff vs Hijack RFI (3bet IP)_

**頻度 (combos / 1326)**:

- Fold: **1192** combos (89.9%)
- Raise (オープン / 3bet): **134** combos (10.1%)

#### Raise (オープン / 3bet)

- **ペア**: AA, KK, QQ, JJ, TT, 99, 88
- **Axs**: AKs, AQs, AJs, ATs, A9s, A5s, A4s
- **Kxs**: KQs, KJs, KTs
- **Qxs**: QJs
- **Axo**: AKo, AQo, AJo
- **Kxo**: KQo

---

### BTN_vs_LJ

_Button vs Lojack RFI (3bet IP)_

**頻度 (combos / 1326)**:

- Fold: **1138** combos (85.8%)
- Raise (オープン / 3bet): **96** combos (7.2%)
- Limp / Call: **92** combos (6.9%)

#### Raise (オープン / 3bet)

- **ペア**: AA, KK, QQ, JJ
- **Axs**: AKs, AQs, A9s, A8s, A4s, A3s
- **Kxs**: K9s
- **Qxs**: QJs
- **Txs**: T9s
- **Axo**: AKo, AJo
- **Kxo**: KQo

#### Limp / Call

- **ペア**: TT, 99, 88, 77, 66, 55
- **Axs**: AJs, ATs, A5s
- **Kxs**: KQs, KJs, KTs
- **Qxs**: QTs
- **Jxs**: JTs
- **7xs**: 76s
- **6xs**: 65s
- **5xs**: 54s
- **Axo**: AQo

---

### BTN_vs_HJ

_Button vs Hijack RFI (3bet IP)_

**頻度 (combos / 1326)**:

- Fold: **1124** combos (84.8%)
- Raise (オープン / 3bet): **118** combos (8.9%)
- Limp / Call: **84** combos (6.3%)

#### Raise (オープン / 3bet)

- **ペア**: AA, KK, QQ, JJ, 66
- **Axs**: AKs, AQs, A9s, A8s, A7s, A4s, A3s
- **Kxs**: KTs, K9s, K8s
- **Qxs**: QTs, Q9s
- **Txs**: T9s
- **Axo**: AKo, AJo
- **Kxo**: KQo

#### Limp / Call

- **ペア**: TT, 99, 88, 77, 55, 44
- **Axs**: AJs, ATs, A5s
- **Kxs**: KQs, KJs
- **Qxs**: QJs
- **Jxs**: JTs
- **9xs**: 98s
- **8xs**: 87s
- **Axo**: AQo

---

### BTN_vs_CO

_Button vs Cutoff RFI (3bet IP)_

**頻度 (combos / 1326)**:

- Fold: **1094** combos (82.5%)
- Raise (オープン / 3bet): **160** combos (12.1%)
- Limp / Call: **72** combos (5.4%)

#### Raise (オープン / 3bet)

- **ペア**: AA, KK, QQ, JJ, TT, 55
- **Axs**: AKs, AQs, A8s, A7s, A6s, A4s, A3s
- **Kxs**: KQs, K9s
- **Qxs**: QJs, Q9s
- **Jxs**: JTs, J9s
- **Axo**: AKo, AJo, ATo
- **Kxo**: KQo, KJo
- **Qxo**: QJo

#### Limp / Call

- **ペア**: 99, 88, 77, 66
- **Axs**: AJs, ATs, A9s, A5s
- **Kxs**: KJs, KTs
- **Qxs**: QTs
- **Txs**: T9s
- **9xs**: 98s
- **Axo**: AQo

---


## Facing RFI: Out of Position (OOP)

### SB_vs_LJ

_Small Blind vs Lojack RFI (3bet OOP)_

**頻度 (combos / 1326)**:

- Fold: **1230** combos (92.8%)
- Raise (オープン / 3bet): **96** combos (7.2%)

#### Raise (オープン / 3bet)

- **ペア**: AA, KK, QQ, JJ, TT, 99
- **Axs**: AKs, AQs, AJs, ATs, A5s
- **Kxs**: KQs, KJs, KTs
- **Qxs**: QJs
- **Axo**: AKo, AQo

---

### SB_vs_HJ

_Small Blind vs Hijack RFI (3bet OOP)_

**頻度 (combos / 1326)**:

- Fold: **1210** combos (91.3%)
- Raise (オープン / 3bet): **116** combos (8.7%)

#### Raise (オープン / 3bet)

- **ペア**: AA, KK, QQ, JJ, TT, 99, 88, 77
- **Axs**: AKs, AQs, AJs, ATs, A5s
- **Kxs**: KQs, KJs, KTs
- **Qxs**: QJs, QTs
- **Jxs**: JTs
- **Axo**: AKo, AQo

---

### SB_vs_CO

_Small Blind vs Cutoff RFI (3bet OOP)_

**頻度 (combos / 1326)**:

- Fold: **1180** combos (89.0%)
- Raise (オープン / 3bet): **146** combos (11.0%)

#### Raise (オープン / 3bet)

- **ペア**: AA, KK, QQ, JJ, TT, 99, 88, 77, 66
- **Axs**: AKs, AQs, AJs, ATs, A9s, A5s
- **Kxs**: KQs, KJs, KTs
- **Qxs**: QJs, QTs
- **Jxs**: JTs, J9s
- **Txs**: T9s
- **Axo**: AKo, AQo
- **Kxo**: KQo

---

### SB_vs_BTN

_Small Blind vs Button RFI (3bet OOP)_

**頻度 (combos / 1326)**:

- Fold: **1114** combos (84.0%)
- Raise (オープン / 3bet): **212** combos (16.0%)

#### Raise (オープン / 3bet)

- **ペア**: AA, KK, QQ, JJ, TT, 99, 88, 77, 66, 55
- **Axs**: AKs, AQs, AJs, ATs, A9s, A8s, A7s, A5s, A4s
- **Kxs**: KQs, KJs, KTs, K9s
- **Qxs**: QJs, QTs, Q9s
- **Jxs**: JTs, J9s
- **Txs**: T9s, T8s
- **Axo**: AKo, AQo, AJo
- **Kxo**: KQo, KJo
- **5xo**: 54o

---

### BB_vs_LJ

_Big Blind vs Lojack RFI (defense)_

**頻度 (combos / 1326)**:

- Fold: **944** combos (71.2%)
- Limp / Call: **306** combos (23.1%)
- Raise (オープン / 3bet): **76** combos (5.7%)

#### Raise (オープン / 3bet)

- **ペア**: AA, KK, QQ, JJ
- **Axs**: AKs, AQs, A5s, A4s
- **Kxs**: KQs, KJs
- **Qxs**: QJs
- **Jxs**: JTs
- **6xs**: 65s
- **5xs**: 54s
- **Axo**: AKo

#### Limp / Call

- **ペア**: TT, 99, 88, 77, 66, 55, 44, 33, 22
- **Axs**: AJs, ATs, A9s, A8s, A7s, A6s, A3s, A2s
- **Kxs**: KTs, K9s, K8s, K7s, K6s, K5s, K4s, K3s, K2s
- **Qxs**: QTs, Q9s, Q8s, Q7s, Q6s, Q5s
- **Jxs**: J9s, J8s
- **Txs**: T9s, T8s, T7s
- **9xs**: 98s, 97s, 96s
- **8xs**: 87s, 86s, 85s
- **7xs**: 76s, 75s, 74s
- **6xs**: 64s, 63s
- **5xs**: 53s
- **4xs**: 43s
- **3xs**: 32s
- **Axo**: AQo, AJo, ATo
- **Kxo**: KQo, KJo
- **Qxo**: QJo
- **Jxo**: JTo

---

### BB_vs_HJ

_Big Blind vs Hijack RFI (defense)_

**頻度 (combos / 1326)**:

- Fold: **908** combos (68.5%)
- Limp / Call: **320** combos (24.1%)
- Raise (オープン / 3bet): **98** combos (7.4%)

#### Raise (オープン / 3bet)

- **ペア**: AA, KK, QQ, JJ, TT
- **Axs**: AKs, AQs, A9s, A5s, A4s
- **Kxs**: KQs, KJs, KTs, K5s
- **Qxs**: QJs, QTs
- **Jxs**: JTs
- **6xs**: 65s
- **5xs**: 54s
- **Axo**: AKo

#### Limp / Call

- **ペア**: 99, 88, 77, 66, 55, 44, 33, 22
- **Axs**: AJs, ATs, A8s, A7s, A6s, A3s, A2s
- **Kxs**: K9s, K8s, K7s, K6s, K4s, K3s, K2s
- **Qxs**: Q9s, Q8s, Q7s, Q6s, Q5s
- **Jxs**: J9s, J8s, J7s
- **Txs**: T9s, T8s, T7s
- **9xs**: 98s, 97s, 96s
- **8xs**: 87s, 86s, 85s
- **7xs**: 76s, 75s, 74s
- **6xs**: 64s, 63s
- **5xs**: 53s
- **4xs**: 43s
- **Axo**: AQo, AJo, ATo, A9o
- **Kxo**: KQo, KJo, KTo
- **Qxo**: QJo, QTo
- **Jxo**: JTo

---

### BB_vs_CO

_Big Blind vs Cutoff RFI (defense)_

**頻度 (combos / 1326)**:

- Fold: **856** combos (64.6%)
- Limp / Call: **342** combos (25.8%)
- Raise (オープン / 3bet): **128** combos (9.7%)

#### Raise (オープン / 3bet)

- **ペア**: AA, KK, QQ, JJ, TT, 99
- **Axs**: AKs, AQs, AJs, A9s, A5s, A4s
- **Kxs**: KQs, KJs, KTs
- **Qxs**: QJs, QTs, Q9s
- **Jxs**: JTs, J9s
- **Txs**: T9s
- **6xs**: 65s
- **5xs**: 54s
- **Axo**: AKo, AQo

#### Limp / Call

- **ペア**: 88, 77, 66, 55, 44, 33, 22
- **Axs**: ATs, A8s, A7s, A6s, A3s, A2s
- **Kxs**: K9s, K8s, K7s, K6s, K5s, K4s, K3s, K2s
- **Qxs**: Q8s, Q7s, Q6s, Q5s, Q4s, Q3s
- **Jxs**: J8s, J7s, J6s
- **Txs**: T8s, T7s
- **9xs**: 98s, 97s, 96s
- **8xs**: 87s, 86s, 85s
- **7xs**: 76s, 75s, 74s
- **6xs**: 64s, 63s
- **5xs**: 53s, 52s
- **4xs**: 43s
- **Axo**: AJo, ATo, A9o, A8o, A5o
- **Kxo**: KQo, KJo, KTo
- **Qxo**: QJo, QTo
- **Jxo**: JTo
- **Txo**: T9o

---

### BB_vs_BTN

_Big Blind vs Button RFI (defense)_

**頻度 (combos / 1326)**:

- Limp / Call: **576** combos (43.4%)
- Fold: **572** combos (43.1%)
- Raise (オープン / 3bet): **178** combos (13.4%)

#### Raise (オープン / 3bet)

- **ペア**: AA, KK, QQ, JJ, TT, 99, 88
- **Axs**: AKs, AQs, AJs, ATs, A6s, A5s, A4s
- **Kxs**: KQs, KJs, KTs, K9s
- **Qxs**: QJs, QTs, Q9s
- **Jxs**: JTs, J9s, J8s
- **Txs**: T9s, T8s
- **9xs**: 98s, 97s
- **8xs**: 87s
- **7xs**: 76s
- **6xs**: 65s
- **5xs**: 54s
- **Axo**: AKo, AQo
- **Kxo**: KQo

#### Limp / Call

- **ペア**: 77, 66, 55, 44, 33, 22
- **Axs**: A9s, A8s, A7s, A3s, A2s
- **Kxs**: K8s, K7s, K6s, K5s, K4s, K3s, K2s
- **Qxs**: Q8s, Q7s, Q6s, Q5s, Q4s, Q3s, Q2s
- **Jxs**: J7s, J6s, J5s, J4s, J3s, J2s
- **Txs**: T7s, T6s, T5s, T4s, T3s, T2s
- **9xs**: 96s, 95s, 94s
- **8xs**: 86s, 85s, 84s
- **7xs**: 75s, 74s, 73s
- **6xs**: 64s, 63s, 62s
- **5xs**: 53s, 52s
- **4xs**: 43s, 42s
- **3xs**: 32s
- **Axo**: AJo, ATo, A9o, A8o, A7o, A6o, A5o, A4o, A3o
- **Kxo**: KJo, KTo, K9o, K8o, K7o, K6o
- **Qxo**: QJo, QTo, Q9o, Q8o
- **Jxo**: JTo, J9o, J8o
- **Txo**: T9o, T8o
- **9xo**: 98o
- **8xo**: 87o
- **7xo**: 76o
- **6xo**: 65o
- **5xo**: 54o

---


## Blind vs Blind

### BvB_SB_strategy

_Blind vs Blind: SB Strategy_

**頻度 (combos / 1326)**:

- Fold: **534** combos (40.3%)
- Raise (オープン / 3bet): **514** combos (38.8%)
- Limp / Call: **250** combos (18.9%)
- Mixed (limp寄り): **28** combos (2.1%)

#### Raise (オープン / 3bet)

- **ペア**: KK, QQ, JJ, TT, 99, 88, 33
- **Axs**: AKs, A6s, A4s, A3s, A2s
- **Kxs**: KQs, K8s, K7s, K6s, K4s
- **Qxs**: QJs, Q8s, Q3s, Q2s
- **Jxs**: J8s, J7s, J4s, J3s
- **Txs**: T7s, T6s, T5s, T4s
- **9xs**: 98s, 97s, 96s, 95s, 94s
- **8xs**: 87s, 86s, 83s
- **7xs**: 75s
- **6xs**: 64s, 63s
- **3xs**: 32s
- **Axo**: AKo, AQo, AJo, ATo, A7o, A5o, A3o
- **Kxo**: KQo, KJo, K8o, K7o, K6o, K3o
- **Qxo**: QJo, Q9o, Q8o, Q7o, Q3o
- **Jxo**: J9o, J3o
- **Txo**: T9o, T3o
- **9xo**: 93o
- **8xo**: 83o
- **7xo**: 73o
- **6xo**: 63o
- **5xo**: 53o
- **4xo**: 43o

#### Limp / Call

- **ペア**: 22
- **Axs**: AJs, ATs, A9s, A8s, A7s, A5s
- **Kxs**: KJs, KTs, K5s
- **Qxs**: QTs
- **Jxs**: J9s
- **Txs**: T9s
- **8xs**: 85s
- **7xs**: 74s
- **5xs**: 53s, 52s
- **Axo**: A2o
- **Kxo**: KTo, K2o
- **Qxo**: QTo, Q2o
- **Jxo**: JTo, J2o
- **Txo**: T2o
- **9xo**: 92o
- **8xo**: 82o
- **7xo**: 72o
- **6xo**: 62o
- **5xo**: 52o
- **4xo**: 42o
- **3xo**: 32o

#### Mixed (limp寄り)

- **Qxs**: Q7s, Q6s, Q5s, Q4s
- **Jxs**: J6s, J5s
- **7xs**: 73s

---

### BvB_BB_vs_SB_limp

_Blind vs Blind: BB vs SB Limp_

**頻度 (combos / 1326)**:

- Limp / Call: **790** combos (59.6%)
- Raise (オープン / 3bet): **536** combos (40.4%)

#### Raise (オープン / 3bet)

- **ペア**: AA, KK, QQ, JJ, TT, 99, 88, 77, 66, 55, 44, 33
- **Axs**: AKs, AQs, AJs, ATs, A9s, A8s, A5s, A4s, A3s
- **Kxs**: KQs, KJs, KTs, K9s, K6s, K5s
- **Qxs**: QJs, QTs, Q9s
- **Jxs**: JTs, J9s, J8s, J2s
- **Txs**: T9s, T8s, T4s, T3s, T2s
- **9xs**: 98s, 97s, 94s, 93s, 92s
- **8xs**: 87s, 86s, 84s
- **7xs**: 76s, 75s, 74s, 73s
- **6xs**: 65s, 64s, 63s
- **5xs**: 54s
- **3xs**: 32s
- **Axo**: AKo, AQo, AJo, ATo, A5o
- **Kxo**: KQo, KJo, K5o, K4o
- **Qxo**: Q6o, Q5o, Q4o
- **Jxo**: JTo, J7o, J6o, J5o
- **Txo**: T9o, T6o, T5o
- **9xo**: 96o, 95o
- **8xo**: 85o
- **7xo**: 75o, 74o

#### Limp / Call

- **ペア**: 22
- **Axs**: A7s, A6s, A2s
- **Kxs**: K8s, K7s, K4s, K3s, K2s
- **Qxs**: Q8s, Q7s, Q6s, Q5s, Q4s, Q3s, Q2s
- **Jxs**: J7s, J6s, J5s, J4s, J3s
- **Txs**: T7s, T6s, T5s
- **9xs**: 96s, 95s
- **8xs**: 85s, 83s, 82s
- **7xs**: 72s
- **6xs**: 62s
- **5xs**: 53s, 52s
- **4xs**: 43s, 42s
- **Axo**: A9o, A8o, A7o, A6o, A4o, A3o, A2o
- **Kxo**: KTo, K9o, K8o, K7o, K6o, K3o, K2o
- **Qxo**: QJo, QTo, Q9o, Q8o, Q7o, Q3o, Q2o
- **Jxo**: J9o, J8o, J4o, J3o, J2o
- **Txo**: T8o, T7o, T4o, T3o, T2o
- **9xo**: 98o, 97o, 94o, 93o, 92o
- **8xo**: 87o, 86o, 84o, 83o, 82o
- **7xo**: 76o, 73o, 72o
- **6xo**: 65o, 64o, 63o, 62o
- **5xo**: 54o, 53o, 52o
- **4xo**: 43o, 42o
- **3xo**: 32o

---

### BvB_BB_vs_SB_raise

_Blind vs Blind: BB vs SB Raise_

**頻度 (combos / 1326)**:

- Limp / Call: **640** combos (48.3%)
- Fold: **468** combos (35.3%)
- Raise (オープン / 3bet): **218** combos (16.4%)

#### Raise (オープン / 3bet)

- **ペア**: AA, KK, QQ, JJ, TT, 99, 88
- **Axs**: AKs, AQs, AJs, ATs, A5s, A4s
- **Kxs**: KQs, KJs, KTs
- **Qxs**: QJs
- **Jxs**: J5s
- **Txs**: T5s
- **9xs**: 95s
- **8xs**: 87s
- **7xs**: 76s
- **6xs**: 65s
- **5xs**: 54s
- **Axo**: AKo, AQo, A6o
- **Kxo**: K6o, K5o
- **Qxo**: Q6o
- **Jxo**: J8o, J7o
- **Txo**: T7o

#### Limp / Call

- **ペア**: 77, 66, 55, 44, 33, 22
- **Axs**: A9s, A8s, A7s, A6s, A3s, A2s
- **Kxs**: K9s, K8s, K7s, K6s, K5s, K4s, K3s, K2s
- **Qxs**: QTs, Q9s, Q8s, Q7s, Q6s, Q5s, Q4s, Q3s, Q2s
- **Jxs**: JTs, J9s, J8s, J7s, J6s, J4s, J3s, J2s
- **Txs**: T9s, T8s, T7s, T6s, T4s, T3s, T2s
- **9xs**: 98s, 97s, 96s, 94s, 93s, 92s
- **8xs**: 86s, 85s, 84s
- **7xs**: 75s, 74s, 73s
- **6xs**: 64s, 63s, 62s
- **5xs**: 53s, 52s
- **4xs**: 43s, 42s
- **3xs**: 32s
- **Axo**: AJo, ATo, A9o, A8o, A7o, A5o, A4o, A3o, A2o
- **Kxo**: KQo, KJo, KTo, K9o, K8o, K7o
- **Qxo**: QJo, QTo, Q9o, Q8o, Q7o
- **Jxo**: JTo, J9o
- **Txo**: T9o, T8o
- **9xo**: 98o, 97o
- **8xo**: 87o, 86o
- **7xo**: 76o
- **6xo**: 65o
- **5xo**: 54o

---


## 利用例

```python
import json
data = json.load(open('knowledges/preflop/gto-charts.json'))
# Lojack (= UTG in 6-max) RFI raise hands:
lj_raise_hands = set(data['LJ_RFI']['actions']['raise'])
# 'AA', 'AKs', ... in lj_raise_hands
```

## 注意事項

- 抽出スクリプトはピクセル分類で多少の誤差が出る場合があります。特に **SB_RFI / BvB_SB_strategy / BvB_BB_vs_SB_***  は赤・青が同じセル内で縞模様や半分塗りで混ざる**混合戦略表示**のため、個別ハンドのアクションが実際の純粋 GTO と数 % 程度ズレる可能性があります。
- 単純な RFI（LJ_RFI / HJ_RFI / CO_RFI / BTN_RFI）と 対 RFI (HJ_vs_LJ などの IP 3bet) は raise / fold の二値なので抽出精度が高いです。
- Implementable GTO は混合戦略を単純化した版です。本格的な GTO 比較には GTO Wizard 等の解析ソフトを使ってください。
- レンジは **2.5BB オープン** を前提としています。サイジングが変わるとレンジも微妙に変化します（特に 3bet 後の 4bet）。
