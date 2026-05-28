"""
CBet Formula v2 — Additional Factor Exploration
=================================================
Starting from F11_TwoGates (best so far: WMSE=0.02727, R²=0.592),
explore additional factors to reduce systematic over-prediction.

Residual analysis showed:
  - All residuals negative → F11 over-predicts for weak/medium hands
  - Worst: low_pair (-46.8%), third_pair (-39.6%), king_high (-31.6%)
  - Ace boards fit better than non-Ace boards
  - 3BP20 scenario worst (-29.0%)

Hypothesis:
  F12: Hand-modulated gate threshold (weak hands need higher RAS)
  F13: Board top-rank gate modifier (ace boards allow wider betting)
  F14: F12 + F13 combined
  F15: F12 + slowplay correction for strong hands (set/FH)
  F16: Full combined (F12 + F13 + F15)

Usage:
  python3 mtt-postflop/cbet_v2_optuna.py
"""

from __future__ import annotations

import json
import math
import warnings
from pathlib import Path
from dataclasses import dataclass
import numpy as np
import optuna

optuna.logging.set_verbosity(optuna.logging.WARNING)
warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# 1. Constants / Mappings (same as cbet_formula_optuna.py)
# ---------------------------------------------------------------------------

FINDINGS_DIR = Path(__file__).parent / "findings"

SCENARIO_FILES = [
    "draw_study_SRP25.jsonl",
    "draw_study_SRP20.jsonl",
    "draw_study_3BP20.jsonl",
    "draw_study_SRP25_SB.jsonl",
    "draw_study_SRP20_SB.jsonl",
    "draw_study_3BP25_SB.jsonl",
    "draw_study_SRP20_CO.jsonl",
    "draw_study_SRP25_SB_cc.jsonl",
    "draw_study_SRP20_SB_cc.jsonl",
    "draw_study_LIMP25_SB.jsonl",
    "draw_study_LIMP20_SB.jsonl",
]

SCENARIO_META: dict[str, tuple[float, int, int]] = {
    "SRP25":       (25.0, 0, 0),
    "SRP20":       (20.0, 0, 0),
    "3BP20":       (20.0, 1, 0),
    "SRP25_SB":    (25.0, 0, 0),
    "SRP20_SB":    (20.0, 0, 0),
    "3BP25_SB":    (25.0, 1, 0),
    "SRP20_CO":    (20.0, 0, 0),
    "SRP25_SB_cc": (25.0, 0, 0),
    "SRP20_SB_cc": (20.0, 0, 0),
    "LIMP25_SB":   (25.0, 0, 1),
    "LIMP20_SB":   (20.0, 0, 1),
}

BOARD_META: dict[str, tuple[int, int, int]] = {
    "K98":  (2, 13, 5),
    "T98":  (3, 10, 2),
    "K72":  (5, 13, 11),
    "Q83":  (2, 12, 5),
    "J73":  (5, 11, 8),
    "A94":  (1, 14, 10),
    "765":  (6, 7, 2),
    "KJT":  (3, 13, 3),
    "T74":  (5, 10, 6),
    "A72":  (1, 14, 12),
    "742":  (1, 7, 5),    # 742は型1扱い（低ドライ）
    "KK8":  (7, 13, 5),
    "AA7":  (7, 14, 7),
}

# Hand type → normalized strength and SA_score (integer 0-9)
HAND_NORM: dict[str, tuple[float, int]] = {
    "no_made_hand": (0.00, 0),
    "ace_high":     (0.10, 1),
    "king_high":    (0.15, 1),
    "underpair":    (0.20, 2),
    "low_pair":     (0.25, 2),
    "third_pair":   (0.35, 3),
    "second_pair":  (0.45, 5),
    "top_pair":     (0.60, 7),
    "overpair":     (0.72, 7),
    "two_pair":     (0.82, 8),
    "set":          (0.90, 8),
    "trips":        (0.90, 9),
    "flush":        (0.88, 9),
    "straight":     (0.87, 9),
    "fullhouse":    (0.95, 9),
    "quads":        (0.97, 9),
}

# Draw type → draw equity proxy and SB_score (integer 0-5)
DRAW_EQUITY: dict[str, tuple[float, int]] = {
    "no_draw":       (0.00, 0),
    "twocards_bdfd": (0.05, 0),
    "onecard_bdfd":  (0.08, 1),
    "gutshot":       (0.20, 2),
    "oesd":          (0.35, 3),
    "fd":            (0.30, 3),
    "flush_draw":    (0.30, 3),
    "nut_flush_draw":(0.32, 4),
    "fd_gutshot":    (0.40, 4),
    "fd_oesd":       (0.50, 5),
    "combo_draw":    (0.50, 5),
}


# ---------------------------------------------------------------------------
# 2. Data Loading
# ---------------------------------------------------------------------------

@dataclass
class DataPoint:
    y: float          # bet_pct / 100  (target, in [0,1])
    w: float          # weight = n_combos
    ras: float        # no_draw bet_pct / 100
    de: float         # draw equity proxy [0,1]
    hand_norm: float  # hand strength [0,1]
    hand_sa: int      # SA score 0-9 (integer bucket)
    draw_sb: int      # SB score 0-5
    sbr_n: float      # (SBR - 20) / 10
    pf_3bp: float     # 0 or 1
    pf_limp: float    # 0 or 1
    board_type: int   # 1-7
    top_rank_n: float # (rank - 2) / 12  → [0,1], Ace=1.0
    span_n: float     # span / 12        → [0,1]
    fd_board: float   # 1 if board has fd potential
    has_ace: float    # 1.0 if top_rank == Ace (14), else 0.0
    is_slowplay: float # 1.0 if hand is set/FH/quads (strong but GTO slows down)
    scenario_key: str # original scenario for analysis


def load_data() -> list[DataPoint]:
    data: list[DataPoint] = []

    for fname in SCENARIO_FILES:
        fpath = FINDINGS_DIR / fname
        if not fpath.exists():
            print(f"  [WARN] missing: {fname}")
            continue

        with open(fpath) as f:
            for line in f:
                rec = json.loads(line.strip())
                if not rec:
                    continue

                scenario = rec["scenario"]
                if scenario not in SCENARIO_META:
                    continue

                sbr, pf_3bp, pf_limp = SCENARIO_META[scenario]
                sbr_n = (sbr - 20.0) / 10.0

                board_id = rec["board_id"]
                group = rec["group"]
                fd_board = 1.0 if board_id.endswith("_fd") else 0.0

                if group not in BOARD_META:
                    continue
                btype, top_rank, span = BOARD_META[group]
                top_rank_n = (top_rank - 2) / 12.0
                span_n = span / 12.0
                has_ace = 1.0 if top_rank == 14 else 0.0

                draw_agg = rec.get("draw_agg", {})
                nd = draw_agg.get("no_draw", {})
                ras = nd.get("bet_pct", 50.0) / 100.0

                cross = rec.get("cross", {})
                for key, cell in cross.items():
                    avg = cell.get("avg", 0.0)
                    n = cell.get("n", 0)
                    if n == 0:
                        continue

                    parts = key.split("|")
                    if len(parts) != 2:
                        continue
                    hand_str, draw_str = parts

                    hand_info = HAND_NORM.get(hand_str)
                    draw_info = DRAW_EQUITY.get(draw_str)
                    if hand_info is None or draw_info is None:
                        continue

                    hand_n, hand_sa = hand_info
                    de, draw_sb = draw_info

                    is_slowplay = 1.0 if hand_str in ("set", "fullhouse", "quads", "trips") else 0.0

                    y = max(0.0, min(1.0, avg / 100.0))

                    data.append(DataPoint(
                        y=y, w=float(n),
                        ras=ras, de=de, hand_norm=hand_n, hand_sa=hand_sa,
                        draw_sb=draw_sb, sbr_n=sbr_n, pf_3bp=float(pf_3bp),
                        pf_limp=float(pf_limp), board_type=btype,
                        top_rank_n=top_rank_n, span_n=span_n, fd_board=fd_board,
                        has_ace=has_ace, is_slowplay=is_slowplay,
                        scenario_key=scenario,
                    ))

    print(f"Loaded {len(data)} data points from {len(SCENARIO_FILES)} files")
    return data


def to_arrays(data: list[DataPoint]):
    ras    = np.array([d.ras        for d in data])
    de     = np.array([d.de         for d in data])
    hand   = np.array([d.hand_norm  for d in data])
    sbr_n  = np.array([d.sbr_n     for d in data])
    p3bp   = np.array([d.pf_3bp    for d in data])
    plimp  = np.array([d.pf_limp   for d in data])
    topR   = np.array([d.top_rank_n for d in data])
    has_ace= np.array([d.has_ace    for d in data])
    sp     = np.array([d.is_slowplay for d in data])
    y      = np.array([d.y         for d in data])
    w      = np.array([d.w         for d in data])
    w = w / w.sum()
    return ras, de, hand, sbr_n, p3bp, plimp, topR, has_ace, sp, y, w


# ---------------------------------------------------------------------------
# 3. Helpers
# ---------------------------------------------------------------------------

def sig(x): return 1.0 / (1.0 + np.exp(-np.clip(x, -15, 15)))
def wmse(pred, y, w): return float(np.sum(w * (pred - y) ** 2))
def wrmse(pred, y, w): return math.sqrt(wmse(pred, y, w))
def r2(pred, y, w, bm): return 1.0 - wmse(pred, y, w) / bm


# ---------------------------------------------------------------------------
# 4. F11 (reference baseline — replicate best found)
# ---------------------------------------------------------------------------

def f11_two_gates(trial, ras, de, hand, sbr_n, p3bp, plimp, topR, has_ace, sp, fixed=None):
    """F11: Two-gate union (value gate + bluff gate)."""
    def p(name, lo, hi):
        if fixed and name in fixed:
            return fixed[name]
        return trial.suggest_float(name, lo, hi)

    ka = p("ka", 1, 20);  ta = p("ta", 0.05, 0.5)
    kb = p("kb", 1, 20);  tb = p("tb", 0.3, 0.95)
    va = p("va", 0, 5);   ba = p("ba", -5, 3)
    vb = p("vb", 0, 10);  bb = p("bb", -5, 3)
    cs = p("cs", -3, 3)
    cp = p("cp", -5, 0)

    gate_A = sig(ka * (ras - ta))
    gate_B = sig(kb * (ras - tb))

    p_val  = gate_A * sig(va * hand + ba + cs * sbr_n + cp * p3bp)
    p_semi = gate_B * sig(vb * de + bb)

    return np.clip(np.maximum(p_val, p_semi), 0, 1)


# ---------------------------------------------------------------------------
# 5. F12: Hand-modulated gate threshold
#    Weak hands need higher RAS to activate value-bet gate.
#    ta_eff = ta + w_hand * (1 - hand_norm)
# ---------------------------------------------------------------------------

def f12_hand_gate(trial, ras, de, hand, sbr_n, p3bp, plimp, topR, has_ace, sp, fixed=None):
    """F12: value gate threshold scales with hand weakness."""
    def p(name, lo, hi):
        if fixed and name in fixed:
            return fixed[name]
        return trial.suggest_float(name, lo, hi)

    ka    = p("ka", 1, 20);   ta = p("ta", 0.05, 0.5)
    w_adj = p("w_adj", 0, 0.6)   # penalty per unit of hand weakness
    kb    = p("kb", 1, 20);   tb = p("tb", 0.3, 0.95)
    va    = p("va", 0, 5);    ba = p("ba", -5, 3)
    vb    = p("vb", 0, 10);   bb = p("bb", -5, 3)
    cs    = p("cs", -3, 3)
    cp    = p("cp", -5, 0)

    # Weak hands require higher RAS to start betting
    ta_eff = ta + w_adj * (1.0 - hand)   # e.g. low_pair: ta+0.56*w_adj, top_pair: ta+0.40*w_adj

    gate_A = sig(ka * (ras - ta_eff))
    gate_B = sig(kb * (ras - tb))

    p_val  = gate_A * sig(va * hand + ba + cs * sbr_n + cp * p3bp)
    p_semi = gate_B * sig(vb * de + bb)

    return np.clip(np.maximum(p_val, p_semi), 0, 1)


# ---------------------------------------------------------------------------
# 6. F13: Board top-rank gate modifier
#    Ace boards allow looser betting → lower gate threshold
#    ta_eff = ta - at * top_rank_n
# ---------------------------------------------------------------------------

def f13_ace_gate(trial, ras, de, hand, sbr_n, p3bp, plimp, topR, has_ace, sp, fixed=None):
    """F13: gate threshold loosened on high-rank (ace) boards."""
    def p(name, lo, hi):
        if fixed and name in fixed:
            return fixed[name]
        return trial.suggest_float(name, lo, hi)

    ka    = p("ka", 1, 20);   ta = p("ta", 0.05, 0.5)
    at    = p("at", 0, 0.4)   # ace-board loosening factor
    kb    = p("kb", 1, 20);   tb = p("tb", 0.3, 0.95)
    at_b  = p("at_b", 0, 0.3) # ace effect on bluff gate too
    va    = p("va", 0, 5);    ba = p("ba", -5, 3)
    vb    = p("vb", 0, 10);   bb = p("bb", -5, 3)
    cs    = p("cs", -3, 3)
    cp    = p("cp", -5, 0)

    ta_eff = ta - at * topR          # Ace boards: ta-at, low boards: ta
    tb_eff = tb - at_b * topR

    gate_A = sig(ka * (ras - ta_eff))
    gate_B = sig(kb * (ras - tb_eff))

    p_val  = gate_A * sig(va * hand + ba + cs * sbr_n + cp * p3bp)
    p_semi = gate_B * sig(vb * de + bb)

    return np.clip(np.maximum(p_val, p_semi), 0, 1)


# ---------------------------------------------------------------------------
# 7. F14: F12 + F13 combined
# ---------------------------------------------------------------------------

def f14_hand_ace_gate(trial, ras, de, hand, sbr_n, p3bp, plimp, topR, has_ace, sp, fixed=None):
    """F14: Hand-modulated gate + ace-board loosening."""
    def p(name, lo, hi):
        if fixed and name in fixed:
            return fixed[name]
        return trial.suggest_float(name, lo, hi)

    ka    = p("ka", 1, 20);   ta = p("ta", 0.05, 0.5)
    w_adj = p("w_adj", 0, 0.5)
    at    = p("at", 0, 0.4)
    kb    = p("kb", 1, 20);   tb = p("tb", 0.3, 0.95)
    at_b  = p("at_b", 0, 0.3)
    va    = p("va", 0, 5);    ba = p("ba", -5, 3)
    vb    = p("vb", 0, 10);   bb = p("bb", -5, 3)
    cs    = p("cs", -3, 3)
    cp    = p("cp", -5, 0)

    ta_eff = ta + w_adj * (1.0 - hand) - at * topR
    tb_eff = tb - at_b * topR

    gate_A = sig(ka * (ras - ta_eff))
    gate_B = sig(kb * (ras - tb_eff))

    p_val  = gate_A * sig(va * hand + ba + cs * sbr_n + cp * p3bp)
    p_semi = gate_B * sig(vb * de + bb)

    return np.clip(np.maximum(p_val, p_semi), 0, 1)


# ---------------------------------------------------------------------------
# 8. F15: F12 + slowplay correction for strong hands
#    GTO bets set/FH at lower rate → add explicit correction term
# ---------------------------------------------------------------------------

def f15_slowplay(trial, ras, de, hand, sbr_n, p3bp, plimp, topR, has_ace, sp, fixed=None):
    """F15: F12 + explicit slowplay penalty for set/FH/trips."""
    def p(name, lo, hi):
        if fixed and name in fixed:
            return fixed[name]
        return trial.suggest_float(name, lo, hi)

    ka    = p("ka", 1, 20);   ta = p("ta", 0.05, 0.5)
    w_adj = p("w_adj", 0, 0.5)
    kb    = p("kb", 1, 20);   tb = p("tb", 0.3, 0.95)
    va    = p("va", 0, 5);    ba = p("ba", -5, 3)
    vb    = p("vb", 0, 10);   bb = p("bb", -5, 3)
    cs    = p("cs", -3, 3)
    cp    = p("cp", -5, 0)
    sp_p  = p("sp_p", 0, 0.5)  # slowplay penalty magnitude

    ta_eff = ta + w_adj * (1.0 - hand)

    gate_A = sig(ka * (ras - ta_eff))
    gate_B = sig(kb * (ras - tb))

    p_val  = gate_A * sig(va * hand + ba + cs * sbr_n + cp * p3bp)
    p_semi = gate_B * sig(vb * de + bb)

    base = np.maximum(p_val, p_semi)
    # Slowplay: reduce bet% for set/FH proportionally
    corrected = base - sp_p * sp

    return np.clip(corrected, 0, 1)


# ---------------------------------------------------------------------------
# 9. F16: Full combined (F12 + F13 + F15)
# ---------------------------------------------------------------------------

def f16_full(trial, ras, de, hand, sbr_n, p3bp, plimp, topR, has_ace, sp, fixed=None):
    """F16: Hand-gate + ace-board + slowplay correction."""
    def p(name, lo, hi):
        if fixed and name in fixed:
            return fixed[name]
        return trial.suggest_float(name, lo, hi)

    ka    = p("ka", 1, 20);   ta = p("ta", 0.05, 0.5)
    w_adj = p("w_adj", 0, 0.5)
    at    = p("at", 0, 0.4)
    kb    = p("kb", 1, 20);   tb = p("tb", 0.3, 0.95)
    at_b  = p("at_b", 0, 0.3)
    va    = p("va", 0, 5);    ba = p("ba", -5, 3)
    vb    = p("vb", 0, 10);   bb = p("bb", -5, 3)
    cs    = p("cs", -3, 3)
    cp    = p("cp", -5, 0)
    sp_p  = p("sp_p", 0, 0.5)

    ta_eff = ta + w_adj * (1.0 - hand) - at * topR
    tb_eff = tb - at_b * topR

    gate_A = sig(ka * (ras - ta_eff))
    gate_B = sig(kb * (ras - tb_eff))

    p_val  = gate_A * sig(va * hand + ba + cs * sbr_n + cp * p3bp)
    p_semi = gate_B * sig(vb * de + bb)

    base = np.maximum(p_val, p_semi)
    corrected = base - sp_p * sp

    return np.clip(corrected, 0, 1)


# ---------------------------------------------------------------------------
# 10. F17: 3-gate (value + semibluff + pure-bluff)
#     Tests whether an explicit 3rd gate for pure-bluff range helps
# ---------------------------------------------------------------------------

def f17_three_gates(trial, ras, de, hand, sbr_n, p3bp, plimp, topR, has_ace, sp, fixed=None):
    """F17: Three separate gates: value / semibluff / pure-bluff."""
    def p(name, lo, hi):
        if fixed and name in fixed:
            return fixed[name]
        return trial.suggest_float(name, lo, hi)

    # Gate A: value hands
    ka    = p("ka", 1, 20);   ta = p("ta", 0.05, 0.5)
    w_adj = p("w_adj", 0, 0.5)
    # Gate B: semibluff (draw)
    kb    = p("kb", 1, 20);   tb = p("tb", 0.3, 0.8)
    # Gate C: pure-bluff / air (requires very high RAS)
    kc    = p("kc", 1, 20);   tc = p("tc", 0.5, 0.95)
    va    = p("va", 0, 5);    ba = p("ba", -5, 3)
    vb    = p("vb", 0, 10);   bb = p("bb", -5, 3)
    vc    = p("vc", -5, 5);   bc = p("bc", -5, 3)
    cs    = p("cs", -3, 3)
    cp    = p("cp", -5, 0)
    sp_p  = p("sp_p", 0, 0.5)

    ta_eff = ta + w_adj * (1.0 - hand)

    gate_A = sig(ka * (ras - ta_eff))
    gate_B = sig(kb * (ras - tb))
    gate_C = sig(kc * (ras - tc))

    # air = hands with hand_norm < 0.2 and no draw
    is_air = (hand < 0.2).astype(float) * (de < 0.1).astype(float)

    p_val   = gate_A * sig(va * hand + ba + cs * sbr_n + cp * p3bp)
    p_semi  = gate_B * sig(vb * de + bb)
    p_bluff = gate_C * sig(vc * is_air + bc) * is_air

    base = np.maximum(np.maximum(p_val, p_semi), p_bluff)
    corrected = base - sp_p * sp

    return np.clip(corrected, 0, 1)


# ---------------------------------------------------------------------------
# 11. F18: RAS-conditioned hand threshold (non-linear hand curve)
#     Different hand shapes on high vs low RAS boards
# ---------------------------------------------------------------------------

def f18_ras_hand_cond(trial, ras, de, hand, sbr_n, p3bp, plimp, topR, has_ace, sp, fixed=None):
    """F18: Separate hand-strength curves for high/low RAS regimes."""
    def p(name, lo, hi):
        if fixed and name in fixed:
            return fixed[name]
        return trial.suggest_float(name, lo, hi)

    # Soft gate splitting high vs low RAS
    kg    = p("kg", 2, 15);   tg = p("tg", 0.3, 0.7)
    gate  = sig(kg * (ras - tg))   # gate=1 → high RAS, gate=0 → low RAS

    # High-RAS: more permissive, air can bet
    ah    = p("ah", 0, 5);    bh = p("bh", -5, 3)
    vh    = p("vh", 0, 8);    ch = p("ch", -3, 3)
    # Low-RAS: tight, needs strong hand
    al_   = p("al", 0, 8);    bl = p("bl", -8, 0)
    vl    = p("vl", 0, 5);    cl = p("cl", -3, 3)
    # Draw component (both regimes)
    vd    = p("vd", 0, 10);   bd = p("bd", -5, 3)
    tb    = p("tb", 0.3, 0.95)
    kb    = p("kb", 1, 20)
    sp_p  = p("sp_p", 0, 0.5)

    p_high = sig(ah * hand + bh * de + ch * sbr_n + vh)
    p_low  = sig(al_ * hand + bl + cl * sbr_n)

    p_base = gate * p_high + (1 - gate) * p_low

    gate_draw = sig(kb * (ras - tb))
    p_draw = gate_draw * sig(vd * de + bd)

    base = np.maximum(p_base, p_draw)
    corrected = base - sp_p * sp

    return np.clip(corrected, 0, 1)


# ---------------------------------------------------------------------------
# 12. Optuna Objective Factory
# ---------------------------------------------------------------------------

FORMULAS = {
    "F11_TwoGates":    f11_two_gates,
    "F12_HandGate":    f12_hand_gate,
    "F13_AceGate":     f13_ace_gate,
    "F14_HandAce":     f14_hand_ace_gate,
    "F15_Slowplay":    f15_slowplay,
    "F16_Full":        f16_full,
    "F17_ThreeGates":  f17_three_gates,
    "F18_RasHandCond": f18_ras_hand_cond,
}


def make_objective(fn, arrays):
    ras, de, hand, sbr_n, p3bp, plimp, topR, has_ace, sp, y, w = arrays

    def objective(trial):
        try:
            pred = fn(trial, ras, de, hand, sbr_n, p3bp, plimp, topR, has_ace, sp)
            pred = np.clip(pred, 0.0, 1.0)
            return wmse(pred, y, w)
        except Exception:
            return 1.0

    return objective


# ---------------------------------------------------------------------------
# 13. Residual analysis helper
# ---------------------------------------------------------------------------

def analyze_residuals(data, pred_all, y, w_raw):
    """Print residual breakdown by hand type, board, and scenario."""
    from collections import defaultdict

    hand_residuals = defaultdict(list)
    board_residuals = defaultdict(list)
    scenario_residuals = defaultdict(list)

    w_total = w_raw.sum()

    for i, dp in enumerate(data):
        err = (y[i] - pred_all[i]) * 100  # in percentage points
        wt = w_raw[i]

        hand_key = f"hand={dp.hand_norm:.2f}"
        hand_residuals[hand_key].append((err, wt))

        from pathlib import Path
        board_residuals[dp.scenario_key].append((err, wt))

    # Print hand-level breakdown
    print("\n=== 残差分析: シナリオ別 (y - pred) ===")
    print(f"{'シナリオ':<20} {'平均残差':>10} {'WRMSE':>8} {'n':>6}")
    print("-" * 50)
    scene_stats = []
    for sc, pairs in scenario_residuals.items():
        errs = np.array([e for e, _ in pairs])
        wts = np.array([wt for _, wt in pairs])
        wts_n = wts / wts.sum()
        mean_err = np.average(errs, weights=wts_n)
        rmse = math.sqrt(np.average(errs**2, weights=wts_n))
        scene_stats.append((sc, mean_err, rmse, len(errs)))
    for sc, me, rm, n in sorted(scene_stats, key=lambda x: x[1]):
        print(f"{sc:<20} {me:>+9.1f}% {rm:>7.1f}%  {n:>6}")


def run_scenario_residuals(data, pred_all, y, w_raw):
    """Quick residual by scenario + hand bucket."""
    from collections import defaultdict

    bucket_map = {
        0.00: "no_made_hand", 0.10: "ace_high", 0.15: "king_high",
        0.20: "underpair",    0.25: "low_pair",  0.35: "third_pair",
        0.45: "second_pair",  0.60: "top_pair",  0.72: "overpair",
        0.82: "two_pair",     0.90: "set/trips", 0.88: "flush",
        0.87: "straight",     0.95: "fullhouse", 0.97: "quads",
    }

    key_to_hand = {}
    for k, v in bucket_map.items():
        key_to_hand[round(k, 2)] = v

    by_hand = defaultdict(lambda: {"errs": [], "wts": []})
    by_board = defaultdict(lambda: {"errs": [], "wts": []})
    by_scene = defaultdict(lambda: {"errs": [], "wts": []})

    for i, dp in enumerate(data):
        err = (y[i] - pred_all[i]) * 100
        wt = w_raw[i]
        hand_label = key_to_hand.get(round(dp.hand_norm, 2), f"{dp.hand_norm:.2f}")

        by_hand[hand_label]["errs"].append(err)
        by_hand[hand_label]["wts"].append(wt)

        board_label = f"top={dp.top_rank_n:.1f}"
        by_board[board_label]["errs"].append(err)
        by_board[board_label]["wts"].append(wt)

        by_scene[dp.scenario_key]["errs"].append(err)
        by_scene[dp.scenario_key]["wts"].append(wt)

    def stats(d):
        errs = np.array(d["errs"])
        wts  = np.array(d["wts"])
        wts_n = wts / wts.sum()
        return (np.average(errs, weights=wts_n),
                math.sqrt(np.average(errs**2, weights=wts_n)),
                len(errs))

    print("\n=== ハンドタイプ別残差 ===")
    print(f"{'ハンド':<16} {'平均残差':>10} {'WRMSE':>8} {'n':>7}")
    for h, d in sorted(by_hand.items(), key=lambda x: stats(x[1])[0]):
        me, rm, n = stats(d)
        print(f"  {h:<14} {me:>+9.1f}% {rm:>7.1f}%  {n:>7}")

    print("\n=== シナリオ別残差 ===")
    print(f"{'シナリオ':<20} {'平均残差':>10} {'WRMSE':>8}")
    for sc, d in sorted(by_scene.items(), key=lambda x: stats(x[1])[0]):
        me, rm, _ = stats(d)
        print(f"  {sc:<18} {me:>+9.1f}% {rm:>7.1f}%")


# ---------------------------------------------------------------------------
# 14. Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 65)
    print("CBet v2 — Additional Factor Exploration (Optuna)")
    print("=" * 65)

    data = load_data()
    if not data:
        print("No data loaded.")
        return

    arrays = to_arrays(data)
    ras, de, hand, sbr_n, p3bp, plimp, topR, has_ace, sp, y, w = arrays
    w_raw = np.array([d.w for d in data])

    bm = float(np.sum(w * (y - np.average(y, weights=w)) ** 2))
    print(f"\nBaseline WMSE (mean): {bm:.5f}  WRMSE={math.sqrt(bm)*100:.1f}%")

    N_TRIALS = 1000
    results = {}

    print(f"\n最適化中 (各{N_TRIALS}試行)...")

    for name, fn in FORMULAS.items():
        study = optuna.create_study(direction="minimize",
                                    sampler=optuna.samplers.TPESampler(seed=42))
        obj = make_objective(fn, arrays)
        study.optimize(obj, n_trials=N_TRIALS, show_progress_bar=False)

        best = study.best_value
        rmse_pct = math.sqrt(best) * 100
        r2_val = 1.0 - best / bm
        results[name] = {
            "wmse": best,
            "wrmse_pct": rmse_pct,
            "r2": r2_val,
            "params": study.best_params,
        }
        print(f"  {name:<18} WMSE={best:.5f}  WRMSE={rmse_pct:.1f}%  R²={r2_val:.3f}")

    # Summary
    print("\n" + "=" * 65)
    print("結果比較")
    print("=" * 65)
    print(f"{'式':<20} {'WMSE':>8} {'WRMSE%':>8} {'R²':>7} {'改善':>8}")
    print("-" * 55)

    f11_wmse = results.get("F11_TwoGates", {}).get("wmse", bm)

    for name, r in sorted(results.items(), key=lambda x: x[1]["wmse"]):
        improvement = (f11_wmse - r["wmse"]) / f11_wmse * 100
        print(f"{name:<20} {r['wmse']:>8.5f} {r['wrmse_pct']:>7.1f}%  {r['r2']:>6.3f}  {improvement:>+6.1f}%")

    # Best formula residual analysis
    best_name = min(results, key=lambda k: results[k]["wmse"])
    best_r = results[best_name]
    print(f"\n最良式: {best_name}  (R²={best_r['r2']:.3f})")
    print("最適パラメータ:")
    for k, v in sorted(best_r["params"].items()):
        print(f"  {k:8s} = {v:+.4f}")

    # Compute predictions for best formula
    fn_best = FORMULAS[best_name]

    class MockTrial:
        def __init__(self, params): self._p = params
        def suggest_float(self, name, lo, hi): return self._p[name]
        def suggest_int(self, name, lo, hi): return int(self._p[name])

    mock = MockTrial(best_r["params"])
    pred_all = fn_best(mock, ras, de, hand, sbr_n, p3bp, plimp, topR, has_ace, sp)
    pred_all = np.clip(pred_all, 0.0, 1.0)

    # Residual analysis
    run_scenario_residuals(data, pred_all, y, w_raw)

    # Also show F11 residuals for comparison if best is different
    if best_name != "F11_TwoGates" and "F11_TwoGates" in results:
        f11_r = results["F11_TwoGates"]
        mock11 = MockTrial(f11_r["params"])
        pred11 = f11_two_gates(mock11, ras, de, hand, sbr_n, p3bp, plimp, topR, has_ace, sp)
        pred11 = np.clip(pred11, 0.0, 1.0)
        print(f"\n--- F11参照 (WRMSE={f11_r['wrmse_pct']:.1f}%) ---")
        run_scenario_residuals(data, pred11, y, w_raw)

    # Practical threshold analysis for best formula
    print(f"\n=== {best_name}: HS境界値分析 ===")
    print("シナリオ別 チェック/ベット境界（ドローなし）")
    print(f"{'シナリオ':<18} {'T_check(20%)':>13} {'T_bet(80%)':>11}")
    print("-" * 46)

    scenario_list = [
        ("SRP25",    0.75, 0, 0),
        ("SRP20",    0.70, 0, 0),
        ("SRP20_CO", 0.80, 0, 0),
        ("3BP20",    0.55, 1, 0),
        ("SRP25_SB", 0.44, 0, 0),
        ("SRP20_SB", 0.50, 0, 0),
        ("LIMP25_SB",0.39, 0, 1),
        ("LIMP20_SB",0.41, 0, 1),
    ]

    # Create hand range
    hand_vals = np.array([0.00, 0.10, 0.15, 0.20, 0.25, 0.35, 0.45, 0.60, 0.72, 0.82, 0.90])
    hand_labels = ["noMade","aceH","kingH","underpair","lowP","3rdP","2ndP","topP","over","2pair","set"]
    de_fixed = np.zeros_like(hand_vals)  # no draw
    sp_fixed = np.where(hand_vals >= 0.88, 1.0, 0.0)
    top_fixed = np.full_like(hand_vals, 0.5)   # mid-rank board
    ace_fixed = np.zeros_like(hand_vals)

    for sc, ras_val, is3bp, islimp in scenario_list:
        ras_arr  = np.full_like(hand_vals, ras_val)
        sbr_arr  = np.full_like(hand_vals, 0.0)  # SBR20 → sbr_n=0
        p3bp_arr = np.full_like(hand_vals, float(is3bp))
        plimp_arr= np.full_like(hand_vals, float(islimp))

        preds = fn_best(mock, ras_arr, de_fixed, hand_vals, sbr_arr, p3bp_arr, plimp_arr,
                        top_fixed, ace_fixed, sp_fixed)
        preds = np.clip(preds, 0, 1)

        # Find T_check (where pred crosses 0.20) and T_bet (where pred crosses 0.80)
        t_check = "なし"
        t_bet   = "なし"
        for idx in range(len(hand_vals)-1):
            if preds[idx] < 0.20 and preds[idx+1] >= 0.20:
                t_check = hand_labels[idx+1]
            if preds[idx] < 0.80 and preds[idx+1] >= 0.80:
                t_bet = hand_labels[idx+1]

        print(f"  {sc:<16} {t_check:>13} {t_bet:>11}")

    print("\n完了。")


if __name__ == "__main__":
    main()
