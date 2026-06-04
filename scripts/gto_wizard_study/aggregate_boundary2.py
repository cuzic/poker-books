#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Aggregate boundary2 results into BOUNDARY_REPORT2.md."""
from __future__ import annotations
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study")


def load(topic):
    p = ROOT / topic
    if not p.exists():
        return []
    files = sorted(p.glob("*.json"))
    out = []
    for f in files:
        out.append(json.loads(f.read_text()))
    return out


def stats(spot):
    bet = sum(a["total_frequency"] for a in spot["action_solutions"]
              if a["action"]["type"] in ("BET", "RAISE"))
    check = sum(a["total_frequency"] for a in spot["action_solutions"]
                if a["action"]["type"] == "CHECK")
    sizes = []
    for a in spot["action_solutions"]:
        if a["action"]["type"] in ("BET", "RAISE"):
            bp = a["action"].get("betsize_by_pot")
            if bp:
                sizes.append((float(bp), a["total_frequency"]))
    sizes.sort(key=lambda x: -x[1])
    main_size = sizes[0][0] * 100 if sizes else None
    return bet * 100, check * 100, main_size


def meta(spot):
    return spot["_meta"]


report = []
report.append("# Boundary Study Report v2 — paired-turn / multiway / river card\n\n")
report.append("生成日: 2026-05-25\n\n")
report.append("46/48 spots (2 failed: duplicate cards in board)\n\n")
report.append("---\n\n")

# ==================== B-1x: paired turn / str8 turn ====================
report.append("## B-1 拡張: ペア化ターン / ストレート完成ターン の boundary\n\n")
report.append("**仮説**: 一部の board pair turn / str8 turn で OOP donk が >20%\n\n")

for topic, label in [("b1_pair_top", "Top pair turn (board pair)"),
                      ("b1_pair_mid", "Mid pair turn"),
                      ("b1_pair_bot", "Bottom pair turn"),
                      ("b1_str8", "Straight completing / draw turn")]:
    spots = load(topic)
    spots = [s for s in spots if meta(s)["id"].startswith("b1x")]
    if not spots:
        continue
    report.append(f"### {label} (n={len(spots)})\n\n")
    report.append("| flop | turn | donk% | check% | size |\n")
    report.append("|------|------|------:|------:|-----:|\n")
    for s in spots:
        m = meta(s)
        board = m["request"]["board"]
        flop = board[:6]
        turn = board[6:8]
        bet, check, size = stats(s)
        size_s = f"{size:.0f}%" if size else "-"
        report.append(f"| `{flop}` | `{turn}` | **{bet:.1f}** | {check:.1f} | {size_s} |\n")
    bets = [stats(s)[0] for s in spots]
    if bets:
        report.append(f"\n**Summary**: mean donk={sum(bets)/len(bets):.1f}%, max={max(bets):.1f}%, min={min(bets):.1f}%\n\n")

# Find pattern: high donk turns
all_b1x = []
for topic in ["b1_pair_top", "b1_pair_mid", "b1_pair_bot", "b1_str8"]:
    for s in load(topic):
        if meta(s)["id"].startswith("b1x"):
            m = meta(s)
            bet, _, _ = stats(s)
            all_b1x.append({
                "id": m["id"], "topic": topic, "board": m["request"]["board"],
                "bet": bet, "note": m.get("note", "")
            })

report.append("\n### ターン donk > 5% の全例外リスト\n\n")
above5 = sorted([d for d in all_b1x if d["bet"] > 5], key=lambda d: -d["bet"])
report.append("| board | donk% | topic |\n|------|------:|-------|\n")
for d in above5:
    report.append(f"| `{d['board']}` | **{d['bet']:.1f}** | {d['topic']} |\n")

# ==================== B-3x: multiway from BTN / CO ====================
report.append("\n\n## B-3 拡張: BTN/CO マルチウェイ SB donk\n\n")

# Combined with original B-3 data
report.append("### HJ vs CO vs BTN open multiway 比較\n\n")
report.append("| board | HJ pos donk% | CO pos donk% | BTN pos donk% |\n")
report.append("|-------|-------------:|-------------:|-------------:|\n")

# Build map: board → {HJ, CO, BTN}
mw_data = defaultdict(dict)
for s in load("b3_mw_donk"):
    m = meta(s)
    board = m["request"]["board"]
    bet, _, _ = stats(s)
    mw_data[board]["HJ"] = bet
for s in load("b3_btn_mw"):
    m = meta(s)
    board = m["request"]["board"]
    bet, _, _ = stats(s)
    mw_data[board]["BTN"] = bet
for s in load("b3_co_mw"):
    m = meta(s)
    board = m["request"]["board"]
    bet, _, _ = stats(s)
    mw_data[board]["CO"] = bet

for board in sorted(mw_data.keys()):
    d = mw_data[board]
    hj = f"{d['HJ']:.1f}" if "HJ" in d else "-"
    co = f"{d['CO']:.1f}" if "CO" in d else "-"
    bt = f"{d['BTN']:.1f}" if "BTN" in d else "-"
    report.append(f"| `{board}` | {hj} | {co} | {bt} |\n")

# Position summary
report.append("\n### Position別平均\n\n| pos | avg donk% | n |\n|----|-----:|--:|\n")
for pos in ["HJ", "CO", "BTN"]:
    vals = [d[pos] for d in mw_data.values() if pos in d]
    if vals:
        report.append(f"| {pos} | {sum(vals)/len(vals):.1f}% | {len(vals)} |\n")

# ==================== B-5: river give-up by river card ====================
report.append("\n\n## B-5 拡張: turn give-up 後 river の card pattern\n\n")
spots = load("b5_river_giveup")
report.append(f"スポット数: {len(spots)}\n\n")

# Group by flop
by_flop = defaultdict(list)
for s in spots:
    m = meta(s)
    board = m["request"]["board"]
    flop_turn = board[:8]
    river = board[8:10]
    bet, _, size = stats(s)
    by_flop[flop_turn].append({"river": river, "bet": bet, "size": size, "note": m.get("note","")})

for flop in sorted(by_flop.keys()):
    report.append(f"### Flop+Turn: `{flop}`\n\n")
    report.append("| river | lead% | size% | note |\n|-------|------:|------:|------|\n")
    for d in sorted(by_flop[flop], key=lambda x: -x["bet"]):
        sz = f"{d['size']:.0f}" if d['size'] else "-"
        report.append(f"| `{d['river']}` | **{d['bet']:.1f}** | {sz} | {d['note'][:40]} |\n")
    report.append("\n")

(ROOT / "BOUNDARY_REPORT2.md").write_text("".join(report))
print(f"Wrote BOUNDARY_REPORT2.md")
