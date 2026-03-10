# Remnis

Remnis is a local work memory app for macOS developers.

It is designed to help you find past context quickly, such as the terminal error from earlier, the file you edited, or the browser tab you used while solving a bug. All core processing is intended to run locally on your machine.

## Why This App Exists

Developer context is fragmented across editors, terminals, browsers, chat tools, and docs. Remnis is being built to reduce context loss and recovery time by creating a searchable local memory layer of your workflow.

## Who It Is For

- Developers who switch between many tools throughout the day
- Builders who lose track of where they solved a specific issue
- People who want intent-based recall without sending data to a cloud service

## What The App Does

- Watches your active window context on macOS
- Normalizes and deduplicates context events
- Exposes a local API for ingest and search workflows
- Provides a desktop UI that talks to the local sidecar

## End-State Model Architecture

- Remnis is intended to ship with two local models, not one.
- Model 1 is the always-on embedding/indexing model used for background semantic indexing. The baseline planned model is `all-MiniLM-L6-v2`.
- Model 2 is a heavier local query-time reasoning model used only when the user invokes Remnis and wants a better answer, rerank, summary, reminder, or synthesized explanation.
- The app is not considered complete without both model tiers running locally on device.

## What Is Implemented Right Now

- Desktop app scaffold with Tauri + React + TypeScript
- Sidecar service with FastAPI
- `GET /health` endpoint with readiness flags
- `POST /ingest` endpoint with schema validation and hash checks
- `GET /observer/stats` endpoint with observer diagnostics
- `GET /search` endpoint with local keyword ranking
- Observer v1 active-window capture loop
- Dedupe and debounce behavior in ingest pipeline
- Local JSONL persistence for stored events
- Tailwind + shadcn-style UI foundation for future screens

## What Users Will Be Able To Do

- Search for intent like "that docker build error from this morning"
- Recover where and when a task was performed
- Resume work with context snippets and timestamps
- Keep all capture and indexing local to the machine

## What Is Not Implemented Yet

- Local embedding generation and LanceDB integration
- Local query-time reasoning model integration
- Semantic `/search` ranking and query-time rerank/summarize flow
- Full Spotlight-style HUD and global hotkey UX

## Repository Layout

- `apps/desktop` desktop application code
- `sidecar` local FastAPI sidecar service
- `integrations` external adapters (for example browser extension)
- `docs` design docs, contracts, status, and runbooks
- `requirements.md` high-level product and engineering requirements

## Getting Started

### 1. Start sidecar

```bash
cd sidecar
python3 -m venv .venv
.venv/bin/python -m pip install -U pip
.venv/bin/python -m pip install fastapi pydantic 'uvicorn[standard]'
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload
```

### 2. Start desktop app

```bash
cd apps/desktop
npm install
npm run tauri dev
```

### 3. Optional: load browser adapter in Chromium

1. Open `chrome://extensions`
2. Enable `Developer mode`
3. Click `Load unpacked`
4. Select `integrations/browser-extension/chromium`

## Documentation

- `requirements.md` baseline product and engineering requirements
- `docs/CONTEXT.md` system context and mental model
- `docs/CONTRACTS.md` event and API contract definitions
- `docs/FAILURE_BEHAVIOR.md` degraded modes and recovery behavior
- `docs/ACCEPTANCE_CRITERIA.md` phase completion criteria
- `docs/HOW_IT_WORKS_NOW.md` current implementation details
- `docs/PROJECT_STATUS.md` current status and open items
- `docs/NEXT_ACTIONS.md` next implementation steps
- `docs/RULES.md` working rules for the project

## Privacy Approach

- No cloud dependency is required for core functionality.
- Sidecar API is local (`127.0.0.1`) for development.
- The target product direction is local-first storage and retrieval.
