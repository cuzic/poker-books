#!/usr/bin/env python3
"""
mtt_flop_cbet.py — MTT フロップCBet（IP）＆OOP守備 分析

収集データ:
  1. IPのCBet判断: hand_category別CBet率（フロップ先手の場合）
  2. OOPのCBet守備: hand_category別コール/CR/フォールド率
  3. IPのCR対応: hand_category別フォールド/コール/3ベット率

使い方:
  TOKEN=eyJ... GWCLIENTID=xxx python3 mtt_flop_cbet.py
  TOKEN=eyJ... SCENARIO=SB_BB SBR=40 python3 mtt_flop_cbet.py
  TOKEN=eyJ... TYPE=型1 python3 mtt_flop_cbet.py
"""

import os, sys, json, time, requests
from pathlib import Path

TOKEN          = os.environ.get("TOKEN", "")
GWCLIENTID     = os.environ.get("GWCLIENTID", "")
GOOGLE_ANAL_ID = os.environ.get("GOOGLE_ANAL_ID", "")
GT             = "MTTGeneral"
SCENARIO       = os.environ.get("SCENARIO", "BTN_BB")
SBR            = os.environ.get("SBR", "25")
TYPE_FILTER    = os.environ.get("TYPE", "")

FINDINGS_DIR = Path(__file__).parent / "findings"
FINDINGS_DIR.mkdir(exist_ok=True)

BASE_URL = "https://api.gtowizard.com/v4/solutions/spot-solution/"

# ─────────────────── SBR設定 ───────────────────
# stacks: GTO Wizardが標準解を持つ場合は "" でよい。ない場合は9プレイヤー分指定
def _stacks(hero_bb: int, n: int = 9) -> str:
    others = round(hero_bb * 0.9)
    return "-".join([str(hero_bb)] + [str(others)] * (n - 1))

SBR_CONFIGS = {
    "40": {"depth": 40.125, "label": "Deep(SBR40)",
           "btn_bb_pf": "F-F-F-F-F-R2.5-F-C",
           "sb_bb_pf":  "F-F-F-F-F-F-R2.5-C",
           "stacks": ""},
    "25": {"depth": 25.125, "label": "Middle-Deep(SBR25)",
           "btn_bb_pf": "F-F-F-F-F-R2.1-F-C",
           "sb_bb_pf":  "F-F-F-F-F-F-R2.5-C",
           "stacks": ""},
    "20": {"depth": 20.125, "label": "Middle(SBR20)",
           "btn_bb_pf": "F-F-F-F-F-R2-F-C",
           "sb_bb_pf":  "F-F-F-F-F-F-R2.5-C",
           "stacks": ""},
    "15": {"depth": 15.125, "label": "Middle-Short(SBR15)",
           "btn_bb_pf": "F-F-F-F-F-R2-F-C",
           "sb_bb_pf":  "F-F-F-F-F-F-R2.5-C",
           "stacks": ""},
}

# ─────────────────── ボード7型 ───────────────────
BOARD_CONFIGS = [
    {"type": "型1_ハイドライ",  "flop": "Ks7d2c", "desc": "K高・レインボー"},
    {"type": "型2_ハイウェット", "flop": "Qh8d3s", "desc": "Q高・2トーン"},
    {"type": "型3_ロードライ",  "flop": "Jd7s5c", "desc": "J中・レインボー"},
    {"type": "型4_ローウェット", "flop": "Th9s8d", "desc": "低連携・2トーン"},
    {"type": "型5_モノトーン",  "flop": "Ah9h5h", "desc": "A高モノトーン"},
    {"type": "型6_ペア高",     "flop": "AsAcKd", "desc": "AAKペアボード"},
    {"type": "型7_ペア低",     "flop": "7s7d2c", "desc": "77低ペアボード"},
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
        "preflop_actions": pf or sbr_cfg["btn_bb_pf"],
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
    players = data.get("players_info", [])
    for p in players:
        if isinstance(p.get("player"), dict) and p["player"].get("position") == pos:
            return p
    # フォールバック: position が異なる場合（SBR20等でラベルが変わる可能性）
    if players:
        all_pos = [p.get("player", {}).get("position") for p in players if isinstance(p.get("player"), dict)]
        print(f"    [DEBUG] players_info positions: {all_pos}")
        # IP/OOP 属性で探す
        for p in players:
            role = p.get("player", {}).get("role") or p.get("role")
            is_ip = p.get("player", {}).get("is_ip")
            if (pos in ("BTN", "CO", "HJ") and (role == "IP" or is_ip)) or \
               (pos in ("BB", "SB") and (role == "OOP" or is_ip is False)):
                print(f"    [FALLBACK] {pos} → {p.get('player',{}).get('position')} (role/is_ip match)")
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
    """1ボードの CBet 3ステップ分析を実行し、結果 dict を返す。"""
    flop = cfg["flop"]

    result = {
        "type":           cfg["type"],
        "flop":           flop,
        "desc":           cfg.get("desc", ""),
        "ip_cbet":        None,
        "oop_defense":    None,
        "ip_cr_response": None,
    }

    # ─── ステップ1: IP CBet（OOPチェック後の IP 先手オプション）───
    print(f"\n  [Step1] IP CBet オプション取得: flop_actions='X'")
    data_ip = call_api(flop, flop_actions="X", pf=pf, depth=depth)
    time.sleep(8.0)

    if not data_ip:
        print("    取得失敗")
        return result

    ip_player = get_player(data_ip, ip)
    # top-level action_solutions を優先。なければ players_info 内を探す
    ip_sols = data_ip.get("action_solutions", [])
    if not ip_sols and ip_player:
        ip_sols = ip_player.get("action_solutions", [])
        if ip_sols:
            print(f"    [INFO] action_solutions を players_info から取得 (pos={ip})")
    # 全 frequency=0 の場合はデータ不正として扱う
    if ip_sols and all(float(s.get("total_frequency") or 0) == 0.0 for s in ip_sols):
        print(f"    [WARN] action_solutions の全 frequency=0: SBR設定・stacks 要確認")
        print(f"    [DEBUG] action codes: {[s['action']['code'] for s in ip_sols]}")
        ip_sols = []
    if not ip_player or not ip_sols:
        print(f"    IPプレイヤーデータなし (pos={ip})")
        if data_ip:
            keys = list(data_ip.keys())
            print(f"    [DEBUG] response keys: {keys}")
        return result

    ip_codes    = classify_actions(ip_sols)
    ip_rows     = calc_hc_action_rates(ip_sols, ip_player, ip_codes)
    bet_keys_ip = [k for k in ip_codes if k not in ("check", "fold")]
    total_bet   = weighted_rate(ip_rows, bet_keys_ip)
    cbet_code   = dominant_bet_code(ip_codes)

    print(f"    IP codes={ip_codes}  主要CBet={cbet_code}")
    if total_bet is not None:
        print(f"    IP CBet率（総合）: {total_bet*100:.0f}%")
    print_hc_table(ip_rows, "hand_category別 IP CBet率（シェア付き）")

    result["ip_cbet"] = {
        "total_bet_pct": round(total_bet * 100, 1) if total_bet is not None else None,
        "bet_code":      cbet_code,
        "by_category":   rows_to_store(ip_rows, ip_codes),
    }

    if not cbet_code:
        print("    CBetオプションなし（チェックのみ）—— OOP守備スキップ")
        return result

    # ─── ステップ2: OOP 守備（CBetに対するコール/CR/フォールド）───
    cbet_action = f"X-{cbet_code}"
    print(f"\n  [Step2] OOP 守備: flop_actions='{cbet_action}'")
    data_oop = call_api(flop, flop_actions=cbet_action, pf=pf, depth=depth)
    time.sleep(8.0)

    if not data_oop:
        print("    取得失敗")
        return result

    oop_player = get_player(data_oop, oop)
    oop_sols   = data_oop.get("action_solutions", [])
    if not oop_player or not oop_sols:
        print(f"    OOPプレイヤーデータなし (pos={oop})")
        return result

    oop_codes  = classify_actions(oop_sols)
    oop_rows   = calc_hc_action_rates(oop_sols, oop_player, oop_codes)

    call_rate  = weighted_rate(oop_rows, ["call"]  if "call"  in oop_codes else [])
    fold_rate  = weighted_rate(oop_rows, ["fold"]  if "fold"  in oop_codes else [])
    cr_keys    = [k for k in oop_codes if k not in ("check", "fold", "call")]
    cr_rate    = weighted_rate(oop_rows, cr_keys)
    cr_code    = dominant_bet_code(oop_codes)

    print(f"    OOP codes={oop_codes}")
    if call_rate is not None:
        cr_pct   = f"{cr_rate*100:.0f}%"   if cr_rate   is not None else "—"
        fold_pct = f"{fold_rate*100:.0f}%" if fold_rate is not None else "—"
        print(f"    コール率={call_rate*100:.0f}%  CR率={cr_pct} (keys={cr_keys})  フォールド率={fold_pct}")
    print_hc_table(oop_rows, "hand_category別 OOP守備率（シェア付き）")

    result["oop_defense"] = {
        "call_pct":    round(call_rate * 100, 1) if call_rate is not None else None,
        "cr_pct":      round(cr_rate   * 100, 1) if cr_rate   is not None else None,
        "fold_pct":    round(fold_rate * 100, 1) if fold_rate is not None else None,
        "by_category": rows_to_store(oop_rows, oop_codes),
    }

    if not cr_code or not cr_keys:
        print("    CR選択肢なし —— IP CR対応スキップ")
        return result

    # ─── ステップ3: IP の CR 対応（フォールド/コール/3ベット）───
    cr_action = f"{cbet_action}-{cr_code}"
    print(f"\n  [Step3] IP CR対応: flop_actions='{cr_action}'")
    data_cr = call_api(flop, flop_actions=cr_action, pf=pf, depth=depth)
    time.sleep(8.0)

    if not data_cr:
        print("    取得失敗")
        return result

    ip_cr_player = get_player(data_cr, ip)
    ip_cr_sols   = data_cr.get("action_solutions", [])
    if not ip_cr_player or not ip_cr_sols:
        print(f"    IP(CR対応)プレイヤーデータなし (pos={ip})")
        return result

    ip_cr_codes  = classify_actions(ip_cr_sols)
    ip_cr_rows   = calc_hc_action_rates(ip_cr_sols, ip_cr_player, ip_cr_codes)
    reraise_keys = [k for k in ip_cr_codes if k not in ("check", "fold", "call")]
    ip_fold_rate  = weighted_rate(ip_cr_rows, ["fold"]  if "fold"  in ip_cr_codes else [])
    ip_call_rate  = weighted_rate(ip_cr_rows, ["call"]  if "call"  in ip_cr_codes else [])
    ip_3b_rate    = weighted_rate(ip_cr_rows, reraise_keys)

    print(f"    IP CR対応 codes={ip_cr_codes}")
    fold_s = f"{ip_fold_rate*100:.0f}%" if ip_fold_rate is not None else "—"
    call_s = f"{ip_call_rate*100:.0f}%" if ip_call_rate is not None else "—"
    rb_s   = f"{ip_3b_rate*100:.0f}%"   if ip_3b_rate   is not None else "—"
    print(f"    フォールド={fold_s}  コール={call_s}  3ベット={rb_s}")
    print_hc_table(ip_cr_rows, "hand_category別 IP CR対応率（シェア付き）")

    result["ip_cr_response"] = {
        "fold_pct":     round(ip_fold_rate * 100, 1) if ip_fold_rate is not None else None,
        "call_pct":     round(ip_call_rate * 100, 1) if ip_call_rate is not None else None,
        "reraised_pct": round(ip_3b_rate   * 100, 1) if ip_3b_rate   is not None else None,
        "by_category":  rows_to_store(ip_cr_rows, ip_cr_codes),
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

    if SCENARIO == "BTN_BB":
        ip, oop, pf = "BTN", "BB", sbr_cfg["btn_bb_pf"]
        scenario_label = f"SRP BTN vs BB ({label})"
    elif SCENARIO == "SB_BB":
        ip, oop, pf = "BB", "SB", sbr_cfg["sb_bb_pf"]
        scenario_label = f"SRP SB vs BB ({label})"
    else:
        print(f"❌ 未知シナリオ: {SCENARIO}. 選択肢: BTN_BB, SB_BB"); sys.exit(1)

    print(f"シナリオ: {scenario_label}  (IP={ip}, OOP={oop}, depth={depth}BB)")
    print(f"分析: フロップ CBet（IP）＆ OOP守備 ＆ IP のCR対応")
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
    print(f"★ 全体サマリー: CBet率 / OOP守備（コール/CR/フォールド）")
    print(f"  {'型':20s} | {'IP CBet%':>9} | {'OOP Call%':>10} | {'OOP CR%':>8} | {'OOP Fold%':>10} | {'IP vs CR Fold%':>14}")
    print(f"  {'-'*80}")
    for r in all_results:
        ic  = r["ip_cbet"]
        od  = r["oop_defense"]
        icr = r["ip_cr_response"]
        cbet_s   = f"{ic['total_bet_pct']:.0f}%"  if ic  and ic["total_bet_pct"]   is not None else "—"
        call_s   = f"{od['call_pct']:.0f}%"       if od  and od["call_pct"]        is not None else "—"
        cr_s     = f"{od['cr_pct']:.0f}%"         if od  and od["cr_pct"]          is not None else "—"
        fold_s   = f"{od['fold_pct']:.0f}%"       if od  and od["fold_pct"]        is not None else "—"
        ip_fold  = f"{icr['fold_pct']:.0f}%"      if icr and icr["fold_pct"]       is not None else "—"
        print(
            f"  {r['type']:20s} | {cbet_s:>9} | {call_s:>10} | {cr_s:>8} | "
            f"{fold_s:>10} | {ip_fold:>14}"
        )

    # JSON 保存
    out = FINDINGS_DIR / f"mtt_flop_cbet_SBR{SBR}_{SCENARIO}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(
            {"scenario": scenario_label, "sbr": SBR, "results": all_results},
            f, ensure_ascii=False, indent=2
        )
    print(f"\n✅ 完了 → {out}")


if __name__ == "__main__":
    main()
