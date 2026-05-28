#!/usr/bin/env python3
"""DCBS 4 context fit (mtt25/50/100 + cash100)

各 context で:
  - HP=2 各 hand の continue freq 平均
  - HP=3,5,7+ の continue freq 平均
を計算して DCBS_BASE / KICKER_OFFSET を確定。
"""
from __future__ import annotations
import sys, json
from pathlib import Path
from collections import defaultdict
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/cuzic/poker-books/scripts")
from ucbs_v2 import HP_TABLE


def load(fp):
    out = []
    with open(fp) as f:
        for line in f:
            entry = json.loads(line)
            for h, vals in entry.get("hand_agg", {}).items():
                if h not in HP_TABLE or vals.get("total", 0) < 3:
                    continue
                out.append({"hand": h, "n": vals["total"],
                            "gto": vals["cont_pct"] / 100.0})
    return out


def fit_context(records):
    """各 hand の combos 加重平均 continue freq を返す"""
    by_hand = defaultdict(lambda: [0.0, 0.0])
    for r in records:
        by_hand[r["hand"]][0] += r["n"] * r["gto"]
        by_hand[r["hand"]][1] += r["n"]
    return {h: s/n for h, (s, n) in by_hand.items() if n > 0}


def main():
    files = {
        "mtt_25bb": "/home/cuzic/poker-books/mtt-postflop/findings/draw_study_DEF_MTT25_BB.jsonl",
        "mtt_50bb": "/home/cuzic/poker-books/mtt-postflop/findings/draw_study_DEF_MTT50_BB.jsonl",
        "mtt_100bb": "/home/cuzic/poker-books/mtt-postflop/findings/draw_study_DEF_MTT100_BB.jsonl",
        "cash_100bb": "/home/cuzic/poker-books/mtt-postflop/findings/draw_study_DEF_CASH100_BB.jsonl",
    }

    fits = {}
    for label, fp in files.items():
        recs = load(fp)
        fits[label] = fit_context(recs)
        n_total = sum(r["n"] for r in recs)
        print(f"\n{label} (n={len(recs)}, combos={int(n_total)})")
        for h in ["no_made_hand", "ace_high", "king_high", "low_pair",
                  "underpair", "third_pair", "second_pair",
                  "top_pair", "overpair", "two_pair", "straight",
                  "set", "trips", "fullhouse"]:
            if h in fits[label]:
                print(f"  {h:14s} (HP={HP_TABLE[h]}): {fits[label][h]*100:.1f}%")

    # ─── Cross-context 比較 ──────────────────────────────
    print("\n" + "=" * 70)
    print("Hand 別 continue freq の context 間比較")
    print("=" * 70)
    hands = ["no_made_hand", "ace_high", "king_high", "low_pair",
             "underpair", "third_pair", "second_pair",
             "top_pair", "overpair", "two_pair", "set"]
    ctxs = list(fits.keys())
    print(f"{'hand':14s} {'HP':>3s}  " + "  ".join(f"{c:>10s}" for c in ctxs))
    for h in hands:
        row = [f"{h:14s} {HP_TABLE.get(h, '?'):>3}"]
        for c in ctxs:
            v = fits[c].get(h)
            row.append(f"{v*100:>9.1f}%" if v else f"{'—':>10s}")
        print("  ".join(row))

    # ─── DCBS_BASE 推奨値 (HP 別中央値) ───────────────────
    print("\n" + "=" * 70)
    print("[推奨] context 別 DCBS_BASE")
    print("=" * 70)
    for c in ctxs:
        print(f"\n{c}:")
        f = fits[c]
        # HP=2 average (kicker offset 計算用)
        hp2 = [f[h] for h in ["no_made_hand", "ace_high", "king_high", "low_pair"]
               if h in f]
        avg2 = sum(hp2) / len(hp2) if hp2 else 0
        print(f"  HP=2 (air, avg): {avg2*100:.1f}%")
        for h in ["no_made_hand", "ace_high", "king_high", "low_pair"]:
            if h in f:
                print(f"    {h:14s} offset: {(f[h] - avg2)*100:+.1f}pt")
        # HP=3,5,7+
        hp3 = [f[h] for h in ["underpair", "third_pair"] if h in f]
        avg3 = sum(hp3) / len(hp3) if hp3 else 0
        hp5 = f.get("second_pair", 0)
        hp7 = [f[h] for h in ["top_pair", "overpair"] if h in f]
        avg7 = sum(hp7) / len(hp7) if hp7 else 0
        print(f"  HP=3 (weak pair): {avg3*100:.1f}%")
        print(f"  HP=5 (mid pair):  {hp5*100:.1f}%")
        print(f"  HP=7 (top pair):  {avg7*100:.1f}%")


if __name__ == "__main__":
    main()
