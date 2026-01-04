import asyncio
import importlib
import os
import sys
import types
from pathlib import Path
from typing import Any, Dict

import pytest


APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))


def _fastmcp_stub_module() -> types.ModuleType:
    stub = types.ModuleType("fastmcp")

    class DummyFastMCP:
        def __init__(self, name: str):
            self.name = name

        def tool(self, func: Any) -> Any:
            return func

        def resource(self, _: Any) -> Any:
            def decorator(func: Any) -> Any:
                return func
            return decorator

        def prompt(self, *args: Any, **kwargs: Any) -> Any:
            def decorator(func: Any) -> Any:
                return func
            return decorator

    stub.FastMCP = DummyFastMCP
    return stub


def load_jira_tool_module() -> Any:
    original_fastmcp = sys.modules.get("fastmcp")
    stub = _fastmcp_stub_module()
    sys.modules["fastmcp"] = stub
    sys.modules.pop("app.mcp_server", None)
    sys.modules.pop("app.tools.jira_tool", None)
    try:
        module = importlib.import_module("app.tools.jira_tool")
        importlib.reload(module)
        return module
    finally:
        if original_fastmcp is not None:
            sys.modules["fastmcp"] = original_fastmcp
        else:
            sys.modules.pop("fastmcp", None)


jira_tool = load_jira_tool_module()


def _ensure_jira_env() -> bool:
    required = ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN")
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


JIRA_ENV_AVAILABLE = _ensure_jira_env()
JIRA_TEST_QUERY = os.environ.get("JIRA_TEST_QUERY", "error")
JIRA_TEST_PROJECT = os.environ.get("JIRA_TEST_PROJECT")


class DummyResponse:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Dict[str, Any]:
        return self._payload


class DummyAsyncClient:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._payload = kwargs.get("payload")

    async def __aenter__(self) -> "DummyAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[misc]
        return None

    async def get(self, *args: Any, **kwargs: Any) -> DummyResponse:
        payload = kwargs.get("payload") or self._payload or {
            "issues": [],
            "isLast": True,
        }
        return DummyResponse(payload)


def _run_query(*, monkeypatch: pytest.MonkeyPatch, response_payload: Dict[str, Any]) -> Dict[str, Any]:
    monkeypatch.setitem(os.environ, "JIRA_BASE_URL", "https://example.atlassian.net")
    monkeypatch.setitem(os.environ, "JIRA_EMAIL", "user@example.com")
    monkeypatch.setitem(os.environ, "JIRA_API_TOKEN", "token")

    def _client_factory(*args: Any, **kwargs: Any) -> DummyAsyncClient:
        return DummyAsyncClient(payload=response_payload)

    monkeypatch.setattr(jira_tool.httpx, "AsyncClient", _client_factory)

    return asyncio.run(jira_tool.jira_search_closest(query="error", project_key="PROJ", mode="text"))


def test_jira_search_closest_missing_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JIRA_BASE_URL", raising=False)
    monkeypatch.delenv("JIRA_EMAIL", raising=False)
    monkeypatch.delenv("JIRA_API_TOKEN", raising=False)

    res = asyncio.run(jira_tool.jira_search_closest(query="error", mode="text"))
    assert res["ok"] is False
    assert res["error"]["code"] == "MISSING_CONFIG"


def test_jira_search_closest_success(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "issues": [
            {
                "key": "PROJ-1",
                "id": "1",
                "self": "https://example.atlassian.net/rest/api/3/issue/1",
                "fields": {
                    "summary": "Saving file" ,
                    "description": {"type": "text", "text": "error"},
                    "status": {"name": "Open"},
                },
            },
        ],
        "isLast": True,
    }

    res = _run_query(monkeypatch=monkeypatch, response_payload=payload)
    assert res["ok"] is True
    data = res["data"]
    assert data["best_match"]["issue"]["key"] == "PROJ-1"
    assert data["ranked"]


def test_jira_search_closest_top_ticket(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "issues": [
            {
                "key": "PROJ-2",
                "id": "2",
                "self": "https://example.atlassian.net/rest/api/3/issue/2",
                "fields": {
                    "summary": "Crash on save",
                    "description": {"type": "text", "text": "save error"},
                    "status": {"name": "Open"},
                },
            },
        ],
        "isLast": True,
    }

    res = _run_query(monkeypatch=monkeypatch, response_payload=payload)
    assert res["ok"]
    data = res["data"]
    ranked = data["ranked"]
    assert len(ranked) == 1
    assert ranked[0]["issue"]["key"] == "PROJ-2"
    assert data["best_match"]["issue"]["key"] == "PROJ-2"


@pytest.mark.integration
@pytest.mark.skipif(not JIRA_ENV_AVAILABLE, reason="Jira credentials not configured")
def test_jira_search_closest_live() -> None:
    res = asyncio.run(
        jira_tool.jira_search_closest(
            query=JIRA_TEST_QUERY,
            project_key=JIRA_TEST_PROJECT,
            max_results=1,
            mode="text",
        )
    )
    assert res["ok"], res
    ranked = res["data"]["ranked"]
    if not ranked:
        pytest.skip(
            "Jira search returned no issues for the live query; adjust JIRA_TEST_QUERY/JIRA_TEST_PROJECT"
        )
    assert isinstance(ranked[0]["issue"]["key"], str)