#!/usr/bin/env python3
"""
mtt_turn_barrel.py — MTT ターンバレル分析

フロップCBet → コール後のターン行動を3種のターンカードで検証:
  blank      : ボードに絡まない中立カード
  IP 強化   : IPのレンジを強化するカード（2ndペアペア / ボードペア等）
  OOP 強化  : OOPのレンジを強化するカード（オーバーカード等）

注: コード内のタグ文字列 ("TA+_2nd" 等) は既存 JSON データとの互換性のため
    そのまま残している (研究 archive)。新規書籍では「IP 強化 / OOP 強化」用語で統一。

各ターンカードで:
  Step0: フロップCBetコード取得         (1 call/board)
  Step1: IP ターンバレル判断            (1 call/board/card)
  Step2: OOP ターン守備（vs バレル）     (1 call/board/card)

API合計: 7 boards × (1 + 3×2) = 49 calls

使い方:
  TOKEN=eyJ... GWCLIENTID=xxx GOOGLE_ANAL_ID=yyy python3 -u mtt_turn_barrel.py
  TOKEN=eyJ... SBR=40 python3 -u mtt_turn_barrel.py
  TOKEN=eyJ... TYPE=型1 python3 -u mtt_turn_barrel.py
"""

import os, sys, json, time, requests
from pathlib import Path

TOKEN          = os.environ.get("TOKEN", "")
GWCLIENTID     = os.environ.get("GWCLIENTID", "")
GOOGLE_ANAL_ID = os.environ.get("GOOGLE_ANAL_ID", "")
GT             = "MTTGeneral"
SCENARIO       = os.environ.get("SCENARIO", "BTN_BB")
SBR            = os.environ.get("SBR", "25")
TYPE_FILTER    = os.environ.get("TYPE", "")

FINDINGS_DIR = Path(__file__).parent / "findings"
FINDINGS_DIR.mkdir(exist_ok=True)

BASE_URL = "https://api.gtowizard.com/v4/solutions/spot-solution/"

# ─────────────────── SBR設定 ───────────────────
def _stacks(hero_bb: int, n: int = 9) -> str:
    others = round(hero_bb * 0.9)
    return "-".join([str(hero_bb)] + [str(others)] * (n - 1))

SBR_CONFIGS = {
    "40": {"depth": 40.125, "label": "Deep(SBR40)",
           "btn_bb_pf": "F-F-F-F-F-R2.5-F-C",
           "sb_bb_pf":  "F-F-F-F-F-F-R2.5-C",
           "stacks": ""},
    "25": {"depth": 25.125, "label": "Middle-Deep(SBR25)",
           "btn_bb_pf": "F-F-F-F-F-R2.1-F-C",
           "sb_bb_pf":  "F-F-F-F-F-F-R2.5-C",
           "stacks": ""},
    "20": {"depth": 20.125, "label": "Middle(SBR20)",
           "btn_bb_pf": "F-F-F-F-F-R2-F-C",
           "sb_bb_pf":  "F-F-F-F-F-F-R2.5-C",
           "stacks": ""},
    "15": {"depth": 15.125, "label": "Middle-Short(SBR15)",
           "btn_bb_pf": "F-F-F-F-F-R2-F-C",
           "sb_bb_pf":  "F-F-F-F-F-F-R2.5-C",
           "stacks": ""},
}

# ターンカード: (タグ, カード)
# IP 強化 ("TA+_*"): IPのポジションを相対的に強化（2ndペアペア→強い手を追加）
# OOP 強化 ("TA-_*"): OOPのポジションを相対的に強化（オーバーカード→コール域が広がる）
# ※ タグ文字列は既存 JSON 互換のため残置 (研究 archive)
BOARD_CONFIGS = [
    {
        "type": "型1_ハイドライ",  "flop": "Ks7d2c", "desc": "K高・レインボー",
        "turns": [("blank", "4h"), ("TA+_2nd", "7h"), ("TA-_OC", "Ah")],
    },
    {
        "type": "型2_ハイウェット", "flop": "Qh8d3s", "desc": "Q高・2トーン",
        "turns": [("blank", "5c"), ("TA+_2nd", "8h"), ("TA-_OC", "Ac")],
    },
    {
        "type": "型3_ロードライ",  "flop": "Jd7s5c", "desc": "J中・レインボー",
        "turns": [("blank", "2h"), ("TA+_2nd", "5h"), ("TA-_OC", "Kc")],
    },
    {
        "type": "型4_ローウェット", "flop": "Th9s8d", "desc": "低連携・2トーン",
        "turns": [("blank", "2c"), ("TA+_board", "9h"), ("TA-_OC", "Ac")],
    },
    {
        "type": "型5_モノトーン",  "flop": "Ah9h5h", "desc": "A高モノトーン",
        "turns": [("blank", "2c"), ("TA+_4th", "Kh"), ("TA-_pair", "5c")],
    },
    {
        "type": "型6_ペア高",     "flop": "AsAcKd", "desc": "AAKペアボード",
        "turns": [("blank", "2h"), ("TA+_mid", "Qh"), ("TA-_mid", "9h")],
    },
    {
        "type": "型7_ペア低",     "flop": "7s7d2c", "desc": "77低ペアボード",
        "turns": [("blank", "3h"), ("TA+_mid", "8h"), ("TA-_OC", "Ah")],
    },
]

HC_SORT = {
    "straight_flush": 97, "quads": 93, "fullhouse": 89,
    "set": 85, "flush": 83, "straight": 80, "two_pair": 77, "trips": 74,
    "overpair": 70, "top_pair": 60, "second_pair": 43, "underpair": 42,
    "third_pair": 35, "low_pair": 30,
    "ace_high": 24, "king_high": 21, "queen_high": 19, "jack_high": 17,
    "ten_high": 15, "no_made_hand": 12,
}


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
    if GWCLIENTID:     h["gwclientid"]     = GWCLIENTID
    if GOOGLE_ANAL_ID: h["google-anal-id"] = GOOGLE_ANAL_ID
    return h


def call_api(board, flop_actions="", turn_actions="", pf=None, depth=100):
    sbr_cfg = SBR_CONFIGS.get(SBR, SBR_CONFIGS["25"])
    params = {
        "gametype":        GT,
        "depth":           str(depth),
        "stacks":          sbr_cfg.get("stacks", ""),
        "preflop_actions": pf or sbr_cfg["btn_bb_pf"],
        "flop_actions":    flop_actions,
        "turn_actions":    turn_actions,
        "river_actions":   "",
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
            print(f"  [HTTP 429] board={board} flop={flop_actions!r} turn={turn_actions!r} → {wait}s 待機中...")
            time.sleep(wait)
            continue
        print(f"  [HTTP {r.status_code}] board={board} flop={flop_actions!r} turn={turn_actions!r}")
        return None
    print(f"  [429 最大リトライ超過] board={board}")
    return None


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


def get_player(data, pos):
    for p in data.get("players_info", []):
        if isinstance(p.get("player"), dict) and p["player"].get("position") == pos:
            return p
    return None


def classify_actions(sols):
    codes = {}
    for s in sols:
        a = s["action"]
        t, c = a["type"], a["code"]
        bp = float(a.get("betsize_by_pot") or 0)
        if   t == "CHECK": codes["check"]    = c
        elif t == "FOLD":  codes["fold"]     = c
        elif t == "CALL":  codes["call"]     = c
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
        act = {ck: action_hc.get(cv, {}).get(hc, 0) / total if total > 0 else 0
               for ck, cv in codes.items()}
        rows.append({"hc": hc, "total": round(total, 1), "share": share, **act})
    return rows


def weighted_rate(rows, keys):
    if not keys or not rows: return None
    total_combos = sum(r["total"] for r in rows)
    if total_combos == 0: return None
    return sum(r["total"] * sum(r.get(k, 0) or 0 for k in keys) for r in rows) / total_combos


def print_hc_table(rows, header=""):
    if not rows: return
    keys = [k for k in rows[0] if k not in ("hc", "total", "share")]
    if header: print(f"\n  {header}")
    col_hdr = f"  {'カテゴリ':22s} {'コンボ':>6} {'シェア':>6}"
    for k in keys: col_hdr += f" {k:>7}"
    print(col_hdr)
    print(f"  {'-'*72}")
    for row in rows:
        line = f"  {row['hc']:22s} {row['total']:6.1f} {row['share']:5.1f}%"
        for k in keys:
            v = row.get(k)
            line += f" {v*100:6.0f}%" if v is not None else f"  {'—':>6}"
        print(line)


def rows_to_store(rows, codes_dict):
    if not rows: return []
    keep_keys = {"hc", "total", "share"} | set(codes_dict.keys())
    return [
        {k: (round(v * 100, 1) if isinstance(v, float) and k not in ("total", "share") else v)
         for k, v in row.items() if k in keep_keys}
        for row in rows
    ]


def analyze_board(cfg, ip, oop, pf, depth):
    flop  = cfg["flop"]
    turns = cfg["turns"]

    result = {"type": cfg["type"], "flop": flop, "desc": cfg["desc"], "cbet_code": None, "turns": []}

    # ─── Step0: フロップCBetコード取得 ───
    print(f"\n  [Step0] フロップCBetコード取得 (flop_actions='X')")
    data_flop = call_api(flop, flop_actions="X", pf=pf, depth=depth)
    time.sleep(8.0)

    if not data_flop:
        print("    フロップデータ取得失敗"); return result

    ip_sols   = data_flop.get("action_solutions", [])
    ip_codes  = classify_actions(ip_sols)
    cbet_code = dominant_bet_code(ip_codes)
    print(f"    IP codes={ip_codes}  CBetコード={cbet_code}")

    result["cbet_code"] = cbet_code

    if not cbet_code:
        print("    CBetなし → ターン分析スキップ"); return result

    barrel_seq = f"X-{cbet_code}-C"  # OOPチェック → IP CBet → OOPコール

    # ─── ターンカード別分析 ───
    for tag, turn_card in turns:
        board4 = flop + turn_card
        print(f"\n  ── [{tag}] {turn_card}  board={board4}")

        turn_result = {
            "tag": tag, "card": turn_card, "board4": board4,
            "ip_barrel": None, "oop_defense": None,
        }

        # Step1: IP ターンバレル判断
        data_ip = call_api(board4, flop_actions=barrel_seq, turn_actions="", pf=pf, depth=depth)
        time.sleep(8.0)

        if not data_ip:
            print("    IPターンデータ取得失敗")
            result["turns"].append(turn_result)
            continue

        ip_p   = get_player(data_ip, ip)
        ip_sol = data_ip.get("action_solutions", [])
        if not ip_p or not ip_sol:
            print(f"    IPプレイヤーデータなし (pos={ip})")
            result["turns"].append(turn_result)
            continue

        t_codes    = classify_actions(ip_sol)
        bet_c_set  = {v for k, v in t_codes.items() if k not in ("check", "fold")}
        barrel_rt  = sum(float(s.get("total_frequency", 0)) for s in ip_sol if s["action"]["code"] in bet_c_set)
        barrel_c   = dominant_bet_code(t_codes)

        print(f"    IP バレル率={barrel_rt*100:.0f}%  主要code={barrel_c}  IP codes={t_codes}")

        turn_result["ip_barrel"] = {
            "total_bet_pct": round(barrel_rt * 100, 1),
            "bet_code":      barrel_c,
        }

        # Step2: OOP ターン守備（IPがバレルした場合）
        if barrel_c:
            data_oop = call_api(board4, flop_actions=barrel_seq, turn_actions=barrel_c,
                                pf=pf, depth=depth)
            time.sleep(8.0)

            if data_oop:
                oop_p   = get_player(data_oop, oop)
                oop_sol = data_oop.get("action_solutions", [])
                if oop_p and oop_sol:
                    d_codes   = classify_actions(oop_sol)
                    call_rt   = sum(float(s.get("total_frequency", 0)) for s in oop_sol if s["action"]["code"] == d_codes.get("call"))
                    fold_rt   = sum(float(s.get("total_frequency", 0)) for s in oop_sol if s["action"]["code"] == d_codes.get("fold"))
                    raise_c_set = {v for k, v in d_codes.items() if k not in ("check", "fold", "call")}
                    raise_rt  = sum(float(s.get("total_frequency", 0)) for s in oop_sol if s["action"]["code"] in raise_c_set)

                    parts = [f"コール={call_rt*100:.0f}%", f"フォールド={fold_rt*100:.0f}%", f"レイズ={raise_rt*100:.0f}%"]
                    print(f"    OOP {' / '.join(parts)}")

                    turn_result["oop_defense"] = {
                        "call_pct":  round(call_rt  * 100, 1),
                        "fold_pct":  round(fold_rt  * 100, 1),
                        "raise_pct": round(raise_rt * 100, 1),
                    }
        else:
            print("    IPバレルなし → OOP守備スキップ")

        result["turns"].append(turn_result)

    return result


def main():
    if not TOKEN:
        print("❌ TOKEN 未設定"); sys.exit(1)

    sbr_cfg = SBR_CONFIGS.get(SBR)
    if not sbr_cfg:
        print(f"❌ 未知SBR: {SBR}. 選択肢: {list(SBR_CONFIGS)}"); sys.exit(1)

    depth = sbr_cfg["depth"]
    label = sbr_cfg["label"]

    if SCENARIO == "BTN_BB":
        ip, oop, pf = "BTN", "BB", sbr_cfg["btn_bb_pf"]
        scenario_label = f"SRP BTN vs BB ({label})"
    else:
        print(f"❌ 未知シナリオ: {SCENARIO}. 選択肢: BTN_BB"); sys.exit(1)

    print(f"シナリオ: {scenario_label}  (IP={ip}, OOP={oop}, depth={depth}BB)")
    print(f"分析: ターンバレル（CBet→Call→Turn）3ターンカード別")
    print(f"gametype: {GT}\n")

    check_token()
    time.sleep(5.0)

    configs = [c for c in BOARD_CONFIGS if not TYPE_FILTER or c["type"] == TYPE_FILTER]
    all_results = []

    for cfg in configs:
        print(f"\n{'='*70}")
        print(f"【{cfg['type']}】 {cfg['flop']}  ({cfg['desc']})")
        result = analyze_board(cfg, ip, oop, pf, depth)
        all_results.append(result)
        time.sleep(3.0)

    # ─── 全体サマリー ───
    print(f"\n\n{'='*70}")
    print(f"★ 全体サマリー: ターンバレル率 vs OOPフォールド率")
    print(f"  {'型':20s} | {'カード':6s} | {'タグ':12s} | {'IP barrel%':>10} | {'OOP fold%':>10}")
    print(f"  {'-'*68}")
    for r in all_results:
        for t in r.get("turns", []):
            ib = t.get("ip_barrel")
            od = t.get("oop_defense")
            b_pct = f"{ib['total_bet_pct']:.0f}%" if ib and ib["total_bet_pct"] is not None else "—"
            f_pct = f"{od['fold_pct']:.0f}%"      if od and od["fold_pct"]       is not None else "—"
            print(f"  {r['type']:20s} | {t['card']:6s} | {t['tag']:12s} | {b_pct:>10} | {f_pct:>10}")

    out = FINDINGS_DIR / f"mtt_turn_barrel_SBR{SBR}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"scenario": scenario_label, "sbr": SBR, "results": all_results}, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 完了 → {out}")


if __name__ == "__main__":
    main()
