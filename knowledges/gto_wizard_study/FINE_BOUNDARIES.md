# 細分化 boundary 分析 — 42 boards、subfamily × hand_strength

既存 board family (POLAR/MERGED/CONDENSED) より細かい sub-family で分析。

## 13 sub-families (board 構造ベース)

| sub-family | 判定条件 | n probes |
|------------|---------|---------:|
| Khigh_spread | K-high、gap ≥5 | 4 |
| paired_low | paired + 2-4 | 3 |
| Ahigh_spread | A-high、gap ≥5、non-connected | 5 |
| paired_mid | paired + 5-9 | 1 |
| Ahigh_close | A-high、gap <5 | 1 |
| paired_high | paired top + K/A high | 4 |
| connected_broadway | connected + high T+ | 1 |
| broadway_dry | broadway high non-connected | 3 |
| connected_low | connected + high 2-6 | 5 |
| mid_dry | その他 | 4 |
| monotone | 3 同 suit | 1 |
| low_dry | low board (5-high以下)、rainbow | 2 |
| Khigh_close | K-high、gap <5 | 2 |
| connected_mid | connected + high 7-9 | 6 |

## sub-family ごとの cbet 頻度 (BTN attacker)

| sub-family | n | cbet 平均 | 範囲 | stddev |
|------------|---:|---------:|------|------:|
| Khigh_spread | 4 | 49.5% | 48-50% | 1.2% |
| paired_low | 3 | 48.8% | 45-57% | 6.9% |
| Ahigh_spread | 5 | 48.7% | 47-50% | 1.5% |
| paired_mid | 1 | 44.7% | 45-45% | 0.0% |
| Ahigh_close | 1 | 43.9% | 44-44% | 0.0% |
| paired_high | 4 | 40.6% | 33-43% | 4.8% |
| connected_broadway | 1 | 40.1% | 40-40% | 0.0% |
| broadway_dry | 3 | 38.6% | 28-44% | 9.3% |
| connected_low | 5 | 38.0% | 32-48% | 6.7% |
| mid_dry | 4 | 34.4% | 33-39% | 3.0% |
| monotone | 1 | 34.2% | 34-34% | 0.0% |
| low_dry | 2 | 33.9% | 33-35% | 1.0% |
| Khigh_close | 2 | 33.9% | 22-46% | 17.2% |
| connected_mid | 6 | 31.1% | 21-48% | 10.8% |

## sub-family × hand_strength tier の cbet%

| sub-family | ナッツメイド | ストロング | ツーペア | トップペア以上 | ミドルペア | エア |
|---|---|---|---|---|---|---|
| Khigh_spread | 0% | 98% | 87% | 59% | 53% | 45% |
| paired_low | 73% | 75% | 0% | 53% | 53% | 46% |
| Ahigh_spread | 0% | 94% | 77% | 62% | 50% | 46% |
| paired_mid | 41% | 77% | 0% | 39% | 55% | 47% |
| Ahigh_close | 0% | 97% | 78% | 61% | 42% | 49% |
| paired_high | 71% | 69% | 0% | 27% | 55% | 47% |
| connected_broadway | 0% | 80% | 82% | 62% | 37% | 51% |
| broadway_dry | 0% | 100% | 85% | 61% | 36% | 50% |
| connected_low | 0% | 92% | 76% | 51% | 27% | 53% |
| mid_dry | 0% | 100% | 97% | 67% | 21% | 52% |
| monotone | 0% | 73% | 84% | 58% | 34% | 51% |
| low_dry | 0% | 100% | 100% | 67% | 21% | 51% |
| Khigh_close | 0% | 96% | 88% | 63% | 31% | 50% |
| connected_mid | 0% | 88% | 73% | 56% | 18% | 53% |

## 解釈: cell ごとの細かい cbet% パターン

- stddev が大きい subfamily = board 依存性大、tier 内でばらつき
- 「特定 tier だけ cbet が偏る」spots は MATCHA で個別に扱うべき
- 同じ row 内で tier 間 cbet% 差が 30%+ の場合 = tier 区分が明確 ✓
- 同じ col 内で sub-family 間 cbet% 差が 20%+ の場合 = board が tier の役割を変える

## 顕著な outlier (sub-family × tier で特異な行動)

| sub-family | tier | local cbet | tier baseline | 差 | n |
|---|---|---:|---:|---:|---:|
| paired_low | ツーペア | 0% | 67% | -67% | 3 |
| paired_high | ツーペア | 0% | 67% | -67% | 4 |
| paired_low | ナッツメイド | 73% | 13% | +61% | 3 |
| paired_high | ナッツメイド | 71% | 13% | +58% | 4 |
| low_dry | ツーペア | 100% | 67% | +33% | 2 |
| mid_dry | ツーペア | 97% | 67% | +31% | 4 |
| paired_high | トップペア以上 | 27% | 55% | -29% | 4 |
| Khigh_close | ツーペア | 88% | 67% | +21% | 2 |
| paired_high | ストロング | 69% | 90% | -20% | 4 |
| Khigh_spread | ツーペア | 87% | 67% | +20% | 4 |
| connected_mid | ミドルペア | 18% | 37% | -19% | 6 |
| broadway_dry | ツーペア | 85% | 67% | +18% | 3 |
| paired_high | ミドルペア | 55% | 37% | +18% | 4 |
| paired_low | ミドルペア | 53% | 37% | +16% | 3 |
| mid_dry | ミドルペア | 21% | 37% | -16% | 4 |
| Khigh_spread | ミドルペア | 53% | 37% | +16% | 4 |
| low_dry | ミドルペア | 21% | 37% | -16% | 2 |