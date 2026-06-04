#!/usr/bin/env python3
"""
cash_river.py — リバー分析

収集データ (複数ラインのリバー終点):
  ラインA終点: CBet→call→barrel→call→river (OOPが先手)
  ラインB終点: CBet→call→turn_check→river  (OOPが先手)
  ラインG終点: X-X→probe→call→river        (OOPが先手)

各ラインで:
  - OOPのbet/check rate by hand_category (ブラフ含む)
  - IPのbet/check rate by hand_category (OOPがチェックした後)
  - リバーブラフ候補: no_made_hand/busted drawのbet率

使い方:
  TOKEN=eyJ... python3 cash_river.py
  TOKEN=eyJ... TYPE=型1 python3 cash_river.py
  TOKEN=eyJ... LINE=A python3 cash_river.py   # ラインAのみ
"""

import os, sys, json, time, requests
from pathlib import Path

TOKEN       = os.environ.get("TOKEN", "")
GWCLIENTID  = os.environ.get("GWCLIENTID", "")
GT          = os.environ.get("GT", "Cash6mGeneral_6mNL25R25")
SCENARIO    = os.environ.get("SCENARIO", "BTN_BB")
TYPE_FILTER = os.environ.get("TYPE", "")
LINE_FILTER = os.environ.get("LINE", "")   # "A" / "B" / "G" / "" (全て)

FINDINGS_DIR = Path(__file__).parent / "findings"
FINDINGS_DIR.mkdir(exist_ok=True)

BASE_URL = "https://api.gtowizard.com/v4/solutions/spot-solution/"

# ─────────────────── プリフロップシナリオ ───────────────────
SCENARIOS = {
    "BTN_BB": {
        "label": "SRP BTN vs BB",
        "pf":    "F-F-F-R2.5-F-C",
        "ip":    "BTN",
        "oop":   "BB",
        "depth": 100,
    },
    "CO_BB": {
        "label": "SRP CO vs BB",
        "pf":    "F-F-R2.5-F-F-C",
        "ip":    "CO",
        "oop":   "BB",
        "depth": 100,
    },
    "SB_BB": {
        "label": "SRP SB vs BB",
        "pf":    "F-F-F-F-R3-C",
        "ip":    "BB",
        "oop":   "SB",
        "depth": 100,
    },
}

# ─────────────────── ボード設定 (型1/型2/型4の3型に絞る) ───────────────────
# river_blank:  ドローを完成させないブリックカード
# river_fd:     フラッシュドロー完成カード（FDがあるボードのみ）
# river_pair:   フロップのカードをペアにするカード
BOARD_CONFIGS = [
    {
        "type":  "型1_ハイドライ",
        "flop":  "Ks7d2c",
        "desc":  "K高・レインボー",
        # レインボーなのでFDなし → river_fd は省略し pair で代替
        "rivers": [
            ("blank", "9h",  "ブリック"),
            ("pair",  "Kh",  "Kペア"),
        ],
        # フロップCBetとターンバレルの標準コード（後のステップで動的に取得するが初期値を設定）
        "cbet_hint":   "R1.8",
        "tbarrel_hint": "R2",
        # OOPプローブコード（ラインG用）
        "probe_hint":  "R2",
    },
    {
        "type":  "型2_ハイウェット",
        "flop":  "Qh8d3s",
        "desc":  "Q高・2トーン",
        "rivers": [
            ("blank", "4c",  "ブリック"),
            ("fd",    "Jh",  "FD完成(h)"),
        ],
        "cbet_hint":   "R1.8",
        "tbarrel_hint": "R2",
        "probe_hint":  "R2",
    },
    {
        "type":  "型4_ローウェット",
        "flop":  "Th9s8d",
        "desc":  "低連携・2トーン",
        "rivers": [
            ("blank", "3c",  "ブリック"),
            ("fd",    "Js",  "ストレート改善・J"),
        ],
        "cbet_hint":   "R1.8",
        "tbarrel_hint": "R2",
        "probe_hint":  "R2",
    },
]

HC_SORT = {
    "straight_flush": 97, "quads": 93, "fullhouse": 89, "flush": 83, "straight": 80,
    "set": 85, "two_pair": 77, "trips": 74, "overpair": 70, "top_pair": 60,
    "underpair": 42, "second_pair": 43, "third_pair": 35, "low_pair": 30,
    "ace_high": 24, "king_high": 21, "queen_high": 19, "jack_high": 17,
    "ten_high": 15, "no_made_hand": 12,
}

# ─────────────────── API ユーティリティ ───────────────────

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


def call_api(board, flop_actions="", turn_actions="", river_actions="", pf=None, depth=100):
    """GTO Wizard API を呼ぶ。board は3/4/5枚の文字列。"""
    params = {
        "gametype": GT, "depth": str(depth), "stacks": "",
        "preflop_actions": pf or SCENARIOS[SCENARIO]["pf"],
        "flop_actions":    flop_actions,
        "turn_actions":    turn_actions,
        "river_actions":   river_actions,
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
                    ra = r.headers.get("Retry-After", "?")
                    print(f"  ❌ 日次クォータ超過 (limit={body['request_limit']}, {int(ra)//3600}時間後リセット)")
                    sys.exit(1)
            except Exception:
                pass
            wait = 10 * (attempt + 1)
            print(f"  [HTTP 429] board={board} fa={flop_actions!r} ta={turn_actions!r}"
                  f" ra={river_actions!r} → {wait}s 待機中...")
            time.sleep(wait)
            continue
        print(f"  [HTTP {r.status_code}] board={board} fa={flop_actions!r}"
              f" ta={turn_actions!r} ra={river_actions!r}")
        return None
    print(f"  [429 最大リトライ超過] board={board}")
    return None


def get_player(data, pos):
    for p in data.get("players_info", []):
        if isinstance(p.get("player"), dict) and p["player"].get("position") == pos:
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
            else:           codes["betover"] = c
    return codes


def dominant_bet_code(codes):
    for key in ["bet33", "bet50", "bet75", "bet100", "betover", "bet20"]:
        if key in codes:
            return codes[key]
    return None


def calc_hc_action_rates(sols, player, codes):
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


def weighted_rate(rows, keys):
    if not keys or not rows:
        return None
    total = sum(r["total"] for r in rows)
    if total == 0:
        return None
    return sum(r["total"] * sum(r.get(k, 0) or 0 for k in keys) for r in rows) / total


def rows_to_store(rows, keep_keys):
    if not rows:
        return []
    return [
        {k: (round(v * 100, 1) if isinstance(v, float) else v)
         for k, v in row.items()
         if k in ("hc", "total", "share") or k in keep_keys}
        for row in rows
    ]


def print_hc_table(rows, header=""):
    if not rows:
        return
    keys = [k for k in rows[0] if k not in ("hc", "total", "share")]
    if header:
        print(f"\n    {header}")
    col_hdr = f"    {'カテゴリ':22s} {'コンボ':>6} {'シェア':>6}"
    for k in keys:
        col_hdr += f" {k:>7}"
    print(col_hdr)
    print(f"    {'-'*72}")
    for row in rows:
        line = f"    {row['hc']:22s} {row['total']:6.1f} {row['share']:5.1f}%"
        for k in keys:
            v = row.get(k)
            line += f" {v*100:6.0f}%" if v is not None else f"  {'—':>6}"
        print(line)


# ─────────────────── フロップCBetコード動的取得 ───────────────────

def get_flop_cbet_code(flop, pf, ip, depth, hint):
    """フロップでIPのCBetコードを取得する。失敗時はhintを返す。"""
    data = call_api(flop, flop_actions="X", pf=pf, depth=depth)
    time.sleep(4.0)
    if not data:
        print(f"    [警告] フロップCBetコード取得失敗 → hint={hint} を使用")
        return hint
    sols    = data.get("action_solutions", [])
    codes   = classify_actions(sols) if sols else {}
    code    = dominant_bet_code(codes)
    if code:
        print(f"    フロップCBetコード: {code}  (全コード: {codes})")
        return code
    print(f"    [警告] フロップにRAISEなし → hint={hint} を使用")
    return hint


def get_turn_barrel_code(board4, flop_fa, pf, ip, depth, hint):
    """ターンでIPのバレルコードを取得する。失敗時はhintを返す。"""
    data = call_api(board4, flop_actions=flop_fa, turn_actions="X", pf=pf, depth=depth)
    time.sleep(4.0)
    if not data:
        print(f"    [警告] ターンバレルコード取得失敗 → hint={hint} を使用")
        return hint
    sols  = data.get("action_solutions", [])
    codes = classify_actions(sols) if sols else {}
    code  = dominant_bet_code(codes)
    if code:
        print(f"    ターンバレルコード: {code}  (全コード: {codes})")
        return code
    print(f"    [警告] ターンにRAISEなし → hint={hint} を使用")
    return hint


def get_probe_code(board4, pf, oop, depth, hint):
    """OOPのプローブコード（X-X後ターン先手）を取得。失敗時はhintを返す。"""
    data = call_api(board4, flop_actions="X-X", turn_actions="", pf=pf, depth=depth)
    time.sleep(4.0)
    if not data:
        print(f"    [警告] プローブコード取得失敗 → hint={hint} を使用")
        return hint
    sols  = data.get("action_solutions", [])
    codes = classify_actions(sols) if sols else {}
    code  = dominant_bet_code(codes)
    if code:
        print(f"    OOPプローブコード: {code}  (全コード: {codes})")
        return code
    print(f"    [警告] プローブにRAISEなし → hint={hint} を使用")
    return hint


# ─────────────────── リバーアクション解析 ───────────────────

def analyze_river_spot(board5, flop_fa, turn_fa, river_fa_prefix,
                       actor_pos, opponent_pos, pf, depth, label):
    """
    board5: 5枚ボード文字列
    actor_pos: 最初に行動するプレイヤーのポジション
    river_fa_prefix: "" = actorが先手、"X" = actorが後手（opponent がXしてから）

    Returns: {
        "actor_bet_pct": float|None,
        "actor_by_cat": [...],
        "ip_bet_pct": float|None,  # opponent がX後にIP/OOPがbet
        "ip_by_cat": [...],
    }
    """
    result = {
        "actor_bet_pct": None,
        "actor_by_cat":  [],
        "opp_bet_pct":   None,
        "opp_by_cat":    [],
    }

    # リバー先手行動（actor が最初に動く）
    data_a = call_api(board5, flop_actions=flop_fa, turn_actions=turn_fa,
                      river_actions=river_fa_prefix, pf=pf, depth=depth)
    time.sleep(4.0)
    if not data_a:
        print(f"    [{label}] リバー先手データ取得失敗")
        return result

    actor_p = get_player(data_a, actor_pos)
    sols_a  = data_a.get("action_solutions", [])
    if not actor_p or not sols_a:
        print(f"    [{label}] リバー先手プレイヤーデータなし (pos={actor_pos})")
        return result

    a_codes   = classify_actions(sols_a)
    a_rows    = calc_hc_action_rates(sols_a, actor_p, a_codes)
    a_bet_k   = [k for k in a_codes if k not in ("check", "fold")]
    a_bet_r   = weighted_rate(a_rows, a_bet_k)

    result["actor_bet_pct"] = round(a_bet_r * 100, 1) if a_bet_r is not None else None
    result["actor_by_cat"]  = rows_to_store(a_rows, a_bet_k + ["check", "fold"])

    actor_bet_s = f"{a_bet_r*100:.0f}%" if a_bet_r is not None else "チェックのみ"
    print(f"    [{label}] {actor_pos} リバー先手ベット率: {actor_bet_s}")
    print_hc_table(a_rows, f"{actor_pos} リバー先手 by hand_category")

    # アクターがチェックしたあと、opponent がベット（相手の反撃）
    if "check" not in a_codes:
        # チェック選択肢なし → 相手の行動は取得不要
        return result

    check_code = a_codes["check"]
    river_fa_check = (river_fa_prefix + f"-{check_code}").lstrip("-") if river_fa_prefix else check_code

    data_b = call_api(board5, flop_actions=flop_fa, turn_actions=turn_fa,
                      river_actions=river_fa_check, pf=pf, depth=depth)
    time.sleep(4.0)
    if not data_b:
        print(f"    [{label}] リバー相手ベットデータ取得失敗")
        return result

    opp_p  = get_player(data_b, opponent_pos)
    sols_b = data_b.get("action_solutions", [])
    if not opp_p or not sols_b:
        print(f"    [{label}] リバー相手プレイヤーデータなし (pos={opponent_pos})")
        return result

    b_codes  = classify_actions(sols_b)
    b_rows   = calc_hc_action_rates(sols_b, opp_p, b_codes)
    b_bet_k  = [k for k in b_codes if k not in ("check", "fold")]
    b_bet_r  = weighted_rate(b_rows, b_bet_k)

    result["opp_bet_pct"] = round(b_bet_r * 100, 1) if b_bet_r is not None else None
    result["opp_by_cat"]  = rows_to_store(b_rows, b_bet_k + ["check", "fold"])

    opp_bet_s = f"{b_bet_r*100:.0f}%" if b_bet_r is not None else "チェックのみ"
    print(f"    [{label}] {opponent_pos} リバー後手ベット率: {opp_bet_s}")
    print_hc_table(b_rows, f"{opponent_pos} リバー後手 by hand_category")

    return result


# ─────────────────── ライン別処理 ───────────────────

def analyze_line_A(cfg, board5, river_tag, river_card, river_desc,
                   cbet_code, t_barrel_code, pf, ip, oop, depth):
    """
    ラインA: CBet→call→barrel→call→river
    フロップ: X-{cbet}-C
    ターン:   X-{t_barrel}-C
    リバー:   OOP先手
    """
    label     = f"ラインA {river_tag}({river_card})"
    flop_fa   = f"X-{cbet_code}-C"
    turn_fa   = f"X-{t_barrel_code}-C"
    print(f"\n  [{label}] board5={board5}")
    print(f"    flop_actions={flop_fa!r}  turn_actions={turn_fa!r}")

    return analyze_river_spot(
        board5, flop_fa, turn_fa, "",
        actor_pos=oop, opponent_pos=ip,
        pf=pf, depth=depth, label=label,
    )


def analyze_line_B(cfg, board5, river_tag, river_card, river_desc,
                   cbet_code, pf, ip, oop, depth):
    """
    ラインB: CBet→call→turn_check(X-X)→river
    フロップ: X-{cbet}-C
    ターン:   X-X  (両者チェックバック)
    リバー:   OOP先手
    """
    label   = f"ラインB {river_tag}({river_card})"
    flop_fa = f"X-{cbet_code}-C"
    turn_fa = "X-X"
    print(f"\n  [{label}] board5={board5}")
    print(f"    flop_actions={flop_fa!r}  turn_actions={turn_fa!r}")

    return analyze_river_spot(
        board5, flop_fa, turn_fa, "",
        actor_pos=oop, opponent_pos=ip,
        pf=pf, depth=depth, label=label,
    )


def analyze_line_G(cfg, board4, board5, river_tag, river_card, river_desc,
                   probe_code, pf, ip, oop, depth):
    """
    ラインG: X-X(フロップ)→probe→call→river
    フロップ: X-X
    ターン:   {probe}-C  (OOPプローブ → IPコール)
    リバー:   OOP先手
    """
    label   = f"ラインG {river_tag}({river_card})"
    flop_fa = "X-X"
    turn_fa = f"{probe_code}-C"
    print(f"\n  [{label}] board5={board5}")
    print(f"    flop_actions={flop_fa!r}  turn_actions={turn_fa!r}")

    return analyze_river_spot(
        board5, flop_fa, turn_fa, "",
        actor_pos=oop, opponent_pos=ip,
        pf=pf, depth=depth, label=label,
    )


# ─────────────────── メイン ───────────────────

def main():
    if not TOKEN:
        print("❌ TOKEN 未設定"); sys.exit(1)

    scen = SCENARIOS.get(SCENARIO)
    if not scen:
        print(f"❌ 未知シナリオ: {SCENARIO}. 選択肢: {list(SCENARIOS)}"); sys.exit(1)

    pf, ip, oop, depth = scen["pf"], scen["ip"], scen["oop"], scen.get("depth", 100)
    print(f"シナリオ: {scen['label']}  (IP={ip}, OOP={oop}, depth={depth}BB)")
    print(f"分析: リバー総合判断（ラインA/B/G）")
    print(f"gametype: {GT}  LINE={LINE_FILTER or 'all'}\n")

    # 認証確認（3枚ボードで基本クエリ）
    test = call_api("Ks7d2c", flop_actions="X", pf=pf, depth=depth)
    if test is None:
        print("❌ 認証失敗"); sys.exit(1)
    time.sleep(4.0)
    print("✅ 認証OK\n")

    do_A = LINE_FILTER in ("A", "")
    do_B = LINE_FILTER in ("B", "")
    do_G = LINE_FILTER in ("G", "")

    all_results = []
    configs = [c for c in BOARD_CONFIGS if not TYPE_FILTER or c["type"] == TYPE_FILTER]

    for cfg in configs:
        flop = cfg["flop"]
        print(f"\n{'='*70}")
        print(f"【{cfg['type']}】 {flop}  ({cfg['desc']})")

        board_results = {
            "type": cfg["type"], "flop": flop, "desc": cfg["desc"],
            "rivers": [],
        }

        # ─── ターンカードを固定（blank のみ使用）→ ボード4枚 ───
        # リバー分析のためにターン1枚を選択する。
        # 代表ターンは最初のエントリ（blank）を使用。
        # ラインA/BのためにCBetとバレルコードを取得する。
        first_river = cfg["rivers"][0]
        # ターンカードをフロップ + 代表ターンで決める
        # ターンカードはリバーに出てくるカードと異なる必要がある。
        # ここでは型ごとに固定の代表ターンを使用する。
        TURN_CARDS = {
            "型1_ハイドライ":  "4c",
            "型2_ハイウェット": "5d",
            "型4_ローウェット": "2c",
        }
        turn_card = TURN_CARDS.get(cfg["type"], "2c")
        board4    = flop + turn_card

        print(f"  代表ターン: {turn_card}  board4={board4}")

        # フロップCBetコード動的取得
        cbet_code = get_flop_cbet_code(flop, pf, ip, depth, cfg["cbet_hint"])

        # ターンバレルコード動的取得（ラインA用）
        t_barrel_code = None
        if do_A:
            t_barrel_code = get_turn_barrel_code(
                board4, f"X-{cbet_code}-C", pf, ip, depth, cfg["tbarrel_hint"])

        # プローブコード動的取得（ラインG用）
        probe_code = None
        if do_G:
            probe_code = get_probe_code(board4, pf, oop, depth, cfg["probe_hint"])

        for river_tag, river_card, river_desc in cfg["rivers"]:
            board5 = board4 + river_card
            print(f"\n  ── [{river_tag}] river={river_card} ({river_desc}) board5={board5}")

            river_entry = {
                "tag":        river_tag,
                "turn_card":  turn_card,
                "river_card": river_card,
                "desc":       river_desc,
                "board5":     board5,
                "line_A":     None,
                "line_B":     None,
                "line_G":     None,
            }

            if do_A:
                print(f"\n    === ラインA: CBet→call→barrel→call→river ===")
                river_entry["line_A"] = analyze_line_A(
                    cfg, board5, river_tag, river_card, river_desc,
                    cbet_code, t_barrel_code, pf, ip, oop, depth,
                )

            if do_B:
                print(f"\n    === ラインB: CBet→call→X-X→river ===")
                river_entry["line_B"] = analyze_line_B(
                    cfg, board5, river_tag, river_card, river_desc,
                    cbet_code, pf, ip, oop, depth,
                )

            if do_G:
                print(f"\n    === ラインG: X-X→probe→call→river ===")
                river_entry["line_G"] = analyze_line_G(
                    cfg, board4, board5, river_tag, river_card, river_desc,
                    probe_code, pf, ip, oop, depth,
                )

            board_results["rivers"].append(river_entry)
            time.sleep(2.0)

        # ─── ボード別サマリー ───
        print(f"\n  ■ {cfg['type']} リバーサマリー（コンボ加重ベット率）")
        print(f"  {'リバー':5s}({'タグ':8s}) | {'ラインA OOP%':>13} | {'ラインB OOP%':>13} | {'ラインG OOP%':>13}")
        print(f"  {'-'*65}")
        for rv in board_results["rivers"]:
            def pct_s(line, key="actor_bet_pct"):
                if line is None:
                    return "—"
                v = line.get(key)
                return f"{v:.0f}%" if v is not None else "—"
            print(f"  {rv['river_card']:5s}({rv['tag'][:8]:8s}) | "
                  f"{pct_s(rv['line_A']):>13} | "
                  f"{pct_s(rv['line_B']):>13} | "
                  f"{pct_s(rv['line_G']):>13}")

        all_results.append(board_results)
        time.sleep(2.0)

    # ─── 全体サマリー ───
    print(f"\n\n{'='*70}")
    print(f"★ 全体サマリー: リバーOOPベット率（コンボ加重総合）")
    print(f"  {'型':20s} | {'リバー':5s}({'タグ':6s}) | {'ラインA':>8} | {'ラインB':>8} | {'ラインG':>8}")
    print(f"  {'-'*65}")
    for r in all_results:
        for rv in r["rivers"]:
            def fmt(line):
                if line is None:
                    return "  —"
                v = line.get("actor_bet_pct")
                return f"{v:.0f}%" if v is not None else "  —"
            print(f"  {r['type']:20s} | {rv['river_card']:5s}({rv['tag'][:6]:6s}) | "
                  f"{fmt(rv['line_A']):>8} | {fmt(rv['line_B']):>8} | {fmt(rv['line_G']):>8}")

    # JSON 保存
    out = FINDINGS_DIR / f"river_{SCENARIO}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"scenario": scen["label"], "results": all_results},
                  f, ensure_ascii=False, indent=2)
    print(f"\n✅ 完了 → {out}")


if __name__ == "__main__":
    main()
