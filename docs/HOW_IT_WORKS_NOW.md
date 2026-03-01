# How It Works Now (Current Implementation)

This describes the code that exists today, not future architecture.

## 1. Desktop Layer (`apps/desktop`)
- Stack: Vite + React + TypeScript + Tauri scaffold.
- Entry point: `src/main.tsx`.
- Main screen: `src/App.tsx`.
- UI primitives:
  - `src/components/ui/button.tsx` (shadcn-style Button primitive)
  - `src/lib/utils.ts` (`cn` helper for class merging)
- Styling:
  - `src/styles.css` uses Tailwind directives and CSS token variables.
  - Black/white default visual tokens are configured in `:root`.

### Current behavior
- On initial render, `App.tsx` calls `fetchHealth()`.
- `fetchHealth()` requests `http://127.0.0.1:8765/health`.
- UI displays:
  - sidecar status and version,
  - UTC timestamp,
  - readiness flags (`observer`, `db`, `embedder`).
- The refresh button triggers the same health fetch manually.

## 2. Sidecar Layer (`sidecar`)
- Stack: FastAPI + background observer loop.
- Entry: `sidecar/app/main.py`.
- Observer module: `sidecar/app/observer.py`.
- Exposed endpoints:
  - `GET /health` returns status metadata and readiness flags.
  - `POST /ingest` validates event schema/hash and returns `stored/skipped` decisions.

### Current observer behavior (v1)
- Polls active frontmost app/window title via macOS `osascript`.
- Emits events when:
  - current context remains stable for >=15 seconds, or
  - context changes significantly (app or title change).
- Emits contract-shaped events with computed `context_hash`.
- Feeds events through ingest dedupe/debounce logic in-memory.

### Current readiness semantics
- `observer_ready=true` when capture loop is successfully polling.
- `observer_ready=false` when capture fails (e.g. permissions/automation issues).
- `db_ready=false`
- `embedder_ready=false`

## 3. Tauri Layer (`apps/desktop/src-tauri`)
- Minimal Tauri v2 scaffold exists:
  - `Cargo.toml`, `build.rs`, `src/main.rs`, `tauri.conf.json`.
- A valid RGBA icon exists at `src-tauri/icons/icon.png`.
- App can run through `npm run tauri dev` once JS dependencies are installed.

## 4. What Is Not Implemented Yet
- Persistent storage for ingest events.
- LanceDB integration.
- Embedding model integration.
- `/search` API and ranking.
- HUD command palette and global hotkey flow.

## 5. Quick Run Sequence
1. Start sidecar:
   - `cd sidecar`
   - `.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload`
2. Start desktop:
   - `cd apps/desktop`
   - `npm run tauri dev` (or `npm run dev` for frontend-only)

