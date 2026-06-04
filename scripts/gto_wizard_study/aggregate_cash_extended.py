#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Aggregate cash extended findings (B-25 through B-31)."""
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
    fld = sum(a["total_frequency"] for a in spot["action_solutions"]
              if a["action"]["type"] == "FOLD")
    cal = sum(a["total_frequency"] for a in spot["action_solutions"]
              if a["action"]["type"] == "CALL")
    sizes = sorted(
        [(float(a["action"]["betsize_by_pot"]) * 100 if a["action"].get("betsize_by_pot") else None,
          a["total_frequency"]) for a in spot["action_solutions"]
         if a["action"]["type"] in ("BET", "RAISE")],
        key=lambda x: -x[1])
    main_size = sizes[0][0] if sizes and sizes[0][0] else None
    return {"bet": bet*100, "check": chk*100, "fold": fld*100, "call": cal*100, "size": main_size}


def parse_pos(pre):
    if pre.startswith("F-F-F-R"): return "BTN"
    if pre.startswith("F-F-R"): return "CO"
    if pre.startswith("F-R"): return "HJ"
    if pre.startswith("R"): return "UTG"
    if pre.startswith("F-F-F-F-R"): return "SB"
    if pre.startswith("F-F-F-F-C"): return "SB(limp)"
    return "?"


report = []
report.append("# Cash 拡張調査レポート (B-25 〜 B-31)\n\n")
report.append("生成日: 2026-05-27\n\n")
report.append("Cash6mGeneral_6mNL25R25 @ 100bb の完全境界調査。67 spots を対象。\n\n")
report.append("---\n\n")

# B-25: 特殊 boards
report.append("## B-25: Cash 特殊 boards × 全 position\n\n")
for sub_topic in ["b25_cash_paired", "b25_cash_mono", "b25_cash_wet"]:
    spots = load(sub_topic)
    if not spots: continue
    label = {"b25_cash_paired": "ペアフロップ", "b25_cash_mono": "モノフロップ", "b25_cash_wet": "ウェット/スーパーウェット"}[sub_topic]
    report.append(f"\n### {label}\n\n")
    report.append("| pos | board | cbet% | size |\n|----|------|------:|------:|\n")
    for s in spots:
        m = s["_meta"]
        board = m["request"]["board"]
        pre = m["request"]["preflop_actions"]
        pos = parse_pos(pre)
        st = stats(s)
        sz = f"{st['size']:.0f}%" if st['size'] else "-"
        report.append(f"| {pos} | `{board}` | {st['bet']:.1f} | {sz} |\n")

# B-26: 3BP
spots = load("b26_cash_3bp")
report.append(f"\n\n## B-26: Cash 3BP HJvBB flop cbet (n={len(spots)})\n\n")
report.append("| board | cbet% | size | type |\n|------|------:|------:|----|\n")
for s in spots:
    m = s["_meta"]
    board = m["request"]["board"]
    st = stats(s)
    sz = f"{st['size']:.0f}%" if st['size'] else "-"
    note = m.get("note", "")
    report.append(f"| `{board}` | {st['bet']:.1f} | {sz} | {note} |\n")

# B-27: OOP defense
spots = load("b27_cash_oop_def")
report.append(f"\n\n## B-27: Cash OOP defense (BB response to IP cbet) n={len(spots)}\n\n")
report.append("| board | fold% | call% | raise% | bet% (cbet中の) | note |\n|------|------:|------:|------:|------:|----|\n")
for s in spots:
    m = s["_meta"]
    board = m["request"]["board"]
    st = stats(s)
    note = m.get("note", "")
    report.append(f"| `{board}` | {st['fold']:.1f} | {st['call']:.1f} | {st['bet']:.1f} | - | {note} |\n")

# B-28: Turn cbet
spots = load("b28_cash_turn")
report.append(f"\n\n## B-28: Cash IP turn cbet (after cbet-call) n={len(spots)}\n\n")
report.append("| board (5 cards) | turn bet% | size | note |\n|------|------:|------:|----|\n")
for s in spots:
    m = s["_meta"]
    board = m["request"]["board"]
    st = stats(s)
    sz = f"{st['size']:.0f}%" if st['size'] else "-"
    note = m.get("note", "")
    report.append(f"| `{board}` | {st['bet']:.1f} | {sz} | {note} |\n")

# B-29: multiway
spots = load("b29_cash_multiway")
report.append(f"\n\n## B-29: Cash 3-way SB donk n={len(spots)}\n\n")
report.append("| board | donk% | size | note |\n|------|------:|------:|----|\n")
for s in spots:
    m = s["_meta"]
    board = m["request"]["board"]
    st = stats(s)
    sz = f"{st['size']:.0f}%" if st['size'] else "-"
    note = m.get("note", "")
    report.append(f"| `{board}` | {st['bet']:.1f} | {sz} | {note} |\n")

# B-30: limp pot
spots = load("b30_cash_limp")
report.append(f"\n\n## B-30: Cash SB limp pot (BB flop first) n={len(spots)}\n\n")
report.append("| board | BB bet% | size | note |\n|------|------:|------:|----|\n")
for s in spots:
    m = s["_meta"]
    board = m["request"]["board"]
    st = stats(s)
    sz = f"{st['size']:.0f}%" if st['size'] else "-"
    note = m.get("note", "")
    report.append(f"| `{board}` | {st['bet']:.1f} | {sz} | {note} |\n")

# B-31: river
spots = load("b31_cash_river")
report.append(f"\n\n## B-31: Cash river (XX-XX 経路 / turn give-up) n={len(spots)}\n\n")
report.append("| line | board (5) | BB lead% | size | note |\n|----|------|------:|------:|----|\n")
for s in spots:
    m = s["_meta"]
    board = m["request"]["board"]
    pre = m["request"]["preflop_actions"]
    flop = m["request"]["flop_actions"]
    line = "XX-XX" if flop == "X-X" else "turn-give-up"
    pos = parse_pos(pre)
    st = stats(s)
    sz = f"{st['size']:.0f}%" if st['size'] else "-"
    note = m.get("note", "")
    report.append(f"| {line}/{pos} | `{board}` | {st['bet']:.1f} | {sz} | {note} |\n")

(ROOT / "CASH_EXTENDED_REPORT.md").write_text("".join(report))
total = sum(1 for _ in ROOT.glob("b2[5-9]_*/*.json")) + sum(1 for _ in ROOT.glob("b3[0-1]_*/*.json"))
print(f"Wrote CASH_EXTENDED_REPORT.md ({total} spots)")
