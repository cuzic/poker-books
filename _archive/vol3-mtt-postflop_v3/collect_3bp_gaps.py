#!/usr/bin/env python3
"""
collect_3bp_gaps.py — 3BP ギャップ補完収集スクリプト

【目的】
  既存の 3BP シナリオ (3BP20 BTN-BB / 3BP25_SB SB-BB) に加え、
  欠けている 3BP 組み合わせ (3BP25 BTN-BB / 3BP20 SB-BB / 3BP40 BTN-BB / 3BP40 SB-BB) を
  --probe で有効サイズを探索してから --collect で収集する。

【既知の 3BP】
  3BP20 BTN-BB: pf=F-F-F-F-F-R2-F-R7-C    (draw_study.py で確認済み)
  3BP25_SB SB-BB: pf=F-F-F-F-F-F-R3-R8-C  (draw_study.py で確認済み)

【使い方】
  TOKEN=xxx GWCLIENTID=xxx uv run collect_3bp_gaps.py --probe
  TOKEN=xxx GWCLIENTID=xxx uv run collect_3bp_gaps.py --collect 3BP25
  TOKEN=xxx GWCLIENTID=xxx uv run collect_3bp_gaps.py --collect-all
  uv run collect_3bp_gaps.py --analyze

【出力】
  findings/3bp_gaps_{SCENARIO}.jsonl
  各レコード: {"board_id":"K72_rain","board":"Ks7d2c","scenario":"3BP25",
               "label":"3BP SBR25 BTN-BB","cross":{...},"draw_agg":{...},
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

# ─── probe ターゲット定義 ────────────────────────────────────
# open_prefix + three_size + "-C" が preflop_actions になる
PROBE_TARGETS = [
    {
        "label": "3BP25 BTN-BB",
        "depth": 25.125,
        "open_prefix": "F-F-F-F-F-R2.1-F-",
        "three_sizes": ["R6", "R7", "R8", "R9", "R10"],
        "board": "Ks7d2c",
    },
    {
        "label": "3BP20 SB-BB",
        "depth": 20.125,
        "open_prefix": "F-F-F-F-F-F-R3-",
        "three_sizes": ["R7", "R8", "R9", "R10", "R11"],
        "board": "Ks7d2c",
    },
    {
        "label": "3BP40 BTN-BB",
        "depth": 40.125,
        "open_prefix": "F-F-F-F-F-R2.5-F-",
        "three_sizes": ["R7", "R8", "R9", "R10", "R11", "R12"],
        "board": "Ks7d2c",
    },
    {
        "label": "3BP40 SB-BB",
        "depth": 40.125,
        "open_prefix": "F-F-F-F-F-F-R3.5-",
        "three_sizes": ["R10", "R11", "R12", "R13", "R14"],
        "board": "Ks7d2c",
    },
]

# ─── シナリオ定義 ────────────────────────────────────────────
# --probe で発見した有効な pf を手動で記入して使う。
# 事前確認済み (draw_study.py より):
#   3BP20 BTN-BB: F-F-F-F-F-R2-F-R7-C  ✓
#   3BP25_SB SB-BB: F-F-F-F-F-F-R3-R8-C  ✓
# 以下は probe 後に更新すること
SCENARIOS: dict[str, dict[str, Any]] = {
    # 確認済み (draw_study.py で収集済み)
    "3BP20":    {"depth": 20.125, "pf": "F-F-F-F-F-R2-F-R7-C",   "label": "3BP SBR20   BTN-BB"},
    "3BP25_SB": {"depth": 25.125, "pf": "F-F-F-F-F-F-R3-R8-C",   "label": "3BP SBR25   SB-BB"},
    # probe 後に更新 (暫定値: probe で発見された値に置き換えること)
    "3BP25":    {"depth": 25.125, "pf": "PROBE_RESULT",           "label": "3BP SBR25   BTN-BB"},
    "3BP20_SB": {"depth": 20.125, "pf": "PROBE_RESULT",           "label": "3BP SBR20   SB-BB"},
    "3BP40":    {"depth": 40.125, "pf": "PROBE_RESULT",           "label": "3BP SBR40   BTN-BB"},
    "3BP40_SB": {"depth": 40.125, "pf": "PROBE_RESULT",           "label": "3BP SBR40   SB-BB"},
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


# ─── probe ──────────────────────────────────────────────────

def probe() -> None:
    """各 3BP ターゲットの有効な 3-bet サイズを探索する。"""
    print("\n=== probe: 3BP 有効サイズ探索 ===\n")
    found: list[dict[str, Any]] = []

    for tgt in PROBE_TARGETS:
        label     = tgt["label"]
        depth     = tgt["depth"]
        prefix    = tgt["open_prefix"]
        sizes     = tgt["three_sizes"]
        board     = tgt["board"]

        print(f"  [{label}]  depth={depth}  board={board}")
        for sz in sizes:
            pf = f"{prefix}{sz}-C"
            try:
                r = requests.get(BASE_URL, params={
                    "gametype": GT, "depth": str(depth), "stacks": "",
                    "preflop_actions": pf, "flop_actions": "X",
                    "turn_actions": "", "river_actions": "", "board": board,
                }, headers=make_headers(), timeout=30)
            except Exception as e:
                print(f"    エラー: {e}")
                continue

            if r.status_code == 200:
                data = r.json()
                n_act = len(data.get("action_solutions", []))
                print(f"    ✅ {sz}  pf={pf}  actions={n_act}")
                found.append({"label": label, "sz": sz, "pf": pf, "depth": depth})
            else:
                print(f"    ❌ {sz}  HTTP {r.status_code}")
            time.sleep(0.5)
        print()

    print("=== 有効な 3BP 組み合わせ一覧 ===")
    if found:
        for item in found:
            print(f"  ✅ {item['label']}: pf={item['pf']}")
        print()
        print("  上記の pf を SCENARIOS 辞書の 'PROBE_RESULT' と置き換えてください。")
    else:
        print("  (有効なものなし)")


# ─── 収集 ────────────────────────────────────────────────────

def collect_scenario(scenario_key: str, force: bool = False) -> None:
    if scenario_key not in SCENARIOS:
        print(f"Unknown scenario: {scenario_key}")
        return
    cfg = SCENARIOS[scenario_key]

    if cfg["pf"] == "PROBE_RESULT":
        print(f"  ⚠ {scenario_key}: pf が未設定です。--probe を実行して有効サイズを特定し、")
        print(f"     SCENARIOS['{scenario_key}']['pf'] に値を設定してください。")
        return

    outf = FINDINGS_DIR / f"3bp_gaps_{scenario_key}.jsonl"
    FINDINGS_DIR.mkdir(exist_ok=True)

    existing = load_existing(outf) if not force else set()
    if force and outf.exists():
        bak = outf.with_suffix(".jsonl.bak")
        outf.rename(bak)
        print(f"  --force: バックアップ → {bak}")

    label = cfg["label"]
    print(f"\n=== COLLECT: {label} ({scenario_key}) ===")
    print(f"  pf: {cfg['pf']}")
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
        if SCENARIOS[key]["pf"] != "PROBE_RESULT":
            collect_scenario(key, force=force)
        else:
            print(f"  スキップ: {key} (pf 未設定 — --probe で確認してください)")


# ─── 分析 ────────────────────────────────────────────────────

def analyze() -> None:
    """3BP RAS を SBR × ポジション別に比較する。"""
    # データ読み込み
    all_data: dict[str, dict[str, float]] = {}
    # 本スクリプト収集分
    for key in SCENARIOS:
        outf = FINDINGS_DIR / f"3bp_gaps_{key}.jsonl"
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

    # draw_study 既存データ (3BP20 / 3BP25_SB)
    for ds_key in ["3BP20", "3BP25_SB"]:
        if ds_key not in all_data:
            f = FINDINGS_DIR / f"draw_study_{ds_key}.jsonl"
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
                    all_data[ds_key] = brd

    def avg_ras(key: str) -> str:
        d = all_data.get(key, {})
        if not d:
            return "  —  "
        vals = list(d.values())
        return f"{sum(vals)/len(vals):5.1f}%"

    print("\n=== 3BP RAS 比較 ===")
    print()
    print(f"  {'ポジション':<12} {'SBR20':>10} {'SBR25':>10} {'SBR40':>10}")
    print(f"  {'-'*12} {'-'*10} {'-'*10} {'-'*10}")

    rows = [
        ("BTN-BB",  "3BP20",    "3BP25",    "3BP40"),
        ("SB-BB",   "3BP20_SB", "3BP25_SB", "3BP40_SB"),
    ]
    for pos, k20, k25, k40 in rows:
        print(f"  {pos:<12} {avg_ras(k20):>10} {avg_ras(k25):>10} {avg_ras(k40):>10}")

    print()
    print("  [参照: SRP の平均 RAS]")
    srp_data: dict[str, dict[str, float]] = {}
    for srp_key in ["SRP20", "SRP25"]:
        for prefix in ["draw_study", "board_ras"]:
            f = FINDINGS_DIR / f"{prefix}_{srp_key}.jsonl"
            if f.exists():
                brd = {}
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
                    srp_data[srp_key] = brd
                break

    def avg_srp(key: str) -> str:
        d = srp_data.get(key, {})
        if not d:
            return "  —  "
        vals = list(d.values())
        return f"{sum(vals)/len(vals):5.1f}%"

    print(f"  {'SRP BTN-BB':<12} {avg_srp('SRP20'):>10} {avg_srp('SRP25'):>10} {'  —  ':>10}")
    print()

    # ボード別詳細 (收集済みシナリオのみ)
    if all_data:
        print("  [収集済みシナリオ詳細]")
        for sc_key, brd in sorted(all_data.items()):
            n = len(brd)
            avg = sum(brd.values()) / n if n else 0
            label = SCENARIOS.get(sc_key, {}).get("label", sc_key)
            print(f"    {sc_key:<12} ({label}): {n}ボード  平均RAS={avg:.1f}%")


# ─── メイン ─────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description="3BP ギャップ補完収集スクリプト"
    )
    ap.add_argument("--probe", action="store_true",
                    help="3BP 有効サイズを探索 (先に実行推奨)")
    ap.add_argument("--collect", metavar="SCENARIO",
                    choices=list(SCENARIOS.keys()),
                    help="指定シナリオを収集 (例: 3BP25, 3BP40_SB)")
    ap.add_argument("--collect-all", action="store_true",
                    help="pf 設定済みの全シナリオを収集")
    ap.add_argument("--analyze", action="store_true",
                    help="収集済みデータを分析して SBR × ポジション比較表を出力")
    ap.add_argument("--force", action="store_true",
                    help="既存データを無視して再収集")
    args = ap.parse_args()

    if args.probe:
        probe()
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
