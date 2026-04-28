#!/usr/bin/env python3
"""GTO Wizard ブログから取得した 3 ボード (QQ6, KJ7, QJT) を TexasSolver で solve.

既存の texassolver_accuracy_30.py のロジックを再利用。
結果は texassolver_accuracy_30.json と同じ format で
knowledges/volume4/results/texassolver_blog_3boards.json に出力。
"""
from __future__ import annotations
import json
import sys
import time
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

# 既存 30 ボードスクリプトから関数群を import
from texassolver_accuracy_30 import (  # noqa: E402
    build_config, run_solver, parse_ip_cbet, RESULTS_DIR
)

OUTPUT_FILE = RESULTS_DIR / "texassolver_blog_3boards.json"
DUMP_DIR = REPO / "knowledges/volume4/scenarios/flop_blog_3boards"
DUMP_DIR.mkdir(parents=True, exist_ok=True)

# GTO Wizard ブログから取った 3 ボード (BTN vs BB SRP 100bb cash)
# ref_cbet_pct = 公式記事の本文・画像 OCR 値
BOARDS = [
    # (board_spec, ref_cbet_pct, board_cards)
    ("QQ6",   82, "Qc,Qs,6d"),    # 81.9% (article 05)
    ("KJ7ss", 49, "Kh,Jh,7c"),    # 49.3% (article 05)
    ("QJTss", 47, "Qc,Jc,Td"),    # 47.3% (article 05)
]


def main():
    print(f"=== TexasSolver 追加 3 ボード solve ===", file=sys.stderr)
    results = []
    t_start = time.time()

    for board_spec, ref, board_cards in BOARDS:
        t0 = time.time()
        print(f"\n[{board_spec}] cards={board_cards} ref={ref}%", file=sys.stderr)

        dump_path = str(DUMP_DIR / f"flop_blog_{board_spec}.json")
        config = build_config(board_cards, dump_path)
        exploitability, rc = run_solver(config)
        elapsed = time.time() - t0

        if rc != 0:
            print(f"  ERROR rc={rc} ({elapsed:.0f}s)", file=sys.stderr)
            results.append({
                "board": board_spec, "board_cards": board_cards,
                "ref_cbet_pct": ref, "status": f"rc={rc}",
                "elapsed_sec": round(elapsed, 1),
            })
            continue

        if not Path(dump_path).exists():
            print(f"  ERROR no dump file ({elapsed:.0f}s)", file=sys.stderr)
            results.append({
                "board": board_spec, "board_cards": board_cards,
                "ref_cbet_pct": ref, "status": "no_dump",
                "elapsed_sec": round(elapsed, 1),
            })
            continue

        try:
            with open(dump_path) as f:
                dump = json.load(f)
            ts_cbet = parse_ip_cbet(dump)
        except Exception as e:
            print(f"  ERROR parse: {e}", file=sys.stderr)
            results.append({
                "board": board_spec, "board_cards": board_cards,
                "ref_cbet_pct": ref, "status": f"parse_error: {e}",
                "elapsed_sec": round(elapsed, 1),
            })
            continue

        err = ts_cbet - ref
        print(f"  TS={ts_cbet:.1f}%  err={err:+.1f}  expl={exploitability}  ({elapsed:.0f}s)",
              file=sys.stderr)
        results.append({
            "board": board_spec,
            "board_cards": board_cards,
            "ref_cbet_pct": ref,
            "solver_cbet_pct": round(ts_cbet, 1),
            "error": round(err, 1),
            "abs_error": round(abs(err), 1),
            "exploitability_pct": exploitability,
            "elapsed_sec": round(elapsed, 1),
            "status": "ok",
        })

    total_elapsed = time.time() - t_start
    output = {
        "summary": {
            "count": len(results),
            "valid_count": sum(1 for r in results if r.get("status") == "ok"),
            "total_elapsed_sec": round(total_elapsed, 1),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        },
        "metadata": {
            "solver": "TexasSolver",
            "scenario": "BTN vs BB SRP 100bb cash 6-max",
            "tree": "flop-only",
            "ip_flop_bets": "33,50,75,150 + allin",
            "oop_flop_bets": "60,100 + allin",
            "source": "GTO Wizard 公式ブログ記事 05 (CBet Sizing Mechanics)",
        },
        "results": results,
    }

    OUTPUT_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"\nWritten: {OUTPUT_FILE}", file=sys.stderr)
    print(f"Total: {total_elapsed:.0f}s", file=sys.stderr)


if __name__ == "__main__":
    main()
