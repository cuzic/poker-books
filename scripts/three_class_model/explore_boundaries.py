"""境界探索スクリプト — 任意の cell で「書籍に書ける境界条件」を data から抽出。

【設計思想】
読者が迷わない境界条件 = 各 (条件) で fold/call/raise の 1 action が dominant な spot。
dominant でない spot は "迷うところ" として別扱い。

【cell 分類】
- PURE (max_freq ≥ 80%): 暗記対象。書籍に「この条件なら必ず X」と書ける
- STRONG (60-80%): 推奨。「基本 X、たまに別」
- MIXED (40-60%): 状況依存。「2 つ拮抗」
- BALANCED (<40%): 完全に状況依存。書籍では 個別分析必要

【入力フィルタ】
- pot_type (SRP/3BP/4BP/DEF) — scenario_id から推定
- street (flop/turn/river)
- depth (Cash/MTT25/50/100/200) — scenario_id から推定
- sub_family / tier — board × hand 分類

【出力】
- 全 cell の分類 (PURE/STRONG/MIXED/BALANCED) と representative action
- PURE cell リスト = 書籍に転載可能な境界条件
- BALANCED cell リスト = さらなる調査が必要な穴

使用例:
    uv run python explore_boundaries.py                 # 全 cell
    uv run python explore_boundaries.py --pot 4BP        # 4BP only
    uv run python explore_boundaries.py --street river   # river only
    uv run python explore_boundaries.py --pot 4BP --street flop --pure-only
"""
from __future__ import annotations
import argparse
import csv
import re
import sys
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT_DIR = ROOT / "knowledges/gto_wizard_study"

MATCHA_TIER = {
    "fullhouse":"ナッツメイド","quads":"ナッツメイド","straight_flush":"ナッツメイド",
    "set":"ストロング","trips":"ストロング","straight":"ストロング","flush":"ストロング",
    "two_pair":"ツーペア",
    "top_pair":"トップペア以上","overpair":"トップペア以上",
    "second_pair":"ミドルペア","third_pair":"ミドルペア","underpair":"ミドルペア","low_pair":"ミドルペア",
    "no_made_hand":"エア","king_high":"エア","ace_high":"エア",
}

TIER_ORDER = ["ナッツメイド","ストロング","ツーペア","トップペア以上","ミドルペア","エア"]


def board_structure(flop: str) -> dict:
    if len(flop) < 6:
        return {}
    cards = [flop[i*2:i*2+2] for i in range(3)]
    RANKS = "23456789TJQKA"
    try:
        rvals = sorted([RANKS.index(c[0].upper()) for c in cards], reverse=True)
    except ValueError:
        return {}
    suits = [c[1].lower() for c in cards]
    paired = rvals[0] == rvals[1] or rvals[1] == rvals[2]
    monotone = len(set(suits)) == 1
    gap_top = rvals[0] - rvals[1]
    gap_bot = rvals[1] - rvals[2]
    connected = gap_top <= 2 and gap_bot <= 2 and not paired
    return {
        "high_idx": rvals[0],
        "max_gap": max(gap_top, gap_bot),
        "paired": paired, "monotone": monotone, "connected": connected,
        "ace_high": rvals[0] == 12, "broadway": rvals[0] >= 8,
        "low_board": rvals[0] <= 5,
    }


def fine_subfamily(s: dict) -> str:
    if not s: return "?"
    if s["paired"]:
        if s["high_idx"] >= 11: return "paired_high"
        if s["high_idx"] >= 8: return "paired_broadway"
        if s["high_idx"] >= 5: return "paired_mid"
        return "paired_low"
    if s["monotone"]: return "monotone"
    if s["connected"]:
        if s["high_idx"] >= 11: return "connected_broadway"
        if s["high_idx"] >= 7: return "connected_mid"
        return "connected_low"
    if s["ace_high"]:
        return "Ahigh_spread" if s["max_gap"] >= 5 else "Ahigh_close"
    if s["high_idx"] == 11:
        return "Khigh_spread" if s["max_gap"] >= 5 else "Khigh_close"
    if s["broadway"]: return "broadway_dry"
    if s["low_board"]: return "low_dry"
    return "mid_dry"


def parse_scenario(scn: str) -> dict:
    """scenario_id から (pot, street, depth) を推定。"""
    s = scn.lower()
    pot = "4BP" if "4bp" in s else "3BP" if "3bp" in s else \
          "DEF" if ("cr_def" in s or "donk_def" in s) else "SRP"
    if "river" in s: street = "river"
    elif "turn" in s: street = "turn"
    elif "flop" in s: street = "flop"
    elif "_r1" in s: street = "preflop"
    else: street = "flop"  # default for bvb, btn_sb, etc.

    # depth
    m = re.search(r"mtt(\d+)", s)
    depth = f"MTT{m.group(1)}" if m else ("MTT100" if "mtt" in s else "Cash100")

    return {"pot": pot, "street": street, "depth": depth}


@dataclass
class CellStats:
    n: int = 0
    fold: float = 0.0
    call: float = 0.0
    raise_: float = 0.0

    def classify(self) -> tuple[str, str, float]:
        """returns (purity_class, dominant_action, dominant_freq)."""
        if self.n == 0:
            return ("NO_DATA", "?", 0)
        actions = [("fold", self.fold), ("call", self.call), ("raise", self.raise_)]
        actions.sort(key=lambda x: -x[1])
        dom_action, dom_freq = actions[0]
        if dom_freq >= 0.80:
            return ("PURE", dom_action, dom_freq)
        if dom_freq >= 0.60:
            return ("STRONG", dom_action, dom_freq)
        if dom_freq >= 0.40:
            return ("MIXED", dom_action, dom_freq)
        return ("BALANCED", dom_action, dom_freq)


def load_cells(args) -> dict[tuple, CellStats]:
    """CSV を読み込み、cell (pot, street, depth, sub, tier) でグループ化。"""
    raw: dict[tuple, list[dict]] = defaultdict(list)
    n_total = 0

    with CSV_PATH.open() as f:
        reader = csv.DictReader(f)
        for r in reader:
            scn_info = parse_scenario(r["scenario_id"])
            if args.pot and scn_info["pot"] != args.pot: continue
            if args.street and scn_info["street"] != args.street: continue
            if args.depth and scn_info["depth"] != args.depth: continue

            board = r.get("board_str", "")[:6].lower()
            sub = fine_subfamily(board_structure(board))
            if args.sub and sub != args.sub: continue

            tier = MATCHA_TIER.get(r["mv_cat"], "?")
            if args.tier and tier != args.tier: continue

            n_total += 1
            try:
                raw[(scn_info["pot"], scn_info["street"], scn_info["depth"], sub, tier)].append({
                    "fold": float(r.get("fold_freq", 0) or 0),
                    "call": float(r.get("call_freq", 0) or 0),
                    "raise": float(r.get("raise_freq", 0) or 0),
                })
            except (ValueError, TypeError):
                continue

    print(f"Loaded {n_total} rows after filtering")

    cells: dict[tuple, CellStats] = {}
    for key, rows in raw.items():
        n = len(rows)
        if n < args.min_n: continue
        cells[key] = CellStats(
            n=n,
            fold=sum(r["fold"] for r in rows) / n,
            call=sum(r["call"] for r in rows) / n,
            raise_=sum(r["raise"] for r in rows) / n,
        )
    return cells


def write_report(cells: dict[tuple, CellStats], args) -> Path:
    """境界 spec を MD ファイルで出力。"""
    pure: list[tuple] = []
    strong: list[tuple] = []
    mixed: list[tuple] = []
    balanced: list[tuple] = []
    for key, c in cells.items():
        cls, dom, freq = c.classify()
        if cls == "PURE": pure.append((key, c, dom, freq))
        elif cls == "STRONG": strong.append((key, c, dom, freq))
        elif cls == "MIXED": mixed.append((key, c, dom, freq))
        else: balanced.append((key, c, dom, freq))

    print(f"\nClassification:")
    print(f"  PURE     (≥80%): {len(pure):>4} cells")
    print(f"  STRONG (60-80%): {len(strong):>4} cells")
    print(f"  MIXED  (40-60%): {len(mixed):>4} cells")
    print(f"  BALANCED (<40%): {len(balanced):>4} cells")

    # filename suffix
    parts = []
    if args.pot: parts.append(args.pot)
    if args.street: parts.append(args.street)
    if args.depth and args.depth != "Cash100": parts.append(args.depth)
    if args.sub: parts.append(args.sub)
    suffix = "_".join(parts) if parts else "all"
    out = OUT_DIR / f"BOUNDARIES_{suffix}.md"

    lines = []
    title_filter = f" ({', '.join(parts)})" if parts else ""
    lines.append(f"# 境界 spec{title_filter} — data 駆動の境界条件")
    lines.append("")
    lines.append(f"フィルタ: pot={args.pot or '*'}, street={args.street or '*'}, "
                 f"depth={args.depth or '*'}, sub={args.sub or '*'}, tier={args.tier or '*'}")
    lines.append(f"閾値: PURE ≥80% / STRONG 60-80% / MIXED 40-60% / BALANCED <40%")
    lines.append(f"最小 n: {args.min_n}")
    lines.append("")
    lines.append(f"## 集計")
    lines.append("")
    lines.append(f"| class | 意味 | n cells |")
    lines.append(f"|---|---|---:|")
    lines.append(f"| PURE | 暗記対象、書籍に書ける | {len(pure)} |")
    lines.append(f"| STRONG | 基本そうする (たまに別) | {len(strong)} |")
    lines.append(f"| MIXED | 拮抗、状況依存 | {len(mixed)} |")
    lines.append(f"| BALANCED | 完全に状況依存、要追加調査 | {len(balanced)} |")
    lines.append("")

    # === PURE: 書籍に書ける境界条件 ===
    lines.append("## 🟢 PURE 境界 (暗記対象)")
    lines.append("")
    lines.append("dominant action 頻度 ≥80% の cell。読者は条件確認 → 即アクション。")
    lines.append("")
    lines.append("| pot | street | depth | sub-family | tier | action | freq | n |")
    lines.append("|---|---|---|---|---|---|---:|---:|")
    pure.sort(key=lambda x: (x[0][0], x[0][1], x[0][3], x[0][4]))
    for key, c, dom, freq in pure:
        pot, st, dep, sub, tier = key
        lines.append(f"| {pot} | {st} | {dep} | {sub} | {tier} | **{dom}** | {freq*100:.0f}% | {c.n:,} |")
    lines.append("")

    # === STRONG: 推奨 ===
    if not args.pure_only:
        lines.append("## 🟡 STRONG 境界 (推奨アクション)")
        lines.append("")
        lines.append("dominant 60-80%。基本そうするが、たまに別の action もあり。")
        lines.append("")
        lines.append("| pot | street | depth | sub-family | tier | action | freq | n |")
        lines.append("|---|---|---|---|---|---|---:|---:|")
        strong.sort(key=lambda x: -x[3])
        for key, c, dom, freq in strong:
            pot, st, dep, sub, tier = key
            lines.append(f"| {pot} | {st} | {dep} | {sub} | {tier} | {dom} | {freq*100:.0f}% | {c.n:,} |")
        lines.append("")

        # === MIXED: 拮抗 ===
        lines.append("## 🟠 MIXED 境界 (拮抗、状況依存)")
        lines.append("")
        lines.append("dominant 40-60%。2 アクションが拮抗。書籍では「状況による」と書く部分。")
        lines.append("")
        lines.append("| pot | street | depth | sub-family | tier | fold | call | raise | n |")
        lines.append("|---|---|---|---|---|---:|---:|---:|---:|")
        mixed.sort(key=lambda x: (x[0][0], x[0][1], x[0][3], x[0][4]))
        for key, c, dom, freq in mixed:
            pot, st, dep, sub, tier = key
            lines.append(f"| {pot} | {st} | {dep} | {sub} | {tier} | {c.fold*100:.0f}% | {c.call*100:.0f}% | {c.raise_*100:.0f}% | {c.n:,} |")
        lines.append("")

        # === BALANCED: 要さらなる細分化 ===
        lines.append("## 🔴 BALANCED (完全に状況依存、追加調査必要)")
        lines.append("")
        lines.append("どの action も <40%。tier より細かい分類 (kicker, draw, equity etc) で")
        lines.append("細分化しないと判断できない。MATCHA で 5 軸目以上の補正候補。")
        lines.append("")
        lines.append("| pot | street | depth | sub-family | tier | fold | call | raise | n |")
        lines.append("|---|---|---|---|---|---:|---:|---:|---:|")
        balanced.sort(key=lambda x: (x[0][0], x[0][1], x[0][3], x[0][4]))
        for key, c, dom, freq in balanced:
            pot, st, dep, sub, tier = key
            lines.append(f"| {pot} | {st} | {dep} | {sub} | {tier} | {c.fold*100:.0f}% | {c.call*100:.0f}% | {c.raise_*100:.0f}% | {c.n:,} |")
        lines.append("")

    # === gap analysis: cell が NO_DATA な組合せ ===
    lines.append("## ⚪ data 欠落 cell")
    lines.append("")
    lines.append(f"今フィルタで観測されない (pot, street, depth, sub, tier) の組合せ。")
    lines.append("新規 probe の対象候補。")
    lines.append("")
    pots = sorted({k[0] for k in cells})
    streets = sorted({k[1] for k in cells})
    deps = sorted({k[2] for k in cells})
    subs = sorted({k[3] for k in cells if k[3] != "?"})
    tiers = TIER_ORDER

    missing_count = 0
    for pot in pots:
        for st in streets:
            for dep in deps:
                for sub in subs:
                    for tier in tiers:
                        if (pot, st, dep, sub, tier) not in cells:
                            missing_count += 1
    lines.append(f"観測 cell: {len(cells)} / 期待 cell: {len(pots)*len(streets)*len(deps)*len(subs)*len(tiers)} → 欠落: {missing_count}")
    lines.append("")

    out.write_text("\n".join(lines))
    print(f"\n📄 {out}")
    return out


def main():
    parser = argparse.ArgumentParser(description="境界探索 — data 駆動の境界条件抽出")
    parser.add_argument("--pot", choices=["SRP","3BP","4BP","DEF"], help="pot type filter")
    parser.add_argument("--street", choices=["flop","turn","river","preflop"], help="street filter")
    parser.add_argument("--depth", help="depth filter (Cash100, MTT25 etc)")
    parser.add_argument("--sub", help="sub-family filter (Khigh_spread, paired_low, etc)")
    parser.add_argument("--tier", help="hand tier filter (ストロング, トップペア以上 等)")
    parser.add_argument("--min-n", type=int, default=10, help="最小サンプル数 (default 10)")
    parser.add_argument("--pure-only", action="store_true", help="PURE cell のみ出力 (簡潔)")
    args = parser.parse_args()

    cells = load_cells(args)
    print(f"Total cells (n>={args.min_n}): {len(cells)}")
    if not cells:
        print("No cells found. Loosen filters or lower --min-n.")
        sys.exit(1)
    write_report(cells, args)


if __name__ == "__main__":
    main()
