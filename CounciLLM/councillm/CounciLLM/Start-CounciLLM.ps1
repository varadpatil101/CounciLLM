param([ValidateRange(1024,65535)][int]$Port = 8780)

$projectRoot = $PSScriptRoot
$serverScript = Join-Path $projectRoot 'backend\server.py'
$logDirectory = Join-Path $projectRoot 'logs'
$outputLog = Join-Path $logDirectory 'councillm-server.out.log'
$errorLog = Join-Path $logDirectory 'councillm-server.err.log'

if (-not (Test-Path -LiteralPath $serverScript)) {
    throw "CounciLLM backend was not found at $serverScript"
}

if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
    Write-Host "CounciLLM is already listening at http://127.0.0.1:$Port/"
    exit 0
}

$python = (Get-Command python -ErrorAction Stop).Source
New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
Start-Process -FilePath $python -ArgumentList @($serverScript, '--port', $Port) -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput $outputLog -RedirectStandardError $errorLog

for ($attempt = 0; $attempt -lt 20; $attempt++) {
    Start-Sleep -Milliseconds 500
    try {
        $health = Invoke-RestMethod "http://127.0.0.1:$Port/api/health" -TimeoutSec 2
        if ($health.status -eq 'ok') {
            Write-Host "CounciLLM is running at http://127.0.0.1:$Port/"
            exit 0
        }
    } catch { }
}

Write-Error "CounciLLM did not start. Check $errorLog"
exit 1
