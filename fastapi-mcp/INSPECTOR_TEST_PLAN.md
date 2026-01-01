# Inspector Test Plan

This document contains quick tests you can run with `curl` (or the MCP Inspector) to exercise the example MCP tools in this repo.

Notes
- The project mounts the MCP ASGI app at `/mcp` when running via `uvicorn app.main:app`.
- FastMCP's HTTP tool call shape varies by implementation; these examples assume a simple HTTP POST to `/mcp/tool` with JSON: `{ "tool": "<name>", "input": { ... } }`.
- If your FastMCP install exposes a different path/shape, adapt accordingly or use the MCP Inspector UI.

1) List tools (Inspector or MCU UI)
- Use the Inspector CLI (`npx @modelcontextprotocol/inspector`) to list tools and inspect schemas.

2) Call `add` tool

```powershell
curl -X POST "http://127.0.0.1:8000/mcp/tool" -H "Content-Type: application/json" -d '{"tool":"add","input":{"a":2,"b":3}}'
```

Expected response (JSON):

```json
{"ok":true,"tool":"add","output":{"ok":true,"data":{"sum":5},"meta":{...}}}
```

3) Call `normalize_name` tool

```powershell
curl -X POST "http://127.0.0.1:8000/mcp/tool" -H "Content-Type: application/json" -d '{"tool":"normalize_name","input":{"name":"  alice   o\'connor  "}}'
```

Expected response JSON contains `output.data.normalized` with a title-cased string, e.g. `"Alice O'Connor"`.

4) Health resource (direct HTTP or Inspector)

Some MCP servers expose resources differently; you can query the resource via the Inspector or by calling the resource endpoint if exposed. Example conceptual call:

```powershell
curl -X GET "http://127.0.0.1:8000/mcp/resource/health://status"
```

Expected: `ok` (or a JSON envelope depending on server shape).

5) Prompt template (inspect via Inspector)
- Use Inspector to view the `Code Review` prompt template and test it with a sample code snippet.

Troubleshooting
- If you get 404s against `/mcp/tool`, inspect the mounted routes or use the Inspector CLI to discover the correct endpoints.
- Use `uvicorn app.main:app --reload --port 8000` to run the app locally before testing.
