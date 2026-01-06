# Unified AI Rules for the Computer Repo

This document merges the LangGraph + MCP playbooks with the FastAPI + FastMCP implementation guide so any agent updating this repo has one canonical rule set.

## Repo Purpose & Respectful Context
- The workspace houses both an MCP tool server and a LangGraph-driven app that orchestrates it; every change should reinforce that pairing.  Keep modifications additive, reversible, and consistent with the recommended layout (see `docs/agents/`).
- Prefer referencing existing markdown policy files rather than copying content unless you are updating them.

## Universal Operating Principles
- Be an engineering agent: correctness, security, maintainability, observability, and portability are equal priorities.
- Always prefer calling tools for facts/execution and use reasoning for planning or interpreting results.
- Document assumptions explicitly or ask for missing information; biases should default to the safest option.
- Keep edits minimal (small diffs) and validate uncertain changes with tools such as schema inspection, linting, or tests.
- Confidential data must never appear in prompts, responses, or commits; use env vars / secret managers.



## Role/Workflow Model
- Every task follows the same LangGraph 4-node graph: Planner → Executor → Reviewer (optional) → Finalizer.
- Planner produces workflows (choose from `docs/agents/workflows/*`), plan steps, tool call list, success criteria, assumptions, and safety constraints.
- Executor follows the chosen workflow playbook, iterates in small increments, records artifacts/tools and handles retries deterministically.
- Reviewer validates success criteria, safety guardrails, and issues minimal fixes if needed.
- Finalizer surfaces the artifact (SQL/code/files) first, explains behavior, lists run instructions, and states assumptions/caveats without exposing chain-of-thought.

## Workflow Guidelines
- Use `workflow_router.md` logic to select the right role-aware playbook (SQL, Python, Go, API integration, MCP builder, project builder). Primary workflow first; add secondary workflows in execution order if needed.
- State should follow the recommended shape (user request, workflows, plan, artifacts, tool calls, review verdict, final response). Keep tool call history & artifacts up to date.

## Project Manifest & Tool Registry
- If you add new agents or MCP tools, update `docs/agents/manifests/example_agent_manifest.yaml` and `example_tool_registry.json` to include them along with the required policy docs/templates and allowlists.
- Always enforce tags/permissions for tools (e.g., `read_only` for SQL helpers, `sandbox` for Python runners).

## FastAPI + FastMCP Implementation Rules
- Base dependencies: pin `fastmcp<3`, alongside `fastapi` and `uvicorn[standard]` (use `requirements.txt` or `pyproject.toml`).
- Build a combined app under `app/` (per existing layout). `app/mcp_server.py` registers FastMCP tools, resources, and prompts with schemas derived from type hints and docstrings. Keep tools single-purpose, synchronous or asynchronous as needed.
- `app/main.py` creates `mcp_app = mcp.http_app(path="/mcp")`, instantiates `FastAPI` with `lifespan=mcp_app.lifespan`, adds REST endpoints, and mounts the MCP ASGI app (`app.mount("/", mcp_app)` to avoid double prefix issues). Keep LifeSpan and route merging consistent.
- Provide health, example tools, and optional prompt hooks; include request IDs/durations in metadata (e.g., `_meta(start)` pattern) for observability.
- Running instructions: use `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`; note FastAPI endpoint (e.g., `/hello`) and MCP endpoint (`/mcp`).

## Testing & Deployment Expectations
- Use MCP Inspector (`npx @modelcontextprotocol/inspector <command>`) to list tools/resources/prompts, execute happy path + failure inputs, and document the test plan in the repo.
- For deployment, prefer HTTP transport over SSE; mention putting behind ALB/API Gateway, applying auth, enforcing timeouts/request size limits, adding structured logs/request IDs, and keeping schemas stable.

## Deliverables Checklist
When completing an implementation change: 
1. Provide a file tree for new/moved files.
2. Show contents of key files (especially `app/mcp_server.py` and `app/main.py`).
3. Update README with run instructions, endpoint map, and list of tools/resources/prompts.
4. Include an Inspector test plan that covers valid and invalid tool calls.

## Communications
- Keep responses concise and factual.
- When generating code: mention how to run it and wrap multiple files with a tree before contents.
- Prefer Markdown that guides other agents, referencing `docs/agents` whenever possible.

Keep this document as the single source of truth for AI behavior when modifying the `computer` repo.