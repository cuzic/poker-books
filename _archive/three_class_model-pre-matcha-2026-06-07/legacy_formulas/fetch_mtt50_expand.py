#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""Expand MTT 50bb defense — fetch additional 36+ turn and 37+ river spots."""
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

# ── Additional turn boards (36+ new) ──
# Reuse existing flops, add new turn cards + new flops
TURN_BOARDS_NEW = [
    # K72 turn cards we haven't fetched
    ("Kd7c2dQs", "K72-Q"),
    ("Kd7c2d5h", "K72-5"),
    ("Kd7c2d9c", "K72-9"),
    ("Kd7c2dJs", "K72-J"),
    # Q83
    ("Qh8d3sAh", "Q83-A"),
    ("Qh8d3s5c", "Q83-5"),
    ("Qh8d3sTd", "Q83-T"),
    # T98
    ("Ts9d8c4h", "T98-4"),
    ("Ts9d8cKs", "T98-K"),
    ("Ts9d8c5d", "T98-5"),
    ("Ts9d8cQc", "T98-Q"),
    ("Ts9d8c6h", "T98-6"),
    # KJT
    ("KsJhTd5c", "KJT-5"),
    ("KsJhTd3s", "KJT-3"),
    ("KsJhTd7h", "KJT-7"),
    # J73
    ("Jh7d3c4d", "J73-4"),
    ("Jh7d3cAh", "J73-A"),
    ("Jh7d3cKs", "J73-K"),
    # New flops we don't have yet
    ("Ad6h2c5s", "A62-5"),    # A-high dry
    ("Ad6h2cKh", "A62-K"),
    ("Ad6h2c3d", "A62-3"),    # gutshot completing
    ("As9d4c2h", "A94-2"),    # A-high mid
    ("As9d4c8c", "A94-8"),    # straight draw complete
    ("As9d4cKh", "A94-K"),
    ("Th6d2s4h", "T62-4"),    # T-high low
    ("Th6d2s9c", "T62-9"),
    ("9h6d2sJc", "962-J"),    # low straight complete
    ("9h6d2s4h", "962-4"),
    ("Qd9c7h2s", "Q97-2"),    # Q-high
    ("Qd9c7hKs", "Q97-K"),
    ("Qd9c7hJh", "Q97-J"),    # straight complete
    ("Js8d4cKh", "J84-K"),    # J-high
    ("Js8d4c2s", "J84-2"),
    ("Th9d4s7c", "T94-7"),    # straight complete
    ("Th9d4s2h", "T94-2"),
    ("8h4d3s2c", "843-2"),    # low pair
    ("8h4d3sKs", "843-K"),
    ("Ks5d2c4h", "K52-4"),
    ("Ks5d2c9s", "K52-9"),
]

# ── Additional river boards (37+ new) ──
RIVER_BOARDS_NEW = [
    # New river cards on existing turn lines
    ("Kd7c2dKs7c", "K72-K-7"),  # backdoor pair
    ("Kd7c2dKsAh", "K72-K-A"),
    ("Kd7c2d7s2s", "K72-7-2"),  # board pair
    ("Kd7c2d7sAh", "K72-7-A"),
    ("Qh8d3sQc8d", "Q83-Q-8"),
    ("Qh8d3sQcAh", "Q83-Q-A"),
    ("Ts9d8c2hAh", "T98-2-A"),
    ("Ts9d8c2hKh", "T98-2-K"),
    ("Ts9d8c2h7s", "T98-2-7"),
    ("Ts9d8cTh2s", "T98-T-2"),
    ("Ts9d8cThKc", "T98-T-K"),
    ("Ts9d8cThAh", "T98-T-A"),
    ("Ts9d8cJc3h", "T98-J-3"),
    ("Ts9d8cJc4s", "T98-J-4"),
    ("KsJhTd9cAs", "KJT-9-A2"),  # diff suit
    ("KsJhTd9c5s", "KJT-9-5"),
    ("KsJhTd9cJs", "KJT-9-J"),
    ("KsJhTd2cAh", "KJT-2-A"),
    ("KsJhTd2c5s", "KJT-2-5"),
    ("KsJhTd2cQs", "KJT-2-Q"),
    # New flops
    ("Ad6h2c5s4h", "A62-5-4"),
    ("Ad6h2c5sAh", "A62-5-A"),
    ("As9d4c2h7s", "A94-2-7"),
    ("As9d4c2hKh", "A94-2-K"),
    ("Th6d2s4h9c", "T62-4-9"),
    ("Th6d2s4hAh", "T62-4-A"),
    ("9h6d2s4h3s", "962-4-3"),
    ("Qd9c7h2sJh", "Q97-2-J"),
    ("Qd9c7h2sAh", "Q97-2-A"),
    ("Qd9c7hKsAh", "Q97-K-A"),
    ("Js8d4cKh3s", "J84-K-3"),
    ("Js8d4cKhAh", "J84-K-A"),
    ("Th9d4s7c2h", "T94-7-2"),
    ("Th9d4s7c8s", "T94-7-8"),
    ("8h4d3s2c5h", "843-2-5"),
    ("8h4d3sKsAh", "843-K-A"),
    ("Ks5d2c4h7c", "K52-4-7"),
    ("Ks5d2c4hAh", "K52-4-A"),
]

SLEEP = 1.0


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
        # Turn defense expansion
        print("=== MTT 50bb TURN DEFENSE (expansion) ===")
        for board, label in TURN_BOARDS_NEW:
            # Check if any file exists for this board
            existing = list(OUT_T.glob(f"{label}_*.json"))
            if existing:
                print(f"  SKIP {label} (already has {len(existing)} file(s))")
                continue
            params = dict(BASE)
            params["turn_actions"] = "X"
            params["river_actions"] = ""
            params["board"] = board
            st, d = fetch(client, params)
            statuses[st] = statuses.get(st, 0) + 1
            n_total += 1
            if st != 200 or not d:
                print(f"  PROBE {label}: {st}"); time.sleep(SLEEP); continue
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
                if fn.exists(): continue
                st, d2 = fetch(client, params2)
                statuses[st] = statuses.get(st, 0) + 1
                n_total += 1
                if st == 200 and d2:
                    d2["_meta"] = {"request": params2}
                    fn.write_text(json.dumps(d2))
                    n_ok += 1
                    print(f"  ✓ {label} bet={bp_str}({code})")
                time.sleep(SLEEP)

        # River defense expansion
        print("\n=== MTT 50bb RIVER DEFENSE (expansion) ===")
        for board, label in RIVER_BOARDS_NEW:
            existing = list(OUT_R.glob(f"{label}_*.json"))
            if existing:
                print(f"  SKIP {label} (already has {len(existing)} file(s))")
                continue
            chosen_turn = None
            d = None
            for turn_attempt in ["X-R2.3-C", "X-R10.6-C"]:
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
                print(f"  PROBE {label}: no valid turn line"); continue
            bet_actions = [a for a in d.get("action_solutions", []) if a.get("action", {}).get("type") in {"RAISE", "BET"}]
            time.sleep(SLEEP)
            if not bet_actions:
                print(f"  {label}: no river bet"); continue
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
