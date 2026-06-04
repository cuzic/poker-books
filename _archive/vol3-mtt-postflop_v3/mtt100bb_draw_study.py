#!/usr/bin/env python3
"""
mtt100bb_draw_study.py — MTT6mSimple @ 100bb の hand_agg 収集

cash6m_draw_study.py を MTT6mSimple/100bb 用に派生。
UCBS-v2 の mtt_100bb context 追加用データを作成。

使い方:
  python3 mtt100bb_draw_study.py --collect [--limit N] [--force]
"""
import os, sys, json, time, argparse, base64
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

# Depth プロファイル (各プロファイルが gametype を持つ)
DEPTH_PROFILES: dict[str, dict[str, Any]] = {
    "100bb": {
        "gametype": "MTT6mSimple",
        "depth": 100.125,
        "stacks": "100.125-100.125-100.125-100.125-100.125-100.125",
        "out_file": "draw_study_MTT100BB.jsonl",
        "raw_dir": "mtt100bb_raw",
        "scenarios": {
            "UTG_BB": {"pf": "R2.1-F-F-F-F-C",   "label": "UTG-BB SRP 100bb"},
            "HJ_BB":  {"pf": "F-R2.1-F-F-F-C",   "label": "HJ-BB  SRP 100bb"},
            "CO_BB":  {"pf": "F-F-R2.2-F-F-C",   "label": "CO-BB  SRP 100bb"},
            "BTN_BB": {"pf": "F-F-F-R2.5-F-C",   "label": "BTN-BB SRP 100bb"},
            "SB_BB":  {"pf": "F-F-F-F-R3.5-C",   "label": "SB-BB  SRP 100bb"},
        },
    },
    "50bb": {
        "gametype": "MTT6mSimple",
        "depth": 50.125,
        "stacks": "50.125-50.125-50.125-50.125-50.125-50.125",
        "out_file": "draw_study_MTT50BB.jsonl",
        "raw_dir": "mtt50bb_raw",
        "scenarios": {
            "UTG_BB": {"pf": "R2.2-F-F-F-F-C",   "label": "UTG-BB SRP 50bb"},
            "HJ_BB":  {"pf": "F-R2.2-F-F-F-C",   "label": "HJ-BB  SRP 50bb"},
            "CO_BB":  {"pf": "F-F-R2.3-F-F-C",   "label": "CO-BB  SRP 50bb"},
            "BTN_BB": {"pf": "F-F-F-R2.5-F-C",   "label": "BTN-BB SRP 50bb"},
            "SB_BB":  {"pf": "F-F-F-F-R3-C",     "label": "SB-BB  SRP 50bb"},
        },
    },
    "cash200bb": {
        "gametype": "Cash6mGeneral_6mNL25R25",
        "depth": 200,
        "stacks": "",   # ※ subscription 範囲外で 403、保留
        "out_file": "draw_study_CASH200BB.jsonl",
        "raw_dir": "cash200bb_raw",
        "scenarios": {
            "UTG_BB": {"pf": "R2.5-F-F-F-F-C",   "label": "UTG-BB SRP 200bb cash"},
            "HJ_BB":  {"pf": "F-R2.5-F-F-F-C",   "label": "HJ-BB  SRP 200bb cash"},
            "CO_BB":  {"pf": "F-F-R2.5-F-F-C",   "label": "CO-BB  SRP 200bb cash"},
            "BTN_BB": {"pf": "F-F-F-R2.5-F-C",   "label": "BTN-BB SRP 200bb cash"},
            "SB_BB":  {"pf": "F-F-F-F-R3.5-C",   "label": "SB-BB  SRP 200bb cash"},
        },
    },
    "cash50bb": {
        "gametype": "Cash6mGeneral_6mNL25R25",
        "depth": 50,
        "stacks": "",   # ※ subscription denied
        "out_file": "draw_study_CASH50BB.jsonl",
        "raw_dir": "cash50bb_raw",
        "scenarios": {
            "UTG_BB": {"pf": "R2.5-F-F-F-F-C",   "label": "UTG-BB SRP 50bb cash"},
            "HJ_BB":  {"pf": "F-R2.5-F-F-F-C",   "label": "HJ-BB  SRP 50bb cash"},
            "CO_BB":  {"pf": "F-F-R2.5-F-F-C",   "label": "CO-BB  SRP 50bb cash"},
            "BTN_BB": {"pf": "F-F-F-R2.5-F-C",   "label": "BTN-BB SRP 50bb cash"},
            "SB_BB":  {"pf": "F-F-F-F-R3.5-C",   "label": "SB-BB  SRP 50bb cash"},
        },
    },
    "200bb": {
        "gametype": "MTT6mSimple",
        "depth": 200.125,
        "stacks": "200.125-200.125-200.125-200.125-200.125-200.125",
        "out_file": "draw_study_MTT200BB.jsonl",
        "raw_dir": "mtt200bb_raw",
        "scenarios": {
            "UTG_BB": {"pf": "R2.5-F-F-F-F-C",   "label": "UTG-BB SRP 200bb"},
            "HJ_BB":  {"pf": "F-R2.5-F-F-F-C",   "label": "HJ-BB  SRP 200bb"},
            "CO_BB":  {"pf": "F-F-R2.5-F-F-C",   "label": "CO-BB  SRP 200bb"},
            "BTN_BB": {"pf": "F-F-F-R2.5-F-C",   "label": "BTN-BB SRP 200bb"},
            "SB_BB":  {"pf": "F-F-F-F-R3.5-C",   "label": "SB-BB  SRP 200bb"},
        },
    },
    # ─── 3-bet pots: BTN cold-call vs BB 3bet → BTN IP cbet ───────────
    # SPR は depth に依存: 25bb ~2.7, 50bb ~5.5, 100bb ~11
    "3bp25": {
        "gametype": "MTT6mSimple",
        "depth": 25.125,
        "stacks": "25.125-25.125-25.125-25.125-25.125-25.125",
        "out_file": "draw_study_3BP25.jsonl",
        "raw_dir": "3bp25_raw",
        "scenarios": {
            "BTN_BB": {"pf": "F-F-F-R2.5-F-R6.5-C", "label": "3BP25 BTN-BB"},
        },
    },
    "3bp50": {
        "gametype": "MTT6mSimple",
        "depth": 50.125,
        "stacks": "50.125-50.125-50.125-50.125-50.125-50.125",
        "out_file": "draw_study_3BP50.jsonl",
        "raw_dir": "3bp50_raw",
        "scenarios": {
            "BTN_BB": {"pf": "F-F-F-R2.5-F-R8-C", "label": "3BP50 BTN-BB"},
        },
    },
    "3bp100": {
        "gametype": "MTT6mSimple",
        "depth": 100.125,
        "stacks": "100.125-100.125-100.125-100.125-100.125-100.125",
        "out_file": "draw_study_3BP100.jsonl",
        "raw_dir": "3bp100_raw",
        "scenarios": {
            "BTN_BB": {"pf": "F-F-F-R2.5-F-R10-C", "label": "3BP100 BTN-BB"},
        },
    },
}

# ── 調査ボード(24枚、cash6m_draw_study.py と同じセット)─────────────────
STUDY_BOARDS: list[dict[str, str]] = [
    {"board_id": "K98_rain", "board": "Kd9s8c"},
    {"board_id": "K98_fd",   "board": "Kd9c8d"},
    {"board_id": "T98_rain", "board": "Th9s8d"},
    {"board_id": "T98_fd",   "board": "Td9s8d"},
    {"board_id": "K72_rain", "board": "Ks7d2c"},
    {"board_id": "K72_fd",   "board": "Kd7c2d"},
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


# ── トークン管理 ─────────────────────────────────────
def get_token() -> str:
    return TOKEN_FILE.read_text().strip()


def get_google_anal_id() -> str:
    return GOOGLE_ANAL_ID_FILE.read_text().strip()


def refresh_access_token() -> str | None:
    if not REFRESH_TOKEN_FILE.exists():
        return None
    refresh = REFRESH_TOKEN_FILE.read_text().strip()
    google_anal = get_google_anal_id()
    try:
        r = httpx.post(
            "https://api.gtowizard.com/v1/token/refresh/",
            json={"refresh": refresh},
            headers={
                "accept": "application/json, text/plain, */*",
                "content-type": "application/json",
                "gwclientid": "930036c8-831c-4fca-8453-b0a298853e86",
                "google-anal-id": google_anal,
                "origin": "https://app.gtowizard.com",
                "referer": "https://app.gtowizard.com/",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
            },
            timeout=15.0,
        )
        if r.status_code == 200:
            access = r.json().get("access")
            if access:
                TOKEN_FILE.write_text(access)
                return access
    except Exception:
        pass
    return None


def make_headers(token: str) -> dict[str, str]:
    return {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token}",
        "google-anal-id": get_google_anal_id(),
        "gwclientid": "930036c8-831c-4fca-8453-b0a298853e86",
        "origin": "https://app.gtowizard.com",
        "referer": "https://app.gtowizard.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
    }


def call_api(client: httpx.Client, params: dict, max_retries: int = 5) -> tuple[int, dict | None]:
    backoff = 2.0
    for _ in range(max_retries):
        try:
            r = client.get(BASE_URL, params=params, timeout=30.0)
            if r.status_code == 200:
                return 200, r.json()
            if r.status_code == 401:
                new = refresh_access_token()
                if new:
                    client.headers["authorization"] = f"Bearer {new}"
                    continue
                return 401, None
            if r.status_code == 429:
                time.sleep(backoff)
                backoff *= 2
                continue
            return r.status_code, None
        except Exception as e:
            print(f"  exception: {e}")
            time.sleep(backoff)
            backoff *= 2
    return 0, None


# ── per-hand 集計ロジック (cash6m_draw_study.py より) ─────────────
def compute_hand_agg(data: dict) -> dict:
    """1326 combos の strategy 配列を hand_categories で集計。"""
    dcr = data.get("draw_categories_range", [])
    hcr = data.get("hand_categories_range", [])
    as_ = data.get("action_solutions", [])

    draw_map: dict[int, str] = {}
    hand_map: dict[int, str] = {}
    strategies: dict[str, list[float]] = {}

    for item in as_:
        code = item["action"]["code"]
        strategies[code] = item.get("strategy", [])
        if not draw_map:
            for d in (item.get("draw_categories") or []):
                draw_map[d["index"]] = d["name"]
        if not hand_map:
            for h in (item.get("hand_categories") or []):
                hand_map[h["index"]] = h["name"]

    bet_codes = [c for c in strategies if c != "X"]
    hand_agg: dict[str, dict] = defaultdict(lambda: {"total": 0.0, "bet": 0.0})
    n_in_range = 0

    for i in range(min(1326, len(dcr), len(hcr))):
        total = sum(s[i] for s in strategies.values() if i < len(s))
        if total < 0.001:
            continue
        n_in_range += 1
        bet_f = sum(strategies[c][i] for c in bet_codes if i < len(strategies[c]))
        h_name = hand_map.get(hcr[i], f"unk_{hcr[i]}")
        hand_agg[h_name]["total"] += 1
        hand_agg[h_name]["bet"]   += bet_f

    return {
        "hand_agg": {k: {"total": v["total"],
                         "bet_pct": v["bet"]/v["total"]*100 if v["total"] > 0 else 0}
                     for k, v in hand_agg.items()},
        "n_combos": n_in_range,
    }


# ── flop_actions の決定 (IP/OOP に応じて) ──────────
# - IP cbet (UTG/HJ/CO/BTN vs BB): flop="X" (BB がまず check)
# - OOP cbet (SB vs BB): flop="" (SB が先手、最初の action)
def flop_actions_for(scenario: str) -> str:
    if scenario == "SB_BB":
        return ""  # SB が OOP、最初の action
    return "X"  # BB が OOP で check、IP の選択を測定


# ── メイン収集 ───────────────────────────────────
def collect(depth_profile: str = "100bb", limit: int | None = None, force: bool = False):
    profile = DEPTH_PROFILES[depth_profile]
    raw_dir = FINDINGS / profile["raw_dir"]
    out_file = FINDINGS / profile["out_file"]
    raw_dir.mkdir(parents=True, exist_ok=True)
    FINDINGS.mkdir(parents=True, exist_ok=True)

    tasks = []
    for scen, cfg in profile["scenarios"].items():
        for board in STUDY_BOARDS:
            tasks.append({
                "scenario": scen, "pf": cfg["pf"], "label": cfg["label"],
                "board_id": board["board_id"], "board": board["board"],
            })

    if limit:
        tasks = tasks[:limit]

    print(f"# Profile: {depth_profile}, Total tasks: {len(tasks)}")

    token = get_token()
    headers = make_headers(token)
    results = []

    with httpx.Client(headers=headers) as client:
        for i, t in enumerate(tasks):
            raw_path = raw_dir / f"{t['scenario']}_{t['board_id']}.json"
            if raw_path.exists() and not force:
                with open(raw_path) as f:
                    data = json.load(f)
                print(f"[{i+1}/{len(tasks)}] CACHED {t['scenario']}/{t['board_id']}")
            else:
                params = {
                    "gametype": profile["gametype"],
                    "depth": str(profile["depth"]),
                    "stacks": profile["stacks"],
                    "preflop_actions": t["pf"],
                    "flop_actions": flop_actions_for(t["scenario"]),
                    "turn_actions": "", "river_actions": "",
                    "board": t["board"],
                }
                status, data = call_api(client, params)
                if status != 200 or not data:
                    print(f"[{i+1}/{len(tasks)}] FAIL {t['scenario']}/{t['board_id']} status={status}")
                    continue
                with open(raw_path, "w") as f:
                    json.dump(data, f)
                print(f"[{i+1}/{len(tasks)}] OK   {t['scenario']}/{t['board_id']}")
                time.sleep(0.3)

            agg = compute_hand_agg(data)
            agg.update({
                "scenario": t["scenario"], "board": t["board"],
                "board_id": t["board_id"], "label": t["label"],
            })
            results.append(agg)

    with open(out_file, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"\nWrote {out_file} ({len(results)} records)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--collect", action="store_true")
    ap.add_argument("--depth",
                    choices=["100bb", "50bb", "200bb", "cash200bb", "cash50bb",
                             "3bp25", "3bp50", "3bp100"],
                    default="100bb")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if args.collect:
        collect(args.depth, args.limit, args.force)
    else:
        ap.print_help()
