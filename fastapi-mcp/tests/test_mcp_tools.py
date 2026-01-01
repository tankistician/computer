import importlib.util
import pathlib


def load_mcp_server_module():
    path = pathlib.Path(__file__).parent.parent / "app" / "mcp_server.py"
    spec = importlib.util.spec_from_file_location("mcp_server", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
