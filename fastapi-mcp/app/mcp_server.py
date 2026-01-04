"""MCP server module.

This module provides small example tools/resources/prompts. Implementations
are available even when `fastmcp` is not installed so unit tests can run.
If `fastmcp` is present, decorated wrappers will be registered so the tools
appear in the MCP server.
"""
from __future__ import annotations

import time
import uuid
from typing import Any

try:
    from fastmcp import FastMCP
except Exception:  # pragma: no cover - missing dependency during scaffolding
    FastMCP = None  # type: ignore


mcp = None
if FastMCP is not None:
    mcp = FastMCP("fastapi-mcp")

# Import tool modules even when FastMCP is missing so their pure Python
# implementations are available for in-process inspection and tests.
from .tools import jira_tool, gov_policy_tool  # type: ignore

# Expose tool callables at module level so `app.main` can discover them
# even when FastMCP is not installed.
jira_search_closest = getattr(jira_tool, "jira_search_closest", None)
gov_policy_search = getattr(gov_policy_tool, "gov_policy_search", None)


def _meta(start: float) -> dict[str, Any]:
    return {
        "request_id": str(uuid.uuid4()),
        "duration_ms": int((time.time() - start) * 1000),
    }


# --- Pure implementations (always available) ---
def _impl_add(a: int, b: int) -> dict[str, Any]:
    """Add two integers and return a stable JSON envelope."""
    start = time.time()
    return {"ok": True, "data": {"sum": a + b}, "meta": _meta(start)}


def _impl_normalize_name(name: str) -> dict[str, Any]:
    """Normalize a name (trim, collapse spaces, title-case)."""
    start = time.time()
    cleaned = " ".join(name.strip().split())
    return {"ok": True, "data": {"normalized": cleaned.title()}, "meta": _meta(start)}


def _impl_health() -> str:
    """Simple health check resource."""
    return "ok"


def _impl_code_review_prompt(code: str) -> str:
    """Prompt template for reviewing code."""
    return (
        "Review the code for correctness, security, and maintainability.\n\n"
        f"CODE:\n{code}\n"
    )


def _impl_echo(input_value: Any) -> dict[str, Any]:
    """Echo tool: returns the input back with a message."""
    start = time.time()
    return {
        "ok": True,
        "data": {"echoed": input_value},
        "meta": _meta(start),
        "message": "echo tool received input",
    }


# Public API points to implementations so tests can import and call them.
add = _impl_add
normalize_name = _impl_normalize_name
health = _impl_health
code_review_prompt = _impl_code_review_prompt
echo = _impl_echo


# If FastMCP is available, register decorated wrappers so the tools appear
# in the MCP server. They delegate to the pure implementations above.
if mcp is not None:
    @mcp.tool
    def add(a: int, b: int) -> dict[str, Any]:
        return _impl_add(a, b)

    @mcp.tool
    def normalize_name(name: str) -> dict[str, Any]:
        return _impl_normalize_name(name)

    @mcp.resource("health://status")
    def health() -> str:
        return _impl_health()

    @mcp.prompt(title="Code Review")
    def code_review_prompt(code: str) -> str:
        return _impl_code_review_prompt(code)

    @mcp.tool
    def echo(input_value: Any) -> dict[str, Any]:
        return _impl_echo(input_value)

    # Register FastMCP-decorated wrappers so tools appear in the MCP server.
    jira_tool.register_mcp_instance(mcp)
    gov_policy_tool.register_mcp_instance(mcp)
