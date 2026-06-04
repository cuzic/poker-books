#!/usr/bin/env python3
"""
deep_inventory.py — 既存研究データを徹底的に深堀り inventory

ファイル名だけでなく中身の game.preflop_actions / players_info / flop_actions まで読み、
以下を抽出:
  - 誰がオープナーか (UTG / HJ / CO / BTN / SB)
  - 誰が defender か (BB / SB / IP)
  - 何 depth (stacks から)
  - flop_actions が「X→bet」(BB check → BTN cbet) か「bet」(BB donk lead) か
  - players_info で player count (6m / 9m)
  - SPR estimate
"""
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path.home() / "poker-books"


def analyze_file(p: Path) -> dict | None:
    try:
        with open(p) as f:
            if p.suffix == ".jsonl":
                line = f.readline()
                data = json.loads(line) if line else {}
            else:
                data = json.load(f)
    except Exception:
        return None

    info = {
        "path": str(p.relative_to(ROOT)),
        "size_kb": p.stat().st_size // 1024,
    }

    # game.players[].chips_on_table から actions 構造を推定
    game = data.get("game", {}) if isinstance(data, dict) else {}
    players = game.get("players", []) if isinstance(game, dict) else []
    info["players_chips"] = {p.get("position", "?"): p.get("chips_on_table", "0") for p in players}
    info["players_stacks"] = {p.get("position", "?"): p.get("stack", "?") for p in players}
    info["players_folded"] = {p.get("position", "?"): p.get("is_folded", False) for p in players}

    # depth (max stack)
    try:
        stacks = [float(p.get("stack", "0")) for p in players if p.get("stack")]
        info["depth"] = max(stacks) if stacks else 0
    except (ValueError, TypeError):
        info["depth"] = 0

    # board / community cards
    info["board"] = game.get("board", "") if isinstance(game, dict) else ""
    # board の長さで phase 判定
    board_len = len(info["board"]) if info["board"] else 0
    if board_len >= 8:  # 5+ cards = river (river card pos may vary)
        info["phase"] = "river"
    elif board_len >= 6:  # 4 cards = turn
        info["phase"] = "turn"
    elif board_len >= 6:  # 3 cards = flop  (board "Ks7d2c" = 6 chars)
        info["phase"] = "flop"
    elif board_len == 0:
        info["phase"] = "preflop"
    else:
        info["phase"] = "?"

    # players_info to count players
    pi = data.get("players_info", []) if isinstance(data, dict) else []
    info["n_players"] = len(pi) if isinstance(pi, list) else 0
    info["players_positions"] = [p.get("position", "?") for p in pi] if pi else []

    # action_solutions の actor position
    acts = data.get("action_solutions", []) if isinstance(data, dict) else []
    if acts:
        first = acts[0]
        info["actor_position"] = first.get("action", {}).get("position", "")
        info["action_types"] = sorted(set(a.get("action", {}).get("code", "") for a in acts))
        info["next_position"] = first.get("action", {}).get("next_position", "")

    # ハンド数推定 (strategy[0] の長さ)
    if acts and "strategy" in acts[0]:
        info["strategy_len"] = len(acts[0]["strategy"])
    else:
        info["strategy_len"] = 0

    return info


def parse_preflop_from_chips(players_chips: dict, players_folded: dict) -> dict:
    """各プレイヤーの chips_on_table から preflop 構造を推定。

    例: BTN=2, BB=1, SB=0.5, 他=0 → BTN open 2BB, SB fold, BB のターン
    """
    if not players_chips:
        return {"opener": "?", "n_callers": 0, "n_raises": 0, "is_3bet_pot": False, "is_4bet_pot": False}

    POSITIONS_6M = ["UTG", "HJ", "CO", "BTN", "SB", "BB"]
    # 各プレイヤーの chips を float に
    chips = {}
    for pos in POSITIONS_6M:
        v = players_chips.get(pos, "0")
        try:
            chips[pos] = float(v)
        except (ValueError, TypeError):
            chips[pos] = 0.0

    # blinds 除外 (SB=0.5、BB=1)
    # 0 = fold or no action, 1 = BB blind only, > 1 = action
    # SB は base 0.5、それ以上は call/raise
    # BB は base 1、それ以上は call/raise
    # 他 (UTG/HJ/CO/BTN) は base 0、> 0 で action

    # raise 連 (chips が連続的に増えていく)
    # 最初に > 0 で base を超えるプレイヤーが opener
    opener = "?"
    n_callers = 0
    n_raises = 0  # number of raises (open is 1st raise, 3-bet is 2nd, 4-bet is 3rd)

    max_chips = 0
    raises_seq = []  # list of (position, chips)
    for pos in POSITIONS_6M:
        base = 0.5 if pos == "SB" else (1.0 if pos == "BB" else 0.0)
        c = chips[pos]
        if c > base + 0.01:  # acted (not just blind)
            if c > max_chips:
                # This is a raise
                opener = opener if opener != "?" else pos
                n_raises += 1
                max_chips = c
                raises_seq.append((pos, c))
            elif abs(c - max_chips) < 0.01:
                # call (matched the raise)
                n_callers += 1

    is_3bet_pot = n_raises >= 2
    is_4bet_pot = n_raises >= 3
    return {
        "opener": opener,
        "n_callers": n_callers,
        "n_raises": n_raises,
        "is_3bet_pot": is_3bet_pot,
        "is_4bet_pot": is_4bet_pot,
        "raises_seq": raises_seq,
    }


def main():
    print("# 深堀り inventory: 全 findings ファイルの実際の中身を抽出")
    print()

    # 全ファイルをスキャン
    by_scenario = defaultdict(list)
    by_donk = defaultdict(list)
    by_depth = defaultdict(int)
    by_phase = defaultdict(int)
    by_actor = defaultdict(int)
    by_opener = defaultdict(int)
    by_player_count = defaultdict(int)
    by_3bp_4bp = defaultdict(int)

    paths = []
    for d in [ROOT/"vol2-cash-postflop"/"findings",
              ROOT/"vol3-mtt-postflop"/"findings",
              ROOT/"research"/"v3-additional"/"findings"]:
        if d.exists():
            paths.extend(d.rglob("*.json"))
            paths.extend(d.rglob("*.jsonl"))

    # ファイル名 / ディレクトリ名から opener/defender を補強推定
    def infer_from_path(p: Path) -> tuple[str, str]:
        """パスから (opener, defender) を推定。"""
        full = str(p)
        # ディレクトリ内に "_BB_" / "BTN_BB" 等のパターン
        # ファイル名 BTN_BB_xxx → opener=BTN, defender=BB
        name = p.name
        parts_in_name = name.replace(".json", "").replace(".jsonl", "").split("_")
        POSITIONS = {"UTG", "HJ", "CO", "BTN", "SB", "BB", "LJ"}
        positions_in_name = [x for x in parts_in_name if x in POSITIONS]
        if len(positions_in_name) >= 2:
            return (positions_in_name[0], positions_in_name[1])
        # ディレクトリ名から
        dir_name = p.parent.name
        if "BTN_BB" in dir_name or "btn_bb" in dir_name.lower():
            return ("BTN", "BB")
        if "CO_BB" in dir_name or "co_bb" in dir_name.lower():
            return ("CO", "BB")
        if "HJ_BB" in dir_name or "hj_bb" in dir_name.lower():
            return ("HJ", "BB")
        if "_btn_" in dir_name.lower():
            return ("BTN", "?")
        if "_bb_" in dir_name.lower():
            return ("?", "BB")
        return ("?", "?")

    total = 0
    failed = 0
    for p in paths:
        info = analyze_file(p)
        if not info:
            failed += 1
            continue
        total += 1

        # parse preflop from chips
        pf_info = parse_preflop_from_chips(
            info.get("players_chips", {}),
            info.get("players_folded", {}),
        )
        # fallback from filename / dir
        if pf_info["opener"] == "?":
            fn_opener, fn_defender = infer_from_path(p)
            if fn_opener != "?":
                pf_info["opener"] = fn_opener
        opener = pf_info["opener"]
        n_callers = pf_info["n_callers"]
        actor = info.get("actor_position", "?")

        # depth (gametype 経由含めて推定)
        depth = info.get("depth", "")
        if not depth:
            gt = info.get("gametype", "")
            if "NL100" in gt: depth = "100"
            elif "NL50" in gt: depth = "50"
            elif "NL25" in gt: depth = "25"
        depth_str = str(depth).split(".")[0] if depth else "?"

        # キーシナリオ集計
        if pf_info["is_4bet_pot"]:
            by_3bp_4bp[f"4BP {opener}-{actor}"] += 1
        elif pf_info["is_3bet_pot"]:
            by_3bp_4bp[f"3BP {opener}-{actor}"] += 1

        scenario_key = f"{opener} open → {actor} act (N_callers={n_callers}, depth={depth_str})"
        by_scenario[scenario_key].append(info["path"])
        by_phase[info["phase"]] += 1
        by_actor[actor] += 1
        by_opener[opener] += 1
        by_depth[depth_str] += 1
        by_player_count[info.get("n_players", "?")] += 1

        # Donk detection: postflop + actor は OOP (BB)、かつ flop_actions が "" (まだ no bet)
        # → BB が flop で先手 (donk lead)
        if info["phase"] == "flop" and not info["flop_actions"] and actor == "BB":
            # BB が先手で flop に立っている = donk option
            by_donk["BB donk option (flop_actions=空、BB の番)"].append(info["path"])
        if info["phase"] == "turn" and actor == "BB":
            by_donk["BB lead at turn"].append(info["path"])
        if info["phase"] == "river" and actor == "BB":
            by_donk["BB lead at river"].append(info["path"])

    print(f"**スキャン完了: 成功 {total} / 失敗 {failed} ファイル**")
    print()

    print("## Phase 別")
    print()
    print("| Phase | ファイル数 |")
    print("|-------|---------|")
    for k, v in sorted(by_phase.items(), key=lambda x: -x[1]):
        print(f"| {k} | {v} |")
    print()

    print("## Depth 別")
    print()
    print("| Depth | ファイル数 |")
    print("|-------|---------|")
    for k, v in sorted(by_depth.items(), key=lambda x: -x[1]):
        print(f"| {k} bb | {v} |")
    print()

    print("## Actor 別 (誰の番か)")
    print()
    print("| Actor | ファイル数 |")
    print("|-------|---------|")
    for k, v in sorted(by_actor.items(), key=lambda x: -x[1]):
        print(f"| {k} | {v} |")
    print()

    print("## Opener 別 (誰がオープンしたか)")
    print()
    print("| Opener | ファイル数 |")
    print("|--------|---------|")
    for k, v in sorted(by_opener.items(), key=lambda x: -x[1]):
        print(f"| {k} | {v} |")
    print()

    print("## Player Count")
    print()
    for k, v in sorted(by_player_count.items()):
        print(f"- {k} players: {v} files")
    print()

    print("## 3BP / 4BP シナリオ")
    print()
    for k, v in sorted(by_3bp_4bp.items(), key=lambda x: -x[1]):
        print(f"- {k}: {v} files")
    print()

    print("## Donk / lead シナリオ (BB が postflop で先手)")
    print()
    for k, files in by_donk.items():
        print(f"- **{k}**: {len(files)} files")
        for f in files[:3]:
            print(f"    - {f}")
        if len(files) > 3:
            print(f"    - ... ({len(files)-3} more)")
    print()

    print("## シナリオパターン TOP 30")
    print()
    print("| シナリオ | ファイル数 | 例 |")
    print("|---------|---------|----|")
    for scenario, files in sorted(by_scenario.items(), key=lambda x: -len(x[1]))[:30]:
        sample = files[0].split("/")[-1] if files else ""
        print(f"| `{scenario}` | {len(files)} | `{sample}` |")
    print()


if __name__ == "__main__":
    main()
