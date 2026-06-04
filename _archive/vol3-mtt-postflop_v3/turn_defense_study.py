#!/usr/bin/env python3
"""
turn_defense_study.py — ターン守備頻度の収集・分析

フロップCBetをコールしたBBが、ターンで再度CBetを受けたときの
call/fold/raise頻度をGTO Wizardから収集する。

【2ステップ収集方式】
  Step1: flop_actions="X-{flop_bet}-C", turn_actions="X"
         → アタッカーのターンベット候補コードを取得
  Step2: turn_actions="X-{turn_bet}"
         → ディフェンダーのcall/fold/raiseを取得

使い方:
  TOKEN=... python3 turn_defense_study.py --probe --scenario SRP25_BTN
  TOKEN=... python3 turn_defense_study.py --collect --scenario SRP25_BTN
  TOKEN=... python3 turn_defense_study.py --collect --all
  python3 turn_defense_study.py --analyze --all
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

# ──────────────────── ターン守備シナリオ定義 ────────────────────
#
# flop_bet:        フロップでBBがコールしたCBetコード（defense_study.pyデータより）
# turn_first_step: ターンで守備側が最初に取るアクション
#   "X"  = OOP(BB/SB)がチェック → IP(BTN)がバレルを打つ
#   ""   = OOP(BB/SB)がリード → IP側が守備（3BP IPシナリオ）

TURN_DEFENSE_SCENARIOS: dict[str, dict[str, Any]] = {
    # ── SRP BTN-BB: BB(OOP) ターン守備 vs BTN 2nd barrel ──
    "SRP25_BTN": {
        "depth": 25.125, "pf": "F-F-F-F-F-R2.1-F-C", "stacks": "",
        "flop_bet": "R1.15",       # BTN dominant flop CBet (SBR25, from defense_study)
        "turn_first_step": "X",    # BB checks turn (OOP)
        "label": "SRP SBR25 BTN-BB | BB OOP ターン守備 vs BTN barrel",
        "pot_type": "SRP",
    },
    "SRP20_BTN": {
        "depth": 20.125, "pf": "F-F-F-F-F-R2-F-C", "stacks": "",
        "flop_bet": "R1.8",        # BTN dominant flop CBet (SBR20)
        "turn_first_step": "X",
        "label": "SRP SBR20 BTN-BB | BB OOP ターン守備 vs BTN barrel",
        "pot_type": "SRP",
    },
    # ── 3BP BTN-BB: BB(OOP/3bet側) ターン守備 vs BTN(caller) barrel ──
    "3BP20_OOP_turn": {
        "depth": 20.125, "pf": "F-F-F-F-F-R2-F-R7-C", "stacks": "",
        "flop_bet": "R1.55",       # BTN dominant CBet in 3BP (BB checked, BTN bet)
        "turn_first_step": "X",    # BB checks turn again
        "label": "3BP SBR20 BTN-BB | BB OOP(3bet) ターン守備 vs BTN barrel",
        "pot_type": "3BP",
    },
    # ── 3BP BTN-BB: BTN(IP/caller) ターン守備 vs BB(OOP/3bet) 2nd lead ──
    "3BP20_IP_turn": {
        "depth": 20.125, "pf": "F-F-F-F-F-R2-F-R7-C", "stacks": "",
        "flop_bet": "R3.9",        # BB dominant lead in 3BP (BB led, BTN called)
        "turn_first_step": "",     # BB(OOP) leads turn again; BTN defends
        "label": "3BP SBR20 BTN-BB | BTN IP(caller) ターン守備 vs BB 2nd lead",
        "pot_type": "3BP",
    },
    # ── 3BP SB-BB: SB(OOP/caller) ターン守備 vs BB(3bet) 2nd barrel ──
    "3BP25_SB_OOP_turn": {
        "depth": 25.125, "pf": "F-F-F-F-F-F-R3-R8-C", "stacks": "",
        "flop_bet": "R2.3",        # BB dominant CBet (SB checked, BB bet)
        "turn_first_step": "X",    # SB checks turn (OOP)
        "label": "3BP SBR25 SB-BB | SB OOP(caller) ターン守備 vs BB barrel",
        "pot_type": "3BP",
    },
    # ── SRP SB-BB: SB(OOP) ターン守備 vs BB(IP) barrel ──
    # フロップ: SB がリード (first_step="") → BB がコール
    # ターン: SB は再度OOP → SBがチェック → BB がバレル → SB が守備
    "SRP25_SB_OOP_turn": {
        "depth": 25.125, "pf": "F-F-F-F-F-F-R3-C", "stacks": "",
        "flop_bet": "R2",          # SB dominant lead on flop (from SRP25_SB_IP data)
        "turn_first_step": "X",    # SB checks turn; BB can barrel
        "label": "SRP SBR25 SB-BB | SB OOP ターン守備 vs BB barrel",
        "pot_type": "SRP",
        "flop_oop_leads": True,    # フロップはOOP(SB)がリード → flop_actions="R{bet}-C"
    },
}

# ──────────────────── ターンカード付きボード定義 ────────────────────
# (board_id, flop_cards, turn_card, turn_type, board_type)
# turn_type: blank=無関係カード / scare=BTN有利カード / draw=ドロー完成カード
#
# スーツ選択: フロップカードと同一rank-suitにならないよう注意済み

BOARDS_WITH_TURNS: list[tuple] = [
    # 型1: A高ドライ
    ("A72_blank",    "Ah7d2s", "3c",  "blank", 1),
    ("A72_scare",    "Ah7d2s", "Ks",  "scare", 1),
    # 型1: A高セミ
    ("A94_blank",    "Ah9d4s", "2c",  "blank", 1),
    ("A94_scare",    "Ah9d4s", "Ks",  "scare", 1),
    # 型2: K/Q高ウェット
    ("K98_blank",    "Kd9s8c", "2h",  "blank", 2),
    ("K98_scare",    "Kd9s8c", "Ah",  "scare", 2),
    ("K98_draw",     "Kd9s8c", "Jh",  "draw",  2),  # T-J でストレート完成
    ("Q83_blank",    "Qh8d3s", "2c",  "blank", 2),
    ("Q83_scare",    "Qh8d3s", "Ah",  "scare", 2),
    # 型3: コネクテッド
    ("T98_blank",    "Th9s8d", "2c",  "blank", 3),
    ("T98_draw",     "Th9s8d", "Jh",  "draw",  3),  # J でストレート完成
    ("KJT_blank",    "KhJdTs", "2c",  "blank", 3),
    ("KJT_draw",     "KhJdTs", "Qh",  "draw",  3),  # Q でストレート完成
    # 型4: ローウェット
    ("765_scare",    "7h6d5s", "Kc",  "scare", 4),
    ("765_draw",     "7h6d5s", "4h",  "draw",  4),  # 4 で低ストレート完成
    # 型5: ミッド断絶
    ("T74_blank",    "Th7d4s", "2c",  "blank", 5),
    ("T74_scare",    "Th7d4s", "Ah",  "scare", 5),
    ("J73_blank",    "Jh7d3s", "2c",  "blank", 5),
    ("J73_scare",    "Jh7d3s", "Ah",  "scare", 5),
    # 型6: ロードライ
    ("742_scare",    "7h4d2s", "Kc",  "scare", 6),
    ("742_low",      "7h4d2s", "3c",  "low",   6),  # 低ストレート接続
    # 型7: ペアボード
    ("KK8_blank",    "KhKd8c", "2h",  "blank", 7),
    ("KK8_scare",    "KhKd8c", "Ah",  "scare", 7),
    ("AA7_blank",    "AhAd7c", "2h",  "blank", 7),
]

BOARD_TYPE_NAMES = {
    1: "型1(A高)", 2: "型2(K/Q高)", 3: "型3(コネクト)",
    4: "型4(ローウェット)", 5: "型5(ミッド)", 6: "型6(ロードライ)", 7: "型7(ペア)",
}

# ハンドグループ（defense_study.pyと同一定義）
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
        print(f"    401 Unauthorized: トークン期限切れ")
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
        ht = key.split("|")[0]
        if ht in hand_types:
            n += v["n"]; c += v["call_pct"] * v["n"]
            f += v["fold_pct"] * v["n"]; r += v["raise_pct"] * v["n"]
    if n == 0:
        return None
    return {"C": c/n, "F": f/n, "R": r/n, "n": n}


def v4_solutions_to_cross(action_solutions: list) -> dict:
    """v4 API の action_solutions をフロップ cross 互換形式に変換。

    aggregate_cross() に渡せる {hand_type: {call_pct, fold_pct, raise_pct, n}} を返す。
    pct 値は 0〜100 スケール（フロップ cross と同一）。

    v4 action_solutions の hand_categories 構造:
      total_combos = そのアクションを取ったコンボ数（アクション固有）
      → 全アクションのコンボを合計 = range 内コンボ合計
      pct = action_combos / total_in_range_combos × 100
    """
    # アクション別コンボ数を累積 → 全アクション合計 = range 内総コンボ
    hand_combos: dict[str, float] = {}
    action_hand_combos: dict[str, dict[str, float]] = {}  # {action_code: {hand_type: combos}}

    for a in action_solutions:
        code = a.get("action", {}).get("code", "?")
        action_hand_combos[code] = {}
        for hc in a.get("hand_categories") or []:
            name = hc.get("name")
            combos = float(hc.get("total_combos", 0) or 0)
            if name and combos > 0:
                action_hand_combos[code][name] = combos
                hand_combos[name] = hand_combos.get(name, 0) + combos  # 全アクション合計

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
    """v4 action_solutions からベットコードと頻度のリストを取得（Step1用）。"""
    bets = []
    for a in action_solutions:
        code = a.get("action", {}).get("code", "")
        freq = float(a.get("total_frequency", 0) or 0)
        if code and code not in ("X", "C", "F") and freq >= min_freq:
            bets.append((code, freq))
    bets.sort(key=lambda x: -x[1])
    return bets


def jsonl_path(scenario: str) -> Path:
    return FINDINGS_DIR / f"turn_defense_{scenario}.jsonl"


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
    sc = TURN_DEFENSE_SCENARIOS[scenario_key]
    check_auth()
    check_auth()
    print(f"\n=== COLLECT: {sc['label']} ===")
    print(f"    flop_bet: {sc['flop_bet']}  turn_first_step: '{sc['turn_first_step']}'")

    existing = load_existing(scenario_key)
    path = jsonl_path(scenario_key)
    oop_leads_flop = sc.get("flop_oop_leads", False)

    for (board_id, flop, turn_card, turn_type, board_type) in BOARDS_WITH_TURNS:
        if board_id in existing:
            print(f"  [{board_id}] スキップ（収集済み）")
            continue

        full_board = flop + turn_card
        bt_name = BOARD_TYPE_NAMES.get(board_type, "")
        print(f"\n  [{board_id}] {flop}+{turn_card} — {bt_name} {turn_type}")

        # フロップアクション構築
        # OOP守備: OOP checks → attacker bets → OOP calls → "X-{bet}-C"
        # OOPリード: OOP leads → IP calls → "{lead}-C"
        if oop_leads_flop:
            flop_actions = f"{sc['flop_bet']}-C"
        else:
            flop_actions = f"X-{sc['flop_bet']}-C"

        # Step1: ターンのアタッカーオプションを取得
        params1 = {
            "gametype": GT, "depth": sc["depth"], "stacks": sc.get("stacks", ""),
            "preflop_actions": sc["pf"],
            "flop_actions": flop_actions,
            "turn_actions": sc["turn_first_step"],
            "river_actions": "", "board": full_board,
        }
        data1 = api_get(params1)
        if data1 is None:
            print(f"    Step1 API失敗")
            continue

        bets = get_bets_from_v4(data1.get("action_solutions", []))

        if not bets:
            print(f"    ターンベット候補なし（チェック/フォールド主体）")
            continue

        dom_code, dom_freq = bets[0]
        print(f"    ターンベット候補: {bets[:4]}")
        print(f"    支配的: {dom_code}  freq={dom_freq:.2f}")

        # Step2: ディフェンダーのターンレスポンスを取得
        fs = sc["turn_first_step"]
        turn_actions2 = f"{fs}-{dom_code}" if fs else dom_code

        params2 = {
            "gametype": GT, "depth": sc["depth"], "stacks": sc.get("stacks", ""),
            "preflop_actions": sc["pf"],
            "flop_actions": flop_actions,
            "turn_actions": turn_actions2,
            "river_actions": "", "board": full_board,
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
            "board_id": board_id, "flop": flop, "turn_card": turn_card,
            "turn_type": turn_type, "full_board": full_board,
            "board_type": board_type, "scenario": scenario_key,
            "flop_actions": flop_actions, "turn_actions": turn_actions2,
            "attack_code": dom_code, "attack_freq": dom_freq,
            "pot_type": sc["pot_type"], "cross": cross,
        }
        with open(path, "a") as out:
            out.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\n  → {path}")


# ──────────────────── プローブ（動作確認） ────────────────────

def probe(scenario_key: str) -> None:
    sc = TURN_DEFENSE_SCENARIOS[scenario_key]
    check_auth()
    _, flop, turn_card, _, _ = BOARDS_WITH_TURNS[0]
    full_board = flop + turn_card
    oop_leads_flop = sc.get("flop_oop_leads", False)
    flop_actions = f"{sc['flop_bet']}-C" if oop_leads_flop else f"X-{sc['flop_bet']}-C"

    print(f"\n=== PROBE: {sc['label']} ===")
    print(f"  board: {full_board}  flop_actions: {flop_actions}  turn_actions: {sc['turn_first_step']}")

    params = {
        "gametype": GT, "depth": sc["depth"], "stacks": sc.get("stacks", ""),
        "preflop_actions": sc["pf"], "flop_actions": flop_actions,
        "turn_actions": sc["turn_first_step"], "river_actions": "", "board": full_board,
    }
    data = api_get(params)
    if data:
        strats = [(a.get("action", {}).get("code"), round(float(a.get("total_frequency", 0) or 0), 2))
                  for a in data.get("action_solutions", [])]
        print(f"  ターンアクション: {strats}")
        game = data.get("game", {})
        print(f"  pot: {game.get('pot')}  active: {game.get('active_position')}")


# ──────────────────── 分析 ────────────────────

def analyze(scenario_key: str | None = None) -> None:
    keys = list(TURN_DEFENSE_SCENARIOS.keys()) if scenario_key is None else [scenario_key]
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
        sc = TURN_DEFENSE_SCENARIOS.get(key, {})
        print(f"  {sc.get('label', '')}")

        # ターンカード別 × ハンドグループ 集計
        by_turn: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
        for r in records:
            tt = r.get("turn_type", "?")
            for label, ht in HAND_GROUPS.items():
                agg = aggregate_cross(r["cross"], ht)
                if agg and agg["n"] > 5:
                    by_turn[tt][label].append(agg)

        for tt in ["blank", "scare", "draw", "low"]:
            if tt not in by_turn:
                continue
            print(f"\n  ターン={tt}:")
            for label in HAND_GROUPS:
                aggs = by_turn[tt].get(label, [])
                if not aggs:
                    continue
                total_n = sum(x["n"] for x in aggs)
                ac = sum(x["C"]*x["n"] for x in aggs) / total_n
                af = sum(x["F"]*x["n"] for x in aggs) / total_n
                ar = sum(x["R"]*x["n"] for x in aggs) / total_n
                print(f"    {label:<12}: C={ac:5.1f}% F={af:5.1f}% R={ar:5.1f}%")

        # ボード型別トップP CR%
        print(f"\n  ボード型別 トップP CR%:")
        by_bt: dict[int, list] = defaultdict(list)
        for r in records:
            agg = aggregate_cross(r["cross"], ["top_pair"])
            if agg and agg["n"] > 5:
                by_bt[r["board_type"]].append(agg)
        for bt in sorted(by_bt):
            aggs = by_bt[bt]
            total_n = sum(x["n"] for x in aggs)
            cr = sum(x["R"]*x["n"] for x in aggs) / total_n
            print(f"    {BOARD_TYPE_NAMES.get(bt, bt)}: CR={cr:.1f}%")


# ──────────────────── メイン ────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--collect", action="store_true", help="データ収集")
    ap.add_argument("--probe",   action="store_true", help="動作確認（1ボードのみ）")
    ap.add_argument("--analyze", action="store_true", help="収集済みデータを分析")
    ap.add_argument("--all",     action="store_true", help="全シナリオ対象")
    ap.add_argument("--scenario", default=None, help="シナリオキー")
    args = ap.parse_args()

    FINDINGS_DIR.mkdir(exist_ok=True)

    if args.probe:
        sc = args.scenario or list(TURN_DEFENSE_SCENARIOS.keys())[0]
        probe(sc)
    elif args.collect:
        if args.all:
            for sc in TURN_DEFENSE_SCENARIOS:
                collect(sc)
        elif args.scenario:
            collect(args.scenario)
        else:
            print("--scenario または --all を指定してください")
            print("シナリオ一覧:")
            for k, v in TURN_DEFENSE_SCENARIOS.items():
                print(f"  {k}: {v['label']}")
    elif args.analyze:
        analyze(args.scenario)
    else:
        print(__doc__)
        print("\n利用可能シナリオ:")
        for k, v in TURN_DEFENSE_SCENARIOS.items():
            p = jsonl_path(k)
            n = sum(1 for _ in open(p) if _.strip()) if p.exists() else 0
            print(f"  {k:<25}: {v['label']}  [{n}件]")


if __name__ == "__main__":
    main()
