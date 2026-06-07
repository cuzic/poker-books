#!/usr/bin/env python3
"""
tier1_generator.py — Vol2 Tier 1 マトリックス公式の章 generator.

新フレームワーク (2026-06-01):
- 5 × 4 マトリックス: ハンド強さ 5 段 × ベットサイズ 4 段
- 全 3 街 (Flop/Turn/River) 共通公式
- "迷わずに 7-8 割正解" を目指す簡易公式

Vol2 = Cash 100bb / 簡易 (Tier 1 ベース)
Vol3 = MTT 詳細 + SPR-axis-switching (別 generator)

Usage:
  uv run --with pyyaml python scripts/generate/tier1_generator.py \\
    scripts/generate/specs/vol2_t1_ch00_intro.yaml \\
    --output vol2-cash-postflop/chapters/00-introduction.md
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import yaml as _yaml
except ImportError:
    raise ImportError("uv run --with pyyaml で実行してください")


def render_section(sec: dict[str, Any]) -> list[str]:
    """1 つのセクション (heading/prose/table/list) を MD 行に変換。"""
    typ = sec.get("type", "prose")
    out: list[str] = []

    if typ == "heading":
        level = sec.get("level", 2)
        text = sec.get("text", "")
        out.append(f"{'#' * level} {text}")
        out.append("")

    elif typ == "prose":
        body = sec.get("body", "").rstrip()
        if body:
            out.append(body)
            out.append("")

    elif typ == "table":
        # Raw markdown table provided as `markdown:` field
        md = sec.get("markdown", "").rstrip()
        title = sec.get("title")
        if title:
            out.append(f"**{title}**")
            out.append("")
        if md:
            out.append(md)
            out.append("")

    elif typ == "list":
        items = sec.get("items", [])
        ordered = sec.get("ordered", False)
        for i, item in enumerate(items, 1):
            prefix = f"{i}." if ordered else "-"
            out.append(f"{prefix} {item}")
        out.append("")

    elif typ == "callout":
        # > Quote-style callout with optional title
        title = sec.get("title", "")
        body = sec.get("body", "")
        if title:
            out.append(f"> **{title}**")
            out.append(">")
        for line in body.strip().splitlines():
            out.append(f"> {line}")
        out.append("")

    elif typ == "code":
        body = sec.get("body", "").rstrip()
        lang = sec.get("lang", "")
        out.append(f"```{lang}")
        out.append(body)
        out.append("```")
        out.append("")

    elif typ == "raw":
        body = sec.get("body", "").rstrip()
        if body:
            out.append(body)
            out.append("")

    return out


def generate_chapter(spec: dict[str, Any]) -> str:
    """Spec → Markdown 文字列。"""
    chapter_num = spec.get("chapter_num", "??")
    title = spec.get("title", "無題")
    summary = spec.get("summary", "").strip()

    lines: list[str] = []
    lines.append(f"# 第{chapter_num}章 {title}")
    lines.append("")
    if summary:
        lines.append(summary)
        lines.append("")

    for sec in spec.get("sections", []):
        lines.extend(render_section(sec))

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Tier 1 chapter generator (Vol2)")
    ap.add_argument("spec", type=Path, help="YAML spec file")
    ap.add_argument("--output", "-o", type=Path, help="Output MD path (default: stdout)")
    args = ap.parse_args()

    spec = _yaml.safe_load(args.spec.read_text(encoding="utf-8"))
    md = generate_chapter(spec)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(md, encoding="utf-8")
        print(f"Wrote {args.output} ({len(md)} chars)", file=sys.stderr)
    else:
        sys.stdout.write(md)


if __name__ == "__main__":
    main()
