#!/bin/bash
# Download turn+river GTO results from GCS and merge into a single JSON.
#
# Usage: BUCKET=poker-gto-study bash collect_turn_river.sh
#
# Outputs:
#   results/turn_river_results_all.json  — all merged results
#   results/turn_results.json            — turn only
#   results/river_results.json           — river only

set -euo pipefail
cd "$(dirname "$0")"

BUCKET="${BUCKET:-poker-gto-study}"
OUT_DIR="$(pwd)/results"
mkdir -p "$OUT_DIR"
TMP_DIR="$(mktemp -d)"

echo "=== Collecting turn+river results from gs://${BUCKET}/turn_river_study/results/ ==="

# Count available results
TOTAL=$(gsutil ls "gs://${BUCKET}/turn_river_study/results/*.json" 2>/dev/null | wc -l)
echo "  Found: $TOTAL result files"

if [[ "$TOTAL" -eq 0 ]]; then
    echo "No results yet. Check VM status:"
    echo "  gcloud compute instances list"
    exit 0
fi

# Download all results
echo "Downloading..."
gsutil -m -q cp "gs://${BUCKET}/turn_river_study/results/*.json" "$TMP_DIR/"
echo "  Downloaded: $(ls "$TMP_DIR"/*.json 2>/dev/null | wc -l) files"

# Download logs
LOG_DIR="$OUT_DIR/logs"
mkdir -p "$LOG_DIR"
gsutil -m -q cp "gs://${BUCKET}/turn_river_study/logs/*.log" "$LOG_DIR/" 2>/dev/null || true
echo "  Logs downloaded to $LOG_DIR/"

# Merge into a single JSON using Python
TMP_DIR="$TMP_DIR" OUT_DIR="$OUT_DIR" python3 - <<'PYEOF'
import json, glob, os, sys

tmp_dir = os.environ.get('TMP_DIR', '/tmp')
out_dir = os.environ.get('OUT_DIR', './results')

files = glob.glob(f'{tmp_dir}/*.json')
all_results = []
for f in files:
    try:
        data = json.loads(open(f).read())
        # skip if it's a list (shouldn't happen, but defensive)
        if isinstance(data, list):
            all_results.extend(data)
        elif isinstance(data, dict):
            all_results.append(data)
    except Exception as e:
        print(f'WARN: {f}: {e}', file=sys.stderr)

turn_results  = [r for r in all_results if r.get('street') == 'turn']
river_results = [r for r in all_results if r.get('street') == 'river']
errors = [r for r in all_results if r.get('error') or (not r.get('ok') and not r.get('cached'))]

print(f'Turn results:  {len(turn_results)}')
print(f'River results: {len(river_results)}')
print(f'Errors:        {len(errors)}')

with open(f'{out_dir}/turn_river_results_all.json', 'w') as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)
with open(f'{out_dir}/turn_results.json', 'w') as f:
    json.dump(turn_results, f, ensure_ascii=False, indent=2)
with open(f'{out_dir}/river_results.json', 'w') as f:
    json.dump(river_results, f, ensure_ascii=False, indent=2)

if errors:
    print(f'\nFailed scenarios:')
    for e in errors[:10]:
        print(f'  {e.get("scenario_id","?")}  {e.get("error","?")}')
PYEOF

echo ""
echo "Saved:"
echo "  $OUT_DIR/turn_river_results_all.json"
echo "  $OUT_DIR/turn_results.json"
echo "  $OUT_DIR/river_results.json"
echo ""
echo "Next: python3 analyze_turn_river.py"

# Cleanup
rm -rf "$TMP_DIR"
