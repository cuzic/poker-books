#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Vol2 Tier 1 マトリックスの統計的検証.

Vol2 の主張:
  - 5×4 守備マトリックス (S/M/W/A/D × s/m/l/o)
  - 攻撃マトリックス (S→BET, M/W/A→CHECK, etc.)
  - 「default 88% 正解、Cash 100bb で huge_gap mistake を 88% 削減」

検証:
  1. Vol2 守備マトリックスを各 street/depth で測定
  2. Vol3 詳細公式 (v7/v8/v9/v14/v15) と比較
  3. always_CALL/always_FOLD baseline と比較
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


# ── Vol2 マトリックス実装 ──
AIR = {"no_made_hand", "ace_high", "king_high"}
WEAK = {"low_pair"}  # A-high, K-high は AIR と分けて W にする
M_HANDS = {"top_pair", "second_pair", "third_pair", "underpair"}
S_HANDS = {"two_pair", "set", "trips", "straight", "flush",
           "fullhouse", "quads", "overpair", "straight_flush"}
STRONG_DRAWS = {"oesd", "flush_draw", "combo_draw", "nut_flush_draw"}


def hand_category(mv: str, dv: str) -> str:
    """Vol2 の S/M/W/A/D 分類."""
    if mv in S_HANDS:
        return "S"
    if mv in M_HANDS:
        return "M"
    if mv == "low_pair":
        return "W"
    # AIR (no_made / A-high / K-high)
    # まずドロー優先 (made が AIR の場合のみ D 扱い)
    if dv in STRONG_DRAWS:
        return "D"
    if mv in {"ace_high", "king_high"}:
        return "W"  # A-high と K-high は W
    return "A"  # no_made_hand + no_draw


def bet_size_category(bs_str: str) -> str:
    """ベットサイズを s/m/l/o に分類. bs_str は context-aware bet size label."""
    if not bs_str: return "m"
    bs = bs_str.lower()
    if "small" in bs or "25p" in bs or "30p" in bs:
        return "s"
    if "med_67" in bs or "med_75" in bs or "med":  # default fallback
        return "m"
    if "med_100" in bs:
        return "l"
    if "overbet" in bs or "allin" in bs:
        return "o"
    return "m"


def normalize_bet_size(bs: str) -> str:
    """raw bet_size label (overbet_185p, med_100p, etc.) を s/m/l/o に変換."""
    if bs in {"s", "m", "l", "o"}: return bs
    bs_lo = bs.lower() if bs else ""
    if "small_25p" in bs_lo or "small_30p" in bs_lo: return "s"
    if "med_67" in bs_lo or "med_75" in bs_lo: return "m"
    if "med_100" in bs_lo: return "l"
    if "overbet_117" in bs_lo: return "l"   # MTT 50bb turn の 117% を l 扱い
    if "overbet_185" in bs_lo or bs_lo == "overbet": return "o"
    if "allin" in bs_lo: return "o"
    return "m"  # default


def vol2_defense(cat: str, bs: str) -> str:
    """Vol2 5x4 守備マトリックス (S/M/W/A/D × s/m/l/o)."""
    bs = normalize_bet_size(bs)
    matrix = {
        "S": {"s": "RAISE", "m": "CALL", "l": "CALL", "o": "CALL"},
        "M": {"s": "CALL",  "m": "CALL", "l": "CALL", "o": "FOLD"},
        "W": {"s": "CALL",  "m": "CALL", "l": "FOLD", "o": "FOLD"},
        "A": {"s": "CALL",  "m": "FOLD", "l": "FOLD", "o": "FOLD"},
        "D": {"s": "CALL",  "m": "CALL", "l": "CALL", "o": "FOLD"},
    }
    return matrix.get(cat, {}).get(bs, "CALL")


def vol2_with_correction(r):
    """Vol2 守備 + 街固有補正."""
    mv = r["mv_cat"]
    dv = r["dv_cat"]
    bs = r["bet_size"]
    bf = r["board_family"]
    cat = hand_category(mv, dv)
    base_action = vol2_defense(cat, bs)

    # Flop 補正: low_pair × no_draw × dry → FOLD
    if r["street"] == "flop":
        if mv in {"low_pair", "third_pair"} and dv == "no_draw":
            if bf in {"dry_high", "low_dry", "dynamic_2tone"}:
                return "FOLD"

    # Turn 補正
    if r["street"] == "turn":
        is_dyn = bf in {"dynamic", "dynamic_2tone", "monotone"}
        weak_mv = mv in AIR | {"low_pair", "underpair", "third_pair", "second_pair"}
        weak_draw = dv in {"no_draw", "twocards_bdfd", "onecard_bdfd", "gutshot"}
        if bs in {"overbet", "overbet_185p", "overbet_117p"}:
            if bf == "dry_high" and mv in AIR and dv in {"flush_draw"}:
                return "FOLD"
            if is_dyn and mv in AIR and dv == "oesd":
                return "FOLD"
            if is_dyn and mv == "top_pair" and dv == "no_draw":
                return "FOLD"
        else:
            if is_dyn and weak_mv and dv in {"oesd"}:
                return "FOLD"

    # River 補正
    if r["street"] == "river":
        is_dyn = bf in {"dynamic", "dynamic_2tone", "monotone"}
        if mv in {"straight", "flush", "trips"}:
            return "CALL"  # 絶対強さ override
        if mv == "top_pair" and bf in {"dry_high", "low_dry"}:
            if bs in {"overbet", "overbet_185p", "med_100p", "l"}:
                return "CALL"
        if is_dyn and mv in {"top_pair", "two_pair"} and bs in {"overbet", "overbet_185p"}:
            return "CALL"

    return base_action


def vol2_simple(r):
    """Vol2 純粋マトリックス (補正なし)."""
    cat = hand_category(r["mv_cat"], r["dv_cat"])
    return vol2_defense(cat, r["bet_size"])


# ── 評価ヘルパー ──
def best_ev(r):
    evs = [e for e in [r.get("ev_fold"), r.get("ev_call"), r.get("ev_raise")] if pd.notna(e)]
    return max(evs) if evs else float("nan")


def ev_of(r, p):
    if p == "FOLD": return r["ev_fold"]
    if p == "CALL": return r["ev_call"]
    return r["ev_raise"] if pd.notna(r["ev_raise"]) else r["ev_call"]


def ev_gap_row(r):
    evs = sorted([e for e in [r.get("ev_fold"), r.get("ev_call"), r.get("ev_raise")] if pd.notna(e)], reverse=True)
    return evs[0] - evs[1] if len(evs) >= 2 else None


def turn_bs(s):
    if "_R2." in s: return "small_25p"
    if "_R6." in s: return "med_67p"
    if "_R16" in s: return "overbet_185p"
    if "_R10" in s: return "overbet_117p"
    return "other"


def river_bs(s):
    if "_R89" in s: return "allin"
    if "_R35" in s: return "allin"
    if "_R16" in s: return "overbet"
    if "_R13" in s: return "med_100p"
    if "_R7" in s or "_R8" in s: return "med_75p"
    if "_R4" in s: return "small_30p"
    return "other"


def flop_bs():
    """For flop defense, we approximate based on cbet size — but most flop spots are m sized.
    実データには明示的 bet_size がないため、すべて m と仮定."""
    return "m"


def evaluate(sub, formulas, ev_fn, label):
    sub = sub.copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev, axis=1)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    sub = sub[sub["ev_gap"].notna()].copy()
    print(f"\n  [{label}] n={len(sub)}")
    for name, f in formulas:
        s = sub.copy()
        s["pred"] = s.apply(f, axis=1)
        s["ev_p"] = s.apply(lambda r: ev_fn(r, r["pred"]), axis=1)
        s["loss"] = s["best_ev"] - s["ev_p"]
        acc = (s["pred"] == s["modal"]).mean() * 100
        mean_l = s["loss"].mean()
        huge = s[s["ev_gap"] > 0.5]
        huge_l = huge["loss"].mean() if len(huge) > 0 else float("nan")
        print(f"    {name:30s} acc={acc:5.1f}% mean={mean_l:7.4f}BB huge(n={len(huge):5d})={huge_l:.4f}BB")


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)

    # ─────────────────────────────────────────────
    # 1. Cash 100bb Flop defense (assume size = "m")
    # ─────────────────────────────────────────────
    print("\n" + "=" * 78)
    print("1. Cash 100bb Flop defense — Vol2 マトリックス vs Vol3 v7")
    print("=" * 78)
    flop_def = df[(df["street"] == "flop") & (df["action_context"] == "defense") &
                   df["source_path"].str.contains("def_cash100_bb_raw") &
                   df["ev_call"].notna() & df["ev_fold"].notna()].copy()
    flop_def["bet_size"] = "m"  # flop assume medium

    # Vol3 v7
    AIR_v7 = {"no_made_hand", "ace_high", "king_high"}
    def flop_v7(r):
        mv, dv = r["mv_cat"], r["dv_cat"]
        bf = r["board_family"]
        if mv in AIR_v7 and dv == "no_draw": return "FOLD"
        if mv in {"low_pair", "third_pair"} and dv == "no_draw" and bf in {"dry_high", "low_dry", "dynamic_2tone"}:
            return "FOLD"
        if mv == "overpair": return "RAISE"
        return "CALL"

    def always_call(r): return "CALL"
    def always_fold(r): return "FOLD"

    evaluate(flop_def, [
        ("always_CALL", always_call),
        ("always_FOLD", always_fold),
        ("Vol2 純粋マトリックス", vol2_simple),
        ("Vol2 + 街補正 (本書 ch05)", vol2_with_correction),
        ("Vol3 v7 (詳細)", flop_v7),
    ], ev_of, "Cash 100bb Flop defense")

    # ─────────────────────────────────────────────
    # 2. Cash 100bb Turn defense
    # ─────────────────────────────────────────────
    print("\n" + "=" * 78)
    print("2. Cash 100bb Turn defense — Vol2 マトリックス vs Vol3 v8")
    print("=" * 78)
    turn_def = df[(df["street"] == "turn") & (df["action_context"] == "defense") &
                   df["source_path"].str.contains("def_cash100_bb_turn") &
                   df["ev_call"].notna() & df["ev_fold"].notna()].copy()
    turn_def["bet_size"] = turn_def["source_path"].apply(turn_bs)

    WEAK_PAIR_LOW = {"low_pair", "underpair", "third_pair"}
    DYNAMIC = {"dynamic", "dynamic_2tone", "monotone"}
    WEAK_DRAWS = {"no_draw", "twocards_bdfd", "onecard_bdfd", "gutshot"}

    def cash_v8(r):
        mv, dv, bs, bf = r["mv_cat"], r["dv_cat"], r["bet_size"], r["board_family"]
        weak_mv = mv in AIR_v7 | WEAK_PAIR_LOW | {"second_pair"}
        is_dyn = bf in DYNAMIC
        if bs == "overbet_185p":
            if weak_mv and dv in WEAK_DRAWS: return "FOLD"
            if bf == "dry_high" and mv in AIR_v7 and dv in {"flush_draw"}: return "FOLD"
            if is_dyn and mv in AIR_v7 and dv == "oesd": return "FOLD"
            if is_dyn and mv == "top_pair" and dv == "no_draw": return "FOLD"
            return "CALL"
        else:
            if mv in AIR_v7 and dv == "no_draw": return "FOLD"
            if is_dyn and weak_mv and dv in WEAK_DRAWS: return "FOLD"
            if is_dyn and dv == "oesd" and weak_mv: return "FOLD"
            return "CALL"

    evaluate(turn_def, [
        ("always_CALL", always_call),
        ("always_FOLD", always_fold),
        ("Vol2 純粋マトリックス", vol2_simple),
        ("Vol2 + 街補正", vol2_with_correction),
        ("Vol3 v8 (詳細)", cash_v8),
    ], ev_of, "Cash 100bb Turn defense")

    # ─────────────────────────────────────────────
    # 3. Cash 100bb River defense
    # ─────────────────────────────────────────────
    print("\n" + "=" * 78)
    print("3. Cash 100bb River defense — Vol2 マトリックス vs Vol3 v14")
    print("=" * 78)
    riv_def = df[(df["street"] == "river") & (df["action_context"] == "defense") &
                  df["source_path"].str.contains("def_cash100_bb_river") &
                  df["ev_call"].notna() & df["ev_fold"].notna() &
                  df["equity_bucket"].notna() & (df["equity_bucket"] != "")].copy()
    riv_def["bet_size"] = riv_def["source_path"].apply(river_bs)

    DRY = {"dry_high", "low_dry"}
    def cash_v14(r):
        eb, mv, eqp = r["equity_bucket"], r["mv_cat"], r.get("eq_percentile")
        bs, bf = r["bet_size"], r["board_family"]
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

    evaluate(riv_def, [
        ("always_CALL", always_call),
        ("always_FOLD", always_fold),
        ("Vol2 純粋マトリックス", vol2_simple),
        ("Vol2 + 街補正", vol2_with_correction),
        ("Vol3 v14 (詳細)", cash_v14),
    ], ev_of, "Cash 100bb River defense")

    # ─────────────────────────────────────────────
    # 4. Summary: 88% reduction claim 検証
    # ─────────────────────────────────────────────
    print("\n" + "=" * 78)
    print("4. Vol2 の '88% reduction' claim 検証")
    print("=" * 78)
    print("""
Vol2 の主張: 「default action からの huge_gap mistake を 88% 削減」

検証法:
  1. always_CALL (Vol2 のデフォルト想定アクション) と Vol2 マトリックスの差
  2. huge_gap (>0.5 BB) loss の削減率
    """)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
