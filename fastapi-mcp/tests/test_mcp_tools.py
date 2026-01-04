import importlib
import importlib.util
import pathlib
import sys
import types
from typing import Any
from typing import Any


def _fastmcp_stub_module():
    stub = types.ModuleType("fastmcp")

    class DummyFastMCP:
        def __init__(self, name: str):
            self.name = name

        def tool(self, func):
            return func

        def resource(self, _):
            def decorator(func):
                return func
            return decorator

        def prompt(self, *args: Any, **kwargs: Any):
            def decorator(func):
                return func
            return decorator

    stub.FastMCP = DummyFastMCP
    return stub


def load_mcp_server_module():
    root = pathlib.Path(__file__).parent.parent.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    original_fastmcp = sys.modules.get("fastmcp")
    stub = _fastmcp_stub_module()
    sys.modules["fastmcp"] = stub
    sys.modules.pop("app.mcp_server", None)
    sys.modules.pop("app.tools.jira_tool", None)
    try:
        module = importlib.import_module("app.mcp_server")
        importlib.reload(module)
        return module
    finally:
        if original_fastmcp is not None:
            sys.modules["fastmcp"] = original_fastmcp
        else:
            sys.modules.pop("fastmcp", None)


def test_add():
    m = load_mcp_server_module()
    res = m.add(2, 3)
    assert res["ok"] is True
    assert res["data"]["sum"] == 5


def test_normalize_name():
    m = load_mcp_server_module()
    res = m.normalize_name("  alice   o'connor  ")
    assert res["ok"] is True
    assert res["data"]["normalized"] in ("Alice O'Connor", "Alice O'connor")


def test_health():
    m = load_mcp_server_module()
    assert m.health() == "ok"


def test_code_review_prompt():
    m = load_mcp_server_module()
    p = m.code_review_prompt("print('x')")
    assert "Review the code" in p and "print('x')" in p
