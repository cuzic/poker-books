#!/usr/bin/env python3
"""
BB defense vs flop cbet データ収集

シナリオ: BTN open R2.x, BB call → flop X (BB), R{size} (BTN cbet)
          → BB's defense decision: F (fold) / C (call) / R (raise)

UCBS-v2 と同じ構造で **continue freq (= 1 - fold freq)** を予測。
プロファイル: mtt_25bb_btn_vs_bb, cash_100bb, mtt_50bb, mtt_100bb
"""
import json, time, argparse, sys
from pathlib import Path
from collections import defaultdict
import httpx

SCRIPT_DIR = Path(__file__).parent
TOKEN_FILE = Path("/home/cuzic/poker-books/scripts/gto_wizard_study/.token")
REFRESH_TOKEN_FILE = Path("/home/cuzic/poker-books/scripts/gto_wizard_study/.refresh_token")
GOOGLE_ANAL_ID_FILE = Path("/home/cuzic/poker-books/scripts/gto_wizard_study/.google_anal_id")

FINDINGS = SCRIPT_DIR / "findings"
BASE_URL = "https://api.gtowizard.com/v4/solutions/spot-solution/"

PROFILES = {
    "mtt25_btn": {
        "gametype": "MTT6mSimple", "depth": "25.125",
        "stacks": "25.125-25.125-25.125-25.125-25.125-25.125",
        "pf": "F-F-F-R2.1-F-C",
        "out_file": "draw_study_DEF_MTT25_BB.jsonl",
        "raw_dir": "def_mtt25_bb_raw",
    },
    "mtt50_btn": {
        "gametype": "MTT6mSimple", "depth": "50.125",
        "stacks": "50.125-50.125-50.125-50.125-50.125-50.125",
        "pf": "F-F-F-R2.5-F-C",
        "out_file": "draw_study_DEF_MTT50_BB.jsonl",
        "raw_dir": "def_mtt50_bb_raw",
    },
    "mtt100_btn": {
        "gametype": "MTT6mSimple", "depth": "100.125",
        "stacks": "100.125-100.125-100.125-100.125-100.125-100.125",
        "pf": "F-F-F-R2.5-F-C",
        "out_file": "draw_study_DEF_MTT100_BB.jsonl",
        "raw_dir": "def_mtt100_bb_raw",
    },
    "cash100_btn": {
        "gametype": "Cash6mGeneral_6mNL25R25", "depth": "100",
        "stacks": "",
        "pf": "F-F-F-R2.5-F-C",
        "out_file": "draw_study_DEF_CASH100_BB.jsonl",
        "raw_dir": "def_cash100_bb_raw",
    },
}

STUDY_BOARDS = [
    {"board_id": "K72_rain", "board": "Ks7d2c"},
    {"board_id": "K72_fd",   "board": "Kd7c2d"},
    {"board_id": "K98_rain", "board": "Kd9s8c"},
    {"board_id": "K98_fd",   "board": "Kd9c8d"},
    {"board_id": "T98_rain", "board": "Th9s8d"},
    {"board_id": "T98_fd",   "board": "Td9s8d"},
    {"board_id": "Q83_rain", "board": "Qh8d3s"},
    {"board_id": "Q83_fd",   "board": "Qd8c3d"},
    {"board_id": "J73_rain", "board": "Jh7d3s"},
    {"board_id": "J73_fd",   "board": "Jd7c3d"},
    {"board_id": "A94_rain", "board": "Ah9d4s"},
    {"board_id": "A94_fd",   "board": "Ad9c4d"},
    {"board_id": "765_rain", "board": "7h6d5s"},
    {"board_id": "765_fd",   "board": "7d6c5d"},
    {"board_id": "KJT_rain", "board": "KhJdTs"},
    {"board_id": "KJT_fd",   "board": "KdJcTd"},
    {"board_id": "T74_rain", "board": "Th7d4s"},
    {"board_id": "T74_fd",   "board": "Td7c4d"},
    {"board_id": "A72_rain", "board": "Ah7d2s"},
    {"board_id": "A72_fd",   "board": "Ad7c2d"},
    {"board_id": "742_rain", "board": "7h4d2s"},
    {"board_id": "742_fd",   "board": "7d4c2d"},
    {"board_id": "KK8_rain", "board": "KhKd8c"},
    {"board_id": "AA7_rain", "board": "AhAd7c"},
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


def compute_continue_agg(data):
    """BB の continue freq (= 1 - fold freq) を hand 別に集計"""
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
    # F (fold) と それ以外を分ける
    fold_code = "F"
    cont_codes = [c for c in strategies if c != fold_code]

    hand_agg = defaultdict(lambda: {"total": 0.0, "cont": 0.0, "fold": 0.0})
    n_in = 0
    for i in range(min(1326, len(dcr), len(hcr))):
        total = sum(s[i] for s in strategies.values() if i < len(s))
        if total < 0.001: continue
        n_in += 1
        cont_f = sum(strategies[c][i] for c in cont_codes if i < len(strategies[c]))
        fold_f = strategies[fold_code][i] if fold_code in strategies and i < len(strategies[fold_code]) else 0
        h_name = hand_map.get(hcr[i], f"unk_{hcr[i]}")
        hand_agg[h_name]["total"] += 1
        hand_agg[h_name]["cont"] += cont_f
        hand_agg[h_name]["fold"] += fold_f
    return {
        "hand_agg": {k: {"total": v["total"],
                         "cont_pct": v["cont"]/v["total"]*100 if v["total"] > 0 else 0,
                         "fold_pct": v["fold"]/v["total"]*100 if v["total"] > 0 else 0}
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


def collect(profile_name):
    profile = PROFILES[profile_name]
    raw_dir = FINDINGS / profile["raw_dir"]
    out_file = FINDINGS / profile["out_file"]
    raw_dir.mkdir(parents=True, exist_ok=True)
    FINDINGS.mkdir(parents=True, exist_ok=True)
    token = TOKEN_FILE.read_text().strip()

    flop_size_cache = {}
    results = []
    with httpx.Client(headers=headers(token)) as client:
        for i, board in enumerate(STUDY_BOARDS):
            flop = board["board"]
            if flop not in flop_size_cache:
                size = detect_flop_bet_size(client, profile, flop)
                flop_size_cache[flop] = size
                print(f"  detected size for {flop}: {size}")
            size_code = flop_size_cache.get(flop)
            if not size_code:
                print(f"[{i+1}/{len(STUDY_BOARDS)}] SKIP {board['board_id']} (no size)")
                continue

            # BB の defense 判断を取るには flop_actions に X-R{size} まで進める
            flop_actions = f"X-{size_code}"
            raw_path = raw_dir / f"{board['board_id']}.json"
            if raw_path.exists():
                data = json.load(open(raw_path))
                print(f"[{i+1}/{len(STUDY_BOARDS)}] CACHED {board['board_id']}")
            else:
                p = {
                    "gametype": profile["gametype"], "depth": profile["depth"],
                    "stacks": profile["stacks"],
                    "preflop_actions": profile["pf"],
                    "flop_actions": flop_actions,
                    "turn_actions": "", "river_actions": "",
                    "board": flop,
                }
                status, data = call_api(client, p)
                if status != 200 or not data:
                    print(f"[{i+1}/{len(STUDY_BOARDS)}] FAIL {board['board_id']} status={status}")
                    continue
                with open(raw_path, "w") as f:
                    json.dump(data, f)
                print(f"[{i+1}/{len(STUDY_BOARDS)}] OK   {board['board_id']} ({flop_actions})")
                time.sleep(0.3)

            agg = compute_continue_agg(data)
            agg.update({
                "board_id": board["board_id"], "board": flop,
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
