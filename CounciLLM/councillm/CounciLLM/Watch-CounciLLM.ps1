param(
    [Parameter(Mandatory = $true)][int]$ParentPid,
    [Parameter(Mandatory = $true)][int]$ServerPid
)

# This helper intentionally outlives the launcher window.  Once the launcher
# closes, it terminates only the Python server process that launcher started.
while (Get-Process -Id $ParentPid -ErrorAction SilentlyContinue) {
    Start-Sleep -Milliseconds 500
}

$server = Get-Process -Id $ServerPid -ErrorAction SilentlyContinue
if ($server) { Stop-Process -Id $ServerPid -Force }
