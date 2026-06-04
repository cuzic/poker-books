#!/usr/bin/env python3
"""
draw_study.py — ストレートドロー・フラッシュドロー別 CBet 影響分析

【新API構造（2026-05-22 確認）】
  GTO Wizard API レスポンスは simple_hand_counters を使わず、以下を使う:
    - action_solutions[i].strategy       : 1326コンボの混合戦略 (per action)
    - action_solutions[i].hand_categories: 17種ハンドカテゴリの集計値
    - action_solutions[i].draw_categories: 8種ドローカテゴリの集計値
    - hand_categories_range              : 1326コンボの hand_category index
    - draw_categories_range              : 1326コンボの draw_category index

  これらを組み合わせて (hand × draw) クロス集計 bet% を計算する。

【ドローカテゴリ (GTO Wizard)】
  index 0  : no_draw
  index 16 : onecard_bdfd   ← 1枚フラッシュバックドア (手1枚+盤2枚=3枚)
  index 17 : twocards_bdfd  ← 2枚フラッシュバックドア (手2枚+盤1枚=3枚)
  index 1  : gutshot
  index 2  : oesd
  index 3  : flush_draw     ← フラッシュドロー (手2枚+盤2枚=4枚)
  index 12 : nut_flush_draw ← ナットフラッシュドロー
  index 4  : combo_draw     ← フラッシュ+ストレートドロー複合

【second_pair + flush_draw が成立する条件】
  ボード上の2色カードの「スーツ」と、ペアするボードカードの「スーツ」が異なる必要がある。
  例: Kd9c8d (K♦9♣8♦)
    - フラッシュスーツ: ♦ (K♦と8♦)
    - セカンドカード: 9♣ (クローバー = 非フラッシュスーツ)
    → 手札 J♦9♦: 9♦が9♣とペア(2ndP) + K♦8♦J♦9♦=4♦(FD) ✓

【調査ボード (rainbow + 同ランク2tone ペア)】
  K-9-8: Kd9s8c (rain) ↔ Kd9c8d (2tone、J♦9♦=2ndP+FD)
  T-9-8: Th9s8d (rain) ↔ Td9s8d (2tone、J♦9♦=2ndP+FD)
  K-7-2: Ks7d2c (rain) ↔ Kd7c2d (2tone、J♦7♦=2ndP+FD)
  Q-8-3: Qh8d3s (rain) ↔ Qd8c3d (2tone、J♦8♦=2ndP+FD)

使い方:
  TOKEN=... GWCLIENTID=... python3 draw_study.py --collect [--sbr 25] [--force]
  python3 draw_study.py --analyze [--sbr 25]
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

SBR_CONFIGS: dict[str, dict[str, Any]] = {
    "25": {"depth": 25.125, "pf": "F-F-F-F-F-R2.1-F-C", "stacks": ""},
    "20": {"depth": 20.125, "pf": "F-F-F-F-F-R2-F-C",   "stacks": ""},
    "15": {"depth": 15.125, "pf": "F-F-F-F-F-R2-F-C",   "stacks": ""},
}

# シナリオ定義: SRP/3BP × SBR
# 3BP の preflop_actions は --probe-pf で発見する必要がある
# 発見済み3BPサイズはここに手動で追記すること
SCENARIO_CONFIGS: dict[str, dict[str, Any]] = {
    # ── BTN vs BB (BTN=IP, BB=OOP) ──
    # flop_actions="X": BB checks → BTN の CBet 判断
    "SRP25":    {"depth": 25.125, "pf": "F-F-F-F-F-R2.1-F-C",  "stacks": "", "label": "SRP SBR25   BTN-BB",  "pos": "BTN_BB"},
    "SRP20":    {"depth": 20.125, "pf": "F-F-F-F-F-R2-F-C",    "stacks": "", "label": "SRP SBR20   BTN-BB",  "pos": "BTN_BB"},
    # probe-pf 確認済み: SBR20 R7=HTTP200、SBR25 R7-R9=HTTP204（GTO Wizard解なし）
    "3BP20":    {"depth": 20.125, "pf": "F-F-F-F-F-R2-F-R7-C", "stacks": "", "label": "3BP SBR20   BTN-BB",  "pos": "BTN_BB"},
    # ── SB vs BB (SB=OOP, BB=IP) ──
    # flop_actions="X": SB checks → BB の CBet 判断
    # probe-pf 確認済み: SBR25/20 R3=HTTP200
    "SRP25_SB": {"depth": 25.125, "pf": "F-F-F-F-F-F-R3-C",   "stacks": "", "label": "SRP SBR25   SB-BB",   "pos": "SB_BB"},
    "SRP20_SB": {"depth": 20.125, "pf": "F-F-F-F-F-F-R3-C",   "stacks": "", "label": "SRP SBR20   SB-BB",   "pos": "SB_BB"},
    # probe-pf 確認済み (2026-05-22): SBR25 R3-R8=HTTP200、SB open R3 → BB 3bet R8 → SB call
    "3BP25_SB": {"depth": 25.125, "pf": "F-F-F-F-F-F-R3-R8-C","stacks": "", "label": "3BP SBR25   SB-BB",   "pos": "SB_BB"},
    # probe-pf 確認済み (2026-05-22): CO vs BB は SBR20 の R2.0 のみ存在（SBR25 は204、HJ/UTG は全204）
    # GTO Wizard MTTGeneral は BTN/SB/CO(SBR20のみ) の限定ポジションしか解なし
    "SRP20_CO": {"depth": 20.125, "pf": "F-F-F-F-R2-F-F-C",  "stacks": "", "label": "SRP SBR20   CO-BB",   "pos": "CO_BB"},
    # probe-pf 確認済み (2026-05-22): BTN vs SB (SBコールドコール、BBフォールド)
    "SRP25_SB_cc": {"depth": 25.125, "pf": "F-F-F-F-F-R2.1-C-F","stacks": "", "label": "SRP SBR25   BTN-SB(cc)","pos": "BTN_SB"},
    "SRP20_SB_cc": {"depth": 20.125, "pf": "F-F-F-F-F-R2-C-F",  "stacks": "", "label": "SRP SBR20   BTN-SB(cc)","pos": "BTN_SB"},
    # probe-pf 確認済み (2026-05-22): SBリンプ → BBチェック (リンプポット)
    # preflop: 6F + C(SB limp) + X(BB option) → flop: SB acts first (X), BB IP
    "LIMP25_SB": {"depth": 25.125, "pf": "F-F-F-F-F-F-C-X",  "stacks": "", "label": "LIMP SBR25  SB-BB",   "pos": "SB_BB"},
    "LIMP20_SB": {"depth": 20.125, "pf": "F-F-F-F-F-F-C-X",  "stacks": "", "label": "LIMP SBR20  SB-BB",   "pos": "SB_BB"},
    # SBR15: HTTP 403（サブスクリプション対象外）
    # multiway (3-way以上): GTO Wizard MTTGeneral に解なし (全204確認済み 2026-05-22)
}

# ─────────────────── 調査ボード定義 ───────────────────
# (board_id, board, label, group, note)
# group: 同一ランク・異スーツのペアを同一グループに
# note: FD 成立条件の説明
STUDY_BOARDS: list[dict[str, str]] = [
    # ─── K-9-8: セカンドペア(9)とFD ───
    # Kd9s8c: レインボー → FDなし (all bdfd)
    # Kd9c8d: 2トーン(K♦8♦ FD, 9♣非FD) → J♦9♦=2ndP+FD
    {
        "board_id": "K98_rain", "board": "Kd9s8c", "group": "K98",
        "label": "K-9-8 レインボー (baseline)",
        "fd": "none",
        "fd_note": "全スーツ異なる→FDなし",
    },
    {
        "board_id": "K98_fd",   "board": "Kd9c8d", "group": "K98",
        "label": "K-9-8 2tone K♦8♦ (9♣は非FD)",
        "fd": "d",
        "fd_note": "J♦+9♦+K♦+8♦=4♦→FD。9♣ブロックなし",
    },
    # ─── T-9-8: OESD豊富なボードにFD追加 ───
    # Th9s8d: レインボー → OESD多数・FDなし
    # Td9s8d: 2トーン(T♦8♦ FD, 9♠非FD) → J♦9♦=2ndP+FD+OESD
    {
        "board_id": "T98_rain", "board": "Th9s8d", "group": "T98",
        "label": "T-9-8 レインボー (baseline)",
        "fd": "none",
        "fd_note": "全スーツ異なる→FDなし",
    },
    {
        "board_id": "T98_fd",   "board": "Td9s8d", "group": "T98",
        "label": "T-9-8 2tone T♦8♦ (9♠は非FD)",
        "fd": "d",
        "fd_note": "J♦+9♦+T♦+8♦=4♦→FD+OESD。9♠ブロックなし",
    },
    # ─── K-7-2: ドライボード × FD ───
    # Ks7d2c: レインボー乾燥ボード
    # Kd7c2d: 2トーン(K♦2♦ FD, 7♣非FD) → J♦7♦=2ndP+FD
    {
        "board_id": "K72_rain", "board": "Ks7d2c", "group": "K72",
        "label": "K-7-2 レインボー ドライ (baseline)",
        "fd": "none",
        "fd_note": "全スーツ異なる→FDなし",
    },
    {
        "board_id": "K72_fd",   "board": "Kd7c2d", "group": "K72",
        "label": "K-7-2 2tone K♦2♦ (7♣は非FD)",
        "fd": "d",
        "fd_note": "J♦+7♦+K♦+2♦=4♦→FD。7♣ブロックなし",
    },
    # ─── Q-8-3: ハイセミ × FD ───
    # Qh8d3s: 型2_ハイウェット (mtt_flop_cbet 標準ボード)
    # Qd8c3d: 2トーン(Q♦3♦ FD, 8♣非FD) → J♦8♦=2ndP+FD
    {
        "board_id": "Q83_rain", "board": "Qh8d3s", "group": "Q83",
        "label": "Q-8-3 レインボー (baseline)",
        "fd": "none",
        "fd_note": "全スーツ異なる→FDなし",
    },
    {
        "board_id": "Q83_fd",   "board": "Qd8c3d", "group": "Q83",
        "label": "Q-8-3 2tone Q♦3♦ (8♣は非FD)",
        "fd": "d",
        "fd_note": "J♦+8♦+Q♦+3♦=4♦→FD。8♣ブロックなし",
    },
    # ─── J-7-3: ミッドドライ、ストレートなし ───
    # J♥7♦3♠: レインボー。セカンドペア=7x。ドローなしで "typical mid-dry" 代表
    # J♦7♣3♦: 2トーン J♦3♦ (7♣非FD) → 9♦7♦=2ndP+FD
    {
        "board_id": "J73_rain", "board": "Jh7d3s", "group": "J73",
        "label": "J-7-3 レインボー ミッドドライ (baseline)",
        "fd": "none",
        "fd_note": "全スーツ異なる→FDなし",
    },
    {
        "board_id": "J73_fd",   "board": "Jd7c3d", "group": "J73",
        "label": "J-7-3 2tone J♦3♦ (7♣は非FD)",
        "fd": "d",
        "fd_note": "9♦+7♦+J♦+3♦=4♦→FD。7♣ブロックなし",
    },
    # ─── A-9-4: エース高セミドライ ───
    # A♥9♦4♠: エース高レインボー。セカンドペア=9x。Kは消えるがA高が支配的
    # A♦9♣4♦: 2トーン A♦4♦ (9♣非FD) → J♦9♦=2ndP+FD
    {
        "board_id": "A94_rain", "board": "Ah9d4s", "group": "A94",
        "label": "A-9-4 レインボー エース高 (baseline)",
        "fd": "none",
        "fd_note": "全スーツ異なる→FDなし",
    },
    {
        "board_id": "A94_fd",   "board": "Ad9c4d", "group": "A94",
        "label": "A-9-4 2tone A♦4♦ (9♣は非FD)",
        "fd": "d",
        "fd_note": "J♦+9♦+A♦+4♦=4♦→FD。9♣ブロックなし",
    },
    # ─── 7-6-5: ローウェット、OESDとFD多数 ───
    # 7♥6♦5♠: ローレインボー超ウェット。セカンドペア=6x(または5x)
    # 7♦6♣5♦: 2トーン 7♦5♦ (6♣非FD) → 9♦6♦=2ndP+FD+OESD or similar
    {
        "board_id": "765_rain", "board": "7h6d5s", "group": "765",
        "label": "7-6-5 レインボー ローウェット (baseline)",
        "fd": "none",
        "fd_note": "全スーツ異なる→FDなし",
    },
    {
        "board_id": "765_fd",   "board": "7d6c5d", "group": "765",
        "label": "7-6-5 2tone 7♦5♦ (6♣は非FD)",
        "fd": "d",
        "fd_note": "9♦+6♦+7♦+5♦=4♦→FD+OESD。6♣ブロックなし",
    },

    # ═══════════════════════════════════════════════════════
    # pairwise 拡張ボード（型3/型5/型7/型1亜種/ローdry）
    # ═══════════════════════════════════════════════════════

    # ─── K-J-T: 型3 高ウェット OESD ───
    # K♥J♦T♠: ストレートドロー豊富。セカンドペア=Jx (J♦がペア対象)
    # K♦J♣T♦: 2tone K♦T♦ (J♣非FD) → Q♦J♦=2ndP(J♦-J♣)+FD(Q♦J♦K♦T♦=4♦) ✓
    {
        "board_id": "KJT_rain", "board": "KhJdTs", "group": "KJT",
        "label": "K-J-T レインボー 型3高ウェット (baseline)",
        "fd": "none",
        "fd_note": "全スーツ異なる→FDなし",
    },
    {
        "board_id": "KJT_fd",   "board": "KdJcTd", "group": "KJT",
        "label": "K-J-T 2tone K♦T♦ (J♣は非FD)",
        "fd": "d",
        "fd_note": "Q♦+J♦+K♦+T♦=4♦→FD+OESD。J♣ブロックなし",
    },

    # ─── T-7-4: 型5 ミッド断絶 ───
    # T♥7♦4♠: 中間カード・断絶。セカンドペア=7x
    # T♦7♣4♦: 2tone T♦4♦ (7♣非FD) → J♦7♦=2ndP(7♦-7♣)+FD(J♦7♦T♦4♦=4♦) ✓
    {
        "board_id": "T74_rain", "board": "Th7d4s", "group": "T74",
        "label": "T-7-4 レインボー 型5ミッド断絶 (baseline)",
        "fd": "none",
        "fd_note": "全スーツ異なる→FDなし",
    },
    {
        "board_id": "T74_fd",   "board": "Td7c4d", "group": "T74",
        "label": "T-7-4 2tone T♦4♦ (7♣は非FD)",
        "fd": "d",
        "fd_note": "J♦+7♦+T♦+4♦=4♦→FD。7♣ブロックなし",
    },

    # ─── A-7-2: 型1亜種 エース高ドライ ───
    # A♥7♦2♠: エース高・最大断絶。セカンドペア=7x
    # A♦7♣2♦: 2tone A♦2♦ (7♣非FD) → J♦7♦=2ndP(7♦-7♣)+FD(J♦7♦A♦2♦=4♦) ✓
    # ※A94(セミ)と対比してドライエース高の特性を確認
    {
        "board_id": "A72_rain", "board": "Ah7d2s", "group": "A72",
        "label": "A-7-2 レインボー 型1エース高ドライ (baseline)",
        "fd": "none",
        "fd_note": "全スーツ異なる→FDなし",
    },
    {
        "board_id": "A72_fd",   "board": "Ad7c2d", "group": "A72",
        "label": "A-7-2 2tone A♦2♦ (7♣は非FD)",
        "fd": "d",
        "fd_note": "J♦+7♦+A♦+2♦=4♦→FD。7♣ブロックなし",
    },

    # ─── 7-4-2: ローdry、ストレートなし ───
    # 7♥4♦2♠: 低カード・完全断絶。セカンドペア=4x。BTNレンジに弱い
    # 7♦4♣2♦: 2tone 7♦2♦ (4♣非FD) → J♦4♦=2ndP(4♦-4♣)+FD(J♦4♦7♦2♦=4♦) ✓
    {
        "board_id": "742_rain", "board": "7h4d2s", "group": "742",
        "label": "7-4-2 レインボー ローdry (baseline)",
        "fd": "none",
        "fd_note": "全スーツ異なる→FDなし",
    },
    {
        "board_id": "742_fd",   "board": "7d4c2d", "group": "742",
        "label": "7-4-2 2tone 7♦2♦ (4♣は非FD)",
        "fd": "d",
        "fd_note": "J♦+4♦+7♦+2♦=4♦→FD。4♣ブロックなし",
    },

    # ─── K-K-8: 型7 ペアボード ───
    # K♥K♦8♣: ペアボード。トップ=K(トリップス or 2P)、セカンドペア=8x
    # FD不可: ペアボードで2枚K+1枚8、フラッシュドロー設計が複雑
    # → rainbowのみ調査し、ドロー分類がペアボードでどう変わるか確認
    {
        "board_id": "KK8_rain", "board": "KhKd8c", "group": "KK8",
        "label": "K-K-8 ペアボード 型7 (rain only)",
        "fd": "none",
        "fd_note": "ペアボードのためFD版は複雑→rainbowのみ",
    },

    # ─── A-A-7: 型7 エースペアボード ───
    {
        "board_id": "AA7_rain", "board": "AhAd7c", "group": "AA7",
        "label": "A-A-7 エースペアボード 型7 (rain only)",
        "fd": "none",
        "fd_note": "ペアボードのためFD版は複雑→rainbowのみ",
    },
]

# 表示対象のカテゴリ
FOCUS_HANDS = ["top_pair", "second_pair", "third_pair", "low_pair",
               "underpair", "two_pair", "set", "no_made_hand", "ace_high", "king_high"]
FOCUS_DRAWS = ["flush_draw", "nut_flush_draw", "combo_draw",
               "oesd", "gutshot", "twocards_bdfd", "onecard_bdfd", "no_draw"]

DRAW_LABEL = {
    "flush_draw":    "FD(2枚)",
    "nut_flush_draw":"ナットFD",
    "combo_draw":    "FD+SD複合",
    "oesd":          "OESD",
    "gutshot":       "ガット",
    "twocards_bdfd": "バックFD2",
    "onecard_bdfd":  "バックFD1",
    "no_draw":       "ドローなし",
}
HAND_LABEL = {
    "top_pair":    "トップP",
    "second_pair": "2ndP",
    "third_pair":  "3rdP",
    "low_pair":    "ロウP",
    "underpair":   "アンダーP",
    "two_pair":    "ツーP",
    "set":         "セット",
    "no_made_hand":"メイドなし",
    "ace_high":    "A高",
    "king_high":   "K高",
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


def check_auth() -> bool:
    import time as _t
    try:
        import base64 as _b64
        payload = TOKEN.split(".")[1] + "=="
        data = json.loads(_b64.b64decode(payload))
        exp = data.get("exp", 0)
        remaining = exp - _t.time()
        if remaining < 60:
            print(f"⚠️  トークン期限切れ (残り {remaining:.0f}秒)")
            return False
        print(f"✅ 認証OK（残り{remaining/60:.1f}分）")
        return True
    except Exception:
        print("⚠️  トークン検証失敗（続行）")
        return True


def call_api(board: str, depth: float = 25.125,
             pf: str = "F-F-F-F-F-R2.1-F-C", stacks: str = "") -> dict[str, Any] | None:
    params: dict[str, Any] = {
        "gametype": GT, "depth": str(depth), "stacks": stacks,
        "preflop_actions": pf, "flop_actions": "X",  # BBチェック後のIP決断
        "turn_actions": "", "river_actions": "", "board": board,
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


def compute_cross(data: dict) -> dict[str, Any]:
    """
    API レスポンスから (hand × draw) bet% クロス集計を計算する。

    戻り値:
      {
        "cross": {(hand_name, draw_name): [bet_freq, ...]},
        "draw_agg": {draw_name: {"total":x, "bet":y}},   # ドロー別集計
        "hand_agg": {hand_name: {"total":x, "bet":y}},   # ハンド別集計
        "draw_map": {index: name},
        "hand_map": {index: name},
        "n_combos": int,
      }
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

    bet_codes  = [c for c in strategies if c != "X"]
    cross: dict[tuple, list] = defaultdict(list)
    draw_agg: dict[str, dict] = defaultdict(lambda: {"total": 0.0, "bet": 0.0})
    hand_agg: dict[str, dict] = defaultdict(lambda: {"total": 0.0, "bet": 0.0})
    n_in_range = 0

    for i in range(min(1326, len(dcr), len(hcr))):
        # range 内コンボの判定: 全策略の和 > 0
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
        "draw_map": {str(k): v for k, v in draw_map.items()},
        "hand_map": {str(k): v for k, v in hand_map.items()},
        "n_combos": n_in_range,
    }


# ─────────────────── 収集 ───────────────────

def collect_scenario(scenario_key: str, cfg: dict[str, Any],
                      force: bool, group_filter: str | None = None) -> None:
    outf = FINDINGS_DIR / f"draw_study_{scenario_key}.jsonl"
    FINDINGS_DIR.mkdir(exist_ok=True)

    existing: dict[str, Any] = {}
    if outf.exists() and not force:
        for line in outf.read_text().splitlines():
            if line.strip():
                rec = json.loads(line)
                if "cross" in rec:
                    existing[rec["board_id"]] = rec

    if not check_auth():
        sys.exit(1)

    if force and outf.exists():
        bak = outf.with_suffix(".jsonl.bak")
        outf.rename(bak)
        print(f"  --force: バックアップ → {bak}")

    label = cfg.get("label", scenario_key)
    print(f"\n=== COLLECT: {label} ===\n")
    results: list[dict] = list(existing.values())

    for bcfg in STUDY_BOARDS:
        bid = bcfg["board_id"]
        if group_filter and bcfg["group"] != group_filter.upper():
            continue
        if bid in existing:
            print(f"  [{bid}] ⏭  スキップ（既存）")
            continue

        board = bcfg["board"]
        print(f"\n  [{bid}] {board} — {bcfg['label']}")
        data = call_api(board, depth=cfg["depth"], pf=cfg["pf"], stacks=cfg.get("stacks",""))
        if data is None or "action_solutions" not in data:
            print(f"    ❌ API失敗またはデータなし")
            continue

        crs = compute_cross(data)
        print(f"    in-range combos: {crs['n_combos']}")

        for dname in FOCUS_DRAWS:
            da = crs["draw_agg"].get(dname)
            if da and da["total"] > 0.5:
                print(f"    {DRAW_LABEL.get(dname, dname):12s}: n={da['total']:5.0f}  bet%={da['bet_pct']:4.0f}%")

        rec = {
            "board_id": bid, "group": bcfg["group"],
            "board":    board, "label": bcfg["label"],
            "fd_suit":  bcfg["fd"], "fd_note": bcfg.get("fd_note",""),
            "scenario": scenario_key,
            "cross":    crs["cross"],
            "draw_agg": crs["draw_agg"],
            "hand_agg": crs["hand_agg"],
            "n_combos": crs["n_combos"],
        }
        results.append(rec)

        with outf.open("a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        time.sleep(1.5)

    if force:
        with outf.open("w") as f:
            for rec in results:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def collect(sbr: str, force: bool, group_filter: str | None = None) -> None:
    """旧互換: --sbr フラグ用ラッパー。"""
    cfg = SBR_CONFIGS[sbr]
    collect_scenario(f"SRP{sbr}", cfg, force, group_filter)


# ─────────────────── 分析 ───────────────────

def fmt_cell(data: dict, hname: str, dname: str) -> str:
    key = f"{hname}|{dname}"
    c = data["cross"].get(key)
    if not c or c["n"] < 2:
        return "  — "
    return f"{c['avg']:3.0f}%"


def analyze(scenario_key: str) -> None:
    # 旧形式 (SBR25) と新形式 (SRP25) の両方を試みる
    inpf = FINDINGS_DIR / f"draw_study_{scenario_key}.jsonl"
    if not inpf.exists():
        # 旧互換: "SRP25" → "SBR25"
        alt = FINDINGS_DIR / f"draw_study_SBR{scenario_key.replace('SRP','')}.jsonl"
        if alt.exists():
            inpf = alt
        else:
            print(f"❌ データなし: {inpf}")
            return

    boards: dict[str, dict] = {}
    for line in inpf.read_text().splitlines():
        if line.strip():
            rec = json.loads(line)
            if "cross" in rec:  # 新API形式のみ
                boards[rec["board_id"]] = rec

    print(f"\n{'═'*80}")
    print(f"  DRAW STUDY 分析 ({scenario_key})")
    print(f"  API: hand × draw カテゴリ別 bet% クロス集計")
    print(f"{'═'*80}")

    # ─── グループ別比較 ───
    groups: dict[str, list[str]] = defaultdict(list)
    for bid, rec in boards.items():
        groups[rec["group"]].append(bid)

    for grp, bid_list in sorted(groups.items()):
        print(f"\n{'─'*80}")
        print(f"  Group {grp}:")
        for bid in bid_list:
            rec = boards.get(bid, {})
            print(f"    [{bid}] {rec.get('board','?')} — {rec.get('label','?')}")
        print()

        # ドロータイプ別 bet% (各ボード)
        print(f"  [draw_agg: ドロー別 bet%]")
        hdr = f"  {'ドロー':10s} " + "  ".join(f"{bid[:12]:>12s}" for bid in bid_list)
        print(hdr)
        for dname in FOCUS_DRAWS:
            row = f"  {DRAW_LABEL.get(dname, dname):10s} "
            any_data = False
            for bid in bid_list:
                rec = boards.get(bid, {})
                da = rec.get("draw_agg", {}).get(dname)
                if da and da["total"] > 0.5:
                    row += f"  {da['bet_pct']:4.0f}%(n{da['total']:5.0f})"
                    any_data = True
                else:
                    row += f"       —      "
            if any_data:
                print(row)

        # hand × draw クロス集計（rainbowボードと2toneボードを並べる）
        rain_bids = [b for b in bid_list if boards.get(b, {}).get("fd_suit") is None or boards.get(b, {}).get("fd_suit") == "none"]
        fd_bids   = [b for b in bid_list if boards.get(b, {}).get("fd_suit") not in (None, "none")]

        if rain_bids and fd_bids:
            rain_rec = boards.get(rain_bids[0], {})
            fd_rec   = boards.get(fd_bids[0], {})

            print(f"\n  [hand × draw クロス集計 bet%]")
            print(f"  ← {rain_bids[0]}: {rain_rec.get('board','?')} (rain)")
            print(f"  → {fd_bids[0]}  : {fd_rec.get('board','?')} (2tone FD)")
            print()

            # ヘッダー
            dnames_short = [DRAW_LABEL.get(d, d[:8]) for d in FOCUS_DRAWS]
            print(f"  {'hand':10s} " + "".join(f"  {d:^9s}" for d in dnames_short))
            print(f"  {'-'*10} " + "-" * (11 * len(FOCUS_DRAWS)))

            for hname in FOCUS_HANDS:
                h_lbl = HAND_LABEL.get(hname, hname)
                # rain の行
                rain_row = f"  {h_lbl+'(r)':10s} "
                fd_row   = f"  {h_lbl+'(fd)':10s} "
                any_r = any_f = False
                for dname in FOCUS_DRAWS:
                    rc = fmt_cell(rain_rec, hname, dname)
                    fc = fmt_cell(fd_rec,  hname, dname)
                    rain_row += f"  {rc:>7s}  "
                    fd_row   += f"  {fc:>7s}  "
                    if rc.strip() and rc.strip() != "—": any_r = True
                    if fc.strip() and fc.strip() != "—": any_f = True
                if any_r or any_f:
                    if any_r: print(rain_row)
                    if any_f: print(fd_row)
                    if any_r and any_f:
                        # Δ行
                        delta_row = f"  {'Δ(fd-r)':10s} "
                        for dname in FOCUS_DRAWS:
                            key = f"{hname}|{dname}"
                            rc = rain_rec.get("cross", {}).get(key)
                            fc = fd_rec.get("cross",  {}).get(key)
                            if rc and fc and rc["n"] >= 2 and fc["n"] >= 2:
                                delta = fc["avg"] - rc["avg"]
                                sign  = "+" if delta >= 0 else ""
                                delta_row += f"  {sign}{delta:3.0f}%    "
                            else:
                                delta_row += f"    —      "
                        print(delta_row)
                    print()

    # ─── 総括 ───
    print(f"\n{'═'*80}")
    print("  FD効果 総括 (second_pair に限定)")
    print(f"{'═'*80}\n")

    print(f"  {'ボード':12s} {'FD設定':8s} | "
          + "  ".join(f"{DRAW_LABEL.get(d,''):>9s}" for d in FOCUS_DRAWS))
    print(f"  {'-'*12} {'-'*8}-" + "-" * (11 * len(FOCUS_DRAWS)))

    for bid, rec in sorted(boards.items()):
        fd = "2tone" if rec.get("fd_suit") not in (None, "none") else "rain"
        row = f"  {bid:12s} {fd:8s} | "
        any_d = False
        for dname in FOCUS_DRAWS:
            c = rec.get("cross", {}).get(f"second_pair|{dname}")
            if c and c["n"] >= 2:
                row += f"  {c['avg']:4.0f}%(n{c['n']:2d})"
                any_d = True
            else:
                row += f"      —    "
        if any_d:
            print(row)

    print(f"\n  読み方: FD(2枚)列に値があれば、2ndP + フラッシュドロー の bet% を示す")
    print(f"  比較: 同グループの rain vs 2tone で same draw type の差 = FD追加効果")


# ─────────────────── メイン ───────────────────

def probe_pf() -> None:
    """3BP や SBR15 の preflop_actions を各 depth で試して有効なサイズを発見する。"""
    if not check_auth():
        sys.exit(1)

    test_board = "Kd9s8c"

    # (label, depth, pf_string, flop_actions)
    # 9-player action order: UTG(1) UTG+1(2) UTG+2(3) HJ(4) CO(5) BTN(6) SB(7) BB(8) [re-act]
    # multiway flop_actions: 複数 OOP が check する場合は "X-X" か "X" か不明 → 両方試す
    candidates = [
        # ── 確認済み ──
        ("SRP25_BTN ✓",        25.125, "F-F-F-F-F-R2.1-F-C",   "X"),
        ("SRP20_CO_R2.0 ✓",    20.125, "F-F-F-F-R2-F-F-C",     "X"),

        # ── multiway: BTN opens, SB calls, BB calls ──
        # preflop: 5F + R2.1(BTN) + C(SB) + C(BB) = 3-way
        # flop order: SB(OOP1) → BB(OOP2) → BTN(IP)
        # flop_actions で SB と BB がどちらも check するには "X-X" or "X" ?
        ("3WAY_BTN_SBBB_25_XX",  25.125, "F-F-F-F-F-R2.1-C-C",  "X-X"),
        ("3WAY_BTN_SBBB_25_X",   25.125, "F-F-F-F-F-R2.1-C-C",  "X"),
        ("3WAY_BTN_SBBB_20_XX",  20.125, "F-F-F-F-F-R2-C-C",    "X-X"),
        ("3WAY_BTN_SBBB_20_X",   20.125, "F-F-F-F-F-R2-C-C",    "X"),

        # ── multiway: BTN opens, BB calls (SB folds), then SB calls?
        #    → 違う。SRP は BTN open + 1 caller でも multiway にはならない
        # ── multiway: CO opens, BTN calls, BB calls ──
        # preflop: 4F + R2(CO) + C(BTN) + F(SB) + C(BB) = 3-way CO/BTN/BB
        # flop order: BB(OOP) → CO(OOP2?) → BTN(IP)? or CO/BB relative position?
        # CO と BB はどちらが先に act?  BB が CO の left なので BB→CO→BTN? 要確認
        ("3WAY_CO_BTN_BB_25_XX", 25.125, "F-F-F-F-R2-C-F-C",   "X-X"),
        ("3WAY_CO_BTN_BB_25_X",  25.125, "F-F-F-F-R2-C-F-C",   "X"),
        ("3WAY_CO_BTN_BB_20_XX", 20.125, "F-F-F-F-R2-C-F-C",   "X-X"),
        ("3WAY_CO_BTN_BB_20_X",  20.125, "F-F-F-F-R2-C-F-C",   "X"),

        # ── multiway: SB opens, BTN calls, BB calls → 3-way ──
        # preflop: 6F + R3(SB) + C(BB) ... wait BBはSBのleftではない。
        # SB open → BB call → BTN? → BTN はもう fold 済みなので BTN は関係ない
        # Actually: 6F + R3(SB) → BB can 3bet or call → if BB calls, HU not 3-way
        # 3-way SB open: needs BTN to also call → F-F-F-F-F-C(BTN)-R3(SB)-C(BB)? No...
        # 別パターン: CO opens, SB calls, BB calls
        ("3WAY_CO_SB_BB_25_XX",  25.125, "F-F-F-F-R2-F-C-C",   "X-X"),
        ("3WAY_CO_SB_BB_25_X",   25.125, "F-F-F-F-R2-F-C-C",   "X"),
        ("3WAY_CO_SB_BB_20_XX",  20.125, "F-F-F-F-R2-F-C-C",   "X-X"),

        # ── multiway: BTN opens, BB calls, SB calls (SB cold-calls) ──
        # BTN open → SB cold-call → BB also calls
        # preflop: F-F-F-F-F-R2.1(BTN)-C(SB)-C(BB) same as 3WAY_BTN_SBBB above? Yes
        # (SBが先に act するので同じ文字列)

        # ── limp pot: SB limp + BB check ──
        ("LIMP_SB_BB_25",        25.125, "F-F-F-F-F-F-C-X",    "X"),  # SB limp, BB check
        ("LIMP_SB_BB_20",        20.125, "F-F-F-F-F-F-C-X",    "X"),

        # ── BTN opens, SB calls のみ (HU だが SB=OOP まれなケース) ──
        ("HU_BTN_SB_25",         25.125, "F-F-F-F-F-R2.1-C-F", "X"),
        ("HU_BTN_SB_20",         20.125, "F-F-F-F-F-R2-C-F",   "X"),
    ]

    print(f"\n=== probe-pf: board={test_board} ===\n")
    for label, depth, pf, flop_act in candidates:
        params: dict[str, Any] = {
            "gametype": GT, "depth": str(depth), "stacks": "",
            "preflop_actions": pf, "flop_actions": flop_act,
            "turn_actions": "", "river_actions": "", "board": test_board,
        }
        r = requests.get(BASE_URL, params=params, headers=make_headers(), timeout=30)
        if r.status_code == 200:
            data = r.json()
            n_actions = len(data.get("action_solutions", []))
            print(f"  ✅ {label}: HTTP 200  actions={n_actions}  flop={flop_act}  pf={pf}")
        else:
            print(f"  ❌ {label}: HTTP {r.status_code}  flop={flop_act}  pf={pf}")
        time.sleep(0.5)


def compare_scenarios(scenario_list: list[str]) -> None:
    """複数シナリオをロードし、second_pair bet% の SPR/preflop比較表を出力する。"""
    print(f"\n{'═'*80}")
    print(f"  シナリオ比較: second_pair bet% (ドローなし / FD / OESD)")
    print(f"  シナリオ: {' vs '.join(scenario_list)}")
    print(f"{'═'*80}\n")

    # Load all scenario data
    all_data: dict[str, dict[str, dict]] = {}  # scenario → board_id → rec
    for scen in scenario_list:
        fpath = FINDINGS_DIR / f"draw_study_{scen}.jsonl"
        if not fpath.exists():
            print(f"  ⚠ データなし: {fpath} (collect --scenario {scen} を先に実行)")
            continue
        boards: dict[str, dict] = {}
        for line in fpath.read_text().splitlines():
            if line.strip():
                rec = json.loads(line)
                if "cross" in rec:
                    boards[rec["board_id"]] = rec
        all_data[scen] = boards
        print(f"  ロード完了: {scen} ({len(boards)} boards)")

    if not all_data:
        return

    # Print comparison for each board group
    # Rows: board × draw_type, Cols: scenarios
    target_hands  = ["second_pair", "third_pair"]
    target_draws  = ["no_draw", "flush_draw", "combo_draw", "oesd", "gutshot"]

    for bid_pair in [
        ("K98_rain","K98_fd"), ("T98_rain","T98_fd"),
        ("K72_rain","K72_fd"), ("Q83_rain","Q83_fd"),
        ("J73_rain","J73_fd"), ("A94_rain","A94_fd"), ("765_rain","765_fd"),
        ("KJT_rain","KJT_fd"), ("T74_rain","T74_fd"),
        ("A72_rain","A72_fd"), ("742_rain","742_fd"),
        ("KK8_rain",None),     ("AA7_rain",None),
    ]:
        rain_id, fd_id = bid_pair
        header_label = f"{rain_id} / {fd_id}" if fd_id else rain_id
        print(f"\n  ── {header_label} ──")
        header = f"  {'hand+draw':25s}"
        for sc in scenario_list:
            header += f"  {sc:>10s}"
        print(header)
        print(f"  {'-'*25}" + f"  {'-'*10}" * len(scenario_list))

        for hname in target_hands:
            for dname in target_draws:
                key = f"{hname}|{dname}"
                row = f"  {HAND_LABEL.get(hname,hname)+'(r) '+DRAW_LABEL.get(dname,dname):25s}"
                any_val = False
                for sc in scenario_list:
                    boards = all_data.get(sc, {})
                    rec = boards.get(rain_id, {})
                    c = rec.get("cross", {}).get(key)
                    if c and c["n"] >= 2:
                        row += f"  {c['avg']:5.0f}%(n{c['n']:2d})"
                        any_val = True
                    else:
                        row += f"       —      "
                if any_val:
                    print(row)

            # FD version
            if fd_id:
                for dname in ["flush_draw", "combo_draw"]:
                    key = f"{hname}|{dname}"
                    row = f"  {HAND_LABEL.get(hname,hname)+'(fd) '+DRAW_LABEL.get(dname,dname):25s}"
                    any_val = False
                    for sc in scenario_list:
                        boards = all_data.get(sc, {})
                        rec = boards.get(fd_id, {})
                        c = rec.get("cross", {}).get(key)
                        if c and c["n"] >= 2:
                            row += f"  {c['avg']:5.0f}%(n{c['n']:2d})"
                            any_val = True
                        else:
                            row += f"       —      "
                    if any_val:
                        print(row)


def main() -> None:
    ap = argparse.ArgumentParser(description="draw_study.py: ドロー別 CBet 影響分析")
    ap.add_argument("--collect",   action="store_true", help="GTO Wizardからデータ収集")
    ap.add_argument("--analyze",   action="store_true", help="シナリオ内分析")
    ap.add_argument("--compare",   action="store_true", help="複数シナリオ比較")
    ap.add_argument("--probe-pf",  action="store_true", dest="probe_pf",
                    help="3BP/SBR15 preflop_actions を probe して有効なサイズを発見")
    ap.add_argument("--sbr",      default="25", choices=["15", "20", "25"],
                    help="SBR レベル (--collect / --analyze 用。旧互換)")
    ap.add_argument("--scenario",  default=None,
                    choices=list(SCENARIO_CONFIGS.keys()),
                    help="シナリオ指定 (SRP25/SRP20/3BP20/SRP25_SB/SRP20_SB)")
    ap.add_argument("--scenarios", default=None, nargs="+",
                    help="--compare 対象のシナリオリスト (例: SRP25 SRP20 SRP15)")
    ap.add_argument("--force",     action="store_true")
    ap.add_argument("--group",     default=None,
                    help="グループ絞り込み (例: K98, T98, K72, Q83, J73, A94, 765)")
    args = ap.parse_args()

    if args.probe_pf:
        probe_pf()
    elif args.compare:
        sc_list = args.scenarios or ["SRP25", "SRP20", "SRP15"]
        compare_scenarios(sc_list)
    elif args.collect:
        # --scenario 優先、なければ --sbr 互換
        if args.scenario:
            cfg = SCENARIO_CONFIGS[args.scenario]
            out_key = args.scenario
        else:
            cfg = SBR_CONFIGS[args.sbr]
            out_key = f"SRP{args.sbr}"
        collect_scenario(out_key, cfg, args.force, args.group)
    elif args.analyze:
        if args.scenario:
            analyze(args.scenario)
        else:
            analyze(f"SRP{args.sbr}")
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
