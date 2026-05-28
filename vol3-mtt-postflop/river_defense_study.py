#!/usr/bin/env python3
"""
river_defense_study.py — リバー守備頻度の収集・分析

フロップ・ターンでCBetをコールしたBBが、リバーで3度目のCBetを受けたときの
call/fold/raise頻度をGTO Wizardから収集する。

【2ステップ収集方式】
  Step1: river_actions="X"  → アタッカーのリバーベット候補コードを取得
  Step2: river_actions="X-{river_bet}" → ディフェンダーのcall/fold/raiseを取得

【前提履歴】
  フロップ: X-{flop_bet}-C  (BBがチェック→BTNがCBet→BBがコール)
  ターン:   X-{turn_bet}-C  (BBがチェック→BTNがバレル→BBがコール)
  ※ turn_bet はturn_defense_study.pyの結果から取得するのが理想。
    暫定的に典型的なサイズを使用。

使い方:
  TOKEN=... python3 river_defense_study.py --probe --scenario SRP25_BTN
  TOKEN=... python3 river_defense_study.py --collect --scenario SRP25_BTN
  TOKEN=... python3 river_defense_study.py --collect --all
  python3 river_defense_study.py --analyze --all
"""

import os, sys, json, time, argparse, requests
from pathlib import Path
from collections import defaultdict
from typing import Any

TOKEN      = os.environ.get("TOKEN", "")
GWCLIENTID = os.environ.get("GWCLIENTID", "")
GT         = "MTTGeneral"
BASE_URL   = "https://api.gtowizard.com/v4/solutions/spot-solution/"
FINDINGS_DIR = Path(__file__).parent / "findings"

# ──────────────────── リバー守備シナリオ定義 ────────────────────
#
# flop_bet:  フロップCBetコード
# turn_bet:  ターンバレルコード（turn_defense_study実行後に精度向上）
# ※ turn_bet の近似値:
#   - SRP25後ターン: ポット≈7.8BB、BTN通常33-50%ポット → R2〜R3
#   - SRP20後ターン: ポット≈7.4BB、やや大きめ → R2.5〜R3.5
#   - 3BP20後ターン: ポット≈17BB（3BPはポット大）、50%前後 → R5〜R7

RIVER_DEFENSE_SCENARIOS: dict[str, dict[str, Any]] = {
    "SRP25_BTN": {
        "depth": 25.125, "pf": "F-F-F-F-F-R2.1-F-C", "stacks": "",
        "flop_bet": "R1.15",
        "turn_bet": "R2",          # ターン後ポット≈7.8BB、R2≈26%pot（暫定）
        "label": "SRP SBR25 BTN-BB | BB OOP リバー守備 vs BTN 3rd barrel",
        "pot_type": "SRP",
    },
    "SRP20_BTN": {
        "depth": 20.125, "pf": "F-F-F-F-F-R2-F-C", "stacks": "",
        "flop_bet": "R1.8",
        "turn_bet": "R2.5",        # ターン後ポット≈7.4BB、R2.5≈34%pot（暫定）
        "label": "SRP SBR20 BTN-BB | BB OOP リバー守備 vs BTN 3rd barrel",
        "pot_type": "SRP",
    },
    "3BP20_OOP_river": {
        "depth": 20.125, "pf": "F-F-F-F-F-R2-F-R7-C", "stacks": "",
        "flop_bet": "R1.55",
        "turn_bet": "R5",          # 3BPはポット≈17BB、R5≈29%pot（暫定）
        "label": "3BP SBR20 BTN-BB | BB OOP(3bet) リバー守備 vs BTN 3rd barrel",
        "pot_type": "3BP",
    },
}

# ──────────────────── 5枚ボード定義 ────────────────────
# (board_id, 5card_board, river_type, board_type)
# river_type: blank=無関係 / scare=BTN有利 / complete=ドロー完成
#
# ターンカードは BOARDS_WITH_TURNS の blank カードを採用（最も代表的）

RIVER_BOARDS: list[tuple] = [
    # 型1: A高ドライ（ターン=blank 3c/2c → リバー追加）
    ("A72_3c_blank",  "Ah7d2s3c5d",  "blank",  1),  # 5ドロー不完成
    ("A72_3c_scare",  "Ah7d2s3cKs",  "scare",  1),  # K on river
    ("A94_2c_blank",  "Ah9d4s2cTs",  "blank",  1),  # Tでの変化
    ("A94_2c_scare",  "Ah9d4s2cKs",  "scare",  1),
    # 型2: K/Q高ウェット（ターン=blank 2h）
    ("K98_2h_blank",  "Kd9s8c2h4s",  "blank",  2),  # 完全ブランク
    ("K98_2h_scare",  "Kd9s8c2hAs",  "scare",  2),  # A on river
    ("K98_2h_flush",  "Kd9s8c2hTh",  "complete", 2), # Th for flush possibility
    ("Q83_2c_blank",  "Qh8d3s2c5h",  "blank",  2),
    ("Q83_2c_scare",  "Qh8d3s2cAh",  "scare",  2),
    # 型3: コネクテッド（ターン=blank）
    ("T98_2c_blank",  "Th9s8d2c4h",  "blank",  3),
    ("T98_2c_scare",  "Th9s8d2cAh",  "scare",  3),
    ("T98_Jh_blank",  "Th9s8dJh4c",  "blank",  3),  # J on turn (draw comp), river blank
    ("KJT_2c_blank",  "KhJdTs2c4h",  "blank",  3),
    ("KJT_Qh_blank",  "KhJdTsQh3c",  "blank",  3),  # Q on turn, river blank
    # 型4: ローウェット（ターン=scare Kc）
    ("765_Kc_blank",  "7h6d5sKc2h",  "blank",  4),
    ("765_Kc_draw",   "7h6d5sKc4h",  "complete", 4), # 4 で straight
    # 型5: ミッド（ターン=blank 2c）
    ("T74_2c_blank",  "Th7d4s2c5h",  "blank",  5),
    ("T74_2c_scare",  "Th7d4s2cAh",  "scare",  5),
    ("J73_2c_blank",  "Jh7d3s2c5h",  "blank",  5),
    ("J73_2c_scare",  "Jh7d3s2cAh",  "scare",  5),
    # 型6: ロードライ（ターン=scare Kc）
    ("742_Kc_blank",  "7h4d2sKc5h",  "blank",  6),
    ("742_Kc_pair",   "7h4d2sKcKs",  "scare",  6),  # K paired on river
    # 型7: ペアボード（ターン=blank 2h）
    ("KK8_2h_blank",  "KhKd8c2h5s",  "blank",  7),
    ("AA7_2h_blank",  "AhAd7c2h5s",  "blank",  7),
]

BOARD_TYPE_NAMES = {
    1: "型1(A高)", 2: "型2(K/Q高)", 3: "型3(コネクト)",
    4: "型4(ローウェット)", 5: "型5(ミッド)", 6: "型6(ロードライ)", 7: "型7(ペア)",
}

HAND_GROUPS: dict[str, list[str]] = {
    "トップP":   ["top_pair"],
    "オーバーP": ["overpair"],
    "2ndP":      ["second_pair"],
    "アンダーP": ["underpair"],
    "セット":    ["set", "trips"],
    "2ペア+":    ["two_pair", "straight", "fullhouse", "quads"],
    "メイドなし": ["no_made_hand", "ace_high", "king_high", "third_pair", "low_pair"],
}


# ──────────────────── APIユーティリティ ────────────────────

def make_headers() -> dict:
    h = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {TOKEN}",
        "origin": "https://app.gtowizard.com",
        "referer": "https://app.gtowizard.com/",
        "user-agent": "Mozilla/5.0",
    }
    if GWCLIENTID:
        h["gwclientid"] = GWCLIENTID
    return h


def api_get(params: dict) -> dict | None:
    time.sleep(0.5)
    try:
        r = requests.get(BASE_URL, headers=make_headers(), params=params, timeout=30)
    except Exception as e:
        print(f"    通信エラー: {e}")
        return None
    if r.status_code == 204:
        print(f"    HTTP 204: ソリューションなし")
        return None
    if r.status_code == 401:
        print(f"    401: トークン期限切れ")
        return None
    if r.status_code == 429:
        info = r.json() if r.content else {}
        print(f"  日次クォータ超過 (limit={info.get('limit','?')}, {info.get('reset_after_seconds','?')}秒後リセット)")
        sys.exit(1)
    if r.status_code != 200:
        print(f"    HTTP {r.status_code}: {r.text[:120]}")
        return None
    return r.json()


def check_auth() -> bool:
    import base64 as b64
    try:
        payload = TOKEN.split(".")[1] + "=="
        data = json.loads(b64.b64decode(payload))
        remaining = data.get("exp", 0) - time.time()
        if remaining < 60:
            print(f"トークン検証失敗（続行）")
            return False
        print(f"認証OK（残り{remaining/60:.1f}分）")
        return True
    except Exception:
        print(f"トークン検証失敗（続行）")
        return True


def aggregate_cross(cross: dict, hand_types: list[str]) -> dict | None:
    n = c = f = r = 0.0
    for key, v in cross.items():
        if key.split("|")[0] in hand_types:
            n += v["n"]; c += v["call_pct"] * v["n"]
            f += v["fold_pct"] * v["n"]; r += v["raise_pct"] * v["n"]
    if n == 0:
        return None
    return {"C": c/n, "F": f/n, "R": r/n, "n": n}


def v4_solutions_to_cross(action_solutions: list) -> dict:
    """v4 API の action_solutions をフロップ cross 互換形式に変換。

    total_combos = アクション固有コンボ数 → 全アクション合計 = range 内コンボ合計。
    pct = action_combos / total_in_range_combos × 100
    """
    hand_combos: dict[str, float] = {}
    action_hand_combos: dict[str, dict[str, float]] = {}

    for a in action_solutions:
        code = a.get("action", {}).get("code", "?")
        action_hand_combos[code] = {}
        for hc in a.get("hand_categories") or []:
            name = hc.get("name")
            combos = float(hc.get("total_combos", 0) or 0)
            if name and combos > 0:
                action_hand_combos[code][name] = combos
                hand_combos[name] = hand_combos.get(name, 0) + combos

    cross: dict[str, dict] = {}
    for ht, ht_total in hand_combos.items():
        if ht_total < 0.5:
            continue
        fold_pct = call_pct = raise_pct = 0.0
        for code, hc_map in action_hand_combos.items():
            act_combos = hc_map.get(ht, 0.0)
            pct = act_combos / ht_total * 100
            if code == "F":
                fold_pct += pct
            elif code == "C":
                call_pct += pct
            else:
                raise_pct += pct
        cross[ht] = {"fold_pct": fold_pct, "call_pct": call_pct, "raise_pct": raise_pct, "n": ht_total}
    return cross


def get_bets_from_v4(action_solutions: list, min_freq: float = 0.03) -> list[tuple[str, float]]:
    """v4 action_solutions からベットコードと頻度を取得（Step1用）。"""
    bets = []
    for a in action_solutions:
        code = a.get("action", {}).get("code", "")
        freq = float(a.get("total_frequency", 0) or 0)
        if code and code not in ("X", "C", "F") and freq >= min_freq:
            bets.append((code, freq))
    bets.sort(key=lambda x: -x[1])
    return bets


def jsonl_path(scenario: str) -> Path:
    return FINDINGS_DIR / f"river_defense_{scenario}.jsonl"


def load_existing(scenario: str) -> set[str]:
    p = jsonl_path(scenario)
    if not p.exists():
        return set()
    seen: set[str] = set()
    with open(p) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    seen.add(json.loads(line)["board_id"])
                except Exception:
                    pass
    return seen


# ──────────────────── コレクション ────────────────────

def collect(scenario_key: str) -> None:
    sc = RIVER_DEFENSE_SCENARIOS[scenario_key]
    check_auth()
    check_auth()
    print(f"\n=== COLLECT: {sc['label']} ===")
    print(f"    flop_bet: {sc['flop_bet']}  turn_bet: {sc['turn_bet']}")

    existing = load_existing(scenario_key)
    path = jsonl_path(scenario_key)

    # フロップ・ターン履歴を構築
    flop_actions = f"X-{sc['flop_bet']}-C"
    turn_actions  = f"X-{sc['turn_bet']}-C"

    for (board_id, full_board, river_type, board_type) in RIVER_BOARDS:
        if board_id in existing:
            print(f"  [{board_id}] スキップ（収集済み）")
            continue

        bt_name = BOARD_TYPE_NAMES.get(board_type, "")
        print(f"\n  [{board_id}] {full_board} — {bt_name} {river_type}")

        # Step1: リバーのアタッカーオプションを取得（BB checks first on river）
        params1 = {
            "gametype": GT, "depth": sc["depth"], "stacks": sc.get("stacks", ""),
            "preflop_actions": sc["pf"],
            "flop_actions": flop_actions,
            "turn_actions": turn_actions,
            "river_actions": "X",   # BB checks river (OOP)
            "board": full_board,
        }
        data1 = api_get(params1)
        if data1 is None:
            print(f"    Step1 API失敗")
            continue

        bets = get_bets_from_v4(data1.get("action_solutions", []))

        if not bets:
            print(f"    リバーベット候補なし")
            continue

        dom_code, dom_freq = bets[0]
        print(f"    リバーベット候補: {bets[:4]}")
        print(f"    支配的: {dom_code}  freq={dom_freq:.2f}")

        # Step2: ディフェンダーのリバーレスポンスを取得
        params2 = {
            "gametype": GT, "depth": sc["depth"], "stacks": sc.get("stacks", ""),
            "preflop_actions": sc["pf"],
            "flop_actions": flop_actions,
            "turn_actions": turn_actions,
            "river_actions": f"X-{dom_code}",
            "board": full_board,
        }
        data2 = api_get(params2)
        if data2 is None:
            print(f"    Step2 API失敗")
            continue

        cross = v4_solutions_to_cross(data2.get("action_solutions", []))
        in_range = sum(v["n"] for v in cross.values()) if cross else 0
        print(f"    in-range combos: {in_range}")

        for label, hand_types in HAND_GROUPS.items():
            agg = aggregate_cross(cross, hand_types)
            if agg and agg["n"] > 5:
                print(f"    {label:<12}: C={agg['C']:4.0f}% F={agg['F']:4.0f}% R={agg['R']:4.0f}%")

        record = {
            "board_id": board_id, "full_board": full_board,
            "river_type": river_type, "board_type": board_type,
            "scenario": scenario_key,
            "flop_actions": flop_actions, "turn_actions": turn_actions,
            "river_actions": f"X-{dom_code}",
            "attack_code": dom_code, "attack_freq": dom_freq,
            "pot_type": sc["pot_type"], "cross": cross,
        }
        with open(path, "a") as out:
            out.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\n  → {path}")


# ──────────────────── プローブ ────────────────────

def probe(scenario_key: str) -> None:
    sc = RIVER_DEFENSE_SCENARIOS[scenario_key]
    check_auth()
    _, full_board, _, _ = RIVER_BOARDS[0]
    flop_actions = f"X-{sc['flop_bet']}-C"
    turn_actions  = f"X-{sc['turn_bet']}-C"

    print(f"\n=== PROBE: {sc['label']} ===")
    print(f"  board: {full_board}")
    print(f"  flop: {flop_actions}  turn: {turn_actions}")

    params = {
        "gametype": GT, "depth": sc["depth"], "stacks": sc.get("stacks", ""),
        "preflop_actions": sc["pf"],
        "flop_actions": flop_actions,
        "turn_actions": turn_actions,
        "river_actions": "X",
        "board": full_board,
    }
    data = api_get(params)
    if data:
        strats = [(a.get("action", {}).get("code"), round(float(a.get("total_frequency", 0) or 0), 2))
                  for a in data.get("action_solutions", [])]
        print(f"  リバーアクション: {strats}")
        game = data.get("game", {})
        print(f"  pot: {game.get('pot')}  active: {game.get('active_position')}")


# ──────────────────── 分析 ────────────────────

def analyze(scenario_key: str | None = None) -> None:
    keys = list(RIVER_DEFENSE_SCENARIOS.keys()) if scenario_key is None else [scenario_key]
    for key in keys:
        p = jsonl_path(key)
        if not p.exists():
            print(f"{key}: データなし")
            continue
        records = []
        with open(p) as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))

        print(f"\n=== ANALYZE: {key} (n={len(records)}) ===")
        sc = RIVER_DEFENSE_SCENARIOS.get(key, {})
        print(f"  {sc.get('label', '')}")

        # リバーカード種別 × ハンドグループ 集計
        by_river: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
        for r in records:
            rt = r.get("river_type", "?")
            for label, ht in HAND_GROUPS.items():
                agg = aggregate_cross(r["cross"], ht)
                if agg and agg["n"] > 5:
                    by_river[rt][label].append(agg)

        for rt in ["blank", "scare", "complete"]:
            if rt not in by_river:
                continue
            print(f"\n  リバー={rt}:")
            for label in HAND_GROUPS:
                aggs = by_river[rt].get(label, [])
                if not aggs:
                    continue
                total_n = sum(x["n"] for x in aggs)
                ac = sum(x["C"]*x["n"] for x in aggs) / total_n
                af = sum(x["F"]*x["n"] for x in aggs) / total_n
                ar = sum(x["R"]*x["n"] for x in aggs) / total_n
                print(f"    {label:<12}: C={ac:5.1f}% F={af:5.1f}% R={ar:5.1f}%")

        # ボード型別 フォールド率（リバーの主要指標）
        print(f"\n  ボード型別 メイドなし フォールド率:")
        by_bt: dict[int, list] = defaultdict(list)
        for r in records:
            agg = aggregate_cross(r["cross"], ["no_made_hand", "ace_high", "king_high"])
            if agg and agg["n"] > 5:
                by_bt[r["board_type"]].append(agg)
        for bt in sorted(by_bt):
            aggs = by_bt[bt]
            total_n = sum(x["n"] for x in aggs)
            fold = sum(x["F"]*x["n"] for x in aggs) / total_n
            print(f"    {BOARD_TYPE_NAMES.get(bt, bt)}: Fold={fold:.1f}%")


# ──────────────────── メイン ────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--collect", action="store_true")
    ap.add_argument("--probe",   action="store_true")
    ap.add_argument("--analyze", action="store_true")
    ap.add_argument("--all",     action="store_true")
    ap.add_argument("--scenario", default=None)
    args = ap.parse_args()

    FINDINGS_DIR.mkdir(exist_ok=True)

    if args.probe:
        sc = args.scenario or list(RIVER_DEFENSE_SCENARIOS.keys())[0]
        probe(sc)
    elif args.collect:
        if args.all:
            for sc in RIVER_DEFENSE_SCENARIOS:
                collect(sc)
        elif args.scenario:
            collect(args.scenario)
        else:
            print("--scenario または --all を指定してください")
            print("シナリオ一覧:")
            for k, v in RIVER_DEFENSE_SCENARIOS.items():
                print(f"  {k}: {v['label']}")
    elif args.analyze:
        analyze(args.scenario)
    else:
        print(__doc__)
        print("\n利用可能シナリオ:")
        for k, v in RIVER_DEFENSE_SCENARIOS.items():
            p = jsonl_path(k)
            n = sum(1 for _ in open(p) if _.strip()) if p.exists() else 0
            print(f"  {k:<25}: {v['label']}  [{n}件]")


if __name__ == "__main__":
    main()
