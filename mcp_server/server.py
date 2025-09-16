import os
from typing import Any, Literal, TypedDict

import httpx
from fastapi import FastAPI
from contextlib import asynccontextmanager
from pydantic import AnyHttpUrl, BaseModel, Field

from mcp.server.fastmcp import FastMCP


# Configuration
SCHEDULER_API_BASE = os.getenv("SCHEDULER_API_BASE", "http://localhost:8000/api")


# Pydantic models for structured tool I/O
class ClientIn(BaseModel):
	name: str
	email: str
	phone: str | None = None


class ClientOut(BaseModel):
	id: int
	name: str
	email: str
	phone: str | None = None
	created_at: str


class MeetingIn(BaseModel):
	client: int = Field(description="Client ID")
	title: str
	start_time: str = Field(description="ISO-8601 with timezone (UTC preferred)")
	end_time: str = Field(description="ISO-8601 with timezone (UTC preferred)")
	location: str | None = None
	notes: str | None = None


class MeetingOut(BaseModel):
	id: int
	client: int
	title: str
	start_time: str
	end_time: str
	location: str | None = None
	notes: str | None = None
	created_at: str


# Create FastMCP server
mcp = FastMCP(name="Meeting Scheduler MCP")
# Ensure the mounted path resolves to /mcp (not /mcp/mcp)
mcp.settings.streamable_http_path = "/"


def _client() -> httpx.AsyncClient:
	return httpx.AsyncClient(base_url=SCHEDULER_API_BASE, timeout=10.0)


@mcp.tool()
async def api_info() -> dict[str, Any]:
	"""Get configured scheduler API base and simple status."""
	async with _client() as client:
		# Try a lightweight list call to confirm connectivity
		try:
			r = await client.get("/clients/", params={"limit": 1})
			ok = r.status_code == 200
		except Exception:
			ok = False
	return {"base": SCHEDULER_API_BASE, "reachable": ok}


@mcp.tool()
async def list_clients(name: str | None = None, email: str | None = None, search: str | None = None, ordering: str | None = None) -> list[ClientOut]:
	"""List clients. Filters: `name` (mapped to `search`), `email`, `search` (name,email,phone), `ordering` (name,-name,created_at).

	Note: If `search` is provided, it takes precedence; otherwise, `name` is
	mapped to `search` to enable case-insensitive matching across name/email/phone.
	"""
	params: dict[str, Any] = {}
	if email:
		params["email"] = email
	# Prefer broad, case-insensitive search; fall back to name -> search
	if search:
		params["search"] = search
	elif name:
		params["search"] = name
	if ordering:
		params["ordering"] = ordering
	async with _client() as client:
		r = await client.get("/clients/", params=params)
		r.raise_for_status()
		data = r.json()
		if isinstance(data, list):
			return [ClientOut(**c) for c in data]
		return [ClientOut(**c) for c in data.get("results", [])]


@mcp.tool()
async def create_client(payload: ClientIn) -> ClientOut:
	"""Create a client with name, email, and optional phone."""
	async with _client() as client:
		r = await client.post("/clients/", json=payload.model_dump(exclude_none=True))
		r.raise_for_status()
		return ClientOut(**r.json())


@mcp.tool()
async def list_meetings(
	client_id: int | None = None,
	title: str | None = None,
	start: str | None = None,
	end: str | None = None,
	ordering: str | None = None,
) -> list[MeetingOut]:
	"""List meetings with optional filters: `client_id`, `title`, `start`, `end`, `ordering`."""
	params: dict[str, Any] = {}
	if client_id is not None:
		params["client"] = client_id
	if title:
		params["title"] = title
	if start:
		params["start"] = start
	if end:
		params["end"] = end
	if ordering:
		params["ordering"] = ordering
	async with _client() as client:
		r = await client.get("/meetings/", params=params)
		r.raise_for_status()
		data = r.json()
		if isinstance(data, list):
			return [MeetingOut(**m) for m in data]
		return [MeetingOut(**m) for m in data.get("results", [])]


@mcp.tool()
async def create_meeting(payload: MeetingIn) -> MeetingOut:
	"""Create a meeting; respects serializer validations (end > start, no per-client overlap)."""
	async with _client() as client:
		r = await client.post("/meetings/", json=payload.model_dump(exclude_none=True))
		if r.status_code >= 400:
			# Normalize DRF errors into a readable string while keeping raw body
			try:
				err = r.json()
			except Exception:
				err = {"detail": r.text}
			raise ValueError(f"Scheduler API error {r.status_code}: {err}")
		return MeetingOut(**r.json())


@asynccontextmanager
async def _lifespan(app: FastAPI):
	# Initialize the Streamable HTTP session manager and keep it running
	# during the lifetime of the FastAPI app to avoid 500s on /mcp/.
	# Ensure the session manager exists (created lazily by streamable_http_app()).
	mcp_app_placeholder = mcp.streamable_http_app()
	_ = mcp_app_placeholder  # silence unused variable warning
	async with mcp.session_manager.run():
		yield


# Expose FastAPI with health and mount MCP (Streamable HTTP)
app = FastAPI(title="Meeting Scheduler MCP", version="0.1.0", lifespan=_lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
	return {"status": "ok"}


# Mount MCP streamable HTTP server at /mcp
_mcp_asgi_app = mcp.streamable_http_app()
app.mount("/mcp", _mcp_asgi_app)


def main():  # pragma: no cover
	# Allow running directly: python -m mcp_server.server
	mcp.run(transport="streamable-http")


if __name__ == "__main__":  # pragma: no cover
	main()
