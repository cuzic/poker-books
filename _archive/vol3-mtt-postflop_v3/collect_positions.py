#!/usr/bin/env python3
"""
collect_positions.py — ポジション別 CBet RAS 収集スクリプト

【目的】
  BTN/SB/CO(SBR20) 以外のポジション（CO-BB SBR25, HJ-BB, UTG-BB）の
  フロップ CBet RAS を収集し、ポジション × SBR 比較表を出力する。

【重要】
  GTO Wizard MTTGeneral は BTN/SB/CO(SBR20のみ) に解が存在し、
  HJ/UTG は 204 No Content が多い。--probe-position で事前確認推奨。

【使い方】
  TOKEN=xxx GWCLIENTID=xxx uv run collect_positions.py --probe-position
  TOKEN=xxx GWCLIENTID=xxx uv run collect_positions.py --collect SRP25_CO
  TOKEN=xxx GWCLIENTID=xxx uv run collect_positions.py --collect-all
  uv run collect_positions.py --analyze

【出力】
  findings/positions_{SCENARIO}.jsonl
  各レコード: {"board_id":"K72_rain","board":"Ks7d2c","scenario":"SRP25_CO",
               "label":"CO-BB SBR25","cross":{...},"draw_agg":{...},
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
# 9-seat action order: UTG(1) UTG+1(2) UTG+2(3) HJ(4) CO(5) BTN(6) SB(7) BB(8)
# F は各席のフォールド、R はオープンレイズ、C はコール
SCENARIOS: dict[str, dict[str, Any]] = {
    # CO-BB (5番目がオープン、BTN/SB フォールド)
    "SRP25_CO": {"depth": 25.125, "pf": "F-F-F-F-R2.1-F-F-C", "label": "CO-BB  SBR25"},  # may 204
    "SRP40_CO": {"depth": 40.125, "pf": "F-F-F-F-R2.5-F-F-C", "label": "CO-BB  SBR40"},
    # HJ-BB (4番目がオープン、CO/BTN/SB フォールド)
    "SRP25_HJ": {"depth": 25.125, "pf": "F-F-F-R2.1-F-F-F-C", "label": "HJ-BB  SBR25"},  # likely 204
    "SRP20_HJ": {"depth": 20.125, "pf": "F-F-F-R2-F-F-F-C",   "label": "HJ-BB  SBR20"},  # likely 204
    # UTG-BB (2番目がオープン、残全フォールド)
    "SRP25_UTG":{"depth": 25.125, "pf": "F-F-R2.1-F-F-F-F-C", "label": "UTG-BB SBR25"},  # likely 204
    # 参照用 BTN (既知シナリオ)
    "SRP40_BTN":{"depth": 40.125, "pf": "F-F-F-F-F-R2.5-F-C", "label": "BTN-BB SBR40"},
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
    nd = crs["draw_agg"].get("no_draw", {})
    return nd.get("bet_pct", 0.0)


# ─── probe-position ─────────────────────────────────────────

def probe_position() -> None:
    """各ポジション × SBR × オープンサイズの有効な組み合わせを探索する。"""
    print("\n=== probe-position: ポジション別有効サイズ探索 ===\n")
    test_board = "Ks7d2c"

    # (position_label, depth, pf_template)
    # pf_template の {sz} を open size に置換
    candidates = [
        # CO-BB
        ("CO-BB SBR25", 25.125, "F-F-F-F-{sz}-F-F-C"),
        ("CO-BB SBR20", 20.125, "F-F-F-F-{sz}-F-F-C"),
        ("CO-BB SBR40", 40.125, "F-F-F-F-{sz}-F-F-C"),
        # HJ-BB
        ("HJ-BB SBR25", 25.125, "F-F-F-{sz}-F-F-F-C"),
        ("HJ-BB SBR20", 20.125, "F-F-F-{sz}-F-F-F-C"),
        ("HJ-BB SBR40", 40.125, "F-F-F-{sz}-F-F-F-C"),
        # UTG-BB (UTG+1 seat = position 2)
        ("UTG-BB SBR25",25.125, "F-F-{sz}-F-F-F-F-C"),
        ("UTG-BB SBR20",20.125, "F-F-{sz}-F-F-F-F-C"),
        ("UTG-BB SBR40",40.125, "F-F-{sz}-F-F-F-F-C"),
    ]
    open_sizes = ["R1.8", "R2.0", "R2.1", "R2.5"]

    found: list[str] = []
    for pos_label, depth, tmpl in candidates:
        print(f"  [{pos_label}]")
        for sz in open_sizes:
            pf = tmpl.format(sz=sz)
            try:
                r = requests.get(BASE_URL, params={
                    "gametype": GT, "depth": str(depth), "stacks": "",
                    "preflop_actions": pf, "flop_actions": "X",
                    "turn_actions": "", "river_actions": "", "board": test_board,
                }, headers=make_headers(), timeout=30)
            except Exception as e:
                print(f"    エラー: {e}")
                continue
            if r.status_code == 200:
                data = r.json()
                n_act = len(data.get("action_solutions", []))
                print(f"    ✅ size={sz}  pf={pf}  actions={n_act}")
                found.append(f"{pos_label} size={sz} pf={pf}")
            else:
                print(f"    ❌ size={sz}  HTTP {r.status_code}")
            time.sleep(0.5)
        print()

    print("=== 有効な組み合わせ一覧 ===")
    if found:
        for line in found:
            print(f"  ✅ {line}")
    else:
        print("  (有効なものなし — HJ/UTG は GTO Wizard の対象外の可能性あり)")


# ─── 収集 ────────────────────────────────────────────────────

def collect_scenario(scenario_key: str, force: bool = False) -> None:
    if scenario_key not in SCENARIOS:
        print(f"Unknown scenario: {scenario_key}")
        return
    cfg = SCENARIOS[scenario_key]
    outf = FINDINGS_DIR / f"positions_{scenario_key}.jsonl"
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
                print(f"    ❌ スキップ（204/エラー）")
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


# ─── 分析 ────────────────────────────────────────────────────

def analyze() -> None:
    """ポジション × SBR の RAS 比較表を出力する。"""
    # データ読み込み (本スクリプト収集分)
    all_data: dict[str, dict[str, float]] = {}
    for key in SCENARIOS:
        outf = FINDINGS_DIR / f"positions_{key}.jsonl"
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
                except Exception:
                    pass
        if board_ras:
            all_data[key] = board_ras

    # draw_study の既存データも参照
    ref_data: dict[str, dict[str, float]] = {}
    for ds_key in ["SRP20", "SRP25", "SRP20_CO"]:
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
                if brd:
                    ref_data[ds_key] = brd
                break

    def avg_ras(data: dict[str, float]) -> str:
        if not data:
            return "  —  "
        vals = list(data.values())
        return f"{sum(vals)/len(vals):5.1f}%"

    print("\n=== ポジション × SBR RAS 比較 ===")
    print()

    # ポジション別テーブル
    pos_rows = [
        ("BTN",   None,          "SRP25",       "SRP40_BTN"),
        ("CO",    "SRP20_CO(ref)","SRP25_CO",    "SRP40_CO"),
        ("HJ",    "SRP20_HJ",    "SRP25_HJ",     None),
        ("UTG",   None,          "SRP25_UTG",    None),
    ]
    print(f"  {'ポジション':<12} {'SBR20':>10} {'SBR25':>10} {'SBR40':>10}")
    print(f"  {'-'*12} {'-'*10} {'-'*10} {'-'*10}")

    for pos, k20, k25, k40 in pos_rows:
        def get_avg(k: str | None) -> str:
            if k is None:
                return "  —  "
            # 本スクリプトデータ → ref_data の順で探す
            d = all_data.get(k, ref_data.get(k.replace("(ref)",""), {}))
            return avg_ras(d)

        r20 = get_avg(k20)
        r25 = get_avg(k25)
        r40 = get_avg(k40)
        print(f"  {pos:<12} {r20:>10} {r25:>10} {r40:>10}")

    print()
    print("  (注: HJ/UTG は GTO Wizard MTTGeneral の対象外の可能性あり)")
    print()

    # 収集済みシナリオの詳細
    if all_data:
        print("  [収集済みシナリオ詳細]")
        for sc_key, brd in sorted(all_data.items()):
            n = len(brd)
            avg = sum(brd.values()) / n if n else 0
            print(f"    {sc_key:<15}: {n}ボード  平均RAS={avg:.1f}%")


# ─── メイン ─────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description="ポジション別 CBet RAS 収集スクリプト"
    )
    ap.add_argument("--collect", metavar="SCENARIO",
                    choices=list(SCENARIOS.keys()),
                    help="指定シナリオを収集 (例: SRP25_CO, SRP40_BTN)")
    ap.add_argument("--collect-all", action="store_true",
                    help="全シナリオを収集")
    ap.add_argument("--analyze", action="store_true",
                    help="収集済みデータを分析してポジション × SBR 比較表を出力")
    ap.add_argument("--probe-position", action="store_true",
                    dest="probe_position",
                    help="各ポジション × SBR × サイズの有効な組み合わせを探索")
    ap.add_argument("--force", action="store_true",
                    help="既存データを無視して再収集")
    args = ap.parse_args()

    if args.probe_position:
        probe_position()
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
