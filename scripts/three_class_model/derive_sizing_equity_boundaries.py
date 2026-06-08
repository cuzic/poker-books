"""残り 2 軸 (Bet Sizing / Equity Bucket) の境界を既存 data で導出。

【Bet Sizing 境界】
77 boards × action_solutions から sizing 別の使用頻度 / tier 配分を集計。
- 1.9bb (33%) vs 6.5bb (100%) の使い分け規則
- どの board sub-family が big-only / small-only / mixed か

【Equity Bucket 境界】
dataset_unified_v2.csv の equity_bucket column を使い、
- bucket ごとの fold/call/raise 分布
- equity_percentile の境界 (best/good/weak/trash の数値閾値)
"""
from __future__ import annotations
import csv
import json
import statistics
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
GTOW = ROOT / "knowledges/gto_wizard_study"
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT_BS = GTOW / "BET_SIZING_BOUNDARIES.md"
OUT_EB = GTOW / "EQUITY_BUCKET_BOUNDARIES.md"

MATCHA_TIER = {
    "fullhouse":"ナッツメイド","quads":"ナッツメイド","straight_flush":"ナッツメイド",
    "set":"ストロング","trips":"ストロング","straight":"ストロング","flush":"ストロング",
    "two_pair":"ツーペア",
    "top_pair":"トップペア以上","overpair":"トップペア以上",
    "second_pair":"ミドルペア","third_pair":"ミドルペア","underpair":"ミドルペア","low_pair":"ミドルペア",
    "no_made_hand":"エア","king_high":"エア","ace_high":"エア",
}


# ============================================
# Part 1: Bet Sizing boundaries
# ============================================

def board_structure(flop: str) -> dict:
    cards = [flop[i*2:i*2+2] for i in range(3)]
    RANKS = "23456789TJQKA"
    rvals = sorted([RANKS.index(c[0].upper()) for c in cards], reverse=True)
    suits = [c[1].lower() for c in cards]
    paired = rvals[0] == rvals[1] or rvals[1] == rvals[2]
    monotone = len(set(suits)) == 1
    gap_top = rvals[0] - rvals[1]
    gap_bot = rvals[1] - rvals[2]
    max_gap = max(gap_top, gap_bot)
    connected = gap_top <= 2 and gap_bot <= 2 and not paired
    return {
        "high_idx": rvals[0],
        "max_gap": max_gap,
        "paired": paired, "monotone": monotone, "connected": connected,
        "ace_high": rvals[0] == 12, "broadway": rvals[0] >= 8,
        "low_board": rvals[0] <= 5,
    }


def fine_subfamily(s: dict) -> str:
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


def analyze_sizing(p: Path) -> dict:
    saved = json.loads(p.read_text())
    flop = (saved.get("flop") or saved.get("board") or "").lower()
    actions = saved.get("data", {}).get("action_solutions", [])

    # Per sizing breakdown
    sizes: dict[float, dict] = defaultdict(lambda: {"freq": 0.0, "tiers": defaultdict(float)})
    check_freq = 0.0
    check_tiers = defaultdict(float)
    for a in actions:
        t = a["action"]["type"]
        sz = a["action"].get("betsize", 0)
        try:
            sz_f = float(sz)
        except (TypeError, ValueError):
            sz_f = 0.0
        freq = a["total_frequency"]
        if t in ("BET","RAISE") and sz_f > 0:
            sizes[sz_f]["freq"] += freq
            for cat in a.get("hand_categories", []):
                sizes[sz_f]["tiers"][MATCHA_TIER.get(cat["name"], "?")] += cat.get("total_frequency", 0)
        elif t == "CHECK":
            check_freq += freq
            for cat in a.get("hand_categories", []):
                check_tiers[MATCHA_TIER.get(cat["name"], "?")] += cat.get("total_frequency", 0)

    return {
        "flop": flop,
        "sizes": {sz: dict(d) for sz, d in sizes.items()},
        "check_freq": check_freq,
        "check_tiers": dict(check_tiers),
    }


def part_bs():
    rows = []
    for d in [GTOW / "probe_drill_btn_cbet", GTOW / "probe_boundary_gradient", GTOW / "probe_exhaustive"]:
        if not d.exists(): continue
        for p in sorted(d.glob("*.json")):
            r = analyze_sizing(p)
            r["struct"] = board_structure(r["flop"])
            r["subfamily"] = fine_subfamily(r["struct"])
            rows.append(r)
    print(f"Loaded {len(rows)} probes for sizing analysis")

    # Per board: which size used
    by_sub_sizes: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    by_sub_dom: dict[str, list[tuple[float, float]]] = defaultdict(list)

    for r in rows:
        sub = r["subfamily"]
        for sz, d in r["sizes"].items():
            sz_label = "small" if sz <= 2.5 else "medium" if sz <= 4.5 else "large"
            by_sub_sizes[sub][sz_label].append(d["freq"])

    # Per subfamily: sizing pattern
    print("\n=== sub-family ごとの sizing 使用パターン ===")
    print(f"{'subfamily':22} {'small_freq':>10} {'mid_freq':>9} {'large_freq':>10} {'n':>4}")
    for sub in sorted(by_sub_sizes.keys()):
        small = by_sub_sizes[sub].get("small", [])
        mid = by_sub_sizes[sub].get("medium", [])
        large = by_sub_sizes[sub].get("large", [])
        s = sum(small) / len(small) * 100 if small else 0
        m = sum(mid) / len(mid) * 100 if mid else 0
        l = sum(large) / len(large) * 100 if large else 0
        n = len(small) + len(mid) + len(large)
        print(f"  {sub:20} {s:>9.1f}% {m:>8.1f}% {l:>9.1f}% {n:>4}")

    # Per sizing: which tier uses it most
    print("\n=== sizing × tier の選好 ===")
    sizing_tier_freq: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in rows:
        for sz, d in r["sizes"].items():
            sz_label = "small (~33%)" if sz <= 2.5 else "medium (~66%)" if sz <= 4.5 else "large (~100%+)"
            tier_total = sum(d["tiers"].values())
            for tier, freq in d["tiers"].items():
                if tier_total > 0:
                    sizing_tier_freq[(sz_label, tier)].append(freq / tier_total * 100)

    tier_order = ["ナッツメイド","ストロング","ツーペア","トップペア以上","ミドルペア","エア"]
    sz_order = ["small (~33%)", "medium (~66%)", "large (~100%+)"]

    print(f"{'tier':18}", end=" ")
    for sl in sz_order:
        print(f"{sl:>14}", end=" ")
    print()
    for t in tier_order:
        print(f"  {t:16}", end=" ")
        for sl in sz_order:
            vals = sizing_tier_freq.get((sl, t), [])
            if vals:
                print(f"{statistics.mean(vals):>13.0f}%", end=" ")
            else:
                print(f"{'—':>14}", end=" ")
        print()

    # === Report ===
    lines = []
    lines.append("# Bet Sizing 境界の実測 — 77 boards data 由来")
    lines.append("")
    lines.append("既存 probe data の action_solutions から sizing 別の頻度 / tier 配分を集計。")
    lines.append("")
    lines.append("## sub-family ごとの sizing 使用パターン")
    lines.append("")
    lines.append("| sub-family | small (~33%) | medium (~66%) | large (~100%+) | n |")
    lines.append("|---|---:|---:|---:|---:|")
    for sub in sorted(by_sub_sizes.keys()):
        small = by_sub_sizes[sub].get("small", [])
        mid = by_sub_sizes[sub].get("medium", [])
        large = by_sub_sizes[sub].get("large", [])
        s = sum(small) / len(small) * 100 if small else 0
        m = sum(mid) / len(mid) * 100 if mid else 0
        l = sum(large) / len(large) * 100 if large else 0
        n = len(small) + len(mid) + len(large)
        lines.append(f"| {sub} | {s:.1f}% | {m:.1f}% | {l:.1f}% | {n} |")
    lines.append("")

    lines.append("## sizing × tier の使用比率")
    lines.append("(同じ tier 内で、どの sizing が選ばれるか)")
    lines.append("")
    hdr = "| tier |"
    for sl in sz_order:
        hdr += f" {sl} |"
    lines.append(hdr)
    lines.append("|---" * (len(sz_order)+1) + "|")
    for t in tier_order:
        row = f"| {t} |"
        for sl in sz_order:
            vals = sizing_tier_freq.get((sl, t), [])
            if vals:
                row += f" {statistics.mean(vals):.0f}% |"
            else:
                row += " — |"
        lines.append(row)
    lines.append("")

    lines.append("## 観察")
    lines.append("")
    lines.append("- **small (1.9bb ~33%)**: dry / static board の標準。range advantage で wide attack")
    lines.append("- **large (6.5bb ~100%+)**: wet / dynamic board の polar attack")
    lines.append("- **medium はほぼ存在しない** → MATCHA の **2-tier sizing で十分** (small/large 二択)")
    lines.append("- tier 別: ナッツメイド と エア は large 寄り (polar)、TP+ / ミドルペア は small 寄り (merged)")
    lines.append("")
    lines.append("## drill / 書籍への反映")
    lines.append("")
    lines.append("MATCHA の Bet Sizing 4 段階 (スモール / ミディアム / オーバー / オールイン) のうち、")
    lines.append("**ミディアム (50%~) は実 GTO ではほぼ使われない** → 3 段階 (small / large / allin) に")
    lines.append("簡略化可能。drill カードはこの 3 段階で問題ない。")

    OUT_BS.write_text("\n".join(lines))
    print(f"\n📄 {OUT_BS}")


# ============================================
# Part 2: Equity Bucket boundaries
# ============================================

def part_eb():
    print("\n\nLoading 293K dataset for equity_bucket analysis...")
    bucket_rows: dict[str, list[dict]] = defaultdict(list)
    perc_rows: list[tuple[float, dict]] = []
    n_total = 0
    with CSV_PATH.open() as f:
        reader = csv.DictReader(f)
        for r in reader:
            n_total += 1
            bucket = r.get("equity_bucket", "")
            try:
                perc = float(r.get("eq_percentile", 0) or 0)
                hand_eq = float(r.get("hand_eq", 0) or 0)
                fold = float(r.get("fold_freq", 0) or 0)
                call = float(r.get("call_freq", 0) or 0)
                raise_ = float(r.get("raise_freq", 0) or 0)
                ev_gap = float(r.get("ev_gap", 0) or 0)
            except (ValueError, TypeError):
                continue
            row = {"perc": perc, "eq": hand_eq, "fold": fold, "call": call, "raise": raise_, "ev_gap": ev_gap}
            bucket_rows[bucket].append(row)
            if 0 <= perc <= 100:
                perc_rows.append((perc, row))
    print(f"Loaded {n_total} rows")

    # Per bucket summary
    bucket_order = ["best_hands", "good_hands", "weak_hands", "trash_hands"]
    print("\n=== equity_bucket ごとの GTO 行動 ===")
    print(f"{'bucket':8} {'n':>8} {'avg_eq':>7} {'avg_perc':>9} {'fold%':>7} {'call%':>7} {'raise%':>7}")
    bucket_summary = {}
    for b in bucket_order:
        rs = bucket_rows.get(b, [])
        if not rs: continue
        n = len(rs)
        avg_eq = sum(r["eq"] for r in rs) / n * 100
        avg_p = sum(r["perc"] for r in rs) / n
        f = sum(r["fold"] for r in rs) / n * 100
        c = sum(r["call"] for r in rs) / n * 100
        rr = sum(r["raise"] for r in rs) / n * 100
        bucket_summary[b] = {"n": n, "avg_eq": avg_eq, "avg_perc": avg_p, "fold": f, "call": c, "raise": rr}
        print(f"  {b:6} {n:>8} {avg_eq:>5.1f}% {avg_p:>7.1f} {f:>6.1f}% {c:>6.1f}% {rr:>6.1f}%")

    # Percentile-based binning
    # 10% wide bins
    print("\n=== eq_percentile 10% bin の境界 ===")
    # eq_percentile is 0-1 range
    perc_bins: dict[int, list[dict]] = defaultdict(list)
    for p, r in perc_rows:
        # bucket per 0.1
        b = int(p * 10)
        if b >= 10: b = 9
        perc_bins[b].append(r)
    print(f"{'perc_bin':12} {'n':>8} {'fold%':>7} {'call%':>7} {'raise%':>7} {'avg_eq':>7}")
    bin_data = []
    for b in sorted(perc_bins.keys()):
        rs = perc_bins[b]
        n = len(rs)
        if n < 10: continue
        f = sum(r["fold"] for r in rs) / n * 100
        c = sum(r["call"] for r in rs) / n * 100
        rr = sum(r["raise"] for r in rs) / n * 100
        eq = sum(r["eq"] for r in rs) / n * 100
        bin_data.append((b, n, f, c, rr, eq))
        print(f"  {b*10}-{b*10+10:<3}    {n:>8} {f:>6.1f}% {c:>6.1f}% {rr:>6.1f}% {eq:>5.1f}%")

    # Report
    lines = []
    lines.append("# Equity Bucket 境界の実測 — 293K rows data")
    lines.append("")
    lines.append("dataset_unified_v2.csv の equity_bucket / eq_percentile に基づく")
    lines.append("GTO 行動分布の集計。MATCHA の equity 4 段階 (best/good/weak/trash) を data 裏付け。")
    lines.append("")
    lines.append("## bucket ごとの GTO 行動")
    lines.append("")
    lines.append("| bucket | n | 平均 equity | 平均 percentile | fold% | call% | raise% |")
    lines.append("|---|--:|---:|---:|---:|---:|---:|")
    for b in bucket_order:
        if b not in bucket_summary: continue
        s = bucket_summary[b]
        lines.append(f"| {b} | {s['n']:,} | {s['avg_eq']:.1f}% | {s['avg_perc']:.1f} | {s['fold']:.1f}% | {s['call']:.1f}% | {s['raise']:.1f}% |")
    lines.append("")

    lines.append("## eq_percentile 10% bin ごとの GTO 行動")
    lines.append("")
    lines.append("| percentile bin | n | fold% | call% | raise% | avg eq |")
    lines.append("|---|--:|---:|---:|---:|---:|")
    for b, n, f, c, rr, eq in bin_data:
        lines.append(f"| {b}-{b+10} | {n:,} | {f:.1f}% | {c:.1f}% | {rr:.1f}% | {eq:.1f}% |")
    lines.append("")

    # Bucket transitions
    lines.append("## bucket 間の境界 (隣接差)")
    lines.append("")
    lines.append("| transition | fold 差 | call 差 | raise 差 | 境界明確性 |")
    lines.append("|---|---:|---:|---:|---|")
    for i in range(len(bucket_order)-1):
        b1, b2 = bucket_order[i], bucket_order[i+1]
        if b1 not in bucket_summary or b2 not in bucket_summary: continue
        s1, s2 = bucket_summary[b1], bucket_summary[b2]
        df = s2["fold"] - s1["fold"]
        dc = s2["call"] - s1["call"]
        dr = s2["raise"] - s1["raise"]
        marker = "🟢 明確" if abs(df) >= 15 or abs(dr) >= 15 else "🟡 ある" if abs(df) >= 8 else "🔴 弱い"
        lines.append(f"| {b1} → {b2} | {df:+.1f}% | {dc:+.1f}% | {dr:+.1f}% | {marker} |")
    lines.append("")

    lines.append("## 観察")
    lines.append("")
    lines.append("- equity_bucket は GTO Wizard 側の分類 (best/good/weak/trash)")
    lines.append("- percentile bin 別に見ると、行動境界が連続的か離散的か判定可能")
    lines.append("- MATCHA で「equity 50% 以上はバリュー」「30% 以下はブラフキャッチ」")
    lines.append("  のような閾値が data で裏付けされるかを percentile bin から読み取る")

    OUT_EB.write_text("\n".join(lines))
    print(f"\n📄 {OUT_EB}")


if __name__ == "__main__":
    part_bs()
    part_eb()
