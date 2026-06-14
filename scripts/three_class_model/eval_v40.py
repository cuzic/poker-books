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

def predict_v37(row):
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
            # v40: OOP SRP エア wet none ace_high tr2=5 → BET (GTO=72.34%, gain=22.8)
            if pot == "SRP" and tier == "エア" and bt == "wet" and has_none and is_ace_high and tr2 == 5: return "BET"
            # v40: OOP SRP エア wet none king_high tr=5 → CHECK (GTO=39.64%, gain=16.16 — low board K trap)
            if pot == "SRP" and tier == "エア" and bt == "wet" and has_none and is_king_high and tr == 5: return "CHECK"
            if pot == "SRP" and tier == "エア" and bt == "wet" and has_none and tr <= 5: return "BET"
            if pot == "SRP" and tier == "エア" and bt == "wet" and has_strong: return "BET" if tr <= 6 else "CHECK"
            if pot == "SRP" and tier == "エア" and bt == "wet" and has_gutshot: return "BET" if tr == 6 else "CHECK"
            if pot == "SRP" and tier == "TP+" and bt == "wet" and has_gutshot: return "BET" if tr <= 6 else "CHECK"
            if pot == "SRP" and tier == "TP+" and bt == "wet" and has_none and tr == 6: return "BET"
            if pot == "SRP" and tier == "TP+" and bt == "wet" and has_strong and tr == 6: return "BET"
            # v40: OOP SRP アンダーペア dry gutshot third_pair tr2=9 → CHECK (GTO=0.09%, gain=19.96)
            if pot == "SRP" and tier == "アンダーペア" and bt == "dry" and has_gutshot and is_third_pair and tr2 == 9: return "CHECK"
            if pot == "SRP" and tier == "アンダーペア" and bt == "dry" and has_gutshot: return "BET" if tr > 12 else "CHECK"
            if pot == "SRP" and tier == "アンダーペア" and bt == "wet" and tr == 6: return "BET"
            if pot == "SRP" and tier == "2P+" and bt == "wet" and has_none: return "BET" if tr <= 6 else "CHECK"
            if pot == "SRP" and tier == "2P+" and bt == "paired" and has_none: return "BET" if tr <= 5 else "CHECK"
            # v41: flop OOP SRP 2P+ dry none trips → CHECK always (board paired, OOP slow-plays)
            if pot == "SRP" and tier == "2P+" and bt == "dry" and has_none and mv == "trips": return "CHECK"
            if pot == "SRP" and tier == "2P+" and bt == "dry" and has_none: return "BET" if tr > 12 else "CHECK"
            if pot == "SRP" and tier == "2P+" and bt == "wet" and has_gutshot: return "BET" if tr <= 6 else "CHECK"
            if pot == "SRP" and tier == "TP+" and bt == "dry" and has_gutshot: return "BET" if tr > 13 else "CHECK"
            # v25: OOP 4BP flop — BB 4bet-call, first to act (refined)
            if pot == "4BP":
                if tier == "TP+":
                    if is_overpair: return "CHECK"   # overpair 25.4% → trap
                    # v33: wet×top_pair×strong×tr>=9 → CHECK (low tr=7 is 99.9% BET, tr>=9 is 0-33%)
                    if bt == "wet" and mv == "top_pair" and has_strong and tr >= 9: return "CHECK"
                    # v37: wet×top_pair×gutshot → CHECK (GTO=45.8%)
                    # v40: wet×top_pair×gutshot×tr<=7 → BET (GTO=85.95%, gain=27.3 — low boards)
                    if bt == "wet" and mv == "top_pair" and has_gutshot and tr <= 7: return "BET"
                    if bt == "wet" and mv == "top_pair" and has_gutshot: return "CHECK"
                    # v39: wet×top_pair×none×tr=14 → CHECK (GTO=0%, ace board top pair trap)
                    if bt == "wet" and mv == "top_pair" and has_none and tr >= 14: return "CHECK"
                    # v40: dry×top_pair×none×tr=10 → CHECK (GTO=5.4%, gain=89.1)
                    if bt == "dry" and mv == "top_pair" and has_none and tr == 10: return "CHECK"
                    # v40: dry×gutshot×top_pair×tr=10 → CHECK (GTO=0.37%, gain=19.85)
                    if bt == "dry" and mv == "top_pair" and has_gutshot and tr == 10: return "CHECK"
                    return "BET"                      # top_pair 64.3%
                if tier == "アンダーペア":
                    if is_low_pair: return "CHECK"    # low_pair 24.0%
                    if mv == "underpair":
                        if bt == "dry": return "BET"  # dry 53.2%
                        # v40: wet×underpair×none×tr2=7 → BET (GTO=85.9%, gain=25.9)
                        if bt == "wet" and has_none and tr2 == 7: return "BET"
                        return "CHECK"                # wet 47.8% / paired 41.6%
                    # v31: wet×third_pair×strong → CHECK (16.5%)
                    if bt == "wet" and is_third_pair and has_strong: return "CHECK"
                    # v40: wet×third_pair×gutshot×tr2=8,9 → CHECK (GTO=13-26%, gain=27.6+18.45)
                    if bt == "wet" and is_third_pair and has_gutshot and tr2 in (8, 9): return "CHECK"
                    # v40: wet×third_pair×none×tr=9-10 → CHECK (GTO=19-27%), tr=7 → BET (GTO=94.8%)
                    if bt == "wet" and is_third_pair and has_none and (9 <= tr <= 10): return "CHECK"
                    # v33: wet×second_pair×strong×tr=9-12 → CHECK (tr=7: 98.2% BET, tr=13: 98.0% BET)
                    if bt == "wet" and is_second_pair and has_strong and (8 < tr < 13): return "CHECK"
                    return "BET"                      # second/third pair 60-77%
                if tier == "エア":
                    if bt == "dry":
                        # v31: dry×no_made_hand×draw → BET (gutshot 61%, strong 83.2%)
                        # v40: no_made_hand×gutshot×tr=10 → CHECK (GTO=35.1%, gain=39.7)
                        if is_no_made and has_gutshot and tr == 10: return "CHECK"
                        if is_no_made and has_any: return "BET"
                        # v31: dry×king_high×strong → BET (71.3%)
                        if is_king_high and has_strong: return "BET"
                        # v40: king_high×none×tr2=8,9 → BET (GTO=56-58%, gain=26.7+19.6)
                        if is_king_high and has_none and tr2 in (8, 9): return "BET"
                        # v31: dry×ace_high×gutshot → CHECK (35.5%), dry×ace_high×none → BET (57.6%)
                        if is_ace_high and has_gutshot: return "CHECK"
                        # v40: ace_high×none×tr=10 → CHECK (GTO=6.2%, gain=102.6)
                        if is_ace_high and tr == 10: return "CHECK"
                        if is_ace_high: return "BET"
                        return "CHECK"
                    if bt == "paired":
                        if is_ace_high: return "BET"  # paired×ace_high×gutshot 57.6%, none 77.8%
                        # v31: paired×no_made_hand×strong → BET (100%)
                        if is_no_made and has_strong: return "BET"
                        # v40: paired×no_made_hand×gutshot×tr=8 → CHECK (GTO=17.7%, gain=69.8)
                        if is_no_made and has_gutshot and tr == 8: return "CHECK"
                        # v40: paired×no_made_hand×gutshot×tr=4 → BET (GTO=67.1%, gain=44.7)
                        if is_no_made and has_gutshot: return "BET"
                        # v40: paired×king_high×gutshot×tr>=14 → BET (GTO=78.77%, gain=17.26 — A board K bluff)
                        if is_king_high and has_gutshot and tr >= 14: return "BET"
                        # v40: paired×king_high×none×tr2<=4 → BET (GTO=57.29%, gain=17.06 — low paired boards)
                        if is_king_high and has_none and tr2 <= 4: return "BET"
                        return "CHECK"
                    # v37: wet×ace_high×strong → BET (GTO=53.7%)
                    if is_ace_high and has_strong: return "BET"
                    # v40: wet×no_made_hand×strong×tr<=8 → BET (GTO=88.6%, gain=86.4)
                    if bt == "wet" and is_no_made and has_strong and tr <= 8: return "BET"
                    # v40: wet×ace_high×none×tr<=8 → BET (GTO=81.2%, gain=48.7)
                    if bt == "wet" and is_ace_high and has_none and tr <= 8: return "BET"
                    # v40: wet×ace_high×none×tr=13 → BET (GTO=62.24%, gain=26.4 — K-high ace top wet)
                    if bt == "wet" and is_ace_high and has_none and tr == 13: return "BET"
                    # v40: wet×king_high×gutshot×tr<=9 → BET (GTO=66-78%, gain=26.1+15.06 — low wet K bluff)
                    if bt == "wet" and is_king_high and has_gutshot and tr <= 9: return "BET"
                    # wet: ace_high×none 48.8% / gutshot 50.7% → borderline CHECK
                    return "CHECK"
                # v40: 2P+×paired×none×trips×tr>=13 → BET (GTO=60-72% on K/A paired boards)
                if tier == "2P+" and bt == "paired" and has_none and mv == "trips" and tr >= 13: return "BET"
                # v40: 2P+×dry×none×two_pair: tr>=13 → BET (GTO=68.14%, K/A boards), tr=11 → BET (65.1%), tr2=8 → BET (66.7%)
                if tier == "2P+" and bt == "dry" and has_none and mv == "two_pair" and tr >= 13: return "BET"
                if tier == "2P+" and bt == "dry" and has_none and mv == "two_pair" and tr == 11: return "BET"
                if tier == "2P+" and bt == "dry" and has_none and mv == "two_pair" and tr2 == 8: return "BET"
                return "CHECK"                        # 2P+ 24.2%
            # v40: OOP 3BP TP+ dry none top_pair tr<=7 → BET (GTO=60.90%, gain=21.80)
            if pot == "3BP" and tier == "TP+" and bt == "dry" and has_none and tr <= 7: return "BET"
            return "CHECK"
        if pot == "4BP":
            # v40: 2P+×wet×none×two_pair×tr2<=9 → BET (GTO=61-80%, gain=21.9+30.9)
            if tier == "2P+" and bt == "wet" and has_none and mv == "two_pair" and tr2 <= 9: return "BET"
            # v40: IP 4BP 2P+ dry×none×two_pair×tr=11 → BET (GTO=65.12%, gain=15.12 — J-board value bet IP)
            if tier == "2P+" and bt == "dry" and has_none and mv == "two_pair" and tr == 11: return "BET"
            # v40: IP 4BP 2P+ dry×none×two_pair×tr>=13 → CHECK (GTO=23-38%, slowplay K/A boards IP)
            if tier == "2P+" and bt == "dry" and has_none and mv == "two_pair" and tr >= 13: return "CHECK"
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
                # v39: IP 4BP エア dry none no_made_hand tr=12 → BET (GTO=58.0%, Q-high boards)
                if bt == "dry" and has_none and is_no_made and tr == 12: return "BET"
                # v40: dry×ace_high×none×tr=7 → BET (GTO=67.2%, gain=31.3)
                if bt == "dry" and has_none and is_ace_high and tr == 7: return "BET"
                # v40: ace_high×none×tr2=5 → BET (GTO=71.9%, gain=39.8) — specific rule before general
                if bt == "dry" and has_none and is_ace_high and tr2 == 5: return "BET"
                if bt == "dry" and has_none: return "BET" if tr2 == 6 else "CHECK"
                # v31: dry×ace_high×gutshot → BET (54.5%), low boards (tr<=7 or tr2=5) CHECK (GTO=8/14%)
                if bt == "dry" and is_ace_high and has_gutshot and (tr <= 7 or tr2 == 5): return "CHECK"
                if bt == "dry" and is_ace_high and has_gutshot: return "BET"
                # v40: dry×no_made_hand×gutshot×tr2=5 → BET (GTO=57.57%, gain=19.22 — low boards)
                if bt == "dry" and is_no_made and has_gutshot and tr2 == 5: return "BET"
                # v40: dry×king_high×gutshot×tr=14 → BET (GTO=71.3%, ace board K-high semi-bluff)
                if bt == "dry" and is_king_high and has_gutshot and tr >= 14: return "BET"
                if bt == "wet":
                    # v28: king_high×strong = 83.4% BET
                    if is_king_high and has_strong: return "BET"
                    # v37: king_high×none → CHECK (GTO=40.3% on wet boards)
                    if is_king_high and has_none: return "CHECK"
                    # v31: ace_high×strong = 67.4% BET
                    # v40: wet×ace_high×strong×tr>=13 → CHECK (GTO=22.74%, gain=17.99 — K/A board trap)
                    if is_ace_high and has_strong and tr >= 13: return "CHECK"
                    if is_ace_high and has_strong: return "BET"
                    # v40: wet×ace_high×gutshot×tr2=9 → BET (GTO=61.77%, gain=24.25)
                    if is_ace_high and has_gutshot and tr2 == 9: return "BET"
                    if has_strong or has_gutshot: return "CHECK"
                    # v40: wet×ace_high×none×tr=10 → CHECK (GTO=33.24%, gain=26.15 — T-high wet ace)
                    if is_ace_high and has_none and tr == 10: return "CHECK"
                    return "BET" if tr <= 10 else "CHECK"
                # v40: raise threshold 12→13 (no_made_hand×tr=13 GTO=45.7% → CHECK)
                if bt == "paired" and has_none: return "BET" if tr > 13 else "CHECK"
                # v40: paired×gutshot×ace_high×tr2=13 → BET (GTO=86.36%, gain=21.82 — K-board ace gutshot)
                if bt == "paired" and has_gutshot and is_ace_high and tr2 >= 13: return "BET"
                # (v33 reverted: paired×ace_high×gutshot bimodal — gutshot 5.9% vs twocards_bdfd 87%)
            if tier == "アンダーペア":
                # v40: wet×second_pair×none×tr>=13 → CHECK (GTO=29.4%, K/A boards)
                if bt == "wet" and is_second_pair and has_none and tr >= 13: return "CHECK"
                # v40: wet×second_pair×none×tr=11 → CHECK (GTO=39.26%, gain=17.18 — J boards)
                if bt == "wet" and is_second_pair and has_none and tr == 11: return "CHECK"
                if bt == "wet" and has_none and is_second_pair: return "BET"
                if bt == "wet" and has_none: return "CHECK"
                # v31: wet×low_pair×gutshot → CHECK (2.4%)
                if bt == "wet" and is_low_pair and has_gutshot: return "CHECK"
                if bt == "dry" and has_none and is_low_pair: return "CHECK"
                # v33: paired×third_pair×none → CHECK (GTO=31.6%)
                if bt == "paired" and is_third_pair and has_none: return "CHECK"
                # v32: wet×underpair×draw → BET (83-100% GTO)
                if bt == "wet" and mv == "underpair" and has_any: return "BET"
                if mv == "underpair": return "CHECK"  # v26: underpair 42.7% dry / 36.2% paired
                return "BET"
            return "CHECK"
        # v31: 3BP×fullhouse×paired = 1.1% BET → trap CHECK (SRP=82.8% → BET so restrict to 3BP)
        if pot == "3BP" and mv == "fullhouse" and bt == "paired": return "CHECK"
        # v31: 3BP×wet×set = 33.6% BET → CHECK (trap)
        if pot == "3BP" and mv == "set" and bt == "wet": return "CHECK"
        # v37: 3BP×dry×set×none = 45.1% BET → CHECK (trap IP dry board set)
        # v40: except tr=11 (J boards) GTO=88.37% → BET
        if pot == "3BP" and mv == "set" and bt == "dry" and has_none and tr == 11: return "BET"
        if pot == "3BP" and mv == "set" and bt == "dry" and has_none: return "CHECK"
        if tier == "2P+": return "BET"
        if pot == "3BP":
            if tier == "TP+":
                # v40: wet×overpair×none → BET (GTO=96-99%, overrides wet none trap rule)
                if bt == "wet" and mv == "overpair" and has_none: return "BET"
                # v40: wet×none threshold 9→8 (tr=9 top_pair GTO=40.7% → CHECK)
                if bt == "wet" and has_none: return "BET" if tr <= 8 else "CHECK"
                return "BET"
            if tier == "アンダーペア":
                if bt == "dry" and has_gutshot: return "BET" if tr > 11 else "CHECK"
                if bt == "paired" and has_gutshot: return "BET"
                # v40: dry×underpair×none×tr=6-9 → BET (GTO=52-78%、probe確認: 6=52%,7=78%,8=66%,9=54%)
                if bt == "dry" and mv == "underpair" and has_none and 6 <= tr <= 9: return "BET"
                # v31: wet×second_pair×strong → BET (77.6%)
                if bt == "wet" and is_second_pair and has_strong: return "BET"
                # v31: paired×underpair → BET (67.1%)
                if bt == "paired" and mv == "underpair": return "BET"
            if tier == "エア":
                if bt == "paired": return "CHECK"
                # v40: ace/king high dry none → always CHECK (GTO=10-34% across all tr)
                if bt == "dry" and has_none and (is_ace_high or is_king_high): return "CHECK"
                # v40: IP 3BP エア dry none — extend BET to tr<=9 and Q boards (tr=12)
                if bt == "dry" and has_none and (tr <= 9 or tr == 12): return "BET"
                # v37: dry×king_high×strong → BET (53.5%)
                if bt == "dry" and is_king_high and has_strong: return "BET"
                # v40: dry×gutshot×ace_high×tr2=11 → BET (GTO=61.75%, gain=24.9)
                if bt == "dry" and has_gutshot and is_ace_high and tr2 == 11: return "BET"
                # v40: wet×gutshot×no_made_hand×tr2=7 → BET (GTO=59.5%, gain=54.8)
                if bt == "wet" and has_gutshot and is_no_made and tr2 == 7: return "BET"
            return "CHECK"
        if tier == "TP+":
            if bt == "dry":
                # v40: dry×none×overpair×tr=8 → BET (GTO=73.0%, gain=33.2)
                if has_none and tr == 8 and mv == "overpair": return "BET"
                if has_none and tr == 8: return "CHECK"
                # v40: dry×none×top_pair×tr2=8 → CHECK (GTO=40.8%, gain=20.6 — 8 as second board card)
                if has_none and mv == "top_pair" and tr2 == 8: return "CHECK"
                return "BET"
            if bt == "paired":
                if has_none: return "BET" if tr <= 12 else "CHECK"
                return "BET"
            if bt == "wet":
                if has_strong: return "BET" if tr > 5 else "CHECK"
                if has_none: return "BET" if (8 < tr < 12) else "CHECK"
                # v40: wet×gutshot×top_pair×tr=10 → CHECK (GTO=43.54%, gain=23.39 — T-high connected)
                if has_gutshot and mv == "top_pair" and tr == 10: return "CHECK"
                return "BET"
            return "CHECK"
        if tier == "アンダーペア":
            # v32: underpair×wet×draw → BET (SRP 75%, v31 wet×has_any→CHECK overrides)
            if bt == "wet" and mv == "underpair" and has_any: return "BET"
            if bt == "wet" and has_any: return "CHECK"
            if bt == "paired": return "BET" if tr != 14 else "CHECK"
            if bt == "dry":
                if has_gutshot: return "BET" if tr > 11 else "CHECK"
                if has_none: return "BET" if 12 <= tr <= 13 else "CHECK"
                if has_any: return "BET"
            return "CHECK"
        if bt == "dry":
            if has_gutshot and is_no_made: return "BET"
            # v38: ace_high+dry+gutshot — low boards (tr<12) CHECK (GTO=14-24%), high boards BET
            if has_gutshot and is_ace_high: return "BET" if tr >= 12 else "CHECK"
            if has_gutshot: return "BET" if (8 < tr < 14) else "CHECK"
            # v40: no_made_hand×none×tr2=9 → BET (GTO=77.0%, gain=53.5) — BEFORE hi check
            if is_no_made and has_none and tr2 == 9: return "BET"
            # v40: no_made_hand×none×tr2=6 → BET (GTO=57.35%, gain=18.95 — low boards)
            if is_no_made and has_none and tr2 == 6: return "BET"
            # v40: king_high×none×tr2=8,9 → BET (GTO=60-67%, gain=35.0+17.11 — 8/9 second card boards)
            if is_king_high and has_none and tr2 in (8, 9): return "BET"
            if hi: return "BET" if has_strong else "CHECK"
            if has_strong: return "BET"
            return "BET" if tr == 12 else "CHECK"
        if bt == "wet":
            # v38: ace_high+wet+strong+tr=10 → CHECK (GTO=47.3% — T-high connected boards)
            if has_strong and is_ace_high and tr == 10: return "CHECK"
            # v40: wet×strong×king_high×tr2=4 → BET (GTO=67.12%, gain=21.91 — low connected boards)
            if has_strong and is_king_high and tr2 == 4: return "BET"
            if has_strong: return "BET" if tr > 8 else "CHECK"
            # v38: ace_high+wet+none — only J-high (tr=11) is BET, Q/K/A boards CHECK (37%)
            if has_none and is_ace_high: return "BET" if tr == 11 else "CHECK"
            # v38: king_high+wet+none — BET only J-K boards; low (tr=5) and ace boards CHECK
            if has_none and is_king_high: return "BET" if (11 <= tr <= 13) else "CHECK"
            if has_gutshot: return "BET" if tr > 10 else "CHECK"
            if has_none: return "BET" if (tr <= 5 or tr >= 11) else "CHECK"
            return "CHECK"
        if bt == "paired":
            # v38: king_high+paired — low boards (tr<9) CHECK, mid/high boards BET
            if is_king_high: return "BET" if tr >= 9 else "CHECK"
            # v40: paired×gutshot×ace_high×tr2=13 → BET (GTO=58.28%, gain=24.85 — K-K boards)
            if has_gutshot and is_ace_high and tr2 >= 13: return "BET"
            if has_gutshot: return "BET" if (tr <= 10 or tr >= 14) else "CHECK"
            # v40: ace_high×paired — fix v39 regression (tr=4,7 GTO=43-44% should be CHECK)
            if is_ace_high and has_none: return "BET" if (9 <= tr <= 12) else "CHECK"
            # v39: tr>=4 fix (no_made_hand×tr=4 GTO=56.5% → BET)
            return "BET" if (has_any or (not hi and tr >= 4)) else "CHECK"
        return "CHECK"

    elif street == "turn":
        if pos == "IP":
            if tier == "2P+":
                if pot == "3BP" and bt == "wet" and has_none: return "CHECK"
                # v40: 3BP×dry×none×two_pair×tr=10 → CHECK (GTO=36.53%, gain=14.55 — T board two pair trap)
                if pot == "3BP" and bt == "dry" and has_none and mv == "two_pair" and tr == 10: return "CHECK"
                # v37: 4BP×dry×straight×none → CHECK (GTO=35.6% — slowplay)
                if pot == "4BP" and bt == "dry" and mv == "straight" and has_none: return "CHECK"
                if pot == "4BP" and bt == "dry" and has_none: return "BET" if tr > 8 else "CHECK"
                # v31: 4BP×wet×two_pair → CHECK (37.3%)
                if pot == "4BP" and bt == "wet" and mv == "two_pair": return "CHECK"
                return "BET"
            if pot == "4BP":
                if tier == "TP+":
                    # v37: paired×overpair×none → CHECK (GTO=48.7% — borderline trap)
                    if bt == "paired" and mv == "overpair" and has_none: return "CHECK"
                    if bt == "paired" and has_none: return "BET" if tr > 7 else "CHECK"
                    # v33: wet×overpair×strong → CHECK (GTO=28.2% — overpair trap on connected wet)
                    if bt == "wet" and mv == "overpair" and has_strong: return "CHECK"
                    return "BET"
                if tier == "アンダーペア":
                    # v31: wet×third_pair×none → BET (64.8%)
                    if bt == "wet" and is_third_pair and has_none: return "BET"
                    if bt == "wet" and has_none: return "CHECK"
                    # v32: wet×second_pair×strong → CHECK (GTO=6.6%)
                    if bt == "wet" and is_second_pair and has_strong: return "CHECK"
                    if bt == "wet": return "BET"
                    if bt == "paired" and is_second_pair: return "CHECK"  # v26: 28.8% BET
                    if bt == "paired" and has_none: return "BET" if (5 < tr < 14) else "CHECK"
                    # v40: dry×low_pair×none — bimodal: tr=10,13,14 BET, others CHECK
                    # v40: tr2=9 → CHECK (GTO=7.6%, gain=147.5) — overrides tr rule
                    if bt == "dry" and is_low_pair and has_none and tr2 == 9: return "CHECK"
                    if bt == "dry" and is_low_pair and has_none and tr in (10, 13, 14): return "BET"
                    if bt == "dry" and is_low_pair and has_none: return "CHECK"
                    # v40: dry×(second/third)_pair×none×tr2=11 → CHECK (GTO=28-38%, gain=54.2+26.4)
                    if bt == "dry" and (is_second_pair or is_third_pair) and has_none and tr2 == 11: return "CHECK"
                    return "BET"
                if tier == "エア":
                    if bt == "dry":
                        # v23: no_made_hand×gutshot → BET always (except tr=11 GTO=25.5%)
                        if has_gutshot and is_no_made and tr == 11: return "CHECK"
                        # v40: no_made_hand×gutshot×tr2=11 → CHECK (GTO=12.9%, gain=35.7)
                        if has_gutshot and is_no_made and tr2 == 11: return "CHECK"
                        # v40: no_made_hand×gutshot×tr2=10 → CHECK (GTO=23.4%, gain=25.7)
                        if has_gutshot and is_no_made and tr2 == 10: return "CHECK"
                        if has_gutshot and is_no_made: return "BET"
                        # v40: ace_high×gutshot×tr2=11 → BET (GTO=99.9%, gain=32.0)
                        if has_gutshot and is_ace_high and tr2 == 11: return "BET"
                        # v40: IP 4BP dry×gutshot×king_high×tr2=10×tr>11 → BET (GTO=67.96% — K/A-T boards only, not J-T)
                        if has_gutshot and is_king_high and tr2 == 10 and tr > 11: return "BET"
                        if has_gutshot: return "BET" if tr2 > 11 else "CHECK"
                        # v40: IP 4BP dry×strong×king_high×tr=9 → BET (GTO=95.90%, gain=14.69 — low board K blocker)
                        if has_strong and is_king_high and tr == 9: return "BET"
                        if has_strong: return "CHECK"
                        # v23: no_made_hand×none → BET always (58.8%)
                        # v40: no_made_hand×none×tr2=7 → CHECK (GTO=38.2%, gain=79.4)
                        if has_none and is_no_made and tr2 == 7: return "CHECK"
                        if has_none and is_no_made: return "BET"
                        # v40: ace_high×none×tr=10 → BET (GTO=99.6%, T-high board)
                        if has_none and is_ace_high and tr == 10: return "BET"
                        if has_none: return "BET" if tr2 > 10 else "CHECK"
                        return "CHECK"
                    if bt == "wet":
                        # v32: king_high×strong → BET (GTO=87.5%), king_high×gutshot → CHECK (35.4%)
                        if is_king_high and has_strong: return "BET"
                        if is_king_high and has_gutshot: return "CHECK"
                        if has_strong: return "CHECK"
                        return "BET"
                    if bt == "paired":
                        if has_strong: return "BET" if tr > 10 else "CHECK"
                        # v23: ace_high×paired×none → BET (69.7%)
                        if has_none and is_ace_high: return "BET"
                        # v26: king_high×paired→BET (56.2%), but low boards (tr<=5) GTO=0.09%
                        if has_none and is_king_high and tr <= 5: return "CHECK"
                        if has_none and is_king_high: return "BET"
                        # v31: king_high×paired×gutshot → BET (86.2%)
                        if is_king_high and has_gutshot: return "BET"
                        # v31: ace_high×paired×gutshot → BET (58.0%), low boards (tr<=5) CHECK
                        if is_ace_high and has_gutshot and tr <= 5: return "CHECK"
                        if is_ace_high and has_gutshot: return "BET"
                        # v40: paired×none×no_made_hand×tr=11 → BET (GTO=53.52%, gain=25.9)
                        if has_none and is_no_made and tr == 11: return "BET"
                        return "CHECK"
                return "CHECK"
            if pot == "3BP":
                if tier == "TP+":
                    if bt == "dry": return "BET"
                    # v40: paired×none×top_pair×tr=10 → BET (GTO=58.17%, gain=21.08)
                    if bt == "paired" and has_none and mv == "top_pair" and tr == 10: return "BET"
                    # v40: paired×none×overpair×tr<=5 → BET (GTO=67.58%, gain=14.77 — low board overpair bet)
                    if bt == "paired" and has_none and mv == "overpair" and tr <= 5: return "BET"
                    if bt == "paired" and has_none: return "CHECK" if tr <= 13 else "BET"
                    # v32: wet×overpair×gutshot → CHECK (GTO=2.12%) — overpair loses vs draws on wet
                    if bt == "wet" and mv == "overpair" and has_gutshot: return "CHECK"
                    if has_gutshot: return "BET"
                    # v32: paired×has_strong → BET (GTO=99.9% e.g. 4s4d2c5h top_pair oesd)
                    if bt == "paired" and has_strong: return "BET"
                    return "CHECK"
                if tier == "2P+":
                    if bt == "dry" and has_none: return "BET" if tr != 10 else "CHECK"
                if tier == "アンダーペア":
                    # v32: paired×underpair×gutshot → BET (GTO=99.5% — paired board underpair+draw)
                    if bt == "paired" and mv == "underpair" and has_gutshot: return "BET"
                    if bt == "paired" and mv == "underpair": return "CHECK"  # v31: underpair 28.2%
                    # v32: paired×second_pair×none → CHECK (GTO=37.5%)
                    if bt == "paired" and is_second_pair and has_none: return "CHECK"
                    if bt == "paired" and has_none: return "BET" if tr > 9 else "CHECK"
                    if bt == "paired" and has_gutshot: return "BET" if tr > 5 else "CHECK"
                    # v40: dry×none×low_pair×tr2>=13 → BET (GTO=70.3%, gain=111.9)
                    if bt == "dry" and has_none and is_low_pair and tr2 >= 13: return "BET"
                    # v40: dry×second_pair×none×tr2=11 → CHECK (GTO=28.2%, gain=47.2)
                    if bt == "dry" and has_none and is_second_pair and tr2 == 11: return "CHECK"
                    if bt == "dry" and has_none: return "BET" if (10 < tr2 < 13) else "CHECK"
                    # v23: dry×gutshot×second_pair → BET (85%)
                    if bt == "dry" and has_gutshot and is_second_pair: return "BET"
                    # v31: dry×strong×second_pair → BET (99.8%)
                    if bt == "dry" and has_strong and is_second_pair: return "BET"
                    # v32: dry×underpair×gutshot → BET (GTO=99.9%)
                    if bt == "dry" and mv == "underpair" and has_gutshot: return "BET"
                    return "BET" if bt == "paired" else "CHECK"
                if tier == "エア":
                    if bt == "dry":
                        # v40: dry×none×no_made_hand×tr=9,10,11 → BET (GTO=53-89%)
                        if has_none and is_no_made and tr in (9, 10, 11): return "BET"
                        # v40: dry×none×king_high×tr<=8 → CHECK (GTO=22.2%)
                        if has_none and is_king_high and tr <= 8: return "CHECK"
                        if has_none: return "BET" if tr <= 8 else "CHECK"
                        # v31: ace_high×strong → CHECK (8.6%)
                        if has_strong and is_ace_high: return "CHECK"
                        # v40: strong×no_made_hand×tr2=9 → BET (GTO=61.5%, gain=25.7)
                        if has_strong and is_no_made and tr2 == 9: return "BET"
                        # v40: strong×no_made_hand×tr=10 → BET (GTO=66.38%, gain=26.2 — T-high boards)
                        if has_strong and is_no_made and tr == 10: return "BET"
                        if has_strong: return "BET" if (tr <= 8 or tr >= 14) else "CHECK"
                        # v23: gutshot×ace_high → CHECK (12%)
                        # v40: gutshot×ace_high×tr2=11 → BET (GTO=99.2%, gain=31.5 — J on board with gutshot)
                        if has_gutshot and is_ace_high and tr2 == 11: return "BET"
                        if has_gutshot and is_ace_high: return "CHECK"
                        # v37: gutshot×king_high → CHECK (22.3%)
                        # v40: gutshot×king_high×tr=8 → BET (GTO=99.11%, gain=15.72 — low board K bluff)
                        if has_gutshot and is_king_high and tr == 8: return "BET"
                        if has_gutshot and is_king_high: return "CHECK"
                        # v40: gutshot×no_made_hand×tr=8 → BET (GTO=73.8%, gain=30.4)
                        if has_gutshot and is_no_made and tr == 8: return "BET"
                        if has_gutshot: return "BET" if (7 < tr2 < 10) else "CHECK"
                    if bt == "wet" and has_strong: return "CHECK"
                    if bt == "wet" and has_gutshot: return "CHECK"
                    if bt == "paired":
                        if has_strong: return "BET" if tr > 9 else "CHECK"
                        # v40: paired×none ace/king high ≥13 → BET (GTO=57-71%)
                        if has_none and (is_ace_high or is_king_high) and tr >= 13: return "BET"
                        # v40: paired×none×no_made_hand×tr=5 → BET (GTO=62%)
                        if has_none and is_no_made and tr == 5: return "BET"
                        if has_none: return "BET" if (5 < tr <= 10) else "CHECK"
                        # v37: no_made_hand+gutshot: low/ace boards BET, mid-range CHECK
                        if has_gutshot and is_no_made: return "BET" if (tr <= 5 or tr >= 14) else "CHECK"
                        if has_gutshot: return "BET" if tr > 10 else "CHECK"
                return "CHECK"
            if tier == "TP+":
                # v37: overpair×dry×none → BET (GTO=89%, tr2 8-12 was incorrectly CHECK)
                if bt == "dry" and mv == "overpair" and has_none: return "BET"
                # v40: dry×none×top_pair×tr2=7 → CHECK (GTO=48.23%, gain=16.92 — 7-card second rank, TP weak)
                if bt == "dry" and has_none and mv == "top_pair" and tr2 == 7: return "CHECK"
                if bt == "dry" and has_none: return "BET" if (tr2 <= 7 or tr2 >= 13) else "CHECK"
                return "BET" if has_any else "CHECK"
            if tier == "アンダーペア":
                # v32: dry×underpair×gutshot → BET (GTO=67.2% avg over 3 boards)
                if bt == "dry" and mv == "underpair" and has_gutshot: return "BET"
                # v40: SRP dry×none×low_pair×tr2>=13 → CHECK (GTO=39.91%, gain=16.95 — SRP K second card)
                if pot == "SRP" and bt == "dry" and has_none and is_low_pair and tr2 >= 13: return "CHECK"
                # v40: dry×none×low_pair×tr2>=13 → BET (GTO=70.3%, gain=111.9 — 3BP/4BP)
                if bt == "dry" and has_none and is_low_pair and tr2 >= 13: return "BET"
                return "CHECK"
            if tier == "エア":
                # v40: dry×gutshot×no_made_hand×tr2=11 → CHECK (GTO=26.69%, gain=18.18 — J board gutshot)
                if bt == "dry" and has_gutshot and is_no_made and tr2 == 11: return "CHECK"
            return "BET" if has_any else "CHECK"
        else:
            if pot == "SRP":
                if tier == "2P+":
                    # v40: wet×none×two_pair×tr2=10 → CHECK (GTO=29.63%, gain=21.99)
                    if bt == "wet" and has_none and mv == "two_pair" and tr2 == 10: return "CHECK"
                    if bt == "wet": return "BET" if tr > 9 else "CHECK"
                    if bt == "paired":
                        if has_none: return "BET" if (tr2 <= 11 or tr2 == 14) else "CHECK"
                        return "BET" if tr <= 10 else "CHECK"
                    # v41: dry×none×trips — tr==tr2(top card paired)→CHECK(trap); AK board K pairs→CHECK
                    if bt == "dry" and has_none and mv == "trips":
                        if tr == 14 and tr2 == 13: return "CHECK"   # A-K board + K pairs → FH-crushed
                        if tr == tr2: return "CHECK"                  # top card paired → slow-play
                        return "BET"                                  # lower card paired → value
                    if bt == "dry" and has_none: return "BET" if (tr2 <= 10 or tr2 >= 13) else "CHECK"
                    return "BET" if bt == "dry" else "CHECK"
                if tier == "TP+":
                    if bt == "wet" and has_none: return "BET" if tr <= 10 else "CHECK"
                    # v31: paired×overpair → BET (92.1%)
                    if bt == "paired" and mv == "overpair": return "BET"
                    # v32: dry×overpair×strong → BET (GTO=99.9% — JdTs9c2c overpair oesd)
                    if bt == "dry" and mv == "overpair" and has_strong: return "BET"
                    # v32: wet×overpair×gutshot → BET (GTO=64.1%)
                    if bt == "wet" and mv == "overpair" and has_gutshot: return "BET"
                    return "CHECK"
                if tier == "エア":
                    if bt == "wet" and has_any: return "BET"
                    if bt == "wet" and has_none: return "BET" if tr2 == 9 else "CHECK"
                    if bt == "paired":
                        if has_strong: return "BET" if tr <= 10 else "CHECK"
                        # v40: paired×gutshot×ace_high×tr=10 → CHECK (GTO=8.01%, gain=26.87 — T board)
                        if has_gutshot and is_ace_high and tr == 10: return "CHECK"
                        if has_gutshot: return "BET" if (tr2 <= 9 or tr2 == 14) else "CHECK"
                    if bt == "dry" and has_strong: return "BET" if tr <= 11 else "CHECK"
                if tier == "アンダーペア":
                    # v31: paired×second_pair×strong → BET (98.2%)
                    if bt == "paired" and is_second_pair and has_strong: return "BET"
                    # v40: dry×gutshot×third_pair×tr2=13 → BET (GTO=81.2%, gain=36.1)
                    if bt == "dry" and has_gutshot and is_third_pair and tr2 == 13: return "BET"
                    # v40: wet×none×second_pair×tr=10 → BET (GTO=62.12%, gain=18.67 — T board second pair)
                    if bt == "wet" and has_none and is_second_pair and tr == 10: return "BET"
                return "CHECK"
            if pot == "3BP":
                if tier == "TP+":
                    # v31: overpair×paired → BET (62.1%)
                    if bt == "paired" and mv == "overpair": return "BET"
                    # v40: paired×none×top_pair×tr=10 → BET (GTO=66%, gain=41.3)
                    if bt == "paired" and has_none and mv == "top_pair" and tr == 10: return "BET"
                    if bt == "paired" and has_none: return "BET" if (4 < tr2 < 10) else "CHECK"
                    if bt == "paired" and has_gutshot: return "BET" if tr <= 5 else "CHECK"
                    # v37: paired×has_strong → CHECK (GTO=35.1% e.g. 4s4d2c5h top_pair oesd)
                    if bt == "paired" and has_strong: return "CHECK"
                    return "BET"
                if tier == "2P+":
                    if bt == "wet": return "BET"
                    if bt == "paired":
                        # v33: trips×strong: low board → BET (4s4d2c5h 97.8%), high board → CHECK
                        if mv == "trips" and has_strong: return "BET" if tr <= 6 else "CHECK"
                        return "BET" if tr > 6 else "CHECK"
                    # v41: dry×none×trips — tr==tr2(top card paired)→CHECK(trap), AK board K pairs→CHECK
                    if bt == "dry" and has_none and mv == "trips":
                        if tr == 14 and tr2 == 13: return "CHECK"   # A-K board + K pairs → crushed
                        if tr == tr2: return "CHECK"                  # top card paired → slow-play
                        return "BET"                                  # lower card paired → value
                    if bt == "dry" and has_none: return "BET" if tr2 > 10 else "CHECK"
                if tier == "アンダーペア":
                    if bt == "wet" and is_low_pair: return "CHECK"  # v31: low_pair 18.7%
                    # v33/v37: wet×third_pair×strong → CHECK (GTO=38.2%) — fix ordering vs wet→BET
                    if bt == "wet" and is_third_pair and has_strong: return "CHECK"
                    if bt == "wet": return "BET"
                    # v40: paired×none×third_pair×tr=10 → BET (GTO=80%, gain=75.6)
                    if bt == "paired" and has_none and is_third_pair and tr == 10: return "BET"
                    if bt == "paired" and has_none: return "BET" if (4 < tr2 < 10) else "CHECK"
                    # v33: dry×second_pair×strong×low board → BET (tr<=9: 59-99%, tr>=11: 0.7-18%)
                    if bt == "dry" and is_second_pair and has_strong and tr <= 10: return "BET"
                    # v33: dry×underpair×gutshot×low board → BET (tr=8: 99.9%, tr=13: 16.2%)
                    if bt == "dry" and mv == "underpair" and has_gutshot and tr <= 10: return "BET"
                if tier == "エア":
                    if has_strong:
                        # v40: paired×strong×king_high → CHECK (GTO=0.08%, gain=15.97 — K-high no bet on paired OOP 3BP)
                        if bt == "paired" and is_king_high: return "CHECK"
                        if bt == "paired": return "BET" if tr <= 10 else "CHECK"
                        # v31: dry×ace_high×strong → CHECK (8.6%)
                        if bt == "dry" and is_ace_high: return "CHECK"
                        # v37: dry×king_high×strong → CHECK (45.4%)
                        if bt == "dry" and is_king_high: return "CHECK"
                        # v31: wet×ace_high×strong → CHECK (0.6%)
                        if bt == "wet" and is_ace_high: return "CHECK"
                        return "BET"
                    # v31: wet×ace_high×gutshot → CHECK (0.8%)
                    if bt == "wet" and has_gutshot and is_ace_high: return "CHECK"
                    if bt == "wet" and has_gutshot: return "BET"
                    if bt == "paired":
                        if has_gutshot: return "BET" if (5 < tr <= 10) else "CHECK"
                        # v40: paired×none×ace/king_high×tr=10 → BET (GTO=88.6%/73.4%)
                        if has_none and (is_ace_high or is_king_high) and tr == 10: return "BET"
                        # v40: paired×none×ace_high×tr2=7 → BET (GTO=72.8%, gain=65.8)
                        if has_none and is_ace_high and tr2 == 7: return "BET"
                    # v23: dry×gutshot ace/king_high → CHECK
                    # v40: dry×gutshot×king_high×tr=8 → BET (GTO=99.2%, gain=15.74 — low board K semi-bluff)
                    if bt == "dry" and has_gutshot and is_king_high and tr == 8: return "BET"
                    if bt == "dry" and has_gutshot and (is_ace_high or is_king_high): return "CHECK"
                    # v40: dry×gutshot×no_made_hand×tr2=7 → BET (GTO=98.7%, gain=62.3) — before tr==13
                    if bt == "dry" and has_gutshot and is_no_made and tr2 == 7: return "BET"
                    # v40: dry×gutshot×no_made_hand×tr=13 → CHECK, tr=10 → BET (GTO=73%)
                    if bt == "dry" and has_gutshot and is_no_made and tr == 13: return "CHECK"
                    if bt == "dry" and has_gutshot and is_no_made and tr == 10: return "BET"
                    # v40: dry×gutshot×no_made_hand×tr2=5 → BET (GTO=65.5%, gain=19.84 — low boards)
                    if bt == "dry" and has_gutshot and is_no_made and tr2 == 5: return "BET"
                    if bt == "dry" and has_gutshot: return "BET" if tr2 > 8 else "CHECK"
                return "CHECK"
            if pot == "4BP":
                if tier == "TP+":
                    # v32: wet×overpair → BET (GTO=93.1% e.g. 9s8d6cTh overpair no_draw)
                    if bt == "wet" and mv == "overpair": return "BET"
                    if bt == "wet" and has_none: return "CHECK"
                    if bt == "paired":
                        if has_gutshot: return "BET"
                        # v32: paired×has_strong → BET (GTO=95.8% e.g. 4s4d2c5h top_pair oesd)
                        if has_strong: return "BET"
                        return "BET" if tr > 10 else "CHECK"
                    if bt == "dry" and mv == "overpair": return "CHECK"  # v31: overpair 34.7%
                    # v40: dry×none×top_pair×tr2=11 → CHECK (GTO=38.66%, gain=24.5 — J as second card)
                    if bt == "dry" and has_none and mv == "top_pair" and tr2 == 11: return "CHECK"
                    if bt == "dry" and has_none: return "BET" if tr <= 13 else "CHECK"
                    # v32: wet×top_pair×strong → CHECK (GTO=14% e.g. 9s8d6cTh top_pair oesd)
                    if bt == "wet" and mv == "top_pair" and has_strong: return "CHECK"
                    return "BET"
                if tier == "2P+":
                    # v37: wet×set×none → CHECK (GTO=39.3%)
                    if bt == "wet" and mv == "set" and has_none: return "CHECK"
                    if bt == "wet": return "BET"
                    if bt == "paired":
                        # v33: trips×paired×strong: low board BET (4s4d2c5h 97.8%), high CHECK
                        if mv == "trips" and has_strong: return "BET" if tr <= 6 else "CHECK"
                        if has_none: return "BET" if (5 < tr < 13) else "CHECK"
                        return "BET" if tr > 9 else "CHECK"
                if tier == "アンダーペア":
                    # v31: low_pair×dry×gutshot → CHECK (31.4%)
                    if bt == "dry" and is_low_pair and has_gutshot: return "CHECK"
                    # v40: dry×low_pair×strong×tr>=13 → CHECK (GTO=0.67%, gain=17.76 — K/A board low pair)
                    if bt == "dry" and is_low_pair and has_strong and tr >= 13: return "CHECK"
                    if bt == "dry" and has_any: return "BET"
                    # v40: dry×low_pair×none → CHECK (GTO=2-24% across tr=8,9,11)
                    if bt == "dry" and is_low_pair and has_none: return "CHECK"
                    # v40: dry×second_pair×none×tr=8,11 → BET (GTO=71-83%)
                    # v40: dry×second_pair×none×tr=9 → BET (GTO=59.88%, gain=14.23)
                    if bt == "dry" and is_second_pair and has_none and tr == 9: return "BET"
                    if bt == "dry" and is_second_pair and has_none and tr in (8, 11): return "BET"
                    # v40: dry×third_pair×none×tr=11 → BET (GTO=71.0%, gain=58.0), tr=8→CHECK (9.4%)
                    if bt == "dry" and is_third_pair and has_none and tr == 11: return "BET"
                    # v40: dry×second_pair×none×tr2=13 → BET (GTO=60.3%, gain=44.6)
                    if bt == "dry" and is_second_pair and has_none and tr2 == 13: return "BET"
                    # v40: dry×third_pair×none×tr2=9 → BET (GTO=62.8%, gain=44.4)
                    if bt == "dry" and is_third_pair and has_none and tr2 == 9: return "BET"
                    # v40: dry×third_pair×none×tr=9 → BET (GTO=63.03%, gain=18.76)
                    if bt == "dry" and is_third_pair and has_none and tr == 9: return "BET"
                    if bt == "dry" and has_none: return "BET" if (5 < tr2 < 8) else "CHECK"
                    if bt == "paired" and has_none: return "BET" if (4 < tr2 < 10) else "CHECK"
                if tier == "エア":
                    # v40: dry×gutshot×no_made_hand×tr2=11 → CHECK (GTO=31.96%, gain=17.32 — J second card bluff check)
                    if bt == "dry" and has_gutshot and is_no_made and tr2 == 11: return "CHECK"
                    # v40: dry×gutshot×no_made_hand×tr: tr=8,14→CHECK, tr=11,13→BET
                    if bt == "dry" and has_gutshot and is_no_made and tr in (8, 14): return "CHECK"
                    if bt == "dry" and has_gutshot and is_no_made and tr in (11, 13): return "BET"
                    # v40: dry×gutshot×ace_high×tr<=9 → CHECK (GTO=0.15%), tr=8 exception BET (GTO=66.2%)
                    if bt == "dry" and has_gutshot and is_ace_high and tr == 8: return "BET"
                    if bt == "dry" and has_gutshot and is_ace_high and tr <= 9: return "CHECK"
                    if bt == "dry" and has_gutshot: return "BET" if tr <= 9 else "CHECK"
                    # v40: dry×strong×no_made_hand×tr=9,11 → BET (GTO=56-65%, gain=15.6+16.3)
                    if bt == "dry" and has_strong and is_no_made and tr in (9, 11): return "BET"
                    if bt == "wet" and has_gutshot: return "BET" if is_no_made else "CHECK"  # v31: no_made 86.4% / ace+king 0-28%
                    if bt == "wet" and has_strong and is_no_made: return "BET" if tr <= 10 else "CHECK"  # v31: no_made×strong 63.5%
                    # v33: ace_high extends to tr<=11 (JsTc4sTh 66.1%), others keep v32 threshold
                    if bt == "paired" and is_ace_high and has_strong: return "BET" if (4 < tr <= 11) else "CHECK"
                    # v40: paired×strong×no_made_hand×tr<=5 → CHECK (GTO=38.52%, gain=29.39)
                    if bt == "paired" and is_no_made and has_strong and tr <= 5: return "CHECK"
                    # v40: paired×strong×king_high → CHECK (GTO=1.54%, gain=15.51 — K-high no bet OOP 4BP)
                    if bt == "paired" and is_king_high and has_strong: return "CHECK"
                    if bt == "paired" and has_strong: return "BET" if (4 < tr < 11) else "CHECK"
                    # v40: paired×gutshot×no_made_hand×tr=10 → BET (GTO=99.75%, gain=31.8)
                    if bt == "paired" and has_gutshot and is_no_made and tr == 10: return "BET"
                return "CHECK"
            return "CHECK"

    else:
        if pos == "IP":
            if tier == "2P+": return "BET"
            if pot == "SRP":
                if tier == "TP+": return "BET" if bt in ("dry","paired") else "CHECK"
                if tier == "アンダーペア":
                    # v31: paired×third_pair → BET (57.4%)
                    # v40: paired×third_pair×tr2=13 → CHECK (GTO=0.04%, gain=30.0 — K board third pair trap)
                    if bt == "paired" and is_third_pair and tr2 == 13: return "CHECK"
                    if bt == "paired" and is_third_pair: return "BET"
                    # v40: paired×none×second_pair×tr=14 → BET (GTO=79.6%, gain=69.3)
                    if bt == "paired" and has_none and is_second_pair and tr >= 14: return "BET"
                    # v40: paired×none×underpair×tr=14 → BET (GTO=99.96%, gain=17.99)
                    if bt == "paired" and has_none and mv == "underpair" and tr >= 14: return "BET"
                    if bt == "paired" and has_none: return "BET" if tr <= 11 else "CHECK"
                    # v40: dry×second_pair×none×tr2=11 → BET (GTO=69.7%, gain=37.9)
                    if bt == "dry" and is_second_pair and has_none and tr2 == 11: return "BET"
                    # v40: dry×underpair×none×tr2=10 → BET (GTO=94.9%, gain=27.0)
                    if bt == "dry" and mv == "underpair" and has_none and tr2 == 10: return "BET"
                    return "BET" if bt == "paired" else "CHECK"
                if tier == "エア":
                    if bt == "paired":
                        if is_king_high: return "CHECK"   # king_high 6.1% BET
                        # v40: paired×none×no_made_hand×tr2=10 → BET (GTO=52.21%, gain=19.8)
                        if is_no_made and has_none and tr2 == 10: return "BET"
                        # v31: ace_high×paired = 98.8% BET → BET (was incorrectly CHECK)
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
                    # v31: dry×underpair → BET (59.5%)
                    if bt == "dry" and mv == "underpair": return "BET"
                    # v31: paired×third_pair→BET (57.4%)
                    if bt == "paired" and is_third_pair: return "BET"
                if tier == "エア":
                    if bt in ("wet",): return "BET"
                    if bt == "dry":
                        if is_ace_high or is_king_high: return "CHECK"
                        # v23: no_made_hand → BET always (including A-high boards)
                        if is_no_made: return "BET"
                        return "BET" if tr <= 13 else "CHECK"
                    # v40: paired×none×no_made_hand×tr=11 → BET (GTO=70.9%, gain=133.5)
                    if bt == "paired" and has_none and is_no_made and tr == 11: return "BET"
                    if bt == "paired" and has_none: return "CHECK"
                    return "CHECK"
                return "CHECK"
            if pot == "4BP":
                if tier == "TP+": return "BET"
                if tier == "アンダーペア":
                    # v40: dry×underpair×none×tr2=8 → CHECK (GTO=0%, gain=24.0)
                    if bt == "dry" and mv == "underpair" and has_none and tr2 == 8: return "CHECK"
                    # v37: dry×underpair × none → BET (GTO=52.9%)
                    if bt == "dry" and mv == "underpair" and has_none: return "BET"
                    # v40: dry×none×second_pair×tr=14 or tr2=9 → BET (gain=80.5+47.3)
                    if bt == "dry" and is_second_pair and has_none and (tr >= 14 or tr2 == 9): return "BET"
                    # v40: paired×none×low_pair×tr2=10 → CHECK (GTO=43.31%, gain=19.27)
                    if bt == "paired" and is_low_pair and has_none and tr2 == 10: return "CHECK"
                    if bt == "paired": return "BET" if tr > 11 else "CHECK"
                    return "CHECK"
                if tier == "エア":
                    if bt == "dry":
                        if is_ace_high or is_king_high: return "CHECK"
                        # v23: no_made_hand → BET (tr2 override)
                        if is_no_made and has_none: return "BET"
                        if has_none: return "BET" if tr2 != 9 else "CHECK"
                        return "BET" if tr <= 13 else "CHECK"
                    # v40: paired×none×no_made_hand×tr2=10 → BET (GTO=53.9%, gain=35.3)
                    if bt == "paired" and has_none and is_no_made and tr2 == 10: return "BET"
                    return "CHECK"
                return "CHECK"
            return "CHECK"
        else:
            if pot == "SRP":
                if tier == "TP+":
                    if bt == "dry" and has_none: return "BET" if tr2 != 9 else "CHECK"
                    return "BET"
                if tier == "2P+":
                    # v40: dry×none×set×tr=10 → BET (GTO=99.81%, gain=14.94 — T board set always bet)
                    if bt == "dry" and has_none and mv == "set" and tr == 10: return "BET"
                    if mv == "set" and has_none: return "CHECK"   # v26: set 43.4% → trap CHECK
                    # v40: dry×none×straight×tr2=12 → CHECK (GTO=0.15%, gain=15.95 — Q/A board straight trap)
                    if bt == "dry" and has_none and mv == "straight" and tr2 == 12: return "CHECK"
                    # v40: dry×none×straight×tr=13 → CHECK (gain=58.2, K-high boards)
                    if bt == "dry" and has_none and mv == "straight" and tr == 13: return "CHECK"
                    # v40: dry×two_pair×none×tr2=10 → BET (GTO=65.4%, gain=70.3 — J/Q-T-x boards)
                    if bt == "dry" and has_none and mv == "two_pair" and tr2 == 10: return "BET"
                    # v40: dry×two_pair×none×tr2=13 → CHECK (GTO=45.0%, gain=24.2 — A-K-x boards)
                    if bt == "dry" and has_none and mv == "two_pair" and tr2 == 13: return "CHECK"
                    if bt == "dry" and has_none: return "BET" if tr <= 10 or tr >= 13 else "CHECK"
                    # v40: paired×none×fullhouse×tr>=13 → BET (GTO=68.7%, gain=38.6)
                    if bt == "paired" and has_none and mv == "fullhouse": return "BET"
                    # v40: paired×none×trips×tr2=12 → BET (GTO=72.27% — QQ board, pair is high card)
                    if bt == "paired" and has_none and mv == "trips" and tr2 == 12: return "BET"
                    # v40: paired×none×trips×tr=12 → CHECK (GTO=40.60% — Q-high with non-Q pair)
                    if bt == "paired" and has_none and mv == "trips" and tr == 12: return "CHECK"
                    if bt == "paired" and has_none: return "BET" if tr <= 12 else "CHECK"
                    return "BET"
                if tier == "アンダーペア":
                    if bt == "paired":
                        # v40: paired×none×low_pair → CHECK unless tr>=14 (gains=74.2+61.7)
                        # v40: paired×none×low_pair×tr2=8 → BET (GTO=55.59%, gain=16.09 — 8 second card)
                        if has_none and is_low_pair and tr2 == 8: return "BET"
                        if has_none and is_low_pair: return "BET" if tr >= 14 else "CHECK"
                        # v40: paired×none×third_pair×tr2=9 → CHECK (GTO=0.04%, gain=91.9)
                        if has_none and is_third_pair and tr2 == 9: return "CHECK"
                        # v40: paired×none×second_pair×tr2=12 → CHECK (GTO=19.96% — QQ board, pair is high card)
                        if has_none and is_second_pair and tr2 == 12: return "CHECK"
                        # v40: paired×none×second_pair×tr=12 → BET (GTO=56.18% — Q-high with non-Q pair)
                        if has_none and is_second_pair and tr == 12: return "BET"
                        if has_none: return "BET" if (tr <= 9 or tr >= 13) else "CHECK"
                        return "BET" if tr > 12 else "CHECK"
                    # v40: dry×underpair×none×tr2=7 → CHECK (GTO=40.08%, gain=17.85 — bimodal low boards)
                    if bt == "dry" and mv == "underpair" and has_none and tr2 == 7: return "CHECK"
                    if bt == "dry" and mv == "underpair": return "BET"  # v26: underpair 54.4%
                    # v40: dry×low_pair×none×tr=10 → BET (GTO=71.5%, gain=54.3)
                    if bt == "dry" and is_low_pair and has_none and tr == 10: return "BET"
                    # v39/v40: dry second_pair tr=10,13 → CHECK (GTO=0.3%/41.0%)
                    # v40: dry×second_pair×tr2>=13 → CHECK (GTO=32.3%, gain=133.1 — K-high second board card)
                    if bt == "dry" and is_second_pair and tr2 >= 13: return "CHECK"
                    if bt == "dry" and is_second_pair: return "BET" if tr not in (10, 13) else "CHECK"
                    # v40: dry×third_pair×none×tr2=9,10×tr>=11 → BET (GTO=58.7%/54.8%, gain=57.3+21.5)
                    # T-9-x boards (tr=10, tr2=9) GTO=0.14% → still CHECK; only J+ boards BET
                    if bt == "dry" and is_third_pair and has_none and tr2 in (9, 10) and tr >= 11: return "BET"
                if tier == "エア":
                    # v40: paired×ace_high×none×tr2=7 → BET (GTO=62.7%, gain=32.6)
                    if bt == "paired" and is_ace_high and has_none and tr2 == 7: return "BET"
                    if bt == "paired" and is_ace_high: return "CHECK"
                    if bt == "paired": return "BET" if tr <= 12 else "CHECK"
                    if bt == "dry" and has_none:
                        # v39: river OOP SRP エア dry none — mv_cat specific (before general tr2 rule)
                        if is_no_made: return "BET" if tr <= 13 else "CHECK"
                        # v40: king_high×tr2=12 → BET (GTO=79.0%, gain=48.7 — K-high boards with Q second card)
                        if is_king_high: return "BET" if (tr <= 12 or tr2 == 12) else "CHECK"
                        # v40: ace_high×tr2=12 → BET (GTO=74.3%, gain=54.4 — A-high boards with Q second card)
                        if is_ace_high: return "BET" if (tr == 10 or tr2 == 12) else "CHECK"
                        return "BET" if (10 < tr2 < 13) else "CHECK"
                return "CHECK"
            if pot == "3BP":
                if tier == "エア":
                    if bt == "dry" and has_none:
                        if is_ace_high or is_king_high: return "CHECK"
                        if is_no_made: return "BET"
                        return "BET" if (tr2 <= 8 or tr2 >= 11) else "CHECK"
                    # v40: paired×none×no_made_hand×tr2<=5 → BET (GTO=53.32%, gain=21.25)
                    if bt == "paired" and has_none and is_no_made and tr2 <= 5: return "BET"
                    if bt in ("dry","paired"): return "CHECK"
                    return "CHECK"
                if tier == "アンダーペア":
                    if bt == "dry":
                        if is_second_pair or is_third_pair: return "BET"
                        # v23: low_pair → CHECK explicitly (includes A-high boards)
                        if is_low_pair: return "CHECK"
                        # v40: dry×underpair×none×tr2=8 → BET (GTO=99.8%, gain=23.9)
                        if mv == "underpair" and has_none and tr2 == 8: return "BET"
                        return "BET" if tr > 13 else "CHECK"
                    # v40: paired×none×low_pair×tr=11 → BET (GTO=99.9%, gain=113.8)
                    if bt == "paired" and has_none and is_low_pair and tr == 11: return "BET"
                    if bt == "paired" and has_none and is_low_pair: return "CHECK"
                    # v31: paired×third_pair × none → BET (75.0%)
                    if bt == "paired" and has_none and is_third_pair: return "BET"
                    if bt == "paired" and has_none: return "BET" if (tr2 <= 5 or tr2 >= 13) else "CHECK"
                # v40: 2P+ dry none two_pair tr>=14 → BET (GTO=52.82%, gain=15.21 — A-board two pair)
                if tier == "2P+" and bt == "dry" and has_none and mv == "two_pair" and tr >= 14: return "BET"
                if tier == "2P+" and bt == "dry" and mv == "two_pair": return "CHECK"  # v31: two_pair 45.6%
                if tier == "2P+" and bt == "dry" and has_none: return "BET" if tr <= 13 else "CHECK"
                if tier == "2P+" and bt == "paired" and has_none: return "BET" if tr2 <= 10 else "CHECK"
                # v37: TP+ dry overpair → CHECK (GTO=22.4%, overpair traps on river)
                if tier == "TP+" and bt == "dry" and mv == "overpair" and has_none: return "CHECK"
                return "BET"
            if pot == "4BP":
                if tier == "TP+":
                    # v37: overpair×dry×none → CHECK (GTO=15.9%, trap)
                    if bt == "dry" and mv == "overpair" and has_none: return "CHECK"
                    if bt == "dry" and has_none: return "BET" if tr2 > 8 else "CHECK"
                    # v31: overpair×paired = 7.9% BET → trap CHECK
                    if bt == "paired" and mv == "overpair": return "CHECK"
                    if bt == "paired": return "BET" if tr <= 11 else "CHECK"
                if tier == "2P+" and bt == "paired": return "BET" if tr <= 11 else "CHECK"
                # v40: アンダーペア×dry×none×low_pair×tr2=10 → CHECK (GTO=28.9%, gain=175.1)
                if tier == "アンダーペア" and bt == "dry" and has_none and is_low_pair and tr2 == 10: return "CHECK"
                if tier == "アンダーペア" and bt == "dry" and has_none: return "BET" if tr2 > 8 else "CHECK"
                # v40: アンダーペア×paired×none×underpair×tr>=14 → CHECK (GTO=0.38%, gain=17.86 — A board trap)
                if tier == "アンダーペア" and bt == "paired" and has_none and mv == "underpair" and tr >= 14: return "CHECK"
                if tier == "エア" and bt == "dry" and has_none: return "BET" if tr2 <= 8 else "CHECK"
                if tier == "エア" and bt == "paired" and is_ace_high: return "BET"  # v31: ace_high 91.5%
                # v40: 2P+×dry×none×two_pair×tr=14 → CHECK (GTO=44.4%, gain=30.3)
                if tier == "2P+" and bt == "dry" and has_none and mv == "two_pair" and tr >= 14: return "CHECK"
                # v40: 2P+×dry×none×two_pair×tr2=10 → CHECK (GTO=44.8%, gain=56.1 — T second card)
                if tier == "2P+" and bt == "dry" and has_none and mv == "two_pair" and tr2 == 10: return "CHECK"
                return "CHECK" if tier == "エア" else "BET"
            return "CHECK"

df = pd.read_csv(CSV)
df["board_type"] = df["board"].apply(board_type_fixed)
df["dv_grp"] = df["dv_cat"].apply(dv_group)
df["tr"] = df["board"].apply(top_rank)
df["tr2"] = df["board"].apply(second_rank)
df["pred"] = df.apply(predict_v37, axis=1)
df["correct"] = df["pred"] == df["best_action"]
df["pred_bet"] = (df["pred"]=="BET").astype(float)
df["freq_loss"] = (df["bet_pct"]/100 - df["pred_bet"]).abs()
total = df["n_combos"].sum()
acc = float(np.average(df["correct"], weights=df["n_combos"]))*100
avg_loss = float(np.average(df["freq_loss"], weights=df["n_combos"]))*100
score = aqs(avg_loss)

V36_LOSS = 26.3046; V36_AQS = 86.94
print(f"v37: acc={acc:.3f}%  avg_loss={avg_loss:.4f}%  AQS={score:.2f}")
print(f"vs v33: avg_loss {V36_LOSS:.4f}% -> {avg_loss:.4f}% ({avg_loss-V36_LOSS:+.4f}pp)  AQS {V36_AQS} -> {score:.2f} ({score-V36_AQS:+.2f})")

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

import sys
if "--gains" in sys.argv:
    df["flip_loss"] = (df["bet_pct"]/100 - (1 - df["pred_bet"])).abs()
    df["row_gain"] = df["freq_loss"] - df["flip_loss"]
    grp_cols = ["street","position","pot_type","tier","board_type","dv_grp","mv_cat"]
    grp = df.groupby(grp_cols).apply(lambda x: pd.Series({
        "n": int(len(x)),
        "wn": float(x["n_combos"].sum()),
        "wgain": float(np.dot(x["row_gain"], x["n_combos"])) / float(x["n_combos"].sum()),
        "avg_gto": float(np.dot(x["bet_pct"], x["n_combos"])) / float(x["n_combos"].sum()),
        "pred_bet_pct": float((x["pred"]=="BET").mean()) * 100,
    })).reset_index()
    grp = grp[grp["n"] >= 4]
    grp_pos = grp[grp["wgain"] > 0.05].sort_values("wgain", ascending=False)
    print("\n=== TOP GAINS (flip improves) ===")
    print(grp_pos.head(40).to_string(index=False))
    print("\n=== WRONG PREDS: pred=BET, avg_gto<45% ===")
    wrong_bet = grp[(grp["pred_bet_pct"] >= 80) & (grp["avg_gto"] < 45)].sort_values("avg_gto")
    print(wrong_bet.head(20).to_string(index=False))
    print("\n=== WRONG PREDS: pred=CHECK, avg_gto>55% ===")
    wrong_chk = grp[(grp["pred_bet_pct"] <= 20) & (grp["avg_gto"] > 55)].sort_values("avg_gto", ascending=False)
    print(wrong_chk.head(20).to_string(index=False))
