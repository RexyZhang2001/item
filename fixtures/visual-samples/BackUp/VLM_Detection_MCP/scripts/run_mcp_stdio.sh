#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
VENV="${VENV_DIR:-$ROOT/.venv}"
# shellcheck source=/dev/null
source "$VENV/bin/activate"
export MCP_TRANSPORT="${MCP_TRANSPORT:-stdio}"
exec python -u mcp_vlm_server.py
