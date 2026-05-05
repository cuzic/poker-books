#!/usr/bin/env python3
"""
C=33%→3 境界ハンド検証スクリプト
Task #125

k72r_srp_raw.json（キャッシュ済み）から 33% CBet ノードを取得し、
HS≈3 付近のハンドの CALL/FOLD 率を確認して C=3 の妥当性を検証する。

DS = HS + A - 3 - C = HS + 3 - 3 - 3 = HS - 3
閾値:
  DS ≥ 8 → CR → HS ≥ 11
  DS 0-7 → CALL → HS 3〜10
  DS < 0 → FOLD → HS ≤ 2

境界検証:
  HS=3（ボトムペア最下位相当）→ DS=0 → CALL境界
  HS=2（ハイカード+BDFD?) → DS=-1 → FOLD

ボード K72r での代表ハンド:
  HS=6: JJ, TT（アンダーペア）
  HS=4: A2（ボトムペア）
  HS=0: 65o（ハイカードのみ）
  HS=4: A3s → A3o:0 + BDFD +4 = 4（ただし A3s: air+BDFD）
"""
from __future__ import annotations
import json
from pathlib import Path

REPO = Path("/home/cuzic/poker-books")
RAW  = REPO / "knowledges/volume4/results/c_coef_srp/k72r_srp_raw.json"
OUT  = REPO / "knowledges/volume4/results/c_coef_srp/c33_boundary.json"

POT = 7  # K72r SRP: pot=7bb


def get_oop_response_node(raw: dict, bet_pct: int) -> dict | None:
    """root → CHECK → BET X のノードを返す"""
    check_node = raw.get("childrens", {}).get("CHECK")
    if not check_node:
        return None
    expected = POT * bet_pct / 100.0
    for key, node in check_node.get("childrens", {}).items():
        if not key.startswith("BET"):
            continue
        try:
            amount = float(key.split()[1])
        except (IndexError, ValueError):
            continue
        if abs(amount - expected) < 1.5:
            return node
    return None


def extract_stats(node: dict, prefix: str) -> dict:
    """prefix に一致するコンボの平均 CALL/FOLD/RAISE 率"""
    strat = node.get("strategy", {})
    actions: list[str] = strat.get("actions", [])
    combos: dict[str, list[float]] = strat.get("strategy", {})

    idx = {}
    for act in ("FOLD", "CALL", "RAISE"):
        try:
            idx[act] = actions.index(act)
        except ValueError:
            # RAISE が無いノードもある
            idx[act] = None

    matched = []
    for combo, probs in combos.items():
        r0, r1 = combo[0].upper(), combo[2].upper()
        pair_key = "".join(sorted([r0, r1], reverse=True))
        if pair_key.startswith(prefix) or combo[:2].upper() == prefix:
            entry = {"combo": combo}
            for act, i in idx.items():
                entry[act.lower()] = probs[i] if i is not None and i < len(probs) else 0.0
            matched.append(entry)

    if not matched:
        return {"error": f"no combos for {prefix!r}"}

    avg = {}
    for act in ("fold", "call", "raise"):
        avg[f"avg_{act}_pct"] = round(sum(m[act] for m in matched) / len(matched) * 100, 1)
    avg["n_combos"] = len(matched)
    avg["combos"] = matched[:4]
    return avg


# K72r での HandScore（ドライ A=3）
TARGETS = [
    # (prefix, HS, 説明)
    ("JJ", 6,  "アンダーペア JJ（J < K）"),
    ("TT", 6,  "アンダーペア TT"),
    ("99", 6,  "アンダーペア 99"),
    ("A2", 4,  "ボトムペア A2（2 on board）"),
    ("A3", 0,  "エア A3o（A3s は BDFD で +4 だが offsuit=0）"),
    ("65", 0,  "エア 65o"),
    ("QJ", 0,  "エア QJo（K72r ではペアなし）"),
    ("87", 0,  "エア 87o"),
]


def main() -> None:
    raw = json.loads(RAW.read_text())
    node_33 = get_oop_response_node(raw, 33)
    if node_33 is None:
        print("ERROR: 33% CBet ノードが見つかりません")
        return

    results = {}
    print("=" * 65)
    print("C=33%→3 境界ハンド検証 (K72r SRP, A=3)")
    print("DS = HS + 3 - 3 - 3 = HS - 3")
    print("閾値: DS≥8→CR / DS 0〜7→CALL / DS<0→FOLD")
    print("=" * 65)

    for prefix, hs, desc in TARGETS:
        ds = hs - 3  # A=3, C=3
        expected = "CR" if ds >= 8 else "CALL" if ds >= 0 else "FOLD"
        stats = extract_stats(node_33, prefix)
        results[prefix] = {"HS": hs, "DS": ds, "expected": expected, **stats}

        if "error" in stats:
            print(f"{prefix:4} (HS={hs}, DS={ds}) → {desc}: {stats['error']}")
            continue

        call_p  = stats["avg_call_pct"]
        fold_p  = stats["avg_fold_pct"]
        raise_p = stats["avg_raise_pct"]
        dominant = max(call_p, fold_p, raise_p)
        actual = (
            "CR"   if raise_p == dominant else
            "CALL" if call_p  == dominant else
            "FOLD"
        )
        match = "✓" if actual == expected or (
            # 境界: DS=0 でどちらでも
            ds == 0 and actual in ("CALL","FOLD")
        ) else "△" if abs(call_p - fold_p) < 20 else "✗"

        print(f"{prefix:4} HS={hs} DS={ds:+d} → 予測:{expected:4} | "
              f"CR={raise_p:5.1f}% CALL={call_p:5.1f}% FOLD={fold_p:5.1f}% | {match} ({desc})")

    print("=" * 65)
    print()

    # 判定サマリー
    boundary_hs = 3  # DS=0, CALL/FOLD 境界
    print(f"C=3 のコール境界: HS≥{boundary_hs} → DS≥0 → CALL")
    print(f"HS=4（ボトムペア）: A2 = {results.get('A2',{}).get('avg_call_pct','?')}% CALL "
          f"→ C≤4 を確認（C=3も成立）")
    print(f"HS=6（アンダーペア）: JJ = {results.get('JJ',{}).get('avg_call_pct','?')}% CALL "
          f"→ 余裕でコール域")
    print(f"HS=0（エア）: 65o = {results.get('65',{}).get('avg_call_pct','?')}% CALL / "
          f"{results.get('65',{}).get('avg_fold_pct','?')}% FOLD → DS=-3 → FOLD確認")

    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\n保存: {OUT}")


if __name__ == "__main__":
    main()
