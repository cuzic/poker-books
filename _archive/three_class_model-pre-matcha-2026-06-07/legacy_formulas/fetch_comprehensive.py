#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""Comprehensive GTO Wizard fetcher — preserves ALL rich fields.

Stores per spot:
- All per-combo: strategy[i], evs[i]
- Per-MV bucket: hand_categories[].{total_combos, total_frequency,
                                    actions_total_combos, actions_total_frequencies}
- Per-DV bucket: same as above
- Per-equity bucket (when available, MTT only): equity_buckets[]
- Range-wide: hand_categories_range[], draw_categories_range[]
- Blockers: blocker_rate, unblocker_rate, blockers_frequencies
- Game: spr, pot
- Per-action: betsize_by_pot, total_ev

Output dir: knowledges/gto_wizard_full/<topic>/<id>.json
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
OUT = ROOT / "knowledges" / "gto_wizard_full"
TOKEN_FILE = SCR / ".token"
ANAL_FILE = SCR / ".google_anal_id"
REFRESH_FILE = SCR / ".refresh_token"
EXISTING_DIR = ROOT / "knowledges" / "gto_wizard_study"

API = "https://api.gtowizard.com/v4/solutions/spot-solution/"
REFRESH_API = "https://api.gtowizard.com/v1/token/refresh/"


def refresh_access_token(refresh_token: str, anal_id: str | None = None) -> str | None:
    """Call refresh endpoint to get a fresh access token. anal_id ignored (anti-bot)."""
    try:
        with httpx.Client(timeout=15.0) as c:
            r = c.post(
                REFRESH_API,
                headers={
                    "accept": "application/json, text/plain, */*",
                    "content-type": "application/json",
                    "gwclientid": "930036c8-831c-4fca-8453-b0a298853e86",
                    "origin": "https://app.gtowizard.com",
                    "referer": "https://app.gtowizard.com/",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
                },
                json={"refresh": refresh_token},
            )
            if r.status_code == 200:
                tok = r.json().get("access")
                if tok:
                    TOKEN_FILE.write_text(tok + "\n")
                    print(f"[token-refresh] OK new token len={len(tok)}", file=sys.stderr)
                    return tok
            print(f"[token-refresh] FAIL status={r.status_code}", file=sys.stderr)
    except Exception as e:
        print(f"[token-refresh] EXC {e!r}", file=sys.stderr)
    return None


def headers(token: str, anal_id: str | None = None) -> dict:
    """Note: google-anal-id is OMITTED — it's anti-bot detection that gets stale.
    Without it, the API accepts any valid Bearer token."""
    h = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token}",
        "origin": "https://app.gtowizard.com",
        "referer": "https://app.gtowizard.com/",
        "gwclientid": "930036c8-831c-4fca-8453-b0a298853e86",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
    }
    # Don't include google-anal-id (anti-bot, becomes stale)
    return h


def _clean(s: str) -> str:
    return (s or "").strip().strip("-")


def load_all_spots() -> list[dict]:
    rows = []
    for f in sorted(SCR.glob("spots*.csv")):
        with f.open() as fh:
            for row in csv.DictReader(fh):
                if row["id"].startswith("#"):
                    continue
                rows.append(row)
    # dedup by id
    seen = set()
    out = []
    for r in rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        out.append(r)
    return out


def get_request_params(row: dict) -> dict | None:
    """Prefer params from existing knowledges/gto_wizard_study/.../{id}.json
    (auto-resolved), fall back to CSV row."""
    spot_id = row["id"]
    existing = None
    for p in EXISTING_DIR.glob(f"**/{spot_id}.json"):
        existing = p
        break
    if existing:
        try:
            d = json.loads(existing.read_text())
            req = (d.get("_meta") or {}).get("request") or {}
            if req.get("board"):
                return {
                    "gametype": req.get("gametype", row.get("gametype", "")),
                    "depth": str(req.get("depth", row.get("depth", ""))),
                    "stacks": req.get("stacks", row.get("stacks", "")),
                    "preflop_actions": _clean(req.get("preflop_actions", "")),
                    "flop_actions": _clean(req.get("flop_actions", "")),
                    "turn_actions": _clean(req.get("turn_actions", "")),
                    "river_actions": _clean(req.get("river_actions", "")),
                    "board": req["board"],
                }
        except Exception:
            pass
    if not row.get("board") or "preflop_actions" not in row:
        return None
    return {
        "gametype": row["gametype"],
        "depth": row["depth"],
        "stacks": row["stacks"],
        "preflop_actions": _clean(row.get("preflop_actions", "")),
        "flop_actions": _clean(row.get("flop_actions", "")),
        "turn_actions": _clean(row.get("turn_actions", "")),
        "river_actions": _clean(row.get("river_actions", "")),
        "board": row["board"],
    }


def slim_full(data: dict) -> dict:
    """Keep ALL fields that matter for analysis. Drop only the unused noise."""
    out = {
        "game": data.get("game"),
        "players_info": [],
        "action_solutions": [],
        "hand_categories_range": data.get("hand_categories_range"),
        "draw_categories_range": data.get("draw_categories_range"),
        "blocker_rate": data.get("blocker_rate"),
        "unblocker_rate": data.get("unblocker_rate"),
        "blockers_frequencies": data.get("blockers_frequencies"),
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
        out["action_solutions"].append({
            "action": a.get("action"),  # full action dict (code, type, betsize, betsize_by_pot, etc)
            "total_frequency": a.get("total_frequency"),
            "total_combos": a.get("total_combos"),
            "total_ev": a.get("total_ev"),
            "strategy": a.get("strategy"),
            "evs": a.get("evs"),
            "hand_categories": a.get("hand_categories"),
            "draw_categories": a.get("draw_categories"),
            "equity_buckets": a.get("equity_buckets"),
        })
    return out


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
    p.add_argument("--sleep", type=float, default=0.3)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true", help="re-fetch even if comprehensive file exists")
    p.add_argument("--filter-topic", default=None)
    args = p.parse_args()

    if not TOKEN_FILE.exists() or not ANAL_FILE.exists():
        print("Missing .token or .google_anal_id", file=sys.stderr)
        return 1
    token = TOKEN_FILE.read_text().strip()
    anal_id = ANAL_FILE.read_text().strip()

    spots = load_all_spots()
    if args.filter_topic:
        spots = [r for r in spots if args.filter_topic in r.get("topic", "")]

    OUT.mkdir(parents=True, exist_ok=True)

    todo = []
    skipped = 0
    for row in spots:
        topic = row["topic"]
        target = OUT / topic / f"{row['id']}.json"
        if target.exists() and not args.force:
            skipped += 1
            continue
        params = get_request_params(row)
        if not params:
            continue
        todo.append((row, target, params))

    if args.limit:
        todo = todo[: args.limit]

    print(f"Todo: {len(todo)} spots (skipped {skipped} already comprehensive)")
    if args.dry_run:
        for row, target, params in todo[:5]:
            print(f"  → {target} board={params['board']}")
        return 0

    # Load refresh token if available
    refresh_token = REFRESH_FILE.read_text().strip() if REFRESH_FILE.exists() else None
    consecutive_401 = 0
    consecutive_429 = 0

    ok = 0
    err = 0
    eq_buckets_count = 0
    status_counts: dict = {}
    client = httpx.Client(headers=headers(token, anal_id))
    try:
        i = 0
        while i < len(todo):
            row, target, params = todo[i]
            status, data = fetch_one(client, params)
            status_counts[status] = status_counts.get(status, 0) + 1

            # ── Auto-refresh on 401 ──
            if status == 401 and refresh_token:
                consecutive_401 += 1
                if consecutive_401 == 1:  # first 401 → try refresh
                    new_tok = refresh_access_token(refresh_token, anal_id)
                    if new_tok:
                        token = new_tok
                        client.close()
                        client = httpx.Client(headers=headers(token, anal_id))
                        continue  # retry this spot
                    # refresh failed: abort
                    print(f"[abort] refresh failed at spot {i+1}/{len(todo)}", file=sys.stderr)
                    break
                # already tried refresh once, still 401 → abort
                print(f"[abort] 401 after refresh, aborting at {i+1}/{len(todo)}", file=sys.stderr)
                break

            # Reset 401 counter on non-401
            if status != 401:
                consecutive_401 = 0

            # ── Back-off on 429 ──
            if status == 429:
                consecutive_429 += 1
                backoff = min(2 ** min(consecutive_429, 6), 60)
                print(f"[429] backoff {backoff}s (consecutive={consecutive_429})", file=sys.stderr)
                time.sleep(backoff)
                continue  # retry this spot
            else:
                consecutive_429 = 0

            if status == 200 and data:
                target.parent.mkdir(parents=True, exist_ok=True)
                slim = slim_full(data)
                slim["_meta"] = {
                    "id": row["id"],
                    "topic": row["topic"],
                    "note": row.get("note", ""),
                    "request": params,
                }
                target.write_text(json.dumps(slim, ensure_ascii=False))
                if any("equity_buckets" in a and a["equity_buckets"] for a in slim["action_solutions"]):
                    eq_buckets_count += 1
                ok += 1
            else:
                err += 1
            i += 1
            if i % 25 == 0:
                print(f"progress: {i}/{len(todo)} ok={ok} err={err} eq_buckets={eq_buckets_count} status={status_counts}")
            time.sleep(args.sleep)
    finally:
        client.close()

    print(f"Done: ok={ok} err={err} eq_buckets_count={eq_buckets_count} status={status_counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
