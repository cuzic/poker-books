#!/usr/bin/env python3
"""
attack_vs_defense_coverage.py — attack(cbet) と defense の網羅性検証

postflop の各 spot で:
  - attack (誰かが先手 bet するか): pot に additional chips が乗っていない → 現 actor が先手
  - defense (誰かの bet を受けて反応): pot に bet 額が乗っている → actor は call/raise/fold

各 phase × actor × depth × scenario で attack/defense の集計を取る。
SB postflop の網羅性も同時に確認。
"""
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path.home() / "poker-books"


def analyze_file(p: Path) -> dict | None:
    try:
        with open(p) as f:
            data = json.load(f) if p.suffix == ".json" else json.loads(f.readline())
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    game = data.get("game", {})
    if not isinstance(game, dict):
        return None
    players = game.get("players", [])
    acts = data.get("action_solutions", [])

    chips = {p.get("position", "?"): float(p.get("chips_on_table", "0") or 0) for p in players}
    stacks_orig = {p.get("position", "?"): float(p.get("stack", "0") or 0) for p in players}
    actor = acts[0].get("action", {}).get("position", "?") if acts else "?"
    action_codes = [a.get("action", {}).get("code", "") for a in acts]
    board = game.get("board", "")

    blen = len(board) if board else 0
    phase = "preflop" if blen == 0 else ("flop" if blen == 6 else ("turn" if blen == 8 else ("river" if blen >= 10 else "?")))

    depth = int(max(stacks_orig.values())) if stacks_orig else 0

    # attack vs defense: action codes が含むものから判別
    # - 含む "X" (check) → 現 actor は先手 (check option あり) = attack 候補 (cbet するか check するか)
    # - 含む "F" (fold) → 現 actor は relief (誰かの bet を受けている) = defense
    # - action codes が "C" "R" "F" のみ で "X" がない → defense (raise を受けている)
    # - action codes が "X" "B" のみ → attack (まだ bet されていない)
    has_check = "X" in action_codes
    has_fold = "F" in action_codes
    has_call = "C" in action_codes
    has_bet_only = any(a.startswith("B") for a in action_codes)

    if has_fold and not has_check:
        spot_type = "defense"
    elif has_check and not has_fold:
        spot_type = "attack"
    elif has_check and has_fold:
        spot_type = "mixed"  # check-call/check-raise/check-fold オプションあり
    elif has_bet_only:
        spot_type = "attack"
    else:
        spot_type = "?"

    return {
        "path": str(p.relative_to(ROOT)),
        "phase": phase,
        "depth": depth,
        "actor": actor,
        "spot_type": spot_type,
        "actions": ",".join(action_codes[:6]),
        "sb_chips": chips.get("SB", 0),
        "bb_chips": chips.get("BB", 0),
    }


def main():
    paths = []
    for d in [ROOT/"vol2-cash-postflop"/"findings",
              ROOT/"vol3-mtt-postflop"/"findings",
              ROOT/"research"/"v3-additional"/"findings"]:
        if d.exists():
            paths.extend(d.rglob("*.json"))

    all_info = []
    for p in paths:
        info = analyze_file(p)
        if not info or info["phase"] in ("preflop", "?"):
            continue
        all_info.append(info)

    print("# attack / defense / mixed の網羅性検証")
    print()
    print(f"**Postflop ファイル数**: {len(all_info)}")
    print()

    # 全体集計
    print("## 1. spot_type × actor 集計")
    print()
    by_type_actor = defaultdict(int)
    for f in all_info:
        by_type_actor[(f["spot_type"], f["actor"])] += 1

    actors = sorted({f["actor"] for f in all_info})
    types = ["attack", "defense", "mixed", "?"]
    print("| Actor | attack | defense | mixed | ? | 合計 |")
    print("|-------|--------|---------|-------|---|------|")
    for actor in actors:
        row = [actor]
        total = 0
        for t in types:
            n = by_type_actor.get((t, actor), 0)
            row.append(str(n))
            total += n
        row.append(str(total))
        print(f"| {' | '.join(row)} |")
    print()

    # ── 2. SB が actor のシナリオを詳細 ──
    sb_actor_files = [f for f in all_info if f["actor"] == "SB"]
    print(f"## 2. SB が actor (postflop)")
    print()
    print(f"ファイル数: {len(sb_actor_files)}")
    by_phase_depth = defaultdict(lambda: defaultdict(int))
    for f in sb_actor_files:
        by_phase_depth[(f["phase"], f["depth"])][f["spot_type"]] += 1
    print()
    print("| Phase | Depth | attack | defense | mixed | ? |")
    print("|-------|-------|--------|---------|-------|---|")
    for (phase, depth), st_counts in sorted(by_phase_depth.items()):
        print(f"| {phase} | {depth}bb | {st_counts.get('attack',0)} | {st_counts.get('defense',0)} | {st_counts.get('mixed',0)} | {st_counts.get('?',0)} |")
    print()

    # ── 3. SB が関与する全ファイル ──
    sb_involved = [f for f in all_info if f["sb_chips"] > 0.5]
    print(f"## 3. SB が pot に参加 (postflop、actor は問わない)")
    print()
    print(f"ファイル数: {len(sb_involved)}")
    # SB chips の値別 (0.5 = blind のみ、1+ = call/raise した、複数 = raise pot)
    by_sb_chips = defaultdict(int)
    for f in sb_involved:
        v = round(f["sb_chips"], 1)
        by_sb_chips[v] += 1
    print()
    print("| SB chips_on_table | ファイル数 | 推定 |")
    print("|-------------------|---------|------|")
    for v, n in sorted(by_sb_chips.items())[:20]:
        hint = ""
        if v == 0.5: hint = "blind のみ (preflop で fold)"
        elif v == 1.0: hint = "limp / SB call"
        elif 2 <= v <= 3: hint = "SB open"
        elif 5 <= v <= 10: hint = "SB 3-bet"
        elif v > 20: hint = "SB 4-bet / 5-bet / pot で deep"
        print(f"| {v} | {n} | {hint} |")
    print()

    # ── 4. SB-BB BvB SRP postflop (SB chips ≈ 2-3, BB matched) ──
    sb_bb_srp = [f for f in all_info
                 if 2.0 <= f["sb_chips"] <= 3.5
                 and f["bb_chips"] >= 2.0
                 and abs(f["sb_chips"] - f["bb_chips"]) < 1.0]
    print(f"## 4. SB-BB BvB SRP postflop (SB open ~2.5BB, BB call)")
    print()
    print(f"ファイル数: {len(sb_bb_srp)}")
    by_phase_depth2 = defaultdict(lambda: defaultdict(int))
    for f in sb_bb_srp:
        by_phase_depth2[(f["phase"], f["depth"])][f["spot_type"]] += 1
    print()
    print("| Phase | Depth | attack | defense | mixed |")
    print("|-------|-------|--------|---------|-------|")
    for (phase, depth), st_counts in sorted(by_phase_depth2.items()):
        print(f"| {phase} | {depth}bb | {st_counts.get('attack',0)} | {st_counts.get('defense',0)} | {st_counts.get('mixed',0)} |")
    print()

    # ── 5. defense 詳細: 誰の bet を受けているか? ──
    defense_files = [f for f in all_info if f["spot_type"] == "defense"]
    print(f"## 5. defense ファイル ({len(defense_files)})")
    print()
    by_actor_defense = defaultdict(int)
    for f in defense_files:
        by_actor_defense[f["actor"]] += 1
    print("| Defender (actor) | ファイル数 |")
    print("|------------------|---------|")
    for actor, n in sorted(by_actor_defense.items(), key=lambda x: -x[1]):
        print(f"| {actor} | {n} |")
    print()
    by_phase_d = defaultdict(int)
    for f in defense_files:
        by_phase_d[f["phase"]] += 1
    print("| Phase | defense ファイル数 |")
    print("|-------|------------------|")
    for phase, n in sorted(by_phase_d.items()):
        print(f"| {phase} | {n} |")
    print()


if __name__ == "__main__":
    main()
