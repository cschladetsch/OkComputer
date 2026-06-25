Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Python = if (Test-Path ".venv/Scripts/python.exe") { ".venv/Scripts/python.exe" } else { "python" }

& $Python -c "import json; json.load(open('okcomputer.config.json', encoding='utf-8'))"
& $Python r.py
