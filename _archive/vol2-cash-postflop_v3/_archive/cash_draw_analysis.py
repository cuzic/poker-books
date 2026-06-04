#!/usr/bin/env python3
"""
draw_categories + simple_hand_counters 調査スクリプト

Phase 1: 動作検証（2コール）
Phase 2: 全14シナリオ × 7型 の draw_categories 収集
Phase 3: 特定ボードの made+draw クロス集計（simple_hand_counters）

使い方:
  TOKEN=eyJ... GWCLIENTID=xxx python3 cash_draw_analysis.py
"""

import os, sys, json, time, requests
from pathlib import Path

TOKEN      = os.environ.get("TOKEN", "")
GWCLIENTID = os.environ.get("GWCLIENTID", "")
GT         = "Cash6mGeneral_6mNL25R25"
BASE_URL   = "https://api.gtowizard.com/v4/solutions/spot-solution/"
FINDINGS   = Path(__file__).parent / "findings"
FINDINGS.mkdir(exist_ok=True)

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "authorization": f"Bearer {TOKEN}",
    "gwclientid": GWCLIENTID,
    "origin": "https://app.gtowizard.com",
    "referer": "https://app.gtowizard.com/",
}

# ─── シナリオ定義（cash_multistreet.py と同じ）───────────────────
SCENARIOS = {
    "BTN_BB":      {"pf": "F-F-F-R2.5-F-C",   "ip": "BTN", "oop": "BB"},
    "CO_BB":       {"pf": "F-F-R2.5-F-F-C",   "ip": "CO",  "oop": "BB"},
    "HJ_BB":       {"pf": "F-R2.5-F-F-F-C",   "ip": "HJ",  "oop": "BB"},
    "UTG_BB":      {"pf": "R2.5-F-F-F-F-C",   "ip": "UTG", "oop": "BB"},
    "SB_BB":       {"pf": "F-F-F-F-R3-C",     "ip": "BB",  "oop": "SB"},
    "BTN_SB":      {"pf": "F-F-F-R2.5-C-F",   "ip": "BTN", "oop": "SB"},
    "HJ_BTN":      {"pf": "F-R2.5-F-C-F-F",   "ip": "BTN", "oop": "HJ"},
    "CO_BTN":      {"pf": "F-F-R2.5-C-F-F",   "ip": "BTN", "oop": "CO"},
    "UTG_CO":      {"pf": "R2.5-F-C-F-F-F",   "ip": "CO",  "oop": "UTG"},
    "BTN_3BP":     {"pf": "F-F-F-R2.5-F-R9-C","ip": "BTN", "oop": "BB"},
    "CO_BB_3BP":   {"pf": "F-F-R2.5-F-F-R9-C","ip": "CO",  "oop": "BB"},
    "CO_BTN_3BP":  {"pf": "F-F-R2.5-R9-F-F",  "ip": "BTN", "oop": "CO"},
    "HJ_BTN_3BP":  {"pf": "F-R2.5-F-R9-F-F",  "ip": "BTN", "oop": "HJ"},
    "BTN_SB_3BP":  {"pf": "F-F-F-R2.5-R9-F-C","ip": "BTN", "oop": "SB"},
}

# ─── ボード7型（代表ボード）─────────────────────────────────────
BOARDS = [
    ("型1_ハイドライ",   "Ks7d2c"),
    ("型2_ハイウェット", "Qh8d3s"),
    ("型3_ロードライ",   "Jd7s5c"),
    ("型4_ローウェット", "Th9s8d"),
    ("型5_モノトーン",   "Ah9h5h"),
    ("型6_ペア高",       "AsAcKd"),
    ("型7_ペア低",       "7s7d2c"),
]

# ─── made+draw クロス集計対象コンボ ──────────────────────────────
# (board, 注目コンボ群, 理由)
CROSS_COMBOS = {
    "Th9s8d": {  # 型4 ローウェット
        "JTs":  "top_pair + OESD (J-T-9-8 needs Q/7)",
        "97s":  "second_pair + OESD (7-8-9-T needs J/6)",
        "87s":  "third_pair + OESD (7-8-9-T needs J/6)",
        "J9s":  "no_pair + OESD (8-9-T-J needs Q/7)",
        "AJs":  "overcards + gutshot",
        "QJs":  "overcards + gutshot (9-T-J-Q needs K/8)",
        "55":   "underpair, no draw",
        "AKo":  "overcards, no draw",
    },
    "Qh8d3s": {  # 型2 ハイウェット
        "JTs":  "no_pair + gutshot (8-9-T-J needs Q/7)",
        "T9s":  "no_pair + gutshot (9-T + FD?)",
        "97s":  "no_pair + gutshot (7-8-9-T? needs J/6... or bd)",
        "87s":  "no_pair + gutshot (7-8-9 needs T)",
        "77":   "underpair, no draw",
        "KQo":  "top_pair + no draw",
        "AJo":  "overcards + no draw",
    },
    "Jd7s5c": {  # 型3 ロードライ
        "86s":  "no_pair + OESD (5-6-7-8 needs 9/4)",
        "64s":  "no_pair + OESD (4-5-6-7 needs 8/3)",
        "87s":  "no_pair + OESD (5-6-7-8? board 7 pairs) → second_pair + OESD",
        "98s":  "no_pair + gutshot (7-8-9-J needs T)",
        "TT":   "overpair, no draw",
        "AKo":  "overcards, no draw",
    },
    "Qh8d3s": {  # 型2 再確認（flush draw board）
        "Ah2h": "flush_draw + no pair (A-high FD)",
        "Kh6h": "flush_draw + no pair",
        "9h7h": "flush_draw + gutshot",
    },
}

# ─── API ─────────────────────────────────────────────────────────
def call_api(board, flop="X", pf="F-F-F-R2.5-F-C"):
    r = requests.get(BASE_URL, params={
        "gametype": GT, "depth": "100", "stacks": "",
        "preflop_actions": pf, "flop_actions": flop,
        "turn_actions": "", "river_actions": "", "board": board,
    }, headers=HEADERS, timeout=30)
    if r.status_code != 200:
        print(f"  HTTP {r.status_code}: {r.text[:80]}")
        return None
    d = r.json()
    if "action_solutions" not in d:
        print(f"  ERR: {d.get('code','?')} {d.get('detail','')}")
        return None
    return d

def extract_draw_categories(data, target_pos="IP"):
    """draw_categories の {name: {combos, bet%}} を返す"""
    for pi in data.get("players_info", []):
        if pi["player"]["relative_postflop_position"] != target_pos:
            continue
        result = {}
        for dc in pi.get("draw_categories", []):
            combos = dc["total_combos"]
            if combos < 0.3:
                continue
            af = dc.get("actions_total_frequencies", {})
            bet = sum(v for k, v in af.items() if k.startswith("R"))
            result[dc["name"]] = {
                "combos": round(combos, 1),
                "bet_pct": round(bet * 100, 1),
                "check_pct": round((1 - bet) * 100, 1),
            }
        return result
    return {}

def extract_hand_categories(data, target_pos="IP"):
    for pi in data.get("players_info", []):
        if pi["player"]["relative_postflop_position"] != target_pos:
            continue
        result = {}
        for hc in pi.get("hand_categories", []):
            combos = hc["total_combos"]
            if combos < 0.3:
                continue
            af = hc.get("actions_total_frequencies", {})
            bet = sum(v for k, v in af.items() if k.startswith("R"))
            result[hc["name"]] = {
                "combos": round(combos, 1),
                "bet_pct": round(bet * 100, 1),
            }
        return result
    return {}

def extract_simple_hand_counters(data, target_pos="IP"):
    for pi in data.get("players_info", []):
        if pi["player"]["relative_postflop_position"] != target_pos:
            continue
        shc = pi.get("simple_hand_counters", {})
        result = {}
        for hand, v in shc.items():
            if v.get("total_combos", 0) < 0.1:
                continue
            af = v.get("actions_total_frequencies", {})
            bet = sum(val for k, val in af.items() if k.startswith("R"))
            result[hand] = {
                "combos": round(v["total_combos"], 2),
                "bet_pct": round(bet * 100, 1),
                "eq": round(v.get("hand_eq", 0) * 100, 1),
                "ev": round(v.get("hand_ev", 0), 3),
            }
        return result
    return {}

# ─── Phase 1: 動作検証 ───────────────────────────────────────────
def phase1_verify():
    print("=" * 60)
    print("Phase 1: 動作検証")
    print("=" * 60)

    # テスト1: BTN_BB / 型4 で draw_categories が取れるか
    print("\n[Test 1] BTN_BB / Th9s8d — draw_categories")
    d = call_api("Th9s8d")
    if d is None:
        print("  ❌ FAIL: APIコール失敗"); return False

    dc = extract_draw_categories(d, "IP")
    if not dc:
        print("  ❌ FAIL: draw_categories 空"); return False

    print(f"  ✅ OK: {list(dc.keys())}")
    for name, v in dc.items():
        print(f"     {name:20s}  combos={v['combos']:5.1f}  bet%={v['bet_pct']:4.1f}%")
    time.sleep(0.5)

    # テスト2: BTN_BB / 型4 で simple_hand_counters から JTs と 97s が取れるか
    print("\n[Test 2] BTN_BB / Th9s8d — simple_hand_counters (JTs, 97s)")
    shc = extract_simple_hand_counters(d, "IP")
    if not shc:
        print("  ❌ FAIL: simple_hand_counters 空"); return False

    for hand in ["JTs", "97s", "87s", "AKo", "55"]:
        v = shc.get(hand)
        if v:
            print(f"  ✅ {hand:6s}  combos={v['combos']:4.1f}  bet%={v['bet_pct']:5.1f}%  eq={v['eq']:4.1f}%")
        else:
            print(f"  ⚠️  {hand:6s} → not found in range")

    print("\n✅ Phase 1 完了")
    return True

# ─── Phase 2: 全シナリオ × 全型の draw_categories ──────────────
def phase2_all_draw():
    print("\n" + "=" * 60)
    print("Phase 2: 全14シナリオ × 7型 draw_categories 収集")
    print("=" * 60)

    all_results = {}
    total = len(SCENARIOS) * len(BOARDS)
    done  = 0

    for scen_name, scen in SCENARIOS.items():
        all_results[scen_name] = {}
        for board_type, board in BOARDS:
            done += 1
            label = f"{scen_name}/{board_type}"
            print(f"  [{done:2d}/{total}] {label} ... ", end="", flush=True)

            d = call_api(board, pf=scen["pf"])
            if d is None:
                print("SKIP")
                all_results[scen_name][board_type] = None
                time.sleep(0.3)
                continue

            ip_pos  = scen["ip"]
            oop_pos = scen["oop"]

            ip_draw  = extract_draw_categories(d, "IP")
            oop_draw = extract_draw_categories(d, "OOP")
            ip_hc    = extract_hand_categories(d, "IP")
            oop_hc   = extract_hand_categories(d, "OOP")

            all_results[scen_name][board_type] = {
                "board": board,
                "ip_pos": ip_pos,
                "oop_pos": oop_pos,
                "ip_draw":  ip_draw,
                "oop_draw": oop_draw,
                "ip_hand":  ip_hc,
                "oop_hand": oop_hc,
            }

            # サマリーをターミナルに表示
            dc_summary = " ".join(
                f"{k.replace('_','')}={v['bet_pct']}%"
                for k, v in ip_draw.items() if v["combos"] > 1
            )
            print(f"OK  IP draw: {dc_summary}")
            time.sleep(0.45)

    out = FINDINGS / "draw_categories_all.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Phase 2 完了 → {out}")
    return all_results

# ─── Phase 3: made+draw クロス集計 ───────────────────────────────
def phase3_cross(all_results):
    print("\n" + "=" * 60)
    print("Phase 3: made+draw クロス集計（simple_hand_counters）")
    print("=" * 60)

    cross_results = {}

    # 代表シナリオ3つ × クロス対象ボード
    target_scenarios = ["BTN_BB", "CO_BTN", "BTN_3BP"]
    target_boards = list(CROSS_COMBOS.keys())  # Th9s8d, Qh8d3s, Jd7s5c

    total = len(target_scenarios) * len(set(target_boards))
    done  = 0

    for scen_name in target_scenarios:
        scen = SCENARIOS[scen_name]
        cross_results[scen_name] = {}

        for board in set(target_boards):
            done += 1
            board_type = next((bt for bt, b in BOARDS if b == board), board)
            label = f"{scen_name}/{board}"
            print(f"\n  [{done}/{total}] {label}")

            d = call_api(board, pf=scen["pf"])
            if d is None:
                print("    SKIP"); continue
            time.sleep(0.45)

            shc = extract_simple_hand_counters(d, "IP")
            cross_results[scen_name][board] = {}

            # 注目コンボを表示
            combos_info = CROSS_COMBOS.get(board, {})
            for hand, desc in combos_info.items():
                v = shc.get(hand)
                if v:
                    cross_results[scen_name][board][hand] = {**v, "desc": desc}
                    flag = ""
                    if v["bet_pct"] > 60:  flag = " ← 高頻度ベット"
                    elif v["bet_pct"] < 20: flag = " ← 低頻度"
                    print(f"    {hand:6s}  bet={v['bet_pct']:5.1f}%  eq={v['eq']:4.1f}%  {desc}{flag}")
                else:
                    print(f"    {hand:6s}  (レンジ外)")

    out = FINDINGS / "cross_made_draw.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(cross_results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Phase 3 完了 → {out}")
    return cross_results

# ─── Phase 4: クイックサマリー表示 ──────────────────────────────
def phase4_summary(all_results):
    print("\n" + "=" * 60)
    print("Phase 4: draw_categories サマリー（型4 Th9s8d 横断）")
    print("=" * 60)

    board_type = "型4_ローウェット"
    draw_cats  = ["no_draw", "gutshot", "oesd"]

    print(f"\n  {'シナリオ':15s}", end="")
    for dc in draw_cats:
        print(f"  {dc:12s}", end="")
    print()
    print("  " + "-" * 55)

    for scen_name in SCENARIOS:
        row = all_results.get(scen_name, {}).get(board_type)
        if not row:
            continue
        ip_draw = row["ip_draw"]
        print(f"  {scen_name:15s}", end="")
        for dc in draw_cats:
            v = ip_draw.get(dc)
            if v:
                print(f"  {v['bet_pct']:5.1f}%      ", end="")
            else:
                print(f"   —           ", end="")
        print()

    print("\n  型1 Ks7d2c 横断（no_draw vs twocards_bdfd）")
    print(f"\n  {'シナリオ':15s}  {'no_draw':>10s}  {'2c_bdfd':>10s}  {'差':>8s}")
    print("  " + "-" * 50)
    for scen_name in SCENARIOS:
        row = all_results.get(scen_name, {}).get("型1_ハイドライ")
        if not row:
            continue
        nd = row["ip_draw"].get("no_draw", {}).get("bet_pct")
        bd = row["ip_draw"].get("twocards_bdfd", {}).get("bet_pct")
        diff = (bd - nd) if (nd is not None and bd is not None) else None
        diff_s = f"{diff:+.1f}%" if diff is not None else "—"
        nd_s = f"{nd:.1f}%" if nd is not None else "—"
        bd_s = f"{bd:.1f}%" if bd is not None else "—"
        print(f"  {scen_name:15s}  {nd_s:>10s}  {bd_s:>10s}  {diff_s:>8s}")

# ─── エントリポイント ────────────────────────────────────────────
if __name__ == "__main__":
    if not TOKEN:
        print("❌ TOKEN 未設定")
        print("   TOKEN=eyJ... GWCLIENTID=xxx python3 cash_draw_analysis.py")
        sys.exit(1)

    ok = phase1_verify()
    if not ok:
        print("❌ 検証失敗: 中断します")
        sys.exit(1)

    print("\n✅ 検証成功 → 全収集を開始します\n")
    all_results = phase2_all_draw()
    phase3_cross(all_results)
    phase4_summary(all_results)
    print("\n🏁 全フェーズ完了")
