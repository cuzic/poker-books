#!/usr/bin/env python3
"""
ICM (Independent Chip Model) calculator using Malmuth-Harville algorithm.

Computes $EV (dollar equity) for each player given:
- chip stacks
- prize pool payout structure

Also provides:
- bubble factor: ratio of risk premium for losing chips vs gaining chips
- holdings score: chip → $EV conversion (ICM equity)
- holdings premium: tournament-life risk premium (ICM 補正)

Usage:
    python icm_calc.py --stacks "5000,3000,2000" --payouts "50,30,20"
    python icm_calc.py --stacks "5000,3000,2000" --payouts "50,30,20" --bubble-factor 0
    python icm_calc.py --table 9-max-ft

References:
    Malmuth, M. (1987). "Settling Up in Tournaments"
    Harville, D. (1973). "Assigning Probabilities to the Outcomes of Multi-Entry Competitions"
"""

import argparse
import json
from itertools import permutations


def icm_equity(stacks, payouts):
    """
    Compute ICM equity ($EV) for each player.

    Args:
        stacks: list of chip stacks (length n). Zero-chip players are treated
                as already eliminated and assigned the lowest unfilled payouts.
        payouts: list of prize payouts in order (1st, 2nd, ...).
                 Padded with zeros to length n.

    Returns:
        list of $EV values, one per player

    Algorithm:
        Malmuth-Harville: probability of finish order (j_1, ..., j_n) is
            P = prod_{k=1}^{n} stacks[j_k] / (S - sum of stacks of those finishing above)
        $EV[i] = sum over all finish orders of P(order) * payout(rank of i)
    """
    n = len(stacks)
    if n == 0:
        return []
    if any(s < 0 for s in stacks):
        raise ValueError("stacks must be non-negative")

    payouts = list(payouts) + [0.0] * (n - len(payouts))
    payouts = payouts[:n]

    active = [i for i in range(n) if stacks[i] > 0]
    eliminated = [i for i in range(n) if stacks[i] == 0]

    equity = [0.0] * n

    # Eliminated players share the bottom payouts equally
    # (without bust-order info, this is the symmetric assumption)
    if eliminated:
        bottom = payouts[len(active):]
        share = sum(bottom) / len(eliminated)
        for i in eliminated:
            equity[i] = share

    if not active:
        return equity

    active_stacks = [stacks[i] for i in active]
    active_payouts = payouts[:len(active)]
    active_equity = _icm_equity_active(active_stacks, active_payouts)
    for idx, i in enumerate(active):
        equity[i] = active_equity[idx]

    return equity


def _icm_equity_active(stacks, payouts):
    """
    ICM where all stacks are positive. O(n * 2^n) DP over subsets.

    Uses bitmask DP:
        g(S) = P(players in S have already finished, in any order)
        g(empty) = 1
        g(S) = sum_{j in S} g(S \\ {j}) * stacks[j] / (total - sum_stacks(S \\ {j}))

    Then EV[i] = sum over subsets S not containing i:
        g(S) * stacks[i] / (total - sum_stacks(S)) * payouts[|S|]

    For n <= 5, the permutation method is comparable; for n >= 7, this is much faster.
    """
    n = len(stacks)
    if n <= 5:
        return _icm_equity_perm(stacks, payouts)

    total = sum(stacks)
    # subset_sum[mask] = sum of stacks for players in `mask`
    subset_sum = [0] * (1 << n)
    for mask in range(1, 1 << n):
        low = mask & -mask  # lowest bit
        idx = low.bit_length() - 1
        subset_sum[mask] = subset_sum[mask ^ low] + stacks[idx]

    # g[mask] = P(players in mask have finished)
    g = [0.0] * (1 << n)
    g[0] = 1.0
    for mask in range(1, 1 << n):
        s = 0.0
        m = mask
        while m:
            low = m & -m
            j = low.bit_length() - 1
            prev = mask ^ low
            denom = total - subset_sum[prev]
            if denom > 0:
                s += g[prev] * stacks[j] / denom
            m ^= low
        g[mask] = s

    # popcount
    popcount = [bin(m).count("1") for m in range(1 << n)]

    equity = [0.0] * n
    for i in range(n):
        ibit = 1 << i
        ev_i = 0.0
        for mask in range(1 << n):
            if mask & ibit:
                continue
            denom = total - subset_sum[mask]
            if denom <= 0:
                continue
            rank = popcount[mask]  # i finishes in rank+1 (0-indexed)
            if rank >= len(payouts):
                continue
            ev_i += g[mask] * stacks[i] / denom * payouts[rank]
        equity[i] = ev_i
    return equity


def _icm_equity_perm(stacks, payouts):
    """ICM via permutation enumeration. Fine for n <= 6."""
    n = len(stacks)
    equity = [0.0] * n
    for finish_order in permutations(range(n)):
        prob = 1.0
        remaining = list(stacks)
        for player_idx in finish_order:
            total = sum(remaining)
            if total == 0:
                prob = 0.0
                break
            prob *= remaining[player_idx] / total
            remaining[player_idx] = 0
        if prob == 0.0:
            continue
        for rank, player_idx in enumerate(finish_order):
            equity[player_idx] += prob * payouts[rank]
    return equity


def bubble_factor(stacks, payouts, hero_idx, villain_idx, mode="allin"):
    """
    Compute bubble factor: ratio of $EV cost of losing chips vs $EV gain from winning chips.

    bubble_factor = |Δ$EV when hero loses chips| / |Δ$EV when hero wins same chips|

    mode:
        "allin": hero risks min(hero_stack, villain_stack). The standard tournament BF.
        "marginal": tiny delta (1% of hero stack). Linear approximation, ≈1.0.

    Bubble factor > 1.0 means hero pays more $EV per chip lost than gains per chip won.
    Higher bubble factor = tighter calling range required.

    Returns: (bubble_factor, hero_ev_baseline)
    """
    n = len(stacks)
    if hero_idx >= n or villain_idx >= n:
        raise ValueError("invalid player index")

    base_equity = icm_equity(stacks, payouts)
    base_hero = base_equity[hero_idx]

    if mode == "allin":
        delta = min(stacks[hero_idx], stacks[villain_idx])
    else:
        delta = max(1, stacks[hero_idx] // 100)
        delta = min(delta, stacks[villain_idx])

    if delta == 0:
        return 1.0, base_hero

    # Hero wins delta chips from villain
    win_stacks = list(stacks)
    win_stacks[hero_idx] += delta
    win_stacks[villain_idx] -= delta
    win_equity = icm_equity(win_stacks, payouts)
    win_gain = win_equity[hero_idx] - base_hero

    # Hero loses delta chips to villain
    loss_stacks = list(stacks)
    loss_stacks[hero_idx] -= delta
    loss_stacks[villain_idx] += delta
    loss_equity = icm_equity(loss_stacks, payouts)
    loss_cost = base_hero - loss_equity[hero_idx]

    if win_gain == 0:
        return float("inf"), base_hero
    return loss_cost / win_gain, base_hero


def icm_share(stacks, payouts, prize_pool=None):
    """
    Compute holdings score (ICM equity) for each player.

    icm_share[i] = $EV[i] / total_prize_pool * 100  (in %)

    Returns: list of holdings scores (ICM%)
    """
    if prize_pool is None:
        prize_pool = sum(payouts)
    equity = icm_equity(stacks, payouts)
    return [e / prize_pool * 100 for e in equity]


def chip_share(stacks):
    """Chip share % for each player."""
    total = sum(stacks)
    return [s / total * 100 for s in stacks]


def icm_premium(stacks, payouts, hero_idx, mode="allin"):
    """
    Compute holdings premium (ICM 補正) for hero.

    icm_premium = bubble_factor - 1.0  (averaged across opponents)

    Higher premium = more conservative calling required.
    """
    n = len(stacks)
    bfs = []
    for v in range(n):
        if v == hero_idx:
            continue
        if stacks[v] == 0:
            continue
        bf, _ = bubble_factor(stacks, payouts, hero_idx, v, mode=mode)
        bfs.append(bf)
    if not bfs:
        return 0.0
    avg_bf = sum(bfs) / len(bfs)
    return avg_bf - 1.0


# ===== Standard tournament scenarios =====

PRESET_SCENARIOS = {
    "hu": {
        "description": "Heads-up, 50/30 payout",
        "stacks": [5000, 5000],
        "payouts": [50, 30],
    },
    "3-handed-equal": {
        "description": "3-handed FT, equal stacks, 50/30/20 payout",
        "stacks": [3333, 3333, 3334],
        "payouts": [50, 30, 20],
    },
    "3-handed-bigblind": {
        "description": "3-handed FT, big stack 50% / others 25% each",
        "stacks": [5000, 2500, 2500],
        "payouts": [50, 30, 20],
    },
    "bubble-9max-stt": {
        "description": "9-max STT, 4-handed bubble (top 3 paid 50/30/20)",
        "stacks": [4500, 3000, 1500, 1000],
        "payouts": [50, 30, 20],
    },
    "bubble-mtt-tight": {
        "description": "MTT bubble, top 15% paid (representative 10-handed)",
        "stacks": [3000, 2500, 2000, 1500, 1000, 800, 600, 400, 200, 100],
        "payouts": [40, 25, 15, 10, 6, 4, 0, 0, 0, 0],
    },
    "ft-9max": {
        "description": "9-max FT, equal stacks, standard 9-place payout",
        "stacks": [10000] * 9,
        "payouts": [30, 20, 13, 10, 8, 6, 5, 4, 4],
    },
    "ft-3way-uneven": {
        "description": "FT 3-handed, leader vs 2 short stacks",
        "stacks": [6000, 2500, 1500],
        "payouts": [50, 30, 20],
    },
}


def format_table(headers, rows, align=None):
    """Format a markdown table."""
    if align is None:
        align = ["right"] * len(headers)
    sep = []
    for a in align:
        if a == "left":
            sep.append(":---")
        elif a == "right":
            sep.append("---:")
        else:
            sep.append(":---:")
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join(sep) + " |")
    for row in rows:
        out.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stacks", help="comma-separated chip stacks")
    p.add_argument("--payouts", help="comma-separated prize amounts")
    p.add_argument("--preset", choices=PRESET_SCENARIOS.keys(),
                   help="use a preset scenario")
    p.add_argument("--bubble-factor", type=int, metavar="HERO_IDX",
                   help="compute bubble factor for hero (player index)")
    p.add_argument("--all-presets", action="store_true",
                   help="run all preset scenarios")
    p.add_argument("--json", action="store_true", help="output as JSON")
    args = p.parse_args()

    if args.all_presets:
        for key, scen in PRESET_SCENARIOS.items():
            print(f"\n## {key}: {scen['description']}")
            stacks = scen["stacks"]
            payouts = scen["payouts"]
            equity = icm_equity(stacks, payouts)
            chips = chip_share(stacks)
            scores = icm_share(stacks, payouts)
            rows = []
            for i, (s, c, e, sc) in enumerate(zip(stacks, chips, equity, scores)):
                rows.append([f"P{i+1}", s, f"{c:.2f}%", f"{e:.2f}", f"{sc:.2f}%"])
            print(format_table(
                ["Player", "Stack", "Chip%", "$EV", "ICM%"],
                rows,
            ))
        return

    if args.preset:
        scen = PRESET_SCENARIOS[args.preset]
        stacks = scen["stacks"]
        payouts = scen["payouts"]
        print(f"# {args.preset}: {scen['description']}")
    else:
        if not args.stacks or not args.payouts:
            p.error("--stacks and --payouts are required (or use --preset)")
        stacks = [int(x) for x in args.stacks.split(",")]
        payouts = [float(x) for x in args.payouts.split(",")]

    equity = icm_equity(stacks, payouts)
    chips = chip_share(stacks)
    scores = icm_share(stacks, payouts)

    if args.json:
        out = {
            "stacks": stacks,
            "payouts": payouts,
            "icm_equity": equity,
            "chip_share_pct": chips,
            "icm_share_pct": scores,
        }
        if args.bubble_factor is not None:
            bfs = []
            for v in range(len(stacks)):
                if v == args.bubble_factor or stacks[v] == 0:
                    continue
                bf, _ = bubble_factor(stacks, payouts, args.bubble_factor, v)
                bfs.append({"villain": v, "bubble_factor": bf})
            out["bubble_factors"] = bfs
            out["icm_premium"] = icm_premium(stacks, payouts, args.bubble_factor)
        print(json.dumps(out, indent=2))
        return

    rows = []
    for i, (s, c, e, sc) in enumerate(zip(stacks, chips, equity, scores)):
        rows.append([f"P{i+1}", s, f"{c:.2f}%", f"{e:.2f}", f"{sc:.2f}%"])
    print(format_table(
        ["Player", "Stack", "Chip%", "$EV", "ICM%"],
        rows,
    ))

    if args.bubble_factor is not None:
        h = args.bubble_factor
        print(f"\n## Bubble factor for P{h+1}")
        rows = []
        for v in range(len(stacks)):
            if v == h or stacks[v] == 0:
                continue
            bf, _ = bubble_factor(stacks, payouts, h, v)
            rows.append([f"P{v+1}", stacks[v], f"{bf:.3f}"])
        print(format_table(["Villain", "V Stack", "Bubble Factor"], rows))
        hp = icm_premium(stacks, payouts, h)
        print(f"\nICM 補正（平均）: {hp:.3f}")


if __name__ == "__main__":
    main()
