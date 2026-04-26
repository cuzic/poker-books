#!/usr/bin/env python3
"""巻4 検証タスク #104 (A/B/C プラン 3 ストリート EV) 用シナリオ JSON 生成スクリプト.

5 局面 × 3 プラン (A/B/C) = 15 シナリオを生成する。

プラン定義 (書籍論点 #104):
  - プラン A: フロップで cbet、BB が fold してポット確保
              → street_to_solve = "flop" (board 3 枚)
  - プラン B: フロップ cbet → BB call → ターン check-check → リバー judgment
              → street_to_solve = "river" (board 5 枚)
  - プラン C: フロップ cbet → BB call → ターン cbet → BB call → リバー judgment
              → street_to_solve = "river" (board 5 枚)

重要な前提:
  現状 `solve_range_vs_range` は単一ストリートサブゲームのみ解ける
  (poker-gto/docs/design/multistreet_solver.md 参照)。
  本物のマルチストリート通し EV は #35 (プリフロップから通し) で実装予定。
  本タスクでは JSON 生成のみ行い、実行は #35 / #30 完了後に行う。
  各プランの最終ストリートを「単ストリート解で近似する」形式である点に留意。

5 局面 (書籍論点の代表例):
  1. K72r      (dry)            AKo TPTK、迷いなし cbet 継続が強い
  2. 987ss     (wet)            QQ overpair、FD/SD 警戒、プラン B が魅力
  3. AKQmono   (完全 flush 完成)  KK 第 2 オーバーペア、プラン A (小サイズで諦め) 正解候補
  4. T75r      (mid dry)        AK オーバー、プラン C で三発打ちする局面
  5. A72r      (A-high)         AQo TP + Q ブロッカー、プラン A 気味

出力先:
  /home/cuzic/poker-books/knowledges/volume4/scenarios/104/<scenario_id>.json
  /home/cuzic/poker-books/knowledges/volume4/scenarios/104/index.json

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
    "/home/cuzic/poker-books/knowledges/volume4/scenarios/104"
)

SCHEMA_PATH = Path(
    "/home/cuzic/poker-gto/docs/schemas/scenario.schema.json"
)

# 標準 bet サイズ (ポット比率)
BET_SIZES: List[float] = [0.33, 0.5, 0.75, 1.5]

# プラン別の pot / stack (BB 単位)
#   プラン A: flop 段階そのまま
#     pot=7   (BTN 2.5 open + BB 2.5 call + blinds 1.5 ≒ 6.5 だが丸めて 7)
#     stack=92
#   プラン B: flop cbet 33% (pot 7 → bet 約 2, BB call 2) + turn check-check
#     追加で +4 BB (双方 2 BB ずつ) がポットに入り 11、実効スタック 92-2=90 → 84 に近似
#     書籍指定値: pot=11, stack=84
#   プラン C: flop cbet (約 2.75) + turn cbet (約 8.25 バレル) を共に BB call
#     pot=7 + 2.75*2 + 8.25*2 = 7 + 5.5 + 16.5 = 29 → 指定 27 に近似
#     実効スタック 92 - 2.75 - 8.25 ≒ 81 → 指定 67 (リバー全押し相当の圧力を想定)
#     書籍指定値: pot=27, stack=67
PLAN_POT_STACK: Dict[str, Dict[str, float]] = {
    "A": {"pot_bb": 7.0, "effective_stack_bb": 92.0},
    "B": {"pot_bb": 11.0, "effective_stack_bb": 84.0},
    "C": {"pot_bb": 27.0, "effective_stack_bb": 67.0},
}

# プラン別の street_to_solve
PLAN_STREET: Dict[str, str] = {
    "A": "flop",
    "B": "river",
    "C": "river",
}

# プラン別の日本語タイトル (description 用)
PLAN_TITLE: Dict[str, str] = {
    "A": "プラン A (フロップ cbet で BB fold 想定)",
    "B": "プラン B (フロップ cbet → ターン check-check → リバー判断)",
    "C": "プラン C (フロップ cbet → ターン cbet-call → リバー判断)",
}


# ---------------------------------------------------------------------------
# 5 局面の board 設計
#
# 各局面は以下を定義:
#   scene            : 局面識別子 (ファイル名に使用)
#   title_ja         : 日本語タイトル (書籍執筆用)
#   flop             : フロップ 3 枚 (プラン A で使用)
#   turn_card        : ターンで追加される 1 枚 (プラン B/C 共通)
#   river_card       : リバーで追加される 1 枚 (プラン B/C 共通)
#   note             : 書籍論点上のコメント
#
# ターン/リバーは書籍で引用しやすい代表的なカード (ランダム選定なし)。
# プラン B (check-check) と C (cbet-call) で同じ board を用いるのは
# 「同じ判断点で、到達経路 (pot/stack) が異なるとどう戦略が変わるか」を
# 比較する意図 (書籍論点 #104)。
# ---------------------------------------------------------------------------


SCENES: List[Dict[str, Any]] = [
    {
        "scene": "K72r",
        "title_ja": "K72r (dry, AKo TPTK 局面)",
        "flop": ["Kc", "7d", "2s"],
        # ターン Ah: オーバーカード (TPTK が 2nd pair 化を警戒しつつも強い)
        # リバー 3c: 完全ブランク
        "turn_card": "Ah",
        "river_card": "3c",
        "note": "dry ボードで BDSD/FD がほぼ無い。プラン A の即 fold が強い局面",
    },
    {
        "scene": "987ss",
        "title_ja": "987ss (wet, QQ overpair 局面)",
        # 9s 8s: spade two-tone、7d が rainbow 打ち消し
        "flop": ["9s", "8s", "7d"],
        # ターン Jc: 接近 rank だが spade ではない (FD 未完成)、ストレート浸食は抑制
        # リバー 2d: ブランク
        "turn_card": "Jc",
        "river_card": "2d",
        "note": "wet ボードで FD/SD が濃い。プラン B (turn check で pot 制御) が魅力",
    },
    {
        "scene": "AKQmono",
        "title_ja": "AKQmono (完全 flush 完成、KK 第 2 オーバーペア局面)",
        # 全て spade
        "flop": ["As", "Ks", "Qs"],
        # ターン 2d / リバー 5h: board のフラッシュ構造を変えないブランク
        "turn_card": "2d",
        "river_card": "5h",
        "note": "既にフラッシュ完成。KK では薄い。プラン A (小サイズで諦め) 正解候補",
    },
    {
        "scene": "T75r",
        "title_ja": "T75r (mid dry, AK オーバーカード局面)",
        "flop": ["Tc", "7d", "5s"],
        # ターン Jc: オーバーカード追加 (Q か K で gutshot 形成可)
        # リバー 2h: ブランク
        "turn_card": "Jc",
        "river_card": "2h",
        "note": "AK オーバー + gutshot ライン。プラン C で三発打ちの検証対象",
    },
    {
        "scene": "A72r",
        "title_ja": "A72r (A-high, AQo TP + Q ブロッカー局面)",
        "flop": ["Ac", "7d", "2s"],
        # ターン 4c: ブランク (3-spade FD は board に存在しない)
        # リバー 9h: ブランク
        "turn_card": "4c",
        "river_card": "9h",
        "note": "A-high で villain call 域薄い。プラン A でチェックバック気味の検証",
    },
]

assert len(SCENES) == 5, "5 局面想定"


# ---------------------------------------------------------------------------
# シナリオ構築
# ---------------------------------------------------------------------------


def _plan_board(scene: Dict[str, Any], plan: str) -> List[str]:
    """プランに応じた board (3 枚 or 5 枚) を返す."""
    flop: List[str] = list(scene["flop"])
    if plan == "A":
        return flop
    # B / C はリバーまで
    turn_card: str = scene["turn_card"]
    river_card: str = scene["river_card"]
    full_board = [*flop, turn_card, river_card]
    # 重複チェック
    if len(set(full_board)) != 5:
        raise ValueError(
            f"duplicate card in scene {scene['scene']} plan {plan}: {full_board}"
        )
    return full_board


def _build_scenario(scene: Dict[str, Any], plan: str) -> Dict[str, Any]:
    """1 シナリオ (局面 × プラン) のスキーマ準拠 dict を構築する."""
    scene_id: str = scene["scene"]
    scenario_id = f"multistreet_104_{scene_id}_plan{plan}"

    board = _plan_board(scene, plan)
    street = PLAN_STREET[plan]
    expected_len = {"flop": 3, "turn": 4, "river": 5}[street]
    if len(board) != expected_len:
        raise ValueError(
            f"{scenario_id}: board length {len(board)} != expected {expected_len}"
        )

    pot_stack = PLAN_POT_STACK[plan]
    description = (
        f"[{scene['title_ja']}] {PLAN_TITLE[plan]} — {scene['note']}"
    )

    return {
        "scenario_id": scenario_id,
        "description": description,
        "street_to_solve": street,
        "board": board,
        "pot_bb": pot_stack["pot_bb"],
        "effective_stack_bb": pot_stack["effective_stack_bb"],
        "hero_position": "BTN",
        "hero_range": {"preset": "BtnOpen100bb"},
        "villain_range": {"preset": "BbDefendVsBtn"},
        "bet_sizes_to_evaluate": list(BET_SIZES),
        "solver_config": {
            "algorithm": "ES_MCCFR",
            "iterations": 5000,
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


def _validate(scenario: Dict[str, Any], schema: Optional[Dict[str, Any]]) -> int:
    """スキーマ検証を試みる。成功時 1、スキップ時 0 を返す."""
    if schema is None:
        return 0
    try:
        import jsonschema  # 遅延 import
    except ImportError:
        return 0
    jsonschema.validate(scenario, schema)
    return 1


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------


def main() -> None:
    schema = _load_schema()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 冪等性のため、既存の 104 系 JSON を一旦クリア
    for p in OUTPUT_DIR.glob("multistreet_104_*.json"):
        p.unlink()
    index_path = OUTPUT_DIR / "index.json"
    if index_path.exists():
        index_path.unlink()

    index_scenes: List[Dict[str, Any]] = []
    plan_counter: Counter = Counter()
    validated = 0
    total = 0

    for scene in SCENES:
        plan_entries: List[Dict[str, Any]] = []
        for plan in ("A", "B", "C"):
            scenario = _build_scenario(scene, plan)
            validated += _validate(scenario, schema)
            total += 1

            out_path = OUTPUT_DIR / f"{scenario['scenario_id']}.json"
            _write_json(out_path, scenario)

            plan_entries.append(
                {
                    "plan": plan,
                    "scenario_id": scenario["scenario_id"],
                    "street": scenario["street_to_solve"],
                    "board": scenario["board"],
                    "pot_bb": scenario["pot_bb"],
                    "effective_stack_bb": scenario["effective_stack_bb"],
                    "file": out_path.name,
                }
            )
            plan_counter[plan] += 1

        index_scenes.append(
            {
                "scene": scene["scene"],
                "title_ja": scene["title_ja"],
                "flop": scene["flop"],
                "turn_card": scene["turn_card"],
                "river_card": scene["river_card"],
                "note": scene["note"],
                "plans": plan_entries,
            }
        )

    index_payload: Dict[str, Any] = {
        "task": "104",
        "title": "A/B/C プラン 3 ストリート EV 比較",
        "approximation_note": (
            "各プランの最終ストリートを単ストリート解で近似する形式。"
            "真のマルチストリート通し EV は poker-gto #35 / #30 完了後に再実行。"
        ),
        "total": total,
        "scenes": len(SCENES),
        "plans_per_scene": 3,
        "plan_counts": dict(plan_counter),
        "scenes_detail": index_scenes,
    }
    _write_json(OUTPUT_DIR / "index.json", index_payload)

    print(f"generated {total} scenarios in {OUTPUT_DIR}")
    print(f"schema validated: {validated}/{total}")
    print("plan counts:", dict(plan_counter))


if __name__ == "__main__":
    main()
