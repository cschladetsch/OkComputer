Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$action = New-ScheduledTaskAction -Execute "pwsh" -Argument "-File scripts/run.ps1"
$trigger = New-ScheduledTaskTrigger -AtLogOn
Register-ScheduledTask -TaskName "OkComputer" -Action $action -Trigger $trigger -Description "OkComputer no-admin fallback" -Force
