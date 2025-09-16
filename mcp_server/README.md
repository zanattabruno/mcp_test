# Meeting Scheduler MCP Server

This folder contains a small MCP server that bridges to the Django + DRF Meeting Scheduler API in this repo.

It provides:
- FastAPI app with `/health` endpoint
- MCP Streamable HTTP transport mounted at `/mcp`
- Tools to list/create clients and meetings against the scheduler REST API

Env vars
- `SCHEDULER_API_BASE`: Base URL of the DRF API (default `http://localhost:8000/api`)

Quick start
1) Start the Django API (in another terminal):
	- Create venv, install deps, migrate, and run server.
2) Install deps for this repo's venv:
	- `pip install -r requirements.txt`
3) Run the MCP server:
	- `uvicorn mcp_server.server:app --reload --port 8001`
4) Check health:
	- `curl http://localhost:8001/health`

Try MCP
- With MCP Inspector or any Streamable HTTP client, connect to `http://localhost:8001/mcp`.
- Available tools: `api_info`, `list_clients`, `create_client`, `list_meetings`, `create_meeting`.

Notes
- Datetime format must be ISO-8601 with timezone (UTC preferred), e.g. `2025-09-16T10:00:00Z`.
- Overlap validation is per-client, enforced by the API. Errors are surfaced back from `create_meeting`.
