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
from .tools import (
    federal_register_summary_tool,
    gov_policy_summary_tool,
    jira_tool,
    policy_search_federal_register,
    policy_search_govinfo,
)  # type: ignore

# Expose tool callables at module level so `app.main` can discover them
# even when FastMCP is not installed.
jira_search_closest = getattr(jira_tool, "jira_search_closest", None)
gov_policy_summary = getattr(gov_policy_summary_tool, "gov_policy_summary", None)


async def gov_policy_search(query: str, sources: list[str] | None = None, start_date: str | None = None, end_date: str | None = None, limit: int = 5, sorts: list[dict] | None = None):
    """Composite search delegating to per-source modules."""
    # simple dispatcher: call requested sources and merge results
    if not query or not query.strip():
        return {"ok": False, "error": {"code": "BAD_INPUT", "message": "query required"}}

    selected = sources or ["federal_register"]
    results = []
    for src in selected:
        if src == "govinfo":
            res = await policy_search_govinfo.govinfo_search(query, limit=limit, start_date=start_date, end_date=end_date, sorts=sorts)
            if res.get("ok"):
                items = res.get("data", {}).get("items", [])
                results.extend({"source": "govinfo", **it} for it in items)
            else:
                results.append({"source": "govinfo", "error": res.get("error")})
        elif src == "federal_register":
            res = await policy_search_federal_register.federal_register_search(query, limit=limit, start_date=start_date, end_date=end_date, sorts=sorts)
            if res.get("ok"):
                items = res.get("data", {}).get("items", [])
                results.extend({"source": "federal_register", **it} for it in items)
            else:
                results.append({"source": "federal_register", "error": res.get("error")})

    ranked = sorted(results, key=lambda r: r.get("publication_date") or r.get("date") or "", reverse=True)
    return {"ok": True, "data": {"query": query, "sources": selected, "results": ranked[:limit]}, "meta": {}}


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
    # register per-source search tools
    policy_search_federal_register.register_mcp_instance(mcp)
    policy_search_govinfo.register_mcp_instance(mcp)
    gov_policy_summary_tool.register_mcp_instance(mcp)
    federal_register_summary_tool.register_mcp_instance(mcp)
