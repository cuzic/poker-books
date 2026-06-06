# Probe Priority Findings — 公式適用域 + opp range structure の完全マップ

**生成**: 2026-06-05 / 2026-06-06 大幅拡張 (phase 3-6 + opp-side extraction + 過去 JSON 統合)
**スクリプト**: `research/v4-postflop/probe_priority.py` + `probe_phase{2,3,4,5,6}.py` + `extract_past.py`
**生データ**: `research/v4-postflop/findings/probe_{priority,phase{2,3,4,5,6}}/` 計 **334 spots**
**集計**: ~321K hand-level rows、6 commits

## 1. 目的と前提

2026-06-05 時点で Vol2/Vol3 旧版 (S/M/W/A/D × s/m/l/o マトリックス) は廃棄済 ([[project-postflop-3rule-formula]] 参照)、新公式 v9b/v10/v15 を確立。

公式の **in-domain** (audit huge_loss):

| 公式 | in-domain scenario | 既存 audit huge_loss |
|------|-----|---------------------|
| Flop v9b | Cash100/MTT100 SRP BB def | 0.061 / 0.129 BB |
| Turn v10 | Cash100/MTT50 SRP BB def | 0.048 / 0.067 BB |
| River v15 | Cash100/MTT50 SRP BB def | 0.212 / 0.130 BB |

しかし以下の **out-of-domain** が未調査だった: depth diff, pot type, opener position, defender position, action context, board family variance.

このプロジェクトは「**どこから本格 fetch するか**」を probe で決定する目的で開始したが、phase 4 以降は本格 fetch そのものへと進化し、最終的に **公式適用域 + opp range structure** の完全マップが完成した。

## 2. 設計と methodology

### 2.1 サンプル戦略

- **CORE_BOARDS 6 枚** (各 family 1 枚): Ks7d2c / 8s5d3h / Th9c7s / Ts9s7c / KsKd2c / Js7s3s
- **EXTENDED_BOARDS_18 枚** (各 family 3 枚): Tier A 拡張 / 公式 N/A 分析用
- turn/river: TURN_POOL/RIVER_POOL から動的選択 (board card と非重複)
- 重要シナリオは複数 trajectory (board × turn × river)

### 2.2 Metric (各 combo × 各 scenario)

```
formula_action = v9b/v10/v15(mv_cat, dv_cat, equity_bucket, board_family, bet_size)
best_action    = argmax_action ev_action  (GTO 上の最適)
formula_loss   = best_ev − ev_of_formula_action  (>= 0)
formula_huge_loss = mean(formula_loss | formula_loss > 0.5 BB)
formula_acc    = P(formula_action == best_action)
bimodal_combo% = P(min(top2_freq) / total_freq > 0.2)
```

### 2.3 opp-side extraction (2026-06-06 追加 ★★★)

雑談から発展して、**相手 range の structure** を全 spot で抽出する extractor を追加：

- spot-level: `opp_polarization` (strong+weak/total), `opp_strong_pct`, `opp_weak_pct`,
  `opp_nut_class` (board family の典型 nut class), `opp_nut_pct`, `opp_nut_eq_median`
- per-combo: `opp_bucket`, `opp_eq`, `opp_eq_percentile`, `hand_eq_vs_opp_nut`

→ 「相手 range が polar か merged か」「相手の nut tier の比率」「自分のハンドが相手 nut tier より強いか」を全 spot で定量化。

### 2.4 過去 JSON 再処理 (extract_past.py)

R1 (62 spots) と R3 (48 spots) を新 extractor で再処理し、110 spot summaries を取得。

## 3. 技術的注意点 (実装で学んだ落とし穴)

### 3.1 MTT 8m API は `depth` も `.125` 形式が必須

memory `project-gtow-api-v4-postflop` には `stacks` の `.125` 形式は記載されていたが、
**`depth` 自体も `.125` が必要**な点は記録漏れだった (phase priority run で MTT 全 scenario 403 となり判明)。

```python
# Cash
params["depth"] = "100"          # OK
# MTT (重要)
params["depth"] = "100.125"      # OK (整数だと 403)
params["stacks"] = "100.125-100.125-...-100.125"
```

検証結果 (取得可能 depth on MTTGeneral_8m):
| depth | 結果 |
|-------|------|
| 10–60 | ✅ |
| **75** | ❌ 403 (pre-computed なし) |
| 100, 200 | ✅ |

### 3.2 `gto_api.GT` は module-level 変数

scenario ごとに gametype を切り替えるとき、`os.environ["GT"] = gt` だけでは反映されない。
gto_api.py は module-load 時に GT を読むので、`gto_api.GT = gt` で直接書き換える必要あり。

### 3.3 既存 audit との metric 不一致

`mtt_formula_audit.py` の huge_loss 値 (Cash100 v15 = 0.212 BB) と probe の値 (B_river = 19.472 BB) は **桁違いに乖離**。原因:

| 観点 | audit | probe |
|------|-------|-------|
| ev_gap 定義 | best − **2nd_best** | best − **worst** |
| huge filter | `ev_gap > 0.5` | `formula_loss > 0.5` |
| huge_loss 分母 | 全 ev_gap>0.5 行 | formula_loss>0.5 行 |

→ **probe の絶対値は audit と直接比較できない**。  
→ probe の **相対順位 / per-board variance / opp range structure** は valid。

## 4. 6 Phase 一覧と成果

| Phase | spots | rows | calls | 主成果 |
|-------|------:|-----:|------:|---------|
| **priority** | 64 | 50K | ~234 | Tier A/B/C/D 確定、baseline probe |
| **phase2 + past** | 130 | 150K | ~228 | opp-side extraction 追加、R1/R3 再処理 |
| **phase3** | 30 | 25K | ~144 | CR/donk 拡張、opener × river、3BP allin の構造的不可能性 |
| **phase4** | 24 | 18K | ~90 | 4BP river の仮説覆し (polar じゃない)、BvB/SB defender |
| **phase5** | 70 | 60K | ~206 | matrix 完成、multi-street walker、opener × turn |
| **phase6** | 16 | 18K | ~78 | MTT 4BP = Cash 4BP 構造同一 確定 |
| **合計** | **334** | **321K** | **~980** | 公式適用域 + opp range の完全マップ |

## 5. 公式適用域マップ (Tier A/B/C/D)

### Tier A: 公式の前提が破綻 (公式 N/A 同等、専用ロジック必要)

**N_cash_4bp_flop / turn / river** (phase2 + phase4 で 18 boards + 16 trajectories + 4BP turn 確認)
- **flop acc=43.2%**, turn acc=49.4%, river acc=60.7%
- 4BP river は **opp_polarization=0.688** (SRP 0.95 と質的に違う)
- mid 31% (range tight で air 限定的、middling hand 多数)
- → SRP の bluff catcher 思考が機能しない、**専用ロジック必須**

**MTT 4BP (phase6 で確認)**
- flop acc=40.3%, turn acc=48.5%, river acc=60.6%
- → Cash 4BP と完全に同構造、**MTT 100bb 4BP は Cash 4BP 公式流用可**

### Tier B: 公式 fit は中程度、per-miss bleed 大

**MTT depth diff** (phase priority + phase2)
- N_mtt100_river acc=86.0%, f_huge_loss=19.6 BB
- N_mtt25_river acc=79.6%, f_huge_loss=8.8 BB (短スタックは bleed 小)
- N_mtt200_turn acc=71.6%, f_huge_loss=2.8 BB
- N_mtt200_river acc=76.1%
- → MTT100 river は v15 (MTT50 fit) で acc 高いが bleed 大

**3BP turn/river** (phase2 + phase5)
- Cash 3BP river f_huge_loss=21.8 BB
- Cash 3BP turn acc=66.3%, MTT 3BP turn acc=66.5%
- Cash 3BP river acc=79.7%, MTT 3BP river acc=77.1%
- → **Cash 3BP ≈ MTT 100bb 3BP** (matrix 完成、共通公式流用)

### Tier C: 公式 N/A (CR/donk/IP defender、専用モデル candidate)

**Flop CR/donk defense (BTN IP)** (phase3 で 18 boards)
- N_cash_cr_def_full: opp_polarization=0.693, opp_weak=45% (air heavy)
- N_cash_donk_def_full: opp_polarization=0.782, **opp_weak=61%** (air heavy)

**Turn donk vs Turn CR** (phase5 multi-street walker)
- P5_D_turn_donk_def: opp_weak=54% (BB の turn donk は air heavy → BTN wider call OK)
- P5_D_turn_cr_def: opp_strong=46% (BB の turn CR は value 寄り → BTN tighter fold)
- → **turn donk と turn CR で BTN defense 方針が真逆**

**River donk defense** (phase5)
- P5_D_river_donk_def: opp_polarization=0.663 (意外と polar じゃない、mid 多)

### Tier D: 公式が比較的健闘 (baseline 公式流用)

- N_cash_3bp_flop acc=66.6% (baseline SRP flop 71.7% に近い)
- 3BP flop は SRP flop と構造的に類似 (board × mv × dv 軸で fit 流用可)

## 6. 軸別 meta-finding

### 6.1 opp range structure × board family
- **mono_Js opp_flush%**: SRP 44% / 3BP 28% / MTT25 17% (preflop action が defender flush 充足率を決める)
- **dyn_T97 opp_straight%**: 3BP river で 70%、SRP river で 69%、MTT200 river で 69% — 板が完成 straight なら opp の 7 割が straight (pot_type 横断で一定)
- **paired_KK2 opp_fullhouse%**: SRP river 16% / 3BP river 0%
- **R1 河 allin 別**: BB の shove range は family 別で全く違う:
  - **low_dry: bluff 0.0%** ← 1 つの数値で書籍 1 章書ける
  - dry_high: 0.6%
  - paired: 2.3%
  - dynamic_2tone: 3.1%
  - monotone: 4.8%
  - dynamic: 6.4% (bluff 最多)

### 6.2 opener position × street (重要な非線形)

| Position | turn opp_polarization | river opp_polarization | river opp_nut_pct |
|----------|---------------------:|----------------------:|------------------:|
| BTN | 0.79 | **0.96** | **0.294** |
| CO | 0.75 | 0.92 | 0.224 |
| HJ | 0.79 | 0.94 | 0.221 |

→ **turn では opener 位置の差はほぼない (0.75-0.79)**  
→ **river で初めて差が顕在化** (BTN open は nut_pct 29%、CO/HJ open は 22%)  
→ 理由: turn ではまだ「相手 range に draw 含む wide」のため opener tightness の効果が薄れる。river で「showdown まで残った range」になって初めて opener tightness が利く。

**Vol3 章設計への影響**: **turn 章は opener 共通、river 章は opener 別** のロジック構造が正当化される。

### 6.3 4BP の構造的特異性 (phase4-6 で確定)

| Street | acc | opp_polarization | opp_weak | 特徴 |
|--------|----:|-----------------:|---------:|------|
| flop | 43.2% | 0.66 | 0.57 | air heavy (range tight で flop hit せず) |
| turn | 49.4% | 0.54 | 0.41 | 3 択ほぼ均等 (modal F/C/R=39/37/24%) |
| river | 60.7% | 0.69 | 0.25 | mid 31% (range tight で air 限定的) |

→ **SRP の polar 戦略 (bluff catcher) が機能しない、middling 比較が支配的**  
→ Cash 4BP と MTT 100bb 4BP は完全に同パターン (phase6 で確認)

### 6.4 defender position の影響

- BB defender (主軸): 全 scenario で取得済
- SB defender (BvB / BTN open vs SB): BB と類似の opp polarization (~0.94)、ただし per-family で SB の弱点あり (low_dry/paired/d2t で huge_loss 大)
- BTN IP defender (CR/donk/allin): 公式 N/A、Tier C 専用モデル candidate

## 7. 雑談から始まった発見の連鎖

このプロジェクトは「river で board 分類いるの不思議」という雑談から始まり、最終的に 7 つの定量化に到達:

1. river の board 分類は **opp range structure の summary** → polarization 0.41-1.00 の幅
2. preflop action で **mono_Js opp_flush%**: SRP 44% → 3BP 28% → MTT25 17%
3. opener position は **river で効くが turn では効かない** → Vol3 章構造の根拠
4. **turn donk vs turn CR で BTN defense 方針が真逆** (donk=call 広く / CR=fold 広く)
5. **low_dry river allin = bluff 0%** (R1 で確定、exploit ルール 1 本)
6. **4BP は SRP と質的別ゲーム** (mid 31%、SPR <1 でも polar じゃない)
7. **MTT 100bb 3BP/4BP は Cash と同公式で代用可** (3BP/4BP は depth 軸に弱依存)

## 8. Vol2/Vol3 章構造への直接的含意

### Vol2 (Cash postflop)
1. **SRP 章**: 既存公式 v9b/v10/v15 で 70-85% カバー、per-board variance を board family 別に提示
2. **3BP 章**: 公式流用 (acc 67%/80%)、ただし per-miss bleed が SRP の 4-10倍
3. **4BP 章**: 専用ロジック必要、特に **「polar じゃない、middling 比較」** を中核メッセージに
4. **多 street CR/donk 章** (新): turn donk = call 広く、turn CR = fold 広く

### Vol3 (MTT postflop)
1. **MTT vs Cash 共通公式章**: Cash の公式は MTT 100bb 3BP/4BP に流用可
2. **depth 別補正章**: MTT25 (短) / MTT100 (中) / MTT200 (深) で per-miss bleed が違う
3. **turn 章は opener 共通 / river 章は opener 別** ← phase5 finding 直接適用

### Vol4 (exploit) — 新規軸
1. **opp range structure 軸**: ボード × pf line × action context で opp range が決まる。書籍では「opp range の bluff/value 比率を読む」をフレームワーク化
2. **R1 ベースの exploit ルール**: 「low_dry river allin = overfold で OK (bluff 0%)」など、family × action 別の単純ルール集
3. **GTO 公式の opp range 仮定に対する exploit 補正**: tight player 相手なら opp_strong を高めに、loose player 相手なら opp_weak を高めに見積もる動的調整

## 9. 残作業と次のステップ

### 即時 (明日 quota 復活後)
- [ ] probe_phase6 残 8 spots (MTT 4BP river の 2 boards + opener×flop の 12 spots)
- [ ] `python3 probe_phase6.py` を再実行で resume

### 中期 (これから 1-2 週間)
- [ ] **Vol2 spec YAML 設計** — `scripts/generate/specs/vol2_*.yaml` に章構成と公式を反映
- [ ] **Vol3 spec YAML 設計** — 同上
- [ ] **probe_priority_rows.csv 統合** — 全 phase の CSV を結合した unified dataset を作成
- [ ] **mtt_formula_audit.py に opp range axis を追加** — 既存 audit に opp_polarization 軸の breakdown を統合

### 長期
- [ ] **公式 v10/v11 設計** — 4BP/3BP 専用ロジックを追加した拡張公式
- [ ] **opp range structure ベース exploit 公式** (Vol4 向け)

## 10. 関連ファイル

| Path | 内容 |
|------|------|
| `research/v4-postflop/probe_priority.py` | 公式 + walker + extractor (新 target 含む) |
| `research/v4-postflop/probe_phase{2,3,4,5,6}.py` | 各 phase 用 runner |
| `research/v4-postflop/extract_past.py` | R1/R3 過去 JSON 再処理 |
| `research/v4-postflop/probe_{priority,phase*}_report.md` | 各 phase 自動生成レポート |
| `research/v4-postflop/probe_{priority,phase*}_rows.csv` | hand-level 集約 (gitignore) |
| `research/v4-postflop/probe_{priority,phase*}_stats.json` | scenario-level stats (sortable) |
| `research/v4-postflop/past_r1_rows.csv` | R1 hand-level (gitignore) |
| `research/v4-postflop/past_spots_summary.csv` | R1+R3 spot 単位 opp 構造 |
| `research/v4-postflop/findings/probe_{priority,phase*}/` | 生 API response 計 334 spots |

## 11. 関連メモリ

- [[project-postflop-3rule-formula]] — v9b/v10/v15 公式の現状実測精度 (Tier A/B/C/D 追記済)
- [[project-gtow-api-v4-postflop]] — GTO Wizard API 取得可能性 (.125 必須など追記済)
- [[project-probe-priority-findings]] — 本プロジェクトの meta-finding 一覧 (新規)
- [[project-mtt-postflop-gto-data]] — 過去の MTT 25/50/100bb 6m データ収集
