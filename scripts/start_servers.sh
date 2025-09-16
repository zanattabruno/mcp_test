#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
cd "$ROOT_DIR"

: "${DJANGO_PORT:=8000}"
: "${MCP_PORT:=8001}"

source .venv/bin/activate

echo "Starting Django API on :$DJANGO_PORT ..."
(
  python manage.py runserver 0.0.0.0:"$DJANGO_PORT"
) &
DJANGO_PID=$!

sleep 1

echo "Starting MCP server on :$MCP_PORT ..."
(
  uvicorn mcp_server.server:app --host 127.0.0.1 --port "$MCP_PORT" --reload
) &
MCP_PID=$!

trap 'echo Stopping...; kill $DJANGO_PID $MCP_PID 2>/dev/null || true' INT TERM EXIT

echo "PIDs: Django=$DJANGO_PID, MCP=$MCP_PID"
echo "Logs will stream below. Press Ctrl+C to stop both."

wait
