#!/usr/bin/env python3
"""
cash_range_share.py — IP/OOP レンジシェア比較

フロップでIPとOOPのレンジ構成を比較する:
  - 各hand_categoryのシェア（%）を両プレイヤーで比較
  - 誰がこのボードで優位か（レンジアドバンテージ）
  - ナットアドバンテージ: 上位カテゴリのシェア差

これは理論的なレンジ比較（アクション分析ではなく分布分析）。

使い方:
  TOKEN=eyJ... python3 cash_range_share.py
"""

import os, sys, json, time, requests
from pathlib import Path

TOKEN          = os.environ.get("TOKEN", "")
GWCLIENTID     = os.environ.get("GWCLIENTID", "")
GOOGLE_ANAL_ID = os.environ.get("GOOGLE_ANAL_ID", "")
GT             = os.environ.get("GT", "Cash6mGeneral_6mNL25R25")

FINDINGS_DIR = Path(__file__).parent / "findings"
FINDINGS_DIR.mkdir(exist_ok=True)

BASE_URL = "https://api.gtowizard.com/v4/solutions/spot-solution/"

SCENARIO = {
    "label": "SRP BTN vs BB",
    "pf":    "F-F-F-R2.5-F-C",
    "ip":    "BTN",
    "oop":   "BB",
    "depth": 100,
}

# 全7型
BOARD_CONFIGS = [
    {"type": "型1_ハイドライ",  "flop": "Ks7d2c", "desc": "K高・レインボー"},
    {"type": "型2_ハイウェット","flop": "Qh8d3s", "desc": "Q高・2トーン"},
    {"type": "型3_ロードライ",  "flop": "Jd7s5c", "desc": "J中・レインボー"},
    {"type": "型4_ローウェット","flop": "Th9s8d", "desc": "低連携・2トーン"},
    {"type": "型5_モノトーン",  "flop": "Ah9h5h", "desc": "A高モノトーン"},
    {"type": "型6_ペア高",      "flop": "AsAcKd", "desc": "AAKペアボード"},
    {"type": "型7_ペア低",      "flop": "7s7d2c", "desc": "77低ペアボード"},
]

HC_SORT = {
    "straight_flush": 97, "quads": 93, "fullhouse": 89, "flush": 83, "straight": 80,
    "set": 85, "two_pair": 77, "trips": 74, "overpair": 70, "top_pair": 60,
    "underpair": 42, "second_pair": 43, "third_pair": 35, "low_pair": 30,
    "ace_high": 24, "king_high": 21, "queen_high": 19, "jack_high": 17,
    "ten_high": 15, "no_made_hand": 12,
}

# ナットアドバンテージ計算に使う「上位」カテゴリ
NUT_CATEGORIES = {"straight_flush", "quads", "fullhouse", "flush", "straight", "set", "two_pair", "trips", "overpair"}

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

def call_api(board, flop_actions=""):
    params = {
        "gametype": GT, "depth": str(SCENARIO["depth"]), "stacks": "",
        "preflop_actions": SCENARIO["pf"],
        "flop_actions": flop_actions,
        "turn_actions": "",
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
            print(f"  [HTTP 429] board={board} flop={flop_actions!r} → {wait}s 待機中...")
            time.sleep(wait)
            continue
        print(f"  [HTTP {r.status_code}] board={board} flop={flop_actions!r}")
        return None
    print(f"  [429 最大リトライ超過] board={board}")
    return None

def get_player(data, pos):
    for p in data.get("players_info", []):
        if isinstance(p.get("player"), dict) and p["player"].get("position") == pos:
            return p
    return None

def extract_range(player):
    """players_info エントリから hand_category リストを抽出・整形。"""
    if not player:
        return []
    cats = player.get("hand_categories", [])
    total_combos = sum(h["total_combos"] for h in cats if h["total_combos"] >= 0.3)
    rows = []
    for h in sorted(cats, key=lambda x: -HC_SORT.get(x["name"], 50)):
        tc = h["total_combos"]
        if tc < 0.3:
            continue
        share = round(tc / total_combos * 100, 2) if total_combos > 0 else 0.0
        rows.append({"hc": h["name"], "combos": round(tc, 1), "share": share})
    return rows

def calc_nut_share(range_rows):
    """上位カテゴリの合計シェアを返す。"""
    return round(sum(r["share"] for r in range_rows if r["hc"] in NUT_CATEGORIES), 2)

def calc_top3_share(range_rows):
    """set + two_pair + overpair のシェア合計。"""
    top3 = {"set", "two_pair", "overpair"}
    return round(sum(r["share"] for r in range_rows if r["hc"] in top3), 2)

def print_range_table(ip_rows, oop_rows, board_type):
    """IP vs OOP レンジシェア対比テーブルを表示。"""
    # hc ごとに両プレイヤーの値をマージ
    all_hc = sorted(
        set(r["hc"] for r in ip_rows) | set(r["hc"] for r in oop_rows),
        key=lambda x: -HC_SORT.get(x, 50),
    )
    ip_map  = {r["hc"]: r for r in ip_rows}
    oop_map = {r["hc"]: r for r in oop_rows}

    print(f"\n  {'カテゴリ':22s} {'IP combos':>10} {'IP share':>9} | {'OOP combos':>11} {'OOP share':>10}")
    print(f"  {'-'*72}")
    for hc in all_hc:
        ip_r  = ip_map.get(hc,  {"combos": 0.0, "share": 0.0})
        oop_r = oop_map.get(hc, {"combos": 0.0, "share": 0.0})
        print(f"  {hc:22s} {ip_r['combos']:10.1f} {ip_r['share']:8.1f}% | "
              f"{oop_r['combos']:11.1f} {oop_r['share']:9.1f}%")


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

    ip  = SCENARIO["ip"]
    oop = SCENARIO["oop"]
    print(f"シナリオ: {SCENARIO['label']}  (IP={ip}, OOP={oop}, depth={SCENARIO['depth']}BB)")
    print(f"分析: フロップ IP/OOP レンジシェア比較（ナットアドバンテージ）")
    print(f"gametype: {GT}\n")

    check_token()
    time.sleep(2.0)

    all_results = {}

    for cfg in BOARD_CONFIGS:
        btype = cfg["type"]
        flop  = cfg["flop"]
        print(f"\n{'='*70}")
        print(f"【{btype}】 {flop}  ({cfg['desc']})")

        # OOP が先手なので flop_actions="" でクエリ
        data = call_api(flop, flop_actions="")
        time.sleep(4.0)

        if not data:
            print("  データ取得失敗")
            all_results[btype] = {
                "type": btype, "flop": flop, "desc": cfg["desc"],
                "ip_range": [], "oop_range": [],
                "range_advantage": None, "nut_advantage_score": None,
            }
            continue

        ip_player  = get_player(data, ip)
        oop_player = get_player(data, oop)

        if not ip_player or not oop_player:
            print(f"  プレイヤーデータなし (ip={ip_player is not None}, oop={oop_player is not None})")
            all_results[btype] = {
                "type": btype, "flop": flop, "desc": cfg["desc"],
                "ip_range": [], "oop_range": [],
                "range_advantage": None, "nut_advantage_score": None,
            }
            continue

        ip_rows  = extract_range(ip_player)
        oop_rows = extract_range(oop_player)

        ip_nut   = calc_nut_share(ip_rows)
        oop_nut  = calc_nut_share(oop_rows)
        ip_top3  = calc_top3_share(ip_rows)
        oop_top3 = calc_top3_share(oop_rows)

        nut_adv_score = round(ip_top3 - oop_top3, 2)
        if nut_adv_score > 0.5:
            range_adv = "IP"
        elif nut_adv_score < -0.5:
            range_adv = "OOP"
        else:
            range_adv = "中立"

        print(f"  IP  ナット系シェア: {ip_nut:.1f}%  (top3: {ip_top3:.1f}%)")
        print(f"  OOP ナット系シェア: {oop_nut:.1f}%  (top3: {oop_top3:.1f}%)")
        print(f"  レンジアドバンテージ: {range_adv}  (スコア: IP-OOP = {nut_adv_score:+.2f}%)")
        print_range_table(ip_rows, oop_rows, btype)

        all_results[btype] = {
            "type":               btype,
            "flop":               flop,
            "desc":               cfg["desc"],
            "ip_range":           ip_rows,
            "oop_range":          oop_rows,
            "ip_nut_share":       ip_nut,
            "oop_nut_share":      oop_nut,
            "ip_top3_share":      ip_top3,
            "oop_top3_share":     oop_top3,
            "range_advantage":    range_adv,
            "nut_advantage_score": nut_adv_score,
        }
        time.sleep(2.0)

    # ─── 全体サマリー ───
    print(f"\n\n{'='*70}")
    print(f"★ 全体サマリー: レンジアドバンテージ")
    print(f"  {'型':20s} | {'IP top3%':>9} | {'OOP top3%':>10} | {'差(IP-OOP)':>11} | {'優位':>5}")
    print(f"  {'-'*68}")
    for btype, res in all_results.items():
        ip3   = res.get("ip_top3_share")
        oop3  = res.get("oop_top3_share")
        score = res.get("nut_advantage_score")
        adv   = res.get("range_advantage") or "—"
        ip3_s   = f"{ip3:.1f}%"   if ip3   is not None else "—"
        oop3_s  = f"{oop3:.1f}%"  if oop3  is not None else "—"
        score_s = f"{score:+.2f}%" if score is not None else "—"
        print(f"  {btype:20s} | {ip3_s:>9} | {oop3_s:>10} | {score_s:>11} | {adv:>5}")

    # JSON 保存
    out = FINDINGS_DIR / "range_share_BTN_BB.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(
            {"scenario": SCENARIO["label"], "results": all_results},
            f, ensure_ascii=False, indent=2,
        )
    print(f"\n✅ 完了 → {out}")


if __name__ == "__main__":
    main()
