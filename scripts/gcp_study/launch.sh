#!/bin/bash
# Upload files to GCS and launch Spot VMs.
# Usage: bash launch.sh [--project PROJECT] [--bucket BUCKET] [--n-vms N]
#
# Prerequisites:
#   gcloud auth login
#   gcloud config set project YOUR_PROJECT

set -euo pipefail
cd "$(dirname "$0")"

# ── Configurable defaults ─────────────────────────────────────────────────────
PROJECT="${GCP_PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
BUCKET="${GCS_BUCKET:-poker-gto-study}"
N_VMS="${N_VMS:-5}"
REGION="${GCP_REGION:-us-central1}"
ZONE="${GCP_ZONE:-us-central1-c}"
MACHINE="${GCP_MACHINE:-c2-standard-60}"
THREADS="${SOLVER_THREADS:-8}"
PARALLEL="${SOLVER_PARALLEL:-6}"   # solver instances per VM (×THREADS = core usage)
LABEL="poker-gto-$(date +%Y%m%d-%H%M%S)"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project)  PROJECT="$2";  shift 2;;
        --bucket)   BUCKET="$2";   shift 2;;
        --n-vms)    N_VMS="$2";    shift 2;;
        --region)   REGION="$2";   shift 2;;
        --zone)     ZONE="$2";     shift 2;;
        *) echo "Unknown arg: $1"; exit 1;;
    esac
done

if [[ -z "$PROJECT" ]]; then
    echo "ERROR: Set GCP_PROJECT env or --project flag" >&2
    exit 1
fi

echo "=== GCP 168-board GTO study ==="
echo "  Project : $PROJECT"
echo "  Bucket  : gs://$BUCKET"
echo "  VMs     : $N_VMS × $MACHINE (Spot)"
echo "  Zone    : $ZONE"
echo ""

# ── Generate boards.json ──────────────────────────────────────────────────────
echo "[1/5] Generating boards.json..."
python3 boards.py

# ── Create GCS bucket if needed ───────────────────────────────────────────────
echo "[2/5] Ensuring GCS bucket exists..."
gsutil ls "gs://${BUCKET}" 2>/dev/null || \
    gsutil mb -p "$PROJECT" -l "$REGION" "gs://${BUCKET}"

# ── Package TexasSolver ───────────────────────────────────────────────────────
echo "[3/5] Packaging TexasSolver..."
SOLVER_BIN="$HOME/TexasSolver/build/console_solver"

if [[ ! -x "$SOLVER_BIN" ]]; then
    echo "ERROR: TexasSolver binary not found at $SOLVER_BIN" >&2
    exit 1
fi
echo "  Binary: $SOLVER_BIN ($(du -sh "$SOLVER_BIN" | cut -f1))"

# ── Upload to GCS ─────────────────────────────────────────────────────────────
echo "[4/5] Uploading files to GCS..."
gsutil -q cp "$SOLVER_BIN"  "gs://${BUCKET}/gcp_study/console_solver"
gsutil -q cp worker.py      "gs://${BUCKET}/gcp_study/worker.py"
gsutil -q cp boards.json    "gs://${BUCKET}/gcp_study/boards.json"
gsutil -q cp startup.sh     "gs://${BUCKET}/gcp_study/startup.sh"
RESOURCES_TAR="/tmp/solver_resources.tar.gz"
if [[ ! -f "$RESOURCES_TAR" ]]; then
    echo "  Packaging resources..."
    tar -czf "$RESOURCES_TAR" -C "$HOME/TexasSolver" resources/compairer/card5_dic_sorted.txt
fi
gsutil -q cp "$RESOURCES_TAR" "gs://${BUCKET}/gcp_study/solver_resources.tar.gz"
echo "  Upload done (resources: $(du -sh "$RESOURCES_TAR" | cut -f1))."

# ── Launch Spot VMs ───────────────────────────────────────────────────────────
echo "[5/5] Launching $N_VMS Spot VMs..."
STARTUP_SCRIPT=$(cat startup.sh)

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
        --metadata-from-file=startup-script=startup.sh \
        --labels="study=${LABEL}" \
        --quiet
done

echo ""
echo "=== All VMs launched ==="
echo "Monitor with:"
echo "  gcloud compute instances list --filter='labels.study=${LABEL}'"
echo "  gsutil ls gs://${BUCKET}/gcp_study/results/ | wc -l"
echo ""
echo "Collect results when done:"
echo "  BUCKET=${BUCKET} bash collect.sh"
