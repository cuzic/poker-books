#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Aggregate boundary study results into focused report."""
from __future__ import annotations
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study")


def load(topic):
    p = ROOT / topic
    if not p.exists():
        return []
    return [json.loads(f.read_text()) for f in sorted(p.glob("*.json"))]


def bet_freq(spot):
    return sum(a["total_frequency"] for a in spot["action_solutions"]
               if a["action"]["type"] in ("BET", "RAISE"))


def check_freq(spot):
    return sum(a["total_frequency"] for a in spot["action_solutions"]
               if a["action"]["type"] == "CHECK")


def bet_size(spot):
    """Return dominant bet size (% pot) or None."""
    sizes = []
    for a in spot["action_solutions"]:
        if a["action"]["type"] in ("BET", "RAISE"):
            bp = a["action"].get("betsize_by_pot")
            if bp:
                sizes.append((float(bp), a["total_frequency"]))
    if not sizes:
        return None
    sizes.sort(key=lambda x: -x[1])
    return sizes[0][0] * 100


def meta(spot):
    return spot["_meta"]


def classify_board(board):
    """Return (high_card, connectedness, suit_pattern, has_pair)."""
    flop = board[:6]
    ranks = [flop[i*2] for i in range(3)]
    suits = [flop[i*2+1] for i in range(3)]
    order = "23456789TJQKA"
    rvals = sorted([order.index(r) for r in ranks], reverse=True)
    pair = len(set(ranks)) < 3
    suit_count = len(set(suits))
    suit_pattern = "mono" if suit_count == 1 else "2tone" if suit_count == 2 else "rainbow"
    gap = rvals[0] - rvals[2]
    if gap <= 4:
        conn = "connected"
    elif gap <= 7:
        conn = "gap"
    else:
        conn = "disconnected"
    high = ranks[rvals.index(rvals[0])] if False else "23456789TJQKA"[rvals[0]]
    return {"high": high, "connectedness": conn, "suit": suit_pattern, "paired": pair, "ranks": rvals}


report = []

report.append("# Boundary Study Report — GTO Wizard 検証\n\n")
report.append(f"生成日: 2026-05-25\n\n")

# B-3: Multiway SB donk
spots = load("b3_mw_donk")
report.append(f"## B-3: マルチウェイ SB donk × board (n={len(spots)})\n\n")
report.append("仮説: 弱コネクト × middle range で 20-30%、その他 5-10%\n\n")
report.append("| board | high | conn | suit | bet% | size% | note |\n")
report.append("|-------|------|------|------|-----:|------:|------|\n")
results_b3 = []
for s in spots:
    m = meta(s)
    board = m["request"]["board"]
    bc = classify_board(board)
    bf = bet_freq(s) * 100
    sz = bet_size(s)
    sz_s = f"{sz:.0f}" if sz else "-"
    report.append(f"| `{board}` | {bc['high']} | {bc['connectedness']} | {bc['suit']} | {bf:.1f} | {sz_s} | {m.get('note','')} |\n")
    results_b3.append((board, bc, bf))

# Summary by connectedness
if results_b3:
    by_conn = defaultdict(list)
    for board, bc, bf in results_b3:
        by_conn[bc["connectedness"]].append(bf)
    report.append("\n### 連結度別平均\n\n| connectedness | avg bet% | n |\n|----|-----:|--:|\n")
    for conn in ["connected", "gap", "disconnected"]:
        if conn in by_conn:
            v = by_conn[conn]
            report.append(f"| {conn} | {sum(v)/len(v):.1f}% | {len(v)} |\n")

# B-4: XX-XX river position
spots = load("b4_xxxx_river")
report.append(f"\n\n## B-4: XX-XX river BB lead × position (n={len(spots)})\n\n")
report.append("仮説: BTN > CO > HJ > UTG の順で OOP river lead 率が高い\n\n")
report.append("| position | board | river card | bet% | size% | note |\n")
report.append("|----------|-------|------------|-----:|------:|------|\n")
results_b4 = []
for s in spots:
    m = meta(s)
    board = m["request"]["board"]
    pre = m["request"]["preflop_actions"]
    if pre.startswith("F-F-F-R"):
        pos = "BTN"
    elif pre.startswith("F-F-R"):
        pos = "CO"
    elif pre.startswith("F-R"):
        pos = "HJ"
    elif pre.startswith("R"):
        pos = "UTG"
    else:
        pos = "?"
    bf = bet_freq(s) * 100
    sz = bet_size(s)
    sz_s = f"{sz:.0f}" if sz else "-"
    river_card = board[8:10] if len(board) >= 10 else "?"
    report.append(f"| {pos} | `{board}` | {river_card} | {bf:.1f} | {sz_s} | {m.get('note','')} |\n")
    results_b4.append((pos, board, bf))

if results_b4:
    by_pos = defaultdict(list)
    for pos, board, bf in results_b4:
        by_pos[pos].append(bf)
    report.append("\n### Position 別平均\n\n| pos | avg bet% | n |\n|----|-----:|--:|\n")
    for pos in ["UTG", "HJ", "CO", "BTN"]:
        if pos in by_pos:
            v = by_pos[pos]
            report.append(f"| {pos} | {sum(v)/len(v):.1f}% | {len(v)} |\n")

# B-1: Turn donk variations
for tk in ["b1_turn_donk", "b1_turn_donk_pair", "b1_turn_donk_str8", "b1_turn_donk_flush",
           "b1_turn_donk_overcard", "b1_turn_donk_paired", "b1_turn_donk_mono"]:
    spots = load(tk)
    if not spots:
        continue
    report.append(f"\n\n## B-1: ターン donk ({tk}) n={len(spots)}\n\n")
    report.append("| line / board | check% | bet% | bet size |\n")
    report.append("|-----|------:|-----:|------:|\n")
    for s in spots:
        m = meta(s)
        board = m["request"]["board"]
        cf = check_freq(s) * 100
        bf = bet_freq(s) * 100
        sz = bet_size(s)
        sz_s = f"{sz:.0f}%" if sz else "-"
        report.append(f"| `{board}` ({m.get('note','')[:30]}) | {cf:.1f} | {bf:.1f} | {sz_s} |\n")

# Aggregate B-1 across all turn donk topics
all_turn_donk = []
for tk in ["b1_turn_donk", "b1_turn_donk_pair", "b1_turn_donk_str8", "b1_turn_donk_flush",
           "b1_turn_donk_overcard", "b1_turn_donk_paired", "b1_turn_donk_mono"]:
    for s in load(tk):
        all_turn_donk.append({"topic": tk, "bet": bet_freq(s) * 100, "board": meta(s)["request"]["board"]})

if all_turn_donk:
    report.append(f"\n\n## B-1 サマリ: 全ターン donk スポット (n={len(all_turn_donk)})\n\n")
    bets = [d["bet"] for d in all_turn_donk]
    report.append(f"- mean bet%: {sum(bets)/len(bets):.2f}%\n")
    report.append(f"- max bet%: {max(bets):.2f}%  → board: {max(all_turn_donk, key=lambda d: d['bet'])['board']}\n")
    report.append(f"- min bet%: {min(bets):.2f}%\n")
    above_5 = [d for d in all_turn_donk if d["bet"] > 5]
    report.append(f"- bet% > 5% の spot: {len(above_5)}/{len(all_turn_donk)}\n")
    if above_5:
        report.append("\n### 5% 超過例外:\n\n")
        for d in above_5:
            report.append(f"- `{d['board']}` ({d['topic']}): {d['bet']:.1f}%\n")

(ROOT / "BOUNDARY_REPORT.md").write_text("".join(report))
print(f"Wrote BOUNDARY_REPORT.md")
