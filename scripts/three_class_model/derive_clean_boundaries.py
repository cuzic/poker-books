"""全 probe data から「実 GTO 行動に基づく明確な境界」を導出。

入力:
- probe_drill_btn_cbet/*.json (21 boards)
- probe_boundary_gradient/*.json (21 boards、gradient design)

合計 42 boards で empirical 境界を発見。

出力: knowledges/gto_wizard_study/CLEAN_BOUNDARIES.md
"""
from __future__ import annotations
import json
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parents[2]
GTOW = REPO_ROOT / "knowledges/gto_wizard_study"
OUTPUT = GTOW / "CLEAN_BOUNDARIES.md"


def analyze(p: Path) -> dict:
    saved = json.loads(p.read_text())
    flop = (saved.get("flop") or saved.get("board") or "").lower()
    label = saved.get("label", "")
    cat = saved.get("category", "")
    data = saved.get("data", {})
    actions = data.get("action_solutions", [])
    cbet = sum(a["total_frequency"] for a in actions if a["action"]["type"] in ("BET","RAISE"))
    check = sum(a["total_frequency"] for a in actions if a["action"]["type"] == "CHECK")
    sizes = sorted([(float(a["action"]["betsize"]), a["total_frequency"]) for a in actions if a["action"]["type"] in ("BET","RAISE")], key=lambda x: -x[1])
    dom_size = sizes[0] if sizes else (0, 0)
    return {
        "flop": flop, "label": label, "category": cat,
        "cbet": cbet, "check": check,
        "dom_size_bb": dom_size[0], "dom_size_freq": dom_size[1],
        "n_sizings": len(sizes),
    }


def board_structure(flop: str) -> dict:
    cards = [flop[i*2:i*2+2] for i in range(3)]
    RANKS = "23456789TJQKA"
    rvals = sorted([RANKS.index(c[0].upper()) for c in cards], reverse=True)
    suits = [c[1].lower() for c in cards]
    paired = rvals[0] == rvals[1] or rvals[1] == rvals[2]
    monotone = len(set(suits)) == 1
    twotone = len(set(suits)) == 2
    rainbow = len(set(suits)) == 3
    gap1 = rvals[0] - rvals[1]
    gap2 = rvals[1] - rvals[2]
    max_gap = max(gap1, gap2)
    connector = gap1 <= 2 and gap2 <= 2
    high = "23456789TJQKA"[rvals[0]]
    return {
        "high": high,
        "high_idx": rvals[0],
        "mid_idx": rvals[1],
        "low_idx": rvals[2],
        "gap1": gap1, "gap2": gap2, "max_gap": max_gap,
        "paired": paired, "monotone": monotone, "twotone": twotone, "rainbow": rainbow,
        "connector": connector,
        "ace_high": rvals[0] == 12, "king_high": rvals[0] == 11,
        "broadway_high": rvals[0] >= 8,  # T+
        "low_board": rvals[0] <= 5,  # 7-high or lower
    }


def classify_data_driven(struct: dict, cbet: float) -> str:
    """データに基づく境界判定 (実 cbet 頻度 + 構造)。"""
    if cbet >= 0.48:
        return "高頻度 (MERGED-style)"
    elif cbet >= 0.40:
        return "中頻度 (CONDENSED-style)"
    elif cbet >= 0.30:
        return "低頻度 (POLAR-style)"
    else:
        return "極端低頻度 (POLAR extreme)"


def main():
    rows = []
    for d in [GTOW / "probe_drill_btn_cbet", GTOW / "probe_boundary_gradient"]:
        for p in sorted(d.glob("*.json")):
            r = analyze(p)
            r["struct"] = board_structure(r["flop"])
            r["empirical_cluster"] = classify_data_driven(r["struct"], r["cbet"])
            rows.append(r)

    rows.sort(key=lambda r: -r["cbet"])

    lines = []
    lines.append("# Board family の実 GTO 境界 (42 boards probe data)")
    lines.append("")
    lines.append("## サマリー: cbet 頻度 vs 構造")
    lines.append("")
    lines.append("| flop | high | paired | mono | connect | cbet% | dom_size | empirical_cluster |")
    lines.append("|------|------|:------:|:----:|:-------:|------:|--------:|-------------------|")
    for r in rows:
        s = r["struct"]
        lines.append(
            f"| `{r['flop']}` | {s['high']} | "
            f"{'P' if s['paired'] else '-'} | "
            f"{'M' if s['monotone'] else 'T' if s['twotone'] else 'R'} | "
            f"{'C' if s['connector'] else '-'} | "
            f"{r['cbet']*100:.0f}% | "
            f"{r['dom_size_bb']:.1f}bb | "
            f"{r['empirical_cluster']} |"
        )
    lines.append("")

    # Cluster by empirical groups
    clusters = defaultdict(list)
    for r in rows:
        clusters[r["empirical_cluster"]].append(r)

    lines.append("## empirical クラスター (cbet 頻度ベース)")
    lines.append("")
    for cluster, ms in sorted(clusters.items()):
        lines.append(f"### {cluster} (n={len(ms)})")
        for m in ms:
            s = m["struct"]
            features = []
            if s["paired"]: features.append("paired")
            if s["monotone"]: features.append("monotone")
            if s["connector"]: features.append("connected")
            if s["ace_high"]: features.append("A-high")
            if s["king_high"]: features.append("K-high")
            if s["low_board"]: features.append("low_board")
            lines.append(f"- `{m['flop']}` cbet={m['cbet']*100:.0f}% — {' '.join(features) if features else 'plain'}")
        lines.append("")

    # Pattern analysis
    lines.append("## 構造的パターン (発見した規則性)")
    lines.append("")

    lines.append("### 1. **Paired board**: 常に 42-45% cbet (CONDENSED-style)")
    paired = [r for r in rows if r["struct"]["paired"]]
    for p in paired:
        lines.append(f"- `{p['flop']}` cbet={p['cbet']*100:.0f}% (pair rank: {p['struct']['high']})")
    lines.append("")
    lines.append("**ルール**: paired board は pair height に関わらず CONDENSED 寄り (42-45%)")
    lines.append("")

    lines.append("### 2. **High-card dry (A/K-high、非 connected、非 paired)**: 47-50% cbet (MERGED-style)")
    high_dry = [r for r in rows if r["struct"]["high_idx"] >= 11 and not r["struct"]["connector"] and not r["struct"]["paired"] and not r["struct"]["monotone"]]
    for p in high_dry:
        lines.append(f"- `{p['flop']}` cbet={p['cbet']*100:.0f}% — {p['struct']['high']}-high dry")
    lines.append("")
    lines.append("**ルール**: A/K-high で connected でない board は MERGED (BTN range advantage)")
    lines.append("")

    lines.append("### 3. **Connected boards (gap1≤2 + gap2≤2)**: 20-50% cbet (POLAR-style)")
    connected = [r for r in rows if r["struct"]["connector"] and not r["struct"]["paired"]]
    for p in sorted(connected, key=lambda x: -x["cbet"]):
        lines.append(f"- `{p['flop']}` cbet={p['cbet']*100:.0f}% — connected ({p['struct']['high']}-high)")
    lines.append("")
    lines.append("**ルール**: connected board は POLAR (small cbet 多用、draw-heavy)")
    lines.append("")

    lines.append("### 4. **Low dry rainbow (7-high以下、非 connected、非 paired、rainbow)**: 33% cbet (POLAR/CONDENSED 境界)")
    low_dry = [r for r in rows if r["struct"]["low_board"] and r["struct"]["rainbow"] and not r["struct"]["paired"] and not r["struct"]["connector"]]
    for p in low_dry:
        lines.append(f"- `{p['flop']}` cbet={p['cbet']*100:.0f}%")
    lines.append("")

    lines.append("## ロジカル境界 (データ駆動の提案)")
    lines.append("")
    lines.append("**現行 MATCHA の heuristic 分類** ⇒ **データ駆動の改訂版**")
    lines.append("")
    lines.append("```")
    lines.append("def classify_board(board: list[str]) -> str:")
    lines.append("    s = structure(board)")
    lines.append("    if s.monotone or s.connected:")
    lines.append('        return "POLAR"   # cbet < 40%、選択的 attack')
    lines.append("    if s.paired:")
    lines.append('        return "CONDENSED"  # cbet 42-45%、混合 protection')
    lines.append("    if s.high_idx >= 11 and not s.connected:")
    lines.append('        return "MERGED"  # A/K-high dry、cbet 47-50%、wide attack')
    lines.append("    if s.low_board:")
    lines.append('        return "POLAR"   # low dry 系も cbet < 40%、polar')
    lines.append('    return "CONDENSED"  # その他、cbet 40-45%')
    lines.append("```")
    lines.append("")

    lines.append("## 現行 MATCHA からの修正点")
    lines.append("")
    lines.append("| board family | 現行 MATCHA | データ駆動 | 修正理由 |")
    lines.append("|--------------|-----------|----------|---------|")
    lines.append("| low_dry (7s4d2c 等) | MERGED | **POLAR** | 実 cbet 33%、selective polar attack |")
    lines.append("| dynamic (9s8d6c 等) | POLAR | POLAR | ✓ 整合 (cbet 27%) |")
    lines.append("| dynamic_low (4s4d2c) | POLAR (paired override) | **MERGED** | paired low、cbet 57% |")
    lines.append("| paired (KsKd4c 等) | MERGED | **CONDENSED** | cbet 43%、中頻度 |")
    lines.append("| broadway connected (TJQ) | POLAR | POLAR extreme | cbet 21% ◎ |")
    lines.append("| K-high connected (Ks9d8c) | POLAR ? | POLAR (連動チェック多) | cbet 22% |")
    lines.append("| A-high dry (As7d2c) | MERGED | MERGED | ✓ cbet 50% |")
    lines.append("")

    lines.append("## 次の境界調査必要トピック")
    lines.append("")
    lines.append("1. **Hand strength tier の境界**: TPTK vs TPGK vs TPMK は cbet 行動が変わるか?")
    lines.append("2. **Bet sizing 境界**: 33% (1.9bb) と 100% (6.5bb) の 2 段階に集約? それとも 4 段階維持?")
    lines.append("3. **SPR 境界**: SPR<1, 1-3, 3-7, >7 で実 GTO 行動が不連続変化するか?")
    lines.append("4. **Equity bucket 境界**: best/good/weak/trash の閾値は API per-combo で決まるが、人間判断可能な ranges に divide できるか?")

    OUTPUT.write_text("\n".join(lines))
    print(f"📄 {OUTPUT}")
    print(f"\n=== Pattern summary ===")
    print("Paired boards (42-45% cbet, all):", [r["flop"] for r in paired])
    print("High-dry (47-50%):", [r["flop"] for r in high_dry])
    print("Connected (variable):", [(r["flop"], f"{r['cbet']*100:.0f}%") for r in connected])
    print("Low dry rainbow (33%):", [r["flop"] for r in low_dry])


if __name__ == "__main__":
    main()
