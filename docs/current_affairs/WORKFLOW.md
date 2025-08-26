# Current Affairs Shared Update Workflow

This document explains how multiple contributors (agents or humans) append synchronized entries to `CURRENT_AFFAIRS.md` across different clones / environments with minimal merge friction.

## Files Involved
- `docs/current_affairs/CURRENT_AFFAIRS.md`  – canonical chronological log (append-only; one entry per line)
- `current_affairs_append.sh` – simple append utility (adds a UTC timestamped line) – local only
- `scripts/current_affairs_git_worker.sh` – automation: pull (rebase) -> append -> commit -> push (+ optional multi-remote + optional mirroring)

## Standard Single-Repo Usage
```bash
# From repo root
scripts/current_affairs_git_worker.sh "Added conceptual retrieval experiment notes"
```
The script will:
1. Acquire an exclusive local lock (`.current_affairs.lock`).
2. `git pull --rebase` (primary remote).
3. Append timestamped line.
4. Commit with message: `current affairs: <your text>`.
5. Push (retry on race up to 5 attempts).

## Multi-Remote Push (Optional)
If you want to push the same commit to multiple remotes (they must already be configured in git):
```bash
CA_REMOTES="origin upstream" scripts/current_affairs_git_worker.sh "Syncing across forks"
```
Primary remote = first in the list (used for retry logic).

## Mirroring to a Secondary Repo Root (Optional)
If you maintain a second clone / root (e.g., another deployment mirror):
```bash
export CA_SECONDARY_ROOT="/path/to/other/clone"
# Optional different branch name for the mirror
export CA_SECONDARY_BRANCH="main"

scripts/current_affairs_git_worker.sh "Mirror test entry"
```
After primary push succeeds, the script copies the updated markdown into the secondary root, commits (if changed), and pushes (best‑effort; does not retry conflicts there).

## Minimal Expectations for Contributors
1. Do not hand-edit existing lines (append only).
2. Keep each entry one line: `- <ISO-UTC> <message>` (script enforces format).
3. Run the worker script instead of manual add/commit to minimize conflicts.
4. Pull (rebase) first if you *must* edit manually.

## Conflict Handling
If a rebase conflict occurs (rare if only appending), the script stops with exit code 4. Resolve manually:
```bash
git status  # inspect
# Edit file, keep all unique lines
git add docs/current_affairs/CURRENT_AFFAIRS.md
git rebase --continue
scripts/current_affairs_git_worker.sh "Retry previous message if needed"
```

## Fallback (Manual Flow)
If automation script unavailable:
```bash
git pull --rebase
./current_affairs_append.sh "Your message"
git add docs/current_affairs/CURRENT_AFFAIRS.md
git commit -m "current affairs: Your message"
git push
```

## Environment Variables Summary
| Var | Purpose | Default |
|-----|---------|---------|
| `CA_REMOTES` | Space separated list of git remotes to push | `origin` |
| `CA_SECONDARY_ROOT` | Path to another repo root to mirror file into | unset |
| `CA_SECONDARY_BRANCH` | Branch in secondary root | current primary branch |

## Recommended Makefile Target (Optional)
Add this to `Makefile` if convenient:
```
current-affairs:
	@scripts/current_affairs_git_worker.sh "$(MSG)"
```
Invoke with: `make current-affairs MSG="Your message"`

---
Questions / improvements: consider an API endpoint, Slack/webhook notifier, or JSONL store if line-based merges become hot.
