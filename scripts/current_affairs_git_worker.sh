#!/usr/bin/env bash
# Automated git worker for appending a current affairs entry, committing, and pushing with retries.
# Usage: scripts/current_affairs_git_worker.sh "your message"
# Behavior:
#  - Acquires a local flock lock to avoid concurrent editors on this clone.
#  - Pulls (rebase) latest changes.
#  - Appends timestamped line via existing current_affairs_append.sh
#  - Commits with standardized message prefix.
#  - Pushes to one or more remotes (space‑separated via CA_REMOTES env, default 'origin').
#  - Optional: replicate updated log into a secondary repo root (CA_SECONDARY_ROOT) and commit/push there too.
#  - On non-fast-forward race it retries (pull --rebase then push) up to N attempts (primary repo only).
# Environment:
#  CA_REMOTES            Space separated list of git remotes to push (default: origin)
#  CA_SECONDARY_ROOT     Path to another git repo root to mirror CURRENT_AFFAIRS.md
#  CA_SECONDARY_BRANCH   Branch for secondary root (default: current branch name of primary)
# Exit codes:
#  0 success
#  1 usage error
#  2 missing file
#  3 lock acquisition failure
#  4 rebase conflict (manual resolution required)
#  5 exhausted retries

set -euo pipefail

MSG=${1:-}
if [ -z "$MSG" ]; then
  echo "Usage: $0 'message'" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

LOG_FILE="docs/current_affairs/CURRENT_AFFAIRS.md"
if [ ! -f "$LOG_FILE" ]; then
  echo "[err] $LOG_FILE not found; run from repo with initialized log." >&2
  exit 2
fi

if [ ! -x ./current_affairs_append.sh ]; then
  chmod +x ./current_affairs_append.sh || true
fi

LOCK_FILE=".current_affairs.lock"
exec 9>"$LOCK_FILE" || { echo "[err] cannot open lock file" >&2; exit 3; }
if ! flock -w 30 9; then
  echo "[err] could not acquire lock within 30s" >&2
  exit 3
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
REMOTES="${CA_REMOTES:-origin}"

# Ensure we have latest refs (primary assumes first remote)
PRIMARY_REMOTE="${REMOTES%% *}"
git fetch --prune "$PRIMARY_REMOTE"

# Rebase to integrate upstream (fast-forward or replay local commits) on primary remote
if ! git pull --rebase "$PRIMARY_REMOTE" "$BRANCH"; then
  echo "[err] rebase produced conflicts; resolve manually then re-run." >&2
  exit 4
fi

MAX_ATTEMPTS=5
attempt=1
while [ $attempt -le $MAX_ATTEMPTS ]; do
  # Append (idempotent w.r.t unique timestamp lines, but timestamps always differ so will add new line)
  ./current_affairs_append.sh "$MSG"

  # Stage & commit (squash duplicate attempts by amending if previous attempt made a commit this loop)
  if git diff --cached --quiet -- "$LOG_FILE"; then
    git add "$LOG_FILE"
  fi

  if git diff --cached --quiet; then
    # Nothing staged (maybe previous identical commit?)
    if git diff --quiet -- "$LOG_FILE"; then
      echo "[info] No changes detected after append (unexpected)." >&2
      exit 0
    fi
  fi

  if git commit -m "current affairs: $MSG"; then
    :
  else
    echo "[info] Nothing to commit (perhaps duplicate message)." >&2
    exit 0
  fi

  # Push to each remote; if primary fails we'll retry loop; failures on secondary remotes are warned only
  primary_push_ok=0
  for R in $REMOTES; do
    if git push "$R" "$BRANCH"; then
      echo "[ok] pushed to $R" >&2
      [ "$R" = "$PRIMARY_REMOTE" ] && primary_push_ok=1
    else
      if [ "$R" = "$PRIMARY_REMOTE" ]; then
        echo "[warn] primary remote push failed for $R" >&2
      else
        echo "[warn] secondary remote push failed for $R (continuing)" >&2
      fi
    fi
  done

  # Mirror to secondary root if configured (best-effort, does not affect retry logic)
  if [ -n "${CA_SECONDARY_ROOT:-}" ]; then
    if [ -d "$CA_SECONDARY_ROOT/.git" ]; then
      SECONDARY_BRANCH="${CA_SECONDARY_BRANCH:-$BRANCH}"
      mkdir -p "$CA_SECONDARY_ROOT/docs/current_affairs"
      cp "$LOG_FILE" "$CA_SECONDARY_ROOT/docs/current_affairs/CURRENT_AFFAIRS.md"
      ( cd "$CA_SECONDARY_ROOT" && \
        git fetch --prune "$PRIMARY_REMOTE" >/dev/null 2>&1 || true; \
        if git rev-parse --verify "$SECONDARY_BRANCH" >/dev/null 2>&1; then git checkout "$SECONDARY_BRANCH" >/dev/null 2>&1; fi; \
        git add docs/current_affairs/CURRENT_AFFAIRS.md; \
        if ! git diff --cached --quiet -- docs/current_affairs/CURRENT_AFFAIRS.md; then \
          git commit -m "mirror(current affairs): $MSG" >/dev/null 2>&1 || true; \
          for R2 in $REMOTES; do git push "$R2" "$SECONDARY_BRANCH" >/dev/null 2>&1 || true; done; \
        fi ) || echo "[warn] secondary root mirror failed" >&2
    else
      echo "[warn] CA_SECONDARY_ROOT does not look like a git repo: $CA_SECONDARY_ROOT" >&2
    fi
  fi

  if [ $primary_push_ok -eq 1 ]; then
    echo "[ok] appended + pushed on attempt $attempt (primary + remotes handled)" >&2
    exit 0
  fi

  echo "[warn] push failed (likely race). Attempt $attempt/$MAX_ATTEMPTS; retrying after rebase..." >&2

  # Re-fetch and rebase, then loop
  if ! git pull --rebase "$PRIMARY_REMOTE" "$BRANCH"; then
    echo "[err] rebase conflict during retry; manual resolution needed." >&2
    exit 4
  fi

  attempt=$((attempt+1))
  sleep $(( (RANDOM % 3) + 1 ))

done

echo "[err] exhausted $MAX_ATTEMPTS attempts without successful push" >&2
exit 5
