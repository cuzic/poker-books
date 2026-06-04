#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""Re-fetch GTO Wizard spots that lost per-combo `strategy` to fetch_smart.py's slim().

Only refetches spots whose JSON either:
  - doesn't exist in knowledges/gto_wizard_study/<topic>/<id>.json, OR
  - exists but action_solutions[*].strategy is all empty arrays.

Spots are pulled from all spots*.csv files under scripts/gto_wizard_study/.

Usage:
  uv run scripts/three_class_model/refetch_strategy.py [--limit N] [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import httpx

ROOT = Path("/home/cuzic/poker-books")
SCR = ROOT / "scripts" / "gto_wizard_study"
OUT = ROOT / "knowledges" / "gto_wizard_study"
TOKEN_FILE = SCR / ".token"
ANAL_FILE = SCR / ".google_anal_id"

API = "https://api.gtowizard.com/v4/solutions/spot-solution/"


def headers(token: str, anal_id: str) -> dict:
    return {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token}",
        "google-anal-id": anal_id,
        "origin": "https://app.gtowizard.com",
        "referer": "https://app.gtowizard.com/",
        "gwclientid": "930036c8-831c-4fca-8453-b0a298853e86",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
    }


def load_all_spots() -> list[dict]:
    rows = []
    for f in sorted(SCR.glob("spots*.csv")):
        with f.open() as fh:
            for row in csv.DictReader(fh):
                if row["id"].startswith("#"):
                    continue
                rows.append(row)
    # dedup by id (keep first occurrence)
    seen = set()
    out = []
    for r in rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        out.append(r)
    return out


def find_existing_path(spot_id: str) -> Path | None:
    """Find existing JSON file in any topic subdir."""
    for p in OUT.glob(f"**/{spot_id}.json"):
        return p
    # also try variants
    for p in OUT.glob(f"**/*{spot_id}*.json"):
        return p
    return None


def has_strategy(path: Path) -> bool:
    try:
        d = json.loads(path.read_text())
    except Exception:
        return False
    for a in d.get("action_solutions") or []:
        if a.get("strategy"):
            return True
    return False


def slim_keep_strategy(data: dict) -> dict:
    """Like fetch.py's slim() — keeps strategy/evs/hand_categories etc."""
    out = {
        "game": {
            "gametype": data.get("game", {}).get("gametype"),
            "pot": data.get("game", {}).get("pot"),
            "spr": data.get("game", {}).get("spr"),
        },
        "players_info": [],
        "action_solutions": [],
        "hand_categories_range": data.get("hand_categories_range"),
        "draw_categories_range": data.get("draw_categories_range"),
    }
    for p in data.get("players_info", []) or []:
        pl = p.get("player", {}) if isinstance(p.get("player"), dict) else p
        out["players_info"].append({
            "position": pl.get("position"),
            "stack": pl.get("stack"),
            "current_stack": pl.get("current_stack"),
            "is_hero": pl.get("is_hero"),
            "is_folded": pl.get("is_folded"),
            "relative_postflop_position": pl.get("relative_postflop_position"),
        })
    for a in data.get("action_solutions", []) or []:
        ac = a.get("action", {})
        out["action_solutions"].append({
            "action": {
                "code": ac.get("code"),
                "type": ac.get("type"),
                "betsize": ac.get("betsize"),
                "position": ac.get("position"),
                "betsize_by_pot": ac.get("betsize_by_pot"),
                "display_name": ac.get("display_name"),
                "next_position": ac.get("next_position"),
            },
            "total_frequency": a.get("total_frequency"),
            "total_combos": a.get("total_combos"),
            "total_ev": a.get("total_ev"),
            "strategy": a.get("strategy"),
            "evs": a.get("evs"),
            "hand_categories": a.get("hand_categories"),
            "draw_categories": a.get("draw_categories"),
        })
    return out


def _clean_actions(s: str) -> str:
    """Strip trailing/leading dashes from action strings — API rejects 'X-'."""
    return (s or "").strip().strip("-")


def get_request_params(row: dict, existing_path: Path | None) -> dict | None:
    """Build query params. Prefer existing JSON's _meta.request (already resolved)
    over raw CSV row (which may contain placeholders like 'Rcbet')."""
    if existing_path and existing_path.exists():
        try:
            d = json.loads(existing_path.read_text())
            req = (d.get("_meta") or {}).get("request") or {}
            if req.get("board"):
                return {
                    "gametype": req.get("gametype", row.get("gametype", "")),
                    "depth": str(req.get("depth", row.get("depth", ""))),
                    "stacks": req.get("stacks", row.get("stacks", "")),
                    "preflop_actions": _clean_actions(req.get("preflop_actions", "")),
                    "flop_actions": _clean_actions(req.get("flop_actions", "")),
                    "turn_actions": _clean_actions(req.get("turn_actions", "")),
                    "river_actions": _clean_actions(req.get("river_actions", "")),
                    "board": req["board"],
                }
        except Exception:
            pass
    # Fallback: use CSV row directly (only works for CSVs with explicit action fields)
    if not row.get("board") or "preflop_actions" not in row:
        return None
    return {
        "gametype": row["gametype"],
        "depth": row["depth"],
        "stacks": row["stacks"],
        "preflop_actions": _clean_actions(row.get("preflop_actions", "")),
        "flop_actions": _clean_actions(row.get("flop_actions", "")),
        "turn_actions": _clean_actions(row.get("turn_actions", "")),
        "river_actions": _clean_actions(row.get("river_actions", "")),
        "board": row["board"],
    }


def fetch_one(client: httpx.Client, params: dict) -> tuple[int, dict | None]:
    r = client.get(API, params=params, timeout=30.0)
    if r.status_code == 200:
        try:
            return 200, r.json()
        except Exception:
            return 200, None
    return r.status_code, None


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--sleep", type=float, default=0.5, help="seconds between API calls")
    args = p.parse_args()

    if not TOKEN_FILE.exists():
        print("Token file missing:", TOKEN_FILE, file=sys.stderr)
        return 1
    if not ANAL_FILE.exists():
        print("google-anal-id file missing:", ANAL_FILE, file=sys.stderr)
        return 1
    token = TOKEN_FILE.read_text().strip()
    anal_id = ANAL_FILE.read_text().strip()

    spots = load_all_spots()
    # Filter: only spots that need (re)fetching, build query params now
    todo = []
    skipped_no_params = 0
    for row in spots:
        existing = find_existing_path(row["id"])
        if existing and has_strategy(existing):
            continue
        topic = row["topic"]
        path = existing or (OUT / topic / f"{row['id']}.json")
        params = get_request_params(row, existing)
        if not params:
            skipped_no_params += 1
            continue
        todo.append((row, path, params))
    if skipped_no_params:
        print(f"Skipped {skipped_no_params} spots — no resolvable params (placeholder line, never fetched)")

    if args.limit:
        todo = todo[: args.limit]

    print(f"Spots needing refetch: {len(todo)}")
    if args.dry_run:
        for row, path, params in todo[:10]:
            print(f"  would fetch: {row['id']} board={params['board']} preflop={params['preflop_actions']!r}")
        if len(todo) > 10:
            print(f"  ... and {len(todo)-10} more")
        return 0

    ok = 0
    err = 0
    status_counts: dict[int, int] = {}
    with httpx.Client(headers=headers(token, anal_id)) as client:
        for i, (row, path, params) in enumerate(todo, 1):
            status, data = fetch_one(client, params)
            status_counts[status] = status_counts.get(status, 0) + 1
            if status == 200 and data:
                path.parent.mkdir(parents=True, exist_ok=True)
                slim = slim_keep_strategy(data)
                slim["_meta"] = {
                    "id": row["id"],
                    "topic": row["topic"],
                    "note": row.get("note", ""),
                    "request": params,
                }
                path.write_text(json.dumps(slim, ensure_ascii=False))
                ok += 1
            else:
                err += 1
            if i % 25 == 0:
                print(f"progress: {i}/{len(todo)} ok={ok} err={err} status_counts={status_counts}")
            time.sleep(args.sleep)

    print(f"Done: ok={ok} err={err} status_counts={status_counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
