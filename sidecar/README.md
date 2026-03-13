# Python Sidecar

## Current Status
- FastAPI app is implemented under `sidecar/app`.
- `GET /health` endpoint is live and consumed by desktop app.
- `POST /ingest` endpoint is implemented with dedupe/debounce decisions.
- `POST /ingest/browser` endpoint is available for browser adapter payloads.
- `GET /observer/stats` endpoint is available for observer diagnostics.
- `GET /index/status` endpoint is available for embedder/vector index visibility.
- `GET /events` endpoint is available with filterable retrieval over persisted events.
- `GET /search` endpoint is available as a keyword fallback over local persisted events.
- Background observer loop is implemented (`app/observer.py`) and starts on app startup.
- Stored events are persisted to `sidecar/data/events.jsonl`.
- Observer-based browser window events are skipped entirely.
- Browser capture is handled by the extension ingest path (`/ingest/browser`).
- Browser URLs are normalized on ingest (tracking params removed) for cleaner dedupe/search behavior.
- Browser ingest applies a short server-side repeat window to suppress rapid duplicate tab emissions.
- CORS allows local dev frontend origins on port `5173`.
- Final sidecar architecture is intended to serve two local model roles:
  - background embedding/indexing
  - query-time local reasoning
- Embedder and vector-store initialization now exist in code and drive real readiness flags when dependencies are installed.
- On startup, the sidecar backfills previously stored JSONL events into the vector index when embedder and LanceDB dependencies are available.

## Key Files
- `app/main.py` - FastAPI app with health/ingest/stats/index/events/search endpoints and observer lifecycle
- `app/observer.py` - active-window polling loop and event emission
- `app/schemas.py` - canonical contracts and response models
- `app/hash_utils.py` - SHA-256 context hash compute/verify helpers
- `data/events.jsonl` - append-only stored event log
- `pyproject.toml` - dependency and project metadata
- `run_dev.sh` - convenience dev runner

## Local Run
1. `cd sidecar`
2. `uv sync`
3. `uv run uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload`

### Python Version
- `sidecar/.python-version` is set to `3.13` so `uv` picks a Python version that matches the current dependency set.
- `pyproject.toml` currently allows Python `>=3.11,<3.14`.
- This is deliberate: `torch` appears to support `3.14`, but `sentence-transformers` does not currently advertise `3.14` support.

## Current Contract Note
- `observer_ready` should become `true` when observer capture loop is functioning.
- `db_ready` and `embedder_ready` now reflect actual sidecar dependency initialization state.
- `/observer/stats` includes `observer_state` and `last_error_code` for degraded-state diagnostics.
- `/index/status` exposes embedder readiness, vector-store readiness, indexed count, and last known dependency errors.
- `/events` provides filterable recent-history retrieval for UI and debugging.
- `/search` supports deterministic filters (`source`, `app_name`, `from_ts`, `to_ts`).
- `/search` now attempts vector retrieval when the embedder and LanceDB store are ready, and falls back to keyword scoring otherwise.
- `/search` reports its active mode (`semantic` or `keyword_fallback`) in the response payload.
- The finished product also requires a second local query-time reasoning layer on top of retrieval.
- `/ingest/browser` maps browser events into canonical ingest events and reuses dedupe/debounce.
