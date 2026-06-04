# research/ — GTO Wizard 研究データ管理

GTO Wizard で取得した研究データを管理する。
新しい Claude セッション (または作業者) は **ここを最初に読んで** 既存データを把握する。

## 🚨 重要: 新規調査の前に必ず確認

GTO Wizard API には:
- **日次クォータ制限** がある
- **トークン有効期間が 15 分** しかない (頻繁な再取得が必要)

**重複調査を絶対に避ける**ため、以下の順で確認:

1. **`RESEARCH_GAPS.md`** — 未調査領域 (本当に調査すべきもの) の一覧
2. **`RESEARCH_INVENTORY.md`** — 既存データのディレクトリ単位サマリ
3. **`RESEARCH_INVENTORY_DETAIL.md`** — 全 896 ファイルの詳細一覧 (必要時のみ)

## ディレクトリ構成

```
research/
├── README.md                       ← 本ファイル
├── RESEARCH_GAPS.md                ← 未調査領域 (調査優先順)
├── RESEARCH_INVENTORY.md           ← 既存データ サマリ
├── RESEARCH_INVENTORY_DETAIL.md    ← 全ファイル詳細
├── inventory_scan.py               ← inventory 自動生成スクリプト (詳細版)
├── inventory_summarize.py          ← inventory 自動生成スクリプト (集約版)
└── v3-additional/                  ← 新規調査作業ディレクトリ
    ├── .env                        ← GTO Wizard token (gitignored)
    ├── .gitignore
    ├── README.md
    ├── hand_order.py               ← strategy[169] のハンド順序確定マッピング
    ├── probe.py                    ← API 動作確認
    ├── order_probe.py / order_probe2.py  ← ハンド順序確定実験
    ├── task_a_bb_boundary.py       ← BB defense 5 シナリオ取得 (完了)
    ├── task_c_squeeze.py           ← Squeeze N=1/2 取得 (完了)
    ├── task_d_ip_defense.py        ← IP defense 取得 (準備済、token 待ち)
    ├── analyze_a_c.py              ← diff report 生成
    └── findings/                   ← 取得済 JSON データ
        ├── task_a_BB_vs_*.json     ← BB defense 5 シナリオ × 169 hand
        ├── task_c_*.json           ← Squeeze 13 シナリオ
        └── diff_report.md          ← 集計レポート
```

## 既存研究データ全体像 (2026-06-04 時点)

**合計 896 JSON ファイル** が分散保管:

| 場所 | ファイル数 | 主な内容 |
|------|----------|---------|
| `vol2-cash-postflop/findings/` | 6 | Cash 100bb postflop 集約 / 5-cat |
| `vol3-mtt-postflop/findings/` | 138 | MTT 各 SBR postflop |
| `vol3-mtt-postflop/findings/3bp{25,50,100}_raw/` | 72 (24×3) | 3BP postflop hand-level |
| `vol3-mtt-postflop/findings/def_cash100_bb_*_raw/` | ~78 | Cash 100bb BB defense flop/turn/river |
| `vol3-mtt-postflop/findings/def_mtt{25,50,100}_bb_*_raw/` | ~120 | MTT BB defense flop/turn/river |
| `research/v3-additional/findings/` | 20 | Preflop hand-level (新規追加) |

## カバー範囲の早見 (詳細は GAPS / INVENTORY 参照)

### ✅ 取得済 (再取得不要)

- **Cash 100bb 6m**: postflop ほぼ全領域 (flop/turn は hand-level)、preflop は集約のみ
- **MTT 25/50/100bb**: BB defense flop/turn/river の hand-level
- **3BP (Cash/MTT)**: 3 depth × 8 board の postflop hand-level
- **Preflop BB defense**: 5 オープナー × 169 hand (2026-06-04 新規)
- **Preflop squeeze**: N=1/2 × 13 シナリオ × 169 hand (同上)

### ❌ 未調査 (本当に必要、優先順は `RESEARCH_GAPS.md`)

#### 🔴 高優先
- Vol1 ch04 §4.2 IP defense hand-level (~6 spots)
- Vol1 ch04 §4.3 SB OOP defense hand-level (~4 spots)
- Vol1 ch04 §4.4 vs 3-bet hand-level (~12 spots)
- Vol1 ch04 §4.5/§4.6 4-bet/5-bet defense (~6 spots、書籍が「理論値」と明言)
- Vol1 ch05 squeeze N=3 (~5 spots)

#### 🟡 中優先
- Vol1 ch03 RFI hand-level (~5 spots)
- Vol2 ch07/ch10 River pairwise (~14 spots)
- Vol2 ch05 board family 境界 (~10 spots)

#### 🟢 低優先 (書籍範囲拡張)
- Vol3 4BP postflop (新章追加、~30 spots)
- Vol3 ICM Bubble/FT 詳細 (~20 spots)
- Vol1 MTT preflop hand-level (~15 spots)

**全 phase 合計**: 約 127 spots = 約 13 分の API call

## API 仕様メモ

- **エンドポイント**: `https://api.gtowizard.com/v4/solutions/spot-solution/`
- **ゲームタイプ**:
  - Cash 100bb 6m: `Cash6mTest_6mNL100R2`
  - Cash 25bb 6m: `Cash6mGeneral_6mNL25R25`
  - MTT 9m: `MTTGeneral`
- **トークン**: JWT、有効期間 **15 分** (`exp` フィールド確認)
- **HTTP**:
  - 200 = OK
  - 204 = この preflop_actions / depth では GTO Wizard が未計算
  - 401 = トークン期限切れ
  - 429 = レート制限 (`Retry-After` 待機)

### strategy[169] のハンド順序 (重要)

GTO Wizard preflop spot の `action_solutions[*].strategy` は **長さ 169 の float 配列** で、ハンド順序は **ASCII sort 順** (`hand_order.py` 参照):

```
22 (idx 0), 32o (1), 32s (2), 33 (3), ..., A2o (64), A2s (65), ..., AA (80), AJo (81), AKs (84), ..., KK (126), QQ (149), TT (168, 最後)
```

詳細は `v3-additional/hand_order.py` の `HANDS` / `HAND_TO_INDEX`。

## 既存データの活用方法

新規 GTO 取得を avoid するため、以下を最初に試す:

1. **特定の集約値が欲しい** (cbet% / fourbet_pct 等):
   - `vol2-cash-postflop/findings/cash_preflop_gto_summary.json`
   - `vol3-mtt-postflop/findings/*.md` (Vol3 の design notes)

2. **特定のボードでの hand category 別頻度**:
   - `vol2/findings/cash_5cat_gto.json` (Cash 100bb 7 ボード × 5-cat)
   - `vol2/findings/cash_pairwise_gto.json` (flop/turn 56+42 ボード × 5-cat)

3. **Cash 100bb の特定ボード postflop の hand-level**:
   - `vol3/findings/def_cash100_bb_*_raw/<board>.json`

4. **MTT 各 depth の postflop hand-level**:
   - `vol3/findings/def_mtt{25,50,100}_bb_*_raw/<board>.json`

5. **3BP の hand-level**:
   - `vol3/findings/3bp{25,50,100}_raw/<scenario>_<board>.json`

## inventory を更新する

新規ファイル追加時:
```bash
cd ~/poker-books
python3 research/inventory_summarize.py > research/RESEARCH_INVENTORY.md
python3 research/inventory_scan.py > research/RESEARCH_INVENTORY_DETAIL.md
```
