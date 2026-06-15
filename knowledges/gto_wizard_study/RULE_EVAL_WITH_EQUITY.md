# equity_bucket を加えた cell key の比較評価

「value / draw の価値概念」を取り入れるため、cell key に equity_bucket を追加。
293K rows で 3 variants を比較。

## ルール構造の比較

| variant | cell key | cell 数 |
|---|---|---:|
| 3-key (現行) | (pot, street, sub, made_tier) | 298 |
| 4-key 統合 | (pot, street, sub, made_tier, **eq_bucket**) | 556 |
| 3-key 代替 | (pot, street, sub, **eq_bucket**) | 246 |

## 全体結果

| variant | cells | accuracy | avg loss | huge% |
|---|---:|---:|---:|---:|
| **3-key (現行)** | 298 | 71.41% | 0.5430 BB | 2.48% |
| **4-key (made_tier × eq_bucket)** | 556 | **78.13%** | **0.2102 BB** | **0.82%** |
| 3-key (eq_bucket のみ) | 246 | 74.68% | 0.2461 BB | 0.80% |
| 既存公式 v9b/v10/v15 | — | 59.46% | 1.8595 BB | 9.65% |

## 改善幅 (3-key → 4-key)

- Accuracy: 71.41% → 78.13% (+6.72pp)
- Avg loss: 0.5430 BB → 0.2102 BB (-61.3%)
- Huge loss: 2.48% → 0.82% (-67.1%)

cell 数は 298 → 556 (+258) で大幅増加。
精度向上と cell 数増のトレードオフを評価する必要あり。

## 解釈

- **eq_bucket を加える」と精度向上**: value / draw / equity の概念が判定に効く
- ただし cell 数は 4 倍程度増加 → 暗記負荷も増
- 「value 4 段階」を hand_tier の上に重ねるアプローチ
- combo draw (made カテゴリ=エア だが eq=good_hands) のような spot が正しく分類される
