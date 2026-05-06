# 既存 GTO データの inventory（Phase 0.5 着手前）

実施日: 2026-05-05

ご指摘の通り、新 HandScore 仕様を確定する前に GTO 実測ベンチマークが必要。
まず**既存の TexasSolver 実測データを inventory** し、新規実行が必要な範囲を絞り込む。

## TexasSolver 環境

- バイナリ: `/home/cuzic/TexasSolver/build/console_solver`
- 既存データ: `knowledges/volume4/results/`、`knowledges/flop/results/`

## 既存シナリオの分布

### Scenario 102 (ターン CBet 検証、最大規模)

```
件数: 270 ファイル
内容: ターン CBet 解析 (632r / 772 / etc 多数のフロップ × ターンカード)
ボード: 632r, 772, J84tt, K72r, T98ss など 主要 10+ フロップ
ターンカード: 各フロップに 9-10 種のターンカード
カバー: 主要フロップ × 主要ターンカード = 100+ ボード
```

**価値**: ターン版 HandScore + ドロー加点の検証に最適。

### Scenario 103 (リバー V/B 検証)

```
件数: 30 ファイル
内容: リバーバリュー・ブラフ配分 (alpha 値別)
ボード: Adry1 (As Kh 7d 4c 2s) / BdryK / Cpaired / Dtrips / Estraight / Fflush / Gmono
alpha 値: 25 / 43 / 55.5 (= 33%/75%/150% pot 相当)
```

**価値**: リバー版 HandScore + α 式の検証に最適。

### Scenario 105 (ブロッカー検証)

```
件数: 20 ファイル
内容: ブロッカー保有 vs 非保有での GTO 比較
ボード: 主要 10 リバーボード × ブロッカー有無
```

**価値**: ブロッカー加点の最適化（調査30）に直接使用可能。

### Scenario 106 (MDF 検証、リバー)

```
件数: 20 ファイル
内容: リバー 75% bet vs balanced/tight ranges
ボード: Adry / BoardTrips / FlushDone / FourStraight / FullHouseable / Kdry / LowStraight / Monotone (8 種類)
```

**価値**: 後手スコア閾値・C 値の検証に使用可能。

### Scenario 107 (ベットサイズ検証、ターン)

```
件数: 10 ファイル
内容: ターン後の各ボードでのベットサイズ別検証
ボード: 987ss / J75r / K72r / T98r (4 種類) × blank/flush/pair/conn/over (5 ターンカード)
```

**価値**: ターンの C 値検証。

### Scenario 108 (フロップ HOOK 検証)

```
件数: 30 ファイル
内容: フロップでの IP first action / BB 3-bet defense / monotone small bet
ボード: ahigh × 5 / bb3bet × 5 / monotone × 5 = 計 15 ボード
ベットサイズ: 33%
```

**価値**: フロップ版 HandScore + 後手スコア の検証に直接使用可能。

## 補助スクリプト

```
scripts/handscore_*.py: HandScore 計算と GTO 比較スクリプト群 (10+ ファイル)
scripts/ds_framework_recheck.py: 後手スコア検証
scripts/texassolver_c_coef_verify.py: C 値検証
scripts/barrel_score_verify.py: バレルスコア検証
scripts/handscore_v2_evaluation.py: v1 vs v2 比較
```

これらは TexasSolver 出力を分析する既存パイプライン。

## カバー状況の評価

| 調査タスク | 既存データの十分度 | 不足分の追加実行コスト |
|---|---|---|
| #322 フロップ equity 実測 | △ (108 で部分カバー) | 1〜2 時間で追加可能 |
| #323 ターン equity 実測 | ◎ (102 で広範囲カバー) | 既存データで十分 |
| #324 リバー equity 実測 | ◎ (103, 105, 106) | 既存データで十分 |
| #325 閾値逆算 | ◎ (各シナリオで CR/コール頻度あり) | 分析のみ |
| #326 C 値検証 | ◎ (107, 既存 c_coef_verify) | 分析のみ |
| #327 A 値検証 | ◎ (108 のボード別) | 分析のみ |
| #328 M 値検証 | △ (multiway データ少ない) | TexasSolver 追加実行必要 |
| #329 ドロー加点検証 | ○ (102, 105 で部分カバー) | 分析中心、一部追加 |
| #330 ブロッカー加点検証 | ◎ (105 が直接該当) | 分析のみ |
| #331 統合 | - | 分析時間のみ |

## 結論

**多くは既存データで分析可能**。新規 TexasSolver 実行が必要なのは:
- フロップでの広範囲役カテゴリの追加実測 (1-2 時間)
- マルチウェイの追加実測 (1-2 時間)

既存データの分析が **2-3 日** かかるので、まずは分析中心で進めるのが効率的。

## 推奨アプローチ

```
Phase 0.5 の優先順位:

優先 A (既存データのみで完結、即着手可能):
  #325 閾値逆算
  #326 C 値検証
  #327 A 値検証
  #330 ブロッカー加点検証

優先 B (既存データ中心 + 部分的に TexasSolver 追加):
  #322 フロップ equity 実測
  #323 ターン equity 実測 (既存十分)
  #324 リバー equity 実測 (既存十分)
  #329 ドロー加点検証

優先 C (TexasSolver 新規実行が主):
  #328 マルチウェイ M 値検証

優先 D (全データ統合):
  #331 統合 + 提案
```

優先 A から着手することで、新規 TexasSolver 実行を最小化しつつ実証ベースの設計が可能。

## 着手順序 (推奨)

```
1. 既存データの大規模分析スクリプト作成 (1日)
   → scripts/analyze_existing_gto_v2.py
   → 各シナリオの hand × equity × GTO action を抽出
   
2. 役カテゴリ別 equity 集計 (調査322/323/324 をカバー)

3. 閾値逆算 (調査325)

4. C/A/M 値の検証 (調査326/327/328)

5. ドロー加点・ブロッカー加点の検証 (調査329/330)

6. 不足部分のみ TexasSolver で追加実測 (1-2 時間)

7. 統合 + 新仕様提案 (調査331)
```

総工数: **3-4 日（フルタイム想定）**

## 次のステップ

#322 フロップ equity 実測の着手として:
- scripts/analyze_existing_gto_v2.py を作成し、既存データの分析を開始
- 不足が判明したら scenario 109 等で TexasSolver 追加実行
