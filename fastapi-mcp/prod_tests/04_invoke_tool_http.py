"""Invoke an MCP tool over HTTP using `fastmcp.client.Client`.

EXAMPLE: This file demonstrates a best-effort HTTP invocation using the
`fastmcp.client.Client`. Different `fastmcp` versions expose different client
APIs; this script attempts common method names and prints helpful errors.

This script assumes a FastAPI server is running and has mounted the MCP app
at `http://127.0.0.1:8000/mcp` (the default used by our dev server).

It will attempt to list tools and then call the requested tool.

Do not use this script as-is in CI without adapting it to your `fastmcp`
version and adding authentication/error handling/assertions.
"""
import asyncio
import json
import sys
import argparse


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:8000/mcp", help="Base URL to the MCP HTTP app")
    p.add_argument("--tool", default="gov_policy_search")
    p.add_argument("--query", default="education")
    p.add_argument("--limit", type=int, default=3)
    return p.parse_args()


async def main():
    args = parse_args()
    try:
        from fastmcp.client import Client
    except Exception as exc:
        print("fastmcp.client not importable. Install fastmcp in your venv.", file=sys.stderr)
        raise

    async with Client(args.url) as client:
        # Best-effort: try to list tools (method may vary by fastmcp version)
        tools = None
        if hasattr(client, "list_tools"):
            try:
                tools = await client.list_tools()
            except Exception:
                tools = None

        print("Discovered tools:", tools)

        # Try to invoke the tool. Different fastmcp versions expose different APIs;
        # try a few common names (call, invoke, run_tool) so the script is robust.
        call_fn = None
        for name in ("call", "invoke", "run_tool", "call_tool", "invoke_tool"):
            if hasattr(client, name):
                call_fn = getattr(client, name)
                break

        if call_fn is None:
            print("Could not find a call/invoke method on Client instance; check fastmcp API.", file=sys.stderr)
            sys.exit(2)

        # Call the tool with keyword args if supported; otherwise call positional.
        kwargs = {"query": args.query, "limit": args.limit, "sources": ["govinfo", "federal_register"]}
        try:
            result = await call_fn(args.tool, **kwargs)
        except TypeError:
            # fallback: positional (tool name first)
            result = await call_fn(args.tool, kwargs)

        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
