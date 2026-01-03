# Add Python 3.11 to User PATH
#
# This script searches common installation locations for Python 3.11 and
# prepends the install folder and its Scripts subfolder to the user PATH using
# setx (persistent for your user). No admin rights required.
#
# Usage:
# 1) Open PowerShell (normal user) in the repo folder:
#    cd C:\Users\fbpol\Documents\ML_Projects\computer\fastapi-mcp
# 2) Run:
#    .\add-python311-to-path.ps1
# 3) Close and reopen PowerShell to pick up the new PATH.

Write-Output "Searching for Python 3.11 installations..."

$found = $null
$candidates = @(
    "$env:LOCALAPPDATA\Programs\Python\Python311",
    "C:\\Program Files\\Python311",
    "C:\\Python311"
)

# Add per-user common locations under each user
try {
    Get-ChildItem C:\Users -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $p = Join-Path $_.FullName "AppData\Local\Programs\Python\Python311"
        $candidates += $p
    }
} catch {
    # ignore
}

$candidates = $candidates | Select-Object -Unique

foreach ($p in $candidates) {
    if ([string]::IsNullOrWhiteSpace($p)) { continue }
    $exe = Join-Path $p "python.exe"
    if (Test-Path $exe) {
        $found = $p
        break
    }
}

if (-not $found) {
    Write-Output "Python 3.11 was not found in common locations."
    Write-Output "If you installed Python 3.11 in a custom location, run this script with the path as an argument:"
    Write-Output "  .\\add-python311-to-path.ps1 C:\\path\\to\\Python311"
    exit 1
}

Write-Output "Found Python 3.11 installation at: $found"

# Build new PATH entries (install root and Scripts)
$root = $found.TrimEnd('\')
$scripts = Join-Path $root 'Scripts'

# Read current user PATH
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')

if ($userPath -and $userPath -like "*${root}*") {
    Write-Output "Python 3.11 path already present in User PATH: $root"
    exit 0
}

# Prepend root and scripts to user PATH
$newUserPath = "${root};${scripts};" + ($userPath -ne $null ? $userPath : '')

# setx truncates at 1024 characters on some older systems; warn if long
if ($newUserPath.Length -gt 2000) {
    Write-Output "Warning: PATH length is large (>2000 chars). setx may truncate the value."
}

# Persist the new user PATH
setx PATH "$newUserPath" | Out-Null
Write-Output "Updated User PATH (persisted)."
Write-Output "Close and reopen PowerShell to pick up changes, or run: $env:Path = [Environment]::GetEnvironmentVariable('Path','User') + ';' + [Environment]::GetEnvironmentVariable('Path','Machine')"

exit 0
