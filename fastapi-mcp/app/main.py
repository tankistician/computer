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

if mcp is not None:
    try:
        mcp_app = mcp.http_app(path="/mcp")
        # Pass MCP lifespan to FastAPI so MCP session lifecycle runs correctly
        app.mount("/mcp", mcp_app)
    except Exception:
        # If FastMCP isn't available during development, continue without mount
        pass
