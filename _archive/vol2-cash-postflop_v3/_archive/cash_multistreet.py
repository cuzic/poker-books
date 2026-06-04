#!/usr/bin/env python3
"""
マルチストリート GTO自動分析スクリプト
フロップ→ターンの連鎖クエリで、IP先手・OOP後手双方の
ハンドカテゴリ別行動を自動収集・集計する

使い方:
  TOKEN=eyJ... GWCLIENTID=xxx python3 cash_multistreet.py
  TOKEN=eyJ... SCENARIO=CO_BB python3 cash_multistreet.py     # CO vs BB SRP
  TOKEN=eyJ... SCENARIO=BTN_3BP python3 cash_multistreet.py   # BTN 3bet pot
  TOKEN=eyJ... TYPE=型1 python3 cash_multistreet.py            # 特定型のみ
  TOKEN=eyJ... TURNS=0 python3 cash_multistreet.py             # ターンクエリをスキップ
"""

import os, sys, json, time, requests
from pathlib import Path
from collections import defaultdict  # noqa: F401

TOKEN      = os.environ.get("TOKEN", "")
GWCLIENTID = os.environ.get("GWCLIENTID", "")
GT         = os.environ.get("GT", "Cash6mGeneral_6mNL25R25")
DEPTH      = float(os.environ.get("DEPTH", "100"))
SCENARIO   = os.environ.get("SCENARIO", "BTN_BB")
TYPE_FILTER = os.environ.get("TYPE", "")          # 特定ボード型のみ実行
SKIP_TURNS = os.environ.get("TURNS", "1") == "0"  # TURNS=0 でターンをスキップ
FINDINGS_DIR = Path(__file__).parent / "findings"
FINDINGS_DIR.mkdir(exist_ok=True)

BASE_URL = "https://api.gtowizard.com/v4/solutions/spot-solution/"

# ─────────────────── プリフロップシナリオ ───────────────────
# preflop_actions は 6-max のアクションを位置順に並べたもの
# 順序: UTG - HJ - CO - BTN - SB - BB
# ポスト先手 = IP_POS (後手に対してCBetを打つ側)
# ポスト後手 = OOP_POS (先手のCBetに応答する側)

SCENARIOS = {
    "BTN_BB": {
        "label": "SRP BTN vs BB",
        "pf":    "F-F-F-R2.5-F-C",   # CO/HJ/UTG fold, BTN open 2.5x, SB fold, BB call
        "ip":    "BTN",               # postflop IP = BTN (acts last)
        "oop":   "BB",                # postflop OOP = BB (acts first)
        "depth": 100,
    },
    "CO_BB": {
        "label": "SRP CO vs BB",
        "pf":    "F-F-R2.5-F-F-C",   # UTG/HJ fold, CO open 2.5x, BTN/SB fold, BB call
        "ip":    "CO",
        "oop":   "BB",
        "depth": 100,
    },
    "HJ_BB": {
        "label": "SRP HJ vs BB",
        "pf":    "F-R2.5-F-F-F-C",   # UTG fold, HJ open 2.5x, CO/BTN/SB fold, BB call
        "ip":    "HJ",
        "oop":   "BB",
        "depth": 100,
    },
    "UTG_BB": {
        "label": "SRP UTG vs BB",
        "pf":    "R2.5-F-F-F-F-C",   # UTG open 2.5x, HJ/CO/BTN/SB fold, BB call
        "ip":    "UTG",
        "oop":   "BB",
        "depth": 100,
    },
    "SB_BB": {
        "label": "SRP SB vs BB",
        "pf":    "F-F-F-F-R3-C",     # UTG/HJ/CO/BTN fold, SB open 3x, BB call
        "ip":    "BB",                # postflop IP = BB (acts last)
        "oop":   "SB",                # postflop OOP = SB (acts first)
        "depth": 100,
    },
    # ─── BBが絡まないマッチアップ（SRPとSB vs BTN）───
    # 6-max: UTG-HJ-CO-BTN-SB-BB 順。ポストフロップはSBから時計回り
    # BTN open、SB call → OOP=SB（先手）、IP=BTN（後手）
    "BTN_SB": {
        "label": "SRP BTN vs SB",
        "pf":    "F-F-F-R2.5-C-F",   # UTG/HJ/CO fold, BTN open 2.5x, SB call, BB fold
        "ip":    "BTN",               # postflop IP = BTN (acts last)
        "oop":   "SB",                # postflop OOP = SB (acts first)
        "depth": 100,
    },
    # HJ open、BTN call → OOP=HJ、IP=BTN（BTNはSB・BBより先に行動）
    "HJ_BTN": {
        "label": "SRP HJ vs BTN (coldcall)",
        "pf":    "F-R2.5-F-C-F-F",   # UTG fold, HJ open 2.5x, CO fold, BTN call, SB/BB fold
        "ip":    "BTN",               # postflop IP = BTN (acts last among 2)
        "oop":   "HJ",                # postflop OOP = HJ (acts first among 2)
        "depth": 100,
    },
    # CO open、BTN call → OOP=CO、IP=BTN
    "CO_BTN": {
        "label": "SRP CO vs BTN (coldcall)",
        "pf":    "F-F-R2.5-C-F-F",   # UTG/HJ fold, CO open 2.5x, BTN call, SB/BB fold
        "ip":    "BTN",               # postflop IP = BTN
        "oop":   "CO",                # postflop OOP = CO
        "depth": 100,
    },
    # UTG open、CO call → OOP=UTG、IP=CO
    "UTG_CO": {
        "label": "SRP UTG vs CO (coldcall)",
        "pf":    "R2.5-F-C-F-F-F",   # UTG open 2.5x, HJ fold, CO call, BTN/SB/BB fold
        "ip":    "CO",
        "oop":   "UTG",
        "depth": 100,
    },
    # BTN open → SB 3bet → BTN call → postflop: OOP=SB、IP=BTN
    "BTN_SB_3BP": {
        "label": "3BP BTN(caller) vs SB(3bettor)",
        "pf":    "F-F-F-R2.5-R9-F-C",  # UTG/HJ/CO fold, BTN open 2.5, SB 3bet 9, BB fold, BTN call
        "ip":    "BTN",
        "oop":   "SB",
        "depth": 100,
    },
    # CO open → BB 3bet → CO call → postflop: OOP=BB、IP=CO
    "CO_BB_3BP": {
        "label": "3BP CO(caller) vs BB(3bettor)",
        "pf":    "F-F-R2.5-F-F-R9-C",  # UTG/HJ fold, CO open 2.5, BTN/SB fold, BB 3bet 9, CO call
        "ip":    "CO",
        "oop":   "BB",
        "depth": 100,
    },
    # CO open → BTN 3bet → CO call → postflop: OOP=CO、IP=BTN
    "CO_BTN_3BP": {
        "label": "3BP CO(caller) vs BTN(3bettor)",
        "pf":    "F-F-R2.5-R9-F-F",  # UTG/HJ fold, CO open 2.5, BTN 3bet 9, SB/BB fold, CO call
        "ip":    "BTN",               # IP = BTN (3bettor, acts last postflop)
        "oop":   "CO",                # OOP = CO (caller, acts first postflop)
        "depth": 100,
    },
    # HJ open → BTN 3bet → HJ call → postflop: OOP=HJ、IP=BTN
    "HJ_BTN_3BP": {
        "label": "3BP HJ(caller) vs BTN(3bettor)",
        "pf":    "F-R2.5-F-R9-F-F",  # UTG fold, HJ open 2.5, CO fold, BTN 3bet 9, SB/BB fold, HJ call
        "ip":    "BTN",
        "oop":   "HJ",
        "depth": 100,
    },
    # 3BPでは BB が3betして BTN がコール → postflop は BB(OOP先手) vs BTN(IP後手)
    # CBetを打つのはOOP側(3bettor=BB)か、またはIP側(caller=BTN)か両方確認する
    "BTN_3BP": {
        "label": "3BP BTN(caller) vs BB(3bettor)",
        "pf":    "F-F-F-R2.5-F-R9-C",  # BTN open 2.5, BB 3bet 9, BTN call
        "ip":    "BTN",                  # postflop IP = BTN (caller, acts last)
        "oop":   "BB",                   # postflop OOP = BB (3bettor, acts first)
        "depth": 100,
    },
}

# ─────────────────── ボード7型 × ターンカードセット ───────────────────
# ターンカードはフロップのカードと重複しない4番目のカードを指定する
# tag: blank=無関係, TA+_2nd=2枚目ペアターン, TA+_3rd=3枚目ペアターン,
#      TA-_OC=オーバーカード, danger=ドロー完成/危険ターン

BOARD_CONFIGS = [
    {
        "type": "型1_ハイドライ",
        "flop": "Ks7d2c",
        "desc": "K高・レインボー",
        "turns": [
            ("blank",    "4c", "ブランク"),
            ("TA+_2nd",  "7h", "2ndカードペア"),
            ("TA+_3rd",  "2s", "3rdカードペア"),
            ("TA-_OC",   "Ah", "オーバーカード(A)"),
        ],
    },
    {
        "type": "型2_ハイウェット",
        "flop": "Qh8d3s",
        "desc": "Q高・2トーン",
        "turns": [
            ("blank",    "5d", "ブランク"),
            ("TA+_2nd",  "8c", "2ndカードペア"),
            ("TA+_3rd",  "3d", "3rdカードペア"),
            ("TA-_OC",   "Ah", "オーバーカード(A)"),
        ],
    },
    {
        "type": "型3_ロードライ",
        "flop": "Jd7s5c",
        "desc": "J中・レインボー",
        "turns": [
            ("blank",    "2c", "ブランク"),
            ("TA+_2nd",  "7h", "2ndカードペア"),
            ("TA+_3rd",  "5h", "3rdカードペア"),
            ("TA-_OC",   "Ah", "オーバーカード(A)"),
        ],
    },
    {
        "type": "型4_ローウェット",
        "flop": "Th9s8d",
        "desc": "低連携・2トーン",
        "turns": [
            ("blank",    "2c", "ブランク"),
            ("TA+_pair", "Th", "フロップ1stカードペア"),  # T pairs: BBのTxも強化
            ("danger",   "6c", "ストレート完成(低)"),
            ("danger",   "7c", "ストレート完成(高)"),
        ],
    },
    {
        "type": "型5_モノトーン",
        "flop": "Ah9h5h",
        "desc": "A高モノトーン",
        "turns": [
            ("blank",    "2c", "ブランク(非ハート)"),
            ("TA+_2nd",  "9d", "2ndカードペア(非ハート)"),
            ("danger",   "4h", "フラッシュ完成(4thハート)"),
            ("TA-_OC",   "Kd", "オーバーカード(非ハート)"),
        ],
    },
    {
        "type": "型6_ペア高",
        "flop": "AsAcKd",
        "desc": "AAKペアボード",
        "turns": [
            ("blank",    "2c", "ブランク"),
            ("TA+_3rd",  "Ks", "3rdカードペア(K)"),
            ("TA-_OC",   "Qd", "準オーバーカード(Q)"),
            ("danger",   "Jd", "Jストレートドロー絡み"),
        ],
    },
    {
        "type": "型7_ペア低",
        "flop": "7s7d2c",
        "desc": "77低ペアボード",
        "turns": [
            ("blank",    "3c", "ブランク"),
            ("TA+_3rd",  "2h", "3rdカードペア(2)"),
            ("TA-_OC",   "Ah", "オーバーカード(A)"),
            ("TA-_OC2",  "Kh", "オーバーカード(K)"),
        ],
    },
]

HC_HS = {
    "straight_flush":97,"quads":93,"fullhouse":89,"flush":83,"straight":80,
    "set":85,"two_pair":77,"trips":74,"overpair":70,"top_pair":60,
    "underpair":42,"second_pair":43,"third_pair":35,"low_pair":30,
    "ace_high":24,"king_high":21,"queen_high":19,"jack_high":17,
    "ten_high":15,"no_made_hand":12,
}

def hs_bucket(hs):
    if hs >= 65: return "V"
    if hs >= 35: return "M"
    return "A"

def make_headers():
    h = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {TOKEN}",
        "origin": "https://app.gtowizard.com",
        "referer": "https://app.gtowizard.com/",
    }
    if GWCLIENTID:
        h["gwclientid"] = GWCLIENTID
    return h

def call_api(board, flop_actions="", turn_actions="", river_actions="", pf=None, depth=100):
    if pf is None:
        pf = SCENARIOS[SCENARIO]["pf"]
    params = {
        "gametype": GT, "depth": str(depth), "stacks": "",
        "preflop_actions": pf,
        "flop_actions": flop_actions,
        "turn_actions": turn_actions,
        "river_actions": river_actions,
        "board": board,
    }
    r = requests.get(BASE_URL, params=params, headers=make_headers(), timeout=30)
    if r.status_code == 200:
        return r.json()
    print(f"  [HTTP {r.status_code}] flop={flop_actions!r} turn={turn_actions!r} board={board}")
    return None

def get_player(data, pos):
    for p in data.get("players_info", []):
        if isinstance(p.get("player"), dict) and p["player"].get("position") == pos:
            return p
    return None

def classify_actions(sols):
    """アクションをキー別に分類してコードを返す"""
    codes = {}
    for s in sols:
        a = s["action"]; t = a["type"]; c = a["code"]
        bp = float(a.get("betsize_by_pot") or 0)
        if   t == "CHECK": codes["check"] = c
        elif t == "FOLD":  codes["fold"]  = c
        elif t == "CALL":  codes["call"]  = c
        elif t == "RAISE":
            if   bp < 0.25: codes["bet20"]   = c
            elif bp < 0.40: codes["bet33"]   = c
            elif bp < 0.65: codes["bet50"]   = c
            elif bp < 0.90: codes["bet75"]   = c
            elif bp < 1.20: codes["bet100"]  = c
            else:           codes["betover"] = c
    return codes

def dominant_bet_code(codes):
    """最も頻度が高そうなベットコードを返す（優先順位: 33>50>75>100>over>20）"""
    for key in ["bet33","bet50","bet75","bet100","betover","bet20"]:
        if key in codes:
            return codes[key]
    return None

def calc_hc_action_rates(sols, player, codes):
    """hand_category ごとのアクション率を計算して返す"""
    range_hc = {h["name"]: h["total_combos"] for h in player["hand_categories"]}
    action_hc = {s["action"]["code"]: {h["name"]: h["total_combos"]
                 for h in (s["hand_categories"] or [])} for s in sols}
    rows = []
    for hc, total in sorted(range_hc.items(), key=lambda x: -HC_HS.get(x[0], 50)):
        if total < 0.3:
            continue
        hs  = HC_HS.get(hc, 0)
        bkt = hs_bucket(hs)
        act = {}
        for code_key, code_val in codes.items():
            n = action_hc.get(code_val, {}).get(hc, 0)
            act[code_key] = n / total if total > 0 else 0
        rows.append({"hc": hc, "total": round(total,1), "hs": hs, "bkt": bkt, **act})
    return rows

def bkt_avg(rows, bkt, key):
    vals = [r[key] for r in rows if r["bkt"] == bkt and key in r]
    return sum(vals) / len(vals) if vals else None

def bucket_summary(rows, code_keys):
    """バケット(V/M/A) × アクション率の平均サマリー"""
    result = {}
    for bkt in ("V","M","A"):
        result[bkt] = {k: bkt_avg(rows, bkt, k) for k in code_keys}
    return result

# ─────────────────── フロップ分析 ───────────────────

def flop_offense(board, pf, ip_pos, depth):
    """IP先手: CBet判断（BBチェック後のIP行動）"""
    data = call_api(board, flop_actions="X", pf=pf, depth=depth)
    if not data:
        return None
    ip   = get_player(data, ip_pos)
    sols = data.get("action_solutions", [])
    if not ip or not sols:
        return None
    codes = classify_actions(sols)
    rows  = calc_hc_action_rates(sols, ip, codes)
    return {"codes": codes, "rows": rows, "dominant_bet": dominant_bet_code(codes)}

def flop_defense(board, pf, bet_code, oop_pos, depth):
    """OOP後手: Fold/Call/Raiseの選択（IP CBet後のOOP行動）"""
    data = call_api(board, flop_actions=f"X-{bet_code}", pf=pf, depth=depth)
    if not data:
        return None
    oop  = get_player(data, oop_pos)
    sols = data.get("action_solutions", [])
    if not oop or not sols:
        return None
    codes = classify_actions(sols)
    rows  = calc_hc_action_rates(sols, oop, codes)
    return {"codes": codes, "rows": rows}

# ─────────────────── ターン分析 ───────────────────

def turn_ip_after_cbet_call(flop, turn_card, bet_code, pf, ip_pos, depth):
    """IP: ターン先手（フロップCBet-コール後、OOPがターンチェックした状態でIPが判断）"""
    board = flop + turn_card
    data  = call_api(board,
                     flop_actions=f"X-{bet_code}-C",
                     turn_actions="X",
                     pf=pf, depth=depth)
    if not data:
        return None
    ip   = get_player(data, ip_pos)
    sols = data.get("action_solutions", [])
    if not ip or not sols:
        return None
    codes = classify_actions(sols)
    rows  = calc_hc_action_rates(sols, ip, codes)
    return {"codes": codes, "rows": rows, "dominant_bet": dominant_bet_code(codes)}

def turn_oop_lead(flop, turn_card, bet_code, pf, oop_pos, depth):
    """OOP: ターンリード判断（フロップCBet-コール後、OOPが先手でターン行動を決める）"""
    board = flop + turn_card
    data  = call_api(board,
                     flop_actions=f"X-{bet_code}-C",
                     turn_actions="",
                     pf=pf, depth=depth)
    if not data:
        return None
    oop  = get_player(data, oop_pos)
    sols = data.get("action_solutions", [])
    if not oop or not sols:
        return None
    codes = classify_actions(sols)
    rows  = calc_hc_action_rates(sols, oop, codes)
    return {"codes": codes, "rows": rows}

# ─────────────────── 表示ヘルパー ───────────────────

def print_hc_table(rows, header=""):
    keys = [k for k in rows[0] if k not in ("hc","total","hs","bkt")] if rows else []
    if header:
        print(f"\n  {header}")
    col_hdr = f"  {'カテゴリ':22s} {'コンボ':>6} {'HS':>3} {'帯':>1}"
    for k in keys:
        col_hdr += f" {k:>7}"
    print(col_hdr)
    print(f"  {'-'*65}")
    for row in rows:
        line = f"  {row['hc']:22s} {row['total']:6.1f} {row['hs']:3d} {row['bkt']:>1}"
        for k in keys:
            v = row.get(k)
            if v is not None:
                line += f" {v*100:6.0f}%"
            else:
                line += f"  {'—':>6}"
        print(line)

def print_bucket_line(label, summary, code_keys):
    parts = []
    for bkt, bkt_name in [("V","バリュー"),("M","マージナル"),("A","エアー")]:
        subs = []
        for k in code_keys:
            v = summary[bkt].get(k)
            if v is not None and v >= 0.04:
                subs.append(f"{k}:{v*100:.0f}%")
        parts.append(f"[{bkt_name}] {' '.join(subs) if subs else 'N/A'}")
    print(f"  {label}: " + " | ".join(parts))

# ─────────────────── メイン ───────────────────

def main():
    if not TOKEN:
        print("❌ TOKEN 未設定")
        sys.exit(1)

    scen = SCENARIOS.get(SCENARIO)
    if not scen:
        print(f"❌ 未知のシナリオ: {SCENARIO}. 選択肢: {list(SCENARIOS)}")
        sys.exit(1)

    pf    = scen["pf"]
    ip    = scen["ip"]
    oop   = scen["oop"]
    depth = scen.get("depth", 100)

    print(f"シナリオ: {scen['label']}  (IP={ip}, OOP={oop}, depth={depth}BB)")
    print(f"gametype: {GT}")

    # 認証確認
    test = call_api("Ks7d2c", flop_actions="X", pf=pf, depth=depth)
    if test is None:
        print("❌ 認証失敗"); sys.exit(1)
    print("✅ 認証OK\n")

    all_results = []

    configs = [c for c in BOARD_CONFIGS if not TYPE_FILTER or c["type"] == TYPE_FILTER]

    for cfg in configs:
        flop = cfg["flop"]
        print(f"\n{'='*70}")
        print(f"【{cfg['type']}】 {flop}  ({cfg['desc']})")

        # ─── フロップ先手（IP CBet）───
        print(f"\n  ▼ フロップ IP先手 ({ip} CBet)")
        f_off = flop_offense(flop, pf, ip, depth)
        if not f_off:
            print("  取得失敗"); continue
        time.sleep(0.6)

        bet_code = f_off["dominant_bet"]
        print(f"  利用コード: {f_off['codes']}  主要bet={bet_code}")
        print_hc_table(f_off["rows"], "hand_category別 CBet率")
        off_summary = bucket_summary(f_off["rows"],
                                     [k for k in f_off["codes"] if k != "check"] + ["check"])
        print_bucket_line("バケット別CBet", off_summary,
                          [k for k in f_off["codes"] if k != "check"])

        # ─── フロップ後手（OOP Defense）───
        def_summary: dict = {}
        if bet_code:
            print(f"\n  ▼ フロップ OOP後手 ({oop} vs {ip} {bet_code})")
            f_def = flop_defense(flop, pf, bet_code, oop, depth)
            time.sleep(0.6)
            if f_def:
                print_hc_table(f_def["rows"], "hand_category別 Fold/Call/Raise率")
                def_keys = [k for k in f_def["codes"] if k in ("fold","call","raise")]
                def_summary = bucket_summary(f_def["rows"], def_keys)
                print_bucket_line("バケット別守備", def_summary, def_keys)
            else:
                f_def = None
                print("  取得失敗")
        else:
            f_def = None

        # ─── ターン分析 ───
        turn_results = []
        if not SKIP_TURNS and bet_code:
            print(f"\n  ▼ ターン分析 (フロップ X-{bet_code}-C 後)")
            for turn_tag, turn_card, turn_desc in cfg["turns"]:
                board4 = flop + turn_card
                print(f"\n  ── ターン [{turn_tag}] {turn_card} ({turn_desc}): board={board4}")

                # IP ターンバレル（OOPチェック後）
                t_ip = turn_ip_after_cbet_call(flop, turn_card, bet_code, pf, ip, depth)
                time.sleep(0.6)
                ip_barrel: dict | None = None
                if t_ip:
                    t_bet_key = [k for k in t_ip["codes"] if k != "check"]
                    t_bkt = bucket_summary(t_ip["rows"], t_bet_key + ["check"])
                    ip_barrel = {}
                    for bkt in ("V","M","A"):
                        ip_barrel[bkt] = sum(t_bkt[bkt].get(k, 0) or 0 for k in t_bet_key)
                    rate_str = " | ".join(f"{b}={v*100:.0f}%" for b, v in ip_barrel.items())
                    print(f"    IP バレル率: {rate_str}")
                else:
                    print(f"    IP ターン取得失敗")

                # OOP ターンリード（先手）
                t_oop = turn_oop_lead(flop, turn_card, bet_code, pf, oop, depth)
                time.sleep(0.6)
                oop_lead: dict | None = None
                if t_oop:
                    t_lead_key = [k for k in t_oop["codes"] if k not in ("check","fold")]
                    if t_lead_key:
                        t_oop_bkt = bucket_summary(t_oop["rows"], t_lead_key + ["check"])
                        oop_lead = {}
                        for bkt in ("V","M","A"):
                            oop_lead[bkt] = sum(t_oop_bkt[bkt].get(k, 0) or 0 for k in t_lead_key)
                        rate_str = " | ".join(f"{b}={v*100:.0f}%" for b, v in oop_lead.items())
                        print(f"    OOP リード率: {rate_str}")
                    else:
                        print(f"    OOP リード: チェックのみ（ベット不可）")
                else:
                    print(f"    OOP ターン取得失敗")

                turn_results.append({
                    "tag": turn_tag, "card": turn_card, "desc": turn_desc,
                    "ip_barrel": ip_barrel,
                    "oop_lead":  oop_lead,
                })

        # ─── ターンサマリー（横断比較）───
        if turn_results:
            print(f"\n  ■ ターンカード比較サマリー（フロップ {flop}）")
            print(f"  {'ターン':10s} {'タグ':12s} | {'IP V':>6} {'IP M':>6} {'IP A':>6} | {'OOP V':>6} {'OOP M':>6} {'OOP A':>6}")
            print(f"  {'-'*72}")
            for tr in turn_results:
                ip_b  = tr["ip_barrel"]  or {}
                oop_l = tr["oop_lead"]   or {}
                def fmt(d, k): return f"{d[k]*100:.0f}%" if d.get(k) is not None else "  —  "
                line = (f"  {tr['card']:5s}({tr['tag'][:8]:8s}) | "
                        f"{fmt(ip_b,'V'):>6} {fmt(ip_b,'M'):>6} {fmt(ip_b,'A'):>6} | "
                        f"{fmt(oop_l,'V'):>6} {fmt(oop_l,'M'):>6} {fmt(oop_l,'A'):>6}")
                print(line)

        all_results.append({
            "type": cfg["type"], "flop": flop, "desc": cfg["desc"],
            "flop_offense": {
                "codes": f_off["codes"],
                "bucket_summary": {
                    bkt: {k: round(v*100,1) for k,v in vals.items() if v is not None}
                    for bkt, vals in off_summary.items()
                },
            },
            "flop_defense": {
                "codes": f_def["codes"] if f_def else {},
                "bucket_summary": {
                    bkt: {k: round(v*100,1) for k,v in vals.items() if v is not None}
                    for bkt, vals in def_summary.items()
                } if f_def else {},
            } if f_def else None,
            "turns": turn_results,
        })
        time.sleep(0.4)

    # ─────────── 全体サマリー ───────────
    print(f"\n\n{'='*70}")
    print(f"★ 全体サマリー: フロップCBet率（バケット別）")
    print(f"  {'型':20s} | {'V CBet%':>8} {'M CBet%':>8} {'A CBet%':>8}")
    print(f"  {'-'*55}")
    for r in all_results:
        bs = r["flop_offense"]["bucket_summary"]
        def cbet(bkt):
            vals = bs.get(bkt,{})
            bets = sum(v for k,v in vals.items() if k not in ("check",))
            return f"{bets:.0f}%"
        print(f"  {r['type']:20s} | {cbet('V'):>8} {cbet('M'):>8} {cbet('A'):>8}")

    print(f"\n★ 全体サマリー: フロップ後手 Fold率（バケット別）")
    print(f"  {'型':20s} | {'V Fold%':>8} {'M Fold%':>8} {'A Fold%':>8}")
    print(f"  {'-'*55}")
    for r in all_results:
        if not r["flop_defense"]:
            continue
        bs = r["flop_defense"]["bucket_summary"]
        def fold(bkt): return f"{bs.get(bkt,{}).get('fold',0):.0f}%"
        print(f"  {r['type']:20s} | {fold('V'):>8} {fold('M'):>8} {fold('A'):>8}")

    if any(r["turns"] for r in all_results):
        print(f"\n★ ターンバレル率サマリー（IP バリューバケット）")
        print(f"  {'型':15s}  {'ターン':8s} {'タグ':12s}  V%   M%   A%")
        print(f"  {'-'*60}")
        for r in all_results:
            for tr in r["turns"]:
                ib = tr["ip_barrel"] or {}
                fv = f"{ib.get('V',0)*100:.0f}%" if "V" in ib else "—"
                fm = f"{ib.get('M',0)*100:.0f}%" if "M" in ib else "—"
                fa = f"{ib.get('A',0)*100:.0f}%" if "A" in ib else "—"
                print(f"  {r['type']:15s}  {tr['card']:5s}   {tr['tag']:12s}  {fv:>4} {fm:>4} {fa:>4}")

    # JSON保存
    out = FINDINGS_DIR / f"multistreet_{SCENARIO}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"scenario": scen["label"], "results": all_results},
                  f, ensure_ascii=False, indent=2)
    print(f"\n✅ 完了 → {out}")


if __name__ == "__main__":
    main()
