import asyncio
import json
from app.mcp_server import gov_policy_search

async def main():
    # Query both sources with a small limit so this runs quickly
    result = await gov_policy_search(
        query="education",
        sources=["govinfo", "federal_register"],
        limit=3,
    )
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
