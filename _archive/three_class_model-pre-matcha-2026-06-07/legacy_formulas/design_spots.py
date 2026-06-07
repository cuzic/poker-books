#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Comprehensive spot design generator.

Produces a CSV of spot definitions covering 4 decision contexts ×
positions × boards × game types. The fetcher reads this CSV.

Decision contexts:
  1. SRP flop CBet (attack)        — opener attacks after caller checks
  2. SRP flop CBet defense          — caller faces CBet
  3. SRP turn 2nd barrel (attack)   — opener fires turn after flop CBet called
  4. SRP turn defense (call/raise)  — caller faces turn bet
  5. SRP turn probe (XX line)       — caller bets turn after flop XX
  6. SRP turn probe defense
  7. 3BP flop CBet (attack)
  8. 3BP flop CBet defense

Boards (18): 3 per board family
  - dry_high:     Ks7d2c, Qh8d3s, Js5c2h
  - dynamic:      Ts9d7c, 9h8d6c, 8c7d5s
  - dynamic_2tone:Ts9s8d, 9s8s6d, 7s6s5d
  - low_dry:      8s5h2c, 9c6d4s, 7h4d2c
  - monotone:     KsQsJs, Ts8s5s, 9s7s4s
  - paired:       Ks7d7c, Th7s7d, 9s9d4c (and KK2: KsKd2c)

Game types:
  - MTT 100bb (preferred — equity_buckets)
  - Cash 100bb NL25 (fallback — no equity_buckets)

Output: scripts/three_class_model/designed_spots.csv
"""
from __future__ import annotations

import csv
from itertools import product
from pathlib import Path

OUT = Path(__file__).parent / "designed_spots.csv"

# ── Board library ──
BOARDS = {
    "dry_high":      ["Ks7d2c", "Qh8d3s", "Js5c2h"],
    "dynamic":       ["Ts9d7c", "9h8d6c", "8c7d5s"],
    "dynamic_2tone": ["Ts9s8d", "9s8s6d", "7s6s5d"],
    "low_dry":       ["8s5h2c", "9c6d4s", "7h4d2c"],
    "monotone":      ["KsQsJs", "Ts8s5s", "9s7s4s"],
    "paired":        ["Ks7d7c", "Th7s7d", "9s9d4c", "KsKd2c"],
}

# Standard turn cards per board family (one representative per family)
TURN_CARDS = {
    "dry_high": "Th",
    "dynamic": "2c",
    "dynamic_2tone": "2h",
    "low_dry": "Td",
    "monotone": "2d",
    "paired": "Th",
}

# ── Position setups ──
# 6max positions in seat order: UTG, HJ, CO, BTN, SB, BB
# stacks string: "STACK-STACK-STACK-STACK-STACK-STACK"
STACK_100BB = "100-100-100-100-100-100"
STACK_MTT_200BB = "200.125-" * 6
STACK_MTT_200BB = STACK_MTT_200BB.rstrip("-")

# Preflop lines (positions abbreviated):
# UTG-HJ-CO-BTN-SB-BB
# F = fold, R<size> = raise, C = call
# RFI 2.5bb, 3bet ~10bb (variable)

POSITION_LINES_SRP_BTN_BB = [
    # 6m BTN open, BB defends — most common SRP
    ("F-F-F-R2.5-F-C", "BTN", "BB"),
    # CO open, BB defends
    ("F-F-R2.3-F-F-C", "CO", "BB"),
    # HJ open, BB defends
    ("F-R2.2-F-F-F-C", "HJ", "BB"),
    # BTN open, SB defends (3bet 100% but we want call line; SB usually 3bets — skip)
]

# ── Game types ──
GAMETYPES = [
    ("MTT6mSimple", STACK_MTT_200BB, "200.125"),  # MTT, 200bb
    # Cash variant added separately if equity_buckets shown unavailable in MTT-only path
]

# ── Decision-context line templates ──
# IMPORTANT: GTO Wizard API uses ABSOLUTE chip sizes that MUST match the solver tree.
# For BTN-vs-BB MTT 200bb (preflop F-F-F-R2.5-F-C):
#   Flop pot = 6.25bb. Solver has R2.1 (33% pot) as small flop CBet
#   After X-R2.1-C, turn pot = 10.45bb. Solver has ... TBD by probe.

DECISION_CONTEXTS = [
    # (name, flop_actions, turn_actions, river_actions, label)
    ("flop_cbet_attack",   "",             "",         "", "IP CBet attack"),
    ("flop_cbet_defense",  "X-R2.1",       "",         "", "Face flop 33% cbet"),
    ("turn_2nd_barrel",    "X-R2.1-C",     "",         "", "Turn 2nd barrel"),
    ("turn_2nd_defense",   "X-R2.1-C",     "X-R5.2",   "", "Turn defense vs 50% barrel"),
    ("turn_probe",         "X-X",          "",         "", "Turn probe after XX"),
    ("turn_probe_defense", "X-X",          "X-R5.2",   "", "Turn defense vs probe"),
]


def generate_spots() -> list[dict]:
    spots = []
    spot_id_counter = 1
    for gt, stacks, depth in GAMETYPES:
        for preflop_line, opener, caller in POSITION_LINES_SRP_BTN_BB:
            for ctx_name, flop_acts, turn_acts, river_acts, _doc in DECISION_CONTEXTS:
                for bf, board_list in BOARDS.items():
                    for board in board_list:
                        # On flop turn-stage contexts, append turn card
                        full_board = board
                        if "turn" in ctx_name:
                            tc = TURN_CARDS.get(bf, "2h")
                            # avoid card conflict
                            if tc[0] in board and tc[1] in board:
                                tc = "Td" if "T" not in board else "9c"
                            full_board = board + tc

                        flop_resolved = flop_acts
                        turn_resolved = turn_acts

                        spot_id = f"D{spot_id_counter:04d}"
                        spots.append({
                            "id": spot_id,
                            "topic": f"design_{ctx_name}",
                            "gametype": gt,
                            "depth": depth,
                            "stacks": stacks,
                            "preflop_actions": preflop_line,
                            "flop_actions": flop_resolved,
                            "turn_actions": turn_resolved,
                            "river_actions": river_acts,
                            "board": full_board,
                            "ctx": ctx_name,
                            "board_family": bf,
                            "opener": opener,
                            "caller": caller,
                            "note": f"{ctx_name} {bf} {opener}v{caller}",
                        })
                        spot_id_counter += 1
    return spots


def main() -> int:
    spots = generate_spots()
    print(f"Generated {len(spots)} spots")

    # Group counts
    from collections import Counter
    print(f"\nPer-context counts:")
    c = Counter(s["ctx"] for s in spots)
    for k, v in c.most_common():
        print(f"  {k:25s} {v}")
    print(f"\nPer-board-family counts:")
    c = Counter(s["board_family"] for s in spots)
    for k, v in c.most_common():
        print(f"  {k:18s} {v}")

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
