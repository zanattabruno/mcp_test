import argparse
import asyncio
import json
import os
from typing import Any, Dict, List

from openai import OpenAI

from mcp import types as mcp_types
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession


def mcp_tools_to_openai_tools(tools: List[mcp_types.Tool]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for t in tools:
        params = t.inputSchema if t.inputSchema is not None else {"type": "object", "properties": {}}
        out.append(
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or "",
                    "parameters": params,
                },
            }
        )
    return out


async def list_tools(server_url: str) -> None:
    async with streamablehttp_client(server_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_resp = await session.list_tools()
            for t in tools_resp.tools:
                print(f"- {t.name}: {t.description}")


async def call_mcp_tool(session: ClientSession, name: str, arguments: Dict[str, Any]) -> str:
    result = await session.call_tool(name, arguments=arguments)
    # Prefer structured content if available
    if hasattr(result, "structuredContent") and result.structuredContent:
        return json.dumps(result.structuredContent, ensure_ascii=False)
    # Fallback to concatenating text content
    parts: List[str] = []
    for c in result.content:
        if isinstance(c, mcp_types.TextContent):
            parts.append(c.text)
        else:
            parts.append(json.dumps(c.model_dump(mode="json")))
    return "\n".join(parts) if parts else ""


async def _complete_with_tools(client: OpenAI, session: ClientSession, model: str, messages: List[Dict[str, Any]], oa_tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=oa_tools or None,
        tool_choice="auto" if oa_tools else None,
    )

    msg = completion.choices[0].message

    # Handle tool calls if any
    while msg.tool_calls:
        tool_messages: List[Dict[str, Any]] = []
        for tc in msg.tool_calls:
            fname = tc.function.name
            try:
                fargs = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                fargs = {}
            # Execute via MCP session
            result_text = await call_mcp_tool(session, fname, fargs)
            tool_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": fname,
                    "content": result_text or "(no result)",
                }
            )

        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
        })
        messages.extend(tool_messages)

        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=oa_tools or None,
            tool_choice="auto" if oa_tools else None,
        )
        msg = completion.choices[0].message

    return msg


async def chat_once(server_url: str, model: str, prompt: str, system: str | None) -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY to use the OpenAI API")

    client = OpenAI(api_key=api_key)

    async with streamablehttp_client(server_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_resp = await session.list_tools()
            oa_tools = mcp_tools_to_openai_tools(tools_resp.tools)

            messages: List[Dict[str, Any]] = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            msg = await _complete_with_tools(client, session, model, messages, oa_tools)
            print(msg.content or "(no assistant content)")


async def chat_interactive(server_url: str, model: str, system: str | None, init: str | None) -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY to use the OpenAI API")

    client = OpenAI(api_key=api_key)

    async with streamablehttp_client(server_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_resp = await session.list_tools()
            oa_tools = mcp_tools_to_openai_tools(tools_resp.tools)

            messages: List[Dict[str, Any]] = []
            if system:
                messages.append({"role": "system", "content": system})
            if init:
                messages.append({"role": "user", "content": init})
                # Run initial turn
                msg = _complete_with_tools(client, session, model, messages, oa_tools)
                print(msg.content or "(no assistant content)")

            print("Interactive chat. Type /exit to quit, /reset to clear context.")
            loop = asyncio.get_event_loop()
            while True:
                try:
                    user_input = await loop.run_in_executor(None, input, "> ")
                except (EOFError, KeyboardInterrupt):
                    print()
                    break

                if not user_input.strip():
                    continue
                if user_input.strip().lower() in {"/exit", "/quit", ":q"}:
                    break
                if user_input.strip().lower() == "/reset":
                    messages = []
                    if system:
                        messages.append({"role": "system", "content": system})
                    print("Context cleared.")
                    continue

                messages.append({"role": "user", "content": user_input})
                msg = await _complete_with_tools(client, session, model, messages, oa_tools)
                # Append assistant message to history
                messages.append({"role": "assistant", "content": msg.content or ""})
                print(msg.content or "(no assistant content)")


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenAI-backed MCP client for Meeting Scheduler MCP server")
    parser.add_argument("--server-url", default=os.getenv("MCP_SERVER_URL", "http://localhost:8001/mcp"), help="MCP Streamable HTTP server URL")
    parser.add_argument("--list-tools", action="store_true", help="List tools from the MCP server and exit")
    parser.add_argument("--ask", help="Ask a single prompt; requires OPENAI_API_KEY")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-5"), help="OpenAI model for chat completions")
    parser.add_argument("--system", default=None, help="Optional system prompt")
    parser.add_argument("--interactive", action="store_true", help="Start an interactive chat session with context")
    parser.add_argument("--init", default=None, help="Optional initial user message in interactive mode")
    args = parser.parse_args()

    if args.list_tools:
        asyncio.run(list_tools(args.server_url))
        return

    if args.ask:
        asyncio.run(chat_once(args.server_url, args.model, args.ask, args.system))
        return

    if args.interactive:
        asyncio.run(chat_interactive(args.server_url, args.model, args.system, args.init))
        return

    print("Nothing to do. Use --list-tools, --ask \"...\", or --interactive.")


if __name__ == "__main__":
    main()
