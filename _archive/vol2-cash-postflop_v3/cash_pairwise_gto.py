#!/usr/bin/env python3
"""
cash_pairwise_gto.py — ペアワイズ網羅性を持つ GTO Wizard 調査

調査軸:
  1. board_type (7型)
  2. hand_role (5類型: V/D/BC/WD/Air)
  3. equity_dynamics (ターンカード別: blank / improving / deteriorating)
  4. position (IP vs OOP)
  5. preflop_action (SRP_aggressor / SRP_caller / 3BP_aggressor / 3BP_caller)

シナリオ:
  SRP_IP   (BTN_BB):  F-F-F-R2.5-F-C       BTN opens, BB calls  → BTN is IP raiser
  SRP_OOP  (SB_BB):   F-F-F-F-R3-C         SB opens, BB calls   → BB is IP caller
  3BP_IP   (BTN_CO):  F-F-R2.5-R9-F-F-C    CO opens, BTN 3bets  → BTN is IP 3bettor
  3BP_OOP  (BTN_BB3): F-F-F-R2.5-F-R9-C    BTN opens, BB 3bets  → BTN is IP caller vs 3bet

使い方:
  TOKEN=eyJ... python3 cash_pairwise_gto.py
  TOKEN=eyJ... PHASE=flop python3 cash_pairwise_gto.py     # フロップのみ
  TOKEN=eyJ... PHASE=turn python3 cash_pairwise_gto.py     # ターンのみ
  TOKEN=eyJ... BOARDS=1 python3 cash_pairwise_gto.py       # 各型1ボードのみ(テスト)
"""

import os, sys, time
from pathlib import Path
from collections import defaultdict
import gto_api
from gto_api import (
    api_get, get_code, is_bet_code, dominant_bet, save_json,
    ip_player, agg_player, agg_sols, CAT5_ORDER,
)

PHASE  = os.environ.get("PHASE", "all")       # "flop", "turn", "all"
BOARDS = int(os.environ.get("BOARDS", "2"))   # boards per type (1-3)

FINDINGS_DIR = Path(__file__).parent / "findings"
FINDINGS_DIR.mkdir(exist_ok=True)

# ─────────────────── シナリオ定義 ───────────────────
SCENARIOS = [
    {
        "id":    "SRP_IP",
        "label": "SRP BTN vs BB (BTN=IP raiser)",
        "pf":    "F-F-F-R2.5-F-C",
        "ip":    "BTN", "oop": "BB",
        "depth": 100,
        "spr":   "~8",
        "preflop_role": "SRP_aggressor",
    },
    {
        "id":    "SRP_OOP",
        "label": "SRP SB vs BB (BB=IP caller vs SB)",
        "pf":    "F-F-F-F-R3-C",
        "ip":    "BB", "oop": "SB",
        "depth": 100,
        "spr":   "~8",
        "preflop_role": "SRP_caller",
    },
    {
        "id":    "3BP_IP",
        "label": "3BP CO vs BTN (BTN=IP 3bettor)",
        "pf":    "F-F-R2.5-R9-F-F-C",
        "ip":    "BTN", "oop": "CO",
        "depth": 100,
        "spr":   "~5",
        "preflop_role": "3BP_aggressor",
    },
    {
        "id":    "3BP_OOP",
        "label": "3BP BTN vs BB (BTN=IP caller vs BB 3bet)",
        "pf":    "F-F-F-R2.5-F-R9-C",
        "ip":    "BTN", "oop": "BB",
        "depth": 100,
        "spr":   "~5",
        "preflop_role": "3BP_caller",
    },
]

# ─────────────────── ボード定義 (3型 × 3枚 = 21ボード) ───────────────────
ALL_BOARDS = [
    # 型1: ハイドライ (K/A/Q高 + レインボー)
    {"type": "型1_ハイドライ", "flop": "Ks7d2c", "desc": "K高・レインボー",
     "turns": [("blank","4c","ブランク"), ("pair2nd","7h","2ndペア"), ("oc","Ah","Aオーバー")]},
    {"type": "型1_ハイドライ", "flop": "As9d3c", "desc": "A高・レインボー",
     "turns": [("blank","4h","ブランク"), ("pair2nd","9h","2ndペア"), ("oc","Kc","Kオーバー")]},
    {"type": "型1_ハイドライ", "flop": "Qs7d3c", "desc": "Q高・レインボー",
     "turns": [("blank","4c","ブランク"), ("pair2nd","7h","2ndペア"), ("oc","Ah","Aオーバー")]},

    # 型2: ハイウェット (Q/K/A高 + 2トーン)
    {"type": "型2_ハイウェット", "flop": "Qh8d3s", "desc": "Q高・2トーン",
     "turns": [("blank","2c","ブランク"), ("fd_complete","7h","FD完成(7h)"), ("pair2nd","8c","2ndペア")]},
    {"type": "型2_ハイウェット", "flop": "Kh9d5s", "desc": "K高・2トーン",
     "turns": [("blank","2c","ブランク"), ("fd_complete","8h","FD完成"), ("pair2nd","9c","2ndペア")]},
    {"type": "型2_ハイウェット", "flop": "Ah8s5d", "desc": "A高・2トーン",
     "turns": [("blank","2c","ブランク"), ("pair2nd","8d","2ndペア"), ("str_complete","7c","ストレート完成")]},

    # 型3: ロードライ (J/9/8中 + レインボー)
    {"type": "型3_ロードライ", "flop": "Jd7s5c", "desc": "J中・レインボー",
     "turns": [("blank","2h","ブランク"), ("oesd_complete","8c","OESD完成(8)"), ("oc","Kh","オーバー")]},
    {"type": "型3_ロードライ", "flop": "9s6d2c", "desc": "9中・レインボー",
     "turns": [("blank","Ah","ブランク(A=OC)"), ("oesd_complete","7h","OESD完成(7)"), ("pair2nd","6s","2ndペア")]},
    {"type": "型3_ロードライ", "flop": "8d5s2c", "desc": "8低・レインボー",
     "turns": [("blank","Kh","ブランク(K=OC)"), ("oesd_complete","6h","OESD完成(6)"), ("pair2nd","5d","2ndペア")]},

    # 型4: ローウェット (連携 + 2トーン)
    {"type": "型4_ローウェット", "flop": "Th9s8d", "desc": "低連携・2トーン",
     "turns": [("blank","2c","ブランク"), ("fd_complete","Js","FD完成(J)"), ("str_pair","7h","ストレート完成(7)")]},
    {"type": "型4_ローウェット", "flop": "9h8d7s", "desc": "9連続・レインボー",
     "turns": [("blank","2c","ブランク"), ("str_complete","6c","ストレート完成(6)"), ("oc","Ah","オーバー(A)")]},
    {"type": "型4_ローウェット", "flop": "Jd9s8h", "desc": "J連携・2トーン",
     "turns": [("blank","2c","ブランク"), ("str_complete","7c","ストレート完成(7)"), ("oc","Ah","オーバー(A)")]},

    # 型5: モノトーン
    {"type": "型5_モノトーン", "flop": "Ah9h5h", "desc": "A高モノトーン",
     "turns": [("offsuit","2c","オフスート"), ("4thflush","8h","フラッシュ4枚"), ("pair2nd","9c","2ndペア")]},
    {"type": "型5_モノトーン", "flop": "Kd7d3d", "desc": "K高モノトーン",
     "turns": [("offsuit","2c","オフスート"), ("4thflush","8d","フラッシュ4枚"), ("pair2nd","7c","2ndペア")]},
    {"type": "型5_モノトーン", "flop": "Qh8h4h", "desc": "Q中モノトーン",
     "turns": [("offsuit","2c","オフスート"), ("4thflush","7h","フラッシュ4枚"), ("pair2nd","8c","2ndペア")]},

    # 型6: ペア高 (AAx/KKx/AAQx等)
    {"type": "型6_ペア高", "flop": "AsAcKd", "desc": "AAKペア",
     "turns": [("blank","2h","ブランク"), ("pair3rd","Kh","3rdカードペア"), ("oc","Qc","Q(OC相当)")]},
    {"type": "型6_ペア高", "flop": "KhKd8c", "desc": "KK8ペア",
     "turns": [("blank","2h","ブランク"), ("pair3rd","8h","3rdカードペア"), ("oc","Ah","A(OC)")]},
    {"type": "型6_ペア高", "flop": "AhAdQs", "desc": "AAQペア",
     "turns": [("blank","2h","ブランク"), ("pair3rd","Qh","3rdカードペア"), ("oc","Kc","K(OC相当)")]},

    # 型7: ペア低 (77x/44x/55x等)
    {"type": "型7_ペア低", "flop": "7s7d2c", "desc": "77低ペア",
     "turns": [("blank","Kh","Kオーバー"), ("pair3rd","2s","3rdカードペア"), ("oc","Ah","Aオーバー")]},
    {"type": "型7_ペア低", "flop": "4s4d9c", "desc": "44中ペア",
     "turns": [("blank","2c","ブランク"), ("pair3rd","9h","3rdカードペア"), ("oc","Ah","Aオーバー")]},
    {"type": "型7_ペア低", "flop": "5h5c2d", "desc": "55低ペア",
     "turns": [("blank","Kh","Kオーバー"), ("pair3rd","2s","3rdカードペア"), ("oc","Ah","Aオーバー")]},
]

# BOARDS 枚数に制限
BOARDS_PER_TYPE = defaultdict(int)
BOARDS_LIST = []
for b in ALL_BOARDS:
    if BOARDS_PER_TYPE[b["type"]] < BOARDS:
        BOARDS_LIST.append(b)
        BOARDS_PER_TYPE[b["type"]] += 1

CAT_ORDER = CAT5_ORDER  # 後方互換エイリアス

def classify_actions(sols):
    """action_solutionsからアクション名→コードのマップを返す"""
    codes = {}
    for a in sols:
        ac = get_code(a)
        if ac == "F": codes["fold"] = ac
        elif ac == "C": codes["call"] = ac
        elif ac == "X": codes["check"] = ac
        elif is_bet_code(ac):
            codes[ac] = ac
    return codes


# ─────────────────── メインロジック ───────────────────
def run_flop_study():
    """フロップ: IP CBet + OOP defense の5類型調査"""
    results = []
    total = len(BOARDS_LIST) * len(SCENARIOS)
    done = 0

    for bconf in BOARDS_LIST:
        for scen in SCENARIOS:
            done += 1
            flop = bconf["flop"]
            pf   = scen["pf"]
            depth = scen["depth"]
            label = f"{bconf['type']} {flop} × {scen['id']}"

            # ── Step 1: OOP checks, IP acts (CBet spot) ──
            sols1 = api_get(flop, "X", pf, depth=depth)
            time.sleep(0.5)
            if not sols1:
                print(f"  SKIP (no data) {label}", file=sys.stderr)
                continue

            action_sols = sols1.get("action_solutions", [])
            cbet_code = dominant_bet(action_sols)
            ip_plr = ip_player(sols1)
            if not ip_plr or not cbet_code:
                print(f"  SKIP (no IP player or bet) {label}", file=sys.stderr)
                continue

            # IP CBet by category
            ip_cbet = agg_player(ip_plr, {"bet": cbet_code, "check": "X"})

            # ── Step 2: After IP CBets, OOP responds ──
            sols2 = api_get(flop, f"X-{cbet_code}", pf, depth=depth)
            time.sleep(0.5)
            oop_defense = None
            cr_code = None
            if sols2:
                action_sols2 = sols2.get("action_solutions", [])
                cr_code = next((get_code(a) for a in action_sols2 if is_bet_code(get_code(a))), None)
                oop_defense = agg_sols(action_sols2)

            entry = {
                "board_type": bconf["type"],
                "flop": flop,
                "desc": bconf["desc"],
                "scenario": scen["id"],
                "preflop_role": scen["preflop_role"],
                "ip": scen["ip"],
                "oop": scen["oop"],
                "spr": scen["spr"],
                "cbet_code": cbet_code,
                "ip_cbet": ip_cbet,
                "cr_code": cr_code,
                "oop_defense": oop_defense,
            }
            results.append(entry)

            # 進捗ログ
            v   = ip_cbet.get("バリュー", {}).get("bet", "N/A")
            bc  = ip_cbet.get("ブラフキャッチャー", {}).get("bet", "N/A")
            air = ip_cbet.get("エアー", {}).get("bet", "N/A")
            print(f"[{done:3d}/{total}] {label}  cbet={cbet_code}  V={v}% BC={bc}% Air={air}%")

    return results


def run_turn_study(flop_results):
    """ターン: 主要ボードで turn card 別の IP CBet 変化を追跡 (equity dynamics)"""
    turn_results = []
    # フロップ調査済みのボードから SRP_IP のみ選ぶ
    srp_boards = {r["flop"]: r for r in flop_results if r["scenario"] == "SRP_IP"}

    total = sum(len(b["turns"]) for b in BOARDS_LIST[:7])  # 1型1ボードのみ
    done = 0
    seen_flops = set()

    for bconf in BOARDS_LIST:
        flop = bconf["flop"]
        if flop in seen_flops: continue
        seen_flops.add(flop)

        flop_data = srp_boards.get(flop)
        if not flop_data: continue
        scen = next(s for s in SCENARIOS if s["id"] == "SRP_IP")  # noqa
        pf   = scen["pf"]
        # XX後 (check-check) のターン
        for t_id, t_card, t_desc in bconf["turns"]:
            done += 1
            board_turn = f"{flop}{t_card}"
            # flop: X-X (両者チェック) → OOP checks turn (X) → IP acts
            sols = api_get(board_turn, "X-X", pf, depth=scen["depth"], turn_actions="X")
            time.sleep(0.5)
            if not sols:
                print(f"  SKIP turn {board_turn}", file=sys.stderr)
                continue

            action_sols = sols.get("action_solutions", [])
            bet_code = dominant_bet(action_sols)
            ip_plr = ip_player(sols)
            if not ip_plr or not bet_code:
                continue

            turn_bet = agg_player(ip_plr, {"bet": bet_code, "check": "X"})

            entry = {
                "board_type": bconf["type"],
                "flop": flop,
                "turn_card": t_card,
                "turn_id": t_id,
                "turn_desc": t_desc,
                "scenario": "SRP_IP",
                "bet_code": bet_code,
                "turn_bet": turn_bet,
            }
            turn_results.append(entry)

            v   = turn_bet.get("V",   {}).get("bet", "N/A")
            d   = turn_bet.get("D",   {}).get("bet", "N/A")
            bc  = turn_bet.get("BC",  {}).get("bet", "N/A")
            air = turn_bet.get("Air", {}).get("bet", "N/A")
            print(f"  TURN [{done}/{total}] {bconf['type']} {board_turn} ({t_desc}): V={v}% D={d}% BC={bc}% Air={air}%")

    return turn_results


def save_results(flop_results, turn_results):
    out = {
        "meta": {
            "scenarios": [s["id"] for s in SCENARIOS],
            "boards_per_type": BOARDS,
            "total_boards": len(BOARDS_LIST),
            "phases": PHASE,
        },
        "flop": flop_results,
        "turn": turn_results,
    }
    path = FINDINGS_DIR / "cash_pairwise_gto.json"
    save_json(path, out)
    print(f"\nSaved: {path}")

    # サマリーテキスト
    _save_summary(flop_results, turn_results)


def _save_summary(flop_results, turn_results):
    lines = ["# Pairwise GTO Wizard 調査結果\n"]

    # ─ フロップ: IP CBet by board_type × scenario ─
    lines.append("## フロップ IP CBet% (5類型)\n")
    for scen in SCENARIOS:
        sid = scen["id"]
        lines.append(f"\n### {sid} ({scen['label']})\n")
        lines.append(f"| ボード型 | ボード | V | D | BC | WD | Air |\n|---|---|---|---|---|---|---|\n")
        for r in flop_results:
            if r["scenario"] != sid: continue
            row = [f"| {r['board_type']} | `{r['flop']}` ({r['desc']})"]
            for cat in CAT5_ORDER:
                v = r["ip_cbet"].get(cat)
                row.append(f" {v['bet']:.0f}%(n={v['n']:.0f})" if v else " N/A")
            lines.append(" |".join(row) + " |\n")

    # ─ フロップ: OOP defense by board_type × scenario ─
    lines.append("\n## フロップ OOP Defense (Fold/Call/Raise%) (5類型)\n")
    for scen in SCENARIOS:
        sid = scen["id"]
        lines.append(f"\n### {sid}\n")
        lines.append("| ボード型 | ボード | 類型 | Fold | Call | Raise |\n|---|---|---|---|---|---|\n")
        for r in flop_results:
            if r["scenario"] != sid or not r["oop_defense"]: continue
            for cat in CAT5_ORDER:
                v = r["oop_defense"].get(cat)
                if not v: continue
                fold = v.get("fold", 0)
                call = v.get("call", 0)
                raise_ = v.get("raise", 0)
                lines.append(f"| {r['board_type']} | `{r['flop']}` | {cat} "
                              f"| {fold:.0f}% | {call:.0f}% | {raise_:.0f}% |\n")

    # ─ ターン: equity dynamics ─
    if turn_results:
        lines.append("\n## ターン Equity Dynamics (SRP_IP, X-X後)\n")
        lines.append("| ボード型 | フロップ | ターンカード | V | D | BC | WD | Air |\n|---|---|---|---|---|---|---|---|\n")
        for r in turn_results:
            row = [f"| {r['board_type']} | `{r['flop']}` | {r['turn_card']} ({r['turn_desc']})"]
            for cat in CAT5_ORDER:
                v = r["turn_bet"].get(cat)
                row.append(f" {v['bet']:.0f}%" if v else " N/A")
            lines.append(" |".join(row) + " |\n")

    path = FINDINGS_DIR / "cash_pairwise_gto_summary.md"
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"Summary: {path}")


# ─────────────────── エントリポイント ───────────────────
if __name__ == "__main__":
    if not gto_api.TOKEN:
        print("ERROR: TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    print(f"Boards: {len(BOARDS_LIST)} ({BOARDS} per type)  Scenarios: {len(SCENARIOS)}  Phase: {PHASE}")

    flop_results = []
    turn_results = []

    if PHASE in ("all", "flop"):
        print("\n=== Phase 1: Flop CBet + OOP Defense ===")
        flop_results = run_flop_study()
        print(f"\nFlop study done: {len(flop_results)} entries")

    if PHASE == "turn":
        # 既存のフロップ結果をファイルから読み込む
        existing = FINDINGS_DIR / "cash_pairwise_gto.json"
        if existing.exists():
            from gto_api import load_json
            saved = load_json(existing, default={})
            flop_results = saved.get("flop", [])
            print(f"Loaded {len(flop_results)} existing flop entries for turn study")

    if PHASE in ("all", "turn") and flop_results:
        print("\n=== Phase 2: Turn Equity Dynamics ===")
        turn_results = run_turn_study(flop_results)
        print(f"Turn study done: {len(turn_results)} entries")

    save_results(flop_results, turn_results)
    print("Done.")
