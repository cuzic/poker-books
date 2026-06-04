#!/usr/bin/env python3
"""
cash_spr.py — SPR・スタック深度比較

スタック深度を変えて同じシナリオを比較する:
  depth=50:  ショートスタック (SPR≒3)
  depth=100: 標準 (SPR≒6-7)
  depth=150: ディープスタック (SPR≒10)

収集データ:
  各深度でのフロップCBet率 by hand_category
  サイズ選択の変化（小サイズ→大サイズへのシフト）
  コール/フォールド境界の変化

使い方:
  TOKEN=eyJ... python3 cash_spr.py
  TOKEN=eyJ... DEPTHS=50,100 python3 cash_spr.py
"""

import os, sys, json, time, requests
from pathlib import Path

TOKEN      = os.environ.get("TOKEN", "")
GWCLIENTID = os.environ.get("GWCLIENTID", "")
GT         = os.environ.get("GT", "Cash6mGeneral_6mNL25R25")
DEPTHS_ENV = os.environ.get("DEPTHS", "50,100,150")

DEPTHS = [int(d.strip()) for d in DEPTHS_ENV.split(",") if d.strip().isdigit()]

FINDINGS_DIR = Path(__file__).parent / "findings"
FINDINGS_DIR.mkdir(exist_ok=True)

BASE_URL = "https://api.gtowizard.com/v4/solutions/spot-solution/"

# BTN_BB シナリオのみ
SCENARIO = {
    "label": "SRP BTN vs BB",
    "pf":    "F-F-F-R2.5-F-C",
    "ip":    "BTN",
    "oop":   "BB",
}

BOARD_CONFIGS = [
    {"type": "型1_ハイドライ",  "flop": "Ks7d2c", "desc": "K高・レインボー"},
    {"type": "型3_ロードライ",  "flop": "Jd7s5c", "desc": "J中・レインボー"},
    {"type": "型4_ローウェット","flop": "Th9s8d", "desc": "低連携・2トーン"},
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
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {TOKEN}",
        "origin": "https://app.gtowizard.com",
        "referer": "https://app.gtowizard.com/",
    }
    if GWCLIENTID:
        h["gwclientid"] = GWCLIENTID
    return h

def call_api(board, flop_actions="", turn_actions="", depth=100):
    params = {
        "gametype": GT, "depth": str(depth), "stacks": "",
        "preflop_actions": SCENARIO["pf"],
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
            print(f"  [HTTP 429] board={board} flop={flop_actions!r} depth={depth} → {wait}s 待機中...")
            time.sleep(wait)
            continue
        print(f"  [HTTP {r.status_code}] board={board} flop={flop_actions!r} depth={depth}")
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
    """コンボ加重平均ベット率（全カテゴリ統合）。ベット選択肢なしなら None。"""
    if not bet_keys or not rows:
        return None
    total_combos = sum(r["total"] for r in rows)
    if total_combos == 0:
        return None
    return sum(r["total"] * sum(r.get(k, 0) or 0 for k in bet_keys) for r in rows) / total_combos

def dominant_bet_size(codes):
    """主要ベットサイズ名を返す（最小サイズ優先）。"""
    for key in ["bet20", "bet33", "bet50", "bet75", "bet100", "betover"]:
        if key in codes:
            return key
    return None

def size_label(codes):
    """表示用サイズラベル文字列。複数サイズがあれば列挙。"""
    sizes = [k for k in ["bet20", "bet33", "bet50", "bet75", "bet100", "betover"] if k in codes]
    if not sizes:
        return "—"
    mapping = {"bet20": "20%", "bet33": "33%", "bet50": "50%",
               "bet75": "75%", "bet100": "100%", "betover": ">100%"}
    return "/".join(mapping[s] for s in sizes)

def weighted_fold_rate(rows, codes):
    """OOP コール/フォールド率（コンボ加重）。"""
    fold_code = codes.get("fold")
    call_code = codes.get("call")
    if not rows:
        return None, None
    total_combos = sum(r["total"] for r in rows)
    if total_combos == 0:
        return None, None
    fold_rate = (sum(r["total"] * r.get("fold", 0) for r in rows) / total_combos
                 if fold_code else None)
    call_rate = (sum(r["total"] * r.get("call", 0) for r in rows) / total_combos
                 if call_code else None)
    return fold_rate, call_rate

def print_hc_table(rows, header=""):
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


def analyze_depth(cfg, depth):
    """1ボード × 1深度の分析。(cbet_pct, size_label, oop_fold_pct, by_category) を返す。"""
    flop = cfg["flop"]

    # ── フロップ IP CBet（OOPチェック後）──
    cbet_data = call_api(flop, flop_actions="X", depth=depth)
    time.sleep(4.0)
    if not cbet_data:
        return None, None, None, []

    ip  = SCENARIO["ip"]
    oop = SCENARIO["oop"]

    ip_player = get_player(cbet_data, ip)
    cbet_sols  = cbet_data.get("action_solutions", [])
    if not ip_player or not cbet_sols:
        print(f"    [depth={depth}] IPデータなし")
        return None, None, None, []

    codes     = classify_actions(cbet_sols)
    rows      = calc_hc_action_rates(cbet_sols, ip_player, codes)
    bet_keys  = [k for k in codes if k not in ("check", "fold")]
    cbet_rate = weighted_bet_rate(rows, bet_keys)
    sz_label  = size_label(codes)

    # CBet コードを決定（dominant）
    cbet_code = None
    for key in ["bet33", "bet50", "bet75", "bet100", "betover", "bet20"]:
        if key in codes:
            cbet_code = codes[key]
            break

    oop_fold = None
    if cbet_code:
        # ── OOP ディフェンス（CBet後） ──
        def_data = call_api(flop, flop_actions=f"X-{cbet_code}", depth=depth)
        time.sleep(4.0)
        if def_data:
            oop_player = get_player(def_data, oop)
            def_sols   = def_data.get("action_solutions", [])
            if oop_player and def_sols:
                def_codes = classify_actions(def_sols)
                def_rows  = calc_hc_action_rates(def_sols, oop_player, def_codes)
                oop_fold, _ = weighted_fold_rate(def_rows, def_codes)

    # by_category: カテゴリ別 CBet 率（% 変換）
    by_cat = [
        {"hc": r["hc"], "total": r["total"], "share": r["share"],
         **{k: round(r[k] * 100, 1) for k in r if k not in ("hc", "total", "share")}}
        for r in rows
    ]

    return (
        round(cbet_rate * 100, 1) if cbet_rate is not None else None,
        sz_label,
        round(oop_fold * 100, 1) if oop_fold is not None else None,
        by_cat,
    )


def main():
    if not TOKEN:
        print("❌ TOKEN 未設定"); sys.exit(1)

    if not DEPTHS:
        print("❌ DEPTHS が不正。例: DEPTHS=50,100,150"); sys.exit(1)

    pf = SCENARIO["pf"]
    print(f"シナリオ: {SCENARIO['label']}  (IP={SCENARIO['ip']}, OOP={SCENARIO['oop']})")
    print(f"分析: SPR別フロップCBet率・サイズ・OOPフォールド率")
    print(f"深度: {DEPTHS}")
    print(f"gametype: {GT}\n")

    # 認証確認
    test = call_api("Ks7d2c", flop_actions="X", depth=100)
    if test is None:
        print("❌ 認証失敗"); sys.exit(1)
    time.sleep(4.0)
    print("✅ 認証OK\n")

    all_results = {}

    for cfg in BOARD_CONFIGS:
        btype = cfg["type"]
        flop  = cfg["flop"]
        print(f"\n{'='*70}")
        print(f"【{btype}】 {flop}  ({cfg['desc']})")

        depth_rows = {}

        for depth in DEPTHS:
            print(f"\n  ─ depth={depth}BB ─")
            cbet_pct, sz, oop_fold, by_cat = analyze_depth(cfg, depth)

            cbet_s = f"{cbet_pct:.0f}%" if cbet_pct is not None else "—"
            fold_s = f"{oop_fold:.0f}%" if oop_fold is not None else "—"
            print(f"    CBet率={cbet_s}  サイズ={sz}  OOP fold={fold_s}")

            depth_rows[depth] = {
                "depth":        depth,
                "cbet_pct":     cbet_pct,
                "size":         sz,
                "oop_fold_pct": oop_fold,
                "by_category":  by_cat,
            }

        # ─── ボード内サマリー表 ───
        print(f"\n  ■ {btype} サマリー")
        print(f"  {'depth':>7} | {'CBet%':>6} | {'サイズ':>10} | {'OOP fold%':>10}")
        print(f"  {'-'*45}")
        for d in DEPTHS:
            row = depth_rows[d]
            cb = f"{row['cbet_pct']:.0f}%" if row['cbet_pct'] is not None else "—"
            fo = f"{row['oop_fold_pct']:.0f}%" if row['oop_fold_pct'] is not None else "—"
            print(f"  {str(d)+'BB':>7} | {cb:>6} | {row['size']:>10} | {fo:>10}")

        all_results[btype] = {
            "type":   btype,
            "flop":   flop,
            "desc":   cfg["desc"],
            "depths": depth_rows,
        }
        time.sleep(2.0)

    # ─── 全体サマリー ───
    print(f"\n\n{'='*70}")
    print(f"★ 全体サマリー: depth別フロップCBet率")
    header = f"  {'型':20s}"
    for d in DEPTHS:
        header += f" | {str(d)+'BB CBet%':>12}"
    print(header)
    print(f"  {'-'*70}")
    for btype, res in all_results.items():
        line = f"  {btype:20s}"
        for d in DEPTHS:
            row = res["depths"].get(d, {})
            cb  = row.get("cbet_pct")
            line += f" | {'{}%'.format(round(cb)) if cb is not None else '—':>12}"
        print(line)

    # JSON 保存
    out = FINDINGS_DIR / "spr_comparison_BTN_BB.json"

    # depth_rows の key を str に変換（JSON serializable）
    serializable = {}
    for btype, res in all_results.items():
        serializable[btype] = {
            "type": res["type"],
            "flop": res["flop"],
            "desc": res["desc"],
            "depths": {str(k): v for k, v in res["depths"].items()},
        }

    with open(out, "w", encoding="utf-8") as f:
        json.dump(
            {"scenario": SCENARIO["label"], "depths_tested": DEPTHS, "results": serializable},
            f, ensure_ascii=False, indent=2,
        )
    print(f"\n✅ 完了 → {out}")


if __name__ == "__main__":
    main()
