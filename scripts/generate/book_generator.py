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
    calc_turn_cbet_decision,
    calc_spr,
    classify_turn_card, calc_turn_barrel_v2,
    classify_river_runout, classify_river_board,
    calc_river_bucket, calc_river_ip_bet, calc_river_oop_lead,
    calc_hand_category, classify_board_type7,
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
    btype = classify_board_type7(board)
    hs = calc_hand_score(hand, board)
    tier = calc_flop_tier(hs)
    cbet = calc_flop_cbet_decision(hs, bs)
    size = calc_cbet_size(tex)
    fold_vs33 = calc_fold_threshold(33, tex)
    fold_vs75 = calc_fold_threshold(75, tex)
    return {
        "hand": hand, "board": board,
        "board_type": btype,
        "HS": hs, "tier": tier,
        "cbet": cbet, "cbet_size": size,
        "fold_vs33": fold_vs33, "fold_vs75": fold_vs75,
    }


def calc_5cat_example(hand: str, board: str) -> dict[str, Any]:
    """Calculate 5-category classification for one hand/board pair."""
    btype = classify_board_type7(board)
    hs = calc_hand_score(hand, board)
    cat, detail = calc_hand_category(hand, board)
    direction_map = {
        "バリュー": "BET",
        "セミブラフ": "BET",
        "ブラフキャッチャー": "CALL",
        "RIO": "FOLD/CALL",
        "エアー": "CHECK",
    }
    return {
        "hand": hand, "board": board,
        "board_type": btype,
        "HS": hs, "category": cat, "detail": detail,
        "ip_action": direction_map.get(cat, "?"),
    }


def calc_turn_example(hand: str, board: str) -> dict[str, Any]:
    """Calculate turn barrel metrics using v2 (turn_tag aware)."""
    cards = [c.strip() for c in board.split(",")]
    bs, _ = calc_board_score(board)
    btype = classify_board_type7(",".join(cards[:3])) if len(cards) >= 3 else "型?"
    hs = calc_hand_score(hand, board)
    if len(cards) >= 4:
        flop_str = ",".join(cards[:3])
        turn_str = cards[3]
        try:
            turn_tag = classify_turn_card(flop_str, turn_str)
        except ValueError:
            turn_tag = "blank"
        should_bet, sz = calc_turn_barrel_v2(hs, bs, turn_tag)
    else:
        turn_tag = "N/A"
        should_bet, sz = calc_turn_cbet_decision(hs, bs)
    return {
        "hand": hand, "board": board,
        "board_type": btype,
        "HS": hs, "turn_tag": turn_tag,
        "barrel": should_bet, "size": sz,
    }


def calc_river_example(hand: str, board: str, position: str = "IP") -> dict[str, Any]:
    """Calculate river bet metrics using v2 (river_tag + board_type aware)."""
    cards = [c.strip() for c in board.split(",")]
    # Use full board for type (pairs/mono introduced on turn/river must be reflected)
    btype7 = classify_board_type7(board) if cards else "型?"
    hs = calc_hand_score(hand, board)
    bucket = calc_river_bucket(hs)
    if len(cards) == 5:
        turn_board_str = ",".join(cards[:4])
        river_card_str = cards[4]
        try:
            river_tag = classify_river_runout(turn_board_str, river_card_str)
        except ValueError:
            river_tag = "blank"
        board_type = classify_river_board(board)
    else:
        river_tag = "N/A"
        board_type = "N/A"
    ip_bet = calc_river_ip_bet(hs, river_tag)
    oop_lead = calc_river_oop_lead(hs, board_type)
    should_bet = ip_bet if position == "IP" else oop_lead
    # 型6 (paired_high) = ポーラーレンジ → 100%ポット、それ以外 → 50%
    size = 100 if btype7 == "型6" else 50
    return {
        "hand": hand, "board": board, "position": position,
        "board_type": btype7,
        "HS": hs, "VMB": bucket,
        "river_tag": river_tag, "board_type_sc": board_type,
        "bet": should_bet, "size": size,
    }


# ── Markdown formatters ───────────────────────────────────────────────────────

def fmt_5cat_table(examples: list[dict[str, Any]]) -> str:
    """Format 5-category examples as a markdown table."""
    hdr = "| ハンド | ボード | ボード型 | HS | カテゴリ | 詳細 | IP基本行動 |"
    sep = "|--------|--------|---------|-----|---------|------|-----------|"
    rows = [hdr, sep]
    for e in examples:
        rows.append(
            f"| {e['hand']} | `{e['board']}` | {e['board_type']} "
            f"| {e['HS']} | **{e['category']}** | {e['detail']} | {e['ip_action']} |"
        )
    return "\n".join(rows)


def fmt_flop_table(examples: list[dict[str, Any]]) -> str:
    """Format flop examples as a markdown table."""
    hdr = "| ハンド | ボード | ボード型 | HS | ティア | CBet? | サイズ | fold vs33% | fold vs75% |"
    sep = "|--------|--------|---------|-----|-------|-------|--------|-----------|-----------|"
    rows = [hdr, sep]
    for e in examples:
        cbet_mark = "✓" if e["cbet"] else "✗"
        rows.append(
            f"| {e['hand']} | `{e['board']}` | {e['board_type']} "
            f"| {e['HS']} | {e['tier']} | {cbet_mark} | {e['cbet_size']}% "
            f"| {e['fold_vs33']} | {e['fold_vs75']} |"
        )
    return "\n".join(rows)


def fmt_turn_table(examples: list[dict[str, Any]]) -> str:
    hdr = "| ハンド | ボード | ボード型 | HS | turn_tag | バレル? | サイズ |"
    sep = "|--------|--------|---------|-----|----------|--------|--------|"
    rows = [hdr, sep]
    for e in examples:
        barrel_mark = "✓" if e["barrel"] else "✗"
        rows.append(
            f"| {e['hand']} | `{e['board']}` | {e['board_type']} | {e['HS']} "
            f"| {e.get('turn_tag', '-')} | {barrel_mark} | {e['size']}% |"
        )
    return "\n".join(rows)


def fmt_river_table(examples: list[dict[str, Any]]) -> str:
    hdr = "| ハンド | ボード | ボード型 | Pos | HS | VMB | river_tag | ベット/リード? | サイズ |"
    sep = "|--------|--------|---------|-----|-----|-----|-----------|--------------|--------|"
    rows = [hdr, sep]
    for e in examples:
        bet_mark = "✓" if e["bet"] else "✗"
        rows.append(
            f"| {e['hand']} | `{e['board']}` | {e['board_type']} | {e['position']} "
            f"| {e['HS']} | {e['VMB']} "
            f"| {e.get('river_tag', '-')} "
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

        if street == "5cat":
            computed = [calc_5cat_example(e["hand"], e["board"]) for e in examples]
            lines.append(fmt_5cat_table(computed))
        elif street == "flop":
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


# ── MTT postflop formatters ──────────────────────────────────────────────────
#
# vol4『迷わないポーカー MTTポストフロップ』向けの章原稿生成ヘルパー。
# specs/index.yaml や designs/*.md から抽出したシナリオ単位の意思決定データを
# Markdown セクションへ整形する。既存の vol2/vol3 系フォーマッターには触れず、
# MTT 専用関数として独立して提供する。


def format_mtt_decision_table(rows: list[dict[str, Any]], caption: str = "") -> str:
    """Render an MTT decision table (board type × SBR) as a markdown table.

    Args:
        rows: 各行は ``board_type`` / ``sbr25`` / ``sbr20`` / ``note`` を持つ
            辞書のリスト。``note`` は任意。任意の追加列は無視する。
        caption: テーブル直前に出力するキャプション（空文字なら省略）。

    Returns:
        markdown table 文字列（末尾改行なし）。
    """
    has_note = any((r.get("note") or "").strip() for r in rows)
    if has_note:
        hdr = "| ボード型 | SBR25 判断 | SBR20 判断 | メモ |"
        sep = "|----------|-----------|-----------|------|"
    else:
        hdr = "| ボード型 | SBR25 判断 | SBR20 判断 |"
        sep = "|----------|-----------|-----------|"

    lines: list[str] = []
    if caption:
        lines.append(f"**{caption}**")
        lines.append("")
    lines.append(hdr)
    lines.append(sep)
    for r in rows:
        board = r.get("board_type", "—")
        s25 = r.get("sbr25", "—")
        s20 = r.get("sbr20", "—")
        if has_note:
            note = r.get("note", "") or ""
            lines.append(f"| {board} | {s25} | {s20} | {note} |")
        else:
            lines.append(f"| {board} | {s25} | {s20} |")
    return "\n".join(lines)


def format_mtt_decision_flow(
    title: str,
    steps: list[str],
    notes: list[str] | None = None,
) -> str:
    """Render a decision-flow section (### level) for an MTT scenario.

    Args:
        title: セクション見出し（###レベル）。
        steps: 判断フローの各ステップ（順序付き箇条書きにする）。
        notes: 補足の箇条書き（``-`` リスト、任意）。

    Returns:
        markdown セクション文字列（末尾改行なし）。
    """
    lines: list[str] = [f"### {title}", ""]
    for i, step in enumerate(steps, 1):
        lines.append(f"{i}. {step}")
    if notes:
        lines.append("")
        lines.append("**補足**")
        lines.append("")
        for n in notes:
            lines.append(f"- {n}")
    return "\n".join(lines)


def format_mtt_scenario_section(scenario_id: str, scenario_data: dict[str, Any]) -> str:
    """Render a full scenario section (## level) for the MTT book.

    Args:
        scenario_id: シナリオID（例: ``F01B``）。
        scenario_data: 以下のキーを含む辞書（すべて任意）:
            - ``title``: セクションタイトル（無い場合は scenario_id を使用）
            - ``description``: シナリオ概要（先頭の段落）
            - ``decision_table``: :func:`format_mtt_decision_table` 用の rows
            - ``decision_caption``: decision_table のキャプション
            - ``flow_title``: 判断フローの見出し（デフォルト「判断フロー」）
            - ``flow_steps``: :func:`format_mtt_decision_flow` 用 steps
            - ``flow_notes``: 判断フローの補足
            - ``memorize``: 暗記ポイント（最大3つ。超過分は警告コメント付与）
            - ``icm_note``: ICM補正の一行コメント

    Returns:
        markdown セクション文字列（末尾改行なし）。
    """
    title = scenario_data.get("title", scenario_id)
    lines: list[str] = [f"## {scenario_id}: {title}", ""]

    description = scenario_data.get("description")
    if description:
        lines += [description.strip(), ""]

    decision_table = scenario_data.get("decision_table")
    if decision_table:
        caption = scenario_data.get("decision_caption", "")
        lines += ["### 板別決定テーブル", ""]
        lines.append(format_mtt_decision_table(decision_table, caption=caption))
        lines.append("")

    flow_steps = scenario_data.get("flow_steps")
    if flow_steps:
        flow_title = scenario_data.get("flow_title", "判断フロー")
        flow_notes = scenario_data.get("flow_notes")
        lines.append(format_mtt_decision_flow(flow_title, flow_steps, flow_notes))
        lines.append("")

    memorize = scenario_data.get("memorize")
    if memorize:
        lines += ["### 暗記ポイント", ""]
        for i, item in enumerate(memorize[:3], 1):
            lines.append(f"{i}. {item}")
        if len(memorize) > 3:
            lines.append("")
            lines.append(
                f"<!-- WARN: memorize に {len(memorize)} 項目あり。"
                f"3項目までに絞り込みを推奨 -->"
            )
        lines.append("")

    icm_note = scenario_data.get("icm_note")
    if icm_note:
        lines += ["### ICM補正", "", f"> {icm_note}", ""]

    # 末尾の余分な空行を1つだけに整える
    while len(lines) >= 2 and lines[-1] == "" and lines[-2] == "":
        lines.pop()
    return "\n".join(lines).rstrip()


def generate_mtt_chapter(
    spec_path: str | Path,
    output_path: str | Path | None = None,
) -> str:
    """Generate a full MTT chapter markdown from a spec YAML.

    spec YAML の想定構造::

        chapter_num: 12
        title: "ターン・リバー判断フロー"
        summary: |
          章冒頭で読者に提示する目的の段落。
        scenarios:
          - id: F01B
            title: "IP CBet（BTNvsBB フロップ）"
            description: ...
            decision_table: [...]
            flow_steps: [...]
            flow_notes: [...]
            memorize: [...]
            icm_note: "..."
        summary_card:  # 任意。まとめカード用の箇条書き
          - "..."

    Args:
        spec_path: spec YAML/JSON ファイルパス。
        output_path: 出力先（``None`` ならファイル出力せず文字列のみ返す）。

    Returns:
        生成した章マークダウン文字列。
    """
    spec_path = Path(spec_path)
    spec = load_spec(spec_path)

    chapter_num = spec.get("chapter_num", "?")
    title = spec.get("title", "無題")
    summary = spec.get("summary")
    scenarios = spec.get("scenarios", []) or []
    summary_card = spec.get("summary_card") or []

    lines: list[str] = [
        f"# 第{chapter_num}章 {title}",
        "<!-- Volume: vol3-mtt-postflop -->",
        "<!-- Auto-generated by book_generator.generate_mtt_chapter -->",
        "",
    ]

    if summary:
        lines += ["## この章で学ぶこと", "", summary.strip(), ""]

    for sc in scenarios:
        sc_id = sc.get("id", "?")
        lines.append(format_mtt_scenario_section(sc_id, sc))
        lines.append("")

    if summary_card:
        lines += ["## まとめカード", ""]
        for item in summary_card:
            lines.append(f"- {item}")
        lines.append("")

    lines += ["---", "<!-- END OF GENERATED MTT CHAPTER -->"]
    text = "\n".join(lines)

    if output_path is not None:
        Path(output_path).write_text(text, encoding="utf-8")
    return text
