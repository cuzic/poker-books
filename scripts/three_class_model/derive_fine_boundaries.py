"""既存 42 boards の per-combo data を最大活用して boundaries を細分化。

board × hand_strength の cross-tab で:
1. 各 board の per-hand-strength cbet 行動
2. board family 内のさらに細かい cluster (例: A-high dry 内で 50% / 60% に分かれる?)
3. hand_strength tier 内の sub-pattern (例: TPTK vs TPMK の差)

出力: knowledges/gto_wizard_study/FINE_BOUNDARIES.md
"""
from __future__ import annotations
import json
from pathlib import Path
from collections import defaultdict
import statistics

REPO_ROOT = Path(__file__).resolve().parents[2]
GTOW = REPO_ROOT / "knowledges/gto_wizard_study"
OUTPUT = GTOW / "FINE_BOUNDARIES.md"

MATCHA_TIER = {
    "fullhouse": "ナッツメイド","quads": "ナッツメイド","straight_flush": "ナッツメイド",
    "set": "ストロング","trips": "ストロング","straight": "ストロング","flush": "ストロング",
    "two_pair": "ツーペア",
    "top_pair": "トップペア以上","overpair": "トップペア以上",
    "second_pair": "ミドルペア","third_pair": "ミドルペア","underpair": "ミドルペア","low_pair": "ミドルペア",
    "no_made_hand": "エア","king_high": "エア","ace_high": "エア",
}


def board_structure(flop: str) -> dict:
    cards = [flop[i*2:i*2+2] for i in range(3)]
    RANKS = "23456789TJQKA"
    rvals = sorted([RANKS.index(c[0].upper()) for c in cards], reverse=True)
    suits = [c[1].lower() for c in cards]
    paired = rvals[0] == rvals[1] or rvals[1] == rvals[2]
    monotone = len(set(suits)) == 1
    twotone = len(set(suits)) == 2
    gap_top = rvals[0] - rvals[1]
    gap_bot = rvals[1] - rvals[2]
    max_gap = max(gap_top, gap_bot)
    connected = gap_top <= 2 and gap_bot <= 2 and not paired
    high = "23456789TJQKA"[rvals[0]]
    return {
        "high": high, "high_idx": rvals[0],
        "mid_idx": rvals[1], "low_idx": rvals[2],
        "gap_top": gap_top, "gap_bot": gap_bot, "max_gap": max_gap,
        "paired": paired, "monotone": monotone, "twotone": twotone,
        "connected": connected,
        "ace_high": rvals[0] == 12, "king_high": rvals[0] == 11, "broadway": rvals[0] >= 8,
        "low_board": rvals[0] <= 5,
    }


def fine_subfamily(s: dict) -> str:
    """細分化された board sub-family。"""
    if s["paired"]:
        if s["high_idx"] >= 11:  # paired top is K or A
            return "paired_high"
        elif s["high_idx"] >= 8:
            return "paired_broadway"
        elif s["high_idx"] >= 5:
            return "paired_mid"
        else:
            return "paired_low"
    if s["monotone"]:
        return "monotone"
    if s["connected"]:
        if s["high_idx"] >= 11:
            return "connected_broadway"
        elif s["high_idx"] >= 7:
            return "connected_mid"
        else:
            return "connected_low"
    # not paired, not connected, not monotone
    if s["ace_high"]:
        if s["max_gap"] >= 5:
            return "Ahigh_spread"
        else:
            return "Ahigh_close"
    if s["king_high"]:
        if s["max_gap"] >= 5:
            return "Khigh_spread"
        else:
            return "Khigh_close"
    if s["broadway"]:
        return "broadway_dry"
    if s["low_board"]:
        return "low_dry"
    return "mid_dry"


def analyze(p: Path) -> dict:
    saved = json.loads(p.read_text())
    flop = (saved.get("flop") or saved.get("board") or "").lower()
    data = saved.get("data", {})
    actions = data.get("action_solutions", [])
    cbet = sum(a["total_frequency"] for a in actions if a["action"]["type"] in ("BET","RAISE"))
    sizes = sorted([(float(a["action"]["betsize"]), a["total_frequency"]) for a in actions if a["action"]["type"] in ("BET","RAISE")], key=lambda x: -x[1])
    dom_size = sizes[0] if sizes else (0, 0)
    n_sizes = len(sizes)

    # Per-tier behavior
    tier_bet: dict[str, float] = defaultdict(float)
    tier_check: dict[str, float] = defaultdict(float)
    for a in actions:
        is_bet = a["action"]["type"] in ("BET", "RAISE")
        is_check = a["action"]["type"] == "CHECK"
        for cat in a.get("hand_categories", []):
            tier = MATCHA_TIER.get(cat["name"], "?")
            freq = cat.get("total_frequency", 0)
            if is_bet:
                tier_bet[tier] += freq
            elif is_check:
                tier_check[tier] += freq
    tier_bet_ratio: dict[str, float] = {}
    for t in tier_bet.keys() | tier_check.keys():
        total = tier_bet.get(t, 0) + tier_check.get(t, 0)
        tier_bet_ratio[t] = tier_bet.get(t, 0) / total if total > 0 else 0

    return {
        "flop": flop,
        "cbet": cbet,
        "dom_size_bb": dom_size[0],
        "dom_size_freq": dom_size[1],
        "n_sizes": n_sizes,
        "tier_bet_ratio": tier_bet_ratio,
    }


def main():
    rows = []
    for d in [GTOW / "probe_drill_btn_cbet", GTOW / "probe_boundary_gradient", GTOW / "probe_exhaustive"]:
        for p in sorted(d.glob("*.json")):
            r = analyze(p)
            r["struct"] = board_structure(r["flop"])
            r["subfamily"] = fine_subfamily(r["struct"])
            rows.append(r)
    print(f"Loaded {len(rows)} boards")

    # Per subfamily aggregation
    by_subfamily: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_subfamily[r["subfamily"]].append(r)

    print("\n=== Sub-family stats (board-level cbet) ===")
    print(f"{'subfamily':22} {'n':>3} {'cbet avg':>9} {'min':>5} {'max':>5} {'stddev':>6}")
    for sub, ms in sorted(by_subfamily.items(), key=lambda x: -statistics.mean([r['cbet'] for r in x[1]]) if x[1] else 0):
        cbets = [r["cbet"] for r in ms]
        if not cbets: continue
        avg = statistics.mean(cbets) * 100
        std = statistics.stdev(cbets)*100 if len(cbets) > 1 else 0
        print(f"  {sub:20} {len(ms):>3} {avg:>7.1f}% {min(cbets)*100:>4.0f}% {max(cbets)*100:>4.0f}% {std:>5.1f}%")

    # Per (subfamily, tier) cbet
    print("\n=== Sub-family × Hand-strength tier (within-tier cbet%) ===")
    sub_tier: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in rows:
        for tier, ratio in r["tier_bet_ratio"].items():
            sub_tier[(r["subfamily"], tier)].append(ratio)
    tier_order = ["ナッツメイド","ストロング","ツーペア","トップペア以上","ミドルペア","エア"]
    subs_sorted = sorted(by_subfamily.keys(),
                        key=lambda x: -statistics.mean([r['cbet'] for r in by_subfamily[x]]))

    # Header
    hdr = f"{'subfamily':22}"
    for t in tier_order:
        hdr += f"{t[:4]:>7}"
    print(hdr)
    for sub in subs_sorted:
        row_str = f"  {sub:20}"
        for t in tier_order:
            vals = sub_tier.get((sub, t), [])
            if vals:
                row_str += f"{statistics.mean(vals)*100:>6.0f}%"
            else:
                row_str += f"{'—':>7}"
        print(row_str)

    # Write report
    lines = []
    lines.append("# 細分化 boundary 分析 — 42 boards、subfamily × hand_strength")
    lines.append("")
    lines.append("既存 board family (POLAR/MERGED/CONDENSED) より細かい sub-family で分析。")
    lines.append("")
    lines.append("## 13 sub-families (board 構造ベース)")
    lines.append("")
    lines.append("| sub-family | 判定条件 | n probes |")
    lines.append("|------------|---------|---------:|")
    definitions = {
        "paired_high": "paired top + K/A high",
        "paired_broadway": "paired top + T-Q",
        "paired_mid": "paired + 5-9",
        "paired_low": "paired + 2-4",
        "monotone": "3 同 suit",
        "connected_broadway": "connected + high T+",
        "connected_mid": "connected + high 7-9",
        "connected_low": "connected + high 2-6",
        "Ahigh_spread": "A-high、gap ≥5、non-connected",
        "Ahigh_close": "A-high、gap <5",
        "Khigh_spread": "K-high、gap ≥5",
        "Khigh_close": "K-high、gap <5",
        "broadway_dry": "broadway high non-connected",
        "low_dry": "low board (5-high以下)、rainbow",
        "mid_dry": "その他",
    }
    for sub, n_or_msg in [(s, len(by_subfamily[s])) for s in subs_sorted]:
        defn = definitions.get(sub, "?")
        lines.append(f"| {sub} | {defn} | {n_or_msg} |")
    lines.append("")

    lines.append("## sub-family ごとの cbet 頻度 (BTN attacker)")
    lines.append("")
    lines.append("| sub-family | n | cbet 平均 | 範囲 | stddev |")
    lines.append("|------------|---:|---------:|------|------:|")
    for sub in subs_sorted:
        ms = by_subfamily[sub]
        cbets = [r["cbet"] for r in ms]
        avg = statistics.mean(cbets)*100
        std = statistics.stdev(cbets)*100 if len(cbets)>1 else 0
        lines.append(f"| {sub} | {len(ms)} | {avg:.1f}% | {min(cbets)*100:.0f}-{max(cbets)*100:.0f}% | {std:.1f}% |")
    lines.append("")

    lines.append("## sub-family × hand_strength tier の cbet%")
    lines.append("")
    header_md = "| sub-family |" + "|".join(f" {t} " for t in tier_order) + "|"
    sep_md = "|---" * (len(tier_order)+1) + "|"
    lines.append(header_md)
    lines.append(sep_md)
    for sub in subs_sorted:
        row = f"| {sub} |"
        for t in tier_order:
            vals = sub_tier.get((sub, t), [])
            if vals:
                v = statistics.mean(vals)*100
                row += f" {v:.0f}% |"
            else:
                row += " — |"
        lines.append(row)
    lines.append("")

    lines.append("## 解釈: cell ごとの細かい cbet% パターン")
    lines.append("")
    lines.append("- stddev が大きい subfamily = board 依存性大、tier 内でばらつき")
    lines.append("- 「特定 tier だけ cbet が偏る」spots は MATCHA で個別に扱うべき")
    lines.append("- 同じ row 内で tier 間 cbet% 差が 30%+ の場合 = tier 区分が明確 ✓")
    lines.append("- 同じ col 内で sub-family 間 cbet% 差が 20%+ の場合 = board が tier の役割を変える")
    lines.append("")

    # Outliers analysis
    lines.append("## 顕著な outlier (sub-family × tier で特異な行動)")
    lines.append("")
    outliers = []
    for (sub, tier), vals in sub_tier.items():
        if not vals: continue
        v = statistics.mean(vals) * 100
        # tier の全 board 平均
        all_tier = []
        for (s2, t2), v2s in sub_tier.items():
            if t2 == tier: all_tier.extend(v2s)
        if not all_tier: continue
        baseline = statistics.mean(all_tier) * 100
        diff = v - baseline
        if abs(diff) > 15 and len(vals) >= 2:
            outliers.append((diff, sub, tier, v, baseline, len(vals)))
    outliers.sort(key=lambda x: -abs(x[0]))
    if outliers:
        lines.append("| sub-family | tier | local cbet | tier baseline | 差 | n |")
        lines.append("|---|---|---:|---:|---:|---:|")
        for diff, sub, tier, v, base, n in outliers[:20]:
            lines.append(f"| {sub} | {tier} | {v:.0f}% | {base:.0f}% | {diff:+.0f}% | {n} |")

    OUTPUT.write_text("\n".join(lines))
    print(f"\n📄 {OUTPUT}")


if __name__ == "__main__":
    main()
