#!/usr/bin/env python3
"""
cash_gto_utils.py — GTO Wizard API 共通ユーティリティ

全 cash_*.py スクリプトからインポートして使う共有モジュール。
"""

import time
import requests
from pathlib import Path

# ─────────────────── 定数 ───────────────────
BASE_URL     = "https://api.gtowizard.com/v4/solutions/spot-solution/"
FINDINGS_DIR = Path(__file__).parent / "findings"

# ─────────────────── 表示順ソートキー ───────────────────
HC_SORT = {
    "straight_flush": 97,
    "quads":          93,
    "fullhouse":      89,
    "set":            85,
    "flush":          83,
    "straight":       80,
    "two_pair":       77,
    "trips":          74,
    "overpair":       70,
    "top_pair":       60,
    "second_pair":    43,
    "underpair":      42,
    "third_pair":     35,
    "low_pair":       30,
    "ace_high":       24,
    "king_high":      21,
    "queen_high":     19,
    "jack_high":      17,
    "ten_high":       15,
    "no_made_hand":   12,
}

# ─────────────────── ボード7型 ───────────────────
BOARD_CONFIGS = [
    {
        "type":  "型1_ハイドライ",
        "flop":  "Ks7d2c",
        "desc":  "K高・レインボー",
        "turns": [
            ("blank",    "4c", "ブランク"),
            ("TA+_2nd",  "7h", "2ndカードペア"),
            ("TA+_3rd",  "2s", "3rdカードペア"),
            ("TA-_OC",   "Ah", "オーバーカード(A)"),
        ],
    },
    {
        "type":  "型2_ハイウェット",
        "flop":  "Qh8d3s",
        "desc":  "Q高・2トーン",
        "turns": [
            ("blank",    "5d", "ブランク"),
            ("TA+_2nd",  "8c", "2ndカードペア"),
            ("TA+_3rd",  "3d", "3rdカードペア"),
            ("TA-_OC",   "Ah", "オーバーカード(A)"),
        ],
    },
    {
        "type":  "型3_ロードライ",
        "flop":  "Jd7s5c",
        "desc":  "J中・レインボー",
        "turns": [
            ("blank",    "2c", "ブランク"),
            ("TA+_2nd",  "7h", "2ndカードペア"),
            ("TA+_3rd",  "5h", "3rdカードペア"),
            ("TA-_OC",   "Ah", "オーバーカード(A)"),
        ],
    },
    {
        "type":  "型4_ローウェット",
        "flop":  "Th9s8d",
        "desc":  "低連携・2トーン",
        "turns": [
            ("blank",    "2c", "ブランク"),
            ("TA+_pair", "Th", "1stカードペア"),
            ("danger",   "6c", "SC(低)"),
            ("danger",   "7c", "SC(高)"),
        ],
    },
    {
        "type":  "型5_モノトーン",
        "flop":  "Ah9h5h",
        "desc":  "A高モノトーン",
        "turns": [
            ("blank",    "2c", "ブランク(非ハート)"),
            ("TA+_2nd",  "9d", "2ndカードペア(非ハート)"),
            ("danger",   "4h", "FC(4thハート)"),
            ("TA-_OC",   "Kd", "オーバーカード(非ハート)"),
        ],
    },
    {
        "type":  "型6_ペア高",
        "flop":  "AsAcKd",
        "desc":  "AAKペアボード",
        "turns": [
            ("blank",    "2c", "ブランク"),
            ("TA+_3rd",  "Ks", "3rdカードペア(K)"),
            ("TA-_OC",   "Qd", "準OC(Q)"),
            ("danger",   "Jd", "J絡み"),
        ],
    },
    {
        "type":  "型7_ペア低",
        "flop":  "7s7d2c",
        "desc":  "77低ペアボード",
        "turns": [
            ("blank",    "3c", "ブランク"),
            ("TA+_3rd",  "2h", "3rdカードペア(2)"),
            ("TA-_OC",   "Ah", "OC(A)"),
            ("TA-_OC2",  "Kh", "OC(K)"),
        ],
    },
]

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
    "HJ_BB": {
        "label": "SRP HJ vs BB",
        "pf":    "F-R2.5-F-F-F-C",
        "ip":    "HJ",
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
    "BTN_SB": {
        "label": "SRP BTN vs SB",
        "pf":    "F-F-F-R2.5-C-F",
        "ip":    "BTN",
        "oop":   "SB",
        "depth": 100,
    },
}


def make_headers(token, gwclientid=""):
    """Authorization ヘッダーを組み立てる。"""
    h = {
        "accept":        "application/json, text/plain, */*",
        "authorization": f"Bearer {token}",
        "origin":        "https://app.gtowizard.com",
        "referer":       "https://app.gtowizard.com/",
    }
    if gwclientid:
        h["gwclientid"] = gwclientid
    return h


def call_api(
    board,
    flop_actions="",
    turn_actions="",
    river_actions="",
    pf="",
    depth=100,
    gametype="Cash6mGeneral_6mNL25R25",
    token="",
    gwclientid="",
):
    """GTO Wizard API を呼び出す。429 は最大4回リトライ。失敗時は None を返す。"""
    params = {
        "gametype":        gametype,
        "depth":           str(depth),
        "stacks":          "",
        "preflop_actions": pf,
        "flop_actions":    flop_actions,
        "turn_actions":    turn_actions,
        "river_actions":   river_actions,
        "board":           board,
    }
    headers = make_headers(token, gwclientid)
    for attempt in range(4):
        r = requests.get(BASE_URL, params=params, headers=headers, timeout=30)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            wait = 10 * (attempt + 1)
            print(
                f"  [HTTP 429] board={board} flop={flop_actions!r} "
                f"turn={turn_actions!r} → {wait}s 待機中..."
            )
            time.sleep(wait)
            continue
        print(
            f"  [HTTP {r.status_code}] board={board} "
            f"flop={flop_actions!r} turn={turn_actions!r}"
        )
        return None
    print(f"  [429 最大リトライ超過] board={board}")
    return None


def get_player(data, pos):
    """players_info からポジション名が一致するプレイヤーを返す。なければ None。"""
    for p in data.get("players_info", []):
        if isinstance(p.get("player"), dict) and p["player"].get("position") == pos:
            return p
    return None


def classify_actions(sols):
    """action_solutions をアクション種別 → コード の辞書に変換する。"""
    codes = {}
    for s in sols:
        a  = s["action"]
        t  = a["type"]
        c  = a["code"]
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
    """優先順位に従って最初に見つかったベットコードを返す。なければ None。"""
    for key in ["bet33", "bet50", "bet75", "bet100", "betover", "bet20"]:
        if key in codes:
            return codes[key]
    return None


def calc_hc_action_rates(sols, player, codes):
    """hand_category 別行動率 + レンジシェア(%) を返す。

    Returns:
        list[dict]: 各要素は hc/total/share/<action_key>... を持つ辞書。
                    行動率は 0.0–1.0 の浮動小数点。
    """
    range_hc = {h["name"]: h["total_combos"] for h in player["hand_categories"]}
    action_hc = {
        s["action"]["code"]: {
            h["name"]: h["total_combos"] for h in (s["hand_categories"] or [])
        }
        for s in sols
    }
    total_range = sum(v for v in range_hc.values() if v >= 0.3)
    rows = []
    for hc, total in sorted(range_hc.items(), key=lambda x: -HC_SORT.get(x[0], 50)):
        if total < 0.3:
            continue
        share = round(total / total_range * 100, 1) if total_range > 0 else 0.0
        act = {
            ck: action_hc.get(cv, {}).get(hc, 0) / total if total > 0 else 0
            for ck, cv in codes.items()
        }
        rows.append({"hc": hc, "total": round(total, 1), "share": share, **act})
    return rows


def weighted_rate(rows, keys):
    """コンボ加重平均行動率 (0-1) を返す。対象キーなし or データなしなら None。"""
    if not keys or not rows:
        return None
    total_combos = sum(r["total"] for r in rows)
    if total_combos == 0:
        return None
    weighted = sum(
        r["total"] * sum(r.get(k, 0) or 0 for k in keys) for r in rows
    )
    return weighted / total_combos


def print_hc_table(rows, header=""):
    """hand_category 別行動率テーブルを見やすく表示する。"""
    if not rows:
        return
    keys = [k for k in rows[0] if k not in ("hc", "total", "share")]
    if header:
        print(f"\n  {header}")
    col_hdr = f"  {'カテゴリ':22s} {'コンボ':>6} {'シェア':>6}"
    for k in keys:
        col_hdr += f" {k:>7}"
    print(col_hdr)
    print(f"  {'-'*72}")
    for row in rows:
        line = f"  {row['hc']:22s} {row['total']:6.1f} {row['share']:5.1f}%"
        for k in keys:
            v = row.get(k)
            line += f" {v*100:6.0f}%" if v is not None else f"  {'—':>6}"
        print(line)


def rows_to_store(rows, codes_dict):
    """行動率 rows を JSON 保存可能な形式（% 表記）に変換する。

    Args:
        rows: calc_hc_action_rates の戻り値。
        codes_dict: classify_actions の戻り値。

    Returns:
        list[dict]: hc/total/share と各行動率(%) を含む辞書のリスト。
    """
    if not rows:
        return []
    keep_keys = {"hc", "total", "share"} | set(codes_dict.keys())
    return [
        {
            k: (round(v * 100, 1) if isinstance(v, float) and k not in ("total", "share") else v)
            for k, v in row.items()
            if k in keep_keys
        }
        for row in rows
    ]
