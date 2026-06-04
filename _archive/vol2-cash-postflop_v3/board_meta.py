"""
board_meta.py — ボードのナット情報・ハンド分類メタデータを計算

API に依存せず純 Python で実行。
- ナットストレート / 非ナットストレート（何枚目のストレートか）
- オーバーペアのランク順
- セット（トップ/ミドル/ボトム）
- フラッシュ可能スーツ・ナットランク
- トップペアのキッカー強度

使い方:
    from board_meta import get_board_meta
    meta = get_board_meta("9s8d7c")
    # → {straights, overpairs, sets, flush_info, top_pair_info, ...}
"""

from collections import Counter

RANKS   = "23456789TJQKA"
RANK_VAL = {r: i for i, r in enumerate(RANKS)}  # '2'→0 ... 'A'→12
SUITS    = "cdhs"

def parse_board(board_str: str) -> list[tuple[str, str]]:
    """'9s8d7c' → [('9','s'),('8','d'),('7','c')]"""
    return [(board_str[i], board_str[i+1]) for i in range(0, len(board_str), 2)]

def get_board_meta(board_str: str) -> dict:
    """ボード文字列からナット情報フルセットを返す"""
    cards    = parse_board(board_str)
    ranks    = [RANK_VAL[c[0]] for c in cards]
    suits    = [c[1] for c in cards]
    rank_set = set(ranks)

    return {
        "board":         board_str,
        "straights":     _straights(ranks, rank_set),
        "sets":          _sets(ranks),
        "overpairs":     _overpairs(ranks),
        "top_pair_info": _top_pair_info(ranks),
        "flush_info":    _flush_info(suits),
    }


# ─────────────────── ストレート ───────────────────
def _straights(ranks: list[int], rank_set: set[int]) -> list[dict]:
    """
    ボードから作れる全ストレートを列挙（ナット順でソート、最強が最後）。
    各エントリ:
      high_card   : ストレートのハイカード文字列 ('J', 'T', ...)
      needed      : 必要な2枚のホールカード（強い順）
      is_nut      : このストレートがナット（=最高）か
      rank_index  : 何番目のストレートか（0=最弱）
    """
    found = []

    # 通常ストレート (6-high → A-high = index4→12)
    for high in range(4, 13):
        s_set = set(range(high - 4, high + 1))
        board_in = [r for r in ranks if r in s_set]
        if len(board_in) < 3:
            continue
        needed_vals = sorted(s_set - rank_set, reverse=True)
        if len(needed_vals) != 2:
            continue
        found.append({
            "high_card": RANKS[high],
            "needed": [RANKS[v] for v in needed_vals],
            "is_nut": False,
            "rank_index": 0,  # 後で付番
        })

    # ウィール (A-2-3-4-5 = 5-high straight)
    wheel = {0, 1, 2, 3, 12}
    board_in_w = [r for r in ranks if r in wheel]
    if len(board_in_w) >= 3:
        needed_w = sorted(wheel - rank_set, reverse=True)
        if len(needed_w) == 2:
            found.insert(0, {
                "high_card": "5",
                "needed": [("A" if v == 12 else RANKS[v]) for v in needed_w],
                "is_nut": False,
                "rank_index": 0,
            })

    # ランク付け（高いほど強い = is_nut は最後の1つ）
    for i, s in enumerate(found):
        s["rank_index"] = i
    if found:
        found[-1]["is_nut"] = True

    return found


# ─────────────────── セット ───────────────────
def _sets(ranks: list[int]) -> dict:
    """
    トップ/ミドル/ボトムセット。ペアボードでは該当カードのみ。
    例: 9-8-7 → {"top":"9","mid":"8","bot":"7"}
         K-K-8 → {"top":"K","kicker":"8"}  (ペアボード = トップのみ意味がある)
    """
    unique = sorted(set(ranks), reverse=True)
    cnt    = Counter(ranks)

    if max(cnt.values()) >= 2:
        # ペアボード: フルハウスになるペアカードだけ
        paired   = [RANKS[r] for r in unique if cnt[r] >= 2]
        unpaired = [RANKS[r] for r in unique if cnt[r] == 1]
        return {
            "type":   "paired_board",
            "pair":   paired[0] if paired else None,
            "quads_card": paired[0] if paired else None,
            "kicker": unpaired[0] if unpaired else None,
        }
    else:
        labels = ["top", "mid", "bot"]
        return {"type": "unpaired", **{labels[i]: RANKS[r] for i, r in enumerate(unique)}}


# ─────────────────── オーバーペア ───────────────────
def _overpairs(ranks: list[int]) -> list[dict]:
    """
    ボードのトップカードより高いポケットペア一覧（強い順）。
    各エントリ:
      rank     : カード文字列 ('A','K',...)
      strength : 'premium'(AA/KK) / 'strong'(QQ/JJ) / 'marginal'(TT以下)
    """
    top = max(ranks)
    result = []
    for r in range(12, top, -1):  # A → top+1
        rank_str = RANKS[r]
        if r >= 11:       strength = "premium"   # AA, KK
        elif r >= 9:      strength = "strong"    # QQ, JJ
        else:             strength = "marginal"  # TT 以下
        result.append({"rank": rank_str, "strength": strength})
    return result


# ─────────────────── トップペア ───────────────────
def _top_pair_info(ranks: list[int]) -> dict:
    """
    トップペアのキッカー強度ガイド。
    top_card  : ボードのトップカード
    tptk_min  : TPTK になる最低キッカー（トップカードの次に強い非ボードカード）
    """
    top = max(ranks)
    top_str = RANKS[top]
    rank_set = set(ranks)

    # TPTK = top pair + nut kicker
    # nut kicker = A（ただしトップカードが A 以外の場合）
    if top < 12:  # top ≠ A
        nut_kicker = "A"
    else:         # top = A
        nut_kicker = "K" if 11 not in rank_set else "Q"

    # 「薄い」トップペアになる最高キッカー = トップカードより1つ下でボードにない最高ランク
    weak_kickers = [RANKS[r] for r in range(top - 1, -1, -1) if r not in rank_set]
    weakest_tpgk = weak_kickers[0] if weak_kickers else None  # GK = good kicker but not nut

    return {
        "top_card":   top_str,
        "nut_kicker": nut_kicker,
        "weak_tpgk":  weakest_tpgk,
    }


# ─────────────────── フラッシュ ───────────────────
def _flush_info(suits: list[str]) -> dict:
    """
    フラッシュ関連情報。
    monotone     : 3枚同スーツか
    fd_suit      : FD 可能スーツ（2トーン時）
    fd_nut_rank  : FD 保有者の中でナットFD になる最小ランク
    """
    cnt = Counter(suits)
    for suit, count in cnt.items():
        if count == 3:
            return {
                "monotone": True,
                "suit": suit,
                "fd_possible": True,
                "fd_nut_rank": "A",
                "note": "モノトーン: フラッシュ完成ハンドも多い",
            }
    for suit, count in cnt.items():
        if count == 2:
            return {
                "monotone": False,
                "suit": suit,
                "fd_possible": True,
                "fd_nut_rank": "A",
                "note": f"2トーン({suit}): ナットFDはA{suit}xx",
            }
    return {
        "monotone": False,
        "fd_possible": False,
        "note": "レインボー: FDなし",
    }


# ─────────────────── ユーティリティ ───────────────────
def summarize(meta: dict) -> str:
    """人間可読なサマリー文字列"""
    lines = [f"Board: {meta['board']}"]

    strs = meta["straights"]
    if strs:
        nut = next((s for s in strs if s["is_nut"]), None)
        non_nuts = [s for s in strs if not s["is_nut"]]
        if nut:
            lines.append(f"  ナットストレート: {nut['needed'][0]}{nut['needed'][1]} "
                         f"({nut['high_card']}-high)")
        if non_nuts:
            # 強い順（rank_index降順）で表示
            lines.append("  非ナットストレート: " + ", ".join(
                f"{''.join(s['needed'])} ({s['high_card']}-high)"
                for s in sorted(non_nuts, key=lambda x: -x["rank_index"])
            ))
    else:
        lines.append("  ストレート: なし")

    sets = meta["sets"]
    if sets["type"] == "unpaired":
        lines.append(f"  セット: トップ={sets.get('top')} "
                     f"ミドル={sets.get('mid')} ボトム={sets.get('bot')}")
    else:
        lines.append(f"  セット(ペアボード): {sets.get('pair')} (クワッズも)")

    ops = meta["overpairs"]
    if ops:
        premium = [o["rank"] for o in ops if o["strength"] == "premium"]
        strong  = [o["rank"] for o in ops if o["strength"] == "strong"]
        marginal= [o["rank"] for o in ops if o["strength"] == "marginal"]
        parts = []
        if premium: parts.append("プレミアム=" + "/".join(r*2 for r in premium))
        if strong:  parts.append("強=" + "/".join(r*2 for r in strong))
        if marginal:parts.append("薄=" + "/".join(r*2 for r in marginal))
        lines.append("  オーバーペア: " + " | ".join(parts))
    else:
        lines.append("  オーバーペア: なし（エース高ボード等）")

    tp = meta["top_pair_info"]
    lines.append(f"  トップペア: {tp['top_card']} | ナットキッカー={tp['nut_kicker']}")

    lines.append(f"  フラッシュ: {meta['flush_info']['note']}")

    return "\n".join(lines)


if __name__ == "__main__":
    test_boards = [
        "9s8d7c",   # 型4 ローウェット (ナットストレート=JT, 非ナット=T6/65)
        "Ks7d2c",   # 型1 ハイドライ
        "Qh8d3s",   # 型2 ハイウェット
        "Ah9h5h",   # 型5 モノトーン
        "KhKd8c",   # 型6a ペア高
        "QhQd8c",   # 型6b ペア高
        "ThTd6s",   # 型6c ペア中
        "Jd7s5c",   # 型3 ロードライ
    ]
    for b in test_boards:
        print(summarize(get_board_meta(b)))
        print()
