#!/usr/bin/env python3
"""probe_phase6.py — Phase 6: MTT 4BP postflop + opener × flop (最後の matrix gap 埋め)

Resume 対応: 各 spot は cache (findings/probe_phase6/{spot_key}.json) で skip 判定。

実行内容:
  Section A: MTT 4BP postflop 全街 (最大の pot type matrix 空白)
    A1. P6_A_mtt_4bp_flop      6 × 2 = 12 calls
    A2. P6_A_mtt_4bp_turn      6 × 3 = 18 calls
    A3. P6_A_mtt_4bp_river     6 × 4 = 24 calls
    → 仮説: Cash 4BP の特異構造 (mid 31%, acc 43%) が MTT でも同じか

  Section B: opener × flop 補完 (turn/river は取得済、flop だけ未取得)
    B1. P6_B_hj_open_flop      6 × 2 = 12 calls
    B2. P6_B_co_open_flop      6 × 2 = 12 calls
    → 仮説: phase5 で「opener 位置は turn では効かず、river で効く」と判明、
       flop でどうか (より wide な flop range で opener 差は最大化?)

合計 ~78 calls
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
import probe_phase3 as ph3   # pf_hj_srp / pf_co_srp  # noqa: E402

OUT_DIR = ROOT / "findings" / "probe_phase6"
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT     = ROOT / "probe_phase6_report.md"
ROWS_CSV   = ROOT / "probe_phase6_rows.csv"
SCEN_STATS = ROOT / "probe_phase6_stats.json"
LOG        = ROOT / "probe_phase6_log.jsonl"

CASH_GT = pp.CASH_GT
MTT_GT  = pp.MTT_GT


# ════════════════════ Scenarios (A → B 順) ════════════════════

SCENARIOS = [
    # ─── Section A: MTT 4BP postflop ───────────────────────
    dict(id="P6_A_mtt_4bp_flop",
         desc="MTT100 4BP × BB OOP flop def (4BP postflop matrix 完成 — flop)",
         GT=MTT_GT, depth=100, stacks=gto_api.uniform_stacks(100, 8),
         pf=gto_api.pf_btn_bb_4bp(8),
         ip_pos="BTN", oop_pos="BB", hero_pos="BB",
         target="flop_def_oop",
         _boards=pp.CORE_BOARDS, _n_turn=0, _n_river=0),

    dict(id="P6_A_mtt_4bp_turn",
         desc="MTT100 4BP × BB OOP turn def",
         GT=MTT_GT, depth=100, stacks=gto_api.uniform_stacks(100, 8),
         pf=gto_api.pf_btn_bb_4bp(8),
         ip_pos="BTN", oop_pos="BB", hero_pos="BB",
         target="turn_def_oop",
         _boards=pp.CORE_BOARDS, _n_turn=1, _n_river=0),

    dict(id="P6_A_mtt_4bp_river",
         desc="MTT100 4BP × BB OOP river def",
         GT=MTT_GT, depth=100, stacks=gto_api.uniform_stacks(100, 8),
         pf=gto_api.pf_btn_bb_4bp(8),
         ip_pos="BTN", oop_pos="BB", hero_pos="BB",
         target="river_def_oop",
         _boards=pp.CORE_BOARDS, _n_turn=1, _n_river=1),

    # ─── Section B: opener × flop 補完 ──────────────────────
    dict(id="P6_B_hj_open_flop",
         desc="Cash100 HJ open × BB call × BB OOP flop def (opener position flop)",
         GT=CASH_GT, depth=100, stacks="",
         pf=ph3.pf_hj_srp(),
         ip_pos="HJ", oop_pos="BB", hero_pos="BB",
         target="flop_def_oop",
         _boards=pp.CORE_BOARDS, _n_turn=0, _n_river=0),

    dict(id="P6_B_co_open_flop",
         desc="Cash100 CO open × BB call × BB OOP flop def (opener position flop)",
         GT=CASH_GT, depth=100, stacks="",
         pf=ph3.pf_co_srp(),
         ip_pos="CO", oop_pos="BB", hero_pos="BB",
         target="flop_def_oop",
         _boards=pp.CORE_BOARDS, _n_turn=0, _n_river=0),
]


# ════════════════════ Iters (phase5 と同じ) ════════════════════

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
        if target in {"turn_def_oop", "turn_def_ip_donk", "turn_def_ip_cr"}:
            for tc in turns:
                yield (bf_str, lbl, fam, tc, "")
            continue
        for tc in turns:
            used = board_cards + ([tc] if tc else [])
            rivers = pp.pick_unique_cards(used, pp.RIVER_POOL, n_river) if n_river > 0 else [""]
            for rc in rivers:
                yield (bf_str, lbl, fam, tc, rc)


# ════════════════════ Runner (resume 対応) ════════════════════

def run_scenario(sc):
    rows = []
    spots_ok = spots_fail = spots_skipped = 0

    for bf_str, lbl, fam, tc, rc in iters_for_scenario(sc):
        spot_key = f"{sc['id']}_{lbl}"
        if tc: spot_key += f"_{tc}"
        if rc: spot_key += f"_{rc}"
        out_path = OUT_DIR / f"{spot_key}.json"
        t0 = time.time()

        if out_path.exists() and out_path.stat().st_size > 0:
            data = json.loads(out_path.read_text())
            sols = data.get("sols")
            bet_codes = data.get("bet_codes", {})
            board_str = data.get("board_str", "")
            if not sols:
                spots_fail += 1; continue
            spots_skipped += 1
        else:
            try:
                sols, bet_codes, err = pp.walk_to_target(sc, bf_str, tc, rc)
            except RuntimeError as e:
                if "DAILY_QUOTA_EXCEEDED" in str(e):
                    print(f"  Daily quota at {spot_key}", flush=True)
                    return rows, dict(spots_ok=spots_ok, spots_fail=spots_fail,
                                       spots_skipped=spots_skipped, quota_out=True)
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
            spots_ok += 1

        spot_rows = pp.extract_hand_rows(sols, sc, board_str, fam, lbl, bet_codes)
        rows.extend(spot_rows)

    return rows, dict(spots_ok=spots_ok, spots_fail=spots_fail,
                       spots_skipped=spots_skipped, quota_out=False)


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
        return -v2 + 1000
    sorted_s = sorted(summaries, key=sort_key)

    with open(REPORT, "w") as f:
        f.write("# Probe Phase 6 Report (MTT 4BP postflop + opener × flop)\n\n")
        f.write(f"生成: probe_phase6.py / scenarios={len(summaries)} / "
                f"all_rows={len(all_rows)} / elapsed={elapsed_s:.0f}s\n\n")
        f.write("Section A: MTT 4BP postflop 全街 (matrix gap 最大)、"
                "Section B: opener × flop 補完\n\n")

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
            f.write(f"- target={s['target']}, spots OK={s['n_spots_ok']} "
                    f"FAIL={s['n_spots_fail']} skipped(cached)={s.get('n_spots_skipped', 0)}, "
                    f"n_combos={s['n']}\n")
            f.write(f"- ev_gap: mean={s['mean_ev_gap']}, p90={s['p90_ev_gap']}, max={s['max_ev_gap']}\n")
            if s["formula_acc"] is not None:
                f.write(f"- **formula**: acc={s['formula_acc']}%, "
                        f"huge_loss={s['formula_huge_loss']}, huge%={s['formula_huge_pct']}%\n")
            else:
                f.write("- **formula**: 適用外\n")
            f.write(f"- modal: FOLD={s['pct_fold']}% CALL={s['pct_call']}% RAISE={s['pct_raise']}%, "
                    f"bimodal_combo%={s['bimodal_pct']}%\n")
            if s.get("opp_polarization_mean") is not None:
                f.write(f"- **opp range**: polarization={s['opp_polarization_mean']} "
                        f"(strong={s['opp_strong_pct_mean']} + weak={s['opp_weak_pct_mean']}), "
                        f"nut_pct={s['opp_nut_pct_mean']}, "
                        f"nut_eq_median={s['opp_nut_eq_median_mean']}\n")
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
    print("=== probe_phase6 開始 ===\n", flush=True)

    for sc in SCENARIOS:
        print(f"--- {sc['id']}: {sc['desc']} ---", flush=True)
        rows, stats = run_scenario(sc)
        all_rows.extend(rows)
        summary = summarize_with_family(rows)
        summary.update({
            "id": sc["id"], "desc": sc["desc"], "GT": sc["GT"], "depth": sc["depth"],
            "target": sc["target"],
            "n_spots_ok": stats["spots_ok"],
            "n_spots_fail": stats["spots_fail"],
            "n_spots_skipped": stats.get("spots_skipped", 0),
        })
        summaries.append(summary)
        print(f"  → n_combos={summary['n']} acc={summary['formula_acc']} "
              f"f_huge_loss={summary['formula_huge_loss']} "
              f"(fetched={summary['n_spots_ok']}, cached={summary.get('n_spots_skipped',0)}, "
              f"fail={summary['n_spots_fail']})\n", flush=True)
        if stats.get("quota_out"):
            print("!! daily quota — 残 scenario はスキップ (re-run で resume 可能)\n", flush=True)
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
