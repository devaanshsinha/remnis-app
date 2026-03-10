# How It Works Now (Current Implementation)

This describes the code that exists today, not future architecture.

## 1. Desktop Layer (`apps/desktop`)
- Stack: Vite + React + TypeScript + Tauri scaffold.
- Entry point: `src/main.tsx`.
- Main screen: `src/App.tsx`.

## 2. Sidecar Layer (`sidecar`)
- Stack: FastAPI + background observer loop.
- Entry: `sidecar/app/main.py`.
- Observer module: `sidecar/app/observer.py`.
- Exposed endpoints:
  - `GET /health` returns status metadata and readiness flags.
  - `POST /ingest` validates event schema/hash and returns `stored/skipped` decisions.
  - `GET /observer/stats` returns observer runtime diagnostics.
  - `GET /search` returns keyword-ranked matches from persisted events.

### Current observer behavior (v1)
- Polls active frontmost app/window title via macOS `osascript`.
- Emits events when:
  - current context remains stable for >=15 seconds, or
  - context changes significantly (app or title change).
- Emits contract-shaped events with computed `context_hash`.
- Feeds events through ingest dedupe/debounce logic.

### Current storage behavior
- Stored events are appended to `sidecar/data/events.jsonl`.
- Skipped events are not persisted.
- Browser ingest applies a short repeat window keyed by browser tab context so rapid duplicate extension emissions are skipped.
- Sidecar now attempts to initialize the local embedder and LanceDB-backed vector store on startup.
- If model/vector dependencies are missing, ingest still works and readiness remains degraded.

### Current search behavior
- `/search` first attempts semantic vector retrieval when both the embedder and LanceDB store are ready.
- If those dependencies are unavailable, it falls back to lightweight keyword scoring over:
  - `app_name`
  - `window_title`
  - `context_text`
- Results are returned in contract-shaped form with score and pagination.

## 3. Tauri Layer (`apps/desktop/src-tauri`)
- Minimal Tauri v2 scaffold exists:
  - `Cargo.toml`, `build.rs`, `src/main.rs`, `tauri.conf.json`.
- A valid RGBA icon exists at `src-tauri/icons/icon.png`.

## 4. What Is Not Implemented Yet
- Local query-time reasoning model integration.
- HUD command palette and global hotkey flow.

## 5. Quick Run Sequence
1. Start sidecar:
   - `cd sidecar`
   - `.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload`
2. Start desktop:
   - `cd apps/desktop`
   - `npm run tauri dev` (or `npm run dev` for frontend-only)
