# MATCHA 5 軸の境界 — 完全 data 裏付け (2026-06-08)

MATCHA Framework の 5 判定軸すべて (Range Morphology / Hand Strength / Bet Sizing /
SPR / Equity Bucket) の境界を実 GTO data で裏付けた日。

詳細別ドキュメント:
- SPR: `INSIGHTS_2026-06-08.md`
- Board / Hand Strength: `INSIGHTS_2026-06-08_BOARDS_HANDS.md`
- 残 3 軸 (Bet Sizing / Defense / Turn-River): `REMAINING_AXES_ANALYSIS.md`
- Equity Bucket: `EQUITY_BUCKET_BOUNDARIES.md`
- Bet Sizing 詳細: `BET_SIZING_BOUNDARIES.md`

本ドキュメントは 5 軸の境界を一覧化したサマリー。

---

## 5 軸の境界一覧

### 1. Range Morphology (board 分類)

13 sub-family × cbet 平均 (BTN attacker、Cash100 SRP):

| empirical class | sub-family | cbet 平均 | 範囲 |
|----------------|-----------|---------:|------|
| **MERGED** (>45%) | paired_low | 50.1% | 45-57% |
| | Khigh_spread | 48.0% | 44-50% |
| | Ahigh_spread | 46.0% | 25-50% |
| **CONDENSED** (40-45%) | broadway_dry | 44.9% | 28-52% |
| | paired_mid | 42.0% | 40-45% |
| | paired_high | 41.1% | 33-43% |
| | connected_low | 41.3% | 32-59% |
| **POLAR** (30-40%) | low_dry | 33.9% | 33-35% |
| | mid_dry | 33.3% | 28-39% |
| | connected_broadway | 32.5% | 17-40% |
| **POLAR extreme** (<30%) | monotone | 29.2% | 15-38% |
| | connected_mid | 28.5% | 21-48% |

現行 heuristic との一致率: **4/21 (19%)** → 修正必要 (low_dry → POLAR, paired_low → MERGED 等)

### 2. Hand Strength

6 カテゴリ × 42 boards 平均 cbet (BTN attacker):

| カテゴリ | avg cbet | 隣接差 | 境界明確性 |
|------|---:|---:|---|
| ナッツメイド (FH/quads) | 9% | — | (slowplay base) |
| ストロング (set/flush) | 29% | +20% | 🟢 明確 |
| **ツーペア** | **67%** | +38% | 🟢 明確 (peak) |
| トップペア+ | 52% | -15% | 🟢 明確 |
| ミドルペア | 24% | -28% | 🟢 明確 |
| エア (bluff) | 37% | +13% | 🟡 ある (逆転) |

**山型 (逆U字) パターン: ツーペアが最高頻度 (67%)**

### 3. Bet Sizing

実 GTO 使用 sizing (77 boards 集計):

| board family | dominant sizing | freq |
|--------------|----------------|------|
| dry MERGED (K72, paired_low) | small 33% (1.9bb) | 40-50% |
| connected wet (T98, 654) | large 100%+ (6.5bb) | 2-6% |
| broadway dry | small 33% | 40-50% |
| low_dry / mid_dry | large 100%+ | 33% |

**medium (50%) はほぼ未使用** → 2 段階 (small 33% / over 100%+) に簡略化可能。
MATCHA の 4 段階 → 2 段階で 90% カバー、`オーバーベット` を `ラージ` に rename 推奨。

### 4. SPR

同 board (Ks7d2c) × SPR variation の cbet 頻度:

| カテゴリ | SPR 1.3 (4BP) | SPR 3.4 (3BP) | SPR 8 (Cash50) | SPR 16 (Cash100) |
|------|---:|---:|---:|---:|
| ストロング (set) | **4%** | 41% | 69% | **96%** |
| ツーペア | 18% | 80% | 97% | 83% |
| トップペア+ | 61% | 70% | 68% | 61% |
| ミドルペア | **73%** | 49% | 43% | 55% |
| エア | 41% | 46% | 46% | 44% |

**SPR=3 が戦略反転点**:
- SPR<3: 強い手 slowplay (set 4%)
- SPR>3: 強い手 fastplay (set 96%)
- 4BP の jam reversal (ミドルペア > set)

MATCHA 4 段階 (オールイン<1 / ロー 1-3 / ミディアム 3-7 / ディープ>7) data 裏付け。

### 5. Equity Bucket

4 bucket の GTO 行動 (293K rows):

| bucket | avg eq | 境界 | fold% | call% | raise% |
|--------|---:|------|---:|---:|---:|
| best_hands | 87% | percentile ≥0.85 | 0% | 76% | **24%** |
| good_hands | 60% | 0.65-0.85 | 4% | 71% | **25%** |
| weak_hands | 40% | 0.35-0.65 | **43%** | 51% | 6% |
| trash_hands | 20% | <0.35 | **86%** | 12% | 2% |

eq_percentile 10% bin の transition:
- **40% bin で fold 48% → 28%** = call vs fold の決定境界
- **80% bin で raise 11% → 30%** = passive vs aggressive 境界

MATCHA 4 段階 (モンスター / 良ハンド / 弱ハンド / ブラフハンド) は完全裏付け。

---

## 5 軸の相互作用 (cross-axis)

### Hand Strength × SPR (set の例)

| SPR | cbet 頻度 | 戦略 |
|-----|---:|------|
| 1.3 | 4% | slowplay (trap) |
| 3.4 | 41% | mixed |
| 8 | 69% | value bet |
| 16 | 96% | 強制 value bet (multi-street) |

→ カテゴリ だけでなく SPR で行動激変。**MATCHA で SPR 軸の独立性が data 裏付け**。

### sub-family × Hand Strength (90 セル cross-tab)

特異な outlier:
- paired board × **ツーペア = 0%** (TP=quads vs you trap 回避)
- low_dry × ツーペア = 100% (range top)
- paired_high × TP+ = 21% (vulnerable)
- mid_dry × ミドルペア = 18% (pot-control)

→ カテゴリ 単独でなく、board × カテゴリ の cross-tab が必要。

---

## drill / 書籍への反映 (優先順)

### 即時 (drill カード裏面表)

1. **Hand Strength 章**: ツーペア peak 強調 (山型グラフ)
2. **SPR 章**: K72 × SPR variation を visual 化
3. **Range Morphology 章**: 13 sub-family table (data 駆動の classify_board)
4. **Bet Sizing 章**: 2 段階 (small / over) で運用
5. **Equity Bucket 章**: 0.40 / 0.80 の percentile 境界数値を明示

### 中期 (Vol2 章設計)

1. **TEA グリッド章**: 15 × 6 cross-tab を付録掲載
2. **3 モード章**: SPR 補正をモード判定に組み込み
3. **境界ハンド集**: SPR≈3 / paired×2P=0% / low_dry×2P=100% 等を暗記リスト

---

## 残課題

1. **defense 軸の細分化**: BB MDF は ~30% で一定確認したが、raise size の polar 度
   (dry 2.6x cbet, wet 5.4x cbet) を sub-family 全種で確認必要
2. **Turn/River 補正**: K72 progression で flop bet-call → turn check 100% 確認したが、
   wet board の同 progression 未取得
3. **opp range structure 軸** (Probe Priority Findings から): 5 軸目とは独立した新軸
   として MATCHA に統合検討

---

## 関連 commits

- `281ece5` spr-gradient: 同 K72 × SPR 1.3-16 で tier 別 cbet を実測
- `12b2b72` spr-boundaries: 293K rows から MATCHA SPR 4 段階を逆算検証
- `c934b4a` insights: board / hand strength 境界知見まとめ
- (本日 boundary 関連) Bet Sizing / Equity Bucket / Defense / Turn-River
