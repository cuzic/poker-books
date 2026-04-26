#!/usr/bin/env python3
"""巻4 検証タスク #105 (ブロッカー論) 用シナリオ JSON 生成スクリプト.

4 論点 × 5 シナリオ = 20 を、特定ハンド (または狭いレンジ) を hero_range に
設定した形で生成し、combo 単位で戦略を取り出せるようにする。

論点:
  A. AA<88 サイズ逆転論      — 低ミドルペアの方が大サイズで value bet するか
  B. ミスド FD ブラフ論      — 完成しなかったフラッシュドローが最適ブラフか
  C. ストレートブロッカー論  — ストレート可能ボードで特定カードを持つ value
  D. 逆ブロッカー論          — Fold 誘発ブロッカーがなく、薄い value で打てる

出力先:
  /home/cuzic/poker-books/knowledges/volume4/scenarios/105/<scenario_id>.json
  /home/cuzic/poker-books/knowledges/volume4/scenarios/105/index.json

スキーマ: /home/cuzic/poker-gto/docs/schemas/scenario.schema.json (draft-07)
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path(
    "/home/cuzic/poker-books/knowledges/volume4/scenarios/105"
)

SCHEMA_PATH = Path(
    "/home/cuzic/poker-gto/docs/schemas/scenario.schema.json"
)

# 標準 bet サイズ
BET_SIZES: List[float] = [0.33, 0.5, 0.75, 1.5]

# 論点ごとの ID プレフィクス (ファイル名生成に使用)
TOPIC_PREFIX: Dict[str, str] = {
    "AA_vs_88": "blocker_105_AA_vs_88",
    "missed_fd": "blocker_105_missed_fd",
    "straight_block": "blocker_105_straight_block",
    "reverse_block": "blocker_105_reverse_block",
}

# 論点ごとの日本語タイトル (description 用)
TOPIC_TITLE: Dict[str, str] = {
    "AA_vs_88": "AA<88 サイズ逆転",
    "missed_fd": "ミスド FD ブラフ",
    "straight_block": "ストレートブロッカー",
    "reverse_block": "逆ブロッカー",
}


# ---------------------------------------------------------------------------
# 20 シナリオ定数定義
#
# 各エントリは以下のフィールドを持つ:
#   topic              : 論点識別子 (上記 TOPIC_PREFIX キー)
#   index              : 論点内の連番 (1..5)
#   description        : 書籍執筆時の参照用日本語コメント
#   street_to_solve    : "flop" / "turn" / "river"
#   board              : ボードカード (3/4/5 枚)
#   hero_position      : "BTN" / "BB" など
#   hero_expr          : PokerStove 記法 (特定ハンド絞り込み)
#   villain_preset     : プリセット名
#   pot_bb             : ポット (BB)
#   effective_stack_bb : 実効スタック (BB)
#
# 特定 combo を狙う場合は expr に具体 combo (例 "AsQs") を記述可能。
# ---------------------------------------------------------------------------


SCENARIOS: List[Dict[str, Any]] = [
    # -----------------------------------------------------------------
    # A. AA<88 サイズ逆転論 — 5 シナリオ
    #   低ミドルペア (88/99/TT) と overpair (AA/KK) を同時に hero_range に
    #   入れ、combo 単位で value サイズを比較する。River 決断点が中心。
    # -----------------------------------------------------------------
    {
        "topic": "AA_vs_88",
        "index": 1,
        "description": "6s5d2c + 8h + 4s (低 drawy ボード, 88/AA サイズ比較)",
        "street_to_solve": "river",
        "board": ["6s", "5d", "2c", "8h", "4s"],
        "hero_position": "BTN",
        "hero_expr": "AA,88",
        "villain_preset": "BbDefendVsBtn",
        "pot_bb": 25,
        "effective_stack_bb": 75,
    },
    {
        "topic": "AA_vs_88",
        "index": 2,
        "description": "7c6d2s + 9h + 3c (コネクタ + オーバー完成, 99/AA 比較)",
        "street_to_solve": "river",
        "board": ["7c", "6d", "2s", "9h", "3c"],
        "hero_position": "BTN",
        "hero_expr": "AA,99",
        "villain_preset": "BbDefendVsBtn",
        "pot_bb": 25,
        "effective_stack_bb": 75,
    },
    {
        "topic": "AA_vs_88",
        "index": 3,
        "description": "8d5c3h + Td + 2c (TT がミドル, AA/TT 比較)",
        "street_to_solve": "river",
        "board": ["8d", "5c", "3h", "Td", "2c"],
        "hero_position": "BTN",
        "hero_expr": "AA,TT",
        "villain_preset": "BbDefendVsBtn",
        "pot_bb": 22,
        "effective_stack_bb": 78,
    },
    {
        "topic": "AA_vs_88",
        "index": 4,
        "description": "9s6h3d + 2s + 7c (スモールボード, AA/99 サイズ逆転)",
        "street_to_solve": "river",
        "board": ["9s", "6h", "3d", "2s", "7c"],
        "hero_position": "BTN",
        "hero_expr": "AA,99",
        "villain_preset": "BbDefendVsBtn",
        "pot_bb": 22,
        "effective_stack_bb": 78,
    },
    {
        "topic": "AA_vs_88",
        "index": 5,
        "description": "7h5s4d + 8c + 2h (コネクタリバー, 88/AA 比較)",
        "street_to_solve": "river",
        "board": ["7h", "5s", "4d", "8c", "2h"],
        "hero_position": "BTN",
        "hero_expr": "AA,88",
        "villain_preset": "BbDefendVsBtn",
        "pot_bb": 25,
        "effective_stack_bb": 75,
    },
    # -----------------------------------------------------------------
    # B. ミスド FD ブラフ論 — 5 シナリオ
    #   ターン/リバーで完成しなかった FD が river の最適ブラフになるか。
    # -----------------------------------------------------------------
    {
        "topic": "missed_fd",
        "index": 1,
        "description": "Kh7h2c + 4h + 2s (3rd h 止まり, Asxs FD missed)",
        "street_to_solve": "river",
        "board": ["Kh", "7h", "2c", "4h", "2s"],
        "hero_position": "BTN",
        "hero_expr": "AsQs,AsJs",
        "villain_preset": "BbDefendVsBtn",
        "pot_bb": 20,
        "effective_stack_bb": 80,
    },
    {
        "topic": "missed_fd",
        "index": 2,
        "description": "Qd8d3s + 5d + 7c (4th d stop, As/Ks no-d FD missed)",
        "street_to_solve": "river",
        "board": ["Qd", "8d", "3s", "5d", "7c"],
        "hero_position": "BTN",
        "hero_expr": "AsKs,AhKh",
        "villain_preset": "BbDefendVsBtn",
        "pot_bb": 20,
        "effective_stack_bb": 80,
    },
    {
        "topic": "missed_fd",
        "index": 3,
        "description": "Jc9c4h + 2c + 3h (4 子クラブ完成なし, Ad spade FD)",
        "street_to_solve": "river",
        "board": ["Jc", "9c", "4h", "2c", "3h"],
        "hero_position": "BTN",
        "hero_expr": "AhTh,AhQh",
        "villain_preset": "BbDefendVsBtn",
        "pot_bb": 18,
        "effective_stack_bb": 82,
    },
    {
        "topic": "missed_fd",
        "index": 4,
        "description": "Ts7s2d + 5s + 6c (3 枚 spade 止まり, Ax non-s missed)",
        "street_to_solve": "river",
        "board": ["Ts", "7s", "2d", "5s", "6c"],
        "hero_position": "BTN",
        "hero_expr": "AhJh,AdQd",
        "villain_preset": "BbDefendVsBtn",
        "pot_bb": 18,
        "effective_stack_bb": 82,
    },
    {
        "topic": "missed_fd",
        "index": 5,
        "description": "Kh5h3c + Qh + 2d (ターン 3h 完成候補, FD missed の河)",
        "street_to_solve": "river",
        "board": ["Kh", "5h", "3c", "Qh", "2d"],
        "hero_position": "BTN",
        "hero_expr": "AsJs,AcTc",
        "villain_preset": "BbDefendVsBtn",
        "pot_bb": 20,
        "effective_stack_bb": 80,
    },
    # -----------------------------------------------------------------
    # C. ストレートブロッカー論 — 5 シナリオ
    #   ストレート可能 / 完成ボードで特定のカードがストレートをブロックし、
    #   value で大きく打てるか。
    # -----------------------------------------------------------------
    {
        "topic": "straight_block",
        "index": 1,
        "description": "9c8h7d + 2s + 3c (完成せずだが TT/KK がストレート牽制)",
        "street_to_solve": "river",
        "board": ["9c", "8h", "7d", "2s", "3c"],
        "hero_position": "BTN",
        "hero_expr": "KK,TT,99",
        "villain_preset": "BbDefendVsBtn",
        "pot_bb": 22,
        "effective_stack_bb": 78,
    },
    {
        "topic": "straight_block",
        "index": 2,
        "description": "Qc6s5h + 4d + 3s (ストレート完成; KK/TT がブロック)",
        "street_to_solve": "river",
        "board": ["Qc", "6s", "5h", "4d", "3s"],
        "hero_position": "BTN",
        "hero_expr": "KK,TT",
        "villain_preset": "BbDefendVsBtn",
        "pot_bb": 24,
        "effective_stack_bb": 76,
    },
    {
        "topic": "straight_block",
        "index": 3,
        "description": "Jd9c8h + Th + 2c (ストレート完成; Q/7 が最強だが KK がブロック薄)",
        "street_to_solve": "river",
        "board": ["Jd", "9c", "8h", "Th", "2c"],
        "hero_position": "BTN",
        "hero_expr": "AA,KK",
        "villain_preset": "BbDefendVsBtn",
        "pot_bb": 24,
        "effective_stack_bb": 76,
    },
    {
        "topic": "straight_block",
        "index": 4,
        "description": "Th9d8c + 7s + 2h (ストレート完成; QQ/JJ/AA ブロッカー比較)",
        "street_to_solve": "river",
        "board": ["Th", "9d", "8c", "7s", "2h"],
        "hero_position": "BTN",
        "hero_expr": "AA,QQ,JJ",
        "villain_preset": "BbDefendVsBtn",
        "pot_bb": 24,
        "effective_stack_bb": 76,
    },
    {
        "topic": "straight_block",
        "index": 5,
        "description": "8s7c6d + 5h + 2s (ストレート完成; 99/TT が上ストレートブロック)",
        "street_to_solve": "river",
        "board": ["8s", "7c", "6d", "5h", "2s"],
        "hero_position": "BTN",
        "hero_expr": "TT,99",
        "villain_preset": "BbDefendVsBtn",
        "pot_bb": 22,
        "effective_stack_bb": 78,
    },
    # -----------------------------------------------------------------
    # D. 逆ブロッカー (薄い value 有利) — 5 シナリオ
    #   Fold 誘発ブロッカーがない/villain の call 域を薄める combo。
    # -----------------------------------------------------------------
    {
        "topic": "reverse_block",
        "index": 1,
        "description": "Ad9s4c + 7h + 2s (A 絡み wo FD, top pair thin value)",
        "street_to_solve": "river",
        "board": ["Ad", "9s", "4c", "7h", "2s"],
        "hero_position": "BTN",
        "hero_expr": "AhQd,AhJd",
        "villain_preset": "BbDefendVsBtn",
        "pot_bb": 20,
        "effective_stack_bb": 80,
    },
    {
        "topic": "reverse_block",
        "index": 2,
        "description": "As8d3c + 6h + 2s (TP + weak kicker, reverse block で thin value)",
        "street_to_solve": "river",
        "board": ["As", "8d", "3c", "6h", "2s"],
        "hero_position": "BTN",
        "hero_expr": "AcTd,AcJd",
        "villain_preset": "BbDefendVsBtn",
        "pot_bb": 18,
        "effective_stack_bb": 82,
    },
    {
        "topic": "reverse_block",
        "index": 3,
        "description": "Kh7d4c + 9s + 2h (TP w/o FD ブロッカー, 薄 value 可)",
        "street_to_solve": "turn",
        "board": ["Kh", "7d", "4c", "9s"],
        "hero_position": "BTN",
        "hero_expr": "KdTc,KdJc",
        "villain_preset": "BbDefendVsBtn",
        "pot_bb": 12,
        "effective_stack_bb": 88,
    },
    {
        "topic": "reverse_block",
        "index": 4,
        "description": "Qc9h5d + 3s + 2c (Qx TP reverse block, Ax 払え)",
        "street_to_solve": "river",
        "board": ["Qc", "9h", "5d", "3s", "2c"],
        "hero_position": "BTN",
        "hero_expr": "QdJc,QdTc",
        "villain_preset": "BbDefendVsBtn",
        "pot_bb": 20,
        "effective_stack_bb": 80,
    },
    {
        "topic": "reverse_block",
        "index": 5,
        "description": "Jh8c4d + 5s + 2h (TP wo draws, 薄 value 比較)",
        "street_to_solve": "river",
        "board": ["Jh", "8c", "4d", "5s", "2h"],
        "hero_position": "BTN",
        "hero_expr": "JdTc,JdQc",
        "villain_preset": "BbDefendVsBtn",
        "pot_bb": 18,
        "effective_stack_bb": 82,
    },
]


# ---------------------------------------------------------------------------
# シナリオ構築
# ---------------------------------------------------------------------------


def _build_scenario(entry: Dict[str, Any]) -> Dict[str, Any]:
    """SCENARIOS の 1 エントリから、スキーマ準拠のシナリオ dict を構築する."""
    topic: str = entry["topic"]
    idx: int = entry["index"]
    prefix = TOPIC_PREFIX[topic]
    scenario_id = f"{prefix}_{idx}"

    # street と board 枚数の整合性を確認
    street: str = entry["street_to_solve"]
    board: List[str] = list(entry["board"])
    expected_len = {"flop": 3, "turn": 4, "river": 5}[street]
    if len(board) != expected_len:
        raise ValueError(
            f"{scenario_id}: board length {len(board)} != expected {expected_len} for {street}"
        )

    description_topic = TOPIC_TITLE[topic]
    description = f"[{description_topic}] {entry['description']}"

    return {
        "scenario_id": scenario_id,
        "description": description,
        "street_to_solve": street,
        "board": board,
        "pot_bb": entry["pot_bb"],
        "effective_stack_bb": entry["effective_stack_bb"],
        "hero_position": entry["hero_position"],
        "hero_range": {"expr": entry["hero_expr"]},
        "villain_range": {"preset": entry["villain_preset"]},
        "bet_sizes_to_evaluate": list(BET_SIZES),
        "solver_config": {
            "algorithm": "ES_MCCFR",
            "iterations": 8000,
            "timeout_sec": 60,
            "rng_seed": 42,
            "exploitability_target_bb": 0.05,
        },
    }


# ---------------------------------------------------------------------------
# ファイル出力とスキーマ検証
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


def _validate(scenario: Dict[str, Any], schema: Optional[Dict[str, Any]]) -> None:
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
    # 件数チェック (4 論点 × 5 = 20)
    if len(SCENARIOS) != 20:
        raise RuntimeError(
            f"expected 20 scenarios, got {len(SCENARIOS)}"
        )
    topic_counts = Counter(e["topic"] for e in SCENARIOS)
    for topic in TOPIC_PREFIX:
        if topic_counts.get(topic, 0) != 5:
            raise RuntimeError(
                f"topic {topic} has {topic_counts.get(topic, 0)} scenarios (expected 5)"
            )

    schema = _load_schema()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 冪等性のため、既存の 105 系 JSON を一旦クリア
    for p in OUTPUT_DIR.glob("blocker_105_*.json"):
        p.unlink()
    index_path = OUTPUT_DIR / "index.json"
    if index_path.exists():
        index_path.unlink()

    index_scenarios: List[Dict[str, Any]] = []
    topics_counter: Counter = Counter()

    for entry in SCENARIOS:
        scenario = _build_scenario(entry)
        _validate(scenario, schema)

        out_path = OUTPUT_DIR / f"{scenario['scenario_id']}.json"
        _write_json(out_path, scenario)

        index_scenarios.append(
            {
                "scenario_id": scenario["scenario_id"],
                "topic": entry["topic"],
                "topic_title": TOPIC_TITLE[entry["topic"]],
                "index": entry["index"],
                "street": scenario["street_to_solve"],
                "board": scenario["board"],
                "hero_expr": entry["hero_expr"],
                "villain_preset": entry["villain_preset"],
                "file": out_path.name,
            }
        )
        topics_counter[entry["topic"]] += 1

    index_payload: Dict[str, Any] = {
        "task": "105",
        "title": "ブロッカー論",
        "total": len(index_scenarios),
        "topics": dict(topics_counter),
        "scenarios": index_scenarios,
    }
    _write_json(OUTPUT_DIR / "index.json", index_payload)

    print(f"generated {len(index_scenarios)} scenarios in {OUTPUT_DIR}")
    print("topics:", dict(topics_counter))


if __name__ == "__main__":
    main()
