# 一键检测（优先 vlm_detection，否则 yolo_v8）
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
if (-not $Py) { $Py = Find-CondaPython "yolo_v8" }
if (-not $Py) {
    Write-Host "请先运行: powershell -ExecutionPolicy Bypass -File setup_env.ps1"
    exit 1
}

$argsList = @("detect.py", "--source", "input", "--save-img", "--export-json")
if ($args.Count -gt 0) { $argsList += $args }

& $Py @argsList
