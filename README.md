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

## Notes

- Overlap prevention applies per client: no two meetings for the same client can share time.
- Use `start` and/or `end` query params to time-window the list.
- Admin is enabled at `/admin` if you create a superuser.