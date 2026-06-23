@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [INFO] Creating virtual environment...
  py -3 -m venv .venv
)

echo [INFO] Activating virtual environment...
call ".venv\Scripts\activate.bat"

echo [INFO] Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

if exist ".env" (
  echo [INFO] Loading environment from .env ...
  for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if not "%%A"=="" if not "%%A:~0,1"=="#" set "%%A=%%B"
  )
)

if "%RESUME_TAILOR_HOST%"=="" set "RESUME_TAILOR_HOST=127.0.0.1"
if "%RESUME_TAILOR_PORT%"=="" set "RESUME_TAILOR_PORT=8787"

echo [INFO] Starting Resume Tailor Studio on http://%RESUME_TAILOR_HOST%:%RESUME_TAILOR_PORT%
python scripts\resume_tailor_web.py --host %RESUME_TAILOR_HOST% --port %RESUME_TAILOR_PORT%
