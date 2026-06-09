"""MATCHA Score 最終形 (18 cells) の huge loss 分析。

【公式】
Score = 4 × tier + Grid[tier][board_3] + 3 × DV
      + 2 × overcards + 3 × pot − 2 × bs − 2

Grid:
         dry  paired  wet
エア      0   2     -3
ミドル    7   12     4
TP+     13   2      2
2P       2   14     0
ストロ    7   10    12
ナッツ   11   9      9

if Score >= 33: raise / >= 6: call / else: fold

性能: accuracy 69.44% / avg loss 0.42 BB / huge 1.77%
"""
from __future__ import annotations
import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/HUGE_LOSS_FINAL.md"

RANKS = "23456789TJQKA"
MV_TIER_MAP = {
    "fullhouse":"ナッツメイド","quads":"ナッツメイド","straight_flush":"ナッツメイド",
    "set":"ストロング","trips":"ストロング","straight":"ストロング","flush":"ストロング",
    "two_pair":"ツーペア",
    "top_pair":"トップペア以上","overpair":"トップペア以上",
    "second_pair":"ミドルペア","third_pair":"ミドルペア","underpair":"ミドルペア","low_pair":"ミドルペア",
    "no_made_hand":"エア","king_high":"エア","ace_high":"エア",
}
TIER_IDX = {"エア":0,"ミドルペア":1,"トップペア以上":2,"ツーペア":3,"ストロング":4,"ナッツメイド":5}
TIER_NAMES = ["エア","ミドルペア","トップペア以上","ツーペア","ストロング","ナッツメイド"]
BL_NAMES = ["dry","paired","wet"]

# 18 cells grid (整数版)
GRID = [
    [ 0,  2, -3],  # エア
    [ 7, 12,  4],  # ミドルペア
    [13,  2,  2],  # TP+
    [ 2, 14,  0],  # ツーペア
    [ 7, 10, 12],  # ストロング
    [11,  9,  9],  # ナッツメイド
]

DV_BASE = {"combo_draw":4,"nut_flush_draw":3,"flush_draw":3,"oesd":3,"gutshot":1,
           "twocards_bdfd":1,"onecard_bdfd":0,"no_draw":0}
BS_BASE = {"small_33":0,"med_75p":1,"med_100p":2,"overbet":3,"overbet_185":4,"allin":5}
OPP_R = {"SRP":0,"DEF":2,"3BP":2,"4BP":4}


def parse_pot(scn):
    s = scn.lower()
    return "4BP" if "4bp" in s else "3BP" if "3bp" in s else \
           "DEF" if ("cr_def" in s or "donk_def" in s) else "SRP"


def board_3(board):
    if len(board) < 6: return 0
    cards = [board[i*2:i*2+2] for i in range(3)]
    try:
        rvals = sorted([RANKS.index(c[0].upper()) for c in cards], reverse=True)
    except ValueError:
        return 0
    suits = [c[1].lower() for c in cards]
    if rvals[0]==rvals[1] or rvals[1]==rvals[2]: return 1  # paired
    if len(set(suits))==1: return 2  # monotone → wet
    if rvals[0]-rvals[1] <=2 and rvals[1]-rvals[2] <=2: return 2  # connected → wet
    return 0  # dry


def hero_oc(card_a, card_b, board):
    try:
        a_r = RANKS.index(card_a[0].upper()); b_r = RANKS.index(card_b[0].upper())
        cards = [board[i*2:i*2+2] for i in range(3)]
        b_h = max([RANKS.index(c[0].upper()) for c in cards])
        return sum(1 for r in (a_r, b_r) if r > b_h)
    except (ValueError, IndexError):
        return 0


print("Analyzing huge loss with MATCHA Score Final (18 cells)...")
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
        tier_i = TIER_IDX[tier]
        b3 = board_3(board)
        dv = DV_BASE.get(r.get("dv_cat", "no_draw"), 0)
        bs_v = BS_BASE[bs_str]
        oc = hero_oc(ca, cb, board)
        pot = parse_pot(r["scenario_id"])
        opp = OPP_R[pot]

        score = 4*tier_i + GRID[tier_i][b3] + 3*dv + 2*oc + 3*opp - 2*bs_v - 2
        if score >= 33: pred = "raise"
        elif score >= 6: pred = "call"
        else: pred = "fold"
        pred_ev = {"fold":efv,"call":ecv,"raise":erv}[pred]
        loss = max(0, be - pred_ev)

        record = {
            "tier": tier, "bl": BL_NAMES[b3], "pot": pot,
            "bs": bs_str, "best_action": ba, "pred": pred, "loss": loss,
            "mv_cat": mv, "dv_cat": r.get("dv_cat","no_draw"),
            "score": score, "board": board,
        }
        all_records.append(record)
        if loss > 5:
            huge_records.append(record)

n_total = len(all_records)
n_huge = len(huge_records)
avg_loss = sum(r['loss'] for r in all_records) / n_total
huge_avg = sum(r['loss'] for r in huge_records) / n_huge if n_huge else 0
print(f"Total: {n_total:,}, huge: {n_huge:,} ({n_huge/n_total*100:.2f}%)")
print(f"avg loss: {avg_loss:.4f} BB, huge spots avg loss: {huge_avg:.2f} BB")

# === Confusion: pred → best ===
print(f"\n=== Pred → Best confusion (huge loss spots) ===")
confusion = defaultdict(int)
for r in huge_records:
    confusion[(r["pred"], r["best_action"])] += 1
for (p, b), c in sorted(confusion.items(), key=lambda x: -x[1]):
    print(f"  pred={p} but best={b}: {c} ({c/n_huge*100:.1f}%)")

# === Top patterns ===
breakdown = defaultdict(lambda: {"n":0, "loss_sum":0.0})
for r in huge_records:
    key = (r["tier"], r["bl"], r["pot"], r["pred"], r["best_action"])
    breakdown[key]["n"] += 1
    breakdown[key]["loss_sum"] += r["loss"]
top = sorted(breakdown.items(), key=lambda x: -x[1]["n"])[:25]

print(f"\n=== Top 25 huge loss patterns ===")
print(f"{'tier':16} {'board':8} {'pot':5} {'pred':>6} {'best':>6} {'n':>5} {'avg':>9}")
for (tier, bl, pot, pred, best), d in top:
    avg_l = d["loss_sum"]/d["n"]
    print(f"  {tier:14} {bl:8} {pot:5} {pred:>6} {best:>6} {d['n']:>5} {avg_l:>7.2f}BB")

# === pot 別 ===
print(f"\n=== Huge loss by pot type ===")
pot_huge = defaultdict(int); pot_total = defaultdict(int)
for r in all_records:
    pot_total[r["pot"]] += 1
    if r["loss"] > 5: pot_huge[r["pot"]] += 1
for pot in ["SRP","DEF","3BP","4BP"]:
    if pot_total[pot] == 0: continue
    pct = pot_huge[pot] / pot_total[pot] * 100
    print(f"  {pot}: {pot_huge[pot]:,}/{pot_total[pot]:,} ({pct:.2f}%)")

# === tier × bs ===
print(f"\n=== Huge loss: tier × bs (top) ===")
tb = defaultdict(int)
for r in huge_records: tb[(r["tier"], r["bs"])] += 1
for (t, bs), n in sorted(tb.items(), key=lambda x: -x[1])[:15]:
    print(f"  {t:14} × {bs:14}: {n}")

# === 旧公式との比較 ===
print(f"\n=== Comparison with previous (24 cells) huge loss ===")
print(f"  24 cells v1: huge 2.28%, avg 0.48 BB, huge avg ~11 BB")
print(f"  18 cells (本): huge {n_huge/n_total*100:.2f}%, avg {avg_loss:.4f} BB, huge avg {huge_avg:.2f} BB")


# Report
lines = []
lines.append("# Huge Loss 分析 — MATCHA Score Final (18 cells)")
lines.append("")
lines.append(f"## 集計")
lines.append("")
lines.append(f"- 全 spots: {n_total:,}")
lines.append(f"- huge loss (>5 BB): **{n_huge:,} ({n_huge/n_total*100:.2f}%)**")
lines.append(f"- 全体 avg loss: **{avg_loss:.4f} BB**")
lines.append(f"- huge spots の avg: **{huge_avg:.2f} BB**")
lines.append("")

lines.append("## Pred → Best confusion (huge loss spots)")
lines.append("")
lines.append("| 公式 pred | GTO best | n | % | 解釈 |")
lines.append("|---|---|---:|---:|------|")
INTERPRET = {
    ("fold","call"): "公式 fold だが call が正解 (MDF 不足)",
    ("fold","raise"): "公式 fold だが raise が正解 (大 blunder)",
    ("call","fold"): "公式 call だが fold が正解 (痛い bluff catch)",
    ("call","raise"): "公式 call だが raise が正解 (機会損失)",
    ("raise","fold"): "公式 raise だが fold が正解 (大 blunder)",
    ("raise","call"): "公式 raise だが call が正解 (過剰 aggression)",
}
for (p, b), c in sorted(confusion.items(), key=lambda x: -x[1]):
    intr = INTERPRET.get((p,b), "?")
    lines.append(f"| {p} | {b} | {c} | {c/n_huge*100:.1f}% | {intr} |")
lines.append("")

lines.append("## Top 25 huge loss patterns")
lines.append("")
lines.append("| tier | board | pot | pred | best | n | avg_loss |")
lines.append("|------|------|-----|------|------|--:|---:|")
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

lines.append("## tier × bs (huge spots)")
lines.append("")
lines.append("| tier | bs | n |")
lines.append("|------|-----|--:|")
for (t, bs), n in sorted(tb.items(), key=lambda x: -x[1])[:15]:
    lines.append(f"| {t} | {bs} | {n} |")
lines.append("")

lines.append("## 旧公式との比較")
lines.append("")
lines.append("| 公式 | huge% | avg loss | huge avg |")
lines.append("|------|---:|---:|---:|")
lines.append("| v1 (24 cells, eq accuracy 最適化) | 2.28% | 0.48 BB | ~11 BB |")
lines.append("| **MATCHA Score Final (18 cells)** | **{:.2f}%** | **{:.4f} BB** | **{:.2f} BB** |".format(
    n_huge/n_total*100, avg_loss, huge_avg))
lines.append("")

lines.append("## 主要な「公式の例外」候補 (n ≥ 50)")
lines.append("")
big_patterns = [(k, d) for k, d in top if d["n"] >= 50]
if big_patterns:
    for (tier, bl, pot, pred, best), d in big_patterns:
        avg_l = d["loss_sum"]/d["n"]
        lines.append(f"- **{tier} × {bl} × {pot}**: 公式 `{pred}` → GTO `{best}` ({d['n']} cases, avg {avg_l:.2f} BB)")
lines.append("")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
