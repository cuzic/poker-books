#!/usr/bin/env python3
"""
cash_check_raise.py — チェックレイズ攻防分析

収集データ:
  フロップCR:
    1. OOPのフロップCR頻度: hand_category別CR率（CBetに対して）
    2. IPのCR対応: hand_category別フォールド/コール/3ベット率
  ターンCR:
    3. OOPのターンCR: CBet-call後、IPバレルに対するCR頻度
    4. IPのターンCR対応

使い方:
  TOKEN=eyJ... python3 cash_check_raise.py
  TOKEN=eyJ... STREET=flop python3 cash_check_raise.py   # フロップのみ
  TOKEN=eyJ... STREET=turn python3 cash_check_raise.py   # ターンのみ
  TOKEN=eyJ... TYPE=型1 python3 cash_check_raise.py      # 特定型のみ
"""

import os, sys, json, time, requests
from pathlib import Path

TOKEN          = os.environ.get("TOKEN", "")
GWCLIENTID     = os.environ.get("GWCLIENTID", "")
GOOGLE_ANAL_ID = os.environ.get("GOOGLE_ANAL_ID", "")
GT             = os.environ.get("GT", "Cash6mGeneral_6mNL25R25")
SCENARIO    = os.environ.get("SCENARIO", "BTN_BB")
TYPE_FILTER = os.environ.get("TYPE", "")
STREET      = os.environ.get("STREET", "both")   # "flop" / "turn" / "both"

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
    "CO_BB": {
        "label": "SRP CO vs BB",
        "pf":    "F-F-R2.5-F-F-C",
        "ip":    "CO",
        "oop":   "BB",
        "depth": 100,
    },
    "HJ_BB": {
        "label": "SRP HJ vs BB",
        "pf":    "F-R2.5-F-F-F-C",
        "ip":    "HJ",
        "oop":   "BB",
        "depth": 100,
    },
    "SB_BB": {
        "label": "SRP SB vs BB",
        "pf":    "F-F-F-F-R3-C",
        "ip":    "BB",
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
            ("TA+_2nd", "7h", "2ndカードペア"),
            ("TA-_OC",  "Ah", "OC(A)"),
        ],
    },
    {
        "type":  "型2_ハイウェット",
        "flop":  "Qh8d3s",
        "desc":  "Q高・2トーン",
        "turns": [
            ("blank",   "5d", "ブランク"),
            ("TA+_2nd", "8c", "2ndカードペア"),
            ("TA-_OC",  "Ah", "OC(A)"),
        ],
    },
    {
        "type":  "型3_ロードライ",
        "flop":  "Jd7s5c",
        "desc":  "J中・レインボー",
        "turns": [
            ("blank",   "2c", "ブランク"),
            ("TA+_2nd", "7h", "2ndカードペア"),
            ("TA-_OC",  "Ah", "OC(A)"),
        ],
    },
    {
        "type":  "型4_ローウェット",
        "flop":  "Th9s8d",
        "desc":  "低連携・2トーン",
        "turns": [
            ("blank",  "2c", "ブランク"),
            ("danger", "6c", "SC危険牌"),
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
            ("TA+_3rd", "Ks", "3rdカードペア(K)"),
        ],
    },
    {
        "type":  "型7_ペア低",
        "flop":  "7s7d2c",
        "desc":  "77低ペアボード",
        "turns": [
            ("blank",  "3c", "ブランク"),
            ("TA-_OC", "Ah", "OC(A)"),
        ],
    },
]

HC_SORT = {
    "straight_flush": 97, "quads": 93, "fullhouse": 89, "flush": 83, "straight": 80,
    "set": 85, "two_pair": 77, "trips": 74, "overpair": 70, "top_pair": 60,
    "underpair": 42, "second_pair": 43, "third_pair": 35, "low_pair": 30,
    "ace_high": 24, "king_high": 21, "queen_high": 19, "jack_high": 17,
    "ten_high": 15, "no_made_hand": 12,
}

# ─────────────────── API ユーティリティ ───────────────────

def make_headers():
    h = {
        "accept":             "application/json, text/plain, */*",
        "accept-language":    "ja,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
        "authorization":      f"Bearer {TOKEN}",
        "cache-control":      "no-cache",
        "origin":             "https://app.gtowizard.com",
        "pragma":             "no-cache",
        "priority":           "u=1, i",
        "referer":            "https://app.gtowizard.com/",
        "sec-ch-ua":          '"Chromium";v="148", "Microsoft Edge";v="148", "Not/A)Brand";v="99"',
        "sec-ch-ua-mobile":   "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest":     "empty",
        "sec-fetch-mode":     "cors",
        "sec-fetch-site":     "same-site",
        "user-agent":         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
    }
    if GWCLIENTID:
        h["gwclientid"] = GWCLIENTID
    if GOOGLE_ANAL_ID:
        h["google-anal-id"] = GOOGLE_ANAL_ID
    return h


def call_api(board, flop_actions="", turn_actions="", river_actions="", pf=None, depth=100):
    params = {
        "gametype": GT, "depth": str(depth), "stacks": "",
        "preflop_actions": pf or SCENARIOS[SCENARIO]["pf"],
        "flop_actions":    flop_actions,
        "turn_actions":    turn_actions,
        "river_actions":   river_actions,
        "board":           board,
    }
    for attempt in range(4):
        r = requests.get(BASE_URL, params=params, headers=make_headers(), timeout=30)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            try:
                body = r.json()
                if body.get("time_period_in_seconds", 0) >= 86400:
                    ra = r.headers.get("Retry-After", "?")
                    print(f"  ❌ 日次クォータ超過 (limit={body['request_limit']}, {int(ra)//3600}時間後リセット)")
                    sys.exit(1)
            except Exception:
                pass
            wait = 10 * (attempt + 1)
            print(f"  [HTTP 429] board={board} fa={flop_actions!r} ta={turn_actions!r} → {wait}s 待機中...")
            time.sleep(wait)
            continue
        print(f"  [HTTP {r.status_code}] board={board} fa={flop_actions!r} ta={turn_actions!r}")
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
        if   t == "CHECK": codes["check"]   = c
        elif t == "FOLD":  codes["fold"]    = c
        elif t == "CALL":  codes["call"]    = c
        elif t == "RAISE":
            if   bp < 0.25: codes["bet20"]   = c
            elif bp < 0.40: codes["bet33"]   = c
            elif bp < 0.65: codes["bet50"]   = c
            elif bp < 0.90: codes["bet75"]   = c
            elif bp < 1.20: codes["bet100"]  = c
            else:           codes["betover"] = c
    return codes


def dominant_bet_code(codes):
    """最も一般的なベットサイズのコードを返す（なければ None）。"""
    for key in ["bet33", "bet50", "bet75", "bet100", "betover", "bet20"]:
        if key in codes:
            return codes[key]
    return None


def find_raise_code(sols):
    """action_solutions からRAISEコードを最初に見つけて返す（CR/3bet用）。"""
    for s in sols:
        if s["action"]["type"] == "RAISE":
            return s["action"]["code"]
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


def weighted_rate(rows, keys):
    """コンボ加重平均行動率。選択肢なしなら None。"""
    if not keys or not rows:
        return None
    total = sum(r["total"] for r in rows)
    if total == 0:
        return None
    return sum(r["total"] * sum(r.get(k, 0) or 0 for k in keys) for r in rows) / total


def rows_to_store(rows, keep_keys):
    """JSON保存用にrowsを整形（keep_keys + hc/total/share のみ残す）。"""
    if not rows:
        return []
    return [
        {k: (round(v * 100, 1) if isinstance(v, float) else v)
         for k, v in row.items()
         if k in ("hc", "total", "share") or k in keep_keys}
        for row in rows
    ]


def print_hc_table(rows, header=""):
    """hand_category 別行動率テーブル表示。"""
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


# ─────────────────── フロップCR分析 ───────────────────

def analyze_flop_cr(cfg, pf, ip, oop, depth):
    """
    フロップCR分析:
      Step1: flop_actions="X" → IPのCBetコードを取得
      Step2: flop_actions="X-{cbet}" → OOPのオプション（fold/call/raise=CR）
      Step3: flop_actions="X-{cbet}-{cr}" → IPのCR対応（fold/call/reraise）
    """
    flop = cfg["flop"]
    print(f"\n  【フロップCR】 {flop}")

    # Step1: IPのCBet選択肢を取得
    data1 = call_api(flop, flop_actions="X", pf=pf, depth=depth)
    time.sleep(4.0)
    if not data1:
        print(f"    Step1 失敗（IPのCBetコード取得）")
        return None

    ip_player1 = get_player(data1, ip)
    sols1      = data1.get("action_solutions", [])
    if not ip_player1 or not sols1:
        print(f"    Step1: IPプレイヤーデータなし")
        return None

    ip_codes1  = classify_actions(sols1)
    cbet_code  = dominant_bet_code(ip_codes1)
    print(f"    Step1 IPコード: {ip_codes1}  主要cbet={cbet_code}")
    if not cbet_code:
        print(f"    IPのCBetなし（チェックバックのみ）")
        return {"flop": flop, "cbet_code": None, "oop_cr_rate_pct": None,
                "ip_cr_response": None, "oop_cr_by_cat": []}

    # Step2: OOPのCR選択肢を取得
    data2 = call_api(flop, flop_actions=f"X-{cbet_code}", pf=pf, depth=depth)
    time.sleep(4.0)
    if not data2:
        print(f"    Step2 失敗（OOP CR選択肢取得）")
        return None

    oop_player2 = get_player(data2, oop)
    sols2       = data2.get("action_solutions", [])
    if not oop_player2 or not sols2:
        print(f"    Step2: OOPプレイヤーデータなし")
        return None

    oop_codes2 = classify_actions(sols2)
    cr_code    = find_raise_code(sols2)
    print(f"    Step2 OOPコード: {oop_codes2}  CR={cr_code}")

    # OOPのCR率（手_category別）
    oop_rows2    = calc_hc_action_rates(sols2, oop_player2, oop_codes2)
    cr_keys      = ["bet33", "bet50", "bet75", "bet100", "betover", "bet20"]
    cr_keys_used = [k for k in cr_keys if k in oop_codes2]
    oop_cr_rate  = weighted_rate(oop_rows2, cr_keys_used)

    if oop_cr_rate is not None:
        print(f"    OOP フロップCR率（総合）: {oop_cr_rate*100:.0f}%")
        print_hc_table(oop_rows2, "OOP CR率 by hand_category")
    else:
        print(f"    OOP フロップCR: チェックのみ（レイズなし）")

    if not cr_code:
        return {
            "flop": flop, "cbet_code": cbet_code, "cr_code": None,
            "oop_cr_rate_pct": None, "ip_cr_response": None,
            "oop_cr_by_cat": rows_to_store(oop_rows2, cr_keys_used + ["call", "fold"]),
        }

    # Step3: IPのCR対応を取得
    data3 = call_api(flop, flop_actions=f"X-{cbet_code}-{cr_code}", pf=pf, depth=depth)
    time.sleep(4.0)
    if not data3:
        print(f"    Step3 失敗（IPのCR対応取得）")
        ip_cr_result = None
    else:
        ip_player3 = get_player(data3, ip)
        sols3      = data3.get("action_solutions", [])
        if not ip_player3 or not sols3:
            print(f"    Step3: IPプレイヤーデータなし")
            ip_cr_result = None
        else:
            ip_codes3   = classify_actions(sols3)
            ip_rows3    = calc_hc_action_rates(sols3, ip_player3, ip_codes3)
            fold_rate   = weighted_rate(ip_rows3, ["fold"])
            call_rate   = weighted_rate(ip_rows3, ["call"])
            reraise_keys = [k for k in ip_codes3 if k not in ("fold", "call", "check")]
            rerraise_rate = weighted_rate(ip_rows3, reraise_keys)
            if fold_rate is not None and call_rate is not None:
                rr_pct = f"{rerraise_rate*100:.0f}%" if rerraise_rate is not None else "—"
                print(f"    IPのCR対応: fold={fold_rate*100:.0f}% call={call_rate*100:.0f}% reraise={rr_pct}")
            else:
                print("    IPのCR対応データなし")
            print_hc_table(ip_rows3, "IP CR対応 by hand_category")
            ip_cr_result = {
                "fold_pct":    round(fold_rate  * 100, 1) if fold_rate    is not None else None,
                "call_pct":    round(call_rate  * 100, 1) if call_rate    is not None else None,
                "reraise_pct": round(rerraise_rate * 100, 1) if rerraise_rate is not None else None,
                "by_cat":      rows_to_store(ip_rows3, list(ip_codes3.keys())),
            }

    return {
        "flop":            flop,
        "cbet_code":       cbet_code,
        "cr_code":         cr_code,
        "oop_cr_rate_pct": round(oop_cr_rate * 100, 1) if oop_cr_rate is not None else None,
        "oop_cr_by_cat":   rows_to_store(oop_rows2, cr_keys_used + ["call", "fold"]),
        "ip_cr_response":  ip_cr_result,
    }


# ─────────────────── ターンCR分析 ───────────────────

def analyze_turn_cr(cfg, pf, ip, oop, depth):
    """
    ターンCR分析（フロップCBet-call後、IPがターンバレル → OOPがCR）:
      各ターンカードに対して:
        Step1: board4, flop_actions="X-{cbet}-C", turn_actions="X" → IPのターンベットコード
        Step2: board4, fa="X-{cbet}-C", ta="X-{t_bet}" → OOPのオプション（CR含む）
        Step3: board4, fa="X-{cbet}-C", ta="X-{t_bet}-{tcr}" → IPのCR対応
    フロップCBetコードは事前にStep0で取得。
    """
    flop = cfg["flop"]
    print(f"\n  【ターンCR】 {flop}")

    # Step0: フロップCBetコード取得
    data0 = call_api(flop, flop_actions="X", pf=pf, depth=depth)
    time.sleep(4.0)
    if not data0:
        print(f"    Step0 失敗（フロップCBetコード取得）")
        return []

    sols0     = data0.get("action_solutions", [])
    ip_codes0 = classify_actions(sols0) if sols0 else {}
    cbet_code = dominant_bet_code(ip_codes0)
    print(f"    フロップCBetコード: {cbet_code}  (コード群: {ip_codes0})")
    if not cbet_code:
        print(f"    フロップCBetなし → ターンCR分析スキップ")
        return []

    turn_results = []
    for turn_tag, turn_card, turn_desc in cfg["turns"]:
        board4 = flop + turn_card
        print(f"\n    ── [{turn_tag}] {turn_card} ({turn_desc}): board={board4}")

        # Step1: IPのターンバレル選択肢を取得
        data1 = call_api(board4, flop_actions=f"X-{cbet_code}-C",
                         turn_actions="X", pf=pf, depth=depth)
        time.sleep(4.0)
        if not data1:
            print(f"      Step1 失敗（IPターンベットコード取得）")
            turn_results.append({
                "tag": turn_tag, "card": turn_card, "desc": turn_desc,
                "oop_tcr_rate_pct": None, "ip_tcr_response": None, "oop_tcr_by_cat": [],
            })
            continue

        ip_player1 = get_player(data1, ip)
        sols1      = data1.get("action_solutions", [])
        if not ip_player1 or not sols1:
            print(f"      Step1: IPプレイヤーデータなし")
            turn_results.append({
                "tag": turn_tag, "card": turn_card, "desc": turn_desc,
                "oop_tcr_rate_pct": None, "ip_tcr_response": None, "oop_tcr_by_cat": [],
            })
            continue

        ip_codes1   = classify_actions(sols1)
        t_bet_code  = dominant_bet_code(ip_codes1)
        print(f"      Step1 IPターンコード: {ip_codes1}  tbet={t_bet_code}")
        if not t_bet_code:
            print(f"      IPターンバレルなし → このターンのCR分析スキップ")
            turn_results.append({
                "tag": turn_tag, "card": turn_card, "desc": turn_desc,
                "t_bet_code": None,
                "oop_tcr_rate_pct": None, "ip_tcr_response": None, "oop_tcr_by_cat": [],
            })
            continue

        # Step2: OOPのターンCR選択肢を取得
        data2 = call_api(board4, flop_actions=f"X-{cbet_code}-C",
                         turn_actions=f"X-{t_bet_code}", pf=pf, depth=depth)
        time.sleep(4.0)
        if not data2:
            print(f"      Step2 失敗（OOP ターンCR取得）")
            turn_results.append({
                "tag": turn_tag, "card": turn_card, "desc": turn_desc,
                "t_bet_code": t_bet_code,
                "oop_tcr_rate_pct": None, "ip_tcr_response": None, "oop_tcr_by_cat": [],
            })
            continue

        oop_player2 = get_player(data2, oop)
        sols2       = data2.get("action_solutions", [])
        if not oop_player2 or not sols2:
            print(f"      Step2: OOPプレイヤーデータなし")
            turn_results.append({
                "tag": turn_tag, "card": turn_card, "desc": turn_desc,
                "t_bet_code": t_bet_code,
                "oop_tcr_rate_pct": None, "ip_tcr_response": None, "oop_tcr_by_cat": [],
            })
            continue

        oop_codes2  = classify_actions(sols2)
        tcr_code    = find_raise_code(sols2)
        print(f"      Step2 OOPターンCRコード: {oop_codes2}  tcr={tcr_code}")

        oop_rows2     = calc_hc_action_rates(sols2, oop_player2, oop_codes2)
        tcr_keys      = ["bet33", "bet50", "bet75", "bet100", "betover", "bet20"]
        tcr_keys_used = [k for k in tcr_keys if k in oop_codes2]
        oop_tcr_rate  = weighted_rate(oop_rows2, tcr_keys_used)

        if oop_tcr_rate is not None:
            print(f"      OOP ターンCR率（総合）: {oop_tcr_rate*100:.0f}%")
            print_hc_table(oop_rows2, "OOP ターンCR率 by hand_category")
        else:
            print(f"      OOP ターンCR: チェックのみ")

        # Step3: IPのターンCR対応
        ip_tcr_result = None
        if tcr_code:
            data3 = call_api(board4, flop_actions=f"X-{cbet_code}-C",
                             turn_actions=f"X-{t_bet_code}-{tcr_code}", pf=pf, depth=depth)
            time.sleep(4.0)
            if data3:
                ip_player3 = get_player(data3, ip)
                sols3      = data3.get("action_solutions", [])
                if ip_player3 and sols3:
                    ip_codes3     = classify_actions(sols3)
                    ip_rows3      = calc_hc_action_rates(sols3, ip_player3, ip_codes3)
                    fold_rate     = weighted_rate(ip_rows3, ["fold"])
                    call_rate     = weighted_rate(ip_rows3, ["call"])
                    reraise_keys  = [k for k in ip_codes3 if k not in ("fold", "call", "check")]
                    rerraise_rate = weighted_rate(ip_rows3, reraise_keys)
                    if fold_rate is not None and call_rate is not None:
                        rr_pct2 = f"{rerraise_rate*100:.0f}%" if rerraise_rate is not None else "—"
                        print(f"      IPのターンCR対応: fold={fold_rate*100:.0f}% call={call_rate*100:.0f}% reraise={rr_pct2}")
                    print_hc_table(ip_rows3, "IP ターンCR対応 by hand_category")
                    ip_tcr_result = {
                        "fold_pct":    round(fold_rate     * 100, 1) if fold_rate     is not None else None,
                        "call_pct":    round(call_rate     * 100, 1) if call_rate     is not None else None,
                        "reraise_pct": round(rerraise_rate * 100, 1) if rerraise_rate is not None else None,
                        "by_cat":      rows_to_store(ip_rows3, list(ip_codes3.keys())),
                    }
            else:
                print(f"      Step3 失敗（IPターンCR対応取得）")

        turn_results.append({
            "tag":             turn_tag,
            "card":            turn_card,
            "desc":            turn_desc,
            "cbet_code":       cbet_code,
            "t_bet_code":      t_bet_code,
            "tcr_code":        tcr_code,
            "oop_tcr_rate_pct": round(oop_tcr_rate * 100, 1) if oop_tcr_rate is not None else None,
            "oop_tcr_by_cat":  rows_to_store(oop_rows2, tcr_keys_used + ["call", "fold"]),
            "ip_tcr_response": ip_tcr_result,
        })
        time.sleep(2.0)

    return turn_results


# ─────────────────── メイン ───────────────────

def check_token():
    import base64 as _b64
    try:
        payload = TOKEN.split('.')[1]
        payload += '=' * (-len(payload) % 4)
        data = json.loads(_b64.urlsafe_b64decode(payload))
        exp = data.get('exp', 0)
        remaining = exp - time.time()
        if remaining <= 60:
            print(f"❌ TOKEN期限切れ（残り{remaining:.0f}秒）"); sys.exit(1)
        print(f"✅ 認証OK（残り{remaining/60:.1f}分）")
    except Exception as e:
        print(f"❌ TOKEN パース失敗: {e}"); sys.exit(1)


def main():
    if not TOKEN:
        print("❌ TOKEN 未設定"); sys.exit(1)

    scen = SCENARIOS.get(SCENARIO)
    if not scen:
        print(f"❌ 未知シナリオ: {SCENARIO}. 選択肢: {list(SCENARIOS)}"); sys.exit(1)

    pf, ip, oop, depth = scen["pf"], scen["ip"], scen["oop"], scen.get("depth", 100)
    print(f"シナリオ: {scen['label']}  (IP={ip}, OOP={oop}, depth={depth}BB)")
    print(f"分析: チェックレイズ攻防（フロップCR + ターンCR）")
    print(f"gametype: {GT}  STREET={STREET}\n")

    check_token()
    time.sleep(2.0)

    do_flop = STREET in ("flop", "both")
    do_turn = STREET in ("turn", "both")

    all_results = []
    configs = [c for c in BOARD_CONFIGS if not TYPE_FILTER or c["type"] == TYPE_FILTER]

    for cfg in configs:
        print(f"\n{'='*70}")
        print(f"【{cfg['type']}】 {cfg['flop']}  ({cfg['desc']})")

        flop_cr_result = None
        turn_cr_results = []

        if do_flop:
            flop_cr_result = analyze_flop_cr(cfg, pf, ip, oop, depth)

        if do_turn:
            turn_cr_results = analyze_turn_cr(cfg, pf, ip, oop, depth)

        # ─── ターンCRサマリー ───
        if turn_cr_results:
            print(f"\n  ■ {cfg['type']} ターンCR サマリー")
            print(f"  {'ターン':5s}({'タグ':10s}) | {'OOP CR%':>9} | IP対応(F/C/R)")
            print(f"  {'-'*55}")
            for tr in turn_cr_results:
                cr_p = tr.get("oop_tcr_rate_pct")
                rsp  = tr.get("ip_tcr_response") or {}
                f_p  = rsp.get("fold_pct")
                c_p  = rsp.get("call_pct")
                r_p  = rsp.get("reraise_pct")
                cr_s = f"{cr_p:.0f}%" if cr_p is not None else "—"
                rsp_s = (f"F{f_p:.0f}%/C{c_p:.0f}%/R{r_p:.0f}%"
                         if f_p is not None else "—")
                print(f"  {tr['card']:5s}({tr['tag'][:10]:10s}) | {cr_s:>9} | {rsp_s}")

        all_results.append({
            "type":          cfg["type"],
            "flop":          cfg["flop"],
            "desc":          cfg["desc"],
            "flop_cr":       flop_cr_result,
            "turn_cr":       turn_cr_results,
        })
        time.sleep(2.0)

    # ─── 全体サマリー ───
    print(f"\n\n{'='*70}")
    print(f"★ 全体サマリー: OOP CR率（コンボ加重総合）")
    if do_flop:
        print(f"\n  [フロップCR]")
        print(f"  {'型':20s} | {'OOP CR%':>9} | IP fold%")
        print(f"  {'-'*45}")
        for r in all_results:
            fc = r.get("flop_cr") or {}
            cr_p = fc.get("oop_cr_rate_pct")
            ip_r = fc.get("ip_cr_response") or {}
            f_p  = ip_r.get("fold_pct")
            cr_s = f"{cr_p:.0f}%" if cr_p is not None else "—"
            f_s  = f"{f_p:.0f}%" if f_p is not None else "—"
            print(f"  {r['type']:20s} | {cr_s:>9} | {f_s}")

    if do_turn:
        print(f"\n  [ターンCR]")
        print(f"  {'型':20s} | {'ターン':5s}({'タグ':10s}) | {'OOP CR%':>9}")
        print(f"  {'-'*55}")
        for r in all_results:
            for tr in r.get("turn_cr", []):
                cr_p = tr.get("oop_tcr_rate_pct")
                cr_s = f"{cr_p:.0f}%" if cr_p is not None else "—"
                print(f"  {r['type']:20s} | {tr['card']:5s}({tr['tag'][:10]:10s}) | {cr_s:>9}")

    # JSON 保存
    out = FINDINGS_DIR / f"check_raise_{SCENARIO}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"scenario": scen["label"], "results": all_results},
                  f, ensure_ascii=False, indent=2)
    print(f"\n✅ 完了 → {out}")


if __name__ == "__main__":
    main()
