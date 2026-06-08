#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""エッジケース 12 spots を GTO Wizard で probe。

【目的】
MATCHA 公式の判定が「直感に反する正しい解」を出す瞬間を data で確認。
各エッジケースで:
- BTN/BB の specific hand のアクション分布
- 該当 tier の集計 freq
- equity / eq_bucket 推定

【12 spots】(2-4 のグループ)

A. 強い tier だが equity 低い (over-evaluation)
  1. 66 on 5-4-2: BB defending with overpair vs BTN cbet
  2. JJ on K-T-9 monotone: BB facing cbet
  3. TT on A-7-2: BB facing cbet (mid pocket vs A)
  4. AA on 9-8-7: BB facing cbet (top overpair on connected)
  5. KK on A-7-2: BB facing cbet (実質 2nd pair)

B. 弱い tier だが equity 高い (under-evaluation)
  6. 65s on 6-5-4: SRP IP, hero has TP+OESD (BTN cbet)
  7. AhKh on Q-J-2 2-tone: BB defending with NFD+2overs
  8. 5h4h on 6h7h8h monotone: BB defending with combo draw

C. Counterfeit / board interaction
  9. A2s on 2-2-7: trip 2 with A kicker, paired board
  10. QQ on 8-8-A: overpair on paired A-high
  11. TT on T-2-2: top set on paired (counterfeit risk)

D. Pot type で格下げ
  12. AKo on A-T-5 in 3BP: TPTK demoted in 3BP

【probe param】
- gametype: Cash6mGeneral_6mNL25R25
- depth: 100
- preflop_actions: F-F-F-R2.6-F-C (SRP) or 3BP variant
- flop_actions: "X" (BB to act after check) or "X-R1.9-C" (after cbet) etc
- board: specific edge case board

【出力】
- knowledges/gto_wizard_study/probe_edge_cases/<label>.json
- 各 probe の action_solutions と hand_categories を保存
"""
from __future__ import annotations
import json, time
from pathlib import Path
import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN = (SCRIPT_DIR / ".token").read_text().strip()
GAID = (SCRIPT_DIR / ".google_anal_id").read_text().strip()
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_edge_cases")
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

# 各 spot: (label, preflop_actions, flop_actions, board, hero_hand, description, category)
TARGETS = [
    # === A. 過大評価リスク (強い tier だが equity 低い) ===
    ("A1_66_low_connected_pre_cbet",  "F-F-F-R2.6-F-C", "",          "5d4c2s", "6s6h",
     "BB pre-cbet, 66 overpair on 5-4-2", "A_overestimate"),
    ("A1_66_low_connected_vs_cbet",   "F-F-F-R2.6-F-C", "X-R1.9",    "5d4c2s", "6s6h",
     "BB facing 33% cbet, 66 overpair on 5-4-2", "A_overestimate"),

    ("A2_JJ_KT9_mono_vs_cbet",        "F-F-F-R2.6-F-C", "X-R1.9",    "KhTh9h", "JsJd",
     "BB facing cbet, JJ overpair on KTh-mono", "A_overestimate"),

    ("A3_TT_A72_vs_cbet",             "F-F-F-R2.6-F-C", "X-R1.9",    "As7d2c", "TsTd",
     "BB facing cbet, TT (mid pocket) vs A-high", "A_overestimate"),

    ("A4_AA_987_vs_cbet",             "F-F-F-R2.6-F-C", "X-R1.9",    "9s8d7c", "AsAd",
     "BB facing cbet, AA overpair on connected 9-8-7", "A_overestimate"),

    ("A5_KK_A72_vs_cbet",             "F-F-F-R2.6-F-C", "X-R1.9",    "As7d2c", "KsKd",
     "BB facing cbet, KK overpair with A overcard", "A_overestimate"),

    # === B. 過小評価リスク (弱い tier だが equity 高い) ===
    ("B6_65s_456_pre_cbet",           "F-F-F-R2.6-F-C", "",          "6d5c4s", "6h5h",
     "BB pre-cbet, 65s = TP+OESD on 6-5-4", "B_underestimate"),
    # Hero is BB (caller), needs to be BTN combo for cbet decision
    # Or: BTN's decision with 65s on 6-5-4 (BTN holds, attacker)

    ("B7_AhKh_QJ2_2tone_vs_cbet",     "F-F-F-R2.6-F-C", "X-R1.9",    "QhJh2c", "AhKh",
     "BB facing cbet, AhKh = NFD+2overs on QhJh2", "B_underestimate"),

    ("B8_54h_678h_mono_vs_cbet",      "F-F-F-R2.6-F-C", "X-R1.9",    "6h7h8h", "5h4h",
     "BB facing cbet, 5h4h = combo draw on monotone 678h", "B_underestimate"),

    # === C. Counterfeit / board interaction ===
    ("C9_A2s_227_vs_cbet",            "F-F-F-R2.6-F-C", "X-R1.9",    "2c2d7s", "As2h",
     "BB facing cbet, A2s = trip 2 + A kicker", "C_counterfeit"),

    ("C10_QQ_88A_vs_cbet",            "F-F-F-R2.6-F-C", "X-R1.9",    "8s8dAh", "QsQd",
     "BB facing cbet, QQ on paired A-high", "C_counterfeit"),

    ("C11_TT_T22_vs_cbet",            "F-F-F-R2.6-F-C", "X-R1.9",    "Tc2d2s", "TsTh",
     "BB facing cbet, TT = top set + FH on T22", "C_counterfeit"),

    # === D. Pot type で格下げ ===
    ("D12_AKo_AT5_3bp_vs_cbet",       "F-F-F-R2.6-F-R8-C", "X-R3",   "AsTd5c", "AhKd",
     "3BP, BB facing cbet on A-high, AKo TPTK in 3BP", "D_pot_demote"),
]


print(f"Edge case probe: {len(TARGETS)} spots")
n_ok = n_fail = 0
start = time.time()

for i, (label, preflop, flop_acts, board, hero_hand, desc, cat) in enumerate(TARGETS, 1):
    out = OUT_DIR / f"{label}.json"
    if out.exists():
        print(f"[{i}/{len(TARGETS)}] {label[:40]:40} (cached)")
        n_ok += 1
        continue

    params = {
        "gametype": "Cash6mGeneral_6mNL25R25", "depth": "100",
        "preflop_actions": preflop,
        "flop_actions": flop_acts,
        "turn_actions": "", "river_actions": "",
        "board": board,
    }
    print(f"[{i}/{len(TARGETS)}] {label[:40]:40}", end=" ")
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
            print(f"✓ {', '.join(summary[:4])}")
            n_ok += 1
        elif r.status_code == 204:
            print("✗ 204 (no spot)")
            n_fail += 1
        elif r.status_code == 401:
            print("✗ 401 TOKEN")
            n_fail += 1
            break
        else:
            print(f"✗ {r.status_code}: {r.text[:60]}")
            n_fail += 1
    except Exception as e:
        print(f"✗ {e}")
        n_fail += 1
    time.sleep(0.3)

print(f"\nDone: {n_ok}/{len(TARGETS)}, {n_fail} fail, {time.time()-start:.0f}s")
