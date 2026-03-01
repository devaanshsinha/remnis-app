# Remnis

Remnis is a local work memory app for macOS developers.

It is designed to help you find past context quickly, such as the terminal error from earlier, the file you edited, or the browser tab you used while solving a bug. All core processing is intended to run locally on your machine.

## What The App Does

- Watches your active window context on macOS
- Normalizes and deduplicates context events
- Exposes a local API for ingest and search workflows
- Provides a desktop UI that talks to the local sidecar

## What Is Implemented Right Now

- Desktop app scaffold with Tauri + React + TypeScript
- Sidecar service with FastAPI
- `GET /health` endpoint with readiness flags
- `POST /ingest` endpoint with schema validation and hash checks
- Observer v1 active-window capture loop
- Basic dedupe and debounce behavior in memory
- Tailwind + shadcn-style UI foundation for future screens

## What Is Not Implemented Yet

- Persistent event storage
- Embedding generation and LanceDB integration
- Semantic `/search` endpoint
- Full Spotlight-style HUD and global hotkey UX

## Repository Layout

- `apps/desktop` desktop application code
- `sidecar` local FastAPI sidecar service
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
