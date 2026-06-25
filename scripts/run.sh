#!/usr/bin/env bash
set -euo pipefail

python3 -c "import json; json.load(open('okcomputer.config.json', encoding='utf-8'))"
python3 r.py
