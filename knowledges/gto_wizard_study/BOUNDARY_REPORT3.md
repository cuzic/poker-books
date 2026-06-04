# Boundary Study Report v3 — turn cbet サイズ / probe spot 完全版

生成日: 2026-05-26
スポット数: **45** (b7: 20 / b8: 25 全完了)

## 主要発見サマリ

### B-7: IP turn cbet サイズ二極化

**仮説**: turn cbet は 33% pot 主体 (旧 GCP study)
**実態**: IP turn cbet は **101% pot / 276% pot / 157% pot の overbet 三層構造**。33% pot サイズは tree に存在しない。

#### B-7 法則

```
■ Turn IP cbet サイズ判定（BB X-cbet-call、BB X turn 後）

  サイズ層:
    276% (huge overbet): dry × range が IP に集中 (Kxx, KQ4, QJ4, A42)
    157% (mid overbet):  AK4 系 (range advantage 強い IP)
    101% (regular overbet): wet / connected (987, T76, JT9, mono)
  
  bet 頻度: 25-65%（板による）
```

| ボード | bet% | サイズ |
|------|---:|---:|
| Kxx + low blank (3) | 28% | 276% |
| Kxx + mid blank (Q) | 35% | 276% |
| QJ4 + blank | 36-40% | 276% |
| A42 + 9 | 25% | 276% |
| KQ4 + blank | 36% | 276% |
| AK4 + 8/2 | 39-44% | 157% |
| Kxx + 5/A | 30-52% | 101% |
| 987 / T76 / JT9 (wet) | 45-61% | 101% |
| Mono (Ts8s5s) | 47% | 101% |

---

### B-8: probe spot turn card 効果（完全版）

`F-R2.2-F-F-F-C / X-X / turn` — BB がフロップ XX 後 turn first

**25 spots、6 つのフロップでの全 turn card パターン**

#### Flop: Ks7d2c (dry K-high)

| turn | probe% | size | 解釈 |
|-----|------:|-----:|-----|
| K | **2%** | 372% | BB に K 少ない |
| 7 (mid pair) | 18% | 101% | mid 役立つ |
| 5 (blank) | 10% | 372% | 標準 |
| 2 (bot pair) | 17% | 372% | 弱い |
| A (overcard) | 14% | 101% | A は IP に |

#### Flop: QhJd4s (connected high)

| turn | probe% | size | 解釈 |
|-----|------:|-----:|-----|
| Q (top pair) | 10% | 101% | IP も Q 持つ |
| 4 (bot pair) | 20% | 372% | board pair |
| T (str8 draw) | **0.1%** | 372% | 攻めない |
| A | 7% | 101% | scare |

#### Flop: 9h8s7d (wet connected)

| turn | probe% | size | 解釈 |
|-----|------:|-----:|-----|
| **9 (top pair)** | **51%** | 101% | BB に 9x 多 |
| **T (overcard/str8)** | **54%** | 34% | BB ナッツ多 |
| 6 (str8 complete) | 32% | 34% | str8 は両者 |
| A (scare) | 17% | 101% | 控えめ |

#### Flop: Td7c6s (wet mid)

| turn | probe% | size | 解釈 |
|-----|------:|-----:|-----|
| **8 (str8 complete)** | **59%** | 34% | BB str8 多 |
| 6 (bot pair top) | 26% | 101% | |
| J (overcard) | 14% | 372% | scare |

#### Flop: JdTs9c (very wet)

| turn | probe% | size | 解釈 |
|-----|------:|-----:|-----|
| 8 (str8 complete) | 31% | 34% | |
| 2 (blank) | 26% | 101% | |
| A (overcard) | 11% | 372% | scare |

#### Flop: AhKd4s (range advantage IP)

| turn | probe% | size | 解釈 |
|-----|------:|-----:|-----|
| 2 (low blank) | **33%** | 101% | surprise — BB leads |
| 8 (mid blank) | 16% | 101% | |
| A (top pair) | 16% | 101% | BB Ax 少なめ |
| K (mid pair) | **0.1%** | 101% | BB K 少 |

#### Flop: Ah4d2c (A-high disconnected)

| turn | probe% | size | 解釈 |
|-----|------:|-----:|-----|
| 3 (wheel str8) | 29% | 101% | BB wheel hits |
| K (overcard) | 15% | 101% | |

---

### B-8 法則（完全版）

```
■ Turn BB probe 判定（フロップ XX 後）

  HIGH probe (50%+) — 攻めて OK:
    - Wet connected board + BB hit turn
      例: 987→9 (51%), 987→T (54%), T76→8 (59%)
  
  MID probe (20-35%):
    - Wet board + middle pair/draw turn
    - AK4 + low blank（IP 弱体化）
    - A42 + wheel str8 turn
  
  LOW probe (5-20%):
    - Dry high board + 多くの turn
    - Top pair on dry high board where BB has few
    - Overcard scare A
  
  ZERO probe (<5%):
    - 「board が IP のレンジを直接強化」
      例: AK4 + K (BB に K ほぼなし)
      例: QJ4 + T (IP の AKJ/AQJ/KQJ 完成)
      例: Kxx + K (BB に K 少ない)

  サイズ層:
    33% pot: wet board + connected/str8 turn（薄め value+ブラフ）
    101% pot: 標準 overbet
    372% pot: dry board polarized（ナッツ+ブラフ極化）
```

---

## 全 6 ボード × turn card マトリクス

| Flop\Turn | top pair | mid pair | bot pair | str8 cmpl | overcard A | blank |
|----------|---------:|---------:|---------:|----------:|----------:|------:|
| Ks7d2c (dry K) | 2% | 18% | 17% | - | 14% | 10% |
| QhJd4s (conn Q) | 10% | - | 20% | 0% | 7% | - |
| 9h8s7d (wet 9) | 51% | - | - | 32% | 17% | - |
| Td7c6s (wet T) | - | - | 26% | 59% | - | - |
| JdTs9c (wet J) | - | - | - | 31% | 11% | 26% |
| AhKd4s (AK range adv) | 16% | 0% | - | - | - | 33% |
| Ah4d2c (A-high) | - | - | - | 29% | - | 15% |

---

## 書籍反映候補（更新）

| 章 | 修正内容 |
|---|------|
| vol2 ch07 「ターン barrel」 | **「ターン barrel size は 33% pot」→ 100-276% overbet 三層構造（dry なほど大）** |
| vol2 ch08 「probe spot」 | **board × turn card マトリクスを掲載** (上記表) |
| vol2 ch08 | 「ZERO probe spot」(AK4+K, QJ4+T 等) と「HIGH probe spot」(987+9, T76+8) の対比 |

---

## 信頼度（完全版）

- **B-7 turn cbet size**: 20 spots — **高信頼**
- **B-8 probe spot**: 25 spots × 6 flops × 各 3-5 turn card — **高信頼**
- 「dry board に対する漏れの少ない網羅」と「wet board の代表的 turn card 全部」をカバー

データ: `b7_turn_cbet/*.json` (20) + `b8_turn_probe/*.json` (25)
