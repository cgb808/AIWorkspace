#!/usr/bin/env bash
# Helper wrapper to inject a GitHub PAT (GITHUB_PAT) into a single command's environment.
# Usage examples:
#   1) Provide token directly:
#        ./scripts/with_github_pat.sh --token ghp_xxx -- ./scripts/current_affairs_publish.sh "msg"
#   2) Prompt (hidden input):
#        ./scripts/with_github_pat.sh --prompt -- ./scripts/current_affairs_pull.sh
#   3) Read token from file (first line only, file not committed):
#        ./scripts/with_github_pat.sh --file ~/.secrets/aiworkshop_pat -- ./scripts/current_affairs_publish.sh "msg"
#   4) Save (update or add) token line into .env for future runs:
#        ./scripts/with_github_pat.sh --prompt --save -- echo "Token stored"
#
# Precedence for obtaining token:
#   --token > --file > --prompt > existing exported $GITHUB_PAT > value in .env (if present)
#
# Notes:
#   - Token label (e.g. "AIWorkshop") is NOT the token string; you must use the actual secret.
#   - The token is never echoed in full; only a masked preview is shown.
#   - When --save is used, .env is created/updated (line 'GITHUB_PAT=...'). Ensure .env is git-ignored.

set -euo pipefail

TOKEN=""
TOKEN_FILE=""
DO_PROMPT=0
DO_SAVE=0

usage() {
  echo "Usage: $0 [--token <token>|--file <path>|--prompt] [--save] -- <command> [args...]" >&2
  echo "If none of --token/--file/--prompt provided and terminal is interactive, you'll be prompted automatically." >&2
  exit 1
}

while [ $# -gt 0 ]; do
  case "$1" in
    --token)
      shift || usage
      TOKEN=${1:-}; [ -z "$TOKEN" ] && usage
      ;;
    --file)
      shift || usage
      TOKEN_FILE=${1:-}; [ -z "$TOKEN_FILE" ] && usage
      ;;
    --prompt)
      DO_PROMPT=1
      ;;
    --save)
      DO_SAVE=1
      ;;
    --)
      shift
      break
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      ;;
  esac
  shift || true
done

[ $# -gt 0 ] || usage

# Resolve token by precedence
if [ -z "$TOKEN" ] && [ -n "$TOKEN_FILE" ]; then
  if [ -f "$TOKEN_FILE" ]; then
    TOKEN=$(head -n1 "$TOKEN_FILE" | tr -d '\r\n')
  else
    echo "[err] token file not found: $TOKEN_FILE" >&2
    exit 2
  fi
fi

if [ -z "$TOKEN" ] && [ $DO_PROMPT -eq 1 ]; then
  if [ -t 0 ]; then
    read -rs -p "Enter GitHub PAT: " TOKEN
    echo
  else
    echo "[err] --prompt used but stdin is not a TTY" >&2
    exit 3
  fi
fi

if [ -z "$TOKEN" ] && [ -n "${GITHUB_PAT:-}" ]; then
  TOKEN="$GITHUB_PAT"
fi

if [ -z "$TOKEN" ] && [ -f .env ]; then
  ENV_LINE=$(grep -E '^GITHUB_PAT=' .env || true)
  if [ -n "$ENV_LINE" ]; then
    TOKEN=${ENV_LINE#GITHUB_PAT=}
  fi
fi

if [ -z "$TOKEN" ]; then
  if [ -t 0 ]; then
    echo "[info] No token source specified; prompting..." >&2
    read -rs -p "Enter GitHub PAT: " TOKEN
    echo
  else
    echo "[err] No token resolved. Provide --token, --file, or run interactively for prompt." >&2
    exit 4
  fi
fi

MASKED="${TOKEN:0:6}********"
echo "[info] Using GitHub PAT (masked): $MASKED" >&2

if [ $DO_SAVE -eq 1 ]; then
  if [ -f .env ]; then
    if grep -q '^GITHUB_PAT=' .env; then
      sed -i.bak -E "s#^GITHUB_PAT=.*#GITHUB_PAT=$TOKEN#" .env && rm -f .env.bak
    else
      echo "GITHUB_PAT=$TOKEN" >> .env
    fi
  else
    echo "GITHUB_PAT=$TOKEN" > .env
  fi
  chmod 600 .env 2>/dev/null || true
  echo "[ok] Token stored in .env (masked: $MASKED)" >&2
fi

# Export for the child command only
GITHUB_PAT="$TOKEN" "$@"
EXIT_CODE=$?
exit $EXIT_CODE
