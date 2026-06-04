#!/usr/bin/env python3
"""
ターン cbet 2nd barrel データ収集 (MTT6mSimple BTN vs BB SRP25bb)

シナリオ: BTN open, BB call → flop X-cbet-C → turn X → BTN 2nd barrel 判断
6 flops × 5 representative turn cards = 30 spots
"""
import json, time, argparse, sys
from pathlib import Path
from collections import defaultdict
from typing import Any
import httpx

SCRIPT_DIR = Path(__file__).parent
TOKEN_FILE = Path("/home/cuzic/poker-books/scripts/gto_wizard_study/.token")
REFRESH_TOKEN_FILE = Path("/home/cuzic/poker-books/scripts/gto_wizard_study/.refresh_token")
GOOGLE_ANAL_ID_FILE = Path("/home/cuzic/poker-books/scripts/gto_wizard_study/.google_anal_id")

FINDINGS = SCRIPT_DIR / "findings"
BASE_URL = "https://api.gtowizard.com/v4/solutions/spot-solution/"

# プロファイル: turn cbet 2nd barrel (BTN IP, BB checked turn)
PROFILES = {
    "mtt25_btn": {
        "gametype": "MTT6mSimple", "depth": "25.125",
        "stacks": "25.125-25.125-25.125-25.125-25.125-25.125",
        "pf": "F-F-F-R2.1-F-C",
        "out_file": "draw_study_TURN_MTT25_BTN.jsonl",
        "raw_dir": "turn_mtt25_btn_raw",
    },
    "mtt50_btn": {
        "gametype": "MTT6mSimple", "depth": "50.125",
        "stacks": "50.125-50.125-50.125-50.125-50.125-50.125",
        "pf": "F-F-F-R2.5-F-C",
        "out_file": "draw_study_TURN_MTT50_BTN.jsonl",
        "raw_dir": "turn_mtt50_btn_raw",
    },
    "mtt100_btn": {
        "gametype": "MTT6mSimple", "depth": "100.125",
        "stacks": "100.125-100.125-100.125-100.125-100.125-100.125",
        "pf": "F-F-F-R2.5-F-C",
        "out_file": "draw_study_TURN_MTT100_BTN.jsonl",
        "raw_dir": "turn_mtt100_btn_raw",
    },
    "cash100_btn": {
        "gametype": "Cash6mGeneral_6mNL25R25", "depth": "100",
        "stacks": "",
        "pf": "F-F-F-R2.5-F-C",
        "out_file": "draw_study_TURN_CASH100_BTN.jsonl",
        "raw_dir": "turn_cash100_btn_raw",
    },
}

# 代表 flop × turn cards (BTN cbet small ~33% pot に固定)
TURN_SPOTS = [
    # K72r (型1 high-dry rainbow)
    {"id": "K72r_K", "flop": "Ks7d2c", "turn": "Kd", "label": "K72r→K (top pair)"},
    {"id": "K72r_7", "flop": "Ks7d2c", "turn": "7h", "label": "K72r→7 (mid pair)"},
    {"id": "K72r_2", "flop": "Ks7d2c", "turn": "2h", "label": "K72r→2 (low pair)"},
    {"id": "K72r_A", "flop": "Ks7d2c", "turn": "Ah", "label": "K72r→A (overcard)"},
    {"id": "K72r_8", "flop": "Ks7d2c", "turn": "8h", "label": "K72r→8 (blank)"},
    # T98r (型4 mid-wet connected)
    {"id": "T98r_T", "flop": "Th9s8d", "turn": "Tc", "label": "T98r→T"},
    {"id": "T98r_J", "flop": "Th9s8d", "turn": "Jc", "label": "T98r→J (straight card)"},
    {"id": "T98r_7", "flop": "Th9s8d", "turn": "7c", "label": "T98r→7 (straight)"},
    {"id": "T98r_A", "flop": "Th9s8d", "turn": "Ac", "label": "T98r→A (overcard)"},
    {"id": "T98r_2", "flop": "Th9s8d", "turn": "2c", "label": "T98r→2 (blank)"},
    # Q83 (型3 mid mixed)
    {"id": "Q83_Q", "flop": "Qh8d3s", "turn": "Qc", "label": "Q83→Q"},
    {"id": "Q83_8", "flop": "Qh8d3s", "turn": "8c", "label": "Q83→8"},
    {"id": "Q83_K", "flop": "Qh8d3s", "turn": "Kc", "label": "Q83→K (overcard)"},
    {"id": "Q83_A", "flop": "Qh8d3s", "turn": "Ac", "label": "Q83→A"},
    {"id": "Q83_2", "flop": "Qh8d3s", "turn": "2c", "label": "Q83→2 (blank)"},
    # K98r (型2 high-wet)
    {"id": "K98r_K", "flop": "Kd9s8c", "turn": "Kh", "label": "K98r→K"},
    {"id": "K98r_T", "flop": "Kd9s8c", "turn": "Tc", "label": "K98r→T (straight card)"},
    {"id": "K98r_7", "flop": "Kd9s8c", "turn": "7c", "label": "K98r→7 (straight)"},
    {"id": "K98r_A", "flop": "Kd9s8c", "turn": "Ah", "label": "K98r→A (overcard)"},
    {"id": "K98r_2", "flop": "Kd9s8c", "turn": "2h", "label": "K98r→2 (blank)"},
    # KJT (型6 high-broadway-connected)
    {"id": "KJT_K", "flop": "KhJdTs", "turn": "Kc", "label": "KJT→K"},
    {"id": "KJT_Q", "flop": "KhJdTs", "turn": "Qc", "label": "KJT→Q (straight)"},
    {"id": "KJT_9", "flop": "KhJdTs", "turn": "9c", "label": "KJT→9 (straight)"},
    {"id": "KJT_A", "flop": "KhJdTs", "turn": "Ac", "label": "KJT→A (broadway A)"},
    {"id": "KJT_2", "flop": "KhJdTs", "turn": "2c", "label": "KJT→2 (blank)"},
    # AA7 (型7 paired)
    {"id": "AA7_A", "flop": "AhAd7c", "turn": "As", "label": "AA7→A (quads possible)"},
    {"id": "AA7_7", "flop": "AhAd7c", "turn": "7d", "label": "AA7→7 (full house)"},
    {"id": "AA7_K", "flop": "AhAd7c", "turn": "Kd", "label": "AA7→K (overcard)"},
    {"id": "AA7_2", "flop": "AhAd7c", "turn": "2d", "label": "AA7→2 (blank)"},
    {"id": "AA7_5", "flop": "AhAd7c", "turn": "5d", "label": "AA7→5 (blank)"},
]


def refresh_token():
    if not REFRESH_TOKEN_FILE.exists():
        return None
    refresh = REFRESH_TOKEN_FILE.read_text().strip()
    ga = GOOGLE_ANAL_ID_FILE.read_text().strip() if GOOGLE_ANAL_ID_FILE.exists() else ""
    try:
        r = httpx.post(
            "https://api.gtowizard.com/v1/token/refresh/",
            json={"refresh": refresh},
            headers={
                "content-type": "application/json",
                "gwclientid": "930036c8-831c-4fca-8453-b0a298853e86",
                "google-anal-id": ga,
                "origin": "https://app.gtowizard.com",
                "referer": "https://app.gtowizard.com/",
                "user-agent": "Mozilla/5.0",
            }, timeout=15.0)
        if r.status_code == 200:
            access = r.json().get("access")
            if access:
                TOKEN_FILE.write_text(access)
                return access
    except Exception:
        pass
    return None


def headers(token):
    return {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token}",
        "google-anal-id": GOOGLE_ANAL_ID_FILE.read_text().strip(),
        "gwclientid": "930036c8-831c-4fca-8453-b0a298853e86",
        "origin": "https://app.gtowizard.com",
        "referer": "https://app.gtowizard.com/",
        "user-agent": "Mozilla/5.0",
    }


def call_api(client, params, max_retries=5):
    backoff = 2.0
    for _ in range(max_retries):
        try:
            r = client.get(BASE_URL, params=params, timeout=30.0)
            if r.status_code == 200:
                return 200, r.json()
            if r.status_code == 401:
                new = refresh_token()
                if new:
                    client.headers["authorization"] = f"Bearer {new}"
                    continue
                return 401, None
            if r.status_code == 429:
                time.sleep(backoff); backoff *= 2; continue
            return r.status_code, None
        except Exception:
            time.sleep(backoff); backoff *= 2
    return 0, None


def compute_hand_agg(data):
    dcr = data.get("draw_categories_range", [])
    hcr = data.get("hand_categories_range", [])
    as_ = data.get("action_solutions", [])
    hand_map = {}
    strategies = {}
    for item in as_:
        code = item["action"]["code"]
        strategies[code] = item.get("strategy", [])
        if not hand_map:
            for h in (item.get("hand_categories") or []):
                hand_map[h["index"]] = h["name"]
    bet_codes = [c for c in strategies if c != "X"]
    hand_agg = defaultdict(lambda: {"total": 0.0, "bet": 0.0})
    n_in = 0
    for i in range(min(1326, len(dcr), len(hcr))):
        total = sum(s[i] for s in strategies.values() if i < len(s))
        if total < 0.001: continue
        n_in += 1
        bet_f = sum(strategies[c][i] for c in bet_codes if i < len(strategies[c]))
        h_name = hand_map.get(hcr[i], f"unk_{hcr[i]}")
        hand_agg[h_name]["total"] += 1
        hand_agg[h_name]["bet"] += bet_f
    return {
        "hand_agg": {k: {"total": v["total"],
                         "bet_pct": v["bet"]/v["total"]*100 if v["total"] > 0 else 0}
                     for k, v in hand_agg.items()},
        "n_combos": n_in,
    }


def detect_flop_bet_size(client, profile, flop):
    p = {
        "gametype": profile["gametype"], "depth": profile["depth"],
        "stacks": profile["stacks"], "preflop_actions": profile["pf"],
        "flop_actions": "X", "turn_actions": "", "river_actions": "",
        "board": flop,
    }
    status, data = call_api(client, p)
    if status != 200 or not data:
        return None
    sizes = []
    for s in data.get("action_solutions", []):
        c = s["action"]["code"]
        if c.startswith("R"):
            try:
                sizes.append((float(c[1:]), c))
            except ValueError:
                pass
    if not sizes:
        return None
    sizes.sort()
    return sizes[0][1]


def collect(profile_name: str):
    profile = PROFILES[profile_name]
    out_file = FINDINGS / profile["out_file"]
    raw_dir = FINDINGS / profile["raw_dir"]
    raw_dir.mkdir(parents=True, exist_ok=True)
    FINDINGS.mkdir(parents=True, exist_ok=True)
    token = TOKEN_FILE.read_text().strip()

    flop_size_cache = {}
    results = []

    with httpx.Client(headers=headers(token)) as client:
        for i, spot in enumerate(TURN_SPOTS):
            flop = spot["flop"]
            turn = spot["turn"]
            board = flop + turn

            if flop not in flop_size_cache:
                size = detect_flop_bet_size(client, profile, flop)
                flop_size_cache[flop] = size
                print(f"  detected flop bet size for {flop}: {size}")
            size_code = flop_size_cache.get(flop)
            if not size_code:
                print(f"[{i+1}/{len(TURN_SPOTS)}] SKIP {spot['id']} (size det failed)")
                continue

            flop_actions = f"X-{size_code}-C"
            raw_path = raw_dir / f"{spot['id']}.json"
            if raw_path.exists():
                data = json.load(open(raw_path))
                print(f"[{i+1}/{len(TURN_SPOTS)}] CACHED {spot['id']}")
            else:
                p = {
                    "gametype": profile["gametype"], "depth": profile["depth"],
                    "stacks": profile["stacks"],
                    "preflop_actions": profile["pf"],
                    "flop_actions": flop_actions,
                    "turn_actions": "", "river_actions": "",
                    "board": board,
                }
                status, data = call_api(client, p)
                if status != 200 or not data:
                    print(f"[{i+1}/{len(TURN_SPOTS)}] FAIL {spot['id']} status={status}")
                    continue
                with open(raw_path, "w") as f:
                    json.dump(data, f)
                print(f"[{i+1}/{len(TURN_SPOTS)}] OK   {spot['id']} ({flop_actions})")
                time.sleep(0.3)

            agg = compute_hand_agg(data)
            agg.update({
                "spot_id": spot["id"], "flop": flop, "turn": turn,
                "board": board, "label": spot["label"],
                "flop_actions": flop_actions, "profile": profile_name,
            })
            results.append(agg)

    with open(out_file, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"\nWrote {out_file} ({len(results)} records)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--collect", action="store_true")
    ap.add_argument("--profile", choices=list(PROFILES.keys()), default="mtt25_btn")
    args = ap.parse_args()
    if args.collect:
        collect(args.profile)
    else:
        ap.print_help()
