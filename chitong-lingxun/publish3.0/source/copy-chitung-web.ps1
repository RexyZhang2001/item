# Copy the Vue desktop workbench into the WPF publish3.0 source tree.
# Usage (from this directory):
#   powershell -ExecutionPolicy Bypass -File .\copy-chitung-web.ps1

$ErrorActionPreference = "Stop"

$SourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $SourceRoot "..\..\..")
$FrontendDir = Join-Path $RepoRoot "chitung-frontend"
$DistDir = Join-Path $FrontendDir "dist"
$TargetDir = Join-Path $SourceRoot "WacliDesktop\Assets\ChitungWeb"

if (-not (Test-Path (Join-Path $FrontendDir "package.json"))) {
    throw "chitung-frontend not found: $FrontendDir"
}

Push-Location $FrontendDir
try {
    npm install
    npm run build
}
finally {
    Pop-Location
}

if (-not (Test-Path (Join-Path $DistDir "index.html"))) {
    throw "Vue build output not found: $DistDir"
}

if (Test-Path $TargetDir) {
    Remove-Item $TargetDir -Recurse -Force
}
New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
Copy-Item (Join-Path $DistDir "*") $TargetDir -Recurse -Force

Write-Host "Copied chitung-frontend/dist -> $TargetDir"
