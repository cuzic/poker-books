# GTO Wizard 検証＆境界調査計画

調査日: 2026-05-25
前回成果: 63 spot 取得済、SUMMARY.md に統合済

## Part 1: 既存 claim の精度評価

| claim | n | 実測 | 信頼度 | 主な弱点 |
|------|--:|-----|------:|--------|
| **SRP HJvBB フロップ donk = 0%** | 5 | 100% check (min 98.1%) | 中-高 | 5 texture のみ、特殊（paired_low 等）未測 |
| **SRP HJvBB ターン donk = 0%** | 3 | 全 100% check | 中 | HJvBB のみ、SPR ~3-4 のみ |
| **BTNvBB ターン donk = 0%** | 1 | 99.9% check | **低** | 1 board のみ |
| **ターン probe (XX 後) wet で 46%** | 5 | Kxx:10% / wet 23-46% / QJ4:5% | 中 | 1 board per texture |
| **XX-XX river BB lead 20-54%** | 3 | HJ Kxx:19% / 連結:49% / BTN Kxx:54% | **低** | position × river card の組合せ薄い |
| **turn give-up 後 river BB lead 37-78%** | 3 | dry:37-42% / wet:78% | 中 | HJvBB のみ |
| **3way SB donk T76=25%** | 4 | T76:25% / 他:5-9% | **低** | T76 1 spot のみ。756, 654 等の境界未測 |
| **ICM BB vs BTN all-in 12.5%** | 4 | F42/C37/3bet9/AI13 | 中 | 1 つの asymmetric 配置のみ |

### 信頼度の総評

- **高信頼**: 5 board 確認済の flop donk=0% / turn donk=0% (HJvBB)
- **中信頼**: turn probe, river give-up（texture variation あり、ただし 1 spot/texture）
- **低信頼**: BTNvBB turn donk, 3way SB donk T76, XX-XX position 依存性, ICM 安定性

## Part 2: 境界調査シナリオ

各 claim に対して「境界はどこにあるか」を測定する設計。各シナリオ 5-15 spots、合計 ~150 spots。

### B-1: ターン donk のロバスト性検証（30 spots）

**仮説**: OOP turn donk は全ライン・全 texture で <5%

**境界条件**:
- 強い turn card（A→K のように OOP のレンジを直撃）
- pair turn（同じ rank が turn で出現）
- str8/flush completing turn
- SPR が低い line (3BP cbet-called)

| サブシナリオ | sample 内訳 | 期待境界 |
|-----------|----------|--------|
| HJvBB SRP 全 texture × 6 board | 6 | <5% 全部 |
| BTNvBB SRP × 6 board (Kxx/9hi/AK4/T76/QJ4/JT9) | 6 | <5% |
| COvBB SRP × 4 board | 4 | <5% |
| 3BP HJvBB cbet-called × 4 board | 4 | 5-15%?（範囲圧縮効果） |
| 強 turn card (pair turn) × 5 board | 5 | 1-3% |
| 強 turn card (str8 completing) × 5 board | 5 | **>10% の可能性** |

### B-2: フロップ donk の特殊 texture 境界（20 spots）

**仮説**: OOP flop donk は 0%、ただし IP のレンジ弱点 board (low connected) で例外あり

| サブシナリオ | board 例 | 期待 donk 率 |
|-----------|--------|----------|
| 低コネクト（543, 654, 765） | 5h4s3c, 6c5d4s, 7d6s5c | 5-15% ? |
| ペアロー (442, 552, 663) | 4h4s2c, 5d5h2s, 6c6d3s | 0-3% |
| モノクロロー (2♠3♠5♠) | 2s3s5s | 5-10%? |
| Q-high mono | Qs8s5s | 0-3% |
| 2tone コネクト (T98 2♠♣) | Ts9s8c | 0-3% |

→ 「low connected ボードでの donk」を仮説検証。GTO Wizard ブログでも 654 等のコネクト OOP donk 言及あり。

### B-3: マルチウェイ SB donk の連結性境界（25 spots）

**仮説**: SB donk は弱コネクト × middle range で 20-30%、それ以外は 5-10%

**境界変数**: 連結度（gap）と high card

| board | 連結度 | 期待 SB donk |
|------|------:|----------:|
| Td7c6s (T76, gap 4) | mid | **25%（実測済）** |
| 9h8c7d (987, gap 2) | high | 9%（実測済） |
| 7c6s5d (765, gap 2) | mid | **20%?** |
| 6s5h4c (654, gap 2) | low | **30%?** |
| 5d4s3c (543, gap 2) | very low | **35%?** |
| 8h6c4d (864, gap 4) | mid | 15% |
| Th8c5d (T85, gap 5) | mixed | 10% |
| Q9c7d (Q97, gap 3) | mid-high | 15% |
| Jc8s5h (J85, gap 6) | mixed-mid | 10% |
| Ah7c4d (A74) | A-high | 5% |
| K6s4c (K64) | K-high | 5% |
| Q4s2c (Q42) | air | 3% |
| 982 (9h8s2c, paired-style) | mid | 7% |

→ **連結度 + middle ranks の組合せが donk 主因かを定量化**

### B-4: XX-XX river OOP lead の position 依存性（20 spots）

**仮説**: BB の river lead 率は IP position が遠いほど高い (BTN > CO > HJ > UTG)

**境界変数**: IP position × river card type

| line | board (river) | 期待 lead 率 |
|------|------------|----------:|
| UTGvBB XX-XX / Ks7d2c5h3d | dry rainbow | 10-15% |
| HJvBB XX-XX / Ks7d2c5h3d | dry rainbow | **19%（実測）** |
| COvBB XX-XX / Ks7d2c5h3d | dry rainbow | 30% |
| BTNvBB XX-XX / Ks7d2c5h3d | dry rainbow | **54%（実測）** |
| 同上 / 9h8s7d4c2d | wet | 40-60% |
| 同上 / AhKd4s8c2h | overcard | 25-35% |
| 同上 / Th9s8c4dAh (A river) | scare | **49%（実測）** |

→ position effect の線形性を確認

### B-5: ターン give-up 後の river BB lead の board 依存（15 spots）

**仮説**: 連結度・river ペア化が lead 率を 30-80% で変動させる

| flop turn river | 期待 lead |
|--------------|---------:|
| Ks7d2c 5h 3d (実測 37%) | 37% |
| Ks7d2c 5h Kd (river K paired) | **15%?** |
| Ks7d2c 5h Ad (overcard) | 25% |
| Ks7d2c 5h Tc (mid blank) | 35% |
| 9h8s7d 4c 2d (実測 78%) | 78% |
| 9h8s7d 4c Th (str8 completing) | **85%?** |
| 9h8s7d 4c 9d (river pair) | **50%?** |
| 9h8s7d 4c As (scare) | 60% |
| QhJd4s 7c 2h (実測 42%) | 42% |
| QhJd4s 7c Td (str8 draw complete) | 55% |
| QhJd4s 7c Ah (top pair scare) | 30% |
| AhKd4s 8c 2d | 30% |
| AhKd4s 8c Ts | 35% |

### B-6: ICM の stack 構成依存性（20 spots）

**仮説**: BB が大スタック (covered) → all-in 率上昇、small stack BB → all-in 率低下

**境界変数**: BB の有効スタック、テーブル平均との比

| BB stack | other config | 期待 BB vs BTN AI率 |
|---------|------------|------------------:|
| 28.125 (実測) | 26-22-30-20-24 | **12.5%** |
| 30.125 (large) | 28-22-25-20-26 | 18% |
| 35.125 (chip leader) | 25-20-28-30-22 | 22% |
| 22.125 (medium) | 30-28-25-20-26 | 10% |
| 18.125 (short) | 30-28-25-32-22 | 5% |
| 15.125 (very short) | 30-28-25-32-22 | 3% |

→ short stack pressure の閾値特定

### B-7: turn cbet サイズ二極化の境界（15 spots）

**仮説**: turn IP cbet は 33% 支配的、ただし AK 系で overbet (>100%) に切替

| board | turn | 期待サイズ |
|------|----|---------|
| AhKd4s 2c | blank | 33% |
| AhKd4s 4c | pair | 33% |
| AhKd4s 8c | mid | **75-150% mixed** |
| AhKd4s Ts | scare | 100%? |
| KsQd4h 2c | broadway | 33% |
| KsQd4h 8c | mid | 75%? |
| QsJh9c 2d | str8 risk | 33% mixed 75% |
| QsJh9c 8s | str8 completing? | 75%+ |
| Ts9s8c 2d | wet | 33% |
| Ts9s8c Ah | overcard | **mixed** |

### B-8: probe spot の境界（20 spots）

**仮説**: XX 後の turn probe 率は wet × 中ランク turn で peak

**変数**: flop texture × turn card のテキスチャ進化

| flop | turn | 期待 probe |
|-----|-----|----------|
| Ks7d2c | 5h (blank) | 10% (実測) |
| Ks7d2c | 5c (BDFD成立) | 18% |
| Ks7d2c | Kd (pair top) | 8% |
| Ks7d2c | Ah (overcard) | 12% |
| 9h8s7d | 4c (実測) | 46% |
| 9h8s7d | 6c (str8) | **60%+** |
| 9h8s7d | 5d (gut成立) | 50% |
| 9h8s7d | Td (overcard+str8) | 55% |
| 9h8s7d | 9d (pair top) | 35% |
| 9h8s7d | Ah (overcard scare) | 40% |
| Td7c6s | 4c (blank) | 25% |
| Td7c6s | 8h (str8 risk) | 50% |
| Td7c6s | 9d (str8 complete) | 60% |
| Td7c6s | Kc (overcard) | 30% |
| QhJd4s | 7c (blank) | 5% (実測) |
| QhJd4s | Ts (str8 wet) | 20% |
| QhJd4s | Ah (overcard scare) | 15% |

## Part 3: 設計上の方針

### 優先順位

1. **B-3 マルチウェイ SB donk**: 既存データが T76 1 spot のみ、書籍 vol2 ch05 に直接影響
2. **B-4 XX-XX river position 依存**: BB の river plan 戦略の core、4 position 線形性検証
3. **B-1 turn donk ロバスト性**: 「donk = 0」の例外を見つける（強 turn での反例期待）
4. **B-8 probe spot 境界**: turn card 進化と probe 率の対応表が完成すれば書籍に直接搭載可能
5. **B-2 flop donk 特殊 texture**: 低コネクト OOP donk の存否（書籍 ch03 に影響）

### スポット規模

| シナリオ | 規模 | 累計 |
|--------|----:|----:|
| B-1 ターン donk | 30 | 30 |
| B-2 フロップ donk 特殊 | 20 | 50 |
| B-3 multiway SB donk | 25 | 75 |
| B-4 XX-XX position | 20 | 95 |
| B-5 give-up river board | 15 | 110 |
| B-6 ICM stack 構成 | 20 | 130 |
| B-7 turn cbet size | 15 | 145 |
| B-8 probe turn card | 20 | **165** |

合計 ~165 spots。前回 92 試行→63 成功 (68%) ペースなら成功 ~112 spot。

### サイズ確認の前処理

precomputed tree の制約で、各 line 投入前に「その spot で IP がどのサイズで打つか」を fetch.py 内で確認するロジックが必要:

```python
def probe_sizes(spot_template):
    # Step 1: Get spot at root, find dominant action codes
    # Step 2: Use those codes to construct full line
    # Step 3: Submit final query
```

これにより 422 失敗を激減できる（前回 13 件発生）。

## Part 4: 実行計画

1. **fresh JWT 取得**（ブラウザから Copy as cURL）
2. **fetch.py v2** に「アクション code 自動検出」追加
3. **spots_boundary.csv** に上記 8 シナリオ ~165 spot 列挙
4. **実行** ~10 分
5. **集計** で各 claim の境界値を表化
6. **SUMMARY.md 更新** + 書籍反映候補のリファイン
