#!/bin/bash
# VM startup script — pre-compiled binary version, no apt-get required.
# All output is logged to /var/log/startup.log and uploaded to GCS for debugging.

METADATA="http://metadata.google.internal/computeMetadata/v1/instance/attributes"
MFLAG="-H Metadata-Flavor:Google"
LOG=/var/log/startup.log

log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

exec > >(tee -a "$LOG") 2>&1

fetch_meta() { curl -sf $MFLAG "${METADATA}/$1" 2>/dev/null; }

GCS_BUCKET=$(fetch_meta gcs-bucket)
VM_INDEX=$(fetch_meta vm-index)
N_VMS=$(fetch_meta n-vms)
THREADS=$(fetch_meta threads)
PARALLEL=$(fetch_meta parallel)
THREADS=${THREADS:-4}
PARALLEL=${PARALLEL:-2}

log "startup: VM=${VM_INDEX}/${N_VMS}  bucket=${GCS_BUCKET}  threads=${THREADS}  parallel=${PARALLEL}"

upload_log() {
    gsutil -q cp "$LOG" "gs://${GCS_BUCKET}/gcp_study/logs/vm${VM_INDEX}.log" 2>/dev/null || true
}

# ── Create work directory ─────────────────────────────────────────────────────
WORK=/opt/gcp_study
mkdir -p "$WORK"
cd "$WORK"

log "Installing libgomp1 (OpenMP runtime)..."
apt-get install -y -qq libgomp1 2>&1 | tail -3
log "libgomp1 install done (exit $?)"

log "Downloading files from GCS..."
gsutil -q cp "gs://${GCS_BUCKET}/gcp_study/worker.py"              worker.py              && log "worker.py OK"
gsutil -q cp "gs://${GCS_BUCKET}/gcp_study/boards.json"            boards.json            && log "boards.json OK"
gsutil -q cp "gs://${GCS_BUCKET}/gcp_study/console_solver"         console_solver         && log "console_solver OK"
gsutil -q cp "gs://${GCS_BUCKET}/gcp_study/solver_resources.tar.gz" solver_resources.tar.gz && log "resources OK"
chmod +x console_solver
tar -xzf solver_resources.tar.gz
log "Resources extracted: $(ls resources/compairer/ 2>/dev/null | head -3)"

SOLVER_BIN="$WORK/console_solver"
SOLVER_DIR="$WORK"

log "Testing binary..."
echo "invalid_cmd" | "$SOLVER_BIN" > /dev/null 2>&1
log "Binary test exit: $?"

upload_log

log "Running worker.py..."
python3 worker.py \
    --bucket     "$GCS_BUCKET" \
    --vm-index   "$VM_INDEX" \
    --n-vms      "$N_VMS" \
    --solver     "$SOLVER_BIN" \
    --solver-dir "$SOLVER_DIR" \
    --boards     boards.json \
    --threads    "$THREADS" \
    --parallel   "$PARALLEL"

WORKER_EXIT=$?
log "Worker exited: ${WORKER_EXIT}"

upload_log
log "Shutting down."
shutdown -h now
