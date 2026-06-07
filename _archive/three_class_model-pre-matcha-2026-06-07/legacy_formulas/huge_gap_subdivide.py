#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""huge_gap_subdivide.py — 優先 3 領域の細粒度集計 + データ充足性チェック。

領域:
  R1: River defense × allin × any
  R2: Turn defense × overbet × air
  R3: Flop defense × any × air

各領域で:
  - 既存 spots 数 (source_path ユニーク数)
  - hand-row 数 / spot
  - mv × dv × board × bucket の cross-tab で huge_gap 集中セル top
  - データ密度 (spot 毎 hand 数) で「もっと欲しい cell」判定
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

DATA = Path("/home/cuzic/poker-books/scripts/three_class_model/dataset_unified.csv")
HUGE = 0.5
AIR = {"no_made_hand", "ace_high", "king_high"}


def ev_gap_row(r):
    if r["action_context"] == "defense":
        evs = [r["ev_fold"], r["ev_call"], r["ev_raise"]]
    else:
        evs = [r["ev_bet"], r["ev_check"]]
    evs = [e for e in evs if pd.notna(e)]
    if len(evs) < 2: return None
    s = sorted(evs, reverse=True)
    return s[0] - s[1]


def turn_bet_size(s):
    if "_R4" in s or "_R5" in s or "_R6" in s: return "small_33"
    if "_R7" in s or "_R8" in s or "_R9" in s: return "med_67"
    if "_R13" in s or "_R14" in s: return "big_100"
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


def section(title, sub):
    print(f"\n{'='*72}\n{title}\n{'='*72}")
    print(f"  rows: {len(sub):,}  unique spots (source_path): {sub['source_path'].nunique():,}")
    if len(sub) == 0: return
    huge = sub[sub["ev_gap"] >= HUGE]
    print(f"  huge_gap rows: {len(huge):,} ({len(huge)/len(sub)*100:.1f}%)  mean_gap={huge['ev_gap'].mean() if len(huge) else 0:.3f} BB")
    print(f"  rows / spot: median={sub.groupby('source_path').size().median():.0f}  max={sub.groupby('source_path').size().max():.0f}")

    print("\n  ▼ pot_type 分布 (rows / huge_rows)")
    for pt in sub["pot_type"].value_counts().index:
        n_all = (sub["pot_type"] == pt).sum()
        n_huge = (huge["pot_type"] == pt).sum() if len(huge) else 0
        m_gap = huge[huge["pot_type"]==pt]["ev_gap"].mean() if n_huge else 0
        n_spot = sub[sub["pot_type"]==pt]["source_path"].nunique()
        print(f"    {pt:10s}  rows={n_all:>6,}  huge={n_huge:>5,}  mean_gap={m_gap:.3f}  spots={n_spot:>3}")


def main():
    df = pd.read_csv(DATA, low_memory=False)
    df["ev_gap"] = df.apply(ev_gap_row, axis=1)
    df = df[df["ev_gap"].notna()].copy()
    df["pot_type"] = df["source_path"].apply(detect_pot_type)
    df["bet_size_river"] = df["source_path"].apply(river_bet_size)
    df["bet_size_turn"] = df["source_path"].apply(turn_bet_size)

    # ─── R1: River defense × allin ───
    r1 = df[(df["street"]=="river") & (df["action_context"]=="defense") & (df["bet_size_river"]=="allin")].copy()
    section("R1: River defense × allin", r1)

    huge1 = r1[r1["ev_gap"] >= HUGE]
    print("\n  ▼ huge 集中 top 12: mv × board × bucket")
    if "equity_bucket" in huge1.columns:
        g = huge1.groupby(["mv_cat","board_family","equity_bucket"]).agg(n=("ev_gap","size"), mean_gap=("ev_gap","mean"), spots=("source_path","nunique")).reset_index()
        g = g.sort_values("n", ascending=False).head(12)
        for _,r in g.iterrows():
            print(f"    {r['mv_cat']:18s} × {r['board_family']:15s} × {r['equity_bucket']:13s}  n={int(r['n']):>4}  mean_gap={r['mean_gap']:.2f} BB  spots={int(r['spots'])}")

    print("\n  ▼ best/good bucket の huge_gap (raise vs call 境界)")
    bg = huge1[huge1["equity_bucket"].isin(["best_hands","good_hands"])]
    g = bg.groupby(["mv_cat","equity_bucket","board_family"]).agg(n=("ev_gap","size"), mean_gap=("ev_gap","mean")).reset_index().sort_values("n", ascending=False).head(10)
    for _,r in g.iterrows():
        print(f"    {r['mv_cat']:14s} × {r['equity_bucket']:13s} × {r['board_family']:15s}  n={int(r['n']):>4}  mean_gap={r['mean_gap']:.2f} BB")

    # ─── R2: Turn defense × overbet × air ───
    r2 = df[(df["street"]=="turn") & (df["action_context"]=="defense") & (df["bet_size_turn"]=="overbet_185") & (df["mv_cat"].isin(AIR))].copy()
    section("R2: Turn defense × overbet × air", r2)

    huge2 = r2[r2["ev_gap"] >= HUGE]
    print("\n  ▼ huge 集中: mv × dv × board × bucket")
    if "equity_bucket" in huge2.columns:
        g = huge2.groupby(["mv_cat","dv_cat","board_family","equity_bucket"]).agg(n=("ev_gap","size"), mean_gap=("ev_gap","mean"), modal_fold=("fold_freq","mean"), modal_call=("call_freq","mean")).reset_index().sort_values("n", ascending=False).head(15)
        for _,r in g.iterrows():
            print(f"    {r['mv_cat']:12s} × {r['dv_cat']:14s} × {r['board_family']:15s} × {r['equity_bucket']:13s}  n={int(r['n']):>3}  gap={r['mean_gap']:.2f}  F={r['modal_fold']:.0%} C={r['modal_call']:.0%}")

    # ─── R3: Flop defense × air ───
    r3 = df[(df["street"]=="flop") & (df["action_context"]=="defense") & (df["mv_cat"].isin(AIR))].copy()
    section("R3: Flop defense × air", r3)

    huge3 = r3[r3["ev_gap"] >= HUGE]
    print("\n  ▼ huge 集中: mv × dv × board × bucket  (gap > 0.5 BB)")
    g = huge3.groupby(["mv_cat","dv_cat","board_family"]).agg(n=("ev_gap","size"), mean_gap=("ev_gap","mean"), modal_fold=("fold_freq","mean"), modal_call=("call_freq","mean")).reset_index().sort_values("n", ascending=False).head(20)
    for _,r in g.iterrows():
        print(f"    {r['mv_cat']:12s} × {r['dv_cat']:14s} × {r['board_family']:15s}  n={int(r['n']):>4}  gap={r['mean_gap']:.2f}  F={r['modal_fold']:.0%} C={r['modal_call']:.0%}")

    print("\n  ▼ weak_draw (BDFD/gutshot) 持ち air は fold すべきか?")
    weak_draw_air = r3[r3["dv_cat"].isin(["onecard_bdfd","twocards_bdfd","gutshot"])]
    g = weak_draw_air.groupby(["dv_cat","board_family"]).agg(n=("ev_gap","size"), huge_n=("ev_gap", lambda x:(x>=HUGE).sum()), huge_gap=("ev_gap", lambda x: x[x>=HUGE].mean() if (x>=HUGE).any() else 0), avg_fold=("fold_freq","mean"), avg_call=("call_freq","mean")).reset_index().sort_values("huge_n", ascending=False).head(15)
    for _,r in g.iterrows():
        print(f"    {r['dv_cat']:14s} × {r['board_family']:15s}  n={int(r['n']):>4}  huge={int(r['huge_n']):>3} (gap={r['huge_gap']:.2f}) GTO: F={r['avg_fold']:.0%} C={r['avg_call']:.0%}")

    # ─── データ充足性 ───
    print(f"\n{'='*72}\nデータ充足性サマリ\n{'='*72}")
    print(f"  R1 (river allin): {r1['source_path'].nunique():>4} spots / {len(r1):>6,} rows")
    print(f"  R2 (turn overbet air): {r2['source_path'].nunique():>4} spots / {len(r2):>6,} rows")
    print(f"  R3 (flop air defense): {r3['source_path'].nunique():>4} spots / {len(r3):>6,} rows")


if __name__ == "__main__":
    main()
