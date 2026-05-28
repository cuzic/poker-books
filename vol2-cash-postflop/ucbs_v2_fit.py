#!/usr/bin/env python3
"""
UCBS-v2 fit: base_freq 12 セル確定 + α/β grid search

Step 1: base_freq[(conf, dir, size)] を cash_100bb の combos 加重平均で確定
Step 2: 各 context で (α, β) を grid search で WRMSE 最小化
        式: freq = base_freq + α + β · I(CBS ≥ 7)
        β 適用範囲: CBS ≥ 7 (strong/nut) のみ
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
    HP_TABLE,
    extract_board_features, parse_board_type, is_polarize_board,
    calc_confidence,
)
from calc import classify_board_type7


# 3BP IP は UCBS-v2 スコープ外 (LSPRS で別設計予定)
SCOPE_CTX = ["cash_100bb", "mtt_25bb"]


def load_records():
    """全データから records を作る (ctx, cbs, conf, dir, size, gto, n)"""
    records = []

    # Cash
    with open("/home/cuzic/poker-books/cash-postflop/findings/cash_5cat_gto.json") as f:
        cash_data = json.load(f)
    T = 5
    for pos, boards in cash_data.items():
        for board_key, info in boards.items():
            hand_cats = info.get("hand_cats", {})
            bt = parse_board_type(info.get("type", ""))
            board_cards = info.get("board", board_key)
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
                cbs = HP_TABLE[hand_type]
                conf = calc_confidence(cbs, T, bt)
                direction = (cbs >= T)
                records.append({
                    "ctx": "cash_100bb", "cbs": cbs, "conf": conf,
                    "dir": direction, "size": size,
                    "gto": vals["bet_pct"] / 100.0, "n": n,
                    "hand": hand_type,
                })

    # MTT (3BP は除外)
    files = sorted(glob.glob("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_*.jsonl"))
    for fp in files:
        name = Path(fp).stem
        if "3BP" in name:
            continue  # UCBS-v2 のスコープ外
        with open(fp) as f:
            for line in f:
                entry = json.loads(line)
                board = entry["board"]
                try:
                    bt = parse_board_type(classify_board_type7(board))
                except Exception:
                    continue
                # MTT は size=33 一律 (polarize_enabled=False)
                size = 33
                for hand_type, vals in entry.get("hand_agg", {}).items():
                    if hand_type not in HP_TABLE:
                        continue
                    n = vals.get("total", 0)
                    if n < 3:
                        continue
                    cbs = HP_TABLE[hand_type]
                    conf = calc_confidence(cbs, T, bt)
                    direction = (cbs >= T)
                    records.append({
                        "ctx": "mtt_25bb", "cbs": cbs, "conf": conf,
                        "dir": direction, "size": size,
                        "gto": vals["bet_pct"] / 100.0, "n": n,
                        "hand": hand_type,
                    })
    return records


def fit_base_freq(cash_records):
    """cash_100bb 12 セル base_freq を加重平均で確定"""
    agg = defaultdict(lambda: [0.0, 0.0])  # [sum_n_gto, sum_n]
    for r in cash_records:
        k = (r["conf"], r["dir"], r["size"])
        agg[k][0] += r["n"] * r["gto"]
        agg[k][1] += r["n"]
    base = {}
    for k, (ng, n) in agg.items():
        if n > 0:
            base[k] = ng / n
    return base


def predict(r, base_freq, alpha, beta):
    """UCBS-v2 予測: freq = base + α + β·I(CBS≥7)"""
    k = (r["conf"], r["dir"], r["size"])
    # base に無いセル (LOW False 等) は近似値で埋める
    if k not in base_freq:
        # フォールバック: 同じ (conf, size) の dir 平均
        candidates = [v for kk, v in base_freq.items()
                      if kk[0] == r["conf"] and kk[2] == r["size"]]
        if candidates:
            base = sum(candidates) / len(candidates)
        else:
            base = 0.30
    else:
        base = base_freq[k]
    beta_indicator = 1.0 if r["cbs"] >= 7 else 0.0
    freq = base + alpha + beta * beta_indicator
    return max(0.02, min(0.98, freq))


def wrmse(records, base_freq, alpha, beta):
    sse, total_n = 0.0, 0.0
    for r in records:
        pred = predict(r, base_freq, alpha, beta)
        err = pred - r["gto"]
        sse += r["n"] * err * err
        total_n += r["n"]
    return (sse / total_n) ** 0.5


def grid_search(records, base_freq, ctx,
                alpha_range=(-0.10, 0.20, 0.01),
                beta_range=(-0.05, 0.30, 0.01)):
    """(α, β) の grid search で WRMSE 最小化"""
    ctx_records = [r for r in records if r["ctx"] == ctx]
    best = (1.0, 0.0, 0.0)  # (wrmse, alpha, beta)
    a = alpha_range[0]
    while a <= alpha_range[1] + 1e-9:
        b = beta_range[0]
        while b <= beta_range[1] + 1e-9:
            w = wrmse(ctx_records, base_freq, a, b)
            if w < best[0]:
                best = (w, a, b)
            b += beta_range[2]
        a += alpha_range[2]
    return best


def main():
    print("=" * 76)
    print("UCBS-v2 fit: base_freq 確定 + α/β grid search")
    print("=" * 76)

    records = load_records()
    print(f"records: {len(records)} (cash={sum(1 for r in records if r['ctx']=='cash_100bb')}, "
          f"mtt_25bb={sum(1 for r in records if r['ctx']=='mtt_25bb')})")

    # Step 1: base_freq 確定 (cash 100bb)
    cash = [r for r in records if r["ctx"] == "cash_100bb"]
    base_freq = fit_base_freq(cash)

    print("\n[Step 1] base_freq 12 セル (cash 100bb から確定):")
    print(f"{'conf':>5s} {'dir':>5s} {'size':>4s}  {'freq':>6s}")
    for conf in ["HIGH", "MID", "LOW"]:
        for d in [True, False]:
            for size in [33, 116]:
                k = (conf, d, size)
                if k in base_freq:
                    print(f"{conf:>5s} {str(d):>5s} {size:>4d}  {base_freq[k]*100:>5.1f}%")
                else:
                    print(f"{conf:>5s} {str(d):>5s} {size:>4d}  {'—':>6s}")

    # Step 2: grid search per context
    print("\n[Step 2] context per (α, β) grid search:")
    print(f"{'ctx':>14s}  {'α':>6s}  {'β':>6s}  {'WRMSE':>8s}  {'(curr)':>8s}")
    current_wrmse = {"cash_100bb": 0.2143, "mtt_25bb": 0.2079}
    for ctx in SCOPE_CTX:
        w, a, b = grid_search(records, base_freq, ctx)
        cw = current_wrmse.get(ctx, 0.0)
        print(f"{ctx:>14s}  {a:>+5.2f}  {b:>+5.2f}  {w*100:>6.2f}%  {cw*100:>6.2f}%")

    # Step 3: hand 別 bias を α/β fit 後で確認
    print("\n[Step 3] α/β fit 後の hand 別 bias (context 別)")
    for ctx in SCOPE_CTX:
        w, a, b = grid_search(records, base_freq, ctx)
        print(f"\n--- {ctx} (α={a:+.2f}, β={b:+.2f}) ---")
        by_hand = defaultdict(lambda: [0.0, 0.0, 0.0])
        for r in records:
            if r["ctx"] != ctx:
                continue
            pred = predict(r, base_freq, a, b)
            err = pred - r["gto"]
            by_hand[r["hand"]][0] += r["n"] * err
            by_hand[r["hand"]][1] += r["n"]
            by_hand[r["hand"]][2] += r["n"] * err ** 2
        print(f"{'hand':14s} {'HP':>3s} {'combos':>7s} {'bias':>8s} {'wrmse':>8s}")
        for h in ["no_made_hand", "ace_high", "king_high", "low_pair", "underpair",
                  "third_pair", "second_pair", "top_pair", "overpair",
                  "two_pair", "straight", "flush", "set", "trips", "fullhouse"]:
            if h not in by_hand:
                continue
            esum, n, sse = by_hand[h]
            if n > 0:
                print(f"  {h:12s} {HP_TABLE[h]:>3d}  {int(n):>6d}  "
                      f"{esum/n*100:+6.1f}%  {(sse/n)**0.5*100:>6.1f}%")


if __name__ == "__main__":
    main()
