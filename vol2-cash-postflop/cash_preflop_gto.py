#!/usr/bin/env python3
"""
cash_preflop_gto.py — プリフロップ GTO データ収集（Vol.1 検証用）

spot-solution エンドポイントに board='' で問い合わせ、
プリフロップ全アクション層のハンド別頻度を取得する。

フェーズ（PHASE 環境変数で指定）:
  probe          :  1コール — レスポンス形式確認（要最初に実行）
  probe_multiway :  6コール — マルチウェイ アクションコード調査
  rfi            :  5コール — UTG/HJ/CO/BTN/SB のオープンレイズ
  vs_open        : 12コール — BB(5) + SB(4) + IP cold-call(3) の single raise 守備
  vs_3bet        : 12コール — オープン側の 3-bet 対応（fold/call/4bet）
  vs_4bet        :  5コール — 3-bet 側の 4-bet 対応（fold/call/5bet）
  vs_5bet        :  3コール — 4-bet 側の 5-bet 対応（fold/call/AI）
  multiway       : 21コール — raise+call(1人/2人/3人) 後の fold/call/3bet
  all            : 64コール — 上記すべて（デフォルト）

使い方:
  TOKEN=eyJ... GWCLIENTID=xxx GOOGLE_ANAL_ID=yyy python3 cash_preflop_gto.py
  TOKEN=eyJ... PHASE=probe   python3 cash_preflop_gto.py  # 最初に形式確認
  TOKEN=eyJ... PHASE=rfi     python3 cash_preflop_gto.py  # RFIのみ
  TOKEN=eyJ... PHASE=all     python3 cash_preflop_gto.py  # 全43コール
"""

import os, sys, json, time, requests
from pathlib import Path

TOKEN          = os.environ.get("TOKEN", "")
GWCLIENTID     = os.environ.get("GWCLIENTID", "")
GOOGLE_ANAL_ID = os.environ.get("GOOGLE_ANAL_ID", "")
GT             = os.environ.get("GT", "Cash6mGeneral_6mNL25R25")
PHASE          = os.environ.get("PHASE", "all")

FINDINGS_DIR = Path(__file__).parent / "findings"
FINDINGS_DIR.mkdir(exist_ok=True)

BASE_URL = "https://api.gtowizard.com/v4/solutions/spot-solution/"

# ─── プリフロップスポット定義 ───────────────────────────────────────
# board="" で呼ぶとプリフロップスポットが返る（postflopと同じエンドポイント）
# 6-max 順: UTG(1) HJ(2) CO(3) BTN(4) SB(5) BB(6)
# NOTE: probe フェーズで actor の正式名称（LJ or UTG）を確認すること

RFI_SPOTS = [
    # 各ポジション初手オープン（5スポット）
    {"label": "UTG RFI",  "pf": "",         "actor": "UTG"},
    {"label": "HJ RFI",   "pf": "F",        "actor": "HJ"},
    {"label": "CO RFI",   "pf": "F-F",      "actor": "CO"},
    {"label": "BTN RFI",  "pf": "F-F-F",    "actor": "BTN"},
    {"label": "SB RFI",   "pf": "F-F-F-F",  "actor": "SB"},
]

VS_OPEN_SPOTS = [
    # BB defense: 全5ポジションのオープンに対して（fold/call/3bet）
    {"label": "BB vs UTG",  "pf": "R2.5-F-F-F-F",  "actor": "BB"},
    {"label": "BB vs HJ",   "pf": "F-R2.5-F-F-F",  "actor": "BB"},
    {"label": "BB vs CO",   "pf": "F-F-R2.5-F-F",  "actor": "BB"},
    {"label": "BB vs BTN",  "pf": "F-F-F-R2.5-F",  "actor": "BB"},
    {"label": "BB vs SB",   "pf": "F-F-F-F-R3.5",  "actor": "BB"},  # SBは3.5BB
    # SB defense: 全4ポジションのオープンに対して（fold/call/3bet）
    {"label": "SB vs UTG",  "pf": "R2.5-F-F-F",    "actor": "SB"},
    {"label": "SB vs HJ",   "pf": "F-R2.5-F-F",    "actor": "SB"},
    {"label": "SB vs CO",   "pf": "F-F-R2.5-F",    "actor": "SB"},
    {"label": "SB vs BTN",  "pf": "F-F-F-R2.5",    "actor": "SB"},
    # IP cold-call（fold/call/3bet）
    {"label": "BTN vs UTG", "pf": "R2.5-F-F",      "actor": "BTN"},
    {"label": "CO vs UTG",  "pf": "R2.5-F",        "actor": "CO"},
    {"label": "BTN vs HJ",  "pf": "F-R2.5-F",      "actor": "BTN"},
    {"label": "BTN vs CO",  "pf": "F-F-R2.5",      "actor": "BTN"},  # Score_C 検証の核心
    {"label": "CO vs HJ",   "pf": "F-R2.5",        "actor": "CO"},
]

VS_3BET_SPOTS = [
    # オープン側が 3-bet を受けたときの対応（fold/call/4bet）
    # UTG オープン vs 各ポジションの 3-bet
    {"label": "UTG vs HJ 3bet",  "pf": "R2.5-R8-F-F-F-F",  "actor": "UTG"},
    {"label": "UTG vs CO 3bet",  "pf": "R2.5-F-R8-F-F-F",  "actor": "UTG"},
    {"label": "UTG vs BTN 3bet", "pf": "R2.5-F-F-R8-F-F",  "actor": "UTG"},
    {"label": "UTG vs SB 3bet",  "pf": "R2.5-F-F-F-R11-F",  "actor": "UTG"},
    {"label": "UTG vs BB 3bet",  "pf": "R2.5-F-F-F-F-RAI",  "actor": "UTG"},
    # HJ オープン vs 3-bet
    {"label": "HJ vs BTN 3bet",  "pf": "F-R2.5-F-R8-F-F",   "actor": "HJ"},
    {"label": "HJ vs BB 3bet",   "pf": "F-R2.5-F-F-F-RAI",  "actor": "HJ"},
    # CO オープン vs 3-bet
    {"label": "CO vs BTN 3bet",  "pf": "F-F-R2.5-R8-F-F",   "actor": "CO"},
    {"label": "CO vs BB 3bet",   "pf": "F-F-R2.5-F-F-RAI",  "actor": "CO"},
    # BTN オープン vs 3-bet
    {"label": "BTN vs SB 3bet",  "pf": "F-F-F-R2.5-R11-F",  "actor": "BTN"},
    {"label": "BTN vs BB 3bet",  "pf": "F-F-F-R2.5-F-RAI",  "actor": "BTN"},
    # SB オープン vs BB 3-bet
    {"label": "SB vs BB 3bet",   "pf": "F-F-F-F-R3.5-RAI",  "actor": "SB"},
]

VS_4BET_SPOTS = [
    # 3-bet 側が 4-bet を受けたときの対応（fold/call/5bet）
    # NOTE: BB の 3-bet は RAI（all-in）なので 4-bet は発生しない。IP 3-bet のみ。
    # UTG が HJ の 3-bet(R8) に対して 4-bet(R21.5)→HJ が対応
    {"label": "HJ vs UTG 4bet",  "pf": "R2.5-R8-F-F-F-F-R21.5",   "actor": "HJ"},
    # UTG が CO の 3-bet(R8) に対して 4-bet(R21.5)→CO が対応
    {"label": "CO vs UTG 4bet",  "pf": "R2.5-F-R8-F-F-F-R21.5",   "actor": "CO"},
    # UTG が BTN の 3-bet(R8) に対して 4-bet(R21.5)→BTN が対応
    {"label": "BTN vs UTG 4bet", "pf": "R2.5-F-F-R8-F-F-R21.5",   "actor": "BTN"},
    # UTG が SB の 3-bet(R11) に対して 4-bet(R23)→SB が対応
    {"label": "SB vs UTG 4bet",  "pf": "R2.5-F-F-F-R11-F-R23",    "actor": "SB"},
    # HJ が BTN の 3-bet(R8) に対して 4-bet(R21.5)→BTN が対応
    {"label": "BTN vs HJ 4bet",  "pf": "F-R2.5-F-R8-F-F-R21.5",   "actor": "BTN"},
]

VS_5BET_SPOTS = [
    # 4-bet 側が 5-bet（事実上 all-in）を受けたときの対応
    # HJ が UTG 4-bet(R21.5) に対して 5-bet(RAI)→UTG が対応
    {"label": "UTG vs HJ 5bet",  "pf": "R2.5-R8-F-F-F-F-R21.5-RAI",  "actor": "UTG"},
    # BTN が UTG 4-bet(R21.5) に対して 5-bet(RAI)→UTG が対応
    {"label": "UTG vs BTN 5bet", "pf": "R2.5-F-F-R8-F-F-R21.5-RAI",  "actor": "UTG"},
    # SB が UTG 4-bet(R23) に対して 5-bet(RAI)→UTG が対応
    {"label": "UTG vs SB 5bet",  "pf": "R2.5-F-F-F-R11-F-R23-RAI",   "actor": "UTG"},
]

MULTIWAY_PRE_SPOTS = [
    # ── ツリー収録確認済みスポット（Cash6mGeneral simplified tree） ───
    #
    # パターン1: UTG raises + HJ cold-calls → CO/BTN/SB がスクイーズ or fold
    # (HJ cold-call 後のみ CO/BTN/SB が判断できる; BB は 204)
    {"label": "CO vs UTG+HJ",   "pf": "R2.5-C",       "actor": "CO"},
    {"label": "BTN vs UTG+HJ",  "pf": "R2.5-C-F",     "actor": "BTN"},
    {"label": "SB vs UTG+HJ",   "pf": "R2.5-C-F-F",   "actor": "SB"},
    #
    # パターン2: opener raises + IP cold-call + SB folds → BB が defend
    # (CO/BTN cold-call の後は BB のみ判断; BTN/SB は 204)
    {"label": "BB vs UTG+CO",   "pf": "R2.5-F-C-F-F",  "actor": "BB"},
    {"label": "BB vs UTG+BTN",  "pf": "R2.5-F-F-C-F",  "actor": "BB"},
    {"label": "BB vs CO+BTN",   "pf": "F-F-R2.5-C-F",  "actor": "BB"},
    #
    # ── 204 で未収録と確認済み（参考） ───────────────────────────────
    # BB vs UTG+HJ  (R2.5-C-F-F-F):     204
    # BTN vs UTG+CO (R2.5-F-C):          204
    # All HJ-as-opener + cold-call:      204
    # All 2+ callers sequences:          204
    # SB as cold-caller (BTN+SB etc.):   204
]

# ─── マルチウェイ調査用プローブ ────────────────────────────────────
# 各仮説を検証するための最小スポット群（PHASE=probe_multiway で実行）
# 仮説A: 'C' が正しいがツリーに存在しない（簡略化ツリー説）
# 仮説B: HJ vs UTG コールド・コールがそもそも利用可能
# 仮説C: コールアクションコードが 'C2.5' など明示サイズ
PROBE_MULTIWAY_SPOTS = [
    # HJ vs UTG: 最初のコールド・コール候補（vs_open に未収録）
    {"label": "HJ vs UTG (probe)",  "pf": "R2.5",          "actor": "HJ"},
    # UTG+CO cold-call → BTN acts: 'C' を使う標準形
    {"label": "BTN vs UTG+CO [C]",  "pf": "R2.5-F-C",      "actor": "BTN"},
    # UTG+BTN cold-call → SB acts: BTN はコールできると確認済み
    {"label": "SB vs UTG+BTN [C]",  "pf": "R2.5-F-F-C",    "actor": "SB"},
    # UTG+BTN cold-call → BB acts (SB folds)
    {"label": "BB vs UTG+BTN [C]",  "pf": "R2.5-F-F-C-F",  "actor": "BB"},
    # CO+BTN call → BB acts: 仮に BTN 側が 'C'
    {"label": "BB vs CO+BTN [C]",   "pf": "F-F-R2.5-C-F",  "actor": "BB"},
    # UTG+CO call → BB (SB folds): CO の 'C' が通るか
    {"label": "BB vs UTG+CO [C]",   "pf": "R2.5-F-C-F-F",  "actor": "BB"},
]

# 全フェーズとスポットのマッピング
ALL_PHASES = [
    ("rfi",           RFI_SPOTS,           "RFI — 各ポジションのオープン"),
    ("vs_open",       VS_OPEN_SPOTS,       "vs Single Raise — BB/SB/IP の守備"),
    ("vs_3bet",       VS_3BET_SPOTS,       "vs 3-bet — オープン側の対応"),
    ("vs_4bet",       VS_4BET_SPOTS,       "vs 4-bet — 3-bet 側の対応"),
    ("vs_5bet",       VS_5BET_SPOTS,       "vs 5-bet — 4-bet 側の対応"),
    ("multiway",      MULTIWAY_PRE_SPOTS,  "マルチウェイ — raise+call(1/2/3) 後の fold/call/3bet"),
    ("probe_multiway",PROBE_MULTIWAY_SPOTS,"マルチウェイ アクションコード調査"),
]

# ─── 本書スコア式（検証用） ────────────────────────────────────────
T_OPEN = {"UTG": 24, "HJ": 22, "CO": 20, "BTN": 18, "SB": 22}

CARD_VAL = {"A": 14, "K": 13, "Q": 12, "J": 11, "T": 10,
            "9": 9, "8": 8, "7": 7, "6": 6, "5": 5, "4": 4, "3": 3, "2": 2}

def book_score(hand: str) -> float:
    """'AKs', 'QJo', '77' 形式のハンドスコアを計算。"""
    if len(hand) == 2 and hand[0] == hand[1]:
        v = CARD_VAL.get(hand[0], 0)
        return v * 2 + 10  # pair bonus
    if len(hand) != 3:
        return 0
    h, l, suited = hand[0], hand[1], hand[2] == "s"
    hv, lv = CARD_VAL.get(h, 0), CARD_VAL.get(l, 0)
    if hv < lv:
        hv, lv = lv, hv
    gap = hv - lv - 1
    s = hv + lv
    s += 3 if suited else 0
    if   gap == 0: s += 1
    elif gap <= 2: s += 0.5
    # A blocker
    if h == "A" and l == "A":
        pass
    elif h == "A" and l == "K":
        s += 4
    elif h == "A":
        s += 3
    elif h == "K":
        s += 2
    # penalties
    if gap >= 4 and h != "A":
        s -= 1
    if hv < 9 and lv < 9:
        s -= 1
    return s

# ─── 共通関数 ──────────────────────────────────────────────────────
def check_token():
    import base64 as _b64
    try:
        payload = TOKEN.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        data = json.loads(_b64.urlsafe_b64decode(payload))
        exp = data.get("exp", 0)
        remaining = exp - time.time()
        if remaining <= 60:
            print(f"❌ TOKEN 期限切れ（残り{remaining:.0f}秒）"); sys.exit(1)
        print(f"✅ TOKEN OK（残り{remaining/60:.1f}分）")
    except Exception as e:
        print(f"❌ TOKEN パース失敗: {e}"); sys.exit(1)

def make_headers():
    h = {
        "accept":             "application/json, text/plain, */*",
        "accept-language":    "ja,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
        "authorization":      f"Bearer {TOKEN}",
        "cache-control":      "no-cache",
        "origin":             "https://app.gtowizard.com",
        "pragma":             "no-cache",
        "priority":           "u=1, i",
        "referer":            "https://app.gtowizard.com/",
        "sec-ch-ua":          '"Chromium";v="148", "Microsoft Edge";v="148", "Not/A)Brand";v="99"',
        "sec-ch-ua-mobile":   "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest":     "empty",
        "sec-fetch-mode":     "cors",
        "sec-fetch-site":     "same-site",
        "user-agent":         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
    }
    if GWCLIENTID:     h["gwclientid"]     = GWCLIENTID
    if GOOGLE_ANAL_ID: h["google-anal-id"] = GOOGLE_ANAL_ID
    return h

def call_api(pf_actions: str, depth: int = 100):
    params = {
        "gametype":        GT,
        "depth":           str(depth),
        "stacks":          "",
        "preflop_actions": pf_actions,
        "flop_actions":    "",
        "turn_actions":    "",
        "river_actions":   "",
        "board":           "",
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
            print(f"  [429] pf={pf_actions!r} → {wait}s 待機...")
            time.sleep(wait)
            continue
        print(f"  [HTTP {r.status_code}] pf={pf_actions!r}")
        return None
    return None

def get_player(data, pos):
    for p in data.get("players_info", []):
        player = p.get("player", {})
        if isinstance(player, dict) and player.get("position") == pos:
            return p
    return None

def classify_actions(sols):
    codes = {}
    for s in sols:
        a = s["action"]
        t, c = a["type"], a["code"]
        bp = float(a.get("betsize_by_pot") or 0)
        if   t == "FOLD":  codes["fold"]   = c
        elif t == "CALL":  codes["call"]   = c
        elif t == "CHECK": codes["check"]  = c
        elif t == "RAISE":
            if   bp < 0.40: codes["raise_small"] = c
            elif bp < 0.80: codes["raise_mid"]   = c
            elif bp < 1.50: codes["raise_large"] = c
            else:           codes["raise_allin"] = c
    return codes

def calc_hand_action_rates_from_shc(shc: dict) -> list:
    """simple_hand_counters から per-hand アクション率を返す（combo加重）。
    raise% = 1 - fold - call で計算（action code の差異を吸収）。"""
    rows = []
    for hand_name, hand_info in shc.items():
        combos = hand_info.get("total_combos", 0.0)
        if combos < 0.1:
            continue
        freqs = hand_info.get("actions_total_frequencies", {})
        fold  = freqs.get("F", 0.0)
        call  = freqs.get("C", 0.0)
        raise_total = max(0.0, 1.0 - fold - call)
        rows.append({"hc": hand_name, "total": round(combos, 1),
                     "fold": fold, "call": call, "raise": raise_total})
    total_range = sum(r["total"] for r in rows)
    for r in rows:
        r["share"] = round(r["total"] / total_range * 100, 1) if total_range > 0 else 0.0
    rows.sort(key=lambda x: -x["total"])
    return rows

def weighted_raise_rate(rows, raise_keys):
    """コンボ加重平均 raise 率。"""
    if not raise_keys or not rows:
        return None
    tc = sum(r["total"] for r in rows)
    if tc == 0:
        return None
    return sum(r["total"] * sum(r.get(k, 0) or 0 for k in raise_keys) for r in rows) / tc

def print_hand_table(rows, label=""):
    if not rows:
        return
    keys = [k for k in rows[0] if k not in ("hc", "total", "share")]
    if label:
        print(f"\n  {label}")
    hdr = f"  {'ハンド':16s} {'コンボ':>6} {'シェア':>6}"
    for k in keys:
        hdr += f" {k:>12}"
    print(hdr)
    print(f"  {'-'*72}")
    for row in rows[:30]:  # 上位30ハンドのみ表示
        line = f"  {row['hc']:16s} {row['total']:6.1f} {row['share']:5.1f}%"
        for k in keys:
            v = row.get(k)
            line += f" {v*100:11.0f}%" if v is not None else f"  {'—':>11}"
        print(line)

# ─── フェーズ別実行 ────────────────────────────────────────────────
def run_probe_multiway():
    """マルチウェイ アクションコード調査。各スポットで action_solutions を表示。"""
    print("\n=== PROBE_MULTIWAY ===")
    results = {}
    for spot in PROBE_MULTIWAY_SPOTS:
        pf, actor, label = spot["pf"], spot["actor"], spot["label"]
        print(f"\n--- {label} (pf={pf!r}, actor={actor}) ---")
        data = call_api(pf)
        time.sleep(5.0)
        if not data:
            print(f"  ❌ HTTP 204 — ツリー未収録"); results[label] = "204"; continue

        sols = data.get("action_solutions", [])
        print(f"  action_solutions ({len(sols)} actions):")
        for s in sols:
            a = s["action"]
            print(f"    type={a['type']} code={a['code']!r} betsize_by_pot={a.get('betsize_by_pot')}")

        player = get_player(data, actor)
        if player:
            shc = player.get("simple_hand_counters", {})
            rows = calc_hand_action_rates_from_shc(shc)
            tc = sum(r["total"] for r in rows)
            rr = sum(r["total"] * r.get("raise", 0) for r in rows) / tc if tc else 0.0
            fr = sum(r["total"] * r.get("fold", 0) for r in rows) / tc if tc else 0.0
            cr = 1.0 - fr - rr
            print(f"  {actor}: fold={fr*100:.0f}% call={cr*100:.0f}% raise={rr*100:.0f}%")
            results[label] = {"fold": round(fr*100,1), "call": round(cr*100,1), "raise": round(rr*100,1)}
        else:
            avail = [p["player"].get("position","?") if isinstance(p.get("player"),dict) else "?"
                     for p in data.get("players_info",[])]
            print(f"  ⚠️ actor={actor!r} 見つからず。利用可能: {avail}")
            results[label] = "actor_not_found"

    out = FINDINGS_DIR / "preflop_probe_multiway.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 完了 → {out}")


def run_probe():
    """レスポンス形式を確認する（BTN RFI: pf="F-F-F"）。"""
    print("\n=== PROBE: BTN RFI (pf='F-F-F') ===")
    data = call_api("F-F-F")
    if not data:
        print("❌ データ取得失敗"); return
    time.sleep(5.0)

    # players_info 構造を確認
    print("\n--- players_info ---")
    for p in data.get("players_info", []):
        player = p.get("player", {})
        pos    = player.get("position", "?") if isinstance(player, dict) else str(player)
        hcs    = p.get("hand_categories", [])
        n_hcs  = len(hcs)
        sample = [h["name"] for h in hcs[:5]] if hcs else []
        print(f"  {pos}: {n_hcs} hand_categories, sample={sample}")

    # action_solutions 構造を確認
    print("\n--- action_solutions ---")
    for s in data.get("action_solutions", []):
        a = s["action"]
        hcs = s.get("hand_categories") or []
        print(f"  {a['type']} code={a['code']} bp={a.get('betsize_by_pot')} hcs={len(hcs)}")

    # raw JSON 保存
    out = FINDINGS_DIR / "preflop_probe_BTN_RFI.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ raw dump → {out}")

def run_spots(spots: list, phase_label: str) -> dict:
    results = {}
    for spot in spots:
        pf    = spot["pf"]
        actor = spot["actor"]
        label = spot["label"]
        print(f"\n--- {label} (pf={pf!r}, actor={actor}) ---")

        data = call_api(pf)
        time.sleep(5.0)
        if not data:
            print("  ❌ データ取得失敗（HTTP 204 = ツリーに未収録の可能性）"); continue

        # 対応するプレイヤー情報取得
        player = get_player(data, actor)
        if not player:
            # actor が見つからない場合、利用可能なポジション一覧を表示
            avail = [p["player"].get("position", "?") if isinstance(p.get("player"), dict) else "?"
                     for p in data.get("players_info", [])]
            print(f"  ⚠️ actor={actor!r} 見つからず。利用可能: {avail}")
            # フォールバック: 最初のアクティブプレイヤー
            player = data.get("players_info", [{}])[0] if data.get("players_info") else None
            if not player:
                continue

        sols   = data.get("action_solutions", [])
        codes  = classify_actions(sols)
        shc    = (player or {}).get("simple_hand_counters", {})
        rows   = calc_hand_action_rates_from_shc(shc)

        tc = sum(r["total"] for r in rows)
        raise_rate = sum(r["total"] * r.get("raise", 0) for r in rows) / tc if tc else 0.0

        print(f"  コード: {codes}")
        print(f"  Raise%: {raise_rate*100:.1f}%")

        # 本書スコアとの比較（RFI フェーズのみ）
        if phase_label == "rfi" and actor in T_OPEN:
            threshold = T_OPEN[actor]
            book_raise = [r["hc"] for r in rows
                          if book_score(r["hc"]) >= threshold and r.get("raise", 0) > 0.01]
            gto_raise  = [r["hc"] for r in rows if r.get("raise", 0) >= 0.50]
            print(f"  T_open={threshold}: 本書オープン≈{len(book_raise)}ハンド / GTO50%+={len(gto_raise)}ハンド")

        print_hand_table(rows, label=label)

        results[label] = {
            "pf":        pf,
            "actor":     actor,
            "codes":     codes,
            "raise_pct": round(raise_rate * 100, 1),
            "rows":      rows,
        }

    return results

def main():
    if not TOKEN:
        print("❌ TOKEN 未設定"); sys.exit(1)

    check_token()
    time.sleep(5.0)

    if PHASE == "probe":
        run_probe()
        return

    if PHASE == "probe_multiway":
        run_probe_multiway()
        return

    # 実行するフェーズを決定
    if PHASE == "all":
        phases_to_run = ALL_PHASES
    else:
        phases_to_run = [(key, spots, desc) for key, spots, desc in ALL_PHASES if key == PHASE]
        if not phases_to_run:
            valid = [k for k, _, _ in ALL_PHASES]
            print(f"❌ PHASE={PHASE!r} は不正。有効値: {valid}"); sys.exit(1)

    all_results = {}
    total_calls = sum(len(spots) for _, spots, _ in phases_to_run)
    print(f"\n実行予定: {len(phases_to_run)}フェーズ / {total_calls}コール")

    for phase_key, spots, desc in phases_to_run:
        print(f"\n{'='*70}")
        print(f"■ {desc}  ({len(spots)}コール)")
        all_results[phase_key] = run_spots(spots, phase_key)

    # JSON 保存
    out = FINDINGS_DIR / f"preflop_gto_{PHASE}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"gametype": GT, "phase": PHASE, "results": all_results},
                  f, ensure_ascii=False, indent=2)
    print(f"\n✅ 完了 → {out}")

    # RFI サマリー表
    if "rfi" in all_results:
        print("\n\n=== RFI サマリー: ポジション別オープン率 ===")
        print(f"  {'スポット':16s} | {'GTO Raise%':>11} | {'T_open':>7}")
        print(f"  {'-'*45}")
        pos_map = {"UTG RFI": "UTG", "HJ RFI": "HJ", "CO RFI": "CO",
                   "BTN RFI": "BTN", "SB RFI": "SB"}
        for label, res in all_results["rfi"].items():
            rp  = res.get("raise_pct")
            pos = pos_map.get(label, "?")
            th  = T_OPEN.get(pos, "?")
            rp_s = f"{rp:.1f}%" if rp is not None else "—"  # noqa
            print(f"  {label:16s} | {rp_s:>11} | {str(th):>7}")

if __name__ == "__main__":
    main()
