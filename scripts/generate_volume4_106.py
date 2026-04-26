#!/usr/bin/env python3
"""巻4 検証タスク #106 (リバー MDF の実測) 用シナリオ JSON 生成スクリプト.

書籍論点: 「SB 防御 10.8% vs 理論 53.5%」のように、相手タイプ別に実測される
Minimum Defense Frequency (MDF) が理論値とどの程度ずれるかを検証する。

設計方針:
  - 10 リバーボード × 2 villain_type (tight / balanced) = 20 シナリオ
  - bet_sizes は 3/4 pot の単一サイズ ([0.75]) に固定し、MDF を測りやすくする
  - 相手タイプ別プリセットが未定義のため、以下で代用:
      tight    : AA,KK,QQ,AKs,AKo,JJ,TT のみ (上位 value 限定, MDF は低くなる想定)
      balanced : {"preset": "BbDefendVsBtn"} (既存プリセットを流用)
  - プリセット追加後は {"preset": "TightCall"} 等に差し替え可能な設計にする

出力先:
  /home/cuzic/poker-books/knowledges/volume4/scenarios/106/<scenario_id>.json
  /home/cuzic/poker-books/knowledges/volume4/scenarios/106/index.json

スキーマ: /home/cuzic/poker-gto/docs/schemas/scenario.schema.json (draft-07)

MDF 理論値:
  bet = 0.75 * pot の場合、MDF = pot / (pot + bet) = 1 / 1.75 ≈ 0.5714 (57.1%)。
  defend ratio = 1 - alpha = 1 - bet / (pot + bet) = 1 - 0.75 / 1.75 ≈ 0.5714。
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# 出力先とスキーマパス
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path(
    "/home/cuzic/poker-books/knowledges/volume4/scenarios/106"
)

SCHEMA_PATH = Path(
    "/home/cuzic/poker-gto/docs/schemas/scenario.schema.json"
)


# ---------------------------------------------------------------------------
# 共通パラメータ
# ---------------------------------------------------------------------------

# pot / effective_stack は #19 (先行タスク) と揃えることで比較しやすくする
POT_BB: float = 27
EFFECTIVE_STACK_BB: float = 80

# ベットサイズは 3/4 pot の単一サイズに絞る
BET_SIZES: List[float] = [0.75]

# hero は IP (BTN) 側で river にベットを打つ構成。hero_range は BtnOpen100bb。
HERO_POSITION: str = "BTN"
HERO_RANGE: Dict[str, Any] = {"preset": "BtnOpen100bb"}

# ソルバー設定 (タスク仕様より)
SOLVER_CONFIG: Dict[str, Any] = {
    "algorithm": "ES_MCCFR",
    "iterations": 8000,
    "timeout_sec": 60,
    "rng_seed": 42,
    "exploitability_target_bb": 0.05,
}

# MDF 理論値 (bet_size -> defend ratio)
# MDF = pot / (pot + bet) = 1 / (1 + bet_ratio)
MDF_THEORY: Dict[str, float] = {
    "0.75": round(1.0 / (1.0 + 0.75), 4),
}


# ---------------------------------------------------------------------------
# villain_type 定義
#
# プリセット追加後は villain_range を {"preset": "TightCall"} のような形に
# 差し替えられるように、"range_spec" フィールドをそのまま埋め込む設計。
# ---------------------------------------------------------------------------


def _tight_range() -> Dict[str, Any]:
    """タイト villain: 上位 value のみ。MDF は 10-20% 想定 (理論 57.1% を大幅に下回る)."""
    return {
        "expr": "AA,KK,QQ,AKs,AKo,JJ,TT",
    }


def _balanced_range() -> Dict[str, Any]:
    """バランス villain: 既存 BbDefendVsBtn プリセットで代用。MDF は理論 57.1% 近傍想定."""
    return {
        "preset": "BbDefendVsBtn",
    }


VILLAIN_TYPES: List[Dict[str, Any]] = [
    {
        "key": "tight",
        "title": "タイト (上位 value のみ)",
        "range_spec": _tight_range(),
        "expected_mdf_range": [0.10, 0.20],
        "note": (
            "villain_range = {expr: 'AA,KK,QQ,AKs,AKo,JJ,TT'}. "
            "プリセット追加後は {preset: 'TightCall'} 相当に差し替え可能。"
        ),
    },
    {
        "key": "balanced",
        "title": "バランス (BbDefendVsBtn プリセット)",
        "range_spec": _balanced_range(),
        "expected_mdf_range": [0.50, 0.65],
        "note": (
            "villain_range = {preset: 'BbDefendVsBtn'}. "
            "相手タイプ別バランスプリセット追加後は {preset: 'BalancedCall'} に差し替え可能。"
        ),
    },
]


# ---------------------------------------------------------------------------
# 10 リバーボード定義 (タスク #19 再利用、命名は 106 系で衝突回避)
# ---------------------------------------------------------------------------


BOARDS: List[Dict[str, Any]] = [
    {
        "label": "Adry",
        "board": ["As", "Kh", "7d", "4c", "2s"],
        "note": "A-high dry (A K 7 4 2 rainbow)",
    },
    {
        "label": "Kdry",
        "board": ["Kc", "8h", "3d", "2s", "Qc"],
        "note": "K-high dry + Q river (K 8 3 2 + Q)",
    },
    {
        "label": "TwoPair",
        "board": ["Kc", "7d", "2s", "7h", "Ac"],
        "note": "2 ペア完成 (K 7 2 7 A)",
    },
    {
        "label": "BoardTrips",
        "board": ["9c", "9h", "4s", "9d", "2h"],
        "note": "ボード・トリップス (9 9 4 9 2)",
    },
    {
        "label": "StraightDone",
        "board": ["9c", "8h", "7d", "6s", "Jc"],
        "note": "ストレート完成 (9 8 7 6 + J)",
    },
    {
        "label": "FlushDone",
        "board": ["As", "Ks", "7s", "2s", "4c"],
        "note": "フラッシュ完成 (A K 7 2 spades + 4c)",
    },
    {
        "label": "Monotone",
        "board": ["Ah", "Kh", "Qh", "3s", "2d"],
        "note": "モノトーン (A K Q hearts + 3 2 offsuit)",
    },
    {
        "label": "FourStraight",
        "board": ["6s", "7h", "8d", "9c", "3s"],
        "note": "4 枚ストレート (6 7 8 9 + 3)",
    },
    {
        "label": "FullHouseable",
        "board": ["Ac", "Ah", "5d", "5h", "Kc"],
        "note": "フルハウス可能 (A A 5 5 K)",
    },
    {
        "label": "LowStraight",
        "board": ["7s", "5d", "3c", "2h", "4s"],
        "note": "Low ストレート (7 5 3 2 4)",
    },
]


# ---------------------------------------------------------------------------
# ボード検証ヘルパ
# ---------------------------------------------------------------------------


def _validate_board(cards: List[str]) -> None:
    """リバー board = 5 枚で重複なしを検証."""
    if len(cards) != 5:
        raise ValueError(
            f"river board must be 5 cards, got {len(cards)}: {cards}"
        )
    if len(set(cards)) != len(cards):
        raise ValueError(f"duplicate cards in board: {cards}")


# ---------------------------------------------------------------------------
# シナリオ構築
# ---------------------------------------------------------------------------


def _build_scenario(
    board_entry: Dict[str, Any],
    villain_entry: Dict[str, Any],
) -> Dict[str, Any]:
    """1 シナリオ分の dict を構築する."""
    board_cards: List[str] = list(board_entry["board"])
    _validate_board(board_cards)

    board_label: str = str(board_entry["label"])
    villain_key: str = str(villain_entry["key"])

    scenario_id = f"mdf_106_{board_label}_{villain_key}"
    description = (
        f"[リバー MDF / villain_type: {villain_key}] "
        f"{board_entry['note']} "
        f"(pot={POT_BB}bb, bet={BET_SIZES[0]}x pot, "
        f"MDF_theory={MDF_THEORY['0.75']})"
    )

    villain_range: Dict[str, Any] = dict(villain_entry["range_spec"])

    return {
        "scenario_id": scenario_id,
        "description": description,
        "street_to_solve": "river",
        "board": board_cards,
        "pot_bb": POT_BB,
        "effective_stack_bb": EFFECTIVE_STACK_BB,
        "hero_position": HERO_POSITION,
        "hero_range": dict(HERO_RANGE),
        "villain_range": villain_range,
        "bet_sizes_to_evaluate": list(BET_SIZES),
        "solver_config": dict(SOLVER_CONFIG),
    }


# ---------------------------------------------------------------------------
# ファイル I/O
# ---------------------------------------------------------------------------


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _load_schema() -> Optional[Dict[str, Any]]:
    if not SCHEMA_PATH.exists():
        return None
    try:
        loaded = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if isinstance(loaded, dict):
        return loaded
    return None


def _validate(
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
    # 件数の事前検証 (10 ボード × 2 タイプ = 20)
    if len(BOARDS) != 10:
        raise RuntimeError(
            f"expected 10 boards, got {len(BOARDS)}"
        )
    if len(VILLAIN_TYPES) != 2:
        raise RuntimeError(
            f"expected 2 villain types, got {len(VILLAIN_TYPES)}"
        )

    schema = _load_schema()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 冪等性: 既存 mdf_106_*.json と index.json をクリア
    for p in OUTPUT_DIR.glob("mdf_106_*.json"):
        p.unlink()
    index_path = OUTPUT_DIR / "index.json"
    if index_path.exists():
        index_path.unlink()

    index_scenarios: List[Dict[str, Any]] = []
    villain_counter: Counter = Counter()

    for board_entry in BOARDS:
        for villain_entry in VILLAIN_TYPES:
            scenario = _build_scenario(board_entry, villain_entry)
            _validate(scenario, schema)

            out_path = OUTPUT_DIR / f"{scenario['scenario_id']}.json"
            _write_json(out_path, scenario)

            index_scenarios.append(
                {
                    "scenario_id": scenario["scenario_id"],
                    "board_label": board_entry["label"],
                    "board": list(scenario["board"]),
                    "villain_type": villain_entry["key"],
                    "villain_title": villain_entry["title"],
                    "villain_range": dict(villain_entry["range_spec"]),
                    "expected_mdf_range": list(
                        villain_entry["expected_mdf_range"]
                    ),
                    "pot_bb": POT_BB,
                    "effective_stack_bb": EFFECTIVE_STACK_BB,
                    "bet_sizes_to_evaluate": list(BET_SIZES),
                    "note": board_entry["note"],
                    "file": out_path.name,
                }
            )
            villain_counter[villain_entry["key"]] += 1

    # index.json
    index_payload: Dict[str, Any] = {
        "task": "106",
        "title": "リバー MDF の実測",
        "total": len(index_scenarios),
        "boards": len(BOARDS),
        "villain_types": [v["key"] for v in VILLAIN_TYPES],
        "villain_type_notes": {
            v["key"]: v["note"] for v in VILLAIN_TYPES
        },
        "mdf_theory": MDF_THEORY,
        "mdf_theory_description": (
            "MDF = pot / (pot + bet) = 1 / (1 + bet_ratio). "
            "bet = 0.75 * pot の場合、MDF ≈ 0.5714 (57.1%)。"
        ),
        "pot_bb": POT_BB,
        "effective_stack_bb": EFFECTIVE_STACK_BB,
        "hero_position": HERO_POSITION,
        "hero_range": dict(HERO_RANGE),
        "bet_sizes_to_evaluate": list(BET_SIZES),
        "scenarios": index_scenarios,
    }
    _write_json(OUTPUT_DIR / "index.json", index_payload)

    print(f"generated {len(index_scenarios)} scenarios in {OUTPUT_DIR}")
    print("villain_types:", dict(villain_counter))


if __name__ == "__main__":
    main()
