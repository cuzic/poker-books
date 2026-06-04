"""
UCBS-v3 階層型モデル (A+C3 Board family)

Vol2 (Light) と Vol3 (Full) で共有する後置式 cbet 頻度予測モデル。
パラメータは knowledges/gto_wizard_study/ucbs_v3_params.json から読み込み。

定義:
  freq = base[ctx5][band]
       + α[ctx13]
       + β[ctx13] · I(CBS ≥ 7)
       + cat_offset[hand_category]
       + ε[board_family][ctx_group]

Vol2 は base のみ使う (4 step、Light 互換)。
Vol3 は全層を使う (7 step、UCBS-v3 Full)。
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path

PARAMS_PATH = Path(__file__).resolve().parent.parent / \
    "knowledges/gto_wizard_study/ucbs_v3_params.json"

_PARAMS = json.loads(PARAMS_PATH.read_text())

# ── テーブル ──
HP_TABLE = {
    "no_made_hand": 2, "ace_high": 2, "king_high": 2,
    "low_pair": 3, "underpair": 3, "third_pair": 3,
    "second_pair": 5, "top_pair": 7, "overpair": 7,
    "two_pair": 8, "set": 9, "trips": 9, "straight": 9,
    "flush": 9, "fullhouse": 9, "quads": 9,
}
DP_TABLE = {
    "no_draw": 0, "twocards_bdfd": 0,
    "gutshot": 1, "oesd": 2, "fd": 2, "combo_draw": 3,
}
HAND_CATEGORY = {
    "set": "slowplay", "trips": "slowplay", "two_pair": "slowplay",
    "fullhouse": "slowplay", "flush": "slowplay", "straight": "slowplay",
    "quads": "slowplay",
    "low_pair": "trash",
    "overpair": "premium", "underpair": "premium",
}

CTX13 = ["cash_100bb",
         "mtt_25bb", "mtt_50bb", "mtt_100bb", "mtt_200bb",
         "mtt_3bp_20bb", "mtt_3bp_25bb", "mtt_3bp_50bb", "mtt_3bp_100bb",
         "mtt_25bb_turn_btn", "mtt_50bb_turn_btn",
         "mtt_100bb_turn_btn", "cash_100bb_turn_btn"]

CTX13_TO_5 = {
    "cash_100bb": "cash",
    "mtt_25bb": "mtt_short", "mtt_50bb": "mtt_short",
    "mtt_100bb": "mtt_deep", "mtt_200bb": "mtt_deep",
    "mtt_3bp_20bb": "3bp", "mtt_3bp_25bb": "3bp",
    "mtt_3bp_50bb": "3bp", "mtt_3bp_100bb": "3bp",
    "mtt_25bb_turn_btn": "turn", "mtt_50bb_turn_btn": "turn",
    "mtt_100bb_turn_btn": "turn", "cash_100bb_turn_btn": "turn",
}

CTX_GROUP = {
    "cash_100bb": "cash", "cash_100bb_turn_btn": "cash",
    "mtt_25bb": "mtt_srp", "mtt_50bb": "mtt_srp",
    "mtt_100bb": "mtt_srp", "mtt_200bb": "mtt_srp",
    "mtt_25bb_turn_btn": "mtt_srp", "mtt_50bb_turn_btn": "mtt_srp",
    "mtt_100bb_turn_btn": "mtt_srp",
    "mtt_3bp_20bb": "3bp", "mtt_3bp_25bb": "3bp",
    "mtt_3bp_50bb": "3bp", "mtt_3bp_100bb": "3bp",
}

CTX5 = ["cash", "mtt_short", "mtt_deep", "3bp", "turn"]
BANDS = ["air", "weak", "mid", "strong", "nut"]
BOARD_FAMILIES = ["dry_high", "paired", "dynamic", "low_dry"]
CTX_GROUPS = ["cash", "mtt_srp", "3bp"]


def cbs_band(cbs: int) -> str:
    if cbs <= 2: return "air"
    if cbs <= 4: return "weak"
    if cbs <= 6: return "mid"
    if cbs <= 8: return "strong"
    return "nut"


# ── パラメータ ──
BASE = _PARAMS["base"]
ALPHA = _PARAMS["alpha"]
BETA = _PARAMS["beta"]
CAT_OFFSET = _PARAMS["cat_offset"]
EPSILON = _PARAMS["epsilon"]


# ── 板分類 ──
_RANK_NUM = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
              "T":10,"J":11,"Q":12,"K":13,"A":14}

def _parse_flop(board: str):
    cards = []
    i = 0
    while i < len(board) - 1 and len(cards) < 3:
        r, s = board[i], board[i+1]
        if r in _RANK_NUM:
            cards.append((_RANK_NUM[r], s))
        i += 2
    return cards


def board_family(board: str) -> str:
    """ボード文字列 (例 'AsKd7c') を 4 family に分類する。"""
    cards = _parse_flop(board)
    if len(cards) < 3:
        return "dry_high"
    ranks = sorted([c[0] for c in cards], reverse=True)
    suits = [c[1] for c in cards]
    is_paired = len(set(ranks)) < 3
    is_mono = len(set(suits)) == 1
    is_two_tone = len(set(suits)) == 2
    gap = ranks[0] - ranks[2]
    is_connected = gap <= 4
    if is_paired:
        return "paired"
    if is_mono or (is_connected and is_two_tone):
        return "dynamic"
    if ranks[0] >= 11:
        return "dry_high"
    return "low_dry"


# ── 予測 ──
@dataclass
class V3Prediction:
    """UCBS-v3 計算過程の dataclass。"""
    hand: str
    draw: str
    board: str
    context: str
    hp: int
    dp: int
    cbs: int
    band: str
    ctx5: str
    ctx_group: str
    category: str
    family: str
    base: float
    alpha: float
    beta_term: float
    cat_offset: float
    epsilon: float
    frequency: float


def predict_v3(hand: str, draw: str = "no_draw",
               board: str = "AsKd7c", context: str = "cash_100bb") -> V3Prediction:
    """UCBS-v3 (A+C3) で cbet 頻度を計算する。"""
    hp = HP_TABLE.get(hand, 0)
    dp = DP_TABLE.get(draw, 0)
    cbs = hp + dp
    band = cbs_band(cbs)
    ctx5 = CTX13_TO_5[context]
    cg = CTX_GROUP[context]
    cat = HAND_CATEGORY.get(hand, "default")
    fam = board_family(board)

    b = BASE[ctx5][band]
    a = ALPHA[context]
    bt = BETA[context] if cbs >= 7 else 0.0
    co = CAT_OFFSET.get(cat, 0.0)
    eps = EPSILON[fam][cg]

    freq = max(0.02, min(0.98, b + a + bt + co + eps))
    return V3Prediction(hand=hand, draw=draw, board=board, context=context,
                         hp=hp, dp=dp, cbs=cbs, band=band, ctx5=ctx5,
                         ctx_group=cg, category=cat, family=fam,
                         base=b, alpha=a, beta_term=bt,
                         cat_offset=co, epsilon=eps, frequency=freq)


def predict_v2_light(hand: str, draw: str, ctx5: str) -> dict:
    """Vol2 用 Light モデル (base のみ + low_pair offset)。"""
    hp = HP_TABLE.get(hand, 0)
    dp = DP_TABLE.get(draw, 0)
    cbs = hp + dp
    band = cbs_band(cbs)
    base = BASE[ctx5][band]
    offset = -0.10 if hand == "low_pair" else 0.0
    final = max(0.02, min(0.98, base + offset))
    return {"hp": hp, "dp": dp, "cbs": cbs, "band": band,
            "base": base, "offset": offset, "final": final}


if __name__ == "__main__":
    # smoke test
    p = predict_v3("top_pair", "no_draw", "AsKd7c", "cash_100bb")
    print(f"top_pair on AsKd7c cash_100bb: HP={p.hp} DP={p.dp} CBS={p.cbs} "
          f"band={p.band} family={p.family}")
    print(f"  base={p.base*100:.0f}% + α{p.alpha*100:+.0f} + β{p.beta_term*100:+.0f} "
          f"+ cat{p.cat_offset*100:+.0f} + ε{p.epsilon*100:+.0f} = {p.frequency*100:.0f}%")

    p2 = predict_v3("flush", "no_draw", "8s7s6s", "mtt_3bp_25bb")
    print(f"\nflush on 8s7s6s mtt_3bp_25bb: family={p2.family} freq={p2.frequency*100:.0f}%")

    p3 = predict_v3("low_pair", "no_draw", "9h6c2d", "mtt_100bb")
    print(f"low_pair on 9h6c2d mtt_100bb: family={p3.family} freq={p3.frequency*100:.0f}%")
