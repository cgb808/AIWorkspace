#!/usr/bin/env bash
set -euo pipefail

FILE="docs/current_affairs/CURRENT_AFFAIRS.md"
if [ ! -f "$FILE" ]; then
  echo "[err] $FILE not found (run from repo root)." >&2
  exit 1
fi

MSG=${1:-}
if [ -z "$MSG" ]; then
  echo "Usage: $0 'your message text'" >&2
  exit 2
fi

TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "- $TS $MSG" >> "$FILE"
echo "[ok] Appended line to $FILE"
