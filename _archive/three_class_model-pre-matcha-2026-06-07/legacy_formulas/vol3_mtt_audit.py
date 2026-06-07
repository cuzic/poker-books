#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""vol3_mtt_audit.py — Vol3 (MTT postflop) 各 depth × street の精度監査。

既存 dataset_unified.csv に含まれる MTT data を depth × street × ctx で集計し、
Cash 公式 (v8a/v10/v14) を適用したときの精度を確認。
Vol3 用の MTT 専用公式が必要な領域を特定。
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"

AIR = {"no_made_hand", "ace_high", "king_high"}
WEAK_PAIR_LOW = {"low_pair", "underpair", "third_pair"}
STRONG = {"two_pair", "set", "trips", "straight", "flush", "fullhouse", "quads"}
DRY_BOARDS = {"dry_high", "low_dry"}
DYNAMIC_BOARDS = {"dynamic", "dynamic_2tone"}
WEAK_DRAW = {"twocards_bdfd", "onecard_bdfd", "gutshot"}


def turn_bet_size(s):
    if "_R4" in s or "_R5" in s or "_R6" in s: return "small_33"
    if "_R16" in s or "_R17" in s or "_R19" in s: return "overbet_185"
    return "other"


def river_bet_size(s):
    if "_R4" in s: return "small_30"
    if "_R7" in s or "_R8" in s: return "med_75"
    if "_R13" in s: return "med_100"
    if "_R16" in s: return "overbet"
    if "_R89" in s or "_R35" in s: return "allin"
    return "other"


def detect_pot_type(p):
    p = str(p).lower()
    if "3bp" in p: return "3BP"
    if "4bp" in p: return "4BP"
    if "mtt25" in p: return "MTT25"
    if "mtt50" in p: return "MTT50"
    if "mtt100" in p: return "MTT100"
    if "mtt200" in p: return "MTT200"
    if "cash50" in p: return "Cash50"
    if "cash100" in p or "def_cash100" in p: return "Cash100"
    return "other"


# === 公式 ===

def flop_def_v8a(r):
    mv, dv, bf = r["mv_cat"], r["dv_cat"], r["board_family"]
    if mv in AIR:
        if dv == "no_draw": return "FOLD"
        if dv in WEAK_DRAW and bf in DYNAMIC_BOARDS: return "FOLD"
    if mv in {"low_pair", "third_pair"} and dv == "no_draw" and bf in DRY_BOARDS | {"dynamic_2tone"}:
        return "FOLD"
    if mv == "overpair": return "RAISE"
    return "CALL"


def turn_def_v10(r):
    mv, dv, bf, bs = r["mv_cat"], r["dv_cat"], r["board_family"], r["bet_size"]
    if bs == "overbet_185":
        weak_no_draw = dv in {"no_draw"} | WEAK_DRAW
        weak_mv = mv in AIR | WEAK_PAIR_LOW | {"second_pair"}
        if weak_mv and weak_no_draw: return "FOLD"
        if bf in DYNAMIC_BOARDS and mv == "top_pair" and dv == "no_draw": return "FOLD"
        if mv in AIR and dv in {"flush_draw", "nut_flush_draw", "oesd", "combo_draw"}: return "FOLD"
        return "CALL"
    else:
        if mv in AIR and bf == "monotone": return "FOLD"
        if mv in AIR and dv in WEAK_DRAW and bf != "low_dry": return "FOLD"
        if mv in AIR and dv == "no_draw": return "FOLD"
        if mv == "low_pair" and dv == "no_draw": return "FOLD"
        if mv == "third_pair" and dv == "no_draw" and bf != "low_dry": return "FOLD"
        weak_mv_no2p = mv in AIR | WEAK_PAIR_LOW
        if bf in DYNAMIC_BOARDS and weak_mv_no2p and dv in WEAK_DRAW: return "FOLD"
        if bf in DYNAMIC_BOARDS and dv == "oesd" and weak_mv_no2p: return "FOLD"
        return "CALL"


# MTT 50bb Turn pure bucket (memory より)
def turn_def_mtt50(r):
    mv = r["mv_cat"]; bs = r["bet_size"]
    bucket = r.get("equity_bucket", "")
    bf = r["board_family"]
    dv = r["dv_cat"]
    is_monotone = bf == "monotone"
    strong_made = mv in {"set", "two_pair", "straight", "flush", "fullhouse", "trips"}
    strong_draw = dv in {"flush_draw", "nut_flush_draw", "oesd", "combo_draw"}
    if bucket == "best_hands":
        if bs == "overbet_185" and strong_made and not is_monotone: return "RAISE"
        return "CALL"
    if bucket == "good_hands":
        if bs == "overbet_185" and strong_made and not is_monotone: return "RAISE"
        return "CALL"
    if bucket == "weak_hands":
        if bs == "overbet_185":
            if strong_draw and not is_monotone: return "CALL"
            return "FOLD"
        return "CALL"
    # trash
    if bs == "overbet_185": return "FOLD"
    if strong_draw and not is_monotone: return "CALL"
    return "FOLD"


# === Eval ===
def best_ev_def(r):
    return max(e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e))

def ev_of_def(r, p):
    if p == "FOLD": return r["ev_fold"]
    if p == "CALL": return r["ev_call"]
    if p == "RAISE": return r["ev_raise"]

def ev_gap_row(r):
    evs = [e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e)]
    if len(evs) < 2: return None
    s = sorted(evs, reverse=True)
    return s[0] - s[1]


def prep(df, street):
    bs_fn = turn_bet_size if street == "turn" else river_bet_size if street == "river" else None
    sub = df[(df["street"] == street) & (df["action_context"] == "defense") &
             df["ev_call"].notna() & df["ev_fold"].notna() & df["mv_cat"].notna() & (df["mv_cat"] != "")].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev_def, axis=1)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    if bs_fn is not None:
        sub["bet_size"] = sub["source_path"].apply(bs_fn)
    else:
        sub["bet_size"] = "—"
    sub["pot_type"] = sub["source_path"].apply(detect_pot_type)
    return sub[sub["ev_gap"].notna()]


def evaluate(sub, formula, label):
    if len(sub) == 0: return None
    sub_c = sub.copy()
    sub_c["pred"] = sub_c.apply(formula, axis=1)
    sub_c["ev_p"] = sub_c.apply(lambda r: ev_of_def(r, r["pred"]), axis=1)
    sub_c["loss"] = sub_c["best_ev"] - sub_c["ev_p"]
    acc = (sub_c["pred"] == sub_c["modal"]).mean() * 100
    mean_l = sub_c["loss"].mean()
    huge = sub_c[sub_c["ev_gap"] > 0.5]
    huge_l = huge["loss"].mean() if len(huge) > 0 else float("nan")
    return acc, mean_l, huge_l, len(huge), len(sub_c)


def main():
    df = pd.read_csv(DATA, low_memory=False)
    df["pot_type"] = df["source_path"].apply(detect_pot_type)

    print("=== Vol3 関連 dataset の depth × street 分布 ===\n")
    for street in ["flop", "turn", "river"]:
        sub = prep(df, street)
        print(f"\n  --- {street} defense ---")
        print(f"{'pot_type':12s} {'n':>7s} {'huge_n':>7s}")
        for pt in ["MTT25", "MTT50", "MTT100", "MTT200", "3BP", "Cash50", "Cash100"]:
            r = sub[sub["pot_type"] == pt]
            if len(r) == 0: continue
            huge = r[r["ev_gap"] > 0.5]
            print(f"  {pt:10s}  {len(r):>7,}  {len(huge):>7,}")

    print("\n\n=== MTT depth 別 × Cash 公式適用時の精度 ===")
    print("(Cash v8a/v10 を MTT に適用するとどうなるか — 軸ミスマッチの検証)\n")

    for street, formula, label in [
        ("flop", flop_def_v8a, "v8a"),
        ("turn", turn_def_v10, "v10"),
    ]:
        sub = prep(df, street)
        print(f"\n  --- {street} defense ({label}) ---")
        print(f"{'pot_type':12s} {'n':>6s} {'acc':>7s} {'mean':>9s} {'huge':>9s}")
        for pt in ["Cash100", "MTT200", "MTT100", "MTT50", "MTT25", "3BP"]:
            r = sub[sub["pot_type"] == pt]
            if len(r) < 200: continue
            res = evaluate(r, formula, label)
            if res:
                acc, mean_l, huge_l, n_huge, n = res
                print(f"  {pt:10s}  {n:>6,}  {acc:>6.1f}% {mean_l:>7.3f}BB {huge_l:>7.3f}BB")


if __name__ == "__main__":
    raise SystemExit(main())
