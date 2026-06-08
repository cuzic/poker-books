"""SPR gradient probe の 5 spots を hand_category 別に分析。

同 board (Ks7d2c) で SPR 変化:
- depth_50_flop (SPR ~8): Cash 50bb SRP
- depth_100_flop (SPR ~16): Cash 100bb SRP
- 3bp_flop (SPR ~3.4): 3BP
- 4bp_flop (SPR ~1.3): 4BP

→ 同じ K72 で SPR だけが変わるとき、tier ごとの cbet 行動はどう変わるか
"""
from __future__ import annotations
import json
from pathlib import Path
from collections import defaultdict

DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_spr_gradient")
OUT = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/SPR_GRADIENT_ANALYSIS.md")

MATCHA_TIER = {
    "fullhouse":"ナッツメイド","quads":"ナッツメイド","straight_flush":"ナッツメイド",
    "set":"ストロング","trips":"ストロング","straight":"ストロング","flush":"ストロング",
    "two_pair":"ツーペア",
    "top_pair":"トップペア以上","overpair":"トップペア以上",
    "second_pair":"ミドルペア","third_pair":"ミドルペア","underpair":"ミドルペア","low_pair":"ミドルペア",
    "no_made_hand":"エア","king_high":"エア","ace_high":"エア",
}

SPR_LABELS = {
    "depth_50_flop": ("SPR 8 (Cash50)", 8.0),
    "depth_100_flop": ("SPR 16 (Cash100)", 16.0),
    "3bp_flop": ("SPR 3.4 (3BP)", 3.4),
    "4bp_flop": ("SPR 1.3 (4BP)", 1.3),
}


def analyze(f: Path) -> dict:
    saved = json.loads(f.read_text())
    label = saved.get("label", "?")
    data = saved.get("data", {})
    actions = data.get("action_solutions", [])

    # Per-tier bet/check ratio
    tier_bet: dict[str, float] = defaultdict(float)
    tier_check: dict[str, float] = defaultdict(float)
    sizes_used = set()
    for a in actions:
        t = a["action"]["type"]
        sz = a["action"].get("betsize", 0)
        try:
            sz_f = float(sz)
        except (TypeError, ValueError):
            sz_f = 0.0
        if t in ("BET","RAISE") and sz_f > 0:
            sizes_used.add(sz_f)
        is_bet = t in ("BET","RAISE")
        is_check = t == "CHECK"
        for cat in a.get("hand_categories", []):
            name = cat["name"]
            freq = cat.get("total_frequency", 0)
            if is_bet:
                tier_bet[MATCHA_TIER.get(name, "?")] += freq
            elif is_check:
                tier_check[MATCHA_TIER.get(name, "?")] += freq

    tier_ratio = {}
    for t in tier_bet.keys() | tier_check.keys():
        total = tier_bet[t] + tier_check[t]
        tier_ratio[t] = (tier_bet[t] / total) if total > 0 else 0.0

    bet_total = sum(a["total_frequency"] for a in actions if a["action"]["type"] in ("BET","RAISE"))
    return {
        "label": label,
        "sizes": sorted(sizes_used),
        "total_bet": bet_total,
        "tier_ratio": tier_ratio,
    }


def main():
    results = {}
    for f in sorted(DIR.glob("*.json")):
        r = analyze(f)
        key = f.stem.replace("spr_", "")
        results[key] = r

    # SPR 順に並べる
    spr_order = ["4bp_flop", "3bp_flop", "depth_50_flop", "depth_100_flop"]
    tier_order = ["ナッツメイド","ストロング","ツーペア","トップペア以上","ミドルペア","エア"]

    lines = []
    lines.append("# SPR gradient 分析 — 同 board (Ks7d2c) × SPR 変化")
    lines.append("")
    lines.append("BTN 攻撃 IP 側、SRP/3BP/4BP × Cash 50/100bb で同 K72 rainbow flop を probe。")
    lines.append("SPR が連続的に変化したとき、tier ごとの cbet 行動がどう変わるか。")
    lines.append("")
    lines.append("## 概要 (SPR 昇順)")
    lines.append("")
    lines.append("| spot | SPR | sizing | 総 cbet% |")
    lines.append("|---|---:|---|---:|")
    for k in spr_order:
        if k not in results: continue
        spr = SPR_LABELS.get(k, ("?", 0))[1]
        r = results[k]
        sizes = ", ".join(f"{s}bb" for s in r["sizes"])
        lines.append(f"| {k} | {spr} | {sizes} | {r['total_bet']*100:.1f}% |")
    lines.append("")

    lines.append("## tier × SPR の cbet 頻度")
    lines.append("")
    hdr = "| tier |"
    sep = "|---|"
    for k in spr_order:
        if k not in results: continue
        spr = SPR_LABELS.get(k, ("?", 0))[1]
        hdr += f" SPR {spr} |"
        sep += "---:|"
    lines.append(hdr)
    lines.append(sep)
    for t in tier_order:
        row = f"| {t} |"
        for k in spr_order:
            if k not in results: continue
            v = results[k]["tier_ratio"].get(t)
            if v is None:
                row += " — |"
            else:
                row += f" {v*100:.0f}% |"
        lines.append(row)
    lines.append("")

    lines.append("## 観察")
    lines.append("")

    # Per-tier SPR sensitivity
    print("\n=== tier × SPR cbet 頻度 ===")
    print(f"{'tier':18} {'SPR1.3':>8} {'SPR3.4':>8} {'SPR8':>8} {'SPR16':>8}  {'gap(low-mid)':>12} {'gap(mid-high)':>13}")
    obs_lines = []
    for t in tier_order:
        vals = []
        for k in spr_order:
            if k not in results: continue
            v = results[k]["tier_ratio"].get(t, 0) * 100
            vals.append(v)
        if len(vals) < 4:
            continue
        # SPR 1.3 -> 3.4 -> 8 -> 16
        gap_low = vals[1] - vals[0]  # 3.4 - 1.3 (ロー→ミディアム)
        gap_high = vals[3] - vals[2]  # 16 - 8 (ミディアム→ディープ)
        gap_mid = vals[2] - vals[1]  # 8 - 3.4 (ミディアム内)
        marker = ""
        if abs(gap_low) > 20: marker = "★ SPR1→3 で急変"
        elif abs(gap_mid) > 20: marker = "★ SPR3→8 で急変"
        elif abs(gap_high) > 20: marker = "★ SPR8→16 で急変"
        print(f"  {t:16} {vals[0]:>7.0f}% {vals[1]:>7.0f}% {vals[2]:>7.0f}% {vals[3]:>7.0f}% | {gap_low:+5.0f}pp {gap_mid:+5.0f}pp {gap_high:+5.0f}pp {marker}")
        obs_lines.append(f"- **{t}**: SPR1.3={vals[0]:.0f}% → SPR3.4={vals[1]:.0f}% → SPR8={vals[2]:.0f}% → SPR16={vals[3]:.0f}% ({marker if marker else '安定'})")

    lines.append("### tier ごとの SPR sensitivity")
    lines.append("")
    for ol in obs_lines:
        lines.append(ol)
    lines.append("")

    lines.append("### MATCHA SPR 4 段階との対応")
    lines.append("")
    lines.append("- **オールイン (<1)**: 本データになし (4BP turn / 3BP river 等が該当)")
    lines.append("- **ロー (1-3)**: SPR 1.3 (4BP flop) 側 — value heavy, jam-or-fold")
    lines.append("- **ミディアム (3-7)**: SPR 3.4 (3BP flop) 側 — value/bluff 分離")
    lines.append("- **ディープ (>7)**: SPR 8/16 (SRP) 側 — protect range, 多様な sizing")
    lines.append("")
    lines.append("実 GTO で tier ごとに SPR の sensitivity が異なる:")
    lines.append("- ナッツメイド/ストロング: SPR↑で常に高頻度ベット (value 一貫)")
    lines.append("- ツーペア/トップペア: SPR↓ (3BP/4BP) で頻度↑ (jam 価値)、SPR↑ (SRP) で控えめ")
    lines.append("- ミドルペア/エア: SPR↑ で頻度↑ (multi-street bluff 可、ブラフ余地)")

    OUT.write_text("\n".join(lines))
    print(f"\n📄 {OUT}")


if __name__ == "__main__":
    main()
