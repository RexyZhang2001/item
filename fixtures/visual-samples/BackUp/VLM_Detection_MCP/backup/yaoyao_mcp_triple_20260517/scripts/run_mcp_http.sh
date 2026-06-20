#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
VENV="${VENV_DIR:-$ROOT/.venv}"
# shellcheck source=/dev/null
source "$VENV/bin/activate"
if [[ -f "$ROOT/.mcp_local.env" ]]; then
  # shellcheck source=/dev/null
  source "$ROOT/.mcp_local.env"
fi
export MCP_TRANSPORT=streamable-http
export MCP_HTTP_HOST="${MCP_HTTP_HOST:-0.0.0.0}"
export MCP_HTTP_PORT="${MCP_HTTP_PORT:-8000}"
# 三图 HTTP 直链（仅项目内 8001，与 MCP 8000 分离）
export MCP_IMAGE_DELIVERY="${MCP_IMAGE_DELIVERY:-json_url}"
export MCP_ARTIFACT_HTTP_PORT="${MCP_ARTIFACT_HTTP_PORT:-8001}"
export MCP_ARTIFACT_PUBLIC_BASE="${MCP_ARTIFACT_PUBLIC_BASE:-http://10.148.1.22:8001}"
export ARTIFACT_ROOT="${ARTIFACT_ROOT:-$ROOT/output/mcp_artifacts}"
# 耀耀工厂 Bearer Token 须与此一致；未 export 则不做鉴权
# export MCP_BEARER_TOKEN='你的密钥'
# export MCP_PUBLIC_URL="http://10.148.1.22:${MCP_HTTP_PORT}"
exec python -u mcp_vlm_server.py
