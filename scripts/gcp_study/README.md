# 168-Board GTO Regression Study (GCP)

TexasSolver を GCP Spot VM 上で並列実行し、168 ボードの CBet 率を体系的に収集、
OLS 回帰で「ボード特徴 → BTN CBet 率」の新式を導出する。

## 前提

```
gcloud auth login
gcloud config set project YOUR_PROJECT
```

Python 3.9+, numpy が手元マシンにインストール済みであること。

## 使い方

### ① ボードリスト生成・確認

```bash
cd scripts/gcp_study
python3 boards.py          # boards.json を生成、枚数を表示
```

### ② GCP VM を起動して解析を実行

```bash
export GCS_BUCKET=poker-gto-study   # GCS バケット名（なければ自動作成）
export GCP_PROJECT=my-project       # GCP プロジェクト ID
export N_VMS=5                      # VM 台数（多いほど速い）

bash launch.sh
```

launch.sh が行うこと:
1. `boards.json` を生成
2. TexasSolver を tar.gz にまとめて GCS にアップロード
3. N 台の Spot VM を起動（各 VM は startup.sh で自動ビルド → worker.py 実行 → 自動終了）

コスト目安: c2-standard-60 Spot × 5台 × 15分 ≈ $0.20 未満

### ③ 結果を収集して回帰分析

```bash
export GCS_BUCKET=poker-gto-study
bash collect.sh
```

collect.sh が行うこと:
1. GCS の結果ファイルを `knowledges/flop/results/168board_study/` にダウンロード
2. `regression.py` を実行して回帰レポートを表示・保存

### ④ 手元で回帰のみ再実行

```bash
python3 regression.py --results ../../knowledges/flop/results/168board_study
```

## ファイル構成

| ファイル | 説明 |
|---------|------|
| `boards.py`     | 168 ボードリスト生成 → `boards.json` |
| `worker.py`     | VM 上で動作するメインロジック |
| `startup.sh`    | VM 起動スクリプト（metadata に渡す） |
| `launch.sh`     | GCS アップロード + VM 起動 |
| `collect.sh`    | 結果ダウンロード + 回帰トリガー |
| `regression.py` | OLS 回帰 + Pearson 相関分析 |

## 環境変数

| 変数 | デフォルト | 説明 |
|-----|-----------|------|
| `GCS_BUCKET` | `poker-gto-study` | GCS バケット名 |
| `GCP_PROJECT` | `gcloud config` から取得 | GCP プロジェクト ID |
| `N_VMS`       | `5`          | 起動する VM 台数 |
| `GCP_ZONE`    | `us-central1-c` | デプロイゾーン |
| `GCP_MACHINE` | `c2-standard-60` | マシンタイプ |
| `SOLVER_THREADS`  | `8`  | TexasSolver の thread_num |
| `SOLVER_PARALLEL` | `6`  | VM 内の並列ボード数 |

## TexasSolver JSON 構造（参考）

```
root (OOP=BB first action)
└── childrens.CHECK  (BB checks → BTN acts)
    ├── strategy.actions  ["BET 2.31", "BET 3.50", "BET 5.25", "CHECK", ...]
    ├── strategy.strategy {"AcKd": [p1, p2, ...], ...}
    └── childrens["BET X"]  (BTN bets → BB responds)
        ├── strategy.actions  ["FOLD", "CALL", "RAISE X", ...]
        └── strategy.strategy {"AcKd": [p_fold, p_call, ...], ...}
```

- pot=7, stack=97
- BTN CBet sizes: 33% (≈2.31), 50% (≈3.50), 75% (≈5.25)
- BB Bet sizes: 60%, 100% (check-raise/donk)
