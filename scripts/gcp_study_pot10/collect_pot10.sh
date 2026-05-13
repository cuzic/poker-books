#!/bin/bash
# Download pot10 GTO results from GCS and merge into a single JSON.
#
# Usage: BUCKET=poker-gto-study bash collect_pot10.sh
#
# Output:
#   /home/cuzic/poker-books/knowledges/gto_canonical/results/pot10_results_all.json

set -euo pipefail
cd "$(dirname "$0")"

BUCKET="${BUCKET:-poker-gto-study}"
OUT_DIR="/home/cuzic/poker-books/knowledges/gto_canonical/results"
mkdir -p "$OUT_DIR"
TMP_DIR="$(mktemp -d)"

echo "=== Collecting pot10 results from gs://${BUCKET}/pot10_study/results/ ==="

TOTAL=$(gsutil ls "gs://${BUCKET}/pot10_study/results/*.json" 2>/dev/null | wc -l)
echo "  Found: $TOTAL result files"

if [[ "$TOTAL" -eq 0 ]]; then
    echo "No results yet. Check VM status:"
    echo "  gcloud compute instances list"
    exit 0
fi

echo "Downloading..."
gsutil -m -q cp "gs://${BUCKET}/pot10_study/results/*.json" "$TMP_DIR/"
echo "  Downloaded: $(ls "$TMP_DIR"/*.json 2>/dev/null | wc -l) files"

# Download logs
LOG_DIR="$OUT_DIR/logs"
mkdir -p "$LOG_DIR"
gsutil -m -q cp "gs://${BUCKET}/pot10_study/logs/*.log" "$LOG_DIR/" 2>/dev/null || true
echo "  Logs downloaded to $LOG_DIR/"

TMP_DIR="$TMP_DIR" OUT_DIR="$OUT_DIR" python3 - <<'PYEOF'
import json, glob, os, sys

tmp_dir = os.environ['TMP_DIR']
out_dir = os.environ['OUT_DIR']

files = glob.glob(f'{tmp_dir}/*.json')
all_results = []
for f in files:
    try:
        data = json.loads(open(f).read())
        if isinstance(data, list):
            all_results.extend(data)
        elif isinstance(data, dict):
            all_results.append(data)
    except Exception as e:
        print(f'WARN: {f}: {e}', file=sys.stderr)

flop_results = [r for r in all_results if len(r.get('board', '').split(',')) == 3]
turn_results = [r for r in all_results if len(r.get('board', '').split(',')) == 4]
errors = [r for r in all_results
          if r.get('error') or (not r.get('ok') and not r.get('cached'))]

print(f'Flop results:  {len(flop_results)}')
print(f'Turn results:  {len(turn_results)}')
print(f'Errors:        {len(errors)}')

with open(f'{out_dir}/pot10_results_all.json', 'w') as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)

if errors:
    print(f'\nFailed scenarios:')
    for e in errors[:10]:
        print(f'  {e.get("id", e.get("scenario_id", "?"))}  {e.get("error", "?")}')
PYEOF

echo ""
echo "Saved:"
echo "  $OUT_DIR/pot10_results_all.json"

rm -rf "$TMP_DIR"
