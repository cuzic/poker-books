#!/usr/bin/env python3
"""
vol2 HandScore / バケット分類の妥当性を深掘り検証するスクリプト

hand_categories 単位で CBet率を測定し、
「Value/Marginal/Air の3分類はGTOと整合しているか」を検証する

使い方:
  TOKEN=eyJ... python3 cash_deep_validation.py
  TOKEN=eyJ... GT=Cash6mGeneral_6mNL25R25 python3 cash_deep_validation.py
"""

import os, sys, json, time, requests
from pathlib import Path
from collections import defaultdict

TOKEN   = os.environ.get("TOKEN", "")
GT      = os.environ.get("GT", "Cash6mGeneral_6mNL25R25")
DEPTH   = float(os.environ.get("DEPTH", "100"))
PF      = "F-F-F-R2.5-F-C"
BASE_URL = "https://api.gtowizard.com/v4/solutions/spot-solution/"
FINDINGS_DIR = Path(__file__).parent / "findings"
FINDINGS_DIR.mkdir(exist_ok=True)

GWCLIENTID = os.environ.get("GWCLIENTID", "")
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "authorization": f"Bearer {TOKEN}",
    "origin": "https://app.gtowizard.com",
    "referer": "https://app.gtowizard.com/",
    **({"gwclientid": GWCLIENTID} if GWCLIENTID else {}),
}

# 各型10ボード（計70ボード）
BOARDS = [
    # 型1: ハイカード（K/A/Q高）× ドライ（レインボー or 2トーン）
    ("型1_ハイドライ",   "Ks7d2c", "K高・レインボー"),
    ("型1_ハイドライ",   "As9d3c", "A高・レインボー"),
    ("型1_ハイドライ",   "Qd8c2h", "Q高・レインボー"),
    ("型1_ハイドライ",   "Kh6d3c", "K高・レインボー2"),
    ("型1_ハイドライ",   "Ah5s2c", "A高・ローキッカー"),
    ("型1_ハイドライ",   "Qs7d3c", "Q高・レインボー2"),
    ("型1_ハイドライ",   "Kd8s3h", "K高・レインボー3"),
    ("型1_ハイドライ",   "Ah7s4c", "A高・ミドルキッカー"),
    ("型1_ハイドライ",   "Qs9d4c", "Q高・ミドルキッカー"),
    ("型1_ハイドライ",   "Kh5d2c", "K高・ローキッカー"),

    # 型2: ハイカード × ウェット（FDあり or コネクト）
    ("型2_ハイウェット", "Qh8d3s", "Q高・2トーン"),
    ("型2_ハイウェット", "Kh9d5s", "K高・2トーン"),
    ("型2_ハイウェット", "Ah8s5d", "A高・2トーン"),
    ("型2_ハイウェット", "Js9h4c", "J高・2トーン"),
    ("型2_ハイウェット", "Td8s5d", "T高・2トーン"),
    ("型2_ハイウェット", "As8d5s", "A高・FD+コネクト"),
    ("型2_ハイウェット", "Ks7s3d", "K高・FD"),
    ("型2_ハイウェット", "Qh6s4d", "Q高・コネクト"),
    ("型2_ハイウェット", "Jd9s6h", "J高・コネクト"),
    ("型2_ハイウェット", "Ah6d4s", "A高・コネクト"),

    # 型3: ロー×ドライ（ミドル以下、レインボー）
    ("型3_ロードライ",   "Jd7s5c", "J中・レインボー"),
    ("型3_ロードライ",   "8d5s2c", "超低・レインボー"),
    ("型3_ロードライ",   "9s6d2c", "9中・レインボー"),
    ("型3_ロードライ",   "Td6s3c", "T中・レインボー"),
    ("型3_ロードライ",   "8s4d2c", "8低・レインボー"),
    ("型3_ロードライ",   "9d7s4c", "9連・レインボー"),
    ("型3_ロードライ",   "6s4d2c", "超低連・レインボー"),
    ("型3_ロードライ",   "Js5d3c", "J中低・レインボー"),
    ("型3_ロードライ",   "Ts7d4c", "T中低・レインボー"),
    ("型3_ロードライ",   "9s5d2c", "9低・レインボー"),

    # 型4: ロー×ウェット（コネクト+2トーン）
    ("型4_ローウェット", "Th9s8d", "低連携・2トーン"),
    ("型4_ローウェット", "7s6d5h", "低連続・レインボー"),
    ("型4_ローウェット", "9h8d7s", "9連続3枚"),
    ("型4_ローウェット", "8s7h6d", "8連続3枚"),
    ("型4_ローウェット", "Jd9s8h", "J連携・2トーン"),
    ("型4_ローウェット", "Th8s7d", "T連携・2トーン"),
    ("型4_ローウェット", "6s5h4d", "低連続2"),
    ("型4_ローウェット", "Js8h7d", "J連・2トーン"),
    ("型4_ローウェット", "Td9h8s", "T連続3枚"),
    ("型4_ローウェット", "8h7s6d", "8連続2"),

    # 型5: モノトーン
    ("型5_モノトーン",   "Ah9h5h", "A高モノトーン"),
    ("型5_モノトーン",   "Kh8h3h", "K高モノトーン"),
    ("型5_モノトーン",   "Qh7h4h", "Q高モノトーン"),
    ("型5_モノトーン",   "Jh9h5h", "J高モノトーン"),
    ("型5_モノトーン",   "Th7h4h", "T高モノトーン"),
    ("型5_モノトーン",   "9h6h3h", "9高モノトーン"),
    ("型5_モノトーン",   "Ah8h4h", "A高モノトーン2"),
    ("型5_モノトーン",   "Kh9h5h", "K高モノトーン2"),
    ("型5_モノトーン",   "Qh6h3h", "Q高モノトーン2"),
    ("型5_モノトーン",   "Jh7h4h", "J高モノトーン2"),

    # 型6: ペア高（AA/KK/QQ + オーバーカード）
    ("型6_ペア高",       "AsAcKd", "AAKペア"),
    ("型6_ペア高",       "KsKcAd", "KKAペア"),
    ("型6_ペア高",       "AhAcQd", "AAQペア"),
    ("型6_ペア高",       "AsAcJd", "AAJペア"),
    ("型6_ペア高",       "KsKcQd", "KKQペア"),
    ("型6_ペア高",       "QsQcAd", "QQAペア"),
    ("型6_ペア高",       "KhKcJd", "KKJペア"),
    ("型6_ペア高",       "AsAc9d", "AA9ペア"),
    ("型6_ペア高",       "QhQcKd", "QQKペア"),
    ("型6_ペア高",       "JsJcAd", "JJAペア"),

    # 型7: ペア低（77以下のロウペア + アンダーカード）
    ("型7_ペア低",       "7s7d2c", "77低ペア"),
    ("型7_ペア低",       "5s5d8c", "55低ペア"),
    ("型7_ペア低",       "3s3d8c", "33低ペア"),
    ("型7_ペア低",       "4s4d9c", "44低ペア"),
    ("型7_ペア低",       "6s6d2c", "66低ペア"),
    ("型7_ペア低",       "2s2d7c", "22低ペア"),
    ("型7_ペア低",       "3s3d9c", "33低ペア2"),
    ("型7_ペア低",       "4s4d7c", "44低ペア2"),
    ("型7_ペア低",       "6s6d3c", "66低ペア2"),
    ("型7_ペア低",       "5s5d3c", "55低ペア2"),
]

# hand_category の HS近似値（代表的な値。ボードによって変動する）
HC_HS = {
    "straight_flush": 97,
    "quads":          93,
    "fullhouse":      89,
    "flush":          83,
    "straight":       80,
    "set":            85,
    "two_pair":       77,
    "trips":          74,
    "overpair":       70,
    "top_pair":       60,   # TPTK≈66, TPmk≈60, TPwk≈53
    "underpair":      42,
    "second_pair":    43,
    "third_pair":     35,
    "low_pair":       30,
    "ace_high":       24,
    "king_high":      21,
    "queen_high":     19,
    "jack_high":      17,
    "ten_high":       15,
    "no_made_hand":   12,
}

# HS境界（vol2の3バケット）
def hs_bucket(hs):
    if hs >= 65: return "バリュー(≥65)"
    if hs >= 35: return "マージナル(35-64)"
    return "エアー(≤34)"

def call_api(board, flop_actions="X"):
    params = {
        "gametype": GT, "depth": str(DEPTH), "stacks": "",
        "preflop_actions": PF, "flop_actions": flop_actions,
        "turn_actions": "", "river_actions": "", "board": board,
    }
    r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
    if r.status_code == 200:
        return r.json()
    print(f"  [HTTP {r.status_code}]")
    return None

def get_btn(data):
    for p in data.get("players_info", []):
        if isinstance(p.get("player"), dict) and p["player"].get("position") == "BTN":
            return p
    return None

def analyze(board_label, board_str, board_desc, data):
    btn = get_btn(data)
    sols = data.get("action_solutions", [])
    if not btn or not sols:
        return None

    # アクション分類
    codes = {}
    for s in sols:
        a = s["action"]; t = a["type"]; c = a["code"]
        bp = float(a.get("betsize_by_pot") or 0)
        if t == "CHECK":   codes["check"] = c
        elif t == "RAISE":
            if bp < 0.25:    codes["bet20"] = c
            elif bp < 0.40:  codes["bet33"] = c
            elif bp < 0.65:  codes["bet50"] = c
            elif bp < 0.90:  codes["bet75"] = c
            elif bp < 1.20:  codes["bet100"] = c
            else:            codes["betover"] = c

    check_code = codes.get("check", "__")

    # BTN レンジ hand_category コンボ数
    range_hc = {h["name"]: h["total_combos"] for h in btn["hand_categories"]}
    # equity_buckets
    range_eb = {h["name"]: h["total_combos"] for h in btn["equity_buckets_advanced"]}

    # アクション別 hand_category コンボ数
    action_hc = {}
    action_eb = {}
    for s in sols:
        c = s["action"]["code"]
        action_hc[c] = {h["name"]: h["total_combos"] for h in (s["hand_categories"] or [])}
        action_eb[c] = {h["name"]: h["total_combos"] for h in (s["equity_buckets_advanced"] or [])}

    # ─── hand_category ごとの CBet率 ───
    hc_rows = []
    for hc, total in sorted(range_hc.items(), key=lambda x: -HC_HS.get(x[0], 50)):
        if total < 0.3:
            continue
        bet = sum(action_hc[c].get(hc, 0) for c in action_hc if c != check_code)
        bet_rate = bet / total if total > 0 else 0
        # 主要サイズ
        main_size, main_rate = "チェック", 0.0
        for sk, sn in [("bet20","20%"),("bet33","33%"),("bet50","50%"),
                       ("bet75","75%"),("bet100","100%"),("betover","120%+")]:
            c = codes.get(sk)
            if c and c in action_hc:
                sr = action_hc[c].get(hc, 0) / total if total > 0 else 0
                if sr > main_rate:
                    main_rate, main_size = sr, sn
        hs_approx = HC_HS.get(hc, 0)
        bucket = hs_bucket(hs_approx)
        hc_rows.append({
            "hc": hc, "total": total, "bet_rate": bet_rate,
            "main_size": main_size, "hs": hs_approx, "bucket": bucket,
        })

    # ─── equity_buckets ごとの CBet率 ───
    eb_order = ["hands_90_100","hands_80_90","hands_70_80","hands_60_70",
                "hands_50_60","hands_25_50","hands_0_25"]
    eb_rows = []
    for eb in eb_order:
        total = range_eb.get(eb, 0)
        if total < 0.3:
            continue
        bet = sum(action_eb[c].get(eb, 0) for c in action_eb if c != check_code)
        bet_rate = bet / total if total > 0 else 0
        eb_rows.append({"eb": eb.replace("hands_","").replace("_","-"),
                        "total": total, "bet_rate": bet_rate})

    return {
        "label": board_label, "board": board_str, "desc": board_desc,
        "codes": codes, "hc_rows": hc_rows, "eb_rows": eb_rows,
    }

def print_board(r):
    print(f"\n{'='*72}")
    print(f"【{r['label']}】 {r['board']}  ({r['desc']})")
    acts = ', '.join(f"{k}={v}" for k, v in r['codes'].items())
    print(f"  アクション: {acts}")

    # ─── hand_category 表 ───
    print(f"\n  ■ hand_category 別 CBet率")
    print(f"  {'カテゴリ':22s}  {'コンボ':>6} {'CBet%':>7} {'主要size':>8}  {'HS近似':>5}  HS帯")
    print(f"  {'-'*68}")
    for row in r["hc_rows"]:
        flag = "◆" if row["bet_rate"] > 0.60 else ("△" if row["bet_rate"] > 0.30 else "×")
        print(f"  {flag} {row['hc']:22s} {row['total']:6.1f} {row['bet_rate']*100:6.1f}%  {row['main_size']:>8}  {row['hs']:>5}  {row['bucket']}")

    # ─── equity_buckets 表 ───
    print(f"\n  ■ equity_buckets 別 CBet率（エクイティパーセンタイル）")
    print(f"  {'Equity帯':15s} {'コンボ':>6} {'CBet%':>7}")
    print(f"  {'-'*32}")
    for row in r["eb_rows"]:
        print(f"  {row['eb']:15s} {row['total']:6.1f} {row['bet_rate']*100:6.1f}%")

def print_summary(results):
    """全ボード横断：hand_category×ボード型でCBet率を集約"""
    print(f"\n\n{'='*72}")
    print("★ 横断サマリー：hand_category ごとの平均 CBet率（ボード型別）")
    print(f"{'='*72}")

    # ボード型ごとにグループ化
    by_type = defaultdict(list)
    for r in results:
        by_type[r["label"]].append(r)

    # 全 hand_category 一覧（HS降順）
    all_hc = sorted(HC_HS.keys(), key=lambda k: -HC_HS[k])

    header = f"  {'カテゴリ':22s} {'HS':>4}"
    for btype in by_type:
        header += f"  {btype[:8]:>10}"
    print(header)
    print(f"  {'-'*70}")

    for hc in all_hc:
        row = f"  {hc:22s} {HC_HS[hc]:>4}"
        any_data = False
        for btype, boards in by_type.items():
            # ボード型の平均 CBet率
            rates = []
            for b in boards:
                for hc_row in b["hc_rows"]:
                    if hc_row["hc"] == hc and hc_row["total"] > 0.5:
                        rates.append(hc_row["bet_rate"])
            if rates:
                avg = sum(rates) / len(rates)
                row += f"  {avg*100:9.0f}%"
                any_data = True
            else:
                row += f"  {'—':>10}"
        if any_data:
            print(row)

    print(f"\n  凡例: ◆=CBet率>60%  △=30〜60%  ×=<30%  — =データなし")

def check_auth():
    data = call_api("Ks7d2c")
    if data is None:
        print(f"❌ 認証失敗")
        sys.exit(1)
    print(f"✅ 認証OK (gametype={GT}, depth={DEPTH}BB)")

def main():
    if not TOKEN:
        print("❌ TOKEN 未設定")
        sys.exit(1)
    check_auth()

    results = []
    for label, board, desc in BOARDS:
        print(f"\n取得中: {label} ({board})...", end="", flush=True)
        data = call_api(board, "X")
        if data is None:
            print(" 失敗")
            continue
        print(" OK")
        r = analyze(label, board, desc, data)
        if r:
            results.append(r)
            print_board(r)
        time.sleep(1)

    print_summary(results)

    # JSON保存
    out = FINDINGS_DIR / "cash_deep_validation.json"
    with open(out, "w") as f:
        json.dump([{k: v for k, v in r.items() if k != "codes"} for r in results],
                  f, ensure_ascii=False, indent=2)
    print(f"\n✅ 完了 → {out}")

if __name__ == "__main__":
    main()
