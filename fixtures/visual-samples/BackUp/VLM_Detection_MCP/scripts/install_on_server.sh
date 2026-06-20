#!/usr/bin/env bash
# 在 Linux 服务器 /root/VLM_Detection_MCP 内执行：安装 venv + 依赖
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== VLM_Detection_MCP 服务器安装 =="
echo "目录: $ROOT"

for f in weights/worker/yolo26x_worker.pt weights/machinery/yolo26l_machinery.pt; do
  if [[ ! -f "$f" ]]; then
    echo "错误: 缺少权重 $f"
    exit 1
  fi
done

bash scripts/setup_linux.sh mcp

echo ""
echo "安装完成。启动 MCP 服务:"
echo "  cd $ROOT"
echo "  export MCP_BEARER_TOKEN='你的密钥'"
echo "  export MCP_PUBLIC_URL=http://10.148.1.22:8000"
echo "  bash scripts/run_mcp_http.sh"
