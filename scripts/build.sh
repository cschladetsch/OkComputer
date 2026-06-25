#!/usr/bin/env bash
set -euo pipefail

cmake -B build/unix -S core -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build build/unix --config Release --parallel
ctest --test-dir build/unix --output-on-failure

python3 -m mypy bridge --strict
python3 -m pytest tests/ -x -v

(cd webapp && pnpm install --frozen-lockfile && pnpm run type-check && pnpm run lint && pnpm run test --run && pnpm run build)
echo "Build complete."
