# 第 3 章　board — 3 タイプ

## 3.1 3 タイプの定義

MATCHA Score では board を **dry / paired / wet** の 3 タイプに分類します。

| タイプ | 定義 |
|---|---|
| **paired** | 同じ rank が 2 枚以上 (ペア板) |
| **wet** | モノトーン (3 枚同 suit) または connected (span ≤ 4) |
| **dry** | 上記以外 (unpaired かつ非 connected かつ非 monotone) |

判定は **フロップの 3 枚のみ** を見ます。ターン・リバーの追加カードは無視します。

## 3.2 判定の手順 (3 ステップ)

```
1. 同 rank が 2 枚以上 → paired
2. モノトーン (3 枚同 suit) または span ≤ 4 で連結 → wet
3. それ以外 → dry
```

### 「connected (span ≤ 4)」 の意味

3 枚の rank を昇順に並べたとき、**最大と最小の差 (span) が 4 以下** (= 5 連続 rank の窓内) の場合を connected と呼びます。隣接カード間の差は問いません。

例：
- T-9-8 → span 2 (10−8)、wet (connected)
- T-9-7 → span 3 (10−7)、wet (5 窓 T9876 に収まる)
- T-9-6 → span 4 (10−6)、wet ← 隣接差が 3 でも wet
- T-9-5 → span 5 (10−5)、dry (5 窓に収まらない)

**注意**: 隣接カード差 (adj gap) ではなく span (max − min) で判定します。T-9-6 は隣接差が 1 と 3 ですが、span=4 ≤ 4 なので **wet** です。GTO データ検証 (10 境界ボード) で cbet 平均 27.2% ≈ wet ベースライン (31.7%) と確認されています。

## 3.3 具体例

| board | 判定 | 理由 |
|---|---|---|
| Kh 7c 2d | **dry** | 非 paired、非 connected、非 mono |
| Kh Kc 7d | **paired** | K が 2 枚 |
| Th 9h 8s | **wet** | span 2 で連結 |
| Th 9h 4h | **wet** | モノトーン |
| Ah Ks 4d | **dry** | span 10、非 connected |
| Qh Jc Th | **wet** | span 2 で連結 |
| 7h 5c 4d | **wet** | span 3 で連結 |
| Qh 9c 8d | **wet** | span 4 (12−8=4) ≤ 4 で connected |
| Tc 9h 6d | **wet** | span 4 (10−6=4) ≤ 4、隣接差 1,3 でも wet |
| Tc 9h 5d | **dry** | span 5 (10−5=5) > 4 で非 connected |
| Ah 8s 3d | **dry** | span 11、非 connected |
| Ah 3s 2d | **wet** (A-low 例外) | wheel draw あり → wet 扱い (後述 3.6) |
| Ah 5s 4d | **wet** (A-low 例外) | wheel draw あり → wet 扱い (後述 3.6) |

## 3.4 旧 6 ボードファミリーとの対応

| 旧 family | 新分類 |
|---|---|
| dry_high (A/K/Q high dry) | dry |
| low_dry (低 rank dry) | dry |
| dynamic (中程度 connector) | wet |
| dynamic_2tone (2 tone connected) | wet |
| monotone | wet |
| paired | paired |

この 3 分類は GTO 実測に基づいており、詳細は第 10 章 (Range Morphology) で扱います。

## 3.5 ターン以降の board 変化

board 判定は **フロップ固定** が原則ですが、ターンで board structure が劇的に変わる場合は注意が必要です。

- ターンで rank がペアになった (例：K72 → K72-7) → 例外 11 ルール候補に
- ターンで flush draw 完成 (例：K72 → K72-h で 3 tone) → DV が変化、board は dry 維持

board 判定そのものは変えず、DV と例外ルールで吸収するのが本書の方針です。

## 3.6 A-low board 例外 (GTO 実測)

**A-low board** (フロップに A があり、他の 2 枚が両方 ≤ 6) は span が 9〜12 と大きく通常ルールでは dry に分類されますが、GTO 実挙動は wet と同等です。

### 根拠：BTN cbet 実測値 (GTO Wizard)

| カテゴリ | 代表例 | BTN cbet 平均 |
|---|---|---:|
| dry baseline (K/Q high) | K72, K83, Q83 | 66.1% |
| **A-low board** | A32, A43, A54, A65 | **47.7%** |
| wet baseline | 987, T96, 654 | 42.7% |

A-low board の BTN cbet (47.7%) は wet baseline (42.7%) に **5pp 差**、dry baseline (66.1%) に **18pp 差**です。wet 扱いが妥当といえます。

### 理由：wheel straight draw

A はポーカーでは高カード (A=14) と同時に低 ace (A=1) としても機能します。A-3-2 フロップでは **4 か 5 が来ると A-2-3-4-5 (wheel straight) が完成**します。この wheel draw の存在が board texture を湿らせ、BTN が cbet できるハンドの range を wet board 並みに絞ります。

A-5-4 では 2/3 で wheel 完成、6/7 でも複数の straight が射程に入るため同様です。

### 実用ルール

```
A-low board: A と ≤6 のカード 2 枚が揃う → wet 扱い

wet 例: A32, A42, A43, A52, A53, A54, A62, A63, A64, A65
dry 維持例: A83, A84, A94 (7 以上のカードがあれば dry のまま)
```

A84 のように 7 以上のカードが入ると wheel draw の強度が大幅に落ちるため、通常の dry として扱います。

## 3.7 board 判定の落とし穴

- **A-low board (A + ≤6 の 2 枚)**：span 大でも **wet** (3.6 参照)
- **A-high mid board (A83, A84 等)**：span 大かつ 7 以上あり → dry のまま
- **2 tone**：それ自体は wet ではない (mono のみ wet)、ただし span ≤ 4 なら wet
- **rainbow + connected**：span ≤ 4 なら wet (suit と独立)
- **3 broadway (JTQ)**：span 2 (12−10=2) なので wet
- **AK7 rainbow**：span 7 (14−7=7) > 4 で dry
- **T-9-6**：span 4 (10−6=4) ≤ 4 → wet (隣接差 3,1 は無関係)

## 3.8 古典ボード 7 分類 → MATCHA 3 分類 集約表

ポーカーの古典文献 (Janda "Applications"、Acevedo "Modern Poker Theory" 等) では board を **7 分類** に細分化していました。本書はこれを 3 分類に集約します。

| 古典 7 分類 | 典型例 | MATCHA 3 分類 | 集約根拠 |
|---|---|---|---|
| Dry rainbow (A/K-high) | Kh 7c 2d、Ah 8s 3d | **dry** | unpaired + 非 connected + rainbow |
| Dry connected (低 gap) | 7-5-2 (span 5、非 wet) | **dry** | span > 4 で connected ではない (低 rank dry) |
| Wet (中 connector) | T-9-8、7-6-5 | **wet** | span ≤ 4 で連結 |
| Monotone (3 同 suit) | 9h 7h 3h | **wet** | mono は wet 扱い (flush 警戒) |
| Two-tone (connected) | T-9-8 2tone (h-h-c) | **wet** | span ≤ 4 で wet (suit 別問わない) |
| Paired high (K-K-X 等) | K-K-7、A-A-2 | **paired** | 同 rank 2 枚以上 |
| Paired low (7-7-X 等) | 7-7-2、4-4-3 | **paired** | 同 rank 2 枚以上 |

### 集約後の各分類の例 board

| 新分類 | 古典分類混合例 |
|---|---|
| **dry** (4 系混合) | Kh 7c 2d (dry rainbow) / Ah 8s 3d (A-high dry) / 7-5-2 (low dry) |
| **paired** (2 系統合) | K-K-7 (paired high) / 7-7-2 (paired low) |
| **wet** (3 系統合) | Q-9-8 (connected) / 9h 7h 3h (mono) / Th 9h 4s (2tone wet) |

### 判定手順 (3 分類版、古典 7 → 3 早見)

```
1. 同 rank 2 枚以上 → paired (古典 paired high / paired low 統合)
2. span ≤ 4 (5 窓内 3 枚) または monotone → wet (古典 wet / mono / 2tone 統合)
3. 上記以外 → dry (古典 dry rainbow / dry connected 統合)
```

### 集約根拠 (data 検証)

3 分類は GTO データから導出されており、sub-family の差は **Grid 値の hand × board interaction** (例えば「ミドル × paired = 40 vs ミドル × wet = 10」) で吸収されます (詳細は第 10 章)。

### 古典理論との対応詳細

古典文献の "Applications of No-Limit Hold'em" (Janda) や "Modern Poker Theory" (Acevedo) では board をより細かく分類していますが、本書の 3 分類との対応関係は第 13 章 (旧来理論との橋渡し) に詳細な対応表があります。

## Cash/MTT note

board 3 タイプ (dry / paired / wet) の判定は Cash/MTT 共通です。ただし late MTT (ante 大) では BB defense wider で「相手が wet board に call で残る range」が +5-10% 広く、board 解釈の hero edge がやや低下します。

## この章で覚える項目 (5 items)

1. 3 タイプ：dry / paired / wet (古典 7 分類を集約)
2. 判定手順：paired → wet → dry の順
3. wet の条件：モノトーン または span ≤ 4 (= max_rank − min_rank ≤ 4)
4. フロップ 3 枚で固定 (ターン以降は変えない)
5. **A-low 例外**：A + ≤6 の 2 枚 → wet (BTN cbet 実測 ~48% ≈ wet 水準)
