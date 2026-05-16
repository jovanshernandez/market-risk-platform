#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../app"
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn market_risk_platform.api:app --reload --host 127.0.0.1 --port 8000
