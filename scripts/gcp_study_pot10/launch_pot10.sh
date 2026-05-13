#!/bin/bash
# Launch GCP Spot VMs for the pot10 GTO study.
#
# Usage:
#   bash launch_pot10.sh [--project PROJECT] [--bucket BUCKET] [--n-vms N]
#
# Env vars (all have defaults):
#   GCP_PROJECT, GCS_BUCKET, N_VMS, GCP_ZONE, GCP_MACHINE
#   SOLVER_THREADS, SOLVER_PARALLEL
#
# Prerequisites:
#   gcloud auth login
#   gcloud config set project YOUR_PROJECT

set -euo pipefail
cd "$(dirname "$0")"

# ── Defaults ───────────────────────────────────────────────────────────────────
PROJECT="${GCP_PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
BUCKET="${GCS_BUCKET:-poker-gto-study}"
N_VMS="${N_VMS:-3}"
ZONE="${GCP_ZONE:-us-central1-c}"
REGION="${GCP_REGION:-us-central1}"
MACHINE="${GCP_MACHINE:-c2-standard-60}"
THREADS="${SOLVER_THREADS:-8}"
PARALLEL="${SOLVER_PARALLEL:-6}"
LABEL="p10-study-$(date +%Y%m%d-%H%M%S)"

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

SCENARIOS_FILE="scenarios_pot10.json"
if [[ ! -f "$SCENARIOS_FILE" ]]; then
    echo "ERROR: $SCENARIOS_FILE not found in $(pwd)" >&2
    exit 1
fi

TOTAL=$(python3 -c "import json; d=json.load(open('$SCENARIOS_FILE')); print(len(d['scenarios']))")
FLOP_N=$(python3 -c "import json; d=json.load(open('$SCENARIOS_FILE')); print(sum(1 for s in d['scenarios'] if len(s['board'].split(','))==3))")
TURN_N=$(python3 -c "import json; d=json.load(open('$SCENARIOS_FILE')); print(sum(1 for s in d['scenarios'] if len(s['board'].split(','))==4))")

echo "=== Pot10 GTO Study ==="
echo "  Project   : $PROJECT"
echo "  Bucket    : gs://$BUCKET/pot10_study/"
echo "  VMs       : $N_VMS × $MACHINE (Spot)"
echo "  Zone      : $ZONE"
echo "  Threads   : $THREADS  Parallel: $PARALLEL"
echo "  Scenarios : $TOTAL total (Flop=$FLOP_N  Turn=$TURN_N)"
echo ""

# ── [1] Ensure GCS bucket exists ──────────────────────────────────────────────
echo "[1/4] Ensuring GCS bucket..."
gsutil ls "gs://${BUCKET}" 2>/dev/null || \
    gsutil mb -p "$PROJECT" -l "$REGION" "gs://${BUCKET}"

# ── [2] Package solver resources ──────────────────────────────────────────────
echo "[2/4] Packaging TexasSolver..."
RESOURCES_TAR="/tmp/solver_resources_p10.tar.gz"
if [[ ! -f "$RESOURCES_TAR" ]]; then
    echo "  Compressing resources..."
    tar -czf "$RESOURCES_TAR" -C "$HOME/TexasSolver" resources/compairer/card5_dic_sorted.txt
fi
echo "  Binary:    $SOLVER_BIN ($(du -sh "$SOLVER_BIN" | cut -f1))"
echo "  Resources: $RESOURCES_TAR ($(du -sh "$RESOURCES_TAR" | cut -f1))"

# ── [3] Upload to GCS ─────────────────────────────────────────────────────────
echo "[3/4] Uploading to GCS..."
gsutil -q cp "$SOLVER_BIN"         "gs://${BUCKET}/pot10_study/console_solver"
gsutil -q cp worker_pot10.py       "gs://${BUCKET}/pot10_study/worker_pot10.py"
gsutil -q cp "$SCENARIOS_FILE"     "gs://${BUCKET}/pot10_study/scenarios_pot10.json"
gsutil -q cp startup_pot10.sh      "gs://${BUCKET}/pot10_study/startup_pot10.sh"
gsutil -q cp "$RESOURCES_TAR"      "gs://${BUCKET}/pot10_study/solver_resources.tar.gz"
echo "  Upload done."

# ── [4] Launch Spot VMs ────────────────────────────────────────────────────────
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
        --metadata-from-file=startup-script=startup_pot10.sh \
        --labels="study=${LABEL}" \
        --quiet
done

echo ""
echo "=== All VMs launched ==="
echo ""
echo "Estimated time: ~60-90 min (${TOTAL} scenarios / ${N_VMS} VMs / ${PARALLEL} parallel)"
echo ""
echo "Monitor:"
echo "  gcloud compute instances list --filter='labels.study=${LABEL}'"
echo "  gsutil ls gs://${BUCKET}/pot10_study/results/ | wc -l"
echo "  gsutil ls gs://${BUCKET}/pot10_study/done/    # completion markers"
echo ""
echo "Collect results:"
echo "  BUCKET=${BUCKET} bash collect_pot10.sh"
echo "  Label: ${LABEL}"
