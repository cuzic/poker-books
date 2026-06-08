"""probe data から MATCHA 板分類境界を実測導出。

現状の MATCHA は heuristic 分類 (dynamic→POLAR 等):
- POLAR: dynamic, dynamic_2tone, monotone
- MERGED: dry_high, low_dry, paired
- CONDENSED: other

これを probe data の実 GTO 行動から検証:
1. 各 board の BTN cbet 振る舞い (freq, size, polarization) を抽出
2. boards を実 GTO 行動でクラスタリング
3. 現状 MATCHA 分類との一致 / 不一致を明示
4. 「実 GTO データから定義した境界」を提案

入力: probe_drill_btn_cbet/*.json (21 boards)
出力: knowledges/gto_wizard_study/BOARD_BOUNDARIES_EMPIRICAL.md
"""
from __future__ import annotations
import json, re
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parents[2]
GTOW = REPO_ROOT / "knowledges/gto_wizard_study"
BTN_DIR = GTOW / "probe_drill_btn_cbet"
BOUNDARY_DIR = GTOW / "probe_drill"  # boundary 系も含む
OUTPUT = GTOW / "BOARD_BOUNDARIES_EMPIRICAL.md"


def board_features(flop: str) -> dict:
    """flop 文字列 ('Ks7d2c') → 構造的特徴。"""
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
    is_dynamic = gap_top <= 2 and gap_bot <= 2  # 連続性高い
    ace_high = rvals[0] == 12
    king_high = rvals[0] == 11
    return {
        "high": "23456789TJQKA"[rvals[0]],
        "mid": "23456789TJQKA"[rvals[1]],
        "low": "23456789TJQKA"[rvals[2]],
        "gap_top": gap_top, "gap_bot": gap_bot, "max_gap": max_gap,
        "paired": paired, "monotone": monotone, "twotone": twotone,
        "is_dynamic": is_dynamic,
        "ace_high": ace_high, "king_high": king_high,
    }


def matcha_static_classification(feat: dict) -> str:
    """現行 MATCHA の heuristic 分類。"""
    if feat["monotone"]:
        return "POLAR (monotone)"
    if feat["is_dynamic"] and feat["twotone"]:
        return "POLAR (dynamic_2tone)"
    if feat["is_dynamic"]:
        return "POLAR (dynamic)"
    if feat["paired"]:
        return "MERGED (paired)"
    if feat["high"] in "KQ" and feat["mid"] < "8":
        return "MERGED (dry_high)"
    if feat["high"] < "T":
        return "MERGED (low_dry)"
    if feat["ace_high"]:
        return "MERGED (ace_high)" if feat["max_gap"] >= 3 else "POLAR (dynamic)"
    return "CONDENSED"


def analyze_probe(p_file: Path) -> dict:
    """1 probe → 行動メトリクス。"""
    saved = json.loads(p_file.read_text())
    data = saved.get("data", {})
    flop = (saved.get("flop") or "").lower()
    actions = data.get("action_solutions", [])

    cbet_freq = 0.0
    bet_actions = []
    check_freq = 0.0
    for a in actions:
        t = a["action"]["type"]
        f = a.get("total_frequency", 0)
        if t in ("BET", "RAISE"):
            cbet_freq += f
            bet_actions.append({
                "betsize": a["action"]["betsize"],
                "freq": f,
                "betsize_by_pot": a["action"].get("betsize_by_pot"),
            })
        elif t == "CHECK":
            check_freq += f

    # dominant sizing
    bet_actions.sort(key=lambda x: -x["freq"])
    dom_size = bet_actions[0] if bet_actions else None

    # polarization: range の bet と check の差
    polarization = abs(cbet_freq - check_freq)

    # number of distinct sizings used
    n_sizings = len(bet_actions)

    return {
        "flop": flop,
        "cbet_freq": cbet_freq,
        "check_freq": check_freq,
        "polarization": polarization,
        "n_sizings": n_sizings,
        "dom_size_bb": float(dom_size["betsize"]) if dom_size else 0,
        "dom_size_freq": dom_size["freq"] if dom_size else 0,
        "dom_size_pct_pot": dom_size["betsize_by_pot"] if dom_size else None,
        "bet_sizes": bet_actions,
    }


def main():
    if not BTN_DIR.exists():
        print(f"✗ {BTN_DIR} missing"); return

    probes = sorted(BTN_DIR.glob("btn_cbet_*.json"))
    print(f"Loaded {len(probes)} BTN cbet probes")

    rows = []
    for p in probes:
        m = analyze_probe(p)
        feat = board_features(m["flop"])
        static_cls = matcha_static_classification(feat)
        rows.append({**m, "feat": feat, "matcha_static": static_cls})

    # Sort by cbet_freq for clustering
    rows.sort(key=lambda r: -r["cbet_freq"])

    print("\n=== Per-board behavior ===")
    print(f"{'flop':12} {'static MATCHA':30} cbet%   chk%   polariz  ndoml sizing")
    for r in rows:
        print(f"  {r['flop']:10}  {r['matcha_static']:30} {r['cbet_freq']*100:5.1f}%  {r['check_freq']*100:5.1f}%  {r['polarization']:.2f}  {r['n_sizings']}    {r['dom_size_bb']:4.1f}bb ({r['dom_size_freq']*100:.0f}%)")

    # Empirical clustering: by cbet pattern
    # Cluster heuristic:
    # - cbet_freq < 35% + 1 size dominant + small size → POLAR-style (BTN ranges thin、選択的に打つ)
    # - cbet_freq > 50% → BTN attacks → MERGED-style (range が混在)
    # - cbet_freq 35-50% + 2+ sizings → CONDENSED (mid range、polar split)
    print("\n=== Empirical clustering ===")
    clusters = {"polar": [], "merged": [], "condensed": []}
    for r in rows:
        cbet = r["cbet_freq"]
        n_size = r["n_sizings"]
        if cbet < 0.40:
            clusters["polar"].append(r)
        elif cbet > 0.55:
            clusters["merged"].append(r)
        else:
            clusters["condensed"].append(r)
    for name, group in clusters.items():
        print(f"  {name} (empirical): {len(group)} boards")
        for r in group:
            print(f"    {r['flop']:10}  cbet={r['cbet_freq']*100:.0f}%  static={r['matcha_static']}")

    # Write markdown report
    lines = []
    lines.append("# Board 分類境界の実測導出 (probe data 21 boards)")
    lines.append("")
    lines.append("MATCHA Framework の現行 heuristic 分類 (POLAR/MERGED/CONDENSED) を")
    lines.append("GTO Wizard probe data の実行動から検証。")
    lines.append("")
    lines.append("## 各 board の BTN cbet 行動データ")
    lines.append("")
    lines.append("| flop | static (heuristic) | cbet% | check% | polariz | sizings | dom_size |")
    lines.append("|------|-------------------|------:|------:|--------:|--------:|---------|")
    for r in rows:
        lines.append(f"| `{r['flop']}` | {r['matcha_static']} | {r['cbet_freq']*100:.0f}% | {r['check_freq']*100:.0f}% | {r['polarization']:.2f} | {r['n_sizings']} | {r['dom_size_bb']:.1f}bb ({r['dom_size_freq']*100:.0f}%) |")
    lines.append("")

    lines.append("## 実測導出境界 (案)")
    lines.append("")
    lines.append("BTN の cbet 頻度を主軸に 3 クラスター:")
    lines.append("")
    lines.append("### POLAR-style (cbet_freq < 40%, 選択的攻撃)")
    lines.append("BTN は polar range で attack、check 過半。")
    lines.append("")
    lines.append("| flop | cbet% | static MATCHA | 一致? |")
    lines.append("|------|------:|---------------|------|")
    for r in clusters["polar"]:
        match = "POLAR" in r["matcha_static"]
        lines.append(f"| `{r['flop']}` | {r['cbet_freq']*100:.0f}% | {r['matcha_static']} | {'✓' if match else '⚠'} |")
    lines.append("")

    lines.append("### MERGED-style (cbet_freq > 55%, 連発攻撃)")
    lines.append("BTN range advantage 強、wide cbet。")
    lines.append("")
    lines.append("| flop | cbet% | static MATCHA | 一致? |")
    lines.append("|------|------:|---------------|------|")
    for r in clusters["merged"]:
        match = "MERGED" in r["matcha_static"]
        lines.append(f"| `{r['flop']}` | {r['cbet_freq']*100:.0f}% | {r['matcha_static']} | {'✓' if match else '⚠'} |")
    lines.append("")

    lines.append("### CONDENSED-style (cbet_freq 40-55%, 混合)")
    lines.append("")
    lines.append("| flop | cbet% | static MATCHA | 一致? |")
    lines.append("|------|------:|---------------|------|")
    for r in clusters["condensed"]:
        match = "CONDENSED" in r["matcha_static"] or "MERGED" in r["matcha_static"]
        lines.append(f"| `{r['flop']}` | {r['cbet_freq']*100:.0f}% | {r['matcha_static']} | {'✓' if match else '?'} |")
    lines.append("")

    lines.append("## 提案: 実 GTO 行動に基づくロジカル分類")
    lines.append("")
    lines.append("【現行 MATCHA (heuristic)】")
    lines.append("- POLAR = {dynamic, dynamic_2tone, monotone}")
    lines.append("- MERGED = {dry_high, low_dry, paired}")
    lines.append("- CONDENSED = その他")
    lines.append("")
    lines.append("【実測導出案 (cbet 頻度ベース)】")
    lines.append("- POLAR: BTN cbet < 40% (board が draws 多くて attack 抑制)")
    lines.append("- CONDENSED: BTN cbet 40-55% (board が mid-heavy で混合)")
    lines.append("- MERGED: BTN cbet > 55% (board が dry でwide attack)")
    lines.append("")
    lines.append("【データから判明した不一致】")
    matches = 0
    mismatches = []
    for r in rows:
        cbet = r["cbet_freq"]
        emp = "polar" if cbet < 0.40 else "merged" if cbet > 0.55 else "condensed"
        static = ("polar" if "POLAR" in r["matcha_static"]
                  else "merged" if "MERGED" in r["matcha_static"]
                  else "condensed")
        if emp == static:
            matches += 1
        else:
            mismatches.append((r["flop"], static, emp, cbet))
    lines.append(f"- 一致: {matches}/{len(rows)}")
    lines.append(f"- 不一致: {len(mismatches)}")
    if mismatches:
        lines.append("")
        lines.append("| flop | static (現行) | empirical (実測) | cbet% |")
        lines.append("|------|-------------|------------------|------:|")
        for flop, s, e, c in mismatches:
            lines.append(f"| `{flop}` | {s} | {e} | {c*100:.0f}% |")
    lines.append("")
    lines.append("## 次のステップ")
    lines.append("")
    lines.append("1. drill cards の Hand Strength tier × board family 振る舞いも同様に実測導出")
    lines.append("2. SPR 境界 (1/3/7) の実測検証 (現状: 計算ベース、行動の不連続性は未確認)")
    lines.append("3. Bet Sizing 4 段階 → 実 GTO 2 段階 (small ~30% / big ~90%) との整合")

    OUTPUT.write_text("\n".join(lines))
    print(f"\n📄 {OUTPUT}")


if __name__ == "__main__":
    main()
