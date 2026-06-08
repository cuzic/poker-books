"""Flop 状態空間の段階的 ablation 実験。

【3 mode 比較】
Mode 1: Board のみ (5-9 features)
Mode 2: + Range (mv_tier + opp_r で代理)
Mode 3: + Nut/specific hand 関連

各 mode で 線形 / DT / RF / GBM を比較し、accuracy 差を見る。
ユーザー仮説: Board 55-60% / +Range 70% / +Nut 77%

【Board 4 軸 (4 × 3 × 3 × 3 = 108 状態)】
- high_card: A / KQ / JT / Low
- connectivity: Disc / Semi / Connected
- suit: Rainbow / 2tone / Monotone
- pair: Unpaired / Paired / Trips

【Dynamicity (draw possibility)】
- straight_outs (data 計算)
- FD possibility (suit count)
"""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/FLOP_ABLATION_STUDY.md"

RANKS = "23456789TJQKA"
EQ_LABEL_TO_IDX = {"trash_hands":0, "weak_hands":1, "good_hands":2, "best_hands":3}

MV_TIER_MAP = {
    "fullhouse":0,"quads":0,"straight_flush":0,
    "set":1,"trips":1,"straight":1,"flush":1,
    "two_pair":2,
    "top_pair":3,"overpair":3,
    "second_pair":4,"third_pair":4,"underpair":4,"low_pair":4,
    "no_made_hand":5,"king_high":5,"ace_high":5,
}
DV_BASE = {"combo_draw":4,"nut_flush_draw":3,"flush_draw":3,"oesd":3,"gutshot":1,
           "twocards_bdfd":1,"onecard_bdfd":0,"no_draw":0}
OPP_R = {"SRP":0,"DEF":1,"3BP":2,"4BP":3}


def parse_pot(scn):
    s = scn.lower()
    return "4BP" if "4bp" in s else "3BP" if "3bp" in s else \
           "DEF" if ("cr_def" in s or "donk_def" in s) else "SRP"


def board_4axes(board: str) -> dict:
    """ユーザー提案の 4 軸 + dynamicity 拡張."""
    if len(board) < 6:
        return None
    try:
        cards = [board[i*2:i*2+2] for i in range(3)]
        rvals = sorted([RANKS.index(c[0].upper()) for c in cards], reverse=True)
        suits = [c[1].lower() for c in cards]
    except ValueError:
        return None

    h = rvals[0]
    # high_card tier: A=3, KQ=2, JT=1, Low=0
    if h == 12: hc = 3       # A
    elif h >= 10: hc = 2     # K, Q
    elif h >= 8: hc = 1      # J, T
    else: hc = 0             # 9 以下

    # connectivity: based on gaps
    gap_top = rvals[0] - rvals[1]; gap_bot = rvals[1] - rvals[2]
    max_gap = max(gap_top, gap_bot); min_gap = min(gap_top, gap_bot)
    paired_flag = rvals[0]==rvals[1] or rvals[1]==rvals[2]
    if paired_flag:
        conn = 0  # paired は connectivity 別軸で扱う
    elif gap_top <= 2 and gap_bot <= 2:
        conn = 2  # connected
    elif gap_top <= 4 and gap_bot <= 4:
        conn = 1  # semi (e.g., J84, gap≤4)
    else:
        conn = 0  # disconnected

    # suit: 0=rainbow, 1=2tone, 2=monotone
    n_unique_suit = len(set(suits))
    if n_unique_suit == 3: suit_v = 0
    elif n_unique_suit == 2: suit_v = 1
    else: suit_v = 2

    # pair: 0=unpaired, 1=paired (only 2 of same rank), 2=trips
    if rvals[0]==rvals[1]==rvals[2]: pair_v = 2
    elif paired_flag: pair_v = 1
    else: pair_v = 0

    # Dynamicity (rough draw possibility)
    # straight potential: outs to complete
    all_ranks = sorted(set(rvals))
    straight_outs = 0
    for r_extra in range(13):
        if r_extra in all_ranks: continue
        test_ranks = sorted(all_ranks + [r_extra])
        # check 4 consecutive in test_ranks (potential for straight w 1 more)
        for i in range(len(test_ranks) - 3):
            if test_ranks[i+3] - test_ranks[i] == 3:
                straight_outs += 1
                break

    # FD possibility = 1 if 2+ same suit
    fd_possible = 1 if n_unique_suit <= 2 else 0
    bdfd_possible = 1 if n_unique_suit == 2 else 0

    return {
        "hc": hc, "conn": conn, "suit": suit_v, "pair": pair_v,
        "max_gap": max_gap, "min_gap": min_gap,
        "straight_outs": straight_outs,
        "fd_possible": fd_possible, "bdfd_possible": bdfd_possible,
        "b_high": h, "b_mid": rvals[1], "b_low": rvals[2],
    }


def hero_vs_board(card_a, card_b, board):
    try:
        a_r = RANKS.index(card_a[0].upper()); a_s = card_a[1].lower()
        b_r = RANKS.index(card_b[0].upper()); b_s = card_b[1].lower()
        if a_r < b_r: a_r, b_r = b_r, a_r; a_s, b_s = b_s, a_s
        bc = [(RANKS.index(board[i*2:i*2+2][0].upper()), board[i*2:i*2+2][1].lower())
              for i in range(len(board) // 2)]
        b_ranks = sorted([r for r, _ in bc], reverse=True)
        b_h = b_ranks[0]; b_m = b_ranks[1] if len(b_ranks)>1 else 0
        b_l = b_ranks[2] if len(b_ranks)>2 else 0

        return {
            "a_r": a_r, "b_r": b_r,
            "hero_pair": int(a_r == b_r),
            "hero_suited": int(a_s == b_s),
            "hero_overpair": int(a_r == b_r and a_r > b_h),
            "hero_set": int(a_r == b_r and a_r in (b_h, b_m, b_l)),
            "hero_top_match": int(a_r == b_h or b_r == b_h),
            "hero_mid_match": int(a_r == b_m or b_r == b_m),
            "hero_overcards": sum(1 for r in (a_r, b_r) if r > b_h),
            "hero_suits_on_board": sum(1 for r, s in bc if s in (a_s, b_s)),
        }
    except (ValueError, IndexError):
        return None


print("Loading rows...")
mode_data = []  # each row: dict of features for all modes
n_skip = 0
with CSV_PATH.open() as f:
    for r in csv.DictReader(f):
        eq_b = r.get("equity_bucket", "")
        mv = r.get("mv_cat", "")
        if eq_b not in EQ_LABEL_TO_IDX or mv not in MV_TIER_MAP:
            n_skip += 1; continue
        board = r.get("board_str", "")[:6].lower()
        if len(board) < 6: n_skip += 1; continue
        ca = r.get("card_a", ""); cb = r.get("card_b", "")
        if not ca or not cb: n_skip += 1; continue
        bf = board_4axes(board)
        if bf is None: n_skip += 1; continue
        hf = hero_vs_board(ca, cb, board)
        if hf is None: n_skip += 1; continue

        opp_r = OPP_R[parse_pot(r["scenario_id"])]
        dv_v = DV_BASE.get(r.get("dv_cat", "no_draw"), 0)
        mv_idx = MV_TIER_MAP[mv]

        mode_data.append({
            "board": bf,
            "hero": hf,
            "mv_idx": mv_idx,
            "dv": dv_v,
            "opp_r": opp_r,
            "y": EQ_LABEL_TO_IDX[eq_b],
        })

print(f"Loaded {len(mode_data):,} rows ({n_skip} skipped)")


def build_X(mode: int, data: list[dict]) -> np.ndarray:
    """Mode 1: Board only / Mode 2: + Range / Mode 3: + Hero specific."""
    rows = []
    for d in data:
        bf = d["board"]; hf = d["hero"]
        # Mode 1: Board features only
        f = [bf["hc"], bf["conn"], bf["suit"], bf["pair"],
             bf["max_gap"], bf["min_gap"], bf["straight_outs"],
             bf["fd_possible"], bf["bdfd_possible"],
             bf["b_high"], bf["b_mid"], bf["b_low"]]
        if mode >= 2:
            # + Range proxy (mv_tier + opp_r)
            f += [d["mv_idx"], d["opp_r"], d["dv"]]
        if mode >= 3:
            # + Hero specific
            f += [hf["a_r"], hf["b_r"], hf["hero_pair"], hf["hero_suited"],
                  hf["hero_overpair"], hf["hero_set"],
                  hf["hero_top_match"], hf["hero_mid_match"],
                  hf["hero_overcards"], hf["hero_suits_on_board"]]
        rows.append(f)
    return np.array(rows, dtype=np.float32)


y = np.array([d["y"] for d in mode_data], dtype=np.int8)
print(f"y distribution: trash={(y==0).sum():,}, weak={(y==1).sum():,}, good={(y==2).sum():,}, best={(y==3).sum():,}")

# Train/Val split
np.random.seed(42)
perm = np.random.permutation(len(y))
split = int(len(y) * 0.8)
tr, va = perm[:split], perm[split:]


print("\n=== Ablation: Mode × Model ===")
results = []
for mode, mode_name in [(1, "Board only"), (2, "+ Range"), (3, "+ Hero")]:
    X = build_X(mode, mode_data)
    X_tr, y_tr = X[tr], y[tr]
    X_va, y_va = X[va], y[va]
    print(f"\n--- {mode_name} (dim={X.shape[1]}) ---")

    # Logistic Regression
    lr = LogisticRegression(max_iter=200, solver="lbfgs")
    lr.fit(X_tr, y_tr)
    lr_va = lr.score(X_va, y_va) * 100
    print(f"  Logistic Reg: val={lr_va:.2f}%")
    results.append((mode_name, "Logistic", lr_va, X.shape[1]))

    # DT depth 5
    for d in [5, 10, None]:
        dt = DecisionTreeClassifier(max_depth=d, random_state=42)
        dt.fit(X_tr, y_tr)
        va_acc = dt.score(X_va, y_va) * 100
        leaves = dt.get_n_leaves()
        print(f"  DT depth={str(d):>4}: val={va_acc:.2f}% (leaves={leaves})")
        results.append((mode_name, f"DT d={d}", va_acc, leaves))

    # RF
    rf = RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42)
    rf.fit(X_tr, y_tr)
    rf_va = rf.score(X_va, y_va) * 100
    print(f"  RF (100 trees): val={rf_va:.2f}%")
    results.append((mode_name, "RF n=100", rf_va, 100))


# Report
lines = []
lines.append("# Flop 状態空間の段階的 ablation 実験")
lines.append("")
lines.append("ユーザー仮説の検証: Board / +Range / +Hero での精度差。")
lines.append("")
lines.append("## Board 4 軸 (User 提案)")
lines.append("")
lines.append("- high_card: A=3 / KQ=2 / JT=1 / Low=0")
lines.append("- connectivity: Connected=2 / Semi=1 / Disconnected=0")
lines.append("- suit: Monotone=2 / 2tone=1 / Rainbow=0")
lines.append("- pair: Trips=2 / Paired=1 / Unpaired=0")
lines.append("+ dynamicity: straight_outs, fd_possible, b_high/mid/low (連続値)")
lines.append("")

lines.append("## 結果")
lines.append("")
lines.append("| Mode | Model | val accuracy | size |")
lines.append("|------|-------|---:|---:|")
for mode_name, model, acc, size in results:
    lines.append(f"| {mode_name} | {model} | {acc:.2f}% | {size} |")
lines.append("")

lines.append("## ユーザー仮説との比較")
lines.append("")
lines.append("| mode | 予想 | 実測 (RF) |")
lines.append("|------|------|---:|")
board_rf = [r[2] for r in results if r[0] == "Board only" and r[1] == "RF n=100"][0]
range_rf = [r[2] for r in results if r[0] == "+ Range" and r[1] == "RF n=100"][0]
hero_rf = [r[2] for r in results if r[0] == "+ Hero" and r[1] == "RF n=100"][0]
lines.append(f"| Board only | 55-60% | {board_rf:.1f}% |")
lines.append(f"| + Range | 70% | {range_rf:.1f}% |")
lines.append(f"| + Hero (Nut) | 77% | {hero_rf:.1f}% |")
lines.append("")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
