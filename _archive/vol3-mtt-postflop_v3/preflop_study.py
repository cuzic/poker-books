#!/usr/bin/env python3
"""
preflop_study.py — MTT6mSimple プリフロップ GTO データ収集・分析

【API特性 (2026-05-24 検証)】
  gametype = "MTT6mSimple"  (ポストフロップのMTTGeneralとは別)
  stacks   = "200.125-..."  (6プレイヤー全員のスタックを明示する必要あり)
  strategy : list[169]      (1326コンボではなく169ハンドタイプ別)
  evs      : list[169]      (各ハンドのEV — ハンド同定に使用)

【ハンド順序 (GTO Wizard独自順序)】
  EVランキング from BB vs HJ 2.2x open (EV from call action):
    idx=80: AA (EV≈9.36)
    idx=126: KK (EV≈7.07)
    idx=149: QQ (EV≈5.12)
    idx=105: JJ (EV≈3.98)
    idx=84:  TT or AKs (EV≈3.26)
  ※ 標準13×13行列スキャン順とは異なる。詳細は --identify を参照。

【プリフロップアクション文字列の形式】
  6-maxポジション順: LJ(UTG)(1), HJ(2), CO(3), BTN(4), SB(5), BB(6)
  preflop_actions = "" → LJの判断
  "F" → HJの判断 (LJがフォールド済み)
  "F-F" → COの判断
  "F-F-F" → BTNの判断
  "F-F-F-F" → SBの判断
  "F-F-F-F-F" → BBの判断 (SBがフォールド済み = BB vs BB? → SBのリンプ?)

  RFIシナリオ:
    LJ RFI: preflop=""           → LJがレイズ or フォールド
    HJ RFI: preflop="F"          → HJがレイズ or フォールド
    CO RFI: preflop="F-F"        → COがレイズ or フォールド
    BTN RFI: preflop="F-F-F"     → BTNがレイズ or フォールド
    SB vs BB: preflop="F-F-F-F"  → SBがレイズ or リンプ or フォールド

  ディフェンスシナリオ (BB defense vs HJ 2.2x):
    preflop="F-R2.2-F-F-F"  → BBがコール or 3ベット or フォールド

使い方:
  TOKEN=... GWCLIENTID=... GOOGLE_ANAL_ID=... python3 preflop_study.py --probe
  TOKEN=... GWCLIENTID=... python3 preflop_study.py --collect --scenario BTN_RFI_200
  TOKEN=... GWCLIENTID=... python3 preflop_study.py --collect --all
  python3 preflop_study.py --analyze --scenario BTN_RFI_200
  python3 preflop_study.py --identify  # EVでハンド順序を推定
"""

import os, sys, json, time, argparse, requests
from pathlib import Path
from collections import defaultdict
from typing import Any

TOKEN          = os.environ.get("TOKEN", "")
GWCLIENTID     = os.environ.get("GWCLIENTID", "")
GOOGLE_ANAL_ID = os.environ.get("GOOGLE_ANAL_ID", "")
GT             = "MTT6mSimple"
FINDINGS_DIR   = Path(__file__).parent / "findings"
BASE_URL       = "https://api.gtowizard.com/v4/solutions/spot-solution/"

# ──────────────────── ハンド順序マッピング ────────────────────
# GTO Wizard の169ハンド順序は独自形式。
# findings/preflop_hand_map.json にEVランキングで同定した完全マッピングを保存。
def _load_hand_map() -> dict[int, str]:
    map_file = FINDINGS_DIR / "preflop_hand_map.json"
    if map_file.exists():
        try:
            d = json.loads(map_file.read_text())
            return {int(k): v for k, v in d.get("idx_to_hand", {}).items()}
        except Exception:
            pass
    # フォールバック: 最低限の対応表（--identify 実行前）
    return {80: "AA", 126: "KK", 149: "QQ", 105: "JJ", 84: "TT"}

KNOWN_HAND_MAP: dict[int, str] = _load_hand_map()

# ──────────────────── シナリオ定義 ────────────────────
# depth と stacks は同じ値 (MTT6mSimple はスタック明示が必要)
def make_stacks(depth: float, n_players: int = 6) -> str:
    return "-".join([str(depth)] * n_players)

# スタックレベル別のdepth (BBアンテ込み)
DEPTHS = {
    "200": 200.125,
    "100": 100.125,
    "50":  50.125,
    "30":  30.125,
    "25":  25.125,
    "20":  20.125,
    "15":  15.125,
    "10":  10.125,
}

PREFLOP_SCENARIOS: dict[str, dict[str, Any]] = {
    # ── RFI: 各ポジションのオープンレンジ ──
    "LJ_RFI_200":  {"depth": 200.125, "pf": "",           "label": "LJ(UTG) RFI  200BB", "pos": "LJ",  "role": "RFI"},
    "LJ_RFI_30":   {"depth": 30.125,  "pf": "",           "label": "LJ(UTG) RFI  30BB",  "pos": "LJ",  "role": "RFI"},
    "LJ_RFI_25":   {"depth": 25.125,  "pf": "",           "label": "LJ(UTG) RFI  25BB",  "pos": "LJ",  "role": "RFI"},
    "LJ_RFI_20":   {"depth": 20.125,  "pf": "",           "label": "LJ(UTG) RFI  20BB",  "pos": "LJ",  "role": "RFI"},
    "LJ_RFI_15":   {"depth": 15.125,  "pf": "",           "label": "LJ(UTG) RFI  15BB",  "pos": "LJ",  "role": "RFI"},

    "HJ_RFI_200":  {"depth": 200.125, "pf": "F",          "label": "HJ RFI  200BB", "pos": "HJ",  "role": "RFI"},
    "HJ_RFI_30":   {"depth": 30.125,  "pf": "F",          "label": "HJ RFI  30BB",  "pos": "HJ",  "role": "RFI"},
    "HJ_RFI_25":   {"depth": 25.125,  "pf": "F",          "label": "HJ RFI  25BB",  "pos": "HJ",  "role": "RFI"},
    "HJ_RFI_20":   {"depth": 20.125,  "pf": "F",          "label": "HJ RFI  20BB",  "pos": "HJ",  "role": "RFI"},
    "HJ_RFI_15":   {"depth": 15.125,  "pf": "F",          "label": "HJ RFI  15BB",  "pos": "HJ",  "role": "RFI"},

    "CO_RFI_200":  {"depth": 200.125, "pf": "F-F",        "label": "CO RFI  200BB", "pos": "CO",  "role": "RFI"},
    "CO_RFI_30":   {"depth": 30.125,  "pf": "F-F",        "label": "CO RFI  30BB",  "pos": "CO",  "role": "RFI"},
    "CO_RFI_25":   {"depth": 25.125,  "pf": "F-F",        "label": "CO RFI  25BB",  "pos": "CO",  "role": "RFI"},
    "CO_RFI_20":   {"depth": 20.125,  "pf": "F-F",        "label": "CO RFI  20BB",  "pos": "CO",  "role": "RFI"},
    "CO_RFI_15":   {"depth": 15.125,  "pf": "F-F",        "label": "CO RFI  15BB",  "pos": "CO",  "role": "RFI"},

    "BTN_RFI_200": {"depth": 200.125, "pf": "F-F-F",      "label": "BTN RFI 200BB", "pos": "BTN", "role": "RFI"},
    "BTN_RFI_30":  {"depth": 30.125,  "pf": "F-F-F",      "label": "BTN RFI 30BB",  "pos": "BTN", "role": "RFI"},
    "BTN_RFI_25":  {"depth": 25.125,  "pf": "F-F-F",      "label": "BTN RFI 25BB",  "pos": "BTN", "role": "RFI"},
    "BTN_RFI_20":  {"depth": 20.125,  "pf": "F-F-F",      "label": "BTN RFI 20BB",  "pos": "BTN", "role": "RFI"},
    "BTN_RFI_15":  {"depth": 15.125,  "pf": "F-F-F",      "label": "BTN RFI 15BB",  "pos": "BTN", "role": "RFI"},

    "SB_RFI_200":  {"depth": 200.125, "pf": "F-F-F-F",    "label": "SB RFI  200BB", "pos": "SB",  "role": "RFI"},
    "SB_RFI_30":   {"depth": 30.125,  "pf": "F-F-F-F",    "label": "SB RFI  30BB",  "pos": "SB",  "role": "RFI"},
    "SB_RFI_25":   {"depth": 25.125,  "pf": "F-F-F-F",    "label": "SB RFI  25BB",  "pos": "SB",  "role": "RFI"},
    "SB_RFI_20":   {"depth": 20.125,  "pf": "F-F-F-F",    "label": "SB RFI  20BB",  "pos": "SB",  "role": "RFI"},
    "SB_RFI_15":   {"depth": 15.125,  "pf": "F-F-F-F",    "label": "SB RFI  15BB",  "pos": "SB",  "role": "RFI"},

    # ── BB defense vs HJ open 2.2x ──
    "BB_def_HJ_200": {"depth": 200.125, "pf": "F-R2.2-F-F-F", "label": "BB def vs HJ 2.2x 200BB", "pos": "BB", "role": "defend_vs_HJ"},
    "BB_def_HJ_30":  {"depth": 30.125,  "pf": "F-R2.2-F-F-F", "label": "BB def vs HJ 2.2x 30BB",  "pos": "BB", "role": "defend_vs_HJ"},
    "BB_def_HJ_25":  {"depth": 25.125,  "pf": "F-R2.2-F-F-F", "label": "BB def vs HJ 2.2x 25BB",  "pos": "BB", "role": "defend_vs_HJ"},
    "BB_def_HJ_20":  {"depth": 20.125,  "pf": "F-R2.2-F-F-F", "label": "BB def vs HJ 2.2x 20BB",  "pos": "BB", "role": "defend_vs_HJ"},
    "BB_def_HJ_15":  {"depth": 15.125,  "pf": "F-R2.2-F-F-F", "label": "BB def vs HJ 2.2x 15BB",  "pos": "BB", "role": "defend_vs_HJ"},

    # ── BB defense vs CO open ──
    "BB_def_CO_200": {"depth": 200.125, "pf": "F-F-R2.2-F-F", "label": "BB def vs CO 2.2x 200BB", "pos": "BB", "role": "defend_vs_CO"},
    "BB_def_CO_25":  {"depth": 25.125,  "pf": "F-F-R2.2-F-F", "label": "BB def vs CO 2.2x 25BB",  "pos": "BB", "role": "defend_vs_CO"},
    "BB_def_CO_20":  {"depth": 20.125,  "pf": "F-F-R2.2-F-F", "label": "BB def vs CO 2.2x 20BB",  "pos": "BB", "role": "defend_vs_CO"},

    # ── BB defense vs BTN open (200BB=R2.6、短スタック≤30BB=R2) ──
    "BB_def_BTN_200": {"depth": 200.125, "pf": "F-F-F-R2.6-F", "label": "BB def vs BTN 2.6x 200BB", "pos": "BB", "role": "defend_vs_BTN"},
    "BB_def_BTN_30":  {"depth": 30.125,  "pf": "F-F-F-R2-F",   "label": "BB def vs BTN 2x 30BB",    "pos": "BB", "role": "defend_vs_BTN"},
    "BB_def_BTN_25":  {"depth": 25.125,  "pf": "F-F-F-R2-F",   "label": "BB def vs BTN 2x 25BB",    "pos": "BB", "role": "defend_vs_BTN"},
    "BB_def_BTN_20":  {"depth": 20.125,  "pf": "F-F-F-R2-F",   "label": "BB def vs BTN 2x 20BB",    "pos": "BB", "role": "defend_vs_BTN"},
    "BB_def_BTN_15":  {"depth": 15.125,  "pf": "F-F-F-R2-F",   "label": "BB def vs BTN 2x 15BB",    "pos": "BB", "role": "defend_vs_BTN"},

    # ── SB defense vs BTN open (200BB=R2.6、短スタック≤30BB=R2) ──
    "SB_def_BTN_200": {"depth": 200.125, "pf": "F-F-F-R2.6", "label": "SB def vs BTN 2.6x 200BB", "pos": "SB", "role": "defend_vs_BTN"},
    "SB_def_BTN_25":  {"depth": 25.125,  "pf": "F-F-F-R2",   "label": "SB def vs BTN 2x 25BB",    "pos": "SB", "role": "defend_vs_BTN"},
    "SB_def_BTN_20":  {"depth": 20.125,  "pf": "F-F-F-R2",   "label": "SB def vs BTN 2x 20BB",    "pos": "SB", "role": "defend_vs_BTN"},
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


def call_preflop_api(depth: float, pf: str) -> dict[str, Any] | None:
    stacks = make_stacks(depth)
    params: dict[str, Any] = {
        "gametype": GT, "depth": str(depth), "stacks": stacks,
        "preflop_actions": pf, "flop_actions": "",
        "turn_actions": "", "river_actions": "", "board": "",
    }
    for attempt in range(4):
        r = requests.get(BASE_URL, params=params, headers=make_headers(), timeout=30)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 10))
            print(f"    429 rate limit, {wait}s 待機...")
            time.sleep(wait)
            continue
        if r.status_code == 401:
            print(f"    401 Unauthorized: トークン期限切れ")
            return None
        print(f"    HTTP {r.status_code}: {r.text[:200]}")
        if attempt < 3:
            time.sleep(3)
    return None


# ──────────────────── プリフロップ戦略抽出 ────────────────────

def extract_strategy(data: dict) -> dict[str, Any]:
    """
    APIレスポンスから全169ハンドの fold/call/raise/allin 頻度と EV を抽出する。
    """
    as_ = data.get("action_solutions", [])
    if not as_:
        return {}

    strategies: dict[str, list[float]] = {}
    evs_by_code: dict[str, list[float]] = {}
    action_meta: dict[str, dict] = {}

    for item in as_:
        code = item["action"]["code"]
        strategies[code]  = item.get("strategy", [])
        evs_by_code[code] = item.get("evs", [])
        action_meta[code] = {
            "type":            item["action"]["type"],
            "betsize":         item["action"]["betsize"],
            "total_frequency": item["total_frequency"],
            "total_ev":        item.get("total_ev", 0),
        }

    n = len(strategies.get(list(strategies.keys())[0], []))

    # アクションをカテゴリ別に集約
    fold_codes  = [c for c in strategies if c == "F"]
    call_codes  = [c for c in strategies if c == "C"]
    raise_codes = [c for c in strategies if c not in ("F", "C", "X") and not c.startswith("RAI")]
    allin_codes = [c for c in strategies if c == "RAI"]

    result: dict[str, Any] = {
        "n_hands":      n,
        "action_codes": list(strategies.keys()),
        "action_meta":  action_meta,
        "hands": [],
    }

    for i in range(n):
        fold_f  = sum(strategies[c][i] for c in fold_codes  if i < len(strategies[c]))
        call_f  = sum(strategies[c][i] for c in call_codes  if i < len(strategies[c]))
        raise_f = sum(strategies[c][i] for c in raise_codes if i < len(strategies[c]))
        allin_f = sum(strategies[c][i] for c in allin_codes if i < len(strategies[c]))

        # EVは非フォールドアクションで有効
        ev_val = 0.0
        for c in call_codes + raise_codes + allin_codes:
            if i < len(evs_by_code.get(c, [])):
                ev_val = max(ev_val, evs_by_code[c][i])  # 最高EVを取る

        hand_name = KNOWN_HAND_MAP.get(i, f"hand_{i:03d}")

        result["hands"].append({
            "idx":     i,
            "name":    hand_name,
            "fold":    round(fold_f,  4),
            "call":    round(call_f,  4),
            "raise":   round(raise_f, 4),
            "allin":   round(allin_f, 4),
            "ev":      round(ev_val,  4),
        })

    return result


# ──────────────────── 収集 ────────────────────

def collect_scenario(scenario_key: str, cfg: dict[str, Any]) -> None:
    outf = FINDINGS_DIR / f"preflop_study_{scenario_key}.json"
    FINDINGS_DIR.mkdir(exist_ok=True)

    if outf.exists():
        print(f"  スキップ（既存）: {outf.name}")
        return

    label = cfg.get("label", scenario_key)
    print(f"\n  [{scenario_key}] {label}  depth={cfg['depth']}")

    data = call_preflop_api(cfg["depth"], cfg["pf"])
    if data is None or "action_solutions" not in data:
        print(f"    API失敗またはデータなし")
        return

    strat = extract_strategy(data)
    if not strat:
        print(f"    strategy取得失敗")
        return

    # 集計
    total_fold  = sum(h["fold"]  for h in strat["hands"]) / len(strat["hands"])
    total_raise = sum(h["raise"] + h["allin"] for h in strat["hands"]) / len(strat["hands"])
    total_call  = sum(h["call"]  for h in strat["hands"]) / len(strat["hands"])

    print(f"    actions={strat['action_codes']}")
    print(f"    fold={total_fold*100:.1f}%  call={total_call*100:.1f}%  raise={total_raise*100:.1f}%")

    # 有名ハンドの表示
    for h in strat["hands"]:
        if h["name"] in ("AA", "KK", "QQ", "JJ", "TT"):
            print(f"    {h['name']}: F={h['fold']:.3f} C={h['call']:.3f} R={h['raise']:.3f} ev={h['ev']:.3f}")

    rec = {
        "scenario":    scenario_key,
        "label":       label,
        "depth":       cfg["depth"],
        "pf_actions":  cfg["pf"],
        "pos":         cfg.get("pos", ""),
        "role":        cfg.get("role", ""),
        **strat,
    }

    with outf.open("w") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    print(f"    保存: {outf.name}")

    time.sleep(1.5)


# ──────────────────── ハンド同定 ────────────────────

def identify_hands() -> None:
    """
    保存済みデータのEVランキングからハンド順序を推定する。
    """
    # EVが最も大きい=最強ハンドを仮定してランキング
    # 複数シナリオのEVを集計して安定したランキングを作る

    combined_ev: dict[int, list[float]] = defaultdict(list)

    for fpath in sorted(FINDINGS_DIR.glob("preflop_study_*.json")):
        try:
            data = json.loads(fpath.read_text())
        except json.JSONDecodeError:
            continue

        for h in data.get("hands", []):
            idx = h["idx"]
            ev = h["ev"]
            if ev > 0:
                combined_ev[idx].append(ev)

    if not combined_ev:
        print("データなし。先に --collect --all を実行してください。")
        return

    # 平均EVでランキング
    avg_ev = {idx: sum(vs)/len(vs) for idx, vs in combined_ev.items()}
    ranked = sorted(avg_ev.items(), key=lambda x: -x[1])

    print(f"\n{'═'*60}")
    print(f"  ハンド同定 — EV降順ランキング (全{len(ranked)}ハンド)")
    print(f"{'═'*60}")
    print(f"  {'ランク':>5s}  {'idx':>5s}  {'平均EV':>8s}  {'推定ハンド':>12s}  {'サンプル数':>8s}")
    print(f"  {'─'*5}  {'─'*5}  {'─'*8}  {'─'*12}  {'─'*8}")

    # 推定ハンド名 (EVランクから推測)
    pair_names = ["AA","KK","QQ","JJ","TT","99","88","77","66","55","44","33","22"]
    suited_names = [
        f"{r1}{r2}s"
        for r1 in "AKQJT98765432"
        for r2 in "AKQJT98765432"
        if "AKQJT98765432".index(r1) < "AKQJT98765432".index(r2)
    ]
    offsuit_names = [
        f"{r1}{r2}o"
        for r1 in "AKQJT98765432"
        for r2 in "AKQJT98765432"
        if "AKQJT98765432".index(r1) < "AKQJT98765432".index(r2)
    ]

    # 大まかな推定 (top13=ペア, 次78=スーテッド, 次78=オフスーツ の期待値順)
    expected_order = pair_names + suited_names + offsuit_names

    for rank, (idx, ev) in enumerate(ranked[:50]):
        known = KNOWN_HAND_MAP.get(idx, "")
        estimated = expected_order[rank] if rank < len(expected_order) else "?"
        n = len(combined_ev[idx])
        print(f"  {rank+1:5d}  {idx:5d}  {ev:8.3f}  {(known or estimated):>12s}  {n:8d}")

    # 低EV (弱ハンド)
    print(f"\n  ... (最弱ハンド)")
    for rank, (idx, ev) in enumerate(ranked[-15:]):
        known = KNOWN_HAND_MAP.get(idx, "")
        offset = len(ranked) - 15 + rank
        estimated = expected_order[offset] if offset < len(expected_order) else "?"
        n = len(combined_ev[idx])
        print(f"  {offset+1:5d}  {idx:5d}  {ev:8.3f}  {(known or estimated):>12s}  {n:8d}")


# ──────────────────── 分析 ────────────────────

def analyze_scenario(scenario_key: str) -> None:
    fpath = FINDINGS_DIR / f"preflop_study_{scenario_key}.json"
    if not fpath.exists():
        print(f"データなし: {fpath}")
        return

    data = json.loads(fpath.read_text())
    print(f"\n{'═'*70}")
    print(f"  PREFLOP STUDY: {data.get('label', scenario_key)}")
    print(f"  depth={data['depth']}BB  pos={data.get('pos','')}  actions={data.get('action_codes')}")
    print(f"{'═'*70}")

    hands = data.get("hands", [])
    # idx から最新のハンド名を解決 (保存時と異なる場合もある)
    for h in hands:
        h["name"] = KNOWN_HAND_MAP.get(h["idx"], h["name"])
    # EV降順ソート
    sorted_hands = sorted(hands, key=lambda h: -h["ev"])

    print(f"\n  [EV上位30ハンド]")
    print(f"  {'idx':>5s}  {'ハンド':>8s}  {'フォールド':>8s}  {'コール':>6s}  {'レイズ':>6s}  {'EV':>8s}")
    print(f"  {'─'*5}  {'─'*8}  {'─'*8}  {'─'*6}  {'─'*6}  {'─'*8}")
    for h in sorted_hands[:30]:
        print(f"  {h['idx']:5d}  {h['name']:>8s}  {h['fold']*100:7.1f}%  {h['call']*100:5.1f}%  {h['raise']*100:5.1f}%  {h['ev']:8.3f}")

    # アクション別集計
    print(f"\n  [アクション集計]")
    n = len(hands)
    avg_fold  = sum(h["fold"]  for h in hands) / n
    avg_call  = sum(h["call"]  for h in hands) / n
    avg_raise = sum(h["raise"] for h in hands) / n
    avg_allin = sum(h["allin"] for h in hands) / n
    print(f"  フォールド:{avg_fold*100:5.1f}%  コール:{avg_call*100:5.1f}%  レイズ:{avg_raise*100:5.1f}%  オールイン:{avg_allin*100:4.1f}%")


def compare_rfi(depth_tags: list[str]) -> None:
    """複数のスタックデプスでRFI頻度を比較する。"""
    print(f"\n{'═'*80}")
    print(f"  RFI 比較: {' vs '.join(depth_tags)}")
    print(f"{'═'*80}")

    position_order = ["LJ", "HJ", "CO", "BTN", "SB"]

    for pos in position_order:
        row = f"  {pos:4s}"
        for tag in depth_tags:
            sk = f"{pos}_RFI_{tag}"
            fpath = FINDINGS_DIR / f"preflop_study_{sk}.json"
            if not fpath.exists():
                row += f"    {'—':>8s}"
                continue
            data = json.loads(fpath.read_text())
            hands = data.get("hands", [])
            n = len(hands)
            avg_raise = sum(h["raise"] + h["allin"] for h in hands) / n if n > 0 else 0
            row += f"  {avg_raise*100:6.1f}%({tag}BB)"
        print(row)


# ──────────────────── プローブ ────────────────────

def probe() -> None:
    """代表シナリオのAPIアクセスを確認する。"""
    if not check_auth():
        sys.exit(1)

    probe_scenarios = [
        ("LJ_RFI_200",  200.125, ""),
        ("BTN_RFI_200", 200.125, "F-F-F"),
        ("BTN_RFI_25",  25.125,  "F-F-F"),
        ("BTN_RFI_15",  15.125,  "F-F-F"),
        ("SB_RFI_25",   25.125,  "F-F-F-F"),
        ("BB_def_HJ_200", 200.125, "F-R2.2-F-F-F"),
        ("BB_def_BTN_25", 25.125,  "F-F-F-R2-F"),
        ("SB_def_BTN_25", 25.125,  "F-F-F-R2"),
    ]

    print(f"\n=== probe: MTT6mSimple プリフロップ ===\n")
    for label, depth, pf in probe_scenarios:
        stacks = make_stacks(depth)
        params: dict[str, Any] = {
            "gametype": GT, "depth": str(depth), "stacks": stacks,
            "preflop_actions": pf, "flop_actions": "",
            "turn_actions": "", "river_actions": "", "board": "",
        }
        r = requests.get(BASE_URL, params=params, headers=make_headers(), timeout=30)
        if r.status_code == 200:
            data = r.json()
            action_solutions = data.get("action_solutions", [])
            codes = [a["action"]["code"] for a in action_solutions]
            n_hands = len(data.get("action_solutions", [{}])[0].get("strategy", []))
            print(f"  OK  {label:25s}  pf={pf!r:20s}  actions={codes}  n_hands={n_hands}")
        else:
            print(f"  NG  {label:25s}  HTTP {r.status_code}")
        time.sleep(0.5)


# ──────────────────── メイン ────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="preflop_study.py: MTT6mSimple プリフロップ GTO 収集・分析")
    ap.add_argument("--probe",    action="store_true", help="代表シナリオのAPIアクセスを確認")
    ap.add_argument("--collect",  action="store_true", help="GTO Wizardからデータ収集")
    ap.add_argument("--analyze",  action="store_true", help="シナリオ分析")
    ap.add_argument("--identify", action="store_true", help="EVランキングでハンド順序を推定")
    ap.add_argument("--compare-rfi", action="store_true", dest="compare_rfi",
                    help="各スタックデプスのRFI頻度比較")
    ap.add_argument("--all",      action="store_true", help="全シナリオを処理")
    ap.add_argument("--scenario", default=None,
                    choices=list(PREFLOP_SCENARIOS.keys()),
                    help="対象シナリオ")
    ap.add_argument("--depths",   default=None, nargs="+",
                    help="--compare-rfi で使うデプスタグ (例: 200 30 25 20 15)")
    args = ap.parse_args()

    if args.probe:
        probe()

    elif args.identify:
        identify_hands()

    elif args.compare_rfi:
        tags = args.depths or ["200", "30", "25", "20", "15"]
        compare_rfi(tags)

    elif args.collect:
        if not check_auth():
            sys.exit(1)
        targets = (list(PREFLOP_SCENARIOS.keys()) if args.all
                   else [args.scenario] if args.scenario
                   else None)
        if not targets:
            print("--scenario または --all を指定してください")
            ap.print_help()
            return
        for sk in targets:
            collect_scenario(sk, PREFLOP_SCENARIOS[sk])

    elif args.analyze:
        if args.scenario:
            analyze_scenario(args.scenario)
        else:
            print("--scenario を指定してください")
            ap.print_help()

    else:
        ap.print_help()


if __name__ == "__main__":
    main()
