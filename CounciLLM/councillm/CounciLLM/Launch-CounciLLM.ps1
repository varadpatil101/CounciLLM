param([ValidateRange(1024,65535)][int]$Port = 8780)

$projectRoot = $PSScriptRoot
$serverScript = Join-Path $projectRoot 'backend\server.py'
$watcherScript = Join-Path $projectRoot 'Watch-CounciLLM.ps1'
$logDirectory = Join-Path $projectRoot 'logs'
$outputLog = Join-Path $logDirectory 'councillm-launcher.out.log'
$errorLog = Join-Path $logDirectory 'councillm-launcher.err.log'

if (-not (Test-Path -LiteralPath $serverScript)) {
    throw "CounciLLM backend was not found at $serverScript"
}
if (-not (Test-Path -LiteralPath $watcherScript)) {
    throw "CounciLLM shutdown helper was not found at $watcherScript"
}

if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
    Write-Host "CounciLLM is already running at http://127.0.0.1:$Port/"
    Start-Process "http://127.0.0.1:$Port/"
    Write-Host 'This launcher did not start that existing server, so closing this window will not stop it.'
    Read-Host 'Press Enter to close this launcher'
    exit 0
}

$python = (Get-Command python -ErrorAction Stop).Source
New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
Write-Host 'Starting CounciLLM locally…'
$server = Start-Process -FilePath $python -ArgumentList @($serverScript, '--port', $Port) -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput $outputLog -RedirectStandardError $errorLog -PassThru
$watcher = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $watcherScript, '-ParentPid', $PID, '-ServerPid', $server.Id) -WindowStyle Hidden -PassThru

try {
    $ready = $false
    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        if ($server.HasExited) { throw "The server stopped while starting. Check $errorLog" }
        try {
            $health = Invoke-RestMethod "http://127.0.0.1:$Port/api/health" -TimeoutSec 2
            if ($health.status -eq 'ok') { $ready = $true; break }
        } catch { }
        Start-Sleep -Milliseconds 500
    }
    if (-not $ready) { throw "CounciLLM did not become ready. Check $errorLog" }
    Write-Host "CounciLLM is ready: http://127.0.0.1:$Port/"
    Write-Host 'Keep this window open while using CounciLLM. Closing it stops the local server.'
    Start-Process "http://127.0.0.1:$Port/"
    Wait-Process -Id $server.Id
} finally {
    if (-not $server.HasExited) { Stop-Process -Id $server.Id -Force }
    if (-not $watcher.HasExited) { Stop-Process -Id $watcher.Id -Force }
}
