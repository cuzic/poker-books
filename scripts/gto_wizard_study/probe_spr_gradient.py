#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""SPR 境界の実測 — 同 board × 異 SPR 値で行動変化を観察。

SPR を変える 2 つの方法:
1. スタック深度変化: 25 / 50 / 100 / 200bb
2. cbet サイズ変化 (turn SPR): 25% / 33% / 50% / 75% / 100% (SRP flop cbet)

Probe target:
- 代表 board (Ks7d2c, 9s8d7c) × 各 SPR 軸

MATCHA SPR tiers:
- オールイン: <1 (4BP river, 3BP river)
- ロー: 1-3 (4BP flop, 3BP turn)
- ミディアム: 3-7 (3BP flop, SRP river)
- ディープ: >7 (SRP flop Cash100)

→ これらが行動の不連続点になっているか検証
"""
from __future__ import annotations
import json, time
from pathlib import Path
import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN = (SCRIPT_DIR / ".token").read_text().strip()
GAID = (SCRIPT_DIR / ".google_anal_id").read_text().strip()
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_spr_gradient")
OUT_DIR.mkdir(parents=True, exist_ok=True)

API = "https://api.gtowizard.com/v4/solutions/spot-solution/"
HEADERS = {
    "authorization": f"Bearer {TOKEN}",
    "google-anal-id": GAID,
    "gwclientid": "930036c8-831c-4fca-8453-b0a298853e86",
    "origin": "https://app.gtowizard.com",
    "referer": "https://app.gtowizard.com/",
    "user-agent": "Mozilla/5.0",
    "accept": "application/json, text/plain, */*",
}

# Probe targets: (gametype, depth, preflop, flop_actions, board, label, expected_SPR)
TARGETS = [
    # === Axis 1: スタック深度 (同 SRP flop、SPR 変化 vs depth) ===
    # Cash 25bb は subscription tier 制限で 403 → 削除
    # Cash 100bb SRP flop: pot ~6bb, stack ~97bb → SPR ~16
    ("Cash6mGeneral_6mNL25R25", "50",  "F-F-F-R2.6-F-C", "X", "Ks7d2c", "depth_50_flop",  "SPR ~8"),
    ("Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-C", "X", "Ks7d2c", "depth_100_flop", "SPR ~16"),
    ("Cash6mGeneral_6mNL25R25", "200", "F-F-F-R2.6-F-C", "X", "Ks7d2c", "depth_200_flop", "SPR ~32"),

    # === Axis 2: cbet サイズ → turn SPR 変化 ===
    # 100bb SRP, cbet 25% (=1.5bb on 6bb pot), turn SPR = ~12.7
    # cbet 33% (1.9bb): turn SPR = ~9.7
    # cbet 50% (3bb): turn SPR = ~7.5
    # cbet 75% (4.5bb): turn SPR = ~5.3
    # cbet 100% (6bb): turn SPR = ~4.0
    ("Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-C", "X-R1.5-C", "Ks7d2c3c", "turn_after_25%", "SPR ~12.7"),
    ("Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-C", "X-R1.9-C", "Ks7d2c3c", "turn_after_33%", "SPR ~9.7"),
    ("Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-C", "X-R3-C",   "Ks7d2c3c", "turn_after_50%", "SPR ~7.5"),
    ("Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-C", "X-R4.5-C", "Ks7d2c3c", "turn_after_75%", "SPR ~5.3"),
    ("Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-C", "X-R6-C",   "Ks7d2c3c", "turn_after_100%","SPR ~4.0"),

    # === Axis 3: 3BP / 4BP の SPR 比較 (flop level) ===
    # 3BP flop: pot ~25, stack ~85 → SPR ~3.4
    # 4BP flop: pot ~55, stack ~70 → SPR ~1.3
    ("Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-R11-C", "X",     "Ks7d2c", "3bp_flop", "SPR ~3.4"),
    ("Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-R11-R28-C", "X", "Ks7d2c", "4bp_flop", "SPR ~1.3"),

    # === Axis 4: river SPR (multi-street barrel) ===
    # SRP river after 2 barrels 50%-66%:
    # flop pot 6, cbet 3, pot 12; turn cbet 8, pot 28; river stack ~ 86 / pot 28 = SPR ~3
    # SRP river after 3 barrels (jam): SPR ~0.3
    ("Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-C", "X-R3-C",   "Ks7d2c3c", "turn_50%_then", "SPR turn ~7.5"),
    # river: 50% turn cbet (8bb on 12), 50% river cbet (14bb on 28) — turn after 50%
    # 上記 turn_50% の後の river: turn cbet 8 (28pot), river stack 78
    ("Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-C", "X-R3-C-X-R8-C", "Ks7d2c3c8h", "river_after_2barrels", "SPR river ~2.8"),
]


def parse_spr(label: str) -> float:
    """label の 'SPR ~X' から数値抽出 (不要、参考のみ)"""
    return 0.0


def probe_one(t: tuple) -> tuple[bool, dict]:
    gametype, depth, preflop, flop_actions, board, label, expected_spr = t
    out = OUT_DIR / f"spr_{label}.json"
    if out.exists():
        saved = json.loads(out.read_text())
        actions = saved.get("data", {}).get("action_solutions", [])
        cbet = sum(a["total_frequency"] for a in actions if a["action"]["type"] in ("BET","RAISE"))
        f_freq = sum(a["total_frequency"] for a in actions if a["action"]["type"] == "FOLD")
        c_freq = sum(a["total_frequency"] for a in actions if a["action"]["type"] == "CALL")
        chk = sum(a["total_frequency"] for a in actions if a["action"]["type"] == "CHECK")
        return True, {"cbet": cbet, "fold": f_freq, "call": c_freq, "check": chk, "cached": True}
    params = {
        "gametype": gametype, "depth": depth,
        "preflop_actions": preflop,
        "flop_actions": flop_actions,
        "turn_actions": "",
        "river_actions": "",
        "board": board,
    }
    # river boards have 5 cards
    if len(board) == 10:
        # split into flop_actions and turn_actions if river_actions empty
        pass
    try:
        r = httpx.get(API, params=params, headers=HEADERS, timeout=30.0)
        if r.status_code == 200:
            data = r.json()
            out.write_text(json.dumps({
                "label": label, "expected_spr": expected_spr,
                "board": board, "gametype": gametype, "depth": depth,
                "preflop": preflop, "flop_actions": flop_actions,
                "data": data,
            }, ensure_ascii=False))
            actions = data.get("action_solutions", [])
            cbet = sum(a["total_frequency"] for a in actions if a["action"]["type"] in ("BET","RAISE"))
            f_freq = sum(a["total_frequency"] for a in actions if a["action"]["type"] == "FOLD")
            c_freq = sum(a["total_frequency"] for a in actions if a["action"]["type"] == "CALL")
            chk = sum(a["total_frequency"] for a in actions if a["action"]["type"] == "CHECK")
            return True, {"cbet": cbet, "fold": f_freq, "call": c_freq, "check": chk}
        elif r.status_code == 204:
            return False, {"error": "204"}
        elif r.status_code == 401:
            return False, {"error": "401"}
        else:
            return False, {"error": f"HTTP {r.status_code}: {r.text[:100]}"}
    except Exception as e:
        return False, {"error": str(e)}


n_ok = n_fail = 0
start = time.time()
for i, t in enumerate(TARGETS, 1):
    gametype, depth, preflop, flop_actions, board, label, expected_spr = t
    print(f"[{i}/{len(TARGETS)}] {label:25} ({expected_spr})", end=" ")
    success, result = probe_one(t)
    if success:
        n_ok += 1
        if "cbet" in result and result["cbet"] > 0:
            print(f"✓ bet={result['cbet']*100:.0f}% check={result.get('check',0)*100:.0f}%")
        else:
            print(f"✓ F={result.get('fold',0)*100:.0f}% C={result.get('call',0)*100:.0f}% R={result.get('cbet',0)*100:.0f}%")
    else:
        n_fail += 1
        print(f"✗ {result.get('error', '?')}")
        if "401" in str(result.get("error", "")):
            break
    time.sleep(0.3)

print(f"\nDone: {n_ok}/{len(TARGETS)}, {n_fail} fail, {time.time()-start:.0f}s")
