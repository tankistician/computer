from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional

import httpx


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


async def federal_register_search(query: str, limit: int = 5, start_date: Optional[str] = None, end_date: Optional[str] = None, sorts: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    start = time.time()
    try:
        items = await _call_federal_register(query, limit, start_date, end_date, sorts=sorts)
        return {"ok": True, "data": {"items": items}, "meta": {"duration_ms": int((time.time() - start) * 1000)}}
    except Exception as exc:
        return {"ok": False, "error": {"code": "INTERNAL", "message": str(exc)}, "meta": {"duration_ms": int((time.time() - start) * 1000)}}


def register_mcp_instance(mcp_instance: Any) -> None:
    if mcp_instance is None:
        return
    try:
        mcp_instance.tool(federal_register_search)
    except Exception:
        pass
