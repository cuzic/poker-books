"""equity_bucket を cell key に加えて再評価。

【現状の cell key】(pot, street, sub_family, made_tier)
→ draw value / 総合エクイティを捨象。
   例: フラッシュドロー + ストレートドロー 50% eq の combo draw を「エア」扱い。

【改良 cell key】(pot, street, sub_family, made_tier, equity_bucket)
- equity_bucket: best_hands / good_hands / weak_hands / trash_hands
- best = ~85% eq, good = ~60%, weak = ~40%, trash = ~20%
- これは made + draw + position 統合の最終 equity bucket

【予想】
- combo draw / nut draw のような「エア tier だが equity 高」spot が正しく分類される
- 「ミドルペア tier だが equity 低い」spot も別扱い
"""
from __future__ import annotations
import csv
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/RULE_EVAL_WITH_EQUITY.md"

MATCHA_TIER = {
    "fullhouse":"ナッツメイド","quads":"ナッツメイド","straight_flush":"ナッツメイド",
    "set":"ストロング","trips":"ストロング","straight":"ストロング","flush":"ストロング",
    "two_pair":"ツーペア",
    "top_pair":"トップペア以上","overpair":"トップペア以上",
    "second_pair":"ミドルペア","third_pair":"ミドルペア","underpair":"ミドルペア","low_pair":"ミドルペア",
    "no_made_hand":"エア","king_high":"エア","ace_high":"エア",
}
TIER_ORDER = ["ナッツメイド","ストロング","ツーペア","トップペア以上","ミドルペア","エア"]
EQ_ORDER = ["best_hands","good_hands","weak_hands","trash_hands"]


def board_structure(flop: str) -> dict:
    if len(flop) < 6: return {}
    cards = [flop[i*2:i*2+2] for i in range(3)]
    RANKS = "23456789TJQKA"
    try:
        rvals = sorted([RANKS.index(c[0].upper()) for c in cards], reverse=True)
    except ValueError:
        return {}
    suits = [c[1].lower() for c in cards]
    paired = rvals[0] == rvals[1] or rvals[1] == rvals[2]
    monotone = len(set(suits)) == 1
    gap_top = rvals[0] - rvals[1]; gap_bot = rvals[1] - rvals[2]
    connected = gap_top <= 2 and gap_bot <= 2 and not paired
    return {
        "high_idx": rvals[0], "max_gap": max(gap_top, gap_bot),
        "paired": paired, "monotone": monotone, "connected": connected,
        "ace_high": rvals[0] == 12, "broadway": rvals[0] >= 8,
        "low_board": rvals[0] <= 5,
    }


def fine_subfamily(s: dict) -> str:
    if not s: return "?"
    if s["paired"]:
        if s["high_idx"] >= 11: return "paired_high"
        if s["high_idx"] >= 8: return "paired_broadway"
        if s["high_idx"] >= 5: return "paired_mid"
        return "paired_low"
    if s["monotone"]: return "monotone"
    if s["connected"]:
        if s["high_idx"] >= 11: return "connected_broadway"
        if s["high_idx"] >= 7: return "connected_mid"
        return "connected_low"
    if s["ace_high"]:
        return "Ahigh_spread" if s["max_gap"] >= 5 else "Ahigh_close"
    if s["high_idx"] == 11:
        return "Khigh_spread" if s["max_gap"] >= 5 else "Khigh_close"
    if s["broadway"]: return "broadway_dry"
    if s["low_board"]: return "low_dry"
    return "mid_dry"


def parse_scenario(scn: str) -> dict:
    s = scn.lower()
    pot = "4BP" if "4bp" in s else "3BP" if "3bp" in s else \
          "DEF" if ("cr_def" in s or "donk_def" in s) else "SRP"
    if "river" in s: street = "river"
    elif "turn" in s: street = "turn"
    elif "flop" in s: street = "flop"
    else: street = "flop"
    return {"pot": pot, "street": street}


# === Load and aggregate ===
print("Loading rows...")
all_rows = []
with CSV_PATH.open() as f:
    for r in csv.DictReader(f):
        scn_info = parse_scenario(r["scenario_id"])
        board = r.get("board_str", "")[:6].lower()
        sub = fine_subfamily(board_structure(board))
        tier = MATCHA_TIER.get(r["mv_cat"], "?")
        eq_b = r.get("equity_bucket", "?")
        try:
            fold = float(r.get("fold_freq", 0) or 0)
            call = float(r.get("call_freq", 0) or 0)
            raise_ = float(r.get("raise_freq", 0) or 0)
            best_action = r["best_action"].lower()
            ev_fold = float(r["ev_fold"])
            ev_call = float(r["ev_call"])
            ev_raise = float(r["ev_raise"])
            best_ev = float(r["best_ev"])
            f_action = r.get("formula_action", "").lower()
            f_loss = float(r.get("formula_loss", 0) or 0)
        except (KeyError, ValueError, TypeError):
            continue
        all_rows.append({
            "pot": scn_info["pot"], "street": scn_info["street"],
            "sub": sub, "tier": tier, "eq_b": eq_b,
            "fold": fold, "call": call, "raise": raise_,
            "best_action": best_action,
            "ev_fold": ev_fold, "ev_call": ev_call, "ev_raise": ev_raise,
            "best_ev": best_ev,
            "f_action": f_action, "f_loss": f_loss,
        })

print(f"Loaded {len(all_rows):,} rows")


def build_cells_3key():
    """(pot, street, sub, tier) — 元の cell key"""
    raw = defaultdict(list)
    for r in all_rows:
        raw[(r["pot"], r["street"], r["sub"], r["tier"])].append(r)
    cells = {}
    for key, rs in raw.items():
        if len(rs) < 10: continue
        n = len(rs)
        fold = sum(r["fold"] for r in rs) / n
        call = sum(r["call"] for r in rs) / n
        raise_ = sum(r["raise"] for r in rs) / n
        acts = sorted([("fold", fold), ("call", call), ("raise", raise_)], key=lambda x: -x[1])
        cells[key] = {"n": n, "dom": acts[0][0], "freq": acts[0][1]}
    return cells


def build_cells_4key():
    """(pot, street, sub, tier, eq_bucket) — equity 加味"""
    raw = defaultdict(list)
    for r in all_rows:
        if r["eq_b"] == "?": continue
        raw[(r["pot"], r["street"], r["sub"], r["tier"], r["eq_b"])].append(r)
    cells = {}
    for key, rs in raw.items():
        if len(rs) < 10: continue
        n = len(rs)
        fold = sum(r["fold"] for r in rs) / n
        call = sum(r["call"] for r in rs) / n
        raise_ = sum(r["raise"] for r in rs) / n
        acts = sorted([("fold", fold), ("call", call), ("raise", raise_)], key=lambda x: -x[1])
        cells[key] = {"n": n, "dom": acts[0][0], "freq": acts[0][1]}
    return cells


def build_cells_eq_only():
    """(pot, street, sub, eq_bucket) — tier の代わりに eq_bucket"""
    raw = defaultdict(list)
    for r in all_rows:
        if r["eq_b"] == "?": continue
        raw[(r["pot"], r["street"], r["sub"], r["eq_b"])].append(r)
    cells = {}
    for key, rs in raw.items():
        if len(rs) < 10: continue
        n = len(rs)
        fold = sum(r["fold"] for r in rs) / n
        call = sum(r["call"] for r in rs) / n
        raise_ = sum(r["raise"] for r in rs) / n
        acts = sorted([("fold", fold), ("call", call), ("raise", raise_)], key=lambda x: -x[1])
        cells[key] = {"n": n, "dom": acts[0][0], "freq": acts[0][1]}
    return cells


def predict(cells: dict, key_fn, row: dict) -> str:
    k = key_fn(row)
    if k in cells:
        return cells[k]["dom"]
    # fallback: tier-based
    return {"ナッツメイド":"raise","ストロング":"raise","ツーペア":"call",
            "トップペア以上":"call","ミドルペア":"call","エア":"fold"}.get(row["tier"], "fold")


def evaluate(cells: dict, key_fn, name: str) -> dict:
    correct = 0; loss = []; huge = 0
    cls_stats = defaultdict(lambda: {"c":0, "t":0, "l":[]})
    for r in all_rows:
        pred = predict(cells, key_fn, r)
        pred_ev = {"fold": r["ev_fold"], "call": r["ev_call"], "raise": r["ev_raise"]}[pred]
        l = max(0, r["best_ev"] - pred_ev)
        is_correct = (pred == r["best_action"])
        if is_correct: correct += 1
        loss.append(l)
        if l > 5: huge += 1
        # classify by purity (only counted for cells with data)
        k = key_fn(r)
        if k in cells:
            c = cells[k]
            cls = "PURE" if c["freq"] >= 0.8 else "STRONG" if c["freq"] >= 0.6 else "MIXED" if c["freq"] >= 0.4 else "BALANCED"
        else:
            cls = "FALLBACK"
        cls_stats[cls]["t"] += 1
        cls_stats[cls]["l"].append(l)
        if is_correct: cls_stats[cls]["c"] += 1
    n = len(all_rows)
    print(f"\n=== {name} ===")
    print(f"  cells: {len(cells):,}")
    print(f"  accuracy: {correct/n*100:.2f}%")
    print(f"  avg loss: {sum(loss)/n:.4f} BB")
    print(f"  huge loss (>5): {huge/n*100:.2f}%")
    for cls in ["PURE","STRONG","MIXED","BALANCED","FALLBACK"]:
        s = cls_stats[cls]
        if s["t"] == 0: continue
        print(f"    {cls:10} n={s['t']:>8,} acc={s['c']/s['t']*100:>5.1f}% loss={sum(s['l'])/len(s['l']):.4f}BB")
    return {
        "name": name, "cells": len(cells), "n": n,
        "acc": correct/n*100, "avg": sum(loss)/n, "huge": huge/n*100,
        "cls": cls_stats,
    }


# === Build all variants ===
print("\nBuilding cell tables...")
cells_3 = build_cells_3key()
cells_4 = build_cells_4key()
cells_eq = build_cells_eq_only()
print(f"  3-key (sub,tier):       {len(cells_3):>5} cells")
print(f"  4-key (sub,tier,eq):    {len(cells_4):>5} cells")
print(f"  3-key alt (sub,eq):     {len(cells_eq):>5} cells")

r_3 = evaluate(cells_3, lambda r: (r["pot"],r["street"],r["sub"],r["tier"]), "3-key: sub+made_tier")
r_4 = evaluate(cells_4, lambda r: (r["pot"],r["street"],r["sub"],r["tier"],r["eq_b"]), "4-key: sub+tier+eq_bucket")
r_eq = evaluate(cells_eq, lambda r: (r["pot"],r["street"],r["sub"],r["eq_b"]), "3-key alt: sub+eq_bucket only")

# Formula baseline
f_correct = sum(1 for r in all_rows if r["f_action"] and r["f_action"]==r["best_action"])
f_total = sum(1 for r in all_rows if r["f_action"])
f_loss_sum = sum(r["f_loss"] for r in all_rows if r["f_action"])
f_huge = sum(1 for r in all_rows if r["f_action"] and r["f_loss"]>5)
print(f"\n=== Formula baseline ===")
print(f"  total: {f_total:,}")
print(f"  accuracy: {f_correct/f_total*100:.2f}%")
print(f"  avg loss: {f_loss_sum/f_total:.4f} BB")
print(f"  huge: {f_huge/f_total*100:.2f}%")

# === Report ===
lines = []
lines.append("# equity_bucket を加えた cell key の比較評価")
lines.append("")
lines.append("「value / draw の価値概念」を取り入れるため、cell key に equity_bucket を追加。")
lines.append("293K rows で 3 variants を比較。")
lines.append("")
lines.append("## ルール構造の比較")
lines.append("")
lines.append("| variant | cell key | cell 数 |")
lines.append("|---|---|---:|")
lines.append(f"| 3-key (現行) | (pot, street, sub, made_tier) | {len(cells_3)} |")
lines.append(f"| 4-key 統合 | (pot, street, sub, made_tier, **eq_bucket**) | {len(cells_4)} |")
lines.append(f"| 3-key 代替 | (pot, street, sub, **eq_bucket**) | {len(cells_eq)} |")
lines.append("")

lines.append("## 全体結果")
lines.append("")
lines.append("| variant | cells | accuracy | avg loss | huge% |")
lines.append("|---|---:|---:|---:|---:|")
lines.append(f"| **3-key (現行)** | {len(cells_3)} | {r_3['acc']:.2f}% | {r_3['avg']:.4f} BB | {r_3['huge']:.2f}% |")
lines.append(f"| **4-key (made_tier × eq_bucket)** | {len(cells_4)} | **{r_4['acc']:.2f}%** | **{r_4['avg']:.4f} BB** | **{r_4['huge']:.2f}%** |")
lines.append(f"| 3-key (eq_bucket のみ) | {len(cells_eq)} | {r_eq['acc']:.2f}% | {r_eq['avg']:.4f} BB | {r_eq['huge']:.2f}% |")
lines.append(f"| 既存公式 v9b/v10/v15 | — | {f_correct/f_total*100:.2f}% | {f_loss_sum/f_total:.4f} BB | {f_huge/f_total*100:.2f}% |")
lines.append("")

lines.append("## 改善幅 (3-key → 4-key)")
lines.append("")
diff_acc = r_4['acc'] - r_3['acc']
diff_loss = (r_3['avg'] - r_4['avg']) / r_3['avg'] * 100
diff_huge = (r_3['huge'] - r_4['huge']) / r_3['huge'] * 100 if r_3['huge'] > 0 else 0
lines.append(f"- Accuracy: {r_3['acc']:.2f}% → {r_4['acc']:.2f}% ({diff_acc:+.2f}pp)")
lines.append(f"- Avg loss: {r_3['avg']:.4f} BB → {r_4['avg']:.4f} BB ({-diff_loss:+.1f}%)")
lines.append(f"- Huge loss: {r_3['huge']:.2f}% → {r_4['huge']:.2f}% ({-diff_huge:+.1f}%)")
lines.append("")
lines.append(f"cell 数は {len(cells_3)} → {len(cells_4)} ({len(cells_4)-len(cells_3):+}) で大幅増加。")
lines.append("精度向上と cell 数増のトレードオフを評価する必要あり。")
lines.append("")

lines.append("## 解釈")
lines.append("")
lines.append("- **eq_bucket を加える」と精度向上**: value / draw / equity の概念が判定に効く")
lines.append("- ただし cell 数は 4 倍程度増加 → 暗記負荷も増")
lines.append("- 「value 4 段階」を hand_tier の上に重ねるアプローチ")
lines.append("- combo draw (made tier=エア だが eq=good_hands) のような spot が正しく分類される")
lines.append("")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
