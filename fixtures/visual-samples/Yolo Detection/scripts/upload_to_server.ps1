# 从 Windows 上传 Yolo Detection 到云服务器（需本机可 ssh root@10.148.1.22）
param(
    [string]$HostAlias = "company-linux",
    [string]$RemoteDir = "/root/vlm-yolo",
    [string]$LocalDir = "E:\3311 AI\Yolo Detection"
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path $LocalDir)) {
    Write-Error "本地目录不存在: $LocalDir"
}

Write-Host "上传到 ${HostAlias}:${RemoteDir} ..."
ssh $HostAlias "mkdir -p $RemoteDir"
scp -r "$LocalDir\*" "${HostAlias}:${RemoteDir}/"
Write-Host "完成。请在服务器执行:"
Write-Host "  cd $RemoteDir && bash scripts/setup_linux.sh mcp"
Write-Host "  export MCP_BEARER_TOKEN='你的密钥' && bash scripts/run_mcp_http.sh"
