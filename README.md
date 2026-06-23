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

## Deploy on Render

This repository includes `render.yaml` and `start_render.sh` for Render deployment.

### Option A: Blueprint deploy (recommended)

1. Open Render Dashboard and click **New +** -> **Blueprint**.
2. Connect repository: `https://github.com/ttoriaa/resume-tailor`.
3. Render will detect `render.yaml` automatically.
4. Set secret env var in Render:
	- `OPENAI_API_KEY` (optional but recommended for model mode)
5. Click **Apply** to deploy.

### Option B: Manual Web Service

1. Create a new **Web Service** from this repository.
2. Build command:
	- `pip install -r requirements.txt`
3. Start command:
	- `bash ./start_render.sh`
4. Add env vars as needed (`OPENAI_API_KEY`, `OPENAI_BASE_URL`, etc.).

### Runtime behavior on Render

- App binds to `0.0.0.0` and uses Render-provided `PORT` automatically.
- Health check path is `/`.

