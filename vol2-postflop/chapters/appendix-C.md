# 付録 C　MATCHA Quality Score (MQS) — 公式の品質保証指標

## C.1 MQS とは

**MATCHA Quality Score (MQS)** は MATCHA Score 公式の総合品質を **0-100 で評価する指標** です。174K hands × 5 context (SRP/3BP/4BP/TURN/RIVER) の検証で **公式が data 駆動で何 %正解か** を定量化します。

## C.2 5 component の評価軸

| Component | weight | 評価対象 |
|---|---:|---|
| Action Accuracy | 0.20 | 公式判定 = GTO 最適 の一致率 |
| Loss Quality (median) | 0.30 | 中央値 loss の小ささ (大半 hand で 0 BB か) |
| High-Conf Coverage | 0.20 | S/A/B 信頼度 cell に属する hand 比率 |
| Outlier Detection F1 | 0.15 | 役ベース outlier rule の検出能力 |
| Cross-Context Robustness | 0.15 | 5 context 間の MQS 標準偏差の逆数 |

## C.3 検証結果 (174,793 hands × 5 context)

| context | n | Acc | avg loss BB | Cov | MQS |
|---|---:|---:|---:|---:|---:|
| **SRP** | 39,736 | 79.3% | 0.0066 | 100% | **94.6** |
| **3BP** | 47,040 | 84.9% | 0.0190 | 100% | **94.8** |
| **4BP** | 47,040 | 65.7% | 0.1199 | 100% | **84.0** |
| **TURN** | 21,227 | 64.9% | 0.0134 | 100% | **90.6** |
| **RIVER** | 19,753 | 70.1% | 0.0415 | 94% | **88.2** |
| **Integrated** | **174,793** | **73.0%** | **0.040 BB** | **98.7%** | **91.2** |

**Grade**: **S (≥80)** / A (70-80) / B (60-70) / C (50-60) / D (<50)

→ **MATCHA Score 公式は Grade S を達成** (MQS=91.2) しました。

## C.4 MQS の評価方法

**実害ベース指標**: avg loss ベースで 91.2 — 「実際の BB loss」を直接測定した品質を表します。

これは「公式が実戦で何 BB 損させるか」を直接示す **実質的な品質指標** です。

## C.5 MQS の天井理由

**MQS = 91.2 は暗算可能な公式での実質的に達成できる高い水準です**。これを超えるには以下が必要になります。

- 公式の outlier の主因 = **cell 内の hand-level eq 差** (cell 平均では bet/check 判定ができません)
- 弱いカテゴリ × draw / bluff bet の見落とし: SRP/3BP の outlier の 32-53% を占めていますが、flop では no_made_hand bet 率が 15-24% で「弱いカテゴリ → bet」ルールは GTO に逆行してしまいます
- 真の改善には **hand-level eq 計算** が必要 = solver-level (暗算放棄) になってしまいます

つまり MQS 91.2 は「**暗算の哲学を守りながら達成できる最適地点**」です。

## C.6 公式品質保証宣言

本書の MATCHA Score 公式 (5 章のルール) は以下の検証を経ました。

- **174,793 hands で検証**
- **avg loss 0.040 BB/hand** (100 hand 平均で 4 BB の損失)
- **Grade S (MQS 91.2)**
- 全 cell が B 級以上 (D cell は完全に消滅)

→ **「暗算で回せる公式」として、実 GTO に最も近い精度** を達成しています。
