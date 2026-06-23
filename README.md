# resume-tailor

Local web app and scripts to tailor an existing HTML resume to a target JD.

## Quick start

1. Create and activate a Python environment.
2. Install deps: pip install -r requirements.txt
3. Run: python scripts/resume_tailor_web.py --port 8787
4. Open: http://127.0.0.1:8787

## Notes

- Without OPENAI_API_KEY, generation uses fallback rules.
- With OPENAI_API_KEY, generation uses model-based rewriting.

