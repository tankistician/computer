<#
EXAMPLE SCRIPT — Query upstream source

This is a PowerShell example to demonstrate how to POST to the GovInfo search
API. It is intentionally simple and meant for local, manual use only. Adapt
and harden before incorporating into automation or CI (add retries, timeouts,
assertions, secrets management, and logging as needed).

PowerShell quoting is tricky; this script uses `curl.exe` to avoid the
PowerShell curl alias behavior.
#>

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $root

if (-not (Test-Path "..\payload.json")) {
    Write-Host "Create payload.json in the repo root first. See prod_tests README."; Pop-Location; return
}

if (-not $env:GOVINFO_API_KEY) {
    # Try loading from repo .env
    if (Test-Path "..\.env") {
        Get-Content "..\.env" | ForEach-Object {
            $ln = $_.Trim()
            if (-not $ln -or $ln.StartsWith('#')) { return }
            if ($ln -notmatch '=') { return }
            $parts = $ln -split '=',2
            if (-not $env:GOVINFO_API_KEY) { $env:GOVINFO_API_KEY = $parts[1].Trim().Trim("'\"") }
        }
    }
}

if (-not $env:GOVINFO_API_KEY) {
    Write-Host "GOVINFO_API_KEY not set. Set it in the environment or in ../.env"; Pop-Location; return
}

Write-Host "Posting payload.json to GovInfo using curl.exe (PowerShell-safe)"
curl.exe -i -X POST "https://api.govinfo.gov/search?api_key=$env:GOVINFO_API_KEY" `
  -H "accept: application/json" -H "Content-Type: application/json" `
  --data-binary "@..\payload.json"

Pop-Location
