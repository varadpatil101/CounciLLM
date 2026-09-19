param([ValidateRange(1024,65535)][int]$Port = 8780)

$listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if (-not $listeners) {
    Write-Host "CounciLLM is not running on port $Port."
    exit 0
}

foreach ($listener in $listeners) {
    $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $($listener.OwningProcess)"
    if ($processInfo.CommandLine -notmatch 'backend[\\/]server\.py') {
        Write-Warning "Port $Port is owned by a different process ($($processInfo.Name)); it was not stopped."
        continue
    }
    Stop-Process -Id $listener.OwningProcess -Force
    Write-Host "CounciLLM stopped on port $Port."
}
