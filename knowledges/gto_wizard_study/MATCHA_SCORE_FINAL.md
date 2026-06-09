# MATCHA Score — Final Formula

**MATCHA Framework の中核公式 (data 駆動の確定版)**

`Math Algorithm for Tier-Categorized Hold'em Action`

---

## 公式

```
Score = 4 × tier + Grid[tier][board] + 3 × DV
      + 2 × overcards + 3 × pot − 2 × bs − 2

if Score >= 33: raise
elif Score >=  6: call
else:            fold
```

### 性能 (293K rows 検証)

| 指標 | 値 |
|------|---:|
| Accuracy | **69.44%** |
| Avg loss | **0.4165 BB/spot** |
| Huge loss (>5 BB) | **1.77%** |
| 既存公式 v9b/v15 比 | **avg loss -78%** |

---

## 軸の値表 (6 軸を覚える)

### 1. tier (made hand strength)

| tier | 該当する手 | 値 |
|------|-----------|---:|
| ナッツメイド | full house / quads / straight flush | 5 |
| ストロング | set / trips / straight / flush | 4 |
| ツーペア | two pair | 3 |
| トップペア以上 | top pair / overpair | 2 |
| ミドルペア | 2nd pair / 3rd pair / underpair / low pair | 1 |
| エア | no made hand / ace high / king high | 0 |

### 2. board (3 段階)

| board | 該当 | 値 |
|-------|------|---:|
| dry | unpaired / rainbow / 非 connected | 0 |
| paired | board に同 rank ペアがある | 1 |
| wet | connected (gap ≤ 2) または monotone | 2 |

### 3. DV (draw value)

| DV | 該当 draw | outs 換算 |
|----|----------|---:|
| 4 | combo draw (FD + straight draw) | ~15 outs |
| 3 | flush draw / nut flush draw / OESD | 8-9 outs |
| 1 | gutshot / backdoor FD (2 cards) | 4 outs / 2 |
| 0 | no draw | 0 |

→ おおよそ **DV ≈ outs / 3-4** で覚えやすい

### 4. overcards (自分のカード rank > board high の数)

| overcards | 例 |
|-----------|---|
| 0 | AKo on Q-J-2 で hero K (= board の K or Q) |
| 1 | AKo on Q-7-2 で hero A は overcard、K も overcard? |
| 2 | AKo on 7-5-2 で hero A, K どちらも overcard |

(注: hero が pair した場合は overcards 計算対象外)

### 5. pot (相手 range の強さ)

| pot type | 値 |
|----------|---:|
| SRP (single raised pot) | 0 |
| DEF (CR/donk defense) | 2 |
| 3BP (3-bet pot) | 2 |
| 4BP (4-bet pot) | 4 |

### 6. bs (相手の bet size、% of pot)

| bs | 該当 | 値 |
|----|------|---:|
| small | ~33% | 0 |
| 75% | 60-80% | 1 |
| 100% | 90-110% | 2 |
| overbet | 110-150% | 3 |
| overbet 185% | 160-200% | 4 |
| allin | >200% or jam | 5 |

---

## Grid (18 cells)

**自分の tier × board の lookup 表**

| 自分の手役 | dry | paired | wet |
|----------|---:|---:|---:|
| 🥇 ナッツメイド | **11** | 9 | 9 |
| 🥈 ストロング (set+) | 7 | 10 | **12** |
| 🥉 ツーペア | 2 | **14** | 0 |
| ⭐ トップペア以上 | **13** | 2 | 2 |
| 🟢 ミドルペア | 7 | 12 | 4 |
| 🔴 エア | 0 | 2 | **-3** |

### Grid 値の根拠 (data 駆動の意味)

| spot | 値 | 解釈 |
|------|---:|------|
| TP+ × dry = **13** | 最高 | TPTK 系の最強 spot |
| 2P × paired = **14** | 最高 | top set / FH range |
| ストロング × wet = **12** | 高 | flush 完成 / straight 完成 |
| ナッツ × dry = **11** | 高 | 確実 nut |
| ミドル × paired = **12** | 中高 | under-FH 警戒で慎重 call |
| エア × dry = **0** | 中性 | 大きな bet には fold |
| エア × wet = **-3** | 最低 | 即降り (相手 draw も持つ) |
| 2P × connected/mono (wet) = **0** | 低 | board crushed リスク |
| TP+ × paired = **2** | 低 | trip / FH 警戒 |

---

## 暗算 example 5 つ

### 例 1: SRP / TPTK (AK on K72 dry) / 相手 33% bet
```
tier=2 (TP+)、Grid[TP+][dry]=13
DV=0、overcards=1 (A が overcard)、pot=0、bs=0

Score = 4×2 + 13 + 3×0 + 2×1 + 3×0 − 2×0 − 2
      = 8 + 13 + 0 + 2 + 0 − 0 − 2 = 21

→ Score 21、6 ≤ 21 < 33 → call ✓
```

### 例 2: 4BP / KK (overpair) on K-Q-T / 相手 overbet
```
tier=2 (TP+)、Grid[TP+][wet]=2
DV=0、overcards=0、pot=4 (4BP)、bs=3 (overbet)

Score = 4×2 + 2 + 0 + 0 + 12 − 6 − 2 = 14

→ call (33 未満)
```

### 例 3: SRP river / ナッツストレート / 相手 100% bet
```
tier=4 (ストロング、straight)、Grid[ストロング][wet]=12
DV=0 (完成済)、overcards=0、pot=0、bs=2

Score = 4×4 + 12 + 0 + 0 + 0 − 4 − 2 = 22

→ call (33 未満なら raise しない)
```

### 例 4: SRP / エア on connected / 相手 overbet 185%
```
tier=0 (エア)、Grid[エア][wet]=-3
DV=0、overcards=0、pot=0、bs=4 (overbet 185%)

Score = 0 + (-3) + 0 + 0 + 0 − 8 − 2 = -13

→ -13 < 6 → fold ✓
```

### 例 5: 4BP / ナッツメイド (full house) on paired / 相手 allin
```
tier=5 (ナッツ)、Grid[ナッツ][paired]=9
DV=0、overcards=0、pot=4 (4BP)、bs=5 (allin)

Score = 4×5 + 9 + 0 + 0 + 12 − 10 − 2 = 29

→ 29 < 33 → call (raise の閾値超えない)
```

### 例 6: draw の評価 — AhKh on Qh-Jh-2 (combo draw)
```
tier=0 (エア)、Grid[エア][wet]=-3
DV=4 (combo)、overcards=2、pot=0、bs=2 (vs 100%)

Score = 0 + (-3) + 12 + 4 + 0 − 4 − 2 = 7

→ 7 ≥ 6 → call ✓ (draw + 2 overs で defensible)
```

### 例 7: 同じ board で gutshot のみ — AKo on Q-J-2
```
tier=0、Grid[エア][wet]=-3
DV=1 (gutshot)、overcards=2、pot=0、bs=2

Score = 0 + (-3) + 3 + 4 + 0 − 4 − 2 = -2

→ -2 < 6 → fold (gutshot だけでは弱い)
```

---

## 7 つの「公式の例外」(huge loss 分析より)

公式が誤判定しやすい spot。書籍ではコラムとして掲載推奨:

| # | spot | 公式 | GTO 正解 | 損失 (huge avg) |
|---|------|------|---------|---:|
| 1 | エア × wet × 4BP | fold | **call** (MDF) | 6.84 BB |
| 2 | ミドルペア × paired × 4BP | call | **raise** | 5.83 BB |
| 3 | エア × dry × DEF | call | **fold** (痛い catch) | 9.02 BB |
| 4 | **ストロング × wet × SRP** | call | **fold or raise** | 14-16 BB |
| 5 | ミドルペア × wet × DEF | call | **fold** | 9.88 BB |
| 6 | エア × wet × 3BP | fold | **call** (MDF) | 7.22 BB |
| 7 | **ナッツメイド × wet × SRP** | call | **raise** (機会損失) | 15.15 BB |

→ 例外 7 ルール暗記で実用 loss が **0.42 → 0.30 BB 程度**に下がる見込み

---

## 暗記項目総数

| 内容 | 項目数 |
|------|---:|
| 軸の値 (tier 6 + board 3 + DV 5 + pot 4 + bs 6) | 24 |
| Grid (3 列 × 6 行 = 18 cells) | 18 |
| Base weights (4, 3, 2, 3, 2) | 5 |
| Intercept (-2) | 1 |
| Threshold (6, 33) | 2 |
| **合計 (公式)** | **50** |
| 例外ルール | 7 |
| **総合計** | **57** |

### Sklansky/Chen 系譜との比較

| 公式 | params | 範囲 | 100hands 想定 loss |
|------|---:|------|---:|
| Sklansky Hand Groups | 8 groups | preflop only | ~80 BB |
| Chen Formula | 10 rules | preflop only | ~50 BB |
| **MATCHA Score Final** | **57** | **postflop 全域** | **~21 BB** |

→ Chen Formula の **postflop 拡張版**。範囲広がる分パラメータ 6 倍、loss 1/2.5。

---

## 設計の根拠 (data 駆動の発見)

### 1. tier × board interaction を Grid で吸収

線形だけでは 60% accuracy 限界 (= DT depth 3 と同じ表現力)。Grid (18 cells) が non-linear interaction を捕捉:
- TP+ × dry = 13 (TPTK 最強)
- 2P × paired = 14 (top set/FH)
- エア × wet = -3 (即降り)

### 2. board は 3 段階で十分

connected と monotone を **wet** に統合:
- 両方とも「draw が多い board」で行動類似
- 4 → 3 で cells 25% 削減、整数化への耐性が上がる
- 24 cells より 18 cells で loss 改善 (0.48 → 0.42)

### 3. tier は 6 段階を保持

3 や 4 に圧縮すると整数化で粒度損失:
- 9 cells (3×3): 0.66 BB
- 12 cells (4×3): 0.62 BB
- 16 cells (4×4): 0.66 BB
- **18 cells (6×3): 0.42 BB** ← 最強

### 4. 補正項は不要 (単一 grid + 加算が最良)

補正項を増やすと過剰適合:
- v2 (24 + 9 補正): loss 0.65 BB ← 悪化
- v5 (multi-grid 30 cells): loss 1.29 BB ← 大悪化
- **Single grid (18 cells) + base weights が data 駆動最適**

### 5. accuracy ではなく loss を最小化

「accuracy 70% より loss 0.42 BB」を直接目標に最適化:
- ミドル × paired = 12 (call で誤判定しても loss 小)
- 2P × paired = 14 (quads risk まれ、call が EV+)

---

## 探索した代替案 (全て劣等と確認)

| 候補 | loss | 理由 |
|------|---:|------|
| **18 cells (本) ✅** | **0.42 BB** | 確定版 |
| td4 × b4 + DV (16 cells) | 0.44 | tier 圧縮で情報損 |
| v1 (24 single grid) | 0.48 | board 過剰細分化 |
| outs direct 自由係数 | 0.45 | 整数化粒度損失 |
| outs direct 係数=1 | 0.52 | 制約強すぎ |
| v3 (9 + 4 補正) | 0.61 | grid 圧縮 + 補正 |
| v5 (multi-grid 30) | 1.29 | 軸重複で干渉 |

---

## 真の上限 (非線形モデル)

| モデル | accuracy | loss |
|--------|---:|---:|
| MATCHA Score Final (線形 + grid) | 69.4% | 0.42 BB |
| DT depth 5 | 64.3% | — |
| DT depth 10 | 74.6% | — |
| Random Forest | 76.6% | — |
| 真の上限 | ~77% | ~0.30 BB |

→ 線形 + grid では 0.42 BB が構造上の限界。さらに上は非線形 (Decision Tree) が必要 → アプリ・solver 実装向け。

---

## 書籍 / drill への反映

### 書籍構成案

**Vol2 巻末「MATCHA Score」章:**
1. 公式 (この doc の冒頭)
2. 軸の値表 (6 軸)
3. Grid 表 (18 cells)
4. 例題 5 つ (上記)
5. 7 つの例外コラム
6. 設計の根拠 (なぜ data 駆動でこの形か)

### drill 構成案

**新規 deck:**
1. **「MATCHA Score 計算問題」** (30 cards) — 公式適用問題
2. **「公式の例外」** (7 cards) — 例外ルールを覚える drill
3. **「Grid 18-cell 暗記」** (18 cards) — 各 cell の値を当てるクイズ
4. **「軸の値」** (24 cards) — tier/board/DV/pot/bs の値を覚える

---

## 関連ファイル

- 最終最適化 script: `scripts/three_class_model/optimize_grid_sizes.py`
- huge loss 分析: `scripts/three_class_model/analyze_huge_loss_final.py`
- 探索した代替案: `optimize_action_loss_v2.py`, `optimize_compressed_v3.py`, `optimize_multigrid_v4/v5.py`, `optimize_outs_*.py`
- DT 比較: `eq_decision_tree.py`
- huge loss report: `HUGE_LOSS_FINAL.md`

---

## 次のアクション (反映フェーズ)

1. **Vol2 巻末「MATCHA Score」章 MD 執筆** (本 doc 元に書籍化)
2. **drill generator 4 種作成** (計算問題 / 例外 / Grid / 軸)
3. **既存 drill との連携配線** (decks.ts に登録)
4. **書籍 build + KDP 化**

---

**MATCHA Score Final 確定日**: 2026-06-08
**累計 optuna 探索**: 12 variants × ~30,000 trials
**最終 dataset**: 293K rows (Cash + MTT + 全 phase 統合)
