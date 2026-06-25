Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Python = if (Test-Path ".venv/Scripts/python.exe") { ".venv/Scripts/python.exe" } else { "python" }

& $Python -c "import json; json.load(open('okcomputer.config.json', encoding='utf-8'))"
New-Item -ItemType Directory -Force -Path logs | Out-Null
$bridge = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    & $using:Python -m bridge.main *> logs/bridge.log
}
$core = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    $exe = "build/win/Release/okcomputer_app.exe"
    if (Test-Path $exe) { & $exe *> logs/core.log } else { "core executable missing" *> logs/core.log; exit 1 }
}

$config = Get-Content okcomputer.config.json | ConvertFrom-Json
if ($config.webapp.open_on_start) {
    Start-Process "http://localhost:$($config.webapp.port)"
}
Write-Host "OkComputer running. Say 'Ok Computer' to begin."
Wait-Job -Any $bridge, $core | Out-Null
Stop-Job $bridge, $core -ErrorAction SilentlyContinue
