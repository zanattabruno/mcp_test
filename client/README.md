# OpenAI MCP Client (Simple)

Small example client that connects to the MCP server at `http://localhost:8001/mcp`, lists tools, and can run a single chat turn using the OpenAI Chat Completions API with tool-calling.

Usage

1) Ensure the server is running:
   - `uvicorn mcp_server.server:app --host 0.0.0.0 --port 8001 --reload`
2) List tools (no OpenAI key needed):
   - `python client/openai_app.py --list-tools`
3) Ask a question (requires `OPENAI_API_KEY`):
   - `export OPENAI_API_KEY=sk-...`
   - `python client/openai_app.py --ask "Create a client named Alice (alice@example.com) and list meetings" --model gpt-4o-mini`

Convenience script
- `scripts/mcp_chat.sh "<prompt>" [MODEL]` wraps the above with sensible defaults and interactive mode when no prompt is given. See the root README section “scripts/mcp_chat.sh usage” for details and examples.

Environment
- `MCP_SERVER_URL` (optional): Defaults to `http://localhost:8001/mcp`
- `OPENAI_API_KEY`: Required for `--ask`
- `OPENAI_MODEL` (optional): Defaults to `gpt-4o-mini`
