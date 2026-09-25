#!/usr/bin/env bash

set -e

cd "$(dirname "$0")/../backend"

source .venv/bin/activate

python -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000
