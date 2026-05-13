#!/usr/bin/env python3
"""
book_generator.py — 書籍章ジェネレーター

章仕様 YAML を読み込み、calc.py で例を計算し、
検証済み outline.md を出力する。

Usage:
  python3 book_generator.py specs/vol2_ch04.yaml
  python3 book_generator.py specs/vol2_ch04.yaml --output chapters/04-output.md
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Any

# calc.py を親ディレクトリから import
sys.path.insert(0, str(Path(__file__).parent.parent))
from calc import (  # type: ignore[import]
    calc_board_score, calc_hand_score, calc_flop_tier,
    calc_flop_cbet_decision, calc_cbet_size, calc_fold_threshold,
    calc_turn_cbet_decision, calc_river_vmb_bucket, calc_river_cbet_decision,
    calc_spr, calc_c_coeff,
    classify_turn_card, calc_turn_barrel_v2,
    classify_river_runout, classify_river_board,
    calc_river_bucket, calc_river_ip_bet, calc_river_oop_lead,
)

try:
    import yaml as _yaml  # type: ignore
    _HAS_YAML = True
except ImportError:
    _yaml = None  # type: ignore
    _HAS_YAML = False


# ── YAML loader (fallback to JSON) ────────────────────────────────────────────

def load_spec(path: Path) -> dict[str, Any]:
    """Load chapter spec from YAML or JSON."""
    text = path.read_text(encoding='utf-8')
    if path.suffix in ('.yaml', '.yml'):
        if not _HAS_YAML or _yaml is None:
            raise ImportError("pip install pyyaml  # for YAML support")
        return _yaml.safe_load(text)
    return json.loads(text)


# ── Example calculators ───────────────────────────────────────────────────────

def calc_flop_example(hand: str, board: str) -> dict[str, Any]:
    """Calculate full flop metrics for one hand/board pair."""
    bs, tex = calc_board_score(board)
    hs = calc_hand_score(hand, board)
    tier = calc_flop_tier(hs)
    cbet = calc_flop_cbet_decision(hs, bs)
    size = calc_cbet_size(tex)
    fold_vs33 = calc_fold_threshold(33, tex)
    fold_vs75 = calc_fold_threshold(75, tex)
    c_coeff_33 = round(calc_c_coeff(33), 1)
    c_coeff_75 = round(calc_c_coeff(75), 1)
    return {
        "hand": hand, "board": board,
        "BS": bs, "texture": tex,
        "HS": hs, "tier": tier,
        "cbet": cbet, "cbet_size": size,
        "fold_vs33": fold_vs33, "fold_vs75": fold_vs75,
        "C_33": c_coeff_33, "C_75": c_coeff_75,
    }


def calc_turn_example(hand: str, board: str) -> dict[str, Any]:
    """Calculate turn barrel metrics using v2 (turn_tag aware)."""
    cards = [c.strip() for c in board.split(",")]
    bs, tex = calc_board_score(board)
    hs = calc_hand_score(hand, board)
    # classify turn_tag from flop (first 3 cards) + turn (4th card)
    if len(cards) >= 4:
        flop_str = ",".join(cards[:3])
        turn_str = cards[3]
        try:
            turn_tag = classify_turn_card(flop_str, turn_str)
        except Exception:
            turn_tag = "blank"
        try:
            should_bet = calc_turn_barrel_v2(hs, bs, turn_tag)
        except Exception:
            old_bet, _ = calc_turn_cbet_decision(hs, bs)
            should_bet = old_bet
    else:
        turn_tag = "N/A"
        old_bet, _ = calc_turn_cbet_decision(hs, bs)
        should_bet = old_bet
    return {
        "hand": hand, "board": board,
        "BS": bs, "texture": tex,
        "HS": hs, "turn_tag": turn_tag,
        "barrel": should_bet, "size": 33,
    }


def calc_river_example(hand: str, board: str, position: str = "IP") -> dict[str, Any]:
    """Calculate river bet metrics using v2 (river_tag + board_type aware)."""
    cards = [c.strip() for c in board.split(",")]
    bs, tex = calc_board_score(board)
    hs = calc_hand_score(hand, board)
    bucket = calc_river_bucket(hs)
    # Determine river_tag and board_type
    if len(cards) == 5:
        turn_board_str = ",".join(cards[:4])
        river_card_str = cards[4]
        try:
            river_tag = classify_river_runout(turn_board_str, river_card_str)
        except Exception:
            river_tag = "blank"
        try:
            board_type = classify_river_board(board)
        except Exception:
            board_type = "blank"
    else:
        river_tag = "N/A"
        board_type = "N/A"
    # IP bet decision
    try:
        ip_bet = calc_river_ip_bet(hs, river_tag)
    except Exception:
        old_bet, _ = calc_river_cbet_decision(hs, bs, "IP")
        ip_bet = old_bet
    # OOP lead decision
    try:
        oop_lead = calc_river_oop_lead(hs, board_type)
    except Exception:
        oop_lead = False
    if position == "IP":
        should_bet = ip_bet
    else:
        should_bet = oop_lead
    size = 100 if bs >= 83 else 50
    return {
        "hand": hand, "board": board, "position": position,
        "BS": bs, "texture": tex,
        "HS": hs, "VMB": bucket,
        "river_tag": river_tag, "board_type": board_type,
        "bet": should_bet, "size": size,
    }


# ── Markdown formatters ───────────────────────────────────────────────────────

def fmt_flop_table(examples: list[dict[str, Any]]) -> str:
    """Format flop examples as a markdown table."""
    hdr = "| ハンド | ボード | BS | テクスチャ | HS | ティア | CBet? | サイズ | fold vs33% | fold vs75% |"
    sep = "|--------|--------|-----|----------|-----|-------|-------|--------|-----------|-----------|"
    rows = [hdr, sep]
    for e in examples:
        cbet_mark = "✓" if e["cbet"] else "✗"
        rows.append(
            f"| {e['hand']} | `{e['board']}` | {e['BS']} | {e['texture']} "
            f"| {e['HS']} | {e['tier']} | {cbet_mark} | {e['cbet_size']}% "
            f"| {e['fold_vs33']} | {e['fold_vs75']} |"
        )
    return "\n".join(rows)


def fmt_turn_table(examples: list[dict[str, Any]]) -> str:
    hdr = "| ハンド | ボード | BS | HS | turn_tag | バレル? | サイズ |"
    sep = "|--------|--------|-----|-----|----------|--------|--------|"
    rows = [hdr, sep]
    for e in examples:
        barrel_mark = "✓" if e["barrel"] else "✗"
        rows.append(
            f"| {e['hand']} | `{e['board']}` | {e['BS']} | {e['HS']} "
            f"| {e.get('turn_tag', '-')} | {barrel_mark} | {e['size']}% |"
        )
    return "\n".join(rows)


def fmt_river_table(examples: list[dict[str, Any]]) -> str:
    hdr = "| ハンド | ボード | Pos | HS | VMB | river_tag | board_type | ベット/リード? | サイズ |"
    sep = "|--------|--------|-----|-----|-----|-----------|-----------|--------------|--------|"
    rows = [hdr, sep]
    for e in examples:
        bet_mark = "✓" if e["bet"] else "✗"
        rows.append(
            f"| {e['hand']} | `{e['board']}` | {e['position']} "
            f"| {e['HS']} | {e['VMB']} "
            f"| {e.get('river_tag', '-')} | {e.get('board_type', '-')} "
            f"| {bet_mark} | {e['size']}% |"
        )
    return "\n".join(rows)


# ── Main outline generator ────────────────────────────────────────────────────

def generate_outline(spec: dict[str, Any]) -> str:
    """Generate chapter outline markdown from spec."""
    volume = spec.get("volume", "?")
    chapter_num = spec.get("chapter_num", "?")
    title = spec.get("title", "無題")
    street = spec.get("street", "flop")  # flop / turn / river

    lines: list[str] = [
        f"# 第{chapter_num}章 {title}",
        f"<!-- Volume: {volume}  Street: {street} -->",
        f"<!-- Auto-generated by book_generator.py from spec -->",
        "",
    ]

    # Summary
    if "summary" in spec:
        lines += ["## この章で学ぶこと", "", spec["summary"], ""]

    # Key formulas
    if "key_formulas" in spec:
        lines += ["## 核心式", ""]
        for name, formula in spec["key_formulas"].items():
            lines += [f"**{name}:**", f"```", formula, "```", ""]

    # Examples section
    if "examples" in spec:
        lines += ["## 計算例（自動生成）", ""]
        examples = spec["examples"]

        if street == "flop":
            computed = [calc_flop_example(e["hand"], e["board"]) for e in examples]
            lines.append(fmt_flop_table(computed))
        elif street == "turn":
            computed = [calc_turn_example(e["hand"], e["board"]) for e in examples]
            lines.append(fmt_turn_table(computed))
        elif street == "river":
            computed = [
                calc_river_example(e["hand"], e["board"], e.get("position", "IP"))
                for e in examples
            ]
            lines.append(fmt_river_table(computed))

        lines.append("")

    # SPR examples
    if "spr_examples" in spec:
        lines += ["## SPR 計算例", "", "| 状況 | スタック | ポット | SPR |", "|------|---------|-------|-----|"]
        for s in spec["spr_examples"]:
            spr = calc_spr(s["stack"], s["pot"])
            lines.append(f"| {s.get('label', '')} | {s['stack']}bb | {s['pot']}bb | {spr:.1f} |")
        lines.append("")

    # GTO reference
    if "gto_reference" in spec:
        lines += ["## GTO 参照データ", ""]
        ref = spec["gto_reference"]
        if isinstance(ref, dict):
            lines.append(f"ソース: `{ref.get('source', '?')}`")
            if "notes" in ref:
                lines.append(f"> {ref['notes']}")
        lines.append("")

    # Key points (for AI writer to expand)
    if "key_points" in spec:
        lines += ["## 章のポイント (執筆ガイド)", ""]
        for i, point in enumerate(spec["key_points"], 1):
            lines.append(f"{i}. {point}")
        lines.append("")

    # Chapter structure
    if "sections" in spec:
        lines += ["## 節構成 (概要)", ""]
        for sec in spec["sections"]:
            lines.append(f"### {sec['title']}")
            if "summary" in sec:
                lines.append(f"\n{sec['summary']}\n")
            else:
                lines.append("")

    lines += ["", "---", "<!-- END OF GENERATED OUTLINE -->"]
    return "\n".join(lines)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="Book chapter outline generator")
    ap.add_argument("spec", type=Path, help="Chapter spec YAML/JSON file")
    ap.add_argument("--output", "-o", type=Path, default=None,
                    help="Output markdown file (default: stdout)")
    args = ap.parse_args()

    spec = load_spec(args.spec)
    outline = generate_outline(spec)

    if args.output:
        args.output.write_text(outline, encoding='utf-8')
        print(f"Written: {args.output}")
    else:
        print(outline)


if __name__ == "__main__":
    main()
