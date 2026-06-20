# 一键：上传 VLM_Detection_MCP 到 /root/VLM_Detection_MCP 并在服务器安装环境
# 在本机 PowerShell 运行（会提示输入 root 密码，约 2 次）
$ErrorActionPreference = "Stop"
$HostAlias = "company-linux"
$RemoteDir = "/root/VLM_Detection_MCP"
$LocalDir = "E:\3311 AI\VLM_Detection_MCP"

if (-not (Test-Path $LocalDir)) {
    Write-Error "本地目录不存在: $LocalDir"
}

Write-Host "=== 1/3 创建远程目录 ===" -ForegroundColor Cyan
ssh $HostAlias "mkdir -p $RemoteDir"

Write-Host "=== 2/3 上传文件（约 300MB+，含权重，请耐心等待）===" -ForegroundColor Cyan
scp -r "$LocalDir\*" "${HostAlias}:${RemoteDir}/"

Write-Host "=== 3/3 远程安装 Python 环境与依赖 ===" -ForegroundColor Cyan
ssh $HostAlias "chmod +x $RemoteDir/scripts/*.sh && bash $RemoteDir/scripts/install_on_server.sh"

Write-Host ""
Write-Host "部署完成。在服务器启动:" -ForegroundColor Green
Write-Host "  ssh $HostAlias"
Write-Host "  cd $RemoteDir"
Write-Host "  export MCP_BEARER_TOKEN='你的密钥'"
Write-Host "  bash scripts/run_mcp_http.sh"
