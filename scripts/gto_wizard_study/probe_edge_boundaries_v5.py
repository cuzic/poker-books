#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""エッジケース境界 v5 — paired board 詳細、wet connected の細分化、3BP 詳細。

【観点】
1. paired board の細分化 (K-K-K, K-K-7, K-K-Q, K-K-T 等)
2. wet connected の細分化 (T98 / 987 / 765 / 432)
3. 3BP の specific preflop sequence (R9.5 / R10.5 等)
4. delayed cbet × river
5. turn vs 多 sizing
"""
from __future__ import annotations
import json, time
from pathlib import Path
import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN = (SCRIPT_DIR / ".token").read_text().strip()
GAID = (SCRIPT_DIR / ".google_anal_id").read_text().strip()
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_edge_boundaries_v5")
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

TARGETS = [
    # === paired board の細分化 (BTN cbet 行動) ===
    ("pair_AAK",    "F-F-F-R2.6-F-C", "", "AsAdKc", "AA-K-? cbet"),
    ("pair_KKQ",    "F-F-F-R2.6-F-C", "", "KsKdQc", "KK-Q cbet"),
    ("pair_KKT",    "F-F-F-R2.6-F-C", "", "KsKdTc", "KK-T cbet"),
    ("pair_QQ7",    "F-F-F-R2.6-F-C", "", "QsQd7c", "QQ-7 cbet"),
    ("pair_998",    "F-F-F-R2.6-F-C", "", "9s9d8c", "99-8 connected pair"),
    ("pair_887",    "F-F-F-R2.6-F-C", "", "8s8d7c", "88-7 connected pair"),
    ("pair_55K",    "F-F-F-R2.6-F-C", "", "5s5dKc", "55-K (lower pair + over)"),
    ("pair_33Q",    "F-F-F-R2.6-F-C", "", "3s3dQc", "33-Q (lowest pair + over)"),

    # === wet connected の細分化 (BTN cbet pre) ===
    ("wet_987",     "F-F-F-R2.6-F-C", "", "9s8d7c", "9-8-7 connected"),
    ("wet_876",     "F-F-F-R2.6-F-C", "", "8s7d6c", "8-7-6"),
    ("wet_765",     "F-F-F-R2.6-F-C", "", "7s6d5c", "7-6-5"),
    ("wet_654",     "F-F-F-R2.6-F-C", "", "6s5d4c", "6-5-4"),
    ("wet_543",     "F-F-F-R2.6-F-C", "", "5s4d3c", "5-4-3"),
    ("wet_432",     "F-F-F-R2.6-F-C", "", "4s3d2c", "4-3-2"),
    ("wet_TJQ",     "F-F-F-R2.6-F-C", "", "TsJdQc", "T-J-Q broadway"),
    ("wet_JQK",     "F-F-F-R2.6-F-C", "", "JsQdKc", "J-Q-K broadway"),

    # === 3BP の preflop sequence 探索 ===
    # try different raise size: R8 / R8.5 / R9 / R9.5 / R10 / R11
    ("3bp_R8_K72",   "F-F-F-R2.6-R8-C", "", "Ks7d2c", "3BP R8 K72"),
    ("3bp_R9_K72",   "F-F-F-R2.6-R9-C", "", "Ks7d2c", "3BP R9 K72"),
    ("3bp_R10_K72",  "F-F-F-R2.6-R10-C","", "Ks7d2c", "3BP R10 K72"),
    ("3bp_R11_K72",  "F-F-F-R2.6-R11-C","", "Ks7d2c", "3BP R11 K72"),

    # === 3BP IP (CO opens, BTN 3-bets) ===
    ("3bp_ip_K72",   "F-F-R2.6-R8-F-F-C", "", "Ks7d2c", "3BP IP (CO open, BTN 3bet)"),

    # === turn vs multiple sizing (BB facing turn cbet after X-R1.9-C) ===
    ("turn_50pct",   "F-F-F-R2.6-F-C", "X-R1.9-C-X-R6", "Ks7d2c3h", "turn BB facing 50% cbet"),
    ("turn_75pct",   "F-F-F-R2.6-F-C", "X-R1.9-C-X-R9", "Ks7d2c3h", "turn BB facing 75%"),
    ("turn_100pct",  "F-F-F-R2.6-F-C", "X-R1.9-C-X-R12", "Ks7d2c3h", "turn BB facing 100%"),

    # === 4BP の sub-board ===
    ("4bp_KQT",     "F-F-F-R2.6-F-R11-R28-C", "", "KsQdTc", "4BP broadway connected"),
    ("4bp_322",     "F-F-F-R2.6-F-R11-R28-C", "", "3s2d2c", "4BP paired low"),
    ("4bp_KK4",     "F-F-F-R2.6-F-R11-R28-C", "", "KsKd4c", "4BP paired K-high"),
    ("4bp_monotone","F-F-F-R2.6-F-R11-R28-C", "", "KsQs2s", "4BP monotone broadway"),

    # === SB open BvB の細分化 (vs cbet) ===
    ("bvb_cbet_K72", "F-F-F-F-R3-C", "X-R1.9", "Ks7d2c", "BvB SB-BB, BB vs SB cbet K72"),
    ("bvb_cbet_T98", "F-F-F-F-R3-C", "X-R1.9", "Ts9d8c", "BvB BB vs cbet T98"),
    ("bvb_cbet_542", "F-F-F-F-R3-C", "X-R1.9", "5d4c2s", "BvB BB vs cbet 5-4-2"),
]


print(f"Edge boundary v5 probe: {len(TARGETS)} spots")
n_ok = n_fail = 0
start = time.time()

for i, t in enumerate(TARGETS, 1):
    label, preflop, flop_acts, board, desc = t
    out = OUT_DIR / f"{label}.json"
    if out.exists():
        print(f"[{i}/{len(TARGETS)}] {label[:25]:25} (cached)")
        n_ok += 1
        continue

    params = {
        "gametype": "Cash6mGeneral_6mNL25R25", "depth": "100",
        "preflop_actions": preflop,
        "flop_actions": flop_acts,
        "turn_actions": "", "river_actions": "",
        "board": board,
    }
    print(f"[{i}/{len(TARGETS)}] {label[:25]:25}", end=" ")
    try:
        r = httpx.get(API, params=params, headers=HEADERS, timeout=30.0)
        if r.status_code == 200:
            data = r.json()
            out.write_text(json.dumps({
                "label": label, "preflop": preflop, "flop_actions": flop_acts,
                "board": board, "description": desc, "data": data,
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
            print(f"✓ {', '.join(summary[:3])}")
            n_ok += 1
        elif r.status_code == 204:
            print("✗ 204")
            n_fail += 1
        elif r.status_code == 401:
            print("✗ 401 TOKEN")
            n_fail += 1
            break
        else:
            print(f"✗ {r.status_code}: {r.text[:50]}")
            n_fail += 1
    except Exception as e:
        print(f"✗ {e}")
        n_fail += 1
    time.sleep(0.3)

print(f"\nDone: {n_ok}/{len(TARGETS)}, {n_fail} fail, {time.time()-start:.0f}s")
