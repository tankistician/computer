from __future__ import annotations

import os
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

import httpx

from difflib import SequenceMatcher


def _meta(start: float) -> dict[str, Any]:
    return {"request_id": str(uuid.uuid4()), "duration_ms": int((time.time() - start) * 1000)}


def _jql_escape_phrase(s: str) -> str:
    return s.replace('"', '\\"') if s is not None else ""


def _adf_to_text(node: Any) -> str:
    """Small ADF flattener: extracts visible text nodes."""
    if node is None:
        return ""
    if isinstance(node, dict):
        t = node.get("type")
        if t == "text":
            return node.get("text", "")
        return "".join(_adf_to_text(c) for c in node.get("content", []))
    if isinstance(node, list):
        return "".join(_adf_to_text(x) for x in node)
    return str(node)


def _score_relevance(query: str, candidates: List[Tuple[str, dict]]) -> List[Tuple[float, dict]]:
    q = (query or "").lower()
    out: List[Tuple[float, dict]] = []
    for text, item in candidates:
        t = (text or "").lower()
        score = SequenceMatcher(None, q, t).ratio()
        out.append((score, item))
    out.sort(key=lambda x: x[0], reverse=True)
    return out


async def _jira_search_closest(
    query: str,
    project_key: Optional[str] = None,
    mode: str = "text",
    max_results: int = 10,
    next_page_token: Optional[str] = None,
    fields: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Search Jira for the issue closest to `query`."""
    start = time.time()

    try:
        base_url = os.environ["JIRA_BASE_URL"].rstrip("/")
        email = os.environ["JIRA_EMAIL"]
        api_token = os.environ["JIRA_API_TOKEN"]
    except KeyError as e:
        return {
            "ok": False,
            "error": {"code": "MISSING_CONFIG", "message": f"Missing env var: {e.args[0]}"},
            "meta": _meta(start),
        }

    max_results = max(1, min(int(max_results), 50))
    phrase = _jql_escape_phrase((query or "").strip())
    if not phrase:
        return {
            "ok": False,
            "error": {"code": "BAD_INPUT", "message": "query cannot be empty"},
            "meta": _meta(start),
        }

    text_clause = f'text ~ "{phrase}"' if mode != "description" else f'description ~ "{phrase}"'
    project_clause = f'project = "{_jql_escape_phrase(project_key)}"' if project_key else None
    jql = f"{project_clause} AND {text_clause}" if project_clause else text_clause

    default_fields = [
        "summary",
        "status",
        "assignee",
        "reporter",
        "priority",
        "issuetype",
        "project",
        "created",
        "updated",
        "description",
    ]
    request_fields = list(dict.fromkeys(default_fields + (fields or [])))

    params = {
        "jql": jql,
        "maxResults": max_results,
        "fields": ",".join(request_fields),
    }
    if next_page_token:
        params["nextPageToken"] = next_page_token

    url = f"{base_url}/rest/api/3/search/jql"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                url,
                params=params,
                headers={"Accept": "application/json"},
                auth=(email, api_token),
            )
            resp.raise_for_status()
            data = resp.json()

        candidates: List[Tuple[str, dict]] = []
        for issue in data.get("issues", []):
            f = issue.get("fields") or {}
            desc = f.get("description")
            desc_text = _adf_to_text(desc)
            summary = f.get("summary") or ""
            item = {
                "key": issue.get("key"),
                "id": issue.get("id"),
                "self": issue.get("self"),
                "summary": summary,
                "status": (f.get("status") or {}).get("name"),
                "assignee": (f.get("assignee") or {}).get("displayName"),
                "reporter": (f.get("reporter") or {}).get("displayName"),
                "priority": (f.get("priority") or {}).get("name"),
                "issue_type": (f.get("issuetype") or {}).get("name"),
                "project": (f.get("project") or {}).get("key"),
                "created": f.get("created"),
                "updated": f.get("updated"),
                "description_text": desc_text,
                "description_raw": desc,
            }
            cand_text = " ".join([summary, desc_text, issue.get("key", "")])
            candidates.append((cand_text, item))

        ranked = _score_relevance(query, candidates)
        ranked_items = [{"score": float(score), "issue": item} for score, item in ranked]
        best = ranked_items[0] if ranked_items else None

        return {
            "ok": True,
            "data": {
                "jql": jql,
                "best_match": best,
                "ranked": ranked_items,
                "nextPageToken": data.get("nextPageToken"),
                "isLast": data.get("isLast"),
            },
            "meta": _meta(start),
        }
    except httpx.HTTPStatusError as e:
        return {"ok": False, "error": {"code": "UPSTREAM_ERROR", "message": str(e)}, "meta": _meta(start)}
    except Exception as e:
        return {"ok": False, "error": {"code": "INTERNAL", "message": str(e)}, "meta": _meta(start)}


jira_search_closest = _jira_search_closest


def register_mcp_instance(mcp_instance: Any) -> None:
    global jira_search_closest
    if mcp_instance is None:
        return
    jira_search_closest = mcp_instance.tool(_jira_search_closest)
