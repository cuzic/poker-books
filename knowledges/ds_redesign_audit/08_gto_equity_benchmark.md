# 調査08: GTO equity ベンチマーク調査（vs 典型レンジ）

実施日: 2026-05-05

## 既存 GTO 実測データの活用

`knowledges/volume4/results/` に TexasSolver 実測データが豊富にある:

```
102/, 103/, 105/, 106/, 107/, 108/   ← シナリオ別 SPR/ボード組み合わせ
3bp_verify/                           ← 3-bet ポット検証（A/B/C 3 シナリオ）
barrel_score_verify/                  ← バレルスコア検証
c_coef_verify/                        ← C 係数検証 (100% / 150% pot)
c_coef_srp/                           ← SRP での C 微調整
```

これらのデータから equity ベンチマークを抽出可能。

## 役カテゴリ別の典型エクイティ（推定値）

### vs BTN open vs BB defend (SRP, ドライ系ボード K72r 想定)

```
ナッツ級
  セット (Kx9x や 7x7x): vs BB random ≈ 88-92% / vs BB call range ≈ 78-85%
  ストレート/フラッシュ: vs random ≈ 80-90% / vs call ≈ 70-85%

強バリュー
  オーバーペア (QQ, JJ): vs random ≈ 75-82% / vs call ≈ 70-78%
  2ペア (top 2): vs random ≈ 78-85% / vs call ≈ 72-82%
  TPTK (AK on K72r): vs random ≈ 70-75% / vs call ≈ 65-72%

中強度
  TPGK (AQ on K72r): vs random ≈ 65-70% / vs call ≈ 58-65%
  TPMK (KT on K72r): vs random ≈ 60-65% / vs call ≈ 50-58%
  オーバーペア (88 on K72r = アンダーペア): vs random ≈ 50-55% / vs call ≈ 40-45%

弱
  TPWK (K2 on K72r、ドライ): vs random ≈ 55-60% / vs call ≈ 45-50%
  セカンドペア (77 on K72r = セカンドペア弱): vs random ≈ 50-55%
  アンダーペア (44 on K72r): vs random ≈ 38-45% / vs call ≈ 30-38%
  
ハイカード
  AJ オフ on 873 (マイス): vs random ≈ 28-32% / vs call ≈ 20-28%
```

### ドロー系のエクイティ

```
コンボドロー
  FD + OESD (15 outs): vs made hand ≈ 55-60% (Rule of 4 で 60%)
  
強ドロー
  FD (9 outs): vs made hand ≈ 35-38% (Rule of 4 で 36%)
  OESD (8 outs): vs made hand ≈ 32-35% (Rule of 4 で 32%)
  FD + ガットショット (12 outs): ≈ 47-50%

弱ドロー
  ガットショット (4 outs): vs made hand ≈ 16-18% (Rule of 4)
  BDFD (3 outs相当): vs made hand ≈ 12-14%
  BDSD (1 outs相当): vs made hand ≈ 4-6%
  2 OC (6 outs): vs made hand ≈ 24-27%
```

## 役スコア（新スケール）の推奨値

equity % をベースに、HandScore = equity % という設計とした場合:

| 役 | vs Wide Range | vs Tight Range | **新 HandScore（推奨）** |
|---|---:|---:|---:|
| ストレートフラッシュ | 99% | 98% | **99** |
| クワッズ | 97% | 95% | **97** |
| フルハウス | 92% | 88% | **92** |
| フラッシュ | 88% | 80% | **85** |
| ストレート | 82% | 75% | **80** |
| セット (set/trips) | 88% | 80% | **85** |
| 2 ペア (top 2) | 78% | 70% | **75** |
| オーバーペア | 75% | 68% | **72** |
| TPTK | 70% | 62% | **68** |
| TPGK | 65% | 55% | **60** |
| 2 ペア (split, weak) | 65% | 55% | **60** |
| TPMK | 55% | 45% | **50** |
| アンダーペア（強位） | 50% | 38% | **45** |
| TPWK | 50% | 40% | **45** |
| セカンドペア（強キッカー） | 48% | 38% | **42** |
| アンダーペア（中） | 42% | 32% | **38** |
| ボトムペア | 38% | 28% | **33** |
| セカンドペア（弱キッカー） | 35% | 25% | **30** |
| 役なし（A high） | 30% | 22% | **25** |
| 役なし（K-high 以下） | 22% | 15% | **18** |
| ハイカード（極弱） | 15% | 8% | **10** |

## ストリート別の equity 補正

### フロップでのドロー加点（Rule of 4 ベース）

```
ドロー加点 = アウツ × 4（2 ストリート分の equity）

例:
  FD (9 outs): +36%
  OESD (8 outs): +32%
  ガットショット (4 outs): +16%
  FD + OESD (15 outs): +60%
  BDFD (~3 outs): +12%
  BDSD (~1.5 outs): +6%
  2 OC (6 outs): +24%
```

### ターンでのドロー加点（Rule of 2 ベース）

```
ドロー加点 = アウツ × 2（1 ストリート分の equity）

例:
  FD (9 outs): +18%
  OESD (8 outs): +16%
  ガットショット (4 outs): +8%
  FD + OESD (15 outs): +30%
  2 OC (6 outs): +12%
```

### リバーでのドロー加点

```
ドロー加点 = 0（確定済み）
```

### ストリート係数の必要性

Rule of 4 をフロップで使うと、極端なケースで equity が 100% を超える可能性:

例: TPGK + FD + OESD on flop
- 役スコア: 60% (TPGK)
- ドロー加点: アウツ × 4 = 9+8 - 4 (重複) ≈ 13 outs × 4 = 52%
- 合計: 60 + 52 = **112%**（超過）

**対策**: HandScore に上限 95% を設定するか、コンボドロー時に補正（ドロー加点 × 0.7 など）。

## 結論

- 既存データ (`knowledges/volume4/results/`) を活用すれば equity ベンチマーク取得可能
- 役カテゴリ別 equity を新 HandScore（0-100 スケール）に直接マッピング可能
- フロップ Rule of 4 を採用するとコンボドローで超過する可能性 → 補正が必要
- **推奨: HandScore 上限 95、コンボドロー時に重複アウツ控除を組み込む**

## 次フェーズで決めるべき設計パラメータ

1. HandScore の上限値（95? 100?）
2. コンボドローの重複アウツ控除ルール
3. 「vs Wide」 vs 「vs Tight」のどちらを基準とするか
4. ブロッカー加点の % 換算（次タスク #289）
