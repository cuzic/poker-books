#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""MATCHA 5 軸の残り (Bet Sizing / Equity / Defense / Turn-River 境界) を一括 probe。

12 spots 配分:
- Bet Sizing 4 spots: multi-sizing 想定の wet/semi-wet boards (flop)
- Defense 4 spots: BB vs BTN cbet (board 別の defense 分布)
- Turn/River 4 spots: 同 flop の street 別境界
"""
from __future__ import annotations
import json, time
from pathlib import Path
import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN = (SCRIPT_DIR / ".token").read_text().strip()
GAID = (SCRIPT_DIR / ".google_anal_id").read_text().strip()
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_remaining_axes")
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

# Probe targets: (label, preflop, flop_actions, turn_actions, river_actions, board, axis)
TARGETS = [
    # === Bet Sizing 軸: wet board で multi-sizing 想定 ===
    ("bs_T98_flop",     "F-F-F-R2.6-F-C", "",          "", "", "Ts9d8c", "BS"),  # connected wet
    ("bs_J86_flop",     "F-F-F-R2.6-F-C", "",          "", "", "Js8d6c", "BS"),  # semi-wet
    ("bs_654_flop",     "F-F-F-R2.6-F-C", "",          "", "", "6s5d4c", "BS"),  # double-connected
    ("bs_AKQ_flop",     "F-F-F-R2.6-F-C", "",          "", "", "AsKdQc", "BS"),  # broadway connected

    # === Defense 軸: BB facing BTN cbet ===
    # BB vs cbet small (33%): flop_actions = "X-R1.9" (BB to act)
    ("def_K72_vs33",    "F-F-F-R2.6-F-C", "X-R1.9",    "", "", "Ks7d2c", "DEF"),  # dry MERGED
    ("def_T98_vs33",    "F-F-F-R2.6-F-C", "X-R1.9",    "", "", "Ts9d8c", "DEF"),  # wet POLAR
    ("def_542_vs33",    "F-F-F-R2.6-F-C", "X-R1.9",    "", "", "5s4d2c", "DEF"),  # low_dry
    ("def_Q72_vs33",    "F-F-F-R2.6-F-C", "X-R1.9",    "", "", "Qs7d2c", "DEF"),  # broadway_dry

    # === Turn/River 軸: 同 K72 flop の street 別境界 ===
    # Turn brick (3h) after flop bet
    ("tr_K723_turn_betc","F-F-F-R2.6-F-C", "X-R1.9-C",  "",         "", "Ks7d2c3h", "TR"),
    # Turn brick after flop check
    ("tr_K723_turn_chk", "F-F-F-R2.6-F-C", "X-X",       "",         "", "Ks7d2c3h", "TR"),
    # River brick (8s) after flop-bet, turn-bet
    ("tr_K7238_river_2barrel", "F-F-F-R2.6-F-C", "X-R1.9-C", "X-R4.5-C", "", "Ks7d2c3h8s", "TR"),
    # River brick after flop-bet, turn-check
    ("tr_K7238_river_1barrel", "F-F-F-R2.6-F-C", "X-R1.9-C", "X-X",      "", "Ks7d2c3h8s", "TR"),
]

print(f"{len(TARGETS)} probes planned")
n_ok = n_fail = 0
start = time.time()
for i, t in enumerate(TARGETS, 1):
    label, preflop, flop_acts, turn_acts, river_acts, board, axis = t
    out = OUT_DIR / f"{axis}_{label}.json"
    if out.exists():
        print(f"[{i}/{len(TARGETS)}] {label:30} (cached)")
        n_ok += 1
        continue
    params = {
        "gametype": "Cash6mGeneral_6mNL25R25", "depth": "100",
        "preflop_actions": preflop,
        "flop_actions": flop_acts,
        "turn_actions": turn_acts,
        "river_actions": river_acts,
        "board": board,
    }
    print(f"[{i}/{len(TARGETS)}] {label:30}", end=" ")
    try:
        r = httpx.get(API, params=params, headers=HEADERS, timeout=30.0)
        if r.status_code == 200:
            data = r.json()
            out.write_text(json.dumps({
                "label": label, "axis": axis,
                "board": board, "preflop": preflop,
                "flop": flop_acts, "turn": turn_acts, "river": river_acts,
                "data": data,
            }, ensure_ascii=False))
            actions = data.get("action_solutions", [])
            summary = []
            for a in actions:
                t_a = a["action"]["type"]
                sz = a["action"].get("betsize", 0)
                fq = a["total_frequency"] * 100
                if t_a in ("BET","RAISE"):
                    summary.append(f"{t_a[0]}{sz}={fq:.0f}%")
                else:
                    summary.append(f"{t_a[0]}={fq:.0f}%")
            print(f"✓ {', '.join(summary)}")
            n_ok += 1
        elif r.status_code == 204:
            print("✗ 204")
            n_fail += 1
        elif r.status_code == 401:
            print("✗ 401 TOKEN")
            n_fail += 1
            break
        else:
            print(f"✗ {r.status_code}: {r.text[:80]}")
            n_fail += 1
    except Exception as e:
        print(f"✗ {e}")
        n_fail += 1
    time.sleep(0.3)

print(f"\nDone: {n_ok}/{len(TARGETS)}, {n_fail} fail, {time.time()-start:.0f}s")
