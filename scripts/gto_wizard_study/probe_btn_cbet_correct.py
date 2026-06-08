#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""BTN cbet を正しく probe — flop_actions="X" で BB check 後、BTN の判断を見る。

【正しい sequence】
- preflop: F-F-F-R2.6-F-C (BTN open, BB call)
- flop_actions: "X" (BB check) → 次に act するのは BTN
- BTN は cbet (R1.9 等) or check の選択
"""
from __future__ import annotations
import json, time
from pathlib import Path
import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN = (SCRIPT_DIR / ".token").read_text().strip()
GAID = (SCRIPT_DIR / ".google_anal_id").read_text().strip()
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_btn_cbet_correct")
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

# (label, board, description)
TARGETS = [
    # A-high
    ("btn_A92",   "As9d2c", "A-9-2"),
    ("btn_A52",   "As5d2c", "A-5-2"),
    ("btn_AT5",   "AsTd5c", "A-T-5"),
    ("btn_A87",   "As8d7c", "A-8-7"),
    ("btn_AJT",   "AsJdTc", "A-J-T broadway"),
    # K-high
    ("btn_K72",   "Ks7d2c", "K-7-2 dry baseline"),
    ("btn_KQT",   "KsQdTc", "K-Q-T connected"),
    ("btn_KQ2",   "KsQd2c", "K-Q-2 dry"),
    ("btn_K94",   "Ks9d4c", "K-9-4 dry"),
    # Q-high
    ("btn_Q72",   "Qs7d2c", "Q-7-2"),
    ("btn_QJ9",   "QsJd9c", "Q-J-9 connected"),
    # J-high
    ("btn_J72",   "Js7d2c", "J-7-2"),
    ("btn_J98",   "Js9d8c", "J-9-8 connected"),
    # T-high and below
    ("btn_T72",   "Ts7d2c", "T-7-2"),
    ("btn_T98",   "Ts9d8c", "T-9-8"),
    ("btn_876",   "8s7d6c", "8-7-6 wet"),
    ("btn_765",   "7s6d5c", "7-6-5"),
    ("btn_654",   "6s5d4c", "6-5-4"),
    ("btn_543",   "5s4d3c", "5-4-3"),
    ("btn_432",   "4s3d2c", "4-3-2"),
    # paired
    ("btn_p_AAK", "AsAdKc", "AA-K"),
    ("btn_p_AA2", "AsAd2c", "AA-2"),
    ("btn_p_KKQ", "KsKdQc", "KK-Q"),
    ("btn_p_KK2", "KsKd2c", "KK-2"),
    ("btn_p_887", "8s8d7c", "88-7"),
    ("btn_p_442", "4s4d2c", "44-2"),
    ("btn_p_222", "2s2d2c", "2-2-2 trips"),
    # monotone
    ("btn_K72s",  "Ks7s2s", "K-7-2 monotone"),
    ("btn_T98s",  "Ts9s8s", "T-9-8 monotone"),
    # 2-tone
    ("btn_K72_2t","Ks7s2c", "K-7-2 2tone"),
    ("btn_T98_2t","Ts9s8c", "T-9-8 2tone"),
]


print(f"BTN cbet correct probe: {len(TARGETS)} spots")
n_ok = n_fail = 0
start = time.time()

for i, (label, board, desc) in enumerate(TARGETS, 1):
    out = OUT_DIR / f"{label}.json"
    if out.exists():
        print(f"[{i}/{len(TARGETS)}] {label[:20]:20} (cached)")
        n_ok += 1
        continue

    params = {
        "gametype": "Cash6mGeneral_6mNL25R25", "depth": "100",
        "preflop_actions": "F-F-F-R2.6-F-C",
        "flop_actions": "X",  # BB check first, BTN's decision
        "turn_actions": "", "river_actions": "", "board": board,
    }
    print(f"[{i}/{len(TARGETS)}] {label[:20]:20}", end=" ")
    try:
        r = httpx.get(API, params=params, headers=HEADERS, timeout=30.0)
        if r.status_code == 200:
            data = r.json()
            out.write_text(json.dumps({
                "label": label, "board": board, "description": desc, "data": data,
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
