<#
EXAMPLE/DEVELOPMENT SCRIPT

Orchestrator to run the prod smoke checks in sequence.

This is an example helper for local/manual verification only. Do not assume
it is safe to run in CI or production without reviewing and adapting it.

Usage (PowerShell):
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .\run_all.ps1

This script assumes the repo `.env` contains any needed API keys and that
the venv is activated (or you have a full path to the python executable).
#>

function Load-DotEnv {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }
    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith('#')) { return }
        if ($line -notmatch '=') { return }
        $pair = $line -split '=', 2
        $name = $pair[0].Trim()
        $value = $pair[1].Trim().Trim("'\"")
        if (-not [string]::IsNullOrEmpty($env:$name)) { return }
        $env:$name = $value
    }
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $root
Write-Host "Loading .env from repository root if present..."
Load-DotEnv (Join-Path $root "..\.env")

if (-not $env:PYTHONPATH) {
    $env:PYTHONPATH = (Resolve-Path "..\fastapi-mcp").ProviderPath
}

Write-Host "Running 01 - query upstream source (PowerShell example)"
if (Test-Path "01_query_source.ps1") { & .\01_query_source.ps1 }

Write-Host "Running 03 - invoke tool in-process"
& $env:PYTHONPATH\..\.venv\Scripts\python.exe ..\fastapi-mcp\scripts\invoke_gov_inproc.py

Write-Host "Done. For HTTP tests, start the server and run 04_invoke_tool_http.py"
Pop-Location
