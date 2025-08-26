#!/usr/bin/env bash
# Idempotent setup for whisper.cpp (CPU or optional GPU acceleration via CUDA)
# Usage: bash scripts/setup_whisper_cpp.sh [model]  (default: small.en)
set -euo pipefail
MODEL="${1:-small.en}"
BASE_DIR=$(pwd)
VENDOR_DIR="${BASE_DIR}/vendor"
WHISPER_DIR="${VENDOR_DIR}/whisper.cpp"
MODELS_DIR="${WHISPER_DIR}/models"

log(){ printf "[whisper-setup] %s\n" "$*"; }

mkdir -p "$VENDOR_DIR"
if [ ! -d "$WHISPER_DIR/.git" ]; then
  log "Cloning whisper.cpp"
  git clone --depth 1 https://github.com/ggerganov/whisper.cpp "$WHISPER_DIR"
else
  log "Updating whisper.cpp"
  git -C "$WHISPER_DIR" pull --ff-only || true
fi

log "Building (auto-detect CPU)"
make -C "$WHISPER_DIR" -j"$(nproc)"

mkdir -p "$MODELS_DIR"
if [ ! -f "$MODELS_DIR/ggml-${MODEL}.bin" ]; then
  log "Downloading model ${MODEL}"
  bash "$WHISPER_DIR"/models/download-ggml-model.sh "${MODEL}"
else
  log "Model ${MODEL} already present"
fi

log "Done. Test with:"
log "  ${WHISPER_DIR}/main -m ${MODELS_DIR}/ggml-${MODEL}.bin -f samples/jfk.wav"
