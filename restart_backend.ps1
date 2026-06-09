Write-Host "Stopping any process listening on port 8000..."
# Find PID listening on 8000 (IPv4)
$port = 8000
$listenerPid = (Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -First 1).OwningProcess
if ($listenerPid) {
    Write-Host "Killing PID $listenerPid"
    Stop-Process -Id $listenerPid -Force
    Start-Sleep -Seconds 2
} else {
    Write-Host "No process found on port $port."
}

# Create/use virtual environment and start FastAPI
$backendDir = Join-Path $PSScriptRoot "backend"
Set-Location $backendDir
if (-Not (Test-Path .\venv)) {
    python -m venv venv
}
$python = Join-Path $backendDir "venv\Scripts\python.exe"
& $python -m pip install -r requirements.txt
Write-Host "Launching FastAPI..."
& $python main.py
