#!/usr/bin/env python3
"""
cash_donk_float.py — OOPドンク＆IPフロート GTO分析

既存の cash_multistreet.py が収集していない OOP先打ちラインを収集：
  1. OOP ドンクベット: フロップ先手OOPがベット（donk bet）
  2. IP フロート: OOPドンクにIPコール後、OOPがターンチェック→IPがベット
  3. OOP ターン継続: ドンクコール後のOOPターンリード（ダブルバレル or プローブ）

IPがフロップをチェックバックする代わりに、OOPが自発的にフロップベットする
シチュエーション（SB vs BBなど、OOPが積極的なケース）を調べる。

使い方:
  TOKEN=eyJ... python3 cash_donk_float.py
  TOKEN=eyJ... SCENARIO=SB_BB python3 cash_donk_float.py
  TOKEN=eyJ... TYPE=型3 python3 cash_donk_float.py
"""

import os, sys, json, time, requests
from pathlib import Path

TOKEN       = os.environ.get("TOKEN", "")
GWCLIENTID  = os.environ.get("GWCLIENTID", "")
GT          = os.environ.get("GT", "Cash6mGeneral_6mNL25R25")
SCENARIO    = os.environ.get("SCENARIO", "BTN_BB")
TYPE_FILTER = os.environ.get("TYPE", "")

FINDINGS_DIR = Path(__file__).parent / "findings"
FINDINGS_DIR.mkdir(exist_ok=True)

BASE_URL = "https://api.gtowizard.com/v4/solutions/spot-solution/"

# ─────────────────── プリフロップシナリオ ───────────────────
SCENARIOS = {
    "BTN_BB": {
        "label": "SRP BTN vs BB",
        "pf":    "F-F-F-R2.5-F-C",
        "ip":    "BTN",
        "oop":   "BB",
        "depth": 100,
    },
    "SB_BB": {
        "label": "SRP SB vs BB",
        "pf":    "F-F-F-F-R3-C",
        "ip":    "BB",   # postflop IP = BB
        "oop":   "SB",
        "depth": 100,
    },
    "CO_BB": {
        "label": "SRP CO vs BB",
        "pf":    "F-F-R2.5-F-F-C",
        "ip":    "CO",
        "oop":   "BB",
        "depth": 100,
    },
    "BTN_SB": {
        "label": "SRP BTN vs SB",
        "pf":    "F-F-F-R2.5-C-F",
        "ip":    "BTN",
        "oop":   "SB",
        "depth": 100,
    },
}

# ─────────────────── ボード7型 × ターンカード ───────────────────
BOARD_CONFIGS = [
    {
        "type":  "型1_ハイドライ",
        "flop":  "Ks7d2c",
        "desc":  "K高・レインボー",
        "turns": [
            ("blank",   "4c", "ブランク"),
            ("TA+_2nd", "7h", "2ndペア"),
            ("TA-_OC",  "Ah", "OC(A)"),
        ],
    },
    {
        "type":  "型2_ハイウェット",
        "flop":  "Qh8d3s",
        "desc":  "Q高・2トーン",
        "turns": [
            ("blank",   "5d", "ブランク"),
            ("TA+_2nd", "8c", "2ndペア"),
            ("TA-_OC",  "Ah", "OC(A)"),
        ],
    },
    {
        "type":  "型3_ロードライ",
        "flop":  "Jd7s5c",
        "desc":  "J中・レインボー",
        "turns": [
            ("blank",   "2c", "ブランク"),
            ("TA+_2nd", "7h", "2ndペア"),
            ("TA-_OC",  "Ah", "OC(A)"),
        ],
    },
    {
        "type":  "型4_ローウェット",
        "flop":  "Th9s8d",
        "desc":  "低連携・2トーン",
        "turns": [
            ("blank",  "2c", "ブランク"),
            ("danger", "6c", "SC(低)"),
        ],
    },
    {
        "type":  "型5_モノトーン",
        "flop":  "Ah9h5h",
        "desc":  "A高モノトーン",
        "turns": [
            ("blank",  "2c", "ブランク(非ハート)"),
            ("danger", "4h", "FC(4thハート)"),
        ],
    },
    {
        "type":  "型6_ペア高",
        "flop":  "AsAcKd",
        "desc":  "AAKペアボード",
        "turns": [
            ("blank",   "2c", "ブランク"),
            ("TA+_3rd", "Ks", "3rdペア(K)"),
        ],
    },
    {
        "type":  "型7_ペア低",
        "flop":  "7s7d2c",
        "desc":  "77低ペアボード",
        "turns": [
            ("blank",   "3c", "ブランク"),
            ("TA-_OC",  "Ah", "OC(A)"),
        ],
    },
]

HC_HS = {
    "straight_flush": 97, "quads": 93, "fullhouse": 89, "flush": 83, "straight": 80,
    "set": 85, "two_pair": 77, "trips": 74, "overpair": 70,
    "top_pair": 60,                               # ブラフキャッチャー/RIO 上位
    "underpair": 42, "second_pair": 43,           # ブラフキャッチャー/RIO 下位
    "third_pair": 35, "low_pair": 30,
    "ace_high": 24, "king_high": 21, "queen_high": 19, "jack_high": 17,
    "ten_high": 15, "no_made_hand": 12,           # エアー + セミブラフ(FD/OESD)混在
}

# HC_SORT: 表示順序のためのソートキーのみ（絶対的な強さの尺度ではない）
HC_SORT = HC_HS

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

def call_api(board, flop_actions="", turn_actions="", pf=None, depth=100):
    params = {
        "gametype": GT, "depth": str(depth), "stacks": "",
        "preflop_actions": pf or SCENARIOS[SCENARIO]["pf"],
        "flop_actions": flop_actions,
        "turn_actions": turn_actions,
        "river_actions": "",
        "board": board,
    }
    for attempt in range(4):
        r = requests.get(BASE_URL, params=params, headers=make_headers(), timeout=30)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            wait = 10 * (attempt + 1)
            print(f"  [HTTP 429] board={board} flop={flop_actions!r} turn={turn_actions!r} → {wait}s 待機中...")
            time.sleep(wait)
            continue
        print(f"  [HTTP {r.status_code}] board={board} flop={flop_actions!r} turn={turn_actions!r}")
        return None
    print(f"  [429 最大リトライ超過] board={board}")
    return None

def get_player(data, pos):
    for p in data.get("players_info", []):
        if isinstance(p.get("player"), dict) and p["player"].get("position") == pos:
            return p
    return None

def classify_actions(sols):
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
    for key in ["bet33", "bet50", "bet75", "bet100", "betover", "bet20"]:
        if key in codes:
            return codes[key]
    return None

def calc_hc_action_rates(sols, player, codes):
    """hand_category 別行動率 + レンジシェア(%)を返す。"""
    range_hc  = {h["name"]: h["total_combos"] for h in player["hand_categories"]}
    action_hc = {
        s["action"]["code"]: {h["name"]: h["total_combos"] for h in (s["hand_categories"] or [])}
        for s in sols
    }
    total_range = sum(v for v in range_hc.values() if v >= 0.3)
    rows = []
    for hc, total in sorted(range_hc.items(), key=lambda x: -HC_SORT.get(x[0], 50)):
        if total < 0.3:
            continue
        share = round(total / total_range * 100, 1) if total_range > 0 else 0.0
        act   = {ck: action_hc.get(cv, {}).get(hc, 0) / total if total > 0 else 0
                 for ck, cv in codes.items()}
        rows.append({"hc": hc, "total": round(total, 1), "share": share, **act})
    return rows

def weighted_bet_rate(rows, bet_keys):
    """コンボ加重平均ベット率。ベット選択肢なしなら None。"""
    if not bet_keys or not rows:
        return None
    total_combos = sum(r["total"] for r in rows)
    if total_combos == 0:
        return None
    return sum(r["total"] * sum(r.get(k, 0) or 0 for k in bet_keys) for r in rows) / total_combos

def extract_bet_rate(sols, player, codes):
    """コンボ加重ベット率 (0-1) と rows を返す。ベットなし → (rows, None)。"""
    if not player or not sols:
        return None, None
    rows     = calc_hc_action_rates(sols, player, codes)
    bet_keys = [k for k in codes if k not in ("check", "fold")]
    return rows, weighted_bet_rate(rows, bet_keys)

def print_hc_table(rows, header=""):
    """hand_category 別行動率テーブル表示。レンジシェア列付き。"""
    if not rows:
        return
    keys = [k for k in rows[0] if k not in ("hc", "total", "share")]
    if header:
        print(f"\n  {header}")
    col_hdr = f"  {'カテゴリ':22s} {'コンボ':>6} {'シェア':>6}"
    for k in keys:
        col_hdr += f" {k:>7}"
    print(col_hdr)
    print(f"  {'-'*72}")
    for row in rows:
        line = f"  {row['hc']:22s} {row['total']:6.1f} {row['share']:5.1f}%"
        for k in keys:
            v = row.get(k)
            line += f" {v*100:6.0f}%" if v is not None else f"  {'—':>6}"
        print(line)


def main():
    if not TOKEN:
        print("❌ TOKEN 未設定"); sys.exit(1)

    scen = SCENARIOS.get(SCENARIO)
    if not scen:
        print(f"❌ 未知シナリオ: {SCENARIO}. 選択肢: {list(SCENARIOS)}"); sys.exit(1)

    pf, ip, oop, depth = scen["pf"], scen["ip"], scen["oop"], scen.get("depth", 100)
    print(f"シナリオ: {scen['label']}  (IP={ip}, OOP={oop}, depth={depth}BB)")
    print(f"分析: OOPドンク → IPフロート（コール後ターンベット）")
    print(f"gametype: {GT}\n")

    # 認証確認
    test = call_api("Ks7d2c", flop_actions="", pf=pf, depth=depth)
    if test is None:
        print("❌ 認証失敗"); sys.exit(1)
    print("✅ 認証OK\n")

    all_results = []
    configs = [c for c in BOARD_CONFIGS if not TYPE_FILTER or c["type"] == TYPE_FILTER]

    for cfg in configs:
        flop = cfg["flop"]
        print(f"\n{'='*70}")
        print(f"【{cfg['type']}】 {flop}  ({cfg['desc']})")

        # ── ステップ1: フロップOOPドンク（先手行動を取得） ──
        donk_data = call_api(flop, flop_actions="", pf=pf, depth=depth)
        time.sleep(4.0)
        if not donk_data:
            print("  ドンクデータ取得失敗")
            all_results.append({"type": cfg["type"], "flop": flop, "desc": cfg["desc"],
                                 "donk_bet_code": None, "turns": []})
            continue

        oop_player   = get_player(donk_data, oop)
        donk_sols    = donk_data.get("action_solutions", [])
        if not oop_player or not donk_sols:
            print(f"  OOPプレイヤーデータなし (pos={oop})")
            all_results.append({"type": cfg["type"], "flop": flop, "desc": cfg["desc"],
                                 "donk_bet_code": None, "turns": []})
            continue

        donk_codes   = classify_actions(donk_sols)
        donk_code    = dominant_bet_code(donk_codes)
        donk_rows, donk_rate = extract_bet_rate(donk_sols, oop_player, donk_codes)
        print(f"  OOP ドンクコード: {donk_codes}  主要bet={donk_code}")
        if donk_rate is not None:
            print(f"  OOP ドンク率（総合）: {donk_rate*100:.0f}%")
            print_hc_table(donk_rows, "hand_category別 ドンク率（シェア付き）")

        if not donk_code:
            print("  ドンクベット不可（チェックのみ）")
            all_results.append({"type": cfg["type"], "flop": flop, "desc": cfg["desc"],
                                 "donk_bet_code": None, "donk_rate_pct": None, "turns": []})
            continue

        turn_results = []
        for turn_tag, turn_card, turn_desc in cfg["turns"]:
            board4 = flop + turn_card
            print(f"\n  ── [{turn_tag}] {turn_card} ({turn_desc}): board={board4}")

            # ── ステップ2: IPフロート（ドンクコール後OOPチェック→IP先手） ──
            float_data = call_api(board4, flop_actions=f"{donk_code}-C",
                                  turn_actions="X", pf=pf, depth=depth)
            time.sleep(4.0)
            ip_float: float | None = None
            float_rows = None
            fcodes: dict = {}
            if float_data:
                ip_p   = get_player(float_data, ip)
                fsols  = float_data.get("action_solutions", [])
                fcodes = classify_actions(fsols) if fsols else {}
                float_rows, ip_float = extract_bet_rate(fsols, ip_p, fcodes)
                if ip_float is not None:
                    print(f"    IP フロート率（総合）: {ip_float*100:.0f}%")
                    print_hc_table(float_rows, "hand_category別 フロート率（シェア付き）")
                else:
                    print(f"    IP フロート: チェックのみ")
            else:
                print(f"    IP フロートデータ取得失敗")

            # ── ステップ3: OOPターン継続（ドンクコール後のOOP先手） ──
            oop_turn_data = call_api(board4, flop_actions=f"{donk_code}-C",
                                     turn_actions="", pf=pf, depth=depth)
            time.sleep(4.0)
            oop_turn: float | None = None
            if oop_turn_data:
                oop_p  = get_player(oop_turn_data, oop)
                osols  = oop_turn_data.get("action_solutions", [])
                ocodes = classify_actions(osols) if osols else {}
                _, oop_turn = extract_bet_rate(osols, oop_p, ocodes)
                if oop_turn is not None:
                    print(f"    OOP ターン継続率（総合）: {oop_turn*100:.0f}%")
                else:
                    print(f"    OOP ターン継続: チェックのみ")
            else:
                print(f"    OOPターン継続データ取得失敗")

            def rows_to_store(rows, codes_dict):
                if not rows:
                    return []
                bet_keys = [k for k in codes_dict if k not in ("check", "fold")]
                return [
                    {k: (round(v * 100, 1) if isinstance(v, float) else v)
                     for k, v in row.items()
                     if k in ("hc", "total", "share") or k in bet_keys or k == "check"}
                    for row in rows
                ]

            turn_results.append({
                "tag":  turn_tag, "card": turn_card, "desc": turn_desc,
                "ip_float_pct":      round(ip_float * 100, 1)  if ip_float  is not None else None,
                "oop_turn_cont_pct": round(oop_turn * 100, 1)  if oop_turn  is not None else None,
                "ip_float_by_cat":   rows_to_store(float_rows, fcodes if float_data else {}),
            })
            time.sleep(2.0)

        # ─── ターンサマリー ───
        if turn_results:
            print(f"\n  ■ {cfg['type']} ターン比較（コンボ加重総合ベット率）")
            print(f"  {'ターン':5s}({'タグ':8s}) | {'IP フロート':>12} | {'OOP 継続':>10}")
            print(f"  {'-'*48}")
            for tr in turn_results:
                fl = tr["ip_float_pct"]
                ob = tr["oop_turn_cont_pct"]
                print(f"  {tr['card']:5s}({tr['tag'][:8]:8s}) | "
                      f"{'{}%'.format(round(fl)) if fl is not None else '—':>12} | "
                      f"{'{}%'.format(round(ob)) if ob is not None else '—':>10}")

        all_results.append({
            "type":           cfg["type"],
            "flop":           flop,
            "desc":           cfg["desc"],
            "donk_bet_code":  donk_code,
            "donk_rate_pct":  round(donk_rate * 100, 1) if donk_rate is not None else None,
            "turns":          turn_results,
        })
        time.sleep(2.0)

    # ─── 全体サマリー ───
    print(f"\n\n{'='*70}")
    print(f"★ 全体サマリー: OOP ドンク率（コンボ加重総合）")
    print(f"  {'型':20s} | {'OOP donk%':>10}")
    print(f"  {'-'*35}")
    for r in all_results:
        dr = r.get("donk_rate_pct")
        print(f"  {r['type']:20s} | {'{}%'.format(round(dr)) if dr is not None else '—':>10}")

    # JSON 保存
    out = FINDINGS_DIR / f"donk_float_{SCENARIO}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"scenario": scen["label"], "results": all_results},
                  f, ensure_ascii=False, indent=2)
    print(f"\n✅ 完了 → {out}")


if __name__ == "__main__":
    main()
