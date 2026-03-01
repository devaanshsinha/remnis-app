# Remnis

Privacy-first, local-first work-memory engine for macOS.

## Current Structure

- `apps/desktop` - Tauri + Vite + React + TypeScript desktop app
- `sidecar` - Python FastAPI sidecar service
- `docs` - architecture, contracts, status, and runbooks
- `requirements.md` - product + engineering requirements baseline

## Current Implementation Status

- Desktop app runs and calls sidecar `GET /health`.
- Sidecar `GET /health` endpoint is live with readiness flags.
- Tauri scaffold is present and runnable with installed dependencies.
- Tailwind + shadcn-style UI foundation is set up in desktop app.

## Documentation Index

- `requirements.md` - canonical requirements and constraints
- `docs/RULES.md` - working rules and guardrails
- `docs/CONTEXT.md` - system-level context and mental model
- `docs/CONTRACTS.md` - frozen event and API contracts (`v0.1`)
- `docs/FAILURE_BEHAVIOR.md` - failure modes, degraded states, retry policy
- `docs/ACCEPTANCE_CRITERIA.md` - objective pass/fail gates per phase
- `docs/HOW_IT_WORKS_NOW.md` - current code behavior and runtime flow
- `docs/PROJECT_STATUS.md` - what has been done and what is next
- `docs/NEXT_ACTIONS.md` - action list and progress markers

## Run (Current)

Sidecar:
1. `cd sidecar`
2. `python3 -m venv .venv`
3. `.venv/bin/pip install fastapi 'uvicorn[standard]'`
4. `.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload`

Desktop:
1. `cd apps/desktop`
2. `npm install`
3. `npm run tauri dev`

