#!/usr/bin/env python3
"""
cash_sb_bb.py — SB vs BB ポストフロップ分析 (Chapter 13)

SB vs BB の特殊構造を分析する:
  - SB はプリフロップアグレッサーだがポストフロップ OOP
  - BB はポストフロップ IP（位置的優位）
  - SBのCBet率（OOPだが initiative あり）
  - BBのディフェンス率（IP だが wide range）
  - X-X後のプローブ/遅延CBet（BTN_BBと比較）

BTN_BB との主な違い:
  - SBのレンジはBTNより wide（ゆえに CBet 頻度に差）
  - BBのIP レンジは wide（blind vs blind なので守備が特殊）

使い方:
  TOKEN=eyJ... python3 cash_sb_bb.py
  TOKEN=eyJ... TYPE=型1 python3 cash_sb_bb.py
"""

import os, sys, json, time, requests
from pathlib import Path

TOKEN          = os.environ.get("TOKEN", "")
GWCLIENTID     = os.environ.get("GWCLIENTID", "")
GOOGLE_ANAL_ID = os.environ.get("GOOGLE_ANAL_ID", "")
GT             = os.environ.get("GT", "Cash6mGeneral_6mNL25R25")
TYPE_FILTER = os.environ.get("TYPE", "")

FINDINGS_DIR = Path(__file__).parent / "findings"
FINDINGS_DIR.mkdir(exist_ok=True)

BASE_URL = "https://api.gtowizard.com/v4/solutions/spot-solution/"

# SB vs BB: SB raises, BB calls → SB is OOP postflop, BB is IP
SCENARIO = {
    "label": "SRP SB vs BB",
    "pf":    "F-F-F-F-R3-C",
    "ip":    "BB",
    "oop":   "SB",
    "depth": 100,
}

BOARD_CONFIGS = [
    {
        "type":  "型1_ハイドライ",
        "flop":  "Ks7d2c",
        "desc":  "K高・レインボー",
        "turns": [("blank", "4c", "ブランク"), ("TA+_2nd", "7h", "2ndペア"), ("TA-_OC", "Ah", "OC(A)")],
    },
    {
        "type":  "型2_ハイウェット",
        "flop":  "Qh8d3s",
        "desc":  "Q高・2トーン",
        "turns": [("blank", "5d", "ブランク"), ("TA+_2nd", "8c", "2ndペア"), ("TA-_OC", "Ah", "OC(A)")],
    },
    {
        "type":  "型3_ロードライ",
        "flop":  "Jd7s5c",
        "desc":  "J中・レインボー",
        "turns": [("blank", "2c", "ブランク"), ("TA+_2nd", "7h", "2ndペア"), ("TA-_OC", "Ah", "OC(A)")],
    },
    {
        "type":  "型4_ローウェット",
        "flop":  "Th9s8d",
        "desc":  "低連携・2トーン",
        "turns": [("blank", "2c", "ブランク"), ("danger", "6c", "SC(低)")],
    },
    {
        "type":  "型5_モノトーン",
        "flop":  "Ah9h5h",
        "desc":  "A高モノトーン",
        "turns": [("blank", "2c", "ブランク"), ("danger", "4h", "FC(4thハート)")],
    },
    {
        "type":  "型6_ペア高",
        "flop":  "AsAcKd",
        "desc":  "AAKペアボード",
        "turns": [("blank", "2c", "ブランク"), ("TA+_3rd", "Ks", "3rdペア(K)")],
    },
    {
        "type":  "型7_ペア低",
        "flop":  "7s7d2c",
        "desc":  "77低ペアボード",
        "turns": [("blank", "3c", "ブランク"), ("TA-_OC", "Ah", "OC(A)")],
    },
]

HC_SORT = {
    "straight_flush": 97, "quads": 93, "fullhouse": 89, "flush": 83, "straight": 80,
    "set": 85, "two_pair": 77, "trips": 74, "overpair": 70, "top_pair": 60,
    "underpair": 42, "second_pair": 43, "third_pair": 35, "low_pair": 30,
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
    if GWCLIENTID:
        h["gwclientid"] = GWCLIENTID
    if GOOGLE_ANAL_ID:
        h["google-anal-id"] = GOOGLE_ANAL_ID
    return h

def call_api(board, flop_actions="", turn_actions="", pf=None, depth=100):
    params = {
        "gametype": GT, "depth": str(depth), "stacks": "",
        "preflop_actions": pf or SCENARIO["pf"],
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
            try:
                body = r.json()
                if body.get("time_period_in_seconds", 0) >= 86400:
                    ra = r.headers.get("Retry-After", "?")
                    print(f"  ❌ 日次クォータ超過 (limit={body['request_limit']}, {int(ra)//3600}時間後リセット)")
                    sys.exit(1)
            except Exception:
                pass
            wait = 10 * (attempt + 1)
            print(f"  [429] board={board} flop={flop_actions!r} → {wait}s 待機中...")
            time.sleep(wait)
            continue
        print(f"  [HTTP {r.status_code}] board={board} flop={flop_actions!r}")
        return None
    print(f"  [429 超過] board={board}")
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
    if not keys or not rows:
        return None
    total = sum(r["total"] for r in rows)
    if total == 0:
        return None
    return sum(r["total"] * sum(r.get(k, 0) or 0 for k in keys) for r in rows) / total

def print_hc_table(rows, header=""):
    if not rows:
        return
    if header:
        print(f"  {header}")
    keys = [k for k in rows[0] if k not in ("hc", "total", "share")]
    col = f"  {'カテゴリ':22s} {'コンボ':>6} {'シェア':>6}"
    for k in keys:
        col += f"  {k:>7}"
    print(col)
    print("  " + "-" * 72)
    for row in rows:
        line = f"  {row['hc']:22s} {row['total']:6.1f} {row['share']:5.1f}%"
        for k in keys:
            v = row.get(k, 0) or 0
            line += f"  {v*100:6.0f}%"
        print(line)

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
    ip  = SCENARIO["ip"]
    oop = SCENARIO["oop"]
    pf  = SCENARIO["pf"]
    depth = SCENARIO["depth"]

    print(f"シナリオ: {SCENARIO['label']}  (IP={ip}, OOP={oop}, depth={depth}BB)")
    print(f"分析: SB vs BB 特殊構造（OOPがCBet権を持つ）")
    print(f"gametype: {GT}")
    print()

    check_token()
    time.sleep(2.0)

    all_results = []

    for cfg in BOARD_CONFIGS:
        if TYPE_FILTER and TYPE_FILTER not in cfg["type"]:
            continue

        flop = cfg["flop"]
        print("=" * 70)
        print(f"【{cfg['type']}】 {flop}  ({cfg['desc']})")

        # ── フロップ: OOP(SB)の行動 ──
        flop_data = call_api(flop, flop_actions="", pf=pf, depth=depth)
        time.sleep(4.0)

        oop_cbet_code = None
        oop_cbet_rate = None
        flop_rows = None

        if flop_data:
            oop_p  = get_player(flop_data, oop)
            fsols  = flop_data.get("action_solutions", [])
            fcodes = classify_actions(fsols) if fsols else {}
            if oop_p and fsols:
                flop_rows = calc_hc_action_rates(fsols, oop_p, fcodes)
                bet_keys  = [k for k in fcodes if k not in ("check", "fold")]
                oop_cbet_rate = weighted_rate(flop_rows, bet_keys)
                oop_cbet_code = dominant_bet_code(fcodes)
                print(f"  OOP(SB) フロップCBet: {fcodes}  主要bet={oop_cbet_code}")
                pct = round(oop_cbet_rate * 100) if oop_cbet_rate is not None else "—"
                print(f"  OOP(SB) CBet率（総合）: {pct}%")
                print_hc_table(flop_rows, "hand_category別 SB CBet率（シェア付き）")
        else:
            print(f"  OOPデータ取得失敗")

        # ── フロップ: OOPチェック後のIPの行動 ──
        ip_flop_data = call_api(flop, flop_actions="X", pf=pf, depth=depth)
        time.sleep(4.0)

        ip_cbet_code = None
        ip_cbet_rate = None
        ip_flop_rows = None

        if ip_flop_data:
            ip_p   = get_player(ip_flop_data, ip)
            isols  = ip_flop_data.get("action_solutions", [])
            icodes = classify_actions(isols) if isols else {}
            if ip_p and isols:
                ip_flop_rows = calc_hc_action_rates(isols, ip_p, icodes)
                bet_keys     = [k for k in icodes if k not in ("check", "fold")]
                ip_cbet_rate = weighted_rate(ip_flop_rows, bet_keys)
                ip_cbet_code = dominant_bet_code(icodes)
                print(f"\n  IP(BB) CBetコード: {icodes}  主要bet={ip_cbet_code}")
                pct = round(ip_cbet_rate * 100) if ip_cbet_rate is not None else "—"
                print(f"  IP(BB) CBet率（総合）: {pct}%")
                print_hc_table(ip_flop_rows, "hand_category別 BB CBet率（シェア付き）")

        # ── ターン比較 ──
        turn_results = []
        for turn_tag, turn_card, turn_desc in cfg["turns"]:
            board4 = flop + turn_card
            print(f"\n  ── [{turn_tag}] {turn_card} ({turn_desc}): board={board4}")

            # X-X後プローブ (OOP=SB先手)
            probe_data = call_api(board4, flop_actions="X-X", turn_actions="", pf=pf, depth=depth)
            time.sleep(4.0)
            probe_rate = None
            probe_rows = None
            if probe_data:
                oop_p  = get_player(probe_data, oop)
                psols  = probe_data.get("action_solutions", [])
                pcodes = classify_actions(psols) if psols else {}
                if oop_p and psols:
                    probe_rows = calc_hc_action_rates(psols, oop_p, pcodes)
                    bet_keys   = [k for k in pcodes if k not in ("check", "fold")]
                    probe_rate = weighted_rate(probe_rows, bet_keys)
                    pct = round(probe_rate * 100) if probe_rate is not None else "—"
                    print(f"    SB プローブ率: {pct}%")

            # 遅延CBet (X-X後OOPチェック→IP)
            delayed_data = call_api(board4, flop_actions="X-X", turn_actions="X", pf=pf, depth=depth)
            time.sleep(4.0)
            delayed_rate = None
            if delayed_data:
                ip_p   = get_player(delayed_data, ip)
                dsols  = delayed_data.get("action_solutions", [])
                dcodes = classify_actions(dsols) if dsols else {}
                if ip_p and dsols:
                    drows    = calc_hc_action_rates(dsols, ip_p, dcodes)
                    bet_keys = [k for k in dcodes if k not in ("check", "fold")]
                    delayed_rate = weighted_rate(drows, bet_keys)
                    pct = round(delayed_rate * 100) if delayed_rate is not None else "—"
                    print(f"    BB 遅延CBet率: {pct}%")

            turn_results.append({
                "tag": turn_tag, "card": turn_card, "desc": turn_desc,
                "sb_probe_pct":    round(probe_rate   * 100, 1) if probe_rate   is not None else None,
                "bb_delayed_pct":  round(delayed_rate * 100, 1) if delayed_rate is not None else None,
            })
            time.sleep(2.0)

        # ターンサマリー
        if turn_results:
            print(f"\n  ■ {cfg['type']} ターン比較")
            print(f"  {'ターン':5s}({'タグ':8s}) | {'SB プローブ':>12} | {'BB 遅延CBet':>12}")
            print(f"  {'-'*50}")
            for tr in turn_results:
                p = f"{round(tr['sb_probe_pct'])}%" if tr["sb_probe_pct"] is not None else "—"
                d = f"{round(tr['bb_delayed_pct'])}%" if tr["bb_delayed_pct"] is not None else "—"
                print(f"  {tr['card']:5s}({tr['tag'][:8]:8s}) | {p:>12} | {d:>12}")

        all_results.append({
            "type":               cfg["type"],
            "flop":               cfg["flop"],
            "desc":               cfg["desc"],
            "oop_cbet_code":      oop_cbet_code,
            "oop_cbet_rate_pct":  round(oop_cbet_rate * 100, 1) if oop_cbet_rate is not None else None,
            "ip_cbet_code":       ip_cbet_code,
            "ip_cbet_rate_pct":   round(ip_cbet_rate  * 100, 1) if ip_cbet_rate  is not None else None,
            "turns":              turn_results,
        })
        time.sleep(2.0)

    # 全体サマリー
    print("\n" + "=" * 70)
    print("★ 全体サマリー: SB(OOP) vs BB(IP) CBet率比較")
    print(f"  {'型':20s} | {'SB CBet%':>10} | {'BB CBet%':>10}")
    print(f"  {'-'*45}")
    for r in all_results:
        sb = f"{round(r['oop_cbet_rate_pct'])}%" if r["oop_cbet_rate_pct"] is not None else "—"
        bb = f"{round(r['ip_cbet_rate_pct'])}%"  if r["ip_cbet_rate_pct"]  is not None else "—"
        print(f"  {r['type']:20s} | {sb:>10} | {bb:>10}")

    out = {
        "scenario": SCENARIO["label"],
        "note": "SB is OOP preflop aggressor, BB is IP. Comparing CBet rates and probe patterns.",
        "results": all_results,
    }
    out_path = FINDINGS_DIR / "sb_bb_scenarios.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 完了 → {out_path}")


if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: TOKEN 環境変数が未設定")
        sys.exit(1)
    main()
