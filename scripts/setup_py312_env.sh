#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Setting up Python 3.12 virtual environment (.venv312)"

if command -v python3.12 >/dev/null 2>&1; then
  PYBIN=$(command -v python3.12)
else
  echo "[WARN] python3.12 not found. Attempting pyenv install." >&2
  if ! command -v pyenv >/dev/null 2>&1; then
    curl -fsSL https://pyenv.run | bash
    export PATH="$HOME/.pyenv/bin:$HOME/.pyenv/shims:$PATH"
    eval "$(pyenv init -)" >/dev/null
  else
    export PATH="$HOME/.pyenv/bin:$HOME/.pyenv/shims:$PATH"
  fi
  if ! pyenv versions --bare | grep -q '^3.12.4$'; then
    pyenv install 3.12.4 -s
  fi
  PYBIN="$HOME/.pyenv/versions/3.12.4/bin/python3.12"
fi

echo "[INFO] Using Python: $PYBIN"
rm -rf .venv312
$PYBIN -m venv .venv312
source .venv312/bin/activate
python -m pip install --upgrade pip wheel setuptools
python -m pip install -r requirements.txt
if [ -f requirements-embed.txt ]; then
  python -m pip install -r requirements-embed.txt || echo "[WARN] Optional embedding deps failed; hash fallback will be used." >&2
fi

echo "[INFO] Done. Activate with: source .venv312/bin/activate"
