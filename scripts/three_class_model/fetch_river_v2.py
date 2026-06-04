#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""River defense v2 — use actual turn sizes from turn fetch (R6.1, R16.8)."""
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

# (flop+turn+river board, turn_size_code, label)
# Only use boards where turn cbet ≤ 67% (R6.1) — overbet 185% likely all-in to river
RIVER_SPOTS = [
    ("Kd7c2dKs5h", "R6.1", "K72-K-5"),
    ("Kd7c2dKs9c", "R6.1", "K72-K-9"),
    ("Kd7c2d7s4c", "R6.1", "K72-7-4"),
    ("Kd7c2d7sQh", "R6.1", "K72-7-Q"),
    ("Qh8d3s8cKh", "R6.1", "Q83-8-K"),
    ("Qh8d3s8c5d", "R6.1", "Q83-8-5"),
    ("Qh8d3sQc4h", "R6.1", "Q83-Q-4"),
    ("Qh8d3sQcJs", "R6.1", "Q83-Q-J"),
    ("Ts9d8c2h4s", "R6.1", "T98-2-4"),
    ("Ts9d8c2hJh", "R6.1", "T98-2-J"),
    ("Ts9d8cTh3h", "R6.1", "T98-T-3"),
    ("Ts9d8cThKc", "R6.1", "T98-T-K"),
    ("Ts9d8cJc2h", "R6.1", "T98-J-2"),
    ("KsJhTd9cAh", "R6.1", "KJT-9-A"),
    ("KsJhTd9c2h", "R6.1", "KJT-9-2"),
    ("KsJhTdAh3h", "R2.3", "KJT-A-3"),  # KJT-A used 25% turn
    ("KsJhTdAh7c", "R2.3", "KJT-A-7"),
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
    n_ok = 0
    n_total = 0
    statuses = {}
    started = time.time()
    with httpx.Client(headers=HEADERS) as client:
        for board, turn_code, label in RIVER_SPOTS:
            # 1) Probe river bets (river_actions=X)
            params = dict(BASE)
            params["board"] = board
            params["turn_actions"] = f"X-{turn_code}-C"
            params["river_actions"] = "X"
            st, d = fetch(client, params)
            statuses[st] = statuses.get(st, 0) + 1
            n_total += 1
            if st != 200 or not d:
                print(f"  PROBE {label} ({turn_code}): {st} (skip)")
                time.sleep(SLEEP)
                continue
            bet_actions = [a for a in d.get("action_solutions", []) if a.get("action", {}).get("type") in {"RAISE", "BET"}]
            time.sleep(SLEEP)
            if not bet_actions:
                print(f"  {label}: BTN checks river only (no bet sizes)")
                continue
            for ba in bet_actions:
                code = ba["action"]["code"]
                bp = ba["action"].get("betsize_by_pot")
                bp_str = f"{float(bp)*100:.0f}p" if bp else "?"
                params2 = dict(BASE)
                params2["board"] = board
                params2["turn_actions"] = f"X-{turn_code}-C"
                params2["river_actions"] = f"X-{code}"
                fn = OUT / f"{label}_{code}.json"
                if fn.exists():
                    print(f"  SKIP {label} {code} (exists)")
                    continue
                st, d2 = fetch(client, params2)
                statuses[st] = statuses.get(st, 0) + 1
                n_total += 1
                if st == 200 and d2:
                    d2["_meta"] = {"request": params2}
                    fn.write_text(json.dumps(d2))
                    n_ok += 1
                    print(f"  ✓ {label} river={bp_str}({code}): saved")
                else:
                    print(f"  ✗ {label} {code}: {st}")
                time.sleep(SLEEP)
    print(f"\nTotal fetches: {n_total}, saved: {n_ok}, elapsed: {time.time()-started:.1f}s")
    print(f"Statuses: {statuses}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
