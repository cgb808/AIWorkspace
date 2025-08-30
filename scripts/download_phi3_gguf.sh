#!/usr/bin/env bash
set -euo pipefail

# download_phi3_gguf.sh
# Fetch the Phi-3 Mini 4K Instruct Q8_0 GGUF model file locally.
# Default source: Hugging Face (TheBloke quantization repo).
# Optional: set HF_TOKEN env var for higher rate limits / gated access (not usually needed for this model).

MODEL_REPO="TheBloke/Phi-3-mini-4k-instruct-GGUF"
FILENAME="phi-3-mini-4k-instruct.Q8_0.gguf"
DEST_DIR="models/phi3"
DEST_PATH="$DEST_DIR/$FILENAME"

mkdir -p "$DEST_DIR"

if [ -f "$DEST_PATH" ]; then
  echo "[info] Model already exists at $DEST_PATH"
  exit 0
fi

echo "[info] Downloading $FILENAME from $MODEL_REPO ..."

# Prefer huggingface-cli if available
if command -v huggingface-cli >/dev/null 2>&1; then
  if [ -n "${HF_TOKEN:-}" ]; then
    huggingface-cli download "$MODEL_REPO" "$FILENAME" --token "$HF_TOKEN" --local-dir "$DEST_DIR" --local-dir-use-symlinks False
  else
    huggingface-cli download "$MODEL_REPO" "$FILENAME" --local-dir "$DEST_DIR" --local-dir-use-symlinks False
  fi
else
  # Fallback to direct curl
  BASE_URL="https://huggingface.co/${MODEL_REPO}/resolve/main/${FILENAME}?download=true"
  if [ -n "${HF_TOKEN:-}" ]; then
    curl -L -H "Authorization: Bearer $HF_TOKEN" "$BASE_URL" -o "$DEST_PATH"
  else
    curl -L "$BASE_URL" -o "$DEST_PATH"
  fi
fi

echo "[ok] Download complete: $DEST_PATH"
ls -lh "$DEST_PATH"

echo "[hint] To use with llama.cpp / server: ./llama-cli -m $DEST_PATH -p 'Hello'"