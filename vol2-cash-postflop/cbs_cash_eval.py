"""
CBS システムのキャッシュゲーム精度評価
- MTT CBS (HP+DP, 閾値 BTN=全ベット/SB=5/7/LIMP=5/9) をキャッシュデータに適用
- ポジション→シナリオマッピング、WRMSE算出
"""
import json

# --- CBS HP mapping ---
HP = {
    "no_made_hand": 2, "ace_high": 2, "king_high": 2,
    "low_pair": 3, "underpair": 3, "third_pair": 3,
    "second_pair": 5,
    "top_pair": 7, "overpair": 7,
    "two_pair": 9, "flush": 9, "straight": 9,
    "set": 7, "trips": 7,
    "fullhouse": 9, "quads": 9,
}

# DP: draw cats から近似
DP_draw = {
    "no_draw": 0, "twocards_bdfd": 0, "gutshot": 1,
    "oesd": 2, "fd": 2, "combo_draw": 3,
}

def cbs_predict(cbs, scenario):
    """CBS スコアとシナリオから CBet 判定を返す (0=check, 0.5=mix, 1=bet)"""
    if scenario == "BTN":   # 全ベット
        if cbs <= 7 and cbs >= 7:  # セット/FH は混合
            return 0.5 if cbs == 7 else 1.0
        return 1.0  # 全ベット
    elif scenario == "SB":  # 5/7
        if cbs < 5: return 0.0
        if cbs >= 7: return 1.0
        return 0.5
    else:  # LIMP / UTG-like: 5/9
        if cbs < 5: return 0.0
        if cbs >= 9: return 1.0
        return 0.5

def scenario_from_position(pos):
    """ポジション→CBSシナリオ（案A: 単純マッピング）"""
    if pos in ("BTN_BB", "CO_BB", "BTN_SB"):
        return "BTN"
    elif pos in ("SB_BB",):
        return "SB"
    else:  # HJ_BB, UTG_BB
        return "LIMP"

def scenario_from_ras(ras):
    """RAS値→CBSシナリオ（案B: RASベース動的）"""
    if ras >= 0.65: return "BTN"
    if ras >= 0.40: return "SB"
    return "LIMP"

def run_eval(use_ras=False):
    with open("/home/cuzic/poker-books/cash-postflop/findings/cash_5cat_gto.json") as f:
        data = json.load(f)

    records = []
    for pos, boards in data.items():
        for board_key, info in boards.items():
            hand_cats = info.get("hand_cats", {})
            draw_cats = info.get("draw_cats", {})
            board_type = info.get("type", "")

            # RAS proxy = no_draw aggregate CBet%
            ras = 0.0
            if "no_draw" in draw_cats and draw_cats["no_draw"].get("combos", 0) > 0:
                ras = draw_cats["no_draw"]["bet_pct"] / 100.0
            else:
                # Fallback: エアーのbet_pct
                if "no_made_hand" in hand_cats:
                    ras = hand_cats["no_made_hand"].get("bet_pct", 50) / 100.0

            for hand_type, vals in hand_cats.items():
                if hand_type not in HP:
                    continue
                n = vals.get("combos", 0)
                if n < 5:
                    continue
                gto_pct = vals.get("bet_pct", 0) / 100.0

                hp = HP[hand_type]
                dp = 0  # hand_catsはドロー込み集計なのでDP=0で近似
                cbs = hp + dp

                if use_ras:
                    sc = scenario_from_ras(ras)
                else:
                    sc = scenario_from_position(pos)

                pred = cbs_predict(cbs, sc)
                err = pred - gto_pct
                records.append({
                    "pos": pos, "board": board_key, "board_type": board_type,
                    "hand": hand_type, "n": n, "gto": gto_pct,
                    "ras": ras, "cbs": cbs, "sc": sc, "pred": pred, "err": err,
                })

    if not records:
        print("No data")
        return

    total_n = sum(r["n"] for r in records)
    wmse = sum(r["n"] * r["err"]**2 for r in records) / total_n
    wrmse = wmse**0.5
    wmae = sum(r["n"] * abs(r["err"]) for r in records) / total_n

    print(f"{'RASベース' if use_ras else 'ポジションベース'} CBS精度:")
    print(f"  データ点数 = {len(records)}, 合計コンボ = {total_n:.0f}")
    print(f"  WRMSE = {wrmse*100:.1f}%")
    print(f"  WMAE  = {wmae*100:.1f}%")
    print()

    # シナリオ別
    from collections import defaultdict
    by_pos = defaultdict(list)
    for r in records:
        by_pos[r["pos"]].append(r)

    print("  ポジション別 WRMSE:")
    for pos in ["BTN_BB","CO_BB","HJ_BB","UTG_BB","SB_BB","BTN_SB"]:
        recs = by_pos.get(pos, [])
        if not recs: continue
        tn = sum(r["n"] for r in recs)
        wms = sum(r["n"] * r["err"]**2 for r in recs) / tn
        print(f"    {pos:10s}: WRMSE={wms**0.5*100:.1f}%  (n={len(recs)}, sc={recs[0]['sc']})")

    print()

    # 手牌別 系統誤差（ポジションベース）
    by_hand = defaultdict(list)
    for r in records:
        by_hand[r["hand"]].append(r)

    print("  手牌別 平均誤差 (pred - GTO):")
    hand_order = ["no_made_hand","ace_high","king_high","low_pair","underpair",
                  "third_pair","second_pair","top_pair","overpair",
                  "two_pair","straight","flush","set","trips","fullhouse","quads"]
    for h in hand_order:
        recs = by_hand.get(h, [])
        if not recs: continue
        tn = sum(r["n"] for r in recs)
        bias = sum(r["n"] * r["err"] for r in recs) / tn
        wmse_h = sum(r["n"] * r["err"]**2 for r in recs) / tn
        avg_gto = sum(r["n"] * r["gto"] for r in recs) / tn
        print(f"    {h:15s} HP={HP[h]} bias={bias*100:+.1f}%  WRMSE={wmse_h**0.5*100:.1f}%  avg_GTO={avg_gto*100:.0f}%  (n={len(recs)})")

print("=" * 60)
print("案A: ポジション → シナリオ固定マッピング")
print("  BTN/CO/BTN_SB → 全ベット, SB_BB → SB(5/7), HJ/UTG → LIMP(5/9)")
print("=" * 60)
run_eval(use_ras=False)

print("=" * 60)
print("案B: RAS(no_draw CBet%) → シナリオ動的マッピング")
print("  RAS≥65%=BTN, RAS40-65%=SB(5/7), RAS<40%=LIMP(5/9)")
print("=" * 60)
run_eval(use_ras=True)
