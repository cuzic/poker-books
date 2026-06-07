"""Enriched feature engineering for 3-class classifier.

Adds hand × board interaction features the v1 baseline lacks:
- has_top_blocker: hand contains a card matching board top rank
- has_pair_blocker: hand contains a card matching the paired-board rank
- bdfd: backdoor flush draw (hand has 1 card of board's dominant suit, board 2-tone+)
- fd_strong: 2 hand cards match a board suit (real flush draw)
- bdsd: backdoor straight draw (hand connects to board within 4 ranks)
- top_pair_kicker: if top pair, what's the other card vs broadway
- equity_proxy: rough TV-like equity score
"""
from __future__ import annotations

import pandas as pd

RANKS = "23456789TJQKA"


def _rank_idx(r: str) -> int:
    return RANKS.index(r) if r in RANKS else -1


def add_v2_features(df: pd.DataFrame) -> pd.DataFrame:
    def per_row(row) -> pd.Series:
        b = str(row.get("board_flop") or "")
        ca = str(row.get("card_a") or "")
        cb = str(row.get("card_b") or "")
        if len(b) < 6 or len(ca) != 2 or len(cb) != 2:
            return pd.Series({
                "has_top_blocker": False,
                "has_2nd_blocker": False,
                "has_bot_blocker": False,
                "fd_strong": False,
                "bdfd": False,
                "bdsd": False,
                "high_blocker": False,  # A or K blocker
                "tp_kicker_bw": False,  # top pair with broadway kicker
                "is_overpair_to_top": False,
            })
        # board ranks/suits
        br = [b[0], b[2], b[4]]
        bs = [b[1], b[3], b[5]]
        rank_vals = sorted([_rank_idx(x) for x in br], reverse=True)
        # board suit composition
        from collections import Counter
        suit_count = Counter(bs)
        dominant_suit, dom_n = suit_count.most_common(1)[0] if suit_count else (None, 0)

        r1, s1 = ca[0], ca[1]
        r2, s2 = cb[0], cb[1]
        i1, i2 = _rank_idx(r1), _rank_idx(r2)
        if i1 < i2:
            i1, i2 = i2, i1
            r1, r2 = r2, r1
            s1, s2 = s2, s1

        top_v, mid_v, bot_v = rank_vals

        # Blockers (by rank)
        has_top_blocker = (i1 == top_v) or (i2 == top_v)
        has_2nd_blocker = (i1 == mid_v) or (i2 == mid_v)
        has_bot_blocker = (i1 == bot_v) or (i2 == bot_v)
        # A/K blocker
        high_blocker = (i1 >= 11) or (i2 >= 11)  # K(11) or A(12)

        # Flush draws
        hand_suits = [s1, s2]
        if dom_n >= 2:  # board has 2+ of one suit
            matches = sum(1 for s in hand_suits if s == dominant_suit)
            fd_strong = matches == 2  # real FD
            bdfd = matches == 1  # backdoor
        else:
            fd_strong = False
            # On rainbow boards, BDFD requires hand suited matching one board card's suit
            # Approximate: hand suited AND s1 in bs (at least one match)
            bdfd = (s1 == s2) and (s1 in bs)

        # BDSD: hand ranks connect with board ranks within 4-rank window
        all_ranks = sorted([i1, i2, top_v, mid_v, bot_v])
        # check if any 5 consecutive (within window 4) appear including both hand cards
        spans = []
        for start in range(max(0, min(i1, i2) - 4), min(13, max(i1, i2) + 5) - 4):
            window = set(range(start, start + 5))
            n_in = sum(1 for r in all_ranks if r in window)
            spans.append(n_in)
        bdsd = max(spans) >= 4 if spans else False

        # Top pair kicker quality
        is_top_pair = (i1 == top_v) ^ (i2 == top_v)  # exactly one matches top
        kicker = (i2 if i1 == top_v else i1) if is_top_pair else -1
        tp_kicker_bw = is_top_pair and kicker >= 9  # J+

        # Overpair check
        is_pair = (r1 == r2)
        is_overpair_to_top = is_pair and i1 > top_v

        return pd.Series({
            "has_top_blocker": has_top_blocker,
            "has_2nd_blocker": has_2nd_blocker,
            "has_bot_blocker": has_bot_blocker,
            "fd_strong": fd_strong,
            "bdfd": bdfd,
            "bdsd": bdsd,
            "high_blocker": high_blocker,
            "tp_kicker_bw": tp_kicker_bw,
            "is_overpair_to_top": is_overpair_to_top,
        })

    extra = df.apply(per_row, axis=1)
    return pd.concat([df, extra], axis=1)


def encode_v2(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    cat_cols = [
        "family", "depth_bucket", "hero_rel", "line", "street",
        "top_rank_bucket", "spread_bucket", "board_family",
        "mv_cat", "dv_cat",
    ]
    num_cols = [
        "paired", "monotone", "twotone", "n_suits",
        "has_A", "has_K", "is_pair", "is_suited",
        "hand_high_vs_top", "spread",
        # v2 additions
        "has_top_blocker", "has_2nd_blocker", "has_bot_blocker",
        "fd_strong", "bdfd", "bdsd",
        "high_blocker", "tp_kicker_bw", "is_overpair_to_top",
    ]
    X = pd.get_dummies(df[cat_cols + num_cols], columns=cat_cols, drop_first=False)
    return X, list(X.columns)
