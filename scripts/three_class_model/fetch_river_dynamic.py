#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""Fetch more dynamic-board river defense spots — focus on diverse turn lines.

Strategy: use boards where turn cbet 67% pot is the common line, then probe river
with diverse bet sizes for diverse exception coverage.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

ROOT = Path("/home/cuzic/poker-books")
TOK = (ROOT / "scripts" / "gto_wizard_study" / ".token").read_text().strip()
OUT = ROOT / "vol3-mtt-postflop" / "findings" / "def_cash100_bb_river_raw"
OUT.mkdir(parents=True, exist_ok=True)

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

# Dynamic river spots — try both R6.1 (67%) turn and R2.3 (25%) turn variants
SPOTS = [
    # Dynamic flops × dynamic turns × varied rivers
    ("Ts9d8c2hAh", "T98-2-A"),
    ("Ts9d8c2h5d", "T98-2-5"),
    ("Ts9d8c2h7c", "T98-2-7"),
    ("Ts9d8c2hKh", "T98-2-K"),
    ("Ts9d8c4h5c", "T98-4-5"),
    ("Ts9d8c4hKs", "T98-4-K"),
    ("Ts9d8c4hAd", "T98-4-A"),
    ("Ts9d8cQc3h", "T98-Q-3"),
    ("Ts9d8cQc5d", "T98-Q-5"),
    # KJT lines with non-A turn
    ("KsJhTd5c2s", "KJT-5-2"),
    ("KsJhTd5cAh", "KJT-5-A"),
    ("KsJhTd5cQs", "KJT-5-Q"),
    ("KsJhTd5cJs", "KJT-5-J"),
    # KJT-9 + more rivers
    ("KsJhTd9c5d", "KJT-9-5"),
    ("KsJhTd9cJs", "KJT-9-J"),
    # T97-mono (monotone) — fewer rivers but interesting
    ("Td9d7d2h5c", "T97m-2-5"),
    ("Td9d7d2h4c", "T97m-2-4"),
    ("Td9d7d2hAh", "T97m-2-A"),
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
        for board, label in SPOTS:
            # Try both turn cbet sizes
            for turn_actions in ["X-R6.1-C", "X-R2.3-C"]:
                params = dict(BASE)
                params["board"] = board
                params["turn_actions"] = turn_actions
                params["river_actions"] = "X"
                st, d = fetch(client, params)
                statuses[st] = statuses.get(st, 0) + 1
                n_total += 1
                if st == 200 and d:
                    break
                time.sleep(SLEEP)
            else:
                print(f"  PROBE {label}: no valid turn line"); continue

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
                params2["turn_actions"] = turn_actions
                params2["river_actions"] = f"X-{code}"
                fn = OUT / f"{label}_{code}.json"
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
