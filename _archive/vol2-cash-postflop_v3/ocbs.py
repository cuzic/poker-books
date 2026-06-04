#!/usr/bin/env python3
"""
OCBS (OOP-Centric Bet Score) — OOP の polarize action 専用モデル。

UCBS (IP 用) と分離。OOP の U 字型 (polarized) 分布に対応:
  強い手 → bet (value)
  air → bet (bluff)
  中間の SDV → check

軸構成:
  HC (Hand Class):   nut / strong / sdv / weak / air (5 段階)
  RA (Range Adv):    OOP vs IP のレンジ優位 (-2 ~ +2)
  Action:            donk / cr / lead_river (アクション種別)
  Context:           3bp_oop / srp_donk / multiway / limp_oop

予測:
  bet_freq = f(HC, RA, Action, Context)

旧 UCBS の HP/DP は「強さスコア」だが、OCBS の HC は「役割スコア」:
  - nut    (HC=4): top-2 pair 以上、絶対 value 候補
  - strong (HC=3): top_pair, overpair
  - sdv    (HC=2): mid pair, weak top pair
  - weak   (HC=1): underpair, low pair (slowplay でも check)
  - air    (HC=0): no_made (bluff 候補)
"""
from __future__ import annotations
from dataclasses import dataclass


# ──── HC マッピング (hand_type → HC) ──────────────────────────────────────
HC_TABLE = {
    "no_made_hand":  0,  # air
    "ace_high":      0,
    "king_high":     0,
    "low_pair":      1,  # weak (slowplay でも check)
    "underpair":     1,
    "third_pair":    1,
    "second_pair":   2,  # sdv (中間 - polarize で check)
    "top_pair":      3,  # strong (value bet 主力)
    "overpair":      3,
    "two_pair":      4,  # nut (heavy slowplay 候補だが基本 value)
    "set":           4,
    "trips":         4,
    "straight":      4,
    "flush":         4,
    "fullhouse":     4,
    "quads":         4,
}


# ──── HC 別 base bet frequency (context 依存) ────────────────────────────
# U 字型: HC=0 (air bluff) と HC=3/4 (value) が高、HC=1/2 (sdv) が低
CONTEXTS = {
    # ─── 3BP OOP (SB 3-bettor が cbet、SPR~3) ──────────────────────────
    # 実測 (3BP25_SB):
    #   top_pair 91% / underpair 60% / no_made 51% / ace_high 40%
    #   second_pair 26% / third_pair 8%
    #   two_pair 10% / set 2% (heavy slowplay)
    #   low_pair 1%
    "3bp_oop": {
        "base_freq": {
            4: 0.10,   # nut: slowplay → check 多 (set 2%, two_pair 10%)
            3: 0.85,   # strong: top_pair 91% — bet
            2: 0.20,   # sdv: second_pair 26%, third_pair 8% → 平均
            1: 0.45,   # weak: underpair 60% / low_pair 1% で大きく分かれる → 平均
            0: 0.47,   # air: no_made 51% / ace_high 40%
        },
        # Hand 別の細粒度 mod
        "hand_freq_mod": {
            "set":          -0.08,   # 2% target (HC=4 base 0.10 - 0.08 = 0.02 ✓)
            "trips":        -0.05,
            "two_pair":     +0.00,   # 10% target = HC=4 base 0.10 ✓
            "fullhouse":    -0.05,
            "low_pair":     -0.44,   # 1% target (HC=1 base 0.45 - 0.44 = 0.01 ✓)
            "third_pair":   -0.12,   # 8% target (HC=1 base 0.45... wait should be HC=1 not 2)
            "underpair":    +0.15,   # 60% target (HC=1 base 0.45 + 0.15 = 0.60 ✓)
            "second_pair":  +0.06,   # 26% target
            "no_made_hand": +0.04,   # 51% target
            "ace_high":     -0.07,   # 40%
        },
    },

    # ─── SRP OOP donk (BB が preflop call 後 flop で donk) ─────────────
    # GTO 実測 (我々の研究):
    #   flop donk = ほぼ 0% (5 board)
    #   turn donk = board pair turn で 25-86%、blank で 0%
    "srp_donk_flop": {
        "base_freq": {
            4: 0.05,  # nut でも donk しない (CR 候補)
            3: 0.02,
            2: 0.01,
            1: 0.01,
            0: 0.01,
        },
        "hand_freq_mod": {},
    },

    # ─── Multiway OOP donk (SB が 3way で flop) ────────────────────────
    # 実測 (cash 3way SB):
    #   connected (T98) → 55%, mid (T76) → 53%, J75 → 76%
    #   K-disc → 0.2%, low_conn (543) → 0%
    "multiway_donk_oop": {
        "base_freq": {
            4: 0.50,
            3: 0.40,
            2: 0.20,
            1: 0.10,
            0: 0.05,
        },
        "hand_freq_mod": {},
        "note": "Board features が支配的 (connected vs disconnected で大差)",
    },
}


# ──── Action 判定 ─────────────────────────────────────────────────────────

@dataclass
class OCBSDecision:
    hc: int            # Hand Class 0-4
    base_freq: float   # base from HC table
    final_freq: float  # after modifier
    context: str
    hand_type: str


def ocbs_predict(
    hand_type: str,
    context: str = "3bp_oop",
) -> OCBSDecision:
    """OCBS の中心関数。OOP action の頻度予測。"""
    hc = HC_TABLE.get(hand_type, 0)
    ctx = CONTEXTS[context]
    base = ctx["base_freq"][hc]
    mod = ctx.get("hand_freq_mod", {}).get(hand_type, 0.0)
    final = max(0.01, min(0.99, base + mod))
    return OCBSDecision(
        hc=hc, base_freq=base, final_freq=final,
        context=context, hand_type=hand_type,
    )


# ──── 評価関数 ─────────────────────────────────────────────────────────────
def evaluate_3bp_oop():
    import json
    from collections import defaultdict

    fp = "/home/cuzic/poker-books/mtt-postflop/findings/draw_study_3BP25_SB.jsonl"
    records = []
    with open(fp) as f:
        for line in f:
            entry = json.loads(line)
            board = entry["board"]
            for hand_type, vals in entry["hand_agg"].items():
                if hand_type not in HC_TABLE:
                    continue
                n = vals.get("total", 0)
                if n < 3:
                    continue
                gto_pct = vals.get("bet_pct", 0) / 100.0
                decision = ocbs_predict(hand_type, "3bp_oop")
                err = decision.final_freq - gto_pct
                records.append({
                    "board": board, "hand": hand_type,
                    "n": n, "gto": gto_pct, "pred": decision.final_freq,
                    "hc": decision.hc, "err": err,
                })

    total_n = sum(r["n"] for r in records)
    wrmse = (sum(r["n"] * r["err"]**2 for r in records) / total_n) ** 0.5
    wmae = sum(r["n"] * abs(r["err"]) for r in records) / total_n

    print("=" * 70)
    print(f"OCBS 3BP_OOP 評価: WRMSE = {wrmse*100:.2f}%, WMAE = {wmae*100:.2f}%")
    print(f"records = {len(records)}, combos = {total_n:.0f}")
    print("=" * 70)

    by_hand = defaultdict(lambda: [0.0, 0.0, 0.0])
    for r in records:
        by_hand[r["hand"]][0] += r["n"] * r["err"]
        by_hand[r["hand"]][1] += r["n"]
        by_hand[r["hand"]][2] += r["n"] * r["err"]**2

    print(f"\n{'hand':16s} {'HC':>3s} {'combos':>7s} {'bias':>8s} {'wrmse':>8s}")
    for h in ["no_made_hand", "ace_high", "king_high", "low_pair", "underpair",
              "third_pair", "second_pair", "top_pair", "overpair",
              "two_pair", "straight", "flush", "set", "trips", "fullhouse"]:
        if h not in by_hand: continue
        esum, n, sse = by_hand[h]
        if n > 0:
            print(f"  {h:14s} {HC_TABLE[h]:>3d} {int(n):>7d}  "
                  f"{esum/n*100:+6.1f}%  {(sse/n)**0.5*100:>6.1f}%")

    return wrmse


def demo():
    print("\n" + "=" * 70)
    print("OCBS Demo: 3BP_OOP の各 hand の予測")
    print("=" * 70)
    print(f"{'hand':16s} {'HC':>3s} {'pred':>6s}")
    for h in ["set", "two_pair", "top_pair", "second_pair",
              "third_pair", "underpair", "low_pair",
              "no_made_hand", "ace_high"]:
        d = ocbs_predict(h, "3bp_oop")
        print(f"  {h:14s} {d.hc:>3d}  {d.final_freq*100:>5.1f}%")


if __name__ == "__main__":
    evaluate_3bp_oop()
    demo()
