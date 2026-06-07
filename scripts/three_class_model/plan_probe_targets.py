"""probe ターゲット計画 — drill カバー + board 境界 spot の 2 軸で立案。

(A) drill カバー: poker-drill の cards で使われている boards のうち
    dataset_unified_v2.csv に無い ものを抽出 → 各 board × scenario の spec を作成

(B) board 境界 spot: MATCHA レンジ分布判定 (POLAR/MERGED/CONDENSED) の
    分類境界に位置する boards を生成 → 境界判定精度を検証

出力: knowledges/gto_wizard_study/PROBE_TARGETS.json (probe 入力用)
     knowledges/gto_wizard_study/PROBE_PLAN.md (人間用 plan doc)
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET = REPO_ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
DRILL_DATA = Path("/home/cuzic/poker-drill/src/data")
TARGETS = REPO_ROOT / "knowledges/gto_wizard_study/PROBE_TARGETS.json"
PLAN_DOC = REPO_ROOT / "knowledges/gto_wizard_study/PROBE_PLAN.md"

SUIT_MAP = {"♠": "s", "♥": "h", "♦": "d", "♣": "c"}


def parse_board(s: str | None) -> list[str] | None:
    if not s:
        return None
    s = re.sub(r"\([^)]*\)", "", s)
    parts = re.findall(r"[\dATJQK]0?[♠♥♦♣]", s)
    cards: list[str] = []
    for p in parts:
        if p[0] == "1":
            rank, suit_ch = "T", p[2]
        else:
            rank, suit_ch = p[0], p[1]
        suit = SUIT_MAP.get(suit_ch)
        if suit is None:
            return None
        cards.append(f"{rank}{suit}")
    return cards if cards else None


def extract_cards(ts_path: Path) -> list[dict]:
    txt = ts_path.read_text()
    m = re.search(r"export const \w+ = (\[.*\])\s+satisfies", txt, re.S)
    if not m:
        return []
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return []


# ════════════════════════════════════════════════════════════
# (A) drill カバー
# ════════════════════════════════════════════════════════════


def collect_drill_targets() -> dict[str, list[tuple[str, str]]]:
    """drill 使用 unique (flop, scenario_type) → drill 内出現 cards list。

    scenario_type: SRP_flop / SRP_turn / SRP_river / 3BP / 4BP / etc.
    """
    targets: dict[str, list[tuple[str, str]]] = defaultdict(list)

    deck_to_type = {
        "matcha-framework-srp-flop-decisions": "SRP_flop",
        "matcha-framework-srp-turn-decisions": "SRP_turn",
        "matcha-framework-srp-river-decisions": "SRP_river",
        "matcha-framework-3bet-pot-decisions": "3BP",
        "matcha-framework-4bet-pot-decisions": "4BP",
        "matcha-framework-vs-check-raise": "CR",
        "matcha-framework-vs-donk-bet": "DONK",
        "matcha-framework-mtt-depth-variations": "MTT_DEPTH",
        "matcha-framework-boundary-hands": "BOUNDARY",
    }
    for ts in sorted(DRILL_DATA.glob("matcha-framework-*-decisions-cards.ts")):
        deck = ts.stem.replace("-cards", "")
        scn_type = deck_to_type.get(deck, "OTHER")
        for card in extract_cards(ts):
            board_s = card.get("front", {}).get("board")
            if not board_s:
                continue
            board = parse_board(board_s)
            if not board or len(board) < 3:
                continue
            flop = "".join(board[:3])
            key = f"{flop}|{scn_type}"
            targets[key].append((deck, card.get("id", "")))
    return targets


# ════════════════════════════════════════════════════════════
# (B) board 境界 spot
# ════════════════════════════════════════════════════════════

# 境界 spot 設計: 各 board type のグレーゾーンに位置する boards を選定
# MATCHA RANGE_MORPHOLOGY: POLAR(dynamic/2tone/monotone) / MERGED(dry_high/low_dry/paired) / CONDENSED(other)
BOUNDARY_SPOTS: list[dict[str, str]] = [
    # ── dynamic vs medium-connectivity 境界 ──
    {"board": "9s8d7c", "category": "dynamic_clear",  "boundary": "dynamic vs medium", "note": "完全 connected straight 可"},
    {"board": "9s8d6c", "category": "dynamic_oneOff", "boundary": "dynamic vs medium", "note": "1 ギャップ、まだ dynamic 寄り"},
    {"board": "9s7d5c", "category": "medium_dynamic", "boundary": "dynamic vs medium", "note": "2 ギャップ、grayzone"},
    {"board": "9s6d3c", "category": "spread_medium",  "boundary": "dynamic vs medium", "note": "3 ギャップ、もう dynamic でない"},
    # ── monotone vs 2-tone 境界 ──
    {"board": "jsts4s", "category": "monotone_3spade","boundary": "monotone vs 2-tone", "note": "3-spade、明確 monotone"},
    {"board": "jsts4h", "category": "two_tone",       "boundary": "monotone vs 2-tone", "note": "2-spade、 FD あり"},
    {"board": "jstc4s", "category": "two_tone_spread","boundary": "monotone vs 2-tone", "note": "JT 2-tone, 完全 2 tone"},
    # ── dry_high vs medium 境界 ──
    {"board": "ks7d2c", "category": "dry_high_clear", "boundary": "dry_high boundary", "note": "K-high で perfect dry"},
    {"board": "ks8d2c", "category": "dry_high_kicker","boundary": "dry_high boundary", "note": "K8x、少し connectivity"},
    {"board": "ks9d4c", "category": "dry_high_mid",   "boundary": "dry_high boundary", "note": "K9x、middle range"},
    {"board": "kh9c5d", "category": "merged_high",    "boundary": "dry_high boundary", "note": "K9x rainbow、merged 寄り"},
    # ── paired board variation ──
    {"board": "kskd4c", "category": "paired_high",    "boundary": "paired boundary",   "note": "K-paired"},
    {"board": "kskd9c", "category": "paired_high_connector", "boundary": "paired boundary", "note": "KK + 9 (TP draw)"},
    {"board": "4s4d2c", "category": "paired_low",     "boundary": "paired boundary",   "note": "low pair-bottom"},
    # ── low_dry boundary ──
    {"board": "8s5d3h", "category": "low_dry",        "boundary": "low_dry boundary",  "note": "low_dry classic"},
    {"board": "7s4d2c", "category": "very_low_dry",   "boundary": "low_dry boundary",  "note": "very low"},
    {"board": "8s6d3h", "category": "low_dynamic",    "boundary": "low_dry boundary",  "note": "ややconnected low"},
    # ── ace high boundary ──
    {"board": "as9d4c", "category": "ace_high_dry",   "boundary": "ace_high boundary", "note": "A-high dry"},
    {"board": "ast d4c","category": "ace_high_kicker","boundary": "ace_high boundary", "note": "A-T-x, broadway"},
    {"board": "astd9c", "category": "ace_high_broadway", "boundary": "ace_high boundary", "note": "A-T-9 broadway"},
]


def collect_boundary_targets() -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = defaultdict(list)
    for spot in BOUNDARY_SPOTS:
        b = spot["board"].replace(" ", "")
        out[b].append(spot)
    return out


# ════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════


def main() -> None:
    # dataset 既存 flops
    print(f"Loading dataset...")
    with open(DATASET) as f:
        rows = list(csv.DictReader(f))
    dataset_flops: set[str] = set()
    for r in rows:
        b = r["board_str"].lower()
        if len(b) >= 6:
            dataset_flops.add(b[:6])
    print(f"  dataset flops: {len(dataset_flops)}")

    # (A) drill targets
    drill_targets = collect_drill_targets()
    print(f"\n(A) drill 使用 (flop, scenario_type) 組合せ: {len(drill_targets)}")

    # filter to missing (not in dataset) — case insensitive
    drill_missing: dict[str, list] = {}
    for key, refs in drill_targets.items():
        flop = key.split("|")[0].lower()
        if flop not in dataset_flops:
            drill_missing[key] = refs
    print(f"  dataset 未カバー: {len(drill_missing)}")

    # (B) boundary — case insensitive
    boundary_targets = collect_boundary_targets()
    print(f"\n(B) board 境界 spots: {len(boundary_targets)}")
    boundary_missing = {b: spots for b, spots in boundary_targets.items() if b.lower() not in dataset_flops}
    print(f"  dataset 未カバー: {len(boundary_missing)}")

    # Build probe spec
    probe_spec: list[dict] = []

    # (A) drill content audit
    for key, refs in drill_missing.items():
        flop, scn_type = key.split("|")
        probe_spec.append({
            "purpose": "drill_audit",
            "flop": flop,
            "scenario_type": scn_type,
            "n_drill_cards": len(refs),
            "example_refs": refs[:3],
            "priority": min(3, max(1, 4 - (len(refs) > 1) - (len(refs) > 3))),  # heuristic
        })

    # (B) boundary
    for board, spots in boundary_missing.items():
        for s in spots:
            probe_spec.append({
                "purpose": "boundary_validation",
                "flop": board,
                "category": s["category"],
                "boundary_type": s["boundary"],
                "note": s["note"],
                "scenario_type": "SRP_flop+3BP+4BP",  # 各 pot type で見る
                "priority": 2,
            })

    # Write JSON
    TARGETS.parent.mkdir(parents=True, exist_ok=True)
    TARGETS.write_text(json.dumps(probe_spec, ensure_ascii=False, indent=2))

    # Summary
    drill_specs = [p for p in probe_spec if p["purpose"] == "drill_audit"]
    boundary_specs = [p for p in probe_spec if p["purpose"] == "boundary_validation"]

    # Markdown plan
    lines: list[str] = []
    lines.append("# Probe targets plan — drill audit + 境界 spot 検証")
    lines.append("")
    lines.append(f"出力 JSON: `{TARGETS.relative_to(REPO_ROOT)}`")
    lines.append("")
    lines.append("## サマリー")
    lines.append("")
    lines.append(f"| 目的 | spec 数 | 内容 |")
    lines.append(f"|------|--------:|------|")
    lines.append(f"| (A) drill audit | {len(drill_specs)} | drill が使うが dataset 未カバーの (flop, scenario) |")
    lines.append(f"| (B) boundary validation | {len(boundary_specs)} | 板タイプ境界 spot で分類精度検証 |")
    lines.append(f"| **合計** | **{len(probe_spec)}** | |")
    lines.append("")

    lines.append("## (A) drill audit targets (優先度順、drill 使用回数 = 重要度)")
    lines.append("")
    lines.append("| priority | flop | scenario_type | drill cards | 例 |")
    lines.append("|---------:|------|---------------|-----------:|-----|")
    for p in sorted(drill_specs, key=lambda x: (x["priority"], -x["n_drill_cards"])):
        examples = ", ".join(f"{d}/{c}" for d, c in p["example_refs"])
        lines.append(f"| P{p['priority']} | `{p['flop']}` | {p['scenario_type']} | {p['n_drill_cards']} | {examples[:80]} |")
    lines.append("")

    lines.append("## (B) 板タイプ境界 spot targets")
    lines.append("")
    lines.append("MATCHA レンジ分布判定 (POLAR / MERGED / CONDENSED) の境界に位置する spots:")
    lines.append("")
    lines.append("| boundary | flop | category | 検証目的 |")
    lines.append("|----------|------|----------|---------|")
    by_boundary = defaultdict(list)
    for p in boundary_specs:
        by_boundary[p["boundary_type"]].append(p)
    for bdry, ps in sorted(by_boundary.items()):
        for p in ps:
            lines.append(f"| {bdry} | `{p['flop']}` | {p['category']} | {p['note']} |")
    lines.append("")

    lines.append("## probe 実行プラン (推定)")
    lines.append("")
    lines.append("各 (flop, scenario_type) ペアに対し:")
    lines.append("- SRP scenarios: GTO Wizard `Cash6mTest_6mNL100R2` 100bb")
    lines.append("- 3BP / 4BP: 各 pot_type で対応")
    lines.append("- MTT: `MTTGeneral_8m` (25 / 100 / 200bb)")
    lines.append("")
    lines.append("API call estimation:")
    lines.append(f"- (A) drill missing: {len(drill_specs)} (flop, scenario_type) ペア")
    lines.append(f"- (B) boundary: {len(boundary_specs)} flops × ~3 pot_types = ~{len(boundary_specs)*3} ペア")
    lines.append(f"- **合計: ~{len(drill_specs) + len(boundary_specs)*3} API calls**")
    lines.append("")
    lines.append("各 API call で ~500-1000 rows (hand combos × bet sizes) 取得可能。")
    lines.append("→ 期待 dataset 拡張: ~30,000-100,000 rows")
    lines.append("")
    lines.append("## 次手")
    lines.append("")
    lines.append("1. quota 確認: `scripts/gto_wizard_study/.token` の認証状態 + 残 quota")
    lines.append("2. probe スクリプト準備: `PROBE_TARGETS.json` を input に `fetch_smart.py` で投入")
    lines.append("3. データ統合: 既存 `aggregate_*.py` 流用 → dataset_unified_v2.csv に追記 (or 新 csv)")
    lines.append("4. audit 再実行: `audit_drill_extensions.py` で match 率上昇を確認")

    PLAN_DOC.write_text("\n".join(lines))

    print(f"\n=== 出力 ===")
    print(f"  JSON: {TARGETS}")
    print(f"  Markdown plan: {PLAN_DOC}")
    print(f"\n=== Probe size 推定 ===")
    print(f"  (A) drill audit specs: {len(drill_specs)}")
    print(f"  (B) boundary validation specs: {len(boundary_specs)}")
    print(f"  合計 specs: {len(probe_spec)}")
    print(f"  推定 API call: ~{len(drill_specs) + len(boundary_specs)*3}")


if __name__ == "__main__":
    main()
