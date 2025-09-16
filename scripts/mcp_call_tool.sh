#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
cd "$ROOT_DIR"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 TOOL_NAME [JSON_ARGS|@file.json]" >&2
  exit 1
fi

TOOL="$1"
ARGS_JSON="${2:-}"
: "${MCP_SERVER_URL:=http://127.0.0.1:8001/mcp}"

source .venv/bin/activate
python client/mcp_tool_cli.py --server-url "$MCP_SERVER_URL" --tool "$TOOL" ${ARGS_JSON:+--args "$ARGS_JSON"}
