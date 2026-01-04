GovInfo PowerShell & curl usage

When using the GovInfo Search API from PowerShell, prefer sending a properly-quoted JSON body to the real `curl` binary (`curl.exe`) or use PowerShell's `Invoke-WebRequest` / `Invoke-RestMethod` with `ConvertTo-Json` to avoid quoting issues.

Working examples (PowerShell):

1) Create a `payload.json` safely using a here-string and send with `curl.exe`:

```powershell
@'
{
  "query": "education",
  "pageSize": 10,
  "offsetMark": "*",
  "sorts": [ { "field": "relevancy", "sortOrder": "DESC" } ],
  "historical": true,
  "resultLevel": "default"
}
'@ | Out-File -FilePath payload.json -Encoding utf8

curl.exe -i -X POST "https://api.govinfo.gov/search?api_key=$env:GOVINFO_API_KEY" \
  -H "accept: application/json" -H "Content-Type: application/json" \
  --data-binary '@payload.json'
```

2) Pipe a here-string directly to `curl.exe` (no temp file):

```powershell
@'
{
  "query": "education",
  "pageSize": 10,
  "offsetMark": "*",
  "sorts": [ { "field": "relevancy", "sortOrder": "DESC" } ],
  "historical": true,
  "resultLevel": "default"
}
'@ | curl.exe -i -X POST "https://api.govinfo.gov/search?api_key=$env:GOVINFO_API_KEY" \
     -H "accept: application/json" -H "Content-Type: application/json" --data-binary @-
```

3) PowerShell-native (no curl): build JSON with `ConvertTo-Json` and call `Invoke-WebRequest`:

```powershell
$body = @{
  query = "education"
  pageSize = 10
  offsetMark = "*"
  sorts = @(@{ field = "relevancy"; sortOrder = "DESC" })
  historical = $true
  resultLevel = "default"
} | ConvertTo-Json -Depth 5

$response = Invoke-WebRequest -Uri "https://api.govinfo.gov/search?api_key=$env:GOVINFO_API_KEY" \
  -Method Post -ContentType 'application/json' -Body $body -Headers @{ Accept = 'application/json' }

$response.StatusCode
$response.Headers['X-Api-Umbrella-Request-Id']
($response.Content | ConvertFrom-Json) | ConvertTo-Json -Depth 5
```

Notes:
- Use `curl.exe` (not the PowerShell `curl` alias) to match examples in the GovInfo docs.
- If you see `\x0a` or unquoted tokens in a `curl --trace` output, the JSON was not transmitted verbatim — that usually indicates a quoting issue with PowerShell.
- If GovInfo returns HTTP 500 after sending properly formatted JSON, capture `X-Api-Umbrella-Request-Id` and the timestamp and contact GovInfo support.
