# Meeting Scheduler API

Simple Django + DRF service to manage Clients and schedule Meetings with overlap prevention per client.

## Quickstart

1) Create venv and install deps

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Migrate database

```bash
python manage.py migrate
```

3) Run server

```bash
python manage.py runserver 0.0.0.0:8000
```

4) Explore docs

- OpenAPI JSON: http://localhost:8000/api/schema/
- Swagger UI: http://localhost:8000/api/docs/

## End-to-End (API + MCP + Client)

Run the Django API, the MCP bridge server, and a client to drive tools/chat.

- Option A — one command (recommended):

```bash
scripts/start_servers.sh
```

- Option B — manual in two terminals:

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

Once both are running:

- List MCP tools (no OpenAI key needed):
```bash
scripts/mcp_list_tools.sh
```

- Call a tool directly (no OpenAI):
```bash
# List clients
scripts/mcp_call_tool.sh list_clients

# Create a client
scripts/mcp_call_tool.sh create_client '{"name":"Alice","email":"alice@example.com","phone":"+1-555"}'

# Create a meeting (adjust client id)
START=$(date -u -d '+1 hour' --iso-8601=seconds)
END=$(date -u -d '+2 hour' --iso-8601=seconds)
scripts/mcp_call_tool.sh create_meeting "{\"client\":1,\"title\":\"Kickoff\",\"start_time\":\"$START\",\"end_time\":\"$END\"}"
```

- Chat via OpenAI (requires `OPENAI_API_KEY`):
```bash
export OPENAI_API_KEY=sk-...  # required
# Optional overrides
# export OPENAI_MODEL=gpt-4o-mini
# export MCP_SERVER_URL=http://127.0.0.1:8001/mcp

scripts/mcp_chat.sh "Create a client named Alice and list meetings"
```

Optional: load demo clients
```bash
scripts/load_clients_fixture.sh
```

## Endpoints

- `POST /api/clients/` create client
- `GET /api/clients/` list clients
- `POST /api/meetings/` schedule meeting
- `GET /api/meetings/` list meetings (filters: `client`, `start`, `end`)

## Curl examples

Create client:

```bash
curl -sS -X POST http://localhost:8000/api/clients/ \
  -H 'Content-Type: application/json' \
  -d '{"name":"Acme","email":"acme@example.com","phone":"+1-555"}'
```

Schedule meeting (use returned `id` as client):

```bash
START=$(date -u -d '+1 hour' --iso-8601=seconds)
END=$(date -u -d '+2 hour' --iso-8601=seconds)
CLIENT_ID=1
curl -sS -X POST http://localhost:8000/api/meetings/ \
  -H 'Content-Type: application/json' \
  -d "{\"client\":$CLIENT_ID,\"title\":\"Kickoff\",\"start_time\":\"$START\",\"end_time\":\"$END\"}"
```

Attempt overlap (should 400):

```bash
curl -sS -X POST http://localhost:8000/api/meetings/ \
  -H 'Content-Type: application/json' \
  -d "{\"client\":$CLIENT_ID,\"title\":\"Overlap\",\"start_time\":\"$START\",\"end_time\":\"$END\"}"
```

List meetings:

```bash
curl -sS 'http://localhost:8000/api/meetings/?client=1'
```

## Environment

- `DJANGO_PORT`: Port for Django API in `scripts/start_servers.sh` (default `8000`).
- `MCP_PORT`: Port for MCP server in `scripts/start_servers.sh` (default `8001`).
- `SCHEDULER_API_BASE`: MCP server target API base (default `http://localhost:8000/api`).
- `MCP_SERVER_URL`: Client URL to MCP (default `http://127.0.0.1:8001/mcp`).
- `OPENAI_API_KEY`: Required for `scripts/mcp_chat.sh` and `client/openai_app.py --ask`.
- `OPENAI_MODEL`: Optional OpenAI model override (defaults vary; e.g., `gpt-4o-mini`).

## Notes

- Overlap prevention applies per client: no two meetings for the same client can share time.
- Use `start` and/or `end` query params to time-window the list.
- Admin is enabled at `/admin` if you create a superuser.