# Bet Sizing / Defense / Turn-River 軸の境界 — 10 spots 実 probe

2026-06-08 token で取得した 10 spots を tier 別に分析。

## 1. Bet Sizing 軸 (wet board cbet)

BTN attacker on wet/connected boards: cbet 頻度 + sizing 選択

### 6s5d4c (bs_654_flop)

| action | size | freq | エア | ミドルペア | TP+ | ツーペア | ストロング | ナッツメイド |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CHECK | 0bb | 98% | 57% | 22% | 14% | 2% | 5% | 0% |
| RAISE | 6.5bb | 2% | 59% | 13% | 12% | 3% | 13% | 0% |

### AsKdQc (bs_AKQ_flop)

| action | size | freq | エア | ミドルペア | TP+ | ツーペア | ストロング | ナッツメイド |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CHECK | 0bb | 94% | 59% | 27% | 10% | 2% | 1% | 0% |
| RAISE | 6.5bb | 6% | 68% | 0% | 7% | 12% | 12% | 0% |

### Js8d6c (bs_J86_flop)

| action | size | freq | エア | ミドルペア | TP+ | ツーペア | ストロング | ナッツメイド |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CHECK | 0bb | 95% | 61% | 25% | 11% | 2% | 1% | 0% |
| RAISE | 6.5bb | 5% | 66% | 5% | 19% | 9% | 2% | 0% |

### Ts9d8c (bs_T98_flop)

| action | size | freq | エア | ミドルペア | TP+ | ツーペア | ストロング | ナッツメイド |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CHECK | 0bb | 94% | 57% | 25% | 12% | 2% | 4% | 0% |
| RAISE | 6.5bb | 6% | 68% | 4% | 10% | 2% | 16% | 0% |

### Bet Sizing 軸の発見

- **Wet/connected board は cbet 頻度激低 (2-6%)** → BTN は check-back 中心
- **cbet するときは 100% pot (6.5bb) 一択** → polar attack
- MATCHA の Bet Sizing 4 段階のうち、wet board では `オーバーベット (>75%)` のみ使用
- → wet board の sizing 判断は **"打つか/打たないか"** が本質、サイズ選択は二次的

## 2. Defense 軸 (BB vs BTN 33% cbet)

BB defender が flop 33% cbet (1.9bb) に対する fold/call/raise 分布

| board | sub-family | fold% | call% | raise% | raise size |
|---|---|---:|---:|---:|---|
| Ks7d2c | ? | 30% | 59% | 12% | 5bb |
| Qs7d2c | ? | 28% | 65% | 6% | 10.3bb |
| Ts9d8c | ? | 28% | 64% | 7% | 10.3bb |

### Defense 軸の発見

- BB は **board に関わらず ~70% defend** (fold 28-30% 一定)
- **raise 頻度は board で変動**:
  - dry K72: raise 12% (sizing 5bb = 2.6x cbet)
  - wet T98: raise 7% (sizing 10.3bb = 5.4x cbet, much larger)
  - broadway Q72: raise 6% (sizing 10.3bb)
- → **CR sizing は board で変わる**: dry は小さく、wet は大きく (polar)
- MATCHA 守備の判断軸として: **fold MDF は一定 (~30%)、raise は board で polar**

## 3. Turn/River 軸 (K72 progression)

同 K72 flop の street ごとの IP cbet 行動

| street/line | action 分布 |
|---|---|
| flop bet-call → turn check → river 8s | CHECK0=55% / RAISE2.4=45% |
| flop bet-call → turn 3h | CHECK0=100% / RAISE17.1=0% |
| flop check-check → turn 3h | CHECK0=45% / RAISE1.9=55% |

### Turn/River 軸の発見

- **flop bet-call → turn brick (3h)**: BTN check 100% — bluff を継続せず、強い手のみ次 barrel
  → "flop bet-call line" の turn は ほぼ完全 check (薄い valued only)
- **flop check-check → turn brick**: BTN delayed cbet 55% (sizing 1.9bb = 33%)
  → flop check 後の turn は 半分以上 bet (range narrow されたため value 多い)
- **flop bet-call → turn check → river brick**: BTN river bet 45% (sizing 2.4bb = 25%)
  → 1 barrel 後の river は薄い value で small bet
- MATCHA Framework に **street 別補正 (薄い valued vs bluff catch)** が必要

## 4. 統合発見 — MATCHA 5 軸への影響

### Bet Sizing 軸 (5 軸目) の data 裏付け

| board family | dominant sizing | 解釈 |
|--------------|----------------|------|
| dry MERGED (K72) | small 33% (1.9bb) | range advantage, wide attack |
| connected wet (T98) | overbet 100%+ (6.5bb) | polar attack, low freq |
| 中間 (broadway dry) | small 33% | merged |
- → MATCHA 4 段階 (small/medium/over/allin) のうち **medium (50%) はほぼ unused**
- → 簡易化: **2 段階 (small ~33% / over ~100%)** で 90% カバー

### Defense 軸の data 裏付け

- BB MDF (fold 上限) は ~30% で board 不変
- raise frequency は board で 6-12% に分布
- raise size は board で 2.6x ~ 5.4x cbet (wet ほど large)

### Street 別補正

- flop bet → turn check はほぼ確定 (giving up bluffs)
- delayed cbet (flop check → turn bet) は range narrowing で 55% bet
- river thin value は small (25%) sizing
- → MATCHA Framework の 3 補正に **"line-aware sizing"** を追加検討