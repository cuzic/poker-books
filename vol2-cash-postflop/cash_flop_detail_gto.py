#!/usr/bin/env python3
"""
cash_flop_detail_gto.py — フロップ詳細調査 (4フェーズ)

フェーズ:
  size_dist  IP が各ボードで使う全サイズ分布 + 5類型別使用率
  size_oop   bet33/bet75 別の OOP fold/call/raise by 5類型
  donk       OOP Donk Bet 率 + IP 応答 by 5類型
  cr_resp    OOP CR 後の IP fold/call/3bet by 5類型
  all        全フェーズ実行

使い方:
  TOKEN=eyJ... GWCLIENTID=xxx PHASE=all  python3 cash_flop_detail_gto.py
  TOKEN=eyJ... GWCLIENTID=xxx PHASE=donk python3 cash_flop_detail_gto.py
  TOKEN=eyJ... GWCLIENTID=xxx BOARDS=1 PHASE=size_dist python3 cash_flop_detail_gto.py
"""

import os, sys, time
from pathlib import Path
from collections import defaultdict
import gto_api
from gto_api import (
    api_get, get_code, is_bet_code, dominant_bet, action_dist, load_json, save_json,
    ip_player, oop_player, all_bet_codes, agg_player, agg_sols, CAT5_ORDER,
)

PHASE  = os.environ.get("PHASE", "all")
BOARDS = int(os.environ.get("BOARDS", "2"))  # boards per type

FINDINGS_DIR  = Path(__file__).parent / "findings"
FINDINGS_DIR.mkdir(exist_ok=True)
PAIRWISE_JSON = FINDINGS_DIR / "cash_pairwise_gto.json"
OUTPUT_JSON   = FINDINGS_DIR / "cash_flop_detail_gto.json"

# ─────────────────── シナリオ定義 ───────────────────
SCENARIOS = [
    {"id": "SRP_IP",  "pf": "F-F-F-R2.5-F-C",   "ip": "BTN", "oop": "BB", "depth": 100, "spr": "~8"},
    {"id": "SRP_OOP", "pf": "F-F-F-F-R3-C",      "ip": "BB",  "oop": "SB", "depth": 100, "spr": "~8"},
    {"id": "3BP_IP",  "pf": "F-F-R2.5-R9-F-F-C", "ip": "BTN", "oop": "CO", "depth": 100, "spr": "~5"},
    {"id": "3BP_OOP", "pf": "F-F-F-R2.5-F-R9-C", "ip": "BTN", "oop": "BB", "depth": 100, "spr": "~5"},
]

# ─────────────────── ボード定義 ───────────────────
ALL_BOARDS = [
    {"type": "型1_ハイドライ",  "flop": "Ks7d2c", "desc": "K高・レインボー"},
    {"type": "型1_ハイドライ",  "flop": "As9d3c", "desc": "A高・レインボー"},
    {"type": "型2_ハイウェット", "flop": "Qh8d3s", "desc": "Q高・2トーン"},
    {"type": "型2_ハイウェット", "flop": "Kh9d5s", "desc": "K高・2トーン"},
    {"type": "型3_ロードライ",  "flop": "Jd7s5c", "desc": "J中・レインボー"},
    {"type": "型3_ロードライ",  "flop": "9s6d2c", "desc": "9中・レインボー"},
    {"type": "型4_ローウェット", "flop": "Th9s8d", "desc": "低連携・2トーン"},
    {"type": "型4_ローウェット", "flop": "9h8d7s", "desc": "9連続・レインボー"},
    {"type": "型5_モノトーン",  "flop": "Ah9h5h", "desc": "A高モノトーン"},
    {"type": "型5_モノトーン",  "flop": "Kd7d3d", "desc": "K高モノトーン"},
    {"type": "型6_ペア高",     "flop": "AsAcKd", "desc": "AAKペア"},
    {"type": "型6_ペア高",     "flop": "KhKd8c", "desc": "KK8ペア"},
    {"type": "型7_ペア低",     "flop": "7s7d2c", "desc": "77低ペア"},
    {"type": "型7_ペア低",     "flop": "4s4d9c", "desc": "44中ペア"},
]

_type_count = defaultdict(int)
BOARDS_LIST = []
for _b in ALL_BOARDS:
    if _type_count[_b["type"]] < BOARDS:
        BOARDS_LIST.append(_b)
        _type_count[_b["type"]] += 1

CAT_ORDER = CAT5_ORDER  # 後方互換エイリアス


# ═══════════════════════════════════════════════════════
# Phase 1: size_dist
#   IP が各ボード×シナリオで使う全サイズ + 5類型別頻度
# ═══════════════════════════════════════════════════════
def run_size_dist():
    results = []
    total = len(BOARDS_LIST) * len(SCENARIOS)
    done  = 0

    for bconf in BOARDS_LIST:
        for scen in SCENARIOS:
            done += 1
            flop  = bconf["flop"]
            label = f"{bconf['type']} {flop} × {scen['id']}"

            sols = api_get(flop, "X", scen["pf"], depth=scen["depth"])
            time.sleep(0.5)
            if not sols:
                print(f"  SKIP {label}", file=sys.stderr); continue

            action_sols = sols.get("action_solutions", [])
            bet_codes   = all_bet_codes(action_sols)
            dist        = action_dist(action_sols)

            plr = ip_player(sols)
            if not plr: continue

            # 全ベットコード + check を一括集計（1クエリで完結）
            action_map = {code: code for code in bet_codes}
            action_map["check"] = "X"
            cat_by_size = agg_player(plr, action_map)

            results.append({
                "board_type":  bconf["type"],
                "flop":        flop,
                "desc":        bconf["desc"],
                "scenario":    scen["id"],
                "action_dist": dist,
                "bet_codes":   bet_codes,
                "cat_by_size": cat_by_size,
            })
            sizes_str = " ".join(f"{d['code']}({d['freq']:.2f})" for d in dist if is_bet_code(d["code"]))
            print(f"[{done:3d}/{total}] {label}  bets={sizes_str}")

    return results


# ═══════════════════════════════════════════════════════
# Phase 2: size_oop
#   bet33 / bet75 別の OOP defense by 5類型
#   アグレッサー (SRP_IP, 3BP_IP) のシナリオのみ
# ═══════════════════════════════════════════════════════
# シナリオ別の実際のサイズペア (size_dist から判明)
SIZE_OOP_PAIRS = {
    "SRP_IP":  ["R1.8",  "R6.4"],
    "SRP_OOP": ["R2",    "R6.7"],
    "3BP_IP":  ["R3.9",  "R11.5"],
    "3BP_OOP": ["R3.7",  "R11.2"],
}

def run_size_oop():
    results = []
    total = sum(len(BOARDS_LIST) * len(sizes) for sizes in SIZE_OOP_PAIRS.values())
    done  = 0

    for bconf in BOARDS_LIST:
        for scen in SCENARIOS:
            for size in SIZE_OOP_PAIRS[scen["id"]]:
                done += 1
                flop  = bconf["flop"]
                label = f"{bconf['type']} {flop} × {scen['id']} × {size}"

                sols = api_get(flop, f"X-{size}", scen["pf"], depth=scen["depth"])
                time.sleep(0.5)
                if not sols:
                    print(f"  SKIP {label}", file=sys.stderr); continue

                action_sols = sols.get("action_solutions", [])
                cr_c = next((get_code(a) for a in action_sols if is_bet_code(get_code(a))), None)

                # fold/call/raise ノード → action_solutions から直接集計
                oop_def = agg_sols(action_sols)

                results.append({
                    "board_type":  bconf["type"],
                    "flop":        flop,
                    "desc":        bconf["desc"],
                    "scenario":    scen["id"],
                    "bet_size":    size,
                    "cr_code":     cr_c,
                    "oop_defense": oop_def,
                })
                bc  = oop_def.get("BC",  {})
                air = oop_def.get("Air", {})
                print(f"[{done:3d}/{total}] {label}  BC_fold={bc.get('fold','NA')}%  Air_fold={air.get('fold','NA')}%")

    return results


# ═══════════════════════════════════════════════════════
# Phase 3: donk
#   flop_actions="" → OOP 先行アクション
#   donk_code が存在すれば IP 応答も取得
# ═══════════════════════════════════════════════════════
def run_donk():
    results = []
    total = len(BOARDS_LIST) * len(SCENARIOS)
    done  = 0

    for bconf in BOARDS_LIST:
        for scen in SCENARIOS:
            done += 1
            flop  = bconf["flop"]
            label = f"{bconf['type']} {flop} × {scen['id']}"

            # Step 1: OOP 先行ノード (flop_actions="")
            sols1 = api_get(flop, "", scen["pf"], depth=scen["depth"])
            time.sleep(0.5)
            if not sols1:
                print(f"  SKIP {label}", file=sys.stderr); continue

            action_sols1 = sols1.get("action_solutions", [])
            donk_code  = dominant_bet(action_sols1)
            check_c    = next((get_code(a) for a in action_sols1 if get_code(a) == "X"), "X")

            plr_oop = oop_player(sols1)
            if not plr_oop: continue

            act_map_oop = {"check": check_c}
            if donk_code: act_map_oop["donk"] = donk_code
            donk_by_cat = agg_player(plr_oop, act_map_oop)

            # Step 2: IP が donk に応答
            ip_vs_donk = None
            if donk_code:
                sols2 = api_get(flop, donk_code, scen["pf"], depth=scen["depth"])
                time.sleep(0.5)
                if sols2:
                    action_sols2 = sols2.get("action_solutions", [])
                    # fold/call/raise ノード → action_solutions から直接集計
                    ip_vs_donk = agg_sols(action_sols2)

            results.append({
                "board_type":  bconf["type"],
                "flop":        flop,
                "desc":        bconf["desc"],
                "scenario":    scen["id"],
                "donk_code":   donk_code,
                "donk_by_cat": donk_by_cat,
                "ip_vs_donk":  ip_vs_donk,
            })
            d_v   = donk_by_cat.get("V",   {}).get("donk", "NA")
            d_air = donk_by_cat.get("Air", {}).get("donk", "NA")
            print(f"[{done:3d}/{total}] {label}  donk={donk_code}  V_donk={d_v}%  Air_donk={d_air}%")

    return results


# ═══════════════════════════════════════════════════════
# Phase 4: cr_resp
#   cash_pairwise_gto.json の cbet_code+cr_code を使って
#   flop_actions="X-{cbet}-{cr}" → IP 応答 (fold/call/3bet)
# ═══════════════════════════════════════════════════════
def run_cr_resp():
    if not PAIRWISE_JSON.exists():
        print("ERROR: cash_pairwise_gto.json が見つかりません", file=sys.stderr)
        return []

    pairwise = load_json(PAIRWISE_JSON, default={})

    # cr_code が存在するエントリのみ対象
    cr_entries = [r for r in pairwise.get("flop", []) if r.get("cr_code")]
    print(f"  CR entries found: {len(cr_entries)}")

    results = []
    done  = 0
    total = len(cr_entries)

    for r in cr_entries:
        done += 1
        flop      = r["flop"]
        cbet_code = r["cbet_code"]
        cr_code   = r["cr_code"]
        scen_id   = r["scenario"]
        scen      = next((s for s in SCENARIOS if s["id"] == scen_id), None)
        if not scen: continue

        label = f"{r['board_type']} {flop} × {scen_id} (cbet={cbet_code} cr={cr_code})"

        # OOP がチェックレイズした後の IP 応答ノード
        sols = api_get(flop, f"X-{cbet_code}-{cr_code}", scen["pf"], depth=scen["depth"])
        time.sleep(0.5)
        if not sols:
            print(f"  SKIP {label}", file=sys.stderr); continue

        action_sols = sols.get("action_solutions", [])
        _3bet_c = next((get_code(a) for a in action_sols if is_bet_code(get_code(a))), None)
        # fold/call/3bet ノード → action_solutions から直接集計
        ip_vs_cr = agg_sols(action_sols)

        results.append({
            "board_type": r["board_type"],
            "flop":       flop,
            "desc":       r["desc"],
            "scenario":   scen_id,
            "cbet_code":  cbet_code,
            "cr_code":    cr_code,
            "3bet_code":  _3bet_c,
            "ip_vs_cr":   ip_vs_cr,
        })
        v   = ip_vs_cr.get("V",   {}).get("fold", "NA")
        bc  = ip_vs_cr.get("BC",  {}).get("fold", "NA")
        air = ip_vs_cr.get("Air", {}).get("fold", "NA")
        print(f"[{done:3d}/{total}] {label}  IP_fold: V={v}% BC={bc}% Air={air}%")

    return results


# ═══════════════════════════════════════════════════════
# 保存 / エントリポイント
# ═══════════════════════════════════════════════════════
def load_existing():
    return load_json(OUTPUT_JSON, default={"size_dist": [], "size_oop": [], "donk": [], "cr_resp": []})

def save(data):
    save_json(OUTPUT_JSON, data)
    print(f"Saved → {OUTPUT_JSON}")


def _run_phase(label, fn, data, key):
    print(f"\n═══ {label} ═══")
    try:
        data[key] = fn()
    except RuntimeError as e:
        if "DAILY_QUOTA_EXCEEDED" in str(e):
            print(f"\n⚠ 日次クォータ超過 — {key} 途中まで保存", file=sys.stderr)
            save(data)
            sys.exit(2)
        raise
    save(data)


if __name__ == "__main__":
    if not gto_api.TOKEN:
        print("ERROR: TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    data = load_existing()
    print(f"Phase={PHASE}  Boards={len(BOARDS_LIST)} ({BOARDS}/type)  Scenarios={len(SCENARIOS)}\n")

    if PHASE in ("all", "size_dist"):
        _run_phase("Phase 1: Size Distribution", run_size_dist, data, "size_dist")

    if PHASE in ("all", "size_oop"):
        _run_phase("Phase 2: Size × OOP Defense", run_size_oop, data, "size_oop")

    if PHASE in ("all", "donk"):
        _run_phase("Phase 3: OOP Donk Bet", run_donk, data, "donk")

    if PHASE in ("all", "cr_resp"):
        _run_phase("Phase 4: IP vs Check-Raise", run_cr_resp, data, "cr_resp")

    print("\nDone.")
