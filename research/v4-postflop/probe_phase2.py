#!/usr/bin/env python3
"""probe_phase2.py — 2026-06-06 用 probe (残 2 + Tier A 拡張)

実行内容:
  Section A: probe_priority.py の残 scenario
    - N_mtt200_river   (6 boards × 1 turn × 1 river)
    - N_mtt_3bp_flop   (6 boards × 1)
    - N_mtt200_turn    (残 2 boards: pair_KK2, mono_Js)
    → cache は findings/probe_priority/ を共有 (既存スキップ済)

  Section B: Tier A 拡張 probe (本格 fetch 前の中規模測定)
    - A_cash_4bp_flop   18 boards (全 6 family × 3)  acc=43.9% 公式破綻の詳細測定
    - A_cash_3bp_river  12 boards × 2 turn × 2 river (48 trajectories) 21.8 BB loss の原因解析
    → cache は findings/probe_phase2/

API call 数推定:
  Section A: 24 + 12 + 6                 = 42
  Section B: 18*2 + 48*4                 = 36 + 192 = 228
  合計                                    = 270 (daily quota 300/day 内)

出力:
  probe_phase2_report.md
  probe_phase2_rows.csv
  probe_phase2_stats.json
  findings/probe_phase2/*.json  (Tier A 生 API response)

probe_priority.py の helpers を import (公式 / walker / extractor / summarizer)。
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

# ════════════════════ 出力 path ════════════════════
PHASE2_OUT_DIR = ROOT / "findings" / "probe_phase2"
PHASE2_OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT     = ROOT / "probe_phase2_report.md"
ROWS_CSV   = ROOT / "probe_phase2_rows.csv"
SCEN_STATS = ROOT / "probe_phase2_stats.json"
LOG        = ROOT / "probe_phase2_log.jsonl"


# ════════════════════ Boards (拡張) ════════════════════
# 全 6 family × 3 boards = 18。Tier A 4BP_flop で全使用、3BP_river は subset 12 を使用。

EXTENDED_BOARDS_18 = [
    # dry_high (3): A-high / K-high / Q-high
    ("Ks7d2c", "dry_K72", "dry_high"),
    ("As9c4d", "dry_A94", "dry_high"),
    ("Qh7s3c", "dry_Q73", "dry_high"),
    # low_dry (3): no card > 9
    ("8s5d3h", "low_853", "low_dry"),
    ("9c6d4s", "low_964", "low_dry"),
    ("7d5s2c", "low_752", "low_dry"),
    # dynamic (3): connected, rainbow
    ("Th9c7s", "dyn_T97", "dynamic"),
    ("9c8d6s", "dyn_986", "dynamic"),
    ("8s7d5c", "dyn_875", "dynamic"),
    # dynamic_2tone (3): connected, 2 suit
    ("Ts9s7c", "d2t_T97", "dynamic_2tone"),
    ("8h7h5d", "d2t_875", "dynamic_2tone"),
    ("Jd9d6c", "d2t_J96", "dynamic_2tone"),
    # paired (3)
    ("KsKd2c", "pair_KK2", "paired"),
    ("9c9s2d", "pair_992", "paired"),
    ("Jh8s8d", "pair_J88", "paired"),  # mid-pair
    # monotone (3)
    ("Js7s3s", "mono_Js", "monotone"),
    ("Ts8s4s", "mono_Ts", "monotone"),
    ("Qh9h3h", "mono_Qh", "monotone"),
]

# 3BP river 用 subset 12 (各 family 2 枚)
EXTENDED_BOARDS_12 = [b for i, b in enumerate(EXTENDED_BOARDS_18) if i % 3 != 2]


# ════════════════════ Scenarios ════════════════════
# Section A: 残 scenario (cache 元: pp.OUT_DIR を共有)
REMAINING_SCENARIOS = [
    dict(id="N_mtt200_turn",
         desc="MTT200 SRP turn × BB def (残 2 boards 完了)",
         GT=pp.MTT_GT, depth=200, stacks=gto_api.uniform_stacks(200, 8),
         pf=pp.PF_8_SRP, ip_pos="BTN", oop_pos="BB", hero_pos="BB",
         target="turn_def_oop",
         _cache_dir=pp.OUT_DIR,         # findings/probe_priority/
         _boards=pp.CORE_BOARDS,        # 全 6, 内 4 boards は cache 済
         _n_turn=1, _n_river=0),
    dict(id="N_mtt200_river",
         desc="MTT200 SRP river × BB def (deep)",
         GT=pp.MTT_GT, depth=200, stacks=gto_api.uniform_stacks(200, 8),
         pf=pp.PF_8_SRP, ip_pos="BTN", oop_pos="BB", hero_pos="BB",
         target="river_def_oop",
         _cache_dir=pp.OUT_DIR,
         _boards=pp.CORE_BOARDS,
         _n_turn=1, _n_river=1),
    dict(id="N_mtt_3bp_flop",
         desc="MTT100 3BP flop × BB def",
         GT=pp.MTT_GT, depth=100, stacks=gto_api.uniform_stacks(100, 8),
         pf=pp.PF_8_3BP, ip_pos="BTN", oop_pos="BB", hero_pos="BB",
         target="flop_def_oop",
         _cache_dir=pp.OUT_DIR,
         _boards=pp.CORE_BOARDS,
         _n_turn=0, _n_river=0),
]

# Section B: Tier A 拡張 probe (new cache: PHASE2_OUT_DIR)
TIER_A_SCENARIOS = [
    dict(id="A_cash_4bp_flop",
         desc="Cash100 4BP flop × BB def (EXTENDED 18 boards / SPR~1 公式破綻調査)",
         GT=pp.CASH_GT, depth=100, stacks="",
         pf=pp.PF_6_4BP, ip_pos="BTN", oop_pos="BB", hero_pos="BB",
         target="flop_def_oop",
         _cache_dir=PHASE2_OUT_DIR,
         _boards=EXTENDED_BOARDS_18,
         _n_turn=0, _n_river=0),
    dict(id="A_cash_3bp_river",
         desc="Cash100 3BP river × BB def (EXTENDED 12 boards × 2 turn × 2 river / 21.8 BB loss 原因解析)",
         GT=pp.CASH_GT, depth=100, stacks="",
         pf=pp.PF_6_3BP, ip_pos="BTN", oop_pos="BB", hero_pos="BB",
         target="river_def_oop",
         _cache_dir=PHASE2_OUT_DIR,
         _boards=EXTENDED_BOARDS_12,
         _n_turn=2, _n_river=2),
]

ALL_SCENARIOS = REMAINING_SCENARIOS + TIER_A_SCENARIOS


# ════════════════════ Iters (per-scenario boards/turn/river) ════════════════════

def iters_for_scenario(sc):
    """sc._boards / _n_turn / _n_river を反映して spot を yield."""
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
        if not turns:
            continue

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
                spots_fail += 1
                continue
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


# ════════════════════ Report ════════════════════

def write_report(summaries, all_rows, elapsed_s):
    SCEN_STATS.write_text(json.dumps(summaries, indent=2, ensure_ascii=False))

    def sort_key(s):
        v = s.get("formula_huge_loss")
        return -(v if v is not None else -1)
    sorted_s = sorted(summaries, key=sort_key)

    with open(REPORT, "w") as f:
        f.write("# Probe Phase 2 Report (残 scenario + Tier A 拡張)\n\n")
        f.write(f"生成: probe_phase2.py / scenarios={len(summaries)} / "
                f"all_rows={len(all_rows)} / elapsed={elapsed_s:.0f}s\n\n")
        f.write("**目的**:\n")
        f.write("- Section A: probe_priority.py で quota 切れだった 残 2 scenario + N_mtt200_turn 残 2 boards\n")
        f.write("- Section B: Tier A 拡張 (4BP flop 18 boards / 3BP river 12 boards × 4 trajectories)\n\n")
        f.write("**注意**: probe_priority と同じく formula_huge_loss は audit と metric 違いのため絶対値比較不可。"
                "scenario 内 board variance / Tier A の board × family 分析が主目的。\n\n")

        f.write("## ランキング (formula_huge_loss 降順)\n\n")
        f.write("| Rank | ID | Target | GT/depth | n_combos | f_acc% | f_mean_loss | "
                "**f_huge_loss** | f_huge% | bimodal% | mean_gap | F/C/R% | ok/fail |\n")
        f.write("|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|\n")
        for rank, s in enumerate(sorted_s, 1):
            def fmt(v): return v if v is not None else "—"
            fhl = s["formula_huge_loss"]
            fhl_s = f"**{fhl}**" if fhl is not None else "—"
            f.write(f"| {rank} | **{s['id']}** | {s['target']} | "
                    f"{s['GT'].split('_')[0]}/{s['depth']} | {s['n']} | "
                    f"{fmt(s['formula_acc'])} | {fmt(s['formula_mean_loss'])} | {fhl_s} | "
                    f"{fmt(s['formula_huge_pct'])} | {s['bimodal_pct']}% | "
                    f"{s['mean_ev_gap']} | "
                    f"{s['pct_fold']}/{s['pct_call']}/{s['pct_raise']}% | "
                    f"{s['n_spots_ok']}/{s['n_spots_fail']} |\n")

        f.write("\n## 詳細 (formula_huge_loss 降順)\n\n")
        for s in sorted_s:
            f.write(f"### {s['id']}: {s['desc']}\n")
            f.write(f"- GT={s['GT']} depth={s['depth']} target={s['target']}\n")
            f.write(f"- spots OK={s['n_spots_ok']} FAIL={s['n_spots_fail']} n_combos={s['n']}\n")
            f.write(f"- ev_gap: mean={s['mean_ev_gap']}, p90={s['p90_ev_gap']}, max={s['max_ev_gap']}\n")
            f.write(f"- GTO huge_loss (公式非依存): {s['huge_loss']}\n")
            if s["formula_acc"] is not None:
                f.write(f"- **formula**: acc={s['formula_acc']}%, "
                        f"mean_loss={s['formula_mean_loss']}, "
                        f"huge_loss={s['formula_huge_loss']}, huge%={s['formula_huge_pct']}%\n")
            else:
                f.write("- **formula**: 適用外 (CR/donk/IP defender)\n")
            f.write(f"- modal split: FOLD={s['pct_fold']}% CALL={s['pct_call']}% RAISE={s['pct_raise']}%, "
                    f"bimodal_combo%={s['bimodal_pct']}%\n")
            if s["per_board_huge_loss"]:
                items = ", ".join(f"{b}={v} (n={s['per_board_n'][b]})"
                                  for b, v in sorted(s["per_board_huge_loss"].items()))
                f.write(f"- per-board huge_loss: {items}\n")
            # per-family stats (Tier A 拡張用)
            if s.get("per_family"):
                f.write(f"- per-family huge_loss: ")
                f.write(", ".join(f"{fam}={v}" for fam, v in sorted(s["per_family"].items())))
                f.write("\n")
            f.write("\n")


def summarize_with_family(rows):
    """probe_priority.summarize() + per-family huge_loss 追加."""
    base = pp.summarize(rows)
    # per-family
    families = {r["board_family"] for r in rows}
    per_family = {}
    for fam in families:
        fr = [r for r in rows if r["board_family"] == fam]
        f_huge = [r["ev_gap"] for r in fr if r["ev_gap"] is not None and r["ev_gap"] > 0.5]
        per_family[fam] = round(statistics.mean(f_huge), 3) if f_huge else 0
    base["per_family"] = per_family
    return base


def main():
    all_rows = []
    summaries = []
    started = time.time()
    print("=== probe_phase2 開始 ===\n", flush=True)

    for sc in ALL_SCENARIOS:
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
              f"f_huge_loss={summary['formula_huge_loss']} "
              f"bimodal={summary['bimodal_pct']}%\n", flush=True)
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
    print(f"stats:  {SCEN_STATS}")


if __name__ == "__main__":
    main()
