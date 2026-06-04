#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Aggregate cash vs MTT 100bb comparison."""
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


report = []
report.append("# Cash vs MTT 100bb 直接比較レポート\n\n")
report.append("生成日: 2026-05-27\n\n")
report.append("**API breakthrough**: Cash6mGeneral_6mNL25R25 @ 100bb がアクセス可能になり、初めて MTT 6m vs Cash NL25 を同じ条件で直接比較できた。\n\n")
report.append("---\n\n")

# Cash @ 100bb data
cash_data = {}  # (pos, board) -> (bet, size)
for topic in ["b20_cash_100bb_utg", "b20_cash_100bb_hj", "b20_cash_100bb_co", "b20_cash_100bb_btn", "b20_cash_100bb_sb"]:
    pos = topic.split("_")[-1].upper()
    for s in load(topic):
        m = s["_meta"]
        board = m["request"]["board"]
        bet, chk, sz = stats(s)
        cash_data[(pos, board)] = (bet, sz)

# MTT @ 100bb data
mtt_data = {}
for topic in ["b15_100bb_utg", "b15_100bb_hj", "b15_100bb_co", "b15_100bb_btn", "b15_100bb_sb", "b21_mtt_btn_more", "b21_mtt_sb"]:
    if "btn_more" in topic:
        pos = "BTN"
    else:
        pos = topic.split("_")[-1].upper()
    for s in load(topic):
        m = s["_meta"]
        board = m["request"]["board"]
        bet, chk, sz = stats(s)
        mtt_data[(pos, board)] = (bet, sz)

# Comparison
report.append("## B-20+21: Cash vs MTT @ 100bb 直接比較\n\n")
report.append("| pos | board | Cash cbet% | MTT cbet% | 差 (MTT-Cash) | Cash size | MTT size |\n")
report.append("|----|------|---------:|---------:|---------:|---------:|---------:|\n")

all_keys = sorted(set(cash_data.keys()) | set(mtt_data.keys()))
diffs = []
matched = 0
for key in all_keys:
    pos, board = key
    cash = cash_data.get(key)
    mtt = mtt_data.get(key)
    cash_b = f"{cash[0]:5.1f}" if cash else "  -  "
    mtt_b = f"{mtt[0]:5.1f}" if mtt else "  -  "
    cash_s = f"{cash[1]:.0f}%" if cash and cash[1] else "-"
    mtt_s = f"{mtt[1]:.0f}%" if mtt and mtt[1] else "-"
    diff = f"{mtt[0]-cash[0]:+5.1f}" if cash and mtt else "  -  "
    if cash and mtt:
        diffs.append(mtt[0]-cash[0])
        matched += 1
    report.append(f"| {pos} | `{board}` | {cash_b} | {mtt_b} | {diff} | {cash_s} | {mtt_s} |\n")

if diffs:
    abs_diffs = [abs(d) for d in diffs]
    report.append(f"\n**統計**: {matched} 板で直接比較。MTT-Cash 差: 平均 {sum(diffs)/len(diffs):+.1f}pt、絶対値平均 {sum(abs_diffs)/len(abs_diffs):.1f}pt、最大絶対差 {max(abs_diffs):.1f}pt\n")

# Position averages
report.append("\n### Position 別平均\n\n| pos | Cash avg | MTT avg | 差 |\n|----|------:|------:|---:|\n")
pos_groups = defaultdict(lambda: {"cash": [], "mtt": []})
for (pos, board), (bet, _) in cash_data.items():
    pos_groups[pos]["cash"].append(bet)
for (pos, board), (bet, _) in mtt_data.items():
    pos_groups[pos]["mtt"].append(bet)

for pos in ["UTG", "HJ", "CO", "BTN", "SB"]:
    if pos in pos_groups:
        cash_vals = pos_groups[pos]["cash"]
        mtt_vals = pos_groups[pos]["mtt"]
        cash_avg = sum(cash_vals)/len(cash_vals) if cash_vals else 0
        mtt_avg = sum(mtt_vals)/len(mtt_vals) if mtt_vals else 0
        diff = mtt_avg - cash_avg if cash_vals and mtt_vals else 0
        report.append(f"| {pos} | {cash_avg:.1f}% (n={len(cash_vals)}) | {mtt_avg:.1f}% (n={len(mtt_vals)}) | {diff:+.1f}pt |\n")

# B-22: Cash rake variation
report.append("\n\n## B-22: Cash rake バリエーション（同 BTN 同 board × 4 rake）\n\n")
report.append("| rake | board | bet% | size |\n|----|------|------:|------:|\n")
for topic in ["b22_cash_rake"]:
    for s in load(topic):
        m = s["_meta"]
        board = m["request"]["board"]
        gt = m["request"]["gametype"]
        rake = gt.replace("Cash6mGeneral_6m", "").replace("R25", "")
        bet, _, sz = stats(s)
        sz_s = f"{sz:.0f}%" if sz else "-"
        report.append(f"| {rake} | `{board}` | {bet:.1f} | {sz_s} |\n")

# B-23: Cash 50bb
report.append("\n\n## B-23: Cash 50bb mid-stack\n\n")
report.append("| pos | board | bet% | size |\n|----|------|------:|------:|\n")
for s in load("b23_cash_50bb"):
    m = s["_meta"]
    board = m["request"]["board"]
    pre = m["request"]["preflop_actions"]
    pos = "HJ" if pre.startswith("F-R") else "BTN"
    bet, _, sz = stats(s)
    sz_s = f"{sz:.0f}%" if sz else "-"
    report.append(f"| {pos} | `{board}` | {bet:.1f} | {sz_s} |\n")

# B-24: Cash special boards
report.append("\n\n## B-24: Cash 特殊 boards (paired/mono/super-wet) @ 100bb BTN\n\n")
report.append("| board | bet% | size | type |\n|------|------:|------:|----|\n")
for s in load("b24_cash_special"):
    m = s["_meta"]
    board = m["request"]["board"]
    bet, _, sz = stats(s)
    sz_s = f"{sz:.0f}%" if sz else "-"
    note = m.get("note", "")[:40]
    report.append(f"| `{board}` | {bet:.1f} | {sz_s} | {note} |\n")

(ROOT / "CASH_MTT_DIRECT_COMPARISON.md").write_text("".join(report))
total = sum(1 for _ in ROOT.glob("b2[0-4]_*/*.json"))
print(f"Wrote CASH_MTT_DIRECT_COMPARISON.md ({total} new spots)")
