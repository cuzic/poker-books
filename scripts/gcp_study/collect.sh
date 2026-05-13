#!/bin/bash
# Wait for all VM results, download from GCS, run regression.
# Usage: BUCKET=my-bucket bash collect.sh [--total N]
set -euo pipefail
cd "$(dirname "$0")"

BUCKET="${GCS_BUCKET:-${1:-}}"
TOTAL="${TOTAL:-}"        # expected result count; auto-detected if empty
POLL_INTERVAL=30          # seconds between checks
OUT_DIR="../../knowledges/flop/results/168board_study"

if [[ -z "$BUCKET" ]]; then
    echo "Usage: BUCKET=my-bucket bash collect.sh" >&2
    exit 1
fi

mkdir -p "$OUT_DIR"

# ── Auto-detect expected board count ─────────────────────────────────────────
if [[ -z "$TOTAL" ]]; then
    if [[ -f boards.json ]]; then
        TOTAL=$(python3 -c "import json; d=json.load(open('boards.json')); print(len(d))")
    else
        echo "WARNING: boards.json not found; set TOTAL env to override" >&2
        TOTAL=168
    fi
fi
echo "Waiting for $TOTAL results in gs://${BUCKET}/gcp_study/results/"
echo ""

# ── Poll until all results arrive ─────────────────────────────────────────────
while true; do
    COUNT=$(gsutil ls "gs://${BUCKET}/gcp_study/results/*.json" 2>/dev/null | wc -l || echo 0)
    PCT=$(( COUNT * 100 / TOTAL ))
    printf "\r[%s] %d/%d (%d%%)" "$(date +%H:%M:%S)" "$COUNT" "$TOTAL" "$PCT"
    if [[ "$COUNT" -ge "$TOTAL" ]]; then
        echo ""
        break
    fi
    sleep "$POLL_INTERVAL"
done

# ── Download results ──────────────────────────────────────────────────────────
echo "Downloading results..."
gsutil -q -m cp "gs://${BUCKET}/gcp_study/results/*.json" "$OUT_DIR/"
echo "Downloaded to $OUT_DIR/ ($(ls "$OUT_DIR"/*.json 2>/dev/null | wc -l) files)"

# ── Run regression ────────────────────────────────────────────────────────────
echo ""
echo "Running regression analysis..."
python3 regression.py --results "$OUT_DIR" \
    | tee "$OUT_DIR/regression_report.txt"

echo ""
echo "Report saved: $OUT_DIR/regression_report.txt"
