"""General in-process invoker for MCP tools.

WARNING: Example invoker for local/manual testing. It imports the tool
implementation directly from `app.mcp_server` and therefore exercises the
in-process behavior only (does not test the HTTP/MCP serialization layer).

Use this script during development to validate implementation logic. Convert
to a guarded pytest integration or an automated smoke test before adding to CI.

Usage:
    python 03_invoke_tool_inproc.py --tool gov_policy_search --query education --limit 3

This imports `app.mcp_server` directly (so `PYTHONPATH` must include `fastapi-mcp`).
"""
import argparse
import asyncio
import json
import sys


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--tool", required=True, help="Tool callable name in app.mcp_server")
    p.add_argument("--query", default="education")
    p.add_argument("--limit", type=int, default=3)
    return p.parse_args()


async def main():
    args = parse_args()
    try:
        from app import mcp_server
    except Exception as exc:
        print("Failed to import app.mcp_server. Ensure PYTHONPATH includes fastapi-mcp.", file=sys.stderr)
        raise

    tool = getattr(mcp_server, args.tool, None)
    if tool is None:
        print(f"Tool {args.tool} not found in app.mcp_server", file=sys.stderr)
        sys.exit(2)

    result = await tool(query=args.query, limit=args.limit, sources=["govinfo", "federal_register"])
    print(json.dumps(result, indent=2))
    if not result.get("ok"):
        print("Tool reported error", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    asyncio.run(main())
