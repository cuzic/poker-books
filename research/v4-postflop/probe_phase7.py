#!/usr/bin/env python3
"""probe_phase7.py — UDG v3 のための board variance / turn card / blocker 調査

2 sections:
  Section A (即実行可能、API 不要): 既存データ再分析
    A1: MTT200 HIGH SPR の挙動分析
    A2: R1_past (BTN IP river allin) の huge_loss 6.3 BB 原因分析
    A3: Per-combo blocker effect 分析
    A4: 4BP MERGED tier 内の board-specific variance 分析

  Section B (要 API、~72 calls): 新規 fetch
    B1: 4BP flop board variance probe (18 boards × 2 calls = 36 calls)
        EXTENDED_BOARDS_18 (phase2 既存) を 4BP context で全部 fetch
    B2: Turn card category sensitivity (3 flops × 4 turn cards × 3 calls = 36 calls)
        同 flop で paired/overcard/brick/draw-complete turn の比較

実行方法:
  python3 probe_phase7.py --section A          # 既存データ分析のみ (即実行可)
  python3 probe_phase7.py --section B          # API fetch (要 token)
  python3 probe_phase7.py --section all        # 両方

出力:
  probe_phase7_section_a.md / section_b.md
  findings/probe_phase7/*.json (Section B 生 API response)
  probe_phase7_rows.csv / stats.json
"""
import argparse
import csv
import json
import os
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent.parent / "scripts" / "three_class_model"))

for line in (ROOT / ".env").read_text().splitlines() if (ROOT / ".env").exists() else []:
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

import gto_api  # noqa: E402

OUT_DIR = ROOT / "findings" / "probe_phase7"
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_A = ROOT / "probe_phase7_section_a.md"
REPORT_B = ROOT / "probe_phase7_section_b.md"
ROWS_CSV = ROOT / "probe_phase7_rows.csv"
LOG = ROOT / "probe_phase7_log.jsonl"

DATASET_V2 = ROOT.parent.parent / "scripts" / "three_class_model" / "dataset_unified_v2.csv"


# ════════════════════════════ Section A: 既存データ分析 (API 不要) ═══════════════════════════

def section_a_analysis():
    """既存 dataset_unified_v2.csv を再分析、UDG v3 の改善 axis を特定."""
    import pandas as pd

    print("=== Section A: 既存データ分析 (API 不要) ===\n", flush=True)
    print(f"Loading {DATASET_V2}...")
    df = pd.read_csv(DATASET_V2, low_memory=False)
    print(f"  {len(df):,} rows\n")

    # Apply UDG v2 to all rows
    from udg_v2 import udg_defense_v2
    print("Applying UDG v2 to all rows (this may take a minute)...")
    df["udg_action"] = df.apply(udg_defense_v2, axis=1)
    df["udg_correct"] = (df["udg_action"] == df["best_action"])
    df["udg_loss"] = df.apply(
        lambda r: r["best_ev"] - {"FOLD": r["ev_fold"], "CALL": r["ev_call"], "RAISE": r["ev_raise"]}.get(r["udg_action"], r["best_ev"] - r["ev_gap"])
        if pd.notna({"FOLD": r["ev_fold"], "CALL": r["ev_call"], "RAISE": r["ev_raise"]}.get(r["udg_action"]))
        else r["ev_gap"],
        axis=1
    )

    sections = []

    # ── A1: MTT200 HIGH SPR 分析 ────────────────────
    print("\n--- A1: MTT200 HIGH SPR 分析 ---")
    a1 = analyze_mtt200(df)
    sections.append(("A1: MTT200 HIGH SPR 分析", a1))

    # ── A2: R1_past IP defender 分析 ──────────────
    print("\n--- A2: R1_past IP defender 分析 ---")
    a2 = analyze_r1_ip(df)
    sections.append(("A2: R1 (IP river allin) 分析", a2))

    # ── A3: Blocker effect 分析 ────────────────────
    print("\n--- A3: Blocker effect 分析 ---")
    a3 = analyze_blocker(df)
    sections.append(("A3: Per-combo blocker effect", a3))

    # ── A4: 4BP board variance 分析 ───────────────
    print("\n--- A4: 4BP MERGED tier 内 board variance ---")
    a4 = analyze_4bp_board_variance(df)
    sections.append(("A4: 4BP board variance", a4))

    # Write report
    with open(REPORT_A, "w") as f:
        f.write("# Probe Phase 7 — Section A 既存データ分析結果\n\n")
        for title, content in sections:
            f.write(f"## {title}\n\n")
            f.write(content)
            f.write("\n\n---\n\n")

    print(f"\nReport: {REPORT_A}")


def analyze_mtt200(df) -> str:
    """MTT200 river/turn で UDG v2 が +20% 悪化した原因を per-board, per-mv で診断."""
    import pandas as pd

    sub = df[df["scenario_id"].isin(["N_mtt200_river", "N_mtt200_turn"])].copy()

    out = []
    out.append(f"対象: N_mtt200_river ({len(sub[sub['scenario_id']=='N_mtt200_river']):,} rows)")
    out.append(f"      N_mtt200_turn  ({len(sub[sub['scenario_id']=='N_mtt200_turn']):,} rows)\n")

    # Per-board huge_loss
    out.append("### Per-board huge_loss (MTT200)\n")
    out.append("| scenario | board_label | n | acc | huge_loss |")
    out.append("|---|---|---:|---:|---:|")
    for (sid, b), g in sub.groupby(["scenario_id", "board_label"]):
        acc = g["udg_correct"].mean() * 100
        huge = g[g["udg_loss"] > 0.5]["udg_loss"].mean() if (g["udg_loss"] > 0.5).any() else 0
        out.append(f"| {sid} | {b} | {len(g):,} | {acc:.1f}% | {huge:.2f} |")

    # mv × board の mismatch
    out.append("\n### MTT200 river での UDG誤判定パターン\n")
    river_sub = sub[sub["scenario_id"] == "N_mtt200_river"].copy()
    wrong = river_sub[~river_sub["udg_correct"] & (river_sub["udg_loss"] > 1)]
    if len(wrong) > 0:
        breakdown = wrong.groupby(["mv_cat", "board_family", "udg_action", "best_action"]).size().reset_index(name="count")
        breakdown = breakdown.sort_values("count", ascending=False).head(20)
        out.append("最頻 mismatch (UDG action vs GTO best_action):\n")
        out.append("| mv_cat | board_family | UDG | GTO best | count |")
        out.append("|---|---|---|---|---:|")
        for _, r in breakdown.iterrows():
            out.append(f"| {r['mv_cat']} | {r['board_family']} | {r['udg_action']} | {r['best_action']} | {r['count']} |")

    out.append("\n### 推定原因 (要 v3 設計指針)")
    out.append("HIGH SPR (MTT200) で UDG v2 の `TIE → CALL` rule が overpressed。")
    out.append("deep stack では bluff catcher の閾値が tighter になる傾向 (read protect)。")
    out.append("→ v3 改善案: SPR=HIGH × TIE × BIG bet で FOLD を増やす")

    return "\n".join(out)


def analyze_r1_ip(df) -> str:
    """R1_past (BTN IP river allin defender) の huge_loss 6.3 BB 原因分析."""

    sub = df[df["scenario_id"] == "R1_past"].copy()

    out = []
    out.append(f"対象: R1_past ({len(sub):,} rows) — BTN IP defender vs BB allin\n")

    # UDG v2 prediction vs GTO best
    out.append(f"UDG v2 acc: {sub['udg_correct'].mean()*100:.1f}%")
    huge_rows = sub[sub["udg_loss"] > 0.5]
    out.append(f"huge_loss: {huge_rows['udg_loss'].mean():.2f} BB ({len(huge_rows):,} rows)\n")

    # Per-board breakdown
    out.append("### Per-board breakdown\n")
    out.append("| board_family | n | acc | huge_loss |")
    out.append("|---|---:|---:|---:|")
    for bf, g in sub.groupby("board_family"):
        acc = g["udg_correct"].mean() * 100
        h = g[g["udg_loss"] > 0.5]["udg_loss"].mean() if (g["udg_loss"] > 0.5).any() else 0
        out.append(f"| {bf} | {len(g):,} | {acc:.1f}% | {h:.2f} |")

    # Mismatch breakdown
    out.append("\n### UDG 誤判定の頻発パターン\n")
    wrong = sub[~sub["udg_correct"] & (sub["udg_loss"] > 1)]
    if len(wrong) > 0:
        breakdown = wrong.groupby(["mv_cat", "equity_bucket", "udg_action", "best_action"]).size().reset_index(name="count")
        breakdown = breakdown.sort_values("count", ascending=False).head(15)
        out.append("| mv_cat | bucket | UDG | GTO best | count |")
        out.append("|---|---|---|---|---:|")
        for _, r in breakdown.iterrows():
            out.append(f"| {r['mv_cat']} | {r['equity_bucket']} | {r['udg_action']} | {r['best_action']} | {r['count']} |")

    out.append("\n### 推定原因")
    out.append("R1 = BTN IP が BB の river allin shove を受ける line。")
    out.append("UDG v2 は OOP defender 想定 → IP の equity bucket 解釈がズレる可能性。")
    out.append("→ v3 改善案: hero_role (IP/OOP) を tier に追加、または IP modifier 専用 rule")

    return "\n".join(out)


def analyze_blocker(df) -> str:
    """card_a / card_b の rank と board の組合せで blocker effect を集計."""

    out = []
    out.append("### Ace blocker on monotone board\n")
    out.append("hero が Ax of suit を持つ場合、opp の nut flush combos は半減 → bluff catch wider 期待\n")

    river_mono = df[(df["board_family"] == "monotone") & (df.get("board_str", "").astype(str).str.len() == 10)].copy()
    if len(river_mono) == 0:
        out.append("対象 river monotone row: 0\n")
    else:
        # Identify hero hands holding A of the board suit
        # board の最初の card のスートを取得
        def has_ace_of_suit(r):
            board = str(r.get("board_str", ""))
            if len(board) < 2: return False
            suit = board[1]  # first card's suit (assumes all flop is same suit on monotone... actually mono only flop)
            ca, cb = str(r.get("card_a", "")), str(r.get("card_b", ""))
            return (ca.startswith("A") and ca[-1] == suit) or (cb.startswith("A") and cb[-1] == suit)

        river_mono["has_a_blocker"] = river_mono.apply(has_ace_of_suit, axis=1)
        with_ = river_mono[river_mono["has_a_blocker"]]
        without = river_mono[~river_mono["has_a_blocker"]]

        if len(with_) > 0 and len(without) > 0:
            # call frequency comparison
            with_call = (with_["best_action"] == "CALL").mean() * 100
            without_call = (without["best_action"] == "CALL").mean() * 100
            out.append(f"With A blocker (n={len(with_):,}): GTO CALL = **{with_call:.1f}%**")
            out.append(f"Without (n={len(without):,}): GTO CALL = **{without_call:.1f}%**")
            out.append(f"\n差: **{with_call - without_call:+.1f}pp**")

    out.append("\n### King blocker on paired board (KK2)\n")
    # KK2 boards でhero が K を持つ場合
    paired = df[(df["board_family"] == "paired") & (df["board_label"].str.contains("KK", na=False))].copy()
    if len(paired) > 0:
        paired["has_k"] = paired.apply(
            lambda r: (str(r.get("card_a", "")).startswith("K") or
                       str(r.get("card_b", "")).startswith("K")), axis=1
        )
        with_k = paired[paired["has_k"]]
        without_k = paired[~paired["has_k"]]
        if len(with_k) > 0 and len(without_k) > 0:
            with_call = (with_k["best_action"] == "CALL").mean() * 100
            without_call = (without_k["best_action"] == "CALL").mean() * 100
            out.append(f"With K blocker (n={len(with_k):,}): GTO CALL = **{with_call:.1f}%**")
            out.append(f"Without (n={len(without_k):,}): GTO CALL = **{without_call:.1f}%**")
            out.append(f"差: **{with_call - without_call:+.1f}pp**")

    out.append("\n### 結論")
    out.append("blocker effect が GTO action freq に与える影響を定量化。")
    out.append("UDG v3 で `blocker_aware` tier を追加すべきか判断材料。")

    return "\n".join(out)


def analyze_4bp_board_variance(df) -> str:
    """4BP MERGED tier 内のボード別 acc / huge_loss バリアンス."""

    sub = df[df["scenario_id"].isin(["N_cash_4bp_flop", "A_cash_4bp_flop"])].copy()

    out = []
    out.append(f"対象: 4BP flop scenarios (n={len(sub):,} rows)\n")

    # Per-board acc, huge_loss
    out.append("### Per-board breakdown (4BP flop)\n")
    out.append("| board_label | board_family | n | UDG acc | UDG huge | v1 huge |")
    out.append("|---|---|---:|---:|---:|---:|")
    for (bl, bf), g in sub.groupby(["board_label", "board_family"]):
        acc = g["udg_correct"].mean() * 100
        h = g[g["udg_loss"] > 0.5]["udg_loss"].mean() if (g["udg_loss"] > 0.5).any() else 0
        v1_h = g[g["formula_loss"] > 0.5]["formula_loss"].mean() if g["formula_loss"].notna().any() and (g["formula_loss"] > 0.5).any() else 0
        out.append(f"| {bl} | {bf} | {len(g):,} | {acc:.1f}% | {h:.2f} | {v1_h:.2f} |")

    # MERGED board の内訳: dry_A94 vs dry_K72 vs dry_Q73 など
    out.append("\n### 推定構造 (要 phase 7 fetch で検証)")
    out.append("MERGED tier 内で Ace-high board は opp の AA/AK が直接 hit するため:")
    out.append("- 期待: dry_A94 は **opp value heavier** で defender tighten")
    out.append("- 期待: dry_K72 は AA overpair が標準、value 構造同等")
    out.append("- 期待: low_dry (8s5d3h) は **opp range 全部 miss** で defender widest")
    out.append("")
    out.append("→ Section B (B1: 4BP flop board variance) で 18 boards × 4BP fetch して検証")

    return "\n".join(out)


# ════════════════════════════ Section B: API probe ═══════════════════════════

def section_b_fetch():
    """新規 API fetch。Section A 結果で priority 確定したら実行."""
    gto_api.init_token_files(ROOT)
    gto_api.update_session()
    import probe_priority as pp

    print("=== Section B: API probe ===\n", flush=True)

    # ── B1: 4BP flop board variance ──
    print("--- B1: 4BP flop × 18 boards (phase2 EXTENDED_BOARDS_18) ---")
    b1_calls = b1_4bp_flop_variance(pp)
    print(f"  B1 完了、{b1_calls} calls 使用\n")

    # ── B2: Turn card category sensitivity ──
    print("--- B2: Turn card category (3 flops × 4 turn cards) ---")
    b2_calls = b2_turn_card_category(pp)
    print(f"  B2 完了、{b2_calls} calls 使用\n")

    print(f"=== Section B 完了、計 {b1_calls + b2_calls} calls ===")


# Board pool for B1 (use phase2 EXTENDED_BOARDS_18)
EXTENDED_BOARDS_18 = [
    ("Ks7d2c", "dry_K72", "dry_high"),
    ("As9c4d", "dry_A94", "dry_high"),  # Ace-high MERGED — key test
    ("Qh7s3c", "dry_Q73", "dry_high"),
    ("8s5d3h", "low_853", "low_dry"),
    ("9c6d4s", "low_964", "low_dry"),
    ("7d5s2c", "low_752", "low_dry"),
    ("Th9c7s", "dyn_T97", "dynamic"),
    ("9c8d6s", "dyn_986", "dynamic"),
    ("8s7d5c", "dyn_875", "dynamic"),
    ("Ts9s7c", "d2t_T97", "dynamic_2tone"),
    ("8h7h5d", "d2t_875", "dynamic_2tone"),
    ("Jd9d6c", "d2t_J96", "dynamic_2tone"),
    ("KsKd2c", "pair_KK2", "paired"),
    ("9c9s2d", "pair_992", "paired"),
    ("Jh8s8d", "pair_J88", "paired"),
    ("Js7s3s", "mono_Js", "monotone"),
    ("Ts8s4s", "mono_Ts", "monotone"),
    ("Qh9h3h", "mono_Qh", "monotone"),
]


def b1_4bp_flop_variance(pp) -> int:
    """B1: 4BP flop × 18 boards で MERGED tier 内 variance を測定."""
    sc = dict(
        id="P7_B1_4bp_flop_var",
        desc="4BP flop × 18 boards (Ace-high vs King-high vs low-dry の variance)",
        GT=pp.CASH_GT, depth=100, stacks="",
        pf=pp.PF_6_4BP, ip_pos="BTN", oop_pos="BB", hero_pos="BB",
        target="flop_def_oop",
    )

    n_calls = 0
    for board, label, family in EXTENDED_BOARDS_18:
        spot_key = f"{sc['id']}_{label}"
        out_path = OUT_DIR / f"{spot_key}.json"
        if out_path.exists() and out_path.stat().st_size > 0:
            print(f"  [B1] {label} ... cached")
            continue

        t0 = time.time()
        try:
            sols, bet_codes, err = pp.walk_to_target(sc, board, "", "")
            n_calls += 2  # X + X-cbet
        except RuntimeError as e:
            if "DAILY_QUOTA_EXCEEDED" in str(e):
                print(f"  Daily quota at {spot_key}, B1 abort")
                return n_calls
            raise

        if sols is None:
            gto_api.log_fetch(LOG, spot_key, "FAIL", int((time.time()-t0)*1000), err=err)
            print(f"  [B1] {label} ... FAIL ({err})")
            continue

        out_path.write_text(json.dumps({
            "scenario_id": sc["id"], "scenario_desc": sc["desc"],
            "board_str": board, "board_label": label, "board_family": family,
            "bet_codes": bet_codes, "sols": sols,
        }, ensure_ascii=False, indent=2))
        gto_api.log_fetch(LOG, spot_key, "OK", int((time.time()-t0)*1000), bet_codes=bet_codes)
        print(f"  [B1] {label} ... OK {bet_codes}")

    return n_calls


# B2 用: 同 flop で異なる turn card を fetch
B2_PROBES = [
    # (flop_board, flop_label, family, [turn_cards: (card, category)])
    ("Ks7d2c", "dry_K72", "dry_high", [
        ("3c", "brick_low"),
        ("Ac", "overcard_ace"),
        ("Kc", "paired_top"),
        ("Td", "midcard_mid"),
    ]),
    ("Th9c7s", "dyn_T97", "dynamic", [
        ("3c", "brick_low"),
        ("Jc", "straight_complete"),  # JT9 straight 完成
        ("Td", "paired_top"),
        ("Ah", "overcard_ace"),
    ]),
    ("Js7s3s", "mono_Js", "monotone", [
        ("3c", "brick_offsuit"),
        ("Qs", "fourth_flush"),  # 4-flush
        ("Ah", "overcard_ace_offsuit"),
        ("Jh", "paired_top"),
    ]),
]


def b2_turn_card_category(pp) -> int:
    """B2: 同 flop × 4 異なる turn card で defender 戦略の変化を測定."""
    sc = dict(
        id="P7_B2_turn_cat",
        desc="同 flop × 4 turn cards (paired/overcard/brick/draw_complete)",
        GT=pp.CASH_GT, depth=100, stacks="",
        pf=pp.PF_6_SRP, ip_pos="BTN", oop_pos="BB", hero_pos="BB",
        target="turn_def_oop",
    )

    n_calls = 0
    for flop_board, flop_label, family, turn_specs in B2_PROBES:
        for turn_card, category in turn_specs:
            spot_key = f"{sc['id']}_{flop_label}_{category}_{turn_card}"
            out_path = OUT_DIR / f"{spot_key}.json"
            if out_path.exists() and out_path.stat().st_size > 0:
                print(f"  [B2] {flop_label} + {turn_card} ({category}) ... cached")
                continue

            t0 = time.time()
            try:
                sols, bet_codes, err = pp.walk_to_target(sc, flop_board, turn_card, "")
                n_calls += 3
            except RuntimeError as e:
                if "DAILY_QUOTA_EXCEEDED" in str(e):
                    print(f"  Daily quota at {spot_key}, B2 abort")
                    return n_calls
                raise

            if sols is None:
                gto_api.log_fetch(LOG, spot_key, "FAIL", int((time.time()-t0)*1000), err=err)
                print(f"  [B2] {flop_label}+{turn_card} ... FAIL ({err})")
                continue

            out_path.write_text(json.dumps({
                "scenario_id": sc["id"], "scenario_desc": sc["desc"],
                "board_str": flop_board + turn_card,
                "board_label": flop_label, "turn_card": turn_card,
                "turn_category": category, "board_family": family,
                "bet_codes": bet_codes, "sols": sols,
            }, ensure_ascii=False, indent=2))
            gto_api.log_fetch(LOG, spot_key, "OK", int((time.time()-t0)*1000), bet_codes=bet_codes)
            print(f"  [B2] {flop_label}+{turn_card} ({category}) ... OK {bet_codes}")

    return n_calls


# ════════════════════════════ Main ═══════════════════════════

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--section", choices=["A", "B", "all"], default="all",
                        help="A: 既存データ分析、B: API fetch、all: 両方")
    args = parser.parse_args()

    if args.section in ("A", "all"):
        section_a_analysis()
    if args.section in ("B", "all"):
        section_b_fetch()


if __name__ == "__main__":
    main()
