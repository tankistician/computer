
# Pytest Integration Template

TEMPLATE NOTES: This file is a template and example for creating a pytest
integration. Tests created from this template should be reviewed and adapted
before adding to CI. In particular, ensure the test is properly guarded,
does not leak secrets, and handles flaky upstreams (retries, timeouts,
backoff) or uses recorded fixtures/mocks where appropriate.

Use this template to convert the manual smoke-check scripts into an automated pytest
integration test. Keep the test guarded (skip) unless the required environment
variables are present so CI does not hit external services unintentionally.

Example skeleton:

```python
import asyncio
import os
import pytest

GOVINFO_REQUIRED = all(os.environ.get(k) for k in ("GOVINFO_API_KEY",))

@pytest.mark.integration
@pytest.mark.skipif(not GOVINFO_REQUIRED, reason="GovInfo API key not configured")
def test_gov_policy_http_smoke():
    # start server OR assume server is running at localhost:8000
    # then use fastmcp.client.Client to call the tool and assert response
    res = asyncio.run(_call_via_http())
    assert res.get("ok") is True
    assert res["data"].get("results")

```

Notes:
- Use the same guard and .env-loading logic used by `tests/test_gov_policy_tool.py`.
- Prefer re-using the scripts in `prod_tests` where practical to avoid duplicating payload shapes.
