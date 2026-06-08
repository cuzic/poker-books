# eq_bucket を人間が判定できる形に分解

MATCHA 公式の最大の障壁 = eq_bucket (best/good/weak/trash) の判定。
以下、人間が暗算で eq_bucket を推定する複数アプローチを提示。

## アプローチ 1: tier 単独で bucket を推定

「自分の hand tier だけで eq_bucket を決められるか」

| tier | best | good | weak | trash | modal (代表) |
|------|---:|---:|---:|---:|---|
| ナッツメイド | 54% | 10% | 23% | 13% | **best_hands** (54%) |
| ストロング | 49% | 21% | 21% | 8% | **best_hands** (49%) |
| ツーペア | 32% | 26% | 18% | 24% | **best_hands** (32%) |
| トップペア以上 | 12% | 43% | 23% | 22% | **good_hands** (43%) |
| ミドルペア | 1% | 22% | 32% | 46% | **trash_hands** (46%) |
| エア | 0% | 4% | 27% | 69% | **trash_hands** (69%) |

→ tier 単独では bucket が一意に決まらない。tier × board が必要。

## アプローチ 2: tier × board_label の対応表 (推奨)

board 4 種 (dry / paired / connected / monotone) × tier 6 種 = 24 cells。
**この表 1 枚で eq_bucket を推定可能。**

| tier | board | best% | good% | weak% | trash% | 推定 |
|---|---|---:|---:|---:|---:|---|
| ナッツメイド | dry | 55% | 18% | 26% | 1% | **best_hands** |
| ナッツメイド | paired | 44% | 5% | 25% | 26% | **best_hands** |
| ナッツメイド | connected | 68% | 10% | 22% | 0% | **best_hands** |
| ナッツメイド | monotone | 96% | 1% | 3% | 0% | **best_hands** |
| ストロング | dry | 72% | 14% | 11% | 3% | **best_hands** |
| ストロング | paired | 77% | 13% | 10% | 0% | **best_hands** |
| ストロング | connected | 40% | 26% | 24% | 11% | **best_hands** |
| ストロング | monotone | 44% | 20% | 27% | 9% | **best_hands** |
| ツーペア | dry | 70% | 21% | 7% | 3% | **best_hands** |
| ツーペア | connected | 14% | 26% | 21% | 39% | **trash_hands** |
| ツーペア | monotone | 16% | 41% | 34% | 9% | **good_hands** |
| トップペア以上 | dry | 26% | 42% | 20% | 11% | **good_hands** |
| トップペア以上 | paired | 13% | 34% | 31% | 22% | **good_hands** |
| トップペア以上 | connected | 3% | 49% | 19% | 29% | **good_hands** |
| トップペア以上 | monotone | 4% | 38% | 32% | 25% | **good_hands** |
| ミドルペア | dry | 0% | 26% | 33% | 41% | **trash_hands** |
| ミドルペア | paired | 5% | 32% | 45% | 18% | **weak_hands** |
| ミドルペア | connected | 0% | 17% | 25% | 58% | **trash_hands** |
| ミドルペア | monotone | 1% | 14% | 34% | 52% | **trash_hands** |
| エア | dry | 0% | 2% | 29% | 70% | **trash_hands** |
| エア | paired | 0% | 7% | 30% | 63% | **trash_hands** |
| エア | connected | 0% | 5% | 26% | 69% | **trash_hands** |
| エア | monotone | 0% | 7% | 19% | 75% | **trash_hands** |

## アプローチ 3: hand_eq (equity%) の閾値判定

自分の hand 概算 equity (相手 range vs) で bucket 推定。

| equity% | best | good | weak | trash | modal |
|---|---:|---:|---:|---:|---|
| 0-10% | 0% | 0% | 0% | 100% | **trash_hands** |
| 10-20% | 0% | 0% | 0% | 100% | **trash_hands** |
| 20-30% | 0% | 0% | 0% | 100% | **trash_hands** |
| 30-40% | 0% | 0% | 66% | 34% | **weak_hands** |
| 40-50% | 0% | 0% | 100% | 0% | **weak_hands** |
| 50-60% | 0% | 100% | 0% | 0% | **good_hands** |
| 60-70% | 0% | 100% | 0% | 0% | **good_hands** |
| 70-80% | 48% | 52% | 0% | 0% | **good_hands** |
| 80-90% | 100% | 0% | 0% | 0% | **best_hands** |
| 90-100% | 100% | 0% | 0% | 0% | **best_hands** |

**簡易ルール (equity 閾値)**: ≥70% → best, ≥50% → good, ≥30% → weak, else trash
- accuracy: **89.8%** (263,506 / 293,319)

## アプローチ 4: eq_percentile (相手 range 内位置)

「相手の hand range の中で自分の手は上位何 %?」で bucket 推定。

| percentile | best | good | weak | trash | modal |
|---|---:|---:|---:|---:|---|
| 0-10% | 0% | 0% | 2% | 98% | **trash_hands** |
| 10-20% | 0% | 0% | 22% | 78% | **trash_hands** |
| 20-30% | 0% | 0% | 40% | 60% | **trash_hands** |
| 30-40% | 0% | 0% | 44% | 56% | **trash_hands** |
| 40-50% | 0% | 2% | 75% | 23% | **weak_hands** |
| 50-60% | 0% | 8% | 67% | 25% | **weak_hands** |
| 60-70% | 0% | 26% | 51% | 23% | **weak_hands** |
| 70-80% | 3% | 55% | 36% | 7% | **good_hands** |
| 80-90% | 21% | 69% | 10% | 1% | **good_hands** |
| 90-100% | 79% | 21% | 1% | 0% | **best_hands** |

**閾値**: percentile ≥ 85% → best, ≥ 65% → good, ≥ 35% → weak, else trash

## 書籍 / drill 向けの推奨アプローチ

### 簡易判定 (暗算用) — 2 段階

1. **tier × board の典型表 (24 cells)** で第一推定
2. equity を体感で +/− 1 段補正

### 中級者向け — equity 直接判定

```
自分の hand 概算 equity (vs 相手 range) で判定:
- 70% 以上 → best_hands
- 50-70%  → good_hands
- 30-50%  → weak_hands
- 30% 未満 → trash_hands
```

この閾値で eq_bucket 推定 **89.8% 一致** (263,506/293,319 rows)

## 結論

- tier 単独では bucket 判定 不可
- **tier × board の 24-cell 対応表** で 大半カバー
- 「equity 概算 → 閾値判定」が最も普遍的、accuracy 90%
- 書籍では (a) 24-cell 表 + (b) equity 閾値 の 2 段階提示が良い