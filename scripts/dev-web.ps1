$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Web = Join-Path $Root "frontend"

if (-not (Test-Path -LiteralPath (Join-Path $Web "package.json"))) {
    Write-Host "frontend\package.json not found."
    exit 1
}

if (-not (Test-Path -LiteralPath (Join-Path $Web "node_modules"))) {
    Write-Host "Installing frontend dependencies..."
    npm install --prefix $Web
}

Write-Host "Web  http://127.0.0.1:5173"
Write-Host "API is a second terminal: scripts\dev-api.ps1"
npm --prefix $Web run dev
