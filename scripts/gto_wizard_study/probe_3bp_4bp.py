#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""3BP / 4BP の OOP first-action + BTN cbet + BB defense を probe。

drill cards で使われている全 flops × {3BP, 4BP} を取得。
"""
from __future__ import annotations
import json, time
from pathlib import Path
import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN = (SCRIPT_DIR / ".token").read_text().strip()
GAID = (SCRIPT_DIR / ".google_anal_id").read_text().strip()
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_3bp_4bp")
OUT_DIR.mkdir(parents=True, exist_ok=True)
BTN_DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_drill_btn_cbet")

API = "https://api.gtowizard.com/v4/solutions/spot-solution/"
headers = {
    "authorization": f"Bearer {TOKEN}",
    "google-anal-id": GAID,
    "gwclientid": "930036c8-831c-4fca-8453-b0a298853e86",
    "origin": "https://app.gtowizard.com",
    "referer": "https://app.gtowizard.com/",
    "user-agent": "Mozilla/5.0",
    "accept": "application/json, text/plain, */*",
}

# preflop sequences (corrected)
PRES = {
    "3BP_BTN_BB": "F-F-F-R2.6-F-R11-C",   # BTN open 2.6, BB 3-bet 11, BTN call
    "4BP_BTN_BB": "F-F-F-R2.6-F-R11-R28-C",  # BTN open, BB 3-bet, BTN 4-bet 28, BB call
}

# flops to probe
flops = sorted(set(f.stem.replace("btn_cbet_", "") for f in BTN_DIR.glob("btn_cbet_*.json")))
print(f"Targets: {len(flops)} flops × 2 pot_types = {len(flops)*2} spots")

n_done = n_failed = 0
start = time.time()
for i, flop in enumerate(flops, 1):
    if time.time() - start > 600:
        print(f"\n⏰ cap reached"); break
    for pot_type, pre in PRES.items():
        out = OUT_DIR / f"{pot_type}_{flop}.json"
        if out.exists():
            continue
        print(f"[{i}/{len(flops)}] {flop} {pot_type}", end=" ")
        try:
            r = httpx.get(API, params={"gametype": "Cash6mGeneral_6mNL25R25", "depth": "100",
                                       "preflop_actions": pre, "flop_actions": "", "board": flop},
                          headers=headers, timeout=20.0)
            if r.status_code == 200:
                data = r.json()
                out.write_text(json.dumps({"flop": flop, "pot_type": pot_type, "preflop": pre, "data": data}, ensure_ascii=False))
                actions = data.get("action_solutions", [])
                summary = ", ".join(f"{a['action']['display_name']}={a['total_frequency']*100:.0f}%" for a in actions[:4])
                print(f"✓ ({summary})")
                n_done += 1
            else:
                print(f"✗ HTTP {r.status_code}")
                n_failed += 1
                if r.status_code == 401:
                    break
        except Exception as e:
            print(f"✗ {e}")
            n_failed += 1
        time.sleep(0.3)
    else:
        continue
    break

print(f"\nDone: {n_done} probed, {n_failed} failed, {time.time()-start:.0f}s")
