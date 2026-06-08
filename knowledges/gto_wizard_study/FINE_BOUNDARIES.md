# 細分化 boundary 分析 — 42 boards、subfamily × hand_strength

既存 board family (POLAR/MERGED/CONDENSED) より細かい sub-family で分析。

## 13 sub-families (board 構造ベース)

| sub-family | 判定条件 | n probes |
|------------|---------|---------:|
| paired_low | paired + 2-4 | 5 |
| Khigh_spread | K-high、gap ≥5 | 6 |
| Ahigh_spread | A-high、gap ≥5、non-connected | 9 |
| broadway_dry | broadway high non-connected | 6 |
| Ahigh_close | A-high、gap <5 | 1 |
| paired_mid | paired + 5-9 | 6 |
| paired_broadway | paired top + T-Q | 3 |
| connected_low | connected + high 2-6 | 9 |
| paired_high | paired top + K/A high | 5 |
| low_dry | low board (5-high以下)、rainbow | 2 |
| Khigh_close | K-high、gap <5 | 2 |
| mid_dry | その他 | 7 |
| connected_broadway | connected + high T+ | 3 |
| monotone | 3 同 suit | 3 |
| connected_mid | connected + high 7-9 | 10 |

## sub-family ごとの cbet 頻度 (BTN attacker)

| sub-family | n | cbet 平均 | 範囲 | stddev |
|------------|---:|---------:|------|------:|
| paired_low | 5 | 50.1% | 45-57% | 6.4% |
| Khigh_spread | 6 | 48.0% | 44-50% | 2.6% |
| Ahigh_spread | 9 | 46.0% | 25-50% | 7.9% |
| broadway_dry | 6 | 44.9% | 28-52% | 9.1% |
| Ahigh_close | 1 | 43.9% | 44-44% | 0.0% |
| paired_mid | 6 | 42.0% | 40-45% | 2.5% |
| paired_broadway | 3 | 41.9% | 39-44% | 2.4% |
| connected_low | 9 | 41.3% | 32-59% | 10.6% |
| paired_high | 5 | 41.1% | 33-43% | 4.3% |
| low_dry | 2 | 33.9% | 33-35% | 1.0% |
| Khigh_close | 2 | 33.9% | 22-46% | 17.2% |
| mid_dry | 7 | 33.3% | 28-39% | 3.7% |
| connected_broadway | 3 | 32.5% | 17-40% | 13.0% |
| monotone | 3 | 29.2% | 15-38% | 12.4% |
| connected_mid | 10 | 28.5% | 21-48% | 9.1% |

## sub-family × hand_strength tier の cbet%

| sub-family | ナッツメイド | ストロング | ツーペア | トップペア以上 | ミドルペア | エア |
|---|---|---|---|---|---|---|
| paired_low | 74% | 74% | 0% | 52% | 58% | 45% |
| Khigh_spread | 0% | 98% | 81% | 59% | 52% | 46% |
| Ahigh_spread | 0% | 94% | 78% | 61% | 47% | 47% |
| broadway_dry | 0% | 100% | 89% | 60% | 43% | 48% |
| Ahigh_close | 0% | 97% | 78% | 61% | 42% | 49% |
| paired_mid | 54% | 75% | 0% | 42% | 51% | 46% |
| paired_broadway | 75% | 71% | 0% | 27% | 56% | 46% |
| connected_low | 0% | 90% | 72% | 51% | 31% | 52% |
| paired_high | 74% | 69% | 0% | 21% | 56% | 46% |
| low_dry | 0% | 100% | 100% | 67% | 21% | 51% |
| Khigh_close | 0% | 96% | 88% | 63% | 31% | 50% |
| mid_dry | 0% | 100% | 96% | 66% | 18% | 52% |
| connected_broadway | 0% | 83% | 82% | 61% | 25% | 52% |
| monotone | 0% | 77% | 78% | 53% | 27% | 52% |
| connected_mid | 0% | 89% | 73% | 53% | 15% | 54% |

## 解釈: cell ごとの細かい cbet% パターン

- stddev が大きい subfamily = board 依存性大、tier 内でばらつき
- 「特定 tier だけ cbet が偏る」spots は MATCHA で個別に扱うべき
- 同じ row 内で tier 間 cbet% 差が 30%+ の場合 = tier 区分が明確 ✓
- 同じ col 内で sub-family 間 cbet% 差が 20%+ の場合 = board が tier の役割を変える

## 顕著な outlier (sub-family × tier で特異な行動)

| sub-family | tier | local cbet | tier baseline | 差 | n |
|---|---|---:|---:|---:|---:|
| paired_low | ツーペア | 0% | 61% | -61% | 5 |
| paired_high | ツーペア | 0% | 61% | -61% | 5 |
| paired_mid | ツーペア | 0% | 61% | -61% | 6 |
| paired_broadway | ツーペア | 0% | 61% | -61% | 3 |
| paired_broadway | ナッツメイド | 75% | 17% | +58% | 3 |
| paired_high | ナッツメイド | 74% | 17% | +57% | 5 |
| paired_low | ナッツメイド | 74% | 17% | +57% | 5 |
| low_dry | ツーペア | 100% | 61% | +39% | 2 |
| paired_mid | ナッツメイド | 54% | 17% | +37% | 6 |
| mid_dry | ツーペア | 96% | 61% | +35% | 7 |
| paired_high | トップペア以上 | 21% | 53% | -32% | 5 |
| broadway_dry | ツーペア | 89% | 61% | +28% | 6 |
| Khigh_close | ツーペア | 88% | 61% | +27% | 2 |
| paired_broadway | トップペア以上 | 27% | 53% | -26% | 3 |
| connected_mid | ミドルペア | 15% | 38% | -22% | 10 |
| connected_broadway | ツーペア | 82% | 61% | +21% | 3 |
| paired_low | ミドルペア | 58% | 38% | +20% | 5 |
| Khigh_spread | ツーペア | 81% | 61% | +20% | 6 |
| paired_high | ストロング | 69% | 88% | -19% | 5 |
| mid_dry | ミドルペア | 18% | 38% | -19% | 7 |