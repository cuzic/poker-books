#!/bin/bash
# Launch VM4 (cleanup) to process the remaining 79 boards missed due to quota limit.
# Run this after VM0-3 have completed (check with check_progress.sh).
#
# Usage: BUCKET=poker-gto-study bash launch_vm4_followup.sh

set -euo pipefail
cd "$(dirname "$0")"

PROJECT="${GCP_PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
BUCKET="${GCS_BUCKET:-poker-gto-study}"
ZONE="${GCP_ZONE:-us-central1-c}"
LABEL="tr-study-vm4-$(date +%Y%m%d-%H%M%S)"

echo "=== VM4 Followup Launch ==="
echo "  Project: $PROJECT"
echo "  Bucket:  gs://$BUCKET/turn_river_study/"
echo "  Machine: n2-standard-4 (4 cores, Spot)"

# VM4 processes boards where index % 5 == 4
python3 -c "
import json
boards = json.load(open('study_boards_all.json'))
missing = [b['scenario_id'] for i,b in enumerate(boards) if i%5==4]
print(f'  Boards to process: {len(missing)} (indices 4,9,14,...)')
"

gcloud compute instances create "${LABEL}-vm4" \
    --project="$PROJECT" \
    --zone="$ZONE" \
    --machine-type="n2-standard-4" \
    --provisioning-model=SPOT \
    --instance-termination-action=DELETE \
    --image-family=debian-12 \
    --image-project=debian-cloud \
    --boot-disk-size=20GB \
    --scopes=storage-rw,logging-write \
    --metadata="^|^gcs-bucket=${BUCKET}|vm-index=4|n-vms=5|threads=2|parallel=2" \
    --metadata-from-file=startup-script=startup_turn_river.sh \
    --labels="study=${LABEL}" \
    --quiet

echo "  VM4 launched."
echo "  Monitor: gsutil ls gs://${BUCKET}/turn_river_study/results/ | wc -l"
