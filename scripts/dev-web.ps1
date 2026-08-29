$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Web = Join-Path $Root "frontend"

if (-not (Test-Path -LiteralPath (Join-Path $Web "package.json"))) {
    Write-Host "frontend\package.json not found."
    exit 1
}

Set-Location -LiteralPath $Web
if (-not (Test-Path -LiteralPath (Join-Path $Web "node_modules"))) {
    Write-Host "Installing frontend dependencies..."
    npm install
}

Write-Host "Web  http://127.0.0.1:5173  (strict port; stop other Vite if bind fails)"
Write-Host "Do not run this from backend. API is .\scripts\dev-api.ps1"
npm run dev
