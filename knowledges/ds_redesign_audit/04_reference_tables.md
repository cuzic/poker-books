# 調査04: 早見表・付録の係数表 inventory

実施日: 2026-05-05

## 表のカテゴリ別ファイル数

| 表カテゴリ | ファイル数 | 主要ファイル |
|---|---:|---|
| C 係数表（ベット負担） | 11 | vol4/10/11/13/15, vol5/10/11/12, vol6/23, digest/12/19/21 |
| A 係数表（ボード値） | 14 | vol4/10/11/13/15, vol5/10/11/12/14, vol6/23, digest/12/19/21, flop/16 |
| M 係数表（マルチウェイ） | 9 | vol4/10/11, vol5/11/12, vol6, digest/12/16/19/21, flop/16 |
| HandScore 早見表 | 4 | vol4/17/18, flop/teaching/* |
| α 早見表 | 4 | vol4/09/17, digest/11, digest/plan.md |
| ドロー加点表 | 2 | flop/05, vol4/10 |
| 9 マスマトリクス | 10 | digest/08/20, vol4/19, vol6/24 ほか |
| 役スコア表 | 9 | flop/05, vol4/07/15, flop-advanced/03, digest/07/12, vol5/12/19 |
| ブロッカー加点表 | 9 | flop/05/07, vol4/07, flop-advanced/03, vol5/05/11/15/19, digest/07 |

**重複を除いた要更新ファイル数: 推定 30-35 ファイル**

## 主要表の所在

### C 係数表（11 ヶ所）

```
volume4/chapters/10-defender-score-turn.md     ← 標準形 33%=3 / 50%=5 / 75%=7
volume4/chapters/11-defender-score-river.md    ← 拡張形 100%=9 / 150%=11
volume4/chapters/13-oop-defense-basic.md
volume4/chapters/15-check-behind-bluffcatch.md
volume5/chapters/10-three-bet-pot.md
volume5/chapters/11-sb-vs-bb.md
volume5/chapters/12-multiway.md
volume6/chapters/23-appendix-b.md              ← 巻⑥ 付録B
digest/chapters/12-defender-score-turn-river.md
digest/chapters/19-appendix-a.md
digest/chapters/21-appendix-c.md
```

### 役スコア表（9 ヶ所）

```
flop/chapters/05-hand-strength-basic.md         ← 巻② Ch5 で初導入（最重要）
flop/chapters/09-hand-score-detailed.md         ← 巻② Ch9 で詳細化
flop-advanced/chapters/03-precise-hand-score.md ← 巻③ Ch3 で精密化
volume4/chapters/07-blocker-basics.md
volume4/chapters/15-check-behind-bluffcatch.md
volume5/chapters/12-multiway.md
volume5/chapters/19-appendix-c.md               ← 巻⑤ 付録C
digest/chapters/07-hand-score.md                ← digest Ch7
digest/chapters/12-defender-score-turn-river.md
```

### ドロー加点表（2 ヶ所、最重要）

```
flop/chapters/05-hand-strength-basic.md         ← 詳細版（FD +13、OESD +14、etc）
volume4/chapters/10-defender-score-turn.md      ← ターン版（FD +13、OESD +12、etc）
```

**注**: 案【大】では「アウツ × 2 = Rule of 2 直接」に再設計するため、これらの表は**全面書き換え**が必要。

### α 早見表（4 ヶ所）

```
volume4/chapters/09-alpha-formula.md            ← α 式定義章
volume4/chapters/17-appendix-a.md               ← 巻④ 付録A
digest/chapters/11-alpha-formula.md             ← digest Ch11
digest/plan.md                                  ← digest 設計メモ
```

α 値（0.25 / 0.33 / 0.43 / 0.50 / 0.60）は equity と直結のため、**スケール変更不要**。ただしC 係数を新スケールにすると α-MDF 早見表の C 列は要更新。

### 9 マスマトリクス（10 ヶ所）

```
digest/chapters/08-defender-score-flop.md
digest/chapters/20-appendix-b.md
volume4/chapters/19-appendix-c.md
volume6/chapters/24-appendix-c.md
preflop/chapters/00-introduction.md
+ 計画ファイル数件
```

9 マスは「役割×頻度帯」のため、HandScore スケール変更の影響は限定的。ただし HandScore の境界値（H1/H2/H3 の閾値）が変わるため**境界数値は要更新**。

## 表別 影響度評価

| 表カテゴリ | スケール変更影響 | 工数 |
|---|---|---:|
| 役スコア表 | **大**（全値が equity % で再定義） | 4 時間 |
| ドロー加点表 | **大**（アウツ × 2 ベース化） | 1 時間 |
| C 係数表 | **中**（equity %スケールで再導出） | 2 時間 |
| A 係数表 | **中**（equity %換算値） | 1 時間 |
| M 係数表 | **中**（equity %換算値） | 30 分 |
| HandScore 早見表 | **大**（全 HS 値の再表示） | 1 時間 |
| α 早見表 | 小（αは不変、C 列のみ更新） | 30 分 |
| 9 マスマトリクス | **中**（境界 HS 値の更新） | 1 時間 |
| 役割マッピング | 小（役割名は変わらない） | 30 分 |
| ブロッカー加点表 | **中**（equity % 換算） | 30 分 |

**合計工数: 約 12 時間（≒ 1.5 日）**

## 表更新時の注意

1. **役スコア表は全巻で値が一致している必要**
   - 巻② / 巻③ / 巻④ / 巻⑤ / digest で同じ値を参照
   - 1 ヶ所変えると 9 ヶ所同期が必要

2. **C/A/M 表も全巻で同期**
   - 14 ヶ所の A 表、11 ヶ所の C 表、9 ヶ所の M 表が同じ値

3. **ドロー加点表は計算式（アウツ × 2）も明記**
   - 暗算式として読者に提示

## 結論

- 表の総数: **推定 70-80 個**（各章の小表含む）
- 要更新ファイル: **30-35 ファイル**
- 工数: **12 時間（1.5 日）**
- **役スコア表とドロー加点表が最も影響大**（各値の equity % 換算が必要）
- **同期が課題**（同じ値を異なる章で参照しているため、ジェネレータ化が望ましい）
