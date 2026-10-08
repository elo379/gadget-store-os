#!/bin/sh
set -eu

if [ -n "${GSOS_PRODUCTION_ACTIVATION_DIGESTS:-}" ]; then
    python -m scripts.manage_activation_codes seed-production-digests
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers
