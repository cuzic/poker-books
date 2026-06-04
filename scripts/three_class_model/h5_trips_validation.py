#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""H5 検証: トリップス SRP vs 3bp 逆転を defense_study .jsonl から確認."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/home/cuzic/poker-books/vol3-mtt-postflop/findings")


def main() -> int:
    print("=== Trips 挙動 SRP vs 3bp ===")
    print(f"{'Scenario':30s} {'CALL %':>10s} {'RAISE %':>10s} {'FOLD %':>10s} {'verdict'}")
    print("-" * 90)

    scenarios = [
        "defense_study_SRP25_OOP",
        "defense_study_SRP20_OOP",
        "defense_study_SRP25_SB_OOP",
        "defense_study_SRP20_SB_OOP",
        "defense_study_SRP25_SB_IP",
        "defense_study_SRP20_SB_IP",
        "defense_study_3BP20_OOP",
        "defense_study_3BP20_IP",
        "defense_study_3BP25_SB_OOP",
        "defense_study_3BP25_SB_IP",
        "defense_study_CO_BB_SRP25",
        "defense_study_HJ_BB_SRP25",
        "defense_study_CO_BB_SRP20",
        "defense_study_HJ_BB_SRP20",
        "defense_study_EP3_BB_SRP20",
        "defense_study_EP3_BB_SRP25",
        "defense_study_EP2_BB_SRP20",
        "defense_study_EP1_BB_SRP20",
    ]

    results = {}
    for sc in scenarios:
        path = ROOT / f"{sc}.jsonl"
        if not path.exists():
            continue
        all_trips_actions = []  # list of (call, fold, raise) tuples weighted by n
        try:
            for line in path.read_text().splitlines():
                if not line.strip(): continue
                d = json.loads(line)
                cross = d.get("cross", {})
                # Find trips category
                trips_keys = [k for k in cross if "trips" in k]
                for k in trips_keys:
                    cell = cross[k]
                    n = cell.get("n", 0)
                    if n < 5: continue
                    call = cell.get("call_pct", 0)
                    fold = cell.get("fold_pct", 0)
                    raise_ = cell.get("raise_pct", 0)
                    all_trips_actions.append((n, call, fold, raise_))
        except Exception as e:
            print(f"  {sc}: parse error {e}")
            continue

        if not all_trips_actions:
            continue
        total_n = sum(x[0] for x in all_trips_actions)
        if total_n == 0: continue
        avg_call = sum(x[0] * x[1] for x in all_trips_actions) / total_n
        avg_fold = sum(x[0] * x[2] for x in all_trips_actions) / total_n
        avg_raise = sum(x[0] * x[3] for x in all_trips_actions) / total_n

        pot_type = "3BP" if "3BP" in sc else "SRP"
        verdict = ""
        if pot_type == "SRP" and avg_raise > 70:
            verdict = "✓ SRP raise高"
        elif pot_type == "3BP" and avg_raise < 30:
            verdict = "✓ 3BP call高"
        elif pot_type == "SRP" and avg_raise < 50:
            verdict = "? SRP でも raise 控えめ"
        elif pot_type == "3BP" and avg_raise > 50:
            verdict = "? 3BP で raise 多い"

        print(f"  {sc:30s} {avg_call:>8.1f}%  {avg_raise:>8.1f}%  {avg_fold:>8.1f}%  {verdict}")
        results[sc] = (avg_call, avg_fold, avg_raise)

    # Summary verdict
    print("\n=== H5 検証結論 ===")
    srp_oop_raises = [v[2] for k, v in results.items() if "SRP" in k and "_OOP" in k and "3BP" not in k]
    bp3_oop_raises = [v[2] for k, v in results.items() if "3BP" in k and "_OOP" in k]
    if srp_oop_raises:
        print(f"  SRP OOP 平均 raise: {sum(srp_oop_raises)/len(srp_oop_raises):.1f}%")
    if bp3_oop_raises:
        print(f"  3BP OOP 平均 raise: {sum(bp3_oop_raises)/len(bp3_oop_raises):.1f}%")
    if srp_oop_raises and bp3_oop_raises:
        diff = sum(srp_oop_raises)/len(srp_oop_raises) - sum(bp3_oop_raises)/len(bp3_oop_raises)
        if diff > 40:
            print(f"  → 逆転 確認 (gap {diff:.1f}pp) ✓")
        elif diff > 20:
            print(f"  → 部分的に逆転 (gap {diff:.1f}pp) △")
        else:
            print(f"  → 逆転 否定 (gap {diff:.1f}pp) ✗")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
