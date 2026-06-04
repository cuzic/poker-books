#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Aggregate flop attack boundary results."""
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
    all_sizes = [(s[0], s[1]) for s in sizes if s[0]]
    return bet * 100, chk * 100, main_size, all_sizes


report = []
report.append("# Flop Attack Boundary Report — 多深度 × 全 position 検証\n\n")
report.append("生成日: 2026-05-26\n\n")
report.append("Cash gametype は 403、MTT 100bb / 50bb / 25bb は新たにアクセス可となった。100bb が cash 相当のプロキシとして使える。\n\n")
report.append("---\n\n")

# B-15: 100bb cash-proxy
report.append("## B-15: 100bb (cash-proxy) flop cbet — 全 position × 標準7板\n\n")
report.append("| pos | board | bet% | size | サイズ詳細 |\n|----|------|------:|-----:|----------|\n")
data_b15 = []
for topic in ["b15_100bb_utg", "b15_100bb_hj", "b15_100bb_co", "b15_100bb_btn", "b15_100bb_sb"]:
    pos = topic.split("_")[-1].upper()
    for s in load(topic):
        m = s["_meta"]
        board = m["request"]["board"]
        bet, chk, sz, all_sz = stats(s)
        sz_s = f"{sz:.0f}%" if sz else "-"
        all_s = " / ".join(f"{s_:.0f}%({f_*100:.0f}%)" for s_, f_ in all_sz[:3])
        report.append(f"| {pos} | `{board}` | {bet:.1f} | {sz_s} | {all_s} |\n")
        data_b15.append({"pos": pos, "board": board, "bet": bet, "size": sz})

# Position 平均
if data_b15:
    by_pos = defaultdict(list)
    for d in data_b15:
        by_pos[d["pos"]].append(d["bet"])
    report.append("\n### Position 別平均 (100bb)\n\n| pos | avg cbet% | n |\n|----|-----:|--:|\n")
    for pos in ["UTG", "HJ", "CO", "BTN", "SB"]:
        if pos in by_pos:
            v = by_pos[pos]
            report.append(f"| {pos} | {sum(v)/len(v):.1f}% | {len(v)} |\n")

# B-16/B-17
for topic_grp, label in [(["b16_50bb_hj", "b16_50bb_btn"], "B-16: 50bb mid-stack"),
                          (["b17_25bb_hj", "b17_25bb_btn"], "B-17: 25bb short stack")]:
    report.append(f"\n\n## {label}\n\n")
    report.append("| pos | board | bet% | size |\n|----|------|------:|-----:|\n")
    for topic in topic_grp:
        pos = topic.split("_")[-1].upper()
        for s in load(topic):
            m = s["_meta"]
            board = m["request"]["board"]
            bet, chk, sz, _ = stats(s)
            sz_s = f"{sz:.0f}%" if sz else "-"
            report.append(f"| {pos} | `{board}` | {bet:.1f} | {sz_s} |\n")

# B-18: depth gradient
report.append("\n\n## B-18: Depth gradient — 同板 × 4 深度\n\n")
report.append("| board | 200bb bet% | 100bb bet% | 50bb bet% | 25bb bet% |\n")
report.append("|------|--------:|--------:|--------:|--------:|\n")
b18 = defaultdict(dict)
for s in load("b18_depth_grad"):
    m = s["_meta"]
    board = m["request"]["board"]
    depth = m["request"]["depth"]
    bet, _, sz, _ = stats(s)
    b18[board][depth] = (bet, sz)

for board in sorted(b18.keys()):
    row = [f"`{board}`"]
    for d in ["200.125", "100.125", "50.125", "25.125"]:
        if d in b18[board]:
            bet, sz = b18[board][d]
            sz_s = f" ({sz:.0f}%)" if sz else ""
            row.append(f"{bet:.1f}{sz_s}")
        else:
            row.append("-")
    report.append("| " + " | ".join(row) + " |\n")

# B-19: special boards @ 100bb
report.append("\n\n## B-19: 特殊板 @ 100bb (cash-proxy)\n\n")
report.append("| board | bet% | size | type |\n|------|------:|-----:|----|\n")
for s in load("b19_100bb_special"):
    m = s["_meta"]
    board = m["request"]["board"]
    note = m.get("note", "")[:40]
    bet, _, sz, _ = stats(s)
    sz_s = f"{sz:.0f}%" if sz else "-"
    report.append(f"| `{board}` | {bet:.1f} | {sz_s} | {note} |\n")

(ROOT / "FLOP_ATTACK_REPORT.md").write_text("".join(report))
total = sum(1 for _ in ROOT.glob("b1[5-9]_*/*.json"))
print(f"Wrote FLOP_ATTACK_REPORT.md ({total} spots)")
