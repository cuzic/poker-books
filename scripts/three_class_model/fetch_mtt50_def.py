#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""MTT 50bb defense fetch — turn + river.

Line: BTN open 2.1 → BB call → flop cbet 33% (R1.8) → BB call → turn …
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

ROOT = Path("/home/cuzic/poker-books")
TOK = (ROOT / "scripts" / "gto_wizard_study" / ".token").read_text().strip()
OUT_T = ROOT / "vol3-mtt-postflop" / "findings" / "def_mtt50_bb_turn_raw"
OUT_R = ROOT / "vol3-mtt-postflop" / "findings" / "def_mtt50_bb_river_raw"
OUT_T.mkdir(parents=True, exist_ok=True)
OUT_R.mkdir(parents=True, exist_ok=True)

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
    "gametype": "MTT6mGeneral",
    "depth": "50.125",
    "stacks": "50.125-50.125-50.125-50.125-50.125-50.125",
    "preflop_actions": "F-F-F-R2.1-F-C",
    "flop_actions": "X-R1.8-C",
}

# Turn defense — diverse boards
TURN_BOARDS = [
    ("Kd7c2d3h", "K72-3"),
    ("Kd7c2dKs", "K72-K"),
    ("Kd7c2dAh", "K72-A"),
    ("Kd7c2d7s", "K72-7"),
    ("Qh8d3s2h", "Q83-2"),
    ("Qh8d3s8c", "Q83-8"),
    ("Qh8d3sQc", "Q83-Q"),
    ("Qh8d3sJc", "Q83-J"),
    ("Ts9d8c2h", "T98-2"),
    ("Ts9d8cTh", "T98-T"),
    ("Ts9d8cJc", "T98-J"),
    ("Ts9d8c3h", "T98-3"),
    ("KsJhTd2c", "KJT-2"),
    ("KsJhTd9c", "KJT-9"),
    ("KsJhTdAh", "KJT-A"),
    ("Jh7d3c2s", "J73-2"),
    ("Td9d7d2h", "T97-mono"),
    ("Ks5d2c5h", "K52-5p"),
]

# River defense — use commonly-supported turn lines
RIVER_BOARDS = [
    ("Kd7c2dKs5h", "K72-K-5"),
    ("Kd7c2dKs9c", "K72-K-9"),
    ("Kd7c2d7s4c", "K72-7-4"),
    ("Qh8d3s8cKh", "Q83-8-K"),
    ("Qh8d3s8c5d", "Q83-8-5"),
    ("Qh8d3sQc4h", "Q83-Q-4"),
    ("Ts9d8c2h4s", "T98-2-4"),
    ("Ts9d8c2hJh", "T98-2-J"),
    ("Ts9d8cTh3h", "T98-T-3"),
    ("Ts9d8cJc2h", "T98-J-2"),
    ("KsJhTd9cAh", "KJT-9-A"),
    ("KsJhTd9c2h", "KJT-9-2"),
    ("KsJhTdAh3h", "KJT-A-3"),
    ("KsJhTdAh7c", "KJT-A-7"),
]

SLEEP = 1.2


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
        # Turn defense
        print("=== MTT 50bb TURN DEFENSE ===")
        for board, label in TURN_BOARDS:
            params = dict(BASE)
            params["turn_actions"] = "X"
            params["river_actions"] = ""
            params["board"] = board
            st, d = fetch(client, params)
            statuses[st] = statuses.get(st, 0) + 1
            n_total += 1
            if st != 200 or not d:
                print(f"  PROBE {label}: {st} skip"); time.sleep(SLEEP); continue
            bet_actions = [a for a in d.get("action_solutions", []) if a.get("action", {}).get("type") in {"RAISE", "BET"}]
            time.sleep(SLEEP)
            if not bet_actions:
                print(f"  {label}: no bet actions"); continue
            for ba in bet_actions:
                code = ba["action"]["code"]
                bp = ba["action"].get("betsize_by_pot")
                bp_str = f"{float(bp)*100:.0f}p" if bp else "?"
                params2 = dict(BASE)
                params2["board"] = board
                params2["turn_actions"] = f"X-{code}"
                params2["river_actions"] = ""
                fn = OUT_T / f"{label}_{code}.json"
                if fn.exists():
                    print(f"  SKIP {label} {code}"); continue
                st, d2 = fetch(client, params2)
                statuses[st] = statuses.get(st, 0) + 1
                n_total += 1
                if st == 200 and d2:
                    d2["_meta"] = {"request": params2}
                    fn.write_text(json.dumps(d2))
                    n_ok += 1
                    print(f"  ✓ {label} bet={bp_str}({code})")
                time.sleep(SLEEP)

        # River defense — try multiple turn sizes per board
        print("\n=== MTT 50bb RIVER DEFENSE ===")
        for board, label in RIVER_BOARDS:
            chosen_turn = None
            d = None
            for turn_attempt in ["X-R1.8-C", "X-R3.5-C", "X-R4.5-C"]:
                params = dict(BASE)
                params["board"] = board
                params["turn_actions"] = turn_attempt
                params["river_actions"] = "X"
                st, d = fetch(client, params)
                statuses[st] = statuses.get(st, 0) + 1
                n_total += 1
                if st == 200 and d:
                    chosen_turn = turn_attempt
                    break
                time.sleep(SLEEP)
            if not chosen_turn or not d:
                print(f"  RIVER PROBE {label}: no valid turn line")
                continue
            bet_actions = [a for a in d.get("action_solutions", []) if a.get("action", {}).get("type") in {"RAISE", "BET"}]
            time.sleep(SLEEP)
            if not bet_actions:
                print(f"  {label}: no river bet actions")
                continue
            for ba in bet_actions:
                code = ba["action"]["code"]
                bp = ba["action"].get("betsize_by_pot")
                bp_str = f"{float(bp)*100:.0f}p" if bp else "?"
                params2 = dict(BASE)
                params2["board"] = board
                params2["turn_actions"] = chosen_turn
                params2["river_actions"] = f"X-{code}"
                fn = OUT_R / f"{label}_{code}.json"
                if fn.exists(): continue
                st, d2 = fetch(client, params2)
                statuses[st] = statuses.get(st, 0) + 1
                n_total += 1
                if st == 200 and d2:
                    d2["_meta"] = {"request": params2}
                    fn.write_text(json.dumps(d2))
                    n_ok += 1
                    print(f"  ✓ {label} river={bp_str}({code})")
                time.sleep(SLEEP)

    print(f"\nTotal: {n_total}, saved: {n_ok}, elapsed: {time.time()-started:.1f}s")
    print(f"Statuses: {statuses}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
