#!/usr/bin/env python3
"""
UCBS の MTT データに対する検証。

データソース: mtt-postflop/findings/draw_study_*.jsonl

形式:
{
  "board": "Kd9s8c",
  "scenario": "SRP25" (or "3BP25_SB", "LIMP25_SB" 等),
  "hand_agg": {hand_type: {"total": n, "bet_pct": %}},
  ...
}

シナリオ → UCBS context マッピング:
  SRP25/SRP20      → mtt_25bb (SBR25 → SPR≈8)
  SRP25_SB         → mtt_25bb, scenario=SB
  SRP25_SB_cc      → mtt_25bb, scenario=BTN (SB called BTN raise → BTN IP)
  SRP20_CO         → mtt_25bb, scenario=CO
  3BP25            → mtt_3bp_25 (要追加 context)
  LIMP25_SB        → mtt_25bb, scenario=SB (limp)
  SBR25            → mtt_25bb (汎用)
"""
import json
import glob
from pathlib import Path
from collections import defaultdict

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/cuzic/poker-books/scripts")
from ucbs import ucbs_predict, HP_TABLE, CONTEXTS

# Use calc.py for board type classification
from calc import classify_board_type7


def parse_scenario(filename: str) -> tuple[str, str]:
    """
    Filename から (ucbs_context, scenario) を抽出。

    Returns:
      (context, scenario_pos)
      context: "mtt_25bb" 等
      scenario_pos: "BTN" / "SB" / "CO" / "UTG" / "HJ"
    """
    name = Path(filename).stem.replace("draw_study_", "")

    # 3BP: file 名に "SB" 含めば OOP (3-bettor)、そうでなければ IP (caller)
    if "3BP" in name:
        if "_SB" in name:
            return "mtt_3bp_oop", "SB"  # SB は 3-bettor、OOP
        else:
            return "mtt_3bp_ip", "BTN"  # BTN コーラー、IP

    # SBR 値の抽出
    if "SBR" in name:
        sbr = 25  # default
    elif "25" in name:
        sbr = 25
    elif "20" in name:
        sbr = 20
    else:
        sbr = 25

    # 全 SBR を mtt_25bb context にマップ (shallow MTT)
    context = "mtt_25bb" if sbr <= 25 else "mtt_50bb"

    # Position 抽出
    if "_SB_cc" in name:
        return context, "BTN"  # SB called BTN → BTN is IP
    if "_SB" in name:
        return context, "SB"
    if "_CO" in name:
        return context, "CO"
    if "_HJ" in name:
        return context, "HJ"
    if "_EP" in name or "_UTG" in name:
        return context, "UTG"
    if "LIMP" in name:
        return context, "SB"  # limp scenarios are usually SB

    return context, "BTN"  # default SRP25 etc


def evaluate_mtt_dataset():
    files = sorted(glob.glob("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_*.jsonl"))
    print(f"=== UCBS MTT 検証: {len(files)} jsonl files ===\n")

    all_records = []
    by_file_summary = {}

    for fp in files:
        ctx, scenario = parse_scenario(fp)

        # 3bp は context 未登録なので skip
        if ctx not in CONTEXTS:
            print(f"  SKIP {Path(fp).name} ({ctx} not in CONTEXTS)")
            continue

        file_records = []
        with open(fp) as f:
            for line in f:
                entry = json.loads(line)
                board = entry["board"]
                hand_agg = entry.get("hand_agg", {})

                for hand_type, vals in hand_agg.items():
                    if hand_type not in HP_TABLE:
                        continue
                    n = vals.get("total", 0)
                    if n < 3:
                        continue
                    gto_pct = vals.get("bet_pct", 0) / 100.0

                    # Infer board type from cards
                    try:
                        bt_str = classify_board_type7(board)
                    except Exception:
                        bt_str = ""
                    decision = ucbs_predict(
                        hand_type, "no_draw",
                        board, bt_str, scenario, ctx,
                    )
                    err = decision.frequency - gto_pct
                    rec = {
                        "file": Path(fp).name,
                        "board": board, "hand": hand_type,
                        "n": n, "gto": gto_pct, "pred": decision.frequency,
                        "context": ctx, "scenario": scenario,
                        "cbs": decision.cbs, "conf": decision.confidence,
                        "size": decision.size, "err": err,
                    }
                    file_records.append(rec)
                    all_records.append(rec)

        if file_records:
            total_n = sum(r["n"] for r in file_records)
            wrmse = (sum(r["n"] * r["err"]**2 for r in file_records) / total_n) ** 0.5
            by_file_summary[Path(fp).name] = {
                "context": ctx, "scenario": scenario,
                "n": len(file_records), "combos": total_n,
                "wrmse": wrmse,
            }

    print(f"\n=== 全体評価 (合計 {len(all_records)} records) ===")
    total_n = sum(r["n"] for r in all_records)
    wrmse = (sum(r["n"] * r["err"]**2 for r in all_records) / total_n) ** 0.5
    wmae = sum(r["n"] * abs(r["err"]) for r in all_records) / total_n
    print(f"  WRMSE = {wrmse*100:.2f}%")
    print(f"  WMAE  = {wmae*100:.2f}%")
    print(f"  combos = {total_n:.0f}")

    print(f"\n=== ファイル別 WRMSE ===")
    for name, s in sorted(by_file_summary.items()):
        print(f"  {name:35s} ctx={s['context']:10s} scen={s['scenario']:4s}  "
              f"n={s['n']:4d}  combos={s['combos']:5.0f}  WRMSE={s['wrmse']*100:.1f}%")

    # By hand
    print(f"\n=== Hand 別 bias ===")
    by_hand = defaultdict(lambda: [0.0, 0.0, 0.0])
    for r in all_records:
        by_hand[r["hand"]][0] += r["n"] * r["err"]
        by_hand[r["hand"]][1] += r["n"]
        by_hand[r["hand"]][2] += r["n"] * r["err"]**2

    print(f"{'hand':16s} {'HP':>3s} {'combos':>7s} {'bias':>8s} {'wrmse':>8s}")
    for h in ["no_made_hand", "ace_high", "king_high", "low_pair", "underpair",
              "third_pair", "second_pair", "top_pair", "overpair",
              "two_pair", "straight", "flush", "set", "trips", "fullhouse"]:
        if h not in by_hand: continue
        esum, n, sse = by_hand[h]
        if n > 0:
            print(f"  {h:14s} {HP_TABLE[h]:>3d} {int(n):>7d}  "
                  f"{esum/n*100:+6.1f}%  {(sse/n)**0.5*100:>6.1f}%")

    # Per-context summary
    print(f"\n=== Context 別 ===")
    by_ctx = defaultdict(lambda: [0.0, 0.0])
    for r in all_records:
        by_ctx[r["context"]][0] += r["n"]
        by_ctx[r["context"]][1] += r["n"] * r["err"]**2
    for ctx, (n, sse) in sorted(by_ctx.items()):
        if n > 0:
            print(f"  {ctx:14s} combos={n:.0f}  WRMSE={(sse/n)**0.5*100:.2f}%")


if __name__ == "__main__":
    evaluate_mtt_dataset()
