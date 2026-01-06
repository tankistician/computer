"""Python example: hit the GovInfo & Federal Register endpoints directly.

NOTE: Example script for manual testing and exploration. This file is a
developer convenience and should be adapted and hardened (timeouts, retries,
secrets handling, logging, assertions) before using in automation or CI.

Run this from the `fastapi-mcp/prod_tests` folder with the venv active.
"""
import os
import json
import asyncio
from pathlib import Path

import httpx


def load_env_from_repo_root() -> None:
    env_path = Path(__file__).resolve().parents[1].parent / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if not key or not value:
            continue
        os.environ.setdefault(key, value)


async def call_govinfo():
    api_key = os.environ.get("GOVINFO_API_KEY")
    if not api_key:
        print("GOVINFO_API_KEY not set; load it into the environment or ../.env")
        return
    payload_path = os.path.join(os.path.dirname(__file__), "..", "payload.json")
    with open(payload_path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post("https://api.govinfo.gov/search", params={"api_key": api_key}, json=payload)
        print(r.status_code)
        try:
            print(json.dumps(r.json(), indent=2))
        except Exception:
            print(r.text)


async def main():
    load_env_from_repo_root()
    await call_govinfo()


if __name__ == "__main__":
    asyncio.run(main())
