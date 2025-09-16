#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
cd "$ROOT_DIR"

: "${MCP_SERVER_URL:=http://127.0.0.1:8001/mcp}"

source .venv/bin/activate
python client/openai_app.py --list-tools --server-url "$MCP_SERVER_URL"
