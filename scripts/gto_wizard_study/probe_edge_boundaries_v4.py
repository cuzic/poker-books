#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""エッジケース境界 v4 — position / MTT depth / delayed cbet / 3BP-4BP 詳細。

【観点】
1. opener position 比較 (UTG/HJ/CO/BTN/SB)
2. MTT 25/50/200bb の同 spot 比較
3. delayed cbet (flop X-X 後の turn) の境界
4. 3BP/4BP の board 別行動
5. SB open vs BB defense
"""
from __future__ import annotations
import json, time
from pathlib import Path
import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN = (SCRIPT_DIR / ".token").read_text().strip()
GAID = (SCRIPT_DIR / ".google_anal_id").read_text().strip()
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_edge_boundaries_v4")
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

# (label, gametype, depth, preflop, flop, board, desc, cat)
TARGETS = [
    # === 1. opener position 比較 (preflop sequence 別) ===
    # UTG open: R2.6-F-F-F-F-C (BB call)
    ("pos_UTG_K72_cbet",  "Cash6mGeneral_6mNL25R25", "100", "R2.6-F-F-F-F-C", "X-R1.9", "Ks7d2c", "UTG vs BB on K72 (BB facing cbet)", "position"),
    ("pos_HJ_K72_cbet",   "Cash6mGeneral_6mNL25R25", "100", "F-R2.6-F-F-F-C", "X-R1.9", "Ks7d2c", "HJ vs BB on K72", "position"),
    ("pos_CO_K72_cbet",   "Cash6mGeneral_6mNL25R25", "100", "F-F-R2.6-F-F-C", "X-R1.9", "Ks7d2c", "CO vs BB on K72", "position"),
    ("pos_BTN_K72_cbet",  "Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-C", "X-R1.9", "Ks7d2c", "BTN vs BB on K72 (baseline)", "position"),
    ("pos_SB_K72_cbet",   "Cash6mGeneral_6mNL25R25", "100", "F-F-F-F-R3-C",   "X-R1.9", "Ks7d2c", "SB vs BB on K72 (BvB)", "position"),

    # === 2. MTT depth 別 (Cash100 baseline vs MTT200/50/25) ===
    ("mtt_25_K72",  "Cash6mGeneral_6mNL25R25", "25",  "F-F-F-R2.6-F-C", "X-R1.9", "Ks7d2c", "Cash 25bb (shallow) K72", "mtt_depth"),
    ("mtt_50_K72",  "Cash6mGeneral_6mNL25R25", "50",  "F-F-F-R2.6-F-C", "X-R1.9", "Ks7d2c", "Cash 50bb K72", "mtt_depth"),
    ("mtt_200_K72", "Cash6mGeneral_6mNL25R25", "200", "F-F-F-R2.6-F-C", "X-R1.9", "Ks7d2c", "Cash 200bb K72 (deep)", "mtt_depth"),

    # === 3. delayed cbet (turn after flop X-X) ===
    # BTN delayed cbet on turn brick
    ("del_K72_3",  "Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-C", "X-X", "Ks7d2c3h", "BTN delayed cbet decision on turn 3", "del_cbet"),
    ("del_K72_8",  "Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-C", "X-X", "Ks7d2c8h", "BTN delayed cbet on turn 8", "del_cbet"),
    ("del_K72_A",  "Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-C", "X-X", "Ks7d2cAh", "BTN delayed cbet on turn A (overcard)", "del_cbet"),
    ("del_K72_K",  "Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-C", "X-X", "Ks7d2cKh", "BTN delayed cbet on turn paired K", "del_cbet"),

    # === 4. 3BP の board 別 ===
    ("3bp_K72",  "Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-R10-C", "X-R3.5", "Ks7d2c", "3BP IP K72 (BB facing cbet)", "3bp_board"),
    ("3bp_T98", "Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-R10-C", "X-R3.5", "Ts9d8c", "3BP T98", "3bp_board"),
    ("3bp_AT5", "Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-R10-C", "X-R3.5", "AsTd5c", "3BP A-T-5", "3bp_board"),
    ("3bp_542", "Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-R10-C", "X-R3.5", "5d4c2s", "3BP 5-4-2", "3bp_board"),

    # === 5. 4BP の board 別 ===
    ("4bp_K72_flop",  "Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-R11-R28-C", "", "Ks7d2c", "4BP flop K72 pre-cbet", "4bp_board"),
    ("4bp_T98_flop",  "Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-R11-R28-C", "", "Ts9d8c", "4BP T98 flop pre-cbet", "4bp_board"),
    ("4bp_AT5_flop",  "Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-R11-R28-C", "", "AsTd5c", "4BP A-T-5 flop pre-cbet", "4bp_board"),
    ("4bp_876_flop",  "Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-R11-R28-C", "", "8s7d6c", "4BP 8-7-6 flop pre-cbet", "4bp_board"),

    # === 6. SB vs BB (limped pot? or SB raise) ===
    ("sb_open_K72",   "Cash6mGeneral_6mNL25R25", "100", "F-F-F-F-R3-C", "", "Ks7d2c", "SB open BB call K72 pre-cbet", "sb_vs_bb"),
    ("sb_open_T98",   "Cash6mGeneral_6mNL25R25", "100", "F-F-F-F-R3-C", "", "Ts9d8c", "SB open BB call T98", "sb_vs_bb"),
    ("sb_open_low",   "Cash6mGeneral_6mNL25R25", "100", "F-F-F-F-R3-C", "", "5d4c2s", "SB open BB call low 5-4-2", "sb_vs_bb"),

    # === 7. river — different sequence (try simpler) ===
    # SRP: BTN cbet flop, BB call, BTN cbet turn, BB call, river BTN bet
    ("river_BTN_3b_K7238", "Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-C", "X-R1.9-C-X-R4.5-C-X-R10", "Ks7d2c3h8s", "river after 2-barrel, BTN 3rd barrel", "river_3barrel"),
    ("river_check_K7238", "Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-C", "X-R1.9-C-X-R4.5-C", "Ks7d2c3h8s", "river BTN to act after 2 barrels", "river_btn_act"),

    # === 8. turn after flop X-X (delayed cbet 後の BB facing) ===
    ("turn_xx_bb_face33", "Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-C", "X-X-X-R1.9", "Ks7d2c3h", "BB facing turn delayed cbet 33%", "turn_xx_bb"),
    ("turn_xx_bb_face75", "Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-C", "X-X-X-R4.5", "Ks7d2c3h", "BB facing turn delayed cbet 75%", "turn_xx_bb"),

    # === 9. paired board の cbet 行動 ===
    ("paired_77_cbet",  "Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-C", "", "7s7d2c", "BTN cbet decision on 7-7-2", "paired_board"),
    ("paired_AA_cbet",  "Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-C", "", "AsAd2c", "BTN cbet on A-A-2", "paired_board"),
    ("paired_KK_cbet",  "Cash6mGeneral_6mNL25R25", "100", "F-F-F-R2.6-F-C", "", "KsKd2c", "BTN cbet on K-K-2", "paired_board"),
]


print(f"Edge boundary v4 probe: {len(TARGETS)} spots")
n_ok = n_fail = 0
start = time.time()

for i, t in enumerate(TARGETS, 1):
    label, gametype, depth, preflop, flop_acts, board, desc, cat = t
    out = OUT_DIR / f"{label}.json"
    if out.exists():
        print(f"[{i}/{len(TARGETS)}] {label[:30]:30} (cached)")
        n_ok += 1
        continue

    params = {
        "gametype": gametype, "depth": depth,
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
                "gametype": gametype, "depth": depth,
                "preflop": preflop, "flop_actions": flop_acts,
                "board": board,
                "description": desc, "data": data,
            }, ensure_ascii=False))
            actions = data.get("action_solutions", [])
            summary = []
            for a in actions:
                t_a = a["action"]["type"]
                sz = a["action"].get("betsize", 0)
                fq = a["total_frequency"] * 100
                if t_a in ("BET","RAISE"):
                    summary.append(f"{t_a[0]}{sz}={fq:.0f}%")
                else:
                    summary.append(f"{t_a[0]}={fq:.0f}%")
            print(f"✓ {', '.join(summary[:3])}")
            n_ok += 1
        elif r.status_code == 204:
            print("✗ 204")
            n_fail += 1
        elif r.status_code == 401:
            print("✗ 401 TOKEN")
            n_fail += 1
            break
        elif r.status_code == 403:
            print(f"✗ 403 (no permission for {depth}bb)")
            n_fail += 1
        else:
            print(f"✗ {r.status_code}: {r.text[:50]}")
            n_fail += 1
    except Exception as e:
        print(f"✗ {e}")
        n_fail += 1
    time.sleep(0.3)

print(f"\nDone: {n_ok}/{len(TARGETS)}, {n_fail} fail, {time.time()-start:.0f}s")
