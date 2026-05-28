#!/usr/bin/env python3
"""
cash_multiway.py — マルチウェイポット分析

3人ポットでのポストフロップ行動:
  BTN open → SB call → BB call (3-way)

主な調査項目:
  - BTN (IP) のCBet率変化 (HU比)
  - SB/BB のディフェンス変化
  - ナッツ偏重の程度

NOTE: GTO Wizard が3wayをサポートしているか確認が必要。
      サポートされていない場合はその旨を記録してスキップ。

使い方:
  TOKEN=eyJ... python3 cash_multiway.py
"""

import os, sys, json, time, requests
from pathlib import Path

TOKEN      = os.environ.get("TOKEN", "")
GWCLIENTID = os.environ.get("GWCLIENTID", "")
GT         = os.environ.get("GT", "Cash6mGeneral_6mNL25R25")

FINDINGS_DIR = Path(__file__).parent / "findings"
FINDINGS_DIR.mkdir(exist_ok=True)

BASE_URL = "https://api.gtowizard.com/v4/solutions/spot-solution/"

# ─────────────────── プリフロップシナリオ ───────────────────
# 3-way: UTG/HJ/CO fold, BTN opens 2.5, SB calls, BB calls
SCENARIO_3WAY = {
    "label":  "3-way SRP: BTN vs SB vs BB",
    "pf":     "F-F-F-R2.5-C-C",   # UTG fold, HJ fold, CO fold, BTN R2.5, SB call, BB call
    "actors": ["BTN", "SB", "BB"],  # postflop: BTN は最後（IP）、SB/BB はOOP
    "ip":     "BTN",
    "oop1":   "SB",
    "oop2":   "BB",
    "depth":  100,
}

# 比較用: HU BTN vs BB (SRPの標準シナリオ)
SCENARIO_HU = {
    "label": "HU SRP BTN vs BB (比較用)",
    "pf":    "F-F-F-R2.5-F-C",    # CO/SB fold, BTN opens, BB calls
    "ip":    "BTN",
    "oop":   "BB",
    "depth": 100,
}

# ─────────────────── ボード設定 ───────────────────
# マルチウェイで特に重要な2型に絞る
BOARD_CONFIGS = [
    {
        "type":  "型1_ハイドライ",
        "flop":  "Ks7d2c",
        "desc":  "K高・レインボー (IP有利なドライボード)",
    },
    {
        "type":  "型4_ローウェット",
        "flop":  "Th9s8d",
        "desc":  "低連携・2トーン (ナッツ偏重が出やすいウェットボード)",
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
            wait = 10 * (attempt + 1)
            print(f"  [HTTP 429] board={board} flop={flop_actions!r} → {wait}s 待機中...")
            time.sleep(wait)
            continue
        # 400/404/500 など: 詳細メッセージも表示
        try:
            detail = r.json()
        except Exception:
            detail = r.text[:200]
        print(f"  [HTTP {r.status_code}] board={board} flop={flop_actions!r}: {detail}")
        return None
    print(f"  [429 最大リトライ超過] board={board}")
    return None


def get_player(data, pos):
    for p in data.get("players_info", []):
        if isinstance(p.get("player"), dict) and p["player"].get("position") == pos:
            return p
    return None


def count_players(data):
    """レスポンスに含まれるプレイヤー数を返す。"""
    return len(data.get("players_info", []))


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


def weighted_bet_rate(rows, bet_keys):
    """コンボ加重平均ベット率。ベット選択肢なしなら None。"""
    if not bet_keys or not rows:
        return None
    total_combos = sum(r["total"] for r in rows)
    if total_combos == 0:
        return None
    return sum(r["total"] * sum(r.get(k, 0) or 0 for k in bet_keys) for r in rows) / total_combos


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
    if not rows:
        return []
    bet_keys = [k for k in codes_dict if k not in ("fold",)]
    return [
        {k: (round(v * 100, 1) if isinstance(v, float) else v)
         for k, v in row.items()
         if k in ("hc", "total", "share") or k in bet_keys}
        for row in rows
    ]


# ─────────────────── 3-way サポート確認 ───────────────────

def check_multiway_support():
    """
    3-way pf で Ks7d2c フロップを叩いて、APIが3wayをサポートするか確認。
    - 成功 (200) → players_info の人数を返す
    - 失敗 → None を返す
    """
    pf = SCENARIO_3WAY["pf"]
    print(f"  テストクエリ: pf={pf!r} board=Ks7d2c")
    data = call_api("Ks7d2c", flop_actions="", pf=pf, depth=100)
    time.sleep(4.0)
    if data is None:
        return None, "API呼び出し失敗（HTTP エラーまたは接続失敗）"
    n = count_players(data)
    positions = [
        p["player"]["position"]
        for p in data.get("players_info", [])
        if isinstance(p.get("player"), dict)
    ]
    return n, positions


# ─────────────────── HU 比較データ取得 ───────────────────

def run_hu_comparison():
    """HU BTN vs BB のCBet率を取得（3wayとの比較基準）。"""
    scen  = SCENARIO_HU
    pf    = scen["pf"]
    ip    = scen["ip"]
    depth = scen["depth"]

    print(f"\n--- HU 比較データ取得中: {scen['label']} ---")
    results = {}

    for cfg in BOARD_CONFIGS:
        flop = cfg["flop"]
        data = call_api(flop, flop_actions="", pf=pf, depth=depth)
        time.sleep(4.0)
        if not data:
            print(f"  [{cfg['type']}] HU データ取得失敗")
            results[cfg["type"]] = None
            continue
        player = get_player(data, ip)
        sols   = data.get("action_solutions", [])
        if not player or not sols:
            print(f"  [{cfg['type']}] HU プレイヤーデータなし")
            results[cfg["type"]] = None
            continue
        codes    = classify_actions(sols)
        rows     = calc_hc_action_rates(sols, player, codes)
        bet_keys = [k for k in codes if k not in ("check", "fold")]
        rate     = weighted_bet_rate(rows, bet_keys)
        results[cfg["type"]] = {
            "cbet_pct": round(rate * 100, 1) if rate is not None else None,
            "by_category": rows_to_store(rows, codes),
        }
        print(f"  [{cfg['type']}] HU CBet率: {rate*100:.0f}%" if rate is not None
              else f"  [{cfg['type']}] HU CBet率: 取得失敗")
        time.sleep(2.0)

    return results


# ─────────────────── 3-way 分析本体 ───────────────────

def run_multiway_analysis(n_players, positions):
    """3-way サポート確認済みの場合に実行。"""
    scen  = SCENARIO_3WAY
    pf    = scen["pf"]
    ip    = scen["ip"]
    depth = scen["depth"]

    print(f"\n{'='*70}")
    print(f"3-way 分析開始: {scen['label']}")
    print(f"players_info 人数={n_players}, positions={positions}")

    all_results = []

    for cfg in BOARD_CONFIGS:
        flop = cfg["flop"]
        print(f"\n{'='*70}")
        print(f"【{cfg['type']}】 {flop}  ({cfg['desc']})")

        # ── BTN (IP最後) のCBet（3-wayでの先手行動）──
        data = call_api(flop, flop_actions="", pf=pf, depth=depth)
        time.sleep(4.0)
        if not data:
            print(f"  3-way フロップデータ取得失敗")
            all_results.append({
                "type": cfg["type"], "flop": flop, "desc": cfg["desc"],
                "error": "API取得失敗",
            })
            continue

        n_actual   = count_players(data)
        print(f"  players_info 人数: {n_actual}")

        # 実際にIPプレイヤーが取れるか
        ip_player = get_player(data, ip)
        sols      = data.get("action_solutions", [])
        if not ip_player or not sols:
            print(f"  BTN(IP) データなし。OOP先手（SBかBBが先手）の可能性。")
            # 3-wayではSBがOOP先手になる場合がある
            sb_player = get_player(data, scen["oop1"])
            bb_player = get_player(data, scen["oop2"])
            active_pos = None
            active_player = None
            if sb_player:
                active_pos    = scen["oop1"]
                active_player = sb_player
                print(f"  アクティブプレイヤー: SB (OOP1)")
            elif bb_player:
                active_pos    = scen["oop2"]
                active_player = bb_player
                print(f"  アクティブプレイヤー: BB (OOP2)")

            if not active_player:
                print(f"  どのプレイヤーも取得不可")
                all_results.append({
                    "type": cfg["type"], "flop": flop, "desc": cfg["desc"],
                    "error": "プレイヤーデータなし",
                })
                continue
            codes    = classify_actions(sols)
            rows     = calc_hc_action_rates(sols, active_player, codes)
            bet_keys = [k for k in codes if k not in ("check", "fold")]
            rate     = weighted_bet_rate(rows, bet_keys)
            print(f"  {active_pos} ベット率: {rate*100:.0f}%" if rate is not None
                  else f"  {active_pos} ベット率: チェックのみ")
            print_hc_table(rows, f"hand_category別 {active_pos} アクション（シェア付き）")
            all_results.append({
                "type":          cfg["type"],
                "flop":          flop,
                "desc":          cfg["desc"],
                "first_actor":   active_pos,
                "total_bet_pct": round(rate * 100, 1) if rate is not None else None,
                "by_category":   rows_to_store(rows, codes),
            })
        else:
            codes    = classify_actions(sols)
            rows     = calc_hc_action_rates(sols, ip_player, codes)
            bet_keys = [k for k in codes if k not in ("check", "fold")]
            rate     = weighted_bet_rate(rows, bet_keys)
            print(f"  BTN CBet率（総合）: {rate*100:.0f}%" if rate is not None
                  else f"  BTN CBet率: チェックのみ")
            print_hc_table(rows, "hand_category別 BTN CBet（シェア付き）")
            all_results.append({
                "type":          cfg["type"],
                "flop":          flop,
                "desc":          cfg["desc"],
                "first_actor":   "BTN",
                "total_bet_pct": round(rate * 100, 1) if rate is not None else None,
                "by_category":   rows_to_store(rows, codes),
            })

        time.sleep(2.0)

    return all_results


# ─────────────────── メイン ───────────────────

def main():
    if not TOKEN:
        print("❌ TOKEN 未設定"); sys.exit(1)

    print(f"gametype: {GT}")
    print(f"\n{'='*70}")
    print(f"STEP 1: GTO Wizard 3-way サポート確認")
    print(f"{'='*70}")
    print(f"  pf={SCENARIO_3WAY['pf']!r}")

    n_players, positions_or_msg = check_multiway_support()

    output = {
        "scenario_3way": SCENARIO_3WAY["label"],
        "scenario_hu":   SCENARIO_HU["label"],
        "gametype":      GT,
        "multiway_api_support": None,
        "multiway_api_note":    "",
        "hu_comparison":        {},
        "multiway_results":     [],
    }

    if n_players is None:
        # API失敗（おそらく3wayは非サポート）
        note = (
            f"3-wayプリフロップ (pf={SCENARIO_3WAY['pf']!r}) でAPIエラー。"
            f"GTO Wizardの標準 Cash6m gametype は2プレイヤー限定と思われる。"
            f"エラー詳細: {positions_or_msg}"
        )
        print(f"\n  ❌ 3-way サポートなし: {note}")
        output["multiway_api_support"] = False
        output["multiway_api_note"]    = note
    else:
        print(f"\n  ✅ API レスポンス成功: players={n_players}, positions={positions_or_msg}")
        if n_players >= 3:
            print(f"  ✅ 3-way サポート確認！players_info に {n_players} 人")
            output["multiway_api_support"] = True
            output["multiway_api_note"]    = (
                f"3-way サポート確認済み。players_info={n_players}人, positions={positions_or_msg}"
            )
        else:
            note = (
                f"pf={SCENARIO_3WAY['pf']!r} で players_info={n_players} 人のみ。"
                f"positions={positions_or_msg}。"
                f"GTO Wizard がコールをフォールドとして処理し、"
                f"実際には2プレイヤーに縮退した可能性あり。"
                f"3-way解析には専用 gametype が必要な可能性。"
            )
            print(f"\n  ⚠️  players={n_players} (3未満): {note}")
            output["multiway_api_support"] = False
            output["multiway_api_note"]    = note

    print(f"\n{'='*70}")
    print(f"STEP 2: HU 比較データ取得 ({SCENARIO_HU['label']})")
    print(f"{'='*70}")
    hu_data = run_hu_comparison()
    output["hu_comparison"] = hu_data

    if output["multiway_api_support"]:
        print(f"\n{'='*70}")
        print(f"STEP 3: 3-way 分析実行")
        print(f"{'='*70}")
        mw_results = run_multiway_analysis(n_players, positions_or_msg)
        output["multiway_results"] = mw_results

        # HU vs 3-way 比較サマリー
        print(f"\n{'='*70}")
        print(f"★ HU vs 3-way CBet率 比較サマリー")
        print(f"  {'型':20s} | {'HU CBet%':>9} | {'3W CBet%':>9}")
        print(f"  {'-'*45}")
        for cfg in BOARD_CONFIGS:
            hu_pct = (hu_data.get(cfg["type"]) or {}).get("cbet_pct")
            mw_rec = next((r for r in mw_results if r["type"] == cfg["type"]), {})
            mw_pct = mw_rec.get("total_bet_pct")
            print(f"  {cfg['type']:20s} | "
                  f"{str(round(hu_pct))+'%' if hu_pct is not None else '—':>9} | "
                  f"{str(round(mw_pct))+'%' if mw_pct is not None else '—':>9}")
    else:
        print(f"\n{'='*70}")
        print(f"STEP 3: SKIP (3-way 非サポートのため)")
        print(f"  → HU 比較データのみ保存")
        print(f"\n【マルチウェイ分析メモ】")
        print(f"  GTO Wizard の Cash6m gametype は基本的に heads-up ポストフロップ前提。")
        print(f"  3-way の正確な解析には PioSOLVER 等の別ツールが必要な可能性あり。")
        print(f"  代替アプローチ: ")
        print(f"    1. GTO Wizard の Multiway 専用 gametype を探す（存在する場合）")
        print(f"    2. PioSOLVER で 3-way ツリーを別途解析")
        print(f"    3. 文献ベース: 'GTO Wizard multiway' 検索で公開レポートを参照")

    # JSON 保存
    out_path = FINDINGS_DIR / "multiway_BTN_BB.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 完了 → {out_path}")


if __name__ == "__main__":
    main()
