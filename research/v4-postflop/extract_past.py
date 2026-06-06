#!/usr/bin/env python3
"""extract_past.py — 過去 fetch 済 JSON (R1 / R3) を opp-side extractor で再処理

処理対象:
  R1 (62 spots): Cash 6m river × BTN IP defender vs BB allin shove
    → hand-level rows (target=river_def_ip_allin) + opp (BB) range structure
  R3 _open (24 spots): BB flop initial action (donk or check)
    → spot-level only (opp=BTN range structure)
  R3 _ip_post_check (24 spots): BTN cbet decision after BB check
    → spot-level only (opp=BB range structure)

出力:
  past_r1_rows.csv          — R1 の hand-level (R1 だけ row 単位、~43K rows)
  past_spots_summary.csv    — 110 spots × opp range structure (R1+R3 spot 単位)
  past_report.md            — 解析サマリー (BB allin range / BTN cbet range pattern)

R3 は initiator (X/R action) なので current extractor の F/C 軸に乗らず、hand-level は省略。
opp structure はどちらも提供できる。
"""
import csv
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

import probe_priority as pp  # noqa: E402

FIND = ROOT / "findings"
ROWS_CSV = ROOT / "past_r1_rows.csv"
SPOTS_CSV = ROOT / "past_spots_summary.csv"
REPORT = ROOT / "past_report.md"


# ════════════════════ Board family parser ════════════════════

def parse_r1_label(stem):
    """r1_dry_high_A_3c_2d → (board_label='dry_high_A_3c_2d', fam='dry_high')."""
    # remove "r1_" prefix
    rest = stem[3:]  # 'dry_high_A_3c_2d'
    # 最後の 2 underscores は turn/river card だが label は board prefix で十分
    parts = rest.rsplit("_", 2)
    label = parts[0] if len(parts) == 3 else rest
    fam = infer_family(label)
    return label, fam


def parse_r3_label(stem):
    """r3_dry_high_K72_open / r3_dry_high_K72_ip_post_check → (board_label, fam, kind)."""
    rest = stem[3:]  # 'dry_high_K72_open'
    # kind = "open" or "ip_post_check"
    if rest.endswith("_ip_post_check"):
        label = rest[: -len("_ip_post_check")]
        kind = "ip_post_check"
    elif rest.endswith("_open"):
        label = rest[: -len("_open")]
        kind = "open"
    else:
        label = rest; kind = "other"
    fam = infer_family(label)
    return label, fam, kind


def infer_family(label):
    """label substring から board family を推測."""
    if "dynamic_2tone" in label: return "dynamic_2tone"
    if "low_dry" in label: return "low_dry"
    if "dry_high" in label: return "dry_high"
    if "dynamic" in label: return "dynamic"
    if "paired" in label: return "paired"
    if "monotone" in label: return "monotone"
    return "other"


# ════════════════════ Spot-level opp structure ════════════════════

STRONG_CATS = {"straight_flush", "quads", "fullhouse", "flush", "straight",
               "set", "trips", "two_pair", "overpair"}
WEAK_CATS = {"no_made_hand", "ace_high", "king_high", "queen_high",
             "jack_high", "ten_high"}
STRONG_DRAW = {"oesd", "combo_draw", "nut_flush_draw", "flush_draw"}
NUT_CLASS = {"dry_high": "set", "low_dry": "set", "dynamic": "straight",
             "dynamic_2tone": "flush", "paired": "fullhouse", "monotone": "flush"}


def opp_structure(opp_dict, fam):
    """opp の hand_categories/draw_categories aggregated → polarization 等."""
    if not opp_dict: return None
    hc_list = opp_dict.get("hand_categories", []) or []
    dc_list = opp_dict.get("draw_categories", []) or []
    hc = {h.get("name", ""): h.get("total_combos", 0) for h in hc_list}
    dc = {d.get("name", ""): d.get("total_combos", 0) for d in dc_list}
    total = sum(hc.values()) or 1.0

    strong_pct = sum(hc.get(c, 0) for c in STRONG_CATS) / total
    weak_pct = sum(hc.get(c, 0) for c in WEAK_CATS) / total
    polarization = strong_pct + weak_pct
    draw_pct = sum(dc.get(c, 0) for c in STRONG_DRAW) / total

    nut_class = NUT_CLASS.get(fam, "set")
    nut_pct = hc.get(nut_class, 0) / total

    return dict(total_combos=round(total, 1),
                strong_pct=round(strong_pct, 3),
                weak_pct=round(weak_pct, 3),
                polarization=round(polarization, 3),
                draw_pct=round(draw_pct, 3),
                nut_class=nut_class,
                nut_pct=round(nut_pct, 3),
                hc_breakdown=hc,
                dc_breakdown=dc)


def opp_nut_eq_median(sols, opp_dict, fam):
    """opp の nut class combo の equity 中央値."""
    if not opp_dict: return None
    fam_nut = NUT_CLASS.get(fam, "set")
    hc_list = opp_dict.get("hand_categories", []) or []
    nut_idx = next((h.get("index", -1) for h in hc_list if h.get("name") == fam_nut), -1)
    if nut_idx < 0: return None
    hcr = sols.get("hand_categories_range") or []
    opp_eb = opp_dict.get("equity_buckets_range") or []
    opp_eq = opp_dict.get("hand_eqs") or []
    eqs = []
    for j in range(1326):
        if j >= len(hcr) or hcr[j] != nut_idx: continue
        if j >= len(opp_eb) or opp_eb[j] < 0: continue
        if j < len(opp_eq): eqs.append(opp_eq[j])
    return round(statistics.median(eqs), 3) if eqs else None


# ════════════════════ R1 hand-level extract ════════════════════

R1_SC = dict(
    id="R1_past", desc="R1 cached: Cash 6m river × BTN IP def vs BB allin",
    GT="Cash6mTest_6mNL100R2", depth=100,
    pf="F-F-F-R2-F-C", ip_pos="BTN", oop_pos="BB", hero_pos="BTN",
    target="river_def_ip_allin",
)


def process_r1():
    print("=== R1 処理開始 ===")
    r1_files = sorted(FIND.glob("r1_*.json"))
    print(f"  files: {len(r1_files)}")

    all_rows = []
    spot_summaries = []

    for f in r1_files:
        data = json.load(open(f))
        label, fam = parse_r1_label(f.stem)
        board_str = data.get("board", "")
        bet_codes = data.get("bet_size_codes", {})

        # hand-level rows via probe_priority extractor
        rows = pp.extract_hand_rows(data, R1_SC, board_str, fam, label, bet_codes)
        all_rows.extend(rows)

        # opp (BB) range structure — opp shoved allin, BB の shove range structure
        pi = data.get("players_info") or []
        opp_bb = next((p for p in pi if isinstance(p, dict)
                       and p.get("player", {}).get("position") == "BB"), None)
        opp_st = opp_structure(opp_bb, fam) or {}
        nut_eq_med = opp_nut_eq_median(data, opp_bb, fam)

        spot_summaries.append(dict(
            source="R1", spot_file=f.name,
            board_str=board_str, board_label=label, board_family=fam,
            hero_pos="BTN", opp_pos="BB", target="river_def_ip_allin",
            opp_total_combos=opp_st.get("total_combos"),
            opp_strong_pct=opp_st.get("strong_pct"),
            opp_weak_pct=opp_st.get("weak_pct"),
            opp_polarization=opp_st.get("polarization"),
            opp_draw_pct=opp_st.get("draw_pct"),
            opp_nut_class=opp_st.get("nut_class"),
            opp_nut_pct=opp_st.get("nut_pct"),
            opp_nut_eq_median=nut_eq_med,
            n_combos=len(rows),
        ))
    print(f"  hand-level rows: {len(all_rows)}, spot summaries: {len(spot_summaries)}")
    return all_rows, spot_summaries


# ════════════════════ R3 spot-level only ════════════════════

def process_r3():
    print("=== R3 処理開始 ===")
    r3_files = sorted(FIND.glob("r3_*.json"))
    print(f"  files: {len(r3_files)}")
    spot_summaries = []

    for f in r3_files:
        data = json.load(open(f))
        label, fam, kind = parse_r3_label(f.stem)
        board_str = data.get("board", "")

        # _open: hero = BB (donk node), opp = BTN
        # _ip_post_check: hero = BTN (cbet node), opp = BB
        if kind == "open":
            hero_pos, opp_pos = "BB", "BTN"
            target = "flop_init_oop"
        elif kind == "ip_post_check":
            hero_pos, opp_pos = "BTN", "BB"
            target = "flop_init_ip"
        else:
            hero_pos, opp_pos = "BB", "BTN"
            target = "unknown"

        pi = data.get("players_info") or []
        opp = next((p for p in pi if isinstance(p, dict)
                    and p.get("player", {}).get("position") == opp_pos), None)
        opp_st = opp_structure(opp, fam) or {}
        nut_eq_med = opp_nut_eq_median(data, opp, fam)

        # hero range structure も計算 (initiator の bet/check 配分)
        hero = next((p for p in pi if isinstance(p, dict)
                     and p.get("player", {}).get("position") == hero_pos), None)
        hero_st = opp_structure(hero, fam) or {}

        spot_summaries.append(dict(
            source=f"R3_{kind}", spot_file=f.name,
            board_str=board_str, board_label=label, board_family=fam,
            hero_pos=hero_pos, opp_pos=opp_pos, target=target,
            # opp (= partner of initiator) range structure
            opp_total_combos=opp_st.get("total_combos"),
            opp_strong_pct=opp_st.get("strong_pct"),
            opp_weak_pct=opp_st.get("weak_pct"),
            opp_polarization=opp_st.get("polarization"),
            opp_draw_pct=opp_st.get("draw_pct"),
            opp_nut_class=opp_st.get("nut_class"),
            opp_nut_pct=opp_st.get("nut_pct"),
            opp_nut_eq_median=nut_eq_med,
            # hero range structure (initiator self)
            hero_total_combos=hero_st.get("total_combos"),
            hero_strong_pct=hero_st.get("strong_pct"),
            hero_weak_pct=hero_st.get("weak_pct"),
            hero_polarization=hero_st.get("polarization"),
            n_combos=None,
        ))
    print(f"  spot summaries: {len(spot_summaries)}")
    return spot_summaries


# ════════════════════ Report ════════════════════

def write_report(r1_rows, r1_spots, r3_spots):
    """過去 JSON 解析サマリー."""
    with open(REPORT, "w") as f:
        f.write("# Past JSON Re-extraction Report\n\n")
        f.write(f"R1 hand-level rows: {len(r1_rows)}\n")
        f.write(f"R1 spot summaries: {len(r1_spots)}\n")
        f.write(f"R3 spot summaries: {len(r3_spots)}\n\n")

        # ─── R1 BB shove range structure (per family) ────
        f.write("## R1: BB river allin shove range structure (per board family)\n\n")
        f.write("BTN as IP defender 視点で、BB が river で allin shove する range の structure。"
                "polarization が低い board = BB の shove に bluff が薄い (call すべき場面少)。\n\n")
        f.write("| family | n_spots | opp_polarization | opp_strong_pct | opp_weak_pct | "
                "opp_nut_class | opp_nut_pct | opp_nut_eq_median |\n")
        f.write("|---|---:|---:|---:|---:|---|---:|---:|\n")
        families = sorted({s["board_family"] for s in r1_spots})
        for fam in families:
            fs = [s for s in r1_spots if s["board_family"] == fam]
            if not fs: continue
            def avg(key): vals = [s[key] for s in fs if s.get(key) is not None]; return round(statistics.mean(vals), 3) if vals else None
            f.write(f"| {fam} | {len(fs)} | {avg('opp_polarization')} | {avg('opp_strong_pct')} | "
                    f"{avg('opp_weak_pct')} | {fs[0]['opp_nut_class']} | {avg('opp_nut_pct')} | "
                    f"{avg('opp_nut_eq_median')} |\n")

        f.write("\n## R3: BB donk range vs BTN cbet range (initiator structure)\n\n")
        f.write("R3 _open は BB の flop initial 行動 (donk or check) を含む node、"
                "_ip_post_check は BTN が BB の check に対して cbet するか考える node。\n"
                "hero 側 (initiator) の range structure と、opp 側の range structure を比較。\n\n")

        for kind in ["open", "ip_post_check"]:
            ks = [s for s in r3_spots if s["source"].endswith(kind)]
            if not ks: continue
            f.write(f"### R3 _{kind} (n={len(ks)})\n\n")
            f.write("| family | n | hero_polarization | hero_strong | opp_polarization | "
                    "opp_strong | opp_weak |\n")
            f.write("|---|---:|---:|---:|---:|---:|---:|\n")
            for fam in sorted({s["board_family"] for s in ks}):
                fs = [s for s in ks if s["board_family"] == fam]
                def avg(key): vals = [s[key] for s in fs if s.get(key) is not None]; return round(statistics.mean(vals), 3) if vals else None
                f.write(f"| {fam} | {len(fs)} | {avg('hero_polarization')} | "
                        f"{avg('hero_strong_pct')} | {avg('opp_polarization')} | "
                        f"{avg('opp_strong_pct')} | {avg('opp_weak_pct')} |\n")
            f.write("\n")

        # ─── R1 per-board breakdown ────
        f.write("\n## R1: BB shove structure × per-board (top variance)\n\n")
        f.write("board ごとに BB の shove range structure。polarization 高 = polar shove (nuts or air)、低 = bluff 薄。\n\n")
        f.write("| board_label | family | opp_polarization | opp_strong | opp_weak | opp_nut_pct | opp_nut_eq_med |\n")
        f.write("|---|---|---:|---:|---:|---:|---:|\n")
        # sort by polarization range
        for s in sorted(r1_spots, key=lambda x: -(x.get("opp_polarization") or 0))[:15]:
            f.write(f"| {s['board_label']} | {s['board_family']} | "
                    f"{s.get('opp_polarization')} | {s.get('opp_strong_pct')} | "
                    f"{s.get('opp_weak_pct')} | {s.get('opp_nut_pct')} | "
                    f"{s.get('opp_nut_eq_median')} |\n")


def main():
    # R1
    r1_rows, r1_spots = process_r1()
    if r1_rows:
        with open(ROWS_CSV, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(r1_rows[0].keys()))
            w.writeheader()
            w.writerows(r1_rows)
        print(f"  saved: {ROWS_CSV} ({len(r1_rows)} rows)")

    # R3
    r3_spots = process_r3()

    # All spot summaries
    all_spots = r1_spots + r3_spots
    if all_spots:
        all_keys = set()
        for s in all_spots: all_keys.update(s.keys())
        with open(SPOTS_CSV, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=sorted(all_keys))
            w.writeheader()
            w.writerows(all_spots)
        print(f"  saved: {SPOTS_CSV} ({len(all_spots)} spots)")

    write_report(r1_rows, r1_spots, r3_spots)
    print(f"  report: {REPORT}")


if __name__ == "__main__":
    main()
