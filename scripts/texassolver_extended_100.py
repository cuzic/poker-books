#!/usr/bin/env python3
"""補正テーブル学習用 100 ボード拡張サンプル.

既存 30 + Phase 1 の 3 ボードに、各型 N=5 を目指して追加する。
ref_cbet_pct は GTO Wizard を直接参照するか、後で UI 手動取得して埋める。
（GTO Wizard 契約が無い場合、ref は推定値・暫定値となる。
 推定値の場合は estimated=true を付ける。）

実行:
    python3 scripts/texassolver_extended_100.py [--dry-run]

注意: 一晩 (~5 時間) 走るので screen / nohup 推奨。
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from texassolver_accuracy_30 import (  # noqa: E402
    build_config, run_solver, parse_ip_cbet, RESULTS_DIR
)

OUTPUT_FILE = RESULTS_DIR / "texassolver_extended_100.json"
DUMP_DIR = REPO / "knowledges/volume4/scenarios/flop_extended_100"
DUMP_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 拡張 84 ボード (各型 N=5 を目指す)
# ref_cbet_pct: 既知の GTO Wizard 値があればその値、無ければ "?" (None) で
#               TexasSolver 値だけ取得 (補正学習に使うときは ref が要るため後で埋める)
# ---------------------------------------------------------------------------
BOARDS = [
    # 型 1a: high-dry-2tone (A/K/Q top, max_diff>=8, 2-tone) - need 4
    ("A92ss", None, "Ah,9h,2c"),
    ("K83ss", None, "Kh,8h,3c"),
    ("Q72ss", None, "Qh,7h,2c"),
    ("A53ss", None, "Ah,5h,3c"),

    # 型 1c: high-mid-rainbow (A/K/Q top, max_diff 5-7, rainbow) - need 5
    ("KJ7r",   49, "Kh,Jd,7c"),  # ref ≈ blog KJ7
    ("Q84r",  None, "Qh,8d,4c"),
    ("A95r",  None, "Ah,9d,5c"),
    ("K94r",  None, "Kh,9d,4c"),
    ("Q73r",  None, "Qh,7d,3c"),

    # 型 2a: high-mid-2tone - need 3
    ("KJ7ss", 49, "Kh,Jh,7c"),  # blog (Phase 1 と重複可)
    ("Q83ss_dup", None, "Qh,8h,3c"),  # 重複避け
    ("A85ss", None, "Ah,8h,5c"),

    # 型 2c: high-broadway-2tone - need 3
    ("KQJss", None, "Kh,Qh,Jc"),
    ("AKJss", None, "Ah,Kh,Jc"),
    ("AQJss", None, "Ah,Qh,Jc"),

    # 型 2c2: high-close-2tone (max_diff <= 4, top high) - need 5
    ("KJ9ss", None, "Kh,Jh,9c"),
    ("Q98ss", None, "Qh,9h,8c"),
    ("KT8ss", None, "Kh,Th,8c"),
    ("J98ss", None, "Jh,9h,8c"),
    ("Q97ss", None, "Qh,9h,7c"),

    # 型 2e: high-midT-rainbow (mid=T) - need 4
    ("KT3r",  None, "Kh,Td,3c"),
    ("AT4r",  None, "Ah,Td,4c"),
    ("QT2r",  None, "Qh,Td,2c"),
    ("AT7r",  None, "Ah,Td,7c"),

    # 型 2f: high-close-rainbow (max_diff<=4, A/K/Q top) - need 4
    ("Q97r",  None, "Qh,9d,7c"),
    ("KJ8r",  None, "Kh,Jd,8c"),
    ("AJ9r",  None, "Ah,Jd,9c"),
    ("Q86r",  None, "Qh,8d,6c"),

    # 型 3c: low-mid-2tone (J以下, max_diff 5-7, 2-tone) - need 5
    ("J52ss", None, "Jh,5h,2c"),
    ("T62ss", None, "Th,6h,2c"),
    ("J63ss", None, "Jh,6h,3c"),
    ("952ss", None, "9h,5h,2c"),
    ("T52ss", None, "Th,5h,2c"),

    # 型 3d: low-J/mid-rainbow - need 4
    ("J62r",  None, "Jh,6d,2c"),
    ("T63r",  None, "Th,6d,3c"),
    ("J42r",  None, "Jh,4d,2c"),
    ("J53r",  None, "Jh,5d,3c"),

    # 型 3e: low-other-rainbow (top<=9, max_diff>=8) - 困難 (ロー散開は少ない) - need 0-2
    # NOTE: top<=9 で max_diff>=8 は数学的にほぼ不可能 (8トップなら最大 8-2=6)
    # 削除

    # 型 4a: low-T/J-2tone - need 1
    ("T76ss", None, "Th,7h,6c"),

    # 型 4b: low-sub9-2tone - need 4
    ("865ss", None, "8h,6h,5c"),
    ("754ss", None, "7h,5h,4c"),
    ("976ss", None, "9h,7h,6c"),
    ("864ss", None, "8h,6h,4c"),

    # 型 4c: low-T-rainbow (T top close) - need 3
    ("T76r",  None, "Th,7d,6c"),
    ("T75r",  None, "Th,7d,5c"),
    ("T98r2", None, "Tc,9s,8h"),  # 異 suit pattern

    # 型 4d: low-sub9-rainbow - need 2
    ("864r",  None, "8h,6d,4c"),
    ("754r",  None, "7h,5d,4c"),

    # 型 5a: mono-broadway - need 4
    ("KQJmono", None, "Kh,Qh,Jh"),
    ("AKJmono", None, "Ah,Kh,Jh"),
    ("AQTmono", None, "Ah,Qh,Th"),
    ("KJTmono", None, "Kh,Jh,Th"),

    # 型 5b: mono-low - need 4
    ("J84mono", None, "Jh,8h,4h"),
    ("T75mono", None, "Th,7h,5h"),
    ("865mono", None, "8h,6h,5h"),
    ("754mono", None, "7h,5h,4h"),

    # 型 6a: paired-AA - need 4
    ("AAQ",   None, "Ah,As,Qd"),
    ("AAJ",   None, "Ah,As,Jd"),
    ("AA7",   None, "Ah,As,7d"),
    ("AA3",   None, "Ah,As,3d"),

    # 型 6b: paired-KK - need 4
    ("KKQ",   None, "Kh,Ks,Qd"),
    ("KKT",   None, "Kh,Ks,Td"),
    ("KK5",   None, "Kh,Ks,5d"),
    ("KK2",   None, "Kh,Ks,2d"),

    # 型 6c: paired-QQ - need 4 (QQ6 は Phase 1 で追加済)
    ("QQJ",   None, "Qh,Qs,Jd"),
    ("QQ8",   None, "Qh,Qs,8d"),
    ("QQ4",   None, "Qh,Qs,4d"),
    ("QQ2",   None, "Qh,Qs,2d"),

    # 型 6d: paired-low - need 4
    ("663",   None, "6h,6s,3d"),
    ("552",   None, "5h,5s,2d"),
    ("773",   None, "7h,7s,3d"),
    ("442",   None, "4h,4s,2d"),

    # 型 7a: AK-high-lowpair (A/K top + pair<=7) - need 4
    ("A77",   None, "Ah,7d,7s"),
    ("K77",   None, "Kh,7d,7s"),
    ("A55",   None, "Ah,5d,5s"),
    ("K55",   None, "Kh,5d,5s"),

    # 型 7b: AK-high-midpair (A/K top + pair 8-T) - need 4
    ("ATT",   None, "Ah,Td,Ts"),
    ("KTT",   None, "Kh,Td,Ts"),
    ("A88",   None, "Ah,8d,8s"),
    ("K88",   None, "Kh,8d,8s"),
]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="ボード一覧のみ出力")
    p.add_argument("--limit", type=int, default=None, help="実行ボード数を制限")
    args = p.parse_args()

    if args.dry_run:
        print(f"Total: {len(BOARDS)} boards")
        for spec, ref, cards in BOARDS:
            print(f"  {spec:<12} ref={ref or '?':<5} cards={cards}")
        return

    boards = BOARDS[:args.limit] if args.limit else BOARDS
    print(f"=== TexasSolver 拡張 {len(boards)} ボード solve ===", file=sys.stderr)
    results = []
    t_start = time.time()

    for i, (board_spec, ref, board_cards) in enumerate(boards, 1):
        t0 = time.time()
        print(f"\n[{i}/{len(boards)}] {board_spec} cards={board_cards}",
              file=sys.stderr)

        dump_path = str(DUMP_DIR / f"flop_ext_{board_spec}.json")
        config = build_config(board_cards, dump_path)
        exploitability, rc = run_solver(config)
        elapsed = time.time() - t0

        if rc != 0 or not Path(dump_path).exists():
            print(f"  ERROR rc={rc} ({elapsed:.0f}s)", file=sys.stderr)
            results.append({
                "board": board_spec, "board_cards": board_cards,
                "ref_cbet_pct": ref, "status": f"rc={rc}",
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
                "ref_cbet_pct": ref, "status": f"parse_error",
                "elapsed_sec": round(elapsed, 1),
            })
            continue

        rec = {
            "board": board_spec,
            "board_cards": board_cards,
            "solver_cbet_pct": round(ts_cbet, 1),
            "exploitability_pct": exploitability,
            "elapsed_sec": round(elapsed, 1),
            "status": "ok",
        }
        if ref is not None:
            rec["ref_cbet_pct"] = ref
            rec["error"] = round(ts_cbet - ref, 1)
            rec["abs_error"] = round(abs(ts_cbet - ref), 1)
            print(f"  TS={ts_cbet:.1f}% ref={ref}% err={rec['error']:+.1f} ({elapsed:.0f}s)",
                  file=sys.stderr)
        else:
            rec["ref_cbet_pct"] = None
            print(f"  TS={ts_cbet:.1f}% ref=? ({elapsed:.0f}s)",
                  file=sys.stderr)
        results.append(rec)

        # 定期的に保存 (途中中断対策)
        if i % 5 == 0:
            _save(results, t_start)

    _save(results, t_start)
    print(f"\nTotal: {(time.time() - t_start)/60:.1f} min", file=sys.stderr)


def _save(results, t_start):
    output = {
        "summary": {
            "count": len(results),
            "valid_count": sum(1 for r in results if r.get("status") == "ok"),
            "with_ref": sum(1 for r in results if r.get("ref_cbet_pct") is not None),
            "total_elapsed_sec": round(time.time() - t_start, 1),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        },
        "metadata": {
            "solver": "TexasSolver",
            "scenario": "BTN vs BB SRP 100bb cash 6-max",
            "tree": "flop-only",
            "purpose": "type-balanced 補正テーブル学習データ拡張",
        },
        "results": results,
    }
    OUTPUT_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
