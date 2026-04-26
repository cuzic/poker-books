#!/usr/bin/env python3
"""巻4 検証 #49 仮説検証: overbet 除去実験のためのシナリオ生成スクリプト.

`generate_flop_accuracy_30.py` と同じ 30 ボードを生成するが、
`bet_sizes_to_evaluate` から 1.0 (pot) と 1.5 (オーバーベット) を
除外し、`[0.33, 0.5, 0.75]` の 3 サイズのみを許可する。

仮説:
  - 987mono の baseline では bet_1.5 が 22.6% も選ばれている
  - overbet を除去すると 33% 小サイズに集中し、総 CBet 頻度が
    84% → 60% 前後に落ちれば「overbet regret の計算側に問題」
  - 落ちなければ別原因 (戦略抽出 / 情報集合設計)

出力先: /home/cuzic/poker-books/knowledges/volume4/scenarios/flop_accuracy_30_no_overbet/
  - <scenario_id>.json  (各シナリオ 30 個)
  - index.json          (scenario_id, ボードラベル, 基準 Bet 頻度 の対応表)

scenario スキーマ: /home/cuzic/poker-gto/docs/schemas/scenario.schema.json
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
RANK_VALUES = {r: i + 2 for i, r in enumerate(RANKS)}  # "2"->2, ..., "A"->14
SUITS = ["c", "d", "h", "s"]

# 出力先ディレクトリ (overbet 除去実験専用)
OUTPUT_DIR = Path(
    "/home/cuzic/poker-books/knowledges/volume4/scenarios/flop_accuracy_30_no_overbet"
)

# スキーマ位置 (検証用、任意)
SCHEMA_PATH = Path(
    "/home/cuzic/poker-gto/docs/schemas/scenario.schema.json"
)

# overbet 除去実験では 1.0 / 1.5 を削った 3 サイズのみを許可する
BET_SIZES_NO_OVERBET: List[float] = [0.33, 0.5, 0.75]

# ---------------------------------------------------------------------------
# 30 ボードの基準データ (generate_flop_accuracy_30.py と同一)
# 出典: poker-books/scripts/verify_flop_gto.py の GTO_BOARD_DATA
# (ボードラベル, GTO Wizard 公開 CBet 頻度 %, サイズ種別, 備考)
# ---------------------------------------------------------------------------

GTO_BOARD_DATA: List[Tuple[str, int, str, str]] = [
    # --- 超ドライ (BoardScore 0〜3) ---
    ("K72r",   91, "small-33",  "GTO Wizard Blog: IP CB in cash"),
    ("A72r",   90, "small-33",  "published by GTO Wizard"),
    ("K44",    43, "small-33",  "GTO Wizard K44 analysis"),
    ("Q53r",   85, "small-33",  "similar to K72r class"),
    ("A82r",   88, "small-33",  ""),
    ("K83r",   87, "small-33",  ""),
    ("A52r",   89, "small-33",  ""),
    ("K95r",   80, "small-33",  ""),
    # --- セミウェット (BoardScore 4〜6) ---
    ("KT5r",   70, "mixed",     "Broadway + 1gap"),
    ("J75r",   40, "mixed",     "J75r analysis"),
    ("Q83ss",  55, "small-33",  "Q高 + two-tone"),
    ("AT7ss",  60, "small-33",  "A高 + two-tone"),
    ("J84ss",  50, "mixed-66",  "flop chapter example"),
    ("QJ9r",   50, "small-33",  "connected high + rainbow"),
    ("T87r",   45, "medium",    "connected mid + rainbow"),
    ("876r",   42, "medium",    "connected low + rainbow"),
    # --- ウェット (BoardScore 7〜11) ---
    ("987ss",  30, "small-33",  "wet connected two-tone"),
    ("JT9ss",  25, "small-33",  "wet broadway two-tone"),
    ("987mono",20, "small-33",  "monotone connected"),
    ("KQTss",  35, "polarized", "flushy broadway"),
    ("AKQmono",15, "small-33",  "monotone broadway"),
    ("JT8ss",  30, "small-33",  "wet broadway"),
    ("T98r",   40, "medium-66", "connected high rainbow"),
    ("T98ss",  35, "medium-71", "本書 10-4節、GTO 71% size"),
    # --- 特殊ボード ---
    ("772",    70, "small-33",  "ペアボード low"),
    ("AAK",    85, "small-33",  "ペアボード high"),
    ("KK9",    80, "small-33",  "ペアボード high"),
    ("965r",   60, "mixed",     "mid connected"),
    ("632r",   62, "small-33",  "付録K で 62.5% 明示"),
    ("A99",    78, "small-33",  "ペアボード A"),
]

assert len(GTO_BOARD_DATA) == 30, "30 flops expected"


# ---------------------------------------------------------------------------
# ボードラベル → 具体カード 3 枚 (generate_flop_accuracy_30.py と同一)
# ---------------------------------------------------------------------------


def cards_for_label(label: str) -> List[str]:
    """ボードラベル → 3 枚のカード配列.

    割付ルール:
      - mono: すべて "s"
      - ss:   上位 2 枚が "s"、最下位が "h"
      - r:    c/d/s の 3 スート
      - 末尾なし: rainbow と同じ c/d/s (ペアボードを含む)
    """
    ranks: List[str] = []
    i = 0
    while i < len(label) and label[i] in RANK_VALUES:
        ranks.append(label[i])
        i += 1
    tail = label[i:].lower()

    if tail == "mono":
        suits = ["s", "s", "s"]
    elif tail == "ss":
        suits = ["s", "s", "h"]
    elif tail == "r":
        suits = ["c", "d", "s"]
    elif tail == "":
        suits = ["c", "d", "s"]
    else:
        raise ValueError(f"unknown board label tail: {label!r}")

    cards = [r + s for r, s in zip(ranks, suits)]
    if len(set(cards)) != len(cards):
        raise ValueError(f"duplicate card in label {label!r}: {cards}")
    return cards


# ---------------------------------------------------------------------------
# シナリオ JSON ビルド
# ---------------------------------------------------------------------------


def build_scenario(board_label: str, cards: List[str], gto_freq: int) -> Dict[str, Any]:
    """overbet 除去用シナリオ dict を構築する.

    baseline (flop_accuracy_30) との差分:
      - bet_sizes_to_evaluate: [0.33, 0.5, 0.75, 1.5] → [0.33, 0.5, 0.75]

    他設定 (iterations=5000, timeout=60, seed=42, pot=7, stack=97) は同じ。
    """
    scenario_id = f"flop_acc30_{board_label}"
    description = (
        f"{board_label} overbet 除去実験 (GTO Wizard {gto_freq}%)"
    )

    return {
        "scenario_id": scenario_id,
        "description": description,
        "street_to_solve": "flop",
        "board": cards,
        "pot_bb": 7,
        "effective_stack_bb": 97,
        "hero_position": "BTN",
        "hero_range": {"preset": "BtnOpen100bb"},
        "villain_range": {"preset": "BbDefendVsBtn"},
        "bet_sizes_to_evaluate": list(BET_SIZES_NO_OVERBET),
        "solver_config": {
            "algorithm": "ES_MCCFR",
            "iterations": 5000,
            "timeout_sec": 60,
            "rng_seed": 42,
            "exploitability_target_bb": 0.05,
        },
    }


# ---------------------------------------------------------------------------
# ファイル出力 / スキーマ検証
# ---------------------------------------------------------------------------


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_schema() -> Optional[Dict[str, Any]]:
    if not SCHEMA_PATH.exists():
        return None
    try:
        raw = SCHEMA_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def validate_scenario(
    scenario: Dict[str, Any], schema: Optional[Dict[str, Any]]
) -> None:
    if schema is None:
        return
    try:
        import jsonschema  # 遅延 import
    except ImportError:
        return
    jsonschema.validate(scenario, schema)


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------


def main() -> None:
    schema = load_schema()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 冪等性のため、既存の flop_acc30_*.json / index.json をクリア
    for p in OUTPUT_DIR.glob("flop_acc30_*.json"):
        p.unlink()
    index_path = OUTPUT_DIR / "index.json"
    if index_path.exists():
        index_path.unlink()

    index_scenarios: List[Dict[str, Any]] = []

    for board_label, gto_freq, size_note, source in GTO_BOARD_DATA:
        cards = cards_for_label(board_label)
        scenario = build_scenario(board_label, cards, gto_freq)
        validate_scenario(scenario, schema)

        out_path = OUTPUT_DIR / f"{scenario['scenario_id']}.json"
        write_json(out_path, scenario)

        index_scenarios.append(
            {
                "scenario_id": scenario["scenario_id"],
                "board_label": board_label,
                "board_cards": cards,
                "gto_wizard_bet_freq": gto_freq,
                "gto_wizard_size_note": size_note,
                "source_note": source,
                "file": out_path.name,
            }
        )

    index_payload = {
        "task": "flop_accuracy_30_no_overbet",
        "title": "30 ボード精度検証 (overbet 除去: bet_sizes=[0.33, 0.5, 0.75])",
        "total": len(index_scenarios),
        "hero_range": "BtnOpen100bb",
        "villain_range": "BbDefendVsBtn",
        "pot_bb": 7,
        "effective_stack_bb": 97,
        "bet_sizes_to_evaluate": list(BET_SIZES_NO_OVERBET),
        "scenarios": index_scenarios,
    }
    write_json(OUTPUT_DIR / "index.json", index_payload)

    print(f"generated {len(index_scenarios)} scenarios in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
