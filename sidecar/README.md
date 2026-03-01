# Python Sidecar

## Current Status
- FastAPI app is implemented under `sidecar/app`.
- `GET /health` endpoint is live and consumed by desktop app.
- `POST /ingest` endpoint is implemented with in-memory dedupe/debounce decisions.
- Background observer loop is implemented (`app/observer.py`) and starts on app startup.
- CORS allows local dev frontend origins on port `5173`.
- Step 1 schema module is implemented:
  - canonical event models in `app/schemas.py`
  - context hash helpers in `app/hash_utils.py`

## Key Files
- `app/main.py` - FastAPI app with health/ingest endpoints and observer lifecycle
- `app/observer.py` - active-window polling loop and event emission
- `app/schemas.py` - canonical data contracts and normalization helpers
- `app/hash_utils.py` - SHA-256 context hash compute/verify helpers
- `pyproject.toml` - dependency and project metadata
- `run_dev.sh` - convenience dev runner

## Local Run
1. `cd sidecar`
2. `python3 -m venv .venv`
3. `.venv/bin/pip install fastapi pydantic 'uvicorn[standard]'`
4. `.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload`

## Current Contract Note
- `observer_ready` should become `true` when observer capture loop is functioning.
- `db_ready` and `embedder_ready` remain `false` until those modules are implemented.

