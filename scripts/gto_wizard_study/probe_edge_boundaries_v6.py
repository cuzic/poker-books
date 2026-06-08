#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""エッジケース境界 v6 — A-high 細分化、monotone 細分化、broadway 区分、特殊 board。

【観点】
1. A-high board の細分化 (A92 / A52 / AT5 / A87 / A65)
2. monotone board の rank 別 (Khh, Qhh, Thh, 8hh)
3. broadway dry の細分化 (KQT / KJT / AJ7 / KQ2)
4. paired_low の細分化 (442, 552, 332, 222, K22)
5. 2-tone board の細分化
6. ace-pair (AA-X) の cbet 行動全 X
"""
from __future__ import annotations
import json, time
from pathlib import Path
import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN = (SCRIPT_DIR / ".token").read_text().strip()
GAID = (SCRIPT_DIR / ".google_anal_id").read_text().strip()
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_edge_boundaries_v6")
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
    # === A-high board の細分化 (BTN cbet pre) ===
    ("A92_rainbow", "F-F-F-R2.6-F-C", "", "As9d2c", "A-9-2 rainbow"),
    ("A52_rainbow", "F-F-F-R2.6-F-C", "", "As5d2c", "A-5-2 (low gap)"),
    ("AT5_rainbow", "F-F-F-R2.6-F-C", "", "AsTd5c", "A-T-5"),
    ("A87_rainbow", "F-F-F-R2.6-F-C", "", "As8d7c", "A-8-7 (connected low)"),
    ("A65_rainbow", "F-F-F-R2.6-F-C", "", "As6d5c", "A-6-5"),
    ("A43_rainbow", "F-F-F-R2.6-F-C", "", "As4d3c", "A-4-3 connected"),
    ("AK2_rainbow", "F-F-F-R2.6-F-C", "", "AsKd2c", "A-K-2 (two broadway)"),
    ("AJT_rainbow", "F-F-F-R2.6-F-C", "", "AsJdTc", "A-J-T (broadway connect)"),

    # === monotone の rank 別 ===
    ("mono_K72s", "F-F-F-R2.6-F-C", "", "Ks7s2s", "K72 monotone"),
    ("mono_Q72s", "F-F-F-R2.6-F-C", "", "Qs7s2s", "Q72 monotone"),
    ("mono_T72s", "F-F-F-R2.6-F-C", "", "Ts7s2s", "T72 monotone"),
    ("mono_872s", "F-F-F-R2.6-F-C", "", "8s7s2s", "8-7-2 monotone"),
    ("mono_A72s", "F-F-F-R2.6-F-C", "", "As7s2s", "A-7-2 monotone"),

    # === broadway dry 細分化 ===
    ("broad_KQT", "F-F-F-R2.6-F-C", "", "KsQdTc", "K-Q-T connected"),
    ("broad_KJT", "F-F-F-R2.6-F-C", "", "KsJdTc", "K-J-T"),
    ("broad_AJ7", "F-F-F-R2.6-F-C", "", "AsJd7c", "A-J-7"),
    ("broad_KQ2", "F-F-F-R2.6-F-C", "", "KsQd2c", "K-Q-2 dry"),
    ("broad_KJ2", "F-F-F-R2.6-F-C", "", "KsJd2c", "K-J-2"),

    # === paired_low 細分化 ===
    ("p_442_BTN", "F-F-F-R2.6-F-C", "", "4s4d2c", "4-4-2"),
    ("p_552_BTN", "F-F-F-R2.6-F-C", "", "5s5d2c", "5-5-2"),
    ("p_222_BTN", "F-F-F-R2.6-F-C", "", "2s2d2c", "2-2-2 trips"),
    ("p_K22_BTN", "F-F-F-R2.6-F-C", "", "Ks2d2c", "K-2-2"),
    ("p_A22_BTN", "F-F-F-R2.6-F-C", "", "As2d2c", "A-2-2"),
    ("p_T22_BTN", "F-F-F-R2.6-F-C", "", "Ts2d2c", "T-2-2"),

    # === 2-tone broadway 細分化 ===
    ("2t_KQT_K", "F-F-F-R2.6-F-C", "", "KsQsTc", "K-Q-T 2tone (K+Q hearts)"),
    ("2t_KJT_K", "F-F-F-R2.6-F-C", "", "KsJsTc", "K-J-T 2tone"),
    ("2t_AT5_A", "F-F-F-R2.6-F-C", "", "AsTs5c", "A-T-5 2tone"),

    # === Ace-pair (AA-X) 全 X ===
    ("AAK_BTN", "F-F-F-R2.6-F-C", "", "AsAdKc", "AA-K"),
    ("AAQ_BTN", "F-F-F-R2.6-F-C", "", "AsAdQc", "AA-Q"),
    ("AAT_BTN", "F-F-F-R2.6-F-C", "", "AsAdTc", "AA-T"),
    ("AA7_BTN", "F-F-F-R2.6-F-C", "", "AsAd7c", "AA-7"),
    ("AA2_BTN", "F-F-F-R2.6-F-C", "", "AsAd2c", "AA-2"),
]


print(f"Edge boundary v6 probe: {len(TARGETS)} spots")
n_ok = n_fail = 0
start = time.time()

for i, (label, preflop, flop_acts, board, desc) in enumerate(TARGETS, 1):
    out = OUT_DIR / f"{label}.json"
    if out.exists():
        print(f"[{i}/{len(TARGETS)}] {label[:22]:22} (cached)")
        n_ok += 1
        continue

    params = {
        "gametype": "Cash6mGeneral_6mNL25R25", "depth": "100",
        "preflop_actions": preflop, "flop_actions": flop_acts,
        "turn_actions": "", "river_actions": "", "board": board,
    }
    print(f"[{i}/{len(TARGETS)}] {label[:22]:22}", end=" ")
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
                t_a = a["action"]["type"]; sz = a["action"].get("betsize", 0); fq = a["total_frequency"] * 100
                if t_a in ("BET","RAISE"): summary.append(f"{t_a[0]}{sz}={fq:.0f}%")
                else: summary.append(f"{t_a[0]}={fq:.0f}%")
            print(f"✓ {', '.join(summary[:3])}")
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
