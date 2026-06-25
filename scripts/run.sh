#!/usr/bin/env bash
set -euo pipefail

python3 -c "import json; json.load(open('okcomputer.config.json', encoding='utf-8'))"
mkdir -p logs
python3 -m bridge.main > logs/bridge.log 2>&1 &
bridge_pid=$!
if [ -x build/unix/okcomputer_app ]; then
  build/unix/okcomputer_app > logs/core.log 2>&1 &
  core_pid=$!
else
  echo "core executable missing" > logs/core.log
  kill "$bridge_pid"
  exit 1
fi
echo "OkComputer running. Say 'Ok Computer' to begin."
wait -n "$bridge_pid" "$core_pid"
kill "$bridge_pid" "$core_pid" 2>/dev/null || true
