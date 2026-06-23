$ErrorActionPreference = 'Stop'

Set-Location $PSScriptRoot

if (-not (Test-Path '.venv/Scripts/python.exe')) {
    Write-Host '[INFO] Creating virtual environment...'
    py -3 -m venv .venv
}

Write-Host '[INFO] Installing dependencies...'
& '.\.venv\Scripts\python.exe' -m pip install --upgrade pip
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt

if (Test-Path '.env') {
    Write-Host '[INFO] Loading environment from .env ...'
    Get-Content '.env' | ForEach-Object {
        if ($_ -and -not $_.StartsWith('#') -and $_.Contains('=')) {
            $parts = $_.Split('=', 2)
            [Environment]::SetEnvironmentVariable($parts[0], $parts[1], 'Process')
        }
    }
}

$hostName = if ($env:RESUME_TAILOR_HOST) { $env:RESUME_TAILOR_HOST } else { '127.0.0.1' }
$port = if ($env:RESUME_TAILOR_PORT) { $env:RESUME_TAILOR_PORT } else { '8787' }

Write-Host "[INFO] Starting Resume Tailor Studio on http://$hostName`:$port"
& '.\.venv\Scripts\python.exe' '.\scripts\resume_tailor_web.py' '--host' $hostName '--port' $port
