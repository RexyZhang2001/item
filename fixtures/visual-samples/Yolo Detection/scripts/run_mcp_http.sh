#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
VENV="${VENV_DIR:-$ROOT/.venv}"
# shellcheck source=/dev/null
source "$VENV/bin/activate"
export MCP_TRANSPORT=streamable-http
export MCP_HTTP_HOST="${MCP_HTTP_HOST:-0.0.0.0}"
export MCP_HTTP_PORT="${MCP_HTTP_PORT:-8000}"
# 耀耀工厂 Bearer Token 须与此一致；未 export 则不做鉴权
# export MCP_BEARER_TOKEN='你的密钥'
# export MCP_PUBLIC_URL="http://10.148.1.22:${MCP_HTTP_PORT}"
exec python -u mcp_vlm_server.py
