#!/bin/bash
# Launch GCP Spot VM for check-raise + river GTO study.
#
# Usage:
#   bash launch_cr_river.sh [--project PROJECT] [--bucket BUCKET] [--n-vms N]
#
# Env vars (all have defaults):
#   GCP_PROJECT, GCS_BUCKET, N_VMS, GCP_ZONE, GCP_MACHINE
#   SOLVER_THREADS, SOLVER_PARALLEL

set -euo pipefail
cd "$(dirname "$0")"

PROJECT="${GCP_PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
BUCKET="${GCS_BUCKET:-poker-gto-study}"
N_VMS="${N_VMS:-1}"
ZONE="${GCP_ZONE:-us-central1-a}"
REGION="${GCP_REGION:-us-central1}"
MACHINE="${GCP_MACHINE:-n2-standard-32}"
THREADS="${SOLVER_THREADS:-8}"
PARALLEL="${SOLVER_PARALLEL:-4}"
LABEL="cr-study-$(date +%Y%m%d-%H%M%S)"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project)  PROJECT="$2";  shift 2;;
        --bucket)   BUCKET="$2";   shift 2;;
        --n-vms)    N_VMS="$2";    shift 2;;
        --zone)     ZONE="$2";     shift 2;;
        --machine)  MACHINE="$2";  shift 2;;
        *) echo "Unknown arg: $1"; exit 1;;
    esac
done

if [[ -z "$PROJECT" ]]; then
    echo "ERROR: Set GCP_PROJECT env or --project flag" >&2
    exit 1
fi

SOLVER_BIN="$HOME/TexasSolver/build/console_solver"
if [[ ! -x "$SOLVER_BIN" ]]; then
    echo "ERROR: TexasSolver binary not found at $SOLVER_BIN" >&2
    exit 1
fi

SCENARIOS_FILE="scenarios_cr_river.json"
if [[ ! -f "$SCENARIOS_FILE" ]]; then
    echo "Generating scenarios..."
    python3 scenarios_cr_river.py
fi

TOTAL=$(python3 -c "import json; d=json.load(open('$SCENARIOS_FILE')); print(len(d['scenarios']))")
FLOP_N=$(python3 -c "import json; d=json.load(open('$SCENARIOS_FILE')); print(sum(1 for s in d['scenarios'] if s['n_board']==3))")
RIVER_N=$(python3 -c "import json; d=json.load(open('$SCENARIOS_FILE')); print(sum(1 for s in d['scenarios'] if s['n_board']==5))")

echo "=== CR + River GTO Study ==="
echo "  Project   : $PROJECT"
echo "  Bucket    : gs://$BUCKET/cr_river_study/"
echo "  VMs       : $N_VMS × $MACHINE (Spot)"
echo "  Zone      : $ZONE"
echo "  Threads   : $THREADS  Parallel: $PARALLEL"
echo "  Scenarios : $TOTAL total (Flop-CR=$FLOP_N  River=$RIVER_N)"
echo ""

# [1] Ensure GCS bucket exists
echo "[1/4] Ensuring GCS bucket..."
gsutil ls "gs://${BUCKET}" 2>/dev/null || \
    gsutil mb -p "$PROJECT" -l "$REGION" "gs://${BUCKET}"

# [2] Package solver resources
echo "[2/4] Packaging TexasSolver..."
RESOURCES_TAR="/tmp/solver_resources_cr.tar.gz"
if [[ ! -f "$RESOURCES_TAR" ]]; then
    echo "  Compressing resources..."
    tar -czf "$RESOURCES_TAR" -C "$HOME/TexasSolver" resources/compairer/card5_dic_sorted.txt
fi
echo "  Binary:    $SOLVER_BIN ($(du -sh "$SOLVER_BIN" | cut -f1))"
echo "  Resources: $RESOURCES_TAR ($(du -sh "$RESOURCES_TAR" | cut -f1))"

# [3] Upload to GCS
echo "[3/4] Uploading to GCS..."
gsutil -q cp "$SOLVER_BIN"            "gs://${BUCKET}/cr_river_study/console_solver"
gsutil -q cp worker_cr_river.py       "gs://${BUCKET}/cr_river_study/worker_cr_river.py"
gsutil -q cp "$SCENARIOS_FILE"        "gs://${BUCKET}/cr_river_study/scenarios_cr_river.json"
gsutil -q cp startup_cr_river.sh      "gs://${BUCKET}/cr_river_study/startup_cr_river.sh"
gsutil -q cp "$RESOURCES_TAR"         "gs://${BUCKET}/cr_river_study/solver_resources.tar.gz"
echo "  Upload done."

# [4] Launch Spot VMs
echo "[4/4] Launching $N_VMS Spot VMs ($MACHINE)..."

for i in $(seq 0 $((N_VMS - 1))); do
    VM_NAME="${LABEL}-vm${i}"
    echo "  Launching $VM_NAME..."
    gcloud compute instances create "$VM_NAME" \
        --project="$PROJECT" \
        --zone="$ZONE" \
        --machine-type="$MACHINE" \
        --provisioning-model=SPOT \
        --instance-termination-action=DELETE \
        --image-family=debian-12 \
        --image-project=debian-cloud \
        --boot-disk-size=20GB \
        --scopes=storage-rw,logging-write \
        --metadata="^|^gcs-bucket=${BUCKET}|vm-index=${i}|n-vms=${N_VMS}|threads=${THREADS}|parallel=${PARALLEL}" \
        --metadata-from-file=startup-script=startup_cr_river.sh \
        --labels="study=${LABEL}" \
        --quiet
done

echo ""
echo "=== All VMs launched ==="
echo ""
echo "Estimated time: ~30-45 min (${TOTAL} scenarios / ${N_VMS} VMs / ${PARALLEL} parallel)"
echo ""
echo "Monitor:"
echo "  gcloud compute instances list --filter='labels.study=${LABEL}'"
echo "  gsutil ls gs://${BUCKET}/cr_river_study/results/ | wc -l"
echo "  gsutil ls gs://${BUCKET}/cr_river_study/done/    # completion markers"
echo ""
echo "Collect:"
echo "  gsutil -m cp -r gs://${BUCKET}/cr_river_study/results/ ./cr_river_results/"
echo "  Label: ${LABEL}"
