# Remnis

Privacy-first, local-first work-memory engine for macOS.

## Repository Initialization (v0)

This repo is intentionally initialized with structure and documentation first, before framework scaffolding.

## Current Structure

- `apps/desktop` - Tauri v2 + Vite + React + TypeScript app (to be scaffolded)
- `sidecar` - Python FastAPI observer/embedding/search engine (to be scaffolded)
- `docs` - project documentation, operating rules, and status tracking
- `requirements.md` - product + engineering requirements baseline

## Documentation Index

- `requirements.md` - canonical requirements and constraints
- `docs/RULES.md` - working rules and guardrails
- `docs/PROJECT_STATUS.md` - what has been done and current state
- `docs/CONTEXT.md` - system-level project context and mental model
- `docs/NEXT_ACTIONS.md` - immediate next actions with purpose and output
- `docs/CONTRACTS.md` - frozen event and API contracts (`v0.1`)
- `docs/ACCEPTANCE_CRITERIA.md` - objective pass/fail gates per phase
- `docs/FAILURE_BEHAVIOR.md` - failure modes, degraded states, and recovery policy

## Scaffolding Status

- Desktop app: skeleton created (`apps/desktop`)
- Python sidecar: skeleton created with `/health` (`sidecar/app/main.py`)

## Recommended Next Step

Run and verify the scaffold locally:
1. Install Python sidecar deps and start sidecar on `127.0.0.1:8765`.
2. Install desktop deps and run the frontend to verify `/health` display.
3. Install Rust toolchain (`cargo`) to enable Tauri runtime.
