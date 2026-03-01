# Python Sidecar

Current status:
- FastAPI skeleton created under `sidecar/app`.
- `GET /health` endpoint implemented in `app/main.py`.
- Dev runner script added: `sidecar/run_dev.sh`.

Responsibilities:
- macOS observer integration (PyObjC)
- Ingest + dedupe + debounce pipeline
- Embedding generation
- LanceDB persistence
- FastAPI local search API

Local run:
1. `cd sidecar`
2. `python3 -m venv .venv`
3. `.venv/bin/pip install fastapi 'uvicorn[standard]'`
4. `.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload`

Current limitation in this environment:
- Network is restricted, so dependency install could not be completed here.
