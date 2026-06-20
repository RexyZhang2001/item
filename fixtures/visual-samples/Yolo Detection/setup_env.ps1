# 创建/更新 VLM-Detection 推理环境（conda，避免中文路径下 venv 的 PyTorch DLL 问题）
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$EnvName = "vlm_detection"
$Conda = "conda"
if (Test-Path "D:\anaconda\Scripts\conda.exe") { $Conda = "D:\anaconda\Scripts\conda.exe" }
elseif (Test-Path "D:\Anaconda\Scripts\conda.exe") { $Conda = "D:\Anaconda\Scripts\conda.exe" }

$exists = & $Conda env list | Select-String "^\s*$EnvName\s"
if (-not $exists) {
    Write-Host "创建 conda 环境: $EnvName (Python 3.10) ..."
    & $Conda create -n $EnvName python=3.10 -y
}

$Py = & $Conda env list | Select-String "^\s*$EnvName\s" | ForEach-Object { ($_ -split '\s+')[1] }
if (-not $Py) { throw "未找到 conda 环境 $EnvName" }
$Python = Join-Path $Py.Trim() "python.exe"

Write-Host "安装 PyTorch (conda cpu) ..."
& $Conda install -n $EnvName pytorch torchvision cpuonly -c pytorch -y

Write-Host "安装推理依赖到 $EnvName ..."
& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt

Write-Host "验证权重加载 ..."
& $Python verify_weights.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "环境就绪。激活: conda activate $EnvName"
Write-Host "校验权重: python verify_weights.py"
Write-Host "检测示例: python detect.py --source input --save-img --export-json"
