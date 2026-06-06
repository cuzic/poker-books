#!/usr/bin/env python3
"""probe_phase3.py — Phase 3 probe (Tier C 拡張 + R1 を 3BP に拡張 + 位置軸)

実行内容:
  Section A: Tier C 拡張 — 公式 N/A 領域の完成
    - A_cash_cr_def_full   18 boards × 3 calls = 54     (BTN IP def vs BB CR)
    - A_cash_donk_def_full 18 boards × 2 calls = 36     (BTN IP def vs BB donk)
  Section B: R1 を 3BP に拡張
    - N_cash_3bp_river_allin 6 boards × 1 turn × 1 river × 5 calls = 30
      (BTN IP def vs BB river allin shove、3BP context)
      仮説: 3BP では BB shove range が更に value 集中 (bluff < 1%)
  Section C: 位置軸 (opener 別 BB defender)
    - N_cash_hj_open_river   6 boards × 1 turn × 1 river × 4 calls = 24
      (HJ open vs BB call、BB river defender)
    - N_cash_co_open_river   6 boards × 1 turn × 1 river × 4 calls = 24
      (CO open vs BB call)

合計 API calls ≈ 168 (daily quota 残内であれば fit)

出力:
  findings/probe_phase3/{id}_{board}_{tc}_{rc}.json
  probe_phase3_report.md / probe_phase3_rows.csv / probe_phase3_stats.json
"""
import csv
import json
import os
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

for line in (ROOT / ".env").read_text().splitlines() if (ROOT / ".env").exists() else []:
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

import gto_api  # noqa: E402

gto_api.init_token_files(ROOT)
gto_api.update_session()

import probe_priority as pp  # noqa: E402

OUT_DIR = ROOT / "findings" / "probe_phase3"
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT     = ROOT / "probe_phase3_report.md"
ROWS_CSV   = ROOT / "probe_phase3_rows.csv"
SCEN_STATS = ROOT / "probe_phase3_stats.json"
LOG        = ROOT / "probe_phase3_log.jsonl"


# ════════════════════ 位置別 preflop builder ════════════════════
# 6m position 順 (preflop): UTG HJ CO BTN SB BB

def pf_hj_srp(open_size="R2"):
    """HJ open → BB call (6m SRP). UTG-F, HJ-R2, CO-F, BTN-F, SB-F, BB-C."""
    return f"F-{open_size}-F-F-F-C"


def pf_co_srp(open_size="R2"):
    """CO open → BB call. F-F-R2-F-F-C."""
    return f"F-F-{open_size}-F-F-C"


def pf_btn_3bp_with_3bet(open_size="R2", three_bet_size="R7"):
    """BTN open → BB 3bet → BTN call. F-F-F-R2-F-R7-C."""
    return f"F-F-F-{open_size}-F-{three_bet_size}-C"


# ════════════════════ Scenarios ════════════════════

PF_6_SRP_BTN = pp.PF_6_SRP                         # F-F-F-R2-F-C  (BTN open)
PF_6_3BP     = pp.PF_6_3BP                         # F-F-F-R2-F-R7-C
CASH_GT      = pp.CASH_GT

SCENARIOS = [
    # ─── Section A: Tier C 拡張 (公式 N/A、現状調査必要) ────────
    dict(id="A_cash_cr_def_full",
         desc="Cash100 SRP × BTN IP def vs BB CR (EXTENDED 18 boards)",
         GT=CASH_GT, depth=100, stacks="",
         pf=PF_6_SRP_BTN, ip_pos="BTN", oop_pos="BB", hero_pos="BTN",
         target="flop_def_ip_cr",
         _cache_dir=OUT_DIR,
         _boards=None,  # 後で EXTENDED_BOARDS_18 を埋める
         _n_turn=0, _n_river=0),

    dict(id="A_cash_donk_def_full",
         desc="Cash100 SRP × BTN IP def vs BB donk (EXTENDED 18 boards)",
         GT=CASH_GT, depth=100, stacks="",
         pf=PF_6_SRP_BTN, ip_pos="BTN", oop_pos="BB", hero_pos="BTN",
         target="flop_def_ip_donk",
         _cache_dir=OUT_DIR,
         _boards=None,
         _n_turn=0, _n_river=0),

    # ─── Section B: R1 を 3BP に拡張 ────────────────────────
    dict(id="N_cash_3bp_river_allin",
         desc="Cash100 3BP × BTN IP def vs BB river allin shove (3BP context、R1=SRP の対比)",
         GT=CASH_GT, depth=100, stacks="",
         pf=PF_6_3BP, ip_pos="BTN", oop_pos="BB", hero_pos="BTN",
         target="river_def_ip_allin",
         _cache_dir=OUT_DIR,
         _boards=None,
         _n_turn=1, _n_river=1),

    # ─── Section C: 位置軸 (opener 別) ───────────────────────
    dict(id="N_cash_hj_open_river",
         desc="Cash100 HJ open × BB call SRP × river BB def (opener position diff)",
         GT=CASH_GT, depth=100, stacks="",
         pf=pf_hj_srp(), ip_pos="HJ", oop_pos="BB", hero_pos="BB",
         target="river_def_oop",
         _cache_dir=OUT_DIR,
         _boards=None,
         _n_turn=1, _n_river=1),

    dict(id="N_cash_co_open_river",
         desc="Cash100 CO open × BB call SRP × river BB def (opener position diff)",
         GT=CASH_GT, depth=100, stacks="",
         pf=pf_co_srp(), ip_pos="CO", oop_pos="BB", hero_pos="BB",
         target="river_def_oop",
         _cache_dir=OUT_DIR,
         _boards=None,
         _n_turn=1, _n_river=1),
]


# Boards 割り当て: Tier C 拡張は 18 boards (phase2 と同じ pool)、他は CORE_BOARDS 6
import probe_phase2 as ph2  # 18 boards pool 流用  # noqa: E402

for sc in SCENARIOS:
    if sc["id"].startswith("A_"):
        sc["_boards"] = ph2.EXTENDED_BOARDS_18
    else:
        sc["_boards"] = pp.CORE_BOARDS


# ════════════════════ Iters (phase2 と同じパターン) ════════════════════

def iters_for_scenario(sc):
    boards = sc.get("_boards", pp.CORE_BOARDS)
    n_turn = sc.get("_n_turn", 1)
    n_river = sc.get("_n_river", 1)
    target = sc["target"]

    for bf_str, lbl, fam in boards:
        board_cards = [bf_str[i:i+2] for i in range(0, 6, 2)]
        if target in {"flop_def_oop", "flop_def_ip_cr", "flop_def_ip_donk"}:
            yield (bf_str, lbl, fam, "", "")
            continue
        turns = pp.pick_unique_cards(board_cards, pp.TURN_POOL, n_turn) if n_turn > 0 else [""]
        if not turns: continue
        if target == "turn_def_oop":
            for tc in turns:
                yield (bf_str, lbl, fam, tc, "")
            continue
        for tc in turns:
            used = board_cards + ([tc] if tc else [])
            rivers = pp.pick_unique_cards(used, pp.RIVER_POOL, n_river) if n_river > 0 else [""]
            for rc in rivers:
                yield (bf_str, lbl, fam, tc, rc)


# ════════════════════ Runner ════════════════════

def run_scenario(sc):
    rows = []
    spots_ok = spots_fail = 0
    cache_dir: Path = sc["_cache_dir"]
    cache_dir.mkdir(parents=True, exist_ok=True)

    for bf_str, lbl, fam, tc, rc in iters_for_scenario(sc):
        spot_key = f"{sc['id']}_{lbl}"
        if tc: spot_key += f"_{tc}"
        if rc: spot_key += f"_{rc}"
        out_path = cache_dir / f"{spot_key}.json"
        t0 = time.time()

        if out_path.exists() and out_path.stat().st_size > 0:
            data = json.loads(out_path.read_text())
            sols = data.get("sols")
            bet_codes = data.get("bet_codes", {})
            board_str = data.get("board_str", "")
            if not sols:
                spots_fail += 1; continue
        else:
            try:
                sols, bet_codes, err = pp.walk_to_target(sc, bf_str, tc, rc)
            except RuntimeError as e:
                if "DAILY_QUOTA_EXCEEDED" in str(e):
                    print(f"  Daily quota at {spot_key}", flush=True)
                    return rows, dict(spots_ok=spots_ok, spots_fail=spots_fail, quota_out=True)
                raise
            if sols is None:
                spots_fail += 1
                gto_api.log_fetch(LOG, spot_key, "FAIL", int((time.time()-t0)*1000), err=err)
                print(f"  [{sc['id']}] {lbl} {tc} {rc} ... FAIL ({err})", flush=True)
                continue
            board_str = bf_str + tc + rc
            out_path.write_text(json.dumps({
                "scenario_id": sc["id"], "scenario_desc": sc["desc"],
                "board_str": board_str, "board_label": lbl, "board_family": fam,
                "bet_codes": bet_codes, "sols": sols,
            }, ensure_ascii=False, indent=2))
            gto_api.log_fetch(LOG, spot_key, "OK", int((time.time()-t0)*1000), bet_codes=bet_codes)
            print(f"  [{sc['id']}] {lbl} {tc} {rc} ... OK {bet_codes}", flush=True)

        spot_rows = pp.extract_hand_rows(sols, sc, board_str, fam, lbl, bet_codes)
        rows.extend(spot_rows)
        spots_ok += 1

    return rows, dict(spots_ok=spots_ok, spots_fail=spots_fail, quota_out=False)


def summarize_with_family(rows):
    base = pp.summarize(rows)
    families = {r["board_family"] for r in rows}
    per_family = {}
    for fam in families:
        fr = [r for r in rows if r["board_family"] == fam]
        f_huge = [r["ev_gap"] for r in fr if r["ev_gap"] is not None and r["ev_gap"] > 0.5]
        per_family[fam] = round(statistics.mean(f_huge), 3) if f_huge else 0
    base["per_family"] = per_family
    return base


def write_report(summaries, all_rows, elapsed_s):
    SCEN_STATS.write_text(json.dumps(summaries, indent=2, ensure_ascii=False))

    def sort_key(s):
        v = s.get("formula_huge_loss")
        if v is not None: return -v
        v2 = s.get("huge_loss") or 0
        return -v2 + 1000  # formula 適用外は後ろ
    sorted_s = sorted(summaries, key=sort_key)

    with open(REPORT, "w") as f:
        f.write("# Probe Phase 3 Report (Tier C 拡張 + 3BP allin + 位置軸)\n\n")
        f.write(f"生成: probe_phase3.py / scenarios={len(summaries)} / "
                f"all_rows={len(all_rows)} / elapsed={elapsed_s:.0f}s\n\n")
        f.write("Section A: Tier C 拡張 (CR/donk 防御 18 boards)、"
                "Section B: R1 を 3BP に拡張、Section C: opener 位置軸\n\n")

        f.write("## ランキング\n\n")
        f.write("| ID | Target | n_combos | f_acc% | f_huge_loss | GTO huge_loss | bimodal% | "
                "opp_pol | opp_strong | opp_weak | opp_nut_pct |\n")
        f.write("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        for s in sorted_s:
            def fmt(v): return v if v is not None else "—"
            f.write(f"| **{s['id']}** | {s['target']} | {s['n']} | "
                    f"{fmt(s['formula_acc'])} | {fmt(s['formula_huge_loss'])} | "
                    f"{s['huge_loss']} | {s['bimodal_pct']}% | "
                    f"{fmt(s.get('opp_polarization_mean'))} | {fmt(s.get('opp_strong_pct_mean'))} | "
                    f"{fmt(s.get('opp_weak_pct_mean'))} | {fmt(s.get('opp_nut_pct_mean'))} |\n")

        f.write("\n## 詳細\n\n")
        for s in sorted_s:
            f.write(f"### {s['id']}: {s['desc']}\n")
            f.write(f"- target={s['target']}, spots OK={s['n_spots_ok']} FAIL={s['n_spots_fail']}, "
                    f"n_combos={s['n']}\n")
            f.write(f"- ev_gap: mean={s['mean_ev_gap']}, p90={s['p90_ev_gap']}, max={s['max_ev_gap']}\n")
            if s["formula_acc"] is not None:
                f.write(f"- **formula**: acc={s['formula_acc']}%, "
                        f"huge_loss={s['formula_huge_loss']}, huge%={s['formula_huge_pct']}%\n")
            else:
                f.write("- **formula**: 適用外 (CR/donk/IP defender)\n")
            f.write(f"- modal: FOLD={s['pct_fold']}% CALL={s['pct_call']}% RAISE={s['pct_raise']}%, "
                    f"bimodal_combo%={s['bimodal_pct']}%\n")
            if s.get("opp_polarization_mean") is not None:
                f.write(f"- **opp range**: polarization={s['opp_polarization_mean']} "
                        f"(strong={s['opp_strong_pct_mean']} + weak={s['opp_weak_pct_mean']}), "
                        f"nut_pct={s['opp_nut_pct_mean']}, nut_eq_median={s['opp_nut_eq_median_mean']}, "
                        f"hero_dominates_nut%={s['hero_dominates_nut_pct']}\n")
            if s.get("per_family"):
                f.write(f"- per-family huge_loss: ")
                f.write(", ".join(f"{fam}={v}" for fam, v in sorted(s["per_family"].items())))
                f.write("\n")
            if s.get("per_board_opp_struct"):
                lines = []
                for b, st in sorted(s["per_board_opp_struct"].items()):
                    if st.get("polarization") is not None:
                        lines.append(f"{b}: pol={st['polarization']:.2f} "
                                     f"nut_class={st['nut_class']} nut_pct={st['nut_pct']:.2f}")
                if lines:
                    f.write(f"- per-board opp: {'; '.join(lines)}\n")
            f.write("\n")


def main():
    all_rows = []
    summaries = []
    started = time.time()
    print("=== probe_phase3 開始 ===\n", flush=True)

    for sc in SCENARIOS:
        print(f"--- {sc['id']}: {sc['desc']} ---", flush=True)
        rows, stats = run_scenario(sc)
        all_rows.extend(rows)
        summary = summarize_with_family(rows)
        summary.update({
            "id": sc["id"], "desc": sc["desc"], "GT": sc["GT"], "depth": sc["depth"],
            "target": sc["target"],
            "n_spots_ok": stats["spots_ok"], "n_spots_fail": stats["spots_fail"],
        })
        summaries.append(summary)
        print(f"  → n_combos={summary['n']} acc={summary['formula_acc']} "
              f"f_huge_loss={summary['formula_huge_loss']} bimodal={summary['bimodal_pct']}%\n",
              flush=True)
        if stats.get("quota_out"):
            print("!! daily quota — 残 scenario はスキップ\n", flush=True)
            break

    if all_rows:
        with open(ROWS_CSV, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
            w.writeheader()
            w.writerows(all_rows)

    write_report(summaries, all_rows, time.time() - started)
    print(f"=== 完了 ({time.time()-started:.0f}s) ===")
    print(f"report: {REPORT}")
    print(f"rows:   {ROWS_CSV} ({len(all_rows)} rows)")


if __name__ == "__main__":
    main()
