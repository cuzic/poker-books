# Probe Priority Findings — 未調査シナリオの huge_loss 測定

**生成**: 2026-06-05
**スクリプト**: `research/v4-postflop/probe_priority.py`
**生データ**: `research/v4-postflop/findings/probe_priority/*.json` (66 spots)
**集計**: `research/v4-postflop/probe_priority_{report.md, rows.csv, stats.json}`

## 1. 背景

2026-06-05 時点で Vol2/Vol3 旧版 (S/M/W/A/D × s/m/l/o マトリックス) は廃棄済 ([[project-postflop-3rule-formula]] 参照)、新公式 v9b/v10/v15 を確立。

| 公式 | in-domain | huge_loss (audit) |
|------|-----------|-------------------|
| Flop v9b | Cash100/MTT100 BB def | 0.061 / 0.129 BB |
| Turn v10 | Cash100/MTT50 BB def | 0.048 / 0.067 BB |
| River v15 | Cash100/MTT50 BB def | 0.212 / 0.130 BB |

しかし以下の **未調査シナリオ** は dataset_unified.csv にデータが存在しないため、公式が当てはまるか不明:

- depth diff: MTT25/MTT100/MTT200 river, MTT200 turn
- pot_type diff: 3BP / 4BP postflop (Cash100, MTT100 とも)
- action context: CR 防御 / donk 防御 (BTN IP defender)
- position diff: BB 以外 (BTN/CO/HJ/SB) の postflop defender

これら **どこから本格 fetch するか** を決定するため、各シナリオを 6 board だけ先行 probe して formula_loss を直接測定した。

## 2. 設計

### 2.1 CORE_BOARDS (全 scenario 共通サンプル)

| board | label | family |
|-------|-------|--------|
| Ks7d2c | dry_K72 | dry_high |
| 8s5d3h | low_853 | low_dry |
| Th9c7s | dyn_T97 | dynamic |
| Ts9s7c | d2t_T97 | dynamic_2tone |
| KsKd2c | pair_KK2 | paired |
| Js7s3s | mono_Js | monotone |

全 6 family を 1 枚ずつ + turn/river は重複回避で動的選択。

### 2.2 SCENARIOS (13 件)

| ID | desc | GT | depth | target |
|----|------|----|----|------|
| B_flop | [BASELINE] Cash100 SRP flop BB def | Cash6mTest | 100 | flop_def_oop |
| B_turn | [BASELINE] Cash100 SRP turn BB def | Cash6mTest | 100 | turn_def_oop |
| B_river | [BASELINE] Cash100 SRP river BB def | Cash6mTest | 100 | river_def_oop |
| N_cash_3bp_flop | Cash100 3BP flop BB def (3bettor OOP) | Cash6mTest | 100 | flop_def_oop |
| N_cash_3bp_river | Cash100 3BP river BB def | Cash6mTest | 100 | river_def_oop |
| N_cash_4bp_flop | Cash100 4BP flop BB def (SPR ~1) | Cash6mTest | 100 | flop_def_oop |
| N_cash_cr_def | Cash100 SRP flop BTN def vs BB CR | Cash6mTest | 100 | flop_def_ip_cr |
| N_cash_donk_def | Cash100 SRP flop BTN def vs BB donk | Cash6mTest | 100 | flop_def_ip_donk |
| N_mtt100_river | MTT100 SRP river BB def | MTT 8m | 100 | river_def_oop |
| N_mtt25_river | MTT25 SRP river BB def (short stack) | MTT 8m | 25 | river_def_oop |
| N_mtt200_turn | MTT200 SRP turn BB def (deep) | MTT 8m | 200 | turn_def_oop |
| N_mtt200_river ⚠ | MTT200 SRP river BB def | MTT 8m | 200 | river_def_oop |
| N_mtt_3bp_flop ⚠ | MTT100 3BP flop BB def | MTT 8m | 100 | flop_def_oop |

⚠ 印 = daily quota 切れで未取得 (2026-06-06 以降に再 fetch 可能)

### 2.3 Metric (各 combo × 各 scenario)

```
formula_action = v9b/v10/v15(mv_cat, dv_cat, equity_bucket, board_family, bet_size)
best_action    = argmax_action ev_action  (GTO 上の最適)
formula_loss   = best_ev − ev_of_formula_action  (>= 0)
formula_huge_loss = mean(formula_loss | formula_loss > 0.5 BB)  (公式が外した時の平均損失)
formula_acc    = P(formula_action == best_action)
bimodal_combo% = P(min(top2_freq) / total_freq > 0.2)  (1 hand 内で freq 二分する combo の割合)
```

CR / donk / IP defender ターゲットは専用公式がないため formula 系列は N/A、`huge_loss` (formula 非依存) と `bimodal%` のみ評価。

## 3. 重要な技術的注意点

### 3.1 MTT 8m API は `depth` も `.125` 形式が必須

memory `project-gtow-api-v4-postflop` には `stacks` の `.125` 形式は記載されていたが、**`depth` 自体も `.125` が必要**な点は記録漏れだった (初回 run で MTT 全 scenario 403 となり判明)。

```python
# Cash
params["depth"] = "100"               # OK
# MTT
params["depth"] = "100.125"           # OK (整数だと 403)
params["stacks"] = "100.125-100.125-...-100.125" # OK
```

検証結果 (取得可能 depth):

| depth | Cash6mTest | MTTGeneral_8m |
|-------|------------|---------------|
| 10–60 | — | ✅ 全 OK |
| 75 | — | ❌ 403 (pre-computed なし) |
| 100 | ✅ | ✅ |
| 200 | — | ✅ |

### 3.2 `gto_api.GT` は module-level 変数

scenario ごとに gametype を切り替えるとき、`os.environ["GT"] = gt` だけでは反映されない (gto_api.py は import 時に GT を読む)。`gto_api.GT = gt` で直接書き換える必要あり。これも初回 run の 403 原因の一つ。

### 3.3 既存 audit との metric 不一致

`mtt_formula_audit.py` の huge_loss 値 (Cash100 v15 = 0.212 BB) と probe の値 (B_river = 19.472 BB) は **桁違いに乖離**。原因:

| 観点 | audit | probe |
|------|-------|-------|
| ev_gap 定義 | best − **2nd_best** | best − **worst** |
| huge filter | `ev_gap > 0.5` | `formula_loss > 0.5` |
| huge_loss 分母 | 全 ev_gap>0.5 行 (97% は loss=0) | formula_loss>0.5 行 (公式 miss のみ) |

→ **probe の絶対値は audit と直接比較できない**。
→ probe の **相対順位 / per-board variance** は valid。
→ baseline scenario (B_flop/B_turn/B_river) を含めることで probe 内での比較 anchor として機能。

probe metric の意味: 「公式が外した時、どれだけ EV を失うか」。
audit metric の意味: 「全 consequential 決断で、公式の平均損失はどれだけか」。
両方妥当だが、priority 判定には probe metric (per-miss bleed) が直接的。

## 4. 結果ランキング (formula_huge_loss 降順、11 scenarios)

| Rank | ID | f_acc | f_mean_loss | f_huge_loss | f_huge% | bimodal% | n_combos |
|------|----|------:|------------:|------------:|--------:|---------:|---------:|
| 1 | **N_cash_3bp_river** | 79.7% | 3.89 | **21.8 BB** | 17.8% | 5.1% | 6486 |
| 2 | **N_mtt100_river** | 86.0% | 1.84 | **19.6 BB** | 9.3% | 4.7% | 6486 |
| 3 | **B_river** (BASELINE) | 81.3% | 2.00 | **19.5 BB** | 10.2% | 7.7% | 3709 |
| 4 | **N_mtt25_river** | 79.6% | 1.07 | **8.8 BB** | 12.0% | 6.8% | 5050 |
| 5 | **N_cash_4bp_flop** | **43.9%** | 2.14 | 4.8 BB | **43.8%** | 21.4% | 7056 |
| 6 | **N_mtt200_turn** | 71.6% | 0.48 | 2.8 BB | 16.7% | 8.6% | 4512 |
| 7 | **N_cash_3bp_flop** | 66.6% | 0.33 | 2.1 BB | 14.7% | 19.9% | 7056 |
| 8 | B_turn (BASELINE) | 71.3% | 0.23 | 1.9 BB | 10.9% | 8.8% | 3900 |
| 9 | B_flop (BASELINE) | 71.7% | 0.06 | 0.9 BB | 3.8% | 26.9% | 3996 |
| 10 | N_cash_cr_def | — | — | — | — | 14.9% | 3127 |
| 11 | N_cash_donk_def | — | — | — | — | 20.7% | 3127 |

## 5. Tier 別解釈

### Tier A: 公式の前提が破綻 (acc < 70% or 巨大絶対損失)

**N_cash_4bp_flop** (acc 43.9%)
- 4BP は SPR ~1 で公式 (SPR ~10 想定) の構造が崩壊
- formula_huge% = 43.8% (combo の 4 割で公式が外す)
- 全 board で uniform に bleed (per-board variance 小、low_853=16.7 / pair_KK2=18.2)
- → **専用公式が必要** (4BP は別ロジック)

**N_cash_3bp_river** (huge_loss 21.8 BB)
- v15 は SRP river fit、3BP river は domain 外
- per-board variance 中 (mono_Js=19.8 / dyn_T97=33.2)
- bet_size R58-75 という大型 bet (3BP は pot 大、river bet が allin-near)
- → **3BP river 専用公式が必要**

### Tier B: depth 軸 (MTT 公式が必要)

**N_mtt100_river** (huge_loss 19.6 BB, acc 86%)
- v15 は MTT50 fit、100bb で per-miss bleed 大
- per-board variance 巨大 (mono_Js=7.3 vs d2t_T97=37.2、5x 差)
- → **MTT100 専用 river 公式の必要性 確認**

**N_mtt25_river** (huge_loss 8.8 BB, acc 79.6%)
- 短スタック (max bleed = stack の制約で物理上限 25 BB)
- per-board variance 小 (全 board ~10-12 BB)
- → 公式拡張は中程度の優先

**N_mtt200_turn** (huge_loss 2.8 BB, acc 71.6%, baseline turn 比 -10pp)
- deep SPR で v10 fit 悪化
- low_853 だけ突出 (12.8 BB) — 他 board ~4-5 BB
- 4/6 board のみ取得 (quota 切れ)
- → 翌日に残 board 取得、追加 fetch 検討

### Tier C: 公式 N/A (専用公式が必要)

**N_cash_cr_def** (CR 防御、BTN IP defender)
- bimodal 14.9%, huge_loss 6.6, n=3127
- 動的 (dyn_T97=10.4, d2t_T97=8.3) は bleed 大、dry/mono は小 (3-4)
- → 専用公式 candidate (Tier 2)

**N_cash_donk_def** (donk 防御、BTN IP defender)
- bimodal 20.7%, huge_loss 3.0, n=3127
- pair_KK2 だけ突出 (6.5)、他は ~2-3
- → 専用公式 candidate (Tier 2)

### Tier D: baseline 近い (3BP flop は SRP flop と類似)

**N_cash_3bp_flop** (acc 66.6%, baseline 71.7% に近い)
- formula_huge% 14.7% (baseline 3.8% より高いが huge_loss 自体は 2.1 BB)
- → 3BP flop は SRP flop と公式構造が共通 (board × mv × dv 軸で fit 流用可)

## 6. 定性的発見

1. **River 系の per-board variance が極端**
   - B_river: low_853=39.9 vs mono_Js=7.4 (5x)、N_mtt100_river: d2t_T97=37.2 vs mono_Js=7.3
   - → river 公式は **board_family の粒度に強く依存** (粒度を上げれば fit 改善余地大)

2. **MTT vs Cash の acc 比較**
   - N_mtt100_river acc 86.0% > B_river 81.3%
   - MTT のほうが GTO が一貫 (CALL/FOLD 二分が明確、RAISE 0%)
   - Cash は RAISE 6.3% を含み 3-way 決断が多い

3. **4BP は完全に別ゲーム**
   - acc 43.9% = ほぼ random (3 択での coin flip + 微優位)
   - FOLD 17% / CALL 57% / RAISE 26% と分散
   - SPR ~1 で「shove or fold」と「marginal call」の境界判定が支配的

4. **CR/donk は modal split が均衡**
   - N_cash_cr_def: FOLD 45.0% / CALL 51.1% / RAISE 3.8%
   - N_cash_donk_def: FOLD 46.7% / CALL 44.9% / RAISE 8.4%
   - → 1 action 出力では原理的に miss、閾値判定が必須

## 7. 次のアクション

### 即時 (今日)
- [x] probe_priority.py 実装 + 13 scenario 設計
- [x] 11 scenarios fetch 完了 (66 spots, 54,505 hand-level rows)
- [x] 本ドキュメント作成
- [ ] commit (script + findings + report)

### 翌日 (2026-06-06 — daily quota 復活後)
- [ ] N_mtt200_river の残 6 spots fetch
- [ ] N_mtt_3bp_flop の 6 spots fetch
- [ ] N_mtt200_turn の残 2 boards (pair_KK2, mono_Js) fetch
- [ ] report 再生成 (13 scenarios complete)

### 本格 fetch スクリプト設計 (probe 結果を基に)

優先順:

1. **`r5_cash_4bp.py`** — Cash100 4BP postflop full (flop/turn/river × 50 boards × 全 position)
   - 推定 ~600 spots
   - 理由: acc 43.9% で公式破綻、最大優先

2. **`r5_cash_3bp.py`** — Cash100 3BP postflop full
   - 推定 ~500 spots
   - 理由: 3BP river huge_loss 21.8 BB、最大絶対損失

3. **`r5_mtt_8m_srp_river.py`** — MTT 8m × depth [25/50/100/200] × river × 50 boards
   - 推定 ~800 spots
   - 理由: river 公式の depth 軸が全 depth で確認必要

4. **`r5_cr_donk_def.py`** — Cash100 SRP CR/donk × 30 boards
   - 推定 ~200 spots
   - 理由: 公式 0、bimodal 高い (新規モデル化が必要)

5. **`r5_mtt_3bp.py`** — MTT100 3BP postflop
   - 推定 ~400 spots
   - 理由: Cash 3BP と比較して MTT depth 補正の必要性確認

**合計 ~2500 spots ≈ 8 日 (daily quota 300/day)**

## 8. 既知の限界と再現性

### probe の限界
- 6 board × 1 turn × 1 river は **trajectory の代表性が限定**
- 本格 fetch では turn × river を多様化 (3-5 通り) する必要
- 単一の bet size のみ捕捉 (例: B_river は cbet R1.5/barrel R15.6 のみ) → bet size sensitivity 未検証

### baseline calibration の問題
- B_flop/B_turn/B_river の probe 値が既存 audit と乖離 (前述の metric 違い)
- baseline は **probe 内での anchor** として機能するが、本格 fetch を始める前に metric 一致版の probe を 1 回追加すれば確実

### N_mtt200_turn は partial
- 4/6 board のみ。残 2 を quota 復活後に取得して結論確定

## 9. 関連ファイル

| Path | 内容 |
|------|------|
| `research/v4-postflop/probe_priority.py` | probe スクリプト (706 lines) |
| `research/v4-postflop/probe_priority_report.md` | 自動生成レポート (ランキング + 詳細) |
| `research/v4-postflop/probe_priority_rows.csv` | hand-level CSV (54,505 rows) |
| `research/v4-postflop/probe_priority_stats.json` | scenario level stats (sortable) |
| `research/v4-postflop/findings/probe_priority/*.json` | 生 API response (66 spots) |
| `research/v4-postflop/probe_priority_log.jsonl` | fetch log |

## 10. 関連メモリ

- [[project-postflop-3rule-formula]] — v9b/v10/v15 公式の現状実測精度
- [[project-gtow-api-v4-postflop]] — GTO Wizard API 取得可能性 + R1 (river allin) 既存データ
- [[project-mtt-postflop-gto-data]] — 過去の MTT 25/50/100bb 6m データ収集
