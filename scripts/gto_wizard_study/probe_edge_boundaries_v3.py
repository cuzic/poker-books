#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""エッジケース境界 v3 — turn / river / donk / CR の境界。

【新観点】
1. turn card type 別の行動 (overcard, pair, brick, draw complete)
2. river bluff catch の境界 (tier 別)
3. donk bet の境界 (low board / paired board)
4. flop CR の境界
5. position 別 (CO vs BTN attacker)
6. board texture 細分化
"""
from __future__ import annotations
import json, time
from pathlib import Path
import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN = (SCRIPT_DIR / ".token").read_text().strip()
GAID = (SCRIPT_DIR / ".google_anal_id").read_text().strip()
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_edge_boundaries_v3")
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

TARGETS = [
    # === 1. turn card type 別 (flop K72 → turn brick/over/pair/draw) ===
    # Flop: BTN cbet 33%, BB call → turn 別 card
    ("turn_K72_brick3",  "F-F-F-R2.6-F-C", "X-R1.9-C", "Ks7d2c3h", "?", "K72 → turn brick 3", "turn_card"),
    ("turn_K72_brick8",  "F-F-F-R2.6-F-C", "X-R1.9-C", "Ks7d2c8h", "?", "K72 → turn brick 8", "turn_card"),
    ("turn_K72_pairK",   "F-F-F-R2.6-F-C", "X-R1.9-C", "Ks7d2cKh", "?", "K72 → turn paired K", "turn_card"),
    ("turn_K72_pair7",   "F-F-F-R2.6-F-C", "X-R1.9-C", "Ks7d2c7h", "?", "K72 → turn paired 7", "turn_card"),
    ("turn_K72_overA",   "F-F-F-R2.6-F-C", "X-R1.9-C", "Ks7d2cAh", "?", "K72 → turn overcard A", "turn_card"),
    ("turn_K72_drawJ",   "F-F-F-R2.6-F-C", "X-R1.9-C", "Ks7d2cJh", "?", "K72 → turn middle card J", "turn_card"),

    # === 2. river bluff catch (after turn check-check, river bet) ===
    # Flop: cbet-call, Turn: check-check, River: BTN bet 50%
    ("river_TP_K72_3c8h", "F-F-F-R2.6-F-C", "X-R1.9-C-X-X-X-R6.7", "Ks7d2c3c8h", "?", "river vs 50% (turn checked back)", "river_catch"),
    # Different sizing: 33% river bet
    ("river_TP_K72_33pct", "F-F-F-R2.6-F-C", "X-R1.9-C-X-X-X-R4.5", "Ks7d2c3c8h", "?", "river vs 33% bet", "river_catch"),

    # === 3. donk bet (OOP BB's first action on flop after preflop call) ===
    ("donk_BB_low542",   "F-F-F-R2.6-F-C", "",       "5d4c2s", "?", "BB pre-cbet check (no donk by default)", "donk"),
    ("donk_BB_paired",   "F-F-F-R2.6-F-C", "",       "7s7d2c", "?", "BB pre-cbet on paired 7", "donk"),
    ("donk_BB_322",      "F-F-F-R2.6-F-C", "",       "3s2d2c", "?", "BB pre-cbet on paired-low", "donk"),
    ("donk_BB_443",      "F-F-F-R2.6-F-C", "",       "4s4d3c", "?", "BB on 443 (BB favored)", "donk"),

    # === 4. flop CR の境界 (BB CR vs BTN cbet) ===
    # BB calls preflop, BTN cbets 33%, BB raises
    ("cr_BB_K72_R6.5",   "F-F-F-R2.6-F-C", "X-R1.9-R6.5", "Ks7d2c", "?", "BB CR to 6.5bb on K72", "flop_cr"),
    ("cr_BB_T98_R6.5",   "F-F-F-R2.6-F-C", "X-R1.9-R6.5", "Ts9d8c", "?", "BB CR on T98 (BB favored)", "flop_cr"),

    # === 5. CO/BTN position 比較 (turn vs cbet) ===
    # CO open instead of BTN: F-F-R2.5-F-F-C? not standard, try CO open
    ("co_open_K72",      "F-F-R2.6-F-F-C", "",       "Ks7d2c", "?", "CO open BB call, K72 pre-cbet", "position"),
    ("co_open_T98",      "F-F-R2.6-F-F-C", "",       "Ts9d8c", "?", "CO open, T98 pre-cbet", "position"),

    # === 6. board texture 細分化 (rainbow vs 2tone vs monotone) ===
    ("k72_rainbow",  "F-F-F-R2.6-F-C", "X-R1.9", "Ks7d2c", "?", "K72 rainbow vs cbet 33% (baseline)", "texture"),
    ("k72_2tone_K",  "F-F-F-R2.6-F-C", "X-R1.9", "Ks7s2c", "?", "K72 2tone (K of FD)", "texture"),
    ("k72_2tone_low","F-F-F-R2.6-F-C", "X-R1.9", "Ks7d2d", "?", "K72 2tone (low of FD)", "texture"),
    ("k72_monotone", "F-F-F-R2.6-F-C", "X-R1.9", "Ks7s2s", "?", "K72 monotone", "texture"),

    # === 7. turn vs cbet (BB facing turn cbet after flop check-check) ===
    ("turn_xx_brick3",   "F-F-F-R2.6-F-C", "X-X-X-R3", "Ks7d2c3h", "?", "BB vs turn cbet after flop X-X (brick)", "turn_xx"),
    ("turn_xx_overA",    "F-F-F-R2.6-F-C", "X-X-X-R3", "Ks7d2cAh", "?", "BB vs turn cbet after X-X (A overcard)", "turn_xx"),
    ("turn_xx_pair7",    "F-F-F-R2.6-F-C", "X-X-X-R3", "Ks7d2c7h", "?", "BB vs turn cbet after X-X (pair)", "turn_xx"),

    # === 8. SPR shallow attacker (4BP attacker decision) ===
    ("attk_4bp_K72_AKs", "F-F-F-R2.6-F-R11-R28-C", "", "Ks7d2c", "?", "4BP attacker on K72 pre-cbet", "attk_4bp"),
    ("attk_4bp_532_low", "F-F-F-R2.6-F-R11-R28-C", "", "5s3d2c", "?", "4BP attacker on 5-3-2 low", "attk_4bp"),

    # === 9. donk turn (BB lead after flop check-check) ===
    ("donk_turn_K72_A",  "F-F-F-R2.6-F-C", "X-X-R3",  "Ks7d2cAh", "?", "BB donk on turn A after flop X-X", "donk_turn"),
    ("donk_turn_K72_7",  "F-F-F-R2.6-F-C", "X-X-R3",  "Ks7d2c7h", "?", "BB donk on turn 7 (paired) after X-X", "donk_turn"),

    # === 10. BvB (SB vs BB) for comparison ===
    ("bvb_flop_K72",     "F-F-F-F-R3-C",   "X-R1.9", "Ks7d2c", "?", "BvB (SB open, BB call), BB vs cbet K72", "bvb"),
]


print(f"Edge boundary v3 probe: {len(TARGETS)} spots")
n_ok = n_fail = 0
start = time.time()

for i, (label, preflop, flop_acts, board, hero_hand, desc, cat) in enumerate(TARGETS, 1):
    out = OUT_DIR / f"{label}.json"
    if out.exists():
        print(f"[{i}/{len(TARGETS)}] {label[:30]:30} (cached)")
        n_ok += 1
        continue

    params = {
        "gametype": "Cash6mGeneral_6mNL25R25", "depth": "100",
        "preflop_actions": preflop,
        "flop_actions": flop_acts,
        "turn_actions": "", "river_actions": "",
        "board": board,
    }
    print(f"[{i}/{len(TARGETS)}] {label[:30]:30}", end=" ")
    try:
        r = httpx.get(API, params=params, headers=HEADERS, timeout=30.0)
        if r.status_code == 200:
            data = r.json()
            out.write_text(json.dumps({
                "label": label, "category": cat,
                "preflop": preflop, "flop_actions": flop_acts,
                "board": board, "hero_hand": hero_hand,
                "description": desc, "data": data,
            }, ensure_ascii=False))
            actions = data.get("action_solutions", [])
            summary = []
            for a in actions:
                t = a["action"]["type"]
                sz = a["action"].get("betsize", 0)
                fq = a["total_frequency"] * 100
                if t in ("BET","RAISE"):
                    summary.append(f"{t[0]}{sz}={fq:.0f}%")
                else:
                    summary.append(f"{t[0]}={fq:.0f}%")
            print(f"✓ {', '.join(summary[:3])}")
            n_ok += 1
        elif r.status_code == 204:
            print("✗ 204")
            n_fail += 1
        elif r.status_code == 401:
            print("✗ 401 TOKEN")
            n_fail += 1
            break
        else:
            print(f"✗ {r.status_code}: {r.text[:50]}")
            n_fail += 1
    except Exception as e:
        print(f"✗ {e}")
        n_fail += 1
    time.sleep(0.3)

print(f"\nDone: {n_ok}/{len(TARGETS)}, {n_fail} fail, {time.time()-start:.0f}s")
