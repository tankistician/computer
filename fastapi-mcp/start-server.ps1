<#
start-server.ps1

Bootstraps the shared workspace .venv (if needed), installs the FastAPI/MCP
requirements, and launches the app from that interpreter so every helper script
shares the same environment.

Usage:
  Open PowerShell, then:
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
    cd C:\Users\fbpol\Documents\ML_Projects\computer\fastapi-mcp
    .\start-server.ps1
#>

function Throw-IfFailed($exe, $args) {
    Write-Output "Running: $exe $args"
    & $exe $args
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $exe $args (exit $LASTEXITCODE)"
    }
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$workspaceRoot = Resolve-Path (Join-Path $scriptDir "..")
$venvPath = Join-Path $workspaceRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

$usePy311 = $false
try {
    & py -3.11 --version > $null 2>&1
    if ($LASTEXITCODE -eq 0) { $usePy311 = $true }
} catch {
    $usePy311 = $false
}

if (-not (Test-Path $venvPython)) {
    Write-Output "Creating shared workspace .venv at $venvPath"
    if ($usePy311) {
        Throw-IfFailed py "-3.11 -m venv $venvPath"
    } else {
        Throw-IfFailed python "-m venv $venvPath"
    }
}

if (-not (Test-Path $venvPython)) {
    throw "Virtual environment python not found at $venvPython"
}

Write-Output "Upgrading pip in shared workspace venv..."
Throw-IfFailed $venvPython "-m pip install --upgrade pip"

$requirements = Join-Path $scriptDir "requirements.txt"
if (Test-Path $requirements) {
    Write-Output "Installing requirements.txt into shared venv..."
    Throw-IfFailed $venvPython "-m pip install -r $requirements"
} else {
    Write-Output "No requirements.txt found; skipping install step."
}

Write-Output "Starting uvicorn with workspace venv python. Press Ctrl+C to stop."
Throw-IfFailed $venvPython "-m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
