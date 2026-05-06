# 調査01: HandScore 系統の使用箇所 audit

実施日: 2026-05-05

## キーワード別ヒット集計

| 巻 | HandScore (files / hits) | 後手スコア | 先手スコア | バレルスコア | α 式 |
|---|---:|---:|---:|---:|---:|
| preflop | 1 / 1 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| flop (巻②) | 11 / 132 | 3 / 19 | 3 / 10 | 1 / 1 | 0 / 0 |
| flop-advanced (巻③) | 9 / 97 | 3 / 4 | 1 / 3 | 4 / 6 | 0 / 0 |
| **volume4 (巻④)** | **14 / 295** | **16 / 465** | 3 / 8 | **15 / 196** | **18 / 126** |
| volume5 (巻⑤) | 17 / 185 | 19 / 360 | 3 / 7 | 19 / 209 | 17 / 133 |
| volume6 (巻⑥) | 8 / 57 | 12 / 112 | 0 / 0 | 10 / 62 | 10 / 45 |
| digest | 14 / 84 | 14 / 104 | 3 / 10 | 9 / 46 | 12 / 49 |

**観察:**

- 巻① preflop は HandScore を 1 度だけ言及（境界注意点として）
- 巻② flop が **HandScore 概念の導入元**（11 ファイル / 132 ヒット）
- **巻④ が最大密度**: HandScore 295・後手スコア 465・バレルスコア 196・α 式 126
- 巻⑤ は応用で参照中心、巻⑥ は ICM 補正コンテキスト
- digest は全巻のダイジェストとして満遍なく出現

## 章別ヒット密度ランキング (HandScore + 後手スコア)

```
190 hits  volume4/10-defender-score-turn.md       ← 後手スコア(ターン版)の式定義章
117 hits  volume4/11-defender-score-river.md       ← 後手スコア(リバー版)の式定義章
 98 hits  volume4/16-basic-drill.md                 ← 巻④基礎ドリル20問
 90 hits  volume4/13-oop-defense-basic.md          ← OOP応戦基礎
 88 hits  volume5/16-comprehensive-drill.md        ← 巻⑤総合ドリル50問
 75 hits  volume5/05-blocker-application.md        ← ブロッカー実戦選択
 72 hits  volume5/15-river-drill-advanced.md       ← リバードリル応用
 67 hits  volume6/19-formula-correction.md          ← トーナメント補正章
 56 hits  flop-advanced/03-precise-hand-score.md   ← 精密 HandScore 章
 53 hits  volume4/19-appendix-c.md                  ← 巻④付録C 巻1-3継承
 49 hits  volume5/04-multistreet-integration.md     ← マルチストリート統合
 47 hits  digest/12-defender-score-turn-river.md
 46 hits  volume4/15-check-behind-bluffcatch.md
 45 hits  volume5/19-appendix-c.md
 37 hits  volume5/12-multiway.md
 36 hits  digest/07-hand-score.md
 34 hits  volume5/13-hand-review.md
 33 hits  volume6/24-appendix-c.md
 30 hits  flop/16-multiway-3bet.md
 30 hits  flop/07-drill-beginner.md
```

**最重要章** (再設計時に最優先で書き換える):

| 順 | 章 | 役割 |
|---|---|---|
| 1 | volume4/10-defender-score-turn.md | 後手スコア(ターン版)の **式定義** |
| 2 | volume4/11-defender-score-river.md | 後手スコア(リバー版)の **式定義** |
| 3 | flop/05-hand-strength-basic.md | HandScore の **概念導入** |
| 4 | flop/09-hand-score-detailed.md | HandScore の **詳細定義** |
| 5 | volume4/08-barrel-score.md | バレルスコアの **式定義** |
| 6 | volume4/09-alpha-formula.md | α 式の **式定義** |
| 7 | flop-advanced/03-precise-hand-score.md | 精密 HandScore の **式定義** |
| 8 | digest/07-hand-score.md | digest の HandScore 章 |

## 「式の定義」章 vs 「式の参照」章

### HandScore 式定義 (`HandScore = 役スコア + ドロー加点`)

主な定義箇所（再設計の主戦場）:
- `flop/chapters/05-hand-strength-basic.md` ← 巻② 第5章
- `flop/chapters/07-drill-beginner.md`     ← 巻② 第7章ドリル
- `volume4/chapters/11-defender-score-river.md` ← リバー版で再定義
- `volume4/chapters/18-appendix-b.md`      ← 巻④付録B 用語集
- `volume4/chapters/19-appendix-c.md`      ← 巻④付録C 巻1-3継承
- `digest/chapters/07-hand-score.md`        ← digest
- `volume5/chapters/19-appendix-c.md`       ← 巻⑤付録C
- `volume6/chapters/19-formula-correction.md` ← 巻⑥補正章
- `volume6/chapters/23-appendix-b.md`       ← 巻⑥付録B
- `volume6/chapters/24-appendix-c.md`       ← 巻⑥付録C

### 後手スコア式定義 (`後手スコア = HandScore + A − 3 − C − M`)

主な定義箇所:
- `flop/chapters/16-multiway-3bet.md`           ← 巻② 第16章 (HU + multiway)
- `volume4/chapters/10-defender-score-turn.md`  ← ターン版定義
- `volume4/chapters/11-defender-score-river.md` ← リバー版定義
- `volume4/chapters/13-oop-defense-basic.md`    ← OOP応戦
- `digest/chapters/12-defender-score-turn-river.md` ← digest
- 各巻の付録C (継承章)

### バレルスコア式定義 (`バレルスコア = FlopType + TurnCard`)

- `volume4/chapters/06-turn-card-categories.md` ← TurnCard 分類
- `volume4/chapters/08-barrel-score.md`         ← バレルスコア式定義
- `digest/chapters/10-barrel-score.md`          ← digest

## 設計時の影響範囲（章数）

| 影響タイプ | 章数 | 工数概算 |
|---|---:|---|
| 式の定義章（要書き換え） | **15章** | 3日 |
| 式の参照章（数値追従のみ） | **40+章** | 2日 |
| ドリル問題章（解答再計算） | **8〜10章** | 2日 |
| 図版・付録 | **20+セクション** | 1日 |
| **合計** | **80+章/セクション** | **8日（フルタイム想定）** |

## 結論

- **影響範囲は巻① preflop を除く全 6 巻 + digest**
- **再設計の主戦場は巻④** (HandScore + 後手スコア + バレルスコア + α 式が全て式定義と例題で集中)
- **巻① preflop はほぼ独立**（Score 系統が別、HandScore 言及は 1 件のみ）→ 案【大】の影響を受けにくい
- **digest は全巻ダイジェストのため最後に統合更新**
