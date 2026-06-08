"""整数公式の huge loss (>5 BB) を分類 — 公式が苦手な spot を特定。"""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/HUGE_LOSS_ANALYSIS.md"

RANKS = "23456789TJQKA"
MV_TIER_MAP = {
    "fullhouse":"ナッツメイド","quads":"ナッツメイド","straight_flush":"ナッツメイド",
    "set":"ストロング","trips":"ストロング","straight":"ストロング","flush":"ストロング",
    "two_pair":"ツーペア",
    "top_pair":"トップペア以上","overpair":"トップペア以上",
    "second_pair":"ミドルペア","third_pair":"ミドルペア","underpair":"ミドルペア","low_pair":"ミドルペア",
    "no_made_hand":"エア","king_high":"エア","ace_high":"エア",
}
TIERS = ["エア","ミドルペア","トップペア以上","ツーペア","ストロング","ナッツメイド"]
BLS = ["dry","paired","connected","monotone"]
DV_BASE = {"combo_draw":4,"nut_flush_draw":3,"flush_draw":3,"oesd":3,"gutshot":1,
           "twocards_bdfd":1,"onecard_bdfd":0,"no_draw":0}
BS_BASE = {"small_33":0,"med_75p":1,"med_100p":2,"overbet":3,"overbet_185":4,"allin":5}
OPP_R = {"SRP":0,"DEF":2,"3BP":2,"4BP":4}

# 整数公式 grid (loss-opt rounded)
GRID_INT = {
    ("エア","dry"):2, ("エア","paired"):8, ("エア","connected"):0, ("エア","monotone"):1,
    ("ミドルペア","dry"):4, ("ミドルペア","paired"):10, ("ミドルペア","connected"):2, ("ミドルペア","monotone"):5,
    ("トップペア以上","dry"):8, ("トップペア以上","paired"):1, ("トップペア以上","connected"):6, ("トップペア以上","monotone"):4,
    ("ツーペア","dry"):4, ("ツーペア","paired"):9, ("ツーペア","connected"):1, ("ツーペア","monotone"):3,
    ("ストロング","dry"):8, ("ストロング","paired"):5, ("ストロング","connected"):9, ("ストロング","monotone"):9,
    ("ナッツメイド","dry"):8, ("ナッツメイド","paired"):6, ("ナッツメイド","connected"):3, ("ナッツメイド","monotone"):7,
}


def parse_pot(scn):
    s = scn.lower()
    return "4BP" if "4bp" in s else "3BP" if "3bp" in s else \
           "DEF" if ("cr_def" in s or "donk_def" in s) else "SRP"


def board_label(board: str) -> str:
    if len(board) < 6: return "dry"
    cards = [board[i*2:i*2+2] for i in range(3)]
    try:
        rvals = sorted([RANKS.index(c[0].upper()) for c in cards], reverse=True)
    except ValueError:
        return "dry"
    suits = [c[1].lower() for c in cards]
    if rvals[0]==rvals[1] or rvals[1]==rvals[2]: return "paired"
    if len(set(suits))==1: return "monotone"
    if rvals[0]-rvals[1] <= 2 and rvals[1]-rvals[2] <= 2: return "connected"
    return "dry"


def hero_oc(card_a, card_b, board):
    try:
        a_r = RANKS.index(card_a[0].upper()); b_r = RANKS.index(card_b[0].upper())
        cards = [board[i*2:i*2+2] for i in range(3)]
        b_h = max([RANKS.index(c[0].upper()) for c in cards])
        return sum(1 for r in (a_r, b_r) if r > b_h)
    except (ValueError, IndexError):
        return 0


print("Analyzing huge loss with integer formula...")
huge_records = []
all_records = []
n_skip = 0
with CSV_PATH.open() as f:
    for r in csv.DictReader(f):
        mv = r.get("mv_cat", "")
        bs_str = r.get("ip_bet_size", "")
        if mv not in MV_TIER_MAP or bs_str not in BS_BASE: n_skip+=1; continue
        board = r.get("board_str", "")[:6].lower()
        if len(board) < 6: n_skip+=1; continue
        ca = r.get("card_a", ""); cb = r.get("card_b", "")
        if not ca or not cb: n_skip+=1; continue
        try:
            ba = r["best_action"].lower()
            efv = float(r["ev_fold"]); ecv = float(r["ev_call"]); erv = float(r["ev_raise"])
            be = float(r["best_ev"])
        except (KeyError, ValueError):
            n_skip+=1; continue

        tier = MV_TIER_MAP[mv]
        bl = board_label(board)
        tier_idx = TIERS.index(tier)
        dv = DV_BASE.get(r.get("dv_cat", "no_draw"), 0)
        opp_r = OPP_R[parse_pot(r["scenario_id"])]
        bs_v = BS_BASE[bs_str]
        oc = hero_oc(ca, cb, board)
        grid_v = GRID_INT[(tier, bl)]
        score = 3*tier_idx + grid_v + 2*dv + 2*oc + 2*opp_r - 1*bs_v - 2
        if score >= 26: pred = "raise"
        elif score >= 6: pred = "call"
        else: pred = "fold"
        pred_ev = {"fold":efv,"call":ecv,"raise":erv}[pred]
        loss = max(0, be - pred_ev)

        record = {
            "tier": tier, "bl": bl, "pot": parse_pot(r["scenario_id"]),
            "bs": bs_str, "best_action": ba, "pred": pred, "loss": loss,
            "mv_cat": mv, "dv_cat": r.get("dv_cat","no_draw"),
            "score": score, "board": board, "card_a": ca, "card_b": cb,
            "scenario": r["scenario_id"],
        }
        all_records.append(record)
        if loss > 5:
            huge_records.append(record)

n_total = len(all_records)
n_huge = len(huge_records)
print(f"Total: {n_total:,}, huge loss (>5 BB): {n_huge:,} ({n_huge/n_total*100:.2f}%)")
print(f"avg loss: {sum(r['loss'] for r in all_records)/n_total:.4f} BB")
print(f"avg huge loss: {sum(r['loss'] for r in huge_records)/n_huge:.2f} BB")

# === 分類 ===
print("\n=== Huge loss by (tier, board, pot, predicted vs best_action) ===")
breakdown = defaultdict(lambda: {"n":0, "loss_sum":0.0})
for r in huge_records:
    key = (r["tier"], r["bl"], r["pot"], r["pred"], r["best_action"])
    breakdown[key]["n"] += 1
    breakdown[key]["loss_sum"] += r["loss"]

top = sorted(breakdown.items(), key=lambda x: -x[1]["n"])[:30]
print(f"\n{'tier':16} {'board':10} {'pot':5} {'pred':>6} {'best':>6} {'n':>5} {'avg_loss':>8}")
for (tier, bl, pot, pred, best), d in top:
    avg_l = d["loss_sum"]/d["n"]
    print(f"  {tier:14} {bl:10} {pot:5} {pred:>6} {best:>6} {d['n']:>5} {avg_l:>7.2f}BB")

# === pot 別の huge loss ===
print("\n=== Huge loss by pot type ===")
pot_huge = defaultdict(int); pot_total = defaultdict(int)
for r in all_records:
    pot_total[r["pot"]] += 1
    if r["loss"] > 5: pot_huge[r["pot"]] += 1
for pot in ["SRP","DEF","3BP","4BP"]:
    if pot_total[pot] == 0: continue
    pct = pot_huge[pot] / pot_total[pot] * 100
    print(f"  {pot}: {pot_huge[pot]:,}/{pot_total[pot]:,} ({pct:.2f}%)")

# === predicted action × best_action confusion ===
print("\n=== Huge loss: pred → best confusion ===")
confusion = defaultdict(int)
for r in huge_records:
    confusion[(r["pred"], r["best_action"])] += 1
for (p, b), c in sorted(confusion.items(), key=lambda x: -x[1]):
    print(f"  pred={p} but best={b}: {c} cases")

# === tier × bs ===
print("\n=== Huge loss: tier × bs ===")
tb = defaultdict(int)
for r in huge_records: tb[(r["tier"], r["bs"])] += 1
for (t, bs), n in sorted(tb.items(), key=lambda x: -x[1])[:15]:
    print(f"  {t:14} × {bs:12}: {n}")


# Report
lines = []
lines.append("# Huge Loss (>5 BB) 分類 — 公式の苦手 spot")
lines.append("")
lines.append(f"整数公式 (accuracy 66.5% / avg loss 0.48 BB / huge 2.28%)")
lines.append(f"の huge loss (>5 BB) を発生 spot で分類。")
lines.append("")
lines.append(f"## 集計")
lines.append("")
lines.append(f"- 全 spots: {n_total:,}")
lines.append(f"- huge loss spots: {n_huge:,} ({n_huge/n_total*100:.2f}%)")
lines.append(f"- huge spots の avg loss: {sum(r['loss'] for r in huge_records)/n_huge:.2f} BB")
lines.append("")

lines.append("## Top 30 huge loss patterns (tier × board × pot × pred→best)")
lines.append("")
lines.append("| tier | board | pot | pred | best | n | avg_loss |")
lines.append("|------|-------|-----|------|------|--:|---:|")
for (tier, bl, pot, pred, best), d in top:
    avg_l = d["loss_sum"]/d["n"]
    lines.append(f"| {tier} | {bl} | {pot} | {pred} | {best} | {d['n']} | {avg_l:.2f} BB |")
lines.append("")

lines.append("## Huge loss by pot type")
lines.append("")
lines.append("| pot | huge / total | huge% |")
lines.append("|-----|--:|---:|")
for pot in ["SRP","DEF","3BP","4BP"]:
    if pot_total[pot] == 0: continue
    pct = pot_huge[pot] / pot_total[pot] * 100
    lines.append(f"| {pot} | {pot_huge[pot]:,} / {pot_total[pot]:,} | {pct:.2f}% |")
lines.append("")

lines.append("## Predicted → Best confusion (huge loss spots のみ)")
lines.append("")
lines.append("| 公式予測 | GTO best | n | 解釈 |")
lines.append("|---------|---------|---:|------|")
for (p, b), c in sorted(confusion.items(), key=lambda x: -x[1]):
    interpretation = {
        ("fold","call"): "公式 fold だが call が正解",
        ("fold","raise"): "公式 fold だが raise が正解 (大きな機会損失)",
        ("call","fold"): "公式 call だが fold が正解 (痛い call)",
        ("call","raise"): "公式 call だが raise が正解",
        ("raise","fold"): "公式 raise だが fold が正解 (大きな blunder)",
        ("raise","call"): "公式 raise だが call が正解 (over-aggression)",
    }.get((p,b), "?")
    lines.append(f"| {p} | {b} | {c} | {interpretation} |")
lines.append("")

lines.append("## 主要な苦手パターン (n ≥ 100)")
lines.append("")
big_patterns = [(k, d) for k, d in top if d["n"] >= 100]
if big_patterns:
    for (tier, bl, pot, pred, best), d in big_patterns:
        avg_l = d["loss_sum"]/d["n"]
        lines.append(f"- **{tier} × {bl} board × {pot}**: 公式 `{pred}` だが GTO `{best}` ({d['n']} cases, avg {avg_l:.2f} BB loss)")
lines.append("")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
