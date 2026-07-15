$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Resolve-Path (Join-Path $scriptDir "..")

Set-Location (Join-Path $rootDir "frontend")
if (Test-Path "package.json") {
  npm install
  npm run build
}

Set-Location $rootDir
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
