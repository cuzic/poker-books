#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""mtt_formula_audit.py — 既存 MTT defense data に Cash 公式を適用し境界 cell を特定

vol3_mtt_audit.py の cell-level 版。

入力:
  - dataset_unified.csv (~400k MTT rows)
  - 公式: v8a (flop) / v10 (turn) / v14 (river)

出力:
  - knowledges/gto_wizard_study/MTT_FORMULA_AUDIT.md (markdown サマリー)
  - knowledges/gto_wizard_study/mtt_boundary_cells.csv (高 huge_loss cell リスト)

「境界 cell」= huge_loss > 0.3 BB & n >= 50 の (pot_type, board_family, mv, dv) 組み合わせ。
これが Phase B fetch (#10) の対象、または公式拡張の候補。
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"
OUT_DIR = ROOT / "knowledges" / "gto_wizard_study"
OUT_MD = OUT_DIR / "MTT_FORMULA_AUDIT.md"
OUT_CSV = OUT_DIR / "mtt_boundary_cells.csv"

# ════════════════════════════ 公式 ════════════════════════════

AIR = {"no_made_hand", "ace_high", "king_high"}
WEAK_PAIR_LOW = {"low_pair", "underpair", "third_pair"}
DRY_BOARDS = {"dry_high", "low_dry"}
DYNAMIC_BOARDS = {"dynamic", "dynamic_2tone"}
WEAK_DRAW = {"twocards_bdfd", "onecard_bdfd", "gutshot"}
DYNAMIC_RIVER = {"dynamic", "dynamic_2tone", "monotone"}
DRY_RIVER = {"dry_high", "low_dry"}
ABSOLUTELY_STRONG = {"straight", "flush", "trips"}


def flop_def_v8a(r):
    mv, dv, bf = r["mv_cat"], r["dv_cat"], r["board_family"]
    if mv in AIR:
        if dv == "no_draw":
            return "FOLD"
        if dv in WEAK_DRAW and bf in DYNAMIC_BOARDS:
            return "FOLD"
    if mv in {"low_pair", "third_pair"} and dv == "no_draw" and bf in DRY_BOARDS | {"dynamic_2tone"}:
        return "FOLD"
    if mv == "overpair":
        return "RAISE"
    return "CALL"


def _is_short_stack(r):
    """source_path から short stack (≤50bb) か判定。"""
    p = str(r.get("source_path", "")).lower()
    if "mtt25" in p or "mtt50" in p:
        return True
    if "cash100" in p or "mtt100" in p or "mtt200" in p:
        return False
    depth_raw = r.get("depth", 100)
    try:
        depth = float(depth_raw) if pd.notna(depth_raw) else 100.0
    except (ValueError, TypeError):
        depth = 100.0
    return depth > 0 and depth <= 50


def flop_def_v9b(r):
    """Flop v9b — v8a の境界 cell 修正版 (stack-depth aware)。

    修正:
    1. AIR × WEAK_DRAW × DRY × deep stack → FOLD (Cash100/MTT100 で modal FOLD)
    2. {low_pair, third_pair} × dry × no_draw × short stack → RAISE (MTT CR)
    """
    mv, dv, bf = r["mv_cat"], r["dv_cat"], r["board_family"]
    is_short = _is_short_stack(r)

    if mv in AIR:
        if dv == "no_draw":
            return "FOLD"
        if dv in WEAK_DRAW and bf in DYNAMIC_BOARDS:
            return "FOLD"
        if dv in WEAK_DRAW and bf in DRY_BOARDS and not is_short:
            return "FOLD"

    if mv in {"low_pair", "third_pair"} and dv == "no_draw" and bf in DRY_BOARDS | {"dynamic_2tone"}:
        if is_short:
            return "RAISE"
        return "FOLD"

    if mv == "overpair":
        return "RAISE"
    return "CALL"


def turn_def_v10(r):
    mv, dv, bf, bs = r["mv_cat"], r["dv_cat"], r["board_family"], r["bet_size"]
    if bs == "overbet_185":
        weak_no_draw = dv in {"no_draw"} | WEAK_DRAW
        weak_mv = mv in AIR | WEAK_PAIR_LOW | {"second_pair"}
        if weak_mv and weak_no_draw:
            return "FOLD"
        if bf in DYNAMIC_BOARDS and mv == "top_pair" and dv == "no_draw":
            return "FOLD"
        if mv in AIR and dv in {"flush_draw", "nut_flush_draw", "oesd", "combo_draw"}:
            return "FOLD"
        return "CALL"
    if mv in AIR and bf == "monotone":
        return "FOLD"
    if mv in AIR and dv in WEAK_DRAW and bf != "low_dry":
        return "FOLD"
    if mv in AIR and dv == "no_draw":
        return "FOLD"
    if mv == "low_pair" and dv == "no_draw":
        return "FOLD"
    if mv == "third_pair" and dv == "no_draw" and bf != "low_dry":
        return "FOLD"
    weak_mv_no2p = mv in AIR | WEAK_PAIR_LOW
    if bf in DYNAMIC_BOARDS and weak_mv_no2p and dv in WEAK_DRAW:
        return "FOLD"
    if bf in DYNAMIC_BOARDS and dv == "oesd" and weak_mv_no2p:
        return "FOLD"
    return "CALL"


def river_def_v14(r):
    eb = r["equity_bucket"]
    bs = r["bet_size"]
    mv = r["mv_cat"]
    eqp = r.get("eq_percentile")
    bf = r["board_family"]
    is_dyn = bf in DYNAMIC_RIVER

    if mv == "quads":
        return "RAISE"
    if mv == "fullhouse" and bs != "overbet":
        return "RAISE"
    if mv == "fullhouse" and bs == "overbet":
        return "CALL"

    if bs == "allin":
        if eb == "best_hands" and pd.notna(eqp) and eqp > 0.85:
            return "CALL"
        if bf in DRY_RIVER and mv in {"set", "trips", "straight", "flush"}:
            return "CALL"
        if eb == "good_hands" and mv in {"straight", "flush", "trips"}:
            return "CALL"
        if bf == "monotone" and mv == "flush":
            return "CALL"
        if is_dyn and mv == "top_pair" and eb in {"weak_hands", "good_hands"}:
            return "CALL"
        return "FOLD"

    if mv in ABSOLUTELY_STRONG:
        return "CALL"
    if mv == "top_pair" and bf in DRY_RIVER and bs in {"overbet", "med_100p"}:
        return "CALL"

    if eb == "best_hands":
        if pd.notna(eqp) and eqp > 0.96:
            return "RAISE"
        return "CALL"
    if eb == "good_hands":
        return "CALL"
    if eb == "weak_hands":
        if bs == "overbet":
            if is_dyn and mv == "two_pair":
                return "CALL"
            return "FOLD"
        if bs == "med_100p":
            return "FOLD"
        return "CALL"
    return "FOLD"


def river_def_v15(r):
    """River v15 — v14 のバグ修正版。

    修正点:
    1. fullhouse は overbet でも常 RAISE (v14: overbet→CALL は誤、実測 raise 96%)
    2. broad is_dyn × TP × weak/good → CALL を削除
       (monotone × TP × allin × weak は FOLD 94% が GTO)
    3. allin spot で 2P を強メイドハンドに追加
       (dynamic × 2P × allin × good_hands → CALL、ev_call +31 BB)
    """
    eb = r["equity_bucket"]
    bs = r["bet_size"]
    mv = r["mv_cat"]
    eqp = r.get("eq_percentile")
    bf = r["board_family"]
    is_dry = bf in DRY_RIVER

    if mv in {"quads", "fullhouse"}:
        return "RAISE"

    if bs == "allin":
        if mv in {"two_pair", "set", "trips", "straight", "flush"}:
            if eb in {"best_hands", "good_hands"}:
                return "CALL"
            if is_dry and mv in {"set", "trips", "straight", "flush"}:
                return "CALL"
            return "FOLD"
        if eb == "best_hands" and pd.notna(eqp) and eqp > 0.85:
            return "CALL"
        if bf == "monotone" and mv == "flush":
            return "CALL"
        return "FOLD"

    if mv in ABSOLUTELY_STRONG:
        if eb == "trash_hands" and bs == "overbet":
            return "FOLD"
        return "CALL"

    if mv == "top_pair" and is_dry and bs in {"overbet", "med_100p"}:
        return "CALL"

    if eb == "best_hands":
        if pd.notna(eqp) and eqp > 0.96:
            return "RAISE"
        return "CALL"
    if eb == "good_hands":
        return "CALL"
    if eb == "weak_hands":
        if bs == "overbet":
            if bf in DYNAMIC_RIVER and mv == "two_pair":
                return "CALL"
            return "FOLD"
        if bs == "med_100p":
            return "FOLD"
        return "CALL"
    return "FOLD"


# ════════════════════════════ Bet size detection ═════════════

def turn_bet_size(s):
    if "_R4" in s or "_R5" in s or "_R6" in s:
        return "small_33"
    if "_R16" in s or "_R17" in s or "_R19" in s:
        return "overbet_185"
    return "other"


def river_bet_size(s):
    # 大きい順にチェック ("_R89.6" が "_R8" にマッチする bug 回避)
    if "_R89" in s or "_R35" in s:
        return "allin"
    if "_R16" in s:
        return "overbet"
    if "_R13" in s:
        return "med_100p"
    if "_R7" in s or "_R8" in s:
        return "med_75p"
    if "_R4" in s:
        return "small_30p"
    return "other"


def detect_pot_type(p):
    p = str(p).lower()
    if "3bp" in p:
        return "3BP"
    if "4bp" in p:
        return "4BP"
    if "mtt25" in p:
        return "MTT25"
    if "mtt50" in p:
        return "MTT50"
    if "mtt100" in p:
        return "MTT100"
    if "mtt200" in p:
        return "MTT200"
    if "cash50" in p:
        return "Cash50"
    if "cash100" in p:
        return "Cash100"
    return "other"


# ════════════════════════════ Evaluation ═══════════════════════

def best_ev(r):
    return max(e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e))


def ev_of(r, p):
    if p == "FOLD":
        return r["ev_fold"]
    if p == "CALL":
        return r["ev_call"]
    if p == "RAISE":
        return r["ev_raise"] if pd.notna(r["ev_raise"]) else r["ev_call"]
    return None


def ev_gap_row(r):
    evs = sorted([e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e)], reverse=True)
    return evs[0] - evs[1] if len(evs) >= 2 else None


def prep(df, street):
    bs_fn = turn_bet_size if street == "turn" else river_bet_size if street == "river" else None
    sub = df[
        (df["street"] == street) & (df["action_context"] == "defense")
        & df["ev_call"].notna() & df["ev_fold"].notna()
        & df["mv_cat"].notna() & (df["mv_cat"] != "") & (df["mv_cat"] != "unknown")
    ].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev, axis=1)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    if bs_fn is not None:
        sub["bet_size"] = sub["source_path"].apply(bs_fn)
    else:
        sub["bet_size"] = "—"
    sub["pot_type"] = sub["source_path"].apply(detect_pot_type)
    return sub[sub["ev_gap"].notna()]


def apply_formula(sub, formula):
    sub = sub.copy()
    sub["pred"] = sub.apply(formula, axis=1)
    sub["ev_p"] = sub.apply(lambda r: ev_of(r, r["pred"]), axis=1)
    sub["loss"] = sub["best_ev"] - sub["ev_p"]
    return sub


# ════════════════════════════ Cell-level analysis ═══════════

def cell_analysis(sub, street, formula_name):
    """pot_type × board_family × mv × dv (river は + bet_size) で集計。"""
    group_cols = ["pot_type", "board_family", "mv_cat", "dv_cat"]
    if street in ("turn", "river"):
        group_cols.append("bet_size")
    rows = []
    for keys, g in sub.groupby(group_cols):
        n = len(g)
        if n < 50:
            continue
        loss = g["loss"]
        huge_mask = g["ev_gap"] > 0.5
        n_huge = int(huge_mask.sum())
        if n_huge < 5:
            continue
        mean_loss = float(loss.mean())
        huge_loss = float(loss[huge_mask].mean()) if n_huge > 0 else 0.0
        acc = float((g["pred"] == g["modal"]).mean()) * 100
        # GTO 推奨は modal
        modal_dist = g["modal"].value_counts(normalize=True).to_dict()
        record = {
            "street": street,
            "formula": formula_name,
            "pot_type": keys[0],
            "board_family": keys[1],
            "mv_cat": keys[2],
            "dv_cat": keys[3],
            "bet_size": keys[4] if len(keys) > 4 else "—",
            "n": n,
            "n_huge": n_huge,
            "mean_loss": round(mean_loss, 3),
            "huge_loss": round(huge_loss, 3),
            "acc%": round(acc, 1),
            "modal_fold%": round(100 * modal_dist.get("FOLD", 0), 1),
            "modal_call%": round(100 * modal_dist.get("CALL", 0), 1),
            "modal_raise%": round(100 * modal_dist.get("RAISE", 0), 1),
        }
        rows.append(record)
    return pd.DataFrame(rows)


def summarize_pot_type(sub):
    """pot_type レベルでの全体サマリー。"""
    rows = []
    for pt, g in sub.groupby("pot_type"):
        n = len(g)
        if n < 200:
            continue
        huge_mask = g["ev_gap"] > 0.5
        rows.append({
            "pot_type": pt,
            "n": n,
            "n_huge": int(huge_mask.sum()),
            "acc%": round(float((g["pred"] == g["modal"]).mean()) * 100, 1),
            "mean_loss": round(float(g["loss"].mean()), 3),
            "huge_loss": round(float(g.loc[huge_mask, "loss"].mean()) if huge_mask.sum() > 0 else 0.0, 3),
        })
    return pd.DataFrame(rows).sort_values("pot_type")


# ════════════════════════════ Main ═════════════════════════════

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA, low_memory=False)

    summaries = []
    cell_dfs = []

    plan = [
        ("flop", flop_def_v8a, "v8a"),
        ("flop", flop_def_v9b, "v9b"),
        ("turn", turn_def_v10, "v10"),
        ("river", river_def_v14, "v14"),
        ("river", river_def_v15, "v15"),
    ]

    for street, formula, fname in plan:
        sub = prep(df, street)
        sub_eval = apply_formula(sub, formula)

        # pot_type サマリー
        s = summarize_pot_type(sub_eval)
        s.insert(0, "street", street)
        s.insert(1, "formula", fname)
        summaries.append(s)

        # cell-level
        c = cell_analysis(sub_eval, street, fname)
        cell_dfs.append(c)

    summary = pd.concat(summaries, ignore_index=True)
    cells = pd.concat(cell_dfs, ignore_index=True)

    # 境界 cell = huge_loss > 0.3 BB
    boundary = cells[cells["huge_loss"] > 0.3].sort_values(["pot_type", "street", "huge_loss"], ascending=[True, True, False])
    boundary.to_csv(OUT_CSV, index=False)

    # Markdown report
    md = ["# MTT 公式 v8a/v10/v14 既存データ適用結果\n"]
    md.append(f"生成: `scripts/three_class_model/mtt_formula_audit.py`  ")
    md.append(f"データ: `dataset_unified.csv`、行数={len(df):,}\n")

    md.append("## 1. Pot-type サマリー\n")
    md.append("Cash100 ベースラインと MTT 各 depth での精度比較。\n")
    md.append("| street | 公式 | pot_type | n | n_huge | acc% | mean_loss | huge_loss |")
    md.append("|--------|------|----------|---|--------|------|-----------|-----------|")
    for _, r in summary.iterrows():
        md.append(f"| {r['street']} | {r['formula']} | {r['pot_type']} | {int(r['n']):,} | "
                  f"{int(r['n_huge']):,} | {r['acc%']}% | {r['mean_loss']} BB | {r['huge_loss']} BB |")
    md.append("")

    md.append("## 2. Cash 100bb vs MTT depth 差分\n")
    md.append("公式 huge_loss の Cash100 比 (= MTT - Cash100)。差分が大きいほど MTT 特有の補正が必要。\n")
    pivot = summary.pivot_table(index=["street", "formula"], columns="pot_type", values="huge_loss", aggfunc="first")
    if "Cash100" in pivot.columns:
        md.append("| street | 公式 | Cash100 | MTT25 | MTT50 | MTT100 | MTT200 |")
        md.append("|--------|------|---------|-------|-------|--------|--------|")
        for (st, fm), r in pivot.iterrows():
            row = [st, fm]
            row.append(f"{r.get('Cash100', float('nan')):.3f}" if pd.notna(r.get("Cash100", float("nan"))) else "—")
            for k in ["MTT25", "MTT50", "MTT100", "MTT200"]:
                v = r.get(k, float("nan"))
                if pd.notna(v):
                    diff = v - r.get("Cash100", v)
                    row.append(f"{v:.3f} ({diff:+.3f})")
                else:
                    row.append("—")
            md.append("| " + " | ".join(row) + " |")
        md.append("")

    md.append(f"## 3. 境界 cell (huge_loss > 0.3 BB, n>=50)\n")
    md.append(f"全 {len(cells)} cell 中、境界 cell = {len(boundary)} 件。\n")
    md.append("`mtt_boundary_cells.csv` に全件出力。以下 huge_loss 降順 top 20。\n")
    md.append("| street | pot_type | bf | mv | dv | bet_size | n | n_huge | huge_loss | mean_loss | modal_fold% | modal_call% | modal_raise% |")
    md.append("|--------|----------|----|----|----|----------|---|--------|-----------|-----------|-------------|-------------|--------------|")
    for _, r in boundary.head(20).iterrows():
        md.append(
            f"| {r['street']} | {r['pot_type']} | {r['board_family']} | {r['mv_cat']} | {r['dv_cat']} | "
            f"{r['bet_size']} | {int(r['n']):,} | {int(r['n_huge']):,} | {r['huge_loss']} | {r['mean_loss']} | "
            f"{r['modal_fold%']}% | {r['modal_call%']}% | {r['modal_raise%']}% |"
        )
    md.append("")

    md.append("## 4. 境界 cell 内訳: pot_type × street 別件数\n")
    bd_count = boundary.groupby(["pot_type", "street"]).size().unstack(fill_value=0)
    md.append("| pot_type | flop | turn | river |")
    md.append("|----------|------|------|-------|")
    for pt in bd_count.index:
        md.append(f"| {pt} | {bd_count.get('flop', {}).get(pt, 0)} | {bd_count.get('turn', {}).get(pt, 0)} | {bd_count.get('river', {}).get(pt, 0)} |")
    md.append("")

    md.append("## 5. Phase B fetch 推奨対象\n")
    md.append("- データ既存 cell (n≥50) で huge_loss が高い場合: **公式拡張で対応** (新規 fetch 不要)\n")
    md.append("- データ不足 cell (n<50): **Phase B fetch 対象**\n")
    md.append("- Cash と MTT で構造的に乖離する cell (差分 > 0.2 BB): **MTT 専用ルール検討**\n")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print(f"=== mtt_formula_audit 完了 ===")
    print(f"summary: {len(summary)} pot_type-street 組")
    print(f"全 cell (n>=50): {len(cells)}")
    print(f"境界 cell (huge>0.3): {len(boundary)}")
    print(f"出力:")
    print(f"  - {OUT_MD}")
    print(f"  - {OUT_CSV}")

    # 標準出力サマリー
    print()
    print("=== 公式適用 huge_loss 一覧 ===")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    raise SystemExit(main())
