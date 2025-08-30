#!/usr/bin/env bash
set -euo pipefail
echo "[quick-test] Activating env"
if [ -d .venv312 ]; then
  source .venv312/bin/activate || true
elif [ -d .venv ]; then
  source .venv/bin/activate || true
fi
echo "[quick-test] Python: $(python -V 2>/dev/null || echo none)"
echo "[quick-test] Running minimal test subset"
pytest -q tests/test_wake.py::test_wake_enable_and_detect || { echo "[quick-test] subset failed"; exit 1; }
if [ "${FULL:-false}" = "true" ]; then
  echo "[quick-test] Running full suite"; pytest -q || { echo "[quick-test] full suite failed"; exit 1; }
fi
echo "[quick-test] OK"
