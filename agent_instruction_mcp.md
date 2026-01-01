````markdown
# Build an MCP Server with FastAPI + FastMCP (AI Implementation Guide)

You are an engineering agent building a **Model Context Protocol (MCP)** server using **FastAPI** + **FastMCP**.  
You must produce a working project that:
- runs locally,
- exposes multiple **tools** (and optionally resources/prompts),
- and has a clean path to hosted deployment.

MCP servers typically expose **Tools**, **Resources**, and **Prompts**, and support transports like **stdio** and **Streamable HTTP**. :contentReference[oaicite:0]{index=0}

---

## 0) Key choices you must make

### FastMCP version pin (recommended)
FastMCP 3.0 may introduce breaking changes; pin to v2 for stability: `fastmcp<3`. :contentReference[oaicite:1]{index=1}

### Integration strategy with FastAPI (pick one, or do both)
FastMCP supports two patterns with FastAPI:
1) **Generate an MCP server from an existing FastAPI app** (`FastMCP.from_fastapi(...)`). :contentReference[oaicite:2]{index=2}  
2) **Mount an MCP server into a FastAPI app** using the MCP ASGI app returned by `http_app(...)`. :contentReference[oaicite:3]{index=3}  

FastMCP notes that auto-converting APIs is good for **bootstrapping/prototyping**, but curated MCP servers typically perform better for LLMs. :contentReference[oaicite:4]{index=4}

### Transport plan
- **Local dev / Claude Desktop**: `stdio` (FastMCP `run()` default). :contentReference[oaicite:5]{index=5}  
- **Hosted / AWS**: **HTTP transport (Streamable HTTP)** via `transport="http"` or by mounting the MCP ASGI app into FastAPI. HTTP supports multiple clients and streaming. :contentReference[oaicite:6]{index=6}  
- **Avoid SSE for new builds** (legacy/backward compatibility). :contentReference[oaicite:7]{index=7}  

---

## 1) Project skeleton (recommended)

You are building a combined server: **FastAPI** routes + an **MCP endpoint** mounted under `/mcp`.

```text
my-mcp-fastapi/
├── pyproject.toml            # or requirements.txt
├── README.md
└── app/
    ├── __init__.py
    ├── mcp_server.py         # FastMCP instance + tools/resources/prompts
    └── main.py               # FastAPI app + mount MCP ASGI app
````

---

## 2) Dependencies

### Minimal dependencies

* `fastapi`
* `uvicorn[standard]`
* `fastmcp<3`

Example (pip):

```bash
pip install "fastmcp<3" fastapi "uvicorn[standard]"
```

FastMCP provides a CLI and recommends installing the package directly. ([GitHub][1])

---

## 3) Implement the MCP server (tools/resources/prompts)

Create `app/mcp_server.py`:

```python
from __future__ import annotations

import time
import uuid
from typing import Any

from fastmcp import FastMCP

# FastMCP holds your tools/resources/prompts and generates schemas from type hints + docstrings. :contentReference[oaicite:9]{index=9}
mcp = FastMCP("my-fastapi-mcp")

def _meta(start: float) -> dict[str, Any]:
    return {
        "request_id": str(uuid.uuid4()),
        "duration_ms": int((time.time() - start) * 1000),
    }

# ---- Tools ----

@mcp.tool
def add(a: int, b: int) -> dict[str, Any]:
    """Add two integers. Returns a stable JSON envelope."""
    start = time.time()
    return {"ok": True, "data": {"sum": a + b}, "meta": _meta(start)}

@mcp.tool
def normalize_name(name: str) -> dict[str, Any]:
    """Normalize a name (trim, collapse spaces, title-case)."""
    start = time.time()
    cleaned = " ".join(name.strip().split())
    return {"ok": True, "data": {"normalized": cleaned.title()}, "meta": _meta(start)}

# ---- Resources (optional) ----

@mcp.resource("health://status")
def health() -> str:
    """Health check resource."""
    return "ok"

# ---- Prompts (optional) ----
# Prompts are reusable templates; FastMCP supports defining them with @mcp.prompt. :contentReference[oaicite:10]{index=10}
@mcp.prompt(title="Code Review")
def code_review_prompt(code: str) -> str:
    """Prompt template for reviewing code."""
    return (
        "Review the code for correctness, security, and maintainability.\n\n"
        f"CODE:\n{code}\n"
    )
```

### Tool design rule you must follow

Keep tools small and single-purpose. Tools can be sync or async; FastMCP generates schemas from type hints and docstrings. ([GitHub][1])

---

## 4) Mount MCP into FastAPI (the core FastAPI+FastMCP pattern)

Create `app/main.py`:

```python
from __future__ import annotations

from fastapi import FastAPI

from .mcp_server import mcp

# Create the MCP ASGI app and mount it into FastAPI.
# FastMCP provides http_app(path="/mcp") which returns an ASGI app you can mount. :contentReference[oaicite:12]{index=12}
mcp_app = mcp.http_app(path="/mcp")

# IMPORTANT: pass the MCP app lifespan into FastAPI so MCP session management runs correctly. :contentReference[oaicite:13]{index=13}
app = FastAPI(title="My FastAPI + MCP Server", lifespan=mcp_app.lifespan)

# Your normal REST endpoints can coexist
@app.get("/hello")
def hello() -> dict:
    return {"message": "hello from FastAPI"}

# Mount MCP under a path segment; MCP endpoint becomes /mcp/mcp/ if you mount at /mcp.
# Prefer mounting at "/" or "/mcp" carefully to avoid double path confusion.
app.mount("/", mcp_app)
```

### Notes you must respect

* FastMCP’s FastAPI integration explicitly recommends mounting the MCP ASGI app via `http_app(...)` and passing `lifespan=mcp_app.lifespan` into FastAPI. ([FastMCP][2])
* You can also combine routes more explicitly (see section 6).

---

## 5) Run locally

### Run the combined FastAPI app

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Your endpoints:

* FastAPI: `GET http://127.0.0.1:8000/hello`
* MCP endpoint: typically at `http://127.0.0.1:8000/mcp` depending on `http_app(path=...)` and mount path.

(When running a standalone FastMCP HTTP server, FastMCP states the endpoint is at `/mcp` by default on the host/port you specify.) ([FastMCP][3])

---

## 6) Optional: “LLM-friendly API” (serve both REST + MCP in one FastAPI app)

If you already have a FastAPI app with routes and you also want MCP routes:
FastMCP shows a pattern that merges route lists and uses the MCP lifespan. ([FastMCP][2])

High-level pattern:

* Convert or build MCP server
* Build MCP ASGI app via `http_app(path="/mcp")`
* Create a new FastAPI app whose `routes=[*mcp_app.routes, *api_app.routes]` and `lifespan=mcp_app.lifespan` ([FastMCP][2])

Use this when you want the MCP routes to live “alongside” your REST routes without a mount prefix.

---

## 7) Optional: Generate MCP tools from existing FastAPI endpoints

This is for bootstrapping:

```python
from fastapi import FastAPI
from fastmcp import FastMCP

app = FastAPI()

# Convert FastAPI endpoints into MCP components (tools by default). :contentReference[oaicite:18]{index=18}
mcp = FastMCP.from_fastapi(app=app)

if __name__ == "__main__":
    mcp.run()
```

FastMCP explicitly frames this as a fast way to bootstrap, but recommends curated MCP servers for best LLM performance. ([FastMCP][2])

---

## 8) Testing: MCP Inspector (required)

Use MCP Inspector to test and debug MCP servers. It runs via `npx` and supports inspecting local servers. ([Model Context Protocol][4])

Example:

```bash
npx @modelcontextprotocol/inspector <command>
```

The Inspector UI lets you:

* list tools/resources/prompts,
* inspect schemas,
* execute tools with custom inputs,
* view logs/notifications. ([Model Context Protocol][4])

---

## 9) Deployment guidance (AWS path)

### Recommended approach

For remote deployments, use **HTTP transport** (Streamable HTTP) rather than SSE. ([FastMCP][3])

FastMCP describes HTTP transport as supporting network access, multiple concurrent clients, and streaming, and shows enabling it via:

````python
mcp.run(transport="http", host="127.0.0.1", port=8000)
``` :contentReference[oaicite:23]{index=23}

### Practical AWS notes (implementation-level)
- Put behind ALB/API Gateway
- Add auth (token/OAuth/IAM depending on environment)
- Enforce timeouts and request size limits
- Add structured logs and request IDs
- Keep tool schemas stable across local/hosted

---

## 10) Deliverables you must output as the implementation agent

When you finish implementing:
1) File tree
2) Full contents of `app/mcp_server.py` and `app/main.py`
3) README with:
   - run instructions
   - endpoint locations
   - list of tools/resources/prompts
4) An Inspector test plan:
   - call each tool with valid inputs
   - call each tool with invalid inputs and confirm predictable errors

---

## Appendix: Why FastMCP “feels easy”
FastMCP is designed so “decorating a Python function” is often enough—schemas are derived from type hints and docstrings. :contentReference[oaicite:24]{index=24}
````

If you want, paste the *first tools you actually plan to ship* (e.g., `db.schema`, `db.query_readonly`, `http.request`), and I’ll adapt the examples to:

* include safe input validation patterns for those tools,
* include recommended limits/timeouts,
* and show a clean `/mcp` mount layout that avoids double-prefix issues.

[1]: https://github.com/jlowin/fastmcp "GitHub - jlowin/fastmcp:  The fast, Pythonic way to build MCP servers and clients"
[2]: https://gofastmcp.com/integrations/fastapi "FastAPI  FastMCP - FastMCP"
[3]: https://gofastmcp.com/deployment/running-server "Running Your Server - FastMCP"
[4]: https://modelcontextprotocol.io/docs/tools/inspector "MCP Inspector - Model Context Protocol"
