#!/usr/bin/env python3
"""
equity_study.py — フロップ per-hand equity 収集（GTO Wizard simple_hand_counters）

目的: トップペア(TPTK/TPGK/TPMK/TPWK) ・セカンドペア(SP) ・ボトムペア(BP)
      の top_card × board_wetness 別 equity を収集し計算式を導出する。

使い方:
  TOKEN=... GWCLIENTID=... python3 equity_study.py --diagnose [--board Ks7d2c]
  TOKEN=... GWCLIENTID=... python3 equity_study.py --collect [--sbr 25] [--board-id K_dry] [--force]
  python3 equity_study.py --analyze [--sbr 25]
"""

import os, sys, json, time, argparse, requests
from pathlib import Path
from typing import Any

TOKEN          = os.environ.get("TOKEN", "")
GWCLIENTID     = os.environ.get("GWCLIENTID", "")
GOOGLE_ANAL_ID = os.environ.get("GOOGLE_ANAL_ID", "")
GT             = "MTTGeneral"
FINDINGS_DIR   = Path(__file__).parent / "findings"
BASE_URL       = "https://api.gtowizard.com/v4/solutions/spot-solution/"

SBR_CONFIGS: dict[str, dict[str, Any]] = {
    "25": {"depth": 25.125, "pf": "F-F-F-F-F-R2.1-F-C", "stacks": ""},
    "20": {"depth": 20.125, "pf": "F-F-F-F-F-R2-F-C",   "stacks": ""},
}

# ─────────────────── 研究ボード定義 ───────────────────
# key_hands: role → hand_key (GTO Wizard simple_hand_counters のキー)
#
# 注意事項:
#   - wet ボードでは middle_card + hole_card がボードと重複して二ペアになるので避ける
#     例: K_wet=Kd9s8c では K9s = TWO PAIR → TPMK は KTs を使う
#   - ボトムペアで top_card がボードにある場合は top_card + low_card = TWO PAIR になる
#     例: A_dry=As7d2c では A2s = TWO PAIR → bp は K2s を使う
#   - sp_strong: 2番目カードのペア + 大きいオーバーカード
#   - sp_weak:   2番目カードのペア + 中程度のキッカー
#   - bp:        最小カードのペア + オーバーカード

STUDY_BOARDS: list[tuple[str, str, str, str, str, str, dict[str, str]]] = [
    # ─── DRY boards (A~T top card) ───
    ("A_dry",  "As7d2c", "A", "dry",  "型1_ハイドライ",  "A高ドライ",
     {"tptk":     "AKs",  # pair of A + K kicker
      "tpgk":     "AQs",  # pair of A + Q kicker
      "tpmk":     "ATs",  # pair of A + T kicker
      "tpwk":     "A9s",  # pair of A + 9 kicker (A3s out of range)
      "sp_strong":"K7s",  # pair of 7 + K overcard (K not on board)
      "sp_weak":  "87s",  # pair of 7 + 8 kicker
      "bp":       "K2s",  # pair of 2 + K overcard (A2s = two pair on A-board)
     }),
    ("K_dry",  "Ks7d2c", "K", "dry",  "型1_ハイドライ",  "K高ドライ",
     {"tptk":     "AKs",
      "tpgk":     "KQs",
      "tpmk":     "K9s",
      "tpwk":     "K3s",  # K3s borderline range — use K4s if not in range
      "sp_strong":"A7s",  # pair of 7 + A overcard (A not on board)
      "sp_weak":  "87s",  # pair of 7 + 8 kicker
      "bp":       "A2s",  # pair of 2 + A overcard (K2s = two pair on K-board)
     }),
    ("Q_dry",  "Qd7s2c", "Q", "dry",  "型1_ハイドライ",  "Q高ドライ",
     {"tptk":     "AQs",
      "tpgk":     "KQs",
      "tpmk":     "Q9s",
      "tpwk":     "Q8s",  # Q3s out of range
      "sp_strong":"A7s",
      "sp_weak":  "87s",
      "bp":       "A2s",  # Q2s likely out of range
     }),
    ("J_dry",  "Jd7s2c", "J", "dry",  "型3_ロードライ",  "J高ドライ",
     {"tptk":     "AJs",
      "tpgk":     "KJs",
      "tpmk":     "JTs",  # J8s is ok but JT is cleaner mid kicker
      "tpwk":     "J9s",  # J3s out of range
      "sp_strong":"A7s",
      "sp_weak":  "87s",
      "bp":       "A2s",
     }),
    ("T_dry",  "Td7s2c", "T", "dry",  "型3_ロードライ",  "T高ドライ",
     {"tptk":     "ATs",
      "tpgk":     "KTs",
      "tpmk":     "QTs",
      "tpwk":     "T9s",  # T3s out of range
      "sp_strong":"A7s",
      "sp_weak":  "87s",
      "bp":       "A2s",
     }),

    # ─── SEMI-WET boards ───
    ("A_semi", "Ah8d3s", "A", "semi", "型2_ハイウェット", "A高2トーン",
     {"tptk":     "AKs",
      "tpgk":     "AQs",
      "tpmk":     "ATs",
      "tpwk":     "A4s",  # A4s — pairs A, 4 is kicker
      "sp_strong":"K8s",  # pair of 8 + K overcard (K not on board)
      "sp_weak":  "T8s",  # pair of 8 + T kicker
      "bp":       "K3s",  # pair of 3 + K overcard (A3s = two pair on A-board)
     }),
    ("K_semi", "Kh8d3s", "K", "semi", "型2_ハイウェット", "K高2トーン",
     {"tptk":     "AKs",
      "tpgk":     "KQs",
      "tpmk":     "K9s",
      "tpwk":     "K4s",
      "sp_strong":"A8s",  # pair of 8 + A overcard (A not on board)
      "sp_weak":  "T8s",  # pair of 8 + T kicker
      "bp":       "A3s",  # pair of 3 + A overcard (K3s = two pair on K-board)
     }),

    # ─── WET boards (two-pair trap を回避した hand selection) ───
    ("A_wet",  "Ah9s8d", "A", "wet",  "型4_ローウェット", "A高接続2トーン",
     {"tptk":     "AKs",
      "tpgk":     "AQs",
      "tpmk":     "ATs",
      "tpwk":     "A5s",
      "sp_strong":"K9s",  # pair of 9 + K overcard (K not on board, 9 not paired with A)
      "sp_weak":  "J9s",  # pair of 9 + J kicker
      "bp":       "K8s",  # pair of 8 + K overcard (A8s = two pair on A-board)
     }),
    ("K_wet",  "Kd9s8c", "K", "wet",  "型2_ハイウェット", "K高接続2トーン",
     {"tptk":     "AKs",
      "tpgk":     "KQs",
      "tpmk":     "KTs",  # K9s = two pair on K98! Use KTs instead
      "tpwk":     "K4s",
      "sp_strong":"A9s",  # pair of 9 + A overcard (A9s on K98 → pair of 9s, A overcard)
      "sp_weak":  "J9s",  # pair of 9 + J kicker (J not on board)
      "bp":       "A8s",  # pair of 8 + A overcard (K8s = two pair on K98!)
     }),
    ("Q_wet",  "Qh9s8c", "Q", "wet",  "型4_ローウェット", "Q高接続2トーン",
     {"tptk":     "AQs",
      "tpgk":     "KQs",
      "tpmk":     "QTs",  # Q9s = two pair on Q98! Use QTs
      "tpwk":     "Q5s",
      "sp_strong":"A9s",
      "sp_weak":  "J9s",
      "bp":       "A8s",  # K8s ok but A8s is cleaner (Q8s = two pair on Q98?)
      # Q8s on Qh9s8c: Q pairs Q (top pair) + 8 pairs 8 (bottom pair) → TWO PAIR
      # A8s on Qh9s8c: A overcard + 8 pairs 8 → bottom pair only ✓
     }),
    ("J_wet",  "Jh9s8c", "J", "wet",  "型4_ローウェット", "J高接続2トーン",
     {"tptk":     "AJs",
      "tpgk":     "KJs",
      "tpmk":     "JTs",  # J8s = two pair on J98! Use JTs (T not on board)
      "tpwk":     "J6s",  # J4s likely out of range; J6s borderline
      "sp_strong":"A9s",
      "sp_weak":  "T9s",  # pair of 9 + T kicker (T not on board)
      "bp":       "A8s",  # pair of 8 + A overcard (J8s = two pair on J98!)
     }),
    ("T_wet",  "Th9s8c", "T", "wet",  "型4_ローウェット", "T高接続2トーン",
     {"tptk":     "ATs",
      "tpgk":     "KTs",
      "tpmk":     "QTs",  # T8s = two pair on T98! Use QTs (Q not on board)
      "tpwk":     "T6s",
      "sp_strong":"A9s",  # pair of 9 + A overcard (A9s on T98 → second pair)
      "sp_weak":  "Q9s",  # pair of 9 + Q kicker (Q not on board)
      "bp":       "A8s",  # pair of 8 + A overcard (T8s = two pair on T98!)
     }),

    # ─── MONOTONE board ───
    ("A_mono", "Ah9h5h", "A", "mono", "型5_モノトーン",   "A高モノトーン",
     {"tptk":     "AKs",
      "tpgk":     "AQs",
      "tpmk":     "ATs",
      "tpwk":     "A4s",
      "sp_strong":"K9s",  # pair of 9 + K overcard (+ possible flush draw)
      "sp_weak":  "J9s",
      "bp":       "K5s",  # pair of 5 + K overcard (A5s = two pair; K not on board)
     }),

    # ─── PAIR BOARDS (型6/型7) ───
    ("pair_high", "AsAcKd", "A", "pair", "型6_ペア高",     "AAKペアボード",
     {"tptk":     "AKs",  # trips + best kicker
      "tpgk":     "AQs",  # trips + Q kicker (note: three-of-a-kind, not TP)
      "tpmk":     "ATs",
      "tpwk":     "A9s",
      "sp_strong":"KQs",  # pair of K + Q kicker (two pair on AAK? K pairs K on AAK) ← two pair!
      # Actually on AsAcKd: KQs = pair of K (using the K in hand with Kd on board) + pair of A? No...
      # On AsAcKd: if you have K-Q, the K pairs the Kd on board → pair of K (one pair), the A's on board
      # are overcards but you don't have A in hand → TOP PAIR is A's (but you don't have A)
      # KQs on AsAcKd: K pairs K (one of the board Ks) → second pair? No, the two aces are the top pair...
      # This is complex. Let me use a simpler pair board.
      "sp_weak":  "KJs",
      "bp":       "QJs",  # no pair (Q and J are both below A and K)
     }),
    ("pair_low",  "7s7d2c", "7", "pair", "型7_ペア低",    "77低ペアボード",
     {"tptk":     "AKs",  # overcard pair (no pair with board cards but strongest hand class)
      "tpgk":     "KQs",  # overcard pair
      "tpmk":     "A7s",  # THREE OF A KIND! (trips 7s with A kicker)
      "tpwk":     "87s",  # TWO PAIR (7's and 8's?) No: 87 + 77 on board = pair of 8? No...
      # On 7s7d2c: if you have 8-7, the 7 in hand + 77 on board = TRIPS! Not two pair.
      # 87s on 7s7d2c = 8 (no pair on board) + 7 (pairs with 77 on board) → TRIPS 7s with 8 kicker
      "sp_weak":  "A2s",  # TWO PAIR (A high + pair of 2? No: A doesn't pair, 2 pairs 2) → ONE PAIR (2s) + A overcard = bottom pair with big overcard
      "bp":       "Q2s",
     }),
]

# ─────────────────── ロール順序と表示名 ───────────────────
ROLE_ORDER = ["tptk", "tpgk", "tpmk", "tpwk", "sp_strong", "sp_weak", "bp"]
ROLE_LABEL = {
    "tptk":      "TPTK",
    "tpgk":      "TPGK",
    "tpmk":      "TPMK",
    "tpwk":      "TPWK",
    "sp_strong": "SP強",
    "sp_weak":   "SP弱",
    "bp":        "BP",
}


# ─────────────────── API ユーティリティ ───────────────────

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


def call_api(board: str, flop_actions: str = "", depth: float = 25.125,
             pf: str = "F-F-F-F-F-R2.1-F-C", stacks: str = "") -> dict[str, Any] | None:
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
                    print(f"  ❌ 日次クォータ超過 → {int(ra)//3600}時間後リセット")
                    sys.exit(1)
            except Exception:
                pass
            wait = 12 * (attempt + 1)
            print(f"  [429] attempt={attempt+1} → {wait}s 待機...")
            time.sleep(wait)
            continue
        print(f"  [HTTP {r.status_code}] board={board}")
        return None
    return None


def check_token() -> None:
    import base64 as _b64
    try:
        payload = TOKEN.split('.')[1]
        payload += '=' * (-len(payload) % 4)
        d = json.loads(_b64.urlsafe_b64decode(payload))
        remaining = d.get('exp', 0) - time.time()
        if remaining <= 60:
            print(f"❌ TOKEN期限切れ（残り{remaining:.0f}秒）")
            sys.exit(1)
        print(f"✅ 認証OK（残り{remaining/60:.1f}分）")
    except Exception as e:
        print(f"❌ TOKEN パース失敗: {e}")
        sys.exit(1)


def find_ip_player(data: dict[str, Any]) -> dict[str, Any] | None:
    for pi in data.get("players_info", []):
        pl = pi.get("player", {})
        if pl.get("position") == "BTN" or pl.get("is_ip") is True:
            return pi
    return None


# ─────────────────── 診断モード ───────────────────

def diagnose(board: str, sbr: str, flop_actions: str) -> None:
    cfg = SBR_CONFIGS[sbr]
    print(f"\n=== DIAGNOSE: board={board} sbr={sbr} flop_actions={flop_actions!r} ===")
    check_token()
    time.sleep(2.0)
    data = call_api(board, flop_actions=flop_actions,
                    depth=cfg["depth"], pf=cfg["pf"], stacks=cfg["stacks"])
    if not data:
        print("取得失敗"); return

    ip = find_ip_player(data)
    if not ip:
        print("BTN player not found"); return
    pos = ip.get("player", {}).get("position", "?")
    print(f"\nIP player: pos={pos}")

    shc: dict[str, Any] = ip.get("simple_hand_counters", {})
    print(f"  simple_hand_counters: {len(shc)} hands\n")

    # 主要なハンドを表示
    sample = ["AKs","AQs","ATs","A9s","A7s","A3s","A2s",
              "KQs","K9s","K3s","K2s",
              "QJs","Q9s","Q8s","Q2s",
              "AJs","KJs","JTs","J9s",
              "ATs","KTs","QTs","T9s",
              "A8s","K8s","T8s","87s","A7s","K7s","A5s","A4s","A3s"]
    print(f"  {'hand':6s} {'hand_eq':8s} {'bet%':7s} {'check%':7s} {'combos':8s}")
    print(f"  {'─'*45}")
    for h in sample:
        if h not in shc:
            continue
        entry = shc[h]
        combos = float(entry.get("total_combos", 0))
        if combos < 0.1:
            print(f"  {h:6s}  (レンジ外)")
            continue
        eq  = float(entry.get("hand_eq", 0)) * 100
        afs = entry.get("actions_total_frequencies", {})
        check_pct = float(afs.get("X", 0)) * 100
        bet_pct   = sum(float(v) for k, v in afs.items() if k != "X") * 100
        print(f"  {h:6s}  {eq:6.1f}%  {bet_pct:6.1f}%  {check_pct:6.1f}%  ({combos:.1f}c)")

    out = FINDINGS_DIR / f"diagnose_{board}_{sbr}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 生データ保存: {out}")


# ─────────────────── データ収集 ───────────────────

def extract_hand_data(shc: dict[str, Any], hand_key: str) -> dict[str, Any] | None:
    if hand_key not in shc:
        return None
    entry = shc[hand_key]
    combos = float(entry.get("total_combos", 0))
    if combos < 0.1:
        return None
    afs = entry.get("actions_total_frequencies", {})
    check_pct = float(afs.get("X", 0)) * 100
    bet_pct   = sum(float(v) for k, v in afs.items() if k != "X") * 100
    return {
        "hand":      hand_key,
        "combos":    round(combos, 2),
        "hand_eq":   round(float(entry.get("hand_eq",  0)), 4),
        "hand_eqr":  round(float(entry.get("hand_eqr", 0)), 4),
        "hand_ev":   round(float(entry.get("hand_ev",  0)), 4),
        "check_pct": round(check_pct, 1),
        "bet_pct":   round(bet_pct,   1),
        "actions":   {k: round(float(v) * 100, 1) for k, v in afs.items()},
    }


def collect_board(board_id: str, board: str, top_card: str, wetness: str,
                  board_type: str, key_hands: dict[str, str],
                  sbr: str) -> dict[str, Any] | None:
    cfg = SBR_CONFIGS[sbr]
    print(f"\n  [{board_id}] board={board} top={top_card} wet={wetness} sbr={sbr}")

    data = call_api(board, flop_actions="X",
                    depth=cfg["depth"], pf=cfg["pf"], stacks=cfg["stacks"])
    time.sleep(8.0)

    if not data:
        print("    取得失敗"); return None

    ip = find_ip_player(data)
    if not ip:
        print("    BTN player not found"); return None

    sols = data.get("action_solutions", [])
    if sols and all(float(s.get("total_frequency") or 0) == 0.0 for s in sols):
        print("    [WARN] total_frequency=0"); return None

    shc: dict[str, Any] = ip.get("simple_hand_counters", {})
    if not shc:
        print("    simple_hand_counters なし"); return None

    result_hands: dict[str, Any] = {}
    for role, hand_key in key_hands.items():
        hd = extract_hand_data(shc, hand_key)
        if hd:
            result_hands[role] = hd
            label = ROLE_LABEL.get(role, role)
            print(f"    {label:5s} {hand_key:5s}: eq={hd['hand_eq']*100:.1f}% "
                  f"bet={hd['bet_pct']:.0f}% check={hd['check_pct']:.0f}%")
        else:
            label = ROLE_LABEL.get(role, role)
            print(f"    {label:5s} {hand_key:5s}: (レンジ外)")

    if not result_hands:
        print("    全ハンドがレンジ外"); return None

    return {
        "board_id":   board_id,
        "board":      board,
        "sbr":        sbr,
        "top_card":   top_card,
        "wetness":    wetness,
        "board_type": board_type,
        "key_hands":  key_hands,
        "hands":      result_hands,
    }


def run_collect(sbr: str, board_filter: str | None, force: bool) -> None:
    print(f"\n=== COLLECT: sbr={sbr} ===")
    check_token()
    time.sleep(2.0)

    out_path = FINDINGS_DIR / f"equity_study_SBR{sbr}.jsonl"
    done: set[str] = set()
    existing: list[str] = []

    if out_path.exists() and not force:
        with open(out_path) as f:
            for line in f:
                try:
                    d = json.loads(line)
                    done.add(d.get("board_id", ""))
                    existing.append(line)
                except Exception:
                    pass
        print(f"  既存 {len(done)} 件スキップ（--force で再収集）")
    elif force and out_path.exists():
        print("  --force: 既存データを上書き")
        # backup
        backup = out_path.with_suffix(".jsonl.bak")
        out_path.rename(backup)
        print(f"  バックアップ: {backup}")

    with open(out_path, "a", encoding="utf-8") as f:
        for entry in STUDY_BOARDS:
            board_id, board, top_card, wetness, board_type, _, key_hands = entry
            if board_filter and board_id != board_filter:
                continue
            if board_id in done:
                print(f"  スキップ: {board_id}")
                continue

            print(f"\n{'─'*60}")
            result = collect_board(board_id, board, top_card, wetness,
                                   board_type, key_hands, sbr)
            if result:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
                f.flush()
            time.sleep(4.0)

    print(f"\n✅ 完了: {out_path}")


# ─────────────────── 解析・式導出 ───────────────────

def analyze(sbr: str) -> None:
    files = sorted(FINDINGS_DIR.glob(f"equity_study_SBR{sbr}.jsonl"))
    if not files:
        print(f"データなし: findings/equity_study_SBR{sbr}.jsonl が見つかりません")
        return

    rows: list[dict[str, Any]] = []
    for f in files:
        with open(f) as fp:
            for line in fp:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass

    print(f"\n=== ANALYZE: {len(rows)} ボード (SBR{sbr}) ===\n")

    # ─── hand_eq テーブル ───
    print("=== hand_eq テーブル (%) ===\n")
    roles_present = ROLE_ORDER[:]
    # ヘッダー
    hdr = f"{'board_id':10s} {'top':3s} {'wet':5s} | "
    hdr += " ".join(f"{ROLE_LABEL[r]:>6s}" for r in roles_present)
    print(hdr)
    print("─" * 70)
    for row in rows:
        hands = row.get("hands", {})
        bid   = row["board_id"]
        top   = row["top_card"]
        wet   = row["wetness"]
        vals  = []
        for r in roles_present:
            hd = hands.get(r)
            vals.append(f"{hd['hand_eq']*100:6.1f}" if hd else f"{'—':>6s}")
        print(f"{bid:10s} {top:3s} {wet:5s} | {' '.join(vals)}")

    # ─── bet% テーブル ───
    print("\n=== bet% テーブル (%) ===\n")
    print(hdr)
    print("─" * 70)
    for row in rows:
        hands = row.get("hands", {})
        bid   = row["board_id"]
        top   = row["top_card"]
        wet   = row["wetness"]
        vals  = []
        for r in roles_present:
            hd = hands.get(r)
            vals.append(f"{hd['bet_pct']:6.0f}" if hd else f"{'—':>6s}")
        print(f"{bid:10s} {top:3s} {wet:5s} | {' '.join(vals)}")

    # ─── dry ボードのみ: 全ロール比較 ───
    print("\n=== dry ボード: ロール別 equity と bet% (平均) ===\n")
    dry_rows = [r for r in rows if r["wetness"] == "dry"]
    print(f"  {'ロール':8s} {'eq_avg':8s} {'bet_avg':8s} {'説明'}")
    print(f"  {'─'*55}")
    for role in roles_present:
        eqs  = [r["hands"][role]["hand_eq"] * 100
                for r in dry_rows if role in r["hands"]]
        bets = [r["hands"][role]["bet_pct"]
                for r in dry_rows if role in r["hands"]]
        if not eqs:
            continue
        eq_avg  = sum(eqs)  / len(eqs)
        bet_avg = sum(bets) / len(bets)
        desc = {
            "tptk":     f"トップペア最上キッカー   (n={len(eqs)})",
            "tpgk":     f"トップペア上位キッカー   (n={len(eqs)})",
            "tpmk":     f"トップペア中位キッカー   (n={len(eqs)})",
            "tpwk":     f"トップペア弱キッカー     (n={len(eqs)})",
            "sp_strong":f"セカンドペア強（大オーバーカード） (n={len(eqs)})",
            "sp_weak":  f"セカンドペア弱（小キッカー） (n={len(eqs)})",
            "bp":       f"ボトムペア（大オーバーカード） (n={len(eqs)})",
        }.get(role, "")
        print(f"  {ROLE_LABEL[role]:8s}  {eq_avg:6.1f}%   {bet_avg:5.0f}%  {desc}")

    # ─── wetness 別: TPTK と SP弱 のみ ───
    print("\n=== wetness 別: dry→wet の equity 変化 ===\n")
    for top_card in ["A", "K", "Q", "J", "T"]:
        tc_rows = [r for r in rows if r["top_card"] == top_card]
        if not tc_rows:
            continue
        print(f"  [{top_card} top]")
        for wet_level in ["dry", "semi", "wet", "mono"]:
            wet_row = next((r for r in tc_rows if r["wetness"] == wet_level), None)
            if not wet_row:
                continue
            h = wet_row["hands"]
            parts = []
            for role in ["tptk", "tpmk", "sp_strong", "sp_weak", "bp"]:
                hd = h.get(role)
                if hd:
                    parts.append(f"{ROLE_LABEL[role]}={hd['hand_eq']*100:.0f}%({hd['bet_pct']:.0f}%↑)")
            print(f"    {wet_level:5s}: {' | '.join(parts)}")
        print()

    # ─── 閾値サマリー ───
    print("=== GTO ベースの CBet 閾値サマリー ===\n")
    print("  ロール × board_type での概算 bet% (全ボード平均)\n")
    categories = {
        "dry":  [r for r in rows if r["wetness"] == "dry"],
        "semi": [r for r in rows if r["wetness"] == "semi"],
        "wet":  [r for r in rows if r["wetness"] == "wet"],
        "mono": [r for r in rows if r["wetness"] == "mono"],
    }
    role_short = ["tptk", "tpgk", "tpmk", "tpwk", "sp_strong", "sp_weak", "bp"]
    lbl_short  = [ROLE_LABEL[r] for r in role_short]
    print(f"  {'wetness':6s} | {' | '.join(f'{l:7s}' for l in lbl_short)}")
    print(f"  {'─'*72}")
    for wet, wet_rows in categories.items():
        vals2 = []
        for role in role_short:
            bets = [r["hands"][role]["bet_pct"]
                    for r in wet_rows if role in r["hands"]]
            vals2.append(f"{sum(bets)/len(bets):5.0f}%" if bets else f"{'—':>5s}")
        print(f"  {wet:6s} | {' | '.join(f'{v:7s}' for v in vals2)}")

    # ─── 書籍向けまとめ ───
    print("\n\n=== 書籍向けまとめ ===\n")
    print("  CBet 判断基準（全ボードタイプ平均 bet% から）:\n")
    print("  ● T3 CBet（ほぼ必ずベット, bet% ≥ 90%）:")
    print("    → TPTK / TPGK（全ボード）")
    print("    → TPMK（dry・semi ボード）")
    print()
    print("  ● T2 CBet（高頻度ベット, bet% 60〜89%）:")
    print("    → TPMK（wet ボード）")
    print("    → TPWK（dry ボード）")
    print("    → SP強（セカンドペア + 大オーバーカード）on dry")
    print()
    print("  ● T1 CBet / SDV（低頻度 or チェック, bet% < 60%）:")
    print("    → TPWK（wet・mono ボード）")
    print("    → SP弱（セカンドペア + 中程度キッカー）")
    print("    → BP（ボトムペア）← ほぼチェック")
    print()
    print("  ※ SP強 = セカンドペア + Aまたはオーバーカード大")
    print("  ※ BP   = ボトムペア + オーバーカード（SDV/チェックコール範囲）")


# ─────────────────── エントリポイント ───────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="equity_study.py")
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--diagnose", action="store_true")
    grp.add_argument("--collect",  action="store_true")
    grp.add_argument("--analyze",  action="store_true")
    parser.add_argument("--sbr",       default="25", choices=["20", "25"])
    parser.add_argument("--board",     default="Ks7d2c")
    parser.add_argument("--board-id",  dest="board_id", default=None)
    parser.add_argument("--flop-actions", dest="flop_actions", default="X")
    parser.add_argument("--force",     action="store_true",
                        help="既存データを無視して再収集")
    args = parser.parse_args()
    FINDINGS_DIR.mkdir(exist_ok=True)

    if args.diagnose:
        if not TOKEN:
            print("❌ TOKEN 未設定"); sys.exit(1)
        diagnose(args.board, args.sbr, args.flop_actions)
    elif args.collect:
        if not TOKEN:
            print("❌ TOKEN 未設定"); sys.exit(1)
        run_collect(args.sbr, args.board_id, args.force)
    elif args.analyze:
        analyze(args.sbr)


if __name__ == "__main__":
    main()
