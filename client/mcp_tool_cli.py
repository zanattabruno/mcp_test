import argparse
import asyncio
import json
import os
from typing import Any, Dict, List, Tuple

from mcp import types as mcp_types
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession


async def _list_tools(server_url: str) -> None:
    async with streamablehttp_client(server_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_resp = await session.list_tools()
            for t in tools_resp.tools:
                print(f"- {t.name}: {t.description}")


async def _call_tool(server_url: str, name: str, arguments: Dict[str, Any]) -> None:
    async with streamablehttp_client(server_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments=arguments)
            # Prefer structured content
            if hasattr(result, "structuredContent") and result.structuredContent:
                print(json.dumps(result.structuredContent, ensure_ascii=False, indent=2))
                return
            parts: List[str] = []
            for c in result.content:
                if isinstance(c, mcp_types.TextContent):
                    parts.append(c.text)
                else:
                    parts.append(json.dumps(c.model_dump(mode="json")))
            print("\n".join(parts))


def _parse_args_payload(arg: str | None) -> Dict[str, Any]:
    if not arg:
        return {}
    if arg.startswith("@"):
        path = arg[1:]
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    # If looks like a file path and exists, read it
    if os.path.exists(arg) and os.path.isfile(arg):
        with open(arg, "r", encoding="utf-8") as f:
            return json.load(f)
    # Otherwise treat as inline JSON
    return json.loads(arg)


def main() -> None:
    parser = argparse.ArgumentParser(description="Direct MCP tool caller (no OpenAI)")
    parser.add_argument("--server-url", default=os.getenv("MCP_SERVER_URL", "http://localhost:8001/mcp"))
    parser.add_argument("--list-tools", action="store_true", help="List tools and exit")
    parser.add_argument("--tool", help="Tool name to call")
    parser.add_argument("--args", default=None, help='JSON arguments, @file.json, or file path')
    args = parser.parse_args()

    if args.list_tools:
        asyncio.run(_list_tools(args.server_url))
        return

    if not args.tool:
        print("Provide --tool or use --list-tools")
        return

    payload = _parse_args_payload(args.args)
    asyncio.run(_call_tool(args.server_url, args.tool, payload))


if __name__ == "__main__":
    main()
