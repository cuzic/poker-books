"""293K rows データから SPR 境界を逆算。

scenario_id × street × pot_type から SPR を推定し、SPR bin ごとの GTO 行動を集計。

SPR 推定ルール (Cash 100bb / MTT 100bb 基準、open=2.6bb):
- SRP flop: pot=6bb, stack=97bb → SPR 16
- SRP turn (after 50% cbet): pot=12bb, stack=94bb → SPR 7.8
- SRP turn (after 33% cbet): pot=8bb, stack=96bb → SPR 12
- SRP turn (after 75% cbet): pot=15bb, stack=92bb → SPR 6.1
- SRP river (after 2x 50% barrel): pot=28, stack=86 → SPR 3.1
- 3BP flop: pot=25, stack=85 → SPR 3.4
- 3BP turn (after 50%): pot=50, stack=70 → SPR 1.4
- 3BP river: pot ~100, stack ~50 → SPR 0.5
- 4BP flop: pot=55, stack=70 → SPR 1.3
- 4BP turn: pot ~100, stack ~50 → SPR 0.5
- 4BP river: pot ~150, stack ~25 → SPR 0.17

MTT depth 補正:
- MTT25: SRP flop SPR=4 (25bb stack, pot=6 → 4)、turn=1.6、river=0.5
- MTT50: SRP flop SPR=8
- MTT100: SRP flop SPR=16
- MTT200: SRP flop SPR=32

CR/donk defense (Phase 3, 5):
- flop CR の defense: SPR は cbet 後 / raise 後の状況依存。とりあえず 3-5 仮置き
"""
from __future__ import annotations
import csv
from collections import defaultdict
from pathlib import Path
import statistics
import re

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/SPR_BOUNDARIES_DERIVED.md"


def estimate_spr(scenario: str) -> tuple[float, str, str]:
    """scenario_id から (推定 SPR, pot_type, street) を返す。

    SPR は中央値の代表値。実際は手中で連続的だが、scenario の代表 spot で固定。
    """
    s = scenario.lower()

    # depth detection
    depth = 100
    m = re.search(r"mtt(\d+)", s)
    if m:
        depth = int(m.group(1))

    # street detection
    if "river" in s:
        street = "river"
    elif "turn" in s:
        street = "turn"
    elif "flop" in s:
        street = "flop"
    elif "_r1" in s or s == "r1_past":
        street = "preflop"
    else:
        # bvb, btn_sb, cr_def 等 → 個別判定
        street = "flop"  # default

    # pot type
    if "4bp" in s:
        pot_type = "4BP"
    elif "3bp" in s:
        pot_type = "3BP"
    elif "cr_def" in s or "donk_def" in s:
        pot_type = "DEF"  # defense vs aggression
    elif "open" in s:  # N_cash_co_open_river etc
        pot_type = "SRP"
    else:
        pot_type = "SRP"

    # depth multiplier: stack ratio
    depth_mult = depth / 100.0

    # base SPR by (pot_type, street)
    if pot_type == "SRP":
        if street == "flop":
            spr = 16.0 * depth_mult
        elif street == "turn":
            spr = 7.5 * depth_mult
        elif street == "river":
            spr = 3.0 * depth_mult
        else:
            spr = 16.0 * depth_mult
    elif pot_type == "3BP":
        if street == "flop":
            spr = 3.4
        elif street == "turn":
            spr = 1.4
        elif street == "river":
            spr = 0.55
        else:
            spr = 3.4
    elif pot_type == "4BP":
        if street == "flop":
            spr = 1.3
        elif street == "turn":
            spr = 0.5
        elif street == "river":
            spr = 0.17
        else:
            spr = 1.3
    elif pot_type == "DEF":
        # CR or donk → CR raised pot or donk raised
        if street == "flop":
            spr = 4.0
        elif street == "turn":
            spr = 2.0
        elif street == "river":
            spr = 0.8
        else:
            spr = 4.0
    else:
        spr = 8.0

    return spr, pot_type, street


def spr_bin(spr: float) -> str:
    if spr < 1:
        return "オールイン(<1)"
    elif spr < 3:
        return "ロー(1-3)"
    elif spr < 7:
        return "ミディアム(3-7)"
    elif spr < 15:
        return "ディープ(7-15)"
    else:
        return "ベリーディープ(>15)"


def main():
    print("Loading dataset...")
    rows_by_bin: dict[str, list[dict]] = defaultdict(list)
    rows_by_scenario: dict[str, list[dict]] = defaultdict(list)
    scenario_spr: dict[str, tuple[float, str, str]] = {}

    n_total = 0
    with CSV.open() as f:
        reader = csv.DictReader(f)
        for r in reader:
            n_total += 1
            scn = r["scenario_id"]
            if scn not in scenario_spr:
                scenario_spr[scn] = estimate_spr(scn)
            spr, pot, street = scenario_spr[scn]
            b = spr_bin(spr)
            rows_by_bin[b].append({
                "spr": spr, "scenario": scn, "pot": pot, "street": street,
                "ev_gap": float(r.get("ev_gap", 0) or 0),
                "best_action": r.get("best_action", ""),
                "fold": float(r.get("fold_freq", 0) or 0),
                "call": float(r.get("call_freq", 0) or 0),
                "raise": float(r.get("raise_freq", 0) or 0),
                "mv_cat": r.get("mv_cat", ""),
                "board_family": r.get("board_family", ""),
            })
            rows_by_scenario[scn].append(rows_by_bin[b][-1])

    print(f"Total rows: {n_total}")

    bin_order = ["オールイン(<1)", "ロー(1-3)", "ミディアム(3-7)", "ディープ(7-15)", "ベリーディープ(>15)"]

    print("\n=== SPR bin ごとの GTO 行動分布 ===")
    print(f"{'bin':24} {'n':>8} {'fold%':>7} {'call%':>7} {'raise%':>7} {'avg_ev_gap':>10}")
    bin_summary = {}
    for b in bin_order:
        rs = rows_by_bin.get(b, [])
        if not rs:
            continue
        n = len(rs)
        f = sum(r["fold"] for r in rs) / n * 100
        c = sum(r["call"] for r in rs) / n * 100
        rr = sum(r["raise"] for r in rs) / n * 100
        ga = sum(r["ev_gap"] for r in rs) / n
        bin_summary[b] = {"n": n, "fold": f, "call": c, "raise": rr, "avg_gap": ga}
        print(f"  {b:22} {n:>8} {f:>6.1f}% {c:>6.1f}% {rr:>6.1f}% {ga:>9.3f}")

    # AIR と NUT_MADE での bin 差: 同じハンドが SPR でどう行動変化するか
    print("\n=== mv_cat × SPR bin の cbet 頻度 (raise が IP の場合のみ) ===")
    cat_bin_raise: dict[tuple[str, str], list[float]] = defaultdict(list)
    for b, rs in rows_by_bin.items():
        for r in rs:
            cat_bin_raise[(r["mv_cat"], b)].append(r["raise"])

    cat_order = ["no_made_hand","ace_high","king_high","low_pair","third_pair","second_pair","underpair","top_pair","overpair","two_pair","trips","set","straight","flush","fullhouse"]
    hdr = f"{'mv_cat':18}"
    for b in bin_order:
        hdr += f" {b[:6]:>8}"
    print(hdr)
    for c in cat_order:
        row = f"  {c:16}"
        for b in bin_order:
            vals = cat_bin_raise.get((c, b), [])
            if vals:
                row += f"  {statistics.mean(vals)*100:>6.0f}%"
            else:
                row += f"  {'—':>7}"
        print(row)

    # pot_type ごとの scenario list (検証用)
    print("\n=== scenario → SPR 推定 一覧 ===")
    sorted_scn = sorted(scenario_spr.items(), key=lambda x: x[1][0])
    for scn, (spr, pot, street) in sorted_scn:
        n = len(rows_by_scenario.get(scn, []))
        print(f"  {scn:32} SPR={spr:>5.2f} ({pot} {street}) n={n}")

    # === Report ===
    lines = []
    lines.append("# SPR 境界の実測 — 293K rows データから逆算")
    lines.append("")
    lines.append("既存 unified dataset (Phase 1-6 統合、Cash/MTT/SRP/3BP/4BP/Defense 全網羅) ")
    lines.append("から SPR を scenario_id × street × pot_type で逆算し、")
    lines.append("SPR bin ごとの GTO 行動 (fold/call/raise) を集計。")
    lines.append("")
    lines.append("## SPR 推定ルール")
    lines.append("")
    lines.append("| pot_type | street | 推定 SPR | 計算根拠 |")
    lines.append("|----------|--------|---------:|---------|")
    lines.append("| SRP | flop  | 16  | pot 6, stack 97 (Cash100bb, open 2.6) |")
    lines.append("| SRP | turn  | 7.5 | pot ~12, stack ~94 (after 50% cbet) |")
    lines.append("| SRP | river | 3.0 | pot ~28, stack ~86 (after 2 barrels) |")
    lines.append("| 3BP | flop  | 3.4 | pot 25, stack 85 |")
    lines.append("| 3BP | turn  | 1.4 | pot 50, stack 70 |")
    lines.append("| 3BP | river | 0.55| pot ~100, stack ~50 |")
    lines.append("| 4BP | flop  | 1.3 | pot 55, stack 70 |")
    lines.append("| 4BP | turn  | 0.5 | pot ~100, stack ~50 |")
    lines.append("| 4BP | river | 0.17| pot ~150, stack ~25 |")
    lines.append("| DEF | flop  | 4.0 | CR/donk raised pot ~22 |")
    lines.append("")
    lines.append("MTT depth 補正: SPR × (depth/100)。MTT25 → 25%、MTT50 → 50%、MTT200 → 200%")
    lines.append("")
    lines.append("## SPR bin ごとの GTO 行動")
    lines.append("")
    lines.append("| SPR bin | n | fold% | call% | raise% | avg EV gap |")
    lines.append("|---------|--:|---:|---:|---:|---:|")
    for b in bin_order:
        if b not in bin_summary:
            continue
        s = bin_summary[b]
        lines.append(f"| {b} | {s['n']:,} | {s['fold']:.1f}% | {s['call']:.1f}% | {s['raise']:.1f}% | {s['avg_gap']:.3f} |")
    lines.append("")

    lines.append("## mv_cat × SPR bin の raise 頻度")
    lines.append("")
    header = "| mv_cat |" + "|".join(f" {b[:6]} " for b in bin_order) + "|"
    sep = "|---" * (len(bin_order)+1) + "|"
    lines.append(header)
    lines.append(sep)
    for c in cat_order:
        row = f"| {c} |"
        for b in bin_order:
            vals = cat_bin_raise.get((c, b), [])
            if vals:
                row += f" {statistics.mean(vals)*100:.0f}% |"
            else:
                row += " — |"
        lines.append(row)
    lines.append("")

    # Bin transition analysis
    lines.append("## SPR bin 間の行動変化 (隣接 bin 差)")
    lines.append("")
    lines.append("| SPR transition | fold 差 | call 差 | raise 差 | 解釈 |")
    lines.append("|---|---:|---:|---:|---|")
    available_bins = [b for b in bin_order if b in bin_summary]
    for i in range(len(available_bins)-1):
        b1, b2 = available_bins[i], available_bins[i+1]
        s1, s2 = bin_summary[b1], bin_summary[b2]
        df = s2["fold"] - s1["fold"]
        dc = s2["call"] - s1["call"]
        dr = s2["raise"] - s1["raise"]
        notes = []
        if abs(df) > 5: notes.append(f"fold {'増' if df>0 else '減'}")
        if abs(dc) > 5: notes.append(f"call {'増' if dc>0 else '減'}")
        if abs(dr) > 5: notes.append(f"raise {'増' if dr>0 else '減'}")
        interpret = "明確な行動変化" if notes else "連続的"
        lines.append(f"| {b1} → {b2} | {df:+.1f}% | {dc:+.1f}% | {dr:+.1f}% | {', '.join(notes) or interpret} |")
    lines.append("")

    lines.append("## scenario × 推定 SPR")
    lines.append("")
    lines.append("| scenario_id | pot | street | 推定 SPR | n rows |")
    lines.append("|---|---|---|---:|---:|")
    for scn, (spr, pot, street) in sorted_scn:
        n = len(rows_by_scenario.get(scn, []))
        lines.append(f"| {scn} | {pot} | {street} | {spr:.2f} | {n:,} |")
    lines.append("")

    lines.append("## MATCHA SPR 4 段階との対応")
    lines.append("")
    lines.append("| MATCHA tier | SPR 範囲 | データ上の検証 |")
    lines.append("|-------------|---------|---------------|")
    lines.append("| オールイン | <1 | 4BP turn/river, 3BP river — fold/call 中心 (raise が allin か) |")
    lines.append("| ロー | 1-3 | 4BP flop, 3BP turn — set/2pair 強気、TP pot-control |")
    lines.append("| ミディアム | 3-7 | 3BP flop, SRP river, DEF — value/bluff 分離 |")
    lines.append("| ディープ | >7 | SRP flop/turn — protect range, 多 sizing |")
    lines.append("")
    lines.append("実測の bin 行動差を見て、4 段階の境界が data に裏付けされるか検証。")
    lines.append("もし bin 間で行動差が小さい (<5%) なら統合検討、大きい (>15%) なら境界明確。")

    OUT.write_text("\n".join(lines))
    print(f"\n📄 {OUT}")


if __name__ == "__main__":
    main()
