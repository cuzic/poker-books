#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas"]
# ///
"""Unified extractor for ALL postflop GTO Wizard JSON files across the project.

Handles two main formats:
  Format A (raw API): vol3-mtt-postflop/findings/* — no _meta, board in filename,
    rich players_info with equity_buckets_range + eq_percentile per combo.
  Format B (slimmed): knowledges/gto_wizard_full/* — has _meta.request, slim players_info.

Output per (spot, combo) row:
  - spot_id, source_path, family (cash/mtt), depth, position, hero_rel
  - line context: preflop_actions, flop_actions, turn_actions (parsed)
  - street, board, board_family, action_context (attack/defense)
  - hand169, card_a, card_b
  - mv_cat, dv_cat (from hand_categories_range / draw_categories_range)
  - equity_bucket (TRUE from equity_buckets_range when available, else approximated)
  - eq_percentile (when available)
  - hand_eq (raw equity vs villain range)
  - bet_freq, check_freq, call_freq, fold_freq, raise_freq
  - ev_bet, ev_check, ev_call, ev_fold, ev_raise
  - ev_gap (max - 2nd best EV)
  - blocker_rate, unblocker_rate (per spot)

Output: scripts/three_class_model/dataset_unified.csv
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path("/home/cuzic/poker-books")

# All postflop data locations
SCAN_PATHS = [
    "vol3-mtt-postflop/findings",
    "knowledges/gto_wizard_full",
    "knowledges/gto_wizard_study",
    "vol2-cash-postflop/_archive/findings",
]

OUT_PATH = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"

RANKS = "23456789TJQKA"
SUITS = "cdhs"


def combo_to_cards(i: int) -> tuple[str, str] | None:
    a_card = -1
    n = 52
    k = i
    for a in range(n - 1):
        block = n - 1 - a
        if k < block:
            return RANKS[a // 4] + SUITS[a % 4], RANKS[(a + 1 + k) // 4] + SUITS[(a + 1 + k) % 4]
        k -= block
    return None


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


# Filename → board parser for Format A
# Examples:
#   BTN_BB_742_fd.json   → opener=BTN, defender=BB, board ranks "742", suits "fd"=flush-draw
#   K72_fd.json          → board K72, fd
#   AA7_rain.json        → AA7 rainbow
#   BTN_BB_A72_rain.json → board A72 rainbow
#   K72r_7.json          → TURN board: flop K72 rainbow + turn 7
#   Q83_8.json           → TURN board: flop Q83 (default rainbow) + turn 8
BOARD_RE = re.compile(r"(?:([A-Z]{2,3})_([A-Z]{2,3})_)?([2-9TJQKA]{3,4})_([a-z]+)$")
# Turn pattern: 3 flop ranks + optional tex letter + underscore + 1 turn rank
TURN_RE = re.compile(r"^([2-9TJQKA]{3})([a-z]*)_([2-9TJQKA])$")
SUITED_BOARDS = {
    # texture suffix → suit assignment for 3 board cards (deterministic for analysis)
    "rain": "cdh",     # rainbow
    "rainbow": "cdh",
    "r": "cdh",        # short form
    "fd": "ssc",       # flush-draw board (2 of same suit)
    "flush": "sss",    # 3 flush
    "mono": "sss",
    "monotone": "sss",
    "fdmono": "sss",
    "paired": "cdh",   # paired board (same as rainbow for suits)
    "": "cdh",         # no suffix → assume rainbow
}


def parse_board_from_filename(stem: str) -> tuple[str, str | None, str | None] | None:
    """Parse a Format A filename. Returns (board_with_suits, opener, defender) or None."""
    # First try TURN pattern (e.g., K72r_7, Q83_8)
    m_turn = TURN_RE.match(stem)
    if m_turn:
        ranks, tex, turn_rank = m_turn.group(1), m_turn.group(2), m_turn.group(3)
        suits = SUITED_BOARDS.get(tex.lower(), "cdh")
        # build flop
        flop_chars = []
        for j, r in enumerate(ranks):
            flop_chars.append(r + suits[j])
        flop = "".join(flop_chars)
        # append turn card with a non-conflicting suit
        used = set(suits[:3])
        turn_suit = next((c for c in "cdhs" if c not in used), "s")
        return flop + turn_rank + turn_suit, None, None

    # Then try general FLOP pattern
    m = BOARD_RE.search(stem)
    if not m:
        return None
    opener, defender, ranks, tex = m.group(1), m.group(2), m.group(3), m.group(4)
    suits = SUITED_BOARDS.get(tex.lower())
    if not suits or len(suits) < len(ranks[:3]):
        return None
    # Assemble: r1+s1 r2+s2 r3+s3 (for first 3 ranks = flop)
    board_chars = []
    for j, r in enumerate(ranks[:3]):
        board_chars.append(r + suits[j])
    flop = "".join(board_chars)
    # Append turn card if 4 ranks
    if len(ranks) == 4:
        used = set(suits[:3])
        turn_suit = next((c for c in "cdhs" if c not in used), "h")
        flop += ranks[3] + turn_suit
    return flop, opener, defender


def detect_street(board: str, req: dict) -> str:
    if board:
        if len(board) >= 10:
            return "river"
        if len(board) >= 8:
            return "turn"
        if len(board) >= 6:
            return "flop"
    if req.get("river_actions"):
        return "river"
    if req.get("turn_actions"):
        return "turn"
    if req.get("flop_actions"):
        return "flop"
    return "preflop"


def classify_board_family(flop: str) -> str:
    if len(flop) < 6:
        return "unknown"
    ranks_str = flop[0] + flop[2] + flop[4]
    suits = [flop[1], flop[3], flop[5]]
    ranks = sorted([RANKS.index(r) for r in ranks_str], reverse=True)
    is_paired = len(set(ranks_str)) < 3
    n_suits = len(set(suits))
    spread = ranks[0] - ranks[2]
    top = ranks[0]
    if is_paired:
        return "paired"
    if n_suits == 1:
        return "monotone"
    if n_suits == 2 and spread <= 4:
        return "dynamic_2tone"
    if spread <= 4:
        return "dynamic"
    if top >= 9:
        return "dry_high"
    return "low_dry"


def get_hero_player(players_info: list) -> dict | None:
    for p in players_info or []:
        if isinstance(p, dict):
            inner = p.get("player") if isinstance(p.get("player"), dict) else p
            if inner.get("is_hero"):
                return p
    return None


def extract_one(path: Path) -> tuple[list[dict], str]:
    """Returns (rows, format_label). format_label: 'A', 'B', 'C', or 'skip'."""
    try:
        data = json.loads(path.read_text())
    except Exception:
        return [], "skip"
    if not isinstance(data, dict):
        return [], "skip"
    actions = data.get("action_solutions") or []
    if not actions:
        return [], "skip"

    meta = data.get("_meta") or {}
    req = meta.get("request") or {}

    # Format detection
    has_meta = bool(meta)
    board = req.get("board") or ""
    opener = None
    defender = None
    if not board:
        # Format A: parse from filename
        parsed = parse_board_from_filename(path.stem)
        if parsed:
            board, opener, defender = parsed

    # Strategy / EV per combo
    strategies = {(a.get("action") or {}).get("code"): a.get("strategy") or [] for a in actions if isinstance(a, dict)}
    evs = {(a.get("action") or {}).get("code"): a.get("evs") or [] for a in actions if isinstance(a, dict)}
    codes = list(strategies.keys())
    is_defense = "F" in codes or "C" in codes

    # Identify action categories
    bet_codes = []
    check_codes = []
    call_codes = []
    fold_codes = []
    raise_codes_def = []
    for a in actions:
        if not isinstance(a, dict):
            continue
        code = (a.get("action") or {}).get("code") or ""
        name = ((a.get("action") or {}).get("display_name") or "").upper()
        if code == "X" or name == "CHECK":
            check_codes.append(code)
        elif code == "F" or name == "FOLD":
            fold_codes.append(code)
        elif code == "C" or name == "CALL":
            call_codes.append(code)
        elif code.startswith("R") or "RAI" in code:
            if is_defense:
                raise_codes_def.append(code)
            else:
                bet_codes.append(code)

    # Hand/draw category maps
    hand_map: dict[int, str] = {}
    draw_map: dict[int, str] = {}
    for a in actions:
        if not isinstance(a, dict):
            continue
        for h in a.get("hand_categories") or []:
            hand_map[h["index"]] = h["name"]
        for dvc in a.get("draw_categories") or []:
            draw_map[dvc["index"]] = dvc["name"]
        if hand_map and draw_map:
            break
    hcr = data.get("hand_categories_range") or []
    dcr = data.get("draw_categories_range") or []

    # Hero player + per-combo equity if available (Format A)
    pi = data.get("players_info") or []
    hero = get_hero_player(pi)
    hero_player = hero.get("player") if isinstance(hero, dict) and isinstance(hero.get("player"), dict) else (hero or {})
    eq_bucket_range = (hero or {}).get("equity_buckets_range", []) if isinstance(hero, dict) else []
    eq_percentile = (hero or {}).get("eq_percentile", []) if isinstance(hero, dict) else []
    hand_eqs = (hero or {}).get("hand_eqs", []) if isinstance(hero, dict) else []
    # bucket index → name
    eb_list = (hero or {}).get("equity_buckets", []) if isinstance(hero, dict) else []
    bucket_idx_to_name: dict[int, str] = {}
    for b in eb_list:
        if isinstance(b, dict):
            bucket_idx_to_name[b.get("index", -1)] = b.get("name", "")
    if not bucket_idx_to_name:
        bucket_idx_to_name = {0: "best_hands", 1: "good_hands", 2: "weak_hands", 3: "trash_hands"}

    hero_pos = hero_player.get("position") or ""
    hero_rel = hero_player.get("relative_postflop_position") or ""
    family = ""
    depth = None
    gametype = req.get("gametype") or (data.get("game") or {}).get("gametype") or ""
    if gametype:
        gt = gametype.lower()
        if "cash" in gt: family = "cash"
        elif "mtt" in gt: family = "mtt"
        elif "icm" in gt: family = "icm"
    # depth from request or filename
    try:
        depth = float(req.get("depth") or 0)
    except (TypeError, ValueError):
        depth = None
    if not depth and "mtt25" in str(path): depth = 25
    elif not depth and "mtt50" in str(path): depth = 50
    elif not depth and "mtt100" in str(path): depth = 100
    elif not depth and "mtt200" in str(path): depth = 200

    street = detect_street(board, req)
    board_flop = board[:6] if len(board) >= 6 else ""
    board_family = classify_board_family(board_flop) if board_flop else "unknown"
    action_ctx = "defense" if is_defense else "attack"

    rows: list[dict] = []
    for i in range(1326):
        total_freq = sum(s[i] for s in strategies.values() if i < len(s))
        if total_freq < 0.001:
            continue
        cards = combo_to_cards(i)
        if not cards:
            continue
        h169 = hand_class169(*cards)
        mv_name = hand_map.get(hcr[i], f"unk_{hcr[i]}") if i < len(hcr) else "unknown"
        dv_name = draw_map.get(dcr[i], f"unk_{dcr[i]}") if i < len(dcr) else "unknown"

        # True equity bucket if available (Format A); else placeholder
        if i < len(eq_bucket_range):
            eb_idx = int(eq_bucket_range[i]) if eq_bucket_range[i] >= 0 else -1
            eq_bucket_name = bucket_idx_to_name.get(eb_idx, "")
        else:
            eq_bucket_name = ""
        eqp = float(eq_percentile[i]) if i < len(eq_percentile) and eq_percentile[i] >= 0 else None
        heq = float(hand_eqs[i]) if i < len(hand_eqs) else None

        # Frequencies per category
        def wsum(code_list):
            return sum(strategies[c][i] for c in code_list if i < len(strategies.get(c, [])))
        bet_f = wsum(bet_codes)
        check_f = wsum(check_codes)
        fold_f = wsum(fold_codes)
        call_f = wsum(call_codes)
        raise_f = wsum(raise_codes_def)

        # Per-action EV (combo i, weighted by strategy)
        def wev(code_list):
            num = 0.0
            den = 0.0
            for c in code_list:
                if i < len(strategies.get(c, [])) and i < len(evs.get(c, [])):
                    w = strategies[c][i]
                    e = evs[c][i]
                    if w > 0 and e is not None:
                        num += w * e
                        den += w
            return num / den if den > 0 else None
        ev_bet = wev(bet_codes)
        ev_check = wev(check_codes)
        ev_fold = wev(fold_codes)
        ev_call = wev(call_codes)
        ev_raise = wev(raise_codes_def)

        # ev_gap = max - 2nd best (across non-None)
        evs_list = [e for e in [ev_bet, ev_check, ev_fold, ev_call, ev_raise] if e is not None]
        if len(evs_list) >= 2:
            srt = sorted(evs_list, reverse=True)
            ev_gap = srt[0] - srt[1]
        else:
            ev_gap = None

        rows.append({
            "source_path": str(path.relative_to(ROOT)),
            "spot_id": (meta.get("id") if has_meta else path.stem),
            "topic": (meta.get("topic") if has_meta else path.parent.name),
            "format": "A" if not has_meta else "B",
            "family": family,
            "depth": depth,
            "gametype": gametype,
            "hero_pos": hero_pos,
            "hero_rel": hero_rel,
            "opener": opener,
            "defender": defender,
            "preflop_actions": req.get("preflop_actions", ""),
            "flop_actions": req.get("flop_actions", ""),
            "turn_actions": req.get("turn_actions", ""),
            "river_actions": req.get("river_actions", ""),
            "board_full": board,
            "board_flop": board_flop,
            "board_family": board_family,
            "street": street,
            "action_context": action_ctx,
            "card_a": cards[0],
            "card_b": cards[1],
            "hand169": h169,
            "mv_cat": mv_name,
            "dv_cat": dv_name,
            "equity_bucket": eq_bucket_name,
            "eq_percentile": round(eqp, 4) if eqp is not None else None,
            "hand_eq": round(heq, 4) if heq is not None else None,
            "bet_freq": round(bet_f, 4),
            "check_freq": round(check_f, 4),
            "fold_freq": round(fold_f, 4),
            "call_freq": round(call_f, 4),
            "raise_freq": round(raise_f, 4),
            "ev_bet": round(ev_bet, 3) if ev_bet is not None else None,
            "ev_check": round(ev_check, 3) if ev_check is not None else None,
            "ev_fold": round(ev_fold, 3) if ev_fold is not None else None,
            "ev_call": round(ev_call, 3) if ev_call is not None else None,
            "ev_raise": round(ev_raise, 3) if ev_raise is not None else None,
            "ev_gap": round(ev_gap, 3) if ev_gap is not None else None,
        })
    return rows, ("A" if not has_meta else "B")


def main() -> int:
    all_rows: list[dict] = []
    fmt_counts: dict[str, int] = defaultdict(int)
    n_attack = 0
    n_defense = 0
    n_with_eq_buckets = 0
    n_files_used = 0
    n_files_skipped = 0

    for sp in SCAN_PATHS:
        base = ROOT / sp
        if not base.exists():
            continue
        for p in base.glob("**/*.json"):
            rows, fmt = extract_one(p)
            if not rows:
                n_files_skipped += 1
                continue
            n_files_used += 1
            fmt_counts[fmt] += 1
            all_rows.extend(rows)
            # Stats
            ctx = rows[0].get("action_context")
            if ctx == "defense": n_defense += 1
            else: n_attack += 1
            if rows[0].get("equity_bucket"):
                n_with_eq_buckets += 1

    print(f"Total rows extracted: {len(all_rows)}")
    print(f"Spots used: {n_files_used} (skipped {n_files_skipped})")
    print(f"  Format A: {fmt_counts.get('A', 0)}")
    print(f"  Format B: {fmt_counts.get('B', 0)}")
    print(f"  Attack: {n_attack}")
    print(f"  Defense: {n_defense}")
    print(f"  With true equity_bucket: {n_with_eq_buckets}")

    if not all_rows:
        print("No rows!", file=sys.stderr)
        return 1
    cols = list(all_rows[0].keys())
    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in all_rows:
            w.writerow(r)
    print(f"\nSaved → {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
