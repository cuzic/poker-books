#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Aggregate boundary4 results — wide-board boundary mapping."""
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


def stats(spot):
    bet = sum(a["total_frequency"] for a in spot["action_solutions"]
              if a["action"]["type"] in ("BET", "RAISE"))
    chk = sum(a["total_frequency"] for a in spot["action_solutions"]
              if a["action"]["type"] == "CHECK")
    sizes = sorted(
        [(float(a["action"]["betsize_by_pot"]) * 100 if a["action"].get("betsize_by_pot") else None,
          a["total_frequency"]) for a in spot["action_solutions"]
         if a["action"]["type"] in ("BET", "RAISE")],
        key=lambda x: -x[1])
    main_size = sizes[0][0] if sizes and sizes[0][0] else None
    return bet * 100, chk * 100, main_size


def meta(s):
    return s["_meta"]


report = []
report.append("# Boundary Study Report v4 — wide-board mapping\n\n")
report.append("生成日: 2026-05-26\n\n")
report.append("65 spot 試行（6 シナリオ）の境界精密測定\n\n")
report.append("---\n\n")


# B-3 grad: multiway SB donk gradient
spots = load("b3_grad")
report.append(f"## B-3 拡張: マルチウェイ SB donk グラデーション (n={len(spots)})\n\n")
report.append("**境界仮説**: 連結度（gap）× high card で donk 率\n\n")
report.append("| board | high | gap | donk% | サイズ |\n")
report.append("|------|------|----:|------:|-----:|\n")
results = []
for s in spots:
    m = meta(s)
    board = m["request"]["board"]
    flop = board[:6]
    ranks = [flop[i*2] for i in range(3)]
    order = "23456789TJQKA"
    rvals = sorted([order.index(r) for r in ranks], reverse=True)
    gap = rvals[0] - rvals[2]
    high = ranks[0] if rvals[0] == order.index(ranks[0]) else ranks[1] if rvals[0] == order.index(ranks[1]) else ranks[2]
    high = order[rvals[0]]
    bet, chk, sz = stats(s)
    sz_s = f"{sz:.0f}%" if sz else "-"
    note = m.get("note", "")
    report.append(f"| `{flop}` | {high} | {gap} | {bet:.1f} | {sz_s} |\n")
    results.append({"board": flop, "high": high, "gap": gap, "donk": bet})

# Summarize by high card group
if results:
    report.append("\n### high card 別\n\n| high group | avg donk% | n |\n|---|---:|--:|\n")
    by_high = defaultdict(list)
    for r in results:
        if r["high"] in ("A",): by_high["A"].append(r["donk"])
        elif r["high"] in ("K",): by_high["K"].append(r["donk"])
        elif r["high"] in ("Q",): by_high["Q"].append(r["donk"])
        elif r["high"] in ("J", "T"): by_high["J/T"].append(r["donk"])
        elif r["high"] in ("9", "8"): by_high["9/8"].append(r["donk"])
        else: by_high["<8"].append(r["donk"])
    for k in ["A", "K", "Q", "J/T", "9/8", "<8"]:
        if k in by_high:
            v = by_high[k]
            report.append(f"| {k} | {sum(v)/len(v):.1f}% | {len(v)} |\n")


# B-7 kxx grad: Turn cbet size by turn card
spots = load("b7_kxx_grad")
report.append(f"\n\n## B-7 拡張: Kxx ターン cbet サイズ × turn card (n={len(spots)})\n\n")
report.append("**仮説**: Kxx+5=101%, Kxx+Q=276% の境界はどこ？\n\n")
report.append("| flop | turn | bet% | サイズ | 解釈 |\n")
report.append("|-----|------|------:|------:|-----|\n")
for s in spots:
    m = meta(s)
    board = m["request"]["board"]
    flop = board[:6]
    turn = board[6:8]
    bet, chk, sz = stats(s)
    sz_s = f"{sz:.0f}%" if sz else "-"
    report.append(f"| `{flop}` | {turn} | {bet:.1f} | {sz_s} | {m.get('note','')[:30]} |\n")


# B-1 pair grad: turn donk near-boundary
spots = load("b1_pair_grad")
report.append(f"\n\n## B-1 拡張: ターン donk 境界 (n={len(spots)})\n\n")
report.append("| flop+turn | donk% | サイズ | 解釈 |\n")
report.append("|----|------:|------:|-----|\n")
for s in spots:
    m = meta(s)
    board = m["request"]["board"]
    bet, chk, sz = stats(s)
    sz_s = f"{sz:.0f}%" if sz else "-"
    report.append(f"| `{board}` | {bet:.1f} | {sz_s} | {m.get('note','')[:35]} |\n")


# B-9 paired flops
spots = load("b9_paired_flop")
report.append(f"\n\n## B-9 NEW: ペアフロップ完全未調査領域 (n={len(spots)})\n\n")
report.append("| board | line | bet/donk/probe% | サイズ | 解釈 |\n")
report.append("|------|------|------:|------:|-----|\n")
for s in spots:
    m = meta(s)
    board = m["request"]["board"]
    req = m["request"]
    line = f"pre={req['preflop_actions'][:20]} fl={req['flop_actions']} tn={req['turn_actions']}"
    bet, chk, sz = stats(s)
    sz_s = f"{sz:.0f}%" if sz else "-"
    report.append(f"| `{board}` | {line} | {bet:.1f} | {sz_s} | {m.get('note','')[:30]} |\n")


# B-10 mono
spots = load("b10_mono")
report.append(f"\n\n## B-10 NEW: モノフロップ完全未調査領域 (n={len(spots)})\n\n")
report.append("| board | line | bet% | サイズ | 解釈 |\n")
report.append("|------|------|------:|------:|-----|\n")
for s in spots:
    m = meta(s)
    board = m["request"]["board"]
    req = m["request"]
    line = f"fl={req['flop_actions']} tn={req['turn_actions']}"
    bet, chk, sz = stats(s)
    sz_s = f"{sz:.0f}%" if sz else "-"
    report.append(f"| `{board}` | {line} | {bet:.1f} | {sz_s} | {m.get('note','')[:30]} |\n")


# B-8 near zero
spots = load("b8_near_zero")
report.append(f"\n\n## B-8 拡張: probe near-zero 境界 (n={len(spots)})\n\n")
report.append("| board | turn | probe% | サイズ | 解釈 |\n")
report.append("|------|------|------:|------:|-----|\n")
for s in spots:
    m = meta(s)
    board = m["request"]["board"]
    flop = board[:6]
    turn = board[6:8]
    bet, chk, sz = stats(s)
    sz_s = f"{sz:.0f}%" if sz else "-"
    report.append(f"| `{flop}` | {turn} | {bet:.1f} | {sz_s} | {m.get('note','')[:35]} |\n")


(ROOT / "BOUNDARY_REPORT4.md").write_text("".join(report))
print(f"Wrote BOUNDARY_REPORT4.md ({sum(1 for _ in (ROOT/'b3_grad').glob('*.json')) + sum(1 for _ in (ROOT/'b7_kxx_grad').glob('*.json')) + sum(1 for _ in (ROOT/'b1_pair_grad').glob('*.json')) + sum(1 for _ in (ROOT/'b9_paired_flop').glob('*.json')) + sum(1 for _ in (ROOT/'b10_mono').glob('*.json')) + sum(1 for _ in (ROOT/'b8_near_zero').glob('*.json'))} spots)")
