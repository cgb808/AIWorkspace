#!/usr/bin/env bash
# Ensure required Piper voice models exist locally.
# Default voices: amy (US), alan (UK), southern_male (UK variant)
set -euo pipefail
BASE_DIR=$(pwd)
MODELS_DIR="models/piper"
mkdir -p "$MODELS_DIR"

download_voice(){
  local file="$1";
  local url="$2";
  if [ -f "$MODELS_DIR/$file" ]; then
    echo "[piper] $file present";
  else
    echo "[piper] downloading $file";
    curl -L "$url" -o "$MODELS_DIR/$file";
  fi
}

# Reference voice URLs (small/low variants for speed)
download_voice en_US-amy-low.onnx https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/low/en_US-amy-low.onnx
download_voice en_GB-alan-low.onnx https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/low/en_GB-alan-low.onnx
download_voice en_GB-southern_english_male-low.onnx https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/southern_english_male/low/en_GB-southern_english_male-low.onnx

echo "[piper] done"
