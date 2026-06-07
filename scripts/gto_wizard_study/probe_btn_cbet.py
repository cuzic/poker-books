#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""BB check に対する BTN cbet decision を probe。

既存の probe_drill/*.json と同じ boards に対し、flop_actions=X (BB check) を追加して
BTN の cbet sizing/freq を取得する。これが drill card の attacker scenarios に対応。
"""
from __future__ import annotations
import json, time, sys
from pathlib import Path
import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN = (SCRIPT_DIR / ".token").read_text().strip()
GAID = (SCRIPT_DIR / ".google_anal_id").read_text().strip()
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_drill_btn_cbet")
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROBE_DRILL = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_drill")

# unique flops from existing probes
flops: set[str] = set()
for f in PROBE_DRILL.glob("*.json"):
    saved = json.loads(f.read_text())
    flop = saved["spec"].get("flop", "").lower()
    if flop:
        flops.add(flop)

print(f"Unique flops: {len(flops)}")

API = "https://api.gtowizard.com/v4/solutions/spot-solution/"
headers = {
    "authorization": f"Bearer {TOKEN}",
    "google-anal-id": GAID,
    "gwclientid": "930036c8-831c-4fca-8453-b0a298853e86",
    "origin": "https://app.gtowizard.com",
    "referer": "https://app.gtowizard.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/149.0.0.0",
    "accept": "application/json, text/plain, */*",
}

n_done, n_failed = 0, 0
start = time.time()
for i, flop in enumerate(sorted(flops), 1):
    out = OUT_DIR / f"btn_cbet_{flop}.json"
    if out.exists():
        continue
    elapsed = time.time() - start
    if elapsed > 360:  # 6 min cap
        print(f"\n⏰ elapsed {elapsed:.0f}s, stopping")
        break
    params = {
        "gametype": "Cash6mGeneral_6mNL25R25",
        "depth": "100",
        "preflop_actions": "F-F-F-R2.6-F-C",
        "flop_actions": "X",  # BB checks first, BTN decides
        "board": flop,
    }
    print(f"[{i}/{len(flops)}] {flop}", end=" ")
    try:
        r = httpx.get(API, params=params, headers=headers, timeout=30.0)
        if r.status_code == 200:
            data = r.json()
            out.write_text(json.dumps({"flop": flop, "data": data}, ensure_ascii=False))
            actions = data.get("action_solutions", [])
            bet = sum(a["total_frequency"] for a in actions if a["action"]["type"] in ("BET","RAISE"))
            sizes = sorted([(a["action"]["betsize"], a["total_frequency"]) for a in actions if a["action"]["type"] in ("BET","RAISE")], key=lambda x:-x[1])
            main = sizes[0] if sizes else ("-", 0)
            print(f"✓ BTN bet={bet*100:.1f}% size={main[0]}({main[1]*100:.0f}%)")
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

print(f"\nDone: {n_done} probed, {n_failed} failed, {time.time()-start:.0f}s")
