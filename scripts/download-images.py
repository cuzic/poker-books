#!/usr/bin/env python3
"""Download images from completed batch jobs (per-book)."""

import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

try:
    from google import genai
except ImportError:
    print("Error: google-genai package not installed")
    print("Run: pip install google-genai")
    sys.exit(1)


BOOKS = ("preflop", "flop")
ROOT = Path(__file__).parent.parent


def download_for_book(client, api_key: str, book_id: str) -> None:
    job_file = ROOT / "dist" / book_id / "batch-job.json"
    if not job_file.exists():
        print(f"[{book_id}] batch-job.json not found, skipping.")
        return

    with open(job_file) as f:
        job_info = json.load(f)

    print(f"\n=== [{book_id}] {job_info['name']} ===")
    batch = client.batches.get(name=job_info["name"])
    state = batch.state.name if batch.state else "UNKNOWN"
    print(f"Status: {state}")
    if state != "JOB_STATE_SUCCEEDED":
        print(f"[{book_id}] not ready: {state}")
        return

    if not batch.dest or not batch.dest.file_name:
        print(f"[{book_id}] no output file")
        return

    output_file_name = batch.dest.file_name
    print(f"Output file: {output_file_name}")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/{output_file_name}"
        f":download?alt=media&key={api_key}"
    )
    print("Downloading results...")
    with urllib.request.urlopen(url) as response:
        results_text = response.read().decode("utf-8")

    output_dir = ROOT / book_id / "chapters" / "images"
    output_dir.mkdir(parents=True, exist_ok=True)

    saved = 0
    failed = 0
    for line in results_text.strip().split("\n"):
        if not line:
            continue
        try:
            result = json.loads(line)
        except json.JSONDecodeError:
            failed += 1
            continue

        image_name = result.get("key", "unknown")
        candidates = result.get("response", {}).get("candidates", [])
        if not candidates:
            failed += 1
            continue

        parts = candidates[0].get("content", {}).get("parts", [])
        for part in parts:
            inline_data = part.get("inlineData")
            if not inline_data:
                continue
            mime_type = inline_data.get("mimeType", "image/png")
            data = inline_data.get("data", "")
            extension = mime_type.split("/")[-1]
            if extension == "jpeg":
                extension = "jpg"
            output_path = output_dir / f"{image_name}.{extension}"
            try:
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(data))
                print(f"  ✓ {output_path.name}")
                saved += 1
            except Exception as e:
                print(f"  ✗ {image_name}: {e}")
                failed += 1
            break

    print(f"[{book_id}] {saved} saved, {failed} failed → {output_dir}")


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
        download_for_book(client, api_key, book_id)


if __name__ == "__main__":
    main()
