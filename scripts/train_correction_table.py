#!/usr/bin/env python3
"""TexasSolver の系統誤差を 17 型別補正テーブルとして学習する.

入力: knowledges/volume4/results/texassolver_accuracy_30.json
      （ref_cbet_pct = GTO Wizard 参照、solver_cbet_pct = TexasSolver 実測）

出力: knowledges/flop-advanced/correction_table.json
      型コード -> {offset, n, stdev, examples}

使い方:
    python3 scripts/train_correction_table.py
    python3 scripts/train_correction_table.py --loocv  # 漏出検証
"""
from __future__ import annotations
import argparse
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from board_classifier import classify  # noqa: E402

INPUT_FILES = [
    REPO / "knowledges/volume4/results/texassolver_accuracy_30.json",
    REPO / "knowledges/volume4/results/texassolver_blog_3boards.json",
    REPO / "knowledges/volume4/results/texassolver_extended_100.json",
]
OUTPUT_FILE = REPO / "knowledges/flop-advanced/correction_table.json"


def load_dataset() -> list[dict]:
    """全 input file を統合して読む。重複ボードは最新のみ採用."""
    combined: dict[str, dict] = {}
    for path in INPUT_FILES:
        if not path.exists():
            continue
        with open(path) as f:
            d = json.load(f)
        for r in d["results"]:
            if r.get("status") != "ok":
                continue
            combined[r["board"]] = r
    return list(combined.values())


def build_table(dataset: list[dict]) -> dict:
    """型ごとに (ref - solver) の平均オフセットを計算."""
    by_type: dict[str, list[dict]] = {}
    for r in dataset:
        feat = classify(r["board"])
        offset = r["ref_cbet_pct"] - r["solver_cbet_pct"]
        by_type.setdefault(feat.type_code, []).append({
            "board": r["board"],
            "type_name": feat.type_name,
            "ref": r["ref_cbet_pct"],
            "ts": r["solver_cbet_pct"],
            "offset": offset,
        })

    table = {}
    for type_code, samples in by_type.items():
        offsets = [s["offset"] for s in samples]
        table[type_code] = {
            "type_name": samples[0]["type_name"],
            "n": len(samples),
            "mean_offset": round(statistics.mean(offsets), 2),
            "stdev_offset": round(statistics.stdev(offsets), 2) if len(offsets) > 1 else 0.0,
            "min_offset": round(min(offsets), 2),
            "max_offset": round(max(offsets), 2),
            "examples": [
                {"board": s["board"], "ref": s["ref"], "ts": s["ts"],
                 "offset": round(s["offset"], 2)}
                for s in samples
            ],
        }

    # 全体フォールバック
    all_offsets = [r["ref_cbet_pct"] - r["solver_cbet_pct"] for r in dataset]
    table["_global"] = {
        "type_name": "fallback",
        "n": len(dataset),
        "mean_offset": round(statistics.mean(all_offsets), 2),
        "stdev_offset": round(statistics.stdev(all_offsets), 2),
        "min_offset": round(min(all_offsets), 2),
        "max_offset": round(max(all_offsets), 2),
    }

    return table


def loocv_evaluate(dataset: list[dict]) -> dict:
    """Leave-One-Out: 各ボードについて、それを除いた集合で型補正を学習し、
    残したボードの予測誤差を測る."""
    abs_errors = []
    raw_abs_errors = []  # 補正なしの誤差
    type_resolved = {"type_match": 0, "global_fallback": 0}

    for held_out in dataset:
        train = [r for r in dataset if r["board"] != held_out["board"]]
        table = build_table(train)
        feat = classify(held_out["board"])
        if feat.type_code in table:
            offset = table[feat.type_code]["mean_offset"]
            type_resolved["type_match"] += 1
        else:
            offset = table["_global"]["mean_offset"]
            type_resolved["global_fallback"] += 1

        predicted = held_out["solver_cbet_pct"] + offset
        ref = held_out["ref_cbet_pct"]
        abs_errors.append(abs(predicted - ref))
        raw_abs_errors.append(abs(held_out["solver_cbet_pct"] - ref))

    return {
        "n": len(abs_errors),
        "corrected_mae": round(statistics.mean(abs_errors), 2),
        "raw_mae": round(statistics.mean(raw_abs_errors), 2),
        "improvement_pct": round(
            (1 - statistics.mean(abs_errors) / statistics.mean(raw_abs_errors)) * 100, 1
        ),
        "type_resolved": type_resolved,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--loocv", action="store_true", help="Leave-One-Out 検証を実行")
    args = p.parse_args()

    dataset = load_dataset()
    table = build_table(dataset)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "_meta": {
            "description": "TexasSolver 系統誤差を 17 型別に補正するテーブル。"
                          "預測値 = TexasSolver 値 + mean_offset。",
            "source_files": [str(p.relative_to(REPO)) for p in INPUT_FILES if p.exists()],
            "n_training": len(dataset),
        },
        "table": table,
    }
    OUTPUT_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"Saved: {OUTPUT_FILE}")
    print()
    print(f"{'Type':<6} {'Name':<25} {'N':>2} {'Mean':>6} {'Stdev':>6} {'Range':<14}")
    print("-" * 70)
    for code, info in sorted(table.items()):
        if code == "_global":
            continue
        print(f"{code:<6} {info['type_name']:<25} {info['n']:>2} "
              f"{info['mean_offset']:>+6.1f} {info['stdev_offset']:>6.1f} "
              f"[{info['min_offset']:+.1f}, {info['max_offset']:+.1f}]")
    g = table["_global"]
    print(f"{'_GLOB':<6} {g['type_name']:<25} {g['n']:>2} "
          f"{g['mean_offset']:>+6.1f} {g['stdev_offset']:>6.1f} "
          f"[{g['min_offset']:+.1f}, {g['max_offset']:+.1f}]")

    if args.loocv:
        print()
        print("=== Leave-One-Out 検証 ===")
        eval_res = loocv_evaluate(dataset)
        print(f"  N: {eval_res['n']}")
        print(f"  補正なし MAE: {eval_res['raw_mae']}")
        print(f"  補正あり MAE: {eval_res['corrected_mae']}")
        print(f"  改善率: {eval_res['improvement_pct']}%")
        print(f"  型一致: {eval_res['type_resolved']['type_match']}, "
              f"全体フォールバック: {eval_res['type_resolved']['global_fallback']}")


if __name__ == "__main__":
    main()
