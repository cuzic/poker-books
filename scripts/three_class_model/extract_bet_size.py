#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas"]
# ///
"""Extract bet_size info for all spots (both Format A and B), build supplementary CSV.

Per spot:
- board_correct: from game.board (Format A) or _meta.request.board (Format B)
- pot_start: pot at start of current street
- pot_end: pot after the bet was placed (before our action)
- bet_size_chips: the bet amount we are facing (from C action's betsize, or from pot diff)
- bet_size_pot_ratio: bet / pot_start (the canonical 33%, 50%, 75% measure)
- pot_odds: from game.pot_odds
- depth_bb: hero stack / bb_size estimate
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path("/home/cuzic/poker-books")
SCAN_PATHS = [
    "vol3-mtt-postflop/findings",
    "knowledges/gto_wizard_full",
    "knowledges/gto_wizard_study",
    "vol2-cash-postflop/_archive/findings",
]
OUT = ROOT / "scripts" / "three_class_model" / "spot_bet_info.csv"


def parse_float(s, default=None):
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


def extract_spot_info(path: Path) -> dict | None:
    try:
        d = json.loads(path.read_text())
    except Exception:
        return None
    if not isinstance(d, dict):
        return None
    meta = d.get("_meta") or {}
    req = meta.get("request") or {}
    game = d.get("game") or {}

    # board
    board = game.get("board") or req.get("board") or ""
    if not board:
        # fallback: parse from filename
        from re import compile as rc
        m = rc(r"([2-9TJQKA]{3,4})").search(path.stem)
        if m:
            ranks = m.group(1)
            board = "".join(r + s for r, s in zip(ranks, "cdhsc"))

    # pot info
    current_street = game.get("current_street") or {}
    pot_start = parse_float(current_street.get("start_pot"))
    pot_end = parse_float(current_street.get("end_pot"))
    pot = parse_float(game.get("pot"))
    pot_odds = parse_float(game.get("pot_odds"))

    # actions
    actions = d.get("action_solutions") or []
    bet_size = None
    for a in actions:
        if not isinstance(a, dict):
            continue
        act = a.get("action") or {}
        if act.get("code") == "C":
            bet_size = parse_float(act.get("betsize"))
            break
    if bet_size is None and pot_start is not None and pot_end is not None:
        bet_size = pot_end - pot_start

    bet_size_pot_ratio = None
    if bet_size and pot_start and pot_start > 0:
        bet_size_pot_ratio = bet_size / pot_start

    # depth
    pi = game.get("players") or d.get("players_info") or []
    hero_stack = None
    for p in pi:
        if not isinstance(p, dict):
            continue
        inner = p.get("player") if isinstance(p.get("player"), dict) else p
        if inner.get("is_hero"):
            hero_stack = parse_float(inner.get("stack"))
            break

    spot_id = meta.get("id") if meta else path.stem
    topic = meta.get("topic") if meta else path.parent.name

    return {
        "spot_id": spot_id,
        "topic": topic,
        "source_path": str(path.relative_to(ROOT)),
        "board_correct": board,
        "pot_start": pot_start,
        "pot_end": pot_end,
        "pot_now": pot,
        "pot_odds": pot_odds,
        "bet_size_chips": bet_size,
        "bet_size_pot_ratio": bet_size_pot_ratio,
        "hero_stack_bb": hero_stack,
    }


def main() -> int:
    rows = []
    for sp in SCAN_PATHS:
        base = ROOT / sp
        if not base.exists():
            continue
        for p in base.glob("**/*.json"):
            info = extract_spot_info(p)
            if info:
                rows.append(info)
    if not rows:
        return 1
    cols = list(rows[0].keys())
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"Wrote {len(rows)} spot records → {OUT}")

    # Quick stats
    import statistics
    bet_pots = [r["bet_size_pot_ratio"] for r in rows if r["bet_size_pot_ratio"]]
    print(f"\nbet_size_pot_ratio: n={len(bet_pots)}")
    if bet_pots:
        print(f"  median={statistics.median(bet_pots):.2f}")
        print(f"  mean={statistics.mean(bet_pots):.2f}")
        print(f"  unique sizes (rounded to 0.05):")
        from collections import Counter
        rounded = Counter(round(x / 0.05) * 0.05 for x in bet_pots)
        for k in sorted(rounded.keys()):
            print(f"    {k:.2f}x pot: {rounded[k]:4d} spots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
