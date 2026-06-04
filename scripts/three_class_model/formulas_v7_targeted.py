#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""v7 — mv_cat-based formulas targeting specific huge-loss cells directly.

Player can compute mv_cat (made-hand category) at the table easily:
  air, A-high, K-high, low_pair, underpair, 3rd_pair, 2nd_pair, TP, OP,
  2P, set, trips, straight, flush, fullhouse, quads

We use this as the primary axis instead of equity_bucket (uncomputable).

Flop defense v7 targets:
  - low_pair/third_pair × no_draw × dry boards → FOLD (top huge-loss cell)
  - set × no_draw × any → CALL (slowplay, not RAISE)

Turn defense v7 (confirmed winner):
  - vs overbet: weak made (incl 2nd/3rd pair) + weak draws (gutshot/BDFD) → FOLD

River attack v7:
  - polarized + slowplay strong on dry boards
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


def best_ev_def(r):
    return max(e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e))


def best_ev_atk(r):
    return max(r["ev_bet"], r["ev_check"])


def ev_of_def(r, p):
    if p == "FOLD": return r["ev_fold"]
    if p == "CALL": return r["ev_call"]
    return r["ev_raise"] if pd.notna(r["ev_raise"]) else r["ev_call"]


def ev_of_atk(r, p):
    return r["ev_bet"] if p == "BET" else r["ev_check"]


def ev_gap_row(r):
    evs = [r.get("ev_fold"), r.get("ev_call"), r.get("ev_raise"),
           r.get("ev_bet"), r.get("ev_check")]
    evs = sorted([e for e in evs if pd.notna(e)], reverse=True)
    return evs[0] - evs[1] if len(evs) >= 2 else None


# ── Formulas ──
AIR = {"no_made_hand", "ace_high", "king_high"}
WEAK_PAIR = {"low_pair", "underpair", "third_pair", "second_pair"}
MED_PAIR = {"top_pair", "overpair"}
STRONG = {"two_pair", "set", "trips", "straight", "flush", "fullhouse", "quads"}
DRY_BOARDS = {"dry_high", "low_dry"}
DYNAMIC_BOARDS = {"dynamic", "dynamic_2tone"}


def flop_v4(r):
    """3-rule baseline — uses equity_bucket (GTO Wizard)."""
    eb = r["equity_bucket"]
    mv = r["mv_cat"]
    dv = r["dv_cat"]
    if eb in {"trash_hands", "weak_hands"} and mv in AIR and dv == "no_draw":
        return "FOLD"
    if eb == "best_hands" and mv in {"overpair"} | STRONG:
        return "RAISE"
    return "CALL"


def flop_v7(r):
    """v7: pure mv_cat + board_family — no equity_bucket needed."""
    mv = r["mv_cat"]
    dv = r["dv_cat"]
    bf = r["board_family"]
    # FOLD air
    if mv in AIR and dv == "no_draw":
        return "FOLD"
    # FOLD weak pairs on dry boards (top huge-loss cells)
    if mv in {"low_pair", "third_pair"} and dv == "no_draw" and bf in DRY_BOARDS | {"dynamic_2tone"}:
        return "FOLD"
    # RAISE only overpair (set/2P slowplay)
    if mv == "overpair":
        return "RAISE"
    return "CALL"


def turn_v6(r):
    """Confirmed winner — vs overbet, FOLD weak draws too."""
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]
    weak = mv in AIR | WEAK_PAIR  # includes 2nd/3rd pair
    weak_no_draw = dv in {"no_draw", "twocards_bdfd", "onecard_bdfd", "gutshot"}
    if bs == "overbet_185p":
        if weak and weak_no_draw:
            return "FOLD"
    else:
        if mv in AIR and dv == "no_draw":
            return "FOLD"
    return "CALL"


def river_v4(r):
    mv = r["mv_cat"]
    VALUE = {"top_pair", "overpair"} | STRONG
    BLUFF = {"no_made_hand", "king_high"}
    if mv in VALUE or mv in BLUFF: return "BET"
    return "CHECK"


def river_v7(r):
    """v4 + targeted fixes for top huge-loss cells."""
    mv = r["mv_cat"]
    bf = r["board_family"]
    # Slowplay STRONG (set/trips/straight/2P/full+) on dry boards (no draws to charge)
    if mv in STRONG and bf in DRY_BOARDS:
        return "CHECK"
    # TP on dynamic → CHECK (vulnerable)
    if mv == "top_pair" and bf in DYNAMIC_BOARDS:
        return "CHECK"
    # BET value otherwise
    VALUE = {"top_pair", "overpair"} | STRONG
    BLUFF = {"no_made_hand", "king_high"}
    if mv in VALUE or mv in BLUFF: return "BET"
    return "CHECK"


# ── Data prep ──
def prep_flop_def(df):
    sub = df[(df["street"] == "flop") & (df["action_context"] == "defense") &
              df["ev_call"].notna() & df["ev_fold"].notna() &
              df["equity_bucket"].notna() & (df["equity_bucket"] != "")].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev_def, axis=1)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    return sub[sub["ev_gap"].notna()]


def prep_turn_def(df):
    sub = df[(df["street"] == "turn") & (df["action_context"] == "defense") &
              df["ev_call"].notna() & df["ev_fold"].notna()].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev_def, axis=1)
    sub["bet_size"] = sub["source_path"].apply(lambda s:
        "small_25p" if "_R2." in s else "med_67p" if "_R6." in s else
        "overbet_185p" if "_R16" in s else "other")
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    return sub[sub["ev_gap"].notna()]


def prep_river_atk(df):
    sub = df[(df["street"] == "river") & (df["action_context"] == "attack") &
              df["ev_bet"].notna() & df["ev_check"].notna() &
              df["mv_cat"].notna() & (df["mv_cat"] != "")].copy()
    sub["modal"] = (sub["bet_freq"].fillna(0) >= 0.5).map({True: "BET", False: "CHECK"})
    sub["best_ev"] = sub.apply(best_ev_atk, axis=1)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    return sub[sub["ev_gap"].notna()]


def evaluate(sub, formulas, ev_of, name):
    print(f"\n=== {name} ===")
    print(f"  Rows: {len(sub)}, huge_gap rows: {len(sub[sub['ev_gap']>0.5])}")
    for label, f in formulas:
        sub_c = sub.copy()
        sub_c["pred"] = sub_c.apply(f, axis=1)
        sub_c["ev_p"] = sub_c.apply(lambda r: ev_of(r, r["pred"]), axis=1)
        sub_c["loss"] = sub_c["best_ev"] - sub_c["ev_p"]
        acc = (sub_c["pred"] == sub_c["modal"]).mean() * 100
        mean_l = sub_c["loss"].mean()
        huge = sub_c[sub_c["ev_gap"] > 0.5]
        huge_l = huge["loss"].mean() if len(huge) > 0 else float("nan")
        print(f"  {label:25s} acc={acc:5.1f}% mean_loss={mean_l:.4f}BB huge_loss={huge_l:.4f}BB")


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)

    fd = prep_flop_def(df)
    evaluate(fd, [
        ("Flop v4 (eq_bucket)", flop_v4),
        ("Flop v7 (mv-based)", flop_v7),
    ], ev_of_def, "FLOP DEFENSE")

    td = prep_turn_def(df)
    evaluate(td, [
        ("Turn v4 (basic)", lambda r: turn_v4_basic(r)),
        ("Turn v6 (vs OB+draw)", turn_v6),
    ], ev_of_def, "TURN DEFENSE")

    ra = prep_river_atk(df)
    evaluate(ra, [
        ("River v4 (pure polar)", river_v4),
        ("River v7 (+slowplay)", river_v7),
    ], ev_of_atk, "RIVER ATTACK")

    return 0


def turn_v4_basic(r):
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]
    weak = mv in AIR | WEAK_PAIR
    if bs == "overbet_185p":
        if weak and dv == "no_draw": return "FOLD"
    else:
        if mv in AIR and dv == "no_draw": return "FOLD"
    return "CALL"


if __name__ == "__main__":
    raise SystemExit(main())
