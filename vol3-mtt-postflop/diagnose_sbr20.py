#!/usr/bin/env python3
"""
SBR20 診断スクリプト
- 各 preflop_actions バリアントで depth=20.125 を試す
- total_frequency が正しく取得できるバリアントを特定する

使い方:
  TOKEN=eyJ... GWCLIENTID=xxx python3 diagnose_sbr20.py
"""

import os, sys, json, time, requests
from pathlib import Path

TOKEN      = os.environ.get("TOKEN", "")
GWCLIENTID = os.environ.get("GWCLIENTID", "")

BASE_URL = "https://api.gtowizard.com/v4/solutions/spot-solution/"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "authorization": f"Bearer {TOKEN}",
    "gwclientid": GWCLIENTID,
    "origin": "https://app.gtowizard.com",
    "referer": "https://app.gtowizard.com/",
}

# テストするプリフロップアクションのバリアント
PF_VARIANTS = [
    ("R2.0-F-C-as-4p",    "F-F-F-F-F-R2-F-C"),       # 現在の設定
    ("R2.1-like-SBR25",   "F-F-F-F-F-R2.1-F-C"),     # SBR25と同じ
    ("R2.5-wider",        "F-F-F-F-F-R2.5-F-C"),     # SBR40の設定
    ("R2.0-6player",      "F-F-F-R2-F-C"),            # 6人用 (4 folds)
]

BOARD = "Ks7d2c"

def check_token():
    import base64 as _b64
    try:
        payload = TOKEN.split('.')[1]
        payload += '=' * (-len(payload) % 4)
        data = json.loads(_b64.urlsafe_b64decode(payload))
        remaining = data['exp'] - time.time()
        if remaining <= 30:
            print(f"❌ TOKEN期限切れ（残り{remaining:.0f}秒）"); sys.exit(1)
        print(f"✅ TOKEN残り{remaining/60:.1f}分")
    except Exception as e:
        print(f"❌ TOKEN解析失敗: {e}"); sys.exit(1)

def test_variant(label, pf_action, depth="20.125", board=BOARD):
    params = {
        "gametype":        "MTTGeneral",
        "depth":           depth,
        "stacks":          "",
        "preflop_actions": pf_action,
        "flop_actions":    "X",
        "turn_actions":    "",
        "river_actions":   "",
        "board":           board,
    }
    r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
    if r.status_code != 200:
        return f"HTTP {r.status_code}"

    d = r.json()
    sols = d.get("action_solutions", [])
    pi   = d.get("players_info", [])
    positions = [p.get("player", {}).get("position") for p in pi if isinstance(p.get("player"), dict)]

    if not sols:
        return f"OK but action_solutions=[] (positions={positions})"

    total_freq_sum = sum(float(s.get("total_frequency", 0)) for s in sols)
    bet_freq = sum(float(s.get("total_frequency", 0)) for s in sols if s["action"]["type"] == "RAISE")
    actions = {s["action"]["code"]: round(float(s.get("total_frequency", 0)) * 100, 1) for s in sols}

    if total_freq_sum < 0.99:
        return f"PARTIAL: total_freq_sum={total_freq_sum:.3f} positions={positions} actions={actions}"

    return f"✓ CBet={bet_freq*100:.1f}% positions={positions} actions={actions}"


if __name__ == "__main__":
    if not TOKEN:
        print("❌ TOKEN未設定"); sys.exit(1)
    check_token()

    print(f"\n=== SBR20 (depth=20.125) 診断 board={BOARD} ===\n")
    for label, pf in PF_VARIANTS:
        print(f"  [{label}]")
        print(f"    preflop: {pf}")
        result = test_variant(label, pf)
        print(f"    結果: {result}")
        time.sleep(3)

    # 比較: SBR25 (動作確認済み)
    print(f"\n=== SBR25 (depth=25.125) 比較 ===")
    result = test_variant("SBR25_reference", "F-F-F-F-F-R2.1-F-C", depth="25.125")
    print(f"  SBR25 (R2.1): {result}")
