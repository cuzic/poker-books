#!/usr/bin/env python3
"""
ターンレベルのドロー戦略調査スクリプト

Phase 1: 動作検証（4 APIコール）
  - ターンAPIで draw_categories が取れるか確認
  - CBet-Call後 と Check-Check後 の2パスを確認

Phase 2: 全収集（27 APIコール）
  - 3シナリオ × 3ボード × 3ターンカード
  - CBet-Call後のIPアクション（draw_categories別継続率）

使い方:
  TOKEN=eyJ... GWCLIENTID=xxx python3 cash_turn_draw.py probe
  TOKEN=eyJ... GWCLIENTID=xxx python3 cash_turn_draw.py all
"""

import os, sys, json, time, requests
from pathlib import Path

TOKEN      = os.environ.get("TOKEN", "")
GWCLIENTID = os.environ.get("GWCLIENTID", "")
GT         = "Cash6mGeneral_6mNL25R25"
BASE_URL   = "https://api.gtowizard.com/v4/solutions/spot-solution/"
FINDINGS   = Path(__file__).parent / "findings"
FINDINGS.mkdir(exist_ok=True)

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "authorization": f"Bearer {TOKEN}",
    "gwclientid": GWCLIENTID,
    "origin": "https://app.gtowizard.com",
    "referer": "https://app.gtowizard.com/",
}

# ── 調査シナリオ（PF文脈3種） ─────────────────────────────────
# BTN_BB: Class B SRP（ポジション優位・レンジ均等）
# UTG_BB: Class A SRP（レンジ優位・UTGはタイト）
# BTN_3BP: Class D 3BP（3betポット・BTN IP）
SCENARIOS = {
    "BTN_BB":  {"pf": "F-F-F-R2.5-F-C",    "desc": "BTN vs BB SRP"},
    "UTG_BB":  {"pf": "R2.5-F-F-F-F-C",    "desc": "UTG vs BB SRP (レンジ強)"},
    "BTN_3BP": {"pf": "F-F-F-R2.5-F-R9-C", "desc": "BTN vs BB 3BP"},
}

# ── ターン調査ボード（ドロー多いフロップ優先） ─────────────────
# flop_bet: シナリオ別フロップ支配ベットコード（multistreet_*.json 実測値）
TURN_BOARDS = [
    {
        "board_type": "型4_ローウェット",
        "flop":       "Th9s8d",
        "flop_bet":   {"BTN_BB": "R1.8", "UTG_BB": "R1.8", "BTN_3BP": "R11.2"},
        "turns": [
            ("blank",      "2c", "ブランク"),
            ("completing", "7c", "ストレート完成(低)"),
            ("completing", "6c", "ストレート完成(高)"),
        ],
        "note": "OESD(JTs/97s/87s) + gutshot豊富",
    },
    {
        "board_type": "型3_ロードライ",
        "flop":       "Jd7s5c",
        "flop_bet":   {"BTN_BB": "R6.4", "UTG_BB": "R6.4", "BTN_3BP": "R11.2"},
        "turns": [
            ("blank",      "2c", "ブランク"),
            ("completing", "4c", "ストレート完成(4-5-6-7-8)"),
            ("TA+",        "7h", "ペア(中段)"),
        ],
        "note": "OESD(86s/64s) + 逆転ドロー高頻度ベット",
    },
    {
        "board_type": "型5_モノトーン",
        "flop":       "Ah9h5h",
        "flop_bet":   {"BTN_BB": "R1.8", "UTG_BB": "R1.8", "BTN_3BP": "R3.7"},
        "turns": [
            ("blank",      "2c", "ブランク(非ハート)"),
            ("completing", "4h", "フラッシュ完成(4th♥)"),
            ("TA+",        "9d", "2ndペア"),
        ],
        "note": "flush_draw + nut_flush_draw戦略",
    },
]

# ── API ──────────────────────────────────────────────────────────
def call_api(board, flop_actions="", turn_actions="", pf="F-F-F-R2.5-F-C"):
    params = {
        "gametype": GT,
        "depth": "100",
        "stacks": "",
        "preflop_actions": pf,
        "flop_actions": flop_actions,
        "turn_actions": turn_actions,
        "river_actions": "",
        "board": board,
    }
    r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
    if r.status_code != 200:
        print(f"  HTTP {r.status_code}: {r.text[:100]}")
        return None
    d = r.json()
    if "action_solutions" not in d:
        print(f"  ERR: {d.get('code','?')} {d.get('detail','')[:80]}")
        return None
    return d

def extract_draw_categories(data, target_pos="IP"):
    for pi in data.get("players_info", []):
        if pi["player"]["relative_postflop_position"] != target_pos:
            continue
        result = {}
        for dc in pi.get("draw_categories", []):
            combos = dc["total_combos"]
            if combos < 0.3:
                continue
            af = dc.get("actions_total_frequencies", {})
            bet = sum(v for k, v in af.items() if k.startswith("R"))
            result[dc["name"]] = {
                "combos": round(combos, 1),
                "bet_pct": round(bet * 100, 1),
            }
        return result
    return {}

def extract_hand_categories(data, target_pos="IP"):
    for pi in data.get("players_info", []):
        if pi["player"]["relative_postflop_position"] != target_pos:
            continue
        result = {}
        for hc in pi.get("hand_categories", []):
            combos = hc["total_combos"]
            if combos < 0.3:
                continue
            af = hc.get("actions_total_frequencies", {})
            bet = sum(v for k, v in af.items() if k.startswith("R"))
            result[hc["name"]] = {
                "combos": round(combos, 1),
                "bet_pct": round(bet * 100, 1),
            }
        return result
    return {}

def fmt_draw(dc):
    """draw_categories を 1行サマリー文字列に"""
    key_types = ["no_draw", "gutshot", "oesd", "flush_draw", "nut_flush_draw", "combo_draw"]
    parts = []
    for k in key_types:
        if k in dc:
            parts.append(f"{k.replace('_','')[:6]}={dc[k]['bet_pct']:.0f}%")
    return "  ".join(parts) if parts else "(なし)"

# ── Phase 1: 動作検証 ─────────────────────────────────────────
def phase1_probe():
    print("=" * 65)
    print("Phase 1: ターン draw_categories 動作検証")
    print("=" * 65)

    ok_count = 0

    # Test 1: BTN_BB / Th9s8d + 2c / CBet-Call後 / OOP-check → IP-turn
    print("\n[Test 1] BTN_BB / Th9s8d2c (blank) / CBet-Call後 / IPターンアクション")
    d = call_api("Th9s8d2c", flop_actions="X-R1.8-C", turn_actions="X",
                  pf="F-F-F-R2.5-F-C")
    if d:
        dc = extract_draw_categories(d, "IP")
        hc = extract_hand_categories(d, "IP")
        if dc:
            print(f"  ✅ draw_categories: {list(dc.keys())}")
            for name, v in dc.items():
                print(f"     {name:20s}  combos={v['combos']:5.1f}  bet%={v['bet_pct']:5.1f}%")
            ok_count += 1
        else:
            print("  ⚠️  draw_categories 空（hand_categoriesで代替確認）")
            for name, v in list(hc.items())[:5]:
                print(f"     {name:20s}  combos={v['combos']:5.1f}  bet%={v['bet_pct']:5.1f}%")
    else:
        print("  ❌ FAIL")
    time.sleep(0.6)

    # Test 2: BTN_BB / Th9s8d + 7c (completing) / CBet-Call後
    print("\n[Test 2] BTN_BB / Th9s8d7c (ストレート完成) / CBet-Call後 / IPターンアクション")
    d = call_api("Th9s8d7c", flop_actions="X-R1.8-C", turn_actions="X",
                  pf="F-F-F-R2.5-F-C")
    if d:
        dc = extract_draw_categories(d, "IP")
        if dc:
            print(f"  ✅ draw_categories: {fmt_draw(dc)}")
            ok_count += 1
        else:
            print("  ⚠️  draw_categories 空")
            hc = extract_hand_categories(d, "IP")
            for name, v in list(hc.items())[:3]:
                print(f"     {name}: bet%={v['bet_pct']:.1f}%")
    else:
        print("  ❌ FAIL")
    time.sleep(0.6)

    # Test 3: BTN_BB / Jd7s5c + 2c / CBet-Call後（型3: 100%ポットベット=R6.4）
    print("\n[Test 3] BTN_BB / Jd7s5c2c (blank) / CBet-Call後(R6.4) / IPターンアクション")
    d = call_api("Jd7s5c2c", flop_actions="X-R6.4-C", turn_actions="X",
                  pf="F-F-F-R2.5-F-C")
    if d:
        dc = extract_draw_categories(d, "IP")
        if dc:
            print(f"  ✅ draw_categories: {fmt_draw(dc)}")
            ok_count += 1
        else:
            print("  ⚠️  draw_categories 空")
    else:
        print("  ❌ FAIL")
    time.sleep(0.6)

    # Test 4: BTN_BB / Th9s8d + 2c / Check-Check後（フロップ無ベット）
    print("\n[Test 4] BTN_BB / Th9s8d2c (blank) / Check-Check後 / IPターンアクション")
    d = call_api("Th9s8d2c", flop_actions="X-X", turn_actions="X",
                  pf="F-F-F-R2.5-F-C")
    if d:
        dc = extract_draw_categories(d, "IP")
        if dc:
            print(f"  ✅ draw_categories: {fmt_draw(dc)}")
            ok_count += 1
        else:
            print("  ⚠️  draw_categories 空")
    else:
        print("  ❌ FAIL")
    time.sleep(0.6)

    if ok_count >= 2:
        print(f"\n✅ Phase 1 完了 ({ok_count}/4 成功) → Phase 2 に進んでください")
        return True
    else:
        print(f"\n❌ Phase 1 失敗 ({ok_count}/4) → APIの確認が必要です")
        return False

# ── Phase 2: 全収集 ───────────────────────────────────────────
def phase2_full():
    print("\n" + "=" * 65)
    print("Phase 2: ターンdraw_categories 全収集")
    print(f"  {len(SCENARIOS)} シナリオ × {len(TURN_BOARDS)} ボード × 3 ターンカード")
    total = len(SCENARIOS) * len(TURN_BOARDS) * 3
    print(f"  合計 {total} APIコール")
    print("=" * 65)

    all_results = {}
    done = 0

    for scen_name, scen in SCENARIOS.items():
        all_results[scen_name] = {}
        for board_cfg in TURN_BOARDS:
            bt    = board_cfg["board_type"]
            flop  = board_cfg["flop"]
            note  = board_cfg["note"]
            all_results[scen_name][bt] = {}

            print(f"\n  === {scen_name} / {bt} ({note}) ===")

            for turn_tag, turn_card, turn_desc in board_cfg["turns"]:
                done += 1
                board4 = flop + turn_card
                label  = f"[{done}/{total}] {scen_name}/{bt}/turn={turn_card}({turn_desc})"
                print(f"  {label} ... ", end="", flush=True)

                # CBet-Call後のIPターンアクション
                flop_bet = board_cfg["flop_bet"][scen_name]
                d = call_api(
                    board4,
                    flop_actions=f"X-{flop_bet}-C",
                    turn_actions="X",
                    pf=scen["pf"],
                )
                if d is None:
                    print("SKIP")
                    time.sleep(0.4)
                    continue

                ip_draw = extract_draw_categories(d, "IP")
                oop_draw = extract_draw_categories(d, "OOP")
                ip_hc   = extract_hand_categories(d, "IP")

                print(f"OK  {fmt_draw(ip_draw)}")

                all_results[scen_name][bt][turn_card] = {
                    "turn_tag":  turn_tag,
                    "turn_desc": turn_desc,
                    "board4":    board4,
                    "flop_bet":  flop_bet,
                    "ip_draw":   ip_draw,
                    "oop_draw":  oop_draw,
                    "ip_hand":   ip_hc,
                }
                time.sleep(0.5)

    out = FINDINGS / "turn_draw_categories.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Phase 2 完了 → {out}")
    return all_results

# ── Phase 3: サマリー表示 ─────────────────────────────────────
def phase3_summary(results):
    print("\n" + "=" * 65)
    print("Phase 3: ターンドロー継続率サマリー")
    print("=" * 65)

    draw_types = ["no_draw", "gutshot", "oesd", "flush_draw", "nut_flush_draw"]

    for board_cfg in TURN_BOARDS:
        bt   = board_cfg["board_type"]
        flop = board_cfg["flop"]
        print(f"\n【{bt} ({flop})】")
        print(f"  {'シナリオ':12s}  {'ターン':6s}  ", end="")
        for dt in draw_types:
            print(f"  {dt[:8]:>8s}", end="")
        print()
        print("  " + "-" * 75)

        for scen_name in SCENARIOS:
            for turn_tag, turn_card, turn_desc in board_cfg["turns"]:
                row = results.get(scen_name, {}).get(bt, {}).get(turn_card)
                if not row:
                    continue
                ip_draw = row.get("ip_draw", {})
                print(f"  {scen_name:12s}  {turn_card}({turn_tag[:5]:5s})", end="")
                for dt in draw_types:
                    v = ip_draw.get(dt)
                    if v:
                        pct = f"{v['bet_pct']:.0f}%"
                    else:
                        pct = "—"
                    print(f"  {pct:>8s}", end="")
                print()

    # 重要インサイト抽出
    print("\n【重要比較: 型4 blank(2c) vs completing(7c)】")
    for scen_name in ["BTN_BB", "UTG_BB"]:
        row_blank = results.get(scen_name, {}).get("型4_ローウェット", {}).get("2c", {})
        row_comp  = results.get(scen_name, {}).get("型4_ローウェット", {}).get("7c", {})
        if row_blank and row_comp:
            for dt in ["oesd", "gutshot", "no_draw"]:
                b = row_blank.get("ip_draw", {}).get(dt, {})
                c = row_comp.get("ip_draw",  {}).get(dt, {})
                if b or c:
                    b_pct = f"{b['bet_pct']:.0f}%" if b else "—"
                    c_pct = f"{c['bet_pct']:.0f}%" if c else "—"
                    print(f"  {scen_name}/{dt}: blank={b_pct} vs completing={c_pct}")

# ── エントリポイント ──────────────────────────────────────────
if __name__ == "__main__":
    if not TOKEN:
        print("❌ TOKEN 環境変数が未設定です")
        print("   TOKEN=eyJ... GWCLIENTID=xxx python3 cash_turn_draw.py probe")
        sys.exit(1)

    cmd = sys.argv[1] if len(sys.argv) > 1 else "probe"

    if cmd == "probe":
        phase1_probe()

    elif cmd == "all":
        ok = phase1_probe()
        if not ok:
            print("\n⚠️  Phase 1 失敗のため中断。TOKEN/APIを確認してください。")
            sys.exit(1)
        results = phase2_full()
        phase3_summary(results)

    elif cmd == "phase2":
        results = phase2_full()
        phase3_summary(results)

    elif cmd == "summary":
        out = FINDINGS / "turn_draw_categories.json"
        if not out.exists():
            print("❌ turn_draw_categories.json が見つかりません。先に 'all' を実行してください。")
            sys.exit(1)
        with open(out) as f:
            results = json.load(f)
        phase3_summary(results)

    else:
        print(f"不明なコマンド: {cmd}")
        print("使い方: TOKEN=eyJ... python3 cash_turn_draw.py [probe|all|phase2|summary]")
