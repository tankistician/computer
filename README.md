# computer
This repository houses the MCP server tools and LangGraph-based agent workflows that work together to power the `computer` AI stack.

## Overview
- **Agent runtime (`app/`)**: LangGraph agents, runtime helpers, and MCP client wiring live under `app/src`.
- **MCP server prototype (`fastapi-mcp/`)**: FastAPI + FastMCP implementation with tools, schemas, and sample REST + MCP mounts.
- **Docs and playbooks (`docs/`)**: Agent role prompts, workflow playbooks, manifests, and policy templates for consistent behavior.
- **Tests and tooling**: `tests/` covers tool tests while `prod_tests/` holds cross-tool scripts; `scripts/` contains other helpers like `invoke_gov_inproc.py`.
- **Infrastructure notes**: `agent_instruction.md` and the docs under `docs/agents/` are the single source of truth for rules, manifests, and workflow guidance.

## Repository Layout
```
agent_instruction.md        # master AI rules file (merge of LangGraph + FastMCP guides)
agent_instruction_1.0.0.md  # original LangGraph + MCP playbook reference
agent_instruction_mcp.md    # original FastAPI + FastMCP guide
app/                       # application-level agents, graph definitions, tools, runtime support
docs/                      # role + workflow docs, manifests, architecture notes
docs/agents/README.md      # entry point for all agent playbooks
fastapi-mcp/               # FastAPI + FastMCP server implementation + tool definitions
prod_tests/                # PowerShell/python checks and templates for production verification
scripts/                   # convenience scripts (tool invocations, integrations)
tests/                     # unit tests for published tools
README.md                  # this guide
payload.json              # payload helper used by govinfo call (existing tooling)
```

## Key Guidance and Running
1. **Read `agent_instruction.md` first**—it is the merged AI rules file every contributor/agent should follow before making edits.
2. **Use the `docs/agents/` playbooks** when creating agents or tools; the manifests reference these policies for planner/executor/reviewer/finalizer nodes.
3. **For FastAPI/FastMCP work**, the `fastapi-mcp/` directory contains the running server, dependencies list, and sample `uvicorn` run command (refer to its README).
4. **Run the FastAPI + MCP stack locally** via `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000` and then exercise `/hello` (REST) and `/mcp` (MCP) endpoints as described in the docs.
5. **Use the MCP Inspector** (`npx @modelcontextprotocol/inspector <command>`) to verify tools/resources/prompts and capture valid/invalid call plans.

## Testing & Contributions
- Tests live under `tests/`; run specific suites via `python -m pytest tests/<file>` or use the `prod_tests/` scripts for integration scenarios.
- When adding tools or agents, update `docs/agents/manifests/example_agent_manifest.yaml` and `example_tool_registry.json` with the new contracts and policies.
- Document run/test steps and tool inputs/outputs in the relevant README (e.g., `fastapi-mcp/README.md` or `docs/agents/README.md`).
- Keep diffs small, include how-to-run info with code changes, and reference the `agent_instruction.md` rules in commit messages or change summaries when applicable.
