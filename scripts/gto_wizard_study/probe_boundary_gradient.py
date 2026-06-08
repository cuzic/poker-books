#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""境界判定用の gradient probe.

5 軸の境界を実データで明確化するため、各軸でグラデーションを取る:

1. High card gradient: 2-high → ... → A-high で cbet どう変わる?
2. Connectivity gradient: 432 → 642 → 754 → 765 → 876 → 987 で?
3. Pair-high vs pair-low gradient: 224 → 884 → KK4 → AA4
4. Mono vs 2-tone gradient: JsTs4s → JsTs4h → JsTc4s → JsTc4h
"""
from __future__ import annotations
import json, time
from pathlib import Path
import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN = (SCRIPT_DIR / ".token").read_text().strip()
GAID = (SCRIPT_DIR / ".google_anal_id").read_text().strip()
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_boundary_gradient")
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

# Boundary gradient boards
BOARDS = [
    # ── High card gradient (all unconnected, rainbow) ──
    ("2s3d4c", "high_2", "high card gradient"),
    ("4s5d6c", "high_4", "high card gradient (low connected)"),
    ("6s7d8c", "high_6", "high card gradient (mid connected)"),
    ("8s9dtc", "high_8", "high card gradient (mid-high connected)"),
    ("tsjdqc", "high_T", "high card gradient (broadway connected)"),
    ("ahkdqc", "high_A", "high card gradient (broadway top)"),
    # ── Connectivity gradient (low cards) ──
    ("4s3d2c", "connectivity_max",  "connectivity gradient"),
    ("6s4d2c", "connectivity_3gap", "connectivity gradient"),
    ("7s5d2c", "connectivity_4gap", "connectivity gradient"),
    ("9s5d2c", "connectivity_spread","connectivity gradient"),
    # ── Pair-high gradient (paired boards) ──
    ("2s2d4c", "pair_low",  "pair height gradient"),
    ("5s5d4c", "pair_mid",  "pair height gradient"),
    ("8s8d4c", "pair_high_mid", "pair height gradient"),
    ("ksKd4c", "pair_high",    "pair height gradient"),
    ("asAd4c", "pair_ace",     "pair height gradient"),
    # ── Suit gradient (JT4 base) ──
    ("jststs", "mono_extreme", "suit gradient (NOTE: invalid, will skip)"),
    # ── A-high subtle gradient ──
    ("as7d2c", "ace_dry",     "ace-high gradient"),
    ("as9d2c", "ace_loose",   "ace-high gradient"),
    ("as9d6c", "ace_connect", "ace-high gradient"),
    # ── K-high gradient ──
    ("ks2d3c", "K_dry_low",   "K-high gradient"),
    ("ks7d2c", "K_dry_mid",   "K-high gradient"),
    ("ks9d8c", "K_connect",   "K-high gradient"),
]


def probe(board: str, label: str, category: str) -> bool:
    out_file = OUT_DIR / f"grad_{label}_{board}.json"
    if out_file.exists():
        return True
    params = {
        "gametype": "Cash6mGeneral_6mNL25R25",
        "depth": "100",
        "preflop_actions": "F-F-F-R2.6-F-C",
        "flop_actions": "X",  # BB checks first, BTN decides
        "board": board,
    }
    try:
        r = httpx.get(API, params=params, headers=HEADERS, timeout=30.0)
        if r.status_code == 200:
            data = r.json()
            out_file.write_text(json.dumps({
                "board": board, "label": label, "category": category,
                "data": data,
            }, ensure_ascii=False))
            return True
        elif r.status_code == 401:
            print(f"  ✗ TOKEN EXPIRED")
            return False
        else:
            print(f"  ✗ {board}: HTTP {r.status_code} {r.text[:80]}")
            return False
    except Exception as e:
        print(f"  ✗ {board}: {e}")
        return False


start = time.time()
n_ok = n_fail = 0
for board, label, cat in BOARDS:
    if time.time() - start > 600:
        print("⏰ time cap"); break
    # Skip invalid boards
    if len(set(board.lower())) < 6:
        # duplicate card? skip
        if len(set([board[i*2:i*2+2] for i in range(3)])) < 3:
            print(f"⊘ skip invalid: {board}")
            continue
    print(f"[{cat[:25]:25}] {label:20} {board}", end=" ")
    if probe(board, label, cat):
        # quick summary
        f = OUT_DIR / f"grad_{label}_{board}.json"
        if f.exists():
            saved = json.loads(f.read_text())
            actions = saved["data"]["action_solutions"]
            cbet = sum(a["total_frequency"] for a in actions if a["action"]["type"] in ("BET","RAISE"))
            sizes = sorted([(a["action"]["betsize"], a["total_frequency"]) for a in actions if a["action"]["type"] in ("BET","RAISE")], key=lambda x:-x[1])
            top = sizes[0] if sizes else ("-", 0)
            print(f"✓ cbet={cbet*100:.0f}% top_size={top[0]}({top[1]*100:.0f}%)")
        n_ok += 1
    else:
        n_fail += 1
        if n_fail >= 3:
            break  # likely token expired
    time.sleep(0.3)

print(f"\nDone: {n_ok}/{len(BOARDS)}, {time.time()-start:.0f}s")
