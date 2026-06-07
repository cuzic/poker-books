#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas"]
# ///
"""Extract per-combo (ctx, board, mv, dv, bet_freq) records from GTO Wizard JSONs.

Walks knowledges/gto_wizard_study/**/*.json. For each spot:
- pulls _meta.request (gametype, board, preflop_actions, ...)
- pulls players_info (hero position, IP/OOP)
- per combo i in [0..1325]: aggregates BET freq across all bet actions

Filter: in-range only (total action freq > 0.001).

Output: CSV at scripts/three_class_model/dataset_gtow.csv
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path("/home/cuzic/poker-books")
DATA_DIR = ROOT / "knowledges" / "gto_wizard_study"
OUT_PATH = ROOT / "scripts" / "three_class_model" / "dataset_gtow.csv"

# combo index → (card1, card2). 1326 = C(52,2).
# Convention used by GTO Wizard: enumerate i in 0..1325 over (a,b) with a<b
# where card index = rank * 4 + suit (rank 0=2..12=A, suit 0=c,1=d,2=h,3=s).
# We don't need actual cards for now — just MV/DV/blocker via hand_categories_range.
RANK_NAMES = "23456789TJQKA"
SUIT_NAMES = "cdhs"


def combo_to_cards(i: int) -> tuple[str, str] | None:
    """Map 1326-combo index → (cardA, cardB) like ('Ah', 'Kd'). GTO Wizard uses
    the convention: enumerate combinations of 52 cards in deck order
    rank-major (0..51 = 2c,2d,2h,2s,3c,...,As)."""
    a_card = b_card = -1
    n = 52
    # lex-rank: i = sum_{a'=0..a-1} (n-1-a') + (b-a-1)
    # solve for a, b
    k = i
    for a in range(n - 1):
        block = n - 1 - a
        if k < block:
            a_card = a
            b_card = a + 1 + k
            break
        k -= block
    if a_card < 0:
        return None
    def fmt(c: int) -> str:
        return RANK_NAMES[c // 4] + SUIT_NAMES[c % 4]
    return fmt(a_card), fmt(b_card)


def hand_class169(ca: str, cb: str) -> str:
    """Reduce 2-card combo to 169 hand-class string: 'AKs', 'AKo', 'TT', etc."""
    r1, s1 = ca[0], ca[1]
    r2, s2 = cb[0], cb[1]
    i1 = RANK_NAMES.index(r1)
    i2 = RANK_NAMES.index(r2)
    if i1 < i2:
        i1, i2 = i2, i1
        r1, r2 = r2, r1
        s1, s2 = s2, s1
    if r1 == r2:
        return r1 + r2
    return r1 + r2 + ("s" if s1 == s2 else "o")


def classify_context(req: dict, players: list[dict]) -> dict:
    """Pull ctx features from request + players_info."""
    gt = (req.get("gametype") or "").lower()
    if "mtt6m" in gt or "mtt9m" in gt:
        family = "mtt"
    elif "cashshort" in gt or "cashdeep" in gt or "cash" in gt:
        family = "cash"
    elif "icm" in gt:
        family = "icm"
    elif "spinrush" in gt or "spin" in gt:
        family = "spin"
    else:
        family = "other"

    depth_str = req.get("depth") or "0"
    try:
        depth = float(depth_str)
    except (TypeError, ValueError):
        depth = 0.0

    hero = next((p for p in players if p.get("is_hero")), None)
    villain = next((p for p in players if not p.get("is_hero") and not p.get("is_folded")), None)
    hero_pos = (hero or {}).get("position") or ""
    villain_pos = (villain or {}).get("position") or ""
    hero_rel = (hero or {}).get("relative_postflop_position") or ""

    preflop = req.get("preflop_actions") or ""
    # quick line classification: count R (raises) before final C
    n_raises = preflop.count("R")
    if n_raises >= 3:
        line = "3bp"
    elif n_raises == 2:
        line = "srp_3bet"  # ambiguous; treat as 3BP-ish
    elif n_raises == 1:
        line = "srp"
    else:
        line = "limped"

    flop_actions = req.get("flop_actions") or ""
    turn_actions = req.get("turn_actions") or ""
    if river := req.get("river_actions"):
        street = "river"
    elif turn_actions:
        street = "turn"
    elif flop_actions or req.get("board") and len(req.get("board")) >= 6:
        # board present → flop
        street = "flop"
    else:
        street = "preflop"

    return {
        "family": family,
        "depth_bb": depth,
        "hero_pos": hero_pos,
        "villain_pos": villain_pos,
        "hero_rel": hero_rel,  # IP / OOP
        "line": line,
        "street": street,
        "flop_actions": flop_actions,
        "turn_actions": turn_actions,
    }


def extract_one(path: Path) -> list[dict] | None:
    try:
        data = json.loads(path.read_text())
    except Exception:
        return None
    meta = data.get("_meta") or {}
    req = meta.get("request") or {}
    board = req.get("board") or ""
    if not board or len(board) < 6:
        return None  # need at least flop
    flop = board[:6]

    actions = data.get("action_solutions") or []
    if not actions:
        return None

    # Identify BET-side actions (anything that isn't pure CHECK or FOLD)
    bet_codes = []
    for a in actions:
        code = (a.get("action") or {}).get("code") or ""
        name = (a.get("action") or {}).get("display_name") or ""
        if code == "X" or name.upper() == "CHECK":
            continue
        if code == "F" or name.upper() == "FOLD":
            continue
        bet_codes.append(code)

    # strategies dict
    strategies = {(a.get("action") or {}).get("code"): (a.get("strategy") or []) for a in actions}
    hcr = data.get("hand_categories_range") or []
    dcr = data.get("draw_categories_range") or []
    # find any hand_categories map (use the first action that has it)
    hand_map: dict[int, str] = {}
    draw_map: dict[int, str] = {}
    for a in actions:
        for h in (a.get("hand_categories") or []):
            hand_map[h["index"]] = h["name"]
        for d in (a.get("draw_categories") or []):
            draw_map[d["index"]] = d["name"]
        if hand_map and draw_map:
            break

    ctx = classify_context(req, data.get("players_info") or [])

    rows = []
    n = max(len(s) for s in strategies.values()) if strategies else 0
    for i in range(n):
        total = sum(s[i] for s in strategies.values() if i < len(s))
        if total < 0.001:
            continue  # out of range
        bet_f = sum(strategies[c][i] for c in bet_codes if i < len(strategies.get(c, [])))
        cards = combo_to_cards(i)
        if not cards:
            continue
        hand169 = hand_class169(*cards)
        mv_name = hand_map.get(hcr[i], f"unk_{hcr[i]}") if i < len(hcr) else "unknown"
        dv_name = draw_map.get(dcr[i], f"unk_{dcr[i]}") if i < len(dcr) else "unknown"
        rows.append({
            "spot_id": meta.get("id") or path.stem,
            "topic": meta.get("topic") or "",
            "family": ctx["family"],
            "depth_bb": ctx["depth_bb"],
            "hero_pos": ctx["hero_pos"],
            "hero_rel": ctx["hero_rel"],
            "line": ctx["line"],
            "street": ctx["street"],
            "flop_actions": ctx["flop_actions"],
            "turn_actions": ctx["turn_actions"],
            "board_flop": flop,
            "board_full": board,
            "card_a": cards[0],
            "card_b": cards[1],
            "hand169": hand169,
            "mv_cat": mv_name,
            "dv_cat": dv_name,
            "bet_freq": round(bet_f, 4),
        })
    return rows


def main() -> int:
    all_rows: list[dict] = []
    json_files = sorted(DATA_DIR.glob("**/*.json"))
    n_files = 0
    n_skipped = 0
    for p in json_files:
        rows = extract_one(p)
        if not rows:
            n_skipped += 1
            continue
        all_rows.extend(rows)
        n_files += 1
    if not all_rows:
        print("No rows extracted!", file=sys.stderr)
        return 1
    cols = list(all_rows[0].keys())
    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in all_rows:
            w.writerow(r)
    print(f"Wrote {len(all_rows)} rows from {n_files} spots ({n_skipped} skipped) → {OUT_PATH}")
    # quick label distribution
    low = mid = high = 0
    for r in all_rows:
        f = r["bet_freq"]
        if f < 0.25:
            low += 1
        elif f < 0.75:
            mid += 1
        else:
            high += 1
    tot = low + mid + high
    print(f"Bucket distribution: LOW {low} ({low/tot*100:.1f}%) / MIX {mid} ({mid/tot*100:.1f}%) / HIGH {high} ({high/tot*100:.1f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
