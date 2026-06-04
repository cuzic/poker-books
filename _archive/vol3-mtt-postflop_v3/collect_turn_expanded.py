#!/usr/bin/env python3
"""
collect_turn_expanded.py — ターンバレル拡張収集スクリプト (45ボード)

【目的】
  board_ras_collect.py の 45 ボードセットに対して、ターンバレル RAS を収集する。
  各ボードで 3 種のターンカード (blank / IP 強化 / OOP 強化) を定義し、
  フロップ CBet サイズを自動取得してからターン行動の RAS を収集する。

【ターンカード定義】
  blank:    ボードに絡まない低ランクカード (最低ランク、非フラッシュスーツ)
  IP 強化:  IP レンジを強化するカード (ミドルカードのペア)
  OOP 強化: OOP レンジを強化するカード (ボードの最高カードへのオーバーカード)

【使い方】
  TOKEN=xxx GWCLIENTID=xxx uv run collect_turn_expanded.py --collect BTN_SBR25
  TOKEN=xxx GWCLIENTID=xxx uv run collect_turn_expanded.py --collect-all
  uv run collect_turn_expanded.py --analyze

【出力】
  findings/turn_expanded_{SCENARIO_KEY}.jsonl
  各レコード: {"board":"Ks7d2c","board_id":"K72_dry","high_cat":"K-high",
               "texture":"dry","scenario":"BTN_SBR25","flop_bet_code":"R33",
               "turns":{"blank":{"card":"4h","barrel_pct":78.5,...},
                        "TA+":{"card":"7h","barrel_pct":85.2,...},
                        "TA-":{"card":"Ah","barrel_pct":65.3,...}}}

  注: 出力 JSON のキー "TA+" / "TA-" は既存データとの互換性のため残置。
      新規書籍では「IP 強化 / OOP 強化」用語を使う (研究 archive 扱い)。
"""

import os, sys, json, time, argparse, requests
from pathlib import Path
from collections import defaultdict
from typing import Any

TOKEN          = os.environ.get("TOKEN", "")
GWCLIENTID     = os.environ.get("GWCLIENTID", "")
GOOGLE_ANAL_ID = os.environ.get("GOOGLE_ANAL_ID", "")
GT             = "MTTGeneral"
BASE_URL       = "https://api.gtowizard.com/v4/solutions/spot-solution/"
FINDINGS_DIR   = Path(__file__).parent / "findings"

# ─── シナリオ定義 ────────────────────────────────────────────
SCENARIOS: dict[str, dict[str, Any]] = {
    "BTN_SBR25": {"depth": 25.125, "pf": "F-F-F-F-F-R2.1-F-C", "label": "BTN-BB SBR25"},
    "BTN_SBR20": {"depth": 20.125, "pf": "F-F-F-F-F-R2-F-C",   "label": "BTN-BB SBR20"},
    "BTN_SBR40": {"depth": 40.125, "pf": "F-F-F-F-F-R2.5-F-C", "label": "BTN-BB SBR40"},
    "SB_SBR25":  {"depth": 25.125, "pf": "F-F-F-F-F-F-R3-C",   "label": "SB-BB  SBR25"},
    "SB_SBR20":  {"depth": 20.125, "pf": "F-F-F-F-F-F-R3-C",   "label": "SB-BB  SBR20"},
}

# ─── 45 ボードリスト (board_ras_collect.py より) ────────────
BOARDS: list[dict[str, str]] = [
    # A-high
    {"id": "A72_dry",   "board": "Ah7d2s",  "high": "A-high", "tex": "dry"},
    {"id": "A72_wet",   "board": "Ad7c2d",  "high": "A-high", "tex": "semi-wet"},
    {"id": "A94_dry",   "board": "Ah9d4s",  "high": "A-high", "tex": "semi-wet"},
    {"id": "A94_wet",   "board": "Ad9c4d",  "high": "A-high", "tex": "semi-wet"},
    {"id": "A87_conn",  "board": "Ah8d7s",  "high": "A-high", "tex": "wet-connected"},
    {"id": "A65_conn",  "board": "Ah6d5s",  "high": "A-high", "tex": "wet-connected"},
    {"id": "AKQ_broad", "board": "AhKdQs",  "high": "A-high", "tex": "dry"},
    {"id": "AJT_conn",  "board": "AhJdTs",  "high": "A-high", "tex": "wet-connected"},
    {"id": "A32_low",   "board": "Ah3d2s",  "high": "A-high", "tex": "dry"},
    {"id": "A_mono",    "board": "Ah9h5h",  "high": "A-high", "tex": "monotone"},
    {"id": "AA7_pair",  "board": "AhAd7c",  "high": "A-high", "tex": "paired"},
    # K-high
    {"id": "K72_dry",   "board": "Ks7d2c",  "high": "K-high", "tex": "dry"},
    {"id": "K72_wet",   "board": "Kd7c2d",  "high": "K-high", "tex": "semi-wet"},
    {"id": "K95_semi",  "board": "Kh9d5s",  "high": "K-high", "tex": "semi-wet"},
    {"id": "K65_conn",  "board": "Kh6d5s",  "high": "K-high", "tex": "wet-connected"},
    {"id": "KJT_conn",  "board": "KhJdTs",  "high": "K-high", "tex": "wet-connected"},
    {"id": "KJT_wet",   "board": "KdJcTd",  "high": "K-high", "tex": "wet-connected"},
    {"id": "K98_conn",  "board": "Kd9s8c",  "high": "K-high", "tex": "wet-connected"},
    {"id": "K_mono",    "board": "Kh8h3h",  "high": "K-high", "tex": "monotone"},
    {"id": "KK5_pair",  "board": "KhKd5s",  "high": "K-high", "tex": "paired"},
    # Q-high
    {"id": "Q83_dry",   "board": "Qh8d3s",  "high": "Q-high", "tex": "semi-wet"},
    {"id": "Q83_wet",   "board": "Qd8c3d",  "high": "Q-high", "tex": "semi-wet"},
    {"id": "Q72_dry",   "board": "Qh7d2s",  "high": "Q-high", "tex": "dry"},
    {"id": "QT8_conn",  "board": "QhTd8s",  "high": "Q-high", "tex": "wet-connected"},
    {"id": "Q_mono",    "board": "Qh7h2h",  "high": "Q-high", "tex": "monotone"},
    {"id": "QQ8_pair",  "board": "QhQd8s",  "high": "Q-high", "tex": "paired"},
    # J-high
    {"id": "J73_dry",   "board": "Jh7d3s",  "high": "J-high", "tex": "dry"},
    {"id": "J73_wet",   "board": "Jd7c3d",  "high": "J-high", "tex": "semi-wet"},
    {"id": "J95_semi",  "board": "Jh9d5s",  "high": "J-high", "tex": "semi-wet"},
    {"id": "JT8_conn",  "board": "JhTd8s",  "high": "J-high", "tex": "wet-connected"},
    {"id": "J_mono",    "board": "Jh6h2h",  "high": "J-high", "tex": "monotone"},
    {"id": "JJ6_pair",  "board": "JhJd6s",  "high": "J-high", "tex": "paired"},
    # T-high
    {"id": "T64_dry",   "board": "Th6d4s",  "high": "T-high", "tex": "dry"},
    {"id": "T98_conn",  "board": "Th9s8d",  "high": "T-high", "tex": "wet-connected"},
    {"id": "T98_wet",   "board": "Td9s8d",  "high": "T-high", "tex": "wet-connected"},
    {"id": "T87_conn",  "board": "Th8d7s",  "high": "T-high", "tex": "wet-connected"},
    {"id": "T_mono",    "board": "Th9h8h",  "high": "T-high", "tex": "monotone"},
    {"id": "TT5_pair",  "board": "ThTd5s",  "high": "T-high", "tex": "paired"},
    # Low boards
    {"id": "974_dry",   "board": "9h7d4s",  "high": "low",    "tex": "dry"},
    {"id": "965_conn",  "board": "9h6d5s",  "high": "low",    "tex": "wet-connected"},
    {"id": "765_conn",  "board": "7h6d5s",  "high": "low",    "tex": "wet-connected"},
    {"id": "765_wet",   "board": "7d6c5d",  "high": "low",    "tex": "wet-connected"},
    {"id": "742_dry",   "board": "7h4d2s",  "high": "low",    "tex": "dry"},
    {"id": "low_mono",  "board": "7h6h5h",  "high": "low",    "tex": "monotone"},
    {"id": "77x_pair",  "board": "7h7d2s",  "high": "low",    "tex": "paired"},
]

# カードランク定義 (高 → 低)
RANKS = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"]
RANK_VAL: dict[str, int] = {r: 14 - i for i, r in enumerate(RANKS)}

# ─── API ────────────────────────────────────────────────────

def make_headers() -> dict[str, str]:
    h: dict[str, str] = {
        "accept":             "application/json, text/plain, */*",
        "accept-language":    "ja,en;q=0.9",
        "authorization":      f"Bearer {TOKEN}",
        "cache-control":      "no-cache",
        "origin":             "https://app.gtowizard.com",
        "pragma":             "no-cache",
        "referer":            "https://app.gtowizard.com/",
        "sec-ch-ua":          '"Chromium";v="148", "Microsoft Edge";v="148", "Not/A)Brand";v="99"',
        "sec-ch-ua-mobile":   "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest":     "empty",
        "sec-fetch-mode":     "cors",
        "sec-fetch-site":     "same-site",
        "user-agent":         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    if GWCLIENTID:
        h["gwclientid"] = GWCLIENTID
    if GOOGLE_ANAL_ID:
        h["google-anal-id"] = GOOGLE_ANAL_ID
    return h


def call_api(board: str, depth: float = 25.125,
             pf: str = "F-F-F-F-F-R2.1-F-C", stacks: str = "",
             flop_actions: str = "X", turn_actions: str = "",
             river_actions: str = "") -> dict[str, Any] | None:
    params: dict[str, Any] = {
        "gametype": GT, "depth": str(depth), "stacks": stacks,
        "preflop_actions": pf, "flop_actions": flop_actions,
        "turn_actions": turn_actions, "river_actions": river_actions,
        "board": board,
    }
    for attempt in range(4):
        try:
            r = requests.get(BASE_URL, params=params, headers=make_headers(), timeout=30)
        except Exception as e:
            print(f"    接続エラー: {e}")
            time.sleep(5)
            continue
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 10))
            print(f"    429 rate limit, {wait}s 待機...")
            time.sleep(wait)
            continue
        if r.status_code == 204:
            print(f"    204 No Content (このシナリオはデータなし)")
            return None
        if r.status_code == 401:
            print(f"    401 Unauthorized: トークン期限切れ")
            sys.exit(1)
        print(f"    HTTP {r.status_code}: {r.text[:200]}")
        if attempt < 3:
            time.sleep(3)
    return None


def compute_cross(data: dict) -> dict[str, Any]:
    """API レスポンスから (hand × draw) bet% クロス集計を計算する。"""
    dcr = data.get("draw_categories_range", [])
    hcr = data.get("hand_categories_range", [])
    as_ = data.get("action_solutions", [])

    draw_map: dict[int, str] = {}
    hand_map: dict[int, str] = {}
    strategies: dict[str, list[float]] = {}

    for item in as_:
        code = item["action"]["code"]
        strategies[code] = item.get("strategy", [])
        if not draw_map:
            for d in (item.get("draw_categories") or []):
                draw_map[d["index"]] = d["name"]
        if not hand_map:
            for h in (item.get("hand_categories") or []):
                hand_map[h["index"]] = h["name"]

    bet_codes  = [c for c in strategies if c != "X"]
    cross: dict[tuple, list] = defaultdict(list)
    draw_agg: dict[str, dict] = defaultdict(lambda: {"total": 0.0, "bet": 0.0})
    hand_agg: dict[str, dict] = defaultdict(lambda: {"total": 0.0, "bet": 0.0})
    n_in_range = 0

    for i in range(min(1326, len(dcr), len(hcr))):
        total = sum(s[i] for s in strategies.values() if i < len(s))
        if total < 0.001:
            continue
        n_in_range += 1
        bet_f  = sum(strategies[c][i] for c in bet_codes if i < len(strategies[c]))
        d_name = draw_map.get(dcr[i], f"unk_{dcr[i]}")
        h_name = hand_map.get(hcr[i], f"unk_{hcr[i]}")

        cross[(h_name, d_name)].append(bet_f)
        draw_agg[d_name]["total"] += 1
        draw_agg[d_name]["bet"]   += bet_f
        hand_agg[h_name]["total"] += 1
        hand_agg[h_name]["bet"]   += bet_f

    return {
        "cross":    {f"{h}|{d}": {"vals": v, "n": len(v),
                                   "avg": sum(v)/len(v)*100 if v else 0}
                     for (h, d), v in cross.items()},
        "draw_agg": {k: {"total": v["total"],
                         "bet_pct": v["bet"]/v["total"]*100 if v["total"] > 0 else 0}
                     for k, v in draw_agg.items()},
        "hand_agg": {k: {"total": v["total"],
                         "bet_pct": v["bet"]/v["total"]*100 if v["total"] > 0 else 0}
                     for k, v in hand_agg.items()},
        "n_combos": n_in_range,
    }


# ─── ターンカード生成 ────────────────────────────────────────

def _board_ranks_suits(board: str) -> tuple[list[str], list[str]]:
    """ボード文字列をランクリストとスーツリストに分解する。
    例: "Ks7d2c" → (["K","7","2"], ["s","d","c"])
    """
    cards = [board[i:i+2] for i in range(0, len(board), 2)]
    ranks = [c[0] for c in cards]
    suits = [c[1] for c in cards]
    return ranks, suits


def _dominant_suit(suits: list[str]) -> str:
    """最も多いスーツ、同数なら出現順で最初のものを返す。"""
    from collections import Counter
    cnt = Counter(suits)
    return cnt.most_common(1)[0][0]


def define_turn_cards(board: str) -> dict[str, str]:
    """
    blank / IP 強化 / OOP 強化 のターンカードを定義する。
    (出力 dict key の "TA+" / "TA-" は研究データの互換性のため残置)

    blank:    ボード最小ランクより低いランク、かつボードにないスーツ
    IP 強化:  ボードのミドルカード (2番目に高いカード) と同ランク、別スーツ
    OOP 強化: ボードの最高カードより高いオーバーカード（A未満）、別スーツ
    """
    ranks, suits = _board_ranks_suits(board)
    board_rank_vals = [RANK_VAL[r] for r in ranks]
    board_rank_set  = set(ranks)
    board_suit_set  = set(suits)

    # 使用可能スーツ (ボードの dominant suit と異なるもの)
    dom_suit = _dominant_suit(suits)
    alt_suits = [s for s in ["h", "c", "d", "s"] if s != dom_suit and s not in board_suit_set]
    if not alt_suits:
        alt_suits = [s for s in ["h", "c", "d", "s"] if s != dom_suit]
    alt_suit = alt_suits[0]

    # blank: ボード最小ランクより低いランク、ボードにないランク
    min_val = min(board_rank_vals)
    blank_rank = None
    for r in reversed(RANKS):  # 2 から探す (reversed = 低順)
        if RANK_VAL[r] < min_val and r not in board_rank_set:
            blank_rank = r
            break
    if blank_rank is None:
        # ボード最低が2→ボードにないランクで最低のもの
        for r in reversed(RANKS):
            if r not in board_rank_set:
                blank_rank = r
                break
    blank_card = f"{blank_rank}{alt_suit}" if blank_rank else f"2{alt_suit}"

    # IP 強化: ボードの2番目に高いカードと同ランク (ミドルのペア)
    sorted_vals = sorted(set(board_rank_vals), reverse=True)
    if len(sorted_vals) >= 2:
        mid_val = sorted_vals[1]
    else:
        mid_val = sorted_vals[0]
    mid_rank = [r for r in RANKS if RANK_VAL[r] == mid_val][0]
    # alt_suit が mid_rank と被っていなければ OK (ランクは被ってもスーツが違えば別カード)
    ta_plus_card = f"{mid_rank}{alt_suit}"

    # OOP 強化: ボード最高カードより高いオーバーカード
    max_val = max(board_rank_vals)
    ta_minus_rank = None
    for r in RANKS:  # A から降順に探す
        if RANK_VAL[r] > max_val and r not in board_rank_set:
            ta_minus_rank = r
            break
    if ta_minus_rank is None:
        # オーバーカードがなければ (ボードがAハイの場合)、最高カードより1つ上にない
        # → K が使えるか試みる
        for r in RANKS:
            if r not in board_rank_set and r != mid_rank:
                ta_minus_rank = r
                break
    ta_minus_card = f"{ta_minus_rank}{alt_suit}" if ta_minus_rank else f"K{alt_suit}"

    return {"blank": blank_card, "TA+": ta_plus_card, "TA-": ta_minus_card}


# ─── フロップ CBet コード取得 ────────────────────────────────

def get_flop_bet_code(data: dict) -> str:
    """フロップ解のアクション一覧から主要ベットサイズコードを取得する。"""
    as_ = data.get("action_solutions", [])
    bet_codes = []
    for item in as_:
        code = item["action"]["code"]
        if code != "X":
            bet_codes.append(code)
    if not bet_codes:
        return "R33"  # デフォルト
    # 出現頻度ベースで最多コードを選ぶ (先頭でも可)
    return bet_codes[0]


def compute_barrel_pct(data: dict) -> float:
    """ターン解の overall bet 率を返す。"""
    as_ = data.get("action_solutions", [])
    if not as_:
        return 0.0
    strategies: dict[str, list[float]] = {}
    for item in as_:
        strategies[item["action"]["code"]] = item.get("strategy", [])
    bet_codes = [c for c in strategies if c != "X"]
    total_combos = 0
    total_bet    = 0.0
    for i in range(min(1326, *[len(s) for s in strategies.values()] if strategies else [0])):
        all_sum = sum(s[i] for s in strategies.values() if i < len(s))
        if all_sum < 0.001:
            continue
        total_combos += 1
        total_bet += sum(strategies[c][i] for c in bet_codes if i < len(strategies[c]))
    if total_combos == 0:
        return 0.0
    return total_bet / total_combos * 100.0


# ─── 収集 ────────────────────────────────────────────────────

def load_existing(outf: Path) -> set[str]:
    existing: set[str] = set()
    if outf.exists():
        for line in outf.read_text().splitlines():
            if line.strip():
                try:
                    rec = json.loads(line)
                    existing.add(rec.get("board_id", ""))
                except json.JSONDecodeError:
                    pass
    return existing


def collect_scenario(scenario_key: str, force: bool = False) -> None:
    if scenario_key not in SCENARIOS:
        print(f"Unknown scenario: {scenario_key}")
        return
    cfg = SCENARIOS[scenario_key]
    outf = FINDINGS_DIR / f"turn_expanded_{scenario_key}.jsonl"
    FINDINGS_DIR.mkdir(exist_ok=True)

    existing = load_existing(outf) if not force else set()
    if force and outf.exists():
        bak = outf.with_suffix(".jsonl.bak")
        outf.rename(bak)
        print(f"  --force: バックアップ → {bak}")

    label = cfg["label"]
    print(f"\n=== COLLECT: ターン拡張 {label} ({scenario_key}) ===")
    print(f"  対象: {len(BOARDS)}ボード（既存スキップ: {len(existing)}）\n")

    with outf.open("a") as fout:
        for bcfg in BOARDS:
            bid   = bcfg["id"]
            board = bcfg["board"]

            if bid in existing:
                print(f"  ⏭  {bid:15s} スキップ（既存）")
                continue

            print(f"  ⬇  {bid:15s} {board} [{bcfg['tex']}]")

            # Step0: フロップ CBet コード取得
            flop_data = call_api(board, depth=cfg["depth"], pf=cfg["pf"],
                                 flop_actions="X")
            if flop_data is None or "action_solutions" not in flop_data:
                print(f"    ❌ フロップ解なし → スキップ")
                time.sleep(1)
                continue
            bet_code = get_flop_bet_code(flop_data)
            print(f"    フロップ CBet コード: {bet_code}")
            time.sleep(1.0)

            # ターンカード定義
            turn_cards = define_turn_cards(board)

            turns_result: dict[str, Any] = {}
            for tag, turn_card in turn_cards.items():
                print(f"    → ターン [{tag}] カード={turn_card}")
                turn_data = call_api(
                    board + turn_card,
                    depth=cfg["depth"], pf=cfg["pf"],
                    flop_actions=bet_code,
                    turn_actions="X",
                )
                if turn_data is None or "action_solutions" not in turn_data:
                    print(f"      ❌ データなし")
                    time.sleep(0.5)
                    continue

                crs = compute_cross(turn_data)
                barrel_pct = compute_barrel_pct(turn_data)
                print(f"      barrel_pct={barrel_pct:.1f}%  combos={crs['n_combos']}")

                turns_result[tag] = {
                    "card":       turn_card,
                    "barrel_pct": round(barrel_pct, 2),
                    "hand_agg":   crs["hand_agg"],
                    "draw_agg":   crs["draw_agg"],
                    "n_combos":   crs["n_combos"],
                }
                time.sleep(1.0)

            if not turns_result:
                print(f"    ❌ ターンデータなし → スキップ")
                continue

            rec = {
                "board":        board,
                "board_id":     bid,
                "high_cat":     bcfg["high"],
                "texture":      bcfg["tex"],
                "scenario":     scenario_key,
                "flop_bet_code": bet_code,
                "turns":        turns_result,
            }
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()
            print(f"    ✅ 保存完了")
            time.sleep(0.5)

    print(f"\n  完了: {scenario_key}")


def collect_all(force: bool = False) -> None:
    for key in SCENARIOS:
        collect_scenario(key, force=force)


# ─── 分析 ────────────────────────────────────────────────────

def analyze() -> None:
    """テクスチャー × ターンカードタイプ別のバレル率比較表を出力する。"""
    # データ読み込み
    all_recs: list[dict] = []
    for key in SCENARIOS:
        outf = FINDINGS_DIR / f"turn_expanded_{key}.jsonl"
        if not outf.exists():
            continue
        for line in outf.read_text().splitlines():
            if line.strip():
                try:
                    rec = json.loads(line)
                    rec["scenario_key"] = key
                    all_recs.append(rec)
                except json.JSONDecodeError:
                    pass

    if not all_recs:
        print("データなし — --collect SCENARIO_KEY を先に実行してください。")
        return

    print("\n=== ターンバレル率 分析 ===")
    print()

    # シナリオ別 × テクスチャー × ターンタイプ
    for sc_key in SCENARIOS:
        recs = [r for r in all_recs if r.get("scenario_key") == sc_key]
        if not recs:
            continue

        label = SCENARIOS[sc_key]["label"]
        print(f"\n  [{sc_key}] {label}  ({len(recs)} boards)")

        # テクスチャー別集計
        tex_data: dict[str, dict[str, list[float]]] = defaultdict(
            lambda: {"blank": [], "TA+": [], "TA-": []}
        )
        for rec in recs:
            tex = rec.get("texture", "unknown")
            for tag in ["blank", "TA+", "TA-"]:
                t = rec.get("turns", {}).get(tag, {})
                if t.get("barrel_pct") is not None:
                    tex_data[tex][tag].append(t["barrel_pct"])

        def avg(lst: list[float]) -> str:
            if not lst:
                return " —  "
            return f"{sum(lst)/len(lst):4.0f}%"

        print(f"  {'テクスチャー':<16} {'blank':>6} {'TA+':>6} {'TA-':>6}  (n)")
        print(f"  {'-'*16} {'-'*6} {'-'*6} {'-'*6}  {'-'*5}")
        for tex in ["dry", "semi-wet", "wet-connected", "monotone", "paired"]:
            d = tex_data.get(tex, {})
            n = len(d.get("blank", []))
            if n == 0:
                continue
            bl = avg(d.get("blank", []))
            tp = avg(d.get("TA+", []))
            tm = avg(d.get("TA-", []))
            print(f"  {tex:<16} {bl:>6} {tp:>6} {tm:>6}  ({n})")

    print()
    print("  読み方:")
    print("    blank    : ターンがブランクカード → CBet 継続率")
    print("    IP 強化  : ターンで IP レンジが強化 → バレル増加期待 (旧 TA+)")
    print("    OOP 強化 : ターンで OOP レンジが強化 → バレル抑制期待 (旧 TA-)")

    # ボード別詳細 (最初の収集済みシナリオのみ)
    first_sc = next((k for k in SCENARIOS if any(r.get("scenario_key") == k for r in all_recs)), None)
    if first_sc:
        recs = [r for r in all_recs if r.get("scenario_key") == first_sc]
        print(f"\n  [ボード別詳細: {first_sc}]")
        print(f"  {'board_id':<15} {'tex':<14} {'blank':>6} {'TA+':>6} {'TA-':>6}")
        print(f"  {'-'*15} {'-'*14} {'-'*6} {'-'*6} {'-'*6}")
        for rec in sorted(recs, key=lambda r: (r.get("texture",""), r.get("board_id",""))):
            turns = rec.get("turns", {})
            def bp(tag: str) -> str:
                t = turns.get(tag, {})
                bp_val = t.get("barrel_pct")
                return f"{bp_val:4.0f}%" if bp_val is not None else "  — "
            print(f"  {rec['board_id']:<15} {rec.get('texture',''):14} "
                  f"{bp('blank'):>6} {bp('TA+'):>6} {bp('TA-'):>6}")


# ─── メイン ─────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description="ターンバレル拡張収集スクリプト (45ボード × 3ターンカード)"
    )
    ap.add_argument("--collect", metavar="SCENARIO_KEY",
                    choices=list(SCENARIOS.keys()),
                    help="指定シナリオを収集 (例: BTN_SBR25, SB_SBR20)")
    ap.add_argument("--collect-all", action="store_true",
                    help="全シナリオを収集")
    ap.add_argument("--analyze", action="store_true",
                    help="収集済みデータを分析してテクスチャー × ターンタイプ比較表を出力")
    ap.add_argument("--force", action="store_true",
                    help="既存データを無視して再収集")
    args = ap.parse_args()

    if args.collect:
        collect_scenario(args.collect, force=args.force)
    elif args.collect_all:
        collect_all(force=args.force)
    elif args.analyze:
        analyze()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
