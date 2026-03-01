# Python Sidecar

## Current Status
- FastAPI app is implemented under `sidecar/app`.
- `GET /health` endpoint is live and consumed by desktop app.
- `POST /ingest` endpoint is implemented with dedupe/debounce decisions.
- `GET /observer/stats` endpoint is available for observer diagnostics.
- `GET /search` endpoint is available as a keyword fallback over local persisted events.
- Background observer loop is implemented (`app/observer.py`) and starts on app startup.
- Stored events are persisted to `sidecar/data/events.jsonl`.
- CORS allows local dev frontend origins on port `5173`.

## Key Files
- `app/main.py` - FastAPI app with health/ingest/stats/search endpoints and observer lifecycle
- `app/observer.py` - active-window polling loop and event emission
- `app/schemas.py` - canonical contracts and response models
- `app/hash_utils.py` - SHA-256 context hash compute/verify helpers
- `data/events.jsonl` - append-only stored event log
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
- `/observer/stats` includes `observer_state` and `last_error_code` for degraded-state diagnostics.
- `/search` currently uses keyword scoring and will be replaced by semantic ranking in the embedding/LanceDB phase.

