# MCP Meeting Scheduler (Django + DRF + FastAPI)

Primary goal: demonstrate MCP capabilities in a simple, self-contained environment.

End-to-end example of a Meeting Scheduler REST API (Django + DRF) with a FastAPI-based MCP bridge server and simple client utilities. Schedule meetings per client with overlap prevention, explore OpenAPI docs, and drive actions via MCP tools or OpenAI tool-calling.

## What’s inside

- Django REST API (folder `scheduler/`, app `api/`) with models:
  - `Client` (name, email, phone)
  - `Meeting` (client, title, start_time, end_time) with per-client overlap prevention
- FastAPI MCP server (`mcp_server/server.py`) exposing tools that call the DRF API
- Example clients (`client/`) and shell scripts (`scripts/`) to run servers and call tools
- OpenAPI docs via drf-spectacular at `/api/schema/` and `/api/docs/`

Repo layout
- `api/` — Models, serializers, views, tests
- `scheduler/` — Django project (settings, urls) — see [`scheduler/README.md`](scheduler/README.md)
- `mcp_server/` — FastAPI MCP bridge (`/mcp`, `/health`)
- `client/` — Simple CLI for listing tools and asking a question with OpenAI
- `scripts/` — Helper scripts to run servers and call tools

## Prerequisites

- Python 3.12+
- Bash shell (for scripts on Linux/macOS)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run it (API + MCP)

Option A — one command (recommended):
```bash
scripts/start_servers.sh
```

Option B — manual in two terminals:

Terminal 1 (Django API):
```bash
source .venv/bin/activate
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Terminal 2 (MCP server):
```bash
source .venv/bin/activate
uvicorn mcp_server.server:app --host 127.0.0.1 --port 8001 --reload
```

Health & docs
- MCP health: http://127.0.0.1:8001/health
- OpenAPI JSON: http://localhost:8000/api/schema/
- Swagger UI: http://localhost:8000/api/docs/

Optional seed data
```bash
scripts/load_clients_fixture.sh
# or management command
python manage.py seed_clients        # add missing
python manage.py seed_clients --reset # reset and add
```

## REST API quick reference

Endpoints
- `POST /api/clients/` — create client
- `GET /api/clients/` — list clients
  - Filters: `email`, `search`
  - Ordering: `name`, `created_at`
- `POST /api/meetings/` — schedule meeting
- `GET /api/meetings/` — list meetings
  - Filters: `client`, `title`
  - Time window: `start` and/or `end` (ISO-8601)

Validation rules
- `end_time` must be strictly greater than `start_time`
- No overlapping meetings for the same client (different clients can overlap)
- Datetimes must be ISO-8601 with timezone (UTC preferred), e.g. `2025-09-16T10:00:00Z`

Curl examples

Create client:
```bash
curl -sS -X POST http://localhost:8000/api/clients/ \
  -H 'Content-Type: application/json' \
  -d '{"name":"Acme","email":"acme@example.com","phone":"+1-555"}'
```

Schedule meeting (use returned client `id`):
```bash
START=$(date -u -d '+1 hour' --iso-8601=seconds)
END=$(date -u -d '+2 hour' --iso-8601=seconds)
CLIENT_ID=1
curl -sS -X POST http://localhost:8000/api/meetings/ \
  -H 'Content-Type: application/json' \
  -d "{\"client\":$CLIENT_ID,\"title\":\"Kickoff\",\"start_time\":\"$START\",\"end_time\":\"$END\"}"
```

Attempt overlap (should return 400):
```bash
curl -sS -X POST http://localhost:8000/api/meetings/ \
  -H 'Content-Type: application/json' \
  -d "{\"client\":$CLIENT_ID,\"title\":\"Overlap\",\"start_time\":\"$START\",\"end_time\":\"$END\"}"
```

List meetings for client 1:
```bash
curl -sS 'http://localhost:8000/api/meetings/?client=1'
```

## MCP tools and examples

Tools exposed at `http://127.0.0.1:8001/mcp`:
- `api_info` — returns basic API info
- `list_clients(name|search)` — maps to DRF `search`
- `create_client(name, email, phone)`
- `list_meetings(client_id?, title?, start?, end?)`
- `create_meeting(client, title, start_time, end_time)`

Scripted usage (no OpenAI key required):
```bash
scripts/mcp_list_tools.sh
scripts/mcp_call_tool.sh list_clients
scripts/mcp_call_tool.sh create_client '{"name":"Alice","email":"alice@example.com","phone":"+1-555"}'

START=$(date -u -d '+1 hour' --iso-8601=seconds)
END=$(date -u -d '+2 hour' --iso-8601=seconds)
scripts/mcp_call_tool.sh create_meeting "{\"client\":1,\"title\":\"Kickoff\",\"start_time\":\"$START\",\"end_time\":\"$END\"}"
```

Chat via OpenAI tool-calling (requires `OPENAI_API_KEY`):
```bash
export OPENAI_API_KEY=sk-...
# optional
# export OPENAI_MODEL=gpt-4o-mini
# export MCP_SERVER_URL=http://127.0.0.1:8001/mcp
scripts/mcp_chat.sh "Create a client named Alice and list meetings"
```

### `scripts/mcp_chat.sh` usage

Synopsis
- `scripts/mcp_chat.sh "<prompt>" [MODEL]` — single-turn chat where the model can call MCP tools
- `scripts/mcp_chat.sh` — interactive chat mode (multi-turn in the same session)

Defaults
- `OPENAI_MODEL` or positional `[MODEL]` controls the model; default is `gpt-4o-mini`.
- `MCP_SERVER_URL` defaults to `http://127.0.0.1:8001/mcp`.
- Requires `OPENAI_API_KEY` and an active venv with repo deps installed.

Examples
```bash
# Single turn (uses OPENAI_MODEL or defaults)
export OPENAI_API_KEY=sk-...
scripts/mcp_chat.sh "Create a client named Alice (alice@example.com) then list clients"

# Override the model via argument
scripts/mcp_chat.sh "List meetings for client 1 this week" gpt-4o-mini

# Interactive session (no prompt argument)
scripts/mcp_chat.sh
# Then type prompts; the model will call tools as needed.

# Point at a non-default MCP server URL
export MCP_SERVER_URL=http://localhost:8001/mcp
scripts/mcp_chat.sh "Schedule a 30-minute meeting for client 1 tomorrow at 10:00 UTC"
```

Notes
- The assistant uses tool-calling to hit the MCP server which proxies to the Django API. Actions like creating clients/meetings will persist in SQLite.
- If you see "OPENAI_API_KEY is required", export your key and re-run.
- Ensure both servers are running (see “Run it” above) before chatting, or tool calls will fail.

## Scripts

- `scripts/start_servers.sh` — start Django API and MCP server together
- `scripts/mcp_list_tools.sh` — list available MCP tools
- `scripts/mcp_call_tool.sh TOOL [JSON|@file]` — call an MCP tool
- `scripts/mcp_chat.sh "..."` — single-turn OpenAI chat with tool-calling
- `scripts/load_clients_fixture.sh` — load demo clients fixture
- `scripts/clients.sh` — curl helpers for Clients CRUD and queries

## Testing

Run the Django tests (includes overlap validation tests):
```bash
python manage.py test
```
See `api/tests.py` for coverage.

## Environment variables

- `DJANGO_PORT` — Used by `scripts/start_servers.sh` (default `8000`)
- `MCP_PORT` — Used by `scripts/start_servers.sh` (default `8001`)
- `SCHEDULER_API_BASE` — MCP target API base (default `http://localhost:8000/api`)
- `MCP_SERVER_URL` — Client URL to MCP (default `http://127.0.0.1:8001/mcp`)
- `OPENAI_API_KEY` — Required for `scripts/mcp_chat.sh` and `client/openai_app.py --ask`
- `OPENAI_MODEL` — Optional model override (e.g., `gpt-4o-mini`)

## Troubleshooting

- 400 overlap error when creating a meeting
  - This is expected if a meeting for the same client overlaps the requested time window.
- Datetime rejected or wrong timezone
  - Ensure ISO-8601 with timezone, e.g. `2025-09-16T10:00:00Z`.
- MCP server can’t reach API
  - Check `SCHEDULER_API_BASE` and that Django API is running on `http://localhost:8000`.
- Port already in use
  - Change ports or stop the process using `8000/8001`.
- SQLite “database is locked”
  - Stop stray servers or wait briefly; SQLite allows one writer at a time.

Admin is available at `/admin` if you create a superuser.