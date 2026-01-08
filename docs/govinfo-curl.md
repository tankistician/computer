GovInfo curl usage (macOS)

These examples use standard `curl` and a JSON file payload.

Prerequisites:
- Export `GOVINFO_API_KEY` in your shell (or put it in your environment before running the command).

1) Create `payload.json` (repo root example)

```bash
cat > payload.json <<'JSON'
{
  "query": "education",
  "pageSize": 10,
  "offsetMark": "*",
  "sorts": [ { "field": "relevancy", "sortOrder": "DESC" } ],
  "historical": true,
  "resultLevel": "default"
}
JSON
```

2) POST the payload

```bash
curl -i -X POST "https://api.govinfo.gov/search?api_key=${GOVINFO_API_KEY}" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  --data-binary '@payload.json'
```

Notes:
- If GovInfo returns HTTP 500, capture `X-Api-Umbrella-Request-Id` and the timestamp and contact GovInfo support.
