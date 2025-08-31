#!/usr/bin/env bash
set -euo pipefail
OLLAMA_HOST=${OLLAMA_HOST:-http://localhost:11435}
MODEL=${MODEL:-phi3:mini}

echo "[ensure_phi3] Ensuring '$MODEL' exists on Ollama host $OLLAMA_HOST"
if curl -s "$OLLAMA_HOST/api/tags" | grep -q '"'$MODEL'"'; then
  echo "[ensure_phi3] Model already present"
else
  echo "[ensure_phi3] Pulling model..."
  curl -s -X POST "$OLLAMA_HOST/api/pull" -d '{"name":"'$MODEL'"}' | jq -r '.status?' || true
  echo "[ensure_phi3] Pull request sent (monitor Ollama logs)"
fi
