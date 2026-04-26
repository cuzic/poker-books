#!/usr/bin/env python3
"""巻4 検証タスク #103 (リバー V:B 比の実測) 用シナリオ JSON 生成スクリプト.

10 リバーボード × 3 ベットサイズ (0.25 / 0.43 / 0.555) = 30 シナリオを生成し、
/home/cuzic/poker-books/knowledges/volume4/scenarios/103/ 配下に
1 シナリオ = 1 JSON ファイルとして出力する。

書籍論点 #103: Alpha = s / (1 + s) で与えられるベットサイズ別のブラフ率理論値:
  - 0.25  -> alpha = 0.20
  - 0.43  -> alpha = 0.30
  - 0.555 -> alpha = 约 0.357

10 ボードはボード質別 (dry A-high / dry K-high / paired / trips / straight /
flush / monotone / 4-card straight / full house / low) に事前定義する。

pot/stack の前提 (全シナリオ共通):
  - プリフロップ: BTN open 2.5x → BB call, pot 5.5 BB
  - フロップ cbet 0.5 pot (2.75) → call, pot ≈ 11 BB
  - ターン 0.75 pot (8.25) → call, pot ≈ 27 BB
  - リバー開始: pot_bb = 27, effective_stack_bb = 80

スキーマ: /home/cuzic/poker-gto/docs/schemas/scenario.schema.json (draft-07)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 出力先とスキーマパス
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path(
    "/home/cuzic/poker-books/knowledges/volume4/scenarios/103"
)

SCHEMA_PATH = Path(
    "/home/cuzic/poker-gto/docs/schemas/scenario.schema.json"
)

# ---------------------------------------------------------------------------
# 10 リバーボード定義 (board_label, category, 5 枚のカード)
# schema の Card pattern ^[2-9TJQKA][cdhs]$ に準拠。重複禁止。
# ---------------------------------------------------------------------------

BOARDS: List[Tuple[str, str, List[str]]] = [
    # 1. dry / A-high (ハイカード A、接続弱、スート分散)
    ("Adry1", "dry_A_high", ["As", "Kh", "7d", "4c", "2s"]),
    # 2. dry / K-high (A なし、ペア/接続弱い)
    ("BdryK", "dry_K_high", ["Kc", "8h", "3d", "2s", "Qc"]),
    # 3. paired board (リバーで 2 ペア完成、K7 ペア)
    ("Cpaired", "paired", ["Kc", "7d", "2s", "7h", "Ac"]),
    # 4. trips (ボード 9 トリップス)
    ("Dtrips", "trips", ["9c", "9h", "4s", "9d", "2h"]),
    # 5. straight 完成 (9-8-7-6-J で J-high はないが 9876 の 1 ギャップ埋め)
    ("Estraight", "straight_complete", ["9c", "8h", "7d", "6s", "Jc"]),
    # 6. flush 完成 (4 枚スペード)
    ("Fflush", "flush_complete", ["As", "Ks", "7s", "2s", "4c"]),
    # 7. monotone + no hand change (ハート 3 枚、リバーで変化なし)
    ("Gmono", "monotone_no_change", ["Ah", "Kh", "Qh", "3s", "2d"]),
    # 8. 4-card straight (完成せず: 6-7-8-9 + 3)
    ("H4straight", "four_card_straight", ["6s", "7h", "8d", "9c", "3s"]),
    # 9. full house 可能性 (A-A-5-5-K ダブルペアボード)
    ("Ifullhouse", "full_house_possible", ["Ac", "Ah", "5d", "5h", "Kc"]),
    # 10. low board (7-5-3-2-4 で 7-high ストレート完成、block A)
    ("Jlow", "low_straight", ["7s", "5d", "3c", "2h", "4s"]),
]

assert len(BOARDS) == 10, "10 river boards expected"

# ---------------------------------------------------------------------------
# 3 ベットサイズ (ポット比率) と alpha 理論値
# alpha = s / (1 + s)
# ---------------------------------------------------------------------------

BET_SIZES: List[Tuple[float, str]] = [
    (0.25, "25"),
    (0.43, "43"),
    (0.555, "555"),
]

# ベットサイズ -> alpha 理論値 (ブラフ率)
ALPHA_THEORY: Dict[str, float] = {
    "0.25": round(0.25 / 1.25, 4),    # 0.20
    "0.43": round(0.43 / 1.43, 4),    # ≈ 0.3007 -> 0.30
    "0.555": round(0.555 / 1.555, 4),  # ≈ 0.3569 -> 0.357
}


# ---------------------------------------------------------------------------
# ボードカード重複チェック (静的検証)
# ---------------------------------------------------------------------------


def _validate_board_unique(cards: List[str]) -> None:
    """ボード 5 枚に重複がないことを確認."""
    if len(set(cards)) != len(cards):
        raise ValueError(f"duplicate cards in board: {cards}")
    if len(cards) != 5:
        raise ValueError(f"river board must be 5 cards, got {len(cards)}: {cards}")


# ---------------------------------------------------------------------------
# シナリオ dict ビルド
# ---------------------------------------------------------------------------


def _build_scenario(
    board_label: str,
    category: str,
    board_cards: List[str],
    bet_size: float,
    size_label: str,
) -> Dict[str, Any]:
    """30 のうち 1 シナリオ分の dict を構築する."""
    _validate_board_unique(board_cards)

    scenario_id = f"river_vb_103_{board_label}_alpha{size_label}"
    alpha = ALPHA_THEORY[str(bet_size)]
    description = (
        f"{board_label} ({category}) / bet {bet_size} pot / "
        f"alpha_theory={alpha}"
    )

    return {
        "scenario_id": scenario_id,
        "description": description,
        "street_to_solve": "river",
        "board": list(board_cards),
        # リバー開始時の pot: プリフロ 5.5 + フロップ call 5.5 + ターン call 16.5 ≈ 27
        "pot_bb": 27,
        # 100 BB エフェクティブから 5.5+2.75+8.25 ≈ 16.5 投入済み、残り ≈ 83。丸めて 80
        "effective_stack_bb": 80,
        # BTN オープン側が IP → hero_position="BTN"
        "hero_position": "BTN",
        "hero_range": {"preset": "BtnOpen100bb"},
        "villain_range": {"preset": "BbDefendVsBtn"},
        # 単一サイズで別シナリオ (schema 側の正式フィールド名は bet_sizes_to_evaluate)
        "bet_sizes_to_evaluate": [bet_size],
        "solver_config": {
            "algorithm": "ES_MCCFR",
            "iterations": 5000,
            "timeout_sec": 60,
            "rng_seed": 42,
            "exploitability_target_bb": 0.05,
        },
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


def _validate_against_schema(
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
    # スキーマ読み込み (任意)
    schema: Optional[Dict[str, Any]] = None
    if SCHEMA_PATH.exists():
        try:
            schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            schema = None

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 冪等性: 既存 river_vb_103_*.json と index.json をクリア
    for p in OUTPUT_DIR.glob("river_vb_103_*.json"):
        p.unlink()
    index_path = OUTPUT_DIR / "index.json"
    if index_path.exists():
        index_path.unlink()

    index_scenarios: List[Dict[str, Any]] = []

    for board_label, category, board_cards in BOARDS:
        for bet_size, size_label in BET_SIZES:
            scenario = _build_scenario(
                board_label=board_label,
                category=category,
                board_cards=board_cards,
                bet_size=bet_size,
                size_label=size_label,
            )
            _validate_against_schema(scenario, schema)

            out_path = OUTPUT_DIR / f"{scenario['scenario_id']}.json"
            _write_json(out_path, scenario)

            index_scenarios.append(
                {
                    "scenario_id": scenario["scenario_id"],
                    "board_label": board_label,
                    "category": category,
                    "board": list(board_cards),
                    "bet_size": bet_size,
                    "alpha_theory": ALPHA_THEORY[str(bet_size)],
                    "file": out_path.name,
                }
            )

    # index.json を書き出す
    index_payload: Dict[str, Any] = {
        "task": "103",
        "title": "リバー V:B 比の実測",
        "total": len(index_scenarios),
        "boards": len(BOARDS),
        "sizes": [bs for bs, _ in BET_SIZES],
        "alpha_theory": {
            "0.25": ALPHA_THEORY["0.25"],
            "0.43": ALPHA_THEORY["0.43"],
            "0.555": ALPHA_THEORY["0.555"],
        },
        "pot_bb": 27,
        "effective_stack_bb": 80,
        "scenarios": index_scenarios,
    }
    _write_json(OUTPUT_DIR / "index.json", index_payload)

    # 終了サマリ
    print(f"generated {len(index_scenarios)} scenarios in {OUTPUT_DIR}")
    print(f"boards: {len(BOARDS)}, sizes: {[bs for bs, _ in BET_SIZES]}")
    print(f"alpha_theory: {ALPHA_THEORY}")


if __name__ == "__main__":
    main()
