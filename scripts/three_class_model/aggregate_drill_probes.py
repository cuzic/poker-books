"""knowledges/gto_wizard_study/probe_drill/*.json を集計して dataset 拡張用 CSV を生成。

各 spot から:
- action_solutions の summary (action × total_frequency × total_ev × dominant_sizing)
- hand_categories ごとの bet freq / EV (簡易版、per-combo は省略)

出力:
- dataset_drill_probes.csv (簡易集計、audit 用)
- 既存 dataset_unified_v2.csv とは形式が違う (per-combo ではない)

GTO Wizard hand_categories integer → label の参照表は memory 不在のため、
本スクリプトでは integer をそのまま使う。
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROBE_DIR = REPO_ROOT / "knowledges/gto_wizard_study/probe_drill"
OUTPUT_CSV = REPO_ROOT / "scripts/three_class_model/dataset_drill_probes.csv"


def aggregate_spot(saved: dict) -> dict:
    """1 spot の summary。"""
    spec = saved.get("spec", {})
    data = saved.get("data", {})
    actions = data.get("action_solutions", [])

    rows: list[dict] = []
    for a in actions:
        act = a.get("action", {})
        rows.append({
            "probe_id": saved.get("probe_id", ""),
            "purpose": spec.get("purpose", ""),
            "flop": spec.get("flop", ""),
            "scenario_type": spec.get("scenario_type", ""),
            "category": spec.get("category", ""),
            "boundary_type": spec.get("boundary_type", ""),
            "n_drill_cards": spec.get("n_drill_cards", 0),
            "action_type": act.get("type", ""),
            "action_name": act.get("display_name", ""),
            "betsize": act.get("betsize", ""),
            "betsize_by_pot": act.get("betsize_by_pot", ""),
            "total_frequency": round(a.get("total_frequency", 0), 4),
            "total_ev": round(a.get("total_ev", 0), 4),
            "total_combos": a.get("total_combos", 0),
            "is_allin": act.get("allin", False),
        })
    return rows


def main() -> None:
    if not PROBE_DIR.exists():
        print(f"✗ {PROBE_DIR} not found")
        return
    files = sorted(PROBE_DIR.glob("*.json"))
    print(f"Loading {len(files)} probe files...")

    all_rows: list[dict] = []
    for f in files:
        try:
            saved = json.loads(f.read_text())
            rows = aggregate_spot(saved)
            all_rows.extend(rows)
        except Exception as e:
            print(f"  ✗ {f.name}: {e}")

    if not all_rows:
        print("No rows to write")
        return

    fieldnames = list(all_rows[0].keys())
    with open(OUTPUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(all_rows)
    print(f"\n✓ wrote {len(all_rows)} rows × {len(fieldnames)} cols → {OUTPUT_CSV}")

    # Quick summary
    print("\n=== Summary ===")
    purposes: dict[str, int] = {}
    flops: set[str] = set()
    for r in all_rows:
        purposes[r["purpose"]] = purposes.get(r["purpose"], 0) + 1
        flops.add(r["flop"])
    for p, n in purposes.items():
        print(f"  {p}: {n} rows")
    print(f"  unique flops: {len(flops)}")

    # Sample per-flop dominant action
    print("\n=== Dominant action per (flop, purpose) ===")
    from collections import defaultdict
    by_flop_purpose: dict[tuple, list[dict]] = defaultdict(list)
    for r in all_rows:
        by_flop_purpose[(r["flop"], r["purpose"])].append(r)
    for (flop, purpose), rows in sorted(by_flop_purpose.items()):
        bet_freq = sum(r["total_frequency"] for r in rows if r["action_type"] in ("BET", "RAISE"))
        sizes = [(r["betsize"], r["total_frequency"]) for r in rows if r["action_type"] in ("BET", "RAISE")]
        sizes.sort(key=lambda x: -x[1])
        main_size = sizes[0][0] if sizes else "—"
        print(f"  {flop:>10} {purpose:>12}: BET={bet_freq*100:5.1f}%, dominant_size={main_size}")


if __name__ == "__main__":
    main()
