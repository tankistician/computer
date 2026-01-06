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
import os
import sys
import argparse
from pathlib import Path
from typing import Any


def load_env_from_repo_root() -> None:
    env_path = Path(__file__).resolve().parents[1].parent / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if not key or not value:
            continue
        os.environ.setdefault(key, value)


load_env_from_repo_root()


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:8000/mcp", help="Base URL to the MCP HTTP app")
    p.add_argument("--tool", default="gov_policy_search")
    p.add_argument("--query", default="AI regulation")
    p.add_argument("--limit", type=int, default=3)
    p.add_argument("--summary-count", type=int, default=2, help="How many summaries to retrieve from GovInfo granules")
    return p.parse_args()


async def main():
    args = parse_args()
    try:
        from fastmcp.client import Client
    except Exception as exc:
        print("fastmcp.client not importable. Install fastmcp in your venv.", file=sys.stderr)
        raise

    async with Client(args.url) as client:
        tools = None
        if hasattr(client, "list_tools"):
            try:
                tools = await client.list_tools()
            except Exception:
                tools = None

        print("Discovered tools:", tools)

        call_fn = None
        for name in ("call", "invoke", "run_tool", "call_tool", "invoke_tool"):
            if hasattr(client, name):
                call_fn = getattr(client, name)
                break

        if call_fn is None:
            print("Could not find a call/invoke method on Client instance; check fastmcp API.", file=sys.stderr)
            sys.exit(2)

        async def invoke(tool_name: str, **kwargs: Any) -> Any:
            try:
                return await call_fn(tool_name, **kwargs)
            except TypeError:
                return await call_fn(tool_name, kwargs)

        kwargs = {"query": args.query, "limit": args.limit, "sources": ["govinfo"]}
        result = await invoke(args.tool, **kwargs)
        print(json.dumps(result, indent=2))

        if args.summary_count <= 0:
            return

        granule_res = await invoke("govinfo_search_granules", query=args.query, page_size=max(args.limit, args.summary_count))
        print("\nGovInfo granule search result:", json.dumps(granule_res, indent=2))
        if not granule_res.get("ok"):
            return

        items = (granule_res.get("data", {}).get("items", []) or [])[: args.summary_count]
        for idx, item in enumerate(items, start=1):
            package_id = item.get("package_id")
            granule_id = item.get("granule_id")
            title = item.get("title")
            print(f"\nSummary {idx}: {package_id}/{granule_id} – {title}")
            if not package_id or not granule_id:
                print("Missing package_id/granule_id; skipping summary")
                continue
            summary = await invoke(
                "govinfo_download_granule_text",
                package_id=package_id,
                granule_id=granule_id,
                fmt="htm",
            )
            print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
