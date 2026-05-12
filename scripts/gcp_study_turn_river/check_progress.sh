#!/bin/bash
# Quick progress check.
cd "$(dirname "$0")"
BUCKET="${BUCKET:-poker-gto-study}"
LABEL="${LABEL:-tr-study-20260512-081822}"

echo "=== Turn+River Study Progress ==="
echo "Label: $LABEL"
echo ""

echo "VMs:"
gcloud compute instances list --filter="labels.study=${LABEL}" --format="table(name,status)" 2>/dev/null || echo "  (none / all complete)"

echo ""
DONE=$(gsutil ls "gs://${BUCKET}/turn_river_study/results/*.json" 2>/dev/null | wc -l)
TOTAL=395
echo "Results: ${DONE}/${TOTAL} ($(( DONE * 100 / TOTAL ))%)"

MARKERS=$(gsutil ls "gs://${BUCKET}/turn_river_study/done/*.txt" 2>/dev/null | wc -l)
echo "Done markers: ${MARKERS}/4 VMs"

if [[ "$MARKERS" -ge 4 ]]; then
    echo ""
    echo "★ VM0-3 COMPLETE. Run: bash launch_vm4_followup.sh"
fi
