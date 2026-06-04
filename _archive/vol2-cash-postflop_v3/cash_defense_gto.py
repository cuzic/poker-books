#!/usr/bin/env python3
"""
cash_defense_gto.py — OOP守備 + IP守備(vs CR) × 5類型 × 6シナリオ

3ステップ:
  Step1: flop_actions="X"           → IP CBet% by 5類型
  Step2: flop_actions="X-{bet}"     → OOP Fold/Call/Raise by 5類型
  Step3: flop_actions="X-{bet}-{cr}"→ IP  Fold/Call/Raise by 5類型

使い方:
  TOKEN=eyJ... python3 cash_defense_gto.py
  TOKEN=eyJ... SCENARIO=BTN_BB python3 cash_defense_gto.py
  TOKEN=eyJ... BOARDS=1 python3 cash_defense_gto.py
"""

import os, sys, json, time, requests
from pathlib import Path

TOKEN      = os.environ.get("TOKEN", "")
GWCLIENTID = os.environ.get("GWCLIENTID", "")
GT         = os.environ.get("GT", "Cash6mGeneral_6mNL25R25")
SCENARIO_F = os.environ.get("SCENARIO", "")
BOARDS_PER_TYPE = int(os.environ.get("BOARDS", "1"))

BASE_URL = "https://api.gtowizard.com/v4/solutions/spot-solution/"
FINDINGS = Path(__file__).parent / "findings"
FINDINGS.mkdir(exist_ok=True)

SCENARIOS = {
    "BTN_BB": {"pf": "F-F-F-R2.5-F-C",  "ip": "BTN", "oop": "BB",  "label": "BTN vs BB"},
    "CO_BB":  {"pf": "F-F-R2.5-F-F-C",  "ip": "CO",  "oop": "BB",  "label": "CO vs BB"},
    "HJ_BB":  {"pf": "F-R2.5-F-F-F-C",  "ip": "HJ",  "oop": "BB",  "label": "HJ vs BB"},
    "UTG_BB": {"pf": "R2.5-F-F-F-F-C",  "ip": "UTG", "oop": "BB",  "label": "UTG vs BB"},
    "SB_BB":  {"pf": "F-F-F-F-R3-C",    "ip": "BB",  "oop": "SB",  "label": "SB vs BB"},
    "BTN_SB": {"pf": "F-F-F-R2.5-C-F",  "ip": "BTN", "oop": "SB",  "label": "BTN vs SB"},
}

BOARDS = [
    ("型1_ハイドライ",   "Ks7d2c", "K高・レインボー"),
    ("型1_ハイドライ",   "As9d3c", "A高・レインボー"),
    ("型1_ハイドライ",   "Qs7d3c", "Q高・レインボー"),
    ("型2_ハイウェット", "Qh8d3s", "Q高・2トーン"),
    ("型2_ハイウェット", "Kh9d5s", "K高・2トーン"),
    ("型2_ハイウェット", "Ah8s5d", "A高・2トーン"),
    ("型3_ロードライ",   "Jd7s5c", "J中・レインボー"),
    ("型3_ロードライ",   "9s6d2c", "9中・レインボー"),
    ("型3_ロードライ",   "8d5s2c", "8低・レインボー"),
    ("型4_ローウェット", "Th9s8d", "低連携・2トーン"),
    ("型4_ローウェット", "9h8d7s", "9連続・レインボー"),
    ("型4_ローウェット", "Jd9s8h", "J連携・2トーン"),
    ("型5_モノトーン",   "Ah9h5h", "A高モノトーン"),
    ("型5_モノトーン",   "Kd7d3d", "K高モノトーン"),
    ("型5_モノトーン",   "Qh8h4h", "Q中モノトーン"),
    ("型6_ペア高",       "AsAcKd", "AAKペア"),
    ("型6_ペア高",       "KhKd8c", "KK8ペア"),
    ("型6_ペア高",       "AhAdQs", "AAQペア"),
    ("型7_ペア低",       "7s7d2c", "77低ペア"),
    ("型7_ペア低",       "4s4d9c", "44中ペア"),
    ("型7_ペア低",       "5h5c2d", "55低ペア"),
]

HC_5CAT = {
    "straight_flush": "V", "quads": "V", "fullhouse": "V", "flush": "V",
    "straight": "V", "set": "V", "trips": "V", "two_pair": "V",
    "overpair": "V", "top_pair": "V",
    "second_pair": "BC", "underpair": "BC", "third_pair": "BC",
    "low_pair": "Air", "ace_high": "Air", "king_high": "Air",
    "queen_high": "Air", "jack_high": "Air", "ten_high": "Air", "no_made_hand": "Air",
}
DC_5CAT = {
    "combo_draw": "D", "nut_flush_draw": "D", "flush_draw": "D", "oesd": "D",
    "gutshot": "WD", "twocards_bdfd": "WD",
}
CAT_LABEL = {"V": "バリュー", "D": "ドロー", "BC": "ブラフキャッチャー",
             "WD": "ウィークドロー", "Air": "エアー"}
CAT_ORDER = ["V", "D", "BC", "WD", "Air"]


# ─── API ─────────────────────────────────────────────────────────
def make_headers():
    h = {"accept": "application/json, text/plain, */*",
         "authorization": f"Bearer {TOKEN}",
         "cache-control": "no-cache",
         "origin": "https://app.gtowizard.com",
         "pragma": "no-cache",
         "referer": "https://app.gtowizard.com/"}
    if GWCLIENTID:
        h["gwclientid"] = GWCLIENTID
    return h


def call_api(board, pf, flop_actions):
    params = {"gametype": GT, "depth": "100", "stacks": "",
              "preflop_actions": pf, "flop_actions": flop_actions,
              "turn_actions": "", "river_actions": "", "board": board}
    for attempt in range(4):
        r = requests.get(BASE_URL, params=params, headers=make_headers(), timeout=30)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            try:
                body = r.json()
                if body.get("time_period_in_seconds", 0) >= 86400:
                    ra = int(r.headers.get("Retry-After", 3600))
                    print(f"\n❌ 日次クォータ超過 ({ra//3600}h後リセット)")
                    sys.exit(1)
            except Exception:
                pass
            wait = 15 * (attempt + 1)
            print(f" [429 {wait}s]", end="", flush=True)
            time.sleep(wait)
            continue
        print(f" [HTTP {r.status_code}]", end="", flush=True)
        return None
    return None


def get_player(data, rel_pos):
    for p in data.get("players_info", []):
        if p.get("player", {}).get("relative_postflop_position") == rel_pos:
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
            else:            codes["betover"] = c
    return codes


def dominant_bet(codes):
    for k in ["bet33", "bet50", "bet75", "bet100", "betover", "bet20"]:
        if k in codes:
            return codes[k]
    return None


def agg_5cat(player, action_codes):
    """
    players_info エントリから 5類型別の加重平均行動頻度を計算。
    action_codes: {"fold": "F", "call": "C", "raise": "R6.4"} など
    """
    buckets = {c: {"n": 0.0, **{k: 0.0 for k in action_codes}} for c in CAT_ORDER}

    for hc in player.get("hand_categories", []):
        n = hc.get("total_combos", 0)
        if n < 0.3:
            continue
        cat = HC_5CAT.get(hc["name"])
        if not cat:
            continue
        af = hc.get("actions_total_frequencies", {})
        buckets[cat]["n"] += n
        for akey, acode in action_codes.items():
            buckets[cat][akey] += af.get(acode, 0.0) * n

    for dc in player.get("draw_categories", []):
        n = dc.get("total_combos", 0)
        if n < 0.3:
            continue
        cat = DC_5CAT.get(dc["name"])
        if not cat:
            continue
        af = dc.get("actions_total_frequencies", {})
        buckets[cat]["n"] += n
        for akey, acode in action_codes.items():
            buckets[cat][akey] += af.get(acode, 0.0) * n

    result = {}
    for cat in CAT_ORDER:
        b = buckets[cat]
        n = b["n"]
        if n < 0.3:
            continue
        result[cat] = {"n": round(n, 0)}
        for akey in action_codes:
            result[cat][akey] = round(b[akey] / n * 100, 1)
    return result


def print_5cat(label, data, actions):
    if not data:
        return
    print(f"    [{label}]")
    hdr = f"      {'':4s}"
    for a in actions:
        hdr += f" {a:>6}"
    hdr += "  (n)"
    print(hdr)
    for cat in CAT_ORDER:
        v = data.get(cat)
        if not v:
            continue
        row = f"      {cat:4s}"
        for a in actions:
            row += f" {v.get(a, 0):5.0f}%"
        row += f"  ({int(v['n'])})"
        print(row)


# ─── 3ステップ分析 ───────────────────────────────────────────────
def analyze(board, desc, btype, scen_name, scen):
    pf = scen["pf"]
    rec = {"board_type": btype, "board": board, "desc": desc,
           "scenario": scen_name, "s1": None, "s2": None, "s3": None}

    # Step1: IP CBet
    d1 = call_api(board, pf, "X")
    if not d1:
        return rec
    time.sleep(3.0)

    ip1 = get_player(d1, "IP")
    if not ip1:
        return rec
    ip_codes = classify_actions(d1.get("action_solutions", []))
    cbet_code = dominant_bet(ip_codes)

    # IP CBet用: bet% + check% のみ
    bet_akeys = {k: v for k, v in ip_codes.items() if k.startswith("bet")}
    if "check" in ip_codes:
        bet_akeys["check"] = ip_codes["check"]
    s1_data = agg_5cat(ip1, bet_akeys)
    rec["s1"] = {"cbet_code": cbet_code, "data": s1_data}

    if not cbet_code:
        return rec

    # Step2: OOP 守備 (Fold/Call/Raise)
    d2 = call_api(board, pf, f"X-{cbet_code}")
    if not d2:
        return rec
    time.sleep(3.0)

    oop2 = get_player(d2, "OOP")
    if not oop2:
        return rec
    oop_codes = classify_actions(d2.get("action_solutions", []))
    oop_akeys = {}
    if "fold" in oop_codes: oop_akeys["fold"]  = oop_codes["fold"]
    if "call" in oop_codes: oop_akeys["call"]  = oop_codes["call"]
    cr_code = dominant_bet(oop_codes)
    if cr_code:              oop_akeys["raise"] = cr_code
    s2_data = agg_5cat(oop2, oop_akeys)
    rec["s2"] = {"cr_code": cr_code, "data": s2_data}

    if not cr_code:
        return rec

    # Step3: IP vs CR (Fold/Call/3Bet)
    d3 = call_api(board, pf, f"X-{cbet_code}-{cr_code}")
    if not d3:
        return rec
    time.sleep(3.0)

    ip3 = get_player(d3, "IP")
    if not ip3:
        return rec
    ip3_codes = classify_actions(d3.get("action_solutions", []))
    ip3_akeys = {}
    if "fold" in ip3_codes: ip3_akeys["fold"]  = ip3_codes["fold"]
    if "call" in ip3_codes: ip3_akeys["call"]  = ip3_codes["call"]
    r3b = dominant_bet(ip3_codes)
    if r3b:                  ip3_akeys["raise"] = r3b
    s3_data = agg_5cat(ip3, ip3_akeys)
    rec["s3"] = {"r3b_code": r3b, "data": s3_data}

    return rec


# ─── Markdown サマリー ────────────────────────────────────────────
def gen_markdown(results):
    lines = ["# OOP守備 + IP守備(vs CR) × 5類型 GTO Wizard", ""]

    SCENS = list(dict.fromkeys(r["scenario"] for r in results))
    TYPES = list(dict.fromkeys(r["board_type"] for r in results))

    for step_key, step_label, actions in [
        ("s1", "IP CBet（Bet/Check）",          ["bet33","bet50","bet75","check"]),
        ("s2", "OOP 守備（Fold/Call/Raise）",    ["fold","call","raise"]),
        ("s3", "IP vs CR（Fold/Call/Raise）",    ["fold","call","raise"]),
    ]:
        lines.append(f"## {step_label}")
        lines.append("")

        for cat in CAT_ORDER:
            cat_label = CAT_LABEL[cat]
            for action in actions:
                # シナリオ×ボード型のクロス表
                rows = {}
                for r in results:
                    step = r.get(step_key)
                    if not step:
                        continue
                    v = step["data"].get(cat, {}).get(action)
                    if v is None:
                        continue
                    rows.setdefault(r["board_type"], {})[r["scenario"]] = v

                if not rows:
                    continue

                lines.append(f"### {cat_label} / {action}%")
                hdr = "| 型 | " + " | ".join(SCENS) + " |"
                sep = "|---|" + "|".join([":---:"] * len(SCENS)) + "|"
                lines.append(hdr)
                lines.append(sep)
                for btype in TYPES:
                    if btype not in rows:
                        continue
                    vals = " | ".join(
                        f"{rows[btype].get(s, '—')}" if isinstance(rows[btype].get(s), str)
                        else f"{rows[btype][s]:.0f}%" if s in rows[btype] else "—"
                        for s in SCENS
                    )
                    lines.append(f"| {btype} | {vals} |")
                lines.append("")

    # ─── 個別ボード詳細 ──────────────────────────────────────────
    lines.append("---")
    lines.append("## 個別ボード詳細")
    lines.append("")
    for r in results:
        lines.append(f"### {r['board_type']} / `{r['board']}` ({r['desc']}) — {r['scenario']}")
        lines.append("")
        for step_key, step_label, actions in [
            ("s1", "IP CBet",     ["bet33","bet50","bet75","check"]),
            ("s2", "OOP守備",     ["fold","call","raise"]),
            ("s3", "IP vs CR",    ["fold","call","raise"]),
        ]:
            step = r.get(step_key)
            if not step or not step.get("data"):
                continue
            present = [a for a in actions if any(a in v for v in step["data"].values() if isinstance(v, dict))]
            if not present:
                continue
            lines.append(f"**{step_label}**")
            lines.append("")
            hdr = "| 類型 | " + " | ".join(present) + " | n |"
            sep = "|---|" + "|".join([":---:"] * len(present)) + "|:---:|"
            lines.append(hdr)
            lines.append(sep)
            for cat in CAT_ORDER:
                v = step["data"].get(cat)
                if not v:
                    continue
                vals = " | ".join(f"{v.get(a, 0):.0f}%" for a in present)
                lines.append(f"| {CAT_LABEL[cat]} | {vals} | {int(v['n'])} |")
            lines.append("")

    out = FINDINGS / "cash_defense_gto_summary.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Markdown: {out}")


# ─── メイン ──────────────────────────────────────────────────────
def check_token():
    import base64 as _b64
    try:
        p = TOKEN.split('.')[1]; p += '='*(-len(p)%4)
        d = json.loads(_b64.urlsafe_b64decode(p))
        rem = d['exp'] - time.time()
        if rem <= 60:
            print(f"❌ TOKEN期限切れ"); sys.exit(1)
        print(f"✅ 認証OK（残り{rem/60:.1f}分）")
        return rem
    except Exception as e:
        print(f"❌ TOKEN失敗: {e}"); sys.exit(1)


def main():
    if not TOKEN:
        print("❌ TOKEN未設定"); sys.exit(1)
    rem = check_token()

    scens = {k: v for k, v in SCENARIOS.items() if not SCENARIO_F or k == SCENARIO_F}
    seen: dict[str, int] = {}
    boards = []
    for typ, board, desc in BOARDS:
        if seen.get(typ, 0) < BOARDS_PER_TYPE:
            boards.append((typ, board, desc))
            seen[typ] = seen.get(typ, 0) + 1

    total = len(scens) * len(boards)
    est = total * 3 * 3.5
    print(f"\n{len(scens)}シナリオ × {len(boards)}ボード = {total}セット / {total*3}コール / 推定{est/60:.1f}分")
    if est > rem - 30:
        print(f"⚠️  TOKEN残り{rem/60:.1f}分 < 推定{est/60:.1f}分")

    all_results = []
    done = 0
    for sname, scen in scens.items():
        for typ, board, desc in boards:
            done += 1
            print(f"\n[{done}/{total}] {sname}/{typ}/{board}", end="", flush=True)
            rec = analyze(board, desc, typ, sname, scen)
            all_results.append(rec)

            # 簡易表示
            s2 = rec.get("s2") or {}
            s3 = rec.get("s3") or {}
            if s2.get("data"):
                print_5cat("OOP守備", s2["data"], ["fold","call","raise"])
            if s3.get("data"):
                print_5cat("IP vs CR", s3["data"], ["fold","call","raise"])

    out = FINDINGS / "cash_defense_gto.json"
    out.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ JSON: {out}")
    gen_markdown(all_results)


if __name__ == "__main__":
    main()
