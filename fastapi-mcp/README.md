# fastapi-mcp

Minimal FastAPI + FastMCP server scaffold.

Status: skeleton only — tools not yet implemented.

Run (after installing dependencies):

```powershell
cd fastapi-mcp
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Endpoints (once running):
- FastAPI: `GET http://127.0.0.1:8000/hello`
- MCP (when mounted): `http://127.0.0.1:8000/mcp` (tool endpoints exposed by FastMCP)

Next steps:
- Confirm tool list to implement (e.g., `db.schema`, `db.query_readonly`, `http.request`, etc.).
- I'll then add `app/mcp_server.py` tools and the Inspector test plan.
