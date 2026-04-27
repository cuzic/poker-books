#!/usr/bin/env python3
"""巻4 検証タスク #103 / #105 / #106 / #108 を蒸留モデル経由で実行するラッパー.

`~/poker-distill/training/gto_query.py`（v7b 蒸留モデル CLI）を呼び出して
scenario JSON のレンジ・ボード・ポット・スタックから戦略分布を取得し、
results/ に集約結果を保存する。

使い方:
    python3 scripts/gto_query_volume4.py --task 103
    python3 scripts/gto_query_volume4.py --task 106 --limit 5  # デバッグ
    python3 scripts/gto_query_volume4.py --task all
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

REPO = Path(__file__).resolve().parents[1]
SCEN_ROOT = REPO / "knowledges" / "volume4" / "scenarios"
RES_ROOT = REPO / "knowledges" / "volume4" / "results"

DISTILL_DIR = Path.home() / "poker-distill"
GTO_QUERY = DISTILL_DIR / "training" / "gto_query.py"

# poker-gto の preset_ranges.rs から抽出した文字列レンジ
PRESET_RANGES = {
    "BtnOpen100bb": "22+, A2s+, K2s+, Q4s+, J6s+, T6s+, 96s+, 85s+, 75s+, 65s, 54s, "
                    "A2o+, K8o+, Q9o+, J8o+, T8o+, 98o, 87o",
    "CoOpen100bb": "22+, A2s+, K5s+, Q8s+, J8s+, T8s+, 98s, 87s, 76s, 65s, "
                   "A5o+, KTo+, QTo+, JTo",
    "UtgOpen100bb": "22+, ATs+, KTs+, QTs+, JTs, AJo+, KQo",
    "BbDefendVsBtn": "JJ-22, AQs-A2s, K8s+, Q2s+, J4s+, T5s+, 95s+, 85s+, 75s+, 64s+, "
                     "53s+, 43s, AQo-A2o, KTo+, Q8o+, J8o+, T8o+, 98o, 87o, 76o, 65o",
    "BbDefendVsCo": "22+, A2s+, K5s+, Q7s+, J8s+, T8s+, 97s+, 87s, 76s, 65s, "
                    "A7o+, KTo+, QTo+, JTo",
    "Sb3betVsBtn": "JJ+, AKs, A5s, A4s, AKo",
    "Bb3betVsBtn": "QQ+, AKs, AKo",
    "BtnCallVsSb3bet": "22-99, AQs, AJs, ATs, A5s, KQs, KJs, QJs, JTs, T9s, 98s, AQo",
    "Btn4betVsSb3bet": "QQ+, AKs, A5s, AKo",
}

# ---------------------------------------------------------------------------
# scenario の preset 解決
# ---------------------------------------------------------------------------

def resolve_range(range_obj: Any) -> str:
    """scenario JSON の range フィールドを文字列に展開する."""
    if isinstance(range_obj, str):
        return range_obj
    if isinstance(range_obj, dict):
        if "preset" in range_obj:
            preset = range_obj["preset"]
            if preset not in PRESET_RANGES:
                raise ValueError(f"未知の preset: {preset}")
            return PRESET_RANGES[preset]
        if "expr" in range_obj:
            return range_obj["expr"]
    raise ValueError(f"未対応の range 形式: {range_obj!r}")


def load_scenario(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# gto_query.py 呼び出し
# ---------------------------------------------------------------------------

@dataclass
class ComboStrategy:
    combo: str
    fold: float
    check_call: float
    bet_small: float
    bet_large: float
    allin: float

    @property
    def total_bet(self) -> float:
        return self.bet_small + self.bet_large + self.allin

    @property
    def best(self) -> str:
        actions = [
            ("FOLD", self.fold),
            ("CHECK_CALL", self.check_call),
            ("BET_SMALL", self.bet_small),
            ("BET_LARGE", self.bet_large),
            ("ALLIN", self.allin),
        ]
        return max(actions, key=lambda x: x[1])[0]


def call_gto_query(
    board: List[str],
    ip_range: str,
    oop_range: str,
    pot: float,
    stack: float,
    player: int = 1,
    street: int = 2,
    facing_bet: float = 0.0,
) -> List[ComboStrategy]:
    """gto_query.py を呼び出して combo 別戦略を取得."""
    cmd = [
        sys.executable,
        str(GTO_QUERY),
        "--board", ",".join(board),
        "--ip-range", ip_range,
        "--oop-range", oop_range,
        "--pot", str(pot),
        "--stack", str(stack),
        "--player", str(player),
        "--street", str(street),
        "--format", "csv",
    ]
    if facing_bet > 0:
        cmd += ["--facing-bet", str(facing_bet)]

    proc = subprocess.run(
        cmd, capture_output=True, text=True, cwd=DISTILL_DIR, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gto_query.py 失敗: {proc.stderr[:500]}")

    strategies: List[ComboStrategy] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("combo"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 6:
            continue
        try:
            strategies.append(ComboStrategy(
                combo=parts[0],
                fold=float(parts[1]),
                check_call=float(parts[2]),
                bet_small=float(parts[3]),
                bet_large=float(parts[4]),
                allin=float(parts[5]),
            ))
        except ValueError:
            continue
    return strategies


# ---------------------------------------------------------------------------
# 集約: コンボの value/bluff 分類（簡易）
# ---------------------------------------------------------------------------

RANK_VAL = {r: i for i, r in enumerate("23456789TJQKA", start=2)}


def classify_combo(combo: str, board: List[str]) -> str:
    """combo を value / bluff / mid に簡易分類する.

    - リバー時点のハンド強度をざっくり分類:
      - セット以上 / オーバーペア / TPTK → value
      - ペアなし & ハイカードなし → bluff
      - それ以外 → mid (TP weak kicker, セカンドペア等)
    """
    if len(combo) != 4:
        return "mid"
    c1_rank, c1_suit = combo[0], combo[1]
    c2_rank, c2_suit = combo[2], combo[3]
    board_ranks = [c[0] for c in board]
    board_suits = [c[1] for c in board]

    rank_counts: Dict[str, int] = defaultdict(int)
    for r in board_ranks:
        rank_counts[r] += 1
    rank_counts[c1_rank] += 1
    rank_counts[c2_rank] += 1

    # セット以上判定
    max_count = max(rank_counts.values())
    if max_count >= 3:
        # トリップス／セット／フルハウス／クアッズ
        return "value"

    # ストレート / フラッシュなどは省略（簡易判定）

    # ペア判定
    pocket_pair = c1_rank == c2_rank
    has_pair = (rank_counts[c1_rank] >= 2 or rank_counts[c2_rank] >= 2)

    top_board_rank = max(board_ranks, key=lambda r: RANK_VAL[r])

    if pocket_pair:
        rank_val = RANK_VAL[c1_rank]
        if rank_val > RANK_VAL[top_board_rank]:
            return "value"  # オーバーペア
        return "mid"

    if has_pair:
        # トップペア判定
        paired_rank = c1_rank if rank_counts[c1_rank] >= 2 else c2_rank
        if paired_rank == top_board_rank:
            kicker = c2_rank if paired_rank == c1_rank else c1_rank
            if RANK_VAL[kicker] >= RANK_VAL["T"]:
                return "value"  # TPGK / TPTK
            return "mid"  # TP weak kicker
        return "mid"  # セカンドペア以下

    # ペアなし
    high = max(c1_rank, c2_rank, key=lambda r: RANK_VAL[r])
    if RANK_VAL[high] >= RANK_VAL["A"]:
        return "mid"  # A high
    return "bluff"


# ---------------------------------------------------------------------------
# タスク別の集約ロジック
# ---------------------------------------------------------------------------

@dataclass
class ScenarioResult:
    scenario_id: str
    board: List[str]
    bet_freq_total: float = 0.0
    bet_freq_value: float = 0.0
    bet_freq_bluff: float = 0.0
    bet_freq_mid: float = 0.0
    fold_freq: float = 0.0
    check_call_freq: float = 0.0
    combos_total: int = 0
    extra: Dict[str, Any] = field(default_factory=dict)


def aggregate_strategies(
    strategies: List[ComboStrategy], board: List[str]
) -> ScenarioResult:
    """combo 別戦略 → シナリオ集計."""
    result = ScenarioResult(scenario_id="", board=board)
    result.combos_total = len(strategies)
    if not strategies:
        return result

    classes = {"value": 0.0, "bluff": 0.0, "mid": 0.0}
    bet_classes = {"value": 0.0, "bluff": 0.0, "mid": 0.0}
    sum_fold = sum_cc = sum_bs = sum_bl = sum_ai = 0.0
    for s in strategies:
        cls = classify_combo(s.combo, board)
        classes[cls] += 1
        bet_classes[cls] += s.total_bet
        sum_fold += s.fold
        sum_cc += s.check_call
        sum_bs += s.bet_small
        sum_bl += s.bet_large
        sum_ai += s.allin

    n = len(strategies)
    result.fold_freq = sum_fold / n
    result.check_call_freq = sum_cc / n
    result.bet_freq_total = (sum_bs + sum_bl + sum_ai) / n
    result.bet_freq_value = bet_classes["value"] / max(1, classes["value"]) if classes["value"] else 0
    result.bet_freq_bluff = bet_classes["bluff"] / max(1, classes["bluff"]) if classes["bluff"] else 0
    result.bet_freq_mid = bet_classes["mid"] / max(1, classes["mid"]) if classes["mid"] else 0
    result.extra = {
        "bet_small_total": sum_bs / n,
        "bet_large_total": sum_bl / n,
        "allin_total": sum_ai / n,
        "combos_value": int(classes["value"]),
        "combos_bluff": int(classes["bluff"]),
        "combos_mid": int(classes["mid"]),
    }
    return result


# ---------------------------------------------------------------------------
# シナリオ実行
# ---------------------------------------------------------------------------

def run_scenario(scen_path: Path, task: str) -> Optional[Dict[str, Any]]:
    scen = load_scenario(scen_path)
    scenario_id = scen["scenario_id"]
    board = scen["board"]
    pot = scen["pot_bb"]
    stack = scen["effective_stack_bb"]
    hero_pos = scen.get("hero_position", "BTN")
    hero_range = resolve_range(scen["hero_range"])
    villain_range = resolve_range(scen["villain_range"])

    # IP/OOP のレンジ割り当て
    if hero_pos in ("BB", "SB"):
        ip_range, oop_range = villain_range, hero_range
        hero_is_ip = False
    else:
        ip_range, oop_range = hero_range, villain_range
        hero_is_ip = True

    # ストリート判定
    n_board = len(board)
    street = {3: 0, 4: 1, 5: 2}.get(n_board, 0)

    # タスク別に query 戦略を決定
    bet_sizes = scen.get("bet_sizes_to_evaluate", [])
    bet_size = bet_sizes[0] if bet_sizes else 0.0

    queries = []
    if task == "103":
        # リバー V:B: IP 先手の bet 戦略を取る
        queries.append(("ip_first", 1, 0.0))
    elif task == "106":
        # リバー MDF: OOP が IP のベットに直面 → 防御率を見る
        queries.append(("oop_facing_bet", 0, bet_size))
    elif task == "105":
        # ブロッカー: IP 先手の戦略 + OOP 防御の両方
        queries.append(("ip_first", 1, 0.0))
        queries.append(("oop_facing_bet", 0, max(bet_size, 0.5)))
    elif task == "108":
        # フック論点: シナリオ依存。IP 先手をベースにする
        queries.append(("ip_first", 1, 0.0))

    results = {}
    for label, player, facing_bet in queries:
        try:
            strategies = call_gto_query(
                board=board, ip_range=ip_range, oop_range=oop_range,
                pot=pot, stack=stack, player=player, street=street,
                facing_bet=facing_bet,
            )
        except Exception as e:
            results[label] = {"error": str(e)}
            continue
        agg = aggregate_strategies(strategies, board)
        results[label] = {
            "fold_freq": round(agg.fold_freq, 4),
            "check_call_freq": round(agg.check_call_freq, 4),
            "bet_freq_total": round(agg.bet_freq_total, 4),
            "bet_freq_by_class": {
                "value": round(agg.bet_freq_value, 4),
                "mid": round(agg.bet_freq_mid, 4),
                "bluff": round(agg.bet_freq_bluff, 4),
            },
            **agg.extra,
            "combos_total": agg.combos_total,
        }

    return {
        "scenario_id": scenario_id,
        "board": board,
        "pot_bb": pot,
        "effective_stack_bb": stack,
        "street": street,
        "hero_position": hero_pos,
        "hero_is_ip": hero_is_ip,
        "bet_size": bet_size,
        "summary": results,
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def run_task(task: str, limit: Optional[int] = None) -> None:
    scen_dir = SCEN_ROOT / task
    if not scen_dir.exists():
        print(f"❌ scenarios/{task}/ が存在しません", file=sys.stderr)
        return

    out_dir = RES_ROOT / task
    out_dir.mkdir(parents=True, exist_ok=True)

    scen_files = sorted(scen_dir.glob("*.json"))
    scen_files = [p for p in scen_files if p.stem != "index"]
    if limit:
        scen_files = scen_files[:limit]

    print(f"\n=== Task #{task}: {len(scen_files)} シナリオ ===")
    summaries: List[Dict[str, Any]] = []
    for i, scen_path in enumerate(scen_files, 1):
        print(f"  [{i}/{len(scen_files)}] {scen_path.stem}", end=" ... ", flush=True)
        result = run_scenario(scen_path, task)
        if result is None:
            print("skip")
            continue
        if "error" in result:
            print(f"ERROR: {result['error'][:80]}")
        else:
            # 最初の query 結果でサマリ表示
            first_key = next(iter(result["summary"]))
            s = result["summary"][first_key]
            if "error" in s:
                print(f"ERROR: {s['error'][:60]}")
            else:
                print(f"[{first_key}] bet={s['bet_freq_total']:.2f} fold={s['fold_freq']:.2f}")
        out_path = out_dir / f"{scen_path.stem}.json"
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        summaries.append(result)

    # サマリ JSON
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps({
        "task": task,
        "n_scenarios": len(summaries),
        "scenarios": summaries,
    }, ensure_ascii=False, indent=2))
    print(f"  → {out_dir}/ に {len(summaries)} ファイル + summary.json 出力")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--task", required=True, help="103 / 105 / 106 / 108 / all")
    p.add_argument("--limit", type=int, help="最初の N シナリオのみ実行")
    args = p.parse_args()

    if args.task == "all":
        for t in ["103", "105", "106", "108"]:
            run_task(t, args.limit)
    else:
        run_task(args.task, args.limit)


if __name__ == "__main__":
    main()
