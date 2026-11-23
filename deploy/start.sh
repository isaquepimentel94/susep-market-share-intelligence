#!/bin/sh
set -eu
cd "$(dirname "$0")/.."

export SUSEP_DATA_DIR="${SUSEP_DATA_DIR:-data/curated}"
unset SUSEP_PARQUETS_ARTIFACT_URL
exec python -B server.py
