#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""BB の defense decision (BTN cbet 受け) を probe。

flop_actions に BTN cbet の actual sizing (33%, 75% など) を入れて、
BB の fold/call/raise 決定を取得。drill cards の defender scenarios に対応。

依存: probe_drill_btn_cbet/*.json (BTN cbet の dominant sizing 確認用)
"""
from __future__ import annotations
import json, time
from pathlib import Path
import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN = (SCRIPT_DIR / ".token").read_text().strip()
GAID = (SCRIPT_DIR / ".google_anal_id").read_text().strip()
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_drill_bb_defense")
OUT_DIR.mkdir(parents=True, exist_ok=True)

BTN_CBET_DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_drill_btn_cbet")

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


def get_btn_cbet_size(flop: str) -> str | None:
    """BTN cbet probe から dominant raise size を取得。"""
    f = BTN_CBET_DIR / f"btn_cbet_{flop}.json"
    if not f.exists():
        return None
    saved = json.loads(f.read_text())
    actions = saved.get("data", {}).get("action_solutions", [])
    raises = [(a["action"]["betsize"], a["total_frequency"]) for a in actions
              if a["action"]["type"] in ("BET", "RAISE")]
    if not raises:
        return None
    raises.sort(key=lambda x: -x[1])
    return raises[0][0]


flops = sorted(set(f.stem.replace("btn_cbet_", "") for f in BTN_CBET_DIR.glob("btn_cbet_*.json")))
print(f"Targets: {len(flops)} flops")

n_done, n_failed = 0, 0
start = time.time()
for i, flop in enumerate(flops, 1):
    if time.time() - start > 480:  # 8 min cap
        print(f"\n⏰ stopping ({time.time()-start:.0f}s elapsed)")
        break
    cbet_size = get_btn_cbet_size(flop)
    if not cbet_size or float(cbet_size) == 0:
        print(f"[{i}/{len(flops)}] {flop}: no BTN cbet → skip")
        continue
    flop_actions = f"X-R{cbet_size}"
    out = OUT_DIR / f"bb_def_{flop}_R{cbet_size}.json"
    if out.exists():
        continue
    print(f"[{i}/{len(flops)}] {flop} R{cbet_size}", end=" ")
    params = {
        "gametype": "Cash6mGeneral_6mNL25R25",
        "depth": "100",
        "preflop_actions": "F-F-F-R2.6-F-C",
        "flop_actions": flop_actions,
        "board": flop,
    }
    try:
        r = httpx.get(API, params=params, headers=headers, timeout=30.0)
        if r.status_code == 200:
            data = r.json()
            out.write_text(json.dumps({"flop": flop, "cbet_size": cbet_size, "data": data}, ensure_ascii=False))
            actions = data.get("action_solutions", [])
            f_freq = sum(a["total_frequency"] for a in actions if a["action"]["type"] == "FOLD")
            c_freq = sum(a["total_frequency"] for a in actions if a["action"]["type"] == "CALL")
            r_freq = sum(a["total_frequency"] for a in actions if a["action"]["type"] == "RAISE")
            print(f"✓ F={f_freq*100:.0f}% C={c_freq*100:.0f}% R={r_freq*100:.0f}%")
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
