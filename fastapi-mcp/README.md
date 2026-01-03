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
