#!/usr/bin/env python3
"""巻4 検証 Phase 2 チューニング実験: max_raises / bet_sizes スイープ.

`generate_flop_accuracy_30.py` の 30 ボードを基に、6 パターンのバリアントを生成する。
- mr1 / mr2 / mr3: max_raises = 1 / 2 / 3 (bet_sizes は baseline と同じ)
- bs_a / bs_b / bs_c: bet_sizes のバリエーション (max_raises=1)

出力先 (各 30 シナリオ + index.json):
  - /home/cuzic/poker-books/knowledges/volume4/scenarios/flop_accuracy_30_mr{1,2,3}/
  - /home/cuzic/poker-books/knowledges/volume4/scenarios/flop_accuracy_30_bs_{a,b,c}/
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import generate_flop_accuracy_30 as base  # pyright: ignore[reportMissingImports]


BOOKS_ROOT = Path("/home/cuzic/poker-books")
SCEN_ROOT = BOOKS_ROOT / "knowledges" / "volume4" / "scenarios"

# (suffix, max_raises, bet_sizes)
EXPERIMENTS: List[Tuple[str, int, List[float]]] = [
    ("mr1", 1, [0.33, 0.5, 0.75, 1.5]),
    ("mr2", 2, [0.33, 0.5, 0.75, 1.5]),
    ("mr3", 3, [0.33, 0.5, 0.75, 1.5]),
    ("bs_a", 1, [0.33, 0.5, 0.75, 1.5]),   # baseline 再現 (対照)
    ("bs_b", 1, [0.25, 0.33, 0.5, 0.75]),  # 小ベット寄り (オーバーベット抑制)
    ("bs_c", 1, [0.33, 0.66, 1.25]),       # GTO Wizard 的 3 サイズ
]


def build_tuning_scenario(
    board_label: str,
    cards: List[str],
    gto_freq: int,
    max_raises: int,
    bet_sizes: List[float],
    suffix: str,
) -> Dict[str, Any]:
    """チューニング用シナリオを構築する。"""
    scenario = base.build_scenario(board_label, cards, gto_freq)
    # scenario_id にサフィックスを付与し、重複ファイル名を避ける
    scenario["scenario_id"] = f"{scenario['scenario_id']}_{suffix}"
    scenario["bet_sizes_to_evaluate"] = bet_sizes
    # solver_config に max_raises を追加
    solver_cfg = scenario.get("solver_config")
    if not isinstance(solver_cfg, dict):
        solver_cfg = {}
    solver_cfg["max_raises"] = max_raises
    scenario["solver_config"] = solver_cfg
    return scenario


def write_experiment(
    suffix: str, max_raises: int, bet_sizes: List[float]
) -> None:
    out_dir = SCEN_ROOT / f"flop_accuracy_30_{suffix}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 既存の flop_acc30_*_{suffix}.json を消す (冪等)
    for p in out_dir.glob("flop_acc30_*.json"):
        p.unlink()
    idx = out_dir / "index.json"
    if idx.exists():
        idx.unlink()

    index_scenarios: List[Dict[str, Any]] = []

    for board_label, gto_freq, size_note, source in base.GTO_BOARD_DATA:
        cards = base.cards_for_label(board_label)
        scenario = build_tuning_scenario(
            board_label, cards, gto_freq, max_raises, bet_sizes, suffix
        )
        out_path = out_dir / f"{scenario['scenario_id']}.json"
        base.write_json(out_path, scenario)

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
        "task": f"flop_accuracy_30_{suffix}",
        "title": (
            f"30 ボード精度検証 チューニング: "
            f"max_raises={max_raises}, bet_sizes={bet_sizes}"
        ),
        "total": len(index_scenarios),
        "hero_range": "BtnOpen100bb",
        "villain_range": "BbDefendVsBtn",
        "pot_bb": 7,
        "effective_stack_bb": 97,
        "max_raises": max_raises,
        "bet_sizes": bet_sizes,
        "scenarios": index_scenarios,
    }
    base.write_json(idx, index_payload)
    print(
        f"[{suffix}] generated {len(index_scenarios)} scenarios in {out_dir} "
        f"(max_raises={max_raises}, bet_sizes={bet_sizes})"
    )


def main() -> None:
    for suffix, max_raises, bet_sizes in EXPERIMENTS:
        write_experiment(suffix, max_raises, bet_sizes)


if __name__ == "__main__":
    main()
