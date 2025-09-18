# Django Project: Scheduler

Primary goal: demonstrate MCP capabilities in a simple, self-contained environment.

This Django project hosts the Meeting Scheduler REST API used by the MCP bridge. It contains the `api` app with DRF viewsets, serializers, and models for `Client` and `Meeting`.

## What's here

- `scheduler/settings.py`, `urls.py` — Django config and DRF routes
- `api/` app — models, serializers, views, tests
  - Models: `Client`, `Meeting`
  - Validation: ISO-8601 datetimes with TZ, `end_time > start_time`, no overlapping meetings per client
  - DRF viewsets: list/create clients and meetings, filters, search, ordering
- OpenAPI via drf-spectacular at `/api/schema/` and `/api/docs/`

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Useful URLs
- API root: `http://localhost:8000/api/`
- OpenAPI JSON: `http://localhost:8000/api/schema/`
- Swagger UI: `http://localhost:8000/api/docs/`

## Data model

- `Client`
  - Fields: `name`, `email`, `phone`, timestamps
- `Meeting`
  - Fields: `client`, `title`, `start_time`, `end_time`, timestamps
  - Constraints: strictly increasing time window; per-client overlap prevention

## Common commands

```bash
# Create admin user (optional)
python manage.py createsuperuser

# Seed demo clients
python manage.py seed_clients          # add missing
python manage.py seed_clients --reset  # reset and add

# Run tests
python manage.py test
```

## Integration with MCP

- The FastAPI MCP server (in `mcp_server/`) calls this API via HTTP using `SCHEDULER_API_BASE` (default `http://localhost:8000/api`).
- Start both servers for end-to-end tool-calling. See `scripts/start_servers.sh` to run API and MCP together.

## Notes

- Datetimes must be ISO-8601 with timezone, e.g. `2025-09-16T10:00:00Z` (UTC recommended).
- Overlap prevention applies per client only; different clients can have concurrent meetings.
