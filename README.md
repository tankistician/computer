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
prod_tests/                # Python checks and templates for production verification
scripts/                   # convenience scripts (tool invocations, integrations)
tests/                     # unit tests for published tools
README.md                  # this guide
payload.json              # payload helper used by govinfo call (existing tooling)
```

## Key Guidance and Running
1. **Read `agent_instruction.md` first**—it is the merged AI rules file every contributor/agent should follow before making edits.
2. **Use the `docs/agents/` playbooks** when creating agents or tools; the manifests reference these policies for planner/executor/reviewer/finalizer nodes.
3. **For FastAPI/FastMCP work**, the `fastapi-mcp/` directory contains the running server, dependencies list, and sample `uvicorn` run command (refer to its README).
4. **Run the FastAPI + MCP stack locally** via `make up` (Docker Compose) and then exercise `/hello` (REST) and `/mcp` (MCP) endpoints as described in the docs.
5. **Use the MCP Inspector** (`npx @modelcontextprotocol/inspector <command>`) to verify tools/resources/prompts and capture valid/invalid call plans.

### GovInfo search response example

When you POST to `/mcp/tool` with `gov_policy_search`, the GovInfo tool now returns most of the fields from the GovInfo search API. Example fragment of the JSON reply:

```json
{
	"ok": true,
	"data": {
		"items": [
			{
				"title": "Vaccine Information Statements for Influenza Vaccines; Revised Instructions for Use of Vaccine Information Statements",
				"package_id": "FR-2005-11-10",
				"granule_id": "05-22441",
				"last_modified": "2025-09-24T21:55:41Z",
				"date": "2005-11-10",
				"collection": "FR",
				"result_link": "https://api.govinfo.gov/packages/FR-2005-11-10/granules/05-22441/summary",
				"download": {
					"url": "https://api.govinfo.gov/packages/FR-2005-11-10/granules/05-22441/htm"
				}
			}
		]
	},
	"meta": {
		"offset_mark": "AoIIQfwlLzhGUi0yMDE2LTA5LTA4LTIwMTYtMjE1NzU=",
		"count": 87859
	}
}

### GovInfo granule summary

After locating a package + granule pair via the GovInfo search tool, you can fetch the full summary record (including granular metadata and download links) directly from GovInfo using the curl command below. Be sure to replace `FR-2005-11-10` and `05-22441` with the values from the search result, and keep your `GOVINFO_API_KEY` handy in `.env` so the container-provided command works without extra flags.

```
curl -X 'GET' \
	'https://api.govinfo.gov/packages/FR-2005-11-10/granules/05-22441/summary?api_key=$GOVINFO_API_KEY' \
	-H 'accept: application/json'
```

GovInfo responds with a payload that looks like this (trimmed for clarity):

```json
{
	"summary": "Under the National Childhood Vaccine Injury Act (NCVIA) (42 U.S.C. 300aa-26), the CDC must develop vaccine information materials that all health care providers are required to give to patients/parents prior to administration of specific vaccines. On July 28, 2005, CDC published a notice in the Federal Register (70 FR 43694) seeking public comments on proposed new vaccine information materials for trivalent influenza vaccines and hepatitis A vaccines. The 60 day comment period ended on September 26, 2005. Following review of the comments submitted and consultation as required under the law, CDC has finalized the influenza vaccine information materials. The final influenza materials, and revised instructions for their use and for use of materials for other covered vaccines, are contained in this notice. The final hepatitis A vaccine information materials will be published later.",
	"dateIssued": "2005-11-10",
	"packageId": "FR-2005-11-10",
	"packageLink": "https://api.govinfo.gov/packages/FR-2005-11-10/summary",
	"collectionCode": "FR",
	"detailsLink": "https://www.govinfo.gov/app/details/FR-2005-11-10/05-22441",
	"agencies": [
		{
			"name": "DEPARTMENT OF HEALTH AND HUMAN SERVICES",
			"order": "1"
		},
		{
			"name": "Centers for Disease Control and Prevention",
			"order": "2"
		}
	],
	"title": "Vaccine Information Statements for Influenza Vaccines; Revised Instructions for Use of Vaccine Information Statements",
	"collectionName": "Federal Register",
	"billingCode": "4163-18-P",
	"granuleClass": "NOTICE",
	"granuleId": "05-22441",
	"download": {
		"premisLink": "https://api.govinfo.gov/packages/FR-2005-11-10/premis",
		"txtLink": "https://api.govinfo.gov/packages/FR-2005-11-10/granules/05-22441/htm",
		"zipLink": "https://api.govinfo.gov/packages/FR-2005-11-10/zip",
		"modsLink": "https://api.govinfo.gov/packages/FR-2005-11-10/granules/05-22441/mods",
		"pdfLink": "https://api.govinfo.gov/packages/FR-2005-11-10/granules/05-22441/pdf"
	},
	"relatedLink": "https://api.govinfo.gov/related/05-22441",
	"docClass": "FR",
	"lastModified": "2025-09-24T21:55:41Z",
	"category": "Regulatory Information",
	"granulesLink": "https://api.govinfo.gov/packages/FR-2005-11-10/granules?offsetMark=*&pageSize=100"
}
```

The summary tool now also surfaces this record as part of its response when you call `gov_policy_summary` via `/mcp/tool`, so downstream agents can include the human-readable summary text, download URLs, and agency metadata in their answers.
```

## Testing & Contributions
- Tests live under `tests/`; run specific suites via `python -m pytest tests/<file>` or use the `prod_tests/` scripts for integration scenarios.
- When adding tools or agents, update `docs/agents/manifests/example_agent_manifest.yaml` and `example_tool_registry.json` with the new contracts and policies.
- Document run/test steps and tool inputs/outputs in the relevant README (e.g., `fastapi-mcp/README.md` or `docs/agents/README.md`).
- Keep diffs small, include how-to-run info with code changes, and reference the `agent_instruction.md` rules in commit messages or change summaries when applicable.
