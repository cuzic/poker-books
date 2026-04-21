#!/usr/bin/env python3
"""Check the status of batch jobs for all books (or a specified book)."""

import json
import os
import sys
from pathlib import Path

try:
    from google import genai
except ImportError:
    print("Error: google-genai package not installed")
    print("Run: pip install google-genai")
    sys.exit(1)


BOOKS = ("preflop", "flop")
ROOT = Path(__file__).parent.parent


def check_one(client, book_id: str) -> None:
    job_file = ROOT / "dist" / book_id / "batch-job.json"
    if not job_file.exists():
        print(f"[{book_id}] batch-job.json not found, skipping.")
        return

    with open(job_file) as f:
        job_info = json.load(f)

    print(f"\n=== [{book_id}] {job_info['name']} ===")

    batch = client.batches.get(name=job_info["name"])
    print(f"Status: {batch.state.name}")
    if batch.create_time:
        print(f"Created: {batch.create_time}")
    if batch.update_time:
        print(f"Updated: {batch.update_time}")

    if hasattr(batch, "batch_stats") and batch.batch_stats:
        stats = batch.batch_stats
        print("Progress:")
        print(f"  Total  : {stats.total_count or 0}")
        print(f"  Success: {stats.success_count or 0}")
        print(f"  Failure: {stats.failure_count or 0}")

    state_name = batch.state.name
    if state_name == "JOB_STATE_SUCCEEDED":
        print(f"[{book_id}] ✅ completed")
        if hasattr(batch, "dest") and batch.dest and hasattr(batch.dest, "file_name"):
            print(f"Output file: {batch.dest.file_name}")
    elif state_name == "JOB_STATE_FAILED":
        print(f"[{book_id}] ❌ failed")
        if hasattr(batch, "error") and batch.error:
            print(f"Error: {batch.error}")
    else:
        print(f"[{book_id}] ⏳ still processing ({state_name})")

    job_info["state"] = state_name
    if hasattr(batch, "dest") and batch.dest and hasattr(batch.dest, "file_name"):
        job_info["outputFile"] = batch.dest.file_name
    with open(job_file, "w") as f:
        json.dump(job_info, f, indent=2)


def main() -> None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set")
        sys.exit(1)

    args = sys.argv[1:]
    target = "all"
    if "--book" in args:
        idx = args.index("--book")
        if idx + 1 < len(args) and args[idx + 1] in (*BOOKS, "all"):
            target = args[idx + 1]

    client = genai.Client(api_key=api_key)
    targets = list(BOOKS) if target == "all" else [target]
    for book_id in targets:
        check_one(client, book_id)


if __name__ == "__main__":
    main()
