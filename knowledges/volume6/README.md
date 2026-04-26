# 巻6（トーナメント編）リサーチ成果

`volume6/plan.md` の章執筆に使う ICM 計算結果と Push/Fold チャートを格納。

## ファイル一覧

| ファイル | 内容 | 主な用途章 |
| :--- | :--- | :--- |
| [01_icm_theory.md](01_icm_theory.md) | ICM 理論と Malmuth-Harville アルゴリズム | 第3章「ICM の直感的理解」、付録C |
| [02_icm_tables.md](02_icm_tables.md) | ICM equity 早見表（HU〜10-handed バブルまで） | 第4章「ICM equity」、付録B |
| [03_push_fold_nash.md](03_push_fold_nash.md) | Push/Fold Nash チャート（M値別、ICM 補正含む） | 第9〜10章、付録A |
| [04_bubble_factor.md](04_bubble_factor.md) | Bubble factor 数値例（ステージ別マトリクス） | 第5章「ICM 補正」、第13章「バブル」 |
| [05_icm_premium.md](05_icm_premium.md) | ICM 補正 ステージ別一覧 | 第5章、第7〜10章「スタック深度別」 |

## 計算ツール

- `scripts/icm_calc.py`: Python 製 ICM 計算器
  - Malmuth-Harville アルゴリズム（n ≤ 5 は順列法、n ≥ 6 は O(n·2^n) DP）
  - bubble factor / ICM 補正 計算機能
  - プリセットシナリオ 7 種

```bash
# 基本使用
python scripts/icm_calc.py --stacks "4500,3000,1500,1000" --payouts "50,30,20"

# bubble factor
python scripts/icm_calc.py --preset bubble-9max-stt --bubble-factor 2

# JSON 出力（プログラム連携用）
python scripts/icm_calc.py --preset hu --json

# 全プリセット表示
python scripts/icm_calc.py --all-presets
```

## 検証ステータス

| データ | 検証元 | ステータス |
| :--- | :--- | :--- |
| ICM equity 値 | `scripts/icm_calc.py` 直接計算 | ✓ 自動再現可能 |
| Bubble factor 値 | `scripts/icm_calc.py` 直接計算 | ✓ 自動再現可能 |
| ICM 補正値 | `scripts/icm_calc.py` 直接計算 | ✓ 自動再現可能 |
| Push/Fold Nash レンジ | 文献参照（HRC/ICMIZER/Kill Everyone） | △ 文献依拠、要再検証 |

Push/Fold Nash チャートの数値は標準的な poker 文献からの代表値を採用。執筆段階で HRC か類似ツールで実測値を再計算する予定。

## 未着手項目

- 各ポジション × M値 × ICM プレミアム の包括的 push/call 範囲表
- バウンティトーナメント特有の補正
- サテライトの「定額勝利」構造での ICM 修正
