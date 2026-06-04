#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas"]
# ///
"""Extract per-spot OFFERED bet size for attack spots."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path("/home/cuzic/poker-books")
OUT = ROOT / "scripts" / "three_class_model" / "attack_bet_size.csv"


def main() -> int:
    rows = []
    for sp in ["vol3-mtt-postflop/findings", "knowledges/gto_wizard_full", "knowledges/gto_wizard_study"]:
        base = ROOT / sp
        if not base.exists():
            continue
        for p in base.glob("**/*.json"):
            try:
                d = json.loads(p.read_text())
            except Exception:
                continue
            if not isinstance(d, dict):
                continue
            actions = d.get("action_solutions") or []
            codes = [(a.get("action") or {}).get("code", "") for a in actions if isinstance(a, dict)]
            if not codes:
                continue
            if "F" in codes or "C" in codes:
                continue  # defense
            # Find offered bet sizes
            sizes = []
            for a in actions:
                if not isinstance(a, dict): continue
                act = a.get("action") or {}
                if act.get("code", "").startswith("R"):
                    bp = act.get("betsize_by_pot")
                    if bp is not None:
                        try:
                            sizes.append(float(bp))
                        except (TypeError, ValueError):
                            continue
            meta = d.get("_meta") or {}
            spot_id = meta.get("id") if meta else p.stem
            # depth / family hints
            req = meta.get("request") or {}
            depth = req.get("depth")
            gametype = req.get("gametype") or (d.get("game") or {}).get("gametype") or ""
            family = "mtt" if "mtt" in str(gametype).lower() or "mtt" in str(p) else ("cash" if "cash" in str(gametype).lower() or "cash" in str(p) else "")
            primary_size = min(sizes) if sizes else None
            largest = max(sizes) if sizes else None
            rows.append({
                "spot_id": spot_id,
                "source_path": str(p.relative_to(ROOT)),
                "family": family,
                "depth": depth,
                "n_sizes": len(sizes),
                "primary_size_pot": round(primary_size, 3) if primary_size else None,
                "largest_size_pot": round(largest, 3) if largest else None,
                "all_sizes": ",".join(f"{s:.2f}" for s in sorted(sizes)),
            })
    if not rows:
        return 1
    cols = list(rows[0].keys())
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"Wrote {len(rows)} attack spots → {OUT}")
    from collections import Counter
    sz_dist = Counter()
    for r in rows:
        s = r["primary_size_pot"]
        if s is None: continue
        if s < 0.45: sz_dist["small (<45%)"] += 1
        elif s < 0.85: sz_dist["mid (45-85%)"] += 1
        else: sz_dist["big (>=85%)"] += 1
    print(f"\nPrimary size distribution:")
    for k, n in sz_dist.most_common():
        print(f"  {k}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
