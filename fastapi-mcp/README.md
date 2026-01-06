# fastapi-mcp

Minimal FastAPI + FastMCP server scaffold.

Status: skeleton only — tools not yet implemented.

Quick start

Prerequisites: Python 3.10+ (3.11 recommended).

Recommended (foreground, simplest)

```powershell
cd C:\Users\fbpol\Documents\ML_Projects\computer\fastapi-mcp
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
py -3.11 -m venv .venv     # or: python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

While the server runs (logs in this terminal), open a second terminal for coding/testing:

```powershell
cd C:\Users\fbpol\Documents\ML_Projects\computer\fastapi-mcp
.\.venv\Scripts\Activate.ps1
```

Scripted helper (same behavior, foreground)

```powershell
cd C:\Users\fbpol\Documents\ML_Projects\computer\fastapi-mcp
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
.\start-server.ps1
```

Detach option (if you prefer your prompt free):

```powershell
cd C:\Users\fbpol\Documents\ML_Projects\computer\fastapi-mcp
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
$p = Start-Process -FilePath "$PWD\.venv\Scripts\python.exe" -ArgumentList "-m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000" -WorkingDirectory $PWD -PassThru
$p.Id   # note PID; stop later with: Stop-Process -Id <PID>
```

Endpoints (once running):
- FastAPI: `GET http://127.0.0.1:8000/hello`
- MCP (when mounted by FastMCP): typically under `/mcp` (e.g. `http://127.0.0.1:8000/mcp`)

Testing & Inspector

- Unit tests (do not require FastMCP):

```powershell
cd C:\Users\fbpol\Documents\ML_Projects\computer\fastapi-mcp
pytest -q
```

- Inspector (optional):

```powershell
npx @modelcontextprotocol/inspector
```

Troubleshooting

- If `python` still points to an older version after installing 3.11, prefer using the `py` launcher (`py -3.11`) or run the `start-server.ps1` script which prefers `py -3.11` automatically.
- If the MCP endpoints are not present, ensure `fastmcp<3` installed successfully in the venv. The app will still run; MCP-decorated tools appear only when FastMCP is available.

Next steps

- Confirm the set of tools to implement (e.g., `db.schema`, `db.query_readonly`, `http.request`), and I will add safe mocked implementations and JSON schemas.

Adding a new MCP tool (Jira example)

- **Create the tool file** in `app/tools/`, e.g., `jira_tool.py`, and implement the core async function (`_jira_search_closest`). Keep the logic reusable even when FastMCP decorators are unavailable.
- **Expose a registrar** like `register_mcp_instance(mcp_instance)` that wraps `_jira_search_closest` using `mcp_instance.tool(...)` and swaps the exported `jira_search_closest` callable so tests/service code can import it without FastMCP present.
- **Wire it into `app/mcp_server.py`** by importing the tool module under the existing `if fastmcp is installed` block and calling its registrar with the shared `mcp` instance so the tool shows up at `/mcp/tools`.
- **Wire it into `app/mcp_server.py`** by importing the tool module under the existing `if fastmcp is installed` block and calling its registrar with the shared `mcp` instance so the tool shows up at `/mcp/tools`.

Automatic exposure checklist for new tools

- **Preferred pattern**: implement a pure-Python async function (e.g. `_my_tool`) and a `register_mcp_instance(mcp_instance)` that replaces the exported callable with a decorated wrapper when `mcp_instance` is provided. Export the fallback name (e.g. `my_tool = _my_tool`) so code and tests can call it without FastMCP installed.

- **Example tool skeleton**:

````python
async def _my_tool(...):
	# pure implementation, returns JSON-serializable dict
	return {"ok": True, "data": ...}

my_tool = _my_tool

def register_mcp_instance(mcp_instance):
	globa\n my_tool
	if mcp_instance is None:
		return
	my_tool = mcp_instance.tool(_my_tool)
````

- **Ensure `app/mcp_server.py` imports tools at module import time** so their pure implementations are always visible to the in-process `/mcp/tools` discovery (this project follows that pattern). `mcp_server` should also call `register_mcp_instance(mcp)` when `FastMCP` is available so the decorated wrappers are registered with the running MCP server.

This pattern makes tools discoverable in two scenarios:
- *Development without `fastmcp` installed*: `/mcp/tools` (in-process debug) will list the exported callables and signatures.
- *With `fastmcp` installed*: the MCP app is mounted and the tools appear in the MCP UI under `/mcp/tools`.
- **Keep tests simple** by loading the tool module via `importlib` from the `app` package, stubbing `fastmcp` before import so decorators become no-ops, and covering both the mock-fueled unit logic and (optionally) a conditional live connection using `.env` credentials.
- **Run `pytest fastapi-mcp/tests`** to ensure the tool and `mcp_server` suite still pass, including integration skips that detect missing Jira credentials.

Government policy research tool

- **Purpose**: `gov_policy_search` aggregates primary-source hits for government policy (Federal Register + govinfo) so agents can cite current rules and publications first, then fall back to secondary fetches.
- **API usage**: the tool reads `GOVINFO_API_KEY` (optional) and hits `https://www.federalregister.gov/api/v1/documents` plus the GovInfo search endpoint. Results are normalized into `{source,data}` items with publication dates.
- **Publishing**: register the Federal Register and govinfo search helpers (`policy_search_federal_register.register_mcp_instance(mcp)` and `policy_search_govinfo.register_mcp_instance(mcp)`) in `app/mcp_server.py` so `/mcp/tools` lists them alongside the Jira search tool.
- **Summarizer**: `gov_policy_summary` consumes the same data, produces a short narrative summary (`summary`, `source_counts`, `total_results`, `top_hits`) for the query, and is registered via `gov_policy_summary_tool.register_mcp_instance(mcp)` so it is discoverable together with the original search tool.
- **Federal Register detail**: for citations that require the original document, `federal_register_summary_tool.federal_register_get_document_summary` fetches the Federal Register payload plus optional HTML/text content, and `federal_register_summary_tool.register_mcp_instance(mcp)` registers it alongside the other helpers.

Testing MCP tools

- **Stub FastMCP decorators** when importing tool modules inside tests so the module remains importable without the third-party package. Create a dummy `fastmcp` module or insert a stub `FastMCP` class into `sys.modules` before the import.
- **Use `importlib`** to load the tool via the package path (e.g., `import app.tools.jira_tool`) and reload it inside the test to ensure the stub takes effect before registration logic runs.
- **Mock HTTP clients** (like `httpx.AsyncClient`) to return simple payloads for deterministic unit tests, and verify the tool’s response envelope, ranking, and metadata.
- **Add conditional integration tests** that read credentials from `.env` (or environment) and skip when `JIRA_BASE_URL`, `JIRA_EMAIL`, or `JIRA_API_TOKEN` are missing; allow `JIRA_TEST_QUERY`/`JIRA_TEST_PROJECT` overrides to control which ticket is fetched.
- **Run the suite** with `pytest fastapi-mcp/tests` and expect the integration test to skip unless properly configured, keeping the cycle fast during routine development.

Making new MCP tools: automatic checklist & tooling

- **Envelope contract**: every tool should return a JSON-serializable dict matching `{ "ok": bool, "data": {...}?, "error": {...}?, "meta": {...}? }`. `meta` should include `request_id` (UUID) and `duration_ms` so callers can correlate logs. When the tool envelopes partial data (multiple sources), include `source`/`type` fields in each item.
- **Required env vars**: document any credentials the tool needs (e.g., `GOVINFO_API_KEY`, `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`). Store them in `.env` at the repo root (see `prod_tests/local_env_example.env`) and load them using the helper in the tool’s tests.
- **Per-tool process**:
  1. Query the upstream API manually (see `prod_tests/01_query_source.*`) and capture the payload/response.
  2. Implement the async tool, returning the agreed envelope, and add tests that mock HTTP clients.
  3. Create an example script under `prod_tests/03_*` or similar that calls the tool (in-process or over HTTP).
  4. Convert the working manual script into a guarded pytest integration test (use `prod_tests/05_pytest_template.md` for guidance).
  5. Confirm `fastapi-mcp/tests` passes, including the new tool and guarded integration(s).
- **Documentation**: add a short section to this README and/or `prod_tests/README.md` linking to the new tool so future contributors know how to run the manual scripts and what env vars are involved.

Adding a new MCP tool (Jira example)

- **Create the tool file** in `app/tools/`, e.g., `jira_tool.py`, and implement the core async function (`_jira_search_closest`). Keep the logic reusable even when FastMCP decorators are unavailable.
- **Expose a registrar** like `register_mcp_instance(mcp_instance)` that wraps `_jira_search_closest` using `mcp_instance.tool(...)` and swaps the exported `jira_search_closest` callable so tests/service code can import it without FastMCP present.
- **Wire it into `app/mcp_server.py`** by importing the tool module under the existing `if fastmcp is installed` block and calling its registrar with the shared `mcp` instance so the tool shows up at `/mcp/tools`.
- **Wire it into `app/mcp_server.py`** by importing the tool module under the existing `if fastmcp is installed` block and calling its registrar with the shared `mcp` instance so the tool shows up at `/mcp/tools`.

Automatic exposure checklist for new tools

- **Preferred pattern**: implement a pure-Python async function (e.g. `_my_tool`) and a `register_mcp_instance(mcp_instance)` that replaces the exported callable with a decorated wrapper when `mcp_instance` is provided. Export the fallback name (e.g. `my_tool = _my_tool`) so code and tests can call it without FastMCP installed.

- **Example tool skeleton**:

```python
async def _my_tool(...):
	# pure implementation, returns JSON-serializable dict
	return {"ok": True, "data": ...}

my_tool = _my_tool

def register_mcp_instance(mcp_instance):
	global my_tool
	if mcp_instance is None:
		return
	my_tool = mcp_instance.tool(_my_tool)
```

- **Ensure `app/mcp_server.py` imports tools at module import time** so their pure implementations are always visible to the in-process `/mcp/tools` discovery (this project follows that pattern). `mcp_server` should also call `register_mcp_instance(mcp)` when `FastMCP` is available so the decorated wrappers are registered with the running MCP server.

This pattern makes tools discoverable in two scenarios:
- *Development without `fastmcp` installed*: `/mcp/tools` (in-process debug) will list the exported callables and signatures.
- *With `fastmcp` installed*: the MCP app is mounted and the tools appear in the MCP UI under `/mcp/tools`.
- **Keep tests simple** by loading the tool module via `importlib` from the `app` package, stubbing `fastmcp` before import so decorators become no-ops, and covering both the mock-fueled unit logic and (optionally) a conditional live connection using `.env` credentials.
- **Run `pytest fastapi-mcp/tests`** to ensure the tool and `mcp_server` suite still pass, including integration skips that detect missing Jira credentials.

Government policy research tool

- **Purpose**: `gov_policy_search` aggregates primary-source hits for government policy (Federal Register + govinfo) so agents can cite current rules and publications first, then fall back to secondary fetches.
- **API usage**: the tool reads `GOVINFO_API_KEY` (optional) and hits `https://www.federalregister.gov/api/v1/documents` plus the GovInfo search endpoint. Results are normalized into `{source,data}` items with publication dates.
- **Publishing**: register the Federal Register and govinfo search helpers (`policy_search_federal_register.register_mcp_instance(mcp)` and `policy_search_govinfo.register_mcp_instance(mcp)`) in `app/mcp_server.py` so `/mcp/tools` lists them alongside the Jira search tool.

Testing MCP tools

- **Stub FastMCP decorators** when importing tool modules inside tests so the module remains importable without the third-party package. Create a dummy `fastmcp` module or insert a stub `FastMCP` class into `sys.modules` before the import.
- **Use `importlib`** to load the tool via the package path (e.g., `import app.tools.jira_tool`) and reload it inside the test to ensure the stub takes effect before registration logic runs.
- **Mock HTTP clients** (like `httpx.AsyncClient`) to return simple payloads for deterministic unit tests, and verify the tool’s response envelope, ranking, and metadata.
- **Add conditional integration tests** that read credentials from `.env` (or environment) and skip when `JIRA_BASE_URL`, `JIRA_EMAIL`, or `JIRA_API_TOKEN` are missing; allow `JIRA_TEST_QUERY`/`JIRA_TEST_PROJECT` overrides to control which ticket is fetched.
- **Run the suite** with `pytest fastapi-mcp/tests` and expect the integration test to skip unless properly configured, keeping the cycle fast during routine development.
