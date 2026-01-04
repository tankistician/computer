import asyncio
import importlib
import sys
import types
from pathlib import Path
from typing import Any, Dict, List
import os

import pytest


APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))


def _ensure_govinfo_env() -> bool:
    required = ("GOVINFO_API_KEY",)
    if all(os.environ.get(key) for key in required):
        return True
    env_path = Path(__file__).resolve().parents[2] / ".env"
    env_path = env_path.resolve()
    if not env_path.exists():
        return False
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key in required and not os.environ.get(key):
            os.environ[key] = value
    return all(os.environ.get(key) for key in required)


GOVINFO_ENV_AVAILABLE = _ensure_govinfo_env()


def _fastmcp_stub_module() -> types.ModuleType:
    stub = types.ModuleType("fastmcp")

    class DummyFastMCP:
        def tool(self, func: Any) -> Any:
            return func

    stub.FastMCP = DummyFastMCP
    return stub


def load_tool_module() -> Any:
    original_fastmcp = sys.modules.get("fastmcp")
    stub = _fastmcp_stub_module()
    sys.modules["fastmcp"] = stub
    sys.modules.pop("app.tools.gov_policy_tool", None)
    try:
        module = importlib.import_module("app.tools.gov_policy_tool")
        importlib.reload(module)
        return module
    finally:
        if original_fastmcp is not None:
            sys.modules["fastmcp"] = original_fastmcp
        else:
            sys.modules.pop("fastmcp", None)


gov_policy_tool = load_tool_module()


def _patch_handlers(module: Any, results: List[Dict[str, Any]]) -> None:
    async def _stub(*args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        return results

    module._call_federal_register = _stub
    module._call_govinfo = _stub


def test_empty_query() -> None:
    res = asyncio.run(gov_policy_tool.gov_policy_search(query="", sources=["federal_register"]))
    assert not res["ok"]
    assert res["error"]["code"] == "BAD_INPUT"


def test_aggregated_results(monkeypatch: pytest.MonkeyPatch) -> None:
    module = gov_policy_tool
    dummy = [{"title": "Title", "publication_date": "2025-01-01", "abstract": "desc"}]
    _patch_handlers(module, dummy)
    monkeypatch.setattr(module, "SOURCE_HANDLERS", {"federal_register": module._call_federal_register})

    res = asyncio.run(module.gov_policy_search(query="policy", sources=["federal_register"], limit=2))
    assert res["ok"]
    data = res["data"]
    assert data["query"] == "policy"
    assert data["results"]


@pytest.mark.integration
@pytest.mark.skipif(not GOVINFO_ENV_AVAILABLE, reason="GovInfo API key not configured")
def test_gov_policy_search_live() -> None:
    # Run a short live query against the govinfo/federal_register endpoints.
    # This test requires a valid GOVINFO_API_KEY in the repo .env or environment.
    res = asyncio.run(gov_policy_tool.gov_policy_search(query="education", sources=["federal_register", "govinfo"], limit=2))
    assert res["ok"] is True
    data = res.get("data", {})
    assert "results" in data