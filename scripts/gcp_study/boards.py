#!/usr/bin/env python3
"""Generate systematic board sampling for GTO regression study (~168 boards).

Run: python3 boards.py
Output: boards.json in the same directory.
"""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

RANK_STR = {14: "A", 13: "K", 12: "Q", 11: "J", 10: "T",
            9: "9", 8: "8", 7: "7", 6: "6", 5: "5", 4: "4", 3: "3", 2: "2"}
SUIT_SYM  = {"c": "♣", "d": "♦", "h": "♥", "s": "♠"}
R = RANK_STR


def make_board(r1: int, r2: int, r3: int, s1: str, s2: str, s3: str) -> dict:
    ranks   = sorted([r1, r2, r3], reverse=True)
    r_hi, r_mid, r_lo = ranks[0], ranks[1], ranks[2]
    is_paired   = (r1 == r2) or (r2 == r3) or (r1 == r3)
    is_mono     = (s1 == s2 == s3)
    is_2tone    = not is_mono and len({s1, s2, s3}) == 2

    if is_mono:
        cat = "monotone"
    elif is_2tone and not is_paired:
        cat = "2tone"
    elif is_paired:
        cat = "paired"
    else:
        cat = "rainbow"

    top_diff = r_hi - r_mid if not is_paired else 0
    mid_diff = r_mid - r_lo

    solver  = f"{R[r1]}{s1},{R[r2]}{s2},{R[r3]}{s3}"
    display = f"{R[r1]}{SUIT_SYM[s1]}{R[r2]}{SUIT_SYM[s2]}{R[r3]}{SUIT_SYM[s3]}"

    return {
        "board_id":    f"{R[r_hi]}{R[r_mid]}{R[r_lo]}_{cat[0]}",
        "solver_str":  solver,
        "display":     display,
        "category":    cat,
        "r_hi":   r_hi,
        "r_mid":  r_mid,
        "r_lo":   r_lo,
        "spread":    r_hi - r_lo,
        "top_diff":  top_diff,
        "mid_diff":  mid_diff,
        "top_rank":  r_hi,
        "is_paired":    is_paired,
        "is_2tone":     is_2tone,
        "is_monotone":  is_mono,
    }


boards: list[dict] = []
seen: set[str] = set()


def add(r1: int, r2: int, r3: int, s1: str, s2: str, s3: str) -> None:
    b = make_board(r1, r2, r3, s1, s2, s3)
    if b["solver_str"] not in seen:
        seen.add(b["solver_str"])
        boards.append(b)


# ── 1. Rainbow unpaired (target ~88) ─────────────────────────────────────────
RAINBOW_PATTERNS = [
    (1, 1), (1, 2), (1, 3), (1, 4), (1, 5),
    (2, 1), (2, 2), (2, 3), (2, 4),
    (3, 1), (3, 2), (3, 3),
    (4, 1), (4, 2),
    (5, 1),
]

for top in [14, 13, 12, 11, 10, 9, 8, 7]:
    for td, md in RAINBOW_PATTERNS:
        r2 = top - td
        r3 = r2 - md
        if r3 < 2:
            continue
        add(top, r2, r3, "c", "d", "s")


# ── 2. 2-tone unpaired (target ~28) ──────────────────────────────────────────
TWOTONE_PATTERNS = [
    (1, 1), (1, 2), (2, 1), (2, 3), (3, 2), (4, 1), (1, 4),
]

for top in [14, 13, 12, 11, 10, 9, 8, 7]:
    for td, md in TWOTONE_PATTERNS:
        r2 = top - td
        r3 = r2 - md
        if r3 < 2:
            continue
        add(top, r2, r3, "c", "d", "c")


# ── 3. Monotone (target ~24) ──────────────────────────────────────────────────
MONO_PATTERNS = [
    (1, 1), (2, 2), (3, 3), (5, 3), (1, 4), (4, 2),
]

for top in [14, 13, 12, 11, 10, 9, 8, 7]:
    for td, md in MONO_PATTERNS:
        r2 = top - td
        r3 = r2 - md
        if r3 < 2:
            continue
        add(top, r2, r3, "c", "c", "c")


# ── 4. Paired (target ~35) ───────────────────────────────────────────────────
for pair in [14, 13, 12, 11, 10, 9, 8, 7]:
    for koff in [1, 2, 3, 5, 8]:
        k = pair - koff
        if k < 2:
            continue
        add(pair, pair, k, "c", "d", "h")
    if pair > 2:
        add(pair, pair, 2, "c", "d", "h")


# ── Deduplicate board_ids ─────────────────────────────────────────────────────
id_count: dict[str, int] = {}
for b in boards:
    bid = b["board_id"]
    if bid in id_count:
        id_count[bid] += 1
        b["board_id"] = f"{bid}{id_count[bid]}"
    else:
        id_count[bid] = 0


# ── Summary ───────────────────────────────────────────────────────────────────
cats = Counter(b["category"] for b in boards)
print(f"Total: {len(boards)} boards")
for cat, cnt in sorted(cats.items()):
    print(f"  {cat}: {cnt}")

out = Path(__file__).parent / "boards.json"
out.write_text(json.dumps(boards, ensure_ascii=False, indent=2))
print(f"Saved → {out}")
