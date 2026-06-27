Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Setup = Join-Path $Root "scripts\setup.ps1"
$Build = Join-Path $Root "scripts\build.ps1"
$Run = Join-Path $Root "scripts\run.ps1"

if (-not (Test-Path $Setup)) {
    throw "Missing bootstrap script: $Setup"
}
if (-not (Test-Path $Build)) {
    throw "Missing build script: $Build"
}
if (-not (Test-Path $Run)) {
    throw "Missing run script: $Run"
}

git submodule update --init --recursive

& $Setup
& $Build
& $Run
