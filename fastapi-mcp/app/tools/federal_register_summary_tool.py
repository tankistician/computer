"""Tools to fetch Federal Register document summaries."""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict

import httpx


def _meta(start: float) -> dict[str, Any]:
    return {
        "request_id": str(uuid.uuid4()),
        "duration_ms": int((time.time() - start) * 1000),
    }


async def federal_register_get_document_summary(document_id: str, fmt: str = "htm") -> Dict[str, Any]:
    """Fetch a Federal Register document summary and optionally download HTML/text content."""
    start = time.time()
    if not document_id:
        return {"ok": False, "error": {"code": "BAD_INPUT", "message": "document_id is required"}, "meta": _meta(start)}

    url = f"https://www.federalregister.gov/api/v1/documents/{document_id}"
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url, params={})
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code if exc.response is not None else None
            return {"ok": False, "error": {"code": "UPSTREAM_ERROR", "message": f"HTTP {status}"}, "meta": _meta(start)}

        payload = resp.json()
        download_url = payload.get("html_url") or payload.get("document_number")
        content = None
        content_type = ""
        if fmt in ("htm", "xml") and download_url:
            try:
                content_resp = await client.get(download_url, timeout=60)
                content_resp.raise_for_status()
                content = content_resp.text
                content_type = content_resp.headers.get("Content-Type", "")
            except Exception:
                content = None

    data = {
        "document_id": document_id,
        "format": fmt,
        "summary": payload,
        "download_url": download_url,
        "content_type": content_type,
        "content": content,
    }
    return {"ok": True, "data": data, "meta": _meta(start)}


def register_mcp_instance(mcp_instance: Any) -> None:
    if mcp_instance is None:
        return
    try:
        mcp_instance.tool(federal_register_get_document_summary)
    except Exception:
        pass
