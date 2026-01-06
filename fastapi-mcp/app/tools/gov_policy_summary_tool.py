"""Fetch GovInfo granule summaries and download links.

This module exposes `gov_policy_summary(package_id, granule_id, fmt)` which
fetches the granule summary and returns a download URL and (for text-like
formats) the content.
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Any, Dict, Literal

import httpx


def _meta(start: float) -> dict[str, Any]:
    return {
        "request_id": str(uuid.uuid4()),
        "duration_ms": int((time.time() - start) * 1000),
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def _extract_download_url(download: dict[str, Any], fmt: Literal["htm", "xml", "pdf"]) -> str | None:
    mapping = {
        "htm": ("txtLink", "htmlLink", "htmLink"),
        "xml": ("xmlLink",),
        "pdf": ("pdfLink",),
    }
    for k in mapping[fmt]:
        if download.get(k):
            return download[k]
    return None


async def _fetch_granule_summary(package_id: str, granule_id: str, fmt: Literal["htm", "xml", "pdf"] = "htm") -> Dict[str, Any]:
    start = time.time()
    api_key = os.environ.get("GOVINFO_API_KEY")
    if not api_key:
        return {"ok": False, "error": {"code": "BAD_INPUT", "message": "GOVINFO_API_KEY not configured"}, "meta": _meta(start)}

    if not package_id or not granule_id:
        return {"ok": False, "error": {"code": "BAD_INPUT", "message": "package_id and granule_id are required"}, "meta": _meta(start)}

    fmt = fmt.lower()
    if fmt not in ("htm", "xml", "pdf"):
        return {"ok": False, "error": {"code": "BAD_INPUT", "message": "format must be one of: htm, xml, pdf"}, "meta": _meta(start)}

    summary_url = f"https://api.govinfo.gov/packages/{package_id}/granules/{granule_id}/summary"
    params = {"api_key": api_key}
    headers = {"Accept": "application/json"}

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(summary_url, params=params, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code if exc.response is not None else None
            return {"ok": False, "error": {"code": "UPSTREAM_ERROR", "message": f"HTTP {status}"}, "meta": _meta(start)}

        summary = resp.json()
        download = summary.get("download") or {}
        download_url = _extract_download_url(download, fmt)

        if not download_url:
            return {"ok": False, "error": {"code": "NOT_FOUND", "message": f"No {fmt} download link found"}, "data": {"summary_url": summary_url}, "meta": _meta(start)}

        content = None
        content_type = ""
        if fmt in ("htm", "xml"):
            content_resp = await client.get(download_url, params=params, timeout=60)
            content_resp.raise_for_status()
            content = content_resp.text
            content_type = content_resp.headers.get("Content-Type", "")

    return {"ok": True, "data": {"package_id": package_id, "granule_id": granule_id, "format": fmt, "summary_url": summary_url, "download_url": download_url, "content_type": content_type, "content": content, "summary": summary}, "meta": _meta(start)}
 
# GovInfo-specific export
govinfo_fetch_granule_summary = _fetch_granule_summary
# Backwards compatible alias
gov_policy_summary = govinfo_fetch_granule_summary


async def govinfo_search_granules(query: str, page_size: int = 10, offset_mark: str = "*") -> Dict[str, Any]:
    """Run GovInfo search and return items that include packageId+granuleId.

    Returns envelope: {ok: bool, data: {items: [...], next_offset_mark, raw}, error?, meta}
    """
    start = time.time()
    api_key = os.environ.get("GOVINFO_API_KEY")
    if not api_key:
        return {"ok": False, "error": {"code": "BAD_INPUT", "message": "GOVINFO_API_KEY not configured"}, "meta": _meta(start)}

    page_size = max(1, min(50, int(page_size)))
    url = "https://api.govinfo.gov/search"
    params = {"api_key": api_key}
    body = {
        "query": query,
        "pageSize": str(page_size),
        "offsetMark": offset_mark,
        "sorts": [{"field": "score", "sortOrder": "DESC"}],
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.post(url, params=params, json=body, headers={"Accept": "application/json"})
            r.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code if exc.response is not None else None
            return {"ok": False, "error": {"code": "UPSTREAM_ERROR", "message": f"HTTP {status}"}, "meta": _meta(start)}

        payload = r.json()

    items = []
    for it in payload.get("results", []) or payload.get("packages", []):
        # tolerate field name variations
        package_id = it.get("packageId") or it.get("packageID") or it.get("package_id")
        granule_id = it.get("granuleId") or it.get("granuleID") or it.get("granule_id")
        if package_id and granule_id:
            items.append({
                "package_id": package_id,
                "granule_id": granule_id,
                "title": it.get("title"),
                "collection": it.get("collection"),
                "result_link": it.get("resultLink") or it.get("result_link"),
            })

    return {"ok": True, "data": {"items": items, "next_offset_mark": payload.get("offsetMark"), "raw": payload}, "meta": _meta(start)}


async def govinfo_download_granule_text(package_id: str, granule_id: str, fmt: str = "htm") -> Dict[str, Any]:
    """Given package_id and granule_id, fetch granule summary and download the requested rendition.

    Returns envelope: {ok, data: {package_id, granule_id, format, content_type, content, download_url, summary_url}, error?, meta}
    """
    return await _fetch_granule_summary(package_id, granule_id, fmt)  # reuse implementation above


def register_mcp_instance(mcp_instance: Any) -> None:
    """Register the GovInfo search and summary helpers with FastMCP."""
    if mcp_instance is None:
        return
    try:
        mcp_instance.tool(govinfo_search_granules)
    except Exception:
        pass
    try:
        mcp_instance.tool(govinfo_download_granule_text)
    except Exception:
        pass