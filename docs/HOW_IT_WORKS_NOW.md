# How It Works Now (Current Implementation)

This describes the code that exists today, not future architecture.

## 1. Desktop Layer (`apps/desktop`)
- Stack: Vite + React + TypeScript + Tauri scaffold.
- Entry point: `src/main.tsx`.
- Window split:
  - `search` window: transparent Spotlight-style launcher surface
  - `settings` window: normal desktop window for inspector/settings details, created on demand
- On macOS, Tauri startup switches the app to `ActivationPolicy::Accessory` and hides the Dock icon.
- Search UI: `src/Launcher.tsx`.
- Settings UI: `src/App.tsx`.
- Tauri runtime registers `Option+Space` to toggle the launcher window.
- Launcher emits a focus event so the search input is focused immediately on show.
- Launcher hides on `Escape` and can open the settings window from its trailing action.

## 2. Sidecar Layer (`sidecar`)
- Stack: FastAPI + background observer loop.
- Entry: `sidecar/app/main.py`.
- Observer module: `sidecar/app/observer.py`.
- Exposed endpoints:
  - `GET /health` returns status metadata and readiness flags.
  - `POST /ingest` validates event schema/hash and returns `stored/skipped` decisions.
  - `GET /observer/stats` returns observer runtime diagnostics.
  - `GET /index/status` returns embedder/vector index readiness and indexed-count visibility.
  - `GET /search` returns semantic-first matches with keyword fallback.

### Current observer behavior (v1)
- Polls active frontmost app/window title via macOS `osascript`.
- Emits events when:
  - current context remains stable for >=15 seconds, or
  - context changes significantly (app or title change).
- Emits contract-shaped events with computed `context_hash`.
- Feeds events through ingest dedupe/debounce logic.

### Current storage behavior
- Stored events are appended to `sidecar/data/events.jsonl` as the raw local event history.
- Skipped events are not persisted.
- Browser ingest applies a short repeat window keyed by browser tab context so rapid duplicate extension emissions are skipped.
- Sidecar now attempts to initialize the local embedder and LanceDB-backed vector store on startup.
- If the embedder and vector store are ready, sidecar backfills stored JSONL events into the vector index on startup.
- The LanceDB vector index should be treated as a derived retrieval layer built from raw history, not the only source of truth for prior work context.
- The current derived retrieval layer now has an explicit retrieval-document shape, even though it is still close to one retrieval document per raw event for current sources.
- If an older empty vector table exists with the wrong embedding width, sidecar repairs it during the next successful index write so semantic indexing can recover without manual table cleanup.
- If the vector table exists but the local manifest file is missing, sidecar rebuilds indexed-count bookkeeping from the table contents on startup.
- If model/vector dependencies are missing, ingest still works and readiness remains degraded.

### Current search behavior
- `/search` first attempts semantic vector retrieval when both the embedder and LanceDB store are ready.
- If those dependencies are unavailable, it falls back to lightweight keyword scoring over:
  - `app_name`
  - `window_title`
  - `context_text`
- Results are returned in contract-shaped form with score, pagination, active search mode, and supporting raw-event IDs for drill-down.

## 3. Tauri Layer (`apps/desktop/src-tauri`)
- Tauri runtime now manages:
  - a transparent `search` window
  - a normal `settings` window
  - global shortcut registration for `Option+Space`
  - show/hide/open commands for launcher and settings behavior
- A valid RGBA icon exists at `src-tauri/icons/icon.png`.

## 4. What Is Not Implemented Yet
- Local query-time reasoning model integration.
- Launcher search results UI and final HUD workflow beyond the pill-style search surface.

## 5. Quick Run Sequence
1. Start sidecar:
   - `cd sidecar`
   - `.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload`
2. Start desktop:
   - `cd apps/desktop`
   - `npm run tauri dev` (or `npm run dev` for frontend-only)
