"""
アウツベース CBS（OBS）の精度評価
- 強アウツ（FD/OESD）+ 弱アウツ（ツーペアドロー、バックドア）+ メイド手アンカー
- MTT JSONL データで WRMSE を CBS と比較
"""
import json, glob, math
from collections import defaultdict

# === アウツ定義 ===

# メイドハンド「アンカーアウツ」: 現在の強さを等価アウツに変換
ANCHOR_OUTS = {
    "no_made":     0,   # エアー: アウツなし
    "king_high":   0,   # ハイカード: 同上
    "low_pair":    3,   # 弱ペア: ツーペア/トリップスへ ~3アウツ相当
    "underpair":   3,
    "third_pair":  3,
    "second_pair": 5,   # セカンドペア: ~5アウツ相当
    "top_pair":   10,   # トップペア: ~10アウツ相当（強い）
    "overpair":   10,
    "two_pair":   14,   # ツーペア+: ~14アウツ（フルハウスまで）
    "flush":      14,
    "straight":   14,
    "set":        10,   # セット: スロープレイ→10（実質14だが混合戦略）
    "trips":      10,
    "fullhouse":  14,
    "quads":      14,
}

# ドロー「実アウツ」: 標準アウツ数
DRAW_OUTS = {
    "no_draw":    0,
    "bdfd":       2,    # バックドアFD: ~1.5アウツ相当（切り上げ2）
    "gutshot":    4,    # ガットショット: 4アウツ
    "oesd":       8,    # 両面ストレートドロー: 8アウツ
    "fd":         9,    # フラッシュドロー: 9アウツ
    "combo_draw": 15,   # コンボドロー: 15アウツ
}

# === HP/DP → CBS（現行）との比較用 ===
HP = {
    "no_made": 2, "king_high": 2,
    "low_pair": 3, "underpair": 3, "third_pair": 3,
    "second_pair": 5,
    "top_pair": 7, "overpair": 7,
    "two_pair": 9, "flush": 9, "straight": 9,
    "set": 7, "trips": 7,
    "fullhouse": 9, "quads": 9,
}
DP = {"no_draw": 0, "bdfd": 0, "gutshot": 1, "oesd": 2, "fd": 2, "combo_draw": 3}

def scenario_type(scenario_name):
    if "LIMP" in scenario_name: return "LIMP"
    if "_SB" in scenario_name and "LIMP" not in scenario_name: return "SB"
    return "BTN"

def cbs_pred(cbs, sc):
    """CBS → 予測 CBet率"""
    if sc == "BTN": return 1.0
    if sc == "SB":  return 0.0 if cbs < 5 else (1.0 if cbs >= 7 else 0.5)
    return 0.0 if cbs < 5 else (1.0 if cbs >= 9 else 0.5)

def obs_pred(outs, sc, t_lo, t_hi):
    """OBS → 予測 CBet率（閾値パラメータ化）"""
    if sc == "BTN": return 1.0
    return 0.0 if outs < t_lo else (1.0 if outs >= t_hi else 0.5)

def load_data():
    records = []
    hand_map = {
        "no_made_hand": "no_made", "king_high": "king_high",
        "low_pair": "low_pair", "underpair": "underpair", "third_pair": "third_pair",
        "second_pair": "second_pair", "top_pair": "top_pair", "overpair": "overpair",
        "two_pair": "two_pair", "flush": "flush", "straight": "straight",
        "set": "set", "trips": "trips", "fullhouse": "fullhouse", "quads": "quads",
    }
    draw_map = {
        "no_draw": "no_draw", "twocards_bdfd": "bdfd", "gutshot": "gutshot",
        "oesd": "oesd", "fd": "fd", "combo_draw": "combo_draw",
    }
    for path in sorted(glob.glob("mtt-postflop/findings/draw_study_*.jsonl")):
        sc_name = path.split("draw_study_")[1].replace(".jsonl","")
        with open(path) as f:
            for line in f:
                d = json.loads(line)
                sc = d.get("scenario", sc_name)
                for cross_key, vals in d.get("cross", {}).items():
                    parts = cross_key.split("|")
                    if len(parts) != 2: continue
                    ht = hand_map.get(parts[0])
                    dt = draw_map.get(parts[1])
                    if not ht or not dt: continue
                    n = vals.get("n", 0)
                    if n < 3: continue
                    avg = vals.get("avg", 0) / 100.0
                    records.append({
                        "sc_name": sc,
                        "sc": scenario_type(sc),
                        "hand": ht, "draw": dt,
                        "n": n, "gto": avg,
                        "hp": HP.get(ht, 2), "dp": DP.get(dt, 0),
                        "anchor": ANCHOR_OUTS.get(ht, 0),
                        "draw_outs": DRAW_OUTS.get(dt, 0),
                    })
    return records

records = load_data()
total_n = sum(r["n"] for r in records)
print(f"データ: {len(records)}点, コンボ合計={total_n:.0f}")

# === CBS WRMSE ===
cbs_wmse = sum(r["n"] * (cbs_pred(r["hp"]+r["dp"], r["sc"]) - r["gto"])**2
               for r in records) / total_n
print(f"\nCBS (HP+DP, 既存): WRMSE = {cbs_wmse**0.5*100:.1f}%")

# === OBS WRMSE: 各閾値でグリッドサーチ ===
print("\nOBS (アンカー+ドローアウツ) 閾値グリッドサーチ:")
best_wrmse = 999
best_params = None
for t_lo in range(2, 10):
    for t_hi in range(t_lo+2, 18):
        wmse = sum(r["n"] * (obs_pred(r["anchor"]+r["draw_outs"], r["sc"], t_lo, t_hi) - r["gto"])**2
                   for r in records) / total_n
        if wmse < best_wrmse:
            best_wrmse = wmse
            best_params = (t_lo, t_hi)

print(f"  最良: t_lo={best_params[0]}, t_hi={best_params[1]}, WRMSE={best_wrmse**0.5*100:.1f}%")

# 近傍も確認
for t_lo in range(best_params[0]-2, best_params[0]+3):
    for t_hi in range(best_params[1]-2, best_params[1]+3):
        if t_hi <= t_lo + 1: continue
        wmse = sum(r["n"] * (obs_pred(r["anchor"]+r["draw_outs"], r["sc"], t_lo, t_hi) - r["gto"])**2
                   for r in records) / total_n
        print(f"    t_lo={t_lo:2d}, t_hi={t_hi:2d}: WRMSE={wmse**0.5*100:.1f}%")

# === SBシナリオ詳細比較 ===
t_lo, t_hi = best_params
print(f"\nSBシナリオ 詳細比較 (OBS閾値={t_lo}/{t_hi}):")
header = f"{'手牌':15s} {'ドロー':10s} {'アンカー':>6s} {'ドローOuts':>9s} {'合計':>5s} {'CBS':>5s} {'OBS判定':>7s} {'実GTO':>7s}"
print(header)

sb_recs = [r for r in records if r["sc"] == "SB"]
by_hd = defaultdict(list)
for r in sb_recs:
    by_hd[(r["hand"], r["draw"])].append(r)

hand_order = ["no_made","king_high","low_pair","underpair","third_pair",
              "second_pair","top_pair","overpair","two_pair","set","fullhouse"]
draw_order = ["no_draw","bdfd","gutshot","oesd","fd","combo_draw"]

for h in hand_order:
    for d in draw_order:
        recs = by_hd.get((h, d), [])
        if not recs: continue
        tn = sum(r["n"] for r in recs)
        avg_gto = sum(r["n"]*r["gto"] for r in recs) / tn
        anc = ANCHOR_OUTS[h]; dr = DRAW_OUTS[d]
        total_outs = anc + dr
        cbs_score = HP.get(h,2) + DP.get(d,0)
        cbs_j = "mix" if 5 <= cbs_score < 7 else ("bet" if cbs_score >= 7 else "check")
        obs_j = "mix" if t_lo <= total_outs < t_hi else ("bet" if total_outs >= t_hi else "check")
        match = "✓" if obs_j == ("bet" if avg_gto >= 0.7 else ("check" if avg_gto < 0.3 else "mix")) else "△"
        print(f"  {h:15s} {d:10s} {anc:6d} {dr:9d} {total_outs:5d}  CBS={cbs_j:5s} OBS={obs_j:5s} GTO={avg_gto*100:.0f}% {match}")

# === アウツの意味整理 ===
print("\n" + "="*60)
print("アウツ対応表（覚える数字）:")
print("  メイドハンド(アンカーアウツ):")
for h, a in [("エアー/ハイカード","0"), ("弱ペア(ロウ/3rd/アンダー)","3"),
             ("セカンドペア","5"), ("トップペア/オーバー","10"),
             ("ツーペア+/ストレート/フラッシュ","14"), ("セット（混合注意）","10")]:
    print(f"    {h}: {a}アウツ")
print("  ドロー(実アウツ):")
for d, o in [("なし","0"), ("バックドアFD","2"), ("ガットショット","4"),
             ("OESD","8"), ("フラッシュドロー","9"), ("コンボドロー","15")]:
    print(f"    {d}: {o}アウツ")
