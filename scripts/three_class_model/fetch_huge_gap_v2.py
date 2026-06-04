#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""Targeted fetch: more boards in huge-gap-prone contexts.

Targets:
  1. River defense: add 20+ boards with diverse turn lines and bet sizes
  2. Turn defense: add boards where overbet vs draws shows largest loss
  3. Flop defense: more dry/dynamic_2tone boards for low_pair/3rd_pair study
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

ROOT = Path("/home/cuzic/poker-books")
TOK = (ROOT / "scripts" / "gto_wizard_study" / ".token").read_text().strip()
OUT_R = ROOT / "vol3-mtt-postflop" / "findings" / "def_cash100_bb_river_raw"
OUT_T = ROOT / "vol3-mtt-postflop" / "findings" / "def_cash100_bb_turn_raw"
OUT_F = ROOT / "vol3-mtt-postflop" / "findings" / "def_cash100_bb_flop_raw"
OUT_R.mkdir(parents=True, exist_ok=True)
OUT_T.mkdir(parents=True, exist_ok=True)
OUT_F.mkdir(parents=True, exist_ok=True)

API = "https://api.gtowizard.com/v4/solutions/spot-solution/"
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "authorization": f"Bearer {TOK}",
    "origin": "https://app.gtowizard.com",
    "referer": "https://app.gtowizard.com/",
    "gwclientid": "930036c8-831c-4fca-8453-b0a298853e86",
    "user-agent": "Mozilla/5.0",
}
BASE = {
    "gametype": "Cash6mGeneral_6mNL25R25",
    "depth": "100",
    "stacks": "",
    "preflop_actions": "F-F-F-R2.5-F-C",
    "flop_actions": "X-R1.8-C",
}

# More river boards — different turn cards & river cards for variety
RIVER_SPOTS = [
    # K-high boards
    ("Kd7c2d3hAs", "K72-3-A"),
    ("Kd7c2d3hTh", "K72-3-T"),
    ("Kd7c2dAh2c", "K72-A-2"),
    ("Kd7c2dAhTh", "K72-A-T"),
    ("Kd7c2dQs8c", "K72-Q-8"),
    ("Kd7c2dQsJh", "K72-Q-J"),
    # Q-high boards
    ("Qh8d3s2h4d", "Q83-2-4"),
    ("Qh8d3s2hAc", "Q83-2-A"),
    ("Qh8d3sJcKh", "Q83-J-K"),
    ("Qh8d3sJc4d", "Q83-J-4"),
    # T98 + various
    ("Ts9d8cJc3h", "T98-J-3"),
    ("Ts9d8cJcAh", "T98-J-A"),
    ("Ts9d8c3hJh", "T98-3-J"),
    ("Ts9d8c3hKc", "T98-3-K"),
    # KJT
    ("KsJhTd2cAh", "KJT-2-A"),
    ("KsJhTd2c5s", "KJT-2-5"),
    ("KsJhTd2cQs", "KJT-2-Q"),
    # KJT-A + various rivers (already had 3, 7; add 9, J/Q/K)
    ("KsJhTdAhJs", "KJT-A-J"),
    ("KsJhTdAh9c", "KJT-A-9"),
    ("KsJhTdAhQc", "KJT-A-Q"),
]

# Test smaller turn bet sizes by adding "X-R3-C" (turn cbet 33%) line variants
RIVER_SMALL_TURN_SPOTS = [
    # Try with R3 (33%) turn cbet first if available
    # Will probe to find valid sizes
    ("Kd7c2dQs8c", "X-R3-C", "K72-Q-8-t33"),
    ("Kd7c2dQs8c", "X-R4.5-C", "K72-Q-8-t50"),
    ("Qh8d3sJc4d", "X-R3-C", "Q83-J-4-t33"),
    ("Ts9d8cJc3h", "X-R3-C", "T98-J-3-t33"),
]

# Re-fetch J73 turn defense (was skipped — try with a different turn card)
TURN_RETRY = [
    ("Jh7d3c4d", "J73-4"),
    ("Jh7d3c8s", "J73-8"),
    ("Jh7d3cKh", "J73-K"),
    ("Jh7d3cAh", "J73-A"),
]

# Flop defense — more spots for huge-gap study (different opener positions)
FLOP_DEFENSE_EXTRA = [
    # Different boards we don't have yet
    ("Ad6h2c", "A62"),       # A-high dry
    ("As9d4c", "A94"),       # A-high dry
    ("Th6d2s", "T62"),       # T-high dry
    ("9h6d2s", "962"),       # 9-high low
    ("8h4d3s", "843"),       # low dry
    ("Qd9c7h", "Q97"),       # Q-high semi-dynamic
    ("Js8d4c", "J84"),       # J-high
    ("Th9d4s", "T94"),       # T-high semi
]

SLEEP = 1.5


def fetch(client, params):
    try:
        r = client.get(API, params=params, timeout=30.0)
        if r.status_code == 200:
            return 200, r.json()
        return r.status_code, None
    except Exception as e:
        print(f"  EXC: {e!r}", file=sys.stderr)
        return -1, None


def main() -> int:
    n_ok = 0; n_total = 0; statuses = {}
    started = time.time()
    with httpx.Client(headers=HEADERS) as client:
        # ── Turn retries (J73 boards) ──
        print("=== Turn defense retries ===")
        for board, label in TURN_RETRY:
            params = dict(BASE)
            params["turn_actions"] = "X"
            params["board"] = board
            st, d = fetch(client, params)
            statuses[st] = statuses.get(st, 0) + 1
            n_total += 1
            if st != 200 or not d:
                print(f"  PROBE {label}: {st} skip"); time.sleep(SLEEP); continue
            bet_actions = [a for a in d.get("action_solutions", []) if a.get("action", {}).get("type") in {"RAISE", "BET"}]
            time.sleep(SLEEP)
            if not bet_actions:
                print(f"  {label}: no bet actions (only X)"); continue
            for ba in bet_actions:
                code = ba["action"]["code"]
                bp = ba["action"].get("betsize_by_pot")
                bp_str = f"{float(bp)*100:.0f}p" if bp else "?"
                params2 = dict(BASE)
                params2["board"] = board
                params2["turn_actions"] = f"X-{code}"
                fn = OUT_T / f"{label}_{code}.json"
                if fn.exists(): print(f"  SKIP {label}"); continue
                st, d2 = fetch(client, params2)
                statuses[st] = statuses.get(st, 0) + 1
                n_total += 1
                if st == 200 and d2:
                    d2["_meta"] = {"request": params2}
                    fn.write_text(json.dumps(d2))
                    n_ok += 1
                    print(f"  ✓ {label} bet={bp_str}({code})")
                else:
                    print(f"  ✗ {label} {code}: {st}")
                time.sleep(SLEEP)

        # ── New river boards ──
        print("\n=== River defense expansion ===")
        for board, label in RIVER_SPOTS:
            params = dict(BASE)
            params["board"] = board
            params["turn_actions"] = "X-R6.1-C"  # known-good turn cbet
            params["river_actions"] = "X"
            st, d = fetch(client, params)
            statuses[st] = statuses.get(st, 0) + 1
            n_total += 1
            if st != 200 or not d:
                # Try R2.3 (25% pot turn used on KJT-A boards)
                params["turn_actions"] = "X-R2.3-C"
                st, d = fetch(client, params)
                statuses[st] = statuses.get(st, 0) + 1
                n_total += 1
            if st != 200 or not d:
                print(f"  PROBE {label}: {st} skip"); time.sleep(SLEEP); continue
            bet_actions = [a for a in d.get("action_solutions", []) if a.get("action", {}).get("type") in {"RAISE", "BET"}]
            time.sleep(SLEEP)
            if not bet_actions:
                print(f"  {label}: no bet (X only)"); continue
            for ba in bet_actions:
                code = ba["action"]["code"]
                bp = ba["action"].get("betsize_by_pot")
                bp_str = f"{float(bp)*100:.0f}p" if bp else "?"
                params2 = dict(BASE)
                params2["board"] = board
                params2["turn_actions"] = params["turn_actions"]
                params2["river_actions"] = f"X-{code}"
                fn = OUT_R / f"{label}_{code}.json"
                if fn.exists(): print(f"  SKIP {label} {code}"); continue
                st, d2 = fetch(client, params2)
                statuses[st] = statuses.get(st, 0) + 1
                n_total += 1
                if st == 200 and d2:
                    d2["_meta"] = {"request": params2}
                    fn.write_text(json.dumps(d2))
                    n_ok += 1
                    print(f"  ✓ {label} river={bp_str}({code})")
                else:
                    print(f"  ✗ {label} {code}: {st}")
                time.sleep(SLEEP)

    print(f"\nTotal fetches: {n_total}, saved: {n_ok}, elapsed: {time.time()-started:.1f}s")
    print(f"Statuses: {statuses}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
