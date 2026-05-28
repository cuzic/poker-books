#!/usr/bin/env python3
"""
cash_5cat_gto.py — 5類型 × 7ボード型 × 6シナリオ GTO Wizard 調査

調査対象:
  - ボード: 各型2〜3ボード (計21ボード)
  - シナリオ: BTN_BB / CO_BB / HJ_BB / UTG_BB / SB_BB / BTN_SB (6種)
  - データ: IP hand_categories (バリュー/BC/エアー) + draw_categories (ドロー/WD)

使い方:
  TOKEN=eyJ... python3 cash_5cat_gto.py
  TOKEN=eyJ... SCENARIO=BTN_BB python3 cash_5cat_gto.py   # 1シナリオのみ
  TOKEN=eyJ... BOARDS=1 python3 cash_5cat_gto.py          # 1ボード/型のみ
"""

import os, sys, json, time, requests
from pathlib import Path

TOKEN      = os.environ.get("TOKEN", "")
GWCLIENTID = os.environ.get("GWCLIENTID", "")
GT         = os.environ.get("GT", "Cash6mGeneral_6mNL25R25")
SCENARIO_F = os.environ.get("SCENARIO", "")        # 空=全シナリオ
BOARDS_PER_TYPE = int(os.environ.get("BOARDS", "3"))  # 1〜3

BASE_URL   = "https://api.gtowizard.com/v4/solutions/spot-solution/"
FINDINGS   = Path(__file__).parent / "findings"
FINDINGS.mkdir(exist_ok=True)

# ─── 6シナリオ ────────────────────────────────────────────────────
SCENARIOS = {
    "BTN_BB": {"pf": "F-F-F-R2.5-F-C",    "ip": "BTN", "oop": "BB",  "label": "BTN vs BB (SRP広レンジ)"},
    "CO_BB":  {"pf": "F-F-R2.5-F-F-C",    "ip": "CO",  "oop": "BB",  "label": "CO vs BB"},
    "HJ_BB":  {"pf": "F-R2.5-F-F-F-C",    "ip": "HJ",  "oop": "BB",  "label": "HJ vs BB"},
    "UTG_BB": {"pf": "R2.5-F-F-F-F-C",    "ip": "UTG", "oop": "BB",  "label": "UTG vs BB (SRP狭レンジ)"},
    "SB_BB":  {"pf": "F-F-F-F-R3-C",      "ip": "BB",  "oop": "SB",  "label": "SB vs BB (BBがIP)"},
    "BTN_SB": {"pf": "F-F-F-R2.5-C-F",    "ip": "BTN", "oop": "SB",  "label": "BTN vs SB"},
}

# ─── 21ボード (7型 × 3ボード) ────────────────────────────────────
BOARDS = [
    ("型1_ハイドライ",   "Ks7d2c",  "K高・レインボー"),
    ("型1_ハイドライ",   "As9d3c",  "A高・レインボー"),
    ("型1_ハイドライ",   "Qs7d3c",  "Q高・レインボー"),
    ("型2_ハイウェット", "Qh8d3s",  "Q高・2トーン"),
    ("型2_ハイウェット", "Kh9d5s",  "K高・2トーン"),
    ("型2_ハイウェット", "Ah8s5d",  "A高・2トーン"),
    ("型3_ロードライ",   "Jd7s5c",  "J中・レインボー"),
    ("型3_ロードライ",   "9s6d2c",  "9中・レインボー"),
    ("型3_ロードライ",   "8d5s2c",  "8低・レインボー"),
    ("型4_ローウェット", "Th9s8d",  "低連携・2トーン"),
    ("型4_ローウェット", "9h8d7s",  "9連続・レインボー"),
    ("型4_ローウェット", "Jd9s8h",  "J連携・2トーン"),
    ("型5_モノトーン",   "Ah9h5h",  "A高モノトーン"),
    ("型5_モノトーン",   "Kd7d3d",  "K高モノトーン"),
    ("型5_モノトーン",   "Qh8h4h",  "Q中モノトーン"),
    ("型6_ペア高",       "AsAcKd",  "AAKペア"),
    ("型6_ペア高",       "KhKd8c",  "KK8ペア"),
    ("型6_ペア高",       "AhAdQs",  "AAQペア"),
    ("型7_ペア低",       "7s7d2c",  "77低ペア"),
    ("型7_ペア低",       "4s4d9c",  "44中ペア"),
    ("型7_ペア低",       "5h5c2d",  "55低ペア"),
]

# ─── 5類型マッピング ─────────────────────────────────────────────
# made hand → 5類型（ドロー情報なしの近似）
HC_5CAT = {
    "straight_flush": "バリュー",
    "quads":          "バリュー",
    "fullhouse":      "バリュー",
    "flush":          "バリュー",
    "straight":       "バリュー",
    "set":            "バリュー",
    "trips":          "バリュー",
    "two_pair":       "バリュー",
    "overpair":       "バリュー",
    "top_pair":       "バリュー",
    "second_pair":    "ブラフキャッチャー",
    "underpair":      "ブラフキャッチャー",
    "third_pair":     "ブラフキャッチャー",
    "low_pair":       "エアー",
    "ace_high":       "エアー",
    "king_high":      "エアー",
    "queen_high":     "エアー",
    "jack_high":      "エアー",
    "ten_high":       "エアー",
    "no_made_hand":   "エアー",
}
# draw category → 5類型
DC_5CAT = {
    "combo_draw":     "ドロー",
    "nut_flush_draw": "ドロー",
    "flush_draw":     "ドロー",
    "oesd":           "ドロー",
    "gutshot":        "ウィークドロー",
    "twocards_bdfd":  "ウィークドロー",
    "no_draw":        None,
}

# ─── API ─────────────────────────────────────────────────────────
def make_headers():
    h = {
        "accept":           "application/json, text/plain, */*",
        "accept-language":  "ja,en;q=0.9",
        "authorization":    f"Bearer {TOKEN}",
        "cache-control":    "no-cache",
        "origin":           "https://app.gtowizard.com",
        "pragma":           "no-cache",
        "referer":          "https://app.gtowizard.com/",
    }
    if GWCLIENTID:
        h["gwclientid"] = GWCLIENTID
    return h


def call_api(board, pf, flop_actions="X"):
    params = {
        "gametype":        GT,
        "depth":           "100",
        "stacks":          "",
        "preflop_actions": pf,
        "flop_actions":    flop_actions,
        "turn_actions":    "",
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
                    ra = int(r.headers.get("Retry-After", 3600))
                    print(f"\n  ❌ 日次クォータ超過 ({ra//3600}時間後リセット)")
                    sys.exit(1)
            except Exception:
                pass
            wait = 15 * (attempt + 1)
            print(f" [429 {wait}s待機]", end="", flush=True)
            time.sleep(wait)
            continue
        if r.status_code == 404:
            print(f" [404 ボード未対応]", end="", flush=True)
            return None
        print(f" [HTTP {r.status_code}]", end="", flush=True)
        return None
    return None


def get_ip_player(data, ip_pos):
    for p in data.get("players_info", []):
        pl = p.get("player", {})
        if isinstance(pl, dict) and pl.get("position") == ip_pos:
            return p
        if pl.get("relative_postflop_position") == "IP":
            return p
    return None


def extract_hand_cats(player):
    """made hand categories → {name: {combos, bet_pct}}"""
    result = {}
    for hc in player.get("hand_categories", []):
        n = hc["total_combos"]
        if n < 0.3:
            continue
        af = hc.get("actions_total_frequencies", {})
        bet = sum(v for k, v in af.items() if k.startswith("R"))
        result[hc["name"]] = {"combos": round(n, 1), "bet_pct": round(bet * 100, 1)}
    return result


def extract_draw_cats(player):
    """draw categories → {name: {combos, bet_pct}}"""
    result = {}
    for dc in player.get("draw_categories", []):
        n = dc["total_combos"]
        if n < 0.3:
            continue
        af = dc.get("actions_total_frequencies", {})
        bet = sum(v for k, v in af.items() if k.startswith("R"))
        result[dc["name"]] = {"combos": round(n, 1), "bet_pct": round(bet * 100, 1)}
    return result


def aggregate_5cat(hand_cats, draw_cats):
    """5類型ごとの加重平均CBet%を返す。"""
    buckets = {
        "バリュー":          {"combos": 0.0, "bet_weighted": 0.0},
        "ドロー":            {"combos": 0.0, "bet_weighted": 0.0},
        "ブラフキャッチャー": {"combos": 0.0, "bet_weighted": 0.0},
        "ウィークドロー":     {"combos": 0.0, "bet_weighted": 0.0},
        "エアー":            {"combos": 0.0, "bet_weighted": 0.0},
    }
    # made hand (バリュー/BC/エアー)
    for name, v in hand_cats.items():
        cat = HC_5CAT.get(name)
        if cat:
            buckets[cat]["combos"]       += v["combos"]
            buckets[cat]["bet_weighted"] += v["combos"] * v["bet_pct"]
    # draw categories (ドロー/ウィークドロー)
    for name, v in draw_cats.items():
        cat = DC_5CAT.get(name)
        if cat:
            buckets[cat]["combos"]       += v["combos"]
            buckets[cat]["bet_weighted"] += v["combos"] * v["bet_pct"]

    result = {}
    for cat, d in buckets.items():
        if d["combos"] > 0:
            result[cat] = {
                "bet_pct": round(d["bet_weighted"] / d["combos"], 1),
                "combos":  round(d["combos"], 0),
            }
        else:
            result[cat] = None
    return result


# ─── メイン ──────────────────────────────────────────────────────
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
        print("❌ TOKEN 未設定  例: TOKEN=eyJ... python3 cash_5cat_gto.py")
        sys.exit(1)

    check_token()

    scenarios = {k: v for k, v in SCENARIOS.items() if not SCENARIO_F or k == SCENARIO_F}
    # 型ごとに最大 BOARDS_PER_TYPE ボードまで
    seen_types: dict[str, int] = {}
    boards = []
    for typ, board, desc in BOARDS:
        cnt = seen_types.get(typ, 0)
        if cnt < BOARDS_PER_TYPE:
            boards.append((typ, board, desc))
            seen_types[typ] = cnt + 1

    total = len(scenarios) * len(boards)
    print(f"\n調査開始: {len(scenarios)}シナリオ × {len(boards)}ボード = {total}コール")
    print(f"gametype: {GT}\n")

    all_results = {}   # scen → board → data
    done = 0

    for scen_name, scen in scenarios.items():
        all_results[scen_name] = {}
        for typ, board, desc in boards:
            done += 1
            key = f"{scen_name}/{typ}/{board}"
            print(f"  [{done:3d}/{total}] {key} ... ", end="", flush=True)

            data = call_api(board, scen["pf"])
            if data is None:
                print("SKIP")
                all_results[scen_name][board] = None
                time.sleep(1.0)
                continue

            ip_player = get_ip_player(data, scen["ip"])
            if not ip_player:
                print("IP取得失敗")
                all_results[scen_name][board] = None
                time.sleep(1.0)
                continue

            hc = extract_hand_cats(ip_player)
            dc = extract_draw_cats(ip_player)
            agg = aggregate_5cat(hc, dc)

            # 表示
            cats_str = "  ".join(
                f"{c[0]}:{v['bet_pct']:.0f}%"
                for c, v in [
                    ("V", agg.get("バリュー")),
                    ("D", agg.get("ドロー")),
                    ("BC", agg.get("ブラフキャッチャー")),
                    ("WD", agg.get("ウィークドロー")),
                    ("Air", agg.get("エアー")),
                ]
                if v is not None
            )
            print(f"OK  {cats_str}")

            all_results[scen_name][board] = {
                "type": typ, "board": board, "desc": desc,
                "hand_cats": hc, "draw_cats": dc, "5cat": agg,
            }
            time.sleep(4.0)

    # ─── JSON保存 ────────────────────────────────────────────────
    out_json = FINDINGS / "cash_5cat_gto.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ JSON保存: {out_json}")

    # ─── Markdown サマリー ────────────────────────────────────────
    generate_summary(all_results, boards, scenarios)


def generate_summary(all_results, boards, scenarios):
    lines = ["# 5類型 × ボード型 × シナリオ CBet% (GTO Wizard)", ""]

    # シナリオ別に表を出力
    for scen_name, scen in scenarios.items():
        lines.append(f"## {scen_name} — {scen['label']}")
        lines.append("")
        lines.append("| 型 | ボード | バリュー | ドロー | ブラフキャッチャー | ウィークドロー | エアー |")
        lines.append("|---|---|:---:|:---:|:---:|:---:|:---:|")

        for typ, board, desc in boards:
            entry = all_results.get(scen_name, {}).get(board)
            if entry is None:
                lines.append(f"| {typ} | `{board}` ({desc}) | — | — | — | — | — |")
                continue
            agg = entry["5cat"]
            def fmt(k):
                v = agg.get(k)
                return f"{v['bet_pct']:.0f}% (n={int(v['combos'])})" if v else "—"
            lines.append(
                f"| {typ} | `{board}` ({desc}) | {fmt('バリュー')} | {fmt('ドロー')} "
                f"| {fmt('ブラフキャッチャー')} | {fmt('ウィークドロー')} | {fmt('エアー')} |"
            )
        lines.append("")

    # 型別平均表（シナリオ横断）
    lines.append("## 型別 × シナリオ 平均CBet% — バリュー")
    lines.append("")
    scen_names = list(scenarios.keys())
    lines.append("| 型 | " + " | ".join(scen_names) + " |")
    lines.append("|---|" + "|".join([":---:"] * len(scen_names)) + "|")

    types_seen: list[str] = []
    for typ, _, _ in boards:
        if typ not in types_seen:
            types_seen.append(typ)

    for target_cat in ["バリュー", "ドロー", "ブラフキャッチャー", "ウィークドロー", "エアー"]:
        lines.append(f"\n## 型別平均 — {target_cat}")
        lines.append("| 型 | " + " | ".join(scen_names) + " |")
        lines.append("|---|" + "|".join([":---:"] * len(scen_names)) + "|")

        for typ in types_seen:
            type_boards = [b for t, b, _ in boards if t == typ]
            row = [typ]
            for sn in scen_names:
                vals = []
                for board in type_boards:
                    entry = all_results.get(sn, {}).get(board)
                    if entry and entry["5cat"].get(target_cat):
                        vals.append(entry["5cat"][target_cat]["bet_pct"])
                avg = f"{sum(vals)/len(vals):.0f}%" if vals else "—"
                row.append(avg)
            lines.append("| " + " | ".join(row) + " |")

    out_md = FINDINGS / "cash_5cat_gto_summary.md"
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"✅ サマリー: {out_md}")


if __name__ == "__main__":
    main()
