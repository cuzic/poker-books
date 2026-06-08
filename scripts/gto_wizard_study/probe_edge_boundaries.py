#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""エッジケース境界の明確化 — 30 spots。

【観点】
1. 「overpair vs 2nd pair」境界 (Q on K-high, J on Q-high 等)
2. AA の slowplay 境界 (board が wet ほど slowplay?)
3. 低 overpair の sizing 境界 (66 on 5-4-2 vs 33%/50%/75%)
4. counterfeit 境界 (board pair の rank で行動変化?)
5. 3BP/4BP の格下げ境界 (TPTK が pot type で扱われ方変化?)

【preflop sequence】
- SRP: F-F-F-R2.6-F-C
- 3BP IP: F-F-F-R2.6-R11-C
- 3BP OOP (BB 3bet): F-F-F-R2.6-F-R11-C
- 4BP: F-F-F-R2.6-R11-R28-C

【flop_actions】
- pre-cbet: ""
- vs 33%: "X-R1.9"
- vs 50%: "X-R3"
- vs 75%: "X-R4.5"
- vs 100%: "X-R6"
"""
from __future__ import annotations
import json, time
from pathlib import Path
import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN = (SCRIPT_DIR / ".token").read_text().strip()
GAID = (SCRIPT_DIR / ".google_anal_id").read_text().strip()
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_edge_boundaries")
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

# (label, preflop, flop_actions, board, hero, description, category)
TARGETS = [
    # === 1. overpair vs 2nd pair 境界 ===
    # board の high が hero pair より上ならどこまで?
    ("ov_QQ_K72",       "F-F-F-R2.6-F-C", "X-R1.9", "Ks7d2c", "QsQd",
     "QQ on K-high — overpair? 2nd pair?", "ov_boundary"),
    ("ov_JJ_Q72",       "F-F-F-R2.6-F-C", "X-R1.9", "Qs7d2c", "JsJd",
     "JJ on Q-high — overpair? 2nd pair?", "ov_boundary"),
    ("ov_TT_J72",       "F-F-F-R2.6-F-C", "X-R1.9", "Js7d2c", "TsTd",
     "TT on J-high", "ov_boundary"),
    ("ov_88_T72",       "F-F-F-R2.6-F-C", "X-R1.9", "Ts7d2c", "8s8d",
     "88 on T-high — 2 overcards", "ov_boundary"),
    ("ov_TT_K72",       "F-F-F-R2.6-F-C", "X-R1.9", "Ks7d2c", "TsTd",
     "TT on K-high — 1 overcard", "ov_boundary"),
    ("ov_77_K72",       "F-F-F-R2.6-F-C", "X-R1.9", "Ks7d2c", "7s7d",
     "77 on K-high (pair of 7s in board overlap)", "ov_boundary"),

    # === 2. AA の slowplay 境界 ===
    ("aa_dry_K72",      "F-F-F-R2.6-F-C", "X-R1.9", "Ks7d2c", "AsAd",
     "AA on dry K-high — TPTK like", "aa_slowplay"),
    ("aa_paired_KK4",   "F-F-F-R2.6-F-C", "X-R1.9", "KsKd4c", "AsAd",
     "AA on paired K — overpair", "aa_slowplay"),
    ("aa_connected_TJQ","F-F-F-R2.6-F-C", "X-R1.9", "TsJdQc", "AsAd",
     "AA on broadway connected", "aa_slowplay"),
    ("aa_low_542",      "F-F-F-R2.6-F-C", "X-R1.9", "5d4c2s", "AsAd",
     "AA on low connected", "aa_slowplay"),
    ("aa_mid_876",      "F-F-F-R2.6-F-C", "X-R1.9", "8s7d6c", "AsAd",
     "AA on mid connected", "aa_slowplay"),

    # === 3. 低 overpair の sizing 境界 (66 等) ===
    ("low_66_75pct",    "F-F-F-R2.6-F-C", "X-R4.5", "5d4c2s", "6s6h",
     "66 on 5-4-2 vs 75% cbet", "low_overpair_sizing"),
    ("low_66_100pct",   "F-F-F-R2.6-F-C", "X-R6",   "5d4c2s", "6s6h",
     "66 on 5-4-2 vs 100% cbet", "low_overpair_sizing"),
    ("low_77_75pct",    "F-F-F-R2.6-F-C", "X-R4.5", "5d4c2s", "7s7d",
     "77 on 5-4-2 vs 75% cbet", "low_overpair_sizing"),
    ("low_88_75pct",    "F-F-F-R2.6-F-C", "X-R4.5", "5d4c2s", "8s8d",
     "88 on 5-4-2 vs 75% cbet", "low_overpair_sizing"),
    ("low_99_75pct",    "F-F-F-R2.6-F-C", "X-R4.5", "5d4c2s", "9s9d",
     "99 on 5-4-2 vs 75% cbet", "low_overpair_sizing"),

    # === 4. counterfeit 境界 (paired board の rank) ===
    ("cf_QQ_K_K_4",     "F-F-F-R2.6-F-C", "X-R1.9", "KsKd4c", "QsQd",
     "QQ on paired K-high — under quads", "counterfeit"),
    ("cf_JJ_8_8_A",     "F-F-F-R2.6-F-C", "X-R1.9", "8s8dAh", "JsJd",
     "JJ on paired 8 with A overcard", "counterfeit"),
    ("cf_QQ_8_8_4",     "F-F-F-R2.6-F-C", "X-R1.9", "8s8d4c", "QsQd",
     "QQ on paired 8 low — clean overpair", "counterfeit"),
    ("cf_88_8_8_A",     "F-F-F-R2.6-F-C", "X-R1.9", "8s8dAh", "8c8h",
     "88 on paired 8 with A — quads", "counterfeit"),
    ("cf_77_7_7_2",     "F-F-F-R2.6-F-C", "X-R1.9", "7s7d2c", "7c7h",
     "77 on paired 7 — quads", "counterfeit"),

    # === 5. combo draw 境界 ===
    ("draw_FD_NFD",     "F-F-F-R2.6-F-C", "X-R1.9", "QhJh2c", "AhKh",
     "AhKh = NFD + 2 overs on QhJh2c (single suit)", "combo_draw"),
    ("draw_OESD_FD",    "F-F-F-R2.6-F-C", "X-R1.9", "8h7h2c", "6h5h",
     "65h on 8h7h2c — OESD + FD", "combo_draw"),
    ("draw_OESD_NFD",   "F-F-F-R2.6-F-C", "X-R1.9", "8h7c2c", "6h5h",
     "65h on 8h7c2c — OESD only", "combo_draw"),
    ("draw_FD_only",    "F-F-F-R2.6-F-C", "X-R1.9", "Kh7h2c", "9h8h",
     "98h on Kh7h2c — FD only (low)", "combo_draw"),
    ("draw_gutshot_FD", "F-F-F-R2.6-F-C", "X-R1.9", "QhTh2c", "Jh9h",
     "J9h on QhTh2c — gutshot + FD", "combo_draw"),

    # === 6. 3BP/4BP の格下げ境界 ===
    ("pot_AKo_AT5_srp", "F-F-F-R2.6-F-C", "X-R1.9", "AsTd5c", "AhKd",
     "AKo TPTK on A-T-5 in SRP — baseline", "pot_demote"),
    ("pot_AKo_AT5_3bp", "F-F-F-R2.6-F-R11-C", "X-R3.5", "AsTd5c", "AhKd",
     "AKo TPTK in 3BP", "pot_demote"),

    # === 7. SPR が浅い時の overpair ===
    ("spr_JJ_4bp",      "F-F-F-R2.6-F-R11-R28-C", "X", "5d4c2s", "JsJd",
     "JJ in 4BP on low board (deep SPR comparison)", "spr_shallow"),
    ("spr_AA_4bp",      "F-F-F-R2.6-F-R11-R28-C", "X", "5d4c2s", "AsAd",
     "AA in 4BP on low board", "spr_shallow"),
]


print(f"Edge boundary probe: {len(TARGETS)} spots")
n_ok = n_fail = 0
start = time.time()

for i, (label, preflop, flop_acts, board, hero_hand, desc, cat) in enumerate(TARGETS, 1):
    out = OUT_DIR / f"{label}.json"
    if out.exists():
        print(f"[{i}/{len(TARGETS)}] {label[:35]:35} (cached)")
        n_ok += 1
        continue

    params = {
        "gametype": "Cash6mGeneral_6mNL25R25", "depth": "100",
        "preflop_actions": preflop,
        "flop_actions": flop_acts,
        "turn_actions": "", "river_actions": "",
        "board": board,
    }
    print(f"[{i}/{len(TARGETS)}] {label[:35]:35}", end=" ")
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
