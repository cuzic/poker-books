#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas"]
# ///
"""river_opener_correction.py — Vol3/Vol2 用 opener-position river 補正 (Task #12)

phase5 で確定: opener position 効果は **RIVER ONLY**、turn では無し。

実測 (probe_priority/phase3/phase5 stats):

| Position | turn opp_polarization | river opp_polarization | river opp_nut_pct |
|----------|----------------------:|-----------------------:|------------------:|
| BTN      | 0.79                  | **0.96**               | **0.294**         |
| CO       | 0.75                  | 0.92                   | 0.224             |
| HJ       | 0.79                  | 0.94                   | 0.221             |

→ turn では opener 位置の差はほぼなし (polarization 0.75-0.79)
→ river で初めて差が顕在化 (BTN open は nut_pct 29%、CO/HJ open は 22%)

理由:
  - turn では opp range にまだ draw 多く wide、opener tightness が effect 薄
  - river で「showdown まで残った range」になって初めて opener tightness が利く
  - CO/HJ open は preflop range が tight → river まで進んだ range も nut tier 少
    → CO/HJ open opp の bet は value-heavier (bluff catcher は fold 方向)

実測支持:
  - N_cash_hj_open_river: acc=80.3, huge_loss=3.36 BB
  - N_cash_co_open_river: acc=82.9, huge_loss=3.51 BB
  - P5_C_hj_open_turn:    acc=72.1, huge_loss=1.68 BB
  - P5_C_co_open_turn:    acc=71.9, huge_loss=2.43 BB

Vol2/Vol3 章設計への直接的含意:
  1. **turn 章は opener 共通** で書ける (本ファイルの turn_def_v10_with_opener は NO-OP)
  2. **river 章は opener 別** ロジックを記述 (BTN open vs CO/HJ open で 2 系統)
  3. CO/HJ open 相手の river overbet/med_100p は **bluff catcher fold 寄り** がフレームワーク
  4. BTN open 相手は v15 そのままで OK (BTN は wider open → river range も polar 維持)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mtt_formula_audit import (  # noqa: E402
    DRY_RIVER,
    DYNAMIC_BOARDS,
    DYNAMIC_RIVER,
    river_def_v15,
    turn_def_v10,
)


def _make_row(mv, dv, bf, bs=None, eb=None, eqp=None):
    return {
        "mv_cat": mv,
        "dv_cat": dv,
        "board_family": bf,
        "bet_size": bs if bs is not None else "—",
        "equity_bucket": eb if eb is not None else "good_hands",
        "eq_percentile": eqp,
    }


# ════════════════════════════ River (opener-aware) ════════════
def river_def_v15_with_opener(mv, eb, bf, bet_size, opener_pos, eqp=None, dv="no_draw"):
    """River OOP defender (BB) vs IP bet, **opener-aware**.

    opener_pos: "BTN" | "CO" | "HJ" (これら 3 つにのみデータあり)

    仮説:
      BTN open  → opp_nut_pct=0.294 (相対的 wide bet range、polar 維持)
                 → v15 base そのままで OK
      CO/HJ open → opp_nut_pct=0.221 (tight bet range、**value-heavier**)
                 → bluff catcher (good_hands × med-large bet) は FOLD 寄り
                 → dynamic board の top_pair × overbet も FOLD 寄り (straight 充足率高)

    Override (CO/HJ のみ、5 条件):
      1. good_hands × med_100p × DRY: FOLD (v15 は CALL、value-heavy 相手は fold)
      2. good_hands × overbet (any bf): FOLD (v15 は CALL)
      3. top_pair × overbet × DYNAMIC: FOLD (相手 straight 多い)
      4. top_pair × med_100p × DYNAMIC: FOLD
      5. weak_hands × med_75p (any bf): FOLD (v15 は CALL、bluff 少ない相手にとっては -EV)
    """
    row = _make_row(mv, dv, bf, bs=bet_size, eb=eb, eqp=eqp)
    base = river_def_v15(row)

    if opener_pos in ("CO", "HJ"):
        # CO/HJ open: opp の bet range は value-heavier、bluff catcher fold 推奨
        # 強メイドハンドは base CALL/RAISE を維持
        if mv in {"quads", "fullhouse", "straight", "flush", "trips", "set", "two_pair"}:
            return base
        # allin は v15 専用 logic が支配的、override しない (短絡しすぎると bleed)
        if bet_size == "allin":
            return base

        # Bluff catcher (good_hands) × med-large bet × dry: fold 寄り
        if eb == "good_hands" and bet_size == "med_100p" and bf in DRY_RIVER:
            return "FOLD"
        # good_hands × overbet は全 family で fold 寄り
        if eb == "good_hands" and bet_size == "overbet":
            return "FOLD"
        # Dynamic river × top_pair × big bet: 相手 straight 完成多 → fold
        if mv == "top_pair" and bf in DYNAMIC_RIVER and bet_size in {"med_100p", "overbet"}:
            return "FOLD"
        # weak_hands × med_75p は v15 で CALL になる場合あり、CO/HJ では FOLD
        if eb == "weak_hands" and bet_size == "med_75p":
            return "FOLD"
        return base

    # BTN open は v15 そのまま
    return base


# ════════════════════════════ Turn (NO-OP) ═══════════════════════
def turn_def_v10_with_opener(mv, dv, bf, bet_size, opener_pos):
    """Turn defense, opener-aware **NO-OP**.

    phase5 で確認: turn opp_polarization は opener position でほぼ差なし
    (BTN 0.79 / CO 0.75 / HJ 0.79)。

    → turn では opener position 軸の補正は不要。
    → Vol2/Vol3 の turn 章は **opener position に依存しない共通ロジック** で書ける。

    本関数は意図的に opener_pos を無視する。Vol3 章設計者が
    「turn だけ opener 別 ロジック書くべきか?」と迷ったら、本 NO-OP が答え:
    **書かなくてよい、turn_def_v10 共通で十分**。
    """
    _ = opener_pos  # 明示的に無視
    row = _make_row(mv, dv, bf, bs=bet_size)
    return turn_def_v10(row)


# ════════════════════════════ Tests ═══════════════════════════
if __name__ == "__main__":
    print("=" * 70)
    print("Opener Position Correction — RIVER ONLY (turn = NO-OP)")
    print("=" * 70)

    print("\nopp_polarization / opp_nut_pct by opener (from phase3/5 probe):")
    print("  BTN open: turn=0.79  river=0.96  river_nut=29.4%")
    print("  CO  open: turn=0.75  river=0.92  river_nut=22.4%")
    print("  HJ  open: turn=0.79  river=0.94  river_nut=22.1%")
    print("  → turn: no meaningful diff")
    print("  → river: BTN polar/wide, CO/HJ tighter/value-heavier")

    # ─── Case 1: River good_hands × dry_high × med_100p ──────
    args = dict(mv="top_pair", eb="good_hands", bf="dry_high", bet_size="med_100p", eqp=0.65)
    print("\n[River] good_hands top_pair × dry_high × med_100p:")
    for pos in ("BTN", "CO", "HJ"):
        a = river_def_v15_with_opener(opener_pos=pos, **args)
        print(f"  opener={pos} → {a}")

    # ─── Case 2: River good_hands × overbet ───────────────
    args = dict(mv="second_pair", eb="good_hands", bf="dry_high", bet_size="overbet", eqp=0.55)
    print("\n[River] good_hands × dry_high × overbet:")
    for pos in ("BTN", "CO", "HJ"):
        a = river_def_v15_with_opener(opener_pos=pos, **args)
        print(f"  opener={pos} → {a}")

    # ─── Case 3: River top_pair × dynamic × overbet ───────
    args = dict(mv="top_pair", eb="good_hands", bf="dynamic", bet_size="overbet", eqp=0.45)
    print("\n[River] top_pair × dynamic × overbet:")
    for pos in ("BTN", "CO", "HJ"):
        a = river_def_v15_with_opener(opener_pos=pos, **args)
        print(f"  opener={pos} → {a}  (CO/HJ: opp straight 多)")

    # ─── Case 4: River set × med_100p (strong hand, no diff) ───
    args = dict(mv="set", eb="good_hands", bf="dynamic", bet_size="med_100p", eqp=0.85)
    print("\n[River] set × dynamic × med_100p (strong hand, base maintained):")
    for pos in ("BTN", "CO", "HJ"):
        a = river_def_v15_with_opener(opener_pos=pos, **args)
        print(f"  opener={pos} → {a}")

    # ─── Case 5: River weak_hands × med_75p ────────────────
    args = dict(mv="ace_high", eb="weak_hands", bf="dry_high", bet_size="med_75p", eqp=0.25)
    print("\n[River] weak_hands ace_high × dry_high × med_75p:")
    for pos in ("BTN", "CO", "HJ"):
        a = river_def_v15_with_opener(opener_pos=pos, **args)
        print(f"  opener={pos} → {a}")

    # ─── Turn NO-OP check ────────────────────────────────
    print("\n[Turn] NO-OP check — all openers must produce same action:")
    cases = [
        ("top_pair", "no_draw", "dynamic", "overbet_185"),
        ("second_pair", "oesd", "dynamic_2tone", "small_33"),
        ("low_pair", "no_draw", "dry_high", "other"),
    ]
    for mv, dv, bf, bs in cases:
        acts = [turn_def_v10_with_opener(mv, dv, bf, bs, pos) for pos in ("BTN", "CO", "HJ")]
        ok = "OK (NO-OP)" if len(set(acts)) == 1 else "FAIL (diff)"
        print(f"  {mv:12s} {dv:14s} {bf:14s} {bs:12s} → {acts[0]}  [{ok}]")

    print("\n" + "=" * 70)
    print("Vol2/Vol3 章設計への含意:")
    print("  - turn 章: opener 共通で書く (NO-OP 関数で正当化)")
    print("  - river 章: BTN open 別 / CO+HJ open 別 で 2 ロジック")
    print("  - CO/HJ open 相手の overbet/med_100p は bluff catcher を fold")
    print("=" * 70)
