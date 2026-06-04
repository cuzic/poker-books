"""Board sub-classification for refined defense analysis.

Goal: split "dry_high" into static (K72) vs connected (KJT), etc.
"""
RANKS = "23456789TJQKA"


def rank_idx(r: str) -> int:
    return RANKS.index(r) if r in RANKS else -1


def board_subfamily(flop: str) -> str:
    """Refined board family from a 6-char flop string like 'K♠7♦2♣' (or KsKd2c)."""
    if not flop or len(flop) < 6:
        return "unknown"
    ranks_str = flop[0] + flop[2] + flop[4]
    suits = [flop[1], flop[3], flop[5]]
    rvs = sorted([rank_idx(r) for r in ranks_str], reverse=True)
    if -1 in rvs:
        return "unknown"
    top, mid, bot = rvs
    n_suits = len(set(suits))
    is_paired = len(set(ranks_str)) < 3
    spread = top - bot
    n_broadway = sum(1 for r in rvs if r >= 8)  # T(8) J(9) Q(10) K(11) A(12)

    # Monotone takes priority
    if n_suits == 1:
        return "monotone"

    # Paired
    if is_paired:
        if top >= 9:  # J or higher
            return "paired_high"
        return "paired_low"

    # Three categories by broadway count
    if n_broadway >= 2:
        if spread <= 4:
            return "broadway_connected"  # KJT, QJT, JT9, T98 (T is broadway)
        return "broadway_disconnected"  # AK4, KQ2
    if n_broadway == 1:
        if spread <= 4:
            return "broadway_connector"  # K98 (K connector w/ 9-8 if T missing)
        return "dry_high"  # K72, A94, Q83, J73, T74
    # n_broadway == 0
    if spread <= 4:
        return "low_connector"  # 765, 654, 543
    return "low_disconnected"  # 742, 853

    # Note: 2tone is captured implicitly by suits but we drop the 2tone axis here for now
