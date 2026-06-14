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
def second_rank(s):
    cs = re.findall(r'[AKQJT2-9]', s.upper()[:10])
    ranks = sorted([RANK_MAP.get(c,0) for c in cs], reverse=True)
    return ranks[1] if len(ranks) >= 2 else 0
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
def aqs(avg_loss): return max(0.0, (50.0-avg_loss)/(50.0-22.746)*100)

def predict_v28(row):
    bt=str(row["board_type"]); tier=str(row["tier"]); pos=str(row["position"])
    street=str(row["street"]); pot=str(row["pot_type"]); dv=dv_group(str(row["dv_cat"]))
    has_any=dv in ("strong","gutshot"); has_strong=(dv=="strong"); has_gutshot=(dv=="gutshot")
    has_none=(dv=="none"); tr=row["tr"]; hi=tr>=13; tr2=row["tr2"]
    mv=str(row["mv_cat"])
    is_no_made=(mv=="no_made_hand"); is_ace_high=(mv=="ace_high"); is_king_high=(mv=="king_high")
    is_low_pair=(mv=="low_pair"); is_second_pair=(mv=="second_pair"); is_third_pair=(mv=="third_pair")
    is_overpair=(mv=="overpair")

    if street == "flop":
        if pos == "OOP":
            if pot == "SRP" and tier == "エア" and bt == "wet" and has_none and tr <= 5: return "BET"
            if pot == "SRP" and tier == "エア" and bt == "wet" and has_strong: return "BET" if tr <= 6 else "CHECK"
            if pot == "SRP" and tier == "エア" and bt == "wet" and has_gutshot: return "BET" if tr == 6 else "CHECK"
            if pot == "SRP" and tier == "TP+" and bt == "wet" and has_gutshot: return "BET" if tr <= 6 else "CHECK"
            if pot == "SRP" and tier == "TP+" and bt == "wet" and has_none and tr == 6: return "BET"
            if pot == "SRP" and tier == "TP+" and bt == "wet" and has_strong and tr == 6: return "BET"
            if pot == "SRP" and tier == "アンダーペア" and bt == "dry" and has_gutshot: return "BET" if tr > 12 else "CHECK"
            if pot == "SRP" and tier == "アンダーペア" and bt == "wet" and tr == 6: return "BET"
            if pot == "SRP" and tier == "2P+" and bt == "wet" and has_none: return "BET" if tr <= 6 else "CHECK"
            if pot == "SRP" and tier == "2P+" and bt == "paired" and has_none: return "BET" if tr <= 5 else "CHECK"
            if pot == "SRP" and tier == "2P+" and bt == "dry" and has_none: return "BET" if tr > 12 else "CHECK"
            if pot == "SRP" and tier == "2P+" and bt == "wet" and has_gutshot: return "BET" if tr <= 6 else "CHECK"
            if pot == "SRP" and tier == "TP+" and bt == "dry" and has_gutshot: return "BET" if tr > 13 else "CHECK"
            # v25: OOP 4BP flop — BB 4bet-call, first to act (refined)
            if pot == "4BP":
                if tier == "TP+":
                    if is_overpair: return "CHECK"   # overpair 25.4% → trap
                    return "BET"                      # top_pair 64.3%
                if tier == "アンダーペア":
                    if is_low_pair: return "CHECK"    # low_pair 24.0%
                    if mv == "underpair":
                        if bt == "dry": return "BET"  # dry 53.2%
                        return "CHECK"                # wet 47.8% / paired 41.6%
                    return "BET"                      # second/third pair 60-77%
                if tier == "エア":
                    if bt == "dry":
                        # v28: dry×no_made_hand×draw → BET (gutshot 61%, strong 83.2%)
                        if is_no_made and has_any: return "BET"
                        # v28: dry×king_high×strong → BET (71.3%)
                        if is_king_high and has_strong: return "BET"
                        # v28: dry×ace_high×gutshot → CHECK (35.5%), dry×ace_high×none → BET (57.6%)
                        if is_ace_high and has_gutshot: return "CHECK"
                        if is_ace_high: return "BET"
                        return "CHECK"
                    if bt == "paired":
                        if is_ace_high: return "BET"  # paired×ace_high×gutshot 57.6%, none 77.8%
                        return "CHECK"
                    # wet: ace_high×none 48.8% / gutshot 50.7% → borderline CHECK
                    return "CHECK"
                return "CHECK"                        # 2P+ 24.2%
            return "CHECK"
        if pot == "4BP":
            if tier == "2P+": return "CHECK"
            if tier == "TP+":
                if bt == "dry":
                    if is_overpair: return "CHECK"   # v26: overpair 25.1% BET → trap CHECK
                    if has_none or has_gutshot: return "BET" if tr2 > 5 else "CHECK"
                    return "BET" if tr > 7 else "CHECK"
                if bt == "wet" and has_none: return "BET" if tr <= 11 else "CHECK"
                return "BET" if bt != "paired" else "CHECK"
            if tier == "エア":
                if bt == "paired" and has_none and is_ace_high: return "BET"
                if bt == "dry" and has_none: return "BET" if tr2 == 6 else "CHECK"
                if bt == "wet":
                    # v28: king_high×strong = 83.4% BET (was CHECK)
                    if is_king_high and has_strong: return "BET"
                    if has_strong or has_gutshot: return "CHECK"
                    return "BET" if tr <= 10 else "CHECK"
                if bt == "paired" and has_none: return "BET" if tr > 12 else "CHECK"
            if tier == "アンダーペア":
                if bt == "wet" and has_none and is_second_pair: return "BET"
                if bt == "wet" and has_none: return "CHECK"
                if bt == "dry" and has_none and is_low_pair: return "CHECK"
                if mv == "underpair": return "CHECK"  # v26: underpair 42.7% dry / 36.2% paired
                return "BET"
            return "CHECK"
        if tier == "2P+": return "BET"
        if pot == "3BP":
            if tier == "TP+":
                if bt == "wet" and has_none: return "BET" if tr <= 9 else "CHECK"
                return "BET"
            if tier == "アンダーペア":
                if bt == "dry" and has_gutshot: return "BET" if tr > 11 else "CHECK"
                if bt == "paired" and has_gutshot: return "BET"
            if tier == "エア":
                if bt == "paired": return "CHECK"
                if bt == "dry" and has_none and tr <= 7: return "BET"
            return "CHECK"
        if tier == "TP+":
            if bt == "dry":
                if has_none and tr == 8: return "CHECK"
                return "BET"
            if bt == "paired":
                if has_none: return "BET" if tr <= 12 else "CHECK"
                return "BET"
            if bt == "wet":
                if has_strong: return "BET" if tr > 5 else "CHECK"
                if has_none: return "BET" if (8 < tr < 12) else "CHECK"
                return "BET"
            return "CHECK"
        if tier == "アンダーペア":
            if bt == "wet" and has_any: return "CHECK"
            if bt == "paired": return "BET" if tr != 14 else "CHECK"
            if bt == "dry":
                if has_gutshot: return "BET" if tr > 11 else "CHECK"
                if has_none: return "BET" if 12 <= tr <= 13 else "CHECK"
                if has_any: return "BET"
            return "CHECK"
        if bt == "dry":
            if has_gutshot and is_no_made: return "BET"
            if has_gutshot: return "BET" if (8 < tr < 14) else "CHECK"
            if hi: return "BET" if has_strong else "CHECK"
            if has_strong: return "BET"
            return "BET" if tr == 12 else "CHECK"
        if bt == "wet":
            if has_strong: return "BET" if tr > 8 else "CHECK"
            if has_gutshot: return "BET" if tr > 10 else "CHECK"
            if has_none: return "BET" if (tr <= 5 or tr >= 11) else "CHECK"
            return "CHECK"
        if bt == "paired":
            if has_gutshot: return "BET" if (tr <= 10 or tr >= 14) else "CHECK"
            return "BET" if (has_any or (not hi and tr > 4)) else "CHECK"
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
                    if bt == "wet" and has_none: return "CHECK"
                    if bt == "wet": return "BET"
                    if bt == "paired" and is_second_pair: return "CHECK"  # v26: 28.8% BET
                    if bt == "paired" and has_none: return "BET" if (5 < tr < 14) else "CHECK"
                    return "BET"
                if tier == "エア":
                    if bt == "dry":
                        # v23: no_made_hand×gutshot → BET always
                        if has_gutshot and is_no_made: return "BET"
                        if has_gutshot: return "BET" if tr2 > 11 else "CHECK"
                        if has_strong: return "CHECK"
                        # v23: no_made_hand×none → BET always (58.8%)
                        if has_none and is_no_made: return "BET"
                        if has_none: return "BET" if tr2 > 10 else "CHECK"
                        return "CHECK"
                    if bt == "wet":
                        if has_strong: return "CHECK"
                        return "BET"
                    if bt == "paired":
                        if has_strong: return "BET" if tr > 10 else "CHECK"
                        # v23: ace_high×paired×none → BET (69.7%)
                        if has_none and is_ace_high: return "BET"
                        # v26: king_high×paired→BET (56.2%)
                        if has_none and is_king_high: return "BET"
                        return "CHECK"
                return "CHECK"
            if pot == "3BP":
                if tier == "TP+":
                    if bt == "dry": return "BET"
                    if bt == "paired" and has_none: return "CHECK" if tr <= 13 else "BET"
                    if has_gutshot: return "BET"
                    return "CHECK"
                if tier == "2P+":
                    if bt == "dry" and has_none: return "BET" if tr != 10 else "CHECK"
                if tier == "アンダーペア":
                    if bt == "paired" and mv == "underpair": return "CHECK"  # v28: underpair 28.2%
                    if bt == "paired" and has_none: return "BET" if tr > 9 else "CHECK"
                    if bt == "paired" and has_gutshot: return "BET" if tr > 5 else "CHECK"
                    if bt == "dry" and has_none: return "BET" if (10 < tr2 < 13) else "CHECK"
                    # v23: dry×gutshot×second_pair → BET (85%)
                    if bt == "dry" and has_gutshot and is_second_pair: return "BET"
                    return "BET" if bt == "paired" else "CHECK"
                if tier == "エア":
                    if bt == "dry":
                        if has_none: return "BET" if tr <= 8 else "CHECK"
                        if has_strong: return "BET" if (tr <= 8 or tr >= 14) else "CHECK"
                        # v23: gutshot×ace_high → CHECK (12%)
                        if has_gutshot and is_ace_high: return "CHECK"
                        if has_gutshot: return "BET" if (7 < tr2 < 10) else "CHECK"
                    if bt == "wet" and has_strong: return "CHECK"
                    if bt == "wet" and has_gutshot: return "CHECK"
                    if bt == "paired":
                        if has_strong: return "BET" if tr > 9 else "CHECK"
                        if has_none: return "BET" if (5 < tr <= 10) else "CHECK"
                        if has_gutshot: return "BET" if tr > 10 else "CHECK"
                return "CHECK"
            if tier == "TP+":
                if bt == "dry" and has_none: return "BET" if (tr2 <= 7 or tr2 >= 13) else "CHECK"
                return "BET" if has_any else "CHECK"
            if tier == "アンダーペア": return "CHECK"
            return "BET" if has_any else "CHECK"
        else:
            if pot == "SRP":
                if tier == "2P+":
                    if bt == "wet": return "BET" if tr > 9 else "CHECK"
                    if bt == "paired":
                        if has_none: return "BET" if (tr2 <= 11 or tr2 == 14) else "CHECK"
                        return "BET" if tr <= 10 else "CHECK"
                    if bt == "dry" and has_none: return "BET" if (tr2 <= 10 or tr2 >= 13) else "CHECK"
                    return "BET" if bt == "dry" else "CHECK"
                if tier == "TP+":
                    if bt == "wet" and has_none: return "BET" if tr <= 10 else "CHECK"
                    return "CHECK"
                if tier == "エア":
                    if bt == "wet" and has_any: return "BET"
                    if bt == "wet" and has_none: return "BET" if tr2 == 9 else "CHECK"
                    if bt == "paired":
                        if has_strong: return "BET" if tr <= 10 else "CHECK"
                        if has_gutshot: return "BET" if (tr2 <= 9 or tr2 == 14) else "CHECK"
                    if bt == "dry" and has_strong: return "BET" if tr <= 11 else "CHECK"
                return "CHECK"
            if pot == "3BP":
                if tier == "TP+":
                    if bt == "paired" and has_none: return "BET" if (4 < tr2 < 10) else "CHECK"
                    if bt == "paired" and has_gutshot: return "BET" if tr <= 5 else "CHECK"
                    return "BET"
                if tier == "2P+":
                    if bt == "wet": return "BET"
                    if bt == "paired": return "BET" if tr > 6 else "CHECK"
                    if bt == "dry" and has_none: return "BET" if tr2 > 10 else "CHECK"
                if tier == "アンダーペア":
                    if bt == "wet" and is_low_pair: return "CHECK"  # v28: low_pair 18.7%
                    if bt == "wet": return "BET"
                    if bt == "paired" and has_none: return "BET" if (4 < tr2 < 10) else "CHECK"
                if tier == "エア":
                    if has_strong:
                        if bt == "paired": return "BET" if tr <= 10 else "CHECK"
                        return "BET"
                    if bt == "wet" and has_gutshot: return "BET"
                    if bt == "paired":
                        if has_gutshot: return "BET" if (5 < tr <= 10) else "CHECK"
                    # v23: dry×gutshot ace/king_high → CHECK
                    if bt == "dry" and has_gutshot and (is_ace_high or is_king_high): return "CHECK"
                    if bt == "dry" and has_gutshot: return "BET" if tr2 > 8 else "CHECK"
                return "CHECK"
            if pot == "4BP":
                if tier == "TP+":
                    if bt == "wet" and has_none: return "CHECK"
                    if bt == "paired":
                        if has_gutshot: return "BET"
                        return "BET" if tr > 10 else "CHECK"
                    if bt == "dry" and mv == "overpair": return "CHECK"  # v28: overpair 34.7%
                    if bt == "dry" and has_none: return "BET" if tr <= 13 else "CHECK"
                    return "BET"
                if tier == "2P+":
                    if bt == "wet": return "BET"
                    if bt == "paired":
                        if has_none: return "BET" if (5 < tr < 13) else "CHECK"
                        return "BET" if tr > 9 else "CHECK"
                if tier == "アンダーペア":
                    if bt == "dry" and has_any: return "BET"
                    if bt == "dry" and has_none: return "BET" if (5 < tr2 < 8) else "CHECK"
                    if bt == "paired" and has_none: return "BET" if (4 < tr2 < 10) else "CHECK"
                if tier == "エア":
                    if bt == "dry" and has_gutshot: return "BET" if tr <= 9 else "CHECK"
                    if bt == "wet" and has_gutshot: return "BET"
                    if bt == "paired" and has_strong: return "BET" if (5 < tr < 11) else "CHECK"
                return "CHECK"
            return "CHECK"

    else:
        if pos == "IP":
            if tier == "2P+": return "BET"
            if pot == "SRP":
                if tier == "TP+": return "BET" if bt in ("dry","paired") else "CHECK"
                if tier == "アンダーペア":
                    if bt == "paired" and has_none: return "BET" if tr <= 11 else "CHECK"
                    return "BET" if bt == "paired" else "CHECK"
                if tier == "エア":
                    if bt == "paired":
                        if is_king_high: return "CHECK"   # king_high 6.1% BET
                        # v28: ace_high×paired = 98.8% BET → BET (was incorrectly CHECK)
                        return "BET" if tr <= 11 else "CHECK"
                    if bt == "dry":
                        if is_ace_high or is_king_high: return "CHECK"
                        return "BET"
                return "BET"
            if pot == "3BP":
                if tier == "TP+": return "BET"
                if tier == "アンダーペア":
                    # v23: paired×none low_pair → CHECK explicitly
                    if bt == "paired" and has_none and is_low_pair: return "CHECK"
                    if bt == "paired" and has_none: return "BET" if tr > 13 else "CHECK"
                    # v23: dry×none second/third_pair → BET
                    if bt == "dry" and has_none and (is_second_pair or is_third_pair): return "BET"
                if tier == "エア":
                    if bt in ("wet",): return "BET"
                    if bt == "dry":
                        if is_ace_high or is_king_high: return "CHECK"
                        # v23: no_made_hand → BET always (including A-high boards)
                        if is_no_made: return "BET"
                        return "BET" if tr <= 13 else "CHECK"
                    if bt == "paired" and has_none: return "CHECK"
                    return "CHECK"
                return "CHECK"
            if pot == "4BP":
                if tier == "TP+": return "BET"
                if tier == "アンダーペア":
                    if bt == "paired": return "BET" if tr > 11 else "CHECK"
                    return "CHECK"
                if tier == "エア":
                    if bt == "dry":
                        if is_ace_high or is_king_high: return "CHECK"
                        # v23: no_made_hand → BET (tr2 override)
                        if is_no_made and has_none: return "BET"
                        if has_none: return "BET" if tr2 != 9 else "CHECK"
                        return "BET" if tr <= 13 else "CHECK"
                    return "CHECK"
                return "CHECK"
            return "CHECK"
        else:
            if pot == "SRP":
                if tier == "TP+":
                    if bt == "dry" and has_none: return "BET" if tr2 != 9 else "CHECK"
                    return "BET"
                if tier == "2P+":
                    if mv == "set" and has_none: return "CHECK"   # v26: set 43.4% → trap CHECK
                    if bt == "dry" and has_none: return "BET" if tr <= 10 or tr >= 13 else "CHECK"
                    if bt == "paired" and has_none: return "BET" if tr <= 12 else "CHECK"
                    return "BET"
                if tier == "アンダーペア":
                    if bt == "paired":
                        if has_none: return "BET" if (tr <= 9 or tr >= 13) else "CHECK"
                        return "BET" if tr > 12 else "CHECK"
                    if bt == "dry" and mv == "underpair": return "BET"  # v26: underpair 54.4%
                    if bt == "dry" and is_second_pair: return "BET"
                if tier == "エア":
                    if bt == "paired" and is_ace_high: return "CHECK"
                    if bt == "paired": return "BET" if tr <= 12 else "CHECK"
                    if bt == "dry" and has_none: return "BET" if (10 < tr2 < 13) else "CHECK"
                return "CHECK"
            if pot == "3BP":
                if tier == "エア":
                    if bt == "dry" and has_none:
                        if is_ace_high or is_king_high: return "CHECK"
                        if is_no_made: return "BET"
                        return "BET" if (tr2 <= 8 or tr2 >= 11) else "CHECK"
                    if bt in ("dry","paired"): return "CHECK"
                    return "CHECK"
                if tier == "アンダーペア":
                    if bt == "dry":
                        if is_second_pair or is_third_pair: return "BET"
                        # v23: low_pair → CHECK explicitly (includes A-high boards)
                        if is_low_pair: return "CHECK"
                        return "BET" if tr > 13 else "CHECK"
                    if bt == "paired" and has_none and is_low_pair: return "CHECK"
                    if bt == "paired" and has_none: return "BET" if (tr2 <= 5 or tr2 >= 13) else "CHECK"
                if tier == "2P+" and bt == "dry" and mv == "two_pair": return "CHECK"  # v28: two_pair 45.6%
                if tier == "2P+" and bt == "dry" and has_none: return "BET" if tr <= 13 else "CHECK"
                if tier == "2P+" and bt == "paired" and has_none: return "BET" if tr2 <= 10 else "CHECK"
                return "BET"
            if pot == "4BP":
                if tier == "TP+":
                    if bt == "dry" and has_none: return "BET" if tr2 > 8 else "CHECK"
                    if bt == "paired": return "BET" if tr <= 11 else "CHECK"
                if tier == "2P+" and bt == "paired": return "BET" if tr <= 11 else "CHECK"
                if tier == "アンダーペア" and bt == "dry" and has_none: return "BET" if tr2 > 8 else "CHECK"
                if tier == "エア" and bt == "dry" and has_none: return "BET" if tr2 <= 8 else "CHECK"
                if tier == "エア" and bt == "paired" and is_ace_high: return "BET"  # v28: ace_high 91.5%
                return "CHECK" if tier == "エア" else "BET"
            return "CHECK"

df = pd.read_csv(CSV)
df["board_type"] = df["board"].apply(board_type_fixed)
df["dv_grp"] = df["dv_cat"].apply(dv_group)
df["tr"] = df["board"].apply(top_rank)
df["tr2"] = df["board"].apply(second_rank)
df["pred"] = df.apply(predict_v28, axis=1)
df["correct"] = df["pred"] == df["best_action"]
df["pred_bet"] = (df["pred"]=="BET").astype(float)
df["freq_loss"] = (df["bet_pct"]/100 - df["pred_bet"]).abs()
total = df["n_combos"].sum()
acc = float(np.average(df["correct"], weights=df["n_combos"]))*100
avg_loss = float(np.average(df["freq_loss"], weights=df["n_combos"]))*100
score = aqs(avg_loss)

V27_LOSS = 26.7652; V27_AQS = 85.25
print(f"v28: acc={acc:.3f}%  avg_loss={avg_loss:.4f}%  AQS={score:.2f}")
print(f"vs v27: avg_loss {V27_LOSS:.4f}% -> {avg_loss:.4f}% ({avg_loss-V27_LOSS:+.4f}pp)  AQS {V27_AQS} -> {score:.2f} ({score-V27_AQS:+.2f})")

print("\nシナリオ別:")
for (st, pos, pot) in [("flop","IP","SRP"),("flop","IP","3BP"),("flop","IP","4BP"),
                        ("flop","OOP","SRP"),("flop","OOP","3BP"),("flop","OOP","4BP"),
                        ("turn","IP","SRP"),("turn","IP","3BP"),
                        ("turn","IP","4BP"),("turn","OOP","SRP"),("turn","OOP","3BP"),
                        ("turn","OOP","4BP"),("river","IP","SRP"),("river","IP","3BP"),
                        ("river","IP","4BP"),("river","OOP","SRP"),("river","OOP","3BP"),("river","OOP","4BP")]:
    sub = df[(df["street"]==st)&(df["position"]==pos)&(df["pot_type"]==pot)]
    if sub.empty: continue
    a = float(np.average(sub["correct"], weights=sub["n_combos"]))*100
    al = float(np.dot(sub["freq_loss"], sub["n_combos"])) / sub["n_combos"].sum() * 100
    print(f"  {st:5} {pos:3} {pot:3}: acc={a:.1f}%  loss={al:.1f}%")
