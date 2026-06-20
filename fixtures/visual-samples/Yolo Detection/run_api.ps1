# 本地启动 HiAgent HTTP 插件（供联调；上云请用 Docker + HTTPS 反代）
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Find-CondaPython([string]$Name) {
    $conda = "conda"
    if (Test-Path "D:\anaconda\Scripts\conda.exe") { $conda = "D:\anaconda\Scripts\conda.exe" }
    $line = & $conda env list | Select-String "^\s*$Name\s"
    if ($line) {
        $prefix = ($line.ToString() -split '\s+', 3)[1]
        return Join-Path $prefix "python.exe"
    }
    return $null
}

$Py = Find-CondaPython "vlm_detection"
if (-not $Py) {
    Write-Host "请先: powershell -File setup_env.ps1"
    exit 1
}

& $Py -m pip install -r requirements-api.txt -q
$port = if ($env:PORT) { $env:PORT } else { "8080" }
Write-Host "API http://127.0.0.1:$port/docs"
Write-Host "健康检查: http://127.0.0.1:$port/health"
& $Py -m uvicorn hiagent_api:app --host 0.0.0.0 --port $port
