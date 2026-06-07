# Postflop Decision Framework v7 — 3-band + Confidence Tier

**Generated**: 2026-06-01
**Data source**: 209,071 records from 384 GTO Wizard spots (mostly attack, 10 defense)
**Status**: Attack-side complete, Defense awaiting more data

---

## 1. The Core Question Restated

In No Limit Hold'em postflop, the user wants:

> 「現在の確率空間内で自分のハンドはどの程度の強さで、ドローによってどの程度の強さになる可能性があるか」を知って、それに基づいて BET / CHECK / FOLD / CALL / RAISE を決めたい。

The framework's job: convert (current hand, board, position, opponent) into a recommended action with calibrated confidence.

---

## 2. Three-Layer Decision

### Layer 1: Determine your equity bucket (4 levels)

| bucket | rough meaning | example |
|---|---|---|
| **best** | 強ハンド層 (top 15-25%) | overpair, 2P+, set, TPGK on dry |
| **good** | 中強層 (25-50%) | TP-weak-kicker, 強 PP, second pair |
| **weak** | 中弱層 (50-75%) | third pair, underpair, A-high+blocker |
| **trash** | 最弱層 (bottom 25%) | no_made, low/weak pair on overcard board |

### Layer 2: Apply DV (Draw Value) refinement

| DV | 効果 |
|---|---|
| **強 (FD/OESD/combo)** | +20-30 pp on bet_freq |
| 中 (gutshot) | +10-15 pp |
| 弱 (BDFD/onecard_bdfd) | +5-10 pp |
| 無 (no_draw) | baseline |

### Layer 3: Board family correction

| board family | bet 寄り傾向 |
|---|---|
| **paired** | +20 pp (全 bucket 強化) |
| dynamic | +5-10 pp (連結性で保護) |
| dynamic_2tone | +0 pp |
| dry_high | 0 (baseline) |
| low_dry | -5 pp |
| **monotone** | -20 pp (全 bucket 弱化) |

---

## 3. 3-band Output: LOW / MIX / HIGH

| band | bet 頻度 | 推奨行動 |
|---|---|---|
| **LOW** | <25% | ほぼ CHECK |
| **MIX** | 25-75% | 混合戦略（時計の秒数等で randomize） |
| **HIGH** | ≥75% | ほぼ BET |

**Overall accuracy: 61.0%**

### 予測クラス別精度

| 予測 | precision | 解釈 |
|---|---:|---|
| LOW | 68.5% | 大きな塊、概ね信頼可 |
| MIX | 38.7% | 混合は本質的に予測困難 |
| HIGH | 61.3% | 信頼可、ただし小さい母数 |

---

## 4. Confidence Tier（HIGH/MED/LOW）

各セル（bucket × MV × board × DV）の IQR（Q75 - Q25）から信頼度を算出：

| Tier | IQR 範囲 | cells | カバー率 | Exact 精度 |
|---|---|---:|---:|---:|
| **HIGH** | <10% | 61 | 14% | **85.5%** ✓ |
| **MED** | 10-30% | 82 | 11% | **75.6%** |
| **LOW** | >30% | 230 | 75% | 54.3% |

→ **HIGH + MED 合計 25% のセルは 80%+ 精度** で予測可。残り 75% は混合戦略の本質的限界。

---

## 5. HIGH Tier セル（「ノータイム決定」一覧）

```
trash × weak_pair  × dry_high  × no_draw  med=0%  iqr=3%   → LOW
trash × third_pair × dry_high  × no_draw  med=0%  iqr=2%   → LOW
trash × weak_pair  × dynamic   × no_draw  med=0%  iqr=3%   → LOW
trash × third_pair × dynamic   × no_draw  med=0%  iqr=3%   → LOW
trash × third_pair × monotone  × no_draw  med=0%  iqr=0%   → LOW (100%!)
weak  × second_pair × dry_high × no_draw  med=0%  iqr=5%   → LOW
good  × 2P+        × monotone  × no_draw  med=0%  iqr=1%   → LOW
（他 54 セル、計 61）
```

これらが**「迷わず check (or bet)」スポット**。書籍で「暗記対象」になるのは主にこの 61 セル。

---

## 6. LOW Tier セル（「混合戦略、ランダム化」）

```
best  × 2P+      × dry_high × no_draw  med=48%  iqr=94%  → MIX  ← 完全ランダム
best  × 2P+      × dynamic  × no_draw  med=57%  iqr=91%  → MIX
best  × top_pair × dry_high × no_draw  med=55%  iqr=65%  → MIX
trash × no_made  × dry_high × no_draw  med=1%   iqr=56%  → LOW (但し 17% が MIX、15% が HIGH)
（他 226 セル、計 230）
```

これらは**「ハンド単独で決まらず、ブロッカー・スーツ・combo 特定の細部で決まる」スポット**。簡易表では捉えきれない。

---

## 7. 旧フレーム（25 セル + α/β/cat/ε）との比較

| 観点 | 旧 (Vol2/Vol3) | 新 v7 |
|---|---|---|
| 入力軸 | TV (=MV+DV) | bucket + MV + DV + board |
| 出力 | bet 頻度 % | 3-band (LOW/MIX/HIGH) + 信頼度タグ |
| パラメータ数 | 63 | 373 セル（表参照） |
| 計算ステップ | 7 (base+4 補正) | 1 (lookup) |
| 混合戦略の扱い | 隠れる (50% で切る) | 明示 (MIX band) |
| 「予測不能」の扱い | 認めず | 認める (LOW tier として) |

---

## 8. 残課題

### A. Defense データ不足
現在 10 spot のみ。次フェッチサイクルで以下を取得予定：
- 4 defense context（cbet_def / 2nd_def / probe_def）
- 3 bet size（33% / 50% / 110% pot）
- 2 stack depth（100bb / 200bb）
- 計 ~360 spot（CSV 設計済 → `designed_defense.csv`）

### B. best × 2P+ on flop の本質的予測困難
IQR 90%+ で combo 単位の差が支配的。これは「**ブロッカー / バックドア / suit constraint** がトップレベルで効く混合戦略 spot」であり、簡易フレームでは原理的に解決不能。

### C. ev_gap layer の活用
ev_gap > 0.5 のスポット（27%）は明確に best action がある。フレームと組み合わせることで、HIGH tier セルを拡張する余地あり。

---

## 9. 書籍向け章構成案（Vol2/Vol3 改訂）

```
第 1 章：4-bucket equity 判定（best / good / weak / trash）
  - MV/DV からの bucket 割当ルール
  - 旧 25 セルの「band」概念を bucket に置換

第 2 章：3-band 出力（LOW / MIX / HIGH）
  - 混合戦略を明示的に MIX として認める
  - LOW = check 寄り、HIGH = bet 寄り

第 3 章：信頼度ティア（HIGH/MED/LOW）
  - 「暗記対象」と「ランダム化対象」を切り分ける
  - HIGH tier 61 セルを暗記、その他は LOW tier として運用

第 4 章：攻撃 vs 守備（対称性）
  - BET → RAISE、CHECK → CALL、CHECK → FOLD のマッピング
  - MDF 制約の組み込み

付録 A：HIGH/MED tier セル一覧表（143 セル）
付録 B：LOW tier の MIX 内 randomization 戦略
```

---

## 10. 成果物ファイル

| ファイル | 内容 |
|---|---|
| `dataset_with_buckets.csv` | 209k 行、equity_bucket 付き |
| `cell_with_confidence.csv` | 373 セル、median/IQR/pred/confidence |
| `v7_3band_table.csv` | 373 セル、3-band 版 |
| `data_driven_tables.yaml` | YAML 機械可読セル値 |
| `DATA_DRIVEN_FRAMEWORK_REPORT.md` | 初期版報告書 |

データ：394 spot with `equity_buckets`、すべて MTT6mSimple gametype。

---

**Next step**: Defense データ拡充（API rate limit recovery 待ち）後、上記 v7 フレームを defense 側に拡張、本格的な書籍章草稿に着手。
