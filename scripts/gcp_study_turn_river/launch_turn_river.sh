#!/bin/bash
# Launch GCP Spot VMs for the comprehensive turn+river GTO study.
#
# Usage:
#   bash launch_turn_river.sh [--project PROJECT] [--bucket BUCKET] [--n-vms N]
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
N_VMS="${N_VMS:-5}"
ZONE="${GCP_ZONE:-us-central1-c}"
REGION="${GCP_REGION:-us-central1}"
MACHINE="${GCP_MACHINE:-n2-standard-8}"
THREADS="${SOLVER_THREADS:-4}"
PARALLEL="${SOLVER_PARALLEL:-2}"
LABEL="tr-study-$(date +%Y%m%d-%H%M%S)"

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

echo "=== Turn+River GTO Study ==="
echo "  Project  : $PROJECT"
echo "  Bucket   : gs://$BUCKET/turn_river_study/"
echo "  VMs      : $N_VMS × $MACHINE (Spot)"
echo "  Zone     : $ZONE"
echo "  Threads  : $THREADS  Parallel: $PARALLEL"
echo ""

# ── [1] Generate merged board list ────────────────────────────────────────────
echo "[1/5] Generating study boards..."
python3 boards_comprehensive.py
python3 extract_deck_boards.py
python3 boards_full_study.py

TOTAL=$(python3 -c "import json; d=json.load(open('study_boards_all.json')); print(len(d))")
TURN_N=$(python3 -c "import json; d=json.load(open('study_boards_all.json')); print(sum(1 for x in d if x.get('street')=='turn'))")
RIVER_N=$(python3 -c "import json; d=json.load(open('study_boards_all.json')); print(sum(1 for x in d if x.get('street')=='river'))")
echo "  Total: $TOTAL scenarios (Turn=$TURN_N  River=$RIVER_N)"

# ── [2] Ensure GCS bucket exists ──────────────────────────────────────────────
echo "[2/5] Ensuring GCS bucket..."
gsutil ls "gs://${BUCKET}" 2>/dev/null || \
    gsutil mb -p "$PROJECT" -l "$REGION" "gs://${BUCKET}"

# ── [3] Package solver resources ──────────────────────────────────────────────
echo "[3/5] Packaging TexasSolver..."
RESOURCES_TAR="/tmp/solver_resources_tr.tar.gz"
if [[ ! -f "$RESOURCES_TAR" ]]; then
    echo "  Compressing resources..."
    tar -czf "$RESOURCES_TAR" -C "$HOME/TexasSolver" resources/compairer/card5_dic_sorted.txt
fi
echo "  Binary:    $SOLVER_BIN ($(du -sh "$SOLVER_BIN" | cut -f1))"
echo "  Resources: $RESOURCES_TAR ($(du -sh "$RESOURCES_TAR" | cut -f1))"

# ── [4] Upload to GCS ─────────────────────────────────────────────────────────
echo "[4/5] Uploading to GCS..."
gsutil -q cp "$SOLVER_BIN"             "gs://${BUCKET}/turn_river_study/console_solver"
gsutil -q cp worker_turn_river.py      "gs://${BUCKET}/turn_river_study/worker_turn_river.py"
gsutil -q cp study_boards_all.json     "gs://${BUCKET}/turn_river_study/study_boards_all.json"
gsutil -q cp startup_turn_river.sh     "gs://${BUCKET}/turn_river_study/startup_turn_river.sh"
gsutil -q cp "$RESOURCES_TAR"          "gs://${BUCKET}/turn_river_study/solver_resources.tar.gz"
echo "  Upload done."

# ── [5] Launch Spot VMs ────────────────────────────────────────────────────────
echo "[5/5] Launching $N_VMS Spot VMs ($MACHINE)..."

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
        --metadata-from-file=startup-script=startup_turn_river.sh \
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
echo "  gsutil ls gs://${BUCKET}/turn_river_study/results/ | wc -l"
echo "  gsutil ls gs://${BUCKET}/turn_river_study/done/    # completion markers"
echo ""
echo "Collect results:"
echo "  BUCKET=${BUCKET} bash collect_turn_river.sh"
echo "  Label: ${LABEL}"
