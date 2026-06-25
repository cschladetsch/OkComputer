#!/usr/bin/env bash
set -euo pipefail

require_command() {
  local name="$1"
  local install="$2"
  if ! command -v "$name" >/dev/null 2>&1; then
    echo "$name is required. Install with: $install" >&2
    exit 1
  fi
}

version_ge() {
  local actual="$1"
  local minimum="$2"
  python3 - "$actual" "$minimum" <<'PY'
import sys
from itertools import zip_longest

actual = [int(part) for part in sys.argv[1].split(".")]
minimum = [int(part) for part in sys.argv[2].split(".")]
for left, right in zip_longest(actual, minimum, fillvalue=0):
    if left > right:
        raise SystemExit(0)
    if left < right:
        raise SystemExit(1)
raise SystemExit(0)
PY
}

require_min_version() {
  local name="$1"
  local minimum="$2"
  local install="$3"
  local output
  if ! output="$("$name" --version 2>&1)"; then
    echo "$name >= $minimum is required. Install with: $install" >&2
    exit 1
  fi
  local actual
  actual="$(printf '%s' "$output" | grep -Eo '[0-9]+(\.[0-9]+){1,3}' | head -n 1)"
  if [ -z "$actual" ] || ! version_ge "$actual" "$minimum"; then
    echo "$name >= $minimum is required. Install with: $install" >&2
    exit 1
  fi
}

require_command cmake "install cmake 3.28+ via your package manager"
require_command python3 "install Python 3.11+"
require_command node "install Node.js 20 from https://nodejs.org"
require_command corepack "install Node.js 20 from https://nodejs.org"
require_min_version cmake "3.28" "install cmake 3.28+ via your package manager"
require_min_version python3 "3.11" "install Python 3.11+"
require_min_version node "20.0" "install Node.js 20 from https://nodejs.org"
corepack prepare pnpm@9.0.0 --activate
if command -v pnpm >/dev/null 2>&1; then
  PNPM=(pnpm)
else
  PNPM=(corepack pnpm)
fi
pnpm_version="$("${PNPM[@]}" --version 2>&1)"
pnpm_actual="$(printf '%s' "$pnpm_version" | grep -Eo '[0-9]+(\.[0-9]+){1,3}' | head -n 1)"
if [ -z "$pnpm_actual" ] || ! version_ge "$pnpm_actual" "9.0"; then
  echo "pnpm >= 9.0 is required. Install with: corepack enable && corepack prepare pnpm@9.0.0 --activate" >&2
  exit 1
fi

case "$(uname -s)" in
  Darwin) model_home="$HOME/Library/Application Support/okcomputer/models" ;;
  *) model_home="$HOME/.local/share/okcomputer/models" ;;
esac
mkdir -p "$model_home"
export DEEPSEEK_MODEL_HOME="$model_home"
grep -qxF "export DEEPSEEK_MODEL_HOME=\"$model_home\"" "$HOME/.bashrc" 2>/dev/null || echo "export DEEPSEEK_MODEL_HOME=\"$model_home\"" >> "$HOME/.bashrc"
grep -qxF "export DEEPSEEK_MODEL_HOME=\"$model_home\"" "$HOME/.zshrc" 2>/dev/null || echo "export DEEPSEEK_MODEL_HOME=\"$model_home\"" >> "$HOME/.zshrc"

if [ ! -d third_party/CppLmmModelStore/.git ]; then
  git submodule add https://github.com/cschladetsch/CppLmmModelStore third_party/CppLmmModelStore
fi
git submodule update --init --recursive

if [ -f third_party/CppLmmModelStore/scripts/ensure_models.py ]; then
  python3 third_party/CppLmmModelStore/scripts/ensure_models.py --config okcomputer.config.json
fi

python3 -m pip install -r bridge/requirements.txt
(cd webapp && "${PNPM[@]}" install --frozen-lockfile)
echo "Setup complete. Run scripts/build.ps1 to build."
