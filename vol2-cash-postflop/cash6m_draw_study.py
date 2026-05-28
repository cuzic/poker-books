#!/usr/bin/env python3
"""
cash6m_draw_study.py — Cash6m 全ポジション CBet 分析

【目的】
  MTT では取れない HJ/UTG ポジションのポストフロップ CBet データを収集し、
  MTT BTN/CO との比較から HJ/UTG 補正値を導く。

【gametype】
  Cash6mTest_6mNL100R2 (100BB 深度)

【シナリオ】
  UTG-BB, HJ-BB, CO-BB, BTN-BB, SB-BB (各 SRP/3BP)

使い方:
  TOKEN=... python3 cash6m_draw_study.py --collect [--force]
  TOKEN=... python3 cash6m_draw_study.py --compare
  TOKEN=... python3 cash6m_draw_study.py --position-overview
"""

import os, sys, json, time, argparse, requests
from pathlib import Path
from collections import defaultdict
from typing import Any

TOKEN      = os.environ.get("TOKEN", "")
GT         = "Cash6mTest_6mNL100R2"
DEPTH      = 100.0   # 100BB
FINDINGS   = Path(__file__).parent / "findings" / "cash6m"
BASE_URL   = "https://api.gtowizard.com/v4/solutions/spot-solution/"

# ── シナリオ定義 ─────────────────────────────────────
# preflop_actions: 6-max (UTG/HJ/CO/BTN/SB/BB)
# flop_actions="X": OOP checks → IP CBet 判断
SCENARIO_CONFIGS: dict[str, dict[str, Any]] = {
    # ── 各ポジション vs BB SRP ──
    "UTG_BB": {"pf": "R2-F-F-F-F-C",    "label": "UTG-BB SRP 100BB", "pos": "UTG_BB"},
    "HJ_BB":  {"pf": "F-R2-F-F-F-C",    "label": "HJ-BB  SRP 100BB", "pos": "HJ_BB"},
    "CO_BB":  {"pf": "F-F-R2-F-F-C",    "label": "CO-BB  SRP 100BB", "pos": "CO_BB"},
    "BTN_BB": {"pf": "F-F-F-R2-F-C",    "label": "BTN-BB SRP 100BB", "pos": "BTN_BB"},
    "SB_BB":  {"pf": "F-F-F-F-R3-C",    "label": "SB-BB  SRP 100BB", "pos": "SB_BB"},
    # ── 3BP (BTN open → BB 3bet → BTN call) ──
    "BTN_BB_3BP": {"pf": "F-F-F-R2-F-R7-C",  "label": "BTN-BB 3BP 100BB", "pos": "BTN_BB"},
    "CO_BB_3BP":  {"pf": "F-F-R2-F-F-R7-C",  "label": "CO-BB  3BP 100BB", "pos": "CO_BB"},
    # ── 200BB 深度 (BTN-BB のみ) ──
    "BTN_BB_200": {"pf": "F-F-F-R2-F-C", "label": "BTN-BB SRP 200BB", "pos": "BTN_BB", "depth": 200.0},
}

# ── 調査ボード（MTT study と同一セット）───────────────
STUDY_BOARDS: list[dict[str, str]] = [
    {"board_id": "K98_rain", "board": "Kd9s8c", "group": "K98", "label": "K-9-8 rain"},
    {"board_id": "K98_fd",   "board": "Kd9c8d", "group": "K98", "label": "K-9-8 2tone"},
    {"board_id": "T98_rain", "board": "Th9s8d", "group": "T98", "label": "T-9-8 rain"},
    {"board_id": "T98_fd",   "board": "Td9s8d", "group": "T98", "label": "T-9-8 2tone"},
    {"board_id": "K72_rain", "board": "Ks7d2c", "group": "K72", "label": "K-7-2 rain"},
    {"board_id": "K72_fd",   "board": "Kd7c2d", "group": "K72", "label": "K-7-2 2tone"},
    {"board_id": "Q83_rain", "board": "Qh8d3s", "group": "Q83", "label": "Q-8-3 rain"},
    {"board_id": "Q83_fd",   "board": "Qd8c3d", "group": "Q83", "label": "Q-8-3 2tone"},
    {"board_id": "J73_rain", "board": "Jh7d3s", "group": "J73", "label": "J-7-3 rain"},
    {"board_id": "J73_fd",   "board": "Jd7c3d", "group": "J73", "label": "J-7-3 2tone"},
    {"board_id": "A94_rain", "board": "Ah9d4s", "group": "A94", "label": "A-9-4 rain"},
    {"board_id": "A94_fd",   "board": "Ad9c4d", "group": "A94", "label": "A-9-4 2tone"},
    {"board_id": "765_rain", "board": "7h6d5s", "group": "765", "label": "7-6-5 rain"},
    {"board_id": "765_fd",   "board": "7d6c5d", "group": "765", "label": "7-6-5 2tone"},
    {"board_id": "KJT_rain", "board": "KhJdTs", "group": "KJT", "label": "K-J-T rain"},
    {"board_id": "KJT_fd",   "board": "KdJcTd", "group": "KJT", "label": "K-J-T 2tone"},
    {"board_id": "T74_rain", "board": "Th7d4s", "group": "T74", "label": "T-7-4 rain"},
    {"board_id": "T74_fd",   "board": "Td7c4d", "group": "T74", "label": "T-7-4 2tone"},
    {"board_id": "A72_rain", "board": "Ah7d2s", "group": "A72", "label": "A-7-2 rain"},
    {"board_id": "A72_fd",   "board": "Ad7c2d", "group": "A72", "label": "A-7-2 2tone"},
    {"board_id": "742_rain", "board": "7h4d2s", "group": "742", "label": "7-4-2 rain"},
    {"board_id": "742_fd",   "board": "7d4c2d", "group": "742", "label": "7-4-2 2tone"},
    {"board_id": "KK8_rain", "board": "KhKd8c", "group": "KK8", "label": "K-K-8 rain"},
    {"board_id": "AA7_rain", "board": "AhAd7c", "group": "AA7", "label": "A-A-7 rain"},
]


# ── API ──────────────────────────────────────────────

def make_headers() -> dict[str, str]:
    return {
        "accept": "application/json",
        "authorization": f"Bearer {TOKEN}",
        "origin": "https://app.gtowizard.com",
        "referer": "https://app.gtowizard.com/",
    }


def check_auth() -> bool:
    import base64 as _b64
    try:
        payload = TOKEN.split(".")[1] + "=="
        data = json.loads(_b64.b64decode(payload))
        exp = data.get("exp", 0)
        remaining = exp - time.time()
        if remaining < 60:
            print(f"⚠️  トークン期限切れ (残り {remaining:.0f}秒)")
            return False
        print(f"✅ 認証OK（残り{remaining/60:.1f}分）")
        return True
    except Exception:
        print("⚠️  トークン検証失敗（続行）")
        return True


def call_api(board: str, pf: str, depth: float = DEPTH) -> dict | None:
    params = {
        "gametype": GT, "depth": str(depth), "stacks": "",
        "preflop_actions": pf,
        "flop_actions": "X",   # OOP checks → IP CBet 判断
        "turn_actions": "", "river_actions": "", "board": board,
    }
    for attempt in range(4):
        r = requests.get(BASE_URL, params=params, headers=make_headers(), timeout=30)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 10))
            print(f"    429 rate limit, {wait}s 待機...")
            time.sleep(wait)
            continue
        if r.status_code == 401:
            print(f"    401 Unauthorized")
            return None
        if r.status_code == 204:
            return None   # データなし
        print(f"    HTTP {r.status_code}: {r.text[:100]}")
        if attempt < 3:
            time.sleep(3)
    return None


def compute_cross(data: dict) -> dict:
    """(hand × draw) bet% クロス集計。draw_study.py と同一ロジック。"""
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


# ── 収集 ────────────────────────────────────────────

def collect_scenario(sc_key: str, cfg: dict, force: bool) -> None:
    depth = cfg.get("depth", DEPTH)
    outf = FINDINGS / f"cash6m_{sc_key}.jsonl"
    FINDINGS.mkdir(parents=True, exist_ok=True)

    existing: dict[str, Any] = {}
    if outf.exists() and not force:
        with open(outf) as f:
            for line in f:
                rec = json.loads(line)
                existing[rec["board_id"]] = rec

    written = 0
    with open(outf, "w") as f:
        for bspec in STUDY_BOARDS:
            bid = bspec["board_id"]

            if bid in existing and not force:
                f.write(json.dumps(existing[bid]) + "\n")
                continue

            print(f"  {bid} ... ", end="", flush=True)
            data = call_api(bspec["board"], cfg["pf"], depth)
            if data is None:
                print("SKIP (no data)")
                continue

            cross_result = compute_cross(data)
            rec = {
                "board_id":  bid,
                "group":     bspec["group"],
                "board":     bspec["board"],
                "label":     bspec["label"],
                "scenario":  sc_key,
                "gametype":  GT,
                "depth":     depth,
                **cross_result,
            }
            f.write(json.dumps(rec) + "\n")
            written += 1
            print(f"ok (n={rec['n_combos']})")
            time.sleep(0.5)

    print(f"  → {sc_key}: {written} 新規, {len(existing)} スキップ")


# ── 比較分析 ─────────────────────────────────────────

def load_cash6m(sc_keys: list[str] | None = None) -> dict[str, list]:
    """シナリオ → レコードリスト のマップを返す"""
    result = {}
    for f in sorted(FINDINGS.glob("cash6m_*.jsonl")):
        sc = f.stem.replace("cash6m_", "")
        if sc_keys and sc not in sc_keys:
            continue
        recs = []
        with open(f) as fh:
            for line in fh:
                recs.append(json.loads(line))
        result[sc] = recs
    return result


def position_overview(data: dict[str, list]) -> None:
    """各シナリオの全ボード平均 CBet% をボード型別に表示"""
    # ras (no_draw bet%) が overall CBet の proxy
    print("\n=== ポジション別 平均 RAS (no_draw bet%) ===")
    print(f"{'シナリオ':<14}", end="")
    for grp in ["K98","T98","K72","A94","765","KJT","742","AA7"]:
        print(f"  {grp:>4}", end="")
    print(f"  {'全avg':>5}")
    print("-" * 90)

    for sc, recs in sorted(data.items()):
        row = {}
        for rec in recs:
            nd = rec.get("draw_agg", {}).get("no_draw", {})
            row[rec["group"]] = nd.get("bet_pct", 0)
        print(f"{sc:<14}", end="")
        vals = []
        for grp in ["K98","T98","K72","A94","765","KJT","742","AA7"]:
            v = row.get(grp)
            if v is not None:
                print(f"  {v:>4.0f}%", end="")
                vals.append(v)
            else:
                print(f"  {'--':>4}", end="")
        avg = sum(vals)/len(vals) if vals else 0
        print(f"  {avg:>4.0f}%")

    print()
    print("=== ポジション別 手タイプ別 平均ベット% ===")
    KEY_HANDS = ["no_made_hand", "ace_high", "third_pair", "second_pair",
                 "top_pair", "overpair", "two_pair", "set"]
    print(f"{'ハンド':<14}", end="")
    sc_list = sorted(data.keys())
    for sc in sc_list:
        print(f"  {sc:>9}", end="")
    print()
    print("-" * (14 + 11 * len(sc_list)))

    hand_avgs: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for sc, recs in data.items():
        for rec in recs:
            ha = rec.get("hand_agg", {})
            for hn, hv in ha.items():
                hand_avgs[hn][sc].append(hv["bet_pct"])

    for hn in KEY_HANDS:
        print(f"{hn:<14}", end="")
        for sc in sc_list:
            vals = hand_avgs[hn].get(sc, [])
            avg = sum(vals)/len(vals) if vals else None
            if avg is not None:
                print(f"  {avg:>8.1f}%", end="")
            else:
                print(f"  {'--':>8}", end="")
        print()


def compare_mtt_cash(mtt_dir: Path, sc_map: dict[str, str]) -> None:
    """
    MTT シナリオ vs Cash6m シナリオを同ボードで比較。
    sc_map: {mtt_sc_key: cash6m_sc_key}
    """
    # key: (scenario, board_id)
    mtt_data: dict[tuple[str, str], dict] = {}
    for sc in sc_map:
        fp = mtt_dir / f"draw_study_{sc}.jsonl"
        if not fp.exists():
            continue
        with open(fp) as f:
            for line in f:
                rec = json.loads(line)
                mtt_data[(sc, rec["board_id"])] = rec

    cash_data: dict[tuple[str, str], dict] = {}
    for sc in sc_map.values():
        fp = FINDINGS / f"cash6m_{sc}.jsonl"
        if not fp.exists():
            continue
        with open(fp) as f:
            for line in f:
                rec = json.loads(line)
                cash_data[(sc, rec["board_id"])] = rec

    print("\n=== MTT vs Cash6m 比較 (RAS: no_draw bet%) ===")
    print(f"{'ボード':<10} {'MTT':>8} {'Cash':>8} {'差':>6}")
    print("-" * 38)

    diffs = []
    for mtt_sc, cash_sc in sc_map.items():
        print(f"\n[{mtt_sc} vs {cash_sc}]")
        for bid in ["K98_rain","T98_rain","K72_rain","A94_rain","765_rain","KJT_rain","742_rain","KK8_rain"]:
            mr = mtt_data.get((mtt_sc, bid), {})
            cr = cash_data.get((cash_sc, bid), {})
            m_ras = mr.get("draw_agg", {}).get("no_draw", {}).get("bet_pct")
            c_ras = cr.get("draw_agg", {}).get("no_draw", {}).get("bet_pct")
            if m_ras is not None and c_ras is not None:
                diff = c_ras - m_ras
                diffs.append(diff)
                print(f"  {bid:<12} MTT={m_ras:5.1f}%  Cash={c_ras:5.1f}%  diff={diff:+.1f}%")
    if diffs:
        import statistics
        print(f"\n  平均差: Cash - MTT = {sum(diffs)/len(diffs):+.1f}%  "
              f"std={statistics.stdev(diffs):.1f}%")


# ── メイン ───────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collect",          action="store_true", help="データ収集")
    parser.add_argument("--compare",          action="store_true", help="MTT vs Cash 比較")
    parser.add_argument("--position-overview",action="store_true", help="ポジション別概要")
    parser.add_argument("--scenario",         default=None,        help="特定シナリオのみ (カンマ区切り)")
    parser.add_argument("--force",            action="store_true", help="既存データを上書き")
    args = parser.parse_args()

    if not TOKEN:
        print("エラー: TOKEN 環境変数が未設定")
        sys.exit(1)

    if args.collect:
        check_auth()
        targets = args.scenario.split(",") if args.scenario else list(SCENARIO_CONFIGS.keys())
        for sc_key in targets:
            if sc_key not in SCENARIO_CONFIGS:
                print(f"未知のシナリオ: {sc_key}")
                continue
            cfg = SCENARIO_CONFIGS[sc_key]
            print(f"\n【{sc_key}】 {cfg['label']}")
            collect_scenario(sc_key, cfg, args.force)
        print("\n✅ 収集完了")

    if args.compare:
        mtt_dir = Path(__file__).parent.parent / "mtt-postflop" / "findings"
        sc_map = {
            "SRP25": "BTN_BB",   # MTT SRP25 vs Cash BTN-BB
            "SRP20": "BTN_BB",   # MTT SRP20 vs Cash BTN-BB
            "SRP20_CO": "CO_BB", # MTT CO vs Cash CO
        }
        cash_data = load_cash6m()
        compare_mtt_cash(mtt_dir, sc_map)

    if args.position_overview:
        cash_data = load_cash6m()
        if not cash_data:
            print("データなし。先に --collect を実行してください")
            sys.exit(1)
        position_overview(cash_data)


if __name__ == "__main__":
    main()
