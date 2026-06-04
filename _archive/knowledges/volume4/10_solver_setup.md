# 巻4 検証環境の選定とセットアップ

巻4 論点検証のためのソルバー環境選定結果と実装方針。

## 選定結果: ローカル CFR ソルバーを自作 (既存 Rust 実装を活用)

### 選定の経緯

4 つの選択肢を比較:

| 候補 | 長所 | 短所 | 判定 |
|---|---|---|---|
| GTO Wizard 有料プラン | 信頼性、即利用可能 | $99/月、API なし (手動入力) | × |
| PioSolver | 業界標準、ローカル計算 | $250、GUI のみ、自動化困難 | × |
| Simple Postflop | 安価 ($200) | 機能限定 | × |
| **ローカル CFR 実装 (自作)** | **完全自動化、データ制約なし** | 精度検証が必要 | ◎ |

### 既存資産の活用

著者ローカルに Rust 製 CFR/DCFR/MCCFR ソルバー実装が存在する。これを活用することで:

- 500+ シナリオを自動で回せる
- JSON 入出力で Python と連携可能
- 有料ソフト不要
- 精度は GTO Wizard のベンチマークで後日検証

### 実装構成

```
検証パイプライン:

  [シナリオ JSON] (poker-books/knowledges/volume4/scenarios/*.json)
         │
         ↓
  [Rust CFR ソルバー] (ローカル実装、poker-books からは非依存)
         │  出力: EV、頻度、サイズ選択
         ↓
  [結果 JSON] (poker-books/knowledges/volume4/results/*.json)
         │
         ↓
  [Python 分析] (poker-books/scripts/analyze_volume4.py)
         │  集計、R² 計算、可視化
         ↓
  [書籍用素材] (knowledges/volume4/11-17_*.md)
```

## 検証シナリオの JSON 形式

```json
{
  "scenario_id": "turn_cbet_001",
  "description": "K72r ターン A",
  "flop": ["Kc", "7d", "2s"],
  "turn": "As",
  "prev_actions": [
    {"street": "preflop", "player": "BTN", "action": "raise", "size": 2.5},
    {"street": "preflop", "player": "BB", "action": "call"},
    {"street": "flop", "player": "BTN", "action": "bet", "size": 0.33},
    {"street": "flop", "player": "BB", "action": "call"}
  ],
  "hero_position": "BTN",
  "hero_cards_range": "BTN_open_range.json",
  "villain_cards_range": "BB_defend_range.json",
  "stack_bb": 100,
  "pot_bb": 7.5,
  "bet_sizes_to_solve": [0.33, 0.5, 0.75, 1.5]
}
```

## 結果 JSON の形式

```json
{
  "scenario_id": "turn_cbet_001",
  "solver_config": {
    "algorithm": "DCFR",
    "iterations": 10000,
    "exploitability_bb": 0.05
  },
  "results": {
    "cbet_frequency_total": 0.68,
    "cbet_by_size": {
      "0.33": 0.45,
      "0.5": 0.12,
      "0.75": 0.08,
      "1.5": 0.03
    },
    "check_frequency": 0.32,
    "range_ev_bb": 4.2,
    "by_hand_category": {
      "nuts": {"cbet": 0.95, "size": 1.5},
      "top_pair": {"cbet": 0.75, "size": 0.5},
      "middle": {"cbet": 0.5, "size": 0.33},
      "bluffs": {"cbet": 0.3, "size": 0.33}
    }
  }
}
```

## Python 分析スクリプト (概要)

```python
# scripts/analyze_volume4.py
import json
from pathlib import Path
from statistics import correlation

RESULTS_DIR = Path("knowledges/volume4/results")

def load_turn_cbet_results():
    """ターン CBet 頻度 270 ケースを読み込み"""
    ...

def build_bdm_turn_model():
    """ターン CBet 頻度を 2 軸 (ターンカード × フロップ型) でモデル化"""
    ...

def compute_r_squared(actual, predicted):
    """R² 計算"""
    ...

def generate_volume4_material():
    """書籍用 Markdown 素材を自動生成"""
    ...
```

## 検証タスク #102-#108 での具体運用

### #102 ターン CBet 頻度 270 ケース

- 30 フロップ × 9 代表ターンカード = 270 シナリオ JSON 生成
- Rust ソルバーで 270 回実行 (推定 6-8 時間、並列で 2-3 時間)
- 結果 JSON から R² を計算し、BDM_turn モデルの成否判定

### #103 リバー V:B 比 30 シナリオ

- 30 リバーシナリオ JSON 生成 (各ボード × ベットサイズ)
- Alpha 25%/43%/55.5% の理論値と実測値を比較

### #104-#107 同様に自動化

全てソルバー → Python 分析 の流れで処理。

## 精度検証 (信頼性確保)

Rust ソルバーの精度を GTO Wizard の公開記事と照合:

- K72r の BTN CBet 頻度 ≈ 91% (GTO Wizard 公開値)
- 987ss の BTN CBet 頻度 ≈ 30% (GTO Wizard 公開値)
- その他 30 ボード分を巻2 の実測データと比較

**一致率 95% 以上なら信頼できるソルバーと判定**。そうでなければ CFR iteration 数を増やすか、アルゴリズムを DCFR → MCCFR に切り替え。

## セットアップ手順

```bash
# 1. Rust ソルバーのビルド (別プロジェクトで完結)
cd ~/poker-solver  # 既存の Rust CFR 実装
cargo build --release

# 2. 検証 example の追加
# crates/poker-solver/examples/volume4_verify.rs を作成

# 3. シナリオ JSON の準備
mkdir -p ~/poker-books/knowledges/volume4/scenarios/
mkdir -p ~/poker-books/knowledges/volume4/results/

# 4. 実行
cargo run --release --example volume4_verify \
  --input ~/poker-books/knowledges/volume4/scenarios/ \
  --output ~/poker-books/knowledges/volume4/results/

# 5. Python 分析
cd ~/poker-books
python3 scripts/analyze_volume4.py
```

## データ量とスケジュール見積もり

| タスク | シナリオ数 | 推定計算時間 (並列) |
|:---:|:---:|:---:|
| #102 ターン CBet | 270 | 2-3 時間 |
| #103 リバー V:B | 30 | 20 分 |
| #104 マルチストリート | 15 × 3 ストリート = 45 | 30 分 |
| #105 ブロッカー | 20 | 15 分 |
| #106 MDF 層化 | 20 | 15 分 |
| #107 カテゴリ妥当性 | 270 (再利用) | 0 分 |
| #108 フック 6 個 | 6 × 5 シナリオ = 30 | 20 分 |
| **合計** | 約 400 シナリオ | **4-5 時間** |

10 並列で実行すれば半日で完了。

## 次のステップ

1. Rust ソルバー側に `examples/volume4_verify.rs` を追加 (タスク #101 の実装部分)
2. シナリオ JSON テンプレートを 5 個程度作成
3. 1-2 シナリオで実行し精度検証 (GTO Wizard 公開値と照合)
4. 精度 OK なら #102 から並列実行

## 注意

- 検証ソルバーは書籍の**内部実装詳細**。巻4 本文では「GTO ソルバー実測」と表記し、ソルバー実装の具体名は言及しない (一般的な用語で語る)
- 結果データのライセンスは poker-books プロジェクトに帰属
- 再現性のため、使用したソルバーのアルゴリズム・iteration 数・exploitability は knowledges/volume4/results/*.json にメタデータとして記録
