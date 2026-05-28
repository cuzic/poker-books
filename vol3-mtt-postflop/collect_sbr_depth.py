#!/usr/bin/env python3
"""
collect_sbr_depth.py — SBR depth 別 CBet RAS 収集スクリプト

【目的】
  SBR15/20/25/40 の各スタック深さで BTN-BB / SB-BB / LIMP の
  フロップ CBet RAS (Range Aggression Score) を収集し、SBR別比較表を出力する。

【使い方】
  TOKEN=xxx GWCLIENTID=xxx uv run collect_sbr_depth.py --collect SRP40
  TOKEN=xxx GWCLIENTID=xxx uv run collect_sbr_depth.py --collect-all
  TOKEN=xxx GWCLIENTID=xxx uv run collect_sbr_depth.py --probe-sbr15
  uv run collect_sbr_depth.py --analyze

【出力】
  findings/sbr_depth_{SCENARIO}.jsonl
  各レコード: {"board_id":"K72_rain","board":"Ks7d2c","scenario":"SRP40",
               "label":"BTN-BB SBR40","cross":{...},"draw_agg":{...},
               "hand_agg":{...},"n_combos":612}
"""

import os, sys, json, time, argparse, requests
from pathlib import Path
from collections import defaultdict
from typing import Any

TOKEN          = os.environ.get("TOKEN", "")
GWCLIENTID     = os.environ.get("GWCLIENTID", "")
GOOGLE_ANAL_ID = os.environ.get("GOOGLE_ANAL_ID", "")
GT             = "MTTGeneral"
BASE_URL       = "https://api.gtowizard.com/v4/solutions/spot-solution/"
FINDINGS_DIR   = Path(__file__).parent / "findings"

# ─── CORE_BOARDS ────────────────────────────────────────────
CORE_BOARDS = [
    {"id": "K98_rain", "board": "Kd9s8c"},
    {"id": "K98_fd",   "board": "Kd9c8d"},
    {"id": "T98_rain", "board": "Th9s8d"},
    {"id": "T98_fd",   "board": "Td9s8d"},
    {"id": "K72_rain", "board": "Ks7d2c"},
    {"id": "K72_fd",   "board": "Kd7c2d"},
    {"id": "Q83_rain", "board": "Qh8d3s"},
    {"id": "Q83_fd",   "board": "Qd8c3d"},
    {"id": "J73_rain", "board": "Jh7d3s"},
    {"id": "J73_fd",   "board": "Jd7c3d"},
    {"id": "A94_rain", "board": "Ah9d4s"},
    {"id": "A94_fd",   "board": "Ad9c4d"},
    {"id": "765_rain", "board": "7h6d5s"},
    {"id": "765_fd",   "board": "7d6c5d"},
    {"id": "KJT_rain", "board": "KhJdTs"},
    {"id": "KJT_fd",   "board": "KdJcTd"},
    {"id": "J75_rain", "board": "Jd7s5c"},
    {"id": "AA7_rain", "board": "AhAd7c"},
    {"id": "77x_rain", "board": "7h7d2s"},
]

# ─── シナリオ定義 ────────────────────────────────────────────
# SBR15 の preflop_actions は --probe-sbr15 で発見する（コメントで暫定値）
SCENARIOS: dict[str, dict[str, Any]] = {
    "SRP40":     {"depth": 40.125, "pf": "F-F-F-F-F-R2.5-F-C",  "label": "BTN-BB SBR40"},
    "SRP40_SB":  {"depth": 40.125, "pf": "F-F-F-F-F-F-R3.5-C",  "label": "SB-BB  SBR40"},
    "LIMP40_SB": {"depth": 40.125, "pf": "F-F-F-F-F-F-C-X",     "label": "LIMP   SBR40"},
    "SRP15":     {"depth": 15.125, "pf": "F-F-F-F-F-R2-F-C",    "label": "BTN-BB SBR15"},  # probe needed
    "SRP15_SB":  {"depth": 15.125, "pf": "F-F-F-F-F-F-R3-C",    "label": "SB-BB  SBR15"},  # probe needed
    "LIMP15_SB": {"depth": 15.125, "pf": "F-F-F-F-F-F-C-X",     "label": "LIMP   SBR15"},  # probe needed
}

# ─── API ────────────────────────────────────────────────────

def make_headers() -> dict[str, str]:
    h: dict[str, str] = {
        "accept":             "application/json, text/plain, */*",
        "accept-language":    "ja,en;q=0.9",
        "authorization":      f"Bearer {TOKEN}",
        "cache-control":      "no-cache",
        "origin":             "https://app.gtowizard.com",
        "pragma":             "no-cache",
        "referer":            "https://app.gtowizard.com/",
        "sec-ch-ua":          '"Chromium";v="148", "Microsoft Edge";v="148", "Not/A)Brand";v="99"',
        "sec-ch-ua-mobile":   "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest":     "empty",
        "sec-fetch-mode":     "cors",
        "sec-fetch-site":     "same-site",
        "user-agent":         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    if GWCLIENTID:
        h["gwclientid"] = GWCLIENTID
    if GOOGLE_ANAL_ID:
        h["google-anal-id"] = GOOGLE_ANAL_ID
    return h


def call_api(board: str, depth: float = 25.125,
             pf: str = "F-F-F-F-F-R2.1-F-C", stacks: str = "",
             flop_actions: str = "X", turn_actions: str = "",
             river_actions: str = "") -> dict[str, Any] | None:
    params: dict[str, Any] = {
        "gametype": GT, "depth": str(depth), "stacks": stacks,
        "preflop_actions": pf, "flop_actions": flop_actions,
        "turn_actions": turn_actions, "river_actions": river_actions,
        "board": board,
    }
    for attempt in range(4):
        try:
            r = requests.get(BASE_URL, params=params, headers=make_headers(), timeout=30)
        except Exception as e:
            print(f"    接続エラー: {e}")
            time.sleep(5)
            continue
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 10))
            print(f"    429 rate limit, {wait}s 待機...")
            time.sleep(wait)
            continue
        if r.status_code == 204:
            print(f"    204 No Content (このシナリオはデータなし)")
            return None
        if r.status_code == 401:
            print(f"    401 Unauthorized: トークン期限切れ")
            sys.exit(1)
        print(f"    HTTP {r.status_code}: {r.text[:200]}")
        if attempt < 3:
            time.sleep(3)
    return None


def compute_cross(data: dict) -> dict[str, Any]:
    """API レスポンスから (hand × draw) bet% クロス集計を計算する。"""
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

    bet_codes  = [c for c in strategies if c != "X"]
    cross: dict[tuple, list] = defaultdict(list)
    draw_agg: dict[str, dict] = defaultdict(lambda: {"total": 0.0, "bet": 0.0})
    hand_agg: dict[str, dict] = defaultdict(lambda: {"total": 0.0, "bet": 0.0})
    n_in_range = 0

    for i in range(min(1326, len(dcr), len(hcr))):
        total = sum(s[i] for s in strategies.values() if i < len(s))
        if total < 0.001:
            continue
        n_in_range += 1
        bet_f  = sum(strategies[c][i] for c in bet_codes if i < len(strategies[c]))
        d_name = draw_map.get(dcr[i], f"unk_{dcr[i]}")
        h_name = hand_map.get(hcr[i], f"unk_{hcr[i]}")

        cross[(h_name, d_name)].append(bet_f)
        draw_agg[d_name]["total"] += 1
        draw_agg[d_name]["bet"]   += bet_f
        hand_agg[h_name]["total"] += 1
        hand_agg[h_name]["bet"]   += bet_f

    return {
        "cross":    {f"{h}|{d}": {"vals": v, "n": len(v),
                                   "avg": sum(v)/len(v)*100 if v else 0}
                     for (h, d), v in cross.items()},
        "draw_agg": {k: {"total": v["total"],
                         "bet_pct": v["bet"]/v["total"]*100 if v["total"] > 0 else 0}
                     for k, v in draw_agg.items()},
        "hand_agg": {k: {"total": v["total"],
                         "bet_pct": v["bet"]/v["total"]*100 if v["total"] > 0 else 0}
                     for k, v in hand_agg.items()},
        "n_combos": n_in_range,
    }


# ─── ユーティリティ ──────────────────────────────────────────

def load_existing(outf: Path) -> set[str]:
    existing: set[str] = set()
    if outf.exists():
        for line in outf.read_text().splitlines():
            if line.strip():
                try:
                    rec = json.loads(line)
                    existing.add(rec.get("board_id", ""))
                except json.JSONDecodeError:
                    pass
    return existing


def compute_ras(crs: dict) -> float:
    """no_draw bet_pct をRASとして返す。"""
    nd = crs["draw_agg"].get("no_draw", {})
    return nd.get("bet_pct", 0.0)


# ─── 収集 ────────────────────────────────────────────────────

def collect_scenario(scenario_key: str, force: bool = False) -> None:
    if scenario_key not in SCENARIOS:
        print(f"Unknown scenario: {scenario_key}")
        return
    cfg = SCENARIOS[scenario_key]
    outf = FINDINGS_DIR / f"sbr_depth_{scenario_key}.jsonl"
    FINDINGS_DIR.mkdir(exist_ok=True)

    existing = load_existing(outf) if not force else set()
    if force and outf.exists():
        bak = outf.with_suffix(".jsonl.bak")
        outf.rename(bak)
        print(f"  --force: バックアップ → {bak}")

    label = cfg["label"]
    print(f"\n=== COLLECT: {label} ({scenario_key}) ===")
    print(f"  対象: {len(CORE_BOARDS)}ボード（既存スキップ: {len(existing)}）\n")

    with outf.open("a") as fout:
        for bcfg in CORE_BOARDS:
            bid = bcfg["id"]
            if bid in existing:
                print(f"  ⏭  {bid:15s} スキップ（既存）")
                continue

            board = bcfg["board"]
            print(f"  ⬇  {bid:15s} {board}")
            data = call_api(board, depth=cfg["depth"], pf=cfg["pf"])
            if data is None or "action_solutions" not in data:
                print(f"    ❌ スキップ")
                time.sleep(1)
                continue

            crs = compute_cross(data)
            ras = compute_ras(crs)
            print(f"    RAS={ras:.1f}%  combos={crs['n_combos']}")

            rec = {
                "board_id":  bid,
                "board":     board,
                "scenario":  scenario_key,
                "label":     label,
                "cross":     crs["cross"],
                "draw_agg":  crs["draw_agg"],
                "hand_agg":  crs["hand_agg"],
                "n_combos":  crs["n_combos"],
            }
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()
            time.sleep(1.5)

    print(f"\n  完了: {scenario_key}")


def collect_all(force: bool = False) -> None:
    for key in SCENARIOS:
        collect_scenario(key, force=force)


# ─── SBR15 probe ────────────────────────────────────────────

def probe_sbr15() -> None:
    """SBR15 の有効な preflop open サイズを探索する。"""
    print("\n=== probe-sbr15: SBR15 有効サイズ探索 ===\n")
    test_board = "Ks7d2c"
    open_sizes = ["R1.8", "R2.0", "R2.1", "R2.5", "R3.0"]

    # BTN-BB パターン
    print("  [BTN-BB @ SBR15]")
    for sz in open_sizes:
        pf = f"F-F-F-F-F-{sz}-F-C"
        r = requests.get(BASE_URL, params={
            "gametype": GT, "depth": "15.125", "stacks": "",
            "preflop_actions": pf, "flop_actions": "X",
            "turn_actions": "", "river_actions": "", "board": test_board,
        }, headers=make_headers(), timeout=30)
        mark = "✅" if r.status_code == 200 else f"❌({r.status_code})"
        print(f"    {mark} size={sz}  pf={pf}")
        time.sleep(0.5)

    print()

    # SB-BB パターン
    print("  [SB-BB @ SBR15]")
    for sz in open_sizes:
        pf = f"F-F-F-F-F-F-{sz}-C"
        r = requests.get(BASE_URL, params={
            "gametype": GT, "depth": "15.125", "stacks": "",
            "preflop_actions": pf, "flop_actions": "X",
            "turn_actions": "", "river_actions": "", "board": test_board,
        }, headers=make_headers(), timeout=30)
        mark = "✅" if r.status_code == 200 else f"❌({r.status_code})"
        print(f"    {mark} size={sz}  pf={pf}")
        time.sleep(0.5)


# ─── 分析 ────────────────────────────────────────────────────

def analyze() -> None:
    """SBR別 RAS 比較表を出力する。"""
    # データ読み込み
    all_data: dict[str, dict[str, float]] = {}  # scenario → board_id → RAS
    for key in SCENARIOS:
        outf = FINDINGS_DIR / f"sbr_depth_{key}.jsonl"
        if not outf.exists():
            continue
        board_ras: dict[str, float] = {}
        for line in outf.read_text().splitlines():
            if line.strip():
                try:
                    rec = json.loads(line)
                    nd = rec.get("draw_agg", {}).get("no_draw", {})
                    ras = nd.get("bet_pct", 0.0) if nd else 0.0
                    board_ras[rec["board_id"]] = ras
                except (json.JSONDecodeError, KeyError):
                    pass
        all_data[key] = board_ras

    print("\n=== SBR別 RAS 比較 ===")
    print()

    # 参照用 SBR20/25 は draw_study のデータを使う
    ds_data: dict[str, dict[str, float]] = {}
    for ds_key in ["SRP20", "SRP25", "SRP20_SB", "SRP25_SB", "LIMP20_SB", "LIMP25_SB"]:
        for prefix in ["draw_study", "board_ras"]:
            f = FINDINGS_DIR / f"{prefix}_{ds_key}.jsonl"
            if f.exists():
                brd: dict[str, float] = {}
                for line in f.read_text().splitlines():
                    if line.strip():
                        try:
                            rec = json.loads(line)
                            nd = rec.get("draw_agg", {}).get("no_draw", {})
                            ras = nd.get("bet_pct", 0.0) if nd else 0.0
                            brd[rec.get("board_id", "")] = ras
                        except Exception:
                            pass
                ds_data[ds_key] = brd
                break

    # ボードごとに集計して平均を計算
    def avg_ras(data: dict[str, float]) -> str:
        if not data:
            return "  —  "
        vals = list(data.values())
        return f"{sum(vals)/len(vals):5.1f}%"

    print(f"  {'ポジション':<10} {'SBR15':>8} {'SBR20':>8} {'SBR25':>8} {'SBR40':>8}")
    print(f"  {'-'*10} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")

    pos_map = [
        ("BTN-BB",  "SRP15",     "SRP20",    "SRP25",    "SRP40"),
        ("SB-BB",   "SRP15_SB",  "SRP20_SB", "SRP25_SB", "SRP40_SB"),
        ("LIMP",    "LIMP15_SB", "LIMP20_SB","LIMP25_SB","LIMP40_SB"),
    ]
    for pos, k15, k20, k25, k40 in pos_map:
        r15 = avg_ras(all_data.get(k15, {}))
        r20 = avg_ras(ds_data.get(k20, {}) or all_data.get(k20, {}))
        r25 = avg_ras(ds_data.get(k25, {}) or all_data.get(k25, {}))
        r40 = avg_ras(all_data.get(k40, {}))
        print(f"  {pos:<10} {r15:>8} {r20:>8} {r25:>8} {r40:>8}")

    print()

    # ボード別詳細
    print("  [ボード別 RAS 詳細 (SBR15 vs SBR40)]")
    print(f"  {'board_id':<15} {'SBR15':>8} {'SBR40':>8}")
    print(f"  {'-'*15} {'-'*8} {'-'*8}")
    all_ids = set()
    for d in all_data.values():
        all_ids.update(d.keys())
    for bid in sorted(all_ids):
        r15 = f"{all_data.get('SRP15',{}).get(bid,0):.1f}%" if bid in all_data.get("SRP15",{}) else "  —  "
        r40 = f"{all_data.get('SRP40',{}).get(bid,0):.1f}%" if bid in all_data.get("SRP40",{}) else "  —  "
        print(f"  {bid:<15} {r15:>8} {r40:>8}")


# ─── メイン ─────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description="SBR depth 別 CBet RAS 収集スクリプト"
    )
    ap.add_argument("--collect", metavar="SCENARIO",
                    choices=list(SCENARIOS.keys()),
                    help="指定シナリオを収集 (例: SRP40, SRP15_SB)")
    ap.add_argument("--collect-all", action="store_true",
                    help="全シナリオを収集")
    ap.add_argument("--analyze",   action="store_true",
                    help="収集済みデータを分析して SBR比較表を出力")
    ap.add_argument("--probe-sbr15", action="store_true",
                    dest="probe_sbr15",
                    help="SBR15 の有効な preflop サイズを探索")
    ap.add_argument("--force", action="store_true",
                    help="既存データを無視して再収集")
    args = ap.parse_args()

    if args.probe_sbr15:
        probe_sbr15()
    elif args.collect:
        collect_scenario(args.collect, force=args.force)
    elif args.collect_all:
        collect_all(force=args.force)
    elif args.analyze:
        analyze()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
