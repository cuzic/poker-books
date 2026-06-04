#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Aggregate GTO Wizard study results into REPORT.md per topic + SUMMARY.md."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study")


def load_topic(topic_dir: Path) -> list[dict]:
    spots = []
    for f in sorted(topic_dir.glob("*.json")):
        try:
            spots.append(json.loads(f.read_text()))
        except Exception:
            continue
    return spots


def summarize_actions(spot: dict) -> list[dict]:
    """Return list of dicts: code, name, freq, pct_pot."""
    out = []
    for a in spot.get("action_solutions", []):
        ac = a.get("action", {})
        bp = ac.get("betsize_by_pot")
        out.append({
            "code": ac.get("code"),
            "name": ac.get("display_name"),
            "freq": a.get("total_frequency"),
            "pct_pot": float(bp) if bp not in (None, "") else None,
            "betsize": ac.get("betsize"),
            "pos": ac.get("position"),
        })
    return out


def fmt_action(a: dict) -> str:
    pct = f" ({a['pct_pot']*100:.0f}%pot)" if a["pct_pot"] is not None else ""
    return f"{a['name']}{pct}: {a['freq']*100:.1f}%"


def board_texture(board: str) -> str:
    """Simple texture classification: 5-char or 6-char or 8-char flop board."""
    if len(board) < 6:
        return "unknown"
    # Extract first 3 cards (flop)
    flop = board[:6]
    ranks = [flop[0], flop[2], flop[4]]
    suits = [flop[1], flop[3], flop[5]]
    rank_order = "23456789TJQKA"
    rvals = sorted([rank_order.index(r) for r in ranks], reverse=True)
    is_paired = len(set(ranks)) < 3
    if is_paired:
        if rvals[0] >= rank_order.index("T"):
            return "paired_high"
        return "paired_low"
    suit_count = len(set(suits))
    is_mono = suit_count == 1
    is_2tone = suit_count == 2
    is_rainbow = suit_count == 3
    high = rvals[0]
    low = rvals[2]
    gap = high - low
    has_ak = high == rank_order.index("A") or rvals[1] == rank_order.index("K")
    if is_mono:
        return "mono"
    if gap <= 4:
        return ("2tone_conn" if is_2tone else "rainbow_conn")
    if has_ak:
        return ("2tone_ak" if is_2tone else "rainbow_ak")
    return ("2tone" if is_2tone else "rainbow")


def render_topic(topic: str, spots: list[dict]) -> str:
    if not spots:
        return f"# {topic}\n\nno data\n"
    lines = [f"# {topic}", "", f"スポット数: {len(spots)}", ""]
    lines.append("| id | board | pos | actions (freq) | note |")
    lines.append("|----|-------|-----|----------------|------|")
    for s in spots:
        m = s.get("_meta", {})
        req = m.get("request", {})
        board = req.get("board", "")
        acts = summarize_actions(s)
        # Find hero position
        pos = acts[0]["pos"] if acts else "?"
        # Pretty actions: show top 4 by freq
        acts_sorted = sorted(acts, key=lambda a: -a["freq"])
        act_str = " / ".join(fmt_action(a) for a in acts_sorted[:4])
        note = m.get("note", "")
        lines.append(f"| {m.get('id', '')} | `{board}` | {pos} | {act_str} | {note} |")
    return "\n".join(lines) + "\n"


def stats_by_action_type(spots: list[dict]) -> dict:
    """Aggregate stats: avg bet freq, avg check freq, etc."""
    stats = defaultdict(list)
    for s in spots:
        for a in s.get("action_solutions", []):
            ac = a.get("action", {})
            t = ac.get("type", "")
            stats[t].append(a.get("total_frequency", 0))
    return {k: {"avg": sum(v) / len(v) if v else 0, "n": len(v)} for k, v in stats.items()}


def texture_table(spots: list[dict]) -> str:
    """Group by board texture and average BET frequency."""
    by_tex: dict[str, list[float]] = defaultdict(list)
    by_tex_size: dict[str, list[float]] = defaultdict(list)
    for s in spots:
        req = s.get("_meta", {}).get("request", {})
        board = req.get("board", "")
        if not board:
            continue
        tex = board_texture(board)
        bet_freq = 0.0
        bet_size_avg = None
        for a in s.get("action_solutions", []):
            if a.get("action", {}).get("type") in ("BET", "RAISE"):
                bet_freq += a.get("total_frequency", 0)
                bp = a.get("action", {}).get("betsize_by_pot")
                if bp not in (None, ""):
                    bet_size_avg = float(bp) if bet_size_avg is None else (bet_size_avg + float(bp)) / 2
        by_tex[tex].append(bet_freq)
        if bet_size_avg is not None:
            by_tex_size[tex].append(bet_size_avg)
    if not by_tex:
        return ""
    lines = ["", "## テクスチャ別 BET/RAISE 頻度", ""]
    lines.append("| texture | bet/raise freq% | avg size %pot | n |")
    lines.append("|---------|----------------:|--------------:|--:|")
    for tex in sorted(by_tex.keys(), key=lambda t: -sum(by_tex[t]) / max(1, len(by_tex[t]))):
        avg_freq = sum(by_tex[tex]) / len(by_tex[tex])
        sizes = by_tex_size.get(tex, [])
        avg_size = sum(sizes) / len(sizes) * 100 if sizes else 0
        lines.append(f"| {tex} | {avg_freq*100:.1f}% | {avg_size:.0f}% | {len(by_tex[tex])} |")
    return "\n".join(lines)


def main() -> int:
    topics = sorted([d for d in ROOT.iterdir() if d.is_dir()])
    summary_sections = []
    summary_sections.append("# GTO Wizard Study Summary\n")
    summary_sections.append(f"生成日: 2026-05-25\n")
    summary_sections.append(f"トピック数: {len(topics)}\n")

    for topic_dir in topics:
        if not topic_dir.is_dir():
            continue
        spots = load_topic(topic_dir)
        if not spots:
            continue
        topic = topic_dir.name
        report = render_topic(topic, spots)
        # Append stats
        stats = stats_by_action_type(spots)
        if stats:
            report += "\n## アクションタイプ別平均頻度\n\n| type | avg freq% | observations |\n|------|----------:|-------------:|\n"
            for t, v in sorted(stats.items()):
                report += f"| {t} | {v['avg']*100:.1f}% | {v['n']} |\n"
        report += texture_table(spots)
        out_path = topic_dir / "REPORT.md"
        out_path.write_text(report)
        # Add to summary
        summary_sections.append(f"\n## [{topic}](./{topic}/REPORT.md)\n")
        summary_sections.append(f"- {len(spots)} スポット\n")
        for t, v in sorted(stats.items()):
            summary_sections.append(f"- {t}: {v['avg']*100:.1f}% avg\n")

    (ROOT / "SUMMARY.md").write_text("".join(summary_sections))
    print(f"Aggregated {len(topics)} topics")
    return 0


if __name__ == "__main__":
    sys.exit(main())
