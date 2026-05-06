# 既存 TexasSolver 実測データの完全 survey

実施日: 2026-05-05

knowledges/ 配下の **1292 JSON ファイル + 多数 CSV/MD** を survey した結果。

## 1. 全体規模

```
JSON ファイル総数:     1,292
シナリオディレクトリ: 30+ (volume4/scenarios/, volume4/results/, flop/results/)
タスク識別子:         102, 103, 105, 106, 107, 108, phase1, c_coef_*, ...
```

## 2. メイン scenario 別の内容

### 102: ターン CBet 頻度モデル (BDM_turn) ★最大規模

```
件数: 270 (全ボード × 全ターンカード)
内容: 30 フロップ × 9 ターンカード = 270 シナリオ
カテゴリ: overcard 53, blank 105, pair 60, connector 42, flush 10
```

**用途**: バレルスコア検証 / ターンドロー加点 / ターン HandScore 検証

### 103: リバー V/B 配分検証

```
件数: 30 (10 ボード × 3 alpha 値)
ボード: Adry / BdryK / Cpaired / Dtrips / Estraight / Fflush / Gmono ほか
alpha: 25 / 43 / 55.5 (=33% / 75% / 150% pot 相当)
```

**用途**: リバー α 式 + 後手スコア検証

### 105: ブロッカー検証 ★

```
件数: 20 (4 タイプ × 5 ボード)
タイプ: AA_vs_88 / missed_fd / reverse_block
```

**用途**: ブロッカー加点の equity 換算（調査330）

### 106: MDF 検証 (リバー 75%)

```
件数: 20 (8 ボード × balanced/tight)
ボード: Adry / BoardTrips / FlushDone / FourStraight / FullHouseable / Kdry / LowStraight / Monotone
```

**用途**: 後手スコア閾値 + C 値検証（調査326）

### 107: ベットサイズ検証 (ターン)

```
件数: 10 (4 フロップ × 各種ターンカード)
ボード: 987ss / J75r / K72r / T98r
```

**用途**: ターン C 値検証

### 108: フロップ HOOK 検証

```
件数: 30 (3 タイプ × 10 ボード)
タイプ: ahigh_check / bb3bet_defense / monotone_small
ベットサイズ: 33%
```

**用途**: フロップ後手スコア + 役カテゴリ検証

### 104: その他 (16 ファイル)

詳細未確認

## 3. 集約済み解析データ ★最重要

### `knowledges/volume4/results/phase1/` ← **最も使える**

3 主要ボードでのフル集約データ:
- `kc7d2s/` (K72r ドライ A=3)
- `khjd7s/` (KJ7r セミ A=2)
- `th9d8c/` (T98r ウェット A=1)

各ボード配下に CSV:
```
defender_summary.csv:  board × bet_pct × bucket × {n, fold%, call%, raise%}
aggressor_summary.csv: board × board_type × A × bucket × {check%, bet_total%, bet_33%, bet_50%, bet_75%}
cr_response_summary.csv: board × cbet_pct × bucket × {fold%, call%, reraise%}
```

**この CSV がそのまま新仕様検証に使える**！

### 主要ボード別データ (kc7d2s = K72r、抜粋):

```
33% ベット:
  H3 (n=10): R 100%
  H2 (n=69): C 31.2% / R 68.8%
  H1 (n=490): F 14.5% / C 81.0% / R 4.4%

50% ベット:
  H3: R 100%
  H2: C 47.7% / R 52.3%
  H1: F 49.9% / C 46.8% / R 3.3%

75% ベット:
  H3: R 100%
  H2: C 56.0% / R 44.0%
  H1: F 54.4% / C 43.8% / R 1.9%
```

### `ds_framework_recheck/` ← **後手スコア検証済み**

27 cases × 3 ボード × 3 ベットサイズの後手スコア検証:
- **一致率: 23/27 = 85.2%**（境界含めて 96.3%）
- 旧 C 値 (33%=3, 50%=4, 75%=6) で検証
- 新 C 値 (50%=5, 75%=7) ではまだ未検証

### `c_coef_verify/` ← **C 値検証データ**

```
100% pot ベット時の MDF (10 ボード):
  Adry: 0.4899 / Kdry: 0.4992 / BoardTrips: 0.5020 / TwoPair: 0.4982
  FlushDone: 0.4751 / FullHouseable: 0.4735 / FourStraight: 0.4715
  LowStraight: 0.8065 / StraightDone: 0.3873 / Monotone: 0.3472

150% pot ベット時の MDF:
  Adry: 0.2469 / Kdry: 0.2659 / BoardTrips: 0.3406 / TwoPair: 0.3014
  FlushDone: 0.2431 / FullHouseable: 0.2417 / ...
```

理論値 (100% → MDF=50%、150% → MDF=40%) との差を示す。

### `c_coef_srp/` ← **SRP 用 C 値の境界検証**

K72r SRP での個別ハンド (JJ, TT, ...) の DS とアクション割合を集約済み。

### `barrel_score_verify/` ← **バレルスコア検証**

```
セル一致率: 14/16 = 87.5%
シナリオ一致率: 149/198 = 75.3%
```

ボード × ターンカードの組み合わせで実測 CBet 頻度を集約済み。

### `role_score_verify/` ← **役スコア検証**

```
K72r 上の 8 cases:
  K7o (two_pair, HS=18): R 100% ✓
  KQo (tpgk, HS=15): C 63.6% / R 36.4% ✓
  KJo (tpmk, HS=8): C 90.6% / R 9.4% ✓
  ...
  
一致率: 7/8 = 87.5%
```

役カテゴリと GTO 実測の対応マッピング。

### `draw_bonus_verify/` ← **ドロー加点検証**

BDFD 単独、BDFD+ペア等のドロー組み合わせでの DS と GTO 比較。

### `flop/results/handscore_boundary/` ← **HandScore 境界**

14 cases で HandScore バケツ判定の境界:
- ナッツFD単独 [HS=13 H2]: vs 33% → R 80.1% (実測は H3 寄り)
- 非ナッツFD [HS=13 H2]: vs 33% → C 99% (H2 想定通り)
- TPMK + nut FD [HS=21]: R 100% (H3 強)
- gutshot 単独 [HS=10]: C 58.9% / R 41.1% (H2 中位)
- BDFD 単独 [HS=4]: F 15.8% / C 84.2% (H1 寄り)

**境界が「H2 と H3 の差は HS≈14」、「H1 と H2 の差は HS≈7」と確認済み**。

### `flop_accuracy_30*/` ← **フロップ精度評価セット**

30 ボード × 複数 setting (no_overbet, mr1-3, bs_a-c, single33, multistreet, 200k 等)
合計: 約 300 シナリオ

**用途**: フロップでの簡易レンジスコア検証データの集大成

### `3bp_verify/` ← **3-bet ポット検証**

3 シナリオ (A/B/C) × ハンド別アクション集計:
- AA: C 53.7% / R 46.3%
- KK: C 69.3% / R 30.7%
- QQ: C 97.5% / F 2.1% / R 0.4%

3BP 想定の SPR 4-5 で各役の挙動を直接確認できる。

## 4. 外部データ

```
flop-advanced/external/gto_wizard_blog/
  - GTO Wizard 公開記事の OCR + 解析
  - book_verification_report.md (本書との照合レポート)
  - extracted_data.json (チャート抽出データ)
```

## 5. 新 HandScore 設計に直接使えるデータ

| 新仕様の項目 | 既存データソース | 新規実行必要？ |
|---|---|---|
| 役スコア値 (TPTK, TPGK, ...) | role_score_verify, phase1, 108 | **No** (集計再計算で導出可能) |
| 閾値 (CR/コール/フォールド境界) | ds_framework_recheck, phase1 | **No** |
| C 値 (新スケール) | c_coef_verify, c_coef_srp, ds_framework_recheck | **No** |
| A 値 (ボード補正) | phase1 (3 board types), 108 | **No** |
| M 値 (マルチウェイ) | flop_accuracy_30_mr1/mr2/mr3 | **要確認** |
| ドロー加点 (Rule of 2/4) | draw_bonus_verify, handscore_boundary | **No** |
| ブロッカー加点 | 105 (blocker_*) | **No** |
| バレルスコア | barrel_score_verify, 102 | **No** |
| フロップ-ターン-リバー連続性 | 102 + 103 + 106 | **No** |

**結論: 新 TexasSolver 実行はほぼ不要**。既存データの分析で十分。

## 6. 特に新仕様検証に重要なファイル Top 10

```
1. knowledges/volume4/results/ds_framework_recheck/result.json
   ↑ 後手スコア式の現状一致率 85.2% / 96.3%（境界含む）

2. knowledges/volume4/results/phase1/{kc7d2s,khjd7s,th9d8c}/defender_summary.csv
   ↑ 3 ボード × 3 ベットサイズ × 3 バケツのフル集約

3. knowledges/volume4/results/role_score_verify/role_score_verify_result.json
   ↑ 役カテゴリ × HS × DS × GTO 実測の対応

4. knowledges/volume4/results/c_coef_verify/c_coef_summary.json
   ↑ ボード別 MDF 実測値

5. knowledges/flop/results/handscore_boundary/summary_v2.json
   ↑ HandScore バケツ境界 14 cases

6. knowledges/volume4/results/draw_bonus_verify/draw_bonus_verify_result.json
   ↑ ドロー加点の実測検証

7. knowledges/volume4/results/barrel_score_verify/barrel_score_verify_result.json
   ↑ バレルスコア 16 セル / 198 シナリオの検証

8. knowledges/volume4/results/3bp_verify/summary.json
   ↑ 3BP 用 役 × アクション集計

9. knowledges/volume4/results/c_coef_srp/result.json
   ↑ SRP 用 C 値境界検証

10. knowledges/volume4/results/103/river_vb_103_*.json
    ↑ リバー V/B 配分検証データ
```

## 7. 推奨次ステップ

### Step 1: 集約 CSV から新仕様の検証 (即着手可能、4-6 時間)

```python
# 擬似コード
import pandas as pd

# Phase1 から 3 board × 3 bet × 3 bucket = 27 cases を読む
df_def = pd.concat([
    pd.read_csv("knowledges/volume4/results/phase1/kc7d2s/defender_summary.csv"),
    pd.read_csv("knowledges/volume4/results/phase1/khjd7s/defender_summary.csv"),
    pd.read_csv("knowledges/volume4/results/phase1/th9d8c/defender_summary.csv"),
])

# 各 spot で「raise_pct ≥ 50%」を CR、「fold_pct ≥ 50%」を フォールド、それ以外コールとして
# 新スケール HS と GTO 実測を比較

# 同様に c_coef_verify, role_score_verify を読み込んで全体一致率を計算
```

### Step 2: 不足部分のみ TexasSolver 追加実行 (オプション、1-2 時間)

- マルチウェイ M 値の検証（既存 flop_accuracy_30_mr* で部分カバー）
- リバーの新スケール HS 検証 (103 + 106 で十分)

### Step 3: 統合 + 新仕様提案 (調査331)

集計結果から新スケールパラメータを最終確定:
- 役スコア値（TPTK = 65 か 68 か 70 か）
- 閾値（CR ≥ 50 か ≥ 45 か ≥ 55 か）
- C 値（α そのまま vs 修正版）

## 8. 結論

**既存 TexasSolver 実測データは新 HandScore 設計に十分**。新規実行はほぼ不要。

データ充実度:
- ボード分類: 主要 3 ボード（dry/semi/wet）でフル集約済み ★
- ベットサイズ: 33%/50%/75%/100%/150% 全部カバー ★
- ストリート: フロップ・ターン・リバー全部カバー ★
- 役カテゴリ: 主要 8-10 カテゴリで実測済み ★
- ドロー: FD/OESD/ガットショット/BDFD/BDSD カバー ★
- ブロッカー: 105 で集約済み ★

**Phase 0.5 の調査322-330 は、ほぼすべて既存データの再分析で完了可能**。

工数見積:
- 集約 CSV ベースの分析スクリプト作成: 半日
- 新仕様の検証と提案: 1 日
- **計 1.5 日** で Phase 0.5 完了 (新規 TexasSolver 実行ゼロの場合)
