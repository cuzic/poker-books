#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Extended defense-focused spot design with multiple bet sizes and stack depths.

Targets: ~1000 defense spots covering
  - 4 defense contexts (cbet_def, 2nd_def_call, probe_def, 2nd_def_xc)
  - 3 bet sizes (33%, 50%, 110%pot)
  - 2 stack depths (100bb, 200bb)
  - 3 preflop lines (BTN/CO/HJ vs BB)
  - 12 representative boards

Output: scripts/three_class_model/designed_defense.csv
"""
from __future__ import annotations

import csv
from pathlib import Path

OUT = Path(__file__).parent / "designed_defense.csv"

# ── Board library (12 representative, balanced across families) ──
BOARDS = {
    "dry_high":      ["Ks7d2c", "Qh8d3s"],
    "dynamic":       ["Ts9d7c", "9h8d6c"],
    "dynamic_2tone": ["Ts9s8d", "9s8s6d"],
    "low_dry":       ["8s5h2c", "9c6d4s"],
    "monotone":      ["KsQsJs", "Ts8s5s"],
    "paired":        ["Ks7d7c", "9s9d4c"],
}

TURN_CARDS = {
    "dry_high": "Th",
    "dynamic": "2c",
    "dynamic_2tone": "2h",
    "low_dry": "Td",
    "monotone": "2d",
    "paired": "Th",
}

# ── Preflop openings ──
PREFLOP_LINES = [
    ("F-F-F-R2.5-F-C", "BTN", "BB", "BTNvBB"),
    ("F-F-R2.3-F-F-C", "CO", "BB", "COvBB"),
    ("F-R2.2-F-F-F-C", "HJ", "BB", "HJvBB"),
]

# Pot sizes (approximate, MTT 200bb / Cash 100bb)
# BTN-vs-BB MTT 200bb: pot ≈ 6.25 chips
# Need to use actual solver-tree sizes. Common solver sizes are 33% (R2.0-2.1) and overbet.

# For MTT 200bb (depth=200.125), flop pot ≈ 6.25
# Sizes the solver knows: R2.1 (33%), R5.7 (~90%/overbet pattern), R26.x (huge over)
# For Cash 100bb (depth=100), flop pot ≈ 5.65
# Sizes: R1.8 (33%), R5.5 (~100%), R17 (~300%)

SIZE_CONFIGS = [
    # (gametype, depth, stacks, sizes per street)
    # ── MTT 200bb ──
    {
        "name": "MTT_200bb",
        "gametype": "MTT6mSimple",
        "depth": "200.125",
        "stacks": "200.125-200.125-200.125-200.125-200.125-200.125",
        "flop_small": "R2.1",    # ~33% pot
        "flop_large": "R5.7",    # ~90% pot (closer to "100%" tier)
        "turn_small_pot_after_xrxc": "R5.2",  # 50% pot ~5.2 chips on 10.45 pot
        "turn_large": "R7.8",    # 75% pot
    },
    # ── Cash 100bb (no equity_buckets, separate analysis) ──
    {
        "name": "Cash_100bb",
        "gametype": "Cash6mGeneral_6mNL25R25",
        "depth": "100",
        "stacks": "",
        "flop_small": "R1.8",
        "flop_large": "R5.5",
        "turn_small_pot_after_xrxc": "R4.5",
        "turn_large": "R7",
    },
]

# ── Decision contexts (defense only — primary need) ──
DECISION_CONTEXTS = [
    # name, flop_actions_template, turn_actions_template, label
    ("flop_cbet_def_small",  "X-{SMALL}",        "", "Face flop small cbet"),
    ("flop_cbet_def_large",  "X-{LARGE}",        "", "Face flop large cbet"),
    ("turn_2nd_def_small",   "X-{SMALL}-C",      "X-{T_SMALL}", "Turn defense vs 50%"),
    ("turn_2nd_def_large",   "X-{SMALL}-C",      "X-{T_LARGE}", "Turn defense vs large"),
    ("turn_probe_def",       "X-X",              "X-{T_SMALL}", "Turn defense vs probe"),
]


def generate_spots() -> list[dict]:
    spots = []
    counter = 1
    for size_cfg in SIZE_CONFIGS:
        for preflop_line, opener, caller, label in PREFLOP_LINES:
            for ctx_name, flop_acts_tpl, turn_acts_tpl, doc in DECISION_CONTEXTS:
                for bf, boards in BOARDS.items():
                    for board in boards:
                        # Resolve sizes
                        flop_acts = flop_acts_tpl.replace("{SMALL}", size_cfg["flop_small"]).replace("{LARGE}", size_cfg["flop_large"])
                        turn_acts = turn_acts_tpl.replace("{T_SMALL}", size_cfg["turn_small_pot_after_xrxc"]).replace("{T_LARGE}", size_cfg["turn_large"])
                        # Add turn card if turn line
                        full_board = board
                        if "turn" in ctx_name:
                            tc = TURN_CARDS.get(bf, "2h")
                            full_board = board + tc

                        spot_id = f"E{counter:04d}"
                        spots.append({
                            "id": spot_id,
                            "topic": f"design_{ctx_name}_{size_cfg['name']}",
                            "gametype": size_cfg["gametype"],
                            "depth": size_cfg["depth"],
                            "stacks": size_cfg["stacks"],
                            "preflop_actions": preflop_line,
                            "flop_actions": flop_acts,
                            "turn_actions": turn_acts,
                            "river_actions": "",
                            "board": full_board,
                            "ctx": ctx_name,
                            "board_family": bf,
                            "opener": opener,
                            "caller": caller,
                            "preflop_label": label,
                            "size_config": size_cfg["name"],
                            "doc": doc,
                            "note": f"{ctx_name} {bf} {opener}v{caller} {size_cfg['name']}",
                        })
                        counter += 1
    return spots


def main() -> int:
    spots = generate_spots()
    print(f"Generated {len(spots)} defense spots")
    from collections import Counter
    print("\nPer-context:")
    for k, n in Counter(s["ctx"] for s in spots).most_common():
        print(f"  {k:35s} {n}")
    print("\nPer-board-family:")
    for k, n in Counter(s["board_family"] for s in spots).most_common():
        print(f"  {k:20s} {n}")
    print("\nPer-game-type:")
    for k, n in Counter(s["size_config"] for s in spots).most_common():
        print(f"  {k:15s} {n}")

    cols = list(spots[0].keys())
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for s in spots:
            w.writerow(s)
    print(f"\nWrote → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
