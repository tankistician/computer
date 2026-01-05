"""Python example: hit the GovInfo & Federal Register endpoints directly.

NOTE: Example script for manual testing and exploration. This file is a
developer convenience and should be adapted and hardened (timeouts, retries,
secrets handling, logging, assertions) before using in automation or CI.

Run this from the `fastapi-mcp/prod_tests` folder with the venv active.
"""
import os
import json
import httpx
import asyncio


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


async def call_federal_register():
    params = {"per_page": 2, "conditions[any]": "education"}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get("https://www.federalregister.gov/api/v1/documents", params=params)
        print(r.status_code)
        try:
            print(json.dumps(r.json(), indent=2))
        except Exception:
            print(r.text)


async def main():
    await call_govinfo()
    await call_federal_register()


if __name__ == "__main__":
    asyncio.run(main())
