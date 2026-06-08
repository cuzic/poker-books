"""全 probe 結果を統合した summary CSV を生成。

入力:
- knowledges/gto_wizard_study/probe_drill/*.json (BB OOP first-action)
- knowledges/gto_wizard_study/probe_drill_btn_cbet/*.json (BTN cbet decisions)
- knowledges/gto_wizard_study/probe_drill_bb_defense/*.json (BB defense vs BTN cbet)
- knowledges/gto_wizard_study/probe_3bp_4bp/*.json (3BP/4BP first-actions)

出力: dataset_drill_probes_v2.csv (全 action summary、purpose 別に分類)
"""
from __future__ import annotations
import csv, json
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parents[2]
GTOW_DIR = REPO_ROOT / "knowledges/gto_wizard_study"
OUT_CSV = REPO_ROOT / "scripts/three_class_model/dataset_drill_probes_v2.csv"


def gather(probe_dir: Path, purpose: str, role_hint: str = "") -> list[dict]:
    rows: list[dict] = []
    if not probe_dir.exists():
        return rows
    for f in sorted(probe_dir.glob("*.json")):
        try:
            saved = json.loads(f.read_text())
        except Exception:
            continue
        flop = saved.get("flop") or saved.get("spec", {}).get("flop", "")
        data = saved.get("data", {})
        actions = data.get("action_solutions", [])
        for a in actions:
            act = a.get("action", {})
            rows.append({
                "purpose": purpose,
                "role": role_hint or act.get("position", ""),
                "flop": flop.lower(),
                "probe_file": f.name,
                "preflop": saved.get("preflop", "") or saved.get("api_params", {}).get("preflop_actions", ""),
                "flop_actions_pre": (data.get("game", {}).get("current_street") or ""),
                "action_type": act.get("type", ""),
                "action_name": act.get("display_name", ""),
                "betsize": act.get("betsize", ""),
                "betsize_by_pot": act.get("betsize_by_pot", ""),
                "is_allin": act.get("allin", False),
                "total_frequency": round(a.get("total_frequency", 0), 4),
                "total_ev": round(a.get("total_ev", 0), 4),
                "total_combos": a.get("total_combos", 0),
            })
    return rows


def main() -> None:
    rows: list[dict] = []
    rows.extend(gather(GTOW_DIR / "probe_drill",            "boundary_or_bb_oop", "BB"))
    rows.extend(gather(GTOW_DIR / "probe_drill_btn_cbet",   "srp_btn_cbet",       "BTN"))
    rows.extend(gather(GTOW_DIR / "probe_drill_bb_defense", "srp_bb_defense",     "BB"))
    rows.extend(gather(GTOW_DIR / "probe_3bp_4bp",          "3bp_or_4bp_first",   "BB"))

    if not rows:
        print("No data")
        return

    fieldnames = list(rows[0].keys())
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"✓ wrote {len(rows)} rows → {OUT_CSV}")

    # Summary
    by_purpose: dict[str, int] = defaultdict(int)
    flops_by_purpose: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        by_purpose[r["purpose"]] += 1
        flops_by_purpose[r["purpose"]].add(r["flop"])
    print("\n=== Coverage ===")
    for p, n in by_purpose.items():
        print(f"  {p}: {n} rows, {len(flops_by_purpose[p])} unique flops")


if __name__ == "__main__":
    main()
