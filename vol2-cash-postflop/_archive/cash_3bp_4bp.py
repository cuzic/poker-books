#!/usr/bin/env python3
"""
cash_3bp_4bp.py — 3BP・4BP後ポストフロップ分析

3BP (3-bet pot, SPR≒5-7):
  IP CBet vs OOP defense — hand_category別
  X-X後のプローブ/遅延CBet

4BP (4-bet pot, SPR≒2-3):
  スタックオフライン: どのhand_categoryでコミットするか

3BPシナリオ (CO vs BTN 3BP, BTN IP):
  pf = "F-F-R2.5-R9-F-F-C"  # CO opens, BTN 3bets, CO calls → BTN is IP
  ip = "BTN", oop = "CO"

4BPシナリオ (BTN vs BB 4BP):
  pf = "F-F-F-R2.5-F-R9-F-R22-C"  # BTN opens, BB 3bets, BTN 4bets, BB calls → BTN is IP
  ip = "BTN", oop = "BB", depth=100

使い方:
  TOKEN=eyJ... python3 cash_3bp_4bp.py
  TOKEN=eyJ... MODE=3bp python3 cash_3bp_4bp.py
  TOKEN=eyJ... MODE=4bp python3 cash_3bp_4bp.py
"""

import os, sys, json, time, requests
from pathlib import Path

TOKEN      = os.environ.get("TOKEN", "")
GWCLIENTID = os.environ.get("GWCLIENTID", "")
GT         = os.environ.get("GT", "Cash6mGeneral_6mNL25R25")
MODE       = os.environ.get("MODE", "all")   # "3bp", "4bp", or "all"

FINDINGS_DIR = Path(__file__).parent / "findings"
FINDINGS_DIR.mkdir(exist_ok=True)

BASE_URL = "https://api.gtowizard.com/v4/solutions/spot-solution/"

# ─────────────────── プリフロップシナリオ ───────────────────
SCENARIO_3BP = {
    "label": "3BP CO vs BTN (BTN is IP)",
    "pf":    "F-F-R2.5-R9-F-F-C",   # CO opens 2.5, BTN 3bets to 9, CO calls
    "ip":    "BTN",
    "oop":   "CO",
    "depth": 100,
    "spr_approx": "5-7",
}

SCENARIO_4BP = {
    "label": "4BP BTN vs BB (BTN is IP)",
    "pf":    "F-F-F-R2.5-F-R9-F-R22-C",  # BTN opens 2.5, BB 3bets to 9, BTN 4bets to 22, BB calls
    "ip":    "BTN",
    "oop":   "BB",
    "depth": 100,
    "spr_approx": "2-3",
}

# ─────────────────── ボード設定 ───────────────────
# 3BP と 4BP で共通して使う 3 型
BOARD_CONFIGS = [
    {
        "type":  "型1_ハイドライ",
        "flop":  "Ks7d2c",
        "desc":  "K高・レインボー",
        "turns": [
            ("blank",    "4c", "ブランク"),
            ("TA+_2nd",  "7h", "2ndカードペア"),
            ("TA-_OC",   "Ah", "オーバーカード(A)"),
        ],
    },
    {
        "type":  "型3_ロードライ",
        "flop":  "Jd7s5c",
        "desc":  "J中・レインボー",
        "turns": [
            ("blank",    "2c", "ブランク"),
            ("TA+_2nd",  "7h", "2ndカードペア"),
            ("TA-_OC",   "Ah", "オーバーカード(A)"),
        ],
    },
    {
        "type":  "型4_ローウェット",
        "flop":  "Th9s8d",
        "desc":  "低連携・2トーン",
        "turns": [
            ("blank",    "2c", "ブランク"),
            ("danger",   "6c", "SC(低)"),
            ("danger",   "7c", "SC(高)"),
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

# ─────────────────── ユーティリティ ───────────────────

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


def call_api(board, flop_actions="", turn_actions="", pf="", depth=100):
    params = {
        "gametype": GT, "depth": str(depth), "stacks": "",
        "preflop_actions": pf,
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
        if   t == "CHECK": codes["check"]   = c
        elif t == "FOLD":  codes["fold"]    = c
        elif t == "CALL":  codes["call"]    = c
        elif t == "RAISE":
            if   bp < 0.25: codes["bet20"]   = c
            elif bp < 0.40: codes["bet33"]   = c
            elif bp < 0.65: codes["bet50"]   = c
            elif bp < 0.90: codes["bet75"]   = c
            elif bp < 1.20: codes["bet100"]  = c
            elif bp < 3.00: codes["betover"] = c
            else:           codes["allin"]   = c
    return codes


def dominant_bet_code(codes):
    for key in ["allin", "betover", "bet100", "bet75", "bet50", "bet33", "bet20"]:
        if key in codes:
            return codes[key]
    return None


def calc_hc_action_rates(sols, player, codes):
    """hand_category 別行動率 + レンジシェア(%) を返す。"""
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


def weighted_action_rate(rows, keys):
    """コンボ加重平均アクション率。アクションがなければ None。"""
    if not keys or not rows:
        return None
    total_combos = sum(r["total"] for r in rows)
    if total_combos == 0:
        return None
    return sum(r["total"] * sum(r.get(k, 0) or 0 for k in keys) for r in rows) / total_combos


def print_hc_table(rows, header=""):
    """hand_category 別行動率テーブル表示（レンジシェア列付き）。"""
    if not rows:
        return
    keys = [k for k in rows[0] if k not in ("hc", "total", "share")]
    if header:
        print(f"\n  {header}")
    col_hdr = f"  {'カテゴリ':22s} {'コンボ':>6} {'シェア':>6}"
    for k in keys:
        col_hdr += f" {k:>8}"
    print(col_hdr)
    print(f"  {'-'*76}")
    for row in rows:
        line = f"  {row['hc']:22s} {row['total']:6.1f} {row['share']:5.1f}%"
        for k in keys:
            v = row.get(k)
            line += f" {v*100:7.0f}%" if v is not None else f"  {'—':>7}"
        print(line)


def rows_to_store(rows, codes_dict):
    """JSON保存用: 行動率を%値に変換し、主要列のみ保持。"""
    if not rows:
        return []
    bet_keys = [k for k in codes_dict if k not in ("fold",)]
    return [
        {k: (round(v * 100, 1) if isinstance(v, float) else v)
         for k, v in row.items()
         if k in ("hc", "total", "share") or k in bet_keys}
        for row in rows
    ]


def query_spot(board, flop_actions, turn_actions, actor_pos, pf, depth, label):
    """APIを叩いて (codes, rows, total_bet_rate) を返す。失敗時は全 None。"""
    data = call_api(board, flop_actions=flop_actions, turn_actions=turn_actions,
                    pf=pf, depth=depth)
    time.sleep(4.0)
    if not data:
        print(f"    [{label}] データ取得失敗")
        return None, None, None
    player = get_player(data, actor_pos)
    sols   = data.get("action_solutions", [])
    if not player or not sols:
        print(f"    [{label}] プレイヤーデータなし (pos={actor_pos})")
        return None, None, None
    codes     = classify_actions(sols)
    rows      = calc_hc_action_rates(sols, player, codes)
    bet_keys  = [k for k in codes if k not in ("check", "fold")]
    total_bet = weighted_action_rate(rows, bet_keys)
    return codes, rows, total_bet


# ═══════════════════════════════════════════════════════════════
# 3BP 分析
# ═══════════════════════════════════════════════════════════════

def run_3bp():
    scen  = SCENARIO_3BP
    pf    = scen["pf"]
    ip    = scen["ip"]
    oop   = scen["oop"]
    depth = scen["depth"]

    print(f"\n{'#'*70}")
    print(f"# 3BP 分析: {scen['label']}")
    print(f"# SPR≒{scen['spr_approx']}  pf={pf}")
    print(f"# gametype: {GT}")
    print(f"{'#'*70}")

    # 認証確認
    test = call_api("Ks7d2c", flop_actions="", pf=pf, depth=depth)
    if test is None:
        print("❌ 認証失敗"); return None
    print("✅ 認証OK\n")

    all_results = []

    for cfg in BOARD_CONFIGS:
        flop = cfg["flop"]
        print(f"\n{'='*70}")
        print(f"【{cfg['type']}】 {flop}  ({cfg['desc']})")

        # ── フロップ IP CBet ──
        cbet_codes, cbet_rows, ip_cbet = query_spot(
            flop, "", "", ip, pf, depth, "IP CBet")
        if ip_cbet is not None:
            print(f"  IP CBet 率（総合）: {ip_cbet*100:.0f}%")
            print_hc_table(cbet_rows, "hand_category別 CBet率（シェア付き）")
        else:
            print(f"  IP CBet: 取得失敗")

        # ── フロップ OOP Defense (vs CBet) ──
        # CBetコードが取れていれば、そのコードに対するOOPのレスポンスを取得
        cbet_code = dominant_bet_code(cbet_codes or {})
        oop_def_codes, oop_def_rows, oop_def_rate = None, None, None
        if cbet_code:
            oop_def_codes, oop_def_rows, oop_def_rate = query_spot(
                flop, cbet_code, "", oop, pf, depth, "OOP Defense")
            if oop_def_rate is not None:
                print(f"  OOP コール/レイズ率（総合）: {oop_def_rate*100:.0f}%")
                print_hc_table(oop_def_rows, "hand_category別 OOP Defense（シェア付き）")
            else:
                print(f"  OOP Defense: 取得失敗")

        # ── X-X 後のターン行動 ──
        print(f"\n  ── X-X 後のターン分析 ──")
        turn_results = []

        for turn_tag, turn_card, turn_desc in cfg["turns"]:
            board4 = flop + turn_card
            print(f"\n  [{turn_tag}] {turn_card} ({turn_desc}): board={board4}")

            # OOP プローブ
            _, probe_rows, oop_probe = query_spot(
                board4, "X-X", "", oop, pf, depth, "OOP probe")
            if oop_probe is not None:
                print(f"    OOP プローブ: {oop_probe*100:.0f}%")
            else:
                print(f"    OOP プローブ: 取得失敗 or チェックのみ")

            # IP 遅延CBet
            _, dcbet_rows, ip_delayed = query_spot(
                board4, "X-X", "X", ip, pf, depth, "IP delayed CBet")
            if ip_delayed is not None:
                print(f"    IP 遅延CBet: {ip_delayed*100:.0f}%")
            else:
                print(f"    IP 遅延CBet: 取得失敗 or チェックのみ")

            turn_results.append({
                "tag":  turn_tag,
                "card": turn_card,
                "desc": turn_desc,
                "oop_probe_pct":   round(oop_probe * 100, 1)  if oop_probe  is not None else None,
                "ip_delayed_pct":  round(ip_delayed * 100, 1) if ip_delayed is not None else None,
                "oop_probe_by_cat":  rows_to_store(probe_rows  or [], {k: k for k in (probe_rows[0] if probe_rows else {})}),
                "ip_delayed_by_cat": rows_to_store(dcbet_rows  or [], {k: k for k in (dcbet_rows[0]  if dcbet_rows  else {})}),
            })
            time.sleep(2.0)

        # ターンサマリー
        if turn_results:
            print(f"\n  ■ {cfg['type']} ターン比較（コンボ加重総合ベット率）")
            print(f"  {'ターン':5s}({'タグ':10s}) | {'OOP probe':>10} | {'IP delayed':>10}")
            print(f"  {'-'*50}")
            for tr in turn_results:
                op = tr["oop_probe_pct"]
                dc = tr["ip_delayed_pct"]
                print(f"  {tr['card']:5s}({tr['tag'][:10]:10s}) | "
                      f"{str(round(op))+'%' if op is not None else '—':>10} | "
                      f"{str(round(dc))+'%' if dc is not None else '—':>10}")

        all_results.append({
            "type":  cfg["type"],
            "flop":  flop,
            "desc":  cfg["desc"],
            "flop_cbet": {
                "total_pct":  round(ip_cbet * 100, 1) if ip_cbet is not None else None,
                "cbet_code":  cbet_code,
                "by_category": rows_to_store(cbet_rows or [], cbet_codes or {}),
            },
            "flop_oop_defense": {
                "total_pct":  round(oop_def_rate * 100, 1) if oop_def_rate is not None else None,
                "by_category": rows_to_store(oop_def_rows or [], oop_def_codes or {}),
            },
            "turns_after_xx": turn_results,
        })
        time.sleep(2.0)

    # 全体サマリー
    print(f"\n\n{'='*70}")
    print(f"★ 3BP 全体サマリー: フロップCBet率")
    print(f"  {'型':20s} | {'IP CBet%':>9} | {'OOP Def%':>9}")
    print(f"  {'-'*45}")
    for r in all_results:
        cb = r["flop_cbet"]["total_pct"]
        df = r["flop_oop_defense"]["total_pct"]
        print(f"  {r['type']:20s} | "
              f"{str(round(cb))+'%' if cb is not None else '—':>9} | "
              f"{str(round(df))+'%' if df is not None else '—':>9}")

    return {
        "scenario":    scen["label"],
        "preflop":     pf,
        "ip":          ip,
        "oop":         oop,
        "spr_approx":  scen["spr_approx"],
        "results":     all_results,
    }


# ═══════════════════════════════════════════════════════════════
# 4BP 分析
# ═══════════════════════════════════════════════════════════════

def run_4bp():
    scen  = SCENARIO_4BP
    pf    = scen["pf"]
    ip    = scen["ip"]
    oop   = scen["oop"]
    depth = scen["depth"]

    print(f"\n{'#'*70}")
    print(f"# 4BP 分析: {scen['label']}")
    print(f"# SPR≒{scen['spr_approx']}  pf={pf}")
    print(f"# gametype: {GT}")
    print(f"{'#'*70}")
    print(f"# NOTE: SPR≒2-3 のため、オールイン（スタックオフ）頻度に注目")
    print(f"{'#'*70}")

    # 認証確認
    test = call_api("Ks7d2c", flop_actions="", pf=pf, depth=depth)
    if test is None:
        print("❌ 認証失敗"); return None
    print("✅ 認証OK\n")

    all_results = []

    for cfg in BOARD_CONFIGS:
        flop = cfg["flop"]
        print(f"\n{'='*70}")
        print(f"【{cfg['type']}】 {flop}  ({cfg['desc']})")

        # ── フロップ IP 先手（X or ベット — SPR低いのでオールイン多い）──
        ip_codes, ip_rows, ip_bet = query_spot(
            flop, "", "", ip, pf, depth, "IP フロップ先手")
        allin_keys = [k for k in (ip_codes or {}) if k in ("allin", "betover")]
        ip_allin   = weighted_action_rate(ip_rows or [], allin_keys)
        if ip_bet is not None:
            print(f"  IP ベット率（総合）: {ip_bet*100:.0f}%  オールイン: "
                  f"{ip_allin*100:.0f}%" if ip_allin is not None else f"  IP ベット率（総合）: {ip_bet*100:.0f}%")
            print_hc_table(ip_rows, "hand_category別 IP アクション（シェア付き）")
        else:
            print(f"  IP フロップ先手: 取得失敗")

        # ── OOP Defense vs IP Bet ──
        ip_bet_code = dominant_bet_code(ip_codes or {})
        oop_def_codes, oop_def_rows, oop_def_rate = None, None, None
        oop_allin_rate = None
        if ip_bet_code:
            oop_def_codes, oop_def_rows, oop_def_rate = query_spot(
                flop, ip_bet_code, "", oop, pf, depth, "OOP Defense")
            oop_allin_keys = [k for k in (oop_def_codes or {}) if k in ("allin", "betover")]
            oop_allin_rate = weighted_action_rate(oop_def_rows or [], oop_allin_keys)
            if oop_def_rate is not None:
                print(f"  OOP コール/レイズ率（総合）: {oop_def_rate*100:.0f}%  オールイン: "
                      f"{oop_allin_rate*100:.0f}%" if oop_allin_rate is not None
                      else f"  OOP コール/レイズ率（総合）: {oop_def_rate*100:.0f}%")
                print_hc_table(oop_def_rows, "hand_category別 OOP Defense（シェア付き）")

        # ── フロップ X → IP bet（チェック後のオールイン確認）──
        xbet_codes, xbet_rows, xbet_rate = query_spot(
            flop, "X", "", ip, pf, depth, "IP X後ベット")
        xbet_allin_keys = [k for k in (xbet_codes or {}) if k in ("allin", "betover")]
        xbet_allin = weighted_action_rate(xbet_rows or [], xbet_allin_keys)
        if xbet_rate is not None:
            print(f"  IP X後ベット率（総合）: {xbet_rate*100:.0f}%  オールイン: "
                  f"{xbet_allin*100:.0f}%" if xbet_allin is not None
                  else f"  IP X後ベット率（総合）: {xbet_rate*100:.0f}%")
            print_hc_table(xbet_rows, "hand_category別 X後ベット（シェア付き）")

        all_results.append({
            "type":  cfg["type"],
            "flop":  flop,
            "desc":  cfg["desc"],
            "ip_flop_first": {
                "total_bet_pct":   round(ip_bet * 100, 1)   if ip_bet   is not None else None,
                "total_allin_pct": round(ip_allin * 100, 1) if ip_allin is not None else None,
                "dominant_code":   ip_bet_code,
                "by_category":     rows_to_store(ip_rows or [], ip_codes or {}),
            },
            "oop_defense": {
                "total_pct":     round(oop_def_rate  * 100, 1) if oop_def_rate  is not None else None,
                "allin_pct":     round(oop_allin_rate * 100, 1) if oop_allin_rate is not None else None,
                "by_category":   rows_to_store(oop_def_rows or [], oop_def_codes or {}),
            },
            "ip_after_check": {
                "total_bet_pct":   round(xbet_rate  * 100, 1) if xbet_rate  is not None else None,
                "total_allin_pct": round(xbet_allin * 100, 1) if xbet_allin is not None else None,
                "by_category":     rows_to_store(xbet_rows or [], xbet_codes or {}),
            },
        })
        time.sleep(2.0)

    # 全体サマリー
    print(f"\n\n{'='*70}")
    print(f"★ 4BP 全体サマリー: スタックオフ（オールイン）率")
    print(f"  {'型':20s} | {'IP bet%':>8} | {'IP AI%':>7} | {'OOP AI%':>8}")
    print(f"  {'-'*52}")
    for r in all_results:
        ib = r["ip_flop_first"]["total_bet_pct"]
        ia = r["ip_flop_first"]["total_allin_pct"]
        oa = r["oop_defense"]["allin_pct"]
        print(f"  {r['type']:20s} | "
              f"{str(round(ib))+'%' if ib is not None else '—':>8} | "
              f"{str(round(ia))+'%' if ia is not None else '—':>7} | "
              f"{str(round(oa))+'%' if oa is not None else '—':>8}")

    return {
        "scenario":   scen["label"],
        "preflop":    pf,
        "ip":         ip,
        "oop":        oop,
        "spr_approx": scen["spr_approx"],
        "note":       "SPR≒2-3: allin/betover が実質スタックオフ。betover は通常 AI相当。",
        "results":    all_results,
    }


# ═══════════════════════════════════════════════════════════════
# メイン
# ═══════════════════════════════════════════════════════════════

def main():
    if not TOKEN:
        print("❌ TOKEN 未設定"); sys.exit(1)

    if MODE not in ("3bp", "4bp", "all"):
        print(f"❌ 未知 MODE: {MODE}. 選択肢: 3bp / 4bp / all"); sys.exit(1)

    output = {}

    if MODE in ("3bp", "all"):
        res_3bp = run_3bp()
        if res_3bp:
            output["3bp"] = res_3bp

    if MODE in ("4bp", "all"):
        res_4bp = run_4bp()
        if res_4bp:
            output["4bp"] = res_4bp

    out_path = FINDINGS_DIR / "3bp_4bp_BTN_BB.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 完了 → {out_path}")


if __name__ == "__main__":
    main()
