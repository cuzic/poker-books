#!/usr/bin/env python3
"""
mtt_sb_bb.py — MTT SB vs BB ポストフロップ分析

SB がレイズ、BB がコール。BB は IP（ポストフロップで後手に行動）。
SB は OOP（ポストフロップで先手に行動）。

収集データ:
  1. SB CBet率（OOPアグレッサーとして先手ベット）
  2. BB コール率（SB CBetに対して）
  3. BB ディレイドCBet率（X-X 後のターンでBBがベット）
  4. SB プローブ率（X-X 後のターンでSBが先手）

使い方:
  TOKEN=eyJ... GWCLIENTID=xxx python3 mtt_sb_bb.py
  TOKEN=eyJ... SBR=40 python3 mtt_sb_bb.py
  TOKEN=eyJ... TYPE=型1 python3 mtt_sb_bb.py
"""

import os, sys, json, time, requests
from pathlib import Path

TOKEN          = os.environ.get("TOKEN", "")
GWCLIENTID     = os.environ.get("GWCLIENTID", "")
GOOGLE_ANAL_ID = os.environ.get("GOOGLE_ANAL_ID", "")
GT             = "MTTGeneral"
SBR            = os.environ.get("SBR", "25")
TYPE_FILTER    = os.environ.get("TYPE", "")

FINDINGS_DIR = Path(__file__).parent / "findings"
FINDINGS_DIR.mkdir(exist_ok=True)

BASE_URL = "https://api.gtowizard.com/v4/solutions/spot-solution/"

# ─────────────────── SBR設定 ───────────────────
def _stacks(hero_bb: int, n: int = 9) -> str:
    others = round(hero_bb * 0.9)
    return "-".join([str(hero_bb)] + [str(others)] * (n - 1))

SBR_CONFIGS = {
    "40": {"depth": 40.125, "label": "Deep(SBR40)",
           "btn_bb_pf": "F-F-F-F-F-R2.5-F-C",
           "sb_bb_pf":  "F-F-F-F-F-F-R3.5-C",
           "stacks": ""},
    "25": {"depth": 25.125, "label": "Middle-Deep(SBR25)",
           "btn_bb_pf": "F-F-F-F-F-R2.1-F-C",
           "sb_bb_pf":  "F-F-F-F-F-F-R3-C",
           "stacks": ""},
    "20": {"depth": 20.125, "label": "Middle(SBR20)",
           "btn_bb_pf": "F-F-F-F-F-R2-F-C",
           "sb_bb_pf":  "F-F-F-F-F-F-R3-C",
           "stacks": ""},
    "15": {"depth": 15.125, "label": "Middle-Short(SBR15)",
           "btn_bb_pf": "F-F-F-F-F-R2-F-C",
           "sb_bb_pf":  "F-F-F-F-F-F-R3-C",
           "stacks": ""},
}

# ─────────────────── ボード7型 ───────────────────
# turn_card: X-X 後のターンクエリに使用する代表ターンカード
BOARD_CONFIGS = [
    {"type": "型1_ハイドライ",  "flop": "Ks7d2c", "desc": "K高・レインボー",   "turn_card": "4h"},
    {"type": "型2_ハイウェット", "flop": "Qh8d3s", "desc": "Q高・2トーン",     "turn_card": "4h"},
    {"type": "型3_ロードライ",  "flop": "Jd7s5c", "desc": "J中・レインボー",   "turn_card": "4h"},
    {"type": "型4_ローウェット", "flop": "Th9s8d", "desc": "低連携・2トーン",   "turn_card": "2c"},
    {"type": "型5_モノトーン",  "flop": "Ah9h5h", "desc": "A高モノトーン",     "turn_card": "2c"},
    {"type": "型6_ペア高",     "flop": "AsAcKd", "desc": "AAKペアボード",     "turn_card": "2h"},
    {"type": "型7_ペア低",     "flop": "7s7d2c", "desc": "77低ペアボード",    "turn_card": "3h"},
]

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


# ─────────────────── API ユーティリティ ───────────────────

def make_headers():
    h = {
        "accept":           "application/json, text/plain, */*",
        "accept-language":  "ja,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
        "authorization":    f"Bearer {TOKEN}",
        "cache-control":    "no-cache",
        "origin":           "https://app.gtowizard.com",
        "pragma":           "no-cache",
        "priority":         "u=1, i",
        "referer":          "https://app.gtowizard.com/",
        "sec-ch-ua":        '"Chromium";v="148", "Microsoft Edge";v="148", "Not/A)Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest":   "empty",
        "sec-fetch-mode":   "cors",
        "sec-fetch-site":   "same-site",
        "user-agent":       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
    }
    if GWCLIENTID:
        h["gwclientid"] = GWCLIENTID
    if GOOGLE_ANAL_ID:
        h["google-anal-id"] = GOOGLE_ANAL_ID
    return h


def call_api(board, flop_actions="", turn_actions="", river_actions="", pf=None, depth=100):
    sbr_cfg = SBR_CONFIGS.get(SBR, SBR_CONFIGS["25"])
    params = {
        "gametype":        GT,
        "depth":           str(depth),
        "stacks":          sbr_cfg.get("stacks", ""),
        "preflop_actions": pf or sbr_cfg["sb_bb_pf"],
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
            print(f"  [HTTP 429] board={board} flop={flop_actions!r} → {wait}s 待機中...")
            time.sleep(wait)
            continue
        print(f"  [HTTP {r.status_code}] board={board} flop={flop_actions!r}")
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
    for key in ["bet33", "bet50", "bet75", "bet100", "betover", "bet20"]:
        if key in codes:
            return codes[key]
    return None


def calc_hc_action_rates(sols, player, codes):
    """hand_category 別行動率 + レンジシェア(%)。行動率は 0.0–1.0。"""
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
    """コンボ加重平均行動率 (0-1)。対象キーなし or データなしなら None。"""
    if not keys or not rows:
        return None
    total_combos = sum(r["total"] for r in rows)
    if total_combos == 0:
        return None
    return sum(
        r["total"] * sum(r.get(k, 0) or 0 for k in keys) for r in rows
    ) / total_combos


def print_hc_table(rows, header=""):
    """hand_category 別行動率テーブルを表示する。"""
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
    """rows を JSON 保存可能な形式（行動率 %）に変換する。"""
    if not rows:
        return []
    keep_keys = {"hc", "total", "share"} | set(codes_dict.keys())
    return [
        {
            k: (
                round(v * 100, 1)
                if isinstance(v, float) and k not in ("total", "share")
                else v
            )
            for k, v in row.items()
            if k in keep_keys
        }
        for row in rows
    ]


# ─────────────────── メイン分析 ───────────────────

def analyze_board(cfg, ip, oop, pf, depth):
    """1ボードの SB vs BB 4ステップ分析を実行し、結果 dict を返す。"""
    flop      = cfg["flop"]
    turn_card = cfg["turn_card"]
    board4    = flop + turn_card

    result = {
        "type":             cfg["type"],
        "flop":             flop,
        "desc":             cfg.get("desc", ""),
        "turn_card":        turn_card,
        "sb_cbet":          None,
        "bb_response":      None,
        "bb_delayed_cbet":  None,
        "sb_probe":         None,
    }

    # ─── ステップ1: SB 先手行動（OOP の SB がフロップ先手）───
    print(f"\n  [Step1] SB 先手行動取得: flop_actions=''")
    data_sb = call_api(flop, flop_actions="", pf=pf, depth=depth)
    time.sleep(8.0)

    if not data_sb:
        print("    取得失敗")
        return result

    sb_player = get_player(data_sb, oop)  # SB は OOP
    sb_sols   = data_sb.get("action_solutions", [])
    if not sb_player or not sb_sols:
        print(f"    SBプレイヤーデータなし (pos={oop})")
        return result

    sb_codes    = classify_actions(sb_sols)
    sb_rows     = calc_hc_action_rates(sb_sols, sb_player, sb_codes)
    bet_keys_sb = [k for k in sb_codes if k not in ("check", "fold")]
    sb_bet_rate = weighted_rate(sb_rows, bet_keys_sb)
    sb_cbet_code = dominant_bet_code(sb_codes)

    print(f"    SB codes={sb_codes}  主要CBet={sb_cbet_code}")
    if sb_bet_rate is not None:
        print(f"    SB CBet率（総合）: {sb_bet_rate*100:.0f}%")
    print_hc_table(sb_rows, "hand_category別 SB 先手行動率（シェア付き）")

    result["sb_cbet"] = {
        "total_bet_pct": round(sb_bet_rate * 100, 1) if sb_bet_rate is not None else None,
        "bet_code":      sb_cbet_code,
        "by_category":   rows_to_store(sb_rows, sb_codes),
    }

    if not sb_cbet_code:
        print("    SB CBetオプションなし（チェックのみ）—— BB応答スキップ")
    else:
        # ─── ステップ2: BB 応答（SB CBetに対するコール/レイズ/フォールド）───
        sb_cbet_action = sb_cbet_code
        print(f"\n  [Step2] BB 応答: flop_actions='{sb_cbet_action}'")
        data_bb = call_api(flop, flop_actions=sb_cbet_action, pf=pf, depth=depth)
        time.sleep(8.0)

        if not data_bb:
            print("    取得失敗")
        else:
            bb_player = get_player(data_bb, ip)  # BB は IP
            bb_sols   = data_bb.get("action_solutions", [])
            if not bb_player or not bb_sols:
                print(f"    BBプレイヤーデータなし (pos={ip})")
            else:
                bb_codes   = classify_actions(bb_sols)
                bb_rows    = calc_hc_action_rates(bb_sols, bb_player, bb_codes)

                bb_call_rate  = weighted_rate(bb_rows, ["call"]  if "call"  in bb_codes else [])
                bb_fold_rate  = weighted_rate(bb_rows, ["fold"]  if "fold"  in bb_codes else [])
                bb_raise_keys = [k for k in bb_codes if k not in ("check", "fold", "call")]
                bb_raise_rate = weighted_rate(bb_rows, bb_raise_keys)

                print(f"    BB codes={bb_codes}")
                call_s  = f"{bb_call_rate*100:.0f}%"  if bb_call_rate  is not None else "—"
                fold_s  = f"{bb_fold_rate*100:.0f}%"  if bb_fold_rate  is not None else "—"
                raise_s = f"{bb_raise_rate*100:.0f}%" if bb_raise_rate is not None else "—"
                print(f"    コール={call_s}  フォールド={fold_s}  レイズ={raise_s}")
                print_hc_table(bb_rows, "hand_category別 BB応答率（シェア付き）")

                result["bb_response"] = {
                    "call_pct":    round(bb_call_rate  * 100, 1) if bb_call_rate  is not None else None,
                    "fold_pct":    round(bb_fold_rate  * 100, 1) if bb_fold_rate  is not None else None,
                    "raise_pct":   round(bb_raise_rate * 100, 1) if bb_raise_rate is not None else None,
                    "by_category": rows_to_store(bb_rows, bb_codes),
                }

    # ─── ステップ3: BB ディレイドCBet（X-X → ターン で BB がベット）───
    # SB X → BB X → ターンカード → BB が先手で行動
    # フロップ: "X-X"（両者チェック）。ターン board4 で BB（IP）が行動
    print(f"\n  [Step3] BB ディレイドCBet: board4={board4} flop_actions='X-X' turn_actions=''")
    data_bb_turn = call_api(board4, flop_actions="X-X", turn_actions="", pf=pf, depth=depth)
    time.sleep(8.0)

    if not data_bb_turn:
        print("    取得失敗")
    else:
        bb_turn_player = get_player(data_bb_turn, ip)  # BB は IP
        bb_turn_sols   = data_bb_turn.get("action_solutions", [])
        if not bb_turn_player or not bb_turn_sols:
            print(f"    BBターンプレイヤーデータなし (pos={ip})")
        else:
            bt_codes    = classify_actions(bb_turn_sols)
            bt_rows     = calc_hc_action_rates(bb_turn_sols, bb_turn_player, bt_codes)
            bet_keys_bt = [k for k in bt_codes if k not in ("check", "fold")]
            bb_dcbet    = weighted_rate(bt_rows, bet_keys_bt)
            bb_dcbet_code = dominant_bet_code(bt_codes)

            print(f"    BB ターン codes={bt_codes}  主要Bet={bb_dcbet_code}")
            if bb_dcbet is not None:
                print(f"    BB ディレイドCBet率: {bb_dcbet*100:.0f}%")
            print_hc_table(bt_rows, "hand_category別 BB ディレイドCBet率（シェア付き）")

            result["bb_delayed_cbet"] = {
                "total_bet_pct": round(bb_dcbet * 100, 1) if bb_dcbet is not None else None,
                "bet_code":      bb_dcbet_code,
                "by_category":   rows_to_store(bt_rows, bt_codes),
            }

    # ─── ステップ4: SB プローブ（X-X → ターン で SB が先手）───
    # SB X → BB X → ターンカード → SB（OOP）が先手で行動
    print(f"\n  [Step4] SB プローブ: board4={board4} flop_actions='X-X' turn_actions=''")
    # For SB probe, SB is OOP and acts first on turn after X-X on flop
    # We need to get the SB's action from the same spot
    # When flop_actions="X-X" and turn_actions="", the OOP player (SB) acts first on the turn
    data_sb_probe = call_api(board4, flop_actions="X-X", turn_actions="", pf=pf, depth=depth)
    time.sleep(8.0)

    if not data_sb_probe:
        print("    取得失敗")
    else:
        sb_probe_player = get_player(data_sb_probe, oop)  # SB は OOP
        sb_probe_sols   = data_sb_probe.get("action_solutions", [])
        if not sb_probe_player or not sb_probe_sols:
            print(f"    SBプローブプレイヤーデータなし (pos={oop})")
        else:
            sp_codes    = classify_actions(sb_probe_sols)
            sp_rows     = calc_hc_action_rates(sb_probe_sols, sb_probe_player, sp_codes)
            bet_keys_sp = [k for k in sp_codes if k not in ("check", "fold")]
            sb_probe    = weighted_rate(sp_rows, bet_keys_sp)
            sb_probe_code = dominant_bet_code(sp_codes)

            print(f"    SB プローブ codes={sp_codes}  主要Bet={sb_probe_code}")
            if sb_probe is not None:
                print(f"    SB プローブ率: {sb_probe*100:.0f}%")
            print_hc_table(sp_rows, "hand_category別 SB プローブ率（シェア付き）")

            result["sb_probe"] = {
                "total_bet_pct": round(sb_probe * 100, 1) if sb_probe is not None else None,
                "bet_code":      sb_probe_code,
                "by_category":   rows_to_store(sp_rows, sp_codes),
            }

    return result


def check_token():
    """JWTをAPIコールなしでローカル検証する。"""
    import base64 as _b64
    try:
        payload = TOKEN.split('.')[1]
        payload += '=' * (-len(payload) % 4)
        data = json.loads(_b64.urlsafe_b64decode(payload))
        exp = data.get('exp', 0)
        remaining = exp - time.time()
        if remaining <= 60:
            print(f"❌ TOKEN期限切れ（残り{remaining:.0f}秒）"); sys.exit(1)
        print(f"✅ 認証OK（残り{remaining/60:.1f}分）")
    except Exception as e:
        print(f"❌ TOKEN パース失敗: {e}"); sys.exit(1)


def main():
    if not TOKEN:
        print("❌ TOKEN 未設定"); sys.exit(1)

    sbr_cfg = SBR_CONFIGS.get(SBR)
    if not sbr_cfg:
        print(f"❌ 未知SBR: {SBR}. 選択肢: {list(SBR_CONFIGS)}"); sys.exit(1)

    depth = sbr_cfg["depth"]
    label = sbr_cfg["label"]
    pf    = sbr_cfg["sb_bb_pf"]

    # SB vs BB: SB はプリフロップレイザー（OOP）、BB は IP
    ip, oop = "BB", "SB"
    scenario_label = f"SRP SB vs BB ({label})"

    print(f"シナリオ: {scenario_label}  (IP={ip}=BB, OOP={oop}=SB, depth={depth}BB)")
    print(f"分析: SB CBet率 / BB コール率 / BB ディレイドCBet率 / SB プローブ率")
    print(f"gametype: {GT}\n")

    check_token()
    time.sleep(5.0)

    configs = [c for c in BOARD_CONFIGS if not TYPE_FILTER or c["type"] == TYPE_FILTER]
    all_results = []

    for cfg in configs:
        print(f"\n{'='*70}")
        print(f"【{cfg['type']}】 {cfg['flop']}  ({cfg['desc']})")
        result = analyze_board(cfg, ip, oop, pf, depth)
        all_results.append(result)
        time.sleep(3.0)

    # ─── 全体サマリー ───
    print(f"\n\n{'='*70}")
    print(f"★ 全体サマリー: SB CBet% / BB Call% / BB DelayedCBet% / SB Probe%")
    print(f"  {'型':20s} | {'SB CBet%':>9} | {'BB Call%':>9} | {'BB DelayedCBet%':>16} | {'SB Probe%':>10}")
    print(f"  {'-'*75}")
    for r in all_results:
        sc  = r["sb_cbet"]
        br  = r["bb_response"]
        bdc = r["bb_delayed_cbet"]
        sp  = r["sb_probe"]
        sb_cbet_s = f"{sc['total_bet_pct']:.0f}%"  if sc  and sc["total_bet_pct"]  is not None else "—"
        bb_call_s = f"{br['call_pct']:.0f}%"       if br  and br["call_pct"]       is not None else "—"
        bb_dc_s   = f"{bdc['total_bet_pct']:.0f}%" if bdc and bdc["total_bet_pct"] is not None else "—"
        sb_pb_s   = f"{sp['total_bet_pct']:.0f}%"  if sp  and sp["total_bet_pct"]  is not None else "—"
        print(
            f"  {r['type']:20s} | {sb_cbet_s:>9} | {bb_call_s:>9} | {bb_dc_s:>16} | {sb_pb_s:>10}"
        )

    # JSON 保存
    out = FINDINGS_DIR / f"mtt_sb_bb_SBR{SBR}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(
            {"scenario": scenario_label, "sbr": SBR, "results": all_results},
            f, ensure_ascii=False, indent=2
        )
    print(f"\n✅ 完了 → {out}")


if __name__ == "__main__":
    main()
