#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""Fetch GTO Wizard solutions for spots listed in spots.csv.

Usage: uv run scripts/gto_wizard_study/fetch.py [--limit N] [--filter TOPIC]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN_FILE = SCRIPT_DIR / ".token"
SPOTS_CSV = SCRIPT_DIR / "spots.csv"
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study")

API = "https://api.gtowizard.com/v4/solutions/spot-solution/"


def headers(token: str) -> dict[str, str]:
    return {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token}",
        "origin": "https://app.gtowizard.com",
        "referer": "https://app.gtowizard.com/",
        "gwclientid": "930036c8-831c-4fca-8453-b0a298853e86",
        "user-agent": "Mozilla/5.0",
    }


def load_spots() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with SPOTS_CSV.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["id"].startswith("#"):
                continue
            rows.append(row)
    return rows


def fetch_one(client: httpx.Client, row: dict[str, str]) -> tuple[int, dict | None]:
    params = {
        "gametype": row["gametype"],
        "depth": row["depth"],
        "stacks": row["stacks"],
        "preflop_actions": row["preflop_actions"],
        "flop_actions": row["flop_actions"],
        "turn_actions": row["turn_actions"],
        "river_actions": row["river_actions"],
        "board": row["board"],
    }
    r = client.get(API, params=params, timeout=30.0)
    if r.status_code == 200:
        try:
            return 200, r.json()
        except Exception:
            return 200, None
    return r.status_code, None


def slim(data: dict) -> dict:
    """Strip extremely verbose fields for storage."""
    out = {
        "game": {
            "gametype": data.get("game", {}).get("gametype"),
            "pot": data.get("game", {}).get("pot"),
            "spr": data.get("game", {}).get("spr"),
        },
        "players_info": [],
        "action_solutions": [],
    }
    # players_info: keep position, stack, range summary
    for p in data.get("players_info", []) or []:
        pl = p.get("player", {})
        out["players_info"].append({
            "position": pl.get("position"),
            "stack": pl.get("stack"),
            "current_stack": pl.get("current_stack"),
            "is_hero": pl.get("is_hero"),
            "is_folded": pl.get("is_folded"),
            "relative_postflop_position": pl.get("relative_postflop_position"),
        })
    for a in data.get("action_solutions", []):
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
            "equity_buckets": a.get("equity_buckets"),
            "hand_categories": a.get("hand_categories"),
        })
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--filter", default=None, help="Substring match on topic")
    p.add_argument("--retry", action="store_true", help="Retry items that previously failed (no JSON)")
    args = p.parse_args()

    token = TOKEN_FILE.read_text().strip()
    spots = load_spots()
    if args.filter:
        spots = [s for s in spots if args.filter in s["topic"]]
    if args.limit:
        spots = spots[: args.limit]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log_path = OUT_DIR / "fetch_log.tsv"
    fetch_log: list[str] = []
    if log_path.exists():
        fetch_log = log_path.read_text().splitlines()

    ok = 0
    skip = 0
    err = 0
    started = time.time()

    with httpx.Client(headers=headers(token)) as client:
        for row in spots:
            spot_id = row["id"]
            topic = row["topic"]
            out_dir = OUT_DIR / topic
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{spot_id}.json"
            if out_path.exists() and not args.retry:
                skip += 1
                continue

            t0 = time.time()
            status, data = fetch_one(client, row)
            dt = (time.time() - t0) * 1000
            if status == 200 and data is not None:
                slim_data = slim(data)
                slim_data["_meta"] = {
                    "id": spot_id,
                    "topic": topic,
                    "note": row.get("note", ""),
                    "request": {
                        "gametype": row["gametype"],
                        "depth": row["depth"],
                        "stacks": row["stacks"],
                        "preflop_actions": row["preflop_actions"],
                        "flop_actions": row["flop_actions"],
                        "turn_actions": row["turn_actions"],
                        "river_actions": row["river_actions"],
                        "board": row["board"],
                    },
                }
                out_path.write_text(json.dumps(slim_data, ensure_ascii=False))
                ok += 1
                fetch_log.append(f"{spot_id}\t{topic}\t200\t{int(dt)}ms")
                print(f"OK   {spot_id:6s} {topic:24s} {int(dt)}ms", flush=True)
            else:
                err += 1
                fetch_log.append(f"{spot_id}\t{topic}\t{status}\t{int(dt)}ms")
                print(f"FAIL {spot_id:6s} {topic:24s} status={status} {int(dt)}ms", flush=True)

            # rate limit safety
            time.sleep(0.15)

    log_path.write_text("\n".join(fetch_log) + "\n")
    print(f"\nDone: ok={ok} skip={skip} err={err} in {time.time()-started:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
