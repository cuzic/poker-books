#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""Fast turn/river defense fetch — Cash6mGeneral_6mNL25R25 100bb BTN vs BB SRP."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

ROOT = Path("/home/cuzic/poker-books")
TOK = (ROOT / "scripts" / "gto_wizard_study" / ".token").read_text().strip()
OUT_TURN = ROOT / "vol3-mtt-postflop" / "findings" / "def_cash100_bb_turn_raw"
OUT_RIVER = ROOT / "vol3-mtt-postflop" / "findings" / "def_cash100_bb_river_raw"
OUT_TURN.mkdir(parents=True, exist_ok=True)
OUT_RIVER.mkdir(parents=True, exist_ok=True)

API = "https://api.gtowizard.com/v4/solutions/spot-solution/"
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "authorization": f"Bearer {TOK}",
    "origin": "https://app.gtowizard.com",
    "referer": "https://app.gtowizard.com/",
    "gwclientid": "930036c8-831c-4fca-8453-b0a298853e86",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
}
BASE_PARAMS = {
    "gametype": "Cash6mGeneral_6mNL25R25",
    "depth": "100",
    "stacks": "",
    "preflop_actions": "F-F-F-R2.5-F-C",
    "flop_actions": "X-R1.8-C",
    "river_actions": "",
}

# Flops + turn/river cards (using boards we have flop defense for)
TURN_BOARDS = [
    # (flop+turn board, label)
    ("Kd7c2d3h", "K72-3"),   # brick low
    ("Kd7c2dKs", "K72-K"),   # K pair
    ("Kd7c2dAh", "K72-A"),   # overcard A
    ("Kd7c2d7s", "K72-7"),   # pair board
    ("Qh8d3s2h", "Q83-2"),
    ("Qh8d3s8c", "Q83-8"),   # pair
    ("Qh8d3sQc", "Q83-Q"),   # pair Q
    ("Ts9d8c2h", "T98-2"),
    ("Ts9d8cTh", "T98-T"),   # pair
    ("Ts9d8cJc", "T98-J"),   # straight
    ("KsJhTd2c", "KJT-2"),
    ("KsJhTd9c", "KJT-9"),   # straight
    ("KsJhTdAh", "KJT-A"),   # broadway
    ("Jh7d3c2s", "J73-2"),
    ("Jh7d3cJd", "J73-J"),   # pair
    ("Td9d7d2h", "T97-mono"),  # monotone 2-tone backup
    ("Ks5d2c5h", "K52-5p"),   # paired
    ("Ts9s8d3h", "T98-3"),
    ("Qh8d3sJc", "Q83-J"),   # overcard J
    ("Kd7c2dQs", "K72-Q"),   # overcard Q
]

# River boards (flop+turn+river)
RIVER_BOARDS = [
    ("Kd7c2d3h4c", "K72-3-4"),
    ("Kd7c2d3hAs", "K72-3-A"),
    ("Kd7c2dKs5h", "K72-K-5"),
    ("Qh8d3s2hJc", "Q83-2-J"),
    ("Qh8d3s8cKh", "Q83-8-K"),
    ("Ts9d8c2h4s", "T98-2-4"),
    ("Ts9d8cTh3h", "T98-T-3"),
    ("KsJhTd2c5s", "KJT-2-5"),
    ("KsJhTd9cAh", "KJT-9-A"),
    ("Jh7d3c2s4d", "J73-2-4"),
    ("Jh7d3cJdQs", "J73-J-Q"),
    ("Ts9d8c2hAh", "T98-2-A"),
    ("Qh8d3s2h4d", "Q83-2-4"),
    ("KsJhTd9c2h", "KJT-9-2"),
    ("Kd7c2dAhTh", "K72-A-T"),
]

SLEEP = 1.5


def fetch(client: httpx.Client, params: dict) -> tuple[int, dict | None]:
    try:
        r = client.get(API, params=params, timeout=30.0)
        if r.status_code == 200:
            return 200, r.json()
        return r.status_code, None
    except Exception as e:
        print(f"  EXC: {e!r}", file=sys.stderr)
        return -1, None


def slim(data: dict) -> dict:
    """Slim format preserving key fields."""
    return {
        "game": data.get("game"),
        "players_info": data.get("players_info") or [],
        "action_solutions": data.get("action_solutions") or [],
        "hand_categories_range": data.get("hand_categories_range"),
        "draw_categories_range": data.get("draw_categories_range"),
        "blocker_rate": data.get("blocker_rate"),
        "_meta": {"request": dict(params := None) or {}},  # filled by caller
    }


def main() -> int:
    n_total = 0
    n_ok = 0
    statuses: dict = {}
    started = time.time()

    with httpx.Client(headers=HEADERS) as client:
        # ── TURN DEFENSE ──
        print("=== TURN DEFENSE ===")
        for board, label in TURN_BOARDS:
            params = dict(BASE_PARAMS)
            params["turn_actions"] = "X"
            params["board"] = board
            # Probe BTN's available actions
            st, d = fetch(client, params)
            statuses[st] = statuses.get(st, 0) + 1
            n_total += 1
            if st != 200 or not d:
                print(f"  PROBE {label} {board}: {st} (skip)")
                time.sleep(SLEEP)
                continue
            bet_actions = [a for a in d.get("action_solutions", []) if a.get("action", {}).get("type") in {"RAISE", "BET"}]
            if not bet_actions:
                print(f"  PROBE {label}: no bet actions (BTN only checks)")
                time.sleep(SLEEP)
                continue
            time.sleep(SLEEP)
            for ba in bet_actions:
                code = ba["action"]["code"]
                bp = ba["action"].get("betsize_by_pot")
                bp_str = f"{float(bp)*100:.0f}p" if bp else "?"
                params2 = dict(BASE_PARAMS)
                params2["board"] = board
                params2["turn_actions"] = f"X-{code}"
                fn = OUT_TURN / f"{label}_{code}.json"
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
                    print(f"  ✓ {label} bet={bp_str}({code}): saved")
                else:
                    print(f"  ✗ {label} {code}: {st}")
                time.sleep(SLEEP)

        # ── RIVER DEFENSE ──
        print("\n=== RIVER DEFENSE ===")
        for board, label in RIVER_BOARDS:
            params = dict(BASE_PARAMS)
            params["board"] = board
            # Need to know turn_actions for the river spot to load
            # Try: turn cbet 50% then call → river
            for turn_attempt in ["X-R4.5-C", "X-R5-C", "X-R3-C", "X-R6-C"]:
                params["turn_actions"] = turn_attempt
                params["river_actions"] = "X"
                st, d = fetch(client, params)
                statuses[st] = statuses.get(st, 0) + 1
                n_total += 1
                if st == 200 and d:
                    break
                time.sleep(SLEEP)
            else:
                print(f"  RIVER PROBE {label}: no valid turn line")
                time.sleep(SLEEP)
                continue
            # Now check river bet sizes available
            bet_actions = [a for a in d.get("action_solutions", []) if a.get("action", {}).get("type") in {"RAISE", "BET"}]
            time.sleep(SLEEP)
            if not bet_actions:
                print(f"  RIVER {label}: no bet actions (only checks)")
                continue
            for ba in bet_actions:
                code = ba["action"]["code"]
                bp = ba["action"].get("betsize_by_pot")
                bp_str = f"{float(bp)*100:.0f}p" if bp else "?"
                params2 = dict(BASE_PARAMS)
                params2["board"] = board
                params2["turn_actions"] = turn_attempt
                params2["river_actions"] = f"X-{code}"
                fn = OUT_RIVER / f"{label}_{code}.json"
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
                    print(f"  ✓ {label} river_bet={bp_str}({code}): saved")
                else:
                    print(f"  ✗ {label} {code}: {st}")
                time.sleep(SLEEP)

    elapsed = time.time() - started
    print(f"\n=== SUMMARY ===")
    print(f"Total fetches: {n_total}, saved: {n_ok}, elapsed: {elapsed:.1f}s")
    print(f"Status counts: {statuses}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
