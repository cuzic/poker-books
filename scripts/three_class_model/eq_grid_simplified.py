"""eq グリッド (tier × board) 経由の simplified MATCHA 公式。

【設計】
1. 自分の手 → tier 判定 (簡単)
2. board → 4 種 (dry / paired / connected / monotone)
3. tier × board の 24-cell grid から eq_bucket を lookup
4. Score = eq - bs + pot で判定

【期待性能】
- 直接 eq (相手 range vs hand 計算): accuracy 75%
- grid 経由 (tier × board): accuracy 70% 程度 (推定)

【目的】
- 素人が equity 計算なしで MATCHA 公式を運用可能に
- Chen Formula と同等の暗算負荷
"""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/EQ_GRID_MATCHA.md"

MATCHA_TIER = {
    "fullhouse":"ナッツメイド","quads":"ナッツメイド","straight_flush":"ナッツメイド",
    "set":"ストロング","trips":"ストロング","straight":"ストロング","flush":"ストロング",
    "two_pair":"ツーペア",
    "top_pair":"トップペア以上","overpair":"トップペア以上",
    "second_pair":"ミドルペア","third_pair":"ミドルペア","underpair":"ミドルペア","low_pair":"ミドルペア",
    "no_made_hand":"エア","king_high":"エア","ace_high":"エア",
}
TIER_ORDER = ["ナッツメイド","ストロング","ツーペア","トップペア以上","ミドルペア","エア"]
EQ_VAL = {"best_hands":9,"good_hands":6,"weak_hands":3,"trash_hands":0}
BS_VAL = {"small_33":0,"med_75p":1,"med_100p":2,"overbet":3,"overbet_185":4,"allin":5}
POT_VAL = {"SRP":0,"DEF":2,"3BP":2,"4BP":4}


def board_label(flop: str) -> str:
    """board を 4 種に分類: dry / paired / connected / monotone."""
    if len(flop) < 6: return "dry"
    cards = [flop[i*2:i*2+2] for i in range(3)]
    RANKS = "23456789TJQKA"
    try:
        rvals = sorted([RANKS.index(c[0].upper()) for c in cards], reverse=True)
    except ValueError:
        return "dry"
    suits = [c[1].lower() for c in cards]
    paired = rvals[0] == rvals[1] or rvals[1] == rvals[2]
    monotone = len(set(suits)) == 1
    gap_top = rvals[0] - rvals[1]; gap_bot = rvals[1] - rvals[2]
    connected = gap_top <= 2 and gap_bot <= 2 and not paired
    if paired: return "paired"
    if monotone: return "monotone"
    if connected: return "connected"
    return "dry"


def parse_pot(scn):
    s = scn.lower()
    return "4BP" if "4bp" in s else "3BP" if "3bp" in s else \
           "DEF" if ("cr_def" in s or "donk_def" in s) else "SRP"


# === Build tier × board → eq_bucket lookup ===
print("Loading and building grid lookup...")
grid_dist: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
all_rows = []
with CSV_PATH.open() as f:
    for r in csv.DictReader(f):
        tier = MATCHA_TIER.get(r["mv_cat"], None)
        eq_b = r.get("equity_bucket", "")
        bs = r.get("ip_bet_size", "")
        if tier is None or eq_b not in EQ_VAL or bs not in BS_VAL: continue
        board = r.get("board_str", "")[:6].lower()
        bl = board_label(board)
        grid_dist[(tier, bl)][eq_b] += 1
        try:
            pot = parse_pot(r["scenario_id"])
            ba = r["best_action"].lower()
            efv = float(r["ev_fold"]); ecv = float(r["ev_call"]); erv = float(r["ev_raise"])
            be = float(r["best_ev"])
        except (KeyError, ValueError):
            continue
        all_rows.append({
            "tier": tier, "board_label": bl, "true_eq": eq_b, "bs": bs, "pot": pot,
            "best_action": ba, "ev_f": efv, "ev_c": ecv, "ev_r": erv, "best_ev": be,
        })

print(f"Loaded {len(all_rows):,} rows")

# === Grid から modal eq_bucket を抽出 (素人用 lookup) ===
GRID: dict[tuple[str, str], str] = {}
for key, dist in grid_dist.items():
    total = sum(dist.values())
    if total < 50: continue
    modal = max(dist.items(), key=lambda x: x[1])
    GRID[key] = modal[0]

print(f"\n=== Grid (tier × board → modal eq_bucket) ===")
BOARD_TYPES = ["dry", "paired", "connected", "monotone"]
print(f"{'tier':18}", end=" ")
for bl in BOARD_TYPES:
    print(f"{bl:>14}", end=" ")
print()
for tier in TIER_ORDER:
    print(f"  {tier:16}", end=" ")
    for bl in BOARD_TYPES:
        eq = GRID.get((tier, bl), "?")
        print(f"{eq:>14}", end=" ")
    print()


def evaluate_with_grid(t_call: int, t_raise: int):
    """Grid 経由で eq を推定、Score 計算。"""
    correct = 0
    losses = []
    huge = 0
    for r in all_rows:
        # Grid lookup
        eq_b = GRID.get((r["tier"], r["board_label"]), "weak_hands")  # fallback to weak
        eq_v = EQ_VAL[eq_b]
        bs_v = BS_VAL[r["bs"]]
        pot_v = POT_VAL[r["pot"]]
        score = eq_v - bs_v + pot_v
        if score >= t_raise: pred = "raise"
        elif score >= t_call: pred = "call"
        else: pred = "fold"
        pred_ev = {"fold": r["ev_f"], "call": r["ev_c"], "raise": r["ev_r"]}[pred]
        loss = max(0, r["best_ev"] - pred_ev)
        losses.append(loss)
        if loss > 5: huge += 1
        if pred == r["best_action"]: correct += 1
    n = len(all_rows)
    return correct/n*100, sum(losses)/n, huge/n*100


def evaluate_with_true_eq(t_call: int, t_raise: int):
    """正しい eq_bucket を直接使う (比較用 upper bound)."""
    correct = 0; losses = []; huge = 0
    for r in all_rows:
        eq_v = EQ_VAL[r["true_eq"]]
        bs_v = BS_VAL[r["bs"]]
        pot_v = POT_VAL[r["pot"]]
        score = eq_v - bs_v + pot_v
        if score >= t_raise: pred = "raise"
        elif score >= t_call: pred = "call"
        else: pred = "fold"
        pred_ev = {"fold": r["ev_f"], "call": r["ev_c"], "raise": r["ev_r"]}[pred]
        loss = max(0, r["best_ev"] - pred_ev)
        losses.append(loss)
        if loss > 5: huge += 1
        if pred == r["best_action"]: correct += 1
    n = len(all_rows)
    return correct/n*100, sum(losses)/n, huge/n*100


print("\n=== Grid search 閾値最適化 ===")
# Score range: eq 0-9, bs 0-5, pot 0-4 → [-5, 13]
best_grid = (-100, 999, 0, 0)
best_true = (-100, 999, 0, 0)
for tc in range(-5, 12):
    for tr in range(tc+1, 14):
        a_g, v_g, h_g = evaluate_with_grid(tc, tr)
        a_t, v_t, h_t = evaluate_with_true_eq(tc, tr)
        bal_g = -a_g + 10*v_g + 5*h_g
        bal_t = -a_t + 10*v_t + 5*h_t
        if -bal_g > -(-best_grid[0] + 10*best_grid[1] + 5*0):
            best_grid = (a_g, v_g, h_g, tc, tr)
        if -bal_t > -(-best_true[0] + 10*best_true[1] + 5*0):
            best_true = (a_t, v_t, h_t, tc, tr)

# Use balanced criterion (simple)
best_grid = max([(evaluate_with_grid(tc, tr), tc, tr) for tc in range(-5, 12) for tr in range(tc+1, 14)],
                key=lambda x: x[0][0] - 10*x[0][1])
best_true = max([(evaluate_with_true_eq(tc, tr), tc, tr) for tc in range(-5, 12) for tr in range(tc+1, 14)],
                key=lambda x: x[0][0] - 10*x[0][1])

print(f"\nGrid 経由 (素人用):")
print(f"  Best: t_call={best_grid[1]}, t_raise={best_grid[2]} → acc={best_grid[0][0]:.2f}%, loss={best_grid[0][1]:.4f}BB, huge={best_grid[0][2]:.2f}%")
print(f"\n直接 eq (中級者用):")
print(f"  Best: t_call={best_true[1]}, t_raise={best_true[2]} → acc={best_true[0][0]:.2f}%, loss={best_true[0][1]:.4f}BB, huge={best_true[0][2]:.2f}%")


# === Report ===
lines = []
lines.append("# eq グリッド表 — 素人向け MATCHA 公式")
lines.append("")
lines.append("equity 計算ができない初心者向けに、自分の手 (tier) × board の 24-cell grid で")
lines.append("eq_bucket を lookup する方式。")
lines.append("")
lines.append("## 簡易公式")
lines.append("")
lines.append("```")
lines.append("Score = eq - bs + pot")
lines.append("")
lines.append("eq:   下のグリッド表で lookup")
lines.append("bs:   small=0, 75%=1, 100%=2, over=3, over185=4, allin=5  (引く)")
lines.append("pot:  SRP=0, DEF=2, 3BP=2, 4BP=4")
lines.append("")
lines.append(f"if Score >= {best_grid[2]}: raise")
lines.append(f"elif Score >= {best_grid[1]}: call")
lines.append("else: fold")
lines.append("```")
lines.append("")

lines.append("## eq グリッド (tier × board → eq_bucket)")
lines.append("")
lines.append("| 自分の手役 | dry | paired | connected | monotone |")
lines.append("|-----------|-----|--------|-----------|----------|")
for tier in TIER_ORDER:
    row = f"| **{tier}** |"
    for bl in BOARD_TYPES:
        eq = GRID.get((tier, bl), "?")
        eq_v = EQ_VAL.get(eq, 0)
        eq_jp = {"best_hands":"best=9","good_hands":"good=6","weak_hands":"weak=3","trash_hands":"trash=0"}.get(eq, "?")
        row += f" {eq_jp} |"
    lines.append(row)
lines.append("")

lines.append("## 性能比較")
lines.append("")
lines.append("| 方式 | rules | accuracy | avg loss | huge% | 暗算負荷 |")
lines.append("|------|---:|---:|---:|---:|---|")
lines.append(f"| **grid 経由 (素人向け)** | グリッド + 3 値 | {best_grid[0][0]:.2f}% | {best_grid[0][1]:.4f} BB | {best_grid[0][2]:.2f}% | 低 |")
lines.append(f"| 直接 eq (中級者) | 3 値のみ | {best_true[0][0]:.2f}% | {best_true[0][1]:.4f} BB | {best_true[0][2]:.2f}% | 中 (eq 概算必要) |")
lines.append(f"| 旧式 (tier + eq) | 4 値 | 71.02% | 0.34 BB | 1.22% | 中 |")
lines.append("")

lines.append("## 暗算の例題 (素人用グリッド経由)")
lines.append("")
ex_grid_lookups = [
    ("SRP / 自分 KKx2 (overpair) on Ks-7-2 (dry) / 相手 33% bet", "トップペア以上", "dry", "SRP", "small_33"),
    ("SRP / AA on 9-8-7 (connected) / 相手 100% bet", "トップペア以上", "connected", "SRP", "med_100p"),
    ("SRP / 22 on K-7-2 (dry, 自分 underpair) / 相手 75% bet", "ミドルペア", "dry", "SRP", "med_75p"),
    ("4BP / AsKs (TP) on As-7-2 / 相手 overbet", "トップペア以上", "dry", "4BP", "overbet"),
    ("SRP / エア on monotone / 相手 100% bet", "エア", "monotone", "SRP", "med_100p"),
]
for desc, tier, bl, pot, bs in ex_grid_lookups:
    eq = GRID.get((tier, bl), "weak_hands")
    eq_v = EQ_VAL[eq]; bs_v = BS_VAL[bs]; pot_v = POT_VAL[pot]
    score = eq_v - bs_v + pot_v
    pred = "raise" if score >= best_grid[2] else "call" if score >= best_grid[1] else "fold"
    lines.append(f"### {desc}")
    lines.append(f"- tier=`{tier}` × board=`{bl}` → eq=**{eq.replace('_hands','')}** ({eq_v} 点)")
    lines.append(f"- Score = {eq_v} - {bs_v} + {pot_v} = **{score}** → **{pred}**")
    lines.append("")

lines.append("## 利用フロー")
lines.append("")
lines.append("```")
lines.append("1. 自分の手を見る → 6 tier のどれか判定 (e.g., overpair / TP+)")
lines.append("2. board を見る → 4 種類のどれか判定 (dry/paired/connected/monotone)")
lines.append("3. グリッド表で eq_bucket lookup")
lines.append("4. 相手の bet サイズ → bs 値 (0-5)")
lines.append("5. pot 種別 (SRP/3BP/4BP) → pot 値 (0/2/4)")
lines.append("6. Score = eq - bs + pot を計算")
lines.append("7. >= 16 raise / >= 3 call / それ未満 fold")
lines.append("```")
lines.append("")

lines.append("## 中級者向け (eq 概算スキル獲得後)")
lines.append("")
lines.append("自分の equity 概算ができれば、grid を skip:")
lines.append("- 70% 以上 → best=9")
lines.append("- 50-70%  → good=6")
lines.append("- 30-50%  → weak=3")
lines.append("- 30% 未満 → trash=0")
lines.append("")
lines.append(f"性能: accuracy {best_true[0][0]:.1f}% / loss {best_true[0][1]:.3f} BB")
lines.append("(grid 経由より若干高精度、暗算負荷は equity 概算分が上乗せ)")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
