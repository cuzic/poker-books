#!/usr/bin/env python3
"""
HandScore フレームワーク検証スクリプト
GTO Wizard の hand_categories / equity_buckets_advanced で
vol2の9マスマトリックスの整合性を確認する

使い方:
  TOKEN=eyJ... python3 hs_validation.py
"""

import os, sys, json, time, requests
from pathlib import Path

TOKEN = os.environ.get("TOKEN", "")
BASE_URL = "https://api.gtowizard.com/v4/solutions/spot-solution/"
FINDINGS_DIR = Path(__file__).parent / "findings"
FINDINGS_DIR.mkdir(exist_ok=True)

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "authorization": f"Bearer {TOKEN}",
    "origin": "https://app.gtowizard.com",
    "referer": "https://app.gtowizard.com/",
}

GT = "MTTGeneral"
DEPTH = 25.125
PF = "F-F-F-F-F-R2.1-F-C"  # BTN open 2.1BB, SB fold, BB call (8-max)

# 検証対象ボード
BOARDS = [
    ("型1_ハイドライ",  "Ks7d2c",  "バリュー75%/マージナル33%/エアー33%"),
    ("型2_ハイウェット", "Qh8d3s",  "バリュー75%/マージナル33%/エアーチェック"),
    ("型3_ミッドウェット","Jd6c4d",  "バリュー75%/マージナルチェック/エアーチェック"),
    ("型4_ローウェット", "Th9s8d",  "バリュー75%/マージナルチェック/エアーチェック"),
    ("型7_ペア低",      "7s7d2c",  "全レンジ20%マイクロベット"),
]

# ハンドカテゴリー → 本書のHS帯マッピング（推定）
HC_TO_HS_BUCKET = {
    "no_made_hand":  "エアー(HS≤34)",
    "ace_high":      "エアー(HS≤34)",  # Aハイは役なし
    "king_high":     "エアー(HS≤34)",
    "low_pair":      "エアー(HS≤34)",
    "third_pair":    "マージナル(35-64)",  # 3rdペア (22 on K72)
    "second_pair":   "マージナル(35-64)",  # 2ndペア (77 on K72)
    "underpair":     "マージナル(35-64)",  # アンダーペア
    "top_pair":      "バリュー(HS≥65)",   # トップペア
    "overpair":      "バリュー(HS≥65)",   # オーバーペア
    "two_pair":      "バリュー(HS≥65)",   # ツーペア
    "trips":         "バリュー(HS≥65)",   # トリップス
    "set":           "バリュー(HS≥65)",   # セット
    "straight":      "バリュー(HS≥65)",
    "flush":         "バリュー(HS≥65)",
    "fullhouse":     "バリュー(HS≥65)",
    "quads":         "バリュー(HS≥65)",
    "straight_flush":"バリュー(HS≥65)",
}

def call_api(board, flop_actions="X"):
    params = {
        "gametype": GT,
        "depth": str(DEPTH),
        "stacks": "",
        "preflop_actions": PF,
        "flop_actions": flop_actions,
        "board": board,
    }
    resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
    if resp.status_code != 200:
        return None
    return resp.json()

def get_btn_player(data):
    for p in data.get("players_info", []):
        if isinstance(p.get("player"), dict) and p["player"].get("position") == "BTN":
            return p
    return None

def analyze_board(label, board_str, book_pred, data):
    """ボード別分析：hand_categories と equity_buckets_advanced を使って
    各手カテゴリーのベット頻度を計算する"""

    sols = data.get("action_solutions", [])
    btn = get_btn_player(data)
    if not btn or not sols:
        print(f"  [ERROR] データ取得失敗")
        return

    # BTNレンジの各hand_categoryの総コンボ数
    range_hc = {hc["name"]: hc["total_combos"] for hc in btn["hand_categories"]}
    range_eb = {eb["name"]: eb["total_combos"] for eb in btn["equity_buckets_advanced"]}

    # 各アクションのhand_category別コンボ数
    action_hc = {}   # action_code -> {hc_name: combos}
    action_eb = {}   # action_code -> {eb_name: combos}
    action_total = {} # action_code -> total_combos

    for s in sols:
        code = s["action"]["code"]
        action_hc[code] = {hc["name"]: hc["total_combos"] for hc in (s["hand_categories"] or [])}
        action_eb[code] = {eb["name"]: eb["total_combos"] for eb in (s["equity_buckets_advanced"] or [])}
        action_total[code] = s["total_combos"]

    # 主要3アクション（CHECK / 33%ベット / 75%ベット）を特定
    codes_by_type = {}
    for s in sols:
        a = s["action"]
        t = a["type"]
        code = a["code"]
        bpot = float(a.get("betsize_by_pot") or 0)
        if t == "CHECK":
            codes_by_type["check"] = code
        elif t == "RAISE" and bpot < 0.25:
            codes_by_type["bet20"] = code   # ~20% pot
        elif t == "RAISE" and 0.25 <= bpot < 0.40:
            codes_by_type["bet33"] = code   # ~33% pot
        elif t == "RAISE" and 0.40 <= bpot < 0.65:
            codes_by_type["bet50"] = code   # ~50% pot
        elif t == "RAISE" and 0.65 <= bpot < 0.90:
            codes_by_type["bet75"] = code   # ~75% pot

    total_bet_all = sum(
        action_total[c] for c in action_total if c != codes_by_type.get("check", "X")
    )
    total_range = sum(range_hc.values())

    print(f"\n{'='*60}")
    print(f"【{label}】{board_str}")
    print(f"  本書の予測: {book_pred}")
    print(f"  全体CBet率: {total_bet_all/total_range*100:.1f}%")
    print()

    # ─── A. hand_categories 別ベット率 ───
    print("  ■ hand_categories別ベット率（GTO実測）")
    print(f"  {'カテゴリ':28s} {'総CB':>7} {'Bet率':>7} {'主要size':>12} {'HS帯推定'}")
    print(f"  {'-'*70}")

    for hc_name, total in sorted(range_hc.items(), key=lambda x: -x[1]):
        if total < 0.5:
            continue

        # 全ベット頻度
        bet_combos = sum(
            action_hc[code].get(hc_name, 0)
            for code in action_hc
            if code != codes_by_type.get("check", "X")
        )
        bet_rate = bet_combos / total if total > 0 else 0

        # 主要ベットサイズを特定
        size_info = []
        for size_key, size_name in [("bet20","20%"),("bet33","33%"),("bet50","50%"),("bet75","75%")]:
            code = codes_by_type.get(size_key)
            if code and code in action_hc:
                sc = action_hc[code].get(hc_name, 0)
                if sc / total > 0.05:
                    size_info.append(f"{size_name}:{sc/total*100:.0f}%")

        hs_bucket = HC_TO_HS_BUCKET.get(hc_name, "?")
        print(f"  {hc_name:28s} {total:7.1f} {bet_rate*100:6.1f}% {' '.join(size_info):12s} {hs_bucket}")

    # ─── B. equity_buckets_advanced 別ベット率 ───
    print()
    print("  ■ equity_buckets_advanced別ベット率（エクイティパーセンタイル）")
    print(f"  {'Equity帯':20s} {'総CB':>7} {'Bet率':>7} {'主要size':>15}")
    print(f"  {'-'*55}")

    eb_order = ["hands_90_100","hands_80_90","hands_70_80","hands_60_70",
                "hands_50_60","hands_25_50","hands_0_25"]
    for eb_name in eb_order:
        total = range_eb.get(eb_name, 0)
        if total < 0.5:
            continue
        bet_combos = sum(
            action_eb[code].get(eb_name, 0)
            for code in action_eb
            if code != codes_by_type.get("check", "X")
        )
        bet_rate = bet_combos / total if total > 0 else 0

        size_info = []
        for size_key, size_name in [("bet20","20%"),("bet33","33%"),("bet50","50%"),("bet75","75%")]:
            code = codes_by_type.get(size_key)
            if code and code in action_eb:
                sc = action_eb[code].get(eb_name, 0)
                if sc / total > 0.05:
                    size_info.append(f"{size_name}:{sc/total*100:.0f}%")

        label_str = eb_name.replace("hands_","").replace("_","-")
        print(f"  {label_str:20s} {total:7.1f} {bet_rate*100:6.1f}% {' '.join(size_info)}")

def check_auth():
    resp = call_api("Ks7d2c")
    if resp is None or "AUTHENTICATION_FAILED" in str(resp):
        print("❌ 認証失敗: TOKEN が無効または期限切れです")
        sys.exit(1)
    print("✅ 認証OK")
    return True

def main():
    if not TOKEN:
        print("❌ TOKEN 環境変数が未設定です")
        sys.exit(1)

    check_auth()

    results = []
    for label, board_str, book_pred in BOARDS:
        print(f"\n取得中: {label} ({board_str})...", end="", flush=True)
        data = call_api(board_str, flop_actions="X")
        if data is None:
            print(f"  取得失敗")
            continue
        print(" OK")

        analyze_board(label, board_str, book_pred, data)

        # 生データ保存
        results.append({
            "label": label,
            "board": board_str,
            "book_pred": book_pred,
            "data": data
        })
        time.sleep(1)

    # 保存
    out_file = FINDINGS_DIR / "hs_validation.jsonl"
    with open(out_file, "w") as f:
        for r in results:
            # data は大きいので要約だけ保存
            summary = {
                "label": r["label"],
                "board": r["board"],
                "book_pred": r["book_pred"],
                "action_solutions": [
                    {
                        "code": s["action"]["code"],
                        "type": s["action"]["type"],
                        "betsize_by_pot": s["action"].get("betsize_by_pot"),
                        "total_frequency": s["total_frequency"],
                        "total_combos": s["total_combos"],
                        "hand_categories": s["hand_categories"],
                        "equity_buckets_advanced": s["equity_buckets_advanced"],
                    }
                    for s in r["data"].get("action_solutions", [])
                ],
                "btn_hand_categories": next(
                    (p["hand_categories"] for p in r["data"].get("players_info", [])
                     if isinstance(p.get("player"), dict) and p["player"].get("position") == "BTN"),
                    []
                ),
                "btn_equity_buckets_advanced": next(
                    (p["equity_buckets_advanced"] for p in r["data"].get("players_info", [])
                     if isinstance(p.get("player"), dict) and p["player"].get("position") == "BTN"),
                    []
                ),
            }
            f.write(json.dumps(summary, ensure_ascii=False) + "\n")

    print(f"\n\n✅ 完了 → {out_file}")

if __name__ == "__main__":
    main()
