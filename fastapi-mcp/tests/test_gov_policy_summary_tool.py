import asyncio
from pathlib import Path
from typing import Any, Dict

import httpx

import pytest


APP_ROOT = Path(__file__).resolve().parents[1]
sys_path = str(APP_ROOT)
if sys_path not in __import__("sys").path:
    __import__("sys").path.insert(0, sys_path)


class DummyResponse:
    def __init__(self, data: Dict[str, Any] | None = None, text: str = "", status_code: int = 200):
        self._data = data or {}
        self.text = text
        self.status_code = status_code
        self.headers = {"Content-Type": "text/html"}

    def json(self) -> Dict[str, Any]:
        return self._data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("err", request=None, response=self)  # type: ignore[arg-type]


class DummyClient:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._mode = "summary"

    async def __aenter__(self) -> "DummyClient":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None

    async def get(self, url: str, *args: Any, **kwargs: Any) -> DummyResponse:
        if "summary" in url:
            return DummyResponse(data={"download": {"txtLink": "https://example.gov/doc/htm"}})
        return DummyResponse(text="<p>content</p>")


@pytest.fixture(autouse=True)
def patch_httpx(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    monkeypatch.setattr(httpx, "AsyncClient", DummyClient)


@pytest.fixture(autouse=True)
def ensure_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOVINFO_API_KEY", "dummy")


def test_requires_package_and_granule() -> None:
    module = __import__("app.tools.gov_policy_summary_tool", fromlist=["*"])
    res = asyncio.run(module.gov_policy_summary(package_id="", granule_id=""))
    assert res["ok"] is False
    assert res["error"]["code"] == "BAD_INPUT"


def test_invalid_format_returns_error() -> None:
    module = __import__("app.tools.gov_policy_summary_tool", fromlist=["*"])
    res = asyncio.run(module.gov_policy_summary(package_id="pkg", granule_id="gran", fmt="txt"))
    assert res["ok"] is False
    assert res["error"]["code"] == "BAD_INPUT"


def test_download_text_flow() -> None:
    module = __import__("app.tools.gov_policy_summary_tool", fromlist=["*"])
    res = asyncio.run(module.gov_policy_summary(package_id="pkg", granule_id="gran", fmt="htm"))
    assert res["ok"] is True
    data = res["data"]
    assert data["package_id"] == "pkg"
    assert data["granule_id"] == "gran"
    assert data["format"] == "htm"
    assert "content" in data