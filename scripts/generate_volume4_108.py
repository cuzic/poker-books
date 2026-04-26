#!/usr/bin/env python3
"""巻4 検証タスク #108 (フック 6 論点の具体値) 用シナリオ JSON 生成スクリプト.

書籍巻4 本文に採用する「読者の直感を揺さぶるフック」6 論点について、
各論点 5 シナリオ、合計 30 シナリオを生成し、
/home/cuzic/poker-books/knowledges/volume4/scenarios/108/ 配下に
1 シナリオ = 1 JSON ファイルとして出力する。

6 フック論点:
  1. ten_vs_ace        テンがエースより有利になる特定ケース (T-high flop)
  2. paired_board      ペアボードでのポケットペア優位 (paired flop/turn)
  3. monotone_small    モノトーンボードでは Bet サイズを控えめにする
  4. ahigh_check       A-high ドライ ボードは check が優位
  5. overbet_bluff     リバー過剰 Bet (>pot) はブラフ比重が高い
  6. bb3bet_defense    BB 3bet pot では BTN/SB のフォールド率が高い

スキーマ: /home/cuzic/poker-gto/docs/schemas/scenario.schema.json (draft-07)

pot/stack の想定:
  - 論点 1, 3, 4 (フロップ SRP):           pot_bb=7,  effective_stack_bb=92
  - 論点 2 (ターン SRP 深め):              pot_bb=20, effective_stack_bb=85
  - 論点 5 (リバー SRP 深め):              pot_bb=30, effective_stack_bb=70
  - 論点 6 (3bet pot フロップ):            pot_bb=15, effective_stack_bb=85
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
    "/home/cuzic/poker-books/knowledges/volume4/scenarios/108"
)

SCHEMA_PATH = Path(
    "/home/cuzic/poker-gto/docs/schemas/scenario.schema.json"
)


# ---------------------------------------------------------------------------
# 共通ソルバー設定
# ---------------------------------------------------------------------------

SOLVER_CONFIG: Dict[str, Any] = {
    "algorithm": "ES_MCCFR",
    "iterations": 5000,
    "timeout_sec": 60,
    "rng_seed": 42,
    "exploitability_target_bb": 0.05,
}


# ---------------------------------------------------------------------------
# シナリオ定義: 6 論点 × 5 シナリオ = 30 件
# 各エントリ: {
#   "topic": フック論点キー,
#   "index": 1..5,
#   "street": "flop"|"turn"|"river",
#   "board": [Card ...],
#   "pot_bb": float,
#   "effective_stack_bb": float,
#   "hero_position": str,
#   "hero_range": RangeSpec,
#   "villain_range": RangeSpec,
#   "bet_sizes": [float ...],
#   "note": 日本語の見出し,
# }
# ---------------------------------------------------------------------------


def _btn_open() -> Dict[str, Any]:
    """BTN オープン 100bb のプリセット参照."""
    return {"preset": "BtnOpen100bb"}


def _bb_defend_vs_btn() -> Dict[str, Any]:
    """BB コール vs BTN オープンのプリセット参照."""
    return {"preset": "BbDefendVsBtn"}


# --- 論点 1: ten_vs_ace (T-high flop, hero = BTN) -------------------------
# T が載るボード 5 種 (T75r / T54r / T92r / T86ss / T63mono)
# BTN open vs BB call、フロップ (SRP)。pot=7 (2.5 + 2.5 + 1 + 1 = 7)。
TEN_VS_ACE: List[Dict[str, Any]] = [
    {
        "board": ["Tc", "7d", "5s"],
        "note": "T75r (rainbow, dry)",
    },
    {
        "board": ["Td", "5c", "4s"],
        "note": "T54r (rainbow, low-connected)",
    },
    {
        "board": ["Th", "9c", "2d"],
        "note": "T92r (rainbow, blank low)",
    },
    {
        "board": ["Ts", "8s", "6h"],
        "note": "T86ss (two-tone, gutshot)",
    },
    {
        "board": ["Ts", "6s", "3s"],
        "note": "T63mono (monotone)",
    },
]

# --- 論点 2: paired_board (paired flop → turn, hero = BTN) ----------------
# ペアボード + ターン。pot=20 (フロップ cbet が call された想定)。stack=85。
PAIRED_BOARD: List[Dict[str, Any]] = [
    {
        "board": ["7c", "7d", "4s", "2h"],
        "note": "77 paired, low turn blank",
    },
    {
        "board": ["4c", "4d", "9s", "2h"],
        "note": "44 paired, mid turn",
    },
    {
        "board": ["9c", "9d", "5s", "3h"],
        "note": "99 paired, low turn",
    },
    {
        "board": ["Jc", "Jd", "6s", "2h"],
        "note": "JJ paired, low turn",
    },
    {
        "board": ["6c", "6d", "2s", "9h"],
        "note": "66 paired, turn overcard 9",
    },
]

# --- 論点 3: monotone_small (monotone flop, hero = BTN, bet size sweep) --
# モノトーン 3 枚のフロップ 5 種。bet_sizes を 5 点振って小さいサイズが選ばれる傾向を確認。
MONOTONE_SMALL: List[Dict[str, Any]] = [
    {
        "board": ["As", "Ks", "Qs"],
        "note": "AKQmono (high monotone)",
    },
    {
        "board": ["Jh", "9h", "7h"],
        "note": "J97mono (mid connected)",
    },
    {
        "board": ["Tc", "8c", "3c"],
        "note": "T83mono (mid-low)",
    },
    {
        "board": ["Kd", "7d", "2d"],
        "note": "K72mono (dry high)",
    },
    {
        "board": ["9s", "6s", "4s"],
        "note": "964mono (low connected)",
    },
]

# --- 論点 4: ahigh_check (A-high dry flop, hero = BTN) --------------------
# A-high ドライ rainbow 5 種。SRP pot=7。bet / check の比率を見る。
AHIGH_CHECK: List[Dict[str, Any]] = [
    {
        "board": ["Ac", "7d", "4s"],
        "note": "A74r (dry, low blank)",
    },
    {
        "board": ["Ad", "5c", "2s"],
        "note": "A52r (dry, wheel)",
    },
    {
        "board": ["Ah", "8c", "3d"],
        "note": "A83r (dry, disconnect)",
    },
    {
        "board": ["As", "9d", "5c"],
        "note": "A95r (dry, gap)",
    },
    {
        "board": ["Ad", "8h", "2c"],
        "note": "A82r (dry, low disconnect)",
    },
]

# --- 論点 5: overbet_bluff (river over-bet, hero = BTN) --------------------
# リバー 5 種。bet_sizes=[0.5, 1.5] の 2 点でサイズ別コンボの分布を比較する。
# pot=30、stack=70。
OVERBET_BLUFF: List[Dict[str, Any]] = [
    {
        "board": ["Kc", "8d", "3s", "2h", "Qc"],
        "note": "K83r + 2h + Qc (Q completes turn-river runouts)",
    },
    {
        "board": ["Ac", "7d", "4s", "2h", "Jc"],
        "note": "A74r + 2h + Jc (A-high with J river brick)",
    },
    {
        "board": ["Jd", "8c", "5s", "3h", "Kc"],
        "note": "J85r + 3h + Kc (K overcard river)",
    },
    {
        "board": ["Qs", "9d", "4c", "2h", "7s"],
        "note": "Q94r + 2h + 7s (low river blank)",
    },
    {
        "board": ["Th", "7d", "3c", "8s", "Ad"],
        "note": "T73r + 8s + Ad (A river overcard)",
    },
]

# --- 論点 6: bb3bet_defense (3bet pot flop, hero = BB) --------------------
# BB 3bet vs BTN call を想定。hero=BB (OOP)、preset は暫定 BbDefendVsBtn で代用。
# pot=15 (3bet pot 想定)、stack=85。
BB3BET_DEFENSE: List[Dict[str, Any]] = [
    {
        "board": ["Kh", "7c", "2d"],
        "note": "K72r (hero BB 3bet vs BTN call)",
    },
    {
        "board": ["Ac", "8d", "3h"],
        "note": "A83r (hero BB 3bet, A-high)",
    },
    {
        "board": ["Qs", "Js", "4h"],
        "note": "QJ4ss (hero BB 3bet, semi-wet)",
    },
    {
        "board": ["9c", "8c", "5d"],
        "note": "985ss (hero BB 3bet, wet)",
    },
    {
        "board": ["Td", "6d", "2s"],
        "note": "T62ss (hero BB 3bet, dry mid)",
    },
]


# 論点ごとの共通パラメータ (pot / stack / street / hero / ranges / bet_sizes)
TOPIC_CONFIG: Dict[str, Dict[str, Any]] = {
    "ten_vs_ace": {
        "title": "テンがエースより有利",
        "street": "flop",
        "pot_bb": 7,
        "effective_stack_bb": 92,
        "hero_position": "BTN",
        "hero_range": _btn_open(),
        "villain_range": _bb_defend_vs_btn(),
        "bet_sizes_to_evaluate": [0.33, 0.75, 1.5],
        "scenarios": TEN_VS_ACE,
    },
    "paired_board": {
        "title": "ペアボードは弱者に強い",
        "street": "turn",
        "pot_bb": 20,
        "effective_stack_bb": 85,
        "hero_position": "BTN",
        "hero_range": _btn_open(),
        "villain_range": _bb_defend_vs_btn(),
        "bet_sizes_to_evaluate": [0.33, 0.75, 1.5],
        "scenarios": PAIRED_BOARD,
    },
    "monotone_small": {
        "title": "モノトーンは控えめに",
        "street": "flop",
        "pot_bb": 7,
        "effective_stack_bb": 92,
        "hero_position": "BTN",
        "hero_range": _btn_open(),
        "villain_range": _bb_defend_vs_btn(),
        # モノトーン用に 5 点サイズスウィープ
        "bet_sizes_to_evaluate": [0.33, 0.5, 0.75, 1.0, 1.5],
        "scenarios": MONOTONE_SMALL,
    },
    "ahigh_check": {
        "title": "A-high は check で稼ぐ",
        "street": "flop",
        "pot_bb": 7,
        "effective_stack_bb": 92,
        "hero_position": "BTN",
        "hero_range": _btn_open(),
        "villain_range": _bb_defend_vs_btn(),
        "bet_sizes_to_evaluate": [0.33, 0.75, 1.5],
        "scenarios": AHIGH_CHECK,
    },
    "overbet_bluff": {
        "title": "リバー過剰 Bet はブラフのみ",
        "street": "river",
        "pot_bb": 30,
        "effective_stack_bb": 70,
        "hero_position": "BTN",
        "hero_range": _btn_open(),
        "villain_range": _bb_defend_vs_btn(),
        "bet_sizes_to_evaluate": [0.5, 1.5],
        "scenarios": OVERBET_BLUFF,
    },
    "bb3bet_defense": {
        "title": "BB 3bet 戦は SB/BTN が降りると得",
        "street": "flop",
        "pot_bb": 15,
        "effective_stack_bb": 85,
        "hero_position": "BB",
        # BB 3bet レンジは未定義のため、暫定的に BbDefendVsBtn プリセットで代用する
        "hero_range": _bb_defend_vs_btn(),
        "villain_range": _btn_open(),
        "bet_sizes_to_evaluate": [0.33, 0.75, 1.5],
        "scenarios": BB3BET_DEFENSE,
    },
}

# 論点の表示順序 (index.json / ファイル名のソート用)
TOPIC_ORDER: List[str] = [
    "ten_vs_ace",
    "paired_board",
    "monotone_small",
    "ahigh_check",
    "overbet_bluff",
    "bb3bet_defense",
]

assert set(TOPIC_ORDER) == set(TOPIC_CONFIG.keys())


# ---------------------------------------------------------------------------
# ボード検証ヘルパ
# ---------------------------------------------------------------------------


def _expected_board_length(street: str) -> int:
    """street_to_solve に対応する board 長."""
    if street == "flop":
        return 3
    if street == "turn":
        return 4
    if street == "river":
        return 5
    raise ValueError(f"unknown street: {street!r}")


def _validate_board(cards: List[str], street: str) -> None:
    """ボードの長さ・重複チェック."""
    expected = _expected_board_length(street)
    if len(cards) != expected:
        raise ValueError(
            f"{street} board must be {expected} cards, got {len(cards)}: {cards}"
        )
    if len(set(cards)) != len(cards):
        raise ValueError(f"duplicate cards in board: {cards}")


# ---------------------------------------------------------------------------
# シナリオ dict 構築
# ---------------------------------------------------------------------------


def _build_scenario(
    topic: str,
    index: int,
    entry: Dict[str, Any],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """1 シナリオ分の dict を構築する."""
    board_cards: List[str] = list(entry["board"])
    street: str = str(config["street"])
    _validate_board(board_cards, street)

    scenario_id = f"hook_108_{topic}_{index}"
    description = (
        f"[{config['title']}] {entry['note']} "
        f"(street={street}, pot={config['pot_bb']}bb)"
    )

    return {
        "scenario_id": scenario_id,
        "description": description,
        "street_to_solve": street,
        "board": board_cards,
        "pot_bb": config["pot_bb"],
        "effective_stack_bb": config["effective_stack_bb"],
        "hero_position": config["hero_position"],
        "hero_range": dict(config["hero_range"]),
        "villain_range": dict(config["villain_range"]),
        "bet_sizes_to_evaluate": list(config["bet_sizes_to_evaluate"]),
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


def _validate_against_schema(
    scenario: Dict[str, Any], schema: Optional[Dict[str, Any]]
) -> None:
    """jsonschema が利用可能なら検証する (無ければスキップ)."""
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

    # 冪等性: 既存 hook_108_*.json と index.json をクリア
    for p in OUTPUT_DIR.glob("hook_108_*.json"):
        p.unlink()
    index_path = OUTPUT_DIR / "index.json"
    if index_path.exists():
        index_path.unlink()

    index_scenarios: List[Dict[str, Any]] = []
    topic_counter: Counter = Counter()

    for topic in TOPIC_ORDER:
        config = TOPIC_CONFIG[topic]
        scenarios: List[Dict[str, Any]] = config["scenarios"]
        if len(scenarios) != 5:
            raise RuntimeError(
                f"topic {topic!r} must have 5 scenarios, got {len(scenarios)}"
            )
        for i, entry in enumerate(scenarios, start=1):
            scenario = _build_scenario(
                topic=topic,
                index=i,
                entry=entry,
                config=config,
            )
            _validate_against_schema(scenario, schema)

            out_path = OUTPUT_DIR / f"{scenario['scenario_id']}.json"
            _write_json(out_path, scenario)

            index_scenarios.append(
                {
                    "scenario_id": scenario["scenario_id"],
                    "topic": topic,
                    "topic_title": config["title"],
                    "index": i,
                    "street": config["street"],
                    "board": list(scenario["board"]),
                    "pot_bb": config["pot_bb"],
                    "effective_stack_bb": config["effective_stack_bb"],
                    "hero_position": config["hero_position"],
                    "bet_sizes_to_evaluate": list(
                        config["bet_sizes_to_evaluate"]
                    ),
                    "note": entry["note"],
                    "file": out_path.name,
                }
            )
            topic_counter[topic] += 1

    # index.json を書き出す
    index_payload: Dict[str, Any] = {
        "task": "108",
        "title": "フック 6 論点の具体値",
        "total": len(index_scenarios),
        "topics": {t: topic_counter[t] for t in TOPIC_ORDER},
        "topic_titles": {t: TOPIC_CONFIG[t]["title"] for t in TOPIC_ORDER},
        "scenarios": index_scenarios,
    }
    _write_json(OUTPUT_DIR / "index.json", index_payload)

    # 終了サマリ
    print(f"generated {len(index_scenarios)} scenarios in {OUTPUT_DIR}")
    print("topics:", {t: topic_counter[t] for t in TOPIC_ORDER})


if __name__ == "__main__":
    main()
