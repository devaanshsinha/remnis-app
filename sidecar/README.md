# Python Sidecar

## Current Status
- FastAPI skeleton is implemented under `sidecar/app`.
- `GET /health` endpoint is live and consumed by desktop app.
- `POST /ingest` endpoint is implemented with in-memory dedupe/debounce decisions.
- CORS allows local dev frontend origins on port `5173`.
- Step 1 schema module is implemented:
  - canonical event models in `app/schemas.py`
  - context hash helpers in `app/hash_utils.py`

## Key Files
- `app/main.py` - FastAPI app with health and ingest endpoints
- `app/schemas.py` - canonical data contracts and normalization helpers
- `app/hash_utils.py` - SHA-256 context hash compute/verify helpers
- `pyproject.toml` - dependency and project metadata
- `run_dev.sh` - convenience dev runner

## Local Run
1. `cd sidecar`
2. `python3 -m venv .venv`
3. `.venv/bin/pip install fastapi 'uvicorn[standard]'`
4. `.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload`

## Current Contract Note
- Readiness flags are intentionally `false` until observer/db/embedder modules are implemented.
