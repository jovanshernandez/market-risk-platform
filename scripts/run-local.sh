#!/usr/bin/env bash
# Create the repo virtualenv if needed, install dependencies, and start the API with reload.
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
.venv/bin/python -m pip install --quiet -r app/requirements-dev.txt

cd app
exec ../.venv/bin/python -m uvicorn market_risk_platform.api:app --reload --host 127.0.0.1 --port 8000
