#!/usr/bin/env python3
"""
後手スコア 20-case 再検証スクリプト v3 (新スケール 0-100 equity %)

旧版 ds_framework_recheck.py の新スケール対応。
旧版は残し、新規 v3 として作成。

phase1 の defender_summary.csv (旧 H1/H2/H3 バケツ) を読み込み、
新スケール代表 HS / 新 A 値 / 新 C 値で DS を再計算して GTO 実測と照合する。

新仕様 (knowledges/ds_redesign_v2/SPEC_OTHER_FORMULAS.md):
  後手スコア = HS + A - C - M
  C: {33: 12, 50: 17, 75: 22, 100: 25, 150: 30}
  A: dry=12 / semi=6 / wet=0
  閾値: >=40 CR / >=20 コール / <20 フォールド
  バケツ代表 HS: H3=70 / H2=50 / H1=28

出力: knowledges/volume4/results/ds_framework_recheck/result_v3.json
       knowledges/volume4/results/ds_framework_recheck/table_v3.md
"""
from __future__ import annotations
import csv
import json
import sys
from pathlib import Path

REPO = Path("/home/cuzic/poker-books")
sys.path.insert(0, str(REPO / "scripts"))
from c_coefficients_v3 import (  # noqa: E402
    C_TABLE, A_TABLE, M_TABLE, HS_REP,
    DS_TH_RAISE, DS_TH_CALL,
    defender_score, predict_defender,
)

PHASE1 = REPO / "knowledges/volume4/results/phase1"
OUT_DIR = REPO / "knowledges/volume4/results/ds_framework_recheck"

# ボード設定 (旧 A 値 → 新 A 値)
# K72r: ドライ → A=12
# KJ7r: セミウェット → A=6
# T98r: ウェット → A=0
BOARDS = [
    ("kc7d2s", "K72r", "dry"),
    ("khjd7s", "KJ7r", "semi"),
    ("th9d8c", "T98r", "wet"),
]


def verdict(predicted: str, row: dict) -> str:
    raise_pct = float(row["raise_pct"])
    call_pct = float(row["call_pct"])
    fold_pct = float(row["fold_pct"])
    dominant = max(raise_pct, call_pct, fold_pct)
    actual = (
        "raise" if raise_pct == dominant else
        "call" if call_pct == dominant else
        "fold"
    )
    if predicted == actual:
        return "✓"
    # boundary check: within 20pp of second-best
    if predicted == "raise" and raise_pct >= 40:
        return "△ 境界"
    if predicted == "call" and call_pct >= 40:
        return "△ 境界"
    if predicted == "fold" and fold_pct >= 40:
        return "△ 境界"
    return "✗"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows_all: list[dict] = []

    for dir_name, board_label, board_type in BOARDS:
        a_val = A_TABLE[board_type]
        csv_path = PHASE1 / dir_name / "defender_summary.csv"
        # CSV header: board,bet_pct,bucket,n,fold_pct,call_pct,raise_pct
        # board "Kc,7d,2s" は 3 列に分かれて格納されているため:
        FIELDNAMES = [
            "c0", "c1", "c2", "bet_pct", "bucket",
            "n", "fold_pct", "call_pct", "raise_pct",
        ]
        if not csv_path.exists():
            print(f"WARN: {csv_path} not found, skipping")
            continue
        with open(csv_path) as f:
            next(f)  # skip header
            reader = csv.DictReader(f, fieldnames=FIELDNAMES)
            for row in reader:
                bet_pct = int(row["bet_pct"])
                bucket = row["bucket"].strip()
                if bet_pct not in C_TABLE:
                    continue
                if bucket not in HS_REP:
                    continue
                c_val = C_TABLE[bet_pct]
                hs = HS_REP[bucket]
                m_val = M_TABLE["HU"]  # phase1 は HU
                ds = defender_score(hs, a_val, c_val, m_val)
                pred = predict_defender(ds)
                v = verdict(pred, row)
                rows_all.append({
                    "board": board_label,
                    "board_type": board_type,
                    "A": a_val,
                    "size": f"{bet_pct}%",
                    "C": c_val,
                    "M": m_val,
                    "bucket": bucket,
                    "HS_rep": hs,
                    "DS": ds,
                    "predicted": pred,
                    "raise_pct": round(float(row["raise_pct"]), 1),
                    "call_pct": round(float(row["call_pct"]), 1),
                    "fold_pct": round(float(row["fold_pct"]), 1),
                    "verdict": v,
                })

    if not rows_all:
        print("ERROR: no rows processed")
        return

    total = len(rows_all)
    correct = sum(1 for r in rows_all if r["verdict"] == "✓")
    boundary = sum(1 for r in rows_all if "境界" in r["verdict"])
    wrong = sum(1 for r in rows_all if r["verdict"] == "✗")

    # JSON 保存
    result = {
        "scale": "v3 (new, 0-100 equity %)",
        "formula": "DS = HS + A - C - M",
        "thresholds": {
            "raise": f">= {DS_TH_RAISE}",
            "call":  f">= {DS_TH_CALL}",
            "fold":  f"< {DS_TH_CALL}",
        },
        "C_TABLE": C_TABLE,
        "A_TABLE": A_TABLE,
        "M_TABLE": M_TABLE,
        "HS_REP": HS_REP,
        "summary": {
            "total": total,
            "correct": correct,
            "boundary": boundary,
            "wrong": wrong,
            "match_rate": round(correct / total * 100, 1),
            "match_rate_incl_boundary":
                round((correct + boundary) / total * 100, 1),
        },
        "rows": rows_all,
    }
    out_json = OUT_DIR / "result_v3.json"
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    # Markdown テーブル保存
    lines = [
        "# 後手スコア 再検証 v3 (新スケール 0-100 equity %)",
        "",
        f"検証日: 2026-05-05 / スケール: v3",
        "",
        f"DS = HS + A - C - M, "
        f"閾値: >={DS_TH_RAISE} CR / >={DS_TH_CALL} call / <{DS_TH_CALL} fold",
        "",
        f"**一致率: {correct}/{total} = {correct/total*100:.1f}%**"
        f" (△境界含む: {(correct+boundary)/total*100:.1f}%)",
        "",
        "| ボード | type | A | サイズ | C | M | バケツ | HS代表 | DS | 予測 | 実測(R/C/F%) | 判定 |",
        "|--------|------|---|--------|---|---|--------|--------|----|----|---|---|",
    ]
    for r in rows_all:
        actual_str = f"{r['raise_pct']}/{r['call_pct']}/{r['fold_pct']}"
        lines.append(
            f"| {r['board']} | {r['board_type']} | {r['A']} | {r['size']} "
            f"| {r['C']} | {r['M']} | {r['bucket']} | {r['HS_rep']} | {r['DS']} "
            f"| {r['predicted']} | {actual_str} | {r['verdict']} |"
        )

    lines += ["", "## 境界・不一致ケース", ""]
    for r in rows_all:
        if r["verdict"] != "✓":
            lines.append(
                f"- **{r['board']} {r['size']} {r['bucket']}**: "
                f"DS={r['DS']} → 予測 {r['predicted']}, "
                f"実測 R{r['raise_pct']}%/C{r['call_pct']}%/F{r['fold_pct']}%"
            )

    (OUT_DIR / "table_v3.md").write_text("\n".join(lines) + "\n")

    # stdout サマリー
    print(f"ボード×サイズ×バケツ 計 {total} ケース")
    print(f"一致: {correct} ({correct/total*100:.1f}%)")
    print(f"境界: {boundary}")
    print(f"不一致: {wrong}")
    print()
    header = (
        f"{'ボード':6} {'type':4} {'A':>2} {'サイズ':5} {'C':>2} "
        f"{'バケツ':4} {'DS':>4}  {'予測':6}  実測(R/C/F)  判定"
    )
    print(header)
    print("-" * len(header))
    for r in rows_all:
        print(
            f"{r['board']:6} {r['board_type']:4} {r['A']:>2} {r['size']:5} "
            f"{r['C']:>2} {r['bucket']:4} {r['DS']:>4}  {r['predicted']:6}  "
            f"R{r['raise_pct']:5.1f}% C{r['call_pct']:5.1f}% F{r['fold_pct']:5.1f}%  "
            f"{r['verdict']}"
        )
    print(f"\n→ 保存: {out_json}")
    print(f"→ 保存: {OUT_DIR / 'table_v3.md'}")


if __name__ == "__main__":
    main()
