#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Vol2 Turn / River の補正改善検証.

Turn 改善候補:
  T1: vs overbet で weak_mv + weak_draw → FOLD (Vol3 v8 Rule O1)
  T2: vs overbet で dry_high + air + flush_draw → FOLD (Rule O2)
  T3: vs medium で dynamic + weak_mv + weak_draw → FOLD (Rule M2)
  T4: vs medium で dynamic + weak_mv + OESD → FOLD (Rule M3)
  T5: vs overbet で TP × dynamic + no_draw → FOLD (Rule O4)

River 改善候補:
  R1: mv override - straight/flush/trips → CALL
  R2: TP × dry × overbet → CALL (bluff catch)
  R3: TP/2P × dynamic × overbet → CALL
  R4: fullhouse/quads → RAISE
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"

S_HANDS = {"two_pair", "set", "trips", "straight", "flush",
           "fullhouse", "quads", "overpair", "straight_flush"}
M_HANDS = {"top_pair", "second_pair", "third_pair", "underpair"}
STRONG_DRAWS = {"oesd", "flush_draw", "combo_draw", "nut_flush_draw"}
WEAK_DRAWS = {"no_draw", "twocards_bdfd", "onecard_bdfd", "gutshot"}
DYNAMIC = {"dynamic", "dynamic_2tone", "monotone"}
DRY = {"dry_high", "low_dry"}
AIR = {"no_made_hand", "ace_high", "king_high"}


def normalize_bs(bs: str) -> str:
    if bs in {"s", "m", "l", "o"}: return bs
    bs_lo = bs.lower() if bs else ""
    if "small" in bs_lo or "25p" in bs_lo or "30p" in bs_lo: return "s"
    if "med_67" in bs_lo or "med_75" in bs_lo: return "m"
    if "med_100" in bs_lo: return "l"
    if "overbet_117" in bs_lo: return "l"
    if "overbet_185" in bs_lo or bs_lo == "overbet": return "o"
    if "allin" in bs_lo: return "o"
    return "m"


def hand_cat(r):
    mv, dv = r["mv_cat"], r["dv_cat"]
    if mv in S_HANDS: return "S"
    if mv in M_HANDS: return "M"
    if mv == "low_pair": return "W"
    if dv in STRONG_DRAWS and mv in AIR: return "D"
    if mv in {"ace_high", "king_high"}: return "W"
    return "A"


def vol2_matrix(cat: str, bs: str) -> str:
    bs = normalize_bs(bs)
    matrix = {
        "S": {"s": "RAISE", "m": "CALL", "l": "CALL", "o": "CALL"},
        "M": {"s": "CALL",  "m": "CALL", "l": "CALL", "o": "FOLD"},
        "W": {"s": "CALL",  "m": "CALL", "l": "FOLD", "o": "FOLD"},
        "A": {"s": "CALL",  "m": "FOLD", "l": "FOLD", "o": "FOLD"},
        "D": {"s": "CALL",  "m": "CALL", "l": "CALL", "o": "FOLD"},
    }
    return matrix.get(cat, {}).get(bs, "CALL")


def vol2_turn_current(r):
    """現状 Vol2 Turn (ch04 + ch06 補正)."""
    mv, dv, bf, bs = r["mv_cat"], r["dv_cat"], r["board_family"], r["bet_size"]
    cat = hand_cat(r)
    base = vol2_matrix(cat, bs)
    is_dyn = bf in DYNAMIC
    bs_n = normalize_bs(bs)
    # 現状の ch06 補正
    if bs_n == "o":  # vs overbet
        if bf == "dry_high" and mv in AIR and dv == "flush_draw": return "FOLD"
        if is_dyn and mv in AIR and dv == "oesd": return "FOLD"
        if is_dyn and mv == "top_pair" and dv == "no_draw": return "FOLD"
    elif bs_n == "m":  # vs medium
        if is_dyn and mv in {"low_pair", "underpair", "third_pair"} and dv in WEAK_DRAWS:
            return "FOLD"
        if is_dyn and dv == "oesd" and mv in {"low_pair", "underpair", "third_pair"}:
            return "FOLD"
    return base


def vol2_turn_v2(r):
    """+T1: vs overbet で weak_mv + weak_draw → FOLD (Rule O1)."""
    base = vol2_turn_current(r)
    mv, dv, bs = r["mv_cat"], r["dv_cat"], r["bet_size"]
    bs_n = normalize_bs(bs)
    weak_mv = mv in AIR | {"low_pair", "underpair", "third_pair", "second_pair"}
    if bs_n == "o" and weak_mv and dv in WEAK_DRAWS:
        return "FOLD"
    return base


def vol2_turn_v3(r):
    """v2 + T3 (medium で dynamic + weak_mv + weak_draw → FOLD)."""
    base = vol2_turn_v2(r)
    mv, dv, bf, bs = r["mv_cat"], r["dv_cat"], r["board_family"], r["bet_size"]
    bs_n = normalize_bs(bs)
    is_dyn = bf in DYNAMIC
    weak_mv_no2nd = mv in AIR | {"low_pair", "underpair", "third_pair"}  # 2nd_pair 除く
    if bs_n == "m" and is_dyn and weak_mv_no2nd and dv in WEAK_DRAWS:
        return "FOLD"
    return base


def vol2_turn_v4(r):
    """v3 + T4 (medium で dynamic + OESD + weak_mv → FOLD)."""
    base = vol2_turn_v3(r)
    mv, dv, bf, bs = r["mv_cat"], r["dv_cat"], r["board_family"], r["bet_size"]
    bs_n = normalize_bs(bs)
    is_dyn = bf in DYNAMIC
    weak_mv_no2nd = mv in AIR | {"low_pair", "underpair", "third_pair"}
    if bs_n == "m" and is_dyn and dv == "oesd" and weak_mv_no2nd:
        return "FOLD"
    return base


def vol3_v8_turn(r):
    """Vol3 v8 詳細 (参考)."""
    mv, dv, bf, bs = r["mv_cat"], r["dv_cat"], r["board_family"], r["bet_size"]
    weak_mv = mv in AIR | {"low_pair", "underpair", "third_pair", "second_pair"}
    is_dyn = bf in DYNAMIC
    if bs == "overbet_185p":
        if weak_mv and dv in WEAK_DRAWS: return "FOLD"
        if bf == "dry_high" and mv in AIR and dv == "flush_draw": return "FOLD"
        if is_dyn and mv in AIR and dv == "oesd": return "FOLD"
        if is_dyn and mv == "top_pair" and dv == "no_draw": return "FOLD"
        return "CALL"
    else:
        if mv in AIR and dv == "no_draw": return "FOLD"
        weak_mv_no2nd = mv in AIR | {"low_pair", "underpair", "third_pair"}
        if is_dyn and weak_mv_no2nd and dv in WEAK_DRAWS: return "FOLD"
        if is_dyn and dv == "oesd" and weak_mv_no2nd: return "FOLD"
        return "CALL"


# River 改善
def vol2_river_current(r):
    """現状 Vol2 River (ch04 + ch07 補正)."""
    mv, bf, bs = r["mv_cat"], r["board_family"], r["bet_size"]
    cat = hand_cat(r)
    base = vol2_matrix(cat, bs)
    is_dyn = bf in DYNAMIC
    bs_n = normalize_bs(bs)
    # ch07 補正
    if mv in {"straight", "flush", "trips"}: return "CALL"  # 絶対強さ
    if mv == "top_pair" and bf in DRY and bs_n in {"l", "o"}: return "CALL"
    if is_dyn and mv in {"top_pair", "two_pair"} and bs_n == "o": return "CALL"
    return base


def vol2_river_v2(r):
    """+R4: fullhouse/quads → RAISE (vs allin の例外)."""
    base = vol2_river_current(r)
    mv, bs = r["mv_cat"], r["bet_size"]
    bs_n = normalize_bs(bs)
    if mv == "quads": return "RAISE"
    if mv == "fullhouse" and bs_n != "o": return "RAISE"
    if mv == "fullhouse" and bs_n == "o": return "CALL"  # slowplay
    return base


def vol2_river_v3(r):
    """v2 + Cash all-in での best_hand → CALL (raise option ありの場合は v2 のまま)."""
    return vol2_river_v2(r)


def vol3_v14_river(r):
    """Vol3 v14 (bucket-based、参考上限)."""
    eb = r["equity_bucket"]
    bs = r["bet_size"]
    mv = r["mv_cat"]
    eqp = r.get("eq_percentile")
    bf = r["board_family"]
    is_dyn = bf in DYNAMIC
    if mv == "quads": return "RAISE"
    if mv == "fullhouse" and bs != "overbet": return "RAISE"
    if mv == "fullhouse" and bs == "overbet": return "CALL"
    if bs == "allin":
        if eb == "best_hands" and pd.notna(eqp) and eqp > 0.85: return "CALL"
        if bf in DRY and mv in {"set", "trips", "straight", "flush"}: return "CALL"
        if eb == "good_hands" and mv in {"straight", "flush", "trips"}: return "CALL"
        if bf == "monotone" and mv == "flush": return "CALL"
        if is_dyn and mv == "top_pair" and eb in {"weak_hands", "good_hands"}: return "CALL"
        return "FOLD"
    if mv in {"straight", "flush", "trips"}: return "CALL"
    if mv == "top_pair" and bf in DRY and bs in {"overbet", "med_100p"}: return "CALL"
    if eb == "best_hands":
        if pd.notna(eqp) and eqp > 0.96: return "RAISE"
        return "CALL"
    if eb == "good_hands": return "CALL"
    if eb == "weak_hands":
        if bs == "overbet":
            if is_dyn and mv == "two_pair": return "CALL"
            return "FOLD"
        if bs == "med_100p": return "FOLD"
        return "CALL"
    return "FOLD"


def best_ev(r):
    evs = [e for e in [r.get("ev_fold"), r.get("ev_call"), r.get("ev_raise")] if pd.notna(e)]
    return max(evs) if evs else float("nan")


def ev_of(r, p):
    if p == "FOLD": return r["ev_fold"]
    if p == "CALL": return r["ev_call"]
    return r["ev_raise"] if pd.notna(r["ev_raise"]) else r["ev_call"]


def ev_gap(r):
    evs = sorted([e for e in [r.get("ev_fold"), r.get("ev_call"), r.get("ev_raise")] if pd.notna(e)], reverse=True)
    return evs[0] - evs[1] if len(evs) >= 2 else None


def turn_bs_label(s):
    if "_R2." in s: return "small_25p"
    if "_R6." in s: return "med_67p"
    if "_R16" in s: return "overbet_185p"
    if "_R10" in s: return "overbet_117p"
    return "other"


def river_bs_label(s):
    if "_R89" in s: return "allin"
    if "_R35" in s: return "allin"
    if "_R16" in s: return "overbet"
    if "_R13" in s: return "med_100p"
    if "_R7" in s or "_R8" in s: return "med_75p"
    if "_R4" in s: return "small_30p"
    return "other"


def evaluate(sub, formulas, baseline_loss, label):
    sub = sub.copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev, axis=1)
    sub["ev_gap"] = sub.apply(ev_gap, axis=1)
    sub = sub[sub["ev_gap"].notna()].copy()
    print(f"\n  [{label}] n={len(sub)}, huge_gap n={len(sub[sub['ev_gap']>0.5])}")
    print(f"  baseline (always_CALL huge_loss): {baseline_loss:.4f} BB")
    print(f"\n  {'公式':40s} {'acc':>7s} {'huge_loss':>12s} {'reduction':>11s}")
    for name, f in formulas:
        s = sub.copy()
        s["pred"] = s.apply(f, axis=1)
        s["ev_p"] = s.apply(lambda r: ev_of(r, r["pred"]), axis=1)
        s["loss"] = s["best_ev"] - s["ev_p"]
        acc = (s["pred"] == s["modal"]).mean() * 100
        huge = s[s["ev_gap"] > 0.5]
        huge_l = huge["loss"].mean()
        reduction = (baseline_loss - huge_l) / baseline_loss * 100
        marker = " ⭐" if reduction > 90 else ""
        print(f"    {name:40s} {acc:6.1f}% {huge_l:10.4f}BB {reduction:9.1f}%{marker}")


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)

    # ─────────── Turn ───────────
    print("=" * 78)
    print("Turn defense — Vol2 改善検証 (Cash 100bb)")
    print("=" * 78)
    turn = df[(df["street"] == "turn") & (df["action_context"] == "defense") &
              df["source_path"].str.contains("def_cash100_bb_turn") &
              df["ev_call"].notna() & df["ev_fold"].notna()].copy()
    turn["bet_size"] = turn["source_path"].apply(turn_bs_label)
    # baseline
    turn_b = turn.copy()
    turn_b["best_ev"] = turn_b.apply(best_ev, axis=1)
    turn_b["ev_gap"] = turn_b.apply(ev_gap, axis=1)
    turn_b = turn_b[turn_b["ev_gap"].notna() & (turn_b["ev_gap"] > 0.5)]
    baseline = (turn_b["best_ev"] - turn_b["ev_call"]).mean()

    evaluate(turn, [
        ("Vol2 現状 (ch04 + ch06)", vol2_turn_current),
        ("Vol2 + T1 (vs OB weak+weak FOLD)", vol2_turn_v2),
        ("Vol2 + T1+T3 (medium 拡張)", vol2_turn_v3),
        ("Vol2 + T1+T3+T4 (全 OESD)", vol2_turn_v4),
        ("Vol3 v8 (詳細、上限)", vol3_v8_turn),
    ], baseline, "Cash 100bb Turn defense")

    # ─────────── River ───────────
    print("\n" + "=" * 78)
    print("River defense — Vol2 改善検証 (Cash 100bb)")
    print("=" * 78)
    riv = df[(df["street"] == "river") & (df["action_context"] == "defense") &
             df["source_path"].str.contains("def_cash100_bb_river") &
             df["ev_call"].notna() & df["ev_fold"].notna() &
             df["equity_bucket"].notna() & (df["equity_bucket"] != "")].copy()
    riv["bet_size"] = riv["source_path"].apply(river_bs_label)
    riv_b = riv.copy()
    riv_b["best_ev"] = riv_b.apply(best_ev, axis=1)
    riv_b["ev_gap"] = riv_b.apply(ev_gap, axis=1)
    riv_b = riv_b[riv_b["ev_gap"].notna() & (riv_b["ev_gap"] > 0.5)]
    baseline = (riv_b["best_ev"] - riv_b["ev_call"]).mean()

    evaluate(riv, [
        ("Vol2 現状 (ch04 + ch07)", vol2_river_current),
        ("Vol2 + R4 (FH/quads RAISE)", vol2_river_v2),
        ("Vol3 v14 (bucket-based、上限)", vol3_v14_river),
    ], baseline, "Cash 100bb River defense")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
