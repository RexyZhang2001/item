#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== VLM / YOLO Linux 环境安装 =="
echo "项目目录: $ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "未找到 python3，请先安装 Python 3.10+（例如: sudo apt install python3 python3-venv python3-pip）"
  exit 1
fi

PY="${PYTHON:-python3}"
if [[ "${INSTALL_APT:-1}" == "1" ]] && command -v apt-get >/dev/null 2>&1; then
  echo "== apt 安装系统依赖（需 sudo；若不需要可设 INSTALL_APT=0）=="
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends \
    python3-venv python3-pip \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    || true
fi

VENV="${VENV_DIR:-$ROOT/.venv}"
echo "== 创建虚拟环境: $VENV =="
"$PY" -m venv "$VENV"
# shellcheck source=/dev/null
source "$VENV/bin/activate"
python -m pip install --upgrade pip

MODE="${1:-infer}"
if [[ "$MODE" == "api" ]]; then
  echo "== 安装推理 + API 依赖 =="
  pip install -r requirements.txt -r requirements-api.txt
elif [[ "$MODE" == "mcp" ]]; then
  echo "== 安装推理 + MCP 插件（Python SDK）依赖 =="
  pip install -r requirements-mcp.txt
else
  echo "== 仅安装推理依赖（流+YOLO）。若需 HTTP 插件: $0 api ；MCP: $0 mcp =="
  pip install -r requirements.txt
fi

if [[ -f "$ROOT/verify_weights.py" ]]; then
  echo "== 校验权重（可选）=="
  python verify_weights.py || echo "权重缺失时请运行: python scripts/redownload_weights.py"
fi

echo ""
echo "完成。使用前执行:"
echo "  source $VENV/bin/activate"
echo "流检测:     ./scripts/run_stream_detect.sh 'rtmp://x.x.x.x/live/test'"
echo "HTTP 插件: ./scripts/run_api.sh"
echo "MCP STDIO:  chmod +x scripts/run_mcp_stdio.sh && ./scripts/run_mcp_stdio.sh"
echo "MCP HTTP:   ./scripts/run_mcp_http.sh"
