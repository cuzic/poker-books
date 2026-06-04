#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""Smart GTO Wizard fetcher with automatic bet-size discovery.

Spots are described declaratively. Bet sizes in flop_actions/turn_actions/river_actions
that start with "R?" or "R??" are auto-resolved by querying the preceding spot.

CSV format:
  id,topic,gametype,depth,stacks,line,target_board,note

  Where `line` is `pre/flop/turn/river` separated by /:
    F-R2.2-F-F-F-C / X-Rcbet-C / X-X / -
  - "Rcbet" auto-resolves to the dominant raise code at that point
  - "X-X" etc means both players check
  - "-" means we want the response at the next decision

Output: knowledges/gto_wizard_study/<topic>/<id>.json
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
REFRESH_TOKEN_FILE = SCRIPT_DIR / ".refresh_token"
GOOGLE_ANAL_ID_FILE = SCRIPT_DIR / ".google_anal_id"
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study")

API = "https://api.gtowizard.com/v4/solutions/spot-solution/"
REFRESH_API = "https://api.gtowizard.com/v1/token/refresh/"


def refresh_access_token() -> str | None:
    """Use the long-lived refresh token to get a new access token."""
    if not REFRESH_TOKEN_FILE.exists():
        return None
    refresh = REFRESH_TOKEN_FILE.read_text().strip()
    google_anal = GOOGLE_ANAL_ID_FILE.read_text().strip() if GOOGLE_ANAL_ID_FILE.exists() else ""
    try:
        r = httpx.post(
            REFRESH_API,
            json={"refresh": refresh},
            headers={
                "accept": "application/json, text/plain, */*",
                "content-type": "application/json",
                "gwclientid": "930036c8-831c-4fca-8453-b0a298853e86",
                "google-anal-id": google_anal,
                "origin": "https://app.gtowizard.com",
                "referer": "https://app.gtowizard.com/",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
            },
            timeout=15.0,
        )
        if r.status_code == 200:
            access = r.json().get("access")
            if access:
                TOKEN_FILE.write_text(access)
                return access
    except Exception:
        pass
    return None

# Known sizes (for caching/fallback) — discovered earlier
SIZE_HINTS = {
    "HJ_open": "R2.2",
    "CO_open": "R2.4",
    "BTN_open": "R2.6",
    "UTG_open": "R2.2",
    "SB_open": "R4",
    "BB_3bet_vs_HJ": "R13.2",
    "BB_3bet_vs_CO": "R14.4",
    "BB_3bet_vs_BTN": "R13.65",
    "BB_3bet_vs_SB": "R14",
}


def headers(token: str) -> dict[str, str]:
    return {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token}",
        "origin": "https://app.gtowizard.com",
        "referer": "https://app.gtowizard.com/",
        "gwclientid": "930036c8-831c-4fca-8453-b0a298853e86",
        "user-agent": "Mozilla/5.0",
    }


def call_api(client: httpx.Client, params: dict, max_retries: int = 5) -> tuple[int, dict | None]:
    """Call API with 429 backoff retry and 401 auto-refresh."""
    backoff = 2.0
    for _ in range(max_retries):
        try:
            r = client.get(API, params=params, timeout=30.0)
            if r.status_code == 200:
                return 200, r.json()
            if r.status_code == 401:
                # Token expired — refresh and update client headers
                new_token = refresh_access_token()
                if new_token:
                    client.headers["authorization"] = f"Bearer {new_token}"
                    continue
                return 401, None
            if r.status_code == 429:
                time.sleep(backoff)
                backoff *= 2
                continue
            return r.status_code, None
        except Exception:
            time.sleep(backoff)
            backoff *= 2
    return 429, None


def split_line(line: str) -> tuple[str, str, str, str]:
    parts = [p.strip() for p in line.split("/")]
    while len(parts) < 4:
        parts.append("")
    pre, flop, turn, river = parts[:4]
    pre = "" if pre in ("-", "") else pre
    flop = "" if flop in ("-", "") else flop
    turn = "" if turn in ("-", "") else turn
    river = "" if river in ("-", "") else river
    return pre, flop, turn, river


def board_for_street(board: str, street: int) -> str:
    """Truncate board for given street index (0=preflop, 1=flop, 2=turn, 3=river)."""
    if street == 0:
        return ""
    if street == 1:
        return board[:6]
    if street == 2:
        return board[:8]
    return board[:10]


def get_dominant_raise_code(actions: list[dict]) -> str | None:
    """Find the highest-freq RAISE/BET action code."""
    raises = [a for a in actions if a["action"]["type"] in ("RAISE", "BET")]
    if not raises:
        return None
    raises.sort(key=lambda a: -a["total_frequency"])
    return raises[0]["action"]["code"]


def resolve_line(client: httpx.Client, gametype: str, depth: str, stacks: str,
                 line: str, board: str) -> tuple[str | None, list[str]]:
    """Replace placeholders like Rcbet, Rbarrel, R? with discovered codes.
    Returns (resolved_line, errors)."""
    pre, flop, turn, river = split_line(line)
    streets = [pre, flop, turn, river]
    errors = []

    for idx, street in enumerate(streets):
        if not street:
            continue
        if "R?" in street or "Rcbet" in street or "Rbarrel" in street or "Rraise" in street:
            # We need to discover this size by querying the prefix
            # Reconstruct prefix line up to (but not including) the placeholder
            actions = street.split("-")
            for j, act in enumerate(actions):
                if act in ("R?", "Rcbet", "Rbarrel", "Rraise"):
                    # Build prefix
                    new_street = "-".join(actions[:j])
                    prefix_streets = streets[:idx] + [new_street]
                    # If we have nothing in this street yet, query previous board level
                    # We're asking: "after these actions, what does next player do?"
                    params = {
                        "gametype": gametype, "depth": depth, "stacks": stacks,
                        "preflop_actions": prefix_streets[0] if len(prefix_streets) > 0 else "",
                        "flop_actions": prefix_streets[1] if len(prefix_streets) > 1 else "",
                        "turn_actions": prefix_streets[2] if len(prefix_streets) > 2 else "",
                        "river_actions": "",
                        "board": board_for_street(board, idx),
                    }
                    status, data = call_api(client, params)
                    if status != 200 or not data:
                        errors.append(f"size-probe failed at street={idx} pos={j} status={status}")
                        return None, errors
                    code = get_dominant_raise_code(data["action_solutions"])
                    if not code:
                        errors.append(f"no raise action at street={idx} pos={j}")
                        return None, errors
                    actions[j] = code
                    time.sleep(0.1)
            streets[idx] = "-".join(actions)

    return "/".join(streets), errors


def slim(data: dict) -> dict:
    out = {
        "action_solutions": [],
    }
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
            },
            "total_frequency": a.get("total_frequency"),
            "total_combos": a.get("total_combos"),
        })
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("csv", help="Path to spots CSV")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--filter", default=None)
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    token = TOKEN_FILE.read_text().strip()
    rows = []
    with open(args.csv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["id"].startswith("#"):
                continue
            rows.append(row)

    if args.filter:
        rows = [r for r in rows if args.filter in r["topic"]]
    if args.limit:
        rows = rows[: args.limit]

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    ok = 0
    skip = 0
    err = 0
    started = time.time()
    log_lines = []

    with httpx.Client(headers=headers(token)) as client:
        for row in rows:
            spot_id = row["id"]
            topic = row["topic"]
            out_dir = OUT_DIR / topic
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{spot_id}.json"
            if out_path.exists() and not args.force:
                skip += 1
                continue

            t0 = time.time()
            # Resolve placeholders
            resolved_line, errs = resolve_line(
                client, row["gametype"], row["depth"], row["stacks"],
                row["line"], row["target_board"]
            )
            if not resolved_line:
                print(f"FAIL {spot_id:8s} {topic:28s} resolve_fail: {errs}", flush=True)
                log_lines.append(f"{spot_id}\t{topic}\tresolve_fail\t{int((time.time()-t0)*1000)}ms")
                err += 1
                continue

            pre, flop, turn, river = split_line(resolved_line)
            # Determine target street: deepest non-empty
            street = 0
            if pre: street = 0
            if flop: street = 1
            if turn: street = 2
            if river: street = 3
            target_street = street
            # Actually, target is one step deeper than the deepest provided action
            # if board has more cards than that
            # Simpler: send all provided actions, send board matching the request
            # Board to send: based on what we're asking
            params = {
                "gametype": row["gametype"],
                "depth": row["depth"],
                "stacks": row["stacks"],
                "preflop_actions": pre,
                "flop_actions": flop,
                "turn_actions": turn,
                "river_actions": river,
                "board": row["target_board"],
            }
            status, data = call_api(client, params)
            dt = (time.time() - t0) * 1000

            if status == 200 and data is not None:
                slim_data = slim(data)
                slim_data["_meta"] = {
                    "id": spot_id,
                    "topic": topic,
                    "note": row.get("note", ""),
                    "request": {**params, "resolved_line": resolved_line, "original_line": row["line"]},
                }
                out_path.write_text(json.dumps(slim_data, ensure_ascii=False))
                ok += 1
                log_lines.append(f"{spot_id}\t{topic}\t200\t{int(dt)}ms")
                print(f"OK   {spot_id:8s} {topic:28s} {int(dt)}ms  resolved={resolved_line}", flush=True)
            else:
                err += 1
                log_lines.append(f"{spot_id}\t{topic}\t{status}\t{int(dt)}ms")
                print(f"FAIL {spot_id:8s} {topic:28s} status={status} {int(dt)}ms resolved={resolved_line}", flush=True)

            time.sleep(0.5)

    log_path = OUT_DIR / "fetch_boundary_log.tsv"
    log_path.write_text("\n".join(log_lines) + "\n")
    print(f"\nDone: ok={ok} skip={skip} err={err} in {time.time()-started:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
