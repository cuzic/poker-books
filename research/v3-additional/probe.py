#!/usr/bin/env python3
"""
probe.py — GTO Wizard API 動作確認

最小限の API call で:
1. 認証
2. game type の正しさ (Cash 100bb 6-max)
3. preflop spot レスポンス形式

を確認する。BB vs BTN open の defense を 1 call で確認。

使い方:
  source .env && python3 probe.py
"""
import os, sys, json
from pathlib import Path

# vol2-cash-postflop/gto_api.py を path に追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vol2-cash-postflop"))
os.environ["GT"] = os.environ.get("GT_CASH_100BB", "Cash6mTest_6mNL100R2")

from gto_api import api_get, action_dist, update_session

update_session()  # token 再読込

print(f"GT = {os.environ['GT']}")
print(f"TOKEN set: {bool(os.environ.get('TOKEN'))}")
print(f"GWCLIENTID set: {bool(os.environ.get('GWCLIENTID'))}")
print()

# probe: BB vs BTN open (R2) を取得 (Vol2 既存 script と同じ sizing)
# pf = "F-F-F-R2-F" は UTG-HJ-CO-fold, BTN raise 2.0, SB fold → BB の defense
pf = "F-F-F-R2-F"
print(f"Probing: BB vs BTN open (pf={pf!r}) ...")
sols = api_get(board="", flop_actions="", pf=pf, depth=100)
if not sols:
    print("R2 failed, trying R2.5...")
    pf = "F-F-F-R2.5-F"
    print(f"Probing: BB vs BTN open (pf={pf!r}) ...")
    sols = api_get(board="", flop_actions="", pf=pf, depth=100)

if not sols:
    print("ERROR: API returned None", file=sys.stderr)
    sys.exit(1)

print()
print("=== Response keys ===")
print(list(sols.keys()))
print()

# action_solutions を取得
action_sols = sols.get("solutions", []) or sols.get("action_solutions", [])
print(f"=== Top-level action distribution (n={len(action_sols)}) ===")
for a in action_dist(action_sols)[:10]:
    print(f"  {a['code']:<15} freq={a['freq']:.4f}  combos={a['combos']}")

# hand_solutions も確認 (個別ハンド頻度)
hand_sols = sols.get("hand_solutions", [])
print()
print(f"=== Hand solutions count: {len(hand_sols)} ===")
if hand_sols:
    # 最初の 5 ハンドを表示
    for h in hand_sols[:5]:
        hand = h.get("hand_combo", "?")
        actions = h.get("actions", [])
        action_str = ", ".join(f"{a['code']}={a['frequency']:.2f}" for a in actions[:5])
        print(f"  {hand}: {action_str}")

print()
print("=== Save raw response ===")
out_path = Path(__file__).parent / "findings"
out_path.mkdir(exist_ok=True)
with open(out_path / "probe_bb_vs_btn.json", "w") as f:
    json.dump(sols, f, ensure_ascii=False, indent=2)
print(f"Saved → {out_path / 'probe_bb_vs_btn.json'}")
print()
print("✅ Probe OK")
