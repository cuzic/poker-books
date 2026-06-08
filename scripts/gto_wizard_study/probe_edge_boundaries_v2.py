#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""エッジケース境界 v2 — 30 spots 追加 probe。

【新観点】
1. overpair → 2nd pair 格下げの境界精緻化 (2/3 overcards)
2. AA on wet/monotone の slowplay
3. low overpair の sizing 境界 (33% で失敗した分の代替 sizing)
4. attacker (BTN) 側の境界
5. river の bluff catch 境界
6. 同 pair で board 違いの cross 比較
"""
from __future__ import annotations
import json, time
from pathlib import Path
import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN = (SCRIPT_DIR / ".token").read_text().strip()
GAID = (SCRIPT_DIR / ".google_anal_id").read_text().strip()
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_edge_boundaries_v2")
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
    # === 1. overpair 格下げ境界 (2/3 overcards) ===
    ("88_KQ3",       "F-F-F-R2.6-F-C", "X-R1.9", "KsQd3c", "8s8d", "88 on K-Q-3 (2 overcards)", "ov_2over"),
    ("88_KQJ",       "F-F-F-R2.6-F-C", "X-R1.9", "KsQdJc", "8s8d", "88 on K-Q-J (3 overcards, connected)", "ov_2over"),
    ("66_KQ3",       "F-F-F-R2.6-F-C", "X-R1.9", "KsQd3c", "6s6d", "66 on K-Q-3", "ov_2over"),
    ("66_AKQ",       "F-F-F-R2.6-F-C", "X-R1.9", "AsKdQc", "6s6d", "66 on A-K-Q (3 overcards broadway)", "ov_2over"),
    ("99_AT2",       "F-F-F-R2.6-F-C", "X-R1.9", "AsTd2c", "9s9d", "99 on A-T-2 (2 overcards)", "ov_2over"),
    ("TT_A52",       "F-F-F-R2.6-F-C", "X-R1.9", "As5d2c", "TsTd", "TT on A-5-2 (1 overcard, low)", "ov_2over"),

    # === 2. AA on wet board ===
    ("aa_QhJh2h",    "F-F-F-R2.6-F-C", "X-R1.9", "QhJh2h", "AsAd", "AA on Q-J-2 monotone", "aa_wet"),
    ("aa_T98_2tone", "F-F-F-R2.6-F-C", "X-R1.9", "Ts9d8s", "AsAd", "AA on T-9-8 (connected 2tone)", "aa_wet"),
    ("aa_KQT_2tone", "F-F-F-R2.6-F-C", "X-R1.9", "KhQhTs", "AsAd", "AA on K-Q-T 2tone broadway", "aa_wet"),
    ("aa_765_rainbow","F-F-F-R2.6-F-C","X-R1.9", "7s6d5c", "AsAd", "AA on 7-6-5 rainbow", "aa_wet"),

    # === 3. low overpair の sizing 境界 (33% pre or post cbet で再試行) ===
    # 5-4-2 は 33% sizing なし → pre-cbet phase の自分の bet 行動
    ("low_66_pre_jam",  "F-F-F-R2.6-F-C", "X-R6.5", "5d4c2s", "6s6h", "66 on 5-4-2, pot vs 100% cbet", "low_sizing"),
    ("low_77_pre_jam",  "F-F-F-R2.6-F-C", "X-R6.5", "5d4c2s", "7s7d", "77 on 5-4-2, vs 100% cbet", "low_sizing"),
    ("low_88_pre_jam",  "F-F-F-R2.6-F-C", "X-R6.5", "5d4c2s", "8s8d", "88 on 5-4-2, vs 100% cbet", "low_sizing"),
    ("low_TT_pre_jam",  "F-F-F-R2.6-F-C", "X-R6.5", "5d4c2s", "TsTd", "TT on 5-4-2, vs 100% cbet", "low_sizing"),

    # === 4. BTN attacker 側エッジケース ===
    # BTN's own cbet decision with specific hand
    ("attk_66_KQ3",  "F-F-F-R2.6-F-C", "",       "KsQd3c", "6s6d", "BTN attacker 66 on KQ3 (pre-cbet)", "attk"),
    ("attk_66_K72",  "F-F-F-R2.6-F-C", "",       "Ks7d2c", "6s6d", "BTN attacker 66 on K72 (pre-cbet)", "attk"),
    ("attk_AhKh_876","F-F-F-R2.6-F-C", "",       "8s7d6c", "AhKh", "BTN attacker AhKh on 876 (overcards+BD)", "attk"),
    ("attk_QQ_KQ3", "F-F-F-R2.6-F-C", "",       "KsQd3c", "QsQd", "BTN attacker QQ on KQ3 (TPTK)", "attk"),

    # === 5. river bluff catch 境界 (BB defender at river) ===
    # SRP river after BTN cbet flop + BB call, turn check-check, river BTN bet
    ("river_AhKh_K72_3c8h", "F-F-F-R2.6-F-C", "X-R1.9-C-X-X-X-R6.7", "Ks7d2c3c8h", "AhKh",
     "BB river facing 75% bet, AhKh = bluff catch", "river_catch"),
    ("river_TT_K72_3c8h", "F-F-F-R2.6-F-C", "X-R1.9-C-X-X-X-R6.7", "Ks7d2c3c8h", "TsTd",
     "BB river facing 75% bet, TT = mid pocket pair", "river_catch"),
    ("river_55_K72_3c8h", "F-F-F-R2.6-F-C", "X-R1.9-C-X-X-X-R6.7", "Ks7d2c3c8h", "5s5d",
     "BB river facing 75% bet, 55 = low pocket pair", "river_catch"),

    # === 6. 同 pair でも board のサブ family による差 ===
    ("jj_T98",       "F-F-F-R2.6-F-C", "X-R1.9", "Ts9d8c", "JsJd", "JJ on T-9-8 (connected, 1 over)", "jj_cross"),
    ("jj_A72",       "F-F-F-R2.6-F-C", "X-R1.9", "As7d2c", "JsJd", "JJ on A-7-2 (1 over, dry)", "jj_cross"),
    ("jj_T22",       "F-F-F-R2.6-F-C", "X-R1.9", "Tc2d2s", "JsJd", "JJ on T-2-2 (paired, 1 over)", "jj_cross"),
    ("jj_222",       "F-F-F-R2.6-F-C", "X-R1.9", "2c2d2s", "JsJd", "JJ on 2-2-2 (paired low)", "jj_cross"),
    ("jj_K22",       "F-F-F-R2.6-F-C", "X-R1.9", "Kc2d2s", "JsJd", "JJ on K-2-2 (paired, K over)", "jj_cross"),

    # === 7. 3 連 overcard ===
    ("44_TJQ",       "F-F-F-R2.6-F-C", "X-R1.9", "TsJdQc", "4s4d", "44 on T-J-Q broadway", "3over"),
    ("55_TJQ",       "F-F-F-R2.6-F-C", "X-R1.9", "TsJdQc", "5s5d", "55 on T-J-Q", "3over"),

    # === 8. TPTK の格下げ ===
    ("AK_AT5",       "F-F-F-R2.6-F-C", "X-R1.9", "AsTd5c", "AhKd", "AKo TPTK on A-T-5", "tptk"),
    ("AK_AT5_mono",  "F-F-F-R2.6-F-C", "X-R1.9", "AhTh5h", "AdKs", "AKo on A-T-5 mono (FD board)", "tptk"),
]


print(f"Edge boundary v2 probe: {len(TARGETS)} spots")
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
