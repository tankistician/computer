<#
start-server.ps1

Creates a .venv (using py -3.11 if available, else `python`), installs dependencies
from requirements.txt into the venv, and launches the app with the venv Python
so you don't need to modify global PATH.

Usage:
  Open PowerShell, then:
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
    cd C:\Users\fbpol\Documents\ML_Projects\computer\fastapi-mcp
    .\start-server.ps1

#>

Write-Output "Starting start-server.ps1"

# Helper to run a command and show output
function Run-Command {
    param($exe, $args)
    Write-Output "Running: $exe $args"
    & $exe $args
    if ($LASTEXITCODE -ne 0) {git
        throw "Command failed: $exe $args (exit $LASTEXITCODE)"
    }
}

# 1) choose python executable to create venv (prefer py -3.11)
$usePy311 = $false
try {
    & py -3.11 --version > $null 2>&1
    if ($LASTEXITCODE -eq 0) { $usePy311 = $true }
} catch { $usePy311 = $false }

if ($usePy311) {
    Write-Output "Using py -3.11 to create venv"
    & py -3.11 -m venv .venv
} else {
    Write-Output "py -3.11 not available; falling back to 'python' on PATH"
    & python -m venv .venv
}

# venv python path
$venvPython = Join-Path $PWD ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Virtual environment python not found at $venvPython"
}

# 2) upgrade pip and install requirements
Write-Output "Upgrading pip in venv..."
& $venvPython -m pip install --upgrade pip

if (Test-Path "requirements.txt") {
    Write-Output "Installing requirements.txt into venv..."
    & $venvPython -m pip install -r requirements.txt
} else {
    Write-Output "No requirements.txt found; skipping install step."
}

# 3) start the server with the venv python (runs in foreground)
Write-Output "Starting uvicorn using venv python. Press Ctrl+C to stop."
& $venvPython -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
