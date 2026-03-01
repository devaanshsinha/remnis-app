# Remnis

Privacy-first, local-first work-memory engine for macOS.

## Repository Initialization (v0)

This repo is intentionally initialized with structure and requirements first, before framework scaffolding.

### Current structure

- `apps/desktop` - Tauri v2 + Vite + React + TypeScript app (to be scaffolded)
- `sidecar` - Python FastAPI observer/embedding/search engine (to be scaffolded)
- `docs` - supporting architecture and implementation docs
- `requirements.md` - product + engineering requirements baseline

## Next scaffolding steps

1. Scaffold desktop app in `apps/desktop` (Tauri + React + TS).
2. Initialize Python project in `sidecar` (FastAPI, observer service, LanceDB integration).
3. Wire sidecar launch + health checks from Tauri.

