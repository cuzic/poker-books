#!/usr/bin/env python3
"""
後手スコア 20-case 再検証スクリプト（C=4/6 修正後）
Task #124

phase1 の defender_summary.csv を読み込み、修正後 C 値で DS を再計算して
GTO 実測と照合する。

出力: knowledges/volume4/results/ds_framework_recheck/result.json
       knowledges/volume4/results/ds_framework_recheck/table.md
"""
from __future__ import annotations
import csv
import json
from pathlib import Path

REPO = Path("/home/cuzic/poker-books")
PHASE1 = REPO / "knowledges/volume4/results/phase1"
OUT_DIR = REPO / "knowledges/volume4/results/ds_framework_recheck"

# 修正済み C 係数
C_TABLE = {33: 3, 50: 4, 75: 6}

# ボード設定
BOARDS = [
    ("kc7d2s", "K72r", 3),   # ドライ
    ("khjd7s", "KJ7r", 2),   # セミウェット
    ("th9d8c", "T98r", 1),   # ウェット
]

# 代表 HandScore（旧ドキュメントと同じ）
# DS = HS + A - 3 - C
# H3=17: ほぼ TPTK / 強目ハンドの平均
# H2=11: TPMK / FD など中堅の平均
# H1=4:  ボトムペア / BDFD など弱ハンドの平均
HS_REP = {"H3": 17, "H2": 11, "H1": 4}


def predict(ds: int) -> str:
    if ds >= 8:
        return "raise"
    elif ds >= 0:
        return "call"
    else:
        return "fold"


def verdict(predicted: str, row: dict) -> str:
    raise_pct = float(row["raise_pct"])
    call_pct  = float(row["call_pct"])
    fold_pct  = float(row["fold_pct"])
    dominant = max(raise_pct, call_pct, fold_pct)
    actual = (
        "raise" if raise_pct == dominant else
        "call"  if call_pct  == dominant else
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

    for dir_name, board_label, a_val in BOARDS:
        csv_path = PHASE1 / dir_name / "defender_summary.csv"
        # CSV header: board,bet_pct,bucket,n,fold_pct,call_pct,raise_pct
        # But board "Kc,7d,2s" is stored as 3 separate comma-delimited fields,
        # so effective columns are: card0,card1,card2,bet_pct,bucket,n,fold_pct,call_pct,raise_pct
        FIELDNAMES = ["c0","c1","c2","bet_pct","bucket","n","fold_pct","call_pct","raise_pct"]
        with open(csv_path) as f:
            next(f)  # skip header
            reader = csv.DictReader(f, fieldnames=FIELDNAMES)
            for row in reader:
                bet_pct = int(row["bet_pct"])
                bucket  = row["bucket"].strip()
                c_val   = C_TABLE[bet_pct]
                hs      = HS_REP[bucket]
                ds      = hs + a_val - 3 - c_val
                pred    = predict(ds)
                v       = verdict(pred, row)
                rows_all.append({
                    "board":     board_label,
                    "A":         a_val,
                    "size":      f"{bet_pct}%",
                    "C":         c_val,
                    "bucket":    bucket,
                    "HS_rep":    hs,
                    "DS":        ds,
                    "predicted": pred,
                    "raise_pct": round(float(row["raise_pct"]), 1),
                    "call_pct":  round(float(row["call_pct"]),  1),
                    "fold_pct":  round(float(row["fold_pct"]),  1),
                    "verdict":   v,
                })

    total    = len(rows_all)
    correct  = sum(1 for r in rows_all if r["verdict"] == "✓")
    boundary = sum(1 for r in rows_all if "境界" in r["verdict"])
    wrong    = sum(1 for r in rows_all if r["verdict"] == "✗")

    # JSON 保存
    result = {
        "summary": {
            "total": total,
            "correct": correct,
            "boundary": boundary,
            "wrong": wrong,
            "match_rate": round(correct / total * 100, 1),
            "match_rate_incl_boundary": round((correct + boundary) / total * 100, 1),
        },
        "rows": rows_all,
    }
    out_json = OUT_DIR / "result.json"
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    # Markdown テーブル保存
    lines = [
        "# 後手スコア 20-case 再検証（C=4/6 修正後）",
        "",
        f"検証日: 2026-05-01 / C 値: 33%→3, 50%→4, 75%→6",
        "",
        f"**一致率: {correct}/{total} = {correct/total*100:.1f}%**"
        f"（△境界含む: {(correct+boundary)/total*100:.1f}%）",
        "",
        "| ボード | A | サイズ | C | バケツ | HS代表 | DS | 予測 | 実測(R/C/F%) | 判定 |",
        "|--------|---|--------|---|--------|--------|----|----|---|---|",
    ]
    for r in rows_all:
        actual_str = f"{r['raise_pct']}/{r['call_pct']}/{r['fold_pct']}"
        lines.append(
            f"| {r['board']} | {r['A']} | {r['size']} | {r['C']} "
            f"| {r['bucket']} | {r['HS_rep']} | {r['DS']} "
            f"| {r['predicted']} | {actual_str} | {r['verdict']} |"
        )

    lines += [
        "",
        "## 境界・不一致ケースの解釈",
        "",
    ]
    for r in rows_all:
        if r["verdict"] != "✓":
            lines.append(
                f"- **{r['board']} {r['size']} {r['bucket']}**: DS={r['DS']} → 予測 {r['predicted']}, "
                f"実測 R{r['raise_pct']}%/C{r['call_pct']}%/F{r['fold_pct']}%"
            )

    (OUT_DIR / "table.md").write_text("\n".join(lines) + "\n")

    # stdout サマリー
    print(f"ボード×サイズ×バケツ 計 {total} ケース")
    print(f"一致: {correct} ({correct/total*100:.1f}%)")
    print(f"境界: {boundary}")
    print(f"不一致: {wrong}")
    print()
    header = f"{'ボード':6} {'A':2} {'サイズ':5} {'C':2} {'バケツ':4} {'DS':>4}  {'予測':8}  実測(Raise/Call/Fold)  判定"
    print(header)
    print("-" * len(header))
    for r in rows_all:
        print(
            f"{r['board']:6} {r['A']:2} {r['size']:5} {r['C']:2} {r['bucket']:4} "
            f"{r['DS']:>4}  {r['predicted']:8}  "
            f"R{r['raise_pct']:5.1f}% C{r['call_pct']:5.1f}% F{r['fold_pct']:5.1f}%  {r['verdict']}"
        )
    print(f"\n→ 保存: {out_json}")
    print(f"→ 保存: {OUT_DIR / 'table.md'}")


if __name__ == "__main__":
    main()
