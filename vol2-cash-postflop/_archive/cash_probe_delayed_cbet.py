#!/usr/bin/env python3
"""
cash_probe_delayed_cbet.py — プローブ＆遅延CBet GTO分析

フロップ両チェック（X-X）後のターン行動を収集する：
  1. OOP プローブ: フロップX-X後、OOPがターン先手（空振りCBet = probe bet）
  2. IP 遅延CBet: フロップX-X後、OOPがチェック→IPがターンベット

既存の cash_multistreet.py が収集していない X-X ライン特有のデータ。

使い方:
  TOKEN=eyJ... python3 cash_probe_delayed_cbet.py
  TOKEN=eyJ... SCENARIO=CO_BB python3 cash_probe_delayed_cbet.py
  TOKEN=eyJ... TYPE=型1 python3 cash_probe_delayed_cbet.py     # 特定型のみ
  TOKEN=eyJ... TURNS=0 python3 cash_probe_delayed_cbet.py      # ターン詳細をスキップ
"""

import os, sys, json, time, requests
from pathlib import Path

TOKEN       = os.environ.get("TOKEN", "")
GWCLIENTID  = os.environ.get("GWCLIENTID", "")
GT          = os.environ.get("GT", "Cash6mGeneral_6mNL25R25")
SCENARIO    = os.environ.get("SCENARIO", "BTN_BB")
TYPE_FILTER = os.environ.get("TYPE", "")
SKIP_TURNS  = os.environ.get("TURNS", "1") == "0"

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
        "ip":    "BB",   # postflop IP = BB
        "oop":   "SB",
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
            ("blank",    "4c", "ブランク"),
            ("TA+_2nd",  "7h", "2ndカードペア"),
            ("TA+_3rd",  "2s", "3rdカードペア"),
            ("TA-_OC",   "Ah", "オーバーカード(A)"),
        ],
    },
    {
        "type":  "型2_ハイウェット",
        "flop":  "Qh8d3s",
        "desc":  "Q高・2トーン",
        "turns": [
            ("blank",    "5d", "ブランク"),
            ("TA+_2nd",  "8c", "2ndカードペア"),
            ("TA+_3rd",  "3d", "3rdカードペア"),
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
            ("TA+_3rd",  "5h", "3rdカードペア"),
            ("TA-_OC",   "Ah", "オーバーカード(A)"),
        ],
    },
    {
        "type":  "型4_ローウェット",
        "flop":  "Th9s8d",
        "desc":  "低連携・2トーン",
        "turns": [
            ("blank",    "2c", "ブランク"),
            ("TA+_pair", "Th", "1stカードペア"),
            ("danger",   "6c", "SC(低)"),
            ("danger",   "7c", "SC(高)"),
        ],
    },
    {
        "type":  "型5_モノトーン",
        "flop":  "Ah9h5h",
        "desc":  "A高モノトーン",
        "turns": [
            ("blank",    "2c", "ブランク(非ハート)"),
            ("TA+_2nd",  "9d", "2ndカードペア(非ハート)"),
            ("danger",   "4h", "FC(4thハート)"),
            ("TA-_OC",   "Kd", "オーバーカード(非ハート)"),
        ],
    },
    {
        "type":  "型6_ペア高",
        "flop":  "AsAcKd",
        "desc":  "AAKペアボード",
        "turns": [
            ("blank",    "2c", "ブランク"),
            ("TA+_3rd",  "Ks", "3rdカードペア(K)"),
            ("TA-_OC",   "Qd", "準OC(Q)"),
            ("danger",   "Jd", "J絡み"),
        ],
    },
    {
        "type":  "型7_ペア低",
        "flop":  "7s7d2c",
        "desc":  "77低ペアボード",
        "turns": [
            ("blank",    "3c", "ブランク"),
            ("TA+_3rd",  "2h", "3rdカードペア(2)"),
            ("TA-_OC",   "Ah", "OC(A)"),
            ("TA-_OC2",  "Kh", "OC(K)"),
        ],
    },
]

# 表示順序のためのソートキー（絶対HS値ではなくカテゴリ名→順位のマッピング）
# ※ボードによってこの順序が適切でない場合があるが、GTO Wizardのカテゴリ名に従う
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
    """コンボ加重平均ベット率（全カテゴリ統合）。ベット選択肢なしなら None。"""
    if not bet_keys or not rows:
        return None
    total_combos = sum(r["total"] for r in rows)
    if total_combos == 0:
        return None
    weighted = sum(r["total"] * sum(r.get(k, 0) or 0 for k in bet_keys) for r in rows)
    return weighted / total_combos

def query_and_extract(board, flop_actions, turn_actions, actor_pos, pf, depth, label):
    """APIを叩いて (codes, rows, total_bet_rate) を返す。
    total_bet_rate: コンボ加重ベット率 (0-1)。ベット不可なら None。失敗なら全 None。
    """
    data = call_api(board, flop_actions=flop_actions, turn_actions=turn_actions,
                    pf=pf, depth=depth)
    time.sleep(4.0)
    if not data:
        return None, None, None
    player = get_player(data, actor_pos)
    sols   = data.get("action_solutions", [])
    if not player or not sols:
        print(f"    [{label}] プレイヤーデータなし (pos={actor_pos})")
        return None, None, None
    codes     = classify_actions(sols)
    rows      = calc_hc_action_rates(sols, player, codes)
    bet_keys  = [k for k in codes if k not in ("check", "fold")]
    total_bet = weighted_bet_rate(rows, bet_keys)
    return codes, rows, total_bet

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
    print(f"分析: フロップ X-X 後のターン行動（プローブ＆遅延CBet）")
    print(f"gametype: {GT}\n")

    # 認証確認（ターンクエリには4枚ボードが必要）
    test = call_api("Ks7d2c4c", flop_actions="X-X", turn_actions="", pf=pf, depth=depth)
    if test is None:
        print("❌ 認証失敗"); sys.exit(1)
    print("✅ 認証OK\n")

    all_results = []
    configs = [c for c in BOARD_CONFIGS if not TYPE_FILTER or c["type"] == TYPE_FILTER]

    for cfg in configs:
        flop = cfg["flop"]
        print(f"\n{'='*70}")
        print(f"【{cfg['type']}】 {flop}  ({cfg['desc']})")

        turn_results = []

        turns_to_run = [cfg["turns"][0]] if SKIP_TURNS else cfg["turns"]
        if SKIP_TURNS:
            print(f"\n  (TURNS=0 モード: {cfg['turns'][0][1]} のみ確認)")

        for turn_tag, turn_card, turn_desc in turns_to_run:
            board4 = flop + turn_card
            if not SKIP_TURNS:
                print(f"\n  ── [{turn_tag}] {turn_card} ({turn_desc}): board={board4}")

            # ─── OOP プローブ ───
            codes_p, rows_p, oop_probe = query_and_extract(
                board4, "X-X", "", oop, pf, depth, "OOP probe")
            if oop_probe is not None:
                print(f"    OOP プローブ: 総合{oop_probe*100:.0f}%")
                if rows_p and not SKIP_TURNS:
                    print_hc_table(rows_p, "hand_category別プローブ率（シェア付き）")
            elif codes_p is not None:
                print(f"    OOP プローブ: チェックのみ")
            else:
                print(f"    OOP プローブ: 取得失敗")

            # ─── IP 遅延CBet ───
            codes_d, rows_d, ip_delayed = query_and_extract(
                board4, "X-X", "X", ip, pf, depth, "IP delayed CBet")
            if ip_delayed is not None:
                print(f"    IP 遅延CBet: 総合{ip_delayed*100:.0f}%")
                if rows_d and not SKIP_TURNS:
                    print_hc_table(rows_d, "hand_category別遅延CBet率（シェア付き）")
            elif codes_d is not None:
                print(f"    IP 遅延CBet: チェックのみ")
            else:
                print(f"    IP 遅延CBet: 取得失敗")

            # JSON用: カテゴリ別詳細 + 加重総合率を保存
            def rows_to_store(rows, bet_keys):
                if not rows:
                    return []
                return [
                    {k: (round(v * 100, 1) if isinstance(v, float) else v)
                     for k, v in row.items()
                     if k in ("hc", "total", "share") or k in bet_keys or k == "check"}
                    for row in rows
                ]

            bet_keys_p = [k for k in (codes_p or {}) if k not in ("check", "fold")]
            bet_keys_d = [k for k in (codes_d or {}) if k not in ("check", "fold")]

            turn_results.append({
                "tag":  turn_tag, "card": turn_card, "desc": turn_desc,
                "oop_probe": {
                    "total_bet_pct": round(oop_probe * 100, 1) if oop_probe is not None else None,
                    "bet_codes": bet_keys_p,
                    "by_category": rows_to_store(rows_p, bet_keys_p),
                },
                "ip_delayed_cbet": {
                    "total_bet_pct": round(ip_delayed * 100, 1) if ip_delayed is not None else None,
                    "bet_codes": bet_keys_d,
                    "by_category": rows_to_store(rows_d, bet_keys_d),
                },
            })
            time.sleep(2.0)

        # ─── ターンサマリー ───
        if turn_results:
            print(f"\n  ■ {cfg['type']} ターン比較サマリー（コンボ加重総合ベット率）")
            print(f"  {'ターン':5s}({'タグ':10s}) | {'OOP probe':>10} | {'IP delayed':>10}")
            print(f"  {'-'*48}")
            for tr in turn_results:
                op = tr["oop_probe"]["total_bet_pct"]
                dc = tr["ip_delayed_cbet"]["total_bet_pct"]
                op_s = f"{op:.0f}%" if op is not None else "—"
                dc_s = f"{dc:.0f}%" if dc is not None else "—"
                print(f"  {tr['card']:5s}({tr['tag'][:10]:10s}) | {op_s:>10} | {dc_s:>10}")

        all_results.append({
            "type":  cfg["type"],
            "flop":  flop,
            "desc":  cfg["desc"],
            "turns": turn_results,
        })
        time.sleep(2.0)

    # ─── 全体サマリー ───
    print(f"\n\n{'='*70}")
    print(f"★ 全体サマリー: コンボ加重総合ベット率")
    print(f"  {'型':20s} | {'ターン':5s}({'タグ':10s}) | {'OOP probe%':>11} | {'IP delayed%':>11}")
    print(f"  {'-'*65}")
    for r in all_results:
        for tr in r["turns"]:
            op = tr["oop_probe"]["total_bet_pct"]
            dc = tr["ip_delayed_cbet"]["total_bet_pct"]
            op_s = f"{op:.0f}%" if op is not None else "—"
            dc_s = f"{dc:.0f}%" if dc is not None else "—"
            print(f"  {r['type']:20s} | {tr['card']:5s}({tr['tag'][:10]:10s}) | {op_s:>11} | {dc_s:>11}")

    # JSON 保存
    out = FINDINGS_DIR / f"probe_delayed_{SCENARIO}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"scenario": scen["label"], "results": all_results},
                  f, ensure_ascii=False, indent=2)
    print(f"\n✅ 完了 → {out}")


if __name__ == "__main__":
    main()
