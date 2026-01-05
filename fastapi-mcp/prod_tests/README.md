# MCP Production Test Framework

IMPORTANT: Example Scripts and Templates

The files in this directory are examples and templates intended to help you
establish a repeatable process for validating MCP-enabled tools. They are
NOT production-ready or CI-safe by default. Before using them in automated
pipelines, adapt the scripts to your environment, add proper error handling,
and convert manual checks into guarded pytest integrations.

This folder contains scripts and templates to validate MCP-enabled tools end-to-end.

Overview
- `01_query_source.*`  — illustrations for hitting the upstream source directly (GovInfo / Federal Register).
- `03_invoke_tool_inproc.py` — call the tool implementation in-process (no server).
- `04_invoke_tool_http.py` — call the tool via the MCP HTTP interface (requires server running).
- `05_pytest_template.md` — a template for converting a manual smoke check into an automated pytest integration.
- `run_all.ps1` — PowerShell orchestrator to run the smoke checks (manual use).

Process (recommended)
1. Query the upstream source directly to confirm expected raw results and payload shape.
2. Implement the tool in `app/tools/` and run the in-process script to confirm behavior.
3. Start the FastAPI server (mounts MCP at `/mcp`) and run the HTTP invocation script.
4. Convert the successful manual checks into a guarded pytest integration test and add to `tests/integration/`.

Environment notes
- Scripts assume you have a Python venv activated and `PYTHONPATH` set to the `fastapi-mcp` package for in-process calls.
- For PowerShell scripts, load environment variables from the project `.env` if present.

See the individual scripts for usage examples.
