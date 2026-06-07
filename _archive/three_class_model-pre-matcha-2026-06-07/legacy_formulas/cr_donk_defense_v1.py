#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""CR / Donk defense v1 — BTN IP defender vs BB's check-raise / donk lines.

新規 Tier C 公式群 (2026-06-06)。既存 v9b/v10/v15 は BB defender 専用で、
**BTN IP × BB の CR/donk ライン** はカバーしていなかった。本ファイルで 5 公式を新設する。

データ源 (PROBE_PRIORITY_FINDINGS.md §5 Tier C / §6.1 / §7-4):
- `probe_phase3_stats.json`:
    * A_cash_cr_def_full  : opp_polarization=0.693, opp_strong=24%, opp_weak=45%  (18 boards)
    * A_cash_donk_def_full: opp_polarization=0.782, opp_strong=17%, opp_weak=61%  (18 boards)
- `probe_phase5_stats.json` (multi-street walker):
    * P5_D_turn_donk_def : opp_polarization=0.696, opp_strong=16%, opp_weak=54%   (6 spots)
    * P5_D_turn_cr_def   : opp_polarization=0.808, opp_strong=46%, opp_weak=35%   (6 spots, value-heavy ★)
    * P5_D_river_donk_def: opp_polarization=0.663, opp_strong=43%, opp_weak=23%   (mid-heavy)

★ 中核インサイト (§7-4):
**「turn donk と turn CR で BTN defense 方針が真逆」**

- **turn donk** : BB の air 54% / strong 16% → BTN は **wider call** が正解。
- **turn CR**   : BB の strong 46%        → BTN は **tighter fold**、TP は wet なら捨てる。

このギャップを 5 公式で明示的に表現する。
"""
from __future__ import annotations

# ── 共通定数 ────────────────────────────────────────────
AIR_MV = {"no_made_hand", "ace_high", "king_high"}
WEAK_PAIR_MV = {"low_pair", "underpair", "third_pair"}
MIDDLING_PAIR_MV = {"second_pair", "middle_pair"}
STRONG_MADE = {"set", "trips", "straight", "flush", "fullhouse", "quads"}

DRY = {"dry_high", "low_dry"}
WET = {"dynamic", "dynamic_2tone", "monotone"}

STRONG_DRAW_DV = {"combo_draw", "flush_draw", "oesd"}
WEAK_DRAW_DV = {"gutshot", "bdfd_bdsd", "bdfd", "bdsd"}


def _is_strong_draw(dv: str | None) -> bool:
    return dv in STRONG_DRAW_DV


def _is_any_draw(dv: str | None) -> bool:
    return dv in STRONG_DRAW_DV or dv in WEAK_DRAW_DV


# ════════════════════════════════════════════════════════
#  (a) flop_cr_def_v1
# ════════════════════════════════════════════════════════
def flop_cr_def_v1(mv, dv, bf, opp_polarization=0.693):
    """BTN IP defender, flop で BB が cbet を CR してきた局面。

    opp range: polarization 0.69, strong 24%, weak 45% (moderately polar).
    → 24% は本物 (top set / 2P+) が混ざる。AIR + weak draw を切るのが分水嶺。

    優先順:
    1. STRONG_MADE (set+) → RAISE (value で被せ返す)
    2. overpair / top_pair → CALL (典型的 bluffcatcher、opp の 45% air を相手に)
    3. middle_pair + strong_draw → CALL (合算 equity 充分)
    4. AIR + strong_draw → CALL (semi-bluff continue)
    5. それ以外 (AIR + weak/no draw, weak_pair) → FOLD (opp 24% strong に勝てない)
    """
    if mv in STRONG_MADE:
        return "RAISE"
    if mv in {"overpair", "top_pair"}:
        return "CALL"
    if mv == "two_pair":
        return "RAISE"  # opp の 24% strong とも戦える
    if mv in MIDDLING_PAIR_MV and _is_strong_draw(dv):
        return "CALL"
    if mv in AIR_MV and _is_strong_draw(dv):
        return "CALL"
    # weak pair / middle pair w/o draw / AIR w/ weak-or-no draw
    return "FOLD"


# ════════════════════════════════════════════════════════
#  (b) flop_donk_def_v1
# ════════════════════════════════════════════════════════
def flop_donk_def_v1(mv, dv, bf, opp_polarization=0.782):
    """BTN IP defender, flop で BB が cbet 前に donk してきた局面。

    opp range: polarization 0.78, strong 17%, **weak 61%** (very air heavy).
    → BB の donk は OOP らしい anti-pattern で、61% が air。
    → CR よりも **大幅に wider call** で OK。「絶対トラッシュ」のみ降りる。

    優先順:
    1. STRONG_MADE → RAISE
    2. top_pair / overpair → RAISE (opp 61% air を狩る、しかも IP)
    3. middling_pair (with or w/o draw) → CALL
    4. AIR + any draw (strong or weak) → CALL (opp 61% air が dominate)
    5. weak_pair → CALL (opp の 17% strong には負けるが 61% air に勝てる)
    6. AIR + no draw → FOLD (絶対トラッシュのみ降りる)
    """
    if mv in STRONG_MADE:
        return "RAISE"
    if mv in {"overpair", "top_pair"}:
        return "RAISE"  # IP value + opp air heavy → 被せ返して fold equity
    if mv in MIDDLING_PAIR_MV:
        return "CALL"
    if mv in WEAK_PAIR_MV:
        return "CALL"  # 61% air dominates
    if mv in AIR_MV and _is_any_draw(dv):
        return "CALL"  # どんな draw でも equity あり
    # AIR + no draw (絶対トラッシュ)
    return "FOLD"


# ════════════════════════════════════════════════════════
#  (c) turn_donk_def_v1
# ════════════════════════════════════════════════════════
def turn_donk_def_v1(mv, dv, bf, opp_polarization=0.696):
    """BTN IP defender, turn で BB が donk してきた (flop X-X の後)。

    opp range: polarization 0.70, strong 16%, weak 54%.
    → BB の turn donk も air 寄り (X-X からの突然の attack は range mismatch)。
    → ただし turn は pot odds が flop より tight になるので、flop donk より
      やや selective に。AIR + weak draw は降ろす。

    優先順:
    1. STRONG_MADE → RAISE
    2. top_pair / overpair → CALL (CR でない donk なので safer call)
    3. middling_pair + strong_draw → CALL
    4. AIR + strong_draw → CALL (semi-bluff equity 残し)
    5. それ以外 → FOLD (turn pot odds は flop より tight)
    """
    if mv in STRONG_MADE:
        return "RAISE"
    if mv in {"overpair", "top_pair"}:
        return "CALL"
    if mv in MIDDLING_PAIR_MV and _is_strong_draw(dv):
        return "CALL"
    if mv in AIR_MV and _is_strong_draw(dv):
        return "CALL"
    # weak pair / middling w/o strong draw / AIR w/ weak-or-no draw
    return "FOLD"


# ════════════════════════════════════════════════════════
#  (d) turn_cr_def_v1  ★ turn donk と真逆方針
# ════════════════════════════════════════════════════════
def turn_cr_def_v1(mv, dv, bf, opp_polarization=0.808, bet_size="med_50p"):
    """BTN IP defender, turn で barrel に対し BB が CR してきた局面。

    opp range: polarization 0.81, **strong 46%** (VERY value-heavy).
    → BB の turn CR は「flop call → turn raise」なので value が乗りやすい。
    → ★turn donk と真逆: **tighter fold** が正解。

    優先順:
    1. STRONG_MADE (set+) → CALL/RAISE (call down できる only)
    2. two_pair → CALL (call down)
    3. top_pair × dry board → CALL (opp 46% strong でも straight/flush は board 上ない)
    4. top_pair × wet board → FOLD (opp 46% strong は straight/flush 完成濃厚)
    5. overpair × dry → CALL、wet → FOLD
    6. それ以外 (middling, AIR) → FOLD (opp value-heavy で勝ち目薄)
    7. bet_size が overbet/allin なら全体的にもう 1 段 tighten
    """
    is_dry = bf in DRY
    is_big = bet_size in {"overbet", "allin", "med_100p"}

    if mv in {"fullhouse", "quads"}:
        return "RAISE"
    if mv in {"set", "trips", "straight", "flush"}:
        # 強メイドは call down (nuts は raise しても良いが、CR 相手では trap が多い)
        return "CALL"
    if mv == "two_pair":
        return "FOLD" if (is_big and not is_dry) else "CALL"
    if mv in {"top_pair", "overpair"}:
        if is_dry and not is_big:
            return "CALL"  # bluffcatch on dry texture
        return "FOLD"      # wet or big size → opp 46% strong に勝てない
    # middling pair, weak pair, AIR: opp value-heavy 相手は全て降りる
    return "FOLD"


# ════════════════════════════════════════════════════════
#  (e) river_donk_def_v1
# ════════════════════════════════════════════════════════
def river_donk_def_v1(mv, eb, bf, opp_polarization=0.663, bet_size="med_50p"):
    """BTN IP defender, river で BB が donk してきた (turn X-X の後)。

    opp range: polarization 0.66 (意外と polar じゃない、**mid 多**), strong 43%, weak 23%.
    → river なので showdown 直前。opp は mid-heavy で bluff 比率は低め。
    → equity_bucket を主軸に判定する (mv だけだと粗い)。

    優先順:
    1. STRONG_MADE (straight+) → CALL (常 value、raise は trap 警戒で控えめ)
    2. eb == best_hands → CALL (どんな mv でも nut tier 確定)
    3. eb == good_hands → bet_size 依存 (small → CALL / big → FOLD)
    4. eb == weak/trash → FOLD (極小 bet なら CALL 余地、それ以外は降りる)
    """
    is_small = bet_size in {"small", "small_33p", "med_33p"}
    is_big = bet_size in {"overbet", "allin", "med_100p"}

    # 強メイドは常に call (full house 以上は raise でも可)
    if mv in {"fullhouse", "quads"}:
        return "RAISE"
    if mv in {"straight", "flush"}:
        return "CALL"

    # eb 主軸 (river なので equity_bucket が支配的)
    if eb == "best_hands":
        return "CALL"
    if eb == "good_hands":
        # opp mid-heavy: small なら抑えて call、big なら降りる
        if is_big:
            return "FOLD"
        return "CALL"
    # weak_hands / trash
    if is_small:
        # 極小 bet のみ pot odds で call
        return "CALL"
    return "FOLD"


# ════════════════════════════════════════════════════════
#  Test harness
# ════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("CR/Donk Defense v1 — sanity tests")
    print("=" * 60)

    # ── Test 1: AKo on Ks7d2c (TP, dry) facing CR vs donk ──
    print("\n[Test 1] AKo on Ks7d2c (top_pair, dry_high)")
    print("  flop CR  (opp polar 0.69, weak 45%):",
          flop_cr_def_v1(mv="top_pair", dv=None, bf="dry_high"))
    print("  flop donk (opp polar 0.78, weak 61%):",
          flop_donk_def_v1(mv="top_pair", dv=None, bf="dry_high"))
    # 期待: CR → CALL (bluffcatcher) / donk → RAISE (opp air heavy)

    # ── Test 2: JJ on Th9c7s (overpair, wet) facing turn CR vs donk ──
    print("\n[Test 2] JJ on Th9c7s turn Qd (overpair → now under straight, dyn)")
    print("  turn donk (opp polar 0.70, weak 54%):",
          turn_donk_def_v1(mv="overpair", dv=None, bf="dynamic"))
    print("  turn CR   (opp polar 0.81, strong 46%):",
          turn_cr_def_v1(mv="overpair", dv=None, bf="dynamic", bet_size="med_50p"))
    # 期待: donk → CALL (opp air-heavy) / CR → FOLD (wet + value-heavy)

    # ── Test 3: AIR + strong draw on flop ──
    print("\n[Test 3] AhJh on Kh7s2d (AIR + flush_draw, dry)")
    print("  flop CR  :", flop_cr_def_v1(mv="ace_high", dv="flush_draw", bf="dry_high"))
    print("  flop donk:", flop_donk_def_v1(mv="ace_high", dv="flush_draw", bf="dry_high"))
    # 期待: 両方 CALL (semi-bluff continue)

    # ── Test 4: AIR + no draw ──
    print("\n[Test 4] QJo on Ks7d2c (AIR + no draw, dry)")
    print("  flop CR  :", flop_cr_def_v1(mv="no_made_hand", dv=None, bf="dry_high"))
    print("  flop donk:", flop_donk_def_v1(mv="no_made_hand", dv=None, bf="dry_high"))
    # 期待: 両方 FOLD (CR でも donk でも no equity は降りる)

    # ── Test 5: top_pair on wet vs dry, turn CR (wet → FOLD finding) ──
    print("\n[Test 5] Top pair turn CR: wet vs dry")
    print("  TP × dry × med_50p:", turn_cr_def_v1("top_pair", None, "dry_high", bet_size="med_50p"))
    print("  TP × wet × med_50p:", turn_cr_def_v1("top_pair", None, "dynamic", bet_size="med_50p"))
    print("  TP × dry × overbet:", turn_cr_def_v1("top_pair", None, "dry_high", bet_size="overbet"))
    # 期待: dry+small → CALL / wet → FOLD / dry+big → FOLD

    # ── Test 6: river donk, eb-driven ──
    print("\n[Test 6] River donk decisions (opp mid-heavy)")
    print("  best_hands × med_50p:", river_donk_def_v1("top_pair", "best_hands", "dry_high", bet_size="med_50p"))
    print("  good_hands × small  :", river_donk_def_v1("top_pair", "good_hands", "dry_high", bet_size="small_33p"))
    print("  good_hands × overbet:", river_donk_def_v1("top_pair", "good_hands", "dry_high", bet_size="overbet"))
    print("  trash      × small  :", river_donk_def_v1("ace_high", "trash", "dry_high", bet_size="small_33p"))
    print("  trash      × med_50p:", river_donk_def_v1("ace_high", "trash", "dry_high", bet_size="med_50p"))

    # ── Verification: "turn donk = wider call, turn CR = tighter fold" ──
    print("\n" + "=" * 60)
    print("Central insight verification: turn donk vs turn CR で真逆")
    print("=" * 60)
    test_cases = [
        ("top_pair",      None,          "dry_high"),
        ("top_pair",      None,          "dynamic"),
        ("overpair",      None,          "dynamic"),
        ("second_pair",   "oesd",        "dynamic"),
        ("ace_high",      "flush_draw",  "dynamic"),
        ("ace_high",      None,          "dry_high"),
    ]
    print(f"\n{'Hand':<20} {'Board':<12} {'turn_donk':<10} {'turn_CR':<10}")
    print("-" * 56)
    donk_calls = 0
    cr_calls = 0
    for mv, dv, bf in test_cases:
        d = turn_donk_def_v1(mv, dv, bf)
        c = turn_cr_def_v1(mv, dv, bf, bet_size="med_50p")
        if d == "CALL": donk_calls += 1
        if c == "CALL": cr_calls += 1
        label = f"{mv}+{dv or 'no_draw'}"
        print(f"{label:<20} {bf:<12} {d:<10} {c:<10}")
    print("-" * 56)
    print(f"CALL counts: turn_donk={donk_calls} / turn_CR={cr_calls}")
    print(f"=> donk wider call ({donk_calls}) > CR tighter ({cr_calls}): "
          f"{'PASS' if donk_calls > cr_calls else 'FAIL'}")
