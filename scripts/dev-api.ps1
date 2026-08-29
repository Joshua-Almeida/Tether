$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Backend = Join-Path $Root "backend"
$AppDir = Join-Path $Backend "app"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"
$Url = "http://127.0.0.1:8765"

if (-not (Test-Path -LiteralPath $Python)) {
    Write-Host "Missing backend\.venv. From the repo root run:"
    Write-Host "  python -m venv backend\.venv"
    Write-Host "  .\backend\.venv\Scripts\Activate.ps1"
    Write-Host "  pip install -r backend\requirements.txt"
    exit 1
}

try {
    $probe = Invoke-WebRequest -Uri "$Url/" -UseBasicParsing -TimeoutSec 3
    if ($probe.Content -match "Tether API") {
        Write-Host "API already running at $Url"
        Write-Host "Open http://127.0.0.1:5173  (second terminal: scripts\dev-web.ps1)"
        exit 0
    }
} catch {
}

$env:PYTHONPATH = $Backend
Write-Host "API  $Url"
Write-Host "Web is a second terminal: scripts\dev-web.ps1"
& $Python -m uvicorn app.main:app --reload --reload-dir $AppDir --app-dir $Backend --host 127.0.0.1 --port 8765
