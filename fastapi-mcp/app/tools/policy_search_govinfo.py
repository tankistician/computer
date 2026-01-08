from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional

import httpx


async def _call_govinfo(query: str, limit: int, start_date: Optional[str], end_date: Optional[str], sorts: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    api_key = os.environ.get("GOVINFO_API_KEY")
    if not api_key:
        return {"results": [], "offsetMark": None, "count": 0}
    params = {"api_key": api_key}
    json_payload: dict[str, Any] = {"query": query, "pageSize": limit}
    json_payload.setdefault("offsetMark", "*")
    if sorts:
        json_payload["sorts"] = sorts
    if start_date:
        json_payload["fromDate"] = start_date
    if end_date:
        json_payload["toDate"] = end_date

    headers = {"Accept": "application/json", "Content-Type": "application/json", "X-Api-Key": api_key}
    async with httpx.AsyncClient(timeout=30) as client:
        last_exc = None
        payload: dict[str, Any] = {}
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
                if status == 503 and attempt < 3:
                    retry_after = resp_headers.get("Retry-After")
                    if retry_after:
                        try:
                            wait = int(float(retry_after))
                        except Exception:
                            wait = 2 ** attempt
                        await asyncio.sleep(wait)
                        continue
                if status and 500 <= status < 600 and attempt < 3:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
            except Exception as exc:
                last_exc = exc
                if attempt < 3:
                    await asyncio.sleep(2 ** attempt)
        if last_exc is not None:
            raise last_exc

    return payload


async def govinfo_search(query: str, limit: int = 5, start_date: Optional[str] = None, end_date: Optional[str] = None, sorts: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    try:
        payload = await _call_govinfo(query, limit, start_date, end_date, sorts=sorts)
        records = payload.get("results", [])
        items = []
        for record in records:
            items.append({
                "type": record.get("collectionCode"),
                "title": record.get("title"),
                "collection": record.get("collectionCode"),
                "package_id": record.get("packageId"),
                "granule_id": record.get("granuleId"),
                "last_modified": record.get("lastModified"),
                "date": record.get("dateIssued"),
                "date_ingested": record.get("dateIngested"),
                "government_author": record.get("governmentAuthor"),
                "result_link": record.get("resultLink"),
                "related_link": record.get("relatedLink"),
                "download": record.get("download"),
                "raw": record,
            })
        meta = {
            "offset_mark": payload.get("offsetMark"),
            "count": payload.get("count"),
        }
        return {"ok": True, "data": {"items": items}, "meta": meta}
    except Exception as exc:
        return {"ok": False, "error": {"code": "INTERNAL", "message": str(exc)}, "meta": {}}


def register_mcp_instance(mcp_instance: Any) -> None:
    if mcp_instance is None:
        return
    try:
        mcp_instance.tool(govinfo_search)
    except Exception:
        pass
