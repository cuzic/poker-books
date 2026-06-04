#!/usr/bin/env python3
"""
defense_study.py — フロップ防御頻度分析（コール/フォールド/レイズ）

【2ステップ収集方式】
  Step1: アタッカーのベットコード取得
    OOP守備 (IP CBet): flop_actions="X"  → IP (BTN) の CBet コードと頻度
    IP守備  (OOP lead): flop_actions=""   → OOP (BB)  の lead コードと頻度
  Step2: ディフェンダーのレスポンス取得
    OOP守備: flop_actions="X-{bet_code}"  → OOP の call/fold/raise
    IP守備:  flop_actions="{lead_code}"   → IP  の call/fold/raise

【シナリオ】
  SRP OOP守備 (BTN-BB): BB が BTN の CBet に対し call/fold/raise
  SRP OOP守備 (BTN-SB cc): SB が BTN の CBet に対し call/fold/raise
  3BP OOP守備 (BB 3-bettor): BB が BTN caller の CBet に対し守備
  3BP IP守備  (BTN caller): BTN が BB 3-bettor のリードに対し守備
  3BP OOP守備 (SB caller vs BB 3-bet): SB が BB の CBet に対し守備

使い方:
  TOKEN=... GWCLIENTID=... python3 defense_study.py --probe
  TOKEN=... GWCLIENTID=... python3 defense_study.py --collect --scenario SRP25_OOP
  TOKEN=... GWCLIENTID=... python3 defense_study.py --collect --all
  python3 defense_study.py --analyze --scenario SRP25_OOP
  python3 defense_study.py --analyze --all
"""

import os, sys, json, time, argparse, requests
from pathlib import Path
from collections import defaultdict
from typing import Any

TOKEN          = os.environ.get("TOKEN", "")
GWCLIENTID     = os.environ.get("GWCLIENTID", "")
GOOGLE_ANAL_ID = os.environ.get("GOOGLE_ANAL_ID", "")
GT             = "MTTGeneral"
FINDINGS_DIR   = Path(__file__).parent / "findings"
BASE_URL       = "https://api.gtowizard.com/v4/solutions/spot-solution/"

# ──────────────────── 防御シナリオ定義 ────────────────────
#
# first_step: アタッカーのオプションを取得するための flop_actions
#   "X"  = OOP がチェック済み → IP の CBet 判断 (SRP/3BP OOP守備)
#   ""   = フロップ開始 → OOP がリード or チェック (3BP IP守備)
#
DEFENSE_SCENARIOS: dict[str, dict[str, Any]] = {
    # ── SRP: OOP(BB)が IP(BTN)の CBetに守備 ──
    "SRP25_OOP": {
        "depth": 25.125, "pf": "F-F-F-F-F-R2.1-F-C", "stacks": "",
        "first_step": "X",
        "label": "SRP SBR25 BTN-BB | OOP(BB)守備 vs BTN CBet",
        "pot_type": "SRP",
    },
    "SRP20_OOP": {
        "depth": 20.125, "pf": "F-F-F-F-F-R2-F-C", "stacks": "",
        "first_step": "X",
        "label": "SRP SBR20 BTN-BB | OOP(BB)守備 vs BTN CBet",
        "pot_type": "SRP",
    },
    # ── SRP: OOP(SB)が IP(BTN)の CBetに守備 (SB コールドコール) ──
    "SRP25_SB_OOP": {
        "depth": 25.125, "pf": "F-F-F-F-F-R2.1-C-F", "stacks": "",
        "first_step": "X",
        "label": "SRP SBR25 BTN-SB(cc) | OOP(SB)守備 vs BTN CBet",
        "pot_type": "SRP",
    },
    # ── 3BP BTN-BB: OOP(BB, 3ベット側)が IP(BTN, コール側)の CBetに守備 ──
    "3BP20_OOP": {
        "depth": 20.125, "pf": "F-F-F-F-F-R2-F-R7-C", "stacks": "",
        "first_step": "X",  # BB チェック → BTN CBet → BB 守備
        "label": "3BP SBR20 BTN-BB | OOP(BB)守備 vs BTN CBet",
        "pot_type": "3BP",
    },
    # ── 3BP BTN-BB: IP(BTN, コール側)が OOP(BB, 3ベット側)のリードに守備 ──
    "3BP20_IP": {
        "depth": 20.125, "pf": "F-F-F-F-F-R2-F-R7-C", "stacks": "",
        "first_step": "",   # BB がリード → BTN 守備
        "label": "3BP SBR20 BTN-BB | IP(BTN)守備 vs BB lead",
        "pot_type": "3BP",
    },
    # ── 3BP SB-BB: OOP(SB, コール側)が IP(BB, 3ベット側)の CBetに守備 ──
    # preflop: SB open R3 → BB 3bet R8 → SB call
    "3BP25_SB_OOP": {
        "depth": 25.125, "pf": "F-F-F-F-F-F-R3-R8-C", "stacks": "",
        "first_step": "X",  # SB チェック → BB CBet → SB 守備
        "label": "3BP SBR25 SB-BB | OOP(SB)守備 vs BB CBet",
        "pot_type": "3BP",
    },
    # ── SRP SB-BB: IP(BB)が OOP(SB)の CBetに守備 ──
    "SRP25_SB_IP": {
        "depth": 25.125, "pf": "F-F-F-F-F-F-R3-C", "stacks": "",
        "first_step": "",   # SB がリード → BB 守備
        "label": "SRP SBR25 SB-BB | IP(BB)守備 vs SB CBet",
        "pot_type": "SRP",
    },
    "SRP20_SB_IP": {
        "depth": 20.125, "pf": "F-F-F-F-F-F-R3-C", "stacks": "",
        "first_step": "",   # SB がリード → BB 守備
        "label": "SRP SBR20 SB-BB | IP(BB)守備 vs SB CBet",
        "pot_type": "SRP",
    },
    # ── SRP BTN-SB cc SBR20: OOP(SB)が IP(BTN)の CBetに守備 ──
    "SRP20_SB_OOP": {
        "depth": 20.125, "pf": "F-F-F-F-F-R2-C-F", "stacks": "",
        "first_step": "X",  # SB チェック → BTN CBet → SB 守備
        "label": "SRP SBR20 BTN-SB(cc) | OOP(SB)守備 vs BTN CBet",
        "pot_type": "SRP",
    },
    # ── 3BP SB-BB: IP(BB, 3ベット側)が OOP(SB, コール側)のリードに守備 ──
    "3BP25_SB_IP": {
        "depth": 25.125, "pf": "F-F-F-F-F-F-R3-R8-C", "stacks": "",
        "first_step": "",   # SB がリード → BB 守備
        "label": "3BP SBR25 SB-BB | IP(BB)守備 vs SB lead",
        "pot_type": "3BP",
    },
    # 3BP25 BTN-BB は MTTGeneral に GTO ソリューションなし（HTTP 204）→ 除外

    # ── ポジション別比較（SBR25/20、全ポジション R2.1/R2.0 で有効）──
    # BB が OOP で IP(opener)の CBet に守備。ポジション幅の違いを実測。

    # SBR25: CO/HJ/EP3（BTN=SRP25_OOP と比較）
    "CO_BB_SRP25": {
        "depth": 25.125, "pf": "F-F-F-F-R2.1-F-F-C", "stacks": "",
        "first_step": "X",
        "label": "SRP SBR25 CO-BB | OOP(BB)守備 vs CO CBet",
        "pot_type": "SRP",
    },
    "HJ_BB_SRP25": {
        "depth": 25.125, "pf": "F-F-F-R2.1-F-F-F-C", "stacks": "",
        "first_step": "X",
        "label": "SRP SBR25 HJ-BB | OOP(BB)守備 vs HJ CBet",
        "pot_type": "SRP",
    },
    "EP3_BB_SRP25": {
        "depth": 25.125, "pf": "F-F-R2.1-F-F-F-F-C", "stacks": "",
        "first_step": "X",
        "label": "SRP SBR25 EP3-BB | OOP(BB)守備 vs EP3 CBet",
        "pot_type": "SRP",
    },

    # SBR20: CO/HJ/EP3/EP2/EP1（BTN=SRP20_OOP と比較）
    "CO_BB_SRP20": {
        "depth": 20.125, "pf": "F-F-F-F-R2-F-F-C", "stacks": "",
        "first_step": "X",
        "label": "SRP SBR20 CO-BB | OOP(BB)守備 vs CO CBet",
        "pot_type": "SRP",
    },
    "HJ_BB_SRP20": {
        "depth": 20.125, "pf": "F-F-F-R2-F-F-F-C", "stacks": "",
        "first_step": "X",
        "label": "SRP SBR20 HJ-BB | OOP(BB)守備 vs HJ CBet",
        "pot_type": "SRP",
    },
    "EP3_BB_SRP20": {
        "depth": 20.125, "pf": "F-F-R2-F-F-F-F-C", "stacks": "",
        "first_step": "X",
        "label": "SRP SBR20 EP3-BB | OOP(BB)守備 vs EP3 CBet",
        "pot_type": "SRP",
    },
    "EP2_BB_SRP20": {
        "depth": 20.125, "pf": "F-R2-F-F-F-F-F-C", "stacks": "",
        "first_step": "X",
        "label": "SRP SBR20 EP2-BB | OOP(BB)守備 vs EP2 CBet",
        "pot_type": "SRP",
    },
    "EP1_BB_SRP20": {
        "depth": 20.125, "pf": "R2-F-F-F-F-F-F-C", "stacks": "",
        "first_step": "X",
        "label": "SRP SBR20 EP1-BB | OOP(BB)守備 vs EP1 CBet",
        "pot_type": "SRP",
    },
}

# ──────────────────── 調査ボード定義 ────────────────────
DEFENSE_BOARDS: list[dict[str, Any]] = [
    # 型1: エースドライ
    {"board_id": "A72_rain", "board": "Ah7d2s", "board_type": 1, "label": "A-7-2 型1 エースドライ"},
    {"board_id": "A94_rain", "board": "Ah9d4s", "board_type": 1, "label": "A-9-4 型1 エース高セミ"},
    # 型2〜3: ハイウェット / セミウェット
    {"board_id": "K98_rain", "board": "Kd9s8c", "board_type": 2, "label": "K-9-8 型2 セミウェット"},
    {"board_id": "Q83_rain", "board": "Qh8d3s", "board_type": 2, "label": "Q-8-3 型2 ハイウェット"},
    {"board_id": "T98_rain", "board": "Th9s8d", "board_type": 3, "label": "T-9-8 型3 OESDコネクト"},
    {"board_id": "KJT_rain", "board": "KhJdTs", "board_type": 3, "label": "K-J-T 型3 高ウェットOESD"},
    # 型4: ローウェット
    {"board_id": "765_rain", "board": "7h6d5s", "board_type": 4, "label": "7-6-5 型4 ローウェット"},
    # 型5: 断絶
    {"board_id": "T74_rain", "board": "Th7d4s", "board_type": 5, "label": "T-7-4 型5 ミッド断絶"},
    {"board_id": "J73_rain", "board": "Jh7d3s", "board_type": 5, "label": "J-7-3 型5 ミッドドライ"},
    # 型6: ローdry
    {"board_id": "742_rain", "board": "7h4d2s", "board_type": 6, "label": "7-4-2 型6 ローdry"},
    # 型7: ペアボード
    {"board_id": "KK8_rain", "board": "KhKd8c", "board_type": 7, "label": "K-K-8 型7 ペアボード"},
    {"board_id": "AA7_rain", "board": "AhAd7c", "board_type": 7, "label": "A-A-7 型7 エースペアボード"},
]

FOCUS_HANDS = [
    "top_pair", "overpair", "second_pair", "third_pair", "low_pair",
    "underpair", "two_pair", "set", "trips", "straight",
    "no_made_hand", "ace_high", "king_high",
]
FOCUS_DRAWS = ["no_draw", "gutshot", "oesd", "flush_draw", "nut_flush_draw", "combo_draw"]

HAND_LABEL = {
    "top_pair":    "トップP",    "overpair":   "オーバーP",
    "second_pair": "2ndP",       "third_pair":  "3rdP",
    "low_pair":    "ロウP",      "underpair":   "アンダーP",
    "two_pair":    "ツーP",      "set":         "セット",
    "trips":       "トリップス", "straight":    "ストレート",
    "no_made_hand":"メイドなし", "ace_high":    "A高",
    "king_high":   "K高",
}
DRAW_LABEL = {
    "no_draw":       "ドローなし",   "gutshot":      "ガット",
    "oesd":          "OESD",        "flush_draw":   "FD",
    "nut_flush_draw":"ナットFD",    "combo_draw":   "コンボ",
}


# ──────────────────── API ユーティリティ ────────────────────

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


def check_auth() -> bool:
    try:
        import base64 as _b64
        payload = TOKEN.split(".")[1] + "=="
        data = json.loads(_b64.b64decode(payload))
        exp = data.get("exp", 0)
        remaining = exp - time.time()
        if remaining < 60:
            print(f"トークン期限切れ (残り {remaining:.0f}秒)")
            return False
        print(f"認証OK（残り{remaining/60:.1f}分）")
        return True
    except Exception:
        print("トークン検証失敗（続行）")
        return True


def call_api(board: str, depth: float, pf: str,
             flop_actions: str, stacks: str = "") -> dict[str, Any] | None:
    params: dict[str, Any] = {
        "gametype": GT, "depth": str(depth), "stacks": stacks,
        "preflop_actions": pf, "flop_actions": flop_actions,
        "turn_actions": "", "river_actions": "", "board": board,
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
                    print(f"  日次クォータ超過 (limit={body['request_limit']}, {int(ra)//3600}時間後リセット)")
                    sys.exit(1)
            except Exception:
                pass
            wait = int(r.headers.get("Retry-After", 10))
            print(f"    429 rate limit, {wait}s 待機...")
            time.sleep(wait)
            continue
        if r.status_code == 401:
            print(f"    401 Unauthorized: トークン期限切れ")
            return None
        if attempt < 3:
            time.sleep(3)
    return None


# ──────────────────── ベットコード抽出 ────────────────────

def dominant_bet_code(sols: list[dict]) -> tuple[str, float, str]:
    """
    action_solutions から最高頻度の RAISE コードを返す。
    (code, total_frequency, betsize_by_pot) を返す。
    """
    best: tuple[str, float, str] = ("", 0.0, "")
    for sol in sols:
        act = sol["action"]
        if act["type"] == "RAISE":
            freq = sol.get("total_frequency", 0.0)
            if freq > best[1]:
                best = (act["code"], freq, act.get("betsize_by_pot", "") or "")
    return best


def all_bet_codes(sols: list[dict]) -> list[tuple[str, float, str]]:
    """action_solutions から全 RAISE コード (code, freq, betsize_by_pot) リストを返す。"""
    result = []
    for sol in sols:
        act = sol["action"]
        if act["type"] == "RAISE":
            result.append((act["code"], sol.get("total_frequency", 0.0),
                           act.get("betsize_by_pot", "") or ""))
    return sorted(result, key=lambda x: -x[1])


# ──────────────────── 防御頻度クロス集計 ────────────────────

def compute_defense(data: dict) -> dict[str, Any]:
    """
    APIレスポンスから (hand × draw) call%/fold%/raise% クロス集計を計算する。
    """
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

    call_codes  = [c for c in strategies if c == "C"]
    fold_codes  = [c for c in strategies if c == "F"]
    raise_codes = [c for c in strategies if c.startswith("R") or c == "RAI"]
    all_codes   = list(strategies.keys())

    cross: dict[tuple, dict] = defaultdict(
        lambda: {"call": [], "fold": [], "raise": []}
    )
    draw_agg: dict[str, dict] = defaultdict(
        lambda: {"total": 0.0, "call": 0.0, "fold": 0.0, "raise": 0.0}
    )
    hand_agg: dict[str, dict] = defaultdict(
        lambda: {"total": 0.0, "call": 0.0, "fold": 0.0, "raise": 0.0}
    )
    n_in_range = 0

    for i in range(min(1326, len(dcr), len(hcr))):
        total = sum(s[i] for s in strategies.values() if i < len(s))
        if total < 0.001:
            continue
        n_in_range += 1

        call_f  = sum(strategies[c][i] for c in call_codes  if i < len(strategies[c]))
        fold_f  = sum(strategies[c][i] for c in fold_codes  if i < len(strategies[c]))
        raise_f = sum(strategies[c][i] for c in raise_codes if i < len(strategies[c]))

        d_name = draw_map.get(dcr[i], f"unk_{dcr[i]}")
        h_name = hand_map.get(hcr[i], f"unk_{hcr[i]}")

        cross[(h_name, d_name)]["call"].append(call_f)
        cross[(h_name, d_name)]["fold"].append(fold_f)
        cross[(h_name, d_name)]["raise"].append(raise_f)

        draw_agg[d_name]["total"] += 1
        draw_agg[d_name]["call"]  += call_f
        draw_agg[d_name]["fold"]  += fold_f
        draw_agg[d_name]["raise"] += raise_f

        hand_agg[h_name]["total"] += 1
        hand_agg[h_name]["call"]  += call_f
        hand_agg[h_name]["fold"]  += fold_f
        hand_agg[h_name]["raise"] += raise_f

    def avg_pct(vals: list) -> float:
        return sum(vals) / len(vals) * 100 if vals else 0.0

    def agg_to_pct(agg: dict) -> dict:
        t = agg["total"]
        if t <= 0:
            return {"total": 0, "call_pct": 0.0, "fold_pct": 0.0, "raise_pct": 0.0}
        return {
            "total":     t,
            "call_pct":  agg["call"]  / t * 100,
            "fold_pct":  agg["fold"]  / t * 100,
            "raise_pct": agg["raise"] / t * 100,
        }

    return {
        "cross": {
            f"{h}|{d}": {
                "n":         len(v["call"]),
                "call_pct":  avg_pct(v["call"]),
                "fold_pct":  avg_pct(v["fold"]),
                "raise_pct": avg_pct(v["raise"]),
            }
            for (h, d), v in cross.items()
        },
        "draw_agg": {k: agg_to_pct(v) for k, v in draw_agg.items()},
        "hand_agg": {k: agg_to_pct(v) for k, v in hand_agg.items()},
        "draw_map": {str(k): v for k, v in draw_map.items()},
        "hand_map": {str(k): v for k, v in hand_map.items()},
        "n_combos":    n_in_range,
        "action_codes": all_codes,
    }


# ──────────────────── 収集 ────────────────────

def collect_scenario(scenario_key: str, cfg: dict[str, Any], force: bool) -> None:
    outf = FINDINGS_DIR / f"defense_study_{scenario_key}.jsonl"
    FINDINGS_DIR.mkdir(exist_ok=True)

    existing: set[str] = set()
    if outf.exists() and not force:
        for line in outf.read_text().splitlines():
            if line.strip():
                try:
                    rec = json.loads(line)
                    if "cross" in rec:
                        existing.add(rec["board_id"])
                except json.JSONDecodeError:
                    pass

    if not check_auth():
        sys.exit(1)

    if force and outf.exists():
        bak = outf.with_suffix(".jsonl.bak")
        outf.rename(bak)
        print(f"  --force: バックアップ → {bak}")
        existing.clear()

    first_step = cfg["first_step"]  # "X" or ""
    label = cfg.get("label", scenario_key)
    print(f"\n=== COLLECT: {label} ===")
    print(f"    first_step: {first_step!r}  pot_type: {cfg['pot_type']}\n")

    for bcfg in DEFENSE_BOARDS:
        bid = bcfg["board_id"]
        if bid in existing:
            print(f"  [{bid}] スキップ（既存）")
            continue

        board = bcfg["board"]
        print(f"\n  [{bid}] {board} — {bcfg['label']}")

        # ── Step1: アタッカーのベットコード取得 ──
        data_attack = call_api(board, cfg["depth"], cfg["pf"],
                                flop_actions=first_step, stacks=cfg.get("stacks", ""))
        if data_attack is None or "action_solutions" not in data_attack:
            print(f"    Step1 API失敗")
            time.sleep(1.0)
            continue

        # 全 RAISE コードと支配的コードを取得
        bet_list = all_bet_codes(data_attack.get("action_solutions", []))
        if not bet_list:
            print(f"    ベットオプションなし（チェック専用）")
            time.sleep(1.0)
            continue

        # 支配的ベットコード
        dom_code, dom_freq, dom_betsize = bet_list[0]
        dom_pot = float(dom_betsize) if dom_betsize else 0.0
        print(f"    攻撃side ベット候補: {[(c, f'{f:.2f}') for c,f,_ in bet_list[:4]]}")
        print(f"    支配的: {dom_code}  freq={dom_freq:.2f}  pot={dom_pot:.2%}")

        time.sleep(1.0)

        # ── Step2: ディフェンダーのレスポンス取得 ──
        defense_step = f"{first_step}-{dom_code}" if first_step else dom_code
        data_def = call_api(board, cfg["depth"], cfg["pf"],
                             flop_actions=defense_step, stacks=cfg.get("stacks", ""))
        if data_def is None or "action_solutions" not in data_def:
            print(f"    Step2 API失敗 (defense_step={defense_step!r})")
            time.sleep(1.0)
            continue

        action_codes = [a["action"]["code"] for a in data_def.get("action_solutions", [])]
        print(f"    守備side アクション: {action_codes}")

        crs = compute_defense(data_def)
        print(f"    in-range combos: {crs['n_combos']}")

        # ハンド別集計表示
        for hname in ["top_pair", "second_pair", "set", "no_made_hand"]:
            ha = crs["hand_agg"].get(hname)
            if ha and ha.get("total", 0) > 0.5:
                print(f"    {HAND_LABEL.get(hname, hname):10s}: "
                      f"C={ha['call_pct']:4.0f}% "
                      f"F={ha['fold_pct']:4.0f}% "
                      f"R={ha['raise_pct']:4.0f}%")

        rec = {
            "board_id":        bid,
            "board":           board,
            "board_type":      bcfg["board_type"],
            "label":           bcfg["label"],
            "scenario":        scenario_key,
            "first_step":      first_step,
            "defense_step":    defense_step,
            "attack_code":     dom_code,
            "attack_freq":     round(dom_freq, 4),
            "attack_betsize_pot": round(dom_pot, 4),
            "pot_type":        cfg["pot_type"],
            "cross":           crs["cross"],
            "draw_agg":        crs["draw_agg"],
            "hand_agg":        crs["hand_agg"],
            "n_combos":        crs["n_combos"],
            "action_codes":    crs["action_codes"],
        }

        with outf.open("a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        time.sleep(1.5)


# ──────────────────── 分析 ────────────────────

def fmt_defense(data: dict, hname: str, dname: str) -> str:
    key = f"{hname}|{dname}"
    c = data["cross"].get(key)
    if not c or c["n"] < 2:
        return "    —   "
    cp = c["call_pct"]
    fp = c["fold_pct"]
    rp = c["raise_pct"]
    return f"C{cp:2.0f}/F{fp:2.0f}/R{rp:2.0f}"


def analyze_scenario(scenario_key: str) -> None:
    inpf = FINDINGS_DIR / f"defense_study_{scenario_key}.jsonl"
    if not inpf.exists():
        print(f"データなし: {inpf}")
        return

    boards: dict[str, dict] = {}
    for line in inpf.read_text().splitlines():
        if line.strip():
            try:
                rec = json.loads(line)
                if "cross" in rec:
                    boards[rec["board_id"]] = rec
            except json.JSONDecodeError:
                pass

    print(f"\n{'═'*90}")
    print(f"  DEFENSE STUDY: {scenario_key}")
    print(f"  (C=コール%, F=フォールド%, R=レイズ%)")
    print(f"{'═'*90}")

    # ── ベットサイズ分布 ──
    print(f"\n  [使用ベットサイズ (支配的コード)]")
    for bid, rec in sorted(boards.items(), key=lambda x: x[1].get("board_type", 0)):
        code = rec.get("attack_code", "?")
        freq = rec.get("attack_freq", 0) * 100
        bpot = rec.get("attack_betsize_pot", 0) * 100
        print(f"    [{bid}] {code}  freq={freq:.0f}%  pot={bpot:.0f}%")

    # ── ハンド別集計（全ボード平均） ──
    print(f"\n  [ハンド別 防御頻度 — 全ボード平均]")
    combined_hand: dict[str, dict] = defaultdict(
        lambda: {"total": 0.0, "call": 0.0, "fold": 0.0, "raise": 0.0}
    )
    for rec in boards.values():
        for hname, ha in rec.get("hand_agg", {}).items():
            t = ha.get("total", 0)
            combined_hand[hname]["total"] += t
            combined_hand[hname]["call"]  += ha.get("call_pct",  0) * t / 100
            combined_hand[hname]["fold"]  += ha.get("fold_pct",  0) * t / 100
            combined_hand[hname]["raise"] += ha.get("raise_pct", 0) * t / 100

    print(f"  {'ハンド':12s}  {'コール':>6s}  {'フォールド':>8s}  {'レイズ':>6s}  {'n':>6s}")
    print(f"  {'-'*12}  {'-'*6}  {'-'*8}  {'-'*6}  {'-'*6}")
    for hname in FOCUS_HANDS:
        v = combined_hand.get(hname)
        if not v or v["total"] < 1:
            continue
        t = v["total"]
        c_pct = v["call"]  / t * 100
        f_pct = v["fold"]  / t * 100
        r_pct = v["raise"] / t * 100
        label = HAND_LABEL.get(hname, hname)
        print(f"  {label:12s}  {c_pct:5.1f}%  {f_pct:7.1f}%  {r_pct:5.1f}%  {t:6.0f}")

    # ── ドロー別集計 ──
    print(f"\n  [ドロー別 防御頻度 — 全ボード平均]")
    combined_draw: dict[str, dict] = defaultdict(
        lambda: {"total": 0.0, "call": 0.0, "fold": 0.0, "raise": 0.0}
    )
    for rec in boards.values():
        for dname, da in rec.get("draw_agg", {}).items():
            t = da.get("total", 0)
            combined_draw[dname]["total"] += t
            combined_draw[dname]["call"]  += da.get("call_pct",  0) * t / 100
            combined_draw[dname]["fold"]  += da.get("fold_pct",  0) * t / 100
            combined_draw[dname]["raise"] += da.get("raise_pct", 0) * t / 100

    print(f"  {'ドロー':12s}  {'コール':>6s}  {'フォールド':>8s}  {'レイズ':>6s}  {'n':>6s}")
    print(f"  {'-'*12}  {'-'*6}  {'-'*8}  {'-'*6}  {'-'*6}")
    for dname in FOCUS_DRAWS:
        v = combined_draw.get(dname)
        if not v or v["total"] < 1:
            continue
        t = v["total"]
        c_pct = v["call"]  / t * 100
        f_pct = v["fold"]  / t * 100
        r_pct = v["raise"] / t * 100
        label = DRAW_LABEL.get(dname, dname)
        print(f"  {label:12s}  {c_pct:5.1f}%  {f_pct:7.1f}%  {r_pct:5.1f}%  {t:6.0f}")

    # ── ボード別クロス集計 ──
    print(f"\n  [ボード別 hand×draw クロス集計]")
    for bid, rec in sorted(boards.items(), key=lambda x: x[1].get("board_type", 0)):
        code = rec.get("attack_code", "?")
        bpot = rec.get("attack_betsize_pot", 0) * 100
        print(f"\n  ── [{bid}] {rec.get('board','')}  {rec.get('label','')}  (型{rec.get('board_type','?')})  攻撃={code}({bpot:.0f}%pot)")
        dl_list = [DRAW_LABEL.get(d, d[:5]) for d in FOCUS_DRAWS]
        print(f"  {'hand':10s} " + " ".join(f"{d:>10s}" for d in dl_list))
        print(f"  {'-'*10} " + " ".join("-"*10 for _ in dl_list))

        for hname in FOCUS_HANDS:
            row = f"  {HAND_LABEL.get(hname, hname):10s} "
            any_data = False
            for dname in FOCUS_DRAWS:
                cell = fmt_defense(rec, hname, dname)
                row += f" {cell:>10s}"
                if "—" not in cell:
                    any_data = True
            if any_data:
                print(row)


def analyze_all() -> None:
    """全シナリオのハンド別コール% 比較表を出力する。"""
    print(f"\n{'═'*100}")
    print(f"  DEFENSE STUDY: 全シナリオ比較 — ハンド別コール%")
    print(f"{'═'*100}")

    scenarios = [k for k in DEFENSE_SCENARIOS if
                 (FINDINGS_DIR / f"defense_study_{k}.jsonl").exists()]
    if not scenarios:
        print("  データなし。先に --collect --all を実行してください。")
        return

    sc_data: dict[str, dict] = {}
    for sk in scenarios:
        inpf = FINDINGS_DIR / f"defense_study_{sk}.jsonl"
        combined: dict[str, dict] = defaultdict(
            lambda: {"total": 0.0, "call": 0.0, "fold": 0.0, "raise": 0.0}
        )
        for line in inpf.read_text().splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                for hname, ha in rec.get("hand_agg", {}).items():
                    t = ha.get("total", 0)
                    combined[hname]["total"] += t
                    combined[hname]["call"]  += ha.get("call_pct",  0) * t / 100
                    combined[hname]["fold"]  += ha.get("fold_pct",  0) * t / 100
                    combined[hname]["raise"] += ha.get("raise_pct", 0) * t / 100
            except json.JSONDecodeError:
                pass
        sc_data[sk] = combined

    def print_table(metric: str, get_val: Any) -> None:
        print(f"\n  [{metric}]")
        hdr = f"  {'ハンド':12s}" + "".join(f"  {sk:>18s}" for sk in scenarios)
        print(hdr)
        print(f"  {'-'*12}" + "".join(f"  {'-'*18}" for _ in scenarios))
        for hname in FOCUS_HANDS:
            label = HAND_LABEL.get(hname, hname)
            row = f"  {label:12s}"
            any_val = False
            for sk in scenarios:
                v = sc_data[sk].get(hname)
                if v and v["total"] > 0:
                    val = get_val(v)
                    row += f"  {val:6.1f}%({v['total']:4.0f})"
                    any_val = True
                else:
                    row += f"  {'—':>18s}"
            if any_val:
                print(row)

    print_table("コール% — ハンド別 × シナリオ別",
                lambda v: v["call"] / v["total"] * 100)
    print_table("フォールド% — ハンド別 × シナリオ別",
                lambda v: v["fold"] / v["total"] * 100)
    print_table("レイズ% — ハンド別 × シナリオ別",
                lambda v: v["raise"] / v["total"] * 100)


# ──────────────────── プローブ ────────────────────

def probe(board: str = "Kd9s8c") -> None:
    """各シナリオのStep1（アタッカーのベット）が有効かを確認する。"""
    if not check_auth():
        sys.exit(1)

    print(f"\n=== probe: board={board} ===\n")
    for sk, cfg in DEFENSE_SCENARIOS.items():
        first_step = cfg["first_step"]
        params: dict[str, Any] = {
            "gametype": GT, "depth": str(cfg["depth"]), "stacks": cfg.get("stacks", ""),
            "preflop_actions": cfg["pf"], "flop_actions": first_step,
            "turn_actions": "", "river_actions": "", "board": board,
        }
        r = requests.get(BASE_URL, params=params, headers=make_headers(), timeout=30)
        if r.status_code == 200:
            sols = r.json().get("action_solutions", [])
            bets = all_bet_codes(sols)
            check_freq = next(
                (s.get("total_frequency", 0) for s in sols if s["action"]["type"] == "CHECK"), 0
            )
            bet_summary = [(c, f"{f:.2f}") for c, f, _ in bets[:3]]
            print(f"  OK  {sk:25s}  first={first_step!r:5s}  check={check_freq:.2f}  bets={bet_summary}")
        else:
            print(f"  NG  {sk:25s}  HTTP {r.status_code}")
        time.sleep(0.5)


# ──────────────────── メイン ────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="defense_study.py: フロップ防御頻度分析")
    ap.add_argument("--probe",   action="store_true", help="全シナリオのStep1アクセスを確認")
    ap.add_argument("--collect", action="store_true", help="GTO Wizardからデータ収集")
    ap.add_argument("--analyze", action="store_true", help="シナリオ内分析")
    ap.add_argument("--all",     action="store_true", help="全シナリオを処理")
    ap.add_argument("--scenario", default=None,
                    choices=list(DEFENSE_SCENARIOS.keys()),
                    help="対象シナリオ")
    ap.add_argument("--force",   action="store_true", help="既存データを上書き")
    ap.add_argument("--board",   default="Kd9s8c", help="--probe 用テストボード")
    args = ap.parse_args()

    if args.probe:
        probe(args.board)

    elif args.collect:
        if not check_auth():
            sys.exit(1)
        targets = (list(DEFENSE_SCENARIOS.keys()) if args.all
                   else [args.scenario] if args.scenario
                   else None)
        if not targets:
            print("--scenario または --all を指定してください")
            ap.print_help()
            return
        for sk in targets:
            collect_scenario(sk, DEFENSE_SCENARIOS[sk], args.force)

    elif args.analyze:
        if args.all:
            analyze_all()
        elif args.scenario:
            analyze_scenario(args.scenario)
        else:
            print("--scenario または --all を指定してください")
            ap.print_help()

    else:
        ap.print_help()


if __name__ == "__main__":
    main()
