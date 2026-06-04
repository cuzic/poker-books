"""
gto_api.py — GTO Wizard API 共通モジュール

使い方:
    from gto_api import api_get, get_code, is_bet_code, dominant_bet, action_dist
    from gto_api import ip_player, oop_player, all_bet_codes
    from gto_api import agg_player, agg_sols
    from gto_api import HC_5CAT, DC_5CAT, CAT5_ORDER, HC_RAW_ORDER, DC_RAW_ORDER
    from gto_api import load_json, save_json

環境変数:
    TOKEN       Bearer トークン (必須)
    GWCLIENTID  クライアント ID (任意)
    GT          gametype (デフォルト: Cash6mGeneral_6mNL25R25)

Raises:
    RuntimeError("DAILY_QUOTA_EXCEEDED")  日次クォータ超過時
"""

import json
import os
import sys
import time
from collections import defaultdict

import requests

TOKEN      = os.environ.get("TOKEN", "")
GWCLIENTID = os.environ.get("GWCLIENTID", "")
GT         = os.environ.get("GT", "Cash6mGeneral_6mNL25R25")

BASE_URL = "https://api.gtowizard.com/v4/solutions/spot-solution/"

SESSION = requests.Session()


def update_session():
    """TOKEN/GWCLIENTID を環境変数から再読みしてセッションヘッダーを更新する。
    スクリプト起動後に TOKEN を変更した場合や、環境変数を後から設定した場合に呼ぶ。
    """
    global TOKEN, GWCLIENTID
    TOKEN      = os.environ.get("TOKEN", TOKEN)
    GWCLIENTID = os.environ.get("GWCLIENTID", GWCLIENTID)
    SESSION.headers.update({
        "Authorization": f"Bearer {TOKEN}",
        "Accept":        "application/json",
        "gwclientid":    GWCLIENTID,
    })


update_session()  # モジュールロード時に1回実行


# ─────────────────── API ─────────────────────────────

def api_get(
    board: str,
    flop_actions: str,
    pf: str,
    *,
    depth: int = 100,
    retries: int = 3,
    turn_actions: str = "",
    river_actions: str = "",
) -> dict | None:
    """
    GTO Wizard spot-solution API を呼び出す。

    Parameters
    ----------
    board         : ボード文字列 (例: "9s8d7c")
    flop_actions  : フロップアクション文字列 (例: "X", "X-bet33")
    pf            : プリフロップアクション文字列
    depth         : ツリー深さ (デフォルト 100)
    retries       : リトライ回数 (デフォルト 3)
    turn_actions  : ターンアクション (デフォルト "")
    river_actions : リバーアクション (デフォルト "")

    Returns
    -------
    レスポンス JSON dict、失敗時は None

    Raises
    ------
    RuntimeError("DAILY_QUOTA_EXCEEDED")  日次クォータ超過時
    """
    params = {
        "gametype":        GT,
        "depth":           str(depth),
        "stacks":          "",
        "preflop_actions": pf,
        "flop_actions":    flop_actions,
        "turn_actions":    turn_actions,
        "river_actions":   river_actions,
        "board":           board,
    }
    for attempt in range(retries):
        try:
            r = SESSION.get(BASE_URL, params=params, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                try:
                    body = r.json()
                    if body.get("time_period_in_seconds", 0) >= 86400:
                        ra = r.headers.get("Retry-After", "?")
                        print(f"  日次クォータ超過 (Retry-After: {ra}s)", file=sys.stderr)
                        raise RuntimeError("DAILY_QUOTA_EXCEEDED")
                except RuntimeError:
                    raise
                except Exception:
                    pass
                wait = 15 * (attempt + 1)
                print(f"  429 rate limit — waiting {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            print(f"  HTTP {r.status_code}  board={board!r} fa={flop_actions!r}", file=sys.stderr)
            return None
        except RuntimeError:
            raise
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)
            time.sleep(5)
    return None


# ─────────────────── アクションヘルパー ───────────────────

def get_code(a: dict) -> str:
    return a.get("action", {}).get("code", "")


def is_bet_code(code: str) -> bool:
    return code.startswith("bet") or (code.startswith("R") and len(code) > 1)


_BET_PREF = ["bet33", "bet50", "bet75", "bet100", "betover", "bet20", "bet25", "bet125", "bet150"]


def dominant_bet(action_sols: list) -> str | None:
    """最も使われているベットサイズコードを返す（優先リスト順、なければ combos 最大）。"""
    bets = {get_code(a): a for a in action_sols if is_bet_code(get_code(a))}
    for p in _BET_PREF:
        if p in bets:
            return p
    if bets:
        return max(bets, key=lambda k: bets[k].get("total_combos", 0))
    return None


def all_bet_codes(action_sols: list) -> list[str]:
    """action_solutions からベットコード一覧を返す。"""
    return [get_code(a) for a in action_sols if is_bet_code(get_code(a))]


def action_dist(action_sols: list) -> list[dict]:
    """全アクションの頻度一覧を freq 降順で返す。"""
    result = []
    for a in action_sols:
        code = get_code(a)
        if not code:
            continue
        result.append({
            "code":   code,
            "freq":   round(a.get("total_frequency", 0), 4),
            "combos": round(a.get("total_combos", 0), 1),
        })
    return sorted(result, key=lambda x: -x["freq"])


# ─────────────────── players_info ユーティリティ ──────────

def ip_player(sols: dict) -> dict | None:
    """players_info[1] (IP: チェック後に行動するプレイヤー) を返す。"""
    pi = sols.get("players_info", [])
    return pi[1] if len(pi) >= 2 else None


def oop_player(sols: dict) -> dict | None:
    """players_info[0] (OOP: 最初に行動するプレイヤー) を返す。"""
    pi = sols.get("players_info", [])
    return pi[0] if pi else None


# ─────────────────── カテゴリマッピング ───────────────────

# 5-cat (英略語): V / D / BC / WD / Air
HC_5CAT: dict[str, str] = {
    "straight_flush": "V", "quads": "V", "fullhouse": "V",
    "flush":          "V", "straight": "V", "set": "V",
    "trips":          "V", "two_pair": "V", "overpair": "V", "top_pair": "V",
    "second_pair":    "BC", "underpair": "BC", "third_pair": "BC",
    "low_pair":       "Air", "ace_high": "Air", "king_high": "Air",
    "queen_high":     "Air", "jack_high": "Air", "ten_high": "Air",
    "no_made_hand":   "Air",
}
DC_5CAT: dict[str, str] = {
    "combo_draw":     "D",  "nut_flush_draw": "D",
    "flush_draw":     "D",  "oesd":           "D",
    "gutshot":        "WD", "twocards_bdfd":  "WD",
}
CAT5_ORDER: list[str] = ["V", "D", "BC", "WD", "Air"]

# GTO Wizard が返す生カテゴリ順（強さ降順）
HC_RAW_ORDER: list[str] = [
    "straight_flush", "quads", "fullhouse", "flush", "straight", "set",
    "trips", "two_pair", "overpair", "top_pair",
    "second_pair", "underpair", "third_pair",
    "low_pair", "ace_high", "king_high", "queen_high", "jack_high", "ten_high",
    "no_made_hand",
]
DC_RAW_ORDER: list[str] = [
    "combo_draw", "nut_flush_draw", "flush_draw", "oesd", "gutshot", "twocards_bdfd",
]

# action_solutions のコードを読みやすいラベルに変換
_ACTION_LABEL: dict[str, str] = {"F": "fold", "C": "call", "X": "check"}


# ─────────────────── 集計ユーティリティ ───────────────────

def agg_player(
    player: dict,
    action_codes: dict[str, str],
    hc_map: dict[str, str] | None = None,
    dc_map: dict[str, str] | None = None,
) -> dict[str, dict]:
    """players_info エントリからカテゴリ × アクション集計（ベット/チェックノード用）。

    Parameters
    ----------
    player       : sols["players_info"][i]
    action_codes : {ラベル: APIコード}  例: {"bet": "bet33", "check": "X"}
    hc_map       : hand_category 名 → カテゴリラベル (省略時 HC_5CAT)
    dc_map       : draw_category 名 → カテゴリラベル (省略時 DC_5CAT)

    Returns
    -------
    {カテゴリ: {"n": コンボ数, "bet": 頻度%, ...}}
    """
    if hc_map is None:
        hc_map = HC_5CAT
    if dc_map is None:
        dc_map = DC_5CAT

    cats = set(list(hc_map.values()) + list(dc_map.values()))
    buckets: dict[str, dict] = {c: {"n": 0.0, **{k: 0.0 for k in action_codes}} for c in cats}

    for hc in player.get("hand_categories", []):
        n = hc.get("total_combos", 0)
        if n < 0.3:
            continue
        cat = hc_map.get(hc["name"])
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
        cat = dc_map.get(dc["name"])
        if not cat:
            continue
        af = dc.get("actions_total_frequencies", {})
        buckets[cat]["n"] += n
        for akey, acode in action_codes.items():
            buckets[cat][akey] += af.get(acode, 0.0) * n

    result = {}
    for cat in cats:
        b = buckets[cat]
        n = b["n"]
        if n < 0.3:
            continue
        result[cat] = {"n": round(n, 1)}
        for akey in action_codes:
            result[cat][akey] = round(b[akey] / n * 100, 1)
    return result


def agg_sols(
    action_sols: list,
    hc_map: dict[str, str] | None = None,
    dc_map: dict[str, str] | None = None,
) -> dict[str, dict]:
    """action_solutions からカテゴリ × fold/call/raise 集計（fold/call/raise ノード用）。

    Parameters
    ----------
    action_sols  : sols["action_solutions"]
    hc_map       : hand_category 名 → カテゴリラベル (省略時 HC_5CAT)
    dc_map       : draw_category 名 → カテゴリラベル (省略時 DC_5CAT)

    Returns
    -------
    {カテゴリ: {"n": コンボ数, "fold": %, "call": %, ...}}
    """
    if hc_map is None:
        hc_map = HC_5CAT
    if dc_map is None:
        dc_map = DC_5CAT

    cat_total:   dict[str, float] = defaultdict(float)
    cat_actions: dict[str, dict]  = defaultdict(lambda: defaultdict(float))

    for asol in action_sols:
        raw = get_code(asol)
        if not raw:
            continue
        name = _ACTION_LABEL.get(raw, raw)
        for hc in asol.get("hand_categories", []):
            n = hc.get("total_combos", 0)
            if n < 0.3:
                continue
            cat = hc_map.get(hc["name"])
            if not cat:
                continue
            cat_total[cat]         += n
            cat_actions[cat][name] += n
        for dc in asol.get("draw_categories", []):
            n = dc.get("total_combos", 0)
            if n < 0.3:
                continue
            cat = dc_map.get(dc["name"])
            if not cat:
                continue
            cat_total[cat]         += n
            cat_actions[cat][name] += n

    result = {}
    for cat, total in cat_total.items():
        if total < 0.3:
            continue
        result[cat] = {"n": round(total, 1)}
        for name, combos in cat_actions[cat].items():
            result[cat][name] = round(combos / total * 100, 1)
    return result


# ─────────────────── JSON 永続化 ───────────────────

def load_json(path, *, default=None):
    """JSON ファイルを読み込む。存在しない/壊れている場合は default を返す。"""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return [] if default is None else default


def save_json(path, data):
    """data を JSON ファイルに保存する。"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
