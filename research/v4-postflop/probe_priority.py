#!/usr/bin/env python3
"""probe_priority.py v2 — 未調査シナリオの公式適用 huge_loss 測定

v1 からの変更:
  (1) v9b/v10/v15 公式を re-implement & 全 combo に適用 → formula_loss 直接測定
  (2) CORE_BOARDS 6 (全 family 1 枚) で全 scenario 共通サンプル
  (3) turn/river card 動的選択 (board と非重複)
  (4) baseline 既知 fit と比較 (probe 自体の calibration)
  (5) CR / donk action context scenario 追加
  (6) per-board huge_loss / per-combo bimodality 出力
  (7) signed formula_loss = best_ev − ev_of_formula_action (>= 0)

出力:
  findings/probe_priority/{id}_{board}_{tc}_{rc}.json — 生 API response
  probe_priority_report.md  — 公式 huge_loss ランキング + 解釈
  probe_priority_rows.csv   — hand-level 詳細
  probe_priority_stats.json — scenario level stats (sortable)
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

OUT_DIR = ROOT / "findings" / "probe_priority"
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT     = ROOT / "probe_priority_report.md"
ROWS_CSV   = ROOT / "probe_priority_rows.csv"
SCEN_STATS = ROOT / "probe_priority_stats.json"
LOG        = ROOT / "probe_priority_log.jsonl"


# ════════════════════ 公式 (v9b/v10/v15 — memory 記載をコード化) ════════════════════

AIR_MV       = {"no_made_hand", "king_high", "queen_high", "jack_high", "ten_high", "ace_high"}
WEAK_DRAW_DV = {"twocards_bdfd", "onecard_bdfd", "gutshot"}
STRONG_DRAW  = {"oesd", "combo_draw", "flush_draw", "nut_flush_draw"}
DYNAMIC_BOARDS = {"dynamic", "dynamic_2tone"}
DRY_BOARDS     = {"dry_high", "low_dry"}
ABSOLUTELY_STRONG = {"straight", "flush", "trips"}


def flop_def_v9b(mv, dv, bf, is_short=False):
    """memory project_postflop_3rule_formula の v9b そのまま."""
    if mv in AIR_MV:
        if dv == "no_draw":
            return "FOLD"
        if dv in WEAK_DRAW_DV and bf in DYNAMIC_BOARDS:
            return "FOLD"
        if dv in WEAK_DRAW_DV and bf in DRY_BOARDS and not is_short:
            return "FOLD"
    if mv in {"low_pair", "third_pair"} and dv == "no_draw" and bf in DRY_BOARDS | {"dynamic_2tone"}:
        return "RAISE" if is_short else "FOLD"
    if mv == "overpair":
        return "RAISE"
    return "CALL"


def turn_def_v10(mv, dv, bf, bet_size):
    """memory の v10 簡易再現 (board × dv × mv 拡張)."""
    if mv in {"fullhouse", "quads", "set"}:
        return "RAISE"
    if mv in {"two_pair", "trips", "straight", "flush"}:
        return "RAISE" if bet_size != "overbet_185" else "CALL"
    if mv == "overpair":
        return "CALL"
    if mv == "top_pair":
        if bf in DRY_BOARDS:
            return "CALL"
        return "FOLD" if bet_size in {"overbet_185"} else "CALL"
    if mv in {"second_pair", "underpair", "third_pair"}:
        if dv in STRONG_DRAW:
            return "CALL"
        return "FOLD"
    if dv in STRONG_DRAW:
        return "CALL"
    if dv == "gutshot" and bf in DRY_BOARDS and bet_size != "overbet_185":
        return "CALL"
    return "FOLD"


def river_def_v15(mv, eb, bf, bet_size, eqp=None):
    """memory の v15 を bucket fallback 付きで再現."""
    is_dry = bf in DRY_BOARDS
    if mv in {"quads", "fullhouse"}:
        return "RAISE"
    if bet_size == "allin":
        if mv in {"two_pair", "set", "trips", "straight", "flush"}:
            if eb in {"best_hands", "good_hands"}:
                return "CALL"
            if is_dry and mv in {"set", "trips", "straight", "flush"}:
                return "CALL"
            return "FOLD"
        if eb == "best_hands" and eqp is not None and eqp > 0.85:
            return "CALL"
        if bf == "monotone" and mv == "flush":
            return "CALL"
        return "FOLD"
    if mv in ABSOLUTELY_STRONG:
        if eb == "trash_hands" and bet_size == "overbet":
            return "FOLD"
        return "CALL"
    if mv == "top_pair" and is_dry and bet_size in {"overbet", "med_100p"}:
        return "CALL"
    # bucket fallback
    if eb == "best_hands":
        return "CALL"
    if eb == "good_hands":
        return "FOLD" if bet_size in {"overbet", "allin"} else "CALL"
    if eb == "weak_hands":
        return "CALL" if bet_size == "small_30p" else "FOLD"
    return "FOLD"


def classify_bet_size(R_code, street):
    """R{chips} → 'small_30p' / 'med_75p' / 'med_100p' / 'overbet' / 'allin'.

    Pot/depth は scenario で異なるので閾値はざっくり (preliminary probe 用)。
    """
    try:
        chips = float(R_code[1:])
    except (ValueError, TypeError):
        return "med_100p"
    if chips >= 50: return "allin"
    if street == "river":
        # pot ~18 BB at river (SRP 100bb): 33%=R6, 75%=R13, 100%=R18, over=R30+
        if chips >= 25: return "overbet"
        if chips >= 15: return "med_100p"
        if chips >= 7:  return "med_75p"
        return "small_30p"
    if street == "turn":
        # pot ~8 BB at turn: 33%=R2.6, 67%=R5.3, over=R10+
        if chips >= 10: return "overbet_185"
        if chips >= 4:  return "med_75p"
        return "small_33"
    # flop, pot 5 BB: 33%=R1.5, 75%=R3.75, over=R5+
    if chips >= 5: return "overbet"
    if chips >= 3: return "med_75p"
    return "small_33"


def apply_formula(row, scenario):
    target = scenario["target"]
    is_short = scenario.get("depth", 100) <= 50
    mv, dv, eb, bf = row["mv_cat"], row["dv_cat"], row["equity_bucket"], row["board_family"]
    if target == "flop_def_oop":
        return flop_def_v9b(mv, dv, bf, is_short)
    if target == "turn_def_oop":
        return turn_def_v10(mv, dv, bf, row.get("ip_bet_size", "med_75p"))
    if target == "river_def_oop":
        return river_def_v15(mv, eb, bf, row.get("ip_bet_size", "med_100p"), row.get("eq_percentile"))
    return None  # CR / donk / ip_allin: 公式 N/A


# ════════════════════ Board / card pool ════════════════════

CORE_BOARDS = [
    ("Ks7d2c", "dry_K72", "dry_high"),
    ("8s5d3h", "low_853", "low_dry"),
    ("Th9c7s", "dyn_T97", "dynamic"),
    ("Ts9s7c", "d2t_T97", "dynamic_2tone"),
    ("KsKd2c", "pair_KK2", "paired"),
    ("Js7s3s", "mono_Js", "monotone"),
]
TURN_POOL  = ["3c", "Ah", "5d", "Kc", "2h", "8d", "Jc", "6h"]
RIVER_POOL = ["8h", "Kh", "Qd", "4s", "2c", "Tc", "5h", "Jd"]


def pick_unique_cards(used, pool, n):
    out = []
    for c in pool:
        if c not in used and c not in out:
            out.append(c)
            if len(out) >= n: return out
    return out


# ════════════════════ Walker ════════════════════

def walk_to_target(sc, board_flop, turn_card="", river_card=""):
    """scenario の target node の sols + bet_codes を返す。"""
    gt, depth, stacks = sc["GT"], sc["depth"], sc.get("stacks", "")
    pf, target = sc["pf"], sc["target"]
    ip_pos, oop_pos = sc["ip_pos"], sc["oop_pos"]
    # MTT は depth も `.125` 形式必須 (memory: API ガイド)
    if gt.startswith("MTT"):
        depth_param = f"{depth}.125"
    else:
        depth_param = str(depth)
    # gto_api.GT は module-level 変数なので、直接書き換える必要あり
    # (os.environ["GT"] = gt だけでは反映されない)
    os.environ["GT"] = gt
    gto_api.GT = gt
    gto_api.update_session()

    def call(board, fa, ta="", ra=""):
        return gto_api.api_get(board=board, flop_actions=fa, turn_actions=ta, river_actions=ra,
                                pf=pf, depth=depth_param, stacks=stacks)

    bet_codes = {}

    # flop_def_ip_donk: OOP donks first
    if target == "flop_def_ip_donk":
        sols0 = call(board_flop, "")
        if not sols0: return None, bet_codes, "no flop init"
        donk = gto_api.dominant_raise_code(sols0, oop_pos)
        if not donk: return None, bet_codes, "no OOP donk code (likely 0 freq)"
        bet_codes["donk"] = donk
        sols = call(board_flop, donk)
        return sols, bet_codes, None if sols else "no IP donk def"

    # all other targets walk through X-cbet
    sols = call(board_flop, "X")
    if not sols: return None, bet_codes, "no flop X"
    cbet = gto_api.dominant_raise_code(sols, ip_pos)
    if not cbet: return None, bet_codes, f"no IP({ip_pos}) cbet"
    bet_codes["cbet"] = cbet

    if target == "flop_def_oop":
        sols2 = call(board_flop, f"X-{cbet}")
        return sols2, bet_codes, None if sols2 else "no flop OOP def"

    if target == "flop_def_ip_cr":
        sols_cr = call(board_flop, f"X-{cbet}")
        if not sols_cr: return None, bet_codes, "no OOP CR node"
        cr = gto_api.dominant_raise_code(sols_cr, oop_pos)
        if not cr: return None, bet_codes, "no OOP CR code (0 freq)"
        bet_codes["cr"] = cr
        sols2 = call(board_flop, f"X-{cbet}-{cr}")
        return sols2, bet_codes, None if sols2 else "no IP CR def"

    turn_board = board_flop + turn_card
    flop_act = f"X-{cbet}-C"
    sols_t = call(turn_board, flop_act, "X")
    if not sols_t: return None, bet_codes, "no turn after X"
    barrel = gto_api.dominant_raise_code(sols_t, ip_pos)
    if not barrel: return None, bet_codes, "no IP barrel"
    bet_codes["barrel"] = barrel

    if target == "turn_def_oop":
        sols2 = call(turn_board, flop_act, f"X-{barrel}")
        return sols2, bet_codes, None if sols2 else "no turn OOP def"

    river_board = turn_board + river_card
    turn_act = f"X-{barrel}-C"
    sols_r = call(river_board, flop_act, turn_act, "X")
    if not sols_r: return None, bet_codes, "no river after X"
    river_bet = gto_api.dominant_raise_code(sols_r, ip_pos)
    if not river_bet: return None, bet_codes, "no IP river bet"
    bet_codes["river_bet"] = river_bet

    if target == "river_def_oop":
        sols2 = call(river_board, flop_act, turn_act, f"X-{river_bet}")
        return sols2, bet_codes, None if sols2 else "no river OOP def"

    return None, bet_codes, f"unknown target {target}"


# ════════════════════ Hand-level extractor ════════════════════

def extract_hand_rows(sols, sc, board_str, fam_str, lbl, bet_codes):
    actions = sols.get("action_solutions") or []
    if not actions: return []
    hero_pos = sc["hero_pos"]
    target   = sc["target"]

    strat = {(a.get("action") or {}).get("code", ""): a.get("strategy") or [] for a in actions}
    evs_d = {(a.get("action") or {}).get("code", ""): a.get("evs") or [] for a in actions}

    hand_map, draw_map = {}, {}
    for a in actions:
        for h in a.get("hand_categories") or []:
            hand_map[h["index"]] = h["name"]
        for d in a.get("draw_categories") or []:
            draw_map[d["index"]] = d["name"]
        if hand_map and draw_map: break

    hcr = sols.get("hand_categories_range") or []
    dcr = sols.get("draw_categories_range") or []

    pi = sols.get("players_info") or []
    hero = None
    for p in pi:
        if isinstance(p, dict) and p.get("player", {}).get("position") == hero_pos:
            hero = p; break
    if hero is None and pi: hero = pi[0]

    # opp 抽出: hero と異なる側
    opp_pos = sc["oop_pos"] if hero_pos == sc["ip_pos"] else sc["ip_pos"]
    opp = None
    for p in pi:
        if isinstance(p, dict) and p.get("player", {}).get("position") == opp_pos:
            opp = p; break
    if opp is None and len(pi) >= 2:
        opp = pi[1] if pi[0] is hero else pi[0]

    eqr = (hero or {}).get("equity_buckets_range") or []
    eqp = (hero or {}).get("eq_percentile") or []
    heq = (hero or {}).get("hand_eqs") or []
    eb_list = (hero or {}).get("equity_buckets") or []
    bucket_name = {b.get("index", -1): b.get("name", "") for b in eb_list if isinstance(b, dict)}
    if not bucket_name:
        bucket_name = {0: "best_hands", 1: "good_hands", 2: "weak_hands", 3: "trash_hands"}

    # opp side data
    opp_eb = (opp or {}).get("equity_buckets_range") or []
    opp_eq = (opp or {}).get("hand_eqs") or []
    opp_pct = (opp or {}).get("eq_percentile") or []
    opp_hc_list = (opp or {}).get("hand_categories") or []
    opp_dc_list = (opp or {}).get("draw_categories") or []
    opp_hc_combos = {h.get("name", ""): h.get("total_combos", 0) for h in opp_hc_list}
    opp_dc_combos = {d.get("name", ""): d.get("total_combos", 0) for d in opp_dc_list}
    opp_total = sum(opp_hc_combos.values()) or 1.0

    # opp range structure (spot-level scalar 集約)
    STRONG_CATS = {"straight_flush", "quads", "fullhouse", "flush", "straight",
                   "set", "trips", "two_pair", "overpair"}
    WEAK_CATS = {"no_made_hand", "ace_high", "king_high", "queen_high",
                 "jack_high", "ten_high"}
    STRONG_DRAW = {"oesd", "combo_draw", "nut_flush_draw", "flush_draw"}
    opp_strong_pct = sum(opp_hc_combos.get(c, 0) for c in STRONG_CATS) / opp_total
    opp_weak_pct = sum(opp_hc_combos.get(c, 0) for c in WEAK_CATS) / opp_total
    opp_polarization = opp_strong_pct + opp_weak_pct  # 1.0 = full polar (0 mid)
    opp_draw_pct = sum(opp_dc_combos.get(c, 0) for c in STRONG_DRAW) / opp_total  # missed draw 候補 (bluff 候補) の指標

    # board family-specific nut class
    NUT_CLASS = {"dry_high": "set", "low_dry": "set", "dynamic": "straight",
                 "dynamic_2tone": "flush", "paired": "fullhouse", "monotone": "flush"}
    nut_class = NUT_CLASS.get(fam_str, "set")
    opp_nut_pct = opp_hc_combos.get(nut_class, 0) / opp_total

    # opp nut tier の equity 中央値 (board nut class に属する opp combos の hand_eqs)
    nut_idx = next((h.get("index", -1) for h in opp_hc_list if h.get("name") == nut_class), -1)
    opp_nut_eqs = []
    if nut_idx >= 0:
        for j in range(1326):
            if j >= len(hcr) or hcr[j] != nut_idx: continue
            if j >= len(opp_eb) or opp_eb[j] < 0: continue  # opp range 外
            if j < len(opp_eq): opp_nut_eqs.append(opp_eq[j])
    opp_nut_eq_median = statistics.median(opp_nut_eqs) if opp_nut_eqs else None

    board_cards = {board_str[i:i+2] for i in range(0, len(board_str), 2)} if board_str else set()

    # bet_size 推定 (formula 適用用)
    if target == "river_def_oop":
        ip_bet_size = classify_bet_size(bet_codes.get("river_bet", ""), "river")
    elif target == "turn_def_oop":
        ip_bet_size = classify_bet_size(bet_codes.get("barrel", ""), "turn")
    elif target == "flop_def_oop":
        ip_bet_size = classify_bet_size(bet_codes.get("cbet", ""), "flop")
    elif target == "river_def_ip_allin":
        ip_bet_size = "allin"
    else:
        ip_bet_size = "med_75p"  # 公式 N/A

    rows = []
    f_arr = strat.get("F", [])
    c_arr = strat.get("C", [])
    f_ev_arr = evs_d.get("F", [])
    c_ev_arr = evs_d.get("C", [])
    r_codes = [code for code in strat.keys() if code.startswith("R") and len(code) > 1]

    for i in range(1326):
        ca, cb = gto_api.combo_to_cards(i)
        if ca in board_cards or cb in board_cards: continue
        f_freq = f_arr[i] if i < len(f_arr) else 0
        c_freq = c_arr[i] if i < len(c_arr) else 0
        r_freq = sum((strat[code][i] if i < len(strat[code]) else 0) for code in r_codes)
        total = f_freq + c_freq + r_freq
        if total < 0.001: continue

        ev_f = f_ev_arr[i] if i < len(f_ev_arr) else None
        ev_c = c_ev_arr[i] if i < len(c_ev_arr) else None
        ev_r = None
        for code in r_codes:
            arr = evs_d.get(code, [])
            if i < len(arr) and arr[i] is not None:
                if ev_r is None or arr[i] > ev_r:
                    ev_r = arr[i]

        candidates = []
        if ev_f is not None: candidates.append(("FOLD", ev_f))
        if ev_c is not None: candidates.append(("CALL", ev_c))
        if ev_r is not None: candidates.append(("RAISE", ev_r))
        if not candidates: continue

        best_action, best_ev = max(candidates, key=lambda x: x[1])
        worst_ev = min(c[1] for c in candidates)
        ev_gap = best_ev - worst_ev

        mv = hand_map.get(hcr[i], "unknown") if i < len(hcr) else "unknown"
        dv = draw_map.get(dcr[i], "unknown") if i < len(dcr) else "unknown"
        eb_idx = int(eqr[i]) if i < len(eqr) and eqr[i] >= 0 else -1
        bucket = bucket_name.get(eb_idx, "")
        eqp_v = float(eqp[i]) if i < len(eqp) and eqp[i] >= 0 else None
        heq_v = float(heq[i]) if i < len(heq) else None

        freqs = {"FOLD": f_freq, "CALL": c_freq, "RAISE": r_freq}
        modal = max(freqs, key=lambda k: freqs[k])
        sorted_f = sorted(freqs.values(), reverse=True)
        per_combo_bimodal = (sorted_f[1] / total) if total > 0 else 0

        # opp side per-combo: opp の bucket / percentile / equity (この combo を opp が持つ場合)
        opp_eb_i = int(opp_eb[i]) if i < len(opp_eb) and opp_eb[i] >= 0 else None
        opp_bucket = bucket_name.get(opp_eb_i, "") if opp_eb_i is not None else ""
        opp_pct_i = float(opp_pct[i]) if i < len(opp_pct) and opp_pct[i] >= 0 else None
        opp_eq_i = float(opp_eq[i]) if i < len(opp_eq) else None
        # hero vs opp nut tier: heq_v - opp_nut_eq_median > 0 → hero dominates opp の nut 中央値
        hand_eq_vs_opp_nut = (heq_v - opp_nut_eq_median
                              if heq_v is not None and opp_nut_eq_median is not None else None)

        row = {
            "scenario_id": sc["id"], "board_label": lbl, "board_family": fam_str,
            "board_str": board_str, "card_a": ca, "card_b": cb,
            "mv_cat": mv, "dv_cat": dv, "equity_bucket": bucket,
            "eq_percentile": eqp_v, "hand_eq": heq_v,
            "fold_freq": round(f_freq, 4), "call_freq": round(c_freq, 4),
            "raise_freq": round(r_freq, 4),
            "ev_fold": ev_f, "ev_call": ev_c, "ev_raise": ev_r,
            "best_action": best_action, "best_ev": round(best_ev, 4),
            "ev_gap": round(ev_gap, 4),
            "gto_modal": modal,
            "per_combo_bimodal": round(per_combo_bimodal, 3),
            "ip_bet_size": ip_bet_size,
            # OPP-SIDE per-combo
            "opp_bucket": opp_bucket,
            "opp_eq_percentile": round(opp_pct_i, 3) if opp_pct_i is not None else None,
            "opp_eq": round(opp_eq_i, 3) if opp_eq_i is not None else None,
            "hand_eq_vs_opp_nut": round(hand_eq_vs_opp_nut, 3) if hand_eq_vs_opp_nut is not None else None,
            # OPP-SIDE spot-level (全行共通)
            "opp_total_combos": round(opp_total, 1),
            "opp_strong_pct": round(opp_strong_pct, 3),
            "opp_weak_pct": round(opp_weak_pct, 3),
            "opp_polarization": round(opp_polarization, 3),
            "opp_nut_class": nut_class,
            "opp_nut_pct": round(opp_nut_pct, 3),
            "opp_nut_eq_median": round(opp_nut_eq_median, 3) if opp_nut_eq_median is not None else None,
            "opp_draw_pct": round(opp_draw_pct, 3),
        }
        formula = apply_formula(row, sc)
        row["formula_action"] = formula
        if formula is not None:
            ev_of_formula = {"FOLD": ev_f, "CALL": ev_c, "RAISE": ev_r}.get(formula)
            if ev_of_formula is not None:
                row["formula_loss"] = round(best_ev - ev_of_formula, 4)
            else:
                row["formula_loss"] = round(ev_gap, 4)  # 公式が tree 外 action → 最大 loss 想定
            row["formula_correct"] = (formula == best_action)
        else:
            row["formula_loss"] = None
            row["formula_correct"] = None
        rows.append(row)
    return rows


# ════════════════════ Scenarios ════════════════════

PF_6_SRP = gto_api.pf_btn_srp(6)
PF_8_SRP = gto_api.pf_btn_srp(8)
PF_6_3BP = gto_api.pf_btn_bb_3bp(6)
PF_8_3BP = gto_api.pf_btn_bb_3bp(8)
PF_6_4BP = gto_api.pf_btn_bb_4bp(6)
CASH_GT = "Cash6mTest_6mNL100R2"
MTT_GT  = "MTTGeneral_8m"
N_TURN_PER_BOARD  = 1
N_RIVER_PER_TURN  = 1

SCENARIOS = [
    # ─── Cash scenarios (cache 済が多い、quota 食わない) を先に ──
    dict(id="B_flop", desc="[BASELINE] Cash100 SRP flop × BB def (v9b in-domain)",
         GT=CASH_GT, depth=100, stacks="", pf=PF_6_SRP,
         ip_pos="BTN", oop_pos="BB", hero_pos="BB", target="flop_def_oop",
         baseline_huge_loss=0.061),
    dict(id="B_turn", desc="[BASELINE] Cash100 SRP turn × BB def (v10 in-domain)",
         GT=CASH_GT, depth=100, stacks="", pf=PF_6_SRP,
         ip_pos="BTN", oop_pos="BB", hero_pos="BB", target="turn_def_oop",
         baseline_huge_loss=0.048),
    dict(id="B_river", desc="[BASELINE] Cash100 SRP river × BB def (v15 in-domain)",
         GT=CASH_GT, depth=100, stacks="", pf=PF_6_SRP,
         ip_pos="BTN", oop_pos="BB", hero_pos="BB", target="river_def_oop",
         baseline_huge_loss=0.212),
    dict(id="N_cash_3bp_flop", desc="Cash100 3BP flop × BB def (3bettor OOP)",
         GT=CASH_GT, depth=100, stacks="", pf=PF_6_3BP,
         ip_pos="BTN", oop_pos="BB", hero_pos="BB", target="flop_def_oop"),
    dict(id="N_cash_3bp_river", desc="Cash100 3BP river × BB def",
         GT=CASH_GT, depth=100, stacks="", pf=PF_6_3BP,
         ip_pos="BTN", oop_pos="BB", hero_pos="BB", target="river_def_oop"),
    dict(id="N_cash_4bp_flop", desc="Cash100 4BP flop × BB def (SPR ~1)",
         GT=CASH_GT, depth=100, stacks="", pf=PF_6_4BP,
         ip_pos="BTN", oop_pos="BB", hero_pos="BB", target="flop_def_oop"),
    dict(id="N_cash_cr_def", desc="Cash100 SRP flop × BTN def (vs BB CR)",
         GT=CASH_GT, depth=100, stacks="", pf=PF_6_SRP,
         ip_pos="BTN", oop_pos="BB", hero_pos="BTN", target="flop_def_ip_cr"),
    dict(id="N_cash_donk_def", desc="Cash100 SRP flop × BTN def (vs BB donk)",
         GT=CASH_GT, depth=100, stacks="", pf=PF_6_SRP,
         ip_pos="BTN", oop_pos="BB", hero_pos="BTN", target="flop_def_ip_donk"),

    # ─── MTT scenarios (depth diff / pot_type diff) — quota 消費 ───
    dict(id="N_mtt100_river", desc="MTT100 SRP river × BB def (depth diff vs MTT50 fit)",
         GT=MTT_GT, depth=100, stacks=gto_api.uniform_stacks(100, 8), pf=PF_8_SRP,
         ip_pos="BTN", oop_pos="BB", hero_pos="BB", target="river_def_oop"),
    dict(id="N_mtt25_river", desc="MTT25 SRP river × BB def (short stack)",
         GT=MTT_GT, depth=25, stacks=gto_api.uniform_stacks(25, 8), pf=PF_8_SRP,
         ip_pos="BTN", oop_pos="BB", hero_pos="BB", target="river_def_oop"),
    dict(id="N_mtt200_turn", desc="MTT200 SRP turn × BB def (deep)",
         GT=MTT_GT, depth=200, stacks=gto_api.uniform_stacks(200, 8), pf=PF_8_SRP,
         ip_pos="BTN", oop_pos="BB", hero_pos="BB", target="turn_def_oop"),
    dict(id="N_mtt200_river", desc="MTT200 SRP river × BB def (deep)",
         GT=MTT_GT, depth=200, stacks=gto_api.uniform_stacks(200, 8), pf=PF_8_SRP,
         ip_pos="BTN", oop_pos="BB", hero_pos="BB", target="river_def_oop"),
    dict(id="N_mtt_3bp_flop", desc="MTT100 3BP flop × BB def",
         GT=MTT_GT, depth=100, stacks=gto_api.uniform_stacks(100, 8), pf=PF_8_3BP,
         ip_pos="BTN", oop_pos="BB", hero_pos="BB", target="flop_def_oop"),
]


# ════════════════════ Runner ════════════════════

def iters_for_scenario(sc):
    """scenario × 全 board × turn/river サンプルを yield."""
    for bf_str, lbl, fam in CORE_BOARDS:
        board_cards = [bf_str[i:i+2] for i in range(0, 6, 2)]
        target = sc["target"]
        if target in {"flop_def_oop", "flop_def_ip_cr", "flop_def_ip_donk"}:
            yield (bf_str, lbl, fam, "", "")
            continue
        turns = pick_unique_cards(board_cards, TURN_POOL, N_TURN_PER_BOARD)
        if not turns:
            continue
        if target == "turn_def_oop":
            for tc in turns:
                yield (bf_str, lbl, fam, tc, "")
            continue
        for tc in turns:
            rivers = pick_unique_cards(board_cards + [tc], RIVER_POOL, N_RIVER_PER_TURN)
            for rc in rivers:
                yield (bf_str, lbl, fam, tc, rc)


def run_scenario(sc):
    rows = []
    spots_ok = spots_fail = 0
    quota_out = False

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
                spots_fail += 1
                continue
        else:
            try:
                sols, bet_codes, err = walk_to_target(sc, bf_str, tc, rc)
            except RuntimeError as e:
                if "DAILY_QUOTA_EXCEEDED" in str(e):
                    print(f"  Daily quota at {spot_key}", flush=True)
                    quota_out = True
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

        spot_rows = extract_hand_rows(sols, sc, board_str, fam, lbl, bet_codes)
        rows.extend(spot_rows)
        spots_ok += 1

    return rows, dict(spots_ok=spots_ok, spots_fail=spots_fail, quota_out=quota_out)


def summarize(rows):
    if not rows:
        return dict(n=0, mean_ev_gap=0, max_ev_gap=0, p90_ev_gap=0,
                    huge_loss=0, formula_acc=None, formula_mean_loss=None,
                    formula_huge_loss=None, formula_huge_pct=None,
                    bimodal_pct=0, pct_fold=0, pct_call=0, pct_raise=0,
                    per_board_huge_loss={}, per_board_n={})

    gaps = [r["ev_gap"] for r in rows if r["ev_gap"] is not None]
    huge_gaps = [g for g in gaps if g > 0.5]
    huge_loss = statistics.mean(huge_gaps) if huge_gaps else 0

    formula_rows = [r for r in rows if r["formula_loss"] is not None]
    if formula_rows:
        correct = sum(1 for r in formula_rows if r["formula_correct"])
        formula_acc = correct / len(formula_rows) * 100
        losses = [r["formula_loss"] for r in formula_rows]
        formula_mean_loss = statistics.mean(losses)
        huge_losses = [l for l in losses if l > 0.5]
        formula_huge_loss = statistics.mean(huge_losses) if huge_losses else 0
        formula_huge_pct = len(huge_losses) / len(formula_rows) * 100
    else:
        formula_acc = formula_mean_loss = formula_huge_loss = formula_huge_pct = None

    n = len(rows)
    n_fold = sum(1 for r in rows if r["gto_modal"] == "FOLD")
    n_call = sum(1 for r in rows if r["gto_modal"] == "CALL")
    n_raise = sum(1 for r in rows if r["gto_modal"] == "RAISE")
    bimodal_n = sum(1 for r in rows if r["per_combo_bimodal"] > 0.2)

    per_board_huge_loss = {}
    per_board_n = {}
    per_board_opp_struct = {}  # opp range structure per board
    for b in {r["board_label"] for r in rows}:
        br = [r for r in rows if r["board_label"] == b]
        per_board_n[b] = len(br)
        b_huge = [r["ev_gap"] for r in br if r["ev_gap"] is not None and r["ev_gap"] > 0.5]
        per_board_huge_loss[b] = round(statistics.mean(b_huge), 3) if b_huge else 0
        # per-board opp range structure (spot 単位なので 1 行目の値で代表)
        first = br[0] if br else {}
        per_board_opp_struct[b] = {
            "polarization": first.get("opp_polarization"),
            "nut_pct": first.get("opp_nut_pct"),
            "nut_class": first.get("opp_nut_class"),
            "strong_pct": first.get("opp_strong_pct"),
            "weak_pct": first.get("opp_weak_pct"),
            "nut_eq_median": first.get("opp_nut_eq_median"),
        }

    # scenario-level opp range structure (平均)
    pol_vals = [r["opp_polarization"] for r in rows if r.get("opp_polarization") is not None]
    nut_vals = [r["opp_nut_pct"] for r in rows if r.get("opp_nut_pct") is not None]
    strong_vals = [r["opp_strong_pct"] for r in rows if r.get("opp_strong_pct") is not None]
    weak_vals = [r["opp_weak_pct"] for r in rows if r.get("opp_weak_pct") is not None]
    nut_eq_vals = [r["opp_nut_eq_median"] for r in rows if r.get("opp_nut_eq_median") is not None]
    dom_vals = [r["hand_eq_vs_opp_nut"] for r in rows if r.get("hand_eq_vs_opp_nut") is not None]

    return dict(
        n=n,
        mean_ev_gap=round(statistics.mean(gaps), 3) if gaps else 0,
        max_ev_gap=round(max(gaps), 3) if gaps else 0,
        p90_ev_gap=round(sorted(gaps)[int(len(gaps)*0.9)], 3) if len(gaps) >= 10 else 0,
        huge_loss=round(huge_loss, 3),
        formula_acc=round(formula_acc, 1) if formula_acc is not None else None,
        formula_mean_loss=round(formula_mean_loss, 3) if formula_mean_loss is not None else None,
        formula_huge_loss=round(formula_huge_loss, 3) if formula_huge_loss is not None else None,
        formula_huge_pct=round(formula_huge_pct, 1) if formula_huge_pct is not None else None,
        bimodal_pct=round(bimodal_n / n * 100, 1) if n else 0,
        pct_fold=round(n_fold / n * 100, 1) if n else 0,
        pct_call=round(n_call / n * 100, 1) if n else 0,
        pct_raise=round(n_raise / n * 100, 1) if n else 0,
        per_board_huge_loss=per_board_huge_loss,
        per_board_n=per_board_n,
        per_board_opp_struct=per_board_opp_struct,
        # opp 集約 (scenario level)
        opp_polarization_mean=round(statistics.mean(pol_vals), 3) if pol_vals else None,
        opp_nut_pct_mean=round(statistics.mean(nut_vals), 3) if nut_vals else None,
        opp_strong_pct_mean=round(statistics.mean(strong_vals), 3) if strong_vals else None,
        opp_weak_pct_mean=round(statistics.mean(weak_vals), 3) if weak_vals else None,
        opp_nut_eq_median_mean=round(statistics.mean(nut_eq_vals), 3) if nut_eq_vals else None,
        hero_dominates_nut_pct=round(sum(1 for v in dom_vals if v > 0) / len(dom_vals) * 100, 1) if dom_vals else None,
    )


def write_report(summaries, all_rows, elapsed_s):
    SCEN_STATS.write_text(json.dumps(summaries, indent=2, ensure_ascii=False))

    def sort_key(s):
        v = s.get("formula_huge_loss")
        return -(v if v is not None else -1)
    sorted_s = sorted(summaries, key=sort_key)

    with open(REPORT, "w") as f:
        f.write("# Probe Priority Report v2 (formula-aware)\n\n")
        f.write(f"生成: probe_priority.py / scenarios={len(summaries)} / "
                f"all_rows={len(all_rows)} / elapsed={elapsed_s:.0f}s\n\n")
        f.write("CORE_BOARDS 6 枚 (各 family 1 枚) × turn/river 動的選択で各 scenario を probe。"
                "公式 v9b/v10/v15 を applicable な hand 全てに適用し formula_loss を直接測定。\n\n")
        f.write("**判定基準**:\n")
        f.write("- `formula_huge_loss` 大 (≥0.3 BB) → 公式が大きく外す = **追加 fetch 価値 大**\n")
        f.write("- `formula_acc` 低 (<70%) → 公式が GTO best と一致しない頻度 大\n")
        f.write("- `bimodal_pct` 大 (>15%) → 単一 action 出力では原理的に miss、閾値判定 必要\n")
        f.write("- BASELINE 行と比較: probe 値が既存 fit と乖離 → out-of-domain の証拠\n\n")
        f.write("**注意**: 3BP/4BP は SPR/pot 単位が SRP と違うため formula_huge_loss の絶対値比較に注意。"
                "代わりに `formula_huge_pct` で「公式 miss 率」として相対比較してください。\n\n")

        f.write("## ランキング (formula_huge_loss 降順)\n\n")
        f.write("| Rank | ID | Target | GT/depth | n_combos | f_acc% | f_mean_loss | "
                "**f_huge_loss** | f_huge% | bimodal% | mean_gap | F/C/R% | ok/fail |\n")
        f.write("|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|\n")
        for rank, s in enumerate(sorted_s, 1):
            def fmt(v): return v if v is not None else "—"
            fhl = s["formula_huge_loss"]
            fhl_s = f"**{fhl}**" if fhl is not None else "—"
            tag = " (BASELINE)" if s.get("baseline_huge_loss") is not None else ""
            f.write(f"| {rank} | **{s['id']}**{tag} | {s['target']} | "
                    f"{s['GT'].split('_')[0]}/{s['depth']} | {s['n']} | "
                    f"{fmt(s['formula_acc'])} | {fmt(s['formula_mean_loss'])} | {fhl_s} | "
                    f"{fmt(s['formula_huge_pct'])} | {s['bimodal_pct']}% | "
                    f"{s['mean_ev_gap']} | "
                    f"{s['pct_fold']}/{s['pct_call']}/{s['pct_raise']}% | "
                    f"{s['n_spots_ok']}/{s['n_spots_fail']} |\n")

        f.write("\n## Baseline 検証 (probe calibration)\n\n")
        f.write("既存 dataset_unified.csv で測定された値と probe 値を比較。"
                "近い → probe が正しく公式 fit を再現できている。乖離大 → board sample 偏り。\n\n")
        f.write("| ID | 既存 huge_loss | probe formula_huge_loss | 乖離 |\n")
        f.write("|---|---:|---:|---:|\n")
        for s in summaries:
            bhl = s.get("baseline_huge_loss")
            phl = s.get("formula_huge_loss")
            if bhl is not None and phl is not None:
                diff = phl - bhl
                f.write(f"| {s['id']} | {bhl} | {phl} | {diff:+.3f} |\n")

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
                f.write("- **formula**: 適用外 (CR/donk/IP defender — 専用公式なし)\n")
            f.write(f"- modal split: FOLD={s['pct_fold']}% CALL={s['pct_call']}% RAISE={s['pct_raise']}%, "
                    f"bimodal_combo%={s['bimodal_pct']}%\n")
            if s["per_board_huge_loss"]:
                items = ", ".join(f"{b}={v} (n={s['per_board_n'][b]})"
                                  for b, v in s["per_board_huge_loss"].items())
                f.write(f"- per-board huge_loss: {items}\n")
            # opp range structure
            if s.get("opp_polarization_mean") is not None:
                f.write(f"- **opp range**: polarization={s['opp_polarization_mean']} "
                        f"(strong={s['opp_strong_pct_mean']} + weak={s['opp_weak_pct_mean']}), "
                        f"nut_pct={s['opp_nut_pct_mean']}, nut_eq_median={s['opp_nut_eq_median_mean']}, "
                        f"hero_dominates_nut%={s['hero_dominates_nut_pct']}\n")
            if s.get("per_board_opp_struct"):
                lines = []
                for b, st in sorted(s["per_board_opp_struct"].items()):
                    if st["polarization"] is not None:
                        lines.append(f"{b}: pol={st['polarization']:.2f} nut_class={st['nut_class']} "
                                     f"nut_pct={st['nut_pct']:.2f}")
                if lines:
                    f.write(f"- per-board opp: {'; '.join(lines)}\n")
            f.write("\n")

        f.write("\n## 推奨フォローアップ\n\n")
        f.write("`formula_huge_loss >= 0.3 BB` かつ `n_combos >= 100` を Tier1 候補とする。\n"
                "CR/donk (formula N/A) は `huge_loss + bimodal_pct` で判定。\n\n")
        f.write("### Tier 1 (即 fetch):\n")
        for s in sorted_s:
            fhl = s.get("formula_huge_loss")
            if fhl and fhl >= 0.3 and s["n"] >= 100 and not s.get("baseline_huge_loss"):
                f.write(f"- **{s['id']}** (formula_huge_loss={fhl}): {s['desc']}\n")
        f.write("\n### Tier 2 (CR/donk 専用):\n")
        for s in sorted_s:
            if s.get("formula_huge_loss") is None and s["huge_loss"] >= 0.5 and s["n"] >= 100:
                f.write(f"- **{s['id']}** (huge_loss={s['huge_loss']}, bimodal={s['bimodal_pct']}%): "
                        f"{s['desc']}\n")


def main():
    all_rows = []
    summaries = []
    started = time.time()
    print("=== probe_priority v2 開始 ===\n", flush=True)

    for sc in SCENARIOS:
        print(f"--- {sc['id']}: {sc['desc']} ---", flush=True)
        rows, stats = run_scenario(sc)
        all_rows.extend(rows)
        summary = summarize(rows)
        summary.update({
            "id": sc["id"], "desc": sc["desc"], "GT": sc["GT"], "depth": sc["depth"],
            "target": sc["target"], "baseline_huge_loss": sc.get("baseline_huge_loss"),
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
