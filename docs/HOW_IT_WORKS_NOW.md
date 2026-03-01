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
- Stack: FastAPI skeleton.
- Entry: `sidecar/app/main.py`.
- Exposed endpoint:
  - `GET /health` returns `status`, `service`, `version`, `time_utc`, and readiness flags.
- Dev CORS is enabled for:
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`

### Current readiness semantics
- `observer_ready=false`
- `db_ready=false`
- `embedder_ready=false`

These are expected until observer/database/embedding modules are implemented.

## 3. Tauri Layer (`apps/desktop/src-tauri`)
- Minimal Tauri v2 scaffold exists:
  - `Cargo.toml`, `build.rs`, `src/main.rs`, `tauri.conf.json`.
- A valid RGBA icon exists at `src-tauri/icons/icon.png`.
- App can run through `npm run tauri dev` once JS dependencies are installed.

## 4. What Is Not Implemented Yet
- Observer capture logic (active window monitoring).
- Ingest endpoint and dedupe/debounce pipeline.
- LanceDB integration.
- Embedding model integration.
- HUD command palette and global hotkey flow.

## 5. Quick Run Sequence
1. Start sidecar:
   - `cd sidecar`
   - `.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload`
2. Start desktop:
   - `cd apps/desktop`
   - `npm run tauri dev` (or `npm run dev` for frontend-only)

