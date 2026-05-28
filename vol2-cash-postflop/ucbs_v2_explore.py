#!/usr/bin/env python3
"""
UCBS-v2 データ探査: CBS → freq の中央値曲線を全 context でプールして観察。

目的:
1. (conf, dir, size) 12 セルごとに、CBS → GTO freq が context 横断で安定か確認
2. context 間のずれが「均一 lift (α)」「middle のみ lift (β)」で説明できるか目視
3. base_freq[(conf, dir, size)] の確定用集計
"""
from __future__ import annotations
import json
import glob
from pathlib import Path
from collections import defaultdict
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/cuzic/poker-books/scripts")

from ucbs import (
    HP_TABLE, DP_TABLE,
    extract_board_features, parse_board_type, is_polarize_board,
    calc_confidence,
)
from calc import classify_board_type7


def cash_records():
    """cash_5cat_gto.json から (cbs, conf, dir, size, gto_freq, combos, ctx) を返す"""
    with open("/home/cuzic/poker-books/cash-postflop/findings/cash_5cat_gto.json") as f:
        data = json.load(f)

    scenarios_from_pos = {
        "BTN_BB": "BTN", "CO_BB": "CO", "HJ_BB": "HJ", "UTG_BB": "UTG",
        "SB_BB": "SB", "BTN_SB": "BTN",
    }
    T = 5  # cash の全 position threshold

    out = []
    for pos, boards in data.items():
        scenario = scenarios_from_pos.get(pos, "BTN")
        for board_key, info in boards.items():
            hand_cats = info.get("hand_cats", {})
            board_type_str = info.get("type", "")
            board_cards = info.get("board", board_key)
            bt = parse_board_type(board_type_str)
            try:
                feats = extract_board_features(board_cards)
            except Exception:
                continue
            size = 116 if is_polarize_board(feats) else 33

            for hand_type, vals in hand_cats.items():
                if hand_type not in HP_TABLE:
                    continue
                n = vals.get("combos", 0)
                if n < 5:
                    continue
                gto = vals.get("bet_pct", 0) / 100.0
                hp = HP_TABLE[hand_type]
                cbs = hp  # draw=no_draw だから DP=0
                conf = calc_confidence(cbs, T, bt)
                direction = (cbs >= T)
                out.append({
                    "ctx": "cash_100bb", "cbs": cbs, "conf": conf,
                    "dir": direction, "size": size,
                    "gto": gto, "n": n, "hand": hand_type,
                    "scenario": scenario, "bt": bt,
                })
    return out


def mtt_records():
    """draw_study_*.jsonl から同様に。3BP_OOP は除外。"""
    files = sorted(glob.glob("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_*.jsonl"))
    T = 5
    out = []
    for fp in files:
        name = Path(fp).stem.replace("draw_study_", "")
        if "3BP" in name and "_SB" in name:
            continue  # 3BP_OOP は OCBS
        if "3BP" in name:
            ctx = "mtt_3bp_ip"
        else:
            ctx = "mtt_25bb"  # 全 SBR を mtt_25bb 集約

        with open(fp) as f:
            for line in f:
                entry = json.loads(line)
                board = entry["board"]
                try:
                    feats = extract_board_features(board)
                    bt_str = classify_board_type7(board)
                    bt = parse_board_type(bt_str)
                except Exception:
                    continue
                # MTT は size=33 一律 (polarize_enabled=False 想定)
                size = 33

                for hand_type, vals in entry.get("hand_agg", {}).items():
                    if hand_type not in HP_TABLE:
                        continue
                    n = vals.get("total", 0)
                    if n < 3:
                        continue
                    gto = vals.get("bet_pct", 0) / 100.0
                    hp = HP_TABLE[hand_type]
                    cbs = hp
                    conf = calc_confidence(cbs, T, bt)
                    direction = (cbs >= T)
                    out.append({
                        "ctx": ctx, "cbs": cbs, "conf": conf,
                        "dir": direction, "size": size,
                        "gto": gto, "n": n, "hand": hand_type,
                        "scenario": "MTT", "bt": bt,
                    })
    return out


def aggregate_by_cell(records, key_fn):
    """records を key_fn(r) でグループ化し、加重平均 GTO freq を返す"""
    agg = defaultdict(lambda: {"sum_n": 0.0, "sum_n_gto": 0.0, "n_records": 0})
    for r in records:
        k = key_fn(r)
        agg[k]["sum_n"] += r["n"]
        agg[k]["sum_n_gto"] += r["n"] * r["gto"]
        agg[k]["n_records"] += 1
    out = {}
    for k, v in agg.items():
        if v["sum_n"] > 0:
            out[k] = {
                "freq": v["sum_n_gto"] / v["sum_n"],
                "combos": v["sum_n"],
                "n": v["n_records"],
            }
    return out


def main():
    print("=" * 76)
    print("UCBS-v2 探査: CBS → GTO freq を (conf, dir, size, ctx) でプール")
    print("=" * 76)

    cash = cash_records()
    mtt = mtt_records()
    print(f"cash records: {len(cash)}, MTT records: {len(mtt)}")

    all_records = cash + mtt

    # ─── (1) context 別の CBS → GTO freq (size=33 だけ) ─────────────────
    print("\n[1] context × CBS → GTO freq (size=33 のみ、加重平均)")
    print(f"{'CBS':>4s} | " + " | ".join(f"{c:>14s}" for c in
                                          ["cash_100bb", "mtt_25bb", "mtt_3bp_ip"]))
    cbs_ctx = aggregate_by_cell(
        [r for r in all_records if r["size"] == 33],
        lambda r: (r["cbs"], r["ctx"]),
    )
    for cbs in sorted(set(r["cbs"] for r in all_records)):
        row = [f"{cbs:>4d}"]
        for ctx in ["cash_100bb", "mtt_25bb", "mtt_3bp_ip"]:
            v = cbs_ctx.get((cbs, ctx))
            if v:
                row.append(f"{v['freq']*100:>5.1f}% (n={int(v['combos']):>6d})")
            else:
                row.append(f"{'—':>14s}")
        print(" | ".join(row))

    # ─── (2) (conf, dir, size) × ctx ─────────────────────────────────────
    print("\n[2] (conf, dir, size) × ctx → GTO freq")
    cell_ctx = aggregate_by_cell(
        all_records,
        lambda r: (r["conf"], r["dir"], r["size"], r["ctx"]),
    )
    print(f"{'conf':>5s} {'dir':>4s} {'size':>4s} | "
          + " | ".join(f"{c:>14s}" for c in ["cash_100bb", "mtt_25bb", "mtt_3bp_ip"]))
    for conf in ["HIGH", "MID", "LOW"]:
        for d in [True, False]:
            for size in [33, 116]:
                row = [f"{conf:>5s} {str(d):>4s} {size:>4d}"]
                any_filled = False
                for ctx in ["cash_100bb", "mtt_25bb", "mtt_3bp_ip"]:
                    v = cell_ctx.get((conf, d, size, ctx))
                    if v:
                        row.append(f"{v['freq']*100:>5.1f}% (n={int(v['combos']):>6d})")
                        any_filled = True
                    else:
                        row.append(f"{'—':>14s}")
                if any_filled:
                    print(" | ".join(row))

    # ─── (3) cash 100bb での 12-cell base_freq 確定 ──────────────────────
    print("\n[3] cash_100bb 12-cell base_freq (combos 加重平均)")
    cash_cells = aggregate_by_cell(
        [r for r in all_records if r["ctx"] == "cash_100bb"],
        lambda r: (r["conf"], r["dir"], r["size"]),
    )
    print(f"{'conf':>5s} {'dir':>4s} {'size':>4s}  {'freq':>6s}  {'combos':>7s}  {'records':>7s}")
    for conf in ["HIGH", "MID", "LOW"]:
        for d in [True, False]:
            for size in [33, 116]:
                v = cash_cells.get((conf, d, size))
                if v:
                    print(f"{conf:>5s} {str(d):>4s} {size:>4d}  "
                          f"{v['freq']*100:>5.1f}%  {int(v['combos']):>7d}  "
                          f"{v['n']:>7d}")

    # ─── (4) MTT との bias を 12-cell で確認 ─────────────────────────────
    print("\n[4] MTT vs cash の 12-cell bias (Δ = mtt - cash)")
    mtt25_cells = aggregate_by_cell(
        [r for r in all_records if r["ctx"] == "mtt_25bb"],
        lambda r: (r["conf"], r["dir"], r["size"]),
    )
    print(f"{'conf':>5s} {'dir':>4s} {'size':>4s}  {'cash':>6s}  {'mtt25':>6s}  {'Δ':>6s}")
    for conf in ["HIGH", "MID", "LOW"]:
        for d in [True, False]:
            for size in [33, 116]:
                c = cash_cells.get((conf, d, size))
                m = mtt25_cells.get((conf, d, size))
                if c and m:
                    delta = (m["freq"] - c["freq"]) * 100
                    print(f"{conf:>5s} {str(d):>4s} {size:>4d}  "
                          f"{c['freq']*100:>5.1f}%  {m['freq']*100:>5.1f}%  "
                          f"{delta:>+5.1f}%")
                elif m:
                    print(f"{conf:>5s} {str(d):>4s} {size:>4d}  "
                          f"{'—':>6s}  {m['freq']*100:>5.1f}%  {'—':>6s}")

    # ─── (5) middle-bump (M(CBS)) 検証: CBS 帯ごとの ctx 間 bias ─────────
    print("\n[5] CBS 帯 × ctx の freq (β の middle bump 候補確認)")
    band_ctx = aggregate_by_cell(
        all_records,
        lambda r: (
            "0-2 air" if r["cbs"] <= 2 else
            "3-4 weak" if r["cbs"] <= 4 else
            "5-6 mid" if r["cbs"] <= 6 else
            "7-8 strong" if r["cbs"] <= 8 else "9+ nut",
            r["ctx"],
        ),
    )
    bands = ["0-2 air", "3-4 weak", "5-6 mid", "7-8 strong", "9+ nut"]
    print(f"{'band':>10s} | " + " | ".join(f"{c:>14s}" for c in
                                            ["cash_100bb", "mtt_25bb", "mtt_3bp_ip"]))
    for b in bands:
        row = [f"{b:>10s}"]
        for ctx in ["cash_100bb", "mtt_25bb", "mtt_3bp_ip"]:
            v = band_ctx.get((b, ctx))
            if v:
                row.append(f"{v['freq']*100:>5.1f}% (n={int(v['combos']):>6d})")
            else:
                row.append(f"{'—':>14s}")
        print(" | ".join(row))


if __name__ == "__main__":
    main()
