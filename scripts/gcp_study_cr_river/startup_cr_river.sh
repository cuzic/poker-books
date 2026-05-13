#!/bin/bash
# VM startup script for check-raise + river GTO study.

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
    gsutil -q cp "$LOG" "gs://${GCS_BUCKET}/cr_river_study/logs/vm${VM_INDEX}.log" 2>/dev/null || true
}

WORK=/opt/gcp_study
mkdir -p "$WORK"
cd "$WORK"

log "Installing libgomp1..."
apt-get install -y -qq libgomp1 2>&1 | tail -3

log "Downloading files from GCS..."
gsutil -q cp "gs://${GCS_BUCKET}/cr_river_study/worker_cr_river.py"       worker_cr_river.py       && log "worker OK"
gsutil -q cp "gs://${GCS_BUCKET}/cr_river_study/scenarios_cr_river.json"  scenarios_cr_river.json  && log "scenarios OK"
gsutil -q cp "gs://${GCS_BUCKET}/cr_river_study/console_solver"           console_solver           && log "solver OK"
gsutil -q cp "gs://${GCS_BUCKET}/cr_river_study/solver_resources.tar.gz"  solver_resources.tar.gz  && log "resources OK"
chmod +x console_solver
tar -xzf solver_resources.tar.gz
log "Resources extracted"

upload_log

log "Running worker_cr_river.py..."
python3 worker_cr_river.py \
    --bucket     "$GCS_BUCKET" \
    --vm-index   "$VM_INDEX" \
    --n-vms      "$N_VMS" \
    --solver     "$WORK/console_solver" \
    --solver-dir "$WORK" \
    --scenarios  scenarios_cr_river.json \
    --threads    "$THREADS" \
    --parallel   "$PARALLEL"

WORKER_EXIT=$?
log "Worker exited: ${WORKER_EXIT}"
upload_log
log "Shutting down."
shutdown -h now
