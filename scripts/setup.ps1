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
}

Require-Command cmake "winget install Kitware.CMake"
Require-Command node "winget install OpenJS.NodeJS.LTS"
Require-Command corepack "winget install OpenJS.NodeJS.LTS"
$Python = Resolve-Python
Require-MinVersion cmake "3.28" "winget install Kitware.CMake" { cmake --version }
Require-MinVersion python "3.11" "winget install Python.Python.3.11" { & $Python --version }
Require-MinVersion node "20.0" "winget install OpenJS.NodeJS.LTS" { node --version }
corepack prepare pnpm@9.0.0 --activate
Require-MinVersion pnpm "9.0" "corepack enable; corepack prepare pnpm@9.0.0 --activate" { Invoke-Pnpm --version }

$modelHome = if ($env:LOCALAPPDATA) { Join-Path $env:LOCALAPPDATA "OkComputer\models" } else { Join-Path $HOME "AppData\Local\OkComputer\models" }
[Environment]::SetEnvironmentVariable("DEEPSEEK_MODEL_HOME", $modelHome, "User")
$env:DEEPSEEK_MODEL_HOME = $modelHome
New-Item -ItemType Directory -Force -Path $modelHome | Out-Null

if (-not (Test-Path "third_party/CppLmmModelStore/.git")) {
    git submodule add https://github.com/cschladetsch/CppLmmModelStore third_party/CppLmmModelStore
}
git submodule update --init --recursive

$ensure = "third_party/CppLmmModelStore/scripts/ensure_models.py"
if (Test-Path $ensure) {
    & $Python $ensure --config okcomputer.config.json
}

& $Python -m pip install -r bridge/requirements.txt
Push-Location webapp
Invoke-Pnpm install --frozen-lockfile
Pop-Location
Write-Host "Setup complete. Run scripts/build.ps1 to build."
