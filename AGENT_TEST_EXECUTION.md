# Agent Test Execution Guide

This repository exposes a consistent command the Copilot (or any automation agent) can invoke to run Python tests for the indexer/RAG system.

## Primary Command
Run all tests:
```
bash run_tests.sh
```
Pass additional pytest selectors / options:
```
bash run_tests.sh -k rag_query
```
Fail fast (first failure):
```
FAST=1 bash run_tests.sh
```

## Script Behavior (`run_tests.sh`)
1. Ensures a Python virtual environment at `.venv` (creates if absent).
2. Installs `dev-indexer_1/requirements.txt` (if not already installed) and `pytest`.
3. Executes `pytest` against `dev-indexer_1/tests` quietly (`-q`).
4. Propagates pytest exit code for CI / agent evaluation.

## VS Code Task
Added a task:
```
Label: Run All Tests
Command: bash run_tests.sh
Group: test
```
Invoke via: Command Palette → Run Task → Run All Tests.

## Expected Exit Codes
| Code | Meaning |
|------|---------|
| 0 | All tests passed |
| 1 | Test failures occurred |
| >1 | Infrastructure / invocation error (environment, import, etc.) |

## Agent Integration Hints
| Step | Action |
|------|--------|
| Verify | Check script exists: `test -f run_tests.sh` |
| Dry Run | `bash run_tests.sh -k smoke || true` |
| Full | `bash run_tests.sh` and parse final line summary |

## Adding New Tests
Place new test modules under `dev-indexer_1/tests/` using `test_*.py` naming.

## Future Enhancements
* Add coverage: integrate `coverage run -m pytest` and emit XML.
* Add API trigger endpoint (`/internal/run-tests`) guarded by token.
* Add Git hook or CI workflow for automated execution.

---
This doc is optimized for autonomous agents needing deterministic test invocation.
