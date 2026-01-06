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
import importlib
import json
import os
import sys
from pathlib import Path


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
    p.add_argument("--tool", required=True, help="Tool callable name in app.mcp_server")
    p.add_argument("--query", default="AI regulation")
    p.add_argument("--limit", type=int, default=3)
    p.add_argument("--summary-count", type=int, default=2, help="Number of granule summaries to fetch after search")
    return p.parse_args()


async def main():
    args = parse_args()
    try:
        app_root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(app_root))
        from app import mcp_server
    except Exception as exc:
        print("Failed to import app.mcp_server. Ensure PYTHONPATH includes fastapi-mcp.", file=sys.stderr)
        raise

    tool = getattr(mcp_server, args.tool, None)
    if tool is None:
        print(f"Tool {args.tool} not found in app.mcp_server", file=sys.stderr)
        sys.exit(2)

    result = await tool(query=args.query, limit=args.limit, sources=["govinfo"])
    print(json.dumps(result, indent=2))
    if not result.get("ok"):
        print("Tool reported error", file=sys.stderr)
        sys.exit(3)

    if args.summary_count <= 0:
        return

    try:
        summary_mod = importlib.import_module("app.tools.gov_policy_summary_tool")
    except Exception as exc:
        print("Could not import gov_policy_summary_tool", exc, file=sys.stderr)
        return

    granule_res = await summary_mod.govinfo_search_granules(query=args.query, page_size=max(args.limit, args.summary_count))
    if not granule_res.get("ok"):
        print("govinfo granule search failed", granule_res)
        return

    items = granule_res.get("data", {}).get("items", []) or []
    for idx, item in enumerate(items[: args.summary_count], start=1):
        package_id = item.get("package_id")
        granule_id = item.get("granule_id")
        title = item.get("title")
        print(f"\nSummary {idx}: {package_id}/{granule_id} – {title}")
        if not package_id or not granule_id:
            print("Missing package_id/granule_id; skipping summary")
            continue
        summary_data = await summary_mod.govinfo_download_granule_text(package_id=package_id, granule_id=granule_id, fmt="htm")
        print(json.dumps(summary_data, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
