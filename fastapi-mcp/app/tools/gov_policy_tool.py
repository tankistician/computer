import os
import time
import uuid
from typing import Any, Dict, Iterable, List, Optional

import httpx
import asyncio


def _meta(start: float, source: Optional[str] = None) -> dict[str, Any]:
    out = {"request_id": str(uuid.uuid4()), "duration_ms": int((time.time() - start) * 1000)}
    if source:
        out["source"] = source
    out["fetched_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return out


def _normalize_sources(sources: Optional[Iterable[str]]) -> List[str]:
    allowed = ("federal_register", "govinfo")
    if not sources:
        return [allowed[0]]
    normalized = []
    for source in sources:
        src = source.strip().lower()
        if src in allowed and src not in normalized:
            normalized.append(src)
    return normalized or [allowed[0]]


async def _call_federal_register(query: str, limit: int, start_date: Optional[str], end_date: Optional[str], sorts: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, Any]]:
    params: dict[str, Any] = {
        "per_page": limit,
        "order": "relevance",
        "conditions[any]": query,
    }
    if start_date:
        params["conditions[from]"] = start_date
    if end_date:
        params["conditions[to]"] = end_date

    headers = {"Accept": "application/json"}
    async with httpx.AsyncClient(timeout=30) as client:
        # Simple retry loop to handle transient upstream failures
        last_exc = None
        payload = {}
        for attempt in range(1, 4):
            try:
                resp = await client.get(
                    "https://www.federalregister.gov/api/v1/documents",
                    params=params,
                    headers=headers,
                )
                resp.raise_for_status()
                payload = resp.json()
                last_exc = None
                break
            except Exception as exc:
                last_exc = exc
                if attempt < 3:
                    await asyncio.sleep(2 ** attempt)
        if last_exc is not None:
            raise last_exc

    items = []
    for result in payload.get("results", []):
        items.append({
            "type": "federal_register",
            "title": result.get("title"),
            "agency": result.get("agency"),
            "publication_date": result.get("publication_date"),
            "url": result.get("html_url"),
            "abstract": result.get("abstract"),
        })
    return items


async def _call_govinfo(query: str, limit: int, start_date: Optional[str], end_date: Optional[str], sorts: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, Any]]:
    api_key = os.environ.get("GOVINFO_API_KEY")
    if not api_key:
        return []
    # GovInfo Search Service requires POST with a JSON body. Prefer sending
    # the api.data.gov key in the `X-Api-Key` header (supported by api.data.gov).
    # Put the API key in the query params (supported by api.data.gov examples)
    params = {"api_key": api_key}
    # GovInfo accepts numeric pageSize as in the API docs example; use int
    json_payload: dict[str, Any] = {"query": query, "pageSize": limit}
    # Use offsetMark="*" for first request behavior (optional)
    json_payload.setdefault("offsetMark", "*")
    # Support sorts array per GovInfo Search Service
    if sorts:
        json_payload["sorts"] = sorts
    if start_date:
        json_payload["fromDate"] = start_date
    if end_date:
        json_payload["toDate"] = end_date

    # Include X-Api-Key header as well (both forms are supported). Keep Accept/Content-Type.
    headers = {"Accept": "application/json", "Content-Type": "application/json", "X-Api-Key": api_key}
    async with httpx.AsyncClient(timeout=30) as client:
        last_exc = None
        payload = {}
        for attempt in range(1, 4):
            try:
                resp = await client.post(
                    "https://api.govinfo.gov/search",
                    params=params,
                    json=json_payload,
                    headers=headers,
                )
                resp.raise_for_status()
                payload = resp.json()
                last_exc = None
                break
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                status = getattr(exc.response, "status_code", None)
                resp_headers = exc.response.headers if exc.response is not None else {}
                # If the server asks us to wait, honor Retry-After for 503
                if status == 503 and attempt < 3:
                    retry_after = resp_headers.get("Retry-After")
                    if retry_after:
                        try:
                            wait = int(float(retry_after))
                        except Exception:
                            wait = 2 ** attempt
                        await asyncio.sleep(wait)
                        continue
                # Retry on other server errors (5xx)
                if status and 500 <= status < 600 and attempt < 3:
                    await asyncio.sleep(2 ** attempt)
                    continue
                # Non-retryable or final attempt: re-raise
                raise
            except Exception as exc:
                last_exc = exc
                if attempt < 3:
                    await asyncio.sleep(2 ** attempt)
        if last_exc is not None:
            raise last_exc

    items = []
    for record in payload.get("results", []):
        items.append({
            "type": "govinfo",
            "title": record.get("title"),
            "collection": record.get("collection"),
            "date": record.get("dateIssued"),
            "url": record.get("url"),
        })
    return items


SOURCE_HANDLERS = {
    "federal_register": _call_federal_register,
    "govinfo": _call_govinfo,
}


async def _gov_policy_search(
    query: str,
    sources: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 5,
    sorts: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    start = time.time()
    if not query or not query.strip():
        return {"ok": False, "error": {"code": "BAD_INPUT", "message": "query required"}, "meta": _meta(start)}

    selected = _normalize_sources(sources)
    results: List[Dict[str, Any]] = []
    for source in selected:
        handler = SOURCE_HANDLERS[source]
        try:
            # Pass sorts through to handlers where supported
            items = await handler(query, limit, start_date, end_date, sorts=sorts)
            results.extend({"source": source, **item} for item in items)
        except httpx.HTTPStatusError as exc:  # upstream HTTP errors we can inspect
            resp = exc.response
            status = resp.status_code if resp is not None else None
            headers = resp.headers if resp is not None else {}
            body = None
            try:
                body = resp.text if resp is not None else None
            except Exception:
                body = None

            if status == 429:
                err = {"code": "RATE_LIMITED", "message": "Rate limit exceeded", "detail": body}
                meta = {"request_id": headers.get("X-Api-Umbrella-Request-Id"), "rate_limit_remaining": headers.get("X-RateLimit-Remaining"), "rate_limit_limit": headers.get("X-RateLimit-Limit")}
            elif status in (401, 403):
                err = {"code": "BAD_AUTH", "message": "Authentication or authorization failed", "detail": body}
                meta = {"request_id": headers.get("X-Api-Umbrella-Request-Id")}
            elif status == 503:
                err = {"code": "UPSTREAM_UNAVAILABLE", "message": "Upstream service unavailable; try again later", "detail": body}
                meta = {"request_id": headers.get("X-Api-Umbrella-Request-Id"), "retry_after": headers.get("Retry-After")}
            else:
                err = {"code": "UPSTREAM_ERROR", "message": f"HTTP {status}", "detail": body}
                meta = {"request_id": headers.get("X-Api-Umbrella-Request-Id")}

            results.append({"source": source, "error": err, "meta": meta})
        except Exception as exc:  # pragma: no cover - other upstream errors
            results.append({"source": source, "error": {"code": "INTERNAL", "message": str(exc)}})

    ranked = sorted(results, key=lambda r: r.get("publication_date") or r.get("date") or "", reverse=True)
    return {
        "ok": True,
        "data": {
            "query": query,
            "sources": selected,
            "results": ranked[: limit],
        },
        "meta": _meta(start, source="gov_policy_search"),
    }


gov_policy_search = _gov_policy_search


def register_mcp_instance(mcp_instance: Any) -> None:
    global gov_policy_search
    if mcp_instance is None:
        return
    gov_policy_search = mcp_instance.tool(_gov_policy_search)