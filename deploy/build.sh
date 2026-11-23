#!/bin/sh
set -eu
cd "$(dirname "$0")/.."

python -B tools/check_uf_map.py
python -m pip install --only-binary=:all: -r requirements.txt
python -B tools/snapshot.py install --target "${SUSEP_DATA_DIR:-data/curated}"
