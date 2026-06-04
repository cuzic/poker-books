#!/usr/bin/env python3
"""
vol2 キャッシュポストフロップ CBet フレームワーク GTO検証スクリプト
GTO Wizard の hand_categories / equity_buckets_advanced で
9マスマトリックス（ボード7分類×HS3バケット）の整合性を確認する

使い方:
  TOKEN=eyJ... python3 cash_validation.py
  TOKEN=eyJ... GT=NL100 python3 cash_validation.py   # gametype を上書き
"""

import os, sys, json, time, requests
from pathlib import Path

TOKEN   = os.environ.get("TOKEN", "")
GT      = os.environ.get("GT", "Cash6mGeneral_6mNL25R25")  # 6-max cash gametype
DEPTH   = float(os.environ.get("DEPTH", "100"))  # 100BB
BASE_URL = "https://api.gtowizard.com/v4/solutions/spot-solution/"
FINDINGS_DIR = Path(__file__).parent / "findings"
FINDINGS_DIR.mkdir(exist_ok=True)

# 6-max SRP: UTG/HJ/CO fold → BTN open 2.5x → SB fold → BB call
PF = "F-F-F-R2.5-F-C"

GWCLIENTID = os.environ.get("GWCLIENTID", "")

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "authorization": f"Bearer {TOKEN}",
    "origin": "https://app.gtowizard.com",
    "referer": "https://app.gtowizard.com/",
    **({"gwclientid": GWCLIENTID} if GWCLIENTID else {}),
}

# 本書の9マスマトリックス予測（vol2 第2章 SRP決定表）
# 値: ベットサイズ(%) または "チェック"
BOOK_PREDICTIONS = {
    "型1_ハイドライ":   {"value": 75, "marginal": 33, "air": 33},
    "型2_ハイウェット": {"value": 75, "marginal": 33, "air": None},
    "型3_ロードライ":   {"value": 75, "marginal": None, "air": None},
    "型4_ローウェット": {"value": 75, "marginal": None, "air": None},
    "型5_モノトーン":   {"value": 50, "marginal": None, "air": None},
    "型6_ペア高":       {"value": 75, "marginal": 33, "air": 33},
    "型7_ペア低":       {"value": 20, "marginal": 20, "air": 20},
}

# 検証ボード（各型の代表例）
BOARDS = [
    ("型1_ハイドライ",   "Ks7d2c", "K高・レインボー"),
    ("型2_ハイウェット", "Qh8d3s", "Q高・2トーン"),
    ("型3_ロードライ",   "Jd7s5c", "J中・レインボー"),
    ("型4_ローウェット", "Th9s8d", "低連携・2トーン"),
    ("型5_モノトーン",   "Ah9h5h", "A高・フラッシュ完成済"),
    ("型6_ペア高",       "AsAcKd", "AAKペアボード"),
    ("型7_ペア低",       "7s7d2c", "77低ペアボード"),
]

# HandScore バケット判定
HC_TO_BUCKET = {
    "no_made_hand":   "air",
    "ace_high":       "air",
    "king_high":      "air",
    "queen_high":     "air",
    "jack_high":      "air",
    "low_pair":       "air",
    "third_pair":     "marginal",
    "second_pair":    "marginal",
    "underpair":      "marginal",
    "top_pair":       "value",
    "overpair":       "value",
    "two_pair":       "value",
    "trips":          "value",
    "set":            "value",
    "straight":       "value",
    "flush":          "value",
    "fullhouse":      "value",
    "quads":          "value",
    "straight_flush": "value",
}

def call_api(board, flop_actions="X"):
    params = {
        "gametype": GT,
        "depth": str(DEPTH),
        "stacks": "",
        "preflop_actions": PF,
        "flop_actions": flop_actions,
        "turn_actions": "",
        "river_actions": "",
        "board": board,
    }
    resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
    if resp.status_code == 200:
        return resp.json()
    print(f"  [HTTP {resp.status_code}] {resp.text[:200]}")
    return None

def get_btn_player(data):
    for p in data.get("players_info", []):
        if isinstance(p.get("player"), dict) and p["player"].get("position") == "BTN":
            return p
    return None

def identify_actions(sols):
    """アクションを種別に分類して返す"""
    codes = {}
    for s in sols:
        a = s["action"]
        t = a["type"]
        code = a["code"]
        bpot = float(a.get("betsize_by_pot") or 0)
        if t == "CHECK":
            codes["check"] = code
        elif t == "RAISE":
            if bpot < 0.25:
                codes["bet20"] = code
            elif bpot < 0.40:
                codes["bet33"] = code
            elif bpot < 0.65:
                codes["bet50"] = code
            elif bpot < 0.90:
                codes["bet75"] = code
            elif bpot < 1.20:
                codes["bet100"] = code
            else:
                codes["betover"] = code
    return codes

def calc_bucket_stats(sols, btn, codes):
    """バケット別のベット率・主要サイズを集計する"""
    check_code = codes.get("check", "__NONE__")

    # BTN レンジの hand_category コンボ数
    range_hc = {hc["name"]: hc["total_combos"] for hc in btn["hand_categories"]}

    # アクション別 hand_category コンボ数
    action_hc = {}
    action_total = {}
    for s in sols:
        code = s["action"]["code"]
        action_hc[code] = {hc["name"]: hc["total_combos"] for hc in (s["hand_categories"] or [])}
        action_total[code] = s["total_combos"]

    # バケット別集計
    bucket_stats = {"value": {}, "marginal": {}, "air": {}}
    for hc_name, total in range_hc.items():
        if total < 0.5:
            continue
        bucket = HC_TO_BUCKET.get(hc_name)
        if not bucket:
            continue

        bet_combos = sum(
            action_hc[code].get(hc_name, 0)
            for code in action_hc
            if code != check_code
        )
        bet_rate = bet_combos / total if total > 0 else 0

        # 主要サイズ（5%以上）
        dominant_size = None
        dominant_rate = 0.0
        for size_key, size_name in [("bet20","20%"),("bet33","33%"),("bet50","50%"),
                                     ("bet75","75%"),("bet100","100%"),("betover","120%+")]:
            code = codes.get(size_key)
            if code and code in action_hc:
                sc = action_hc[code].get(hc_name, 0)
                if total > 0 and sc / total > dominant_rate:
                    dominant_rate = sc / total
                    dominant_size = size_name

        b = bucket_stats[bucket]
        b["total"] = b.get("total", 0) + total
        b["bet_combos"] = b.get("bet_combos", 0) + bet_combos
        if dominant_size and dominant_rate > 0.05:
            key = dominant_size
            b.setdefault("sizes", {})[key] = b.get("sizes", {}).get(key, 0) + total * dominant_rate

    # バケット別ベット率・主要サイズ確定
    result = {}
    for bkt in ("value", "marginal", "air"):
        b = bucket_stats[bkt]
        if b.get("total", 0) < 0.5:
            result[bkt] = None
            continue
        bet_rate = b.get("bet_combos", 0) / b["total"]
        sizes = b.get("sizes", {})
        main_size = max(sizes, key=sizes.get) if sizes else "チェック"
        result[bkt] = {
            "total": b["total"],
            "bet_rate": bet_rate,
            "main_size": main_size,
        }
    return result

def compare_with_book(gto_stats, book_pred):
    """本書の予測とGTO実測を比較して一致・乖離を判定"""
    rows = []
    for bkt_name, bkt_label in [("value","バリュー"),("marginal","マージナル"),("air","エアー")]:
        gto = gto_stats.get(bkt_name)
        pred_size = book_pred.get(bkt_name)  # None = チェック予測

        if gto is None:
            rows.append(f"  {bkt_label:10s} | データなし")
            continue

        bet_rate_pct = gto["bet_rate"] * 100
        gto_size = gto["main_size"] if gto["bet_rate"] > 0.10 else "チェック"

        # 判定
        if pred_size is None:
            # 本書: チェック予測
            if gto["bet_rate"] < 0.15:
                judge = "✅ 一致"
            elif gto["bet_rate"] < 0.40:
                judge = "⚠️  小差（GTO低頻度ベット）"
            else:
                judge = f"❌ 乖離（GTO {bet_rate_pct:.0f}%ベット）"
        else:
            # 本書: ベット予測
            if gto["bet_rate"] < 0.15:
                judge = "❌ 乖離（GTOはチェック主体）"
            else:
                book_size_str = f"{pred_size}%"
                if gto_size == book_size_str:
                    judge = "✅ 一致"
                else:
                    judge = f"⚠️  サイズ差（本書{book_size_str} vs GTO {gto_size}）"

        book_str = "チェック" if pred_size is None else f"{pred_size}%"
        rows.append(f"  {bkt_label:10s} | 本書:{book_str:6s} GTO:{bet_rate_pct:5.1f}%ベット/{gto_size:6s}  {judge}")
    return rows

def analyze_board(label, board_str, board_desc, data):
    btn = get_btn_player(data)
    sols = data.get("action_solutions", [])
    if not btn or not sols:
        print(f"  [ERROR] BTN データなし")
        return None

    codes = identify_actions(sols)
    gto_stats = calc_bucket_stats(sols, btn, codes)
    book_pred = BOOK_PREDICTIONS.get(label, {})

    total_range = sum(hc["total_combos"] for hc in btn["hand_categories"])
    check_code = codes.get("check", "__NONE__")
    total_bet = sum(s["total_combos"] for s in sols if s["action"]["code"] != check_code)
    cbet_rate = total_bet / total_range if total_range > 0 else 0

    print(f"\n{'='*65}")
    print(f"【{label}】 {board_str}  ({board_desc})")
    print(f"  利用可能アクション: {', '.join(f'{k}={v}' for k,v in codes.items())}")
    print(f"  全体CBet率: {cbet_rate*100:.1f}%")
    print()
    print(f"  {'バケット':10s} | {'本書予測':6s}  {'GTO実測':>20s}  判定")
    print(f"  {'-'*60}")
    rows = compare_with_book(gto_stats, book_pred)
    for r in rows:
        print(r)

    return {
        "label": label,
        "board": board_str,
        "cbet_rate": cbet_rate,
        "gto_stats": gto_stats,
        "book_pred": book_pred,
        "codes": codes,
    }

def check_auth():
    data = call_api("Ks7d2c")
    if data is None:
        print(f"❌ 認証失敗 (gametype={GT}, depth={DEPTH})")
        print("   ヒント: GT=NL100 TOKEN=eyJ... python3 cash_validation.py")
        sys.exit(1)
    if "AUTHENTICATION_FAILED" in str(data) or "error" in str(data).lower():
        print(f"❌ APIエラー: {str(data)[:200]}")
        sys.exit(1)
    print(f"✅ 認証OK (gametype={GT}, depth={DEPTH}BB)")
    return True

def main():
    if not TOKEN:
        print("❌ TOKEN 環境変数が未設定です")
        sys.exit(1)

    check_auth()

    results = []
    summary_lines = ["\n\n" + "="*65, "★ サマリー：本書CBet予測 vs GTO実測", "="*65]

    for label, board_str, board_desc in BOARDS:
        print(f"\n取得中: {label} ({board_str})...", end="", flush=True)
        data = call_api(board_str, flop_actions="X")
        if data is None:
            print(" 取得失敗")
            continue
        print(" OK")

        result = analyze_board(label, board_str, board_desc, data)
        if result:
            results.append(result)

            # サマリー行
            summary_lines.append(f"\n【{label}】")
            rows = compare_with_book(result["gto_stats"], result["book_pred"])
            summary_lines.extend(rows)

        # 生データ保存（jsonl）
        out_data = {
            "label": label,
            "board": board_str,
            "gametype": GT,
            "depth": DEPTH,
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
                for s in data.get("action_solutions", [])
            ],
            "btn_hand_categories": next(
                (p["hand_categories"] for p in data.get("players_info", [])
                 if isinstance(p.get("player"), dict) and p["player"].get("position") == "BTN"),
                []
            ),
        }

        out_file = FINDINGS_DIR / f"cash_{label}.json"
        with open(out_file, "w") as f:
            json.dump(out_data, f, ensure_ascii=False, indent=2)

        time.sleep(1)

    # サマリー出力
    print("\n".join(summary_lines))

    # サマリーファイル保存
    summary_file = FINDINGS_DIR / "cash_validation_summary.md"
    with open(summary_file, "w") as f:
        f.write(f"# キャッシュゲーム CBet GTO検証\n\n")
        f.write(f"- gametype: `{GT}`\n- depth: {DEPTH}BB\n- preflop: `{PF}`\n\n")
        for line in summary_lines:
            f.write(line + "\n")

    print(f"\n✅ 完了 → {FINDINGS_DIR}/")

if __name__ == "__main__":
    main()
