"""ハンドストレングス階層 (NUT_MADE/STRONG/TWO_PAIR/PAIR/MID_PAIR/AIR) の境界を実 GTO 行動で検証。

既存 probe data の hand_categories per-action を使い、各 mv_cat の cbet 頻度を抽出。
境界が明確 (連続した tier 間で cbet 頻度が大きく変わる) か検証。

GTO Wizard の hand_categories 列挙 (発見):
- 0: no_made_hand
- 1: king_high
- 2: ace_high
- 3: low_pair
- 4: third_pair
- 5: second_pair
- 6: underpair
- 7: top_pair
- 8: overpair
- 9: two_pair
- 10+: trips / set / straight / flush / fullhouse 等

MATCHA tier との対応:
- ナッツメイド = fullhouse/quads/straight_flush (cat 13+?)
- ストロング = set/trips/straight/flush (cat 10-12)
- ツーペア = two_pair (cat 9)
- トップペア以上 = top_pair/overpair (cat 7, 8)
- ミドルペア = second_pair/third_pair/underpair/low_pair (cat 3-6)
- エア = no_made_hand/king_high/ace_high (cat 0-2)
"""
from __future__ import annotations
import json
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parents[2]
GTOW = REPO_ROOT / "knowledges/gto_wizard_study"
BTN_DIR = GTOW / "probe_drill_btn_cbet"
GRAD_DIR = GTOW / "probe_boundary_gradient"
OUTPUT = GTOW / "HAND_STRENGTH_BOUNDARIES.md"

# MATCHA tier mapping
MATCHA_TIER = {
    "fullhouse": "ナッツメイド",
    "quads": "ナッツメイド",
    "straight_flush": "ナッツメイド",
    "set": "ストロング",
    "trips": "ストロング",
    "straight": "ストロング",
    "flush": "ストロング",
    "two_pair": "ツーペア",
    "top_pair": "トップペア以上",
    "overpair": "トップペア以上",
    "second_pair": "ミドルペア",
    "third_pair": "ミドルペア",
    "underpair": "ミドルペア",
    "low_pair": "ミドルペア",
    "no_made_hand": "エア",
    "king_high": "エア",
    "ace_high": "エア",
}


def analyze_probe(p_file: Path) -> dict:
    saved = json.loads(p_file.read_text())
    flop = (saved.get("flop") or saved.get("board") or "").lower()
    data = saved.get("data", {})
    actions = data.get("action_solutions", [])

    # For each action, get hand_categories list of dicts
    # hand_categories: [{name, total_combos, total_frequency}, ...]
    per_cat: dict[str, dict] = defaultdict(lambda: {"bet_freq": 0.0, "check_freq": 0.0, "total_combos": 0.0})

    for a in actions:
        act_type = a["action"]["type"]
        cats = a.get("hand_categories", [])
        is_bet = act_type in ("BET", "RAISE")
        is_check = act_type == "CHECK"
        for cat in cats:
            name = cat["name"]
            freq_in_action = cat.get("total_frequency", 0)
            combos = cat.get("total_combos", 0)
            if is_bet:
                per_cat[name]["bet_freq"] += freq_in_action
            elif is_check:
                per_cat[name]["check_freq"] += freq_in_action
            per_cat[name]["total_combos"] = max(per_cat[name]["total_combos"], combos)

    # Normalize: bet ratio within category = bet_freq / (bet_freq + check_freq)
    cats_summary = {}
    for name, d in per_cat.items():
        total = d["bet_freq"] + d["check_freq"]
        bet_ratio = d["bet_freq"] / total if total > 0 else 0
        cats_summary[name] = {
            "bet_ratio_within_cat": bet_ratio,
            "total_freq_in_range": total,
        }
    return {"flop": flop, "cats": cats_summary}


def main():
    # Load all probes
    rows = []
    for d in [BTN_DIR, GRAD_DIR]:
        for p in sorted(d.glob("*.json")):
            r = analyze_probe(p)
            if r["cats"]:
                rows.append(r)
    print(f"Loaded {len(rows)} probes")

    # Aggregate per (matcha_tier, board)
    # Better: per matcha_tier, average bet_ratio across all boards
    tier_stats: dict[str, list[float]] = defaultdict(list)
    cat_stats: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        for cat_name, d in r["cats"].items():
            tier = MATCHA_TIER.get(cat_name, f"unmapped_{cat_name}")
            tier_stats[tier].append(d["bet_ratio_within_cat"])
            cat_stats[cat_name].append(d["bet_ratio_within_cat"])

    # Print MATCHA tier summary
    tier_order = ["ナッツメイド", "ストロング", "ツーペア", "トップペア以上", "ミドルペア", "エア"]

    print("\n=== MATCHA tier ごとの BTN cbet 頻度 (within tier、42 boards 平均) ===")
    print(f"{'tier':18} {'avg_bet%':>8} {'min%':>6} {'max%':>6} {'n_data':>7}")
    for t in tier_order:
        vals = tier_stats.get(t, [])
        if not vals:
            continue
        avg = sum(vals) / len(vals) * 100
        print(f"  {t:16} {avg:>7.1f}% {min(vals)*100:>5.0f}% {max(vals)*100:>5.0f}% {len(vals):>7}")

    print("\n=== mv_cat ごとの詳細 ===")
    print(f"{'mv_cat':18} {'tier':16} {'avg_bet%':>8} {'min%':>6} {'max%':>6}")
    cat_order = ["fullhouse","quads","straight_flush","set","trips","straight","flush","two_pair","top_pair","overpair","second_pair","third_pair","underpair","low_pair","no_made_hand","king_high","ace_high"]
    for c in cat_order:
        vals = cat_stats.get(c, [])
        if not vals:
            continue
        avg = sum(vals)/len(vals)*100
        tier = MATCHA_TIER.get(c, "?")
        print(f"  {c:16} {tier:14} {avg:>7.1f}% {min(vals)*100:>5.0f}% {max(vals)*100:>5.0f}%")

    # Look for boundaries: where does bet% drop between adjacent tiers?
    print("\n=== 境界判定: tier 間 cbet% 差 ===")
    avg_by_tier = {t: sum(vals)/len(vals)*100 for t, vals in tier_stats.items() if vals}
    for i, t in enumerate(tier_order[:-1]):
        t_next = tier_order[i+1]
        if t in avg_by_tier and t_next in avg_by_tier:
            diff = avg_by_tier[t] - avg_by_tier[t_next]
            marker = "**境界**" if abs(diff) >= 15 else "境界" if abs(diff) >= 8 else "弱境界"
            print(f"  {t:16} ({avg_by_tier[t]:5.1f}%) → {t_next:16} ({avg_by_tier[t_next]:5.1f}%) | 差={diff:>+5.1f}% [{marker}]")

    # Write report
    lines = []
    lines.append("# ハンドストレングス階層 境界分析 — 42 boards 実 GTO データ")
    lines.append("")
    lines.append("MATCHA 6 階層 (NUT_MADE/STRONG/TWO_PAIR/PAIR/MID_PAIR/AIR) 間で")
    lines.append("BTN cbet 行動が明確に変化するか検証。")
    lines.append("")
    lines.append("## MATCHA tier ごとの平均 cbet 頻度 (42 boards)")
    lines.append("")
    lines.append("| tier | avg_bet% | min% | max% | n_data |")
    lines.append("|------|---:|---:|---:|---:|")
    for t in tier_order:
        vals = tier_stats.get(t, [])
        if not vals:
            lines.append(f"| {t} | — | — | — | 0 |")
            continue
        avg = sum(vals)/len(vals)*100
        lines.append(f"| {t} | {avg:.1f}% | {min(vals)*100:.0f}% | {max(vals)*100:.0f}% | {len(vals)} |")
    lines.append("")

    lines.append("## tier 間境界 (cbet% 差)")
    lines.append("")
    lines.append("| 隣接 tier | tier A 平均 | tier B 平均 | 差 | 境界判定 |")
    lines.append("|-----------|---:|---:|---:|------|")
    for i, t in enumerate(tier_order[:-1]):
        t_next = tier_order[i+1]
        if t not in avg_by_tier or t_next not in avg_by_tier:
            continue
        diff = avg_by_tier[t] - avg_by_tier[t_next]
        marker = "🟢 明確" if abs(diff) >= 15 else "🟡 ある" if abs(diff) >= 8 else "🔴 弱い"
        lines.append(f"| {t} → {t_next} | {avg_by_tier[t]:.1f}% | {avg_by_tier[t_next]:.1f}% | {diff:+.1f}% | {marker} |")
    lines.append("")

    lines.append("## mv_cat 詳細")
    lines.append("")
    lines.append("| mv_cat (GTOW) | MATCHA tier | avg_bet% | min% | max% |")
    lines.append("|---|---|---:|---:|---:|")
    for c in cat_order:
        vals = cat_stats.get(c, [])
        if not vals:
            continue
        avg = sum(vals)/len(vals)*100
        tier = MATCHA_TIER.get(c, "?")
        lines.append(f"| {c} | {tier} | {avg:.1f}% | {min(vals)*100:.0f}% | {max(vals)*100:.0f}% |")
    lines.append("")

    lines.append("## 解釈")
    lines.append("")
    lines.append("各 tier の min/max 幅が広い = board 依存性が大きい (= 境界が board に依存)")
    lines.append("- 全 board で一貫して bet が多い tier = 単純に強い手 (ナッツ系)")
    lines.append("- 全 board で一貫して check が多い tier = エア")
    lines.append("- 中間 tier (PAIR, MID_PAIR) は board family で大きく変動 = 文脈依存")
    lines.append("")
    lines.append("### 境界の明確性まとめ")
    lines.append("")
    lines.append("- 🟢 明確な境界 (差 ≥15%): tier 区分の正当性 ◎")
    lines.append("- 🟡 ある境界 (差 8-15%): tier 区分 OK だが微妙な spots あり")
    lines.append("- 🔴 弱い境界 (差 <8%): 隣接 tier が実質同じ行動 → 統合検討")

    OUTPUT.write_text("\n".join(lines))
    print(f"\n📄 {OUTPUT}")


if __name__ == "__main__":
    main()
