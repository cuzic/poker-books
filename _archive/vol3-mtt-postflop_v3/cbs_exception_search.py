"""
CBS 例外ルール探索
- 現行CBSの残差を分析し、追加すべき例外を特定
- 各例外ルールの WRMSE 改善量を測定
"""
import json, glob
from collections import defaultdict

HP = {"no_made": 2, "king_high": 2, "low_pair": 3, "underpair": 3, "third_pair": 3,
      "second_pair": 5, "top_pair": 7, "overpair": 7, "two_pair": 9, "flush": 9,
      "straight": 9, "set": 7, "trips": 7, "fullhouse": 9, "quads": 9}
DP = {"no_draw": 0, "bdfd": 0, "gutshot": 1, "oesd": 2, "fd": 2, "combo_draw": 3}

hand_map = {"no_made_hand":"no_made","king_high":"king_high","low_pair":"low_pair",
            "underpair":"underpair","third_pair":"third_pair","second_pair":"second_pair",
            "top_pair":"top_pair","overpair":"overpair","two_pair":"two_pair",
            "flush":"flush","straight":"straight","set":"set","trips":"trips",
            "fullhouse":"fullhouse","quads":"quads"}
draw_map = {"no_draw":"no_draw","twocards_bdfd":"bdfd","gutshot":"gutshot",
            "oesd":"oesd","fd":"fd","combo_draw":"combo_draw"}

def sc_type(sc):
    if "LIMP" in sc: return "LIMP"
    if "3BP" in sc: return "3BP"
    if "_SB" in sc: return "SB"
    return "BTN"

records = []
for path in sorted(glob.glob("mtt-postflop/findings/draw_study_*.jsonl")):
    with open(path) as f:
        for line in f:
            d = json.loads(line)
            sc = sc_type(d.get("scenario",""))
            for ck, cv in d.get("cross",{}).items():
                parts = ck.split("|")
                if len(parts)!=2: continue
                ht = hand_map.get(parts[0]); dt = draw_map.get(parts[1])
                if not ht or not dt: continue
                n = cv.get("n",0)
                if n < 3: continue
                records.append({
                    "sc": sc, "hand": ht, "draw": dt, "n": n,
                    "gto": cv["avg"]/100.0,
                    "hp": HP[ht], "dp": DP[dt],
                    "cbs": HP[ht] + DP[dt],
                })

total_n = sum(r["n"] for r in records)

# ベースCBS予測（例外なし）
def pred_base(r, override=None):
    sc = r["sc"]; cbs = r["cbs"]
    if override: cbs = override
    if sc == "BTN": return 1.0
    if sc == "3BP":  # 3BP caller想定
        return 0.0 if cbs < 5 else (1.0 if cbs >= 7 else 0.5)
    if sc == "SB":
        return 0.0 if cbs < 5 else (1.0 if cbs >= 7 else 0.5)
    return 0.0 if cbs < 5 else (1.0 if cbs >= 9 else 0.5)  # LIMP

def wrmse(recs, pred_fn):
    tn = sum(r["n"] for r in recs)
    return (sum(r["n"]*(pred_fn(r)-r["gto"])**2 for r in recs)/tn)**0.5

base_wrmse = wrmse(records, pred_base)
print(f"ベース CBS WRMSE = {base_wrmse*100:.1f}%\n")

# --- 例外ルール候補を列挙してテスト ---
exceptions = []

# E1: 3BP → 全シナリオ「混合」
def e1(r):
    if r["sc"] == "3BP": return 0.5
    return pred_base(r)
w = wrmse(records, e1)
exceptions.append(("E1: 3BPは全ハンド混合(0.5固定)", w))

# E2: セット/トリップスをSB/LIMPで強制mix
def e2(r):
    if r["hand"] in ("set","trips") and r["sc"] in ("SB","LIMP"):
        return 0.5
    return pred_base(r)
w = wrmse(records, e2)
exceptions.append(("E2: set/tripsをSB/LIMPで強制mix", w))

# E3: FH/quadsをSB/LIMPで強制check
def e3(r):
    if r["hand"] in ("fullhouse","quads") and r["sc"] in ("SB","LIMP"):
        return 0.0
    return pred_base(r)
w = wrmse(records, e3)
exceptions.append(("E3: FH/quadsをSB/LIMPでcheck", w))

# E4: エアー+FD/OESDをSBで強制mix
def e4(r):
    if r["hand"] in ("no_made","king_high") and r["draw"] in ("fd","oesd") and r["sc"] in ("SB","LIMP"):
        return 0.5
    return pred_base(r)
w = wrmse(records, e4)
exceptions.append(("E4: air+FD/OESDをSB/LIMPでmix", w))

# E5: 弱ペア+コンボドローをSBでベット
def e5(r):
    if r["hand"] in ("low_pair","underpair","third_pair") and r["draw"] == "combo_draw" and r["sc"] in ("SB","LIMP"):
        return 1.0
    return pred_base(r)
w = wrmse(records, e5)
exceptions.append(("E5: 弱ペア+コンボドローをSB/LIMPでbet", w))

# E6: LIMPでトップペア+ドローなしをmix（現状はbet=7≥7）
def e6(r):
    if r["hand"] in ("top_pair","overpair") and r["draw"] == "no_draw" and r["sc"] == "LIMP":
        return 0.5
    return pred_base(r)
w = wrmse(records, e6)
exceptions.append(("E6: LIMP×トップペア+noDrawをmix", w))

# E7: BTNでセット/FHをmix（現状は全ベット）
def e7(r):
    if r["hand"] in ("set","trips","fullhouse","quads") and r["sc"] == "BTN":
        return 0.5
    return pred_base(r)
w = wrmse(records, e7)
exceptions.append(("E7: BTN×set/trips/FH/quadsをmix", w))

# E8: E1+E2+E3 複合
def e8(r):
    if r["sc"] == "3BP": return 0.5
    if r["hand"] in ("set","trips") and r["sc"] in ("SB","LIMP"): return 0.5
    if r["hand"] in ("fullhouse","quads") and r["sc"] in ("SB","LIMP"): return 0.0
    return pred_base(r)
w = wrmse(records, e8)
exceptions.append(("E8: E1+E2+E3 複合", w))

# E9: E1+E2+E3+E4 複合
def e9(r):
    if r["sc"] == "3BP": return 0.5
    if r["hand"] in ("set","trips") and r["sc"] in ("SB","LIMP"): return 0.5
    if r["hand"] in ("fullhouse","quads") and r["sc"] in ("SB","LIMP"): return 0.0
    if r["hand"] in ("no_made","king_high") and r["draw"] in ("fd","oesd") and r["sc"] in ("SB","LIMP"): return 0.5
    return pred_base(r)
w = wrmse(records, e9)
exceptions.append(("E9: E1+E2+E3+E4 複合（4例外）", w))

# E10: E1+E2+E3+E4+E6+E7 全部入り
def e10(r):
    if r["sc"] == "3BP": return 0.5
    if r["hand"] in ("set","trips") and r["sc"] in ("SB","LIMP"): return 0.5
    if r["hand"] in ("set","trips","fullhouse","quads") and r["sc"] == "BTN": return 0.5
    if r["hand"] in ("fullhouse","quads") and r["sc"] in ("SB","LIMP"): return 0.0
    if r["hand"] in ("no_made","king_high") and r["draw"] in ("fd","oesd") and r["sc"] in ("SB","LIMP"): return 0.5
    if r["hand"] in ("top_pair","overpair") and r["draw"] == "no_draw" and r["sc"] == "LIMP": return 0.5
    return pred_base(r)
w = wrmse(records, e10)
exceptions.append(("E10: 全例外（6ルール）", w))

print(f"{'ルール':<40s}  {'WRMSE':>8s}  {'改善':>8s}")
print("-"*62)
for name, w in exceptions:
    imp = (base_wrmse - w) * 100
    mark = "★★★" if imp > 3 else ("★★" if imp > 1.5 else ("★" if imp > 0.5 else ""))
    print(f"  {name:<40s}  {w*100:6.1f}%  {imp:+6.1f}% {mark}")

print()
# E9 詳細: シナリオ別
print("E9複合ルール シナリオ別 WRMSE:")
for sc in ["BTN","3BP","SB","LIMP"]:
    recs = [r for r in records if r["sc"]==sc]
    if not recs: continue
    wb = wrmse(recs, pred_base)
    we = wrmse(recs, e9)
    print(f"  {sc:6s}: {wb*100:.1f}% → {we*100:.1f}%  ({(wb-we)*100:+.1f}%)")

# 手牌×シナリオ別 残差（E9後）
print("\nE9後の大残差ケース（重み付き二乗誤差 上位10）:")
residuals = []
for r in records:
    pred = e9(r)
    residuals.append((r["n"]*(pred-r["gto"])**2, r["hand"], r["draw"], r["sc"], r["gto"], pred))
residuals.sort(reverse=True)
for contrib, h, d, sc, gto, pred in residuals[:10]:
    print(f"  {h:15s} {d:12s} {sc:5s}  GTO={gto*100:.0f}%  pred={pred*100:.0f}%  contrib={contrib:.1f}")
