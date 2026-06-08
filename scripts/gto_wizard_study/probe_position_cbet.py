#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""各 opener position の cbet を網羅的に probe。

【preflop sequence】 (BB call, defender = BB)
- UTG open: R2.6-F-F-F-F-C
- HJ open:  F-R2.6-F-F-F-C
- CO open:  F-F-R2.6-F-F-C
- BTN open: F-F-F-R2.6-F-C ← baseline
- SB open:  F-F-F-F-R3-C (BvB)

【flop_actions】
- "X" → defender (BB) check 後、opener の cbet decision

【board sets】 baseline 6 boards × 5 positions = 30 spots
"""
from __future__ import annotations
import json, time
from pathlib import Path
import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN = (SCRIPT_DIR / ".token").read_text().strip()
GAID = (SCRIPT_DIR / ".google_anal_id").read_text().strip()
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_position_cbet")
OUT_DIR.mkdir(parents=True, exist_ok=True)

API = "https://api.gtowizard.com/v4/solutions/spot-solution/"
HEADERS = {
    "authorization": f"Bearer {TOKEN}",
    "google-anal-id": GAID,
    "gwclientid": "930036c8-831c-4fca-8453-b0a298853e86",
    "origin": "https://app.gtowizard.com",
    "referer": "https://app.gtowizard.com/",
    "user-agent": "Mozilla/5.0",
    "accept": "application/json, text/plain, */*",
}

POSITIONS = [
    ("UTG", "R2.6-F-F-F-F-C"),
    ("HJ",  "F-R2.6-F-F-F-C"),
    ("CO",  "F-F-R2.6-F-F-C"),
    ("BTN", "F-F-F-R2.6-F-C"),
    ("SB",  "F-F-F-F-R3-C"),
]

BOARDS = [
    ("K72_dry",   "Ks7d2c"),
    ("A72_dry",   "As7d2c"),
    ("AT5_dry",   "AsTd5c"),
    ("T98_conn",  "Ts9d8c"),
    ("542_low",   "5d4c2s"),
    ("AAK_paired","AsAdKc"),
    ("KK2_paired","KsKd2c"),
    ("442_paired","4s4d2c"),
]

TARGETS = [(pos, preflop, board_label, board)
           for pos, preflop in POSITIONS
           for board_label, board in BOARDS]


print(f"Position cbet probe: {len(TARGETS)} spots")
n_ok = n_fail = 0
start = time.time()

for i, (pos, preflop, board_label, board) in enumerate(TARGETS, 1):
    label = f"{pos}_cbet_{board_label}"
    out = OUT_DIR / f"{label}.json"
    if out.exists():
        print(f"[{i}/{len(TARGETS)}] {label[:25]:25} (cached)")
        n_ok += 1
        continue

    params = {
        "gametype": "Cash6mGeneral_6mNL25R25", "depth": "100",
        "preflop_actions": preflop, "flop_actions": "X",
        "turn_actions": "", "river_actions": "", "board": board,
    }
    print(f"[{i}/{len(TARGETS)}] {label[:25]:25}", end=" ")
    try:
        r = httpx.get(API, params=params, headers=HEADERS, timeout=30.0)
        if r.status_code == 200:
            data = r.json()
            out.write_text(json.dumps({
                "label": label, "position": pos, "preflop": preflop,
                "board_label": board_label, "board": board, "data": data,
            }, ensure_ascii=False))
            actions = data.get("action_solutions", [])
            cbet = sum(a["total_frequency"] for a in actions if a["action"]["type"] in ("BET","RAISE"))
            check = sum(a["total_frequency"] for a in actions if a["action"]["type"] == "CHECK")
            sizes = [(a["action"].get("betsize", 0), a["total_frequency"])
                     for a in actions if a["action"]["type"] in ("BET","RAISE")]
            top_size = max(sizes, key=lambda x: x[1])[0] if sizes else "-"
            print(f"✓ cbet={cbet*100:.0f}% (size={top_size}bb) check={check*100:.0f}%")
            n_ok += 1
        elif r.status_code == 204:
            print("✗ 204"); n_fail += 1
        elif r.status_code == 401:
            print("✗ 401 TOKEN"); n_fail += 1; break
        else:
            print(f"✗ {r.status_code}: {r.text[:50]}"); n_fail += 1
    except Exception as e:
        print(f"✗ {e}"); n_fail += 1
    time.sleep(0.3)

print(f"\nDone: {n_ok}/{len(TARGETS)}, {n_fail} fail, {time.time()-start:.0f}s")
