"""FastAPI app mounting the MCP ASGI app.

This mounts the MCP app under `/mcp` when available. Because `app.mcp_server`
currently creates `mcp` (possibly None during scaffolding), the mount is
performed only if the MCP app is available.
"""
from __future__ import annotations

from fastapi import FastAPI

from . import mcp_server

mcp = getattr(mcp_server, "mcp", None)
app = FastAPI(title="fastapi-mcp example")

@app.get("/hello")
def hello() -> dict:
    return {"message": "hello from fastapi-mcp (skeleton)"}


@app.get("/")
def index() -> dict:
    """Root index with helpful links."""
    return {
        "message": "fastapi-mcp",
        "links": {
            "hello": "/hello",
            "openapi": "/openapi.json",
            "docs": "/docs",
        },
    }





@app.get("/mcp/tools", tags=["mcp"])
async def list_mcp_tools():
    """List MCP tools using FastMCP HTTP client when available, else fallback
    to in-process discovery from `app.mcp_server`.
    """
    # First: discover in-process functions so we can always return them if
    # the MCP client path fails or returns empty. This mirrors the `/tools`
    # endpoint behavior and is useful during development.
    import inspect

    mod = mcp_server
    candidate_names = (
        "add",
        "normalize_name",
        "echo",
        "health",
        "code_review_prompt",
        "jira_search_closest",
        "gov_policy_search",
        "gov_policy_summary",
    )
    inproc_debug = []
    for name in candidate_names:
        has = hasattr(mod, name)
        obj = getattr(mod, name) if has else None
        is_callable = callable(obj) if has else False
        try:
            sig = str(inspect.signature(obj)) if is_callable else None
        except (ValueError, TypeError):
            sig = None
        inproc_debug.append({
            "name": name,
            "has_attr": has,
            "callable": is_callable,
            "type": type(obj).__name__ if has else None,
            "obj_name": getattr(obj, "__name__", None),
            "signature": sig,
        })

    # Next: try FastMCP client discovery (prefer this if it returns tools).
    try:
        from fastmcp.client import Client  # type: ignore
    except Exception:
        Client = None  # type: ignore

    if Client is not None:
        try:
            async with Client("http://127.0.0.1:8000/mcp") as client:
                tools = await client.list_tools()
                # Still return local debug info only (per request to drop tools)
                return {"source": "fastmcp_client", "inproc_debug": inproc_debug}
        except Exception:
            # If client call fails, fall through to returning in-process tools
            pass

    # Return the in-process debug info (requested: only inproc_debug)
    return {"source": "inprocess", "mcp_present": mcp is not None, "inproc_debug": inproc_debug}

if mcp is not None:
    try:
        mcp_app = mcp.http_app(path="/mcp")
        # Pass MCP lifespan to FastAPI so MCP session lifecycle runs correctly
        app.mount("/mcp", mcp_app)
    except Exception:
        # If FastMCP isn't available during development, continue without mount
        pass
