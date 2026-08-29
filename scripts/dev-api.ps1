$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python)) {
    Write-Host "Missing backend\.venv. From the repo root run:"
    Write-Host "  python -m venv backend\.venv"
    Write-Host "  .\backend\.venv\Scripts\Activate.ps1"
    Write-Host "  pip install -r backend\requirements.txt"
    exit 1
}

$env:PYTHONPATH = $Backend
Set-Location -LiteralPath $Backend
Write-Host "API  http://127.0.0.1:8000   (PYTHONPATH=$Backend)"
Write-Host "Do not run npm from backend. Web UI is .\scripts\dev-web.ps1"
& $Python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
