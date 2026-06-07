#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""PROBE_TARGETS.json に基づいて GTO Wizard API で probe 実行。

各 spec (flop × scenario_type) について:
- SRP / 3BP / 4BP の preflop_actions を構築
- flop_actions で各 cbet sizing を試行 (= aggressor 視点 + defender 視点)
- raw JSON を knowledges/gto_wizard_study/probe_drill/<spec_id>.json に保存

token は 15 分 expire なので、 batch 完了前に re-token 要請する可能性あり。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN_FILE = SCRIPT_DIR / ".token"
GAID_FILE = SCRIPT_DIR / ".google_anal_id"
PROBE_TARGETS = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/PROBE_TARGETS.json")
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_drill")

API = "https://api.gtowizard.com/v4/solutions/spot-solution/"
GAMETYPE_CASH = "Cash6mGeneral_6mNL25R25"
GAMETYPE_MTT = "MTTGeneral_8m"


# preflop_actions の templates (gametype × scenario_type → preflop_actions)
# 6m table の position: UTG, HJ, CO, BTN, SB, BB (in order)
PREFLOP_ACTIONS = {
    "SRP_BTN_open": "F-F-F-R2.6-F-C",       # BTN open vs BB call
    "SRP_CO_open":  "F-F-R2.4-F-F-C",       # CO open vs BB call
    "SRP_HJ_open":  "F-R2.2-F-F-F-C",       # HJ open vs BB call
    "SRP_UTG_open": "R2.2-F-F-F-F-C",       # UTG open vs BB call
    "3BP_BTN_BB":   "F-F-F-R2.6-F-R13.2-F-C", # BTN open, BB 3-bet, BTN call
    "4BP_BTN_BB":   "F-F-F-R2.6-F-R13.2-R30-F-C", # BTN open, BB 3-bet, BTN 4-bet, BB call
    "3BP_CO_BTN":   "F-F-R2.4-R10-F-F-F-C",  # CO open, BTN 3-bet — needs adjustment
}


def load_token() -> tuple[str, str]:
    return TOKEN_FILE.read_text().strip(), GAID_FILE.read_text().strip()


def call_api(token: str, gaid: str, gametype: str, depth: str, preflop: str, flop_actions: str, board: str) -> dict | None:
    headers = {
        "authorization": f"Bearer {token}",
        "google-anal-id": gaid,
        "gwclientid": "930036c8-831c-4fca-8453-b0a298853e86",
        "origin": "https://app.gtowizard.com",
        "referer": "https://app.gtowizard.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0",
        "accept": "application/json, text/plain, */*",
    }
    params = {
        "gametype": gametype,
        "depth": depth,
        "preflop_actions": preflop,
        "flop_actions": flop_actions,
        "board": board,
    }
    try:
        r = httpx.get(API, params=params, headers=headers, timeout=30.0)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"  ✗ HTTP {r.status_code}: {r.text[:200]}")
            return None
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        return None


def build_probe_id(spec: dict, suffix: str = "") -> str:
    """spec から file 名用 ID を組み立て。"""
    flop = spec.get("flop", "unknown")
    scn = spec.get("scenario_type", "unknown").replace("+", "_")
    purpose = spec.get("purpose", "x")[:5]
    base = f"{purpose}_{flop}_{scn}"
    if suffix:
        base += f"_{suffix}"
    return base


# Each spec → list of (preflop_template, gametype, depth, suffix)
def derive_api_calls(spec: dict) -> list[tuple[str, str, str, str]]:
    """spec → list of (preflop_actions_template_name, gametype, depth, suffix)"""
    scn = spec.get("scenario_type", "")
    calls: list[tuple[str, str, str, str]] = []
    # default: BTN open SRP / 3BP / 4BP
    if "SRP" in scn:
        calls.append(("SRP_BTN_open", GAMETYPE_CASH, "100", "btn_v_bb"))
    if "3BP" in scn:
        calls.append(("3BP_BTN_BB", GAMETYPE_CASH, "100", "btn_v_bb_3bp"))
    if "4BP" in scn:
        calls.append(("4BP_BTN_BB", GAMETYPE_CASH, "100", "btn_v_bb_4bp"))
    if "boundary" in spec.get("purpose", ""):
        # boundary も SRP + 3BP + 4BP 各 1 つ
        calls.extend([
            ("SRP_BTN_open", GAMETYPE_CASH, "100", "btn_v_bb_srp"),
            ("3BP_BTN_BB", GAMETYPE_CASH, "100", "btn_v_bb_3bp"),
            ("4BP_BTN_BB", GAMETYPE_CASH, "100", "btn_v_bb_4bp"),
        ])
    return calls


def main() -> None:
    if not PROBE_TARGETS.exists():
        print(f"✗ {PROBE_TARGETS} not found. Run plan_probe_targets.py first.")
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    specs = json.loads(PROBE_TARGETS.read_text())
    token, gaid = load_token()
    print(f"Loaded {len(specs)} specs from PROBE_TARGETS.json")
    print(f"Output dir: {OUT_DIR}")

    # priority sort
    specs_sorted = sorted(specs, key=lambda s: (s.get("priority", 9), -s.get("n_drill_cards", 0)))

    n_done = 0
    n_skipped = 0
    n_failed = 0
    start_time = time.time()

    # rate limit: pause between calls
    for i, spec in enumerate(specs_sorted, 1):
        flop = spec.get("flop")
        if not flop:
            continue
        calls = derive_api_calls(spec)

        # token age check (refresh every 10 min)
        elapsed = time.time() - start_time
        if elapsed > 600:
            print(f"\n⚠ {elapsed:.0f}s elapsed, token may be near expiration. Stopping for safety.")
            break

        for preflop_name, gametype, depth, suffix in calls:
            probe_id = build_probe_id(spec, suffix)
            out_path = OUT_DIR / f"{probe_id}.json"
            if out_path.exists():
                n_skipped += 1
                continue

            preflop = PREFLOP_ACTIONS.get(preflop_name)
            if not preflop:
                print(f"  ⚠ unknown template: {preflop_name}")
                continue

            print(f"[{i}/{len(specs_sorted)}] {probe_id} (flop={flop}, scn={spec.get('scenario_type')})")
            data = call_api(token, gaid, gametype, depth, preflop, "", flop)
            if data is None:
                n_failed += 1
                continue

            # 保存
            out_path.write_text(json.dumps({
                "spec": spec,
                "probe_id": probe_id,
                "api_params": {"gametype": gametype, "depth": depth, "preflop_actions": preflop, "board": flop},
                "response_keys": list(data.keys()),
                "n_actions": len(data.get("action_solutions", [])),
                "data": data,
            }, ensure_ascii=False, indent=2))
            n_done += 1
            print(f"  ✓ saved {probe_id} ({len(data.get('action_solutions', []))} actions)")

            # rate limit
            time.sleep(0.5)

    print(f"\n=== Done ===")
    print(f"  probed: {n_done}")
    print(f"  skipped (already exist): {n_skipped}")
    print(f"  failed: {n_failed}")
    print(f"  elapsed: {time.time()-start_time:.0f}s")


if __name__ == "__main__":
    main()
