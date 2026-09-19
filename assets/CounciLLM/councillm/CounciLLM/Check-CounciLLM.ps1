param([ValidateRange(1024,65535)][int]$Port = 8780)

$listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $listener) {
    Write-Host "CounciLLM is OFF (nothing is listening on port $Port)." -ForegroundColor Yellow
    exit 0
}

$processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $($listener.OwningProcess)"
if ($processInfo.CommandLine -match 'backend[\\/]server\.py') {
    Write-Host "CounciLLM is ON at http://127.0.0.1:$Port/ (process $($listener.OwningProcess))." -ForegroundColor Green
} else {
    Write-Host "Port $Port is ON, but it is being used by $($processInfo.Name), not CounciLLM." -ForegroundColor Yellow
}
