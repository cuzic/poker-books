# 巻③ (flop-advanced) 新スケール対応 変更点記録

確定日: 2026-05-05
新仕様: SPEC_HANDSCORE.md / SPEC_OTHER_FORMULAS.md (案【大】= 0-100 equity %)

## 更新したファイル

1. `flop-advanced/chapters/00-introduction.md` — 道具マップ HS 境界更新
2. `flop-advanced/chapters/01-bdm-v5.md` — 後手スコア式の "−3" 削除、境界 HS 更新
3. `flop-advanced/chapters/02-mixed-strategy-r1-r6.md` — 9 マス HS 境界、R5 役スコア閾値
4. `flop-advanced/chapters/03-precise-hand-score.md` — 主要章、全面改訂
5. `flop-advanced/chapters/17-comprehensive-drill.md` — ドリル例題の HS 値
6. `flop-advanced/chapters/18-appendix.md` — Value/Bluff 圧の HS 閾値、C 係数注記

## 主な変更パターン

### 役スコア (主要対応)

| 役 | 旧 (0-30) | 新 (0-100 equity%) |
|---|---:|---:|
| ストレートフラッシュ / クワッズ | 30 | 95 |
| Top set | 30 | 92 |
| Mid set / Bottom set / Trips | 30 | 85-88 |
| 2 ペア top | 18 | 78 |
| オーバーペア高 (AA/KK/QQ) | 20 | 78 |
| オーバーペア中 (JJ-TT) | 20 | 72 |
| TPTK | 18 | 70 |
| TPGK | 15 | 62 |
| TPMK | 8 | 50 |
| TPWK | 6 | 45 |
| セカンドペア | 3-9 | 32-42 |
| ボトムペア | 4 | 32 |
| A ハイ | 0 | 25 |
| K ハイ | 0 | 20 |
| 完全空振り | 0 | 8 |

### ドロー加点 (フロップ、Rule of 4)

| ドロー | 旧 | 新 |
|---|---:|---:|
| FD | +13 | +36 |
| OESD | +14 | +32 |
| ガットショット | +10 | +16 |
| FD + OESD (13 outs) | +17 | +52 |
| FD + ガットショット (12) | +14 | +48 |
| BDFD | +4 | +5 |
| ナッツ BDFD | +6 | +8 |
| ナッツ FD | +16 | +44 |
| BDSD | +2 | +2 |

### 9 マス HS 境界

- 旧: 強 ≥14 / 中 7-13 / 弱 <7 (または 0-6)
- 新: 強 ≥65 / 中 35-64 / 弱 <35

### 型別補正

| 型 | 旧 | 新 |
|---|---:|---:|
| 型1 (ハイ×ドライ) | 0 | 0 |
| 型2 (ハイ×ウェット) | -3 | -10 |
| 型3 (ロー×ドライ) | -2 | -8 |
| 型4 (ロー×ウェット) | -8 | -25 |
| 型5 (モノトーン) | -10 | -35 |
| 型6 (ペア+高キッカー) | +2 | +5 |

### 後手スコア式の削減

- 旧: 後手スコア = HandScore + A − 3 − C − M (ベースライン補正 -3 込)
- 新: 後手スコア = HandScore + A − C − M ("−3" は A 値に吸収)

### Value 圧 / Bluff 圧 (付録 J)

- 旧: Value 圧 = HS≥14 が bet される確率 / Bluff 圧 = HS≤4
- 新: Value 圧 = HS≥65 / Bluff 圧 = HS≤25

## 巻② との整合性検証

- 巻② 役スコア表 (TPTK=70, TPGK=62, TPMK=50, TPWK=45) と一致 ✓
- 巻② 9 マス境界 (≥65 / 25-64 / <25) と一致 ✓
- 巻② 後手スコア式 (HandScore + A − C − M) と一致 ✓
- 精密版 (本巻 ch3) は ±5 以内のオフセット (例 5: 巻② TPTK + BDFD = 75 vs 精密 78) ✓
- 型別補正は強ハンドのみに適用 (中/弱は変更なし) ✓

## 残課題

- 章 03 の Ablation 表 (81%→92%) は質的記述のため変更不要
- 章 04 (17 型) は CBet 頻度のため新スケール影響なし
- 章 05-15 は質的記述中心で具体的 HS 値はほぼ無し
- 章 09 (range-vs-range) の 5 バケット (Equity %) は元から % のため整合
