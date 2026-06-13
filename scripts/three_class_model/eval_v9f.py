#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
from __future__ import annotations
import pandas as pd, numpy as np, re
from collections import Counter

CSV = "/home/cuzic/poker-books/scripts/three_class_model/dataset_attack_v1.csv"
RANK_MAP = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"T":10,"J":11,"Q":12,"K":13,"A":14}

def top_rank(s):
    cs = re.findall(r'[AKQJT2-9]', s.upper()[:10])
    return max((RANK_MAP.get(c,0) for c in cs), default=0)

def dv_group(dv):
    if dv in ("combo_draw","fd","oesd","nut_flush_draw"): return "strong"
    elif dv in ("gutshot","twocards_bdfd"): return "gutshot"
    return "none"

def board_type_fixed(board_str):
    cards = re.findall(r'[AKQJT2-9][shdcSHDC]', board_str, re.IGNORECASE)
    if len(cards) < 3: return "dry"
    ranks = [RANK_MAP.get(c[0].upper(), 0) for c in cards]
    suits = [c[1].lower() for c in cards]
    if any(v >= 2 for v in Counter(ranks).values()): return "paired"
    if 14 in ranks:
        non_a = [r for r in ranks if r != 14]
        if non_a and max(non_a) <= 6: return "wet"
    if len(set(suits)) == 1: return "wet"
    if max(ranks) - min(ranks) <= 4: return "wet"
    return "dry"

def predict_v9f(row):
    bt=str(row["board_type"]); tier=str(row["tier"]); pos=str(row["position"])
    street=str(row["street"]); pot=str(row["pot_type"]); dv=dv_group(str(row["dv_cat"]))
    has_any=dv in ("strong","gutshot"); has_strong=(dv=="strong"); has_gutshot=(dv=="gutshot")
    has_none=(dv=="none"); tr=row["tr"]; hi=tr>=13

    if street == "flop":
        if pos == "OOP":
            if pot == "SRP" and tier == "TP+" and bt == "dry" and has_none and tr > 12: return "BET"
            if pot == "SRP" and tier == "エア" and bt == "wet" and has_none and tr <= 5: return "BET"
            # v9f: TP+×wet×gutshot rank rule
            if pot == "SRP" and tier == "TP+" and bt == "wet" and has_gutshot: return "BET" if tr <= 6 else "CHECK"
            # v9f: アンダーペア×dry×gutshot rank rule
            if pot == "SRP" and tier == "アンダーペア" and bt == "dry" and has_gutshot: return "BET" if tr > 12 else "CHECK"
            if pot == "SRP" and tier == "2P+" and bt == "wet" and has_none: return "BET" if tr <= 6 else "CHECK"
            if pot == "SRP" and tier == "2P+" and bt == "paired" and has_none: return "BET" if tr <= 5 else "CHECK"
            if pot == "SRP" and tier == "2P+" and bt == "dry" and has_none: return "BET" if tr > 12 else "CHECK"
            return "CHECK"
        if pot == "4BP":
            if tier == "2P+": return "CHECK"
            if tier == "TP+":
                if bt == "dry": return "BET" if tr > 8 else "CHECK"
                if bt == "wet" and has_none: return "BET" if tr <= 11 else "CHECK"
                return "BET" if bt != "paired" else "CHECK"
            if tier == "エア":
                if bt == "dry" and has_none: return "BET" if tr <= 13 else "CHECK"
                if bt == "wet":
                    if has_strong or has_gutshot: return "CHECK"
                    return "BET" if tr <= 9 else "CHECK"
            if tier == "アンダーペア":
                if bt == "wet" and has_none: return "CHECK"
                return "BET"
            return "CHECK"
        if tier == "2P+": return "BET"
        if pot == "3BP":
            if tier == "TP+":
                if bt == "wet" and has_none: return "BET" if tr <= 9 else "CHECK"
                return "BET"
            if tier == "アンダーペア":
                if bt == "dry" and has_gutshot: return "BET" if tr > 11 else "CHECK"
            if tier == "エア":
                if bt == "paired": return "BET" if tr <= 6 else "CHECK"
                if bt == "dry" and has_none and tr <= 9: return "BET"
            return "CHECK"
        # IP SRP flop
        if tier == "TP+":
            if bt == "dry": return "BET" if (has_any or tr > 11) else "CHECK"
            if bt == "paired": return "BET"
            if bt == "wet":
                # v9f: strong×wet low board → CHECK
                if has_strong: return "BET" if tr > 5 else "CHECK"
                return "BET" if (has_gutshot or tr > 8) else "CHECK"
            return "CHECK"
        if tier == "アンダーペア":
            if bt == "wet" and has_any: return "CHECK"
            if bt == "paired": return "BET" if tr != 14 else "CHECK"
            if bt == "dry":
                if has_gutshot: return "BET" if tr > 11 else "CHECK"
                if has_any: return "BET"
            return "CHECK"
        if bt == "dry":
            if hi: return "BET" if has_strong else "CHECK"
            else: return "BET" if has_any else "CHECK"
        if bt == "wet":
            if has_strong: return "BET" if tr > 8 else "CHECK"
            if has_gutshot: return "BET" if tr > 10 else "CHECK"
            # v9f: エア×wet×none threshold ≤5 (was ≤6)
            if has_none: return "BET" if tr <= 5 else "CHECK"
            return "CHECK"
        if bt == "paired": return "BET" if (has_any or not hi) else "CHECK"
        return "CHECK"

    elif street == "turn":
        if pos == "IP":
            if tier == "2P+":
                if pot == "3BP" and bt == "wet" and has_none: return "CHECK"
                if pot == "4BP" and bt == "dry" and has_none: return "BET" if tr > 8 else "CHECK"
                return "BET"
            if pot == "4BP":
                if tier == "TP+":
                    if bt == "paired" and has_none: return "BET" if tr > 7 else "CHECK"
                    return "BET"
                if tier == "アンダーペア":
                    if bt == "wet": return "BET"
                    if bt == "paired" and has_none: return "BET" if tr <= 11 else "CHECK"
                    return "BET"
                if tier == "エア":
                    if bt == "dry":
                        if has_gutshot: return "BET" if tr > 11 else "CHECK"
                        return "BET" if not has_strong else "CHECK"
                    if bt == "wet":
                        if has_strong: return "CHECK"
                        return "BET"
                    if bt == "paired":
                        if has_strong: return "BET" if tr > 10 else "CHECK"
                        return "CHECK"
                return "CHECK"
            if pot == "3BP":
                if tier == "TP+":
                    if bt == "dry": return "BET"
                    if bt == "paired" and has_none: return "CHECK" if tr <= 13 else "BET"
                    if has_gutshot: return "BET"
                    return "CHECK"
                if tier == "アンダーペア":
                    if bt == "paired" and has_none: return "BET" if tr > 9 else "CHECK"
                    return "BET" if bt == "paired" else "CHECK"
                if tier == "エア":
                    if bt == "dry":
                        if has_none: return "BET" if tr <= 8 else "CHECK"
                        if has_any: return "BET"
                    if bt == "wet" and has_gutshot: return "BET"
                    if bt == "paired":
                        if has_strong: return "BET" if tr > 9 else "CHECK"
                        if has_none: return "BET" if tr <= 9 else "CHECK"
                        if has_gutshot: return "BET" if tr > 13 else "CHECK"
                return "CHECK"
            # SRP IP turn
            if tier == "TP+":
                # v9f: TP+×dry×none rank rule
                if bt == "dry" and has_none: return "BET" if tr <= 10 else "CHECK"
                return "BET" if has_any else "CHECK"
            if tier == "アンダーペア": return "CHECK"
            return "BET" if has_any else "CHECK"
        else:  # OOP turn
            if pot == "SRP":
                if tier == "2P+":
                    if bt == "wet": return "BET" if tr > 9 else "CHECK"
                    if bt == "paired": return "BET" if tr <= 10 else "CHECK"
                    return "BET" if bt == "dry" else "CHECK"
                # v9f: TP+×wet×none rank rule
                if tier == "TP+":
                    if bt == "wet" and has_none: return "BET" if tr <= 10 else "CHECK"
                    return "CHECK"
                if tier == "エア":
                    if bt == "wet" and has_any: return "BET"
                    if bt == "paired":
                        if has_strong: return "BET" if tr <= 10 else "CHECK"
                        if has_gutshot: return "BET" if tr <= 10 else "CHECK"
                    if bt == "dry" and has_strong: return "BET" if tr <= 11 else "CHECK"
                return "CHECK"
            if pot == "3BP":
                if tier == "TP+":
                    if bt == "paired" and has_none: return "BET" if tr <= 10 else "CHECK"
                    return "BET"
                if tier == "2P+":
                    if bt == "wet": return "BET"
                    if bt == "paired": return "BET" if tr > 6 else "CHECK"
                if tier == "エア":
                    # v9f: エア×paired×strong rank rule
                    if has_strong:
                        if bt == "paired": return "BET" if tr <= 10 else "CHECK"
                        return "BET"
                    if bt == "paired":
                        if has_gutshot: return "BET" if tr > 11 else "CHECK"
                return "CHECK"
            if pot == "4BP":
                if tier == "TP+":
                    if bt == "wet" and has_none: return "CHECK"
                    if bt == "paired": return "BET" if tr > 10 else "CHECK"
                    if bt == "dry" and has_none: return "BET" if tr <= 13 else "CHECK"
                    return "BET"
                if tier == "2P+":
                    if bt == "wet": return "BET"
                    if bt == "paired" and has_none: return "BET" if tr > 9 else "CHECK"
                if tier == "アンダーペア" and bt == "dry" and has_any: return "BET"
                if tier == "エア":
                    if bt == "dry" and has_gutshot: return "BET" if tr <= 9 else "CHECK"
                return "CHECK"
            return "CHECK"

    else:  # river
        if pos == "IP":
            if tier == "2P+": return "BET"
            if pot == "SRP":
                if tier == "TP+": return "BET" if bt in ("dry","paired") else "CHECK"
                if tier == "アンダーペア":
                    if bt == "paired" and has_none: return "BET" if tr <= 11 else "CHECK"
                    return "BET" if bt == "paired" else "CHECK"
                if tier == "エア" and bt == "paired": return "BET" if tr <= 11 else "CHECK"
                return "BET"
            if pot == "3BP":
                if tier == "TP+": return "BET"
                if tier == "エア":
                    if bt in ("wet","dry"): return "BET"
                    if bt == "paired" and has_none: return "BET" if tr <= 11 else "CHECK"
                    return "CHECK"
                return "CHECK"
            if pot == "4BP":
                if tier == "TP+": return "BET"
                if tier == "アンダーペア":
                    if bt == "paired": return "BET" if tr > 11 else "CHECK"
                    return "CHECK"
                if tier == "エア":
                    if bt == "dry": return "BET" if tr <= 13 else "CHECK"
                    return "CHECK"
                return "CHECK"
            return "CHECK"
        else:  # OOP river
            if pot == "SRP":
                if tier == "TP+": return "BET"
                if tier == "2P+":
                    if bt == "dry" and has_none: return "BET" if tr <= 10 else "CHECK"
                    # v9f: 2P+×paired×none rank rule (A-high → CHECK)
                    if bt == "paired" and has_none: return "BET" if tr <= 13 else "CHECK"
                    return "BET"
                if tier == "アンダーペア" and bt == "paired": return "BET" if tr > 12 else "CHECK"
                if tier == "エア":
                    if bt == "paired": return "BET" if tr <= 12 else "CHECK"
                    if bt == "dry" and has_none: return "BET" if tr <= 10 else "CHECK"
                return "CHECK"
            if pot == "3BP":
                if tier == "エア":
                    if bt == "dry": return "BET"
                    if bt == "paired" and has_none: return "BET" if tr <= 11 else "CHECK"
                    return "CHECK"
                if tier == "アンダーペア" and bt == "dry": return "BET" if tr > 13 else "CHECK"
                return "BET"
            if pot == "4BP":
                if tier == "TP+":
                    if bt == "paired": return "BET" if tr <= 11 else "CHECK"
                if tier == "2P+" and bt == "paired": return "BET" if tr <= 11 else "CHECK"
                return "CHECK" if tier == "エア" else "BET"
            return "CHECK"

df = pd.read_csv(CSV)
df["board_type"] = df["board"].apply(board_type_fixed)
df["dv_grp"] = df["dv_cat"].apply(dv_group)
df["tr"] = df["board"].apply(top_rank)
df["pred"] = df.apply(predict_v9f, axis=1)
df["correct"] = df["pred"] == df["best_action"]
acc = float(np.average(df["correct"], weights=df["n_combos"]))*100
total = df["n_combos"].sum()
print(f"v9f精度: {acc:.3f}%  (v9e=80.984%)")

print("\nシナリオ別:")
for (st, pos, pot) in [("flop","IP","SRP"),("flop","IP","3BP"),("flop","IP","4BP"),
                        ("flop","OOP","SRP"),("turn","IP","SRP"),("turn","IP","3BP"),
                        ("turn","IP","4BP"),("turn","OOP","SRP"),("turn","OOP","3BP"),
                        ("turn","OOP","4BP"),("river","IP","SRP"),("river","IP","3BP"),
                        ("river","IP","4BP"),("river","OOP","SRP"),("river","OOP","3BP"),("river","OOP","4BP")]:
    sub = df[(df["street"]==st)&(df["position"]==pos)&(df["pot_type"]==pot)]
    if sub.empty: continue
    a = float(np.average(sub["correct"], weights=sub["n_combos"]))*100
    print(f"  {st:5} {pos:3} {pot:3}: {a:.1f}%")
