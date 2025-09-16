#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
cd "$ROOT_DIR"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 'your prompt' [model]" >&2
  exit 1
fi

PROMPT="$1"
MODEL="${2:-${OPENAI_MODEL:-gpt-4o-mini}}"
: "${MCP_SERVER_URL:=http://127.0.0.1:8001/mcp}"

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "OPENAI_API_KEY is required" >&2
  exit 2
fi

source .venv/bin/activate
python client/openai_app.py --ask "$PROMPT" --model "$MODEL" --server-url "$MCP_SERVER_URL"
