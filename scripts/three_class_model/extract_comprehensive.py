#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas"]
# ///
"""Extract rich per-combo records from comprehensive JSONs.

Per (spot, combo) row:
- mv, dv: from hand_categories_range / draw_categories_range
- bet_freq, check_freq: from strategy[]
- ev_bet, ev_check: from evs[]
- ev_gap: max(ev_bet, ev_check) - min(...)
- ev_dominance: which action has higher EV (BET / CHECK / TIE)
- equity_bucket: if equity_buckets[] is present
- equity_range: e.g., "60-80%" (from bucket name)

Output: scripts/three_class_model/dataset_full.csv
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "knowledges" / "gto_wizard_full"
OUT = ROOT / "scripts" / "three_class_model" / "dataset_full.csv"

RANKS = "23456789TJQKA"
SUITS = "cdhs"


def combo_to_cards(i: int) -> tuple[str, str] | None:
    a_card = b_card = -1
    n = 52
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
        return RANKS[c // 4] + SUITS[c % 4]
    return fmt(a_card), fmt(b_card)


def hand_class169(ca: str, cb: str) -> str:
    r1, s1 = ca[0], ca[1]
    r2, s2 = cb[0], cb[1]
    i1, i2 = RANKS.index(r1), RANKS.index(r2)
    if i1 < i2:
        i1, i2 = i2, i1
        r1, r2 = r2, r1
        s1, s2 = s2, s1
    if r1 == r2:
        return r1 + r2
    return r1 + r2 + ("s" if s1 == s2 else "o")


def classify_context(meta: dict, players: list[dict]) -> dict:
    req = meta.get("request") or {}
    gt = (req.get("gametype") or "").lower()
    if "mtt6m" in gt or "mtt9m" in gt:
        family = "mtt"
    elif "cash" in gt:
        family = "cash"
    elif "icm" in gt:
        family = "icm"
    else:
        family = "other"
    try:
        depth = float(req.get("depth") or 0)
    except (TypeError, ValueError):
        depth = 0.0
    hero = next((p for p in players if p.get("is_hero")), None)
    hero_pos = (hero or {}).get("position") or ""
    hero_rel = (hero or {}).get("relative_postflop_position") or ""
    preflop = req.get("preflop_actions") or ""
    n_raises = preflop.count("R")
    if n_raises >= 3:
        line = "3bp"
    elif n_raises == 2:
        line = "srp_3bet"
    elif n_raises == 1:
        line = "srp"
    else:
        line = "limped"
    flop_actions = req.get("flop_actions") or ""
    turn_actions = req.get("turn_actions") or ""
    river_actions = req.get("river_actions") or ""
    board = req.get("board") or ""
    if river_actions or len(board) >= 10:
        street = "river"
    elif turn_actions or len(board) >= 8:
        street = "turn"
    elif flop_actions or len(board) >= 6:
        street = "flop"
    else:
        street = "preflop"
    return {
        "family": family,
        "depth_bb": depth,
        "hero_pos": hero_pos,
        "hero_rel": hero_rel,
        "line": line,
        "street": street,
        "flop_actions": flop_actions,
        "turn_actions": turn_actions,
        "river_actions": river_actions,
        "board_full": board,
        "board_flop": board[:6],
    }


def extract_one(path: Path) -> list[dict] | None:
    try:
        data = json.loads(path.read_text())
    except Exception:
        return None
    meta = data.get("_meta") or {}
    ctx = classify_context(meta, data.get("players_info") or [])
    actions = data.get("action_solutions") or []
    if not actions:
        return None

    # Identify BET vs CHECK actions
    bet_codes, check_codes = [], []
    for a in actions:
        code = (a.get("action") or {}).get("code") or ""
        name = (a.get("action") or {}).get("display_name") or ""
        if code == "X" or name.upper() == "CHECK":
            check_codes.append(code)
        elif code == "F" or name.upper() == "FOLD":
            pass  # ignore
        else:
            bet_codes.append(code)

    # Build strategy + evs maps
    strategies = {(a.get("action") or {}).get("code"): a.get("strategy") or [] for a in actions}
    evs = {(a.get("action") or {}).get("code"): a.get("evs") or [] for a in actions}

    # hand_categories index→name (from any action)
    hand_map: dict[int, str] = {}
    draw_map: dict[int, str] = {}
    for a in actions:
        for h in (a.get("hand_categories") or []):
            hand_map[h["index"]] = h["name"]
        for d in (a.get("draw_categories") or []):
            draw_map[d["index"]] = d["name"]
        if hand_map and draw_map:
            break

    # equity_buckets — assign each combo to the bucket whose hand_categories contain
    # the same combo index. Buckets may be present in just one action's metadata.
    # For now we just check if buckets exist and extract their NAMES (not per-combo).
    eq_bucket_names: list[str] = []
    for a in actions:
        eb = a.get("equity_buckets") or []
        if eb:
            eq_bucket_names = [b.get("name", "") for b in eb]
            break

    hcr = data.get("hand_categories_range") or []
    dcr = data.get("draw_categories_range") or []

    rows = []
    for i in range(1326):
        # in-range filter
        total_freq = sum(s[i] for s in strategies.values() if i < len(s))
        if total_freq < 0.001:
            continue
        cards = combo_to_cards(i)
        if not cards:
            continue
        hand169 = hand_class169(*cards)

        mv_name = hand_map.get(hcr[i], f"unk_{hcr[i]}") if i < len(hcr) else "unknown"
        dv_name = draw_map.get(dcr[i], f"unk_{dcr[i]}") if i < len(dcr) else "unknown"

        # Bet/check frequencies and EVs
        bet_freq = sum(strategies[c][i] for c in bet_codes if i < len(strategies.get(c, [])))
        check_freq = sum(strategies[c][i] for c in check_codes if i < len(strategies.get(c, [])))

        # Weighted EV per action group
        # For multi-sized bets, EV is weighted average within bet codes
        def weighted_ev(codes):
            num = 0.0
            den = 0.0
            for c in codes:
                if i < len(strategies.get(c, [])) and i < len(evs.get(c, [])):
                    w = strategies[c][i]
                    e = evs[c][i]
                    if w > 0 and e is not None:
                        num += w * e
                        den += w
            return num / den if den > 0 else None

        ev_bet = weighted_ev(bet_codes)
        ev_check = weighted_ev(check_codes)
        ev_gap = (
            abs(ev_bet - ev_check)
            if (ev_bet is not None and ev_check is not None)
            else None
        )
        if ev_bet is not None and ev_check is not None:
            ev_dominance = "BET" if ev_bet > ev_check + 0.01 else ("CHECK" if ev_check > ev_bet + 0.01 else "TIE")
        else:
            ev_dominance = "ONE_ACTION"

        # bucket: lookup via hand_categories actions data is complex; defer.
        rows.append({
            "spot_id": meta.get("id") or path.stem,
            "topic": meta.get("topic") or "",
            **ctx,
            "card_a": cards[0],
            "card_b": cards[1],
            "hand169": hand169,
            "mv_cat": mv_name,
            "dv_cat": dv_name,
            "bet_freq": round(bet_freq, 4),
            "check_freq": round(check_freq, 4),
            "ev_bet": round(ev_bet, 3) if ev_bet is not None else None,
            "ev_check": round(ev_check, 3) if ev_check is not None else None,
            "ev_gap": round(ev_gap, 3) if ev_gap is not None else None,
            "ev_dominance": ev_dominance,
            "has_equity_buckets": bool(eq_bucket_names),
        })
    return rows


def main() -> int:
    all_rows: list[dict] = []
    n_files = n_skipped = 0
    for p in sorted(DATA.glob("**/*.json")):
        rows = extract_one(p)
        if not rows:
            n_skipped += 1
            continue
        all_rows.extend(rows)
        n_files += 1
    if not all_rows:
        print("No rows extracted", file=sys.stderr)
        return 1
    cols = list(all_rows[0].keys())
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in all_rows:
            w.writerow(r)
    print(f"Wrote {len(all_rows)} rows from {n_files} spots ({n_skipped} skipped) → {OUT}")
    # quick stats
    import statistics
    have_ev = [r["ev_gap"] for r in all_rows if r["ev_gap"] is not None]
    print(f"EV gap available: {len(have_ev)}/{len(all_rows)} rows")
    if have_ev:
        print(f"  median EV gap: {statistics.median(have_ev):.3f}")
        print(f"  >0.5 EV gap (clear best action): {sum(1 for g in have_ev if g > 0.5)}/{len(have_ev)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
