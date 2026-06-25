Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Python = if (Test-Path ".venv/Scripts/python.exe") { ".venv/Scripts/python.exe" } else { "python" }
function Invoke-Pnpm {
    if (Get-Command pnpm -ErrorAction SilentlyContinue) {
        & pnpm @args
    } else {
        & corepack pnpm @args
    }
}

cmake -B build/win -S core -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build build/win --config Release --parallel
ctest --test-dir build/win -C Release --output-on-failure

& $Python -m mypy bridge --strict
& $Python -m pytest tests/ -x -v

Push-Location webapp
Invoke-Pnpm install --frozen-lockfile
Invoke-Pnpm run type-check
Invoke-Pnpm run lint
Invoke-Pnpm run test --run
Invoke-Pnpm run build
Pop-Location

Write-Host "Build complete."
