#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""網羅的 probe — board family と hand strength 境界の細分化用。

設計:
1. 各 high card (A〜2) × 3 patterns (dry / connected / paired)
2. paired 種類 (top/mid/bottom paired)
3. suit pattern 変化 (mono/2-tone/rainbow)
4. ace-high / king-high 詳細
"""
from __future__ import annotations
import json, time
from pathlib import Path
import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN = (SCRIPT_DIR / ".token").read_text().strip()
GAID = (SCRIPT_DIR / ".google_anal_id").read_text().strip()
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_exhaustive")
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

# Exhaustive board set
BOARDS = []

# (1) High card × 3 patterns (rainbow):
HIGHS = "AKQJT98765432"
# Skip already probed boards
ALREADY_PROBED = set()
for d in [Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_drill_btn_cbet"),
          Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_boundary_gradient")]:
    for f in d.glob("*.json"):
        try:
            saved = json.loads(f.read_text())
            b = (saved.get("flop") or saved.get("board") or "").lower()
            if b:
                ALREADY_PROBED.add(b)
        except: pass

def add(board, label):
    b = board.lower().replace(" ", "")
    if b not in ALREADY_PROBED and len({b[0:2], b[2:4], b[4:6]}) == 3:
        BOARDS.append((b, label))

# Dry boards (no pair, no connector, rainbow): X-low-low
# Use 7-2 as low cards to ensure dry
for h in "AKQJT9876":
    if h in "76": continue  # 7-low-low overlaps
    add(f"{h}s7d2c", f"{h}_dry")  # high s + 7d + 2c, rainbow

# Connected boards (high + connected mid-low): X-Y-Z where X=Y+1=Z+2
# already have 9s8d7c, 6s7d8c, 4s5d6c, 2s3d4c, tsjdqc, ahkdqc
# Add: 5-high connected, 7-high connected, J-high connected, A-high connected
add("5s4d3c", "5_connect")  # 5-4-3
add("7s6d5c", "7_connect")
add("jsts9c", "J_connect")  # J-T-9
add("AsKdQc", "A_broadway_max")  # AKQ
add("ksqdjc", "K_broadway")
add("qsjdtc", "Q_broadway")

# Paired (XX-low, paired high)
for h in "AKQJT98765432":
    if h in "K54Q":  # already have KsKd4c, kskd9c, asAd4c (from earlier)
        continue
    if h == "2":
        add(f"{h}s{h}d4c", f"pair_{h}")
    else:
        add(f"{h}s{h}d2c", f"pair_{h}")  # XX-2c (rainbow)

# Paired-top variation (top card paired) — exists in earlier
# Paired-mid (mid card paired): low-X-X
add("9s4d4c", "mid_pair_4")
add("8s7d7c", "mid_pair_7")
add("ts8d8c", "mid_pair_8")

# Suit pattern: Ks9d4c rainbow vs Ks9s4c 2-tone vs Ks9s4s mono
add("ks9s4s", "Kdry_mono")  # monotone (3 spades on K-high)
add("ks9s4d", "Kdry_2tone_ks") # 2-tone (K and 9 spade)
add("ks9d4s", "Kdry_2tone_ks2") # 2-tone (K and 4 spade)

# Ace-high suit pattern
add("as9s4s", "Adry_mono")
add("as9s4d", "Adry_2tone")

# Same high card, varied low-low: A-high spread
add("as5d2c", "A_5_low")
add("as8d3c", "A_8_3")
add("astd5c", "A_T_5")

# Pure low connected (gap variations)
add("8s5d4c", "low_gap1")
add("7s6d4c", "low_gap1b")
add("6s5d4c", "low_straight")  # 4-5-6 straight pos
add("4s3d2c_dup", "skip")  # placeholder

# Middle straight area
add("9s7d6c", "9_gap1_low")
add("ts8d6c", "T_gap_lows")

print(f"Probe targets: {len(BOARDS)} new boards (already probed: {len(ALREADY_PROBED)})")

n_ok = n_fail = 0
start = time.time()
for i, (board, label) in enumerate(BOARDS, 1):
    if time.time() - start > 540:
        print("⏰ time cap"); break
    out = OUT_DIR / f"ex_{label}_{board}.json"
    if out.exists(): continue
    params = {
        "gametype": "Cash6mGeneral_6mNL25R25",
        "depth": "100",
        "preflop_actions": "F-F-F-R2.6-F-C",
        "flop_actions": "X",
        "board": board,
    }
    print(f"[{i}/{len(BOARDS)}] {board} ({label})", end=" ")
    try:
        r = httpx.get(API, params=params, headers=HEADERS, timeout=20.0)
        if r.status_code == 200:
            data = r.json()
            out.write_text(json.dumps({"flop": board, "label": label, "data": data}, ensure_ascii=False))
            actions = data.get("action_solutions", [])
            cbet = sum(a["total_frequency"] for a in actions if a["action"]["type"] in ("BET","RAISE"))
            sizes = sorted([(a["action"]["betsize"], a["total_frequency"]) for a in actions if a["action"]["type"] in ("BET","RAISE")], key=lambda x:-x[1])
            top = sizes[0] if sizes else ("-", 0)
            print(f"✓ cbet={cbet*100:.0f}% size={top[0]}({top[1]*100:.0f}%)")
            n_ok += 1
        elif r.status_code == 401:
            print(f"✗ TOKEN EXPIRED"); break
        else:
            print(f"✗ {r.status_code}: {r.text[:60]}")
            n_fail += 1
    except Exception as e:
        print(f"✗ {e}")
        n_fail += 1
    time.sleep(0.25)

print(f"\nDone: {n_ok}/{len(BOARDS)}, {n_fail} failed, {time.time()-start:.0f}s")
