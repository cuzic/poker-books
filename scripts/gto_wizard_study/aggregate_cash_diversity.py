#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Aggregate cash diversity boundary results (B-32 through B-40)."""
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
    sizes = sorted(
        [(float(a["action"]["betsize_by_pot"]) * 100 if a["action"].get("betsize_by_pot") else None,
          a["total_frequency"]) for a in spot["action_solutions"]
         if a["action"]["type"] in ("BET", "RAISE")],
        key=lambda x: -x[1])
    main_size = sizes[0][0] if sizes and sizes[0][0] else None
    return {"bet": bet*100, "size": main_size}


def board_features(board):
    """Extract (high, mid, low, gap, suit_pattern, paired, mono)."""
    cards = [board[i*2:i*2+2] for i in range(3)]
    ranks = [c[0] for c in cards]
    suits = [c[1] for c in cards]
    order = "23456789TJQKA"
    rvals = sorted([order.index(r) for r in ranks], reverse=True)
    paired = len(set(ranks)) < 3
    suit_pattern = "mono" if len(set(suits)) == 1 else ("2tone" if len(set(suits)) == 2 else "rainbow")
    gap = rvals[0] - rvals[2]
    high = "23456789TJQKA"[rvals[0]]
    return {"high": high, "gap": gap, "suit": suit_pattern, "paired": paired,
            "ranks_str": "-".join(["23456789TJQKA"[v] for v in rvals])}


report = []
report.append("# Cash Flop CBet 境界調査 — 99 spots 多様性分析\n\n")
report.append("生成日: 2026-05-27\n")
report.append("対象: Cash6mGeneral_6mNL25R25 @ 100bb BTNvBB（一部 HJvBB）\n\n")
report.append("---\n\n")

# Combine all topics
all_topics = ["b32_khigh_gradient", "b33_ahigh_gradient", "b34_qhigh_gradient",
              "b35_jt_low", "b36_low_connected", "b37_2tone_compare",
              "b38_mono_diverse", "b39_paired_diverse", "b40_hj_diverse"]

# Build full dataset
all_data = []
for topic in all_topics:
    for s in load(topic):
        m = s["_meta"]
        board = m["request"]["board"]
        pre = m["request"]["preflop_actions"]
        pos = "HJ" if pre.startswith("F-R") else "BTN" if pre.startswith("F-F-F-R") else "?"
        st = stats(s)
        feat = board_features(board)
        all_data.append({
            "topic": topic, "board": board, "pos": pos,
            "bet": st["bet"], "size": st["size"],
            **feat,
        })

# Per-topic reports
for topic in all_topics:
    spots = [d for d in all_data if d["topic"] == topic]
    if not spots:
        continue
    label_map = {
        "b32_khigh_gradient": "K-high boards (BTN vs BB)",
        "b33_ahigh_gradient": "A-high boards (BTN vs BB)",
        "b34_qhigh_gradient": "Q-high boards (BTN vs BB)",
        "b35_jt_low": "J/T-high boards (BTN vs BB)",
        "b36_low_connected": "Low connected boards (BTN vs BB)",
        "b37_2tone_compare": "2tone vs rainbow 比較",
        "b38_mono_diverse": "Mono boards 多様性",
        "b39_paired_diverse": "Paired flop 多様性",
        "b40_hj_diverse": "HJ vs BB 多様性",
    }
    report.append(f"\n## {label_map[topic]} (n={len(spots)})\n\n")
    report.append("| board | high | gap | suit | bet% | size |\n|------|------|----:|------|------:|------:|\n")
    for d in spots:
        sz = f"{d['size']:.0f}%" if d['size'] else "-"
        paired_mark = "**P**" if d['paired'] else ""
        report.append(f"| `{d['board']}` {paired_mark} | {d['high']} | {d['gap']} | {d['suit']} | {d['bet']:.1f} | {sz} |\n")

# Cross analyses
report.append("\n\n## 横断分析\n\n")

# High card avg
report.append("### 1. High card 別 cbet 平均 (BTN, rainbow only)\n\n")
report.append("| high | avg cbet% | n |\n|----|------:|--:|\n")
by_high = defaultdict(list)
for d in all_data:
    if d["pos"] == "BTN" and d["suit"] == "rainbow" and not d["paired"]:
        by_high[d["high"]].append(d["bet"])
for high in "AKQJT98765432":
    if high in by_high:
        v = by_high[high]
        report.append(f"| {high}-high | {sum(v)/len(v):.1f}% | {len(v)} |\n")

# Gap analysis
report.append("\n### 2. Gap (連結度) 別 cbet 平均\n\n")
report.append("| gap | avg cbet% | n |\n|----|------:|--:|\n")
by_gap = defaultdict(list)
for d in all_data:
    if d["pos"] == "BTN" and d["suit"] == "rainbow" and not d["paired"]:
        by_gap[d["gap"]].append(d["bet"])
for gap in sorted(by_gap.keys()):
    v = by_gap[gap]
    if v:
        report.append(f"| gap {gap} | {sum(v)/len(v):.1f}% | {len(v)} |\n")

# Suit pattern
report.append("\n### 3. Suit pattern 別 cbet 平均\n\n")
report.append("| pattern | avg cbet% | n |\n|----|------:|--:|\n")
by_suit = defaultdict(list)
for d in all_data:
    if d["pos"] == "BTN" and not d["paired"]:
        by_suit[d["suit"]].append(d["bet"])
for s in ["rainbow", "2tone", "mono"]:
    if s in by_suit:
        v = by_suit[s]
        report.append(f"| {s} | {sum(v)/len(v):.1f}% | {len(v)} |\n")

# Paired stats
report.append("\n### 4. Paired flop 平均\n\n")
report.append("| board | bet% | size |\n|------|------:|------:|\n")
for d in all_data:
    if d["paired"] and d["pos"] == "BTN":
        sz = f"{d['size']:.0f}%" if d['size'] else "-"
        report.append(f"| `{d['board']}` | {d['bet']:.1f} | {sz} |\n")

# Size distribution
report.append("\n### 5. サイズ層分布 (BTN, non-paired)\n\n")
report.append("| size層 | count |\n|----|--:|\n")
size_bins = defaultdict(int)
for d in all_data:
    if d["pos"] == "BTN" and not d["paired"] and d["size"]:
        sz = d["size"]
        if sz < 50: bin_ = "small (33-50%)"
        elif sz < 100: bin_ = "med (50-100%)"
        elif sz < 150: bin_ = "overbet 100-150%"
        else: bin_ = "huge >150%"
        size_bins[bin_] += 1
for b in ["small (33-50%)", "med (50-100%)", "overbet 100-150%", "huge >150%"]:
    if b in size_bins:
        report.append(f"| {b} | {size_bins[b]} |\n")

(ROOT / "CASH_DIVERSITY_REPORT.md").write_text("".join(report))
print(f"Wrote CASH_DIVERSITY_REPORT.md ({len(all_data)} spots analyzed)")
