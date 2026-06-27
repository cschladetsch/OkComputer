Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Require-Command($Name, $Install) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Write-Error "$Name is required. Install with: $Install"
        exit 1
    }
}

function Get-VersionFromText($Text) {
    $match = [regex]::Match(($Text -join " "), "\d+(\.\d+){1,3}")
    if (-not $match.Success) {
        return $null
    }
    return [version]$match.Value
}

function Require-MinVersion($Name, $Minimum, $Install, [scriptblock]$VersionCommand) {
    try {
        $output = & $VersionCommand 2>&1
    } catch {
        Write-Error "$Name >= $Minimum is required. Install with: $Install"
        exit 1
    }
    $version = Get-VersionFromText $output
    if ($null -eq $version -or $version -lt [version]$Minimum) {
        Write-Error "$Name >= $Minimum is required. Install with: $Install"
        exit 1
    }
}

function Resolve-Python {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "python"
    )
    foreach ($candidate in $candidates) {
        try {
            $output = & $candidate --version 2>&1
            $version = Get-VersionFromText $output
            if ($null -ne $version -and $version -ge [version]"3.11") {
                return $candidate
            }
        } catch {
            continue
        }
    }
    Write-Error "python >= 3.11 is required. Install with: winget install Python.Python.3.11"
    exit 1
}

function Invoke-Pnpm {
    if (Get-Command pnpm -ErrorAction SilentlyContinue) {
        & pnpm @args
    } else {
        & corepack pnpm @args
    }
    if ($LASTEXITCODE -ne 0) {
        throw "pnpm failed with exit code $LASTEXITCODE"
    }
}

function Invoke-Native($Description, [scriptblock]$Command) {
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE"
    }
}

function Initialize-GitModules {
    if (-not (Test-Path ".gitmodules")) {
        return
    }

    $pathLines = & git config --file .gitmodules --get-regexp '^submodule\..*\.path$'
    if ($LASTEXITCODE -ne 0 -or $null -eq $pathLines) {
        return
    }

    foreach ($line in @($pathLines)) {
        $parts = $line -split '\s+', 2
        if ($parts.Count -ne 2) {
            continue
        }
        $pathKey = $parts[0]
        $path = $parts[1]
        $urlKey = $pathKey -replace '\.path$', '.url'
        $url = & git config --file .gitmodules --get $urlKey
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($url)) {
            throw "Missing URL for git module path $path"
        }
        if (-not (Test-Path $path)) {
            Invoke-Native "git clone $path" { git clone $url $path }
        }
    }
}

Require-Command cmake "winget install Kitware.CMake"
Require-Command git "winget install Git.Git"
Require-Command node "winget install OpenJS.NodeJS.LTS"
Require-Command corepack "winget install OpenJS.NodeJS.LTS"
$Python = Resolve-Python
Require-MinVersion cmake "3.28" "winget install Kitware.CMake" { cmake --version }
Require-MinVersion python "3.11" "winget install Python.Python.3.11" { & $Python --version }
Require-MinVersion node "20.0" "winget install OpenJS.NodeJS.LTS" { node --version }
Invoke-Native "corepack prepare pnpm" { corepack prepare pnpm@9.0.0 --activate }
Require-MinVersion pnpm "9.0" "corepack enable; corepack prepare pnpm@9.0.0 --activate" { Invoke-Pnpm --version }

$VenvPython = ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Invoke-Native "python venv creation" { & $Python -m venv .venv }
}
$Python = $VenvPython

$GitExe = (Get-Command git -ErrorAction Stop).Source
$GitRoot = Split-Path -Parent (Split-Path -Parent $GitExe)
$GitUsrBin = Join-Path $GitRoot "usr\bin"
if (Test-Path $GitUsrBin) {
    $env:PATH = "$GitUsrBin;$env:PATH"
}

$modelHome = if ($env:LOCALAPPDATA) { Join-Path $env:LOCALAPPDATA "OkComputer\models" } else { Join-Path $HOME "AppData\Local\OkComputer\models" }
[Environment]::SetEnvironmentVariable("DEEPSEEK_MODEL_HOME", $modelHome, "User")
$env:DEEPSEEK_MODEL_HOME = $modelHome
New-Item -ItemType Directory -Force -Path $modelHome | Out-Null

if (-not (Test-Path ".gitmodules") -and -not (Test-Path "third_party/CppLmmModelStore")) {
    Invoke-Native "CppLmmModelStore clone" { git clone https://github.com/cschladetsch/CppLmmModelStore third_party/CppLmmModelStore }
}
Initialize-GitModules

$ensure = "third_party/CppLmmModelStore/scripts/ensure_models.py"
if (Test-Path $ensure) {
    $modelNames = & $Python -c @"
import json
with open('okcomputer.config.json', encoding='utf-8') as handle:
    config = json.load(handle)
for model in config['model_store']['models']:
    print(model['name'])
"@
    $modelArgs = @("--model") + ($modelNames -split "`r?`n" | Where-Object { $_ })
    Invoke-Native "CppLmmModelStore model ensure" { & $Python $ensure @modelArgs }
}

$filteredRequirements = New-TemporaryFile
try {
    Get-Content bridge/requirements.txt |
        Where-Object { $_ -notmatch '^dbus-python==' } |
        Set-Content -Path $filteredRequirements -Encoding ASCII
    Invoke-Native "Python dependency install" { & $Python -m pip install --retries 10 --timeout 120 -r $filteredRequirements }
} finally {
    Remove-Item -LiteralPath $filteredRequirements -Force -ErrorAction SilentlyContinue
}
Push-Location webapp
Invoke-Pnpm install --frozen-lockfile
Pop-Location
Write-Host "Setup complete. Run scripts/build.ps1 to build."
