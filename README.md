# resume-tailor

Local web app and scripts to tailor an existing HTML resume to a target JD.

## What is included

- `scripts/resume_tailor_web.py`: local web UI (`http://127.0.0.1:8787`)
- `scripts/tailor_resume_for_jd.py`: core tailoring logic (fallback + model mode)
- `.github/workflows/ci.yml`: minimal CI (syntax check + startup smoke test)
- `.env.example`: release-ready environment template
- `start_windows.bat` / `start_windows.ps1`: one-click startup scripts for Windows

## Quick start

1. Create and activate a Python environment.
2. Install deps: pip install -r requirements.txt
3. Run: python scripts/resume_tailor_web.py --port 8787
4. Open: http://127.0.0.1:8787

## Notes

- Without OPENAI_API_KEY, generation uses fallback rules.
- With OPENAI_API_KEY, generation uses model-based rewriting.

## Environment variables

Copy `.env.example` to `.env` and fill values as needed.

Required for model mode:
- `OPENAI_API_KEY`

Optional:
- `OPENAI_BASE_URL` (default: `https://api.openai.com/v1`)
- `RESUME_TAILOR_MODEL` (default: `gpt-4o-mini`)
- `RESUME_JD_OCR_MODEL` (default: `gpt-4.1-mini`)
- `RESUME_TAILOR_HOST` (default: `127.0.0.1`)
- `RESUME_TAILOR_PORT` (default: `8787`)

## Windows one-click startup

- CMD: run `start_windows.bat`
- PowerShell: run `./start_windows.ps1`

Both scripts will:
1. Create `.venv` if missing
2. Install dependencies
3. Load `.env` if present
4. Start web app

